"""
Evaluation scoring thresholds and verdict classification.
"""

from enum import Enum


class EvalVerdict(str, Enum):
    PASS = "pass"       # >= 0.8
    REVIEW = "review"   # >= 0.6
    FAIL = "fail"       # < 0.6


THRESHOLDS = {
    "pass": 0.8,
    "review": 0.6,
}


def classify_score(score: float) -> EvalVerdict:
    """Classify a 0-1 score into pass/review/fail."""
    if score >= THRESHOLDS["pass"]:
        return EvalVerdict.PASS
    elif score >= THRESHOLDS["review"]:
        return EvalVerdict.REVIEW
    return EvalVerdict.FAIL
