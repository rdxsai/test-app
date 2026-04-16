"""
Tutoring prompt templates.

Three prompt systems:
  - TUTOR_SYSTEM_PROMPT: Socratic tutor for Instance B (guided learning)
  - CONCEPT_DECOMPOSITION_PROMPT: Instructional designer for teaching plans
  - RETRIEVAL_PLANNER_PROMPT: Retrieval planner for evidence pack curation

Instance A (Q&A) retains the older teach-first approach.
Instance B (Guided Learning) uses TUTOR_SYSTEM_PROMPT with plan + evidence.
"""

from .socratic_tutor import (
    build_assessment_reflector_prompt,
    build_guided_reflector_prompt,
    build_guided_retrieval_agent_prompt,
    build_turn_analyzer_prompt,
    build_instance_a_prompt,
    build_instance_b_prompt,
    get_instance_b_prompt_registry,
    ASSESSMENT_REFLECTOR_PROMPT,
    GUIDED_RETRIEVAL_AGENT_PROMPT,
    GUIDED_REFLECTOR_PROMPT,
    TURN_ANALYZER_PROMPT,
    TUTOR_SYSTEM_PROMPT,
    CONCEPT_DECOMPOSITION_PROMPT,
    RETRIEVAL_PLANNER_PROMPT,
    TOOL_CALL_EXTRACTION_PROMPT,
    AGENT_TOOL_INSTRUCTIONS,
    FIRST_TURN_INSTRUCTION,
    format_lesson_state,
    format_misconception_state,
    format_pacing_state,
    format_teaching_plan,
    format_teaching_plan_for_display,
)

__all__ = [
    "build_assessment_reflector_prompt",
    "build_guided_reflector_prompt",
    "build_guided_retrieval_agent_prompt",
    "build_turn_analyzer_prompt",
    "build_instance_a_prompt",
    "build_instance_b_prompt",
    "get_instance_b_prompt_registry",
    "ASSESSMENT_REFLECTOR_PROMPT",
    "GUIDED_RETRIEVAL_AGENT_PROMPT",
    "GUIDED_REFLECTOR_PROMPT",
    "TURN_ANALYZER_PROMPT",
    "TUTOR_SYSTEM_PROMPT",
    "CONCEPT_DECOMPOSITION_PROMPT",
    "RETRIEVAL_PLANNER_PROMPT",
    "TOOL_CALL_EXTRACTION_PROMPT",
    "AGENT_TOOL_INSTRUCTIONS",
    "FIRST_TURN_INSTRUCTION",
    "format_lesson_state",
    "format_misconception_state",
    "format_pacing_state",
    "format_teaching_plan",
    "format_teaching_plan_for_display",
]
