"""
Unit tests for SessionContentCache.

Tests the in-memory teaching content cache used during objective-based
learning sessions.
"""

import pytest
from question_app.services.tutor.session_cache import SessionContentCache


@pytest.fixture
def cache():
    return SessionContentCache()


class TestCacheBasics:

    def test_empty_cache_returns_none(self, cache):
        assert cache.get("sess-1") is None

    def test_store_and_get(self, cache):
        cache.store(
            session_id="sess-1",
            objective_id="obj-alt-text",
            objective_text="Apply alt text to images",
            rag_chunks=[{"content": "quiz chunk 1"}],
            wcag_context="SC 1.1.1 details...",
            teaching_content="Combined teaching content...",
        )
        entry = cache.get("sess-1")
        assert entry is not None
        assert entry["objective_id"] == "obj-alt-text"
        assert entry["objective_text"] == "Apply alt text to images"
        assert len(entry["rag_chunks"]) == 1
        assert "SC 1.1.1" in entry["wcag_context"]
        assert entry["retrieved_at"] is not None

    def test_store_overwrites_existing(self, cache):
        cache.store("sess-1", "obj-1", "Old", [], "", "old content")
        cache.store("sess-1", "obj-2", "New", [], "", "new content")
        entry = cache.get("sess-1")
        assert entry["objective_id"] == "obj-2"
        assert entry["teaching_content"] == "new content"

    def test_invalidate(self, cache):
        cache.store("sess-1", "obj-1", "Test", [], "", "content")
        cache.invalidate("sess-1")
        assert cache.get("sess-1") is None

    def test_invalidate_nonexistent_is_noop(self, cache):
        cache.invalidate("nonexistent")  # should not raise

    def test_size(self, cache):
        assert cache.size == 0
        cache.store("sess-1", "obj-1", "", [], "", "")
        assert cache.size == 1
        cache.store("sess-2", "obj-2", "", [], "", "")
        assert cache.size == 2
        cache.invalidate("sess-1")
        assert cache.size == 1


class TestNeedsRetrieval:

    def test_no_cache_needs_retrieval(self, cache):
        assert cache.needs_retrieval("sess-1", "obj-1") is True

    def test_same_objective_no_retrieval(self, cache):
        cache.store("sess-1", "obj-1", "", [], "", "")
        assert cache.needs_retrieval("sess-1", "obj-1") is False

    def test_different_objective_needs_retrieval(self, cache):
        cache.store("sess-1", "obj-1", "", [], "", "")
        assert cache.needs_retrieval("sess-1", "obj-2") is True

    def test_after_invalidate_needs_retrieval(self, cache):
        cache.store("sess-1", "obj-1", "", [], "", "")
        cache.invalidate("sess-1")
        assert cache.needs_retrieval("sess-1", "obj-1") is True


class TestConvenienceMethods:

    def test_get_rag_chunks(self, cache):
        chunks = [{"content": "chunk 1"}, {"content": "chunk 2"}]
        cache.store("sess-1", "obj-1", "", chunks, "", "")
        assert cache.get_rag_chunks("sess-1") == chunks

    def test_get_rag_chunks_empty(self, cache):
        assert cache.get_rag_chunks("nonexistent") == []

    def test_get_teaching_content(self, cache):
        cache.store("sess-1", "obj-1", "", [], "", "the teaching content")
        assert cache.get_teaching_content("sess-1") == "the teaching content"

    def test_get_teaching_content_empty(self, cache):
        assert cache.get_teaching_content("nonexistent") == ""


class TestMultipleSessions:

    def test_independent_sessions(self, cache):
        cache.store("sess-1", "obj-1", "", [], "", "content 1")
        cache.store("sess-2", "obj-2", "", [], "", "content 2")
        assert cache.get("sess-1")["objective_id"] == "obj-1"
        assert cache.get("sess-2")["objective_id"] == "obj-2"

    def test_invalidate_one_preserves_other(self, cache):
        cache.store("sess-1", "obj-1", "", [], "", "")
        cache.store("sess-2", "obj-2", "", [], "", "")
        cache.invalidate("sess-1")
        assert cache.get("sess-1") is None
        assert cache.get("sess-2") is not None
