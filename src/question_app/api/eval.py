"""
Evaluation API — endpoints for viewing eval results and RAG samples.
"""

import logging
from typing import Any, Dict, List, Optional

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


def _build_rag_sample_analysis(sample: dict) -> dict:
    metric_map = sample.get("eval_metrics_by_name", {})
    return {
        "sample": sample,
        "signals": {
            "retrieval_context_count": metric_map.get("retrieval_context_count"),
            "retrieval_query_overlap": metric_map.get("retrieval_query_overlap"),
            "wcag_context_used": metric_map.get("wcag_context_used"),
            "response_wcag_citation_present": metric_map.get("response_wcag_citation_present"),
            "response_wcag_citation_grounded": metric_map.get("response_wcag_citation_grounded"),
        },
    }


def _extract_case_meta(sample: dict) -> dict:
    metric_map = sample.get("eval_metrics_by_name", {})
    details_sources = [
        payload.get("details", {})
        for payload in metric_map.values()
        if isinstance(payload, dict)
    ]
    category = next((d.get("category") for d in details_sources if d.get("category")), None)
    difficulty = next((d.get("difficulty") for d in details_sources if d.get("difficulty")), None)
    expected_wcag_refs = next(
        (d.get("expected_wcag_refs") for d in details_sources if d.get("expected_wcag_refs") is not None),
        [],
    )
    benchmark_item_id = sample.get("session_id") or next(
        (d.get("benchmark_item_id") for d in details_sources if d.get("benchmark_item_id")),
        sample.get("id"),
    )
    return {
        "benchmark_item_id": benchmark_item_id,
        "category": category,
        "difficulty": difficulty,
        "expected_wcag_refs": expected_wcag_refs,
    }


def _compact_case_analysis(sample: dict) -> dict:
    metric_map = sample.get("eval_metrics_by_name", {})
    meta = _extract_case_meta(sample)
    case_pass_signal = metric_map.get("benchmark_case_pass") or {}
    return {
        "sample_id": sample.get("id"),
        "benchmark_item_id": meta["benchmark_item_id"],
        "category": meta["category"],
        "difficulty": meta["difficulty"],
        "query": sample.get("query"),
        "intent": sample.get("intent"),
        "expected_wcag_refs": meta["expected_wcag_refs"],
        "response": sample.get("response"),
        "retrieved_contexts": sample.get("retrieved_contexts", []),
        "ground_truth": sample.get("ground_truth"),
        "signals": {
            "judge_overall": metric_map.get("benchmark_judge_overall"),
            "judge_correctness": metric_map.get("benchmark_judge_correctness"),
            "judge_wcag_alignment": metric_map.get("benchmark_judge_wcag_alignment"),
            "must_include_coverage": metric_map.get("benchmark_judge_must_include_coverage"),
            "must_not_do_compliance": metric_map.get("benchmark_judge_must_not_do_compliance"),
            "expected_wcag_ref_recall": metric_map.get("benchmark_expected_wcag_ref_recall"),
            "wcag_context_ref_recall": metric_map.get("benchmark_wcag_context_ref_recall"),
            "intent_match": metric_map.get("benchmark_intent_match"),
            "quiz_retrieval_expectation_met": metric_map.get("benchmark_quiz_retrieval_expectation_met"),
            "retrieval_target_coverage": metric_map.get("benchmark_retrieval_target_coverage"),
            "case_pass": case_pass_signal,
            "latency_seconds": metric_map.get("benchmark_latency_seconds"),
        },
        "case_pass_reasons": list((case_pass_signal.get("details") or {}).get("reasons", [])),
    }


