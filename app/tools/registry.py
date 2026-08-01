"""
Tool Registry: whitelist of allowed tools with metadata.

Security rules:
1. Unknown tools are rejected.
2. Model-visible tools are filtered by role.
3. Even if model forges hidden tool, Gateway re-validates at execution.
4. No execute_sql, shell, file_write, or arbitrary HTTP tools.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel

from app.tools.enums import RiskLevel, Role
from app.tools.models import AuthContext
from app.tools.schemas import (
    TOOL_SCHEMAS,
    CreateCareEventArgs,
    CreateReminderArgs,
    GetUserScheduleArgs,
)


@dataclass
class ToolDefinition:
    """Definition of a registered tool."""

    name: str
    description: str
    argument_model: type[BaseModel]
    handler: Callable[..., Any]
    risk_level: RiskLevel
    is_write: bool
    allowed_roles: set[Role]
    requires_confirmation: Callable[[dict[str, Any]], bool]
    max_timeout_seconds: int = 30


class ToolRegistry:
    """Registry of allowed tools with permission checking."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        """Register a tool definition."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition | None:
        """Get tool by name, returns None if not found."""
        return self._tools.get(name)

    def exists(self, name: str) -> bool:
        """Check if tool exists in registry."""
        return name in self._tools

    def list_all_names(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    def list_allowed_tools(self, auth_context: AuthContext) -> list[ToolDefinition]:
        """
        List tools allowed for the given auth context.
        Family role cannot see write tools.
        """
        allowed = []
        for tool in self._tools.values():
            if auth_context.role in tool.allowed_roles:
                # Family can only see read tools
                if auth_context.role == Role.FAMILY and tool.is_write:
                    continue
                allowed.append(tool)
        return allowed

    def get_bedrock_tool_config(
        self, auth_context: AuthContext
    ) -> list[dict[str, Any]]:
        """
        Generate Bedrock toolConfig for model consumption.
        
        Filters by role and ensures no persona_id in schema.
        Uses additionalProperties=false to prevent unauthorized fields.
        """
        allowed_tools = self.list_allowed_tools(auth_context)
        configs = []
        for tool in allowed_tools:
            if tool.name in TOOL_SCHEMAS:
                configs.append({"toolSpec": TOOL_SCHEMAS[tool.name]})
        return configs


def _always_false(_args: dict[str, Any]) -> bool:
    """Never requires confirmation."""
    return False


def _never_confirm(_args: dict[str, Any]) -> bool:
    """Never requires confirmation - alias for clarity."""
    return False


# Placeholder handlers - will be replaced by actual handlers from handlers.py
def _placeholder_handler(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Placeholder handler that should never be called directly."""
    raise NotImplementedError("Handler not set")


def create_default_registry() -> ToolRegistry:
    """
    Create registry with the three MVP tools.
    
    Handlers will be set by the Gateway when it initializes.
    """
    registry = ToolRegistry()

    # Tool: create_care_event
    registry.register(
        ToolDefinition(
            name="create_care_event",
            description="記錄照護事件",
            argument_model=CreateCareEventArgs,
            handler=_placeholder_handler,
            risk_level=RiskLevel.MEDIUM,
            is_write=True,
            allowed_roles={Role.RESIDENT, Role.CAREGIVER, Role.ADMIN, Role.SYSTEM},
            requires_confirmation=lambda args: args.get("event_type") == "medication",
            max_timeout_seconds=30,
        )
    )

    # Tool: create_reminder
    registry.register(
        ToolDefinition(
            name="create_reminder",
            description="建立提醒事項",
            argument_model=CreateReminderArgs,
            handler=_placeholder_handler,
            risk_level=RiskLevel.MEDIUM,
            is_write=True,
            allowed_roles={Role.RESIDENT, Role.CAREGIVER, Role.ADMIN, Role.SYSTEM},
            requires_confirmation=lambda args: (
                args.get("importance") == "high"
                or _contains_medical_keywords(args.get("title", ""))
            ),
            max_timeout_seconds=30,
        )
    )

    # Tool: get_user_schedule
    registry.register(
        ToolDefinition(
            name="get_user_schedule",
            description="查詢行程安排",
            argument_model=GetUserScheduleArgs,
            handler=_placeholder_handler,
            risk_level=RiskLevel.LOW,
            is_write=False,
            allowed_roles={
                Role.RESIDENT,
                Role.CAREGIVER,
                Role.FAMILY,
                Role.ADMIN,
                Role.SYSTEM,
            },
            requires_confirmation=_never_confirm,
            max_timeout_seconds=15,
        )
    )

    return registry


def _contains_medical_keywords(text: str) -> bool:
    """Check if text contains medical-related keywords requiring confirmation."""
    keywords = ["醫院", "回診", "用藥", "藥物", "看診", "門診", "檢查", "手術"]
    return any(kw in text for kw in keywords)
