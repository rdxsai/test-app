"""
Evaluation pipeline for AI-generated content.

Stream 2: RAG pipeline metrics (Faithfulness, Relevancy, Context Precision)
Stream 3: Computed text metrics (readability, ROUGE-L, BLEU, consistency)

Streams 1 (custom rubrics) and 4 (human feedback) are deferred.
"""

from .repository import EvalRepository
from .thresholds import EvalVerdict, classify_score

__all__ = ["EvalRepository", "EvalVerdict", "classify_score"]
