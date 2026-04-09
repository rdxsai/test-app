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

    def test_get_retrieval_bundle(self, cache):
        bundle = {"version": 1, "sections": {"core_rules": []}}
        cache.store("sess-1", "obj-1", "", [], "", "content", retrieval_bundle=bundle)
        assert cache.get_retrieval_bundle("sess-1") == bundle

    def test_get_retrieval_bundle_empty(self, cache):
        assert cache.get_retrieval_bundle("nonexistent") is None

    def test_export_session_returns_snapshot(self, cache):
        cache.store("sess-1", "obj-1", "Objective", [], "", "content")
        cache.store_teaching_plan(
            "sess-1",
            {
                "objective": "Objective",
                "concepts": [{"id": "c1", "name": "Hierarchy", "status": "not_covered"}],
                "recommended_order": ["c1"],
            },
        )

        exported = cache.export_session("sess-1")

        assert exported is not None
        assert exported["objective_id"] == "obj-1"
        assert exported["teaching_plan"]["objective"] == "Objective"
        assert exported["lesson_state"]["active_concept"] == "c1"
        assert exported["pacing_state"]["current_pace"] == "steady"

    def test_export_session_slims_retrieval_bundle(self, cache):
        """Verify export strips raw_hits and per-item round/sequence but keeps content."""
        bundle = {
            "version": 1,
            "objective_text": "Test objective",
            "coverage": {"hit_count": 2, "required_checks": {}},
            "raw_hits": [
                {"tool": "get_criterion", "args": {"id": "1.1.1"}, "round": 1, "sequence": 1, "chars": 500, "preview": "..."},
                {"tool": "get_glossary_term", "args": {"term": "alt text"}, "round": 1, "sequence": 2, "chars": 200, "preview": "..."},
            ],
            "sections": {
                "core_rules": [
                    {"title": "SC 1.1.1", "content": "Non-text Content", "source_tool": "get_criterion", "source_args": {"id": "1.1.1"}, "round": 1, "sequence": 1},
                ],
                "definitions": [
                    {"title": "Alt Text", "content": "Alternative text", "source_tool": "get_glossary_term", "source_args": {"term": "alt text"}, "round": 1, "sequence": 2},
                ],
                "examples": [],
            },
        }
        cache.store("sess-slim", "obj-1", "Objective", [], "", "content", retrieval_bundle=bundle)

        exported = cache.export_session("sess-slim")
        slim = exported["retrieval_bundle"]

        # raw_hits dropped entirely
        assert "raw_hits" not in slim
        # coverage and version preserved
        assert slim["version"] == 1
        assert slim["coverage"]["hit_count"] == 2
        # section content preserved
        assert slim["sections"]["core_rules"][0]["title"] == "SC 1.1.1"
        assert slim["sections"]["core_rules"][0]["content"] == "Non-text Content"
        assert slim["sections"]["core_rules"][0]["source_tool"] == "get_criterion"
        # round/sequence stripped from items
        assert "round" not in slim["sections"]["core_rules"][0]
        assert "sequence" not in slim["sections"]["core_rules"][0]
        assert "round" not in slim["sections"]["definitions"][0]
        # empty sections preserved
        assert slim["sections"]["examples"] == []

    def test_restore_rehydrates_entry(self, cache):
        cache.restore(
            "sess-restore",
            {
                "objective_id": "obj-1",
                "objective_text": "Objective",
                "rag_chunks": [{"content": "chunk"}],
                "wcag_context": "WCAG context",
                "teaching_content": "Rendered evidence pack",
                "retrieval_bundle": {"version": 1},
                "teaching_plan": "8. dependency_order\n1. Hierarchy\n",
                "lesson_state": {
                    "active_concept": "hierarchy",
                    "pending_check": "Hierarchy",
                    "bridge_back_target": "hierarchy",
                    "teaching_order": ["hierarchy"],
                    "concepts": [{"id": "hierarchy", "label": "Hierarchy", "status": "in_progress"}],
                },
                "pacing_state": {
                    "current_pace": "slow",
                    "pace_reason": "Needs more scaffold",
                    "turns_at_current_pace": 2,
                    "cooldown_remaining": 1,
                    "recent_signals": [
                        {
                            "grasp_level": "fragile",
                            "reasoning_mode": "paraphrase",
                            "support_needed": "heavy",
                            "confusion_level": "high",
                            "response_pattern": "hedging",
                            "concept_closure": "not_ready",
                            "override_pace": "none",
                            "recommended_next_step": "re-explain",
                        }
                    ],
                },
                "retrieved_at": "2026-04-08T12:00:00",
            },
        )

        assert cache.get_teaching_content("sess-restore") == "Rendered evidence pack"
        assert cache.get_retrieval_bundle("sess-restore") == {"version": 1}
        assert cache.get_teaching_plan("sess-restore") == "8. dependency_order\n1. Hierarchy\n"
        assert cache.get_lesson_state("sess-restore")["active_concept"] == "hierarchy"
        assert cache.get_pacing_state("sess-restore")["current_pace"] == "slow"


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


