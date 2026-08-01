"""Prepare the teammate MySQL schema for Agent + Skill integration.

Actions are idempotent:
1. Verify required v2 tables/columns.
2. Add care_events.idempotency_key when absent.
3. Create/update demo organization, user, persona, relationship and access rows.

Run only against a development/demo database.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

from app.config import settings
from app.repositories.mysql import MySQLCareRepository

REQUIRED_COLUMNS = {
    "organizations": {"organization_id", "name", "organization_type"},
    "personas": {"persona_id", "primary_organization_id", "memory_namespace"},
    "app_users": {"user_id", "username", "account_type"},
    "organization_personas": {"organization_id", "persona_id", "status"},
    "user_persona_access": {
        "organization_id",
        "user_id",
        "persona_id",
        "can_create_event",
        "can_manage_reminder",
    },
    "care_events": {"event_id", "organization_id", "persona_id", "event_type"},
    "reminders": {"reminder_id", "organization_id", "persona_id", "scheduled_at"},
}


def _column_names(cursor, database: str, table: str) -> set[str]:
    cursor.execute(
        """
        SELECT COLUMN_NAME
          FROM INFORMATION_SCHEMA.COLUMNS
         WHERE TABLE_SCHEMA = %s
           AND TABLE_NAME = %s
        """,
        (database, table),
    )
    return {str(row[0]) for row in cursor.fetchall()}


def main() -> int:
    if not settings.DATABASE_URL:
        print("[FAIL] DATABASE_URL is not configured", file=sys.stderr)
        return 2

    repo = MySQLCareRepository(settings.DATABASE_URL)
    database = repo._connection_kwargs["database"]  # local setup script only
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    organization_id = "demo-organization"

    with repo._connection() as connection:  # local setup script only
        cursor = connection.cursor()
        try:
            for table, required in REQUIRED_COLUMNS.items():
                actual = _column_names(cursor, database, table)
                missing = required - actual
                if missing:
                    print(
                        f"[FAIL] {table} is missing columns: {sorted(missing)}\n"
                        "Run `npx prisma db push` with the included prisma/schema.prisma first.",
                        file=sys.stderr,
                    )
                    connection.rollback()
                    return 3

            event_columns = _column_names(cursor, database, "care_events")
            if "idempotency_key" not in event_columns:
                cursor.execute(
                    "ALTER TABLE care_events ADD COLUMN idempotency_key VARCHAR(191) NULL"
                )
                cursor.execute(
                    "CREATE UNIQUE INDEX care_events_idempotency_key_key "
                    "ON care_events(idempotency_key)"
                )
                print("[OK] Added care_events.idempotency_key")
            else:
                print("[OK] care_events.idempotency_key already exists")

            cursor.execute(
                """
                INSERT INTO organizations (
                    organization_id, name, organization_type, status, timezone,
                    created_at, updated_at
                ) VALUES (%s, %s, 'COMMUNITY_SERVICE', 'active', 'Asia/Taipei', %s, %s)
                ON DUPLICATE KEY UPDATE name = VALUES(name), updated_at = VALUES(updated_at)
                """,
                (organization_id, "智慧長照 Demo 機構", now, now),
            )

            cursor.execute(
                """
                INSERT INTO personas (
                    persona_id, primary_organization_id, display_name,
                    memory_namespace, preferred_language, timezone, status,
                    created_at, updated_at
                ) VALUES (%s, %s, %s, %s, 'zh-TW', 'Asia/Taipei', 'ACTIVE', %s, %s)
                ON DUPLICATE KEY UPDATE
                    primary_organization_id = VALUES(primary_organization_id),
                    display_name = VALUES(display_name),
                    updated_at = VALUES(updated_at)
                """,
                (
                    settings.DEMO_PERSONA_ID,
                    organization_id,
                    "Demo 長者",
                    f"persona:{settings.DEMO_PERSONA_ID}",
                    now,
                    now,
                ),
            )

            cursor.execute(
                """
                INSERT INTO app_users (
                    user_id, username, password_hash, display_name, account_type,
                    is_active, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, 'ELDER', TRUE, %s, %s)
                ON DUPLICATE KEY UPDATE
                    display_name = VALUES(display_name),
                    is_active = TRUE,
                    updated_at = VALUES(updated_at)
                """,
                (
                    settings.DEMO_USER_ID,
                    settings.DEMO_USER_ID,
                    "DEMO_ONLY_NO_LOGIN",
                    "Demo 使用者",
                    now,
                    now,
                ),
            )

            cursor.execute(
                """
                INSERT INTO organization_personas (
                    relationship_id, organization_id, persona_id,
                    relationship_type, status, created_at, updated_at
                ) VALUES (UUID(), %s, %s, 'primary_care', 'active', %s, %s)
                ON DUPLICATE KEY UPDATE status = 'active', updated_at = VALUES(updated_at)
                """,
                (organization_id, settings.DEMO_PERSONA_ID, now, now),
            )

            cursor.execute(
                """
                INSERT INTO user_persona_access (
                    access_id, organization_id, user_id, persona_id,
                    can_read_profile, can_read_health, can_read_medication,
                    can_read_conversation, can_create_event, can_update_event,
                    can_manage_reminder, can_acknowledge_alert,
                    can_approve_ai_action, created_at, updated_at
                ) VALUES (
                    UUID(), %s, %s, %s,
                    TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, FALSE, TRUE, %s, %s
                )
                ON DUPLICATE KEY UPDATE
                    can_create_event = TRUE,
                    can_manage_reminder = TRUE,
                    revoked_at = NULL,
                    updated_at = VALUES(updated_at)
                """,
                (
                    organization_id,
                    settings.DEMO_USER_ID,
                    settings.DEMO_PERSONA_ID,
                    now,
                    now,
                ),
            )

            connection.commit()
            print(f"[OK] Demo user: {settings.DEMO_USER_ID}")
            print(f"[OK] Demo persona: {settings.DEMO_PERSONA_ID}")
            print("[OK] Agent + Skill database prerequisites are ready")
            return 0
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()


if __name__ == "__main__":
    raise SystemExit(main())
