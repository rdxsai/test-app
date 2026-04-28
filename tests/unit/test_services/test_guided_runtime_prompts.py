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
