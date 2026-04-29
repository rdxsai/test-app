from question_app.services.tutor.analyzer_schema import (
    analyzer_output_to_legacy,
    default_analyzer_output,
    normalize_analyzer_output,
)


def test_default_analyzer_output_uses_grouped_non_overlapping_sections():
    output = default_analyzer_output(
        student_response="Can you explain the next edge case?",
        current_stage="exploration",
    )

    assert set(output) == {
        "student_turn",
        "next_tutor_handoff",
        "progression_recommendation",
        "graph_handoff",
        "state_patch",
        "misconceptions",
        "mastery_signal",
        "memory_patch",
        "consistency_check",
    }
    assert output["student_turn"]["answer_first"] is True
    assert output["progression_recommendation"]["stage_action"] == "stay"
    assert output["progression_recommendation"]["target_stage"] == "exploration"
    assert output["graph_handoff"]["bridge_mode"] == "answer_within_current_node"


def test_normalize_analyzer_output_converts_legacy_shape_to_canonical_schema():
    legacy = {
        "turn_route": "objective_answer",
        "answer_current_question_first": True,
        "student_question_to_answer": "Does this always require a table?",
        "teaching_move": "clarify",
        "stage_action": "stay",
        "target_stage": "exploration",
        "bridge_scope": {
            "mode": "temporary_bridge",
            "current_node_basis": "n6",
            "candidate_next_node": "n7",
            "return_to_current_node": True,
        },
        "pacing_signal": {
            "support_needed": "light",
            "reasoning_mode": "transfer",
            "concept_closure": "almost_ready",
        },
        "lesson_state_patch": {
            "active_concept": "n6",
            "pending_check": "Close the table boundary.",
            "concept_updates": [{"concept_id": "n6", "status": "in_progress"}],
        },
        "misconception_events": [
            {
                "key": "table_absolutism",
                "text": "Overgeneralizes tables.",
                "action": "log",
                "repair_priority": "normal",
            }
        ],
    }

    output = normalize_analyzer_output(legacy, current_stage="exploration")

    assert output["student_turn"]["question_to_answer"] == (
        "Does this always require a table?"
    )
    assert output["next_tutor_handoff"]["move"] == "clarify"
    assert output["next_tutor_handoff"]["support_level"] == "light"
    assert output["progression_recommendation"]["evidence_quality"] == "strong"
    assert output["graph_handoff"]["bridge_mode"] == "temporary_bridge"
    assert output["state_patch"]["active_concept_id"] == "n6"
    assert output["misconceptions"][0]["priority"] == "normal"


def test_analyzer_output_to_legacy_maps_canonical_schema_for_runtime_consumers():
    canonical = normalize_analyzer_output(
        {
            "student_turn": {
                "route": "objective_answer",
                "answer_first": False,
                "question_to_answer": "",
                "open_question_type": "none",
            },
            "next_tutor_handoff": {
                "move": "consolidate",
                "support_level": "none",
                "one_turn_goal": "Close the concept and move on.",
                "source_certainty_needed": "low",
            },
            "progression_recommendation": {
                "stage_action": "advance",
                "target_stage": "readiness_check",
                "closure_state": "ready",
                "evidence_quality": "strong",
                "progression_blocker": "none",
            },
            "graph_handoff": {
                "bridge_mode": "entry_into_next_node",
                "current_node_id": "n6",
                "candidate_next_node_id": "n7",
                "return_to_current_node": False,
            },
            "state_patch": {
                "active_concept_id": "n7",
                "pending_check": "Introduce media alternatives.",
                "concept_updates": [{"concept_id": "n6", "status": "covered"}],
            },
            "misconceptions": [],
            "mastery_signal": {"update": True, "level": "in_progress"},
            "memory_patch": {
                "objective_summary": "Student closed chart sufficiency.",
                "learner_summary": "Learner transfers well.",
                "next_focus": "Media alternatives",
            },
            "consistency_check": {
                "status": "consistent",
                "conflict": "",
                "repair_instruction": "",
            },
        }
    )

    legacy = analyzer_output_to_legacy(canonical)

    assert legacy["stage_action"] == "advance"
    assert legacy["target_stage"] == "readiness_check"
    assert legacy["teaching_move"] == "consolidate"
    assert legacy["pacing_signal"]["concept_closure"] == "ready"
    assert legacy["pacing_signal"]["recommended_next_step"] == "advance"
    assert legacy["lesson_state_patch"]["active_concept"] == "n7"
    assert legacy["mastery_signal"]["should_update"] is True