def _build_metric_deltas(
    baseline_summary: dict,
    candidate_summary: dict,
) -> Dict[str, Dict[str, float]]:
    baseline_metrics = baseline_summary.get("metrics", {})
    candidate_metrics = candidate_summary.get("metrics", {})
    metric_names = sorted(set(baseline_metrics) | set(candidate_metrics))
    deltas: Dict[str, Dict[str, float]] = {}
    for name in metric_names:
        baseline_avg = float((baseline_metrics.get(name) or {}).get("avg", 0.0))
        candidate_avg = float((candidate_metrics.get(name) or {}).get("avg", 0.0))
        deltas[name] = {
            "baseline_avg": round(baseline_avg, 4),
            "candidate_avg": round(candidate_avg, 4),
            "delta": round(candidate_avg - baseline_avg, 4),
        }
    return deltas


def _build_instance_a_batch_analysis(
    batch_id: str,
    summary: dict,
    samples: List[dict],
) -> dict:
    cases = [_compact_case_analysis(sample) for sample in samples]
    cases.sort(
        key=lambda case: (
            float((case["signals"].get("judge_overall") or {}).get("value", 0.0)),
            float((case["signals"].get("judge_wcag_alignment") or {}).get("value", 0.0)),
            -float((case["signals"].get("latency_seconds") or {}).get("value", 0.0)),
        )
    )

    by_category: Dict[str, Dict[str, Any]] = {}
    for case in cases:
        category = case.get("category") or "uncategorized"
        bucket = by_category.setdefault(
            category,
            {
                "case_count": 0,
                "pass_count": 0,
                "avg_judge_overall": 0.0,
                "avg_wcag_alignment": 0.0,
                "avg_expected_wcag_ref_recall": 0.0,
                "avg_retrieval_target_coverage": 0.0,
            },
        )
        bucket["case_count"] += 1
        bucket["pass_count"] += int(
            float((case["signals"].get("case_pass") or {}).get("value", 0.0)) >= 1.0
        )
        bucket["avg_judge_overall"] += float(
            (case["signals"].get("judge_overall") or {}).get("value", 0.0)
        )
        bucket["avg_wcag_alignment"] += float(
            (case["signals"].get("judge_wcag_alignment") or {}).get("value", 0.0)
        )
        bucket["avg_expected_wcag_ref_recall"] += float(
            (case["signals"].get("expected_wcag_ref_recall") or {}).get("value", 0.0)
        )
        bucket["avg_retrieval_target_coverage"] += float(
            (case["signals"].get("retrieval_target_coverage") or {}).get("value", 0.0)
        )

    for bucket in by_category.values():
        count = max(bucket["case_count"], 1)
        bucket["pass_rate"] = round(bucket["pass_count"] / count, 4)
        bucket["avg_judge_overall"] = round(bucket["avg_judge_overall"] / count, 4)
        bucket["avg_wcag_alignment"] = round(bucket["avg_wcag_alignment"] / count, 4)
        bucket["avg_expected_wcag_ref_recall"] = round(
            bucket["avg_expected_wcag_ref_recall"] / count, 4
        )
        bucket["avg_retrieval_target_coverage"] = round(
            bucket["avg_retrieval_target_coverage"] / count, 4
        )

    weakest_cases = [
        {
            "benchmark_item_id": case["benchmark_item_id"],
            "category": case["category"],
            "query": case["query"],
            "judge_overall": case["signals"].get("judge_overall"),
            "judge_wcag_alignment": case["signals"].get("judge_wcag_alignment"),
            "expected_wcag_ref_recall": case["signals"].get("expected_wcag_ref_recall"),
            "retrieval_target_coverage": case["signals"].get("retrieval_target_coverage"),
            "case_pass": case["signals"].get("case_pass"),
            "case_pass_reasons": case.get("case_pass_reasons", []),
            "latency_seconds": case["signals"].get("latency_seconds"),
        }
        for case in cases[:5]
    ]

    failed_cases = [
        {
            "benchmark_item_id": case["benchmark_item_id"],
            "category": case["category"],
            "query": case["query"],
            "case_pass": case["signals"].get("case_pass"),
            "case_pass_reasons": case.get("case_pass_reasons", []),
            "judge_overall": case["signals"].get("judge_overall"),
            "judge_wcag_alignment": case["signals"].get("judge_wcag_alignment"),
            "retrieval_target_coverage": case["signals"].get("retrieval_target_coverage"),
        }
        for case in cases
        if float((case["signals"].get("case_pass") or {}).get("value", 0.0)) < 1.0
    ]

    return {
        "batch_id": batch_id,
        "case_count": len(cases),
        "pass_count": sum(
            1 for case in cases if float((case["signals"].get("case_pass") or {}).get("value", 0.0)) >= 1.0
        ),
        "pass_rate": round(
            sum(
                float((case["signals"].get("case_pass") or {}).get("value", 0.0))
                for case in cases
            ) / max(len(cases), 1),
            4,
        ),
        "summary": summary,
        "by_category": by_category,
        "weakest_cases": weakest_cases,
        "failed_cases": failed_cases,
        "cases": cases,
    }


