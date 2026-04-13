from question_app.api.eval import (
    _build_instance_a_batch_analysis,
    _build_instance_a_batch_comparison,
    _build_rag_sample_analysis,
)


def test_build_rag_sample_analysis_surfaces_instance_a_eval_signals():
    analysis = _build_rag_sample_analysis(
        {
            "id": "sample-123",
            "query": "What makes alt text effective?",
            "response": "Under WCAG 1.1.1, effective alt text describes the purpose of the image.",
            "eval_metrics_by_name": {
                "retrieval_context_count": {"value": 3.0, "details": {}},
                "retrieval_query_overlap": {"value": 0.75, "details": {}},
                "wcag_context_used": {"value": 1.0, "details": {}},
                "response_wcag_citation_present": {"value": 1.0, "details": {}},
                "response_wcag_citation_grounded": {"value": 1.0, "details": {"grounded_refs": ["1.1.1"]}},
            },
        }
    )

    assert analysis["sample"]["id"] == "sample-123"
    assert analysis["signals"]["retrieval_context_count"]["value"] == 3.0
    assert analysis["signals"]["retrieval_query_overlap"]["value"] == 0.75
    assert analysis["signals"]["response_wcag_citation_grounded"]["details"]["grounded_refs"] == ["1.1.1"]


def test_build_instance_a_batch_analysis_groups_cases_and_categories():
    analysis = _build_instance_a_batch_analysis(
        batch_id="batch-1",
        summary={
            "content_type": "rag_sample",
            "batch_id": "batch-1",
            "metrics": {
                "benchmark_judge_overall": {"avg": 0.9, "min": 0.82, "max": 0.98, "count": 2}
            },
        },
        samples=[
            {
                "id": "sample-1",
                "session_id": "a_code_001",
                "query": "Can you check this button for me?",
                "intent": "code_analysis_request",
                "response": "Use a button.",
                "retrieved_contexts": ["ctx-1"],
                "ground_truth": "Use a native button.",
                "eval_metrics_by_name": {
                    "benchmark_judge_overall": {
                        "value": 0.82,
                        "details": {"category": "code_analysis", "difficulty": "medium"},
                    },
                    "benchmark_judge_wcag_alignment": {
                        "value": 0.55,
                        "details": {"category": "code_analysis", "difficulty": "medium"},
                    },
                    "benchmark_expected_wcag_ref_recall": {
                        "value": 0.5,
                        "details": {
                            "benchmark_item_id": "a_code_001",
                            "category": "code_analysis",
                            "difficulty": "medium",
                            "expected_wcag_refs": ["2.1.1", "4.1.2"],
                        },
                    },
                    "benchmark_retrieval_target_coverage": {
                        "value": 0.0,
                        "details": {"benchmark_item_id": "a_code_001"},
                    },
                    "benchmark_case_pass": {
                        "value": 0.0,
                        "details": {"benchmark_item_id": "a_code_001", "reasons": ["low_overall_score"]},
                    },
                    "benchmark_latency_seconds": {"value": 15.8, "details": {}},
                },
            },
            {
                "id": "sample-2",
                "session_id": "a_alt_001",
                "query": "Should I use alt text for a spacer image?",
                "intent": "conceptual_question",
                "response": "Use alt=\"\".",
                "retrieved_contexts": [],
                "ground_truth": "Use alt=\"\".",
                "eval_metrics_by_name": {
                    "benchmark_judge_overall": {
                        "value": 0.98,
                        "details": {"category": "alt_text_and_images", "difficulty": "easy"},
                    },
                    "benchmark_judge_wcag_alignment": {
                        "value": 0.98,
                        "details": {"category": "alt_text_and_images", "difficulty": "easy"},
                    },
                    "benchmark_expected_wcag_ref_recall": {
                        "value": 1.0,
                        "details": {
                            "benchmark_item_id": "a_alt_001",
                            "category": "alt_text_and_images",
                            "difficulty": "easy",
                            "expected_wcag_refs": ["1.1.1"],
                        },
                    },
                    "benchmark_retrieval_target_coverage": {
                        "value": 1.0,
                        "details": {"benchmark_item_id": "a_alt_001"},
                    },
                    "benchmark_case_pass": {
                        "value": 1.0,
                        "details": {"benchmark_item_id": "a_alt_001", "reasons": []},
                    },
                    "benchmark_latency_seconds": {"value": 12.4, "details": {}},
                },
            },
        ],
    )

    assert analysis["batch_id"] == "batch-1"
    assert analysis["case_count"] == 2
    assert analysis["pass_count"] == 1
    assert analysis["pass_rate"] == 0.5
    assert analysis["weakest_cases"][0]["benchmark_item_id"] == "a_code_001"
    assert analysis["failed_cases"][0]["benchmark_item_id"] == "a_code_001"
    assert analysis["failed_cases"][0]["case_pass_reasons"] == ["low_overall_score"]
    assert analysis["by_category"]["code_analysis"]["avg_judge_overall"] == 0.82
    assert analysis["by_category"]["code_analysis"]["pass_rate"] == 0.0
    assert analysis["by_category"]["alt_text_and_images"]["avg_expected_wcag_ref_recall"] == 1.0


def test_build_instance_a_batch_comparison_surfaces_metric_and_case_deltas():
    comparison = _build_instance_a_batch_comparison(
        baseline={
            "batch_id": "baseline-1",
            "summary": {
                "metrics": {
                    "benchmark_judge_overall": {"avg": 0.82},
                    "benchmark_latency_seconds": {"avg": 12.0},
                }
            },
            "cases": [
                {
                    "benchmark_item_id": "a_code_001",
                    "category": "code_analysis",
                    "query": "Check this button",
                    "signals": {
                        "judge_overall": {"value": 0.82},
                        "judge_wcag_alignment": {"value": 0.55},
                        "case_pass": {"value": 0.0},
                        "retrieval_target_coverage": {"value": 0.0},
                        "latency_seconds": {"value": 15.8},
                    },
                }
            ],
            "pass_rate": 0.0,
        },
        candidate={
            "batch_id": "candidate-1",
            "summary": {
                "metrics": {
                    "benchmark_judge_overall": {"avg": 0.91},
                    "benchmark_latency_seconds": {"avg": 10.5},
                }
            },
            "cases": [
                {
                    "benchmark_item_id": "a_code_001",
                    "category": "code_analysis",
                    "query": "Check this button",
                    "signals": {
                        "judge_overall": {"value": 0.94},
                        "judge_wcag_alignment": {"value": 0.88},
                        "case_pass": {"value": 1.0},
                        "retrieval_target_coverage": {"value": 1.0},
                        "latency_seconds": {"value": 11.2},
                    },
                }
            ],
            "pass_rate": 1.0,
        },
    )

    assert comparison["baseline_batch_id"] == "baseline-1"
    assert comparison["candidate_batch_id"] == "candidate-1"
    assert comparison["pass_rate_delta"] == 1.0
    assert comparison["metric_deltas"]["benchmark_judge_overall"]["delta"] == 0.09
    assert comparison["metric_deltas"]["benchmark_latency_seconds"]["delta"] == -1.5
    assert comparison["case_deltas"][0]["judge_overall_delta"] == 0.12
    assert comparison["case_deltas"][0]["case_pass_delta"] == 1.0
    assert comparison["case_deltas"][0]["retrieval_target_coverage_delta"] == 1.0
    assert comparison["case_deltas"][0]["baseline_pass_reasons"] == []
    assert comparison["case_deltas"][0]["candidate_pass_reasons"] == []
    assert comparison["largest_improvements"][0]["benchmark_item_id"] == "a_code_001"
