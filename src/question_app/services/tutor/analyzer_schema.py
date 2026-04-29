"""Structured turn-analyzer schema adapters.

The canonical analyzer contract is the grouped, non-overlapping schema used by
the model prompt. Legacy conversion is intentionally kept here so older runtime
consumers can be migrated without reintroducing duplicate model-facing signals.
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional


TURN_ROUTES = {"objective_answer", "adjacent_topic", "meta_request", "off_topic"}
OPEN_QUESTION_TYPES = {
    "none",
    "clarification",
    "edge_case",
    "implementation",
    "scope_boundary",
    "meta",
}
TUTOR_MOVES = {"continue", "clarify", "repair", "consolidate", "redirect"}
SUPPORT_LEVELS = {"heavy", "moderate", "light", "none"}
SOURCE_CERTAINTY_LEVELS = {"none", "low", "medium", "high"}
STAGE_ACTIONS = {"stay", "advance", "regress"}
TARGET_STAGES = {
    "onboarding",
    "introduction",
    "exploration",
    "readiness_check",
    "mini_assessment",
    "final_assessment",
    "transition",
}
CLOSURE_STATES = {"not_ready", "almost_ready", "ready"}
EVIDENCE_QUALITY = {"none", "weak", "partial", "strong"}
PROGRESSION_BLOCKERS = {
    "none",
    "open_question",
    "misconception",
    "weak_evidence",
    "coverage_gap",
    "terminal_node",
    "source_uncertainty",
}
BRIDGE_MODES = {
    "none",
    "answer_within_current_node",
    "temporary_bridge",
    "entry_into_next_node",
    "integration",
    "terminal_assessment",
}
CONCEPT_STATUSES = {"not_covered", "in_progress", "covered"}
MISCONCEPTION_ACTIONS = {"log", "still_active", "resolve_candidate"}
MISCONCEPTION_PRIORITIES = {"normal", "must_address_now"}
MASTERY_LEVELS = {
    "not_attempted",
    "misconception",
    "in_progress",
    "assessment_ready",
    "partial",
    "mastered",
}
CONSISTENCY_STATUSES = {"consistent", "needs_repair"}


def _string(value: Any, default: str = "") -> str:
    text = str(value or "").strip()
    return text if text else default


def _enum(value: Any, allowed: set[str], default: str) -> str:
    text = _string(value).lower()
    return text if text in allowed else default


def _bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "1"}:
            return True
        if lowered in {"false", "no", "0"}:
            return False
    return default


def _list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if value in (None, "", {}):
        return []
    return [value]


def _support_from_old(value: Any) -> str:
    return _enum(value, SUPPORT_LEVELS, "moderate")


def _evidence_from_reasoning(value: Any) -> str:
    mode = _string(value).lower()
    if mode == "transfer":
        return "strong"
    if mode == "application":
        return "partial"
    if mode in {"recall", "paraphrase"}:
        return "weak"
    return "none" if mode == "guessing" else "partial"


def _reasoning_from_evidence(value: Any) -> str:
    quality = _enum(value, EVIDENCE_QUALITY, "partial")
    return {
        "none": "guessing",
        "weak": "recall",
        "partial": "application",
        "strong": "transfer",
    }[quality]


def _grasp_from_support(support: str, evidence: str) -> str:
    if support == "heavy" or evidence in {"none", "weak"}:
        return "fragile"
    if support == "moderate" or evidence == "partial":
        return "emerging"
    return "solid"


def _confusion_from_support(support: str) -> str:
    return {"heavy": "high", "moderate": "medium", "light": "low", "none": "low"}.get(
        support,
        "medium",
    )


def _next_step_from_move(move: str, closure: str) -> str:
    if closure == "ready" and move in {"continue", "consolidate"}:
        return "advance"
    if move == "repair":
        return "re-explain"
    if move == "clarify":
        return "give_example"
    if move == "consolidate" and closure == "ready":
        return "advance"
    if move == "redirect":
        return "ask_narrower"
    return "ask_same_level"


def default_analyzer_output(
    *,
    student_response: str = "",
    current_stage: str = "introduction",
) -> Dict[str, Any]:
    """Return a conservative canonical analyzer output."""
    stage = _enum(current_stage, TARGET_STAGES, "introduction")
    return {
        "student_turn": {
            "route": "objective_answer",
            "answer_first": True,
            "question_to_answer": _string(student_response)[:160],
            "open_question_type": "clarification",
        },
        "next_tutor_handoff": {
            "move": "continue",
            "support_level": "moderate",
            "one_turn_goal": "Answer the student's current question and keep the lesson anchored.",
            "source_certainty_needed": "low",
        },
        "progression_recommendation": {
            "stage_action": "stay",
            "target_stage": stage,
            "closure_state": "not_ready",
            "evidence_quality": "weak",
            "progression_blocker": "open_question",
        },
        "graph_handoff": {
            "bridge_mode": "answer_within_current_node",
            "current_node_id": "",
            "candidate_next_node_id": "",
            "return_to_current_node": True,
        },
        "state_patch": {
            "active_concept_id": "",
            "pending_check": "",
            "concept_updates": [],
        },
        "misconceptions": [],
        "mastery_signal": {
            "update": False,
            "level": "not_attempted",
        },
        "memory_patch": {
            "objective_summary": "",
            "learner_summary": "",
            "next_focus": "",
        },
        "consistency_check": {
            "status": "consistent",
            "conflict": "",
            "repair_instruction": "",
        },
    }


def is_canonical_analyzer_output(payload: Optional[Dict[str, Any]]) -> bool:
    return isinstance(payload, dict) and isinstance(payload.get("student_turn"), dict)


def normalize_analyzer_output(
    payload: Optional[Dict[str, Any]],
    *,
    student_response: str = "",
    current_stage: str = "introduction",
) -> Dict[str, Any]:
    """Normalize old or new analyzer output into the canonical grouped schema."""
    base = default_analyzer_output(
        student_response=student_response,
        current_stage=current_stage,
    )
    payload = copy.deepcopy(payload or {})
    if not isinstance(payload, dict):
        return base

    if not is_canonical_analyzer_output(payload):
        payload = legacy_to_analyzer_output(
            payload,
            student_response=student_response,
            current_stage=current_stage,
        )

    out = copy.deepcopy(base)
    student_turn = payload.get("student_turn") or {}
    out["student_turn"] = {
        "route": _enum(student_turn.get("route"), TURN_ROUTES, "objective_answer"),
        "answer_first": _bool(student_turn.get("answer_first"), True),
        "question_to_answer": _string(
            student_turn.get("question_to_answer"),
            _string(student_response)[:160],
        )[:220],
        "open_question_type": _enum(
            student_turn.get("open_question_type"),
            OPEN_QUESTION_TYPES,
            "none",
        ),
    }

    tutor = payload.get("next_tutor_handoff") or {}
    out["next_tutor_handoff"] = {
        "move": _enum(tutor.get("move"), TUTOR_MOVES, "continue"),
        "support_level": _support_from_old(tutor.get("support_level")),
        "one_turn_goal": _string(tutor.get("one_turn_goal"))[:280],
        "source_certainty_needed": _enum(
            tutor.get("source_certainty_needed"),
            SOURCE_CERTAINTY_LEVELS,
            "low",
        ),
    }

    progression = payload.get("progression_recommendation") or {}
    target_stage = _enum(
        progression.get("target_stage"),
        TARGET_STAGES,
        out["progression_recommendation"]["target_stage"],
    )
    out["progression_recommendation"] = {
        "stage_action": _enum(progression.get("stage_action"), STAGE_ACTIONS, "stay"),
        "target_stage": target_stage,
        "closure_state": _enum(
            progression.get("closure_state"),
            CLOSURE_STATES,
            "not_ready",
        ),
        "evidence_quality": _enum(
            progression.get("evidence_quality"),
            EVIDENCE_QUALITY,
            "weak",
        ),
        "progression_blocker": _enum(
            progression.get("progression_blocker"),
            PROGRESSION_BLOCKERS,
            "open_question",
        ),
    }

    graph = payload.get("graph_handoff") or {}
    out["graph_handoff"] = {
        "bridge_mode": _enum(
            graph.get("bridge_mode"),
            BRIDGE_MODES,
            "answer_within_current_node",
        ),
        "current_node_id": _string(graph.get("current_node_id"))[:80],
        "candidate_next_node_id": _string(graph.get("candidate_next_node_id"))[:80],
        "return_to_current_node": _bool(graph.get("return_to_current_node"), True),
    }

    state = payload.get("state_patch") or {}
    concept_updates = []
    for item in _list(state.get("concept_updates")):
        if not isinstance(item, dict):
            continue
        concept_id = _string(item.get("concept_id"))[:80]
        if not concept_id:
            continue
        concept_updates.append(
            {
                "concept_id": concept_id,
                "status": _enum(item.get("status"), CONCEPT_STATUSES, "in_progress"),
            }
        )
    out["state_patch"] = {
        "active_concept_id": _string(state.get("active_concept_id"))[:120],
        "pending_check": _string(state.get("pending_check"))[:280],
        "concept_updates": concept_updates,
    }

    misconceptions = []
    for item in _list(payload.get("misconceptions")):
        if not isinstance(item, dict):
            continue
        key = _string(item.get("key"))[:100]
        repair_focus = _string(item.get("repair_focus"))[:280]
        if not key and not repair_focus:
            continue
        misconceptions.append(
            {
                "key": key or "misconception",
                "action": _enum(
                    item.get("action"),
                    MISCONCEPTION_ACTIONS,
                    "still_active",
                ),
                "priority": _enum(
                    item.get("priority"),
                    MISCONCEPTION_PRIORITIES,
                    "normal",
                ),
                "repair_focus": repair_focus,
            }
        )
    out["misconceptions"] = misconceptions

    mastery = payload.get("mastery_signal") or {}
    out["mastery_signal"] = {
        "update": _bool(mastery.get("update"), False),
        "level": _enum(mastery.get("level"), MASTERY_LEVELS, "not_attempted"),
    }

    memory = payload.get("memory_patch") or {}
    out["memory_patch"] = {
        "objective_summary": _string(memory.get("objective_summary"))[:320],
        "learner_summary": _string(memory.get("learner_summary"))[:320],
        "next_focus": _string(memory.get("next_focus"))[:220],
    }

    consistency = payload.get("consistency_check") or {}
    out["consistency_check"] = {
        "status": _enum(
            consistency.get("status"),
            CONSISTENCY_STATUSES,
            "consistent",
        ),
        "conflict": _string(consistency.get("conflict"))[:280],
        "repair_instruction": _string(consistency.get("repair_instruction"))[:280],
    }
    _mark_consistency_conflicts(out)
    return out


def _mark_consistency_conflicts(output: Dict[str, Any]) -> None:
    """Flag contradictions between grouped sections without choosing pedagogy.

    This is a schema integrity check, not a lesson policy. It only catches
    impossible or internally conflicting combinations so the orchestrator can
    narrow the move instead of treating mixed signals as authoritative.
    """
    tutor = output.get("next_tutor_handoff") or {}
    progression = output.get("progression_recommendation") or {}
    graph = output.get("graph_handoff") or {}
    state = output.get("state_patch") or {}
    mastery = output.get("mastery_signal") or {}
    consistency = output.setdefault("consistency_check", {})

    conflicts: List[str] = []
    if (
        progression.get("stage_action") == "advance"
        and progression.get("closure_state") != "ready"
    ):
        conflicts.append("stage_action=advance requires closure_state=ready")
    if progression.get("stage_action") == "advance" and progression.get(
        "evidence_quality"
    ) in {"none", "weak"}:
        conflicts.append("stage_action=advance requires stronger evidence_quality")
    if (
        progression.get("progression_blocker") not in {"", "none"}
        and progression.get("stage_action") == "advance"
    ):
        conflicts.append("stage_action=advance conflicts with progression_blocker")
    if (
        progression.get("closure_state") == "ready"
        and progression.get("progression_blocker") == "none"
        and tutor.get("move") in {"repair", "clarify"}
    ):
        conflicts.append(
            "ready/no-blocker progression conflicts with repair/clarify move"
        )
    if (
        graph.get("bridge_mode") == "temporary_bridge"
        and graph.get("return_to_current_node") is True
        and state.get("active_concept_id")
        and state.get("active_concept_id") == graph.get("candidate_next_node_id")
    ):
        conflicts.append("temporary bridge cannot also make candidate_next_node active")
    if mastery.get("update") and progression.get("evidence_quality") in {
        "none",
        "weak",
    }:
        conflicts.append("mastery update requires partial or strong evidence")

    if not conflicts:
        return
    existing = _string(consistency.get("conflict"))
    joined = "; ".join(conflicts)
    consistency["status"] = "needs_repair"
    consistency["conflict"] = f"{existing}; {joined}".strip("; ")
    if not _string(consistency.get("repair_instruction")):
        consistency[
            "repair_instruction"
        ] = "Choose one owner for the disputed decision and use the conservative stay/clarify interpretation."


def legacy_to_analyzer_output(
    legacy: Optional[Dict[str, Any]],
    *,
    student_response: str = "",
    current_stage: str = "introduction",
) -> Dict[str, Any]:
    """Convert the former flat analyzer schema into the canonical grouped form."""
    legacy = copy.deepcopy(legacy or {})
    base = default_analyzer_output(
        student_response=student_response,
        current_stage=current_stage,
    )
    pacing = legacy.get("pacing_signal") or {}
    lesson = legacy.get("lesson_state_patch") or {}
    bridge = legacy.get("bridge_scope") or {}
    consistency = legacy.get("self_consistency") or {}
    mastery = legacy.get("mastery_signal") or {}
    objective_memory = legacy.get("objective_memory_patch") or {}
    learner_memory = legacy.get("learner_memory_patch") or {}

    base["student_turn"] = {
        "route": legacy.get("turn_route", "objective_answer"),
        "answer_first": legacy.get("answer_current_question_first", True),
        "question_to_answer": legacy.get(
            "student_question_to_answer",
            _string(student_response)[:160],
        ),
        "open_question_type": "clarification"
        if legacy.get("student_question_to_answer")
        else "none",
    }
    base["next_tutor_handoff"] = {
        "move": legacy.get("teaching_move", "continue"),
        "support_level": pacing.get("support_needed", "moderate"),
        "one_turn_goal": (
            pacing.get("override_reason")
            or legacy.get("stage_reason")
            or pacing.get("recommended_next_step")
            or ""
        ),
        "source_certainty_needed": "medium"
        if "wcag" in _string(legacy.get("student_question_to_answer")).lower()
        else "low",
    }
    base["progression_recommendation"] = {
        "stage_action": legacy.get("stage_action", "stay"),
        "target_stage": legacy.get("target_stage", current_stage),
        "closure_state": pacing.get("concept_closure", "not_ready"),
        "evidence_quality": _evidence_from_reasoning(pacing.get("reasoning_mode")),
        "progression_blocker": (
            "misconception"
            if any(
                isinstance(item, dict)
                and item.get("repair_priority") == "must_address_now"
                and item.get("action") != "resolve_candidate"
                for item in legacy.get("misconception_events", []) or []
            )
            else "open_question"
            if legacy.get("answer_current_question_first")
            and legacy.get("student_question_to_answer")
            else "none"
        ),
    }
    base["graph_handoff"] = {
        "bridge_mode": bridge.get("mode", "answer_within_current_node"),
        "current_node_id": bridge.get("current_node_basis", ""),
        "candidate_next_node_id": bridge.get("candidate_next_node", ""),
        "return_to_current_node": bridge.get("return_to_current_node", True),
    }
    base["state_patch"] = {
        "active_concept_id": lesson.get("active_concept", ""),
        "pending_check": lesson.get("pending_check", ""),
        "concept_updates": [
            {
                "concept_id": _string(item.get("concept_id")),
                "status": _string(item.get("status"), "in_progress"),
            }
            for item in _list(lesson.get("concept_updates"))
            if isinstance(item, dict) and _string(item.get("concept_id"))
        ],
    }
    base["misconceptions"] = [
        {
            "key": _string(item.get("key"), "misconception"),
            "action": item.get("action", "still_active"),
            "priority": item.get("repair_priority", "normal"),
            "repair_focus": item.get("text", ""),
        }
        for item in _list(legacy.get("misconception_events"))
        if isinstance(item, dict)
    ]
    base["mastery_signal"] = {
        "update": mastery.get("should_update", False),
        "level": mastery.get("level", "not_attempted"),
    }
    base["memory_patch"] = {
        "objective_summary": objective_memory.get("summary", ""),
        "learner_summary": learner_memory.get("summary", ""),
        "next_focus": objective_memory.get("next_focus", ""),
    }
    needs_repair = bool(consistency.get("needs_repair"))
    fields_agree = consistency.get("fields_agree")
    base["consistency_check"] = {
        "status": "needs_repair"
        if needs_repair or fields_agree is False
        else "consistent",
        "conflict": consistency.get("repair_note", ""),
        "repair_instruction": consistency.get("repair_note", ""),
    }
    return normalize_analyzer_output(
        base,
        student_response=student_response,
        current_stage=current_stage,
    )


def runtime_misconception_events(
    payload: Optional[Dict[str, Any]],
) -> List[Dict[str, str]]:
    """Map canonical misconception records to the cache/event representation."""
    canonical = normalize_analyzer_output(payload)
    return [
        {
            "key": item["key"],
            "text": item["repair_focus"],
            "action": item["action"],
            "repair_priority": item["priority"],
            "repair_scope": "distinction",
            "repair_pattern": "direct_recheck",
        }
        for item in canonical["misconceptions"]
    ]


def runtime_lesson_state_patch(
    payload: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Map canonical state_patch/graph_handoff to lesson-state cache patch."""
    canonical = normalize_analyzer_output(payload)
    graph = canonical["graph_handoff"]
    state = canonical["state_patch"]
    return {
        "active_concept": state["active_concept_id"],
        "pending_check": state["pending_check"],
        "bridge_back_target": graph["current_node_id"]
        if graph["return_to_current_node"]
        else "",
        "concept_updates": copy.deepcopy(state["concept_updates"]),
    }


