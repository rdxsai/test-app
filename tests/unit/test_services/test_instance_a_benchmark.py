import json

import pytest

from question_app.services.eval.instance_a_benchmark import InstanceABenchmarkRunner


class FakeJudgeClient:
    def chat(
        self,
        messages,
        temperature=0.0,
        max_tokens=250,
        reasoning_effort="low",
        response_format=None,
    ):
        if "retrieval support" in messages[0]["content"]:
            return json.dumps(
                {
                    "coverage": 1.0,
                    "relevance": 0.8,
                    "matched_targets": ["focus order", "focus trap", "modal accessibility"],
                    "missing_targets": [],
                    "notes": ["Retrieved chunks are semantically about modal focus handling."],
                }
            )
        return json.dumps(
            {
                "correctness": 0.9,
                "must_include_coverage": 0.8,
                "must_not_do_compliance": 1.0,
                "wcag_alignment": 1.0,
                "helpfulness": 0.85,
                "overall": 0.89,
                "notes": ["Grounded in the expected WCAG criterion."],
            }
        )


class FakeChatService:
    def __init__(self, result, judge_client=None):
        self._result = result
        self.reasoning_client = judge_client

    async def run_benchmark_case(self, user_message: str):
        return self._result


class FakeEvalRepo:
    def __init__(self):
        self.captured_sample = None
        self.logged_metrics = []
        self.marked_samples = []
        self.summary_calls = []

    def capture_rag_sample(self, **kwargs):
        self.captured_sample = kwargs
        return "sample-123"

    def log_eval(self, **kwargs):
        self.logged_metrics.append(kwargs)
        return f"eval-{len(self.logged_metrics)}"

    def mark_evaluated(self, sample_id: str):
        self.marked_samples.append(sample_id)
        return True

    def get_eval_summary(self, content_type: str, metric_name=None, batch_id=None):
        self.summary_calls.append(
            {
                "content_type": content_type,
                "metric_name": metric_name,
                "batch_id": batch_id,
            }
        )
        return {"content_type": content_type, "batch_id": batch_id, "metrics": {}}


@pytest.mark.asyncio
async def test_run_case_logs_metrics_and_marks_sample_evaluated(tmp_path):
    dataset_path = tmp_path / "dataset.json"
    dataset_path.write_text(json.dumps({"items": []}))
    result = {
        "intent": "conceptual_question",
        "response": "Under WCAG 1.1.1, decorative images should use alt=\"\".",
        "retrieved_chunks": [
            {"question_id": "q-1", "topic": "images"},
        ],
        "rag_chunk_payload": [
            {
                "source_label": "Quiz Source 1 | topic=images | question_id=q-1 | type=question",
                "summary": "Key point: Decorative images should use a null alt attribute.",
                "topic": "images",
                "question_id": "q-1",
                "chunk_type": "question",
                "distance": 0.1,
                "rrf_score": 0.4,
            }
        ],
        "wcag_context": "SC 1.1.1 Non-text Content",
        "combined_context": "",
        "code_analysis": "",
    }
    item = {
        "id": "a_alt_001",
        "query": "Should decorative images use alt text?",
        "category": "alt_text_and_images",
        "difficulty": "easy",
        "intent_expected": "conceptual_question",
        "expected_wcag_refs": ["1.1.1"],
        "forbidden_wcag_refs": [],
        "reference_answer_outline": "Decorative images should use alt=\"\" and be ignored by screen readers.",
        "retrieval_expectation": {"quiz_should_help": False},
    }
    repo = FakeEvalRepo()
    runner = InstanceABenchmarkRunner(
        chat_service=FakeChatService(result=result, judge_client=FakeJudgeClient()),
        eval_repo=repo,
        dataset_path=dataset_path,
    )

    case = await runner.run_case(item=item, batch_id="batch-1", use_judge=True)

    assert case["sample_id"] == "sample-123"
    assert repo.captured_sample["ground_truth"] == item["reference_answer_outline"]
    assert repo.captured_sample["session_id"] == item["id"]
    assert repo.marked_samples == ["sample-123"]
    metric_names = [entry["metric_name"] for entry in repo.logged_metrics]
    assert "benchmark_intent_match" in metric_names
    assert "benchmark_expected_wcag_ref_recall" in metric_names
    assert "benchmark_judge_overall" in metric_names
    assert "benchmark_retrieval_target_coverage" in metric_names
    assert "benchmark_case_pass" in metric_names
    assert all(entry["batch_id"] == "batch-1" for entry in repo.logged_metrics)
    assert all(entry["details"]["benchmark_item_id"] == item["id"] for entry in repo.logged_metrics)


