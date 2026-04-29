from question_app.services.tutor.prompts.socratic_tutor import TURN_ANALYZER_PROMPT


def test_turn_analyzer_prompt_requires_consistent_progression_signals():
    assert "Keep progression signals internally consistent" in TURN_ANALYZER_PROMPT
    assert "`concept_closure=almost_ready`, usually use `stage_action=stay`" in (
        TURN_ANALYZER_PROMPT
    )
    assert (
        "Do not pair `recommended_next_step=give_example` with"
        in TURN_ANALYZER_PROMPT
    )
    assert "no open must-repair misconception" in TURN_ANALYZER_PROMPT


def test_turn_analyzer_prompt_separates_bridge_questions_from_node_progression():
    assert "Separate bridge questions from graph/node progression" in (
        TURN_ANALYZER_PROMPT
    )
    assert "does not by itself" in TURN_ANALYZER_PROMPT
    assert "Keep `active_concept` anchored" in TURN_ANALYZER_PROMPT
    assert "Use `bridge_back_target` and `pending_check`" in TURN_ANALYZER_PROMPT


def test_turn_analyzer_prompt_requires_handoff_self_consistency_fields():
    assert "Emit explicit handoff signals" in TURN_ANALYZER_PROMPT
    assert '"bridge_scope"' in TURN_ANALYZER_PROMPT
    assert '"self_consistency"' in TURN_ANALYZER_PROMPT
    assert "Stage progression and graph progression are separate" in (
        TURN_ANALYZER_PROMPT
    )