def runtime_pacing_signal(payload: Optional[Dict[str, Any]]) -> Dict[str, str]:
    """Map canonical handoff/progression fields to pacing cache signal."""
    canonical = normalize_analyzer_output(payload)
    tutor = canonical["next_tutor_handoff"]
    progression = canonical["progression_recommendation"]
    support = tutor["support_level"]
    evidence = progression["evidence_quality"]
    closure = progression["closure_state"]
    move = tutor["move"]
    return {
        "grasp_level": _grasp_from_support(support, evidence),
        "reasoning_mode": _reasoning_from_evidence(evidence),
        "support_needed": support,
        "confusion_level": _confusion_from_support(support),
        "response_pattern": "direct",
        "concept_closure": closure,
        "override_pace": "slow"
        if support == "heavy"
        else "fast"
        if support == "none"
        else "steady",
        "override_reason": tutor["one_turn_goal"],
        "recommended_next_step": _next_step_from_move(move, closure),
    }


def runtime_objective_memory_patch(
    payload: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Map canonical memory patch to objective-memory persistence patch."""
    canonical = normalize_analyzer_output(payload)
    memory = canonical["memory_patch"]
    return {
        "summary": memory["objective_summary"],
        "demonstrated_skills_add": [],
        "active_gaps_current": [],
        "next_focus": memory["next_focus"],
    }


def runtime_learner_memory_patch(
    payload: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Map canonical memory patch to learner-memory persistence patch."""
    canonical = normalize_analyzer_output(payload)
    memory = canonical["memory_patch"]
    return {
        "summary": memory["learner_summary"],
        "strengths_add": [],
        "support_needs_current": [],
        "tendencies_current": [],
        "successful_strategies_add": [],
    }


def canonical_progression(payload: Optional[Dict[str, Any]]) -> Dict[str, str]:
    return normalize_analyzer_output(payload)["progression_recommendation"]


def canonical_student_turn(payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    return normalize_analyzer_output(payload)["student_turn"]


def canonical_tutor_handoff(payload: Optional[Dict[str, Any]]) -> Dict[str, str]:
    return normalize_analyzer_output(payload)["next_tutor_handoff"]


def canonical_consistency_check(payload: Optional[Dict[str, Any]]) -> Dict[str, str]:
    return normalize_analyzer_output(payload)["consistency_check"]


def has_open_must_repair(payload: Optional[Dict[str, Any]]) -> bool:
    return any(
        item.get("priority") == "must_address_now"
        and item.get("action") != "resolve_candidate"
        for item in normalize_analyzer_output(payload)["misconceptions"]
    )


def canonical_to_trace_legacy(payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Compatibility view for old trace readers only; not used by live runtime."""
    canonical = normalize_analyzer_output(payload)
    student_turn = canonical["student_turn"]
    tutor = canonical["next_tutor_handoff"]
    progression = canonical["progression_recommendation"]
    graph = canonical["graph_handoff"]
    state = canonical["state_patch"]
    mastery = canonical["mastery_signal"]
    memory = canonical["memory_patch"]
    consistency = canonical["consistency_check"]

    evidence = progression["evidence_quality"]
    move = tutor["move"]
    pacing = runtime_pacing_signal(canonical)
    if move == "repair" and consistency["status"] == "needs_repair":
        pacing["recommended_next_step"] = "ask_narrower"

    trace = {
        "turn_route": student_turn["route"],
        "answer_current_question_first": student_turn["answer_first"],
        "student_question_to_answer": student_turn["question_to_answer"],
        "teaching_move": move,
        "stage_action": progression["stage_action"],
        "target_stage": progression["target_stage"],
        "stage_reason": consistency["conflict"] or progression["progression_blocker"],
        "bridge_scope": {
            "mode": graph["bridge_mode"],
            "current_node_basis": graph["current_node_id"],
            "candidate_next_node": graph["candidate_next_node_id"],
            "return_to_current_node": graph["return_to_current_node"],
            "reason": "",
        },
        "self_consistency": {
            "current_node_basis": graph["current_node_id"],
            "proposed_active_concept": state["active_concept_id"],
            "concept_closure_evidence": evidence,
            "stage_progression_intent": progression["stage_action"],
            "graph_progression_intent": "advance"
            if graph["bridge_mode"] == "entry_into_next_node"
            else "integrate"
            if graph["bridge_mode"] == "integration"
            else "terminal_assessment"
            if graph["bridge_mode"] == "terminal_assessment"
            else "stay",
            "fields_agree": consistency["status"] == "consistent",
            "needs_repair": consistency["status"] == "needs_repair",
            "repair_note": consistency["repair_instruction"] or consistency["conflict"],
        },
        "mastery_signal": {
            "should_update": mastery["update"],
            "level": mastery["level"],
            "confidence": 0.0,
            "evidence_summary": memory["objective_summary"],
        },
        "misconception_events": runtime_misconception_events(canonical),
        "lesson_state_patch": runtime_lesson_state_patch(canonical),
        "pacing_signal": pacing,
        "objective_memory_patch": runtime_objective_memory_patch(canonical),
        "learner_memory_patch": runtime_learner_memory_patch(canonical),
    }
    if "optional" in tutor.get("one_turn_goal", "").lower():
        trace["follow_up_question_policy"] = "optional_if_explanation_suffices"
    return trace
