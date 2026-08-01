"""FastAPI application entry point."""

import logging
import uuid

from fastapi import FastAPI

from app.config import settings
from app.models import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    InputGuardCheckRequest,
    InputGuardCheckResponse,
)
from app.providers.bedrock import BedrockProvider
from app.repositories import create_care_repository
from app.security import AgentInputGuard
from app.services.agent_service import AgentService
from app.tools import DemoAuthContextFactory, ToolGateway

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = FastAPI(
    title="智慧長照語音 Agent",
    description="智慧長照生活協助系統 API",
    version="0.3.0",
)

provider = BedrockProvider()
repository = create_care_repository()
gateway = ToolGateway(repository=repository)
input_guard = AgentInputGuard(
    enabled=settings.INPUT_GUARD_ENABLED,
    fail_closed=settings.INPUT_GUARD_FAIL_CLOSED,
)
agent_service = AgentService(
    provider=provider,
    gateway=gateway,
    input_guard=input_guard,
)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        app_env=settings.APP_ENV,
        model_id=settings.BEDROCK_MODEL_ID,
    )


@app.post("/api/security/input-guard/check", response_model=InputGuardCheckResponse)
async def input_guard_check(
    request: InputGuardCheckRequest,
) -> InputGuardCheckResponse:
    """Inspect text without invoking Bedrock or any tool.

    The user role and authorization are intentionally not accepted from the
    request body. They are constructed from trusted backend demo context.
    """
    session_id = request.session_id or str(uuid.uuid4())
    request_id = str(uuid.uuid4())
    auth_context = DemoAuthContextFactory.create_resident(
        requester_id=settings.DEMO_USER_ID,
        persona_id=settings.DEMO_PERSONA_ID,
        session_id=session_id,
        request_id=request_id,
    )
    outcome = input_guard.inspect(
        text=request.message,
        auth_context=auth_context,
    )
    return InputGuardCheckResponse(
        request_id=request_id,
        session_id=session_id,
        allowed=outcome.allowed,
        action=outcome.evidence.action,
        sanitized_text=outcome.sanitized_text if outcome.allowed else None,
        safe_response=outcome.safe_response,
        input_guard=outcome.evidence,
    )


@app.post("/api/agent/chat", response_model=ChatResponse)
async def agent_chat(request: ChatRequest) -> ChatResponse:
    return await agent_service.chat(request)
