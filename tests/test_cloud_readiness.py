"""Cloud deployment and Edwin RDS compatibility tests."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.config import settings
from app.main import app
from app.repositories.mysql import MySQLCareRepository, parse_mysql_database_url

TZ = ZoneInfo("Asia/Taipei")


class FakeCursor:
    def __init__(self, schema_rows: list[tuple[str, str]]) -> None:
        self.schema_rows = schema_rows
        self.current_rows: list[tuple[Any, ...]] = []
        self.executed: list[tuple[str, tuple[Any, ...] | None]] = []
        self.rowcount = 1

    def execute(self, sql: str, params: tuple[Any, ...] | None = None) -> None:
        self.executed.append((sql, params))
        normalized = " ".join(sql.lower().split())
        if "information_schema.columns" in normalized:
            self.current_rows = list(self.schema_rows)
        elif "from personas" in normalized:
            self.current_rows = [("persona-1",)]
        elif "from app_users" in normalized:
            self.current_rows = [("user-1",)]
        elif "select reminder_id" in normalized:
            self.current_rows = []
        else:
            self.current_rows = []

    def fetchone(self):
        return self.current_rows[0] if self.current_rows else None

    def fetchall(self):
        return list(self.current_rows)

    def close(self) -> None:
        pass


class FakeConnection:
    def __init__(self, cursor: FakeCursor) -> None:
        self._cursor = cursor
        self.commits = 0
        self.rollbacks = 0

    def cursor(self) -> FakeCursor:
        return self._cursor

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1

    def start_transaction(self) -> None:
        pass


@contextmanager
def fake_connection(connection: FakeConnection) -> Iterator[FakeConnection]:
    yield connection


def edwin_schema_rows() -> list[tuple[str, str]]:
    event_columns = {
        "event_id", "persona_id", "session_id", "interaction_id",
        "tool_execution_id", "event_type", "content", "event_time",
        "event_end_time", "confidence", "source_text", "memory_status",
        "risk_level", "created_by_type", "created_by_id", "committed_at",
        "archived_at", "deleted_at", "created_at", "updated_at",
    }
    reminder_columns = {
        "reminder_id", "persona_id", "interaction_id", "title", "description",
        "scheduled_at", "importance", "reminder_status", "confirmation_status",
        "idempotency_key", "triggered_at", "completed_at", "created_at", "updated_at",
    }
    return [*(('care_events', column) for column in event_columns), *(('reminders', column) for column in reminder_columns)]


def test_database_url_verify_identity_configures_rds_tls(tmp_path) -> None:
    ca = tmp_path / "global-bundle.pem"
    ca.write_text("test-ca")
    kwargs = parse_mysql_database_url(
        "mysql://app:CHANGE_ME%40@example.rds.amazonaws.com:3306/smart_care_agent",
        ssl_mode="verify_identity",
        ssl_ca=str(ca),
    )
    assert kwargs["password"] == "CHANGE_ME@"
    assert kwargs["ssl_disabled"] is False
    assert kwargs["ssl_verify_cert"] is True
    assert kwargs["ssl_verify_identity"] is True
    assert kwargs["ssl_ca"] == str(ca)


def test_auto_schema_detects_edwin_care_events() -> None:
    cursor = FakeCursor(edwin_schema_rows())
    connection = FakeConnection(cursor)
    repository = MySQLCareRepository(
        "mysql://app:password@db.example:3306/smart_care_agent",
        care_event_table="auto",
    )
    repository._connection = lambda: fake_connection(connection)  # type: ignore[method-assign]

    repository.ping = lambda: True  # type: ignore[method-assign]
    schema = repository._detect_schema(connection)  # noqa: SLF001 - contract test
    assert schema.event_table == "care_events"
    assert "confirmed_at" not in schema.reminder_columns


def test_edwin_compact_reminder_insert_omits_missing_columns() -> None:
    cursor = FakeCursor(edwin_schema_rows())
    connection = FakeConnection(cursor)
    repository = MySQLCareRepository(
        "mysql://app:password@db.example:3306/smart_care_agent",
        care_event_table="auto",
    )
    repository._connection = lambda: fake_connection(connection)  # type: ignore[method-assign]

    record_id = repository.create_reminder(
        persona_id="persona-1",
        title="回診",
        scheduled_at=datetime(2026, 8, 2, 15, 0, tzinfo=TZ),
        importance="high",
        created_by="user-1",
        idempotency_key="cloud-reminder-1",
    )

    insert_sql = next(sql for sql, _ in cursor.executed if "INSERT INTO reminders" in sql)
    assert record_id
    assert "`idempotency_key`" in insert_sql
    assert "`confirmation_status`" in insert_sql
    assert "`risk_level`" not in insert_sql
    assert "`confirmed_at`" not in insert_sql
    assert connection.commits == 1


def test_api_bearer_protects_api_but_not_health(monkeypatch) -> None:
    monkeypatch.setattr(settings, "API_AUTH_ENABLED", True)
    monkeypatch.setattr(settings, "API_BEARER_TOKEN", SecretStr("cloud-demo-token"))

    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        denied = client.post(
            "/api/security/input-guard/check",
            json={"message": "你好", "session_id": "auth-test"},
        )
        allowed = client.post(
            "/api/security/input-guard/check",
            headers={"Authorization": "Bearer cloud-demo-token"},
            json={"message": "你好", "session_id": "auth-test"},
        )

    assert denied.status_code == 401
    assert allowed.status_code == 200


def test_demo_has_cloud_token_and_browser_speech_controls() -> None:
    with TestClient(app) as client:
        page = client.get("/demo")
        script = client.get("/demo-assets/app.js")

    assert 'id="apiToken"' in page.text
    assert 'id="browserSpeechEnabled"' in page.text
    assert "Authorization" in script.text
    assert "speechSynthesis" in script.text
    assert "reminder.triggered" in script.text
    assert page.headers["x-content-type-options"] == "nosniff"
    assert "frame-ancestors 'none'" in page.headers["content-security-policy"]


def test_ecs_stack_keeps_runtime_private_and_uses_secret_refs() -> None:
    stack = (Path(__file__).resolve().parents[1] / "infra/ecs/stack.yaml").read_text()
    assert "AWS::ECS::Service" in stack
    assert "AWS::ApiGatewayV2::VpcLink" in stack
    assert "AWS::ElasticLoadBalancingV2::LoadBalancer" in stack
    assert "Scheme: internal" in stack
    assert "AssignPublicIp: DISABLED" in stack
    assert "Name: DATABASE_URL" in stack
    assert "ValueFrom: !Ref DatabaseUrlSecretArn" in stack
    assert "Name: API_BEARER_TOKEN" in stack
    assert "ValueFrom: !Ref ApiBearerTokenSecretArn" in stack
    assert "0.0.0.0/0" not in stack


def test_primary_cloud_deploy_targets_ecs_not_apprunner() -> None:
    root = Path(__file__).resolve().parents[1]
    deploy = (root / "scripts/cloud/deploy.sh").read_text()
    legacy = (root / "scripts/cloud/deploy_apprunner.sh").read_text()
    assert "deploy_ecs.sh" in deploy
    assert "deploy_apprunner.sh" not in deploy
    assert "ALLOW_LEGACY_APPRUNNER" in legacy


def test_cloud_preflight_requires_private_route_tables() -> None:
    preflight = (
        Path(__file__).resolve().parents[1] / "scripts/cloud/preflight.py"
    ).read_text()
    assert '"PRIVATE_ROUTE_TABLE_IDS"' in preflight


def test_python_package_discovery_is_explicit_for_container_build() -> None:
    pyproject = (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text()
    assert "[build-system]" in pyproject
    assert '["app*", "secretguard*", "scripts*"]' in pyproject