class TestLessonState:

    def test_store_dict_plan_builds_lesson_state(self, cache):
        cache.store("sess-1", "obj-1", "Objective", [], "", "content")
        cache.store_teaching_plan(
            "sess-1",
            {
                "objective": "Objective",
                "concepts": [
                    {"id": "c1", "name": "Hierarchy", "status": "not_covered"},
                    {"id": "c2", "name": "Conformance", "status": "not_covered"},
                ],
                "recommended_order": ["c1", "c2"],
            },
        )
        lesson_state = cache.get_lesson_state("sess-1")
        assert lesson_state is not None
        assert lesson_state["active_concept"] == "c1"
        assert lesson_state["bridge_back_target"] == "c1"
        assert lesson_state["teaching_order"] == ["c1", "c2"]

    def test_store_text_plan_builds_lesson_state(self, cache):
        cache.store("sess-1", "obj-1", "Objective", [], "", "content")
        cache.store_teaching_plan(
            "sess-1",
            (
                "1. plain_language_goal\nExplain WCAG structure simply.\n\n"
                "7. concept_decomposition\n"
                "- Principles vs guidelines\n"
                "- Success criteria placement\n\n"
                "8. dependency_order\n"
                "1. Principles vs guidelines\n"
                "2. Success criteria placement\n"
            ),
        )
        lesson_state = cache.get_lesson_state("sess-1")
        assert lesson_state is not None
        assert lesson_state["active_concept"] == "principles-vs-guidelines"
        assert lesson_state["pending_check"] == "Principles vs guidelines"
        assert lesson_state["teaching_order"] == [
            "principles-vs-guidelines",
            "success-criteria-placement",
        ]

    def test_apply_lesson_state_patch_updates_concepts(self, cache):
        cache.store("sess-1", "obj-1", "Objective", [], "", "content")
        cache.store_teaching_plan(
            "sess-1",
            {
                "objective": "Objective",
                "concepts": [
                    {"id": "c1", "name": "Hierarchy", "status": "not_covered"},
                    {"id": "c2", "name": "Conformance", "status": "not_covered"},
                ],
                "recommended_order": ["c1", "c2"],
            },
        )
        lesson_state = cache.apply_lesson_state_patch(
            "sess-1",
            {
                "active_concept": "c2",
                "pending_check": "Explain the conformance roll-up rule",
                "bridge_back_target": "c2",
                "concept_updates": [
                    {"concept_id": "c1", "status": "covered"},
                    {"concept_id": "c2", "status": "in_progress"},
                ],
            },
        )
        assert lesson_state is not None
        assert lesson_state["active_concept"] == "c2"
        assert lesson_state["pending_check"] == "Explain the conformance roll-up rule"
        assert lesson_state["concepts"][0]["status"] == "covered"
        assert lesson_state["concepts"][1]["status"] == "in_progress"

    def test_update_concept_status_updates_text_plan_lesson_state(self, cache):
        cache.store("sess-1", "obj-1", "Objective", [], "", "content")
        cache.store_teaching_plan(
            "sess-1",
            (
                "1. plain_language_goal\nExplain WCAG structure simply.\n\n"
                "8. dependency_order\n"
                "1. Principles vs guidelines\n"
                "2. Success criteria placement\n"
            ),
        )
        cache.update_concept_status("sess-1", "principles-vs-guidelines", "covered")
        lesson_state = cache.get_lesson_state("sess-1")
        assert lesson_state is not None
        assert lesson_state["active_concept"] == "success-criteria-placement"

    def test_apply_patch_deduplicates_variant_concept_ids(self, cache):
        """Turn analyzer may use hyphens, underscores, or raw labels for the
        same concept. Verify that all variants match the canonical concept
        instead of creating duplicates."""
        cache.store("sess-1", "obj-1", "Objective", [], "", "content")
        cache.store_teaching_plan(
            "sess-1",
            plan=None,
            extracted_concepts=[
                {"id": "prefer_native_html", "label": "Rule 1: prefer native HTML"},
                {"id": "dont_change_semantics", "label": "Rule 2: don't change native semantics"},
            ],
        )
        lesson_state = cache.get_lesson_state("sess-1")
        assert len(lesson_state["concepts"]) == 2

        # Patch with hyphenated ID — should match prefer_native_html
        cache.apply_lesson_state_patch("sess-1", {
            "concept_updates": [
                {"concept_id": "prefer-native-html", "status": "covered"},
            ],
        })
        lesson_state = cache.get_lesson_state("sess-1")
        assert len(lesson_state["concepts"]) == 2  # no duplicate
        assert lesson_state["concepts"][0]["status"] == "covered"

        # Patch with raw label as ID — should match dont_change_semantics
        cache.apply_lesson_state_patch("sess-1", {
            "concept_updates": [
                {"concept_id": "Rule 2: don't change native semantics", "status": "in_progress"},
            ],
        })
        lesson_state = cache.get_lesson_state("sess-1")
        assert len(lesson_state["concepts"]) == 2  # still no duplicate
        assert lesson_state["concepts"][1]["status"] == "in_progress"

    def test_apply_patch_resolves_active_concept_fuzzy(self, cache):
        """active_concept in a patch should resolve to canonical ID."""
        cache.store("sess-1", "obj-1", "Objective", [], "", "content")
        cache.store_teaching_plan(
            "sess-1",
            plan=None,
            extracted_concepts=[
                {"id": "prefer_native_html", "label": "Prefer native HTML"},
                {"id": "keyboard_support", "label": "Keyboard support"},
            ],
        )
        cache.apply_lesson_state_patch("sess-1", {
            "active_concept": "prefer-native-html",  # hyphenated variant
        })
        lesson_state = cache.get_lesson_state("sess-1")
        assert lesson_state["active_concept"] == "prefer_native_html"  # resolved to canonical