@pytest.mark.asyncio
async def test_run_case_scores_retrieval_expectation_miss_when_quiz_support_missing(tmp_path):
    dataset_path = tmp_path / "dataset.json"
    dataset_path.write_text(json.dumps({"items": []}))
    repo = FakeEvalRepo()
    runner = InstanceABenchmarkRunner(
        chat_service=FakeChatService(
            result={
                "intent": "conceptual_question",
                "response": "Move focus into the modal and return it on close.",
                "retrieved_chunks": [],
                "rag_chunk_payload": [],
                "wcag_context": "SC 2.4.3 Focus Order",
                "combined_context": "",
                "code_analysis": "",
            }
        ),
        eval_repo=repo,
        dataset_path=dataset_path,
    )

    await runner.run_case(
        item={
            "id": "a_key_002",
            "query": "How do I fix focus in a modal?",
            "category": "keyboard_and_focus",
            "difficulty": "hard",
            "intent_expected": "conceptual_question",
            "expected_wcag_refs": ["2.4.3"],
            "forbidden_wcag_refs": [],
            "reference_answer_outline": "Move focus into the modal, trap it, and return it when closing.",
            "retrieval_expectation": {
                "quiz_should_help": True,
                "topical_targets": ["focus trap", "modal accessibility"],
            },
        },
        batch_id="batch-2",
        use_judge=False,
    )

    retrieval_metric = next(
        entry for entry in repo.logged_metrics
        if entry["metric_name"] == "benchmark_quiz_retrieval_expectation_met"
    )
    target_coverage_metric = next(
        entry for entry in repo.logged_metrics
        if entry["metric_name"] == "benchmark_retrieval_target_coverage"
    )
    case_pass_metric = next(
        entry for entry in repo.logged_metrics
        if entry["metric_name"] == "benchmark_case_pass"
    )
    assert retrieval_metric["metric_value"] == 0.0
    assert target_coverage_metric["metric_value"] == 0.0
    assert case_pass_metric["metric_value"] == 0.0
    assert "missing_quiz_retrieval" in case_pass_metric["details"]["reasons"]
    assert "weak_retrieval_target_coverage" in case_pass_metric["details"]["reasons"]


