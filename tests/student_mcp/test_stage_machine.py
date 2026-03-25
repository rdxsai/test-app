"""
Unit tests for the Stage Machine.

Uses a mock Student MCP client to verify stage transitions,
assessment scoring, mastery updates, and misconception logging
without hitting the real MCP server or database.
"""

import json
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock

from question_app.services.tutor.stage_machine import StageMachine


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_mcp():
    """Mock StudentMCPClient with all methods as AsyncMock."""
    mcp = AsyncMock()
    mcp.update_session_state.return_value = {}
    mcp.update_mastery.return_value = {}
    mcp.log_misconception.return_value = {}
    mcp.get_recommended_next_objective.return_value = {
        "objective_id": "obj-next",
        "objective_text": "Next objective",
    }
    return mcp


@pytest.fixture
def machine(mock_mcp):
    return StageMachine(mock_mcp)


def _session(stage="introduction", turns=0, objective="obj-1",
             mini_progress=None, final_progress=None):
    """Helper to build a session_state dict."""
    return {
        "session_id": "sess-1",
        "student_id": "stu-1",
        "current_stage": stage,
        "active_objective_id": objective,
        "turns_on_objective": turns,
        "mini_assessment_progress": mini_progress or {"asked": 0, "correct": 0},
        "final_assessment_progress": final_progress or {"asked": 0, "correct": 0},
        "stage_summary": "",
    }


def _eval(state="CORRECT", mode="GUIDANCE", recommendation="stay",
          evidence="", level_change="no_change", misconceptions=None,
          summary=None, confidence=0.8):
    """Helper to build an eval_data dict."""
    return {
        "detected_state": state,
        "response_mode": mode,
        "stage_recommendation": recommendation,
        "mastery_evidence": evidence,
        "mastery_level_change": level_change,
        "misconceptions_detected": misconceptions or [],
        "stage_summary": summary,
        "confidence": confidence,
    }


# ---------------------------------------------------------------------------
# Tests: Turn Tracking
# ---------------------------------------------------------------------------

class TestTurnTracking:

    @pytest.mark.asyncio
    async def test_increments_turns(self, machine, mock_mcp):
        result = await machine.process_eval(
            "stu-1", "sess-1", _session(turns=3), _eval()
        )
        assert result["turns_incremented"] is True
        mock_mcp.update_session_state.assert_any_call("sess-1", turns=4)


# ---------------------------------------------------------------------------
# Tests: Introduction stage
# ---------------------------------------------------------------------------

class TestIntroduction:

    @pytest.mark.asyncio
    async def test_advance_to_exploration(self, machine, mock_mcp):
        result = await machine.process_eval(
            "stu-1", "sess-1",
            _session(stage="introduction", turns=2),
            _eval(recommendation="advance_to_exploration"),
        )
        assert result["stage_changed"] is True
        assert result["new_stage"] == "exploration"

    @pytest.mark.asyncio
    async def test_advance_to_readiness_check_with_evidence(self, machine, mock_mcp):
        result = await machine.process_eval(
            "stu-1", "sess-1",
            _session(stage="introduction", turns=3),
            _eval(recommendation="advance_to_readiness_check", evidence="strong understanding"),
        )
        assert result["stage_changed"] is True
        assert result["new_stage"] == "readiness_check"

    @pytest.mark.asyncio
    async def test_fast_track_to_mini_assessment(self, machine, mock_mcp):
        result = await machine.process_eval(
            "stu-1", "sess-1",
            _session(stage="introduction", turns=1),
            _eval(recommendation="advance_to_mini_assessment"),
        )
        assert result["stage_changed"] is True
        assert result["new_stage"] == "mini_assessment"

    @pytest.mark.asyncio
    async def test_force_to_exploration_at_max_turns(self, machine, mock_mcp):
        result = await machine.process_eval(
            "stu-1", "sess-1",
            _session(stage="introduction", turns=7),  # +1 = 8 = MAX
            _eval(recommendation="stay"),
        )
        assert result["stage_changed"] is True
        assert result["new_stage"] == "exploration"

    @pytest.mark.asyncio
    async def test_stay_in_introduction(self, machine, mock_mcp):
        result = await machine.process_eval(
            "stu-1", "sess-1",
            _session(stage="introduction", turns=2),
            _eval(recommendation="stay"),
        )
        assert result["stage_changed"] is False


