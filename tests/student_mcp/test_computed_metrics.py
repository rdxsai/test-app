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


class TestConsistency:

    def test_identical_texts_are_consistent(self):
        texts = ["alt text is important", "alt text is important"]
        assert ComputedMetrics.cross_reference_consistency(texts) == pytest.approx(1.0)

    def test_unrelated_texts_low_consistency(self):
        texts = [
            "keyboard navigation requires focus management",
            "color contrast ratio must be sufficient",
        ]
        score = ComputedMetrics.cross_reference_consistency(texts)
        assert score < 0.5

    def test_single_text_returns_one(self):
        assert ComputedMetrics.cross_reference_consistency(["only one"]) == 1.0

    def test_empty_returns_one(self):
        assert ComputedMetrics.cross_reference_consistency([]) == 1.0


class TestDiscriminability:

    def test_distinct_distractors_high_score(self):
        answers = [
            {"text": "keyboard navigation", "is_correct": False},
            {"text": "color contrast ratio", "is_correct": False},
            {"text": "semantic HTML elements", "is_correct": False},
            {"text": "alt text for images", "is_correct": True},
        ]
        score = ComputedMetrics.question_discriminability(answers)
        assert score > 0.5  # distinct distractors

    def test_similar_distractors_low_score(self):
        answers = [
            {"text": "add alt text to the image", "is_correct": False},
            {"text": "add alt text to all images", "is_correct": False},
            {"text": "alt text should describe the image", "is_correct": False},
            {"text": "correct answer here", "is_correct": True},
        ]
        score = ComputedMetrics.question_discriminability(answers)
        assert score < 0.7  # overlapping distractors score lower than distinct ones

    def test_single_distractor_returns_one(self):
        answers = [
            {"text": "wrong", "is_correct": False},
            {"text": "right", "is_correct": True},
        ]
        assert ComputedMetrics.question_discriminability(answers) == 1.0
