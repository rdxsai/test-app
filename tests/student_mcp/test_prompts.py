"""
Unit tests for stage-adaptive tutoring prompt builders.

Verifies that the prompt templates assemble correctly with the
stage-dependent teaching approach swap.
"""

import pytest
from question_app.services.tutor.prompts.socratic_tutor import (
    build_assessment_reflector_prompt,
    build_guided_reflector_prompt,
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
    """Instance B: Guided Learning — Socratic tutor with plan + evidence."""

    def test_contains_tutor_identity(self):
        prompt = build_instance_b_prompt()
        assert "Socratic AI tutor" in prompt
        assert "web accessibility" in prompt

    def test_contains_teaching_rules(self):
        prompt = build_instance_b_prompt()
        assert "NON-NEGOTIABLE TEACHING RULES" in prompt
        assert "Teach from the teaching plan" in prompt
        assert "Teach from the validated evidence pack" in prompt
        assert "Socratic teaching, not interrogation" in prompt

    def test_contains_teaching_rhythm(self):
        prompt = build_instance_b_prompt()
        assert "TEACHING RHYTHM" in prompt
        assert "Anchor" in prompt
        assert "Listen first" in prompt
        assert "Consolidate" in prompt
        assert "Move forward" in prompt

    def test_contains_pacing_rules(self):
        prompt = build_instance_b_prompt()
        assert "PACING" in prompt
        assert "ONE concept per turn" in prompt

    def test_contains_questioning_guide(self):
        prompt = build_instance_b_prompt()
        assert "QUESTIONING GUIDE" in prompt
        assert "prediction" in prompt
        assert "classification" in prompt
        assert "comparison" in prompt

    def test_contains_balancing_rules(self):
        prompt = build_instance_b_prompt()
        assert "BALANCING EXPLANATION AND QUESTIONING" in prompt
        assert "Default to questioning" in prompt

    def test_contains_adaptation_rules(self):
        prompt = build_instance_b_prompt()
        assert "ADAPTING TO LEARNER RESPONSES" in prompt
        assert "Strong understanding" in prompt
        assert "Partial understanding" in prompt
        assert "Confused" in prompt
        assert "Guessing" in prompt
        assert "Misconception" in prompt

    def test_contains_misconception_handling(self):
        prompt = build_instance_b_prompt()
        assert "WHEN THE STUDENT SAYS SOMETHING WRONG" in prompt
        assert "NEVER show this analysis to the student" in prompt

    def test_contains_scope_rules(self):
        prompt = build_instance_b_prompt()
        assert "STAYING ON TOPIC" in prompt

    def test_contains_evidence_pack_rules(self):
        prompt = build_instance_b_prompt()
        assert "USE OF EVIDENCE PACK" in prompt
        assert "short instructional paraphrases" in prompt

    def test_contains_priority_order(self):
        prompt = build_instance_b_prompt()
        assert "PRIORITY ORDER" in prompt
        assert "accuracy to evidence pack" in prompt
        assert "alignment with teaching plan" in prompt

    def test_contains_output_behavior(self):
        prompt = build_instance_b_prompt()
        assert "NEVER ask more than ONE question per response" in prompt
        assert "natural conversation" in prompt

    def test_does_not_contain_old_sections(self):
        """Old modular constants should not appear in Instance B."""
        prompt = build_instance_b_prompt()
        assert "CLAIM EXTRACTION" not in prompt
        assert "STUDENT STATE DETECTION" not in prompt
        assert "FIVE RESPONSE MODES" not in prompt
        assert "TERMINATION RULES" not in prompt
        assert "GROUNDING RULES" not in prompt
        assert "=== TONE ===" not in prompt
        assert "SCOPE BOUNDARIES" not in prompt
        # Deferred sections (not in v2 prompt)
        assert "STAGE AWARENESS" not in prompt
        assert "EXAMPLES OF GOOD TUTORING" not in prompt
        assert "TOOL USAGE" not in prompt

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
        assert "VALIDATED EVIDENCE PACK" in prompt
        assert "Ground all factual claims" in prompt

    def test_includes_teaching_plan(self):
        prompt = build_instance_b_prompt(teaching_plan="1. objective_text\nTest plan")
        assert "TEACHING PLAN:" in prompt

    def test_no_stage_dependent_approach_swap(self):
        """New prompt uses a single adaptive approach, not stage-dependent swap."""
        intro = build_instance_b_prompt(current_stage="introduction")
        explore = build_instance_b_prompt(current_stage="exploration")
        # Both should have the same TUTOR_SYSTEM_PROMPT base
        assert "TEACHING RHYTHM" in intro
        assert "TEACHING RHYTHM" in explore
        # Neither should have the old stage-dependent approaches
        assert "HOW TO TEACH (INTRODUCTION PHASE)" not in intro
        assert "HOW TO TEACH (EXPLORATION PHASE)" not in explore


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


class TestReflectorPrompts:
    """Structured reflector prompts for guided-tutor bookkeeping."""

    def test_guided_reflector_contains_json_contract(self):
        prompt = build_guided_reflector_prompt(
            current_stage="exploration",
            active_objective="Apply alt text to images",
        )
        assert "stage_action" in prompt
        assert "objective_memory_patch" in prompt
        assert "learner_memory_patch" in prompt
        assert "CURRENT STAGE: EXPLORATION" in prompt

    def test_assessment_reflector_contains_correctness_contract(self):
        prompt = build_assessment_reflector_prompt(
            current_stage="mini_assessment",
            active_objective="Apply alt text to images",
        )
        assert "is_correct" in prompt
        assert "rationale" in prompt
        assert "ACTIVE OBJECTIVE: Apply alt text to images" in prompt