# ---------------------------------------------------------------------------
# Tests: Exploration stage
# ---------------------------------------------------------------------------

class TestExploration:

    @pytest.mark.asyncio
    async def test_advance_to_readiness_check(self, machine, mock_mcp):
        result = await machine.process_eval(
            "stu-1", "sess-1",
            _session(stage="exploration", turns=4),
            _eval(recommendation="advance_to_readiness_check", evidence="understands concept"),
        )
        assert result["stage_changed"] is True
        assert result["new_stage"] == "readiness_check"

    @pytest.mark.asyncio
    async def test_deny_advance_too_few_turns(self, machine, mock_mcp):
        result = await machine.process_eval(
            "stu-1", "sess-1",
            _session(stage="exploration", turns=1),
            _eval(recommendation="advance_to_readiness_check", evidence="some evidence"),
        )
        assert result["stage_changed"] is False

    @pytest.mark.asyncio
    async def test_deny_advance_no_evidence(self, machine, mock_mcp):
        result = await machine.process_eval(
            "stu-1", "sess-1",
            _session(stage="exploration", turns=5),
            _eval(state="CONFUSED_ABOUT_PROBLEM",
                  recommendation="advance_to_readiness_check", evidence=""),
        )
        assert result["stage_changed"] is False

    @pytest.mark.asyncio
    async def test_correct_state_counts_as_evidence(self, machine, mock_mcp):
        result = await machine.process_eval(
            "stu-1", "sess-1",
            _session(stage="exploration", turns=4),
            _eval(state="CORRECT", recommendation="advance_to_readiness_check"),
        )
        assert result["stage_changed"] is True
        assert result["new_stage"] == "readiness_check"

    @pytest.mark.asyncio
    async def test_advance_to_mini_directly(self, machine, mock_mcp):
        result = await machine.process_eval(
            "stu-1", "sess-1",
            _session(stage="exploration", turns=5),
            _eval(state="CORRECT", recommendation="advance_to_mini_assessment"),
        )
        assert result["stage_changed"] is True
        assert result["new_stage"] == "mini_assessment"

    @pytest.mark.asyncio
    async def test_force_readiness_at_max_turns(self, machine, mock_mcp):
        result = await machine.process_eval(
            "stu-1", "sess-1",
            _session(stage="exploration", turns=7),  # +1 = 8 = MAX
            _eval(recommendation="stay"),
        )
        assert result["stage_changed"] is True
        assert result["new_stage"] == "readiness_check"

    @pytest.mark.asyncio
    async def test_stay_in_exploration(self, machine, mock_mcp):
        result = await machine.process_eval(
            "stu-1", "sess-1",
            _session(stage="exploration", turns=3),
            _eval(recommendation="stay"),
        )
        assert result["stage_changed"] is False


# ---------------------------------------------------------------------------
# Tests: Readiness Check
# ---------------------------------------------------------------------------

class TestReadinessCheck:

    @pytest.mark.asyncio
    async def test_accept_to_mini(self, machine, mock_mcp):
        result = await machine.process_eval(
            "stu-1", "sess-1",
            _session(stage="readiness_check"),
            _eval(recommendation="advance_to_mini_assessment"),
        )
        assert result["stage_changed"] is True
        assert result["new_stage"] == "mini_assessment"

    @pytest.mark.asyncio
    async def test_decline_back_to_exploration(self, machine, mock_mcp):
        result = await machine.process_eval(
            "stu-1", "sess-1",
            _session(stage="readiness_check"),
            _eval(recommendation="loop_back_to_introduction"),
        )
        assert result["stage_changed"] is True
        assert result["new_stage"] == "exploration"


