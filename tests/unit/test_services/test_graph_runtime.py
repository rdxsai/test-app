from question_app.services.tutor.graph_runtime import (
    build_graph_runtime_patch,
    fallback_graph_decision,
    format_analyzer_graph_context,
    format_orchestrator_directive,
    normalize_graph_decision,
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
    assert graph_state["edge_bridges"] == {}
    assert graph_state["node_status"]["name"] == "active"
    assert graph_state["node_status"]["role"] == "locked"


def test_session_cache_derives_edge_bridges_from_retrieval_bundle():
    cache = SessionContentCache()
    cache.store(
        "sess-1",
        "obj-1",
        "Explain route edges",
        [],
        "",
        "teaching content",
        retrieval_bundle={
            "graph": {
                "primary_route": ["n1", "n2"],
                "nodes": [
                    {"id": "n1", "label": "First"},
                    {"id": "n2", "label": "Second"},
                ],
                "edges": [
                    {
                        "from": "n1",
                        "to": "n2",
                        "bridge_claim": "First concept prepares the second.",
                    }
                ],
            }
        },
    )

    graph_state = cache.get_graph_runtime_state("sess-1")

    assert graph_state["edge_bridges"]["n1->n2"] == (
        "First concept prepares the second."
    )


def test_graph_decision_normalization_exposes_route_audit_fields():
    graph_state = {
        "active_node_id": "n1",
        "primary_route": ["n1", "n2", "n3"],
        "node_labels": {"n1": "First", "n2": "Second", "n3": "Third"},
        "edge_bridges": {"n1->n3": "Compressed bridge."},
    }
    raw_decision = {
        "graph_action": "advance",
        "active_node_id": "n3",
        "next_node_id": "n3",
        "allowed_teaching_move": "introduce_next_node",
        "confidence": "0.82",
        "accepted_analyzer_recommendation": True,
    }

    decision = normalize_graph_decision(raw_decision, graph_state, {})

    assert decision["route_position_before"] == 1
    assert decision["route_position_after"] == 3
    assert decision["expected_next_node_id"] == "n2"
    assert decision["skipped_node_ids"] == ["n2"]
    assert decision["next_node_id"] == ""
    assert decision["active_edge_id"] == "n1->n3"
    assert decision["edge_bridge_used"] == "Compressed bridge."
    assert decision["confidence"] == 0.82


def test_orchestrator_directive_requires_bridge_and_assessment_shapes():
    bridge_directive = format_orchestrator_directive(
        {
            "graph_action": "advance",
            "active_node_id": "n2",
            "allowed_teaching_move": "introduce_next_node",
            "edge_bridge_used": "First concept prepares the second.",
            "skipped_node_ids": [],
        }
    )
    assessment_directive = format_orchestrator_directive(
        {
            "graph_action": "stay",
            "active_node_id": "n3",
            "allowed_teaching_move": "assess_mastery",
            "skipped_node_ids": [],
        }
    )

    assert "include one explicit bridge sentence" in bridge_directive
    assert "`edge_bridge_used`" in bridge_directive
    assert "ask one clear mastery/transfer assessment question" in assessment_directive


def test_analyzer_graph_context_surfaces_orchestrator_feedback():
    context = format_analyzer_graph_context(
        {
            "active_node_id": "n1",
            "primary_route": ["n1", "n2"],
            "node_labels": {"n1": "First", "n2": "Second"},
            "completed_node_ids": [],
            "previous_orchestrator_override": {
                "reason": "Analyzer wanted advancement before repair.",
                "feedback": "Stay on the active node until the misconception is fixed.",
            },
        },
        {"graph": {"graph_type": "teaching_graph"}},
    )

    assert "GRAPH RUNTIME CONTEXT:" in context
    assert "ORCHESTRATOR FEEDBACK FROM LAST TURN:" in context
    assert "Analyzer wanted advancement before repair." in context
    assert "Stay on the active node" in context
    assert "do not repeat the rejected recommendation" in context


def test_analyzer_graph_context_omits_feedback_block_without_override():
    context = format_analyzer_graph_context(
        {
            "active_node_id": "n1",
            "primary_route": ["n1"],
            "node_labels": {"n1": "First"},
        },
        None,
    )

    assert "GRAPH RUNTIME CONTEXT:" in context
    assert "ORCHESTRATOR FEEDBACK FROM LAST TURN:" not in context