def _build_instance_a_batch_comparison(
    baseline: dict,
    candidate: dict,
) -> dict:
    baseline_cases = {
        case["benchmark_item_id"]: case
        for case in baseline.get("cases", [])
    }
    candidate_cases = {
        case["benchmark_item_id"]: case
        for case in candidate.get("cases", [])
    }
    case_ids = sorted(set(baseline_cases) | set(candidate_cases))
    case_deltas = []
    for case_id in case_ids:
        before = baseline_cases.get(case_id, {})
        after = candidate_cases.get(case_id, {})
        before_overall = float(
            ((before.get("signals") or {}).get("judge_overall") or {}).get("value", 0.0)
        )
        after_overall = float(
            ((after.get("signals") or {}).get("judge_overall") or {}).get("value", 0.0)
        )
        before_alignment = float(
            ((before.get("signals") or {}).get("judge_wcag_alignment") or {}).get("value", 0.0)
        )
        after_alignment = float(
            ((after.get("signals") or {}).get("judge_wcag_alignment") or {}).get("value", 0.0)
        )
        before_latency = float(
            ((before.get("signals") or {}).get("latency_seconds") or {}).get("value", 0.0)
        )
        after_latency = float(
            ((after.get("signals") or {}).get("latency_seconds") or {}).get("value", 0.0)
        )
        before_pass = float(
            ((before.get("signals") or {}).get("case_pass") or {}).get("value", 0.0)
        )
        after_pass = float(
            ((after.get("signals") or {}).get("case_pass") or {}).get("value", 0.0)
        )
        before_retrieval_coverage = float(
            ((before.get("signals") or {}).get("retrieval_target_coverage") or {}).get("value", 0.0)
        )
        after_retrieval_coverage = float(
            ((after.get("signals") or {}).get("retrieval_target_coverage") or {}).get("value", 0.0)
        )
        case_deltas.append(
            {
                "benchmark_item_id": case_id,
                "category": after.get("category") or before.get("category"),
                "query": after.get("query") or before.get("query"),
                "judge_overall_delta": round(after_overall - before_overall, 4),
                "judge_wcag_alignment_delta": round(after_alignment - before_alignment, 4),
                "case_pass_delta": round(after_pass - before_pass, 4),
                "retrieval_target_coverage_delta": round(
                    after_retrieval_coverage - before_retrieval_coverage, 4
                ),
                "latency_seconds_delta": round(after_latency - before_latency, 4),
                "baseline_overall": round(before_overall, 4),
                "candidate_overall": round(after_overall, 4),
                "baseline_pass": round(before_pass, 4),
                "candidate_pass": round(after_pass, 4),
                "baseline_pass_reasons": before.get("case_pass_reasons", []),
                "candidate_pass_reasons": after.get("case_pass_reasons", []),
            }
        )

    regressions = sorted(case_deltas, key=lambda case: case["judge_overall_delta"])[:5]
    improvements = sorted(
        case_deltas,
        key=lambda case: case["judge_overall_delta"],
        reverse=True,
    )[:5]

    return {
        "baseline_batch_id": baseline.get("batch_id"),
        "candidate_batch_id": candidate.get("batch_id"),
        "baseline_pass_rate": baseline.get("pass_rate"),
        "candidate_pass_rate": candidate.get("pass_rate"),
        "pass_rate_delta": round(
            float(candidate.get("pass_rate", 0.0)) - float(baseline.get("pass_rate", 0.0)),
            4,
        ),
        "metric_deltas": _build_metric_deltas(
            baseline_summary=baseline.get("summary", {}),
            candidate_summary=candidate.get("summary", {}),
        ),
        "case_deltas": case_deltas,
        "largest_regressions": regressions,
        "largest_improvements": improvements,
    }


