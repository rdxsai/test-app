"""
Tutoring prompt templates.

Three prompt systems:
  - TUTOR_SYSTEM_PROMPT: Socratic tutor for Instance B (guided learning)
  - CONCEPT_DECOMPOSITION_PROMPT: Instructional designer for teaching plans
  - graph prompts: graph planning, retrieval, synthesis, and validation

Instance A (Q&A) retains the older teach-first approach.
Instance B (Guided Learning) uses graph-grounded teaching content.
"""

from .socratic_tutor import (
    build_assessment_reflector_prompt,
    build_guided_reflector_prompt,
    build_turn_analyzer_prompt,
    build_instance_a_prompt,
    build_instance_b_prompt,
    get_instance_b_prompt_registry,
    ASSESSMENT_REFLECTOR_PROMPT,
    GUIDED_REFLECTOR_PROMPT,
    TURN_ANALYZER_PROMPT,
    TUTOR_SYSTEM_PROMPT,
    CONCEPT_DECOMPOSITION_PROMPT,
    AGENT_TOOL_INSTRUCTIONS,
    FIRST_TURN_INSTRUCTION,
    format_lesson_state,
    format_misconception_state,
    format_pacing_state,
    format_teaching_plan,
    format_teaching_plan_for_display,
)
from .graph import (
    EDGE_INTEGRATION_SYNTHESIS_PROMPT,
    GROUNDING_VALIDATOR_PROMPT,
    NODE_CONTENT_SYNTHESIS_PROMPT,
    NODE_EVIDENCE_FINALIZATION_PROMPT,
    NODE_EVIDENCE_RETRIEVAL_PLANNING_PROMPT,
    NODE_EVIDENCE_RETRIEVAL_TOOLCALL_PROMPT,
    TEACHING_GRAPH_PLANNER_PROMPT,
)

__all__ = [
    "build_assessment_reflector_prompt",
    "build_guided_reflector_prompt",
    "build_turn_analyzer_prompt",
    "build_instance_a_prompt",
    "build_instance_b_prompt",
    "get_instance_b_prompt_registry",
    "ASSESSMENT_REFLECTOR_PROMPT",
    "GUIDED_REFLECTOR_PROMPT",
    "TURN_ANALYZER_PROMPT",
    "TUTOR_SYSTEM_PROMPT",
    "CONCEPT_DECOMPOSITION_PROMPT",
    "AGENT_TOOL_INSTRUCTIONS",
    "FIRST_TURN_INSTRUCTION",
    "format_lesson_state",
    "format_misconception_state",
    "format_pacing_state",
    "format_teaching_plan",
    "format_teaching_plan_for_display",
    "EDGE_INTEGRATION_SYNTHESIS_PROMPT",
    "GROUNDING_VALIDATOR_PROMPT",
    "NODE_CONTENT_SYNTHESIS_PROMPT",
    "NODE_EVIDENCE_FINALIZATION_PROMPT",
    "NODE_EVIDENCE_RETRIEVAL_PLANNING_PROMPT",
    "NODE_EVIDENCE_RETRIEVAL_TOOLCALL_PROMPT",
    "TEACHING_GRAPH_PLANNER_PROMPT",
]
