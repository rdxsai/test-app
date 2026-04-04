"""
Stage-adaptive tutoring prompt templates.

Two teaching styles that shift by stage:
  - Introduction: teach-first (explain, check, respond)
  - Exploration: Socratic (set up, question, adapt)

Two prompt variants:
  - Instance A: General Q&A (teach-first, no stages or tools)
  - Instance B: Guided learning (stage-aware with adaptive teaching approach)
"""

from .socratic_tutor import (
    build_instance_a_prompt,
    build_instance_b_prompt,
    CONCEPT_DECOMPOSITION_PROMPT,
    AGENT_TOOL_INSTRUCTIONS,
    format_teaching_plan,
)

__all__ = [
    "build_instance_a_prompt",
    "build_instance_b_prompt",
    "CONCEPT_DECOMPOSITION_PROMPT",
    "AGENT_TOOL_INSTRUCTIONS",
    "format_teaching_plan",
]