class TestAdaptivePacing:
    def test_preview_pacing_state_waits_for_window(self, cache):
        cache.store("sess-1", "obj-1", "Objective", [], "", "content")

        preview = cache.preview_pacing_state(
            "sess-1",
            {
                "grasp_level": "fragile",
                "reasoning_mode": "paraphrase",
                "support_needed": "moderate",
                "confusion_level": "medium",
                "response_pattern": "hedging",
                "concept_closure": "not_ready",
                "override_pace": "none",
                "recommended_next_step": "ask_narrower",
            },
        )

        assert preview["current_pace"] == "steady"
        assert len(preview["recent_signals"]) == 1

    def test_apply_pacing_signal_slows_after_repeated_confusion(self, cache):
        cache.store("sess-1", "obj-1", "Objective", [], "", "content")
        signal = {
            "grasp_level": "fragile",
            "reasoning_mode": "paraphrase",
            "support_needed": "heavy",
            "confusion_level": "high",
            "response_pattern": "hedging",
            "concept_closure": "not_ready",
            "override_pace": "none",
            "recommended_next_step": "re-explain",
        }

        for _ in range(3):
            pacing_state = cache.apply_pacing_signal("sess-1", signal)

        assert pacing_state["current_pace"] == "slow"
        assert "slow" in pacing_state["pace_reason"].lower() or "scaffold" in pacing_state["pace_reason"].lower()
        assert pacing_state["cooldown_remaining"] == 2

    def test_apply_pacing_signal_speeds_up_after_stable_transfer(self, cache):
        cache.store("sess-1", "obj-1", "Objective", [], "", "content")
        signal = {
            "grasp_level": "solid",
            "reasoning_mode": "transfer",
            "support_needed": "none",
            "confusion_level": "low",
            "response_pattern": "direct",
            "concept_closure": "ready",
            "override_pace": "none",
            "recommended_next_step": "advance",
        }

        for _ in range(3):
            pacing_state = cache.apply_pacing_signal("sess-1", signal)

        assert pacing_state["current_pace"] == "fast"
        assert "pace can increase" in pacing_state["pace_reason"].lower()

    def test_cooldown_blocks_immediate_flip_from_slow_to_fast(self, cache):
        cache.store("sess-1", "obj-1", "Objective", [], "", "content")
        slow_signal = {
            "grasp_level": "fragile",
            "reasoning_mode": "paraphrase",
            "support_needed": "heavy",
            "confusion_level": "high",
            "response_pattern": "hedging",
            "concept_closure": "not_ready",
            "override_pace": "none",
            "recommended_next_step": "re-explain",
        }
        fast_signal = {
            "grasp_level": "solid",
            "reasoning_mode": "transfer",
            "support_needed": "none",
            "confusion_level": "low",
            "response_pattern": "direct",
            "concept_closure": "ready",
            "override_pace": "none",
            "recommended_next_step": "advance",
        }

        for _ in range(3):
            cache.apply_pacing_signal("sess-1", slow_signal)

        pacing_state = cache.apply_pacing_signal("sess-1", fast_signal)
        pacing_state = cache.apply_pacing_signal("sess-1", fast_signal)

        assert pacing_state["current_pace"] == "slow"
