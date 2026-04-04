"""
Unit tests for stage-adaptive tutoring prompt builders.

Verifies that the prompt templates assemble correctly with the
stage-dependent teaching approach swap.
"""

import pytest
from question_app.services.tutor.prompts.socratic_tutor import (
    build_instance_a_prompt,
    build_instance_b_prompt,
)


class TestInstanceAPrompt:
    """Instance A: General Q&A — teach-first, no stages or tools."""

    def test_contains_role_preamble(self):
        prompt = build_instance_a_prompt()
        assert "warm, patient tutor" in prompt
        assert "TEACHING, not testing" in prompt

    def test_contains_teach_first_approach(self):
        prompt = build_instance_a_prompt()
        assert "HOW TO TEACH (INTRODUCTION PHASE)" in prompt
        assert "clear, concise explanation" in prompt
        assert "ONE gentle question" in prompt
        assert "natural conversation" in prompt

    def test_contains_what_to_never_do(self):
        prompt = build_instance_a_prompt()
        assert "WHAT TO NEVER DO" in prompt
        assert "Never ask about a concept you haven't explained yet" in prompt
        assert "Never ask more than ONE question" in prompt

    def test_contains_misconception_handling(self):
        prompt = build_instance_a_prompt()
        assert "WHEN THE STUDENT SAYS SOMETHING WRONG" in prompt
        assert "log_misconception" in prompt

    def test_contains_few_shot_examples(self):
        prompt = build_instance_a_prompt()
        assert "EXAMPLES OF GOOD TUTORING" in prompt
        assert "blue decorative border" in prompt  # Example 1
        assert "screen reader is" in prompt         # Example 2
        assert "volume levels" in prompt            # Example 3

    def test_contains_scope_boundary(self):
        prompt = build_instance_a_prompt()
        assert "STAYING ON TOPIC" in prompt
        assert "outside what I can help" in prompt

    def test_does_not_contain_stage_awareness(self):
        prompt = build_instance_a_prompt()
        assert "STAGE AWARENESS" not in prompt

    def test_does_not_contain_tool_instructions(self):
        prompt = build_instance_a_prompt()
        assert "TOOL USAGE" not in prompt

    def test_does_not_contain_exploration_approach(self):
        prompt = build_instance_a_prompt()
        assert "HOW TO TEACH (EXPLORATION PHASE)" not in prompt

    def test_does_not_contain_eliminated_sections(self):
        prompt = build_instance_a_prompt()
        assert "CLAIM EXTRACTION" not in prompt
        assert "STUDENT STATE DETECTION" not in prompt
        assert "FIVE RESPONSE MODES" not in prompt
        assert "TERMINATION RULES" not in prompt
        assert "GROUNDING RULES" not in prompt
        assert "=== TONE ===" not in prompt

    def test_includes_knowledge_context(self):
        prompt = build_instance_a_prompt(knowledge_context="SC 1.1.1 Non-text Content")
        assert "SC 1.1.1 Non-text Content" in prompt
        assert "KNOWLEDGE BASE CONTEXT" in prompt

    def test_includes_student_context(self):
        prompt = build_instance_a_prompt(student_context="Level: intermediate | Role: developer")
        assert "Level: intermediate" in prompt
        assert "Adapt your vocabulary" in prompt

    def test_empty_contexts_produce_clean_prompt(self):
        prompt = build_instance_a_prompt()
        assert "KNOWLEDGE BASE CONTEXT" not in prompt
        assert "warm, patient tutor" in prompt


