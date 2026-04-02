"""
Tests for concept decomposition (Phase 2).

Tests the teaching plan generation, session cache storage,
concept coverage tracking, and prompt injection.
"""

import pytest
from question_app.services.tutor.session_cache import SessionContentCache
from question_app.services.tutor.prompts.socratic_tutor import (
    build_instance_b_prompt,
    format_teaching_plan,
    CONCEPT_DECOMPOSITION_PROMPT,
)


# ---------------------------------------------------------------------------
# Sample teaching plan
# ---------------------------------------------------------------------------

SAMPLE_PLAN = {
    "objective": "Apply ARIA live regions to communicate dynamic content updates",
    "concepts": [
        {"id": "c1", "name": "What aria-live does", "description": "Creates a live region for AT announcements",
         "prerequisites": [], "key_points": ["live regions", "dynamic content"], "status": "not_covered"},
        {"id": "c2", "name": "polite vs assertive", "description": "Urgency levels for announcements",
         "prerequisites": ["c1"], "key_points": ["polite", "assertive", "interruption"], "status": "not_covered"},
        {"id": "c3", "name": "aria-atomic and aria-relevant", "description": "Control what gets announced",
         "prerequisites": ["c1"], "key_points": ["atomic", "relevant", "additions"], "status": "not_covered"},
    ],
    "recommended_order": ["c1", "c2", "c3"],
}


# ---------------------------------------------------------------------------
# Tests: format_teaching_plan
# ---------------------------------------------------------------------------

class TestFormatTeachingPlan:

    def test_formats_all_concepts(self):
        text = format_teaching_plan(SAMPLE_PLAN)
        assert "c1: What aria-live does" in text
        assert "c2: polite vs assertive" in text
        assert "c3: aria-atomic and aria-relevant" in text

    def test_shows_teaching_order(self):
        text = format_teaching_plan(SAMPLE_PLAN)
        assert "c1 → c2 → c3" in text

    def test_shows_prerequisites(self):
        text = format_teaching_plan(SAMPLE_PLAN)
        assert "(requires: c1)" in text

    def test_shows_key_points(self):
        text = format_teaching_plan(SAMPLE_PLAN)
        assert "live regions" in text
        assert "polite" in text

    def test_shows_coverage_status(self):
        plan = {**SAMPLE_PLAN, "concepts": [
            {**SAMPLE_PLAN["concepts"][0], "status": "covered"},
            {**SAMPLE_PLAN["concepts"][1], "status": "partially_covered"},
            {**SAMPLE_PLAN["concepts"][2], "status": "not_covered"},
        ]}
        text = format_teaching_plan(plan)
        assert "✓" in text   # covered
        assert "◐" in text   # partially_covered
        assert "○" in text   # not_covered

    def test_empty_plan_returns_empty(self):
        assert format_teaching_plan({}) == ""
        assert format_teaching_plan(None) == ""

    def test_focus_instruction(self):
        text = format_teaching_plan(SAMPLE_PLAN)
        assert "Focus on the first not_covered concept" in text


# ---------------------------------------------------------------------------
# Tests: Session cache teaching plan storage
# ---------------------------------------------------------------------------

class TestCacheTeachingPlan:

    def test_store_and_get_plan(self):
        cache = SessionContentCache()
        cache.store("s1", "obj-1", "Objective", [], "", "content")
        cache.store_teaching_plan("s1", SAMPLE_PLAN)
        plan = cache.get_teaching_plan("s1")
        assert plan is not None
        assert len(plan["concepts"]) == 3

    def test_get_plan_no_entry(self):
        cache = SessionContentCache()
        assert cache.get_teaching_plan("nonexistent") is None

    def test_update_concept_status(self):
        cache = SessionContentCache()
        cache.store("s1", "obj-1", "", [], "", "")
        cache.store_teaching_plan("s1", {
            "objective": "test",
            "concepts": [
                {"id": "c1", "name": "A", "status": "not_covered"},
                {"id": "c2", "name": "B", "status": "not_covered"},
            ],
            "recommended_order": ["c1", "c2"],
        })
        cache.update_concept_status("s1", "c1", "covered")
        plan = cache.get_teaching_plan("s1")
        assert plan["concepts"][0]["status"] == "covered"
        assert plan["concepts"][1]["status"] == "not_covered"

    def test_update_nonexistent_concept(self):
        cache = SessionContentCache()
        cache.store("s1", "obj-1", "", [], "", "")
        cache.store_teaching_plan("s1", {
            "objective": "test", "concepts": [{"id": "c1", "name": "A", "status": "not_covered"}],
            "recommended_order": ["c1"],
        })
        cache.update_concept_status("s1", "c99", "covered")  # no crash
        plan = cache.get_teaching_plan("s1")
        assert plan["concepts"][0]["status"] == "not_covered"  # unchanged

    def test_invalidate_clears_plan(self):
        cache = SessionContentCache()
        cache.store("s1", "obj-1", "", [], "", "")
        cache.store_teaching_plan("s1", SAMPLE_PLAN)
        cache.invalidate("s1")
        assert cache.get_teaching_plan("s1") is None


# ---------------------------------------------------------------------------
# Tests: Teaching plan in Instance B prompt
# ---------------------------------------------------------------------------

class TestPromptIntegration:

    def test_plan_injected_into_prompt(self):
        prompt = build_instance_b_prompt(teaching_plan=SAMPLE_PLAN)
        assert "TEACHING PLAN:" in prompt
        assert "c1: What aria-live does" in prompt
        assert "c1 → c2 → c3" in prompt

    def test_no_plan_no_injection(self):
        prompt = build_instance_b_prompt(teaching_plan=None)
        assert "TEACHING PLAN:" not in prompt

    def test_tool_instructions_in_prompt(self):
        prompt = build_instance_b_prompt()
        assert "TOOL USAGE" in prompt


# ---------------------------------------------------------------------------
# Tests: CONCEPT_DECOMPOSITION_PROMPT
# ---------------------------------------------------------------------------

class TestDecompositionPrompt:

    def test_prompt_exists_and_has_key_instructions(self):
        assert "Minimum 3" in CONCEPT_DECOMPOSITION_PROMPT
        assert "maximum 6" in CONCEPT_DECOMPOSITION_PROMPT
        assert "prerequisites" in CONCEPT_DECOMPOSITION_PROMPT
        assert "recommended_order" in CONCEPT_DECOMPOSITION_PROMPT
        assert "not_covered" in CONCEPT_DECOMPOSITION_PROMPT
        assert "valid JSON" in CONCEPT_DECOMPOSITION_PROMPT
        assert "GROUND IN CONTENT" in CONCEPT_DECOMPOSITION_PROMPT
        assert "quiz_mappings" in CONCEPT_DECOMPOSITION_PROMPT
