from __future__ import annotations

import copy
import json
from typing import Any, Dict, List, Optional

GRAPH_ORCHESTRATOR_SCHEMA: Dict[str, Any] = {
    "graph_action": "stay | advance | integrate",
    "active_node_id": "string",
    "next_node_id": "string",
    "active_edge_id": "string",
    "route_position_before": 0,
    "route_position_after": 0,
    "expected_next_node_id": "string",
    "skipped_node_ids": [],
    "skip_rationale": "string",
    "edge_bridge_used": "string",
    "allowed_teaching_move": "string",
    "decision_reason": "string",
    "confidence": 0.0,
    "accepted_analyzer_recommendation": True,
    "override_reason": "string",
    "tutor_directive": "string",
    "analyzer_feedback": "string",
}


GRAPH_ORCHESTRATOR_PROMPT = """You are the graph progression orchestrator for a Socratic tutor.

You do not teach the student. You decide what graph move the tutor is allowed to make next.

Inputs:
- The current teaching graph runtime state.
- The structured turn-analyzer output.
- The current lesson state.

Decision rules:
- The analyzer recommends; you decide.
- Keep the student on the active node if there is an open misconception, fragile grasp, high confusion, or concept_closure is not ready.
- Advance only when the analyzer evidence says the active concept is ready and no must-repair issue remains.
- If you reject an analyzer recommendation, explain the reason so the analyzer can improve next turn.
- Do not invent WCAG or technical facts. You are only controlling progression.
- Do not change the analyzer schema. Your output is only the JSON object below.

Return exactly one JSON object matching this schema:
{
  "graph_action": "stay | advance | integrate",
  "active_node_id": "current node after the decision",
  "next_node_id": "next route node if known, else empty string",
  "active_edge_id": "from->to when bridging, else empty string",
  "route_position_before": 0,
  "route_position_after": 0,
  "expected_next_node_id": "the next primary-route node after the previous active node, else empty string",
  "skipped_node_ids": ["route nodes skipped by this decision, else empty array"],
  "skip_rationale": "required when skipped_node_ids is non-empty, else empty string",
  "edge_bridge_used": "bridge claim used for the transition, else empty string",
  "allowed_teaching_move": "repair_current_node | clarify_current_node | practice_current_node | answer_student_question_then_return | introduce_next_node | integrate_nodes | assess_mastery",
  "decision_reason": "brief reason for the decision",
  "confidence": 0.0,
  "accepted_analyzer_recommendation": true,
  "override_reason": "non-empty only when you reject or narrow the analyzer recommendation",
  "tutor_directive": "specific instruction for what the tutor should do now",
  "analyzer_feedback": "specific feedback to provide to the analyzer next turn, empty if none"
}
"""


def _as_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    return [str(item or "").strip() for item in value if str(item or "").strip()]


def _active_index(graph_state: Dict[str, Any]) -> int:
    route = _as_list(graph_state.get("primary_route"))
    active = str(graph_state.get("active_node_id", "") or "").strip()
    if active in route:
        return route.index(active)
    return 0


def _node_index(route: List[str], node_id: str) -> int:
    return route.index(node_id) if node_id in route else -1


def _next_route_node(route: List[str], node_id: str) -> str:
    index = _node_index(route, node_id)
    if index < 0 or index + 1 >= len(route):
        return ""
    return route[index + 1]


def _edge_bridge(graph_state: Dict[str, Any], edge_id: str) -> str:
    bridges = graph_state.get("edge_bridges") or {}
    return str(bridges.get(edge_id) or "").strip()


def _skipped_nodes(route: List[str], before_node: str, after_node: str) -> List[str]:
    before = _node_index(route, before_node)
    after = _node_index(route, after_node)
    if before < 0 or after < 0 or after <= before + 1:
        return []
    return route[before + 1 : after]


def _has_must_repair(analysis: Dict[str, Any]) -> bool:
    for event in analysis.get("misconception_events", []) or []:
        if not isinstance(event, dict):
            continue
        priority = str(event.get("repair_priority", "") or "").strip().lower()
        action = str(event.get("action", "") or "").strip().lower()
        if priority == "must_address_now" and action != "resolve_candidate":
            return True
    return False


def _analyzer_wants_advance(analysis: Dict[str, Any]) -> bool:
    pacing = analysis.get("pacing_signal") or {}
    return (
        str(analysis.get("stage_action", "") or "").strip().lower() == "advance"
        or str(pacing.get("recommended_next_step", "") or "").strip().lower()
        == "advance"
        or str(pacing.get("concept_closure", "") or "").strip().lower() == "ready"
    )


