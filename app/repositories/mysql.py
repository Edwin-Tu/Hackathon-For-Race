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
import json
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

from app.repositories.base import (
    CareEvent,
    ConversationMessage,
    PendingToolConfirmation,
    Reminder,
    ScheduleItem,
    SessionScopeError,
)

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


@dataclass(frozen=True)
class ConversationSchemaCapabilities:
    """Detected columns used for durable session-scoped conversation history."""

    session_columns: frozenset[str]
    interaction_columns: frozenset[str]
    persona_columns: frozenset[str]
    access_columns: frozenset[str]
    organization_persona_columns: frozenset[str]
    organization_columns: frozenset[str]


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
        self._conversation_schema: ConversationSchemaCapabilities | None = None
        self._conversation_schema_lock = threading.Lock()

    def _get_table_columns(
        self,
        connection: MySQLConnection,
        *table_names: str,
    ) -> dict[str, frozenset[str]]:
        """Return columns for a fixed internal table allowlist."""
        allowed = {
            "confirmation_requests",
            "tool_executions",
            "audit_logs",
        }
        if not table_names or any(name not in allowed for name in table_names):
            raise RepositoryConfigurationError("Unsupported internal table lookup")
        placeholders = ", ".join(["%s"] * len(table_names))
        cursor = connection.cursor()
        try:
            cursor.execute(
                f"""
                SELECT table_name, column_name
                  FROM information_schema.columns
                 WHERE table_schema = %s
                   AND table_name IN ({placeholders})
                """,
                (self._connection_kwargs["database"], *table_names),
            )
            columns: dict[str, set[str]] = {name: set() for name in table_names}
            for table_name, column_name in cursor.fetchall():
                columns[str(table_name)].add(str(column_name))
            return {name: frozenset(values) for name, values in columns.items()}
        finally:
            cursor.close()

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
                if idempotency_key and "idempotency_key" in schema.event_columns:
                    cursor.execute(
                        f"SELECT event_id FROM `{table}` WHERE idempotency_key = %s LIMIT 1",
                        (idempotency_key,),
                    )
                    existing = cursor.fetchone()
                    if existing:
                        connection.rollback()
                        return str(existing[0])

                columns = [
                    "event_id",
                    "persona_id",
                    "event_type",
                    "content",
                    "event_time",
                    "confidence",
                    "source_text",
                    "memory_status",
                    "risk_level",
                    "created_by_type",
                    "created_by_id",
                    "committed_at",
                    "created_at",
                    "updated_at",
                ]
                values: list[Any] = [
                    event_id,
                    persona_id,
                    event_type,
                    content,
                    event_time_utc,
                    confidence,
                    source_text,
                    "committed",
                    "low",
                    actor_type,
                    existing_user_id,
                    now_utc,
                    now_utc,
                    now_utc,
                ]
                if idempotency_key and "idempotency_key" in schema.event_columns:
                    columns.append("idempotency_key")
                    values.append(idempotency_key)

                column_sql = ", ".join(f"`{column}`" for column in columns)
                placeholders = ", ".join(["%s"] * len(columns))
                cursor.execute(
                    f"INSERT INTO `{table}` ({column_sql}) VALUES ({placeholders})",
                    tuple(values),
                )
                connection.commit()
                return event_id
            except MySQLError as exc:
                connection.rollback()
                if (
                    idempotency_key
                    and getattr(exc, "errno", None) == 1062
                    and "idempotency_key" in schema.event_columns
                ):
                    cursor.execute(
                        f"SELECT event_id FROM `{table}` WHERE idempotency_key = %s LIMIT 1",
                        (idempotency_key,),
                    )
                    existing = cursor.fetchone()
                    if existing:
                        return str(existing[0])
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

    def _detect_conversation_schema(
        self,
        connection: MySQLConnection,
    ) -> ConversationSchemaCapabilities:
        if self._conversation_schema is not None:
            return self._conversation_schema

        with self._conversation_schema_lock:
            if self._conversation_schema is not None:
                return self._conversation_schema

            cursor = connection.cursor()
            try:
                cursor.execute(
                    """
                    SELECT table_name, column_name
                      FROM information_schema.columns
                     WHERE table_schema = %s
                       AND table_name IN (
                           'sessions', 'interactions', 'personas',
                           'user_persona_access', 'organization_personas',
                           'organizations'
                       )
                    """,
                    (self._connection_kwargs["database"],),
                )
                columns: dict[str, set[str]] = {}
                for table_name, column_name in cursor.fetchall():
                    columns.setdefault(str(table_name), set()).add(str(column_name))
            finally:
                cursor.close()

            required_session = {
                "session_id", "persona_id", "client_type",
                "started_at", "last_active_at",
            }
            required_interaction = {
                "interaction_id", "request_id", "session_id", "persona_id",
                "input_type", "transcript", "agent_response", "started_at",
            }
            missing_session = required_session - columns.get("sessions", set())
            missing_interaction = required_interaction - columns.get("interactions", set())
            if missing_session:
                raise RepositoryConfigurationError(
                    "sessions table is missing conversation columns: "
                    + ", ".join(sorted(missing_session))
                )
            if missing_interaction:
                raise RepositoryConfigurationError(
                    "interactions table is missing conversation columns: "
                    + ", ".join(sorted(missing_interaction))
                )

            self._conversation_schema = ConversationSchemaCapabilities(
                session_columns=frozenset(columns.get("sessions", set())),
                interaction_columns=frozenset(columns.get("interactions", set())),
                persona_columns=frozenset(columns.get("personas", set())),
                access_columns=frozenset(columns.get("user_persona_access", set())),
                organization_persona_columns=frozenset(
                    columns.get("organization_personas", set())
                ),
                organization_columns=frozenset(columns.get("organizations", set())),
            )
            return self._conversation_schema

    @staticmethod
    def _validate_session_scope_row(
        row: tuple[Any, ...],
        *,
        session_id: str,
        user_id: str,
        persona_id: str,
    ) -> None:
        existing_persona = str(row[0]) if row[0] is not None else ""
        existing_user = str(row[1]) if len(row) > 1 and row[1] is not None else ""
        if existing_persona and existing_persona != persona_id:
            raise SessionScopeError(
                f"session_id {session_id} belongs to a different persona"
            )
        if existing_user and existing_user != user_id:
            raise SessionScopeError(
                f"session_id {session_id} belongs to a different user"
            )

    def _ensure_conversation_session_with_cursor(
        self,
        cursor: Any,
        schema: ConversationSchemaCapabilities,
        *,
        session_id: str,
        user_id: str,
        persona_id: str,
        now_utc: datetime,
    ) -> None:
        self._ensure_active_persona(cursor, persona_id)
        if self._existing_user_id(cursor, user_id) is None:
            raise RepositoryDataError(f"Unknown or inactive user_id: {user_id}")

        client_select = (
            "client_identifier"
            if "client_identifier" in schema.session_columns
            else "NULL"
        )
        cursor.execute(
            f"""
            SELECT persona_id, {client_select}
              FROM sessions
             WHERE session_id = %s
             LIMIT 1
            """,
            (session_id,),
        )
        existing = cursor.fetchone()
        if existing is not None:
            self._validate_session_scope_row(
                existing,
                session_id=session_id,
                user_id=user_id,
                persona_id=persona_id,
            )
            assignments = ["last_active_at = %s"]
            params: list[Any] = [now_utc]
            if "client_identifier" in schema.session_columns and not existing[1]:
                assignments.append("client_identifier = %s")
                params.append(user_id)
            params.append(session_id)
            cursor.execute(
                f"UPDATE sessions SET {', '.join(assignments)} WHERE session_id = %s",
                tuple(params),
            )
            return

        columns = ["session_id", "persona_id", "client_type", "started_at", "last_active_at"]
        values: list[Any] = [session_id, persona_id, "voice_agent", now_utc, now_utc]
        if "client_identifier" in schema.session_columns:
            columns.insert(3, "client_identifier")
            values.insert(3, user_id)
        placeholders = ", ".join(["%s"] * len(columns))
        cursor.execute(
            f"INSERT INTO sessions ({', '.join(columns)}) VALUES ({placeholders})",
            tuple(values),
        )

    def ensure_conversation_session(
        self,
        *,
        session_id: str,
        user_id: str,
        persona_id: str,
    ) -> None:
        now_utc = datetime.now(UTC).replace(tzinfo=None)
        with self._connection() as connection:
            schema = self._detect_conversation_schema(connection)
            cursor = connection.cursor()
            try:
                self._ensure_conversation_session_with_cursor(
                    cursor,
                    schema,
                    session_id=session_id,
                    user_id=user_id,
                    persona_id=persona_id,
                    now_utc=now_utc,
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()

    def _resolve_organization_id(
        self,
        cursor: Any,
        schema: ConversationSchemaCapabilities,
        *,
        user_id: str,
        persona_id: str,
    ) -> str:
        if "primary_organization_id" in schema.persona_columns:
            cursor.execute(
                "SELECT primary_organization_id FROM personas WHERE persona_id = %s",
                (persona_id,),
            )
            row = cursor.fetchone()
            if row and row[0]:
                return str(row[0])

        if {"organization_id", "user_id", "persona_id"}.issubset(
            schema.access_columns
        ):
            cursor.execute(
                """
                SELECT organization_id
                  FROM user_persona_access
                 WHERE user_id = %s AND persona_id = %s
                   AND (revoked_at IS NULL OR %s = 0)
                 LIMIT 1
                """
                if "revoked_at" in schema.access_columns
                else """
                SELECT organization_id
                  FROM user_persona_access
                 WHERE user_id = %s AND persona_id = %s
                 LIMIT 1
                """,
                (user_id, persona_id, 1)
                if "revoked_at" in schema.access_columns
                else (user_id, persona_id),
            )
            row = cursor.fetchone()
            if row and row[0]:
                return str(row[0])

        if {"organization_id", "persona_id"}.issubset(
            schema.organization_persona_columns
        ):
            cursor.execute(
                """
                SELECT organization_id
                  FROM organization_personas
                 WHERE persona_id = %s
                 LIMIT 1
                """,
                (persona_id,),
            )
            row = cursor.fetchone()
            if row and row[0]:
                return str(row[0])

        if "organization_id" in schema.organization_columns:
            cursor.execute("SELECT organization_id FROM organizations LIMIT 2")
            rows = cursor.fetchall()
            if len(rows) == 1 and rows[0][0]:
                return str(rows[0][0])

        raise RepositoryDataError(
            "Cannot resolve organization_id for conversation interaction"
        )

    def append_conversation_turn(
        self,
        *,
        session_id: str,
        user_id: str,
        persona_id: str,
        request_id: str,
        user_message: str,
        assistant_message: str,
        input_type: str = "text",
    ) -> None:
        now_utc = datetime.now(UTC).replace(tzinfo=None)
        with self._connection() as connection:
            schema = self._detect_conversation_schema(connection)
            cursor = connection.cursor()
            try:
                self._ensure_conversation_session_with_cursor(
                    cursor,
                    schema,
                    session_id=session_id,
                    user_id=user_id,
                    persona_id=persona_id,
                    now_utc=now_utc,
                )
                columns = [
                    "interaction_id", "request_id", "session_id", "persona_id",
                    "input_type", "transcript", "agent_response", "started_at",
                ]
                values: list[Any] = [
                    str(uuid.uuid4()), request_id, session_id, persona_id,
                    input_type, user_message.strip(), assistant_message.strip(), now_utc,
                ]
                if "normalized_text" in schema.interaction_columns:
                    columns.append("normalized_text")
                    values.append(user_message.strip())
                if "actor_user_id" in schema.interaction_columns:
                    columns.append("actor_user_id")
                    values.append(user_id)
                if "organization_id" in schema.interaction_columns:
                    columns.append("organization_id")
                    values.append(self._resolve_organization_id(
                        cursor,
                        schema,
                        user_id=user_id,
                        persona_id=persona_id,
                    ))
                if "completed_at" in schema.interaction_columns:
                    columns.append("completed_at")
                    values.append(now_utc)

                placeholders = ", ".join(["%s"] * len(columns))
                cursor.execute(
                    f"INSERT INTO interactions ({', '.join(columns)}) VALUES ({placeholders})",
                    tuple(values),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()

    def list_recent_conversation_messages(
        self,
        *,
        session_id: str,
        user_id: str,
        persona_id: str,
        max_messages: int,
        max_chars: int,
    ) -> list[ConversationMessage]:
        now_utc = datetime.now(UTC).replace(tzinfo=None)
        row_limit = max(1, (max_messages + 1) // 2 + 1)
        with self._connection() as connection:
            schema = self._detect_conversation_schema(connection)
            cursor = connection.cursor()
            try:
                self._ensure_conversation_session_with_cursor(
                    cursor,
                    schema,
                    session_id=session_id,
                    user_id=user_id,
                    persona_id=persona_id,
                    now_utc=now_utc,
                )
                cursor.execute(
                    """
                    SELECT transcript, agent_response, started_at
                      FROM interactions
                     WHERE session_id = %s
                       AND persona_id = %s
                     ORDER BY started_at DESC
                     LIMIT %s
                    """,
                    (session_id, persona_id, row_limit),
                )
                rows = list(reversed(cursor.fetchall()))
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()

        messages: list[ConversationMessage] = []
        for transcript, agent_response, started_at in rows:
            created_at = _from_utc_naive(started_at)
            if transcript and str(transcript).strip():
                messages.append(ConversationMessage(
                    role="user",
                    content=str(transcript).strip(),
                    created_at=created_at,
                ))
            if agent_response and str(agent_response).strip():
                messages.append(ConversationMessage(
                    role="assistant",
                    content=str(agent_response).strip(),
                    created_at=created_at,
                ))

        selected: list[ConversationMessage] = []
        chars = 0
        for message in reversed(messages):
            if len(selected) >= max(0, max_messages):
                break
            size = len(message.content)
            if selected and chars + size > max_chars:
                break
            if not selected and size > max_chars:
                message = ConversationMessage(
                    role=message.role,
                    content=message.content[-max_chars:],
                    created_at=message.created_at,
                )
                size = len(message.content)
            selected.append(message)
            chars += size
        return list(reversed(selected))

    @staticmethod
    def _decode_json_object(value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return dict(value)
        if isinstance(value, (bytes, bytearray)):
            value = value.decode("utf-8")
        if isinstance(value, str) and value:
            try:
                decoded = json.loads(value)
            except (json.JSONDecodeError, TypeError, ValueError):
                return {}
            if isinstance(decoded, dict):
                return decoded
        return {}

    @staticmethod
    def _confirmation_from_row(row: tuple[Any, ...]) -> PendingToolConfirmation:
        arguments = MySQLCareRepository._decode_json_object(row[5])
        payload = MySQLCareRepository._decode_json_object(row[6])
        created_at = row[8]
        expires_at = row[9]
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=UTC)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        return PendingToolConfirmation(
            token_hash=str(row[0]),
            request_id=str(row[1]),
            session_id=str(row[2]),
            requester_id=str(payload.get("requester_id", "")),
            role=str(payload.get("role", "")),
            tool_call_id=str(payload.get("tool_call_id", row[4])),
            tool_name=str(row[4]),
            arguments=arguments,
            target_persona_id=(
                str(payload["target_persona_id"])
                if payload.get("target_persona_id") is not None
                else (str(row[3]) if row[3] is not None else None)
            ),
            arguments_hash=str(payload.get("arguments_hash", "")),
            summary=str(row[7]),
            created_at=created_at,
            expires_at=expires_at,
            consumed=str(row[10]).lower() != "pending",
        )

    def create_pending_confirmation(
        self,
        confirmation: PendingToolConfirmation,
    ) -> None:
        """Persist a pending ToolCall without storing the raw confirmation token."""
        now_utc = datetime.now(UTC).replace(tzinfo=None)
        expires_utc = _to_utc_naive(confirmation.expires_at)
        tool_execution_id = str(uuid.uuid4())

        with self._connection() as connection:
            table_columns = self._get_table_columns(
                connection,
                "confirmation_requests",
                "tool_executions",
            )
            confirmation_columns = table_columns["confirmation_requests"]
            execution_columns = table_columns["tool_executions"]
            required_confirmation = {
                "confirmation_id",
                "session_id",
                "target_type",
                "target_id",
                "confirmation_question",
                "confirmation_status",
                "expires_at",
                "created_at",
                "updated_at",
            }
            required_execution = {
                "tool_execution_id",
                "request_id",
                "session_id",
                "persona_id",
                "tool_name",
                "tool_arguments",
                "tool_status",
                "result_payload",
                "started_at",
            }
            if missing := required_confirmation - confirmation_columns:
                raise RepositoryConfigurationError(
                    "confirmation_requests is missing columns: "
                    + ", ".join(sorted(missing))
                )
            if missing := required_execution - execution_columns:
                raise RepositoryConfigurationError(
                    "tool_executions is missing columns: "
                    + ", ".join(sorted(missing))
                )

            conversation_schema = self._detect_conversation_schema(connection)
            cursor = connection.cursor()
            try:
                self._ensure_conversation_session_with_cursor(
                    cursor,
                    conversation_schema,
                    session_id=confirmation.session_id,
                    user_id=confirmation.requester_id,
                    persona_id=confirmation.target_persona_id or "",
                    now_utc=now_utc,
                )
                organization_id: str | None = None
                if (
                    "organization_id" in execution_columns
                    or "organization_id" in confirmation_columns
                ):
                    organization_id = self._resolve_organization_id(
                        cursor,
                        conversation_schema,
                        user_id=confirmation.requester_id,
                        persona_id=confirmation.target_persona_id or "",
                    )

                # A trusted session has at most one active pending action.
                assignments = ["confirmation_status = 'rejected'"]
                if "response_text" in confirmation_columns:
                    assignments.append("response_text = 'superseded'")
                if "updated_at" in confirmation_columns:
                    assignments.append("updated_at = %s")
                    replace_params: list[Any] = [now_utc, confirmation.session_id]
                else:
                    replace_params = [confirmation.session_id]
                cursor.execute(
                    f"""
                    UPDATE confirmation_requests
                       SET {', '.join(assignments)}
                     WHERE session_id = %s
                       AND LOWER(confirmation_status) = 'pending'
                    """,
                    tuple(replace_params),
                )

                execution_payload = {
                    "requester_id": confirmation.requester_id,
                    "role": confirmation.role,
                    "tool_call_id": confirmation.tool_call_id,
                    "target_persona_id": confirmation.target_persona_id,
                    "arguments_hash": confirmation.arguments_hash,
                    "summary": confirmation.summary[:190],
                }
                execution_insert_columns = [
                    "tool_execution_id",
                    "request_id",
                    "session_id",
                    "persona_id",
                    "tool_name",
                    "tool_arguments",
                    "tool_status",
                    "result_payload",
                    "started_at",
                ]
                execution_values: list[Any] = [
                    tool_execution_id,
                    confirmation.request_id,
                    confirmation.session_id,
                    confirmation.target_persona_id,
                    confirmation.tool_name,
                    json.dumps(confirmation.arguments, ensure_ascii=False, default=str),
                    "awaiting_confirmation",
                    json.dumps(execution_payload, ensure_ascii=False),
                    now_utc,
                ]
                if "organization_id" in execution_columns:
                    execution_insert_columns.append("organization_id")
                    execution_values.append(organization_id)
                if "risk_level" in execution_columns:
                    execution_insert_columns.append("risk_level")
                    execution_values.append("medium")
                execution_sql_columns = ", ".join(
                    f"`{column}`" for column in execution_insert_columns
                )
                cursor.execute(
                    f"INSERT INTO tool_executions ({execution_sql_columns}) "
                    f"VALUES ({', '.join(['%s'] * len(execution_values))})",
                    tuple(execution_values),
                )

                confirmation_insert_columns = [
                    "confirmation_id",
                    "session_id",
                    "target_type",
                    "target_id",
                    "confirmation_question",
                    "confirmation_status",
                    "expires_at",
                    "created_at",
                    "updated_at",
                ]
                confirmation_values: list[Any] = [
                    confirmation.token_hash,
                    confirmation.session_id,
                    "tool_execution",
                    tool_execution_id,
                    confirmation.summary[:190],
                    "pending",
                    expires_utc,
                    now_utc,
                    now_utc,
                ]
                if "organization_id" in confirmation_columns:
                    confirmation_insert_columns.append("organization_id")
                    confirmation_values.append(organization_id)
                if "persona_id" in confirmation_columns:
                    confirmation_insert_columns.append("persona_id")
                    confirmation_values.append(confirmation.target_persona_id)
                confirmation_sql_columns = ", ".join(
                    f"`{column}`" for column in confirmation_insert_columns
                )
                cursor.execute(
                    f"INSERT INTO confirmation_requests ({confirmation_sql_columns}) "
                    f"VALUES ({', '.join(['%s'] * len(confirmation_values))})",
                    tuple(confirmation_values),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()

    def _select_pending_confirmation_rows(
        self,
        cursor: Any,
        *,
        where_sql: str,
        params: tuple[Any, ...],
    ) -> list[tuple[Any, ...]]:
        cursor.execute(
            f"""
            SELECT c.confirmation_id,
                   t.request_id,
                   c.session_id,
                   t.persona_id,
                   t.tool_name,
                   t.tool_arguments,
                   t.result_payload,
                   c.confirmation_question,
                   c.created_at,
                   c.expires_at,
                   c.confirmation_status
              FROM confirmation_requests c
              JOIN tool_executions t ON t.tool_execution_id = c.target_id
             WHERE c.target_type = 'tool_execution'
               AND {where_sql}
             ORDER BY c.created_at DESC
            """,
            params,
        )
        return list(cursor.fetchall())

    def get_pending_confirmation(
        self,
        *,
        token_hash: str,
    ) -> PendingToolConfirmation | None:
        with self._connection() as connection:
            cursor = connection.cursor()
            try:
                rows = self._select_pending_confirmation_rows(
                    cursor,
                    where_sql="c.confirmation_id = %s",
                    params=(token_hash,),
                )
                return self._confirmation_from_row(rows[0]) if rows else None
            finally:
                cursor.close()

    def get_pending_confirmation_for_context(
        self,
        *,
        session_id: str,
        requester_id: str,
        role: str,
    ) -> list[PendingToolConfirmation]:
        with self._connection() as connection:
            cursor = connection.cursor()
            try:
                rows = self._select_pending_confirmation_rows(
                    cursor,
                    where_sql=(
                        "c.session_id = %s "
                        "AND LOWER(c.confirmation_status) = 'pending'"
                    ),
                    params=(session_id,),
                )
                return [
                    item
                    for item in (self._confirmation_from_row(row) for row in rows)
                    if item.requester_id == requester_id and item.role == role
                ]
            finally:
                cursor.close()

    def consume_pending_confirmation(
        self,
        *,
        token_hash: str,
        response_text: str,
    ) -> bool:
        normalized = response_text.strip().lower()
        status = {
            "confirmed": "approved",
            "cancelled": "rejected",
            "expired": "expired",
            "integrity_failed": "rejected",
        }.get(normalized, "rejected")
        now_utc = datetime.now(UTC).replace(tzinfo=None)
        with self._connection() as connection:
            columns = self._get_table_columns(
                connection,
                "confirmation_requests",
            )["confirmation_requests"]
            assignments = ["confirmation_status = %s"]
            values: list[Any] = [status]
            if "response_text" in columns:
                assignments.append("response_text = %s")
                values.append(normalized)
            if status == "approved" and "confirmed_at" in columns:
                assignments.append("confirmed_at = %s")
                values.append(now_utc)
            if "updated_at" in columns:
                assignments.append("updated_at = %s")
                values.append(now_utc)
            values.append(token_hash)
            cursor = connection.cursor()
            try:
                cursor.execute(
                    f"""
                    UPDATE confirmation_requests
                       SET {', '.join(assignments)}
                     WHERE confirmation_id = %s
                       AND LOWER(confirmation_status) = 'pending'
                    """,
                    tuple(values),
                )
                changed = cursor.rowcount == 1
                connection.commit()
                return changed
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()

    def append_audit_log(
        self,
        *,
        audit_id: str,
        timestamp: datetime,
        request_id: str,
        session_id: str,
        requester_id: str,
        role: str,
        target_persona_id: str | None,
        tool_name: str,
        argument_names: list[str],
        decision: str,
        status: str,
        risk_level: str,
        requires_confirmation: bool,
        error_code: str | None,
        record_id: str | None,
        duration_ms: int | None,
    ) -> None:
        created_at = _to_utc_naive(timestamp)
        with self._connection() as connection:
            columns = self._get_table_columns(connection, "audit_logs")["audit_logs"]
            required = {
                "audit_id",
                "request_id",
                "actor_type",
                "action_type",
                "resource_type",
                "result",
                "created_at",
            }
            if missing := required - columns:
                raise RepositoryConfigurationError(
                    "audit_logs is missing columns: " + ", ".join(sorted(missing))
                )

            metadata = {
                "session_id": session_id,
                "requester_id": requester_id,
                "role": role,
                "argument_names": list(argument_names),
                "decision": decision,
                "status": status,
                "requires_confirmation": requires_confirmation,
                "duration_ms": duration_ms,
            }
            insert_columns = [
                "audit_id",
                "request_id",
                "actor_type",
                "action_type",
                "resource_type",
                "result",
                "created_at",
            ]
            values: list[Any] = [
                audit_id,
                request_id,
                "user",
                f"tool.{decision}",
                "tool",
                status,
                created_at,
            ]
            optional: tuple[tuple[str, Any], ...] = (
                ("persona_id", target_persona_id),
                ("actor_id", requester_id),
                ("resource_id", record_id),
                ("tool_name", tool_name),
                ("risk_level", risk_level),
                ("reason", error_code),
                ("metadata", json.dumps(metadata, ensure_ascii=False)),
            )
            for column, value in optional:
                if column in columns:
                    insert_columns.append(column)
                    values.append(value)

            cursor = connection.cursor()
            try:
                sql_columns = ", ".join(f"`{column}`" for column in insert_columns)
                cursor.execute(
                    f"INSERT INTO audit_logs ({sql_columns}) "
                    f"VALUES ({', '.join(['%s'] * len(values))})",
                    tuple(values),
                )
                connection.commit()
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
