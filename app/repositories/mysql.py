"""MySQL persistence adapter compatible with local MySQL and teammate RDS.

Supported live schemas:
- Local verified schema: ``events`` + extended ``reminders`` columns.
- Edwin RDS schema: ``care_events`` + compact ``reminders`` columns.

The adapter detects the existing table/column contract through
``information_schema`` and only emits parameterized SQL. Table identifiers are
selected from a fixed allowlist and never come from the model or user input.
"""

from __future__ import annotations

import logging
import threading
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import unquote, urlparse
from zoneinfo import ZoneInfo

try:
    import mysql.connector as mysql_connector
    from mysql.connector import Error as MySQLError
    from mysql.connector.connection import MySQLConnection
except ModuleNotFoundError:  # Allows memory-mode tests without MySQL extras.
    mysql_connector = None
    MySQLError = Exception  # type: ignore[assignment,misc]
    MySQLConnection = Any  # type: ignore[assignment,misc]

from app.repositories.base import CareEvent, Reminder, ScheduleItem

logger = logging.getLogger(__name__)
TAIPEI_TZ = ZoneInfo("Asia/Taipei")
UTC = timezone.utc
_ALLOWED_EVENT_TABLES = frozenset({"events", "care_events"})
_ALLOWED_SSL_MODES = frozenset(
    {"preferred", "required", "verify_ca", "verify_identity", "disabled"}
)


class RepositoryConfigurationError(RuntimeError):
    """Raised when DATABASE_URL or database schema cannot be used safely."""


class RepositoryDataError(RuntimeError):
    """Raised when required persona/user data is absent or inconsistent."""


@dataclass(frozen=True)
class SchemaCapabilities:
    """Detected, allowlisted database contract."""

    event_table: str
    event_columns: frozenset[str]
    reminder_columns: frozenset[str]


def parse_mysql_database_url(
    database_url: str,
    *,
    ssl_mode: str = "preferred",
    ssl_ca: str | None = None,
) -> dict[str, Any]:
    """Parse a mysql:// URL into mysql-connector keyword arguments.

    ``verify_ca`` and ``verify_identity`` require an explicit CA bundle path.
    The cloud Docker image installs the Amazon RDS global bundle at
    ``/opt/aws/rds-global-bundle.pem``.
    """

    parsed = urlparse(database_url)
    if parsed.scheme not in {"mysql", "mysql+mysqlconnector"}:
        raise RepositoryConfigurationError(
            "DATABASE_URL must use mysql:// or mysql+mysqlconnector://"
        )
    if not parsed.hostname or not parsed.path or parsed.path == "/":
        raise RepositoryConfigurationError("DATABASE_URL must include host and database")

    normalized_ssl_mode = ssl_mode.strip().lower()
    if normalized_ssl_mode not in _ALLOWED_SSL_MODES:
        raise RepositoryConfigurationError(
            "DATABASE_SSL_MODE must be one of: "
            + ", ".join(sorted(_ALLOWED_SSL_MODES))
        )

    kwargs: dict[str, Any] = {
        "host": parsed.hostname,
        "port": parsed.port or 3306,
        "user": unquote(parsed.username or ""),
        "password": unquote(parsed.password or ""),
        "database": unquote(parsed.path.lstrip("/")),
        "charset": "utf8mb4",
        "use_unicode": True,
        "autocommit": False,
        "connection_timeout": 10,
    }

    if normalized_ssl_mode == "disabled":
        kwargs["ssl_disabled"] = True
    else:
        kwargs["ssl_disabled"] = False
        if normalized_ssl_mode in {"verify_ca", "verify_identity"}:
            if not ssl_ca:
                raise RepositoryConfigurationError(
                    f"DATABASE_SSL_MODE={normalized_ssl_mode} requires DATABASE_SSL_CA"
                )
            ca_path = Path(ssl_ca)
            if not ca_path.is_file():
                raise RepositoryConfigurationError(
                    f"DATABASE_SSL_CA does not exist: {ca_path}"
                )
            kwargs["ssl_ca"] = str(ca_path)
            kwargs["ssl_verify_cert"] = True
            kwargs["ssl_verify_identity"] = normalized_ssl_mode == "verify_identity"
        elif normalized_ssl_mode == "required":
            kwargs["ssl_verify_cert"] = False
            kwargs["ssl_verify_identity"] = False
        # preferred keeps TLS enabled while allowing connector defaults.

    return kwargs


