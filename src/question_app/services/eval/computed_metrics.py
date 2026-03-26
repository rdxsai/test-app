"""
Stream 3: Computed text metrics — no LLM needed.

Readability, similarity, consistency, and discriminability metrics
for evaluating AI-generated content quality.
"""

import math
import re
from collections import Counter
from typing import Any, Dict, List


class ComputedMetrics:
    """Pure-Python text metrics for content evaluation."""

    # ------------------------------------------------------------------
    # Readability
    # ------------------------------------------------------------------

    @staticmethod
    def flesch_kincaid_grade(text: str) -> float:
        """Flesch-Kincaid grade level. Uses textstat if available, falls back to manual."""
        if not text or not text.strip():
            return 0.0
        try:
            import textstat
            return textstat.flesch_kincaid_grade(text)
        except ImportError:
            # Manual fallback
            sentences = ComputedMetrics._count_sentences(text)
            words = ComputedMetrics._count_words(text)
            syllables = ComputedMetrics._count_syllables(text)
            if sentences == 0 or words == 0:
                return 0.0
            return 0.39 * (words / sentences) + 11.8 * (syllables / words) - 15.59

    @staticmethod
    def average_sentence_length(text: str) -> float:
        """Average number of words per sentence."""
        sentences = ComputedMetrics._count_sentences(text)
        words = ComputedMetrics._count_words(text)
        return words / max(sentences, 1)

    @staticmethod
    def vocabulary_complexity(text: str) -> float:
        """Ratio of unique words longer than 6 characters to total words."""
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        if not words:
            return 0.0
        long_unique = len({w for w in words if len(w) > 6})
        return long_unique / len(words)

    @staticmethod
    def readability_score(text: str) -> Dict[str, float]:
        """Combined readability metrics."""
        return {
            "flesch_kincaid_grade": ComputedMetrics.flesch_kincaid_grade(text),
            "avg_sentence_length": ComputedMetrics.average_sentence_length(text),
            "vocabulary_complexity": ComputedMetrics.vocabulary_complexity(text),
            "word_count": ComputedMetrics._count_words(text),
        }

    # ------------------------------------------------------------------
    # Similarity (ROUGE-L, BLEU)
    # ------------------------------------------------------------------

    @staticmethod
    def rouge_l(hypothesis: str, reference: str) -> float:
        """ROUGE-L F-measure based on Longest Common Subsequence."""
        if not hypothesis or not reference:
            return 0.0

        hyp_tokens = hypothesis.lower().split()
        ref_tokens = reference.lower().split()

        if not hyp_tokens or not ref_tokens:
            return 0.0

        # LCS length via dynamic programming
        m, n = len(hyp_tokens), len(ref_tokens)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if hyp_tokens[i - 1] == ref_tokens[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

        lcs_len = dp[m][n]
        if lcs_len == 0:
            return 0.0

        precision = lcs_len / m
        recall = lcs_len / n
        f1 = 2 * precision * recall / (precision + recall)
        return f1

    @staticmethod
    def bleu_1(hypothesis: str, reference: str) -> float:
        """BLEU-1 unigram precision with brevity penalty."""
        if not hypothesis or not reference:
            return 0.0

        hyp_tokens = hypothesis.lower().split()
        ref_tokens = reference.lower().split()

        if not hyp_tokens:
            return 0.0

        ref_counts = Counter(ref_tokens)
        hyp_counts = Counter(hyp_tokens)

        # Clipped counts
        clipped = sum(min(hyp_counts[w], ref_counts.get(w, 0)) for w in hyp_counts)
        precision = clipped / len(hyp_tokens)

        # Brevity penalty
        bp = 1.0
        if len(hyp_tokens) < len(ref_tokens):
            bp = math.exp(1 - len(ref_tokens) / len(hyp_tokens))

        return bp * precision

    # ------------------------------------------------------------------
    # Consistency & Discriminability
    # ------------------------------------------------------------------

    @staticmethod
    def cross_reference_consistency(texts: List[str]) -> float:
        """Average pairwise cosine similarity of TF-IDF vectors.

        Measures how consistent multiple texts are with each other.
        Score 0-1, where 1 = all texts use identical vocabulary.
        Useful for checking if feedback texts for the same question
        don't contradict each other.
        """
        if len(texts) < 2:
            return 1.0

        # Build vocabulary
        all_words: set = set()
        tokenized = []
        for t in texts:
            words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
            tokenized.append(words)
            all_words.update(words)

        if not all_words:
            return 1.0

        vocab = sorted(all_words)
        word_to_idx = {w: i for i, w in enumerate(vocab)}

        # TF vectors
        vectors = []
        for words in tokenized:
            vec = [0.0] * len(vocab)
            counts = Counter(words)
            for w, c in counts.items():
                vec[word_to_idx[w]] = c
            vectors.append(vec)

        # Average pairwise cosine similarity
        similarities = []
        for i in range(len(vectors)):
            for j in range(i + 1, len(vectors)):
                sim = ComputedMetrics._cosine_sim(vectors[i], vectors[j])
                similarities.append(sim)

        return sum(similarities) / len(similarities) if similarities else 1.0

    @staticmethod
    def question_discriminability(answers: List[Dict[str, Any]]) -> float:
        """Measure how distinct incorrect answers are from each other.

        Lower word overlap between distractors = better discriminability
        (each distractor tests a different misconception).
        Returns 0-1 where 1 = maximally discriminating (no overlap).
        """
        incorrect = [
            a.get("text", "") for a in answers
            if not a.get("is_correct", False) and a.get("text")
        ]

        if len(incorrect) < 2:
            return 1.0

        # Pairwise word overlap ratio
        overlaps = []
        for i in range(len(incorrect)):
            for j in range(i + 1, len(incorrect)):
                words_i = set(re.findall(r'\b[a-zA-Z]+\b', incorrect[i].lower()))
                words_j = set(re.findall(r'\b[a-zA-Z]+\b', incorrect[j].lower()))
                if not words_i or not words_j:
                    continue
                overlap = len(words_i & words_j) / len(words_i | words_j)
                overlaps.append(overlap)

        if not overlaps:
            return 1.0

        avg_overlap = sum(overlaps) / len(overlaps)
        return 1.0 - avg_overlap  # invert: less overlap = better

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _count_sentences(text: str) -> int:
        return max(len(re.split(r'[.!?]+', text.strip())) - 1, 1)

    @staticmethod
    def _count_words(text: str) -> int:
        return len(re.findall(r'\b\w+\b', text))

    @staticmethod
    def _count_syllables(text: str) -> int:
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        count = 0
        for word in words:
            vowels = len(re.findall(r'[aeiouy]+', word))
            if word.endswith('e') and vowels > 1:
                vowels -= 1
            count += max(vowels, 1)
        return count

    @staticmethod
    def _cosine_sim(a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