class TestInstanceBPrompt:
    """Instance B: Guided Learning — stage-aware with adaptive teaching."""

    def test_contains_role_preamble(self):
        prompt = build_instance_b_prompt()
        assert "warm, patient tutor" in prompt
        assert "TEACHING, not testing" in prompt

    def test_default_stage_uses_intro_approach(self):
        prompt = build_instance_b_prompt()
        assert "HOW TO TEACH (INTRODUCTION PHASE)" in prompt
        assert "HOW TO TEACH (EXPLORATION PHASE)" not in prompt

    def test_exploration_stage_uses_exploration_approach(self):
        prompt = build_instance_b_prompt(current_stage="exploration")
        assert "HOW TO TEACH (EXPLORATION PHASE)" in prompt
        assert "HOW TO TEACH (INTRODUCTION PHASE)" not in prompt

    def test_all_non_exploration_stages_use_intro_approach(self):
        for stage in ["introduction", "readiness_check", "mini_assessment",
                       "final_assessment", "transition"]:
            prompt = build_instance_b_prompt(current_stage=stage)
            assert "HOW TO TEACH (INTRODUCTION PHASE)" in prompt, f"Failed for stage: {stage}"
            assert "HOW TO TEACH (EXPLORATION PHASE)" not in prompt, f"Failed for stage: {stage}"

    def test_exploration_approach_has_socratic_elements(self):
        prompt = build_instance_b_prompt(current_stage="exploration")
        assert "enough context for the student to reason" in prompt
        assert "ONE analytical question" in prompt
        assert "Adapt based on how they respond" in prompt

    def test_intro_approach_has_teach_first_elements(self):
        prompt = build_instance_b_prompt(current_stage="introduction")
        assert "clear, concise explanation" in prompt
        assert "ONE gentle question" in prompt
        assert "natural conversation" in prompt

    def test_contains_misconception_handling(self):
        prompt = build_instance_b_prompt()
        assert "WHEN THE STUDENT SAYS SOMETHING WRONG" in prompt
        assert "log_misconception" in prompt
        assert "resolve_misconception" in prompt

    def test_misconception_is_internal_only(self):
        prompt = build_instance_b_prompt()
        assert "NEVER show this analysis to the student" in prompt

    def test_contains_stage_awareness(self):
        prompt = build_instance_b_prompt()
        assert "STAGE AWARENESS" in prompt
        assert "INTRODUCTION" in prompt
        assert "EXPLORATION" in prompt
        assert "READINESS_CHECK" in prompt
        assert "MINI_ASSESSMENT" in prompt
        assert "FINAL_ASSESSMENT" in prompt
        assert "TRANSITION" in prompt
        assert "application manages stage transitions" in prompt

    def test_stage_awareness_references_teaching_styles(self):
        prompt = build_instance_b_prompt()
        assert "TEACH-FIRST" in prompt
        assert "SOCRATIC" in prompt

    def test_contains_scope_rules(self):
        prompt = build_instance_b_prompt()
        assert "STAYING ON TOPIC" in prompt
        assert "Q&A chatbot" in prompt

    def test_contains_few_shot_examples(self):
        prompt = build_instance_b_prompt()
        assert "EXAMPLES OF GOOD TUTORING" in prompt
        assert "INTRODUCTION PHASE" in prompt
        assert "EXPLORATION PHASE" in prompt
        assert "blue decorative border" in prompt   # Example 1
        assert "company logo" in prompt             # Example 4
        assert "stock ticker" in prompt             # Example 5

    def test_contains_tool_instructions(self):
        prompt = build_instance_b_prompt()
        assert "TOOL USAGE" in prompt
        assert "log_misconception" in prompt
        assert "record_assessment_answer" in prompt
        assert "WHEN TO READ STATE" in prompt
        assert "WHEN TO WRITE STATE" in prompt
        assert "WHEN TO JUST RESPOND" in prompt

    def test_does_not_contain_eliminated_sections(self):
        prompt = build_instance_b_prompt()
        assert "CLAIM EXTRACTION" not in prompt
        assert "STUDENT STATE DETECTION" not in prompt
        assert "FIVE RESPONSE MODES" not in prompt
        assert "TERMINATION RULES" not in prompt
        assert "GROUNDING RULES" not in prompt
        assert "=== TONE ===" not in prompt
        assert "SCOPE BOUNDARIES" not in prompt

    def test_misconception_before_stage_awareness(self):
        prompt = build_instance_b_prompt()
        misc_pos = prompt.index("WHEN THE STUDENT SAYS SOMETHING WRONG")
        stage_pos = prompt.index("STAGE AWARENESS")
        assert misc_pos < stage_pos

    def test_tool_instructions_at_end(self):
        prompt = build_instance_b_prompt()
        tool_pos = prompt.index("TOOL USAGE")
        # Tool instructions should be after the context block
        assert tool_pos > prompt.index("CURRENT STAGE")

    def test_includes_current_stage(self):
        prompt = build_instance_b_prompt(current_stage="exploration")
        assert "CURRENT STAGE: EXPLORATION" in prompt

    def test_includes_active_objective(self):
        prompt = build_instance_b_prompt(active_objective="Apply alt text to images")
        assert "ACTIVE OBJECTIVE: Apply alt text to images" in prompt

    def test_includes_student_context(self):
        prompt = build_instance_b_prompt(
            student_context="MASTERY STATE:\n  obj-1: in_progress"
        )
        assert "MASTERY STATE" in prompt

    def test_includes_knowledge_context(self):
        prompt = build_instance_b_prompt(
            knowledge_context="Quiz Q47: decorative images"
        )
        assert "Quiz Q47: decorative images" in prompt
        assert "wrong-answer feedback" in prompt


class TestPromptTokenBudget:
    """Verify prompts stay within reasonable token bounds."""

    def test_instance_a_base_size(self):
        """Base prompt (no context) should be under 3000 tokens (~12000 chars)."""
        prompt = build_instance_a_prompt()
        assert len(prompt) < 12000, f"Instance A base prompt is {len(prompt)} chars — may be too large"

    def test_instance_b_base_size(self):
        """Base prompt (no context) should be under 4500 tokens (~18000 chars)."""
        prompt = build_instance_b_prompt()
        assert len(prompt) < 18000, f"Instance B base prompt is {len(prompt)} chars — may be too large"

    def test_instance_a_with_contexts(self):
        """With typical context, should stay under 4000 tokens (~16000 chars)."""
        prompt = build_instance_a_prompt(
            knowledge_context="x" * 3000,
            student_context="y" * 500,
        )
        assert len(prompt) < 16000

    def test_instance_b_with_contexts(self):
        """With typical context, should stay under 5000 tokens (~22000 chars)."""
        prompt = build_instance_b_prompt(
            knowledge_context="x" * 3000,
            student_context="y" * 500,
            current_stage="exploration",
            active_objective="Apply alt text to images",
        )
        assert len(prompt) < 22000
