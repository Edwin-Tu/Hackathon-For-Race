"""Repository selection for application startup."""

from __future__ import annotations

import logging

from app.config import settings
from app.repositories.base import CareRepository
from app.repositories.memory import InMemoryCareRepository

logger = logging.getLogger(__name__)


def create_care_repository() -> CareRepository:
    """Create the configured repository without silently weakening policy.

    Modes:
    - memory: always process-local storage
    - mysql: require DATABASE_URL and a working database
    - auto: use MySQL when DATABASE_URL is present, otherwise memory
    """

    backend = settings.CARE_REPOSITORY_BACKEND.strip().lower()
    if backend not in {"memory", "mysql", "auto"}:
        raise RuntimeError(
            "CARE_REPOSITORY_BACKEND must be one of: memory, mysql, auto"
        )

    should_use_mysql = backend == "mysql" or (
        backend == "auto" and bool(settings.DATABASE_URL)
    )
    if not should_use_mysql:
        logger.warning("Using in-memory repository; data will not survive restart")
        return InMemoryCareRepository()

    if not settings.DATABASE_URL:
        raise RuntimeError(
            "CARE_REPOSITORY_BACKEND=mysql requires DATABASE_URL"
        )

    from app.repositories.mysql import MySQLCareRepository

    repository = MySQLCareRepository(settings.DATABASE_URL)
    if settings.DATABASE_PING_ON_STARTUP:
        repository.ping()
    logger.info("Using MySQL care repository")
    return repository
