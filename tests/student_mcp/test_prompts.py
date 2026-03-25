"""
Unit tests for Socratic tutoring prompt builders.

Verifies that the prompt templates assemble correctly and contain
the expected components from the research sources.
"""

import pytest
from question_app.services.tutor.prompts.socratic_tutor import (
    build_instance_a_prompt,
    build_instance_b_prompt,
    COGNITIVE_STATES,
    RESPONSE_MODES,
    TERMINATION_RULES,
    ANTI_PATTERNS,
    FEW_SHOT_EXAMPLES,
    STAGE_AWARENESS,
    EVAL_OUTPUT_SCHEMA,
)


class TestInstanceAPrompt:
    """Instance A: General Q&A — Socratic without stage awareness."""

    def test_contains_cognitive_states(self):
        prompt = build_instance_a_prompt()
        assert "CONFUSED_ABOUT_PROBLEM" in prompt
        assert "MISSING_PREREQUISITES" in prompt
        assert "DISENGAGED" in prompt
        assert "CORRECT" in prompt

    def test_contains_response_modes(self):
        prompt = build_instance_a_prompt()
        assert "REVIEW:" in prompt
        assert "GUIDANCE:" in prompt
        assert "RECTIFICATION:" in prompt
        assert "SUMMARIZATION:" in prompt

    def test_contains_termination_rules(self):
        prompt = build_instance_a_prompt()
        assert "3 failed attempts" in prompt
        assert "just tell me" in prompt

    def test_contains_anti_patterns(self):
        prompt = build_instance_a_prompt()
        assert "Never ask more than ONE question" in prompt
        assert "Never keep probing" in prompt

    def test_contains_all_four_examples(self):
        prompt = build_instance_a_prompt()
        assert "blue decorative border" in prompt  # Example 1
        assert "screen reader is" in prompt         # Example 2
        assert "company logo" in prompt             # Example 3
        assert "idk, just tell me" in prompt        # Example 4

    def test_does_not_contain_stage_awareness(self):
        prompt = build_instance_a_prompt()
        assert "STAGE AWARENESS" not in prompt
        assert "STRUCTURED OUTPUT" not in prompt

    def test_contains_off_topic_boundary(self):
        prompt = build_instance_a_prompt()
        assert "outside what I can help with" in prompt

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
        assert "Socratic tutor" in prompt


class TestInstanceBPrompt:
    """Instance B: Guided Learning — stage-aware with eval JSON."""

    def test_contains_all_shared_components(self):
        prompt = build_instance_b_prompt()
        assert "CONFUSED_ABOUT_PROBLEM" in prompt
        assert "REVIEW:" in prompt
        assert "3 failed attempts" in prompt
        assert "blue decorative border" in prompt

    def test_contains_stage_awareness(self):
        prompt = build_instance_b_prompt()
        assert "STAGE AWARENESS" in prompt
        assert "ONBOARDING" in prompt
        assert "INTRODUCTION" in prompt
        assert "EXPLORATION" in prompt
        assert "READINESS_CHECK" in prompt
        assert "MINI_ASSESSMENT" in prompt
        assert "FINAL_ASSESSMENT" in prompt
        assert "TRANSITION" in prompt

    def test_contains_eval_output_schema(self):
        prompt = build_instance_b_prompt()
        assert "STRUCTURED OUTPUT" in prompt
        assert "detected_state" in prompt
        assert "response_mode" in prompt
        assert "stage_recommendation" in prompt
        assert "mastery_evidence" in prompt
        assert "misconceptions_detected" in prompt
        assert "confidence" in prompt

    def test_contains_scope_boundaries(self):
        prompt = build_instance_b_prompt()
        assert "SCOPE BOUNDARIES" in prompt
        assert "OFF_TOPIC" in prompt
        assert "OUT_OF_SCOPE" in prompt
        assert "Q&A chatbot" in prompt

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
        assert "Target known misconceptions" in prompt

    def test_includes_knowledge_context(self):
        prompt = build_instance_b_prompt(
            knowledge_context="Quiz Q47: decorative images"
        )
        assert "Quiz Q47: decorative images" in prompt
        assert "wrong-answer feedback" in prompt


class TestPromptTokenBudget:
    """Verify prompts stay within reasonable token bounds."""

    def test_instance_a_base_size(self):
        """Base prompt (no context) should be under 2000 tokens (~8000 chars)."""
        prompt = build_instance_a_prompt()
        assert len(prompt) < 8000, f"Instance A base prompt is {len(prompt)} chars — may be too large"

    def test_instance_b_base_size(self):
        """Base prompt (no context) should be under 3000 tokens (~12000 chars)."""
        prompt = build_instance_b_prompt()
        assert len(prompt) < 12000, f"Instance B base prompt is {len(prompt)} chars — may be too large"

    def test_instance_a_with_contexts(self):
        """With typical context, should stay under 4000 tokens (~16000 chars)."""
        prompt = build_instance_a_prompt(
            knowledge_context="x" * 3000,
            student_context="y" * 500,
        )
        assert len(prompt) < 16000

    def test_instance_b_with_contexts(self):
        """With typical context, should stay under 5000 tokens (~20000 chars)."""
        prompt = build_instance_b_prompt(
            knowledge_context="x" * 3000,
            student_context="y" * 500,
            current_stage="exploration",
            active_objective="Apply alt text to images",
        )
        assert len(prompt) < 20000