# ---------------------------------------------------------------------------
# Tests: Mini Assessment
# ---------------------------------------------------------------------------

class TestMiniAssessment:

    @pytest.mark.asyncio
    async def test_correct_answer_tracked(self, machine, mock_mcp):
        result = await machine.process_eval(
            "stu-1", "sess-1",
            _session(stage="mini_assessment", mini_progress={"asked": 0, "correct": 0}),
            _eval(state="CORRECT"),
        )
        # After 1 question, not done yet
        assert result["assessment_result"]["asked"] == 1
        assert result["assessment_result"]["correct"] == 1
        assert result["assessment_result"]["passed"] is None  # not complete

    @pytest.mark.asyncio
    async def test_mini_pass_2_of_3(self, machine, mock_mcp):
        result = await machine.process_eval(
            "stu-1", "sess-1",
            _session(stage="mini_assessment", mini_progress={"asked": 2, "correct": 1}),
            _eval(state="CORRECT"),  # 3rd question, correct → 2/3
        )
        assert result["assessment_result"]["passed"] is True
        assert result["stage_changed"] is True
        assert result["new_stage"] == "final_assessment"

    @pytest.mark.asyncio
    async def test_mini_fail_1_of_3(self, machine, mock_mcp):
        result = await machine.process_eval(
            "stu-1", "sess-1",
            _session(stage="mini_assessment", mini_progress={"asked": 2, "correct": 1}),
            _eval(state="INCORRECT_APPLICATION"),  # 3rd wrong → 1/3
        )
        assert result["assessment_result"]["passed"] is False
        assert result["stage_changed"] is True
        assert result["new_stage"] == "introduction"  # loop back


# ---------------------------------------------------------------------------
# Tests: Final Assessment
# ---------------------------------------------------------------------------

class TestFinalAssessment:

    @pytest.mark.asyncio
    async def test_final_mastered_4_of_5(self, machine, mock_mcp):
        result = await machine.process_eval(
            "stu-1", "sess-1",
            _session(stage="final_assessment", final_progress={"asked": 4, "correct": 3}),
            _eval(state="CORRECT"),  # 5th correct → 4/5
        )
        assert result["assessment_result"]["passed"] is True
        assert result["mastery_updated"] is True
        assert result["new_mastery_level"] == "mastered"
        assert result["new_stage"] == "transition"

    @pytest.mark.asyncio
    async def test_final_partial_3_of_5(self, machine, mock_mcp):
        result = await machine.process_eval(
            "stu-1", "sess-1",
            _session(stage="final_assessment", final_progress={"asked": 4, "correct": 3}),
            _eval(state="INCORRECT_APPLICATION"),  # 5th wrong → 3/5
        )
        assert result["new_mastery_level"] == "partial"
        assert result["new_stage"] == "transition"

    @pytest.mark.asyncio
    async def test_final_fail_2_of_5(self, machine, mock_mcp):
        result = await machine.process_eval(
            "stu-1", "sess-1",
            _session(stage="final_assessment", final_progress={"asked": 4, "correct": 2}),
            _eval(state="INCORRECT_APPLICATION"),  # 5th wrong → 2/5
        )
        assert result["new_mastery_level"] == "in_progress"
        assert result["new_stage"] == "introduction"  # loop back


# ---------------------------------------------------------------------------
# Tests: Transition
# ---------------------------------------------------------------------------

class TestTransition:

    @pytest.mark.asyncio
    async def test_transition_to_next_objective(self, machine, mock_mcp):
        result = await machine.process_eval(
            "stu-1", "sess-1",
            _session(stage="transition"),
            _eval(),
        )
        assert result["stage_changed"] is True
        assert result["new_stage"] == "introduction"
        mock_mcp.get_recommended_next_objective.assert_called_once_with("stu-1")

    @pytest.mark.asyncio
    async def test_all_objectives_mastered(self, machine, mock_mcp):
        mock_mcp.get_recommended_next_objective.return_value = None
        result = await machine.process_eval(
            "stu-1", "sess-1",
            _session(stage="transition"),
            _eval(),
        )
        assert result["stage_changed"] is False
        assert "mastered" in result["stage_summary"].lower()