@pytest.mark.asyncio
async def test_run_case_uses_semantic_retrieval_support_for_quiz_sensitive_items(tmp_path):
    dataset_path = tmp_path / "dataset.json"
    dataset_path.write_text(json.dumps({"items": []}))
    repo = FakeEvalRepo()
    runner = InstanceABenchmarkRunner(
        chat_service=FakeChatService(
            result={
                "intent": "conceptual_question",
                "response": "Move focus into the modal, trap it there, and return it to the opener when the modal closes.",
                "retrieved_chunks": [
                    {"question_id": "q-modal", "topic": "dialogs"},
                ],
                "rag_chunk_payload": [
                    {
                        "source_label": "Quiz Source 1 | topic=dialogs | question_id=q-modal | type=question",
                        "summary": "Key point: When a dialog opens, move keyboard focus into it, keep focus within it, and restore focus afterward.",
                        "topic": "dialogs",
                        "question_id": "q-modal",
                        "chunk_type": "question",
                        "distance": 0.16,
                        "rrf_score": 0.21,
                    }
                ],
                "wcag_context": "SC 2.4.3 Focus Order",
                "combined_context": "",
                "code_analysis": "",
            },
            judge_client=FakeJudgeClient(),
        ),
        eval_repo=repo,
        dataset_path=dataset_path,
    )

    await runner.run_case(
        item={
            "id": "a_key_002",
            "query": "How do I fix focus in a modal?",
            "category": "keyboard_and_focus",
            "difficulty": "hard",
            "intent_expected": "conceptual_question",
            "expected_wcag_refs": ["2.4.3"],
            "forbidden_wcag_refs": [],
            "reference_answer_outline": "Move focus into the modal, trap it, and return it when closing.",
            "retrieval_expectation": {
                "quiz_should_help": True,
                "topical_targets": ["focus order", "focus trap", "modal accessibility"],
            },
        },
        batch_id="batch-2b",
        use_judge=False,
    )

    target_coverage_metric = next(
        entry for entry in repo.logged_metrics
        if entry["metric_name"] == "benchmark_retrieval_target_coverage"
    )
    case_pass_metric = next(
        entry for entry in repo.logged_metrics
        if entry["metric_name"] == "benchmark_case_pass"
    )

    assert target_coverage_metric["metric_value"] == 0.8
    assert target_coverage_metric["details"]["lexical_coverage"] == 0.0
    assert target_coverage_metric["details"]["semantic_coverage"] == 1.0
    assert target_coverage_metric["details"]["semantic_relevance"] == 0.8
    assert target_coverage_metric["details"]["matched_targets"] == [
        "focus order",
        "focus trap",
        "modal accessibility",
    ]
    assert case_pass_metric["metric_value"] == 1.0


@pytest.mark.asyncio
async def test_run_batch_loads_dataset_and_returns_summary(tmp_path):
    dataset_path = tmp_path / "dataset.json"
    dataset_path.write_text(
        json.dumps(
            {
                "dataset_metadata": {
                    "dataset_name": "instance_a_gold_v1",
                    "version": "1.0.0",
                },
                "items": [
                    {
                        "id": "a_off_001",
                        "query": "Can you share a recipe?",
                        "category": "off_topic",
                        "difficulty": "easy",
                        "intent_expected": "off_topic",
                        "expected_wcag_refs": [],
                        "forbidden_wcag_refs": [],
                        "reference_answer_outline": "Politely refuse and redirect to accessibility.",
                        "retrieval_expectation": {"quiz_should_help": False},
                    },
                    {
                        "id": "a_off_002",
                        "query": "What is the best MacBook price?",
                        "category": "off_topic",
                        "difficulty": "easy",
                        "intent_expected": "off_topic",
                        "expected_wcag_refs": [],
                        "forbidden_wcag_refs": [],
                        "reference_answer_outline": "Politely refuse shopping help.",
                        "retrieval_expectation": {"quiz_should_help": False},
                    },
                ],
            }
        )
    )
    repo = FakeEvalRepo()
    runner = InstanceABenchmarkRunner(
        chat_service=FakeChatService(
            result={
                "intent": "off_topic",
                "response": "I can only help with web accessibility questions.",
                "retrieved_chunks": [],
                "rag_chunk_payload": [],
                "wcag_context": "",
                "combined_context": "",
                "code_analysis": "",
            }
        ),
        eval_repo=repo,
        dataset_path=dataset_path,
    )

    result = await runner.run_batch(limit=1, use_judge=False, batch_id="batch-3")

    assert result["batch_id"] == "batch-3"
    assert result["dataset_name"] == "instance_a_gold_v1"
    assert result["dataset_version"] == "1.0.0"
    assert result["item_count"] == 1
    assert repo.summary_calls == [
        {
            "content_type": "rag_sample",
            "metric_name": None,
            "batch_id": "batch-3",
        }
    ]
