"""MySQL persistence adapter for the teammate database schema.

The live schema uses these tables:
- personas
- app_users
- user_persona_access
- events
- reminders

Only ToolHandlers call this repository after Tool Gateway validation and
authorization. SQL is parameterized and never exposed to Claude.
"""

from __future__ import annotations

import logging
import uuid
from contextlib import contextmanager
from datetime import date, datetime, time, timezone
from typing import Any, Iterator
from urllib.parse import unquote, urlparse
from zoneinfo import ZoneInfo

import mysql.connector
from mysql.connector import Error as MySQLError
from mysql.connector.connection import MySQLConnection

from app.repositories.base import CareEvent, Reminder, ScheduleItem

logger = logging.getLogger(__name__)
TAIPEI_TZ = ZoneInfo("Asia/Taipei")
UTC = timezone.utc


class RepositoryConfigurationError(RuntimeError):
    """Raised when DATABASE_URL cannot be used safely."""


class RepositoryDataError(RuntimeError):
    """Raised when required persona/user data is absent or inconsistent."""


def parse_mysql_database_url(database_url: str) -> dict[str, Any]:
    """Parse a mysql:// URL into mysql-connector keyword arguments."""

    parsed = urlparse(database_url)
    if parsed.scheme not in {"mysql", "mysql+mysqlconnector"}:
        raise RepositoryConfigurationError(
            "DATABASE_URL must use mysql:// or mysql+mysqlconnector://"
        )
    if not parsed.hostname or not parsed.path or parsed.path == "/":
        raise RepositoryConfigurationError("DATABASE_URL must include host and database")

    return {
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


def _to_utc_naive(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("datetime must include timezone information")
    return value.astimezone(UTC).replace(tzinfo=None)


def _from_utc_naive(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(TAIPEI_TZ)


class MySQLCareRepository:
    """Persistent repository mapped to the live teammate schema."""

    def __init__(self, database_url: str) -> None:
        self._connection_kwargs = parse_mysql_database_url(database_url)

    @contextmanager
    def _connection(self) -> Iterator[MySQLConnection]:
        connection: MySQLConnection | None = None
        try:
            connection = mysql.connector.connect(**self._connection_kwargs)
            yield connection
        except MySQLError:
            if connection is not None and connection.is_connected():
                connection.rollback()
            raise
        finally:
            if connection is not None and connection.is_connected():
                connection.close()

    def ping(self) -> bool:
        with self._connection() as connection:
            connection.ping(reconnect=False, attempts=1, delay=0)
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
        # The live `events` table has no idempotency_key column. Duplicate
        # suppression remains enforced by ToolGateway's idempotency store.
        del idempotency_key

        event_id = str(uuid.uuid4())
        event_time_utc = _to_utc_naive(event_time)
        now_utc = datetime.now(UTC).replace(tzinfo=None)

        with self._connection() as connection:
            cursor = connection.cursor()
            try:
                self._ensure_active_persona(cursor, persona_id)
                existing_user_id = self._existing_user_id(cursor, created_by)
                actor_type = "user" if existing_user_id else "agent"

                cursor.execute(
                    """
                    INSERT INTO events (
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
            cursor = connection.cursor()
            try:
                self._ensure_active_persona(cursor, persona_id)

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

                # Validate requester identity even though the live reminders
                # table does not currently store created_by_id.
                self._existing_user_id(cursor, created_by)

                cursor.execute(
                    """
                    INSERT INTO reminders (
                        reminder_id,
                        persona_id,
                        title,
                        description,
                        scheduled_at,
                        importance,
                        risk_level,
                        reminder_status,
                        confirmation_status,
                        idempotency_key,
                        confirmed_at,
                        created_at,
                        updated_at
                    ) VALUES (
                        %s, %s, %s, NULL, %s, %s, 'low',
                        'scheduled', %s, %s, %s, %s, %s
                    )
                    """,
                    (
                        reminder_id,
                        persona_id,
                        title,
                        scheduled_at_utc,
                        normalized_importance,
                        confirmation_status,
                        effective_key,
                        confirmed_at,
                        now_utc,
                        now_utc,
                    ),
                )
                connection.commit()
                return reminder_id
            except MySQLError as exc:
                connection.rollback()
                if getattr(exc, "errno", None) == 1062:
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
            cursor = connection.cursor()
            try:
                self._ensure_active_persona(cursor, persona_id)
                cursor.execute(
                    """
                    SELECT reminder_id, title, scheduled_at
                      FROM reminders
                     WHERE persona_id = %s
                       AND reminder_status IN ('scheduled', 'SCHEDULED')
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

    def get_all_events(self) -> list[CareEvent]:
        with self._connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    """
                    SELECT event_id, persona_id, event_type, content, event_time,
                           confidence, created_at, COALESCE(created_by_id, ''),
                           source_text
                      FROM events
                     WHERE deleted_at IS NULL
                     ORDER BY created_at ASC
                    """
                )
                return [
                    CareEvent(
                        record_id=str(row[0]),
                        persona_id=str(row[1]),
                        event_type=str(row[2]),
                        content=str(row[3]),
                        event_time=_from_utc_naive(row[4]),
                        confidence=float(row[5]) if row[5] is not None else None,
                        created_at=_from_utc_naive(row[6]),
                        created_by=str(row[7]),
                        source_text=row[8],
                        idempotency_key=None,
                    )
                    for row in cursor.fetchall()
                ]
            finally:
                cursor.close()

    def get_all_reminders(self) -> list[Reminder]:
        with self._connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    """
                    SELECT reminder_id, persona_id, title, scheduled_at, importance,
                           created_at, idempotency_key
                      FROM reminders
                     ORDER BY created_at ASC
                    """
                )
                return [
                    Reminder(
                        record_id=str(row[0]),
                        persona_id=str(row[1]),
                        title=str(row[2]),
                        scheduled_at=_from_utc_naive(row[3]),
                        importance=str(row[4]),
                        created_at=_from_utc_naive(row[5]),
                        created_by="",
                        idempotency_key=row[6],
                    )
                    for row in cursor.fetchall()
                ]
            finally:
                cursor.close()
