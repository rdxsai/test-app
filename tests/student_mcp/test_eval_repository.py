"""
Integration tests for EvalRepository.

Tests eval_log and rag_eval_samples operations against real PostgreSQL.
"""

import os
import pytest
from question_app.services.eval.repository import EvalRepository
from question_app.services.database import DatabaseManager


_repo = None


def _get_repo():
    global _repo
    if _repo is None:
        db = DatabaseManager(
            dsn=(
                f"host={os.getenv('POSTGRES_HOST', 'localhost')} "
                f"port={os.getenv('POSTGRES_PORT', '5432')} "
                f"dbname={os.getenv('POSTGRES_DB', 'socratic_tutor')} "
                f"user={os.getenv('POSTGRES_USER', 'app_user')} "
                f"password={os.getenv('POSTGRES_PASSWORD', 'changeme_dev')}"
            ),
            schema=os.getenv("DB_SCHEMA", "dev"),
        )
        _repo = EvalRepository(db=db)
    return _repo


@pytest.fixture
def repo():
    return _get_repo()


@pytest.fixture(autouse=True)
def clean_between_tests():
    yield
    r = _get_repo()
    with r.db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM eval_log WHERE content_id LIKE 'test-%'")
            cur.execute("DELETE FROM rag_eval_samples WHERE student_id LIKE 'test-%'")
        conn.commit()


class TestEvalLog:

    def test_log_eval(self, repo):
        eval_id = repo.log_eval(
            content_type="rag_response",
            content_id="test-sample-1",
            metric_name="faithfulness",
            metric_value=0.85,
            details={"breakdown": "grounded in 3/4 contexts"},
            evaluator="ragas",
        )
        assert eval_id is not None

    def test_get_eval_logs_empty(self, repo):
        logs = repo.get_eval_logs(content_id="test-nonexistent")
        assert logs == []

    def test_log_and_retrieve(self, repo):
        repo.log_eval("rag_response", "test-r-1", "faithfulness", 0.9)
        repo.log_eval("rag_response", "test-r-1", "relevancy", 0.7)
        logs = repo.get_eval_logs(content_id="test-r-1")
        assert len(logs) == 2
        names = {l["metric_name"] for l in logs}
        assert names == {"faithfulness", "relevancy"}

    def test_filter_by_metric(self, repo):
        repo.log_eval("rag_response", "test-f-1", "faithfulness", 0.9)
        repo.log_eval("rag_response", "test-f-1", "relevancy", 0.7)
        logs = repo.get_eval_logs(content_id="test-f-1", metric_name="faithfulness")
        assert len(logs) == 1
        assert logs[0]["metric_name"] == "faithfulness"

    def test_eval_summary(self, repo):
        repo.log_eval("feedback", "test-s-1", "flesch_kincaid", 8.5)
        repo.log_eval("feedback", "test-s-2", "flesch_kincaid", 10.2)
        repo.log_eval("feedback", "test-s-3", "flesch_kincaid", 7.1)
        summary = repo.get_eval_summary("feedback", metric_name="flesch_kincaid")
        assert summary["content_type"] == "feedback"
        assert "flesch_kincaid" in summary["metrics"]
        m = summary["metrics"]["flesch_kincaid"]
        assert m["count"] == 3
        assert 7.0 < m["avg"] < 11.0


class TestRagSamples:

    def test_capture_and_retrieve(self, repo):
        sample_id = repo.capture_rag_sample(
            query="What is alt text?",
            retrieved_contexts=["Alt text is...", "SC 1.1.1 requires..."],
            response="Alt text provides a text alternative for images.",
            student_id="test-student-1",
            intent="conceptual_question",
            instance="a",
        )
        assert sample_id is not None

        sample = repo.get_rag_sample(sample_id)
        assert sample is not None
        assert sample["query"] == "What is alt text?"
        assert len(sample["retrieved_contexts"]) == 2
        assert sample["evaluated"] is False

    def test_list_samples(self, repo):
        repo.capture_rag_sample("q1", ["c1"], "r1", student_id="test-list-1")
        repo.capture_rag_sample("q2", ["c2"], "r2", student_id="test-list-1")
        samples = repo.get_rag_samples(limit=10)
        test_samples = [s for s in samples if s["student_id"] == "test-list-1"]
        assert len(test_samples) == 2

    def test_filter_by_evaluated(self, repo):
        sid = repo.capture_rag_sample("q", ["c"], "r", student_id="test-eval-filt")
        unevaluated = repo.get_rag_samples(evaluated=False)
        assert any(s["id"] == sid for s in unevaluated)

        repo.mark_evaluated(sid)
        unevaluated = repo.get_rag_samples(evaluated=False)
        assert not any(s["id"] == sid for s in unevaluated)

    def test_mark_evaluated(self, repo):
        sid = repo.capture_rag_sample("q", ["c"], "r", student_id="test-mark")
        assert repo.mark_evaluated(sid) is True
        sample = repo.get_rag_sample(sid)
        assert sample["evaluated"] is True

    def test_get_nonexistent_sample(self, repo):
        assert repo.get_rag_sample("nonexistent-id") is None
