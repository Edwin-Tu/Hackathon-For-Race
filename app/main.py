"""FastAPI application entry point."""

import logging

from fastapi import FastAPI

from app.config import settings
from app.models import ChatRequest, ChatResponse, HealthResponse
from app.providers.bedrock import BedrockProvider
from app.repositories import create_care_repository
from app.services.agent_service import AgentService
from app.tools import ToolGateway

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = FastAPI(
    title="智慧長照語音 Agent",
    description="智慧長照生活協助系統 API",
    version="0.2.0",
)

provider = BedrockProvider()
repository = create_care_repository()
gateway = ToolGateway(repository=repository)
agent_service = AgentService(provider=provider, gateway=gateway)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        app_env=settings.APP_ENV,
        model_id=settings.BEDROCK_MODEL_ID,
    )


@app.post("/api/agent/chat", response_model=ChatResponse)
async def agent_chat(request: ChatRequest) -> ChatResponse:
    return await agent_service.chat(request)