# ---------------------------------------------------------------------------
# Tests: Mastery Changes
# ---------------------------------------------------------------------------

class TestMasteryChanges:

    @pytest.mark.asyncio
    async def test_mastery_updated_above_threshold(self, machine, mock_mcp):
        result = await machine.process_eval(
            "stu-1", "sess-1",
            _session(stage="exploration", turns=2),
            _eval(level_change="not_attempted→in_progress",
                  evidence="Student began exploring", confidence=0.85),
        )
        assert result["mastery_updated"] is True
        mock_mcp.update_mastery.assert_called_once()

    @pytest.mark.asyncio
    async def test_mastery_not_updated_below_threshold(self, machine, mock_mcp):
        result = await machine.process_eval(
            "stu-1", "sess-1",
            _session(stage="exploration", turns=2),
            _eval(level_change="not_attempted→misconception", confidence=0.5),
        )
        assert result["mastery_updated"] is False

    @pytest.mark.asyncio
    async def test_no_change_skips_update(self, machine, mock_mcp):
        result = await machine.process_eval(
            "stu-1", "sess-1",
            _session(stage="exploration", turns=2),
            _eval(level_change="no_change", confidence=0.9),
        )
        assert result["mastery_updated"] is False

    @pytest.mark.asyncio
    async def test_mastery_capped_during_exploration(self, machine, mock_mcp):
        """LLM suggests 'mastered' during exploration but stage machine caps to 'in_progress'."""
        result = await machine.process_eval(
            "stu-1", "sess-1",
            _session(stage="exploration", turns=5),
            _eval(level_change="not_attempted→mastered", confidence=0.9),
        )
        assert result["mastery_updated"] is True
        # The level written to MCP should be "in_progress", not "mastered"
        call_str = str(mock_mcp.update_mastery.call_args)
        assert "in_progress" in call_str, f"Expected 'in_progress' in call but got: {call_str}"

    @pytest.mark.asyncio
    async def test_mastery_capped_during_introduction(self, machine, mock_mcp):
        """LLM suggests 'partial' during introduction but stage machine caps to 'in_progress'."""
        result = await machine.process_eval(
            "stu-1", "sess-1",
            _session(stage="introduction", turns=2),
            _eval(level_change="not_attempted→partial", confidence=0.85),
        )
        assert result["mastery_updated"] is True
        call_str = str(mock_mcp.update_mastery.call_args)
        assert "in_progress" in call_str, f"Expected 'in_progress' in call but got: {call_str}"


# ---------------------------------------------------------------------------
# Tests: Misconception Logging
# ---------------------------------------------------------------------------

class TestMisconceptionLogging:

    @pytest.mark.asyncio
    async def test_misconceptions_logged(self, machine, mock_mcp):
        result = await machine.process_eval(
            "stu-1", "sess-1",
            _session(stage="exploration", turns=2),
            _eval(misconceptions=["Thinks aria-hidden removes from DOM"]),
        )
        assert len(result["misconceptions_logged"]) == 1
        mock_mcp.log_misconception.assert_called_once()

    @pytest.mark.asyncio
    async def test_empty_misconceptions_not_logged(self, machine, mock_mcp):
        result = await machine.process_eval(
            "stu-1", "sess-1",
            _session(stage="exploration", turns=2),
            _eval(misconceptions=[]),
        )
        assert result["misconceptions_logged"] == []
        mock_mcp.log_misconception.assert_not_called()

    @pytest.mark.asyncio
    async def test_multiple_misconceptions(self, machine, mock_mcp):
        result = await machine.process_eval(
            "stu-1", "sess-1",
            _session(stage="exploration", turns=2),
            _eval(misconceptions=["misc 1", "misc 2"]),
        )
        assert len(result["misconceptions_logged"]) == 2
        assert mock_mcp.log_misconception.call_count == 2
