"""
Socratic tutoring prompt templates.

Research-backed prompt engineering for Socratic teaching, extracted from:
  - SocraticLM (NeurIPS 2024): 6 cognitive states
  - SocraticMATH (CIKM 2024): 4 response modes
  - Edward Chang (2023): Anti-patterns and termination rules

Two prompt variants:
  - Instance A: General Q&A (stateless, no stage awareness)
  - Instance B: Guided learning (stage-aware, structured eval output)
"""

from .socratic_tutor import (
    build_instance_a_prompt,
    build_instance_b_prompt,
)

__all__ = ["build_instance_a_prompt", "build_instance_b_prompt"]
