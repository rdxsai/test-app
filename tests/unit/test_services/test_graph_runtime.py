from question_app.services.tutor.graph_runtime import (
    build_graph_runtime_patch,
    fallback_graph_decision,
)
from question_app.services.tutor.session_cache import SessionContentCache


def test_graph_decision_blocks_advance_when_must_repair_is_open():
    graph_state = {
        "active_node_id": "n1",
        "primary_route": ["n1", "n2"],
        "node_labels": {"n1": "Names", "n2": "Roles"},
    }
    analysis = {
        "stage_action": "advance",
        "teaching_move": "continue",
        "pacing_signal": {"concept_closure": "ready"},
        "misconception_events": [
            {
                "text": "Treats visible text and accessible name as unrelated.",
                "action": "log",
                "repair_priority": "must_address_now",
            }
        ],
    }

    decision = fallback_graph_decision(graph_state, analysis)

    assert decision["graph_action"] == "stay"
    assert decision["allowed_teaching_move"] == "repair_current_node"
    assert decision["accepted_analyzer_recommendation"] is False
    assert "must-address misconception" in decision["override_reason"]
    assert "Do not recommend graph advancement" in decision["analyzer_feedback"]


def test_graph_runtime_patch_advances_route_and_records_decision():
    graph_state = {
        "active_node_id": "n1",
        "active_edge_id": "",
        "primary_route": ["n1", "n2", "n3"],
        "completed_node_ids": [],
        "visited_node_ids": ["n1"],
        "node_status": {"n1": "active", "n2": "locked", "n3": "locked"},
        "repair_count_for_active_node": 2,
    }
    decision = {
        "graph_action": "advance",
        "active_node_id": "n2",
        "active_edge_id": "n1->n2",
        "allowed_teaching_move": "introduce_next_node",
        "accepted_analyzer_recommendation": True,
    }

    patch = build_graph_runtime_patch(graph_state, decision)

    assert patch["active_node_id"] == "n2"
    assert patch["active_edge_id"] == "n1->n2"
    assert patch["completed_node_ids"] == ["n1"]
    assert patch["visited_node_ids"] == ["n1", "n2"]
    assert patch["node_status"]["n1"] == "covered"
    assert patch["node_status"]["n2"] == "active"
    assert patch["repair_count_for_active_node"] == 0
    assert patch["previous_orchestrator_override"] is None


def test_session_cache_derives_graph_runtime_state_from_retrieval_bundle():
    cache = SessionContentCache()
    cache.store(
        "sess-1",
        "obj-1",
        "Explain accessible names",
        [],
        "",
        "teaching content",
        retrieval_bundle={
            "graph": {
                "primary_route": ["name", "role", "integration"],
                "nodes": [
                    {"id": "name", "label": "Accessible names"},
                    {"id": "role", "label": "Semantic roles"},
                    {"id": "integration", "label": "Real control audit"},
                ],
            }
        },
    )

    graph_state = cache.get_graph_runtime_state("sess-1")

    assert graph_state["active_node_id"] == "name"
    assert graph_state["primary_route"] == ["name", "role", "integration"]
    assert graph_state["node_labels"]["role"] == "Semantic roles"
    assert graph_state["node_status"]["name"] == "active"
    assert graph_state["node_status"]["role"] == "locked"
