"""Tests for retained prompt-side tool instructions."""

import pytest

from question_app.services.tutor.prompts.socratic_tutor import (
    build_instance_b_prompt,
    AGENT_TOOL_INSTRUCTIONS,
)


# ---------------------------------------------------------------------------
# Tests: AGENT_TOOL_INSTRUCTIONS prompt
# ---------------------------------------------------------------------------

class TestAgentToolInstructions:

    def test_prompt_contains_tool_instructions(self):
        """Tool instructions are deferred in v2 prompt (will be re-integrated
        with student model). AGENT_TOOL_INSTRUCTIONS still exists as a constant
        for future use."""
        from question_app.services.tutor.prompts import AGENT_TOOL_INSTRUCTIONS
        assert "TOOL USAGE" in AGENT_TOOL_INSTRUCTIONS
        assert "log_misconception" in AGENT_TOOL_INSTRUCTIONS
        assert "record_assessment_answer" in AGENT_TOOL_INSTRUCTIONS
        # Instance B v2 prompt does not include tool instructions yet
        prompt = build_instance_b_prompt()
        assert "TOOL USAGE" not in prompt

    def test_prompt_no_longer_has_eval_json(self):
        prompt = build_instance_b_prompt()
        assert "STRUCTURED OUTPUT" not in prompt
        assert "```json" not in prompt
        assert "REMINDER: You MUST end every response" not in prompt

    def test_constraints_present(self):
        assert "Never call update_mastery with" in AGENT_TOOL_INSTRUCTIONS
        assert "mastered" in AGENT_TOOL_INSTRUCTIONS
        assert "record_assessment_answer" in AGENT_TOOL_INSTRUCTIONS
