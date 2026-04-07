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
    build_instance_a_prompt,
    build_instance_b_prompt,
    TUTOR_SYSTEM_PROMPT,
    CONCEPT_DECOMPOSITION_PROMPT,
    RETRIEVAL_PLANNER_PROMPT,
    TOOL_CALL_EXTRACTION_PROMPT,
    AGENT_TOOL_INSTRUCTIONS,
    format_teaching_plan,
)

__all__ = [
    "build_instance_a_prompt",
    "build_instance_b_prompt",
    "TUTOR_SYSTEM_PROMPT",
    "CONCEPT_DECOMPOSITION_PROMPT",
    "RETRIEVAL_PLANNER_PROMPT",
    "TOOL_CALL_EXTRACTION_PROMPT",
    "AGENT_TOOL_INSTRUCTIONS",
    "format_teaching_plan",
]
