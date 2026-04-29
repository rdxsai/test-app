from question_app.services.tutor.prompts.socratic_tutor import TURN_ANALYZER_PROMPT


def test_turn_analyzer_prompt_requires_consistent_progression_signals():
    assert "Keep progression signals internally consistent" in TURN_ANALYZER_PROMPT
    assert "`closure_state=almost_ready`, usually use `stage_action=stay`" in (
        TURN_ANALYZER_PROMPT
    )
    assert (
        "`evidence_quality=strong`, no real student question must be answered first"
        in TURN_ANALYZER_PROMPT
    )
    assert "no open must-repair misconception" in TURN_ANALYZER_PROMPT


def test_turn_analyzer_prompt_separates_bridge_questions_from_node_progression():
    assert "Separate bridge questions from graph/node progression" in (
        TURN_ANALYZER_PROMPT
    )
    assert "does not by itself" in TURN_ANALYZER_PROMPT
    assert "Keep `state_patch.active_concept_id` anchored" in TURN_ANALYZER_PROMPT
    assert '`graph_handoff.bridge_mode="temporary_bridge"`' in TURN_ANALYZER_PROMPT


def test_turn_analyzer_prompt_classifies_question_ownership():
    assert "Do not treat every student question as a progression blocker" in (
        TURN_ANALYZER_PROMPT
    )
    assert "Current-node blocker" in TURN_ANALYZER_PROMPT
    assert "Next-node entry" in TURN_ANALYZER_PROMPT
    assert 'stage_action="advance"' in TURN_ANALYZER_PROMPT
    assert 'bridge_mode="entry_into_next_node"' in TURN_ANALYZER_PROMPT
    assert "Temporary bridge" in TURN_ANALYZER_PROMPT


def test_turn_analyzer_prompt_tightens_mastery_update_discipline():
    assert "Mastery update discipline" in TURN_ANALYZER_PROMPT
    assert "Prefer `memory_patch` over `mastery_signal.update=true`" in (
        TURN_ANALYZER_PROMPT
    )
    assert (
        "Never set `mastery_signal.update=true` when `evidence_quality` is `none` or"
        in (TURN_ANALYZER_PROMPT)
    )
    assert 'consistency_check.status="needs_repair"' in TURN_ANALYZER_PROMPT


def test_turn_analyzer_prompt_requires_non_overlapping_grouped_schema():
    assert "nine non-overlapping decisions" in TURN_ANALYZER_PROMPT
    assert '"student_turn"' in TURN_ANALYZER_PROMPT
    assert '"next_tutor_handoff"' in TURN_ANALYZER_PROMPT
    assert '"progression_recommendation"' in TURN_ANALYZER_PROMPT
    assert '"graph_handoff"' in TURN_ANALYZER_PROMPT
    assert '"consistency_check"' in TURN_ANALYZER_PROMPT
    assert "Single-ownership rule" in TURN_ANALYZER_PROMPT
    assert "Do not encode the same decision in multiple fields" in TURN_ANALYZER_PROMPT
