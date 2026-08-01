"""Smoke tests for the dependency-free validation UI."""

from fastapi.testclient import TestClient

from app.main import app


def test_demo_page_is_served() -> None:
    with TestClient(app) as client:
        response = client.get("/demo")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "智慧照護語音驗證台" in response.text
    assert "/api/voice/turn" not in response.text  # endpoint logic lives in JS
    assert 'id="startRecordBtn"' in response.text
    assert 'id="toolTableBody"' in response.text
    assert 'id="confirmActionBtn"' in response.text
    assert 'id="cancelActionBtn"' in response.text


def test_demo_assets_are_served_locally() -> None:
    with TestClient(app) as client:
        script = client.get("/demo-assets/app.js")
        stylesheet = client.get("/demo-assets/app.css")

    assert script.status_code == 200
    assert "javascript" in script.headers["content-type"]
    assert 'requestJson("/api/voice/turn"' not in script.text
    assert 'sendVoice("/api/voice/turn")' in script.text
    assert 'requestJson("/api/agent/confirm"' in script.text
    assert 'resolveConfirmation("cancel")' in script.text
    assert "text/css" in stylesheet.headers["content-type"]
    assert ".record-orb" in stylesheet.text


def test_demo_page_does_not_embed_server_secrets() -> None:
    with TestClient(app) as client:
        response = client.get("/demo")

    forbidden = (
        "AWS_SECRET_ACCESS_KEY",
        "DATABASE_URL",
        "confirmation_token",
        "DEMO_PERSONA_ID",
    )
    for value in forbidden:
        assert value not in response.text
