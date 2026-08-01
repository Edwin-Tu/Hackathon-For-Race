"""Idempotently seed the cloud RDS with the demo resident identity.

The script never prints DATABASE_URL or passwords. It supports both the local
schema and Edwin's RDS schema because the relevant identity tables share the
same core columns.
"""

from __future__ import annotations

import argparse
import os
import uuid
from datetime import datetime, timezone

from app.repositories.mysql import (
    RepositoryConfigurationError,
    mysql_connector,
    parse_mysql_database_url,
)

UTC = timezone.utc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--display-name", default="王奶奶")
    parser.add_argument("--username", default="resident_wang")
    parser.add_argument("--persona-id", default=os.getenv("DEMO_PERSONA_ID", ""))
    parser.add_argument("--user-id", default=os.getenv("DEMO_USER_ID", ""))
    parser.add_argument("--access-level", default="read", choices=["read", "care", "manage"])
    args = parser.parse_args()

    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        raise SystemExit("DATABASE_URL is required")
    if not args.persona_id or not args.user_id:
        raise SystemExit("DEMO_PERSONA_ID and DEMO_USER_ID are required")
    if mysql_connector is None:
        raise SystemExit("mysql-connector-python is required")

    kwargs = parse_mysql_database_url(
        database_url,
        ssl_mode=os.getenv("DATABASE_SSL_MODE", "preferred"),
        ssl_ca=os.getenv("DATABASE_SSL_CA") or None,
    )
    now = datetime.now(UTC).replace(tzinfo=None)
    access_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{args.user_id}:{args.persona_id}"))
    namespace = f"resident:{args.persona_id}"

    connection = mysql_connector.connect(**kwargs)
    cursor = connection.cursor()
    try:
        connection.start_transaction()
        cursor.execute(
            """
            INSERT INTO personas (
                persona_id, display_name, memory_namespace, preferred_language,
                status, created_at, updated_at, deleted_at
            ) VALUES (%s, %s, %s, 'zh-TW', 'active', %s, %s, NULL)
            ON DUPLICATE KEY UPDATE
                display_name = VALUES(display_name),
                preferred_language = 'zh-TW',
                status = 'active',
                deleted_at = NULL,
                updated_at = VALUES(updated_at)
            """,
            (args.persona_id, args.display_name, namespace, now, now),
        )
        cursor.execute(
            """
            INSERT INTO app_users (
                user_id, username, password_hash, display_name, role,
                persona_id, is_active, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, 'resident', %s, TRUE, %s, %s)
            ON DUPLICATE KEY UPDATE
                display_name = VALUES(display_name),
                role = 'resident',
                persona_id = VALUES(persona_id),
                is_active = TRUE,
                updated_at = VALUES(updated_at)
            """,
            (
                args.user_id,
                args.username,
                "DISABLED_CLOUD_DEMO_NO_PASSWORD_LOGIN",
                args.display_name,
                args.persona_id,
                now,
                now,
            ),
        )
        cursor.execute(
            """
            INSERT INTO user_persona_access (
                access_id, user_id, persona_id, access_level, created_at
            ) VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                access_level = VALUES(access_level)
            """,
            (access_id, args.user_id, args.persona_id, args.access_level, now),
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()

    print("Cloud demo identity is ready.")
    print(f"persona_id={args.persona_id}")
    print(f"user_id={args.user_id}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RepositoryConfigurationError as exc:
        raise SystemExit(str(exc)) from exc
