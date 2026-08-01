"""Tests for Tool Registry."""

import pytest

from app.tools import (
    AuthContext,
    DemoAuthContextFactory,
    Role,
    ToolRegistry,
    create_default_registry,
)


@pytest.fixture
def registry() -> ToolRegistry:
    """Create a default registry for testing."""
    return create_default_registry()


@pytest.fixture
def resident_auth() -> AuthContext:
    """Create a resident auth context."""
    return DemoAuthContextFactory.create_resident(
        requester_id="user-001",
        persona_id="persona-001",
        session_id="session-001",
        request_id="req-001",
    )


@pytest.fixture
def family_auth() -> AuthContext:
    """Create a family member auth context."""
    return DemoAuthContextFactory.create_family(
        requester_id="family-001",
        authorized_persona_ids={"persona-001"},
        session_id="session-002",
        request_id="req-002",
    )


class TestRegistryWhitelist:
    """Test 1: Registry only contains three whitelisted tools."""

    def test_registry_has_exactly_three_tools(self, registry: ToolRegistry):
        tool_names = registry.list_all_names()
        assert len(tool_names) == 3
        assert set(tool_names) == {
            "create_care_event",
            "create_reminder",
            "get_user_schedule",
        }


class TestUnknownToolRejection:
    """Test 2: Unknown tools are rejected."""

    def test_unknown_tool_returns_none(self, registry: ToolRegistry):
        assert registry.get("execute_sql") is None
        assert registry.get("shell_command") is None
        assert registry.get("file_write") is None
        assert registry.get("http_request") is None
        assert registry.get("delete_all_data") is None

    def test_unknown_tool_not_exists(self, registry: ToolRegistry):
        assert registry.exists("execute_sql") is False
        assert registry.exists("drop_table") is False



class TestFamilyCannotSeeWriteTools:
    """Test 3: Family role cannot see write tool schemas."""

    def test_family_list_allowed_tools_excludes_writes(
        self, registry: ToolRegistry, family_auth: AuthContext
    ):
        allowed = registry.list_allowed_tools(family_auth)
        tool_names = [t.name for t in allowed]

        # Family should only see read tools
        assert "get_user_schedule" in tool_names
        assert "create_care_event" not in tool_names
        assert "create_reminder" not in tool_names

    def test_family_bedrock_config_excludes_writes(
        self, registry: ToolRegistry, family_auth: AuthContext
    ):
        config = registry.get_bedrock_tool_config(family_auth)
        tool_names = [c["toolSpec"]["name"] for c in config]

        assert "get_user_schedule" in tool_names
        assert "create_care_event" not in tool_names
        assert "create_reminder" not in tool_names


class TestBedrockConfigNoPersonaId:
    """Test 4: Bedrock toolConfig does not contain persona_id."""

    def test_create_care_event_schema_no_persona_id(
        self, registry: ToolRegistry, resident_auth: AuthContext
    ):
        config = registry.get_bedrock_tool_config(resident_auth)

        for tool_config in config:
            tool_spec = tool_config["toolSpec"]
            if tool_spec["name"] == "create_care_event":
                properties = tool_spec["inputSchema"]["json"]["properties"]
                assert "persona_id" not in properties
                assert "resident_id" not in properties
                assert "requester_id" not in properties
                assert "authorized_persona_ids" not in properties
                assert "SQL" not in properties
                assert "table_name" not in properties

    def test_create_reminder_schema_no_persona_id(
        self, registry: ToolRegistry, resident_auth: AuthContext
    ):
        config = registry.get_bedrock_tool_config(resident_auth)

        for tool_config in config:
            tool_spec = tool_config["toolSpec"]
            if tool_spec["name"] == "create_reminder":
                properties = tool_spec["inputSchema"]["json"]["properties"]
                assert "persona_id" not in properties
                assert "resident_id" not in properties

    def test_get_user_schedule_schema_no_persona_id(
        self, registry: ToolRegistry, resident_auth: AuthContext
    ):
        config = registry.get_bedrock_tool_config(resident_auth)

        for tool_config in config:
            tool_spec = tool_config["toolSpec"]
            if tool_spec["name"] == "get_user_schedule":
                properties = tool_spec["inputSchema"]["json"]["properties"]
                assert "persona_id" not in properties


class TestAdditionalPropertiesFalse:
    """Test 5: Tool schemas use additionalProperties=false."""

    def test_all_schemas_forbid_additional_properties(
        self, registry: ToolRegistry, resident_auth: AuthContext
    ):
        config = registry.get_bedrock_tool_config(resident_auth)

        for tool_config in config:
            tool_spec = tool_config["toolSpec"]
            schema = tool_spec["inputSchema"]["json"]
            assert schema.get("additionalProperties") is False, (
                f"Tool {tool_spec['name']} must have additionalProperties=false"
            )
