"""
Evaluation API — endpoints for viewing eval results and RAG samples.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from pydantic import BaseModel

from ..core import get_logger
from ..services.eval.repository import EvalRepository
from ..services.eval.computed_metrics import ComputedMetrics

logger = get_logger(__name__)
router = APIRouter(prefix="/eval", tags=["evaluation"])

# Lazy-init repository (created on first request)
_repo: Optional[EvalRepository] = None


def _get_repo() -> EvalRepository:
    global _repo
    if _repo is None:
        _repo = EvalRepository()
    return _repo


# ------------------------------------------------------------------
# Eval log endpoints
# ------------------------------------------------------------------

@router.get("/logs")
async def list_eval_logs(
    content_type: Optional[str] = None,
    content_id: Optional[str] = None,
    metric_name: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
):
    """List evaluation results with optional filters."""
    repo = _get_repo()
    logs = repo.get_eval_logs(
        content_type=content_type, content_id=content_id,
        metric_name=metric_name, limit=limit, offset=offset,
    )
    return {"logs": logs, "count": len(logs)}


@router.get("/logs/{content_id}")
async def get_eval_logs_for_content(content_id: str):
    """Get all evaluation results for a specific content item."""
    repo = _get_repo()
    logs = repo.get_eval_logs(content_id=content_id, limit=100)
    if not logs:
        raise HTTPException(status_code=404, detail="No eval logs found for this content")
    return {"content_id": content_id, "logs": logs}


@router.get("/summary/{content_type}")
async def get_eval_summary(
    content_type: str,
    metric_name: Optional[str] = None,
):
    """Aggregated eval summary (avg, min, max, count) per metric."""
    repo = _get_repo()
    summary = repo.get_eval_summary(content_type, metric_name=metric_name)
    return summary


# ------------------------------------------------------------------
# RAG sample endpoints
# ------------------------------------------------------------------

@router.get("/rag/samples")
async def list_rag_samples(
    evaluated: Optional[bool] = None,
    limit: int = Query(default=50, le=200),
):
    """List captured RAG evaluation samples."""
    repo = _get_repo()
    samples = repo.get_rag_samples(evaluated=evaluated, limit=limit)
    return {"samples": samples, "count": len(samples)}


@router.get("/rag/samples/{sample_id}")
async def get_rag_sample(sample_id: str):
    """Get a single RAG evaluation sample."""
    repo = _get_repo()
    sample = repo.get_rag_sample(sample_id)
    if not sample:
        raise HTTPException(status_code=404, detail="RAG sample not found")
    return sample


# ------------------------------------------------------------------
# Computed metrics endpoints (Stream 3)
# ------------------------------------------------------------------

@router.post("/compute/readability/rag/{sample_id}")
async def compute_readability_for_rag_sample(sample_id: str):
    """Compute readability metrics for a captured RAG response."""
    repo = _get_repo()
    sample = repo.get_rag_sample(sample_id)
    if not sample:
        raise HTTPException(status_code=404, detail="RAG sample not found")

    scores = ComputedMetrics.readability_score(sample["response"])

    # Log each metric
    for metric_name, value in scores.items():
        repo.log_eval(
            content_type="rag_response",
            content_id=sample_id,
            metric_name=metric_name,
            metric_value=value,
            evaluator="computed",
        )

    return {"sample_id": sample_id, "readability": scores}


@router.post("/compute/readability/feedback/{answer_id}")
async def compute_readability_for_feedback(answer_id: str):
    """Compute readability metrics for answer feedback text."""
    repo = _get_repo()
    # Load feedback from main DB
    from ..services.database import get_database_manager
    db = get_database_manager()
    answers = db.get_answers_for_questions(answer_id)
    if not answers:
        # Try loading as answer ID directly
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, feedback_text FROM answer WHERE id = %s", (answer_id,))
                row = cur.fetchone()
        if not row or not row.get("feedback_text"):
            raise HTTPException(status_code=404, detail="Answer or feedback not found")
        text = row["feedback_text"]
    else:
        text = answers[0].get("feedback_text", "")

    if not text:
        raise HTTPException(status_code=404, detail="No feedback text found")

    scores = ComputedMetrics.readability_score(text)

    for metric_name, value in scores.items():
        repo.log_eval(
            content_type="feedback",
            content_id=answer_id,
            metric_name=metric_name,
            metric_value=value,
            evaluator="computed",
        )

    return {"answer_id": answer_id, "readability": scores}


class SimilarityRequest(BaseModel):
    hypothesis: str
    reference: str


@router.post("/compute/similarity")
async def compute_similarity(data: SimilarityRequest):
    """Compute ROUGE-L and BLEU-1 between two texts."""
    rouge = ComputedMetrics.rouge_l(data.hypothesis, data.reference)
    bleu = ComputedMetrics.bleu_1(data.hypothesis, data.reference)
    return {
        "rouge_l": round(rouge, 4),
        "bleu_1": round(bleu, 4),
    }