def _to_utc_naive(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("datetime must include timezone information")
    return value.astimezone(UTC).replace(tzinfo=None)


def _from_utc_naive(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(TAIPEI_TZ)


def _safe_event_table(value: str) -> str:
    normalized = value.strip().lower()
    if normalized == "auto":
        return normalized
    if normalized not in _ALLOWED_EVENT_TABLES:
        raise RepositoryConfigurationError(
            "CARE_EVENT_TABLE must be auto, events, or care_events"
        )
    return normalized


class MySQLCareRepository:
    """Persistent repository mapped to either supported teammate schema."""

    def __init__(
        self,
        database_url: str,
        *,
        care_event_table: str = "auto",
        ssl_mode: str = "preferred",
        ssl_ca: str | None = None,
    ) -> None:
        self._connection_kwargs = parse_mysql_database_url(
            database_url,
            ssl_mode=ssl_mode,
            ssl_ca=ssl_ca,
        )
        self._event_table_preference = _safe_event_table(care_event_table)
        self._schema: SchemaCapabilities | None = None
        self._schema_lock = threading.Lock()

    @property
    def event_table(self) -> str:
        """Return detected event table or the configured safe preference."""
        if self._schema is not None:
            return self._schema.event_table
        return self._event_table_preference

    @contextmanager
    def _connection(self) -> Iterator[MySQLConnection]:
        connection: MySQLConnection | None = None
        try:
            if mysql_connector is None:
                raise RepositoryConfigurationError(
                    "mysql-connector-python is required for MySQL/RDS mode"
                )
            connection = mysql_connector.connect(**self._connection_kwargs)
            yield connection
        except MySQLError:
            if connection is not None and connection.is_connected():
                connection.rollback()
            raise
        finally:
            if connection is not None and connection.is_connected():
                connection.close()

    def _detect_schema(self, connection: MySQLConnection) -> SchemaCapabilities:
        if self._schema is not None:
            return self._schema

        with self._schema_lock:
            if self._schema is not None:
                return self._schema

            cursor = connection.cursor()
            try:
                cursor.execute(
                    """
                    SELECT table_name, column_name
                      FROM information_schema.columns
                     WHERE table_schema = %s
                       AND table_name IN ('events', 'care_events', 'reminders')
                    """,
                    (self._connection_kwargs["database"],),
                )
                columns_by_table: dict[str, set[str]] = {}
                for table_name, column_name in cursor.fetchall():
                    columns_by_table.setdefault(str(table_name), set()).add(str(column_name))
            finally:
                cursor.close()

            preferred = self._event_table_preference
            if preferred == "auto":
                # Prefer the already end-to-end verified local table when both
                # happen to exist; otherwise use Edwin's cloud table.
                if "events" in columns_by_table:
                    event_table = "events"
                elif "care_events" in columns_by_table:
                    event_table = "care_events"
                else:
                    raise RepositoryConfigurationError(
                        "Database must contain events or care_events"
                    )
            elif preferred in columns_by_table:
                event_table = preferred
            else:
                raise RepositoryConfigurationError(
                    f"Configured event table does not exist: {preferred}"
                )

            reminder_columns = frozenset(columns_by_table.get("reminders", set()))
            required_reminder_columns = {
                "reminder_id",
                "persona_id",
                "title",
                "scheduled_at",
                "importance",
                "reminder_status",
                "created_at",
                "updated_at",
            }
            missing = required_reminder_columns - reminder_columns
            if missing:
                raise RepositoryConfigurationError(
                    "reminders table is missing required columns: "
                    + ", ".join(sorted(missing))
                )

            event_columns = frozenset(columns_by_table[event_table])
            required_event_columns = {
                "event_id",
                "persona_id",
                "event_type",
                "content",
                "event_time",
                "created_at",
                "updated_at",
            }
            missing = required_event_columns - event_columns
            if missing:
                raise RepositoryConfigurationError(
                    f"{event_table} is missing required columns: "
                    + ", ".join(sorted(missing))
                )

            self._schema = SchemaCapabilities(
                event_table=event_table,
                event_columns=event_columns,
                reminder_columns=reminder_columns,
            )
            logger.info(
                "Detected MySQL schema: event_table=%s reminder_columns=%s",
                event_table,
                len(reminder_columns),
            )
            return self._schema

    def ping(self) -> bool:
        with self._connection() as connection:
            connection.ping(reconnect=False, attempts=1, delay=0)
            self._detect_schema(connection)
        return True

    @staticmethod
    def _ensure_active_persona(cursor: Any, persona_id: str) -> None:
        cursor.execute(
            """
            SELECT persona_id
              FROM personas
             WHERE persona_id = %s
               AND status = 'active'
               AND deleted_at IS NULL
             LIMIT 1
            """,
            (persona_id,),
        )
        if cursor.fetchone() is None:
            raise RepositoryDataError(f"Unknown or inactive persona_id: {persona_id}")

    @staticmethod
    def _existing_user_id(cursor: Any, requester_id: str) -> str | None:
        cursor.execute(
            """
            SELECT user_id
              FROM app_users
             WHERE user_id = %s
               AND is_active = TRUE
             LIMIT 1
            """,
            (requester_id,),
        )
        row = cursor.fetchone()
        return str(row[0]) if row else None

    def create_care_event(
        self,
        persona_id: str,
        event_type: str,
        content: str,
        event_time: datetime,
        confidence: float | None,
        created_by: str,
        source_text: str | None = None,
        idempotency_key: str | None = None,
    ) -> str:
        # Neither supported event table has an idempotency column. Duplicate
        # suppression remains enforced by ToolGateway's server-side store.
        del idempotency_key

        event_id = str(uuid.uuid4())
        event_time_utc = _to_utc_naive(event_time)
        now_utc = datetime.now(UTC).replace(tzinfo=None)

        with self._connection() as connection:
            schema = self._detect_schema(connection)
            cursor = connection.cursor()
            try:
                self._ensure_active_persona(cursor, persona_id)
                existing_user_id = self._existing_user_id(cursor, created_by)
                actor_type = "user" if existing_user_id else "agent"

                table = schema.event_table  # fixed allowlist, not user input
                cursor.execute(
                    f"""
                    INSERT INTO `{table}` (
                        event_id,
                        persona_id,
                        event_type,
                        content,
                        event_time,
                        confidence,
                        source_text,
                        memory_status,
                        risk_level,
                        created_by_type,
                        created_by_id,
                        committed_at,
                        created_at,
                        updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s,
                        'committed', 'low', %s, %s, %s, %s, %s
                    )
                    """,
                    (
                        event_id,
                        persona_id,
                        event_type,
                        content,
                        event_time_utc,
                        confidence,
                        source_text,
                        actor_type,
                        existing_user_id,
                        now_utc,
                        now_utc,
                        now_utc,
                    ),
                )
                connection.commit()
                return event_id
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()

    def create_reminder(
        self,
        persona_id: str,
        title: str,
        scheduled_at: datetime,
        importance: str,
        created_by: str,
        idempotency_key: str | None = None,
    ) -> str:
        reminder_id = str(uuid.uuid4())
        scheduled_at_utc = _to_utc_naive(scheduled_at)
        now_utc = datetime.now(UTC).replace(tzinfo=None)
        effective_key = idempotency_key or f"reminder:{reminder_id}"
        normalized_importance = importance.strip().lower()
        requires_confirmation = normalized_importance in {"high", "critical"}
        confirmation_status = "confirmed" if requires_confirmation else "not_required"
        confirmed_at = now_utc if requires_confirmation else None

        with self._connection() as connection:
            schema = self._detect_schema(connection)
            cursor = connection.cursor()
            try:
                self._ensure_active_persona(cursor, persona_id)

                if "idempotency_key" in schema.reminder_columns:
                    cursor.execute(
                        """
                        SELECT reminder_id
                          FROM reminders
                         WHERE idempotency_key = %s
                         LIMIT 1
                        """,
                        (effective_key,),
                    )
                    existing = cursor.fetchone()
                    if existing:
                        connection.rollback()
                        return str(existing[0])

                # Validate requester identity even though reminders does not
                # currently store created_by_id in either supported schema.
                self._existing_user_id(cursor, created_by)

                columns = [
                    "reminder_id",
                    "persona_id",
                    "title",
                    "description",
                    "scheduled_at",
                    "importance",
                    "reminder_status",
                    "created_at",
                    "updated_at",
                ]
                values: list[Any] = [
                    reminder_id,
                    persona_id,
                    title,
                    None,
                    scheduled_at_utc,
                    normalized_importance,
                    "scheduled",
                    now_utc,
                    now_utc,
                ]

                optional_values: tuple[tuple[str, Any], ...] = (
                    ("risk_level", "low"),
                    ("confirmation_status", confirmation_status),
                    ("idempotency_key", effective_key),
                    ("confirmed_at", confirmed_at),
                )
                for column, value in optional_values:
                    if column in schema.reminder_columns:
                        columns.append(column)
                        values.append(value)

                column_sql = ", ".join(f"`{column}`" for column in columns)
                placeholders = ", ".join(["%s"] * len(columns))
                cursor.execute(
                    f"INSERT INTO reminders ({column_sql}) VALUES ({placeholders})",
                    tuple(values),
                )
                connection.commit()
                return reminder_id
            except MySQLError as exc:
                connection.rollback()
                if (
                    getattr(exc, "errno", None) == 1062
                    and "idempotency_key" in schema.reminder_columns
                ):
                    cursor.execute(
                        """
                        SELECT reminder_id
                          FROM reminders
                         WHERE idempotency_key = %s
                         LIMIT 1
                        """,
                        (effective_key,),
                    )
                    existing = cursor.fetchone()
                    if existing:
                        return str(existing[0])
                raise
            finally:
                cursor.close()

    def get_user_schedule(
        self,
        persona_id: str,
        target_date: date | None = None,
    ) -> list[ScheduleItem]:
        if target_date is None:
            target_date = datetime.now(TAIPEI_TZ).date()

        start_local = datetime.combine(target_date, time.min, tzinfo=TAIPEI_TZ)
        end_local = datetime.combine(
            target_date.fromordinal(target_date.toordinal() + 1),
            time.min,
            tzinfo=TAIPEI_TZ,
        )
        start_utc = _to_utc_naive(start_local)
        end_utc = _to_utc_naive(end_local)

        with self._connection() as connection:
            self._detect_schema(connection)
            cursor = connection.cursor()
            try:
                self._ensure_active_persona(cursor, persona_id)
                cursor.execute(
                    """
                    SELECT reminder_id, title, scheduled_at
                      FROM reminders
                     WHERE persona_id = %s
                       AND LOWER(reminder_status) = 'scheduled'
                       AND scheduled_at >= %s
                       AND scheduled_at < %s
                     ORDER BY scheduled_at ASC
                    """,
                    (persona_id, start_utc, end_utc),
                )
                return [
                    ScheduleItem(
                        item_id=str(row[0]),
                        item_type="reminder",
                        title=str(row[1]),
                        scheduled_time=_from_utc_naive(row[2]),
                    )
                    for row in cursor.fetchall()
                ]
            finally:
                cursor.close()

    def claim_due_reminders(
        self,
        now: datetime,
        *,
        limit: int,
        missed_after_seconds: int,
    ) -> list[Reminder]:
        """Atomically claim due reminders for one scheduler worker."""
        if now.tzinfo is None:
            raise ValueError("now must include timezone information")
        if limit < 1:
            return []

        now_utc = _to_utc_naive(now)
        claimed: list[Reminder] = []

        with self._connection() as connection:
            schema = self._detect_schema(connection)
            cursor = connection.cursor()
            try:
                connection.start_transaction()
                idempotency_select = (
                    "idempotency_key" if "idempotency_key" in schema.reminder_columns else "NULL"
                )
                cursor.execute(
                    f"""
                    SELECT reminder_id, persona_id, title, description,
                           scheduled_at, importance, created_at, {idempotency_select}
                      FROM reminders
                     WHERE LOWER(reminder_status) = 'scheduled'
                       AND scheduled_at <= %s
                     ORDER BY scheduled_at ASC
                     LIMIT %s
                     FOR UPDATE SKIP LOCKED
                    """,
                    (now_utc, int(limit)),
                )
                rows = cursor.fetchall()

                for row in rows:
                    reminder_id = str(row[0])
                    scheduled_local = _from_utc_naive(row[4])
                    overdue_seconds = max(
                        0.0,
                        (now.astimezone(UTC) - scheduled_local.astimezone(UTC)).total_seconds(),
                    )
                    if overdue_seconds > missed_after_seconds:
                        cursor.execute(
                            """
                            UPDATE reminders
                               SET reminder_status = 'missed',
                                   updated_at = %s
                             WHERE reminder_id = %s
                               AND LOWER(reminder_status) = 'scheduled'
                            """,
                            (now_utc, reminder_id),
                        )
                        continue

                    cursor.execute(
                        """
                        UPDATE reminders
                           SET reminder_status = 'triggering',
                               updated_at = %s
                         WHERE reminder_id = %s
                           AND LOWER(reminder_status) = 'scheduled'
                        """,
                        (now_utc, reminder_id),
                    )
                    if cursor.rowcount != 1:
                        continue

                    claimed.append(
                        Reminder(
                            record_id=reminder_id,
                            persona_id=str(row[1]),
                            title=str(row[2]),
                            description=row[3],
                            scheduled_at=scheduled_local,
                            importance=str(row[5]),
                            created_at=_from_utc_naive(row[6]),
                            created_by="",
                            idempotency_key=row[7],
                            status="triggering",
                        )
                    )

                connection.commit()
                return claimed
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()

    def mark_reminder_triggered(
        self,
        reminder_id: str,
        *,
        triggered_at: datetime,
    ) -> bool:
        triggered_at_utc = _to_utc_naive(triggered_at)
        with self._connection() as connection:
            self._detect_schema(connection)
            cursor = connection.cursor()
            try:
                cursor.execute(
                    """
                    UPDATE reminders
                       SET reminder_status = 'triggered',
                           triggered_at = %s,
                           updated_at = %s
                     WHERE reminder_id = %s
                       AND LOWER(reminder_status) = 'triggering'
                    """,
                    (triggered_at_utc, triggered_at_utc, reminder_id),
                )
                changed = cursor.rowcount == 1
                connection.commit()
                return changed
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()

    def mark_reminder_failed(
        self,
        reminder_id: str,
        *,
        failed_at: datetime,
    ) -> bool:
        failed_at_utc = _to_utc_naive(failed_at)
        with self._connection() as connection:
            self._detect_schema(connection)
            cursor = connection.cursor()
            try:
                cursor.execute(
                    """
                    UPDATE reminders
                       SET reminder_status = 'failed',
                           updated_at = %s
                     WHERE reminder_id = %s
                       AND LOWER(reminder_status) = 'triggering'
                    """,
                    (failed_at_utc, reminder_id),
                )
                changed = cursor.rowcount == 1
                connection.commit()
                return changed
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()

    def recover_stale_reminders(
        self,
        *,
        stale_before: datetime,
    ) -> int:
        stale_before_utc = _to_utc_naive(stale_before)
        now_utc = datetime.now(UTC).replace(tzinfo=None)
        with self._connection() as connection:
            self._detect_schema(connection)
            cursor = connection.cursor()
            try:
                cursor.execute(
                    """
                    UPDATE reminders
                       SET reminder_status = 'scheduled',
                           updated_at = %s
                     WHERE LOWER(reminder_status) = 'triggering'
                       AND updated_at < %s
                    """,
                    (now_utc, stale_before_utc),
                )
                recovered = int(cursor.rowcount)
                connection.commit()
                return recovered
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()

    def get_all_events(self) -> list[CareEvent]:
        with self._connection() as connection:
            schema = self._detect_schema(connection)
            cursor = connection.cursor()
            try:
                table = schema.event_table
                cursor.execute(
                    f"""
                    SELECT event_id, persona_id, event_type, content, event_time,
                           confidence, created_at, COALESCE(created_by_id, ''),
                           source_text
                      FROM `{table}`
                     WHERE deleted_at IS NULL
                     ORDER BY created_at ASC
                    """
                )
                events: list[CareEvent] = []
                for row in cursor.fetchall():
                    effective_event_time = row[4] or row[6]
                    events.append(
                        CareEvent(
                            record_id=str(row[0]),
                            persona_id=str(row[1]),
                            event_type=str(row[2]),
                            content=str(row[3]),
                            event_time=_from_utc_naive(effective_event_time),
                            confidence=float(row[5]) if row[5] is not None else None,
                            created_at=_from_utc_naive(row[6]),
                            created_by=str(row[7]),
                            source_text=row[8],
                            idempotency_key=None,
                        )
                    )
                return events
            finally:
                cursor.close()

    def get_all_reminders(self) -> list[Reminder]:
        with self._connection() as connection:
            schema = self._detect_schema(connection)
            cursor = connection.cursor()
            try:
                idempotency_select = (
                    "idempotency_key" if "idempotency_key" in schema.reminder_columns else "NULL"
                )
                cursor.execute(
                    f"""
                    SELECT reminder_id, persona_id, title, description,
                           scheduled_at, importance, created_at, {idempotency_select},
                           reminder_status, triggered_at
                      FROM reminders
                     ORDER BY created_at ASC
                    """
                )
                return [
                    Reminder(
                        record_id=str(row[0]),
                        persona_id=str(row[1]),
                        title=str(row[2]),
                        description=row[3],
                        scheduled_at=_from_utc_naive(row[4]),
                        importance=str(row[5]),
                        created_at=_from_utc_naive(row[6]),
                        created_by="",
                        idempotency_key=row[7],
                        status=str(row[8]),
                        triggered_at=(
                            _from_utc_naive(row[9]) if row[9] is not None else None
                        ),
                    )
                    for row in cursor.fetchall()
                ]
            finally:
                cursor.close()
