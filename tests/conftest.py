"""Pytest-wide environment isolation.

The developer's local ``.env`` may intentionally select MySQL for manual or cloud
integration work. Unit/API tests must not connect to that database during module
collection, so force the process-local repository before importing ``app.main``.

Dedicated MySQL repository tests instantiate ``MySQLCareRepository`` directly with
fake connections and therefore remain covered without requiring a running server.
"""

from __future__ import annotations

import os


# Environment variables have higher priority than values loaded from .env by
# pydantic-settings. These assignments must execute before test modules import
# app.config/app.main.
os.environ["APP_ENV"] = "test"
os.environ["CARE_REPOSITORY_BACKEND"] = "memory"
os.environ["DATABASE_PING_ON_STARTUP"] = "false"
os.environ["REMINDER_SCHEDULER_ENABLED"] = "false"
os.environ["LOCAL_ALARM_ENABLED"] = "false"
os.environ["LOCAL_TTS_ENABLED"] = "false"
os.environ["API_AUTH_ENABLED"] = "false"