def _node_label(graph_state: Dict[str, Any], node_id: str) -> str:
    labels = graph_state.get("node_labels") or {}
    return str(labels.get(node_id) or node_id).strip()


def fallback_graph_decision(
    graph_state: Optional[Dict[str, Any]],
    turn_analysis: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    state = graph_state or {}
    analysis = turn_analysis or {}
    route = _as_list(state.get("primary_route"))
    index = _active_index(state)
    active = str(state.get("active_node_id", "") or "").strip()
    if not active and route:
        active = route[index]
    next_node = route[index + 1] if index + 1 < len(route) else ""
    position = index + 1 if route else 0
    must_repair = _has_must_repair(analysis)
    wants_advance = _analyzer_wants_advance(analysis)

    if must_repair:
        reason = "The latest turn contains a must-address misconception."
        return {
            "graph_action": "stay",
            "active_node_id": active,
            "next_node_id": next_node,
            "active_edge_id": "",
            "route_position_before": position,
            "route_position_after": position,
            "expected_next_node_id": next_node,
            "skipped_node_ids": [],
            "skip_rationale": "",
            "edge_bridge_used": "",
            "allowed_teaching_move": "repair_current_node",
            "decision_reason": reason,
            "confidence": 0.9,
            "accepted_analyzer_recommendation": not wants_advance,
            "override_reason": reason if wants_advance else "",
            "tutor_directive": (
                f"Stay on {_node_label(state, active)}. Repair the misconception "
                "before introducing or assessing another graph node."
            ),
            "analyzer_feedback": (
                "Do not recommend graph advancement while a must-address "
                "misconception remains open."
                if wants_advance
                else ""
            ),
        }

    if wants_advance and next_node:
        edge_id = f"{active}->{next_node}" if active else ""
        return {
            "graph_action": "advance",
            "active_node_id": next_node,
            "next_node_id": route[index + 2] if index + 2 < len(route) else "",
            "active_edge_id": edge_id,
            "route_position_before": position,
            "route_position_after": index + 2,
            "expected_next_node_id": next_node,
            "skipped_node_ids": [],
            "skip_rationale": "",
            "edge_bridge_used": _edge_bridge(state, edge_id),
            "allowed_teaching_move": "introduce_next_node",
            "decision_reason": "Analyzer evidence indicates the current node is ready.",
            "confidence": 0.75,
            "accepted_analyzer_recommendation": True,
            "override_reason": "",
            "tutor_directive": (
                f"Briefly close {_node_label(state, active)}, bridge to "
                f"{_node_label(state, next_node)}, then ask one focused check."
            ),
            "analyzer_feedback": "",
        }

    if wants_advance and not next_node:
        return {
            "graph_action": "integrate",
            "active_node_id": active,
            "next_node_id": "",
            "active_edge_id": "",
            "route_position_before": position,
            "route_position_after": position,
            "expected_next_node_id": "",
            "skipped_node_ids": [],
            "skip_rationale": "",
            "edge_bridge_used": "",
            "allowed_teaching_move": "integrate_nodes",
            "decision_reason": "The active node is the end of the route.",
            "confidence": 0.75,
            "accepted_analyzer_recommendation": True,
            "override_reason": "",
            "tutor_directive": (
                "Synthesize the completed graph nodes into one realistic transfer "
                "scenario before assessment."
            ),
            "analyzer_feedback": "",
        }

    teaching_move = str(analysis.get("teaching_move", "") or "").strip().lower()
    if teaching_move == "repair":
        allowed_move = "repair_current_node"
    elif teaching_move == "clarify":
        allowed_move = "clarify_current_node"
    elif (
        str(analysis.get("turn_route", "") or "").strip().lower() != "objective_answer"
    ):
        allowed_move = "answer_student_question_then_return"
    else:
        allowed_move = "practice_current_node"
    return {
        "graph_action": "stay",
        "active_node_id": active,
        "next_node_id": next_node,
        "active_edge_id": "",
        "route_position_before": position,
        "route_position_after": position,
        "expected_next_node_id": next_node,
        "skipped_node_ids": [],
        "skip_rationale": "",
        "edge_bridge_used": "",
        "allowed_teaching_move": allowed_move,
        "decision_reason": "The current node still needs teaching evidence.",
        "confidence": 0.7,
        "accepted_analyzer_recommendation": True,
        "override_reason": "",
        "tutor_directive": (
            f"Stay on {_node_label(state, active)} and make one focused move: "
            f"{allowed_move}."
        ),
        "analyzer_feedback": "",
    }


def normalize_graph_decision(
    decision: Optional[Dict[str, Any]],
    graph_state: Optional[Dict[str, Any]],
    turn_analysis: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    fallback = fallback_graph_decision(graph_state, turn_analysis)
    if not isinstance(decision, dict) or not decision:
        return fallback

    normalized = copy.deepcopy(fallback)
    for key in GRAPH_ORCHESTRATOR_SCHEMA:
        if key in decision:
            normalized[key] = decision[key]

    allowed_actions = {"stay", "advance", "integrate"}
    graph_action = str(normalized.get("graph_action", "") or "").strip().lower()
    if graph_action not in allowed_actions:
        graph_action = fallback["graph_action"]
    normalized["graph_action"] = graph_action

    allowed_moves = {
        "repair_current_node",
        "clarify_current_node",
        "practice_current_node",
        "answer_student_question_then_return",
        "introduce_next_node",
        "integrate_nodes",
        "assess_mastery",
    }
    allowed_move = str(normalized.get("allowed_teaching_move", "") or "").strip()
    if allowed_move not in allowed_moves:
        normalized["allowed_teaching_move"] = fallback["allowed_teaching_move"]

    route = _as_list((graph_state or {}).get("primary_route"))
    previous_active = str((graph_state or {}).get("active_node_id", "") or "").strip()
    before_index = _node_index(route, previous_active)
    active_node_id = str(normalized.get("active_node_id", "") or "").strip()
    if route and active_node_id not in route:
        normalized["active_node_id"] = fallback["active_node_id"]
        active_node_id = normalized["active_node_id"]

    after_index = _node_index(route, active_node_id)
    expected_next = _next_route_node(route, previous_active)
    if str(normalized.get("expected_next_node_id", "") or "").strip() not in set(
        route + [""]
    ):
        normalized["expected_next_node_id"] = expected_next
    elif not str(normalized.get("expected_next_node_id", "") or "").strip():
        normalized["expected_next_node_id"] = expected_next

    route_next = _next_route_node(route, active_node_id)
    next_node_id = str(normalized.get("next_node_id", "") or "").strip()
    if next_node_id == active_node_id or (route and next_node_id not in route and next_node_id):
        normalized["next_node_id"] = route_next

    edge_id = str(normalized.get("active_edge_id", "") or "").strip()
    if normalized["graph_action"] in {"advance", "integrate"} and not edge_id:
        if previous_active and active_node_id and previous_active != active_node_id:
            edge_id = f"{previous_active}->{active_node_id}"
            normalized["active_edge_id"] = edge_id

    skipped = _skipped_nodes(route, previous_active, active_node_id)
    if not isinstance(normalized.get("skipped_node_ids"), list):
        normalized["skipped_node_ids"] = skipped
    else:
        normalized["skipped_node_ids"] = _as_list(normalized["skipped_node_ids"])
    if skipped and not normalized["skipped_node_ids"]:
        normalized["skipped_node_ids"] = skipped
    if edge_id and not str(normalized.get("edge_bridge_used", "") or "").strip():
        normalized["edge_bridge_used"] = _edge_bridge(graph_state or {}, edge_id)

    normalized["route_position_before"] = before_index + 1 if before_index >= 0 else 0
    normalized["route_position_after"] = after_index + 1 if after_index >= 0 else 0

    try:
        confidence = float(normalized.get("confidence", fallback.get("confidence", 0.0)))
    except (TypeError, ValueError):
        confidence = float(fallback.get("confidence", 0.0) or 0.0)
    normalized["confidence"] = min(1.0, max(0.0, confidence))

    for key in (
        "next_node_id",
        "active_edge_id",
        "expected_next_node_id",
        "skip_rationale",
        "edge_bridge_used",
        "decision_reason",
        "override_reason",
        "tutor_directive",
        "analyzer_feedback",
    ):
        normalized[key] = str(normalized.get(key, "") or "").strip()
    normalized["accepted_analyzer_recommendation"] = bool(
        normalized.get("accepted_analyzer_recommendation", True)
    )
    return normalized


def build_graph_runtime_patch(
    graph_state: Optional[Dict[str, Any]],
    decision: Dict[str, Any],
) -> Dict[str, Any]:
    state = graph_state or {}
    route = _as_list(state.get("primary_route"))
    previous_active = str(state.get("active_node_id", "") or "").strip()
    active = str(decision.get("active_node_id", "") or "").strip()
    completed = _as_list(state.get("completed_node_ids"))
    visited = _as_list(state.get("visited_node_ids"))
    node_status = dict(state.get("node_status", {}) or {})

    if decision.get("graph_action") in {"advance", "integrate"} and previous_active:
        if previous_active not in completed:
            completed.append(previous_active)
        node_status[previous_active] = "covered"
    if active:
        if active not in visited:
            visited.append(active)
        node_status[active] = "active"
    for node_id in route:
        node_status.setdefault(node_id, "locked")

    override = None
    if not decision.get("accepted_analyzer_recommendation", True):
        override = {
            "reason": decision.get("override_reason", ""),
            "feedback": decision.get("analyzer_feedback", ""),
        }

    repair_count = int(state.get("repair_count_for_active_node", 0) or 0)
    if active != previous_active:
        repair_count = 0
    elif decision.get("allowed_teaching_move") == "repair_current_node":
        repair_count += 1

    return {
        "active_node_id": active,
        "active_edge_id": decision.get("active_edge_id", ""),
        "completed_node_ids": completed,
        "visited_node_ids": visited,
        "node_status": node_status,
        "mode": decision.get("graph_action", "stay"),
        "repair_count_for_active_node": repair_count,
        "last_orchestrator_decision": copy.deepcopy(decision),
        "previous_orchestrator_override": override,
    }


def format_graph_runtime_context(
    graph_state: Optional[Dict[str, Any]],
    retrieval_bundle: Optional[Dict[str, Any]] = None,
) -> str:
    state = graph_state or {}
    if not state:
        return ""
    active = str(state.get("active_node_id", "") or "").strip()
    route = _as_list(state.get("primary_route"))
    labels = state.get("node_labels") or {}
    route_labels = [f"{node_id}: {labels.get(node_id, node_id)}" for node_id in route]
    graph_type = ""
    if isinstance(retrieval_bundle, dict):
        graph = retrieval_bundle.get("graph")
        if isinstance(graph, dict):
            graph_type = str(graph.get("graph_type", "") or "").strip()
    lines = ["GRAPH RUNTIME CONTEXT:"]
    if graph_type:
        lines.append(f"- graph_type: {graph_type}")
    lines.append(f"- active_node_id: {active}")
    lines.append(f"- active_node_label: {labels.get(active, active)}")
    lines.append(
        "- completed_node_ids: " + ", ".join(_as_list(state.get("completed_node_ids")))
    )
    lines.append("- primary_route: " + " -> ".join(route_labels))
    previous_override = state.get("previous_orchestrator_override")
    if previous_override:
        lines.append(
            "- previous_orchestrator_override: "
            + json.dumps(previous_override, ensure_ascii=True)
        )
    return "\n".join(lines)


def format_orchestrator_directive(decision: Optional[Dict[str, Any]]) -> str:
    if not decision:
        return ""
    allowed_move = str(decision.get("allowed_teaching_move", "") or "").strip()
    lines = [
        "ORCHESTRATOR DIRECTIVE:",
        f"- graph_action: {decision.get('graph_action', '')}",
        f"- active_node_id: {decision.get('active_node_id', '')}",
        f"- route_position_before: {decision.get('route_position_before', '')}",
        f"- route_position_after: {decision.get('route_position_after', '')}",
        f"- expected_next_node_id: {decision.get('expected_next_node_id', '')}",
        f"- skipped_node_ids: {', '.join(_as_list(decision.get('skipped_node_ids')))}",
        f"- active_edge_id: {decision.get('active_edge_id', '')}",
        f"- edge_bridge_used: {decision.get('edge_bridge_used', '')}",
        f"- allowed_teaching_move: {allowed_move}",
        f"- decision_reason: {decision.get('decision_reason', '')}",
        f"- tutor_directive: {decision.get('tutor_directive', '')}",
        "- Do not advance to another graph node unless this directive explicitly allows it.",
    ]
    if allowed_move == "introduce_next_node":
        lines.append(
            "- Required response shape: include one explicit bridge sentence using "
            "`edge_bridge_used` before teaching the new node, then ask one focused check."
        )
    if allowed_move == "assess_mastery":
        lines.append(
            "- Required response shape: ask one clear mastery/transfer assessment "
            "question and wait for the student's answer."
        )
    if decision.get("skipped_node_ids"):
        lines.append(
            "- If any skipped_node_ids are present, explicitly connect why the "
            "student's prior answer already covered them before moving on."
        )
    return "\n".join(lines)


def format_graph_orchestrator_input(
    graph_state: Optional[Dict[str, Any]],
    turn_analysis: Optional[Dict[str, Any]],
    lesson_state: Optional[Dict[str, Any]],
) -> str:
    return json.dumps(
        {
            "graph_runtime_state": graph_state or {},
            "turn_analysis": turn_analysis or {},
            "lesson_state": lesson_state or {},
        },
        ensure_ascii=True,
        indent=2,
    )
