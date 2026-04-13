"""Instance A benchmark runner for frozen gold datasets."""

from __future__ import annotations

import json
import re
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...core import get_logger
from ..general_chat_service import GeneralChatService
from .computed_metrics import ComputedMetrics
from .repository import EvalRepository

logger = get_logger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_DATASET_PATH = PROJECT_ROOT / "eval" / "instance_a_gold_v1.json"


class InstanceABenchmarkRunner:
    """Runs the frozen Instance A benchmark and logs comparable metrics."""

    def __init__(
        self,
        chat_service: GeneralChatService,
        eval_repo: EvalRepository,
        dataset_path: Optional[Path | str] = None,
    ):
        self.chat_service = chat_service
        self.eval_repo = eval_repo
        self.dataset_path = Path(dataset_path) if dataset_path else DEFAULT_DATASET_PATH

    def load_dataset(self) -> Dict[str, Any]:
        with self.dataset_path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict) or "items" not in data:
            raise ValueError(f"Invalid benchmark dataset format: {self.dataset_path}")
        return data

    @staticmethod
    def _extract_success_criteria_refs(text: str) -> List[str]:
        refs = re.findall(r"\b\d\.\d\.\d\b", text or "")
        return sorted(set(refs))

    @staticmethod
    def _tokenize_text(value: str) -> set[str]:
        return {
            token
            for token in re.findall(r"[a-z0-9]+", (value or "").lower())
            if len(token) >= 2
        }

    @staticmethod
    def _parse_judge_response(raw: str) -> Optional[Dict[str, Any]]:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            start = raw.find("{")
            end = raw.rfind("}")
            if start == -1 or end == -1 or end <= start:
                return None
            try:
                return json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                return None

    @staticmethod
    def _build_retrieved_contexts(chunk_payload: List[Dict[str, Any]]) -> List[str]:
        contexts: List[str] = []
        for chunk in chunk_payload:
            source_label = chunk.get("source_label", "").strip()
            summary = chunk.get("summary", "").strip()
            rendered = f"[{source_label}] {summary}".strip()
            if rendered:
                contexts.append(rendered)
        return contexts

    def _score_retrieval_targets(
        self,
        item: Dict[str, Any],
        result: Dict[str, Any],
    ) -> Dict[str, Any]:
        topical_targets = item.get("retrieval_expectation", {}).get("topical_targets", []) or []
        retrieved_chunks = result.get("rag_chunk_payload", []) or []
        if not topical_targets:
            return {
                "coverage": 1.0,
                "lexical_coverage": 1.0,
                "semantic_coverage": None,
                "semantic_relevance": None,
                "matched_targets": [],
                "missing_targets": [],
                "notes": [],
            }

        retrieval_text_parts: List[str] = []
        for chunk in retrieved_chunks:
            retrieval_text_parts.extend(
                [
                    chunk.get("source_label", ""),
                    chunk.get("summary", ""),
                    chunk.get("topic", ""),
                    chunk.get("chunk_type", ""),
                ]
            )
        retrieval_tokens = self._tokenize_text(" ".join(retrieval_text_parts))

        lexical_matches: List[str] = []
        lexical_missing: List[str] = []
        for target in topical_targets:
            target_tokens = self._tokenize_text(str(target))
            if not target_tokens:
                continue
            if target_tokens.issubset(retrieval_tokens):
                lexical_matches.append(str(target))
            else:
                lexical_missing.append(str(target))

        lexical_coverage = len(lexical_matches) / len(topical_targets) if topical_targets else 1.0
        semantic_score = self._judge_retrieval_support(item=item, result=result)
        semantic_coverage = None
        semantic_relevance = None
        matched_targets = lexical_matches
        missing_targets = lexical_missing
        notes: List[str] = []

        if semantic_score:
            semantic_coverage = max(0.0, min(1.0, float(semantic_score.get("coverage", 0.0))))
            semantic_relevance = max(0.0, min(1.0, float(semantic_score.get("relevance", 0.0))))
            if semantic_score.get("matched_targets"):
                matched_targets = [str(target) for target in semantic_score.get("matched_targets", [])]
            if semantic_score.get("missing_targets"):
                missing_targets = [str(target) for target in semantic_score.get("missing_targets", [])]
            notes = [str(note) for note in semantic_score.get("notes", []) if str(note).strip()]

        hybrid_coverage = lexical_coverage
        if semantic_coverage is not None and semantic_relevance is not None:
            hybrid_coverage = max(
                lexical_coverage,
                semantic_coverage * semantic_relevance,
            )

        return {
            "coverage": round(hybrid_coverage, 4),
            "lexical_coverage": round(lexical_coverage, 4),
            "semantic_coverage": round(semantic_coverage, 4) if semantic_coverage is not None else None,
            "semantic_relevance": round(semantic_relevance, 4) if semantic_relevance is not None else None,
            "matched_targets": matched_targets,
            "missing_targets": missing_targets,
            "notes": notes,
        }

    def _judge_retrieval_support(
        self,
        item: Dict[str, Any],
        result: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        if not bool(item.get("retrieval_expectation", {}).get("quiz_should_help")):
            return None

        retrieved_chunks = result.get("rag_chunk_payload", []) or []
        if not retrieved_chunks:
            return {
                "coverage": 0.0,
                "relevance": 0.0,
                "matched_targets": [],
                "missing_targets": item.get("retrieval_expectation", {}).get("topical_targets", []) or [],
                "notes": ["No quiz chunks were retrieved."],
            }

        judge_client = getattr(self.chat_service, "reasoning_client", None)
        if judge_client is None:
            return None

        prompt = {
            "query": item["query"],
            "category": item.get("category"),
            "retrieval_expectation": item.get("retrieval_expectation", {}),
            "retrieved_chunks": [
                {
                    "source_label": chunk.get("source_label", ""),
                    "summary": chunk.get("summary", ""),
                    "topic": chunk.get("topic", ""),
                    "chunk_type": chunk.get("chunk_type", ""),
                    "question_id": chunk.get("question_id", ""),
                    "distance": chunk.get("distance"),
                    "rrf_score": chunk.get("rrf_score"),
                }
                for chunk in retrieved_chunks
            ],
        }
        messages = [
            {
                "role": "system",
                "content": (
                    "You are evaluating retrieval support for a web accessibility benchmark item. "
                    "Judge only whether the retrieved quiz chunks materially support the benchmark query and the expected topical targets. "
                    "Do not judge the final answer. Use semantic meaning, not exact phrase matching. "
                    "Return strict JSON only with schema: "
                    "{\"coverage\":0.0,\"relevance\":0.0,"
                    "\"matched_targets\":[\"target\"],\"missing_targets\":[\"target\"],"
                    "\"notes\":[\"short note\"]}"
                ),
            },
            {
                "role": "user",
                "content": json.dumps(prompt, ensure_ascii=False),
            },
        ]
        try:
            raw = judge_client.chat(
                messages,
                temperature=0.0,
                max_tokens=180,
                reasoning_effort="low",
                response_format={"type": "json_object"},
            )
        except Exception as exc:
            logger.warning(f"Instance A retrieval support judge failed: {exc}")
            return None

        parsed = self._parse_judge_response(raw or "")
        if not parsed:
            logger.warning("Instance A retrieval support judge returned unparseable output")
            return None
        return parsed

    @staticmethod
    def _compute_case_pass(
        item: Dict[str, Any],
        metric_values: Dict[str, float],
    ) -> Dict[str, Any]:
        reasons: List[str] = []
        quiz_should_help = bool(item.get("retrieval_expectation", {}).get("quiz_should_help"))
        wcag_required = bool(item.get("retrieval_expectation", {}).get("wcag_required"))

        if metric_values.get("benchmark_intent_match", 0.0) < 1.0:
            reasons.append("intent_mismatch")
        if metric_values.get("benchmark_forbidden_wcag_ref_compliance", 1.0) < 1.0:
            reasons.append("forbidden_wcag_ref_violation")
        if metric_values.get("benchmark_judge_must_not_do_compliance", 1.0) < 1.0:
            reasons.append("must_not_do_violation")
        if metric_values.get("benchmark_judge_must_include_coverage", 0.0) < 0.9:
            reasons.append("must_include_gap")
        if metric_values.get("benchmark_judge_overall", 0.0) < 0.9:
            reasons.append("low_overall_score")
        if wcag_required and metric_values.get("benchmark_judge_wcag_alignment", 0.0) < 0.85:
            reasons.append("low_wcag_alignment")
        if quiz_should_help and metric_values.get("benchmark_quiz_retrieval_expectation_met", 0.0) < 1.0:
            reasons.append("missing_quiz_retrieval")
        if quiz_should_help and metric_values.get("benchmark_retrieval_target_coverage", 0.0) < 0.34:
            reasons.append("weak_retrieval_target_coverage")

        return {
            "passed": 0.0 if reasons else 1.0,
            "reasons": reasons,
        }

    def _judge_case(
        self,
        item: Dict[str, Any],
        result: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        judge_client = getattr(self.chat_service, "reasoning_client", None)
        if judge_client is None:
            return None

        prompt = {
            "query": item["query"],
            "expected_intent": item["intent_expected"],
            "expected_wcag_refs": item.get("expected_wcag_refs", []),
            "forbidden_wcag_refs": item.get("forbidden_wcag_refs", []),
            "must_include": item.get("must_include", []),
            "must_not_do": item.get("must_not_do", []),
            "reference_answer_outline": item.get("reference_answer_outline", ""),
            "actual_intent": result["intent"],
            "actual_response": result["response"],
            "actual_wcag_refs_in_response": self._extract_success_criteria_refs(result["response"]),
            "actual_wcag_refs_in_context": self._extract_success_criteria_refs(result["wcag_context"]),
            "retrieved_chunks": result["rag_chunk_payload"],
        }
        messages = [
            {
                "role": "system",
                "content": (
                    "You are evaluating a web accessibility benchmark response. "
                    "Return strict JSON with numeric scores from 0.0 to 1.0. "
                    "Be strict and rubric-driven. "
                    "Schema: "
                    "{\"correctness\":0.0,\"must_include_coverage\":0.0,"
                    "\"must_not_do_compliance\":0.0,\"wcag_alignment\":0.0,"
                    "\"helpfulness\":0.0,\"overall\":0.0,"
                    "\"notes\":[\"short note\"]}"
                ),
            },
            {
                "role": "user",
                "content": json.dumps(prompt, ensure_ascii=False),
            },
        ]
        try:
            raw = judge_client.chat(
                messages,
                temperature=0.0,
                max_tokens=250,
                reasoning_effort="low",
                response_format={"type": "json_object"},
            )
        except Exception as exc:
            logger.warning(f"Instance A benchmark judge failed: {exc}")
            return None

        parsed = self._parse_judge_response(raw or "")
        if not parsed:
            logger.warning("Instance A benchmark judge returned unparseable output")
            return None
        return parsed

    def _build_case_metrics(
        self,
        item: Dict[str, Any],
        result: Dict[str, Any],
        latency_seconds: float,
        judge_scores: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        expected_refs = sorted(set(item.get("expected_wcag_refs", [])))
        forbidden_refs = sorted(set(item.get("forbidden_wcag_refs", [])))
        response_refs = self._extract_success_criteria_refs(result["response"])
        wcag_context_refs = self._extract_success_criteria_refs(result["wcag_context"])
        expected_response_matches = sorted(set(expected_refs) & set(response_refs))
        expected_context_matches = sorted(set(expected_refs) & set(wcag_context_refs))
        forbidden_hits = sorted(set(forbidden_refs) & set(response_refs))
        quiz_required = bool(item.get("retrieval_expectation", {}).get("quiz_should_help"))
        retrieved_chunks = result.get("retrieved_chunks", [])
        contexts = self._build_retrieved_contexts(result.get("rag_chunk_payload", []))
        retrieval_target_score = self._score_retrieval_targets(item=item, result=result)

        expected_ref_recall = (
            len(expected_response_matches) / len(expected_refs)
            if expected_refs
            else 1.0
        )
        wcag_context_recall = (
            len(expected_context_matches) / len(expected_refs)
            if expected_refs
            else 1.0
        )
        forbidden_compliance = 1.0 if not forbidden_hits else 0.0
        retrieval_expectation_met = 1.0 if (not quiz_required or contexts) else 0.0

        metrics = [
            {
                "metric_name": "benchmark_intent_match",
                "metric_value": 1.0 if result["intent"] == item["intent_expected"] else 0.0,
                "details": {
                    "benchmark_item_id": item["id"],
                    "expected_intent": item["intent_expected"],
                    "actual_intent": result["intent"],
                },
            },
            {
                "metric_name": "benchmark_expected_wcag_ref_recall",
                "metric_value": round(expected_ref_recall, 4),
                "details": {
                    "benchmark_item_id": item["id"],
                    "expected_refs": expected_refs,
                    "response_refs": response_refs,
                    "matched_refs": expected_response_matches,
                },
            },
            {
                "metric_name": "benchmark_wcag_context_ref_recall",
                "metric_value": round(wcag_context_recall, 4),
                "details": {
                    "benchmark_item_id": item["id"],
                    "expected_refs": expected_refs,
                    "wcag_context_refs": wcag_context_refs,
                    "matched_refs": expected_context_matches,
                },
            },
            {
                "metric_name": "benchmark_forbidden_wcag_ref_compliance",
                "metric_value": forbidden_compliance,
                "details": {
                    "benchmark_item_id": item["id"],
                    "forbidden_refs": forbidden_refs,
                    "response_refs": response_refs,
                    "violations": forbidden_hits,
                },
            },
            {
                "metric_name": "benchmark_quiz_retrieval_expectation_met",
                "metric_value": retrieval_expectation_met,
                "details": {
                    "benchmark_item_id": item["id"],
                    "quiz_should_help": quiz_required,
                    "retrieved_chunk_count": len(retrieved_chunks),
                    "question_ids": [chunk.get("question_id", "") for chunk in retrieved_chunks],
                },
            },
            {
                "metric_name": "benchmark_retrieval_target_coverage",
                "metric_value": retrieval_target_score["coverage"],
                "details": {
                    "benchmark_item_id": item["id"],
                    "topical_targets": item.get("retrieval_expectation", {}).get("topical_targets", []),
                    "lexical_coverage": retrieval_target_score.get("lexical_coverage"),
                    "semantic_coverage": retrieval_target_score.get("semantic_coverage"),
                    "semantic_relevance": retrieval_target_score.get("semantic_relevance"),
                    "matched_targets": retrieval_target_score["matched_targets"],
                    "missing_targets": retrieval_target_score["missing_targets"],
                    "notes": retrieval_target_score.get("notes", []),
                    "retrieved_chunk_count": len(retrieved_chunks),
                },
            },
            {
                "metric_name": "benchmark_reference_rouge_l",
                "metric_value": round(
                    ComputedMetrics.rouge_l(
                        result["response"],
                        item.get("reference_answer_outline", ""),
                    ),
                    4,
                ),
                "details": {
                    "benchmark_item_id": item["id"],
                },
            },
            {
                "metric_name": "benchmark_reference_bleu_1",
                "metric_value": round(
                    ComputedMetrics.bleu_1(
                        result["response"],
                        item.get("reference_answer_outline", ""),
                    ),
                    4,
                ),
                "details": {
                    "benchmark_item_id": item["id"],
                },
            },
            {
                "metric_name": "benchmark_latency_seconds",
                "metric_value": round(latency_seconds, 4),
                "details": {
                    "benchmark_item_id": item["id"],
                },
            },
        ]

        if judge_scores:
            for key in (
                "correctness",
                "must_include_coverage",
                "must_not_do_compliance",
                "wcag_alignment",
                "helpfulness",
                "overall",
            ):
                if key not in judge_scores:
                    continue
                metrics.append(
                    {
                        "metric_name": f"benchmark_judge_{key}",
                        "metric_value": round(float(judge_scores[key]), 4),
                        "details": {
                            "benchmark_item_id": item["id"],
                            "notes": judge_scores.get("notes", []),
                        },
                    }
                )

        metric_values = {
            metric["metric_name"]: float(metric["metric_value"])
            for metric in metrics
        }
        case_pass = self._compute_case_pass(item=item, metric_values=metric_values)
        metrics.append(
            {
                "metric_name": "benchmark_case_pass",
                "metric_value": case_pass["passed"],
                "details": {
                    "benchmark_item_id": item["id"],
                    "reasons": case_pass["reasons"],
                },
            }
        )

        return metrics

    async def run_case(
        self,
        item: Dict[str, Any],
        batch_id: str,
        use_judge: bool = True,
    ) -> Dict[str, Any]:
        started_at = time.perf_counter()
        result = await self.chat_service.run_benchmark_case(item["query"])
        latency_seconds = time.perf_counter() - started_at
        judge_scores = self._judge_case(item, result) if use_judge else None

        sample_id = self.eval_repo.capture_rag_sample(
            query=item["query"],
            retrieved_contexts=self._build_retrieved_contexts(result["rag_chunk_payload"]),
            response=result["response"],
            ground_truth=item.get("reference_answer_outline", ""),
            student_id="instance_a_benchmark",
            session_id=item["id"],
            intent=result["intent"],
            instance="a",
        )

        metrics = self._build_case_metrics(
            item=item,
            result=result,
            latency_seconds=latency_seconds,
            judge_scores=judge_scores,
        )
        for metric in metrics:
            details = {
                **metric.get("details", {}),
                "category": item.get("category"),
                "difficulty": item.get("difficulty"),
                "expected_wcag_refs": item.get("expected_wcag_refs", []),
            }
            self.eval_repo.log_eval(
                content_type="rag_sample",
                content_id=sample_id,
                metric_name=metric["metric_name"],
                metric_value=metric["metric_value"],
                details=details,
                evaluator="benchmark_judge" if metric["metric_name"].startswith("benchmark_judge_") else "benchmark_auto",
                batch_id=batch_id,
            )

        self.eval_repo.mark_evaluated(sample_id)
        return {
            "benchmark_item_id": item["id"],
            "sample_id": sample_id,
            "query": item["query"],
            "intent_expected": item["intent_expected"],
            "intent_actual": result["intent"],
            "response": result["response"],
            "retrieved_chunks": result["rag_chunk_payload"],
            "wcag_context": result["wcag_context"],
            "latency_seconds": round(latency_seconds, 4),
            "judge_scores": judge_scores,
            "metrics": metrics,
        }

    async def run_batch(
        self,
        limit: Optional[int] = None,
        use_judge: bool = True,
        batch_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        dataset = self.load_dataset()
        items = list(dataset["items"])
        if limit is not None:
            items = items[:limit]

        batch_id = batch_id or f"instance-a-benchmark-{uuid.uuid4().hex[:12]}"
        cases: List[Dict[str, Any]] = []
        for item in items:
            cases.append(await self.run_case(item=item, batch_id=batch_id, use_judge=use_judge))

        summary = self.eval_repo.get_eval_summary(
            content_type="rag_sample",
            batch_id=batch_id,
        )
        return {
            "batch_id": batch_id,
            "dataset_name": dataset.get("dataset_metadata", {}).get("dataset_name"),
            "dataset_version": dataset.get("dataset_metadata", {}).get("version"),
            "item_count": len(cases),
            "cases": cases,
            "summary": summary,
        }


async def run_instance_a_benchmark(
    chat_service: GeneralChatService,
    eval_repo: EvalRepository,
    dataset_path: Optional[Path | str] = None,
    limit: Optional[int] = None,
    use_judge: bool = True,
    batch_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Convenience wrapper for running the frozen Instance A benchmark."""
    runner = InstanceABenchmarkRunner(
        chat_service=chat_service,
        eval_repo=eval_repo,
        dataset_path=dataset_path,
    )
    return await runner.run_batch(
        limit=limit,
        use_judge=use_judge,
        batch_id=batch_id,
    )
