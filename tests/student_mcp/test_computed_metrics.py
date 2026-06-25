"""
Unit tests for ComputedMetrics (Stream 3).
"""

import pytest
from question_app.services.eval.computed_metrics import ComputedMetrics


class TestReadability:

    def test_flesch_kincaid_returns_float(self):
        score = ComputedMetrics.flesch_kincaid_grade(
            "This is a simple sentence. It has short words."
        )
        assert isinstance(score, float)

    def test_flesch_kincaid_empty(self):
        assert ComputedMetrics.flesch_kincaid_grade("") == 0.0

    def test_average_sentence_length(self):
        text = "Hello world. This is a test. Short."
        avg = ComputedMetrics.average_sentence_length(text)
        assert 1.0 < avg < 5.0

    def test_vocabulary_complexity(self):
        simple = "the cat sat on the mat"
        complex_text = "accessibility implementation guidelines requirements"
        assert ComputedMetrics.vocabulary_complexity(simple) < ComputedMetrics.vocabulary_complexity(complex_text)

    def test_readability_score_returns_all_keys(self):
        scores = ComputedMetrics.readability_score("This is a test sentence.")
        assert "flesch_kincaid_grade" in scores
        assert "avg_sentence_length" in scores
        assert "vocabulary_complexity" in scores
        assert "word_count" in scores


class TestSimilarity:

    def test_rouge_l_identical(self):
        text = "the cat sat on the mat"
        assert ComputedMetrics.rouge_l(text, text) == pytest.approx(1.0)

    def test_rouge_l_no_overlap(self):
        assert ComputedMetrics.rouge_l("hello world", "foo bar baz") == 0.0

    def test_rouge_l_partial(self):
        score = ComputedMetrics.rouge_l(
            "the cat sat on a mat",
            "the cat is on the mat",
        )
        assert 0.3 < score < 1.0

    def test_rouge_l_empty(self):
        assert ComputedMetrics.rouge_l("", "something") == 0.0
        assert ComputedMetrics.rouge_l("something", "") == 0.0

    def test_bleu_1_identical(self):
        text = "the cat sat on the mat"
        assert ComputedMetrics.bleu_1(text, text) == pytest.approx(1.0)

    def test_bleu_1_no_overlap(self):
        assert ComputedMetrics.bleu_1("hello world", "foo bar baz") == 0.0

    def test_bleu_1_partial(self):
        score = ComputedMetrics.bleu_1(
            "the cat sat",
            "the cat sat on the mat",
        )
        assert 0.3 < score < 1.0

    def test_bleu_1_empty(self):
        assert ComputedMetrics.bleu_1("", "something") == 0.0