# ------------------------------------------------------------------
# Eval log endpoints
# ------------------------------------------------------------------

@router.get("/logs")
async def list_eval_logs(
    content_type: Optional[str] = None,
    content_id: Optional[str] = None,
    metric_name: Optional[str] = None,
    batch_id: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
):
    """List evaluation results with optional filters."""
    repo = _get_repo()
    logs = repo.get_eval_logs(
        content_type=content_type, content_id=content_id,
        metric_name=metric_name, batch_id=batch_id, limit=limit, offset=offset,
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
    batch_id: Optional[str] = None,
):
    """Aggregated eval summary (avg, min, max, count) per metric."""
    repo = _get_repo()
    summary = repo.get_eval_summary(
        content_type,
        metric_name=metric_name,
        batch_id=batch_id,
    )
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


@router.get("/rag/samples/{sample_id}/analysis")
async def get_rag_sample_analysis(sample_id: str):
    """Get a RAG sample plus its attached eval signals in one payload."""
    repo = _get_repo()
    sample = repo.get_rag_sample_with_eval(sample_id)
    if not sample:
        raise HTTPException(status_code=404, detail="RAG sample not found")
    return _build_rag_sample_analysis(sample)


@router.get("/instance-a/batches/{batch_id}/analysis")
async def get_instance_a_batch_analysis(batch_id: str):
    """Return a persisted Instance A benchmark batch with grouped case analysis."""
    repo = _get_repo()
    samples = repo.get_batch_rag_samples_with_eval(batch_id=batch_id, instance="a")
    if not samples:
        raise HTTPException(status_code=404, detail="Instance A batch not found")
    summary = repo.get_eval_summary(
        content_type="rag_sample",
        batch_id=batch_id,
    )
    return _build_instance_a_batch_analysis(batch_id=batch_id, summary=summary, samples=samples)


@router.get("/instance-a/compare")
async def compare_instance_a_batches(
    baseline_batch_id: str,
    candidate_batch_id: str,
):
    """Compare two persisted Instance A benchmark batches."""
    repo = _get_repo()
    baseline_samples = repo.get_batch_rag_samples_with_eval(
        batch_id=baseline_batch_id,
        instance="a",
    )
    candidate_samples = repo.get_batch_rag_samples_with_eval(
        batch_id=candidate_batch_id,
        instance="a",
    )
    if not baseline_samples:
        raise HTTPException(status_code=404, detail="Baseline Instance A batch not found")
    if not candidate_samples:
        raise HTTPException(status_code=404, detail="Candidate Instance A batch not found")

    baseline = _build_instance_a_batch_analysis(
        batch_id=baseline_batch_id,
        summary=repo.get_eval_summary("rag_sample", batch_id=baseline_batch_id),
        samples=baseline_samples,
    )
    candidate = _build_instance_a_batch_analysis(
        batch_id=candidate_batch_id,
        summary=repo.get_eval_summary("rag_sample", batch_id=candidate_batch_id),
        samples=candidate_samples,
    )
    return _build_instance_a_batch_comparison(baseline=baseline, candidate=candidate)


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
