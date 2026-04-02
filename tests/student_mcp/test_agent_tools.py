"""
Tests for agent tool schemas and execution routing (Phase 3, Commit 2).
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from question_app.services.tutor.prompts.socratic_tutor import (
    build_instance_b_prompt,
    AGENT_TOOL_INSTRUCTIONS,
)


# ---------------------------------------------------------------------------
# Tests: AGENT_TOOL_INSTRUCTIONS prompt
# ---------------------------------------------------------------------------

class TestAgentToolInstructions:

    def test_prompt_contains_tool_instructions(self):
        prompt = build_instance_b_prompt()
        assert "TOOL USAGE" in prompt
        assert "get_misconception_patterns" in prompt
        assert "log_misconception" in prompt
        assert "record_assessment_answer" in prompt
        assert "resolve_misconception" in prompt

    def test_prompt_no_longer_has_eval_json(self):
        prompt = build_instance_b_prompt()
        assert "STRUCTURED OUTPUT" not in prompt
        assert "```json" not in prompt
        assert "REMINDER: You MUST end every response" not in prompt

    def test_constraints_present(self):
        assert "Never call update_mastery with" in AGENT_TOOL_INSTRUCTIONS
        assert "mastered" in AGENT_TOOL_INSTRUCTIONS
        assert "record_assessment_answer" in AGENT_TOOL_INSTRUCTIONS


# ---------------------------------------------------------------------------
# Tests: Tool schema generation
# ---------------------------------------------------------------------------

class TestToolSchemaGeneration:
    """Test _build_agent_tool_schemas() output format."""

    @pytest.fixture
    def schemas(self):
        """Get tool schemas from a mock system instance."""
        # Create a minimal mock to call the method
        from question_app.services.tutor.hybrid_system import HybridCrewAISocraticSystem
        mock_system = MagicMock(spec=HybridCrewAISocraticSystem)
        mock_system._build_agent_tool_schemas = HybridCrewAISocraticSystem._build_agent_tool_schemas.__get__(mock_system)
        return mock_system._build_agent_tool_schemas()

    def test_returns_8_tools(self, schemas):
        assert len(schemas) == 8

    def test_all_have_function_type(self, schemas):
        for s in schemas:
            assert s["type"] == "function"

    def test_all_have_required_fields(self, schemas):
        for s in schemas:
            fn = s["function"]
            assert "name" in fn
            assert "description" in fn
            assert "parameters" in fn
            assert fn["parameters"]["type"] == "object"
            assert "properties" in fn["parameters"]
            assert "required" in fn["parameters"]

    def test_read_tools_present(self, schemas):
        names = {s["function"]["name"] for s in schemas}
        assert "get_mastery_state" in names
        assert "get_misconception_patterns" in names
        assert "get_active_session" in names

    def test_write_tools_present(self, schemas):
        names = {s["function"]["name"] for s in schemas}
        assert "log_misconception" in names
        assert "resolve_misconception" in names
        assert "update_mastery" in names
        assert "update_session_state" in names
        assert "record_assessment_answer" in names

    def test_update_mastery_has_confidence_param(self, schemas):
        mastery_tool = next(s for s in schemas if s["function"]["name"] == "update_mastery")
        props = mastery_tool["function"]["parameters"]["properties"]
        assert "confidence" in props
        assert props["confidence"]["type"] == "number"

    def test_update_mastery_restricts_levels(self, schemas):
        mastery_tool = next(s for s in schemas if s["function"]["name"] == "update_mastery")
        props = mastery_tool["function"]["parameters"]["properties"]
        # Should NOT include "mastered" or "partial" in enum
        allowed = props["mastery_level"]["enum"]
        assert "mastered" not in allowed
        assert "partial" not in allowed
        assert "in_progress" in allowed

    def test_record_assessment_has_is_correct(self, schemas):
        tool = next(s for s in schemas if s["function"]["name"] == "record_assessment_answer")
        props = tool["function"]["parameters"]["properties"]
        assert "is_correct" in props
        assert props["is_correct"]["type"] == "boolean"


# ---------------------------------------------------------------------------
# Tests: Tool execution routing
# ---------------------------------------------------------------------------

class TestToolExecution:
    """Test _execute_agent_tool() routes to correct MCP methods."""

    @pytest.fixture
    def system(self):
        from question_app.services.tutor.hybrid_system import HybridCrewAISocraticSystem
        mock = MagicMock(spec=HybridCrewAISocraticSystem)
        mock.student_mcp = AsyncMock()
        mock.student_mcp.get_mastery_state.return_value = [{"objective_id": "obj-1", "mastery_level": "in_progress"}]
        mock.student_mcp.get_misconception_patterns.return_value = []
        mock.student_mcp.get_active_session.return_value = {"current_stage": "exploration"}
        mock.student_mcp.log_misconception.return_value = {"id": 1}
        mock.student_mcp.resolve_misconception.return_value = {"resolved": True}
        mock.student_mcp.record_assessment_answer.return_value = {"recorded": True}
        mock.student_mcp._call.return_value = {"updated": True}
        mock._execute_agent_tool = HybridCrewAISocraticSystem._execute_agent_tool.__get__(mock)
        return mock

    @pytest.mark.asyncio
    async def test_routes_get_mastery_state(self, system):
        tc = {"function": {"name": "get_mastery_state", "arguments": '{"student_id": "s1"}'}, "id": "tc1"}
        result = await system._execute_agent_tool(tc)
        system.student_mcp.get_mastery_state.assert_called_once_with("s1")
        assert result[0]["mastery_level"] == "in_progress"

    @pytest.mark.asyncio
    async def test_routes_log_misconception(self, system):
        tc = {"function": {"name": "log_misconception", "arguments": json.dumps({
            "student_id": "s1", "objective_id": "o1", "misconception_text": "wrong"
        })}, "id": "tc2"}
        result = await system._execute_agent_tool(tc)
        system.student_mcp.log_misconception.assert_called_once_with("s1", "o1", "wrong")

    @pytest.mark.asyncio
    async def test_routes_record_assessment(self, system):
        tc = {"function": {"name": "record_assessment_answer", "arguments": json.dumps({
            "session_id": "sess-1", "is_correct": True
        })}, "id": "tc3"}
        result = await system._execute_agent_tool(tc)
        system.student_mcp.record_assessment_answer.assert_called_once_with("sess-1", True)

    @pytest.mark.asyncio
    async def test_routes_update_mastery_via_call(self, system):
        tc = {"function": {"name": "update_mastery", "arguments": json.dumps({
            "student_id": "s1", "objective_id": "o1", "mastery_level": "in_progress", "confidence": 0.8
        })}, "id": "tc4"}
        await system._execute_agent_tool(tc)
        system.student_mcp._call.assert_called_once()

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(self, system):
        tc = {"function": {"name": "nonexistent_tool", "arguments": '{"x": 1}'}, "id": "tc5"}
        result = await system._execute_agent_tool(tc)
        assert "error" in result

    @pytest.mark.asyncio
    async def test_invalid_arguments_returns_error(self, system):
        tc = {"function": {"name": "get_mastery_state", "arguments": "not json"}, "id": "tc6"}
        result = await system._execute_agent_tool(tc)
        assert "error" in result
