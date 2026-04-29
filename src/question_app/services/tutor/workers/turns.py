from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, List, Optional

from ..graph_runtime import (
    GRAPH_ORCHESTRATOR_PROMPT,
    fallback_graph_decision,
    format_graph_orchestrator_input,
    normalize_graph_decision,
)

TURN_ANALYZER_MAX_TOKENS = 3500
TURN_ANALYZER_REASONING_EFFORT = "medium"
ASSESSMENT_REFLECTOR_MAX_TOKENS = 2500
ASSESSMENT_REFLECTOR_REASONING_EFFORT = "medium"
GRAPH_ORCHESTRATOR_MAX_TOKENS = 2200
GRAPH_ORCHESTRATOR_REASONING_EFFORT = "medium"


class TutorMessageBuilder:
    def __init__(
        self,
        *,
        prompt_builder: Callable[..., str],
        lesson_state_formatter: Callable[[Any], str],
        misconception_state_formatter: Callable[[Any], str],
        turn_analysis_formatter: Callable[[Any], str],
        pacing_formatter: Callable[[Any], str],
        response_constraints_formatter: Callable[..., str],
        active_misconception_formatter: Callable[..., str],
        first_turn_instruction: str,
    ) -> None:
        self.prompt_builder = prompt_builder
        self.lesson_state_formatter = lesson_state_formatter
        self.misconception_state_formatter = misconception_state_formatter
        self.turn_analysis_formatter = turn_analysis_formatter
        self.pacing_formatter = pacing_formatter
        self.response_constraints_formatter = response_constraints_formatter
        self.active_misconception_formatter = active_misconception_formatter
        self.first_turn_instruction = first_turn_instruction

    def build(
        self,
        *,
        student_response: Optional[str],
        history: Optional[List[Dict[str, str]]],
        teaching_content: str,
        student_context: str,
        current_stage: str,
        active_objective: str,
        teaching_plan: Any,
        lesson_state: Optional[Dict[str, Any]] = None,
        turn_analysis: Optional[Dict[str, Any]] = None,
        pacing_state: Optional[Dict[str, Any]] = None,
        misconception_state: Optional[Dict[str, Any]] = None,
        extra_system_messages: Optional[List[str]] = None,
        first_turn: bool = False,
    ) -> List[Dict[str, str]]:
        system_prompt = self.prompt_builder(
            knowledge_context=teaching_content,
            student_context=student_context,
            current_stage=current_stage,
            active_objective=active_objective,
            teaching_plan=teaching_plan,
            lesson_state_context=self.lesson_state_formatter(lesson_state),
            misconception_state_context=self.misconception_state_formatter(
                misconception_state
            ),
        )
        messages = [{"role": "system", "content": system_prompt}]
        turn_analysis_block = self.turn_analysis_formatter(turn_analysis)
        if turn_analysis_block:
            messages.append({"role": "system", "content": turn_analysis_block})
        pacing_block = self.pacing_formatter(pacing_state)
        if pacing_block:
            messages.append({"role": "system", "content": pacing_block})
        response_constraints_block = self.response_constraints_formatter(
            pacing_state=pacing_state,
            turn_analysis=turn_analysis,
            misconception_state=misconception_state,
        )
        if response_constraints_block:
            messages.append({"role": "system", "content": response_constraints_block})
        misconception_block = self.active_misconception_formatter(
            turn_analysis, misconception_state
        )
        if misconception_block:
            messages.append({"role": "system", "content": misconception_block})
        for extra in extra_system_messages or []:
            if extra:
                messages.append({"role": "system", "content": extra})
        if first_turn:
            messages.append({"role": "system", "content": self.first_turn_instruction})
            messages.append({"role": "user", "content": "Begin the lesson."})
            return messages
        if history:
            messages.extend(history[-6:])
        messages.append({"role": "user", "content": student_response or ""})
        return messages


class StructuredTurnAnalyzer:
    def __init__(
        self,
        *,
        reasoning_client,
        turn_prompt_builder: Callable[..., str],
        assessment_prompt_builder: Callable[..., str],
        lesson_state_formatter: Callable[[Any], str],
        pacing_state_formatter: Callable[[Any], str],
        misconception_state_formatter: Callable[[Any], str],
        transcript_formatter: Callable[[List[Dict[str, str]], str], str],
        json_parser: Callable[[str, Dict[str, Any]], Dict[str, Any]],
    ) -> None:
        self.reasoning_client = reasoning_client
        self.turn_prompt_builder = turn_prompt_builder
        self.assessment_prompt_builder = assessment_prompt_builder
        self.lesson_state_formatter = lesson_state_formatter
        self.pacing_state_formatter = pacing_state_formatter
        self.misconception_state_formatter = misconception_state_formatter
        self.transcript_formatter = transcript_formatter
        self.json_parser = json_parser

    async def analyze_turn(
        self,
        *,
        history: List[Dict[str, str]],
        student_response: str,
        teaching_content: str,
        student_context: str,
        current_stage: str,
        active_objective: str,
        teaching_plan: Any,
        lesson_state: Optional[Dict[str, Any]] = None,
        pacing_state: Optional[Dict[str, Any]] = None,
        misconception_state: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        prompt = self.turn_prompt_builder(
            knowledge_context=teaching_content,
            student_context=student_context,
            current_stage=current_stage,
            active_objective=active_objective,
            teaching_plan=teaching_plan,
            lesson_state_context=self.lesson_state_formatter(lesson_state),
            pacing_state_context=self.pacing_state_formatter(pacing_state),
            misconception_state_context=self.misconception_state_formatter(
                misconception_state
            ),
        )
        transcript = self.transcript_formatter(history, student_response)
        response = await asyncio.to_thread(
            self.reasoning_client.chat,
            [
                {"role": "system", "content": prompt},
                {"role": "user", "content": transcript},
            ],
            0.0,
            TURN_ANALYZER_MAX_TOKENS,
            reasoning_effort=TURN_ANALYZER_REASONING_EFFORT,
        )
        return self.json_parser(
            response,
            fallback={
                "turn_route": "objective_answer",
                "answer_current_question_first": True,
                "student_question_to_answer": student_response[:160],
                "teaching_move": "continue",
                "stage_action": "stay",
                "target_stage": current_stage,
                "stage_reason": "",
                "bridge_scope": {
                    "mode": "answer_within_current_node",
                    "current_node_basis": "",
                    "candidate_next_node": "",
                    "return_to_current_node": True,
                    "reason": "Fallback analyzer output keeps the tutor anchored.",
                },
                "self_consistency": {
                    "current_node_basis": "",
                    "proposed_active_concept": "",
                    "concept_closure_evidence": "Fallback output has no closure evidence.",
                    "stage_progression_intent": "stay",
                    "graph_progression_intent": "stay",
                    "fields_agree": True,
                    "needs_repair": False,
                    "repair_note": "",
                },
                "mastery_signal": {
                    "should_update": False,
                    "level": "not_attempted",
                    "confidence": 0.0,
                    "evidence_summary": "",
                },
                "misconception_events": [],
                "lesson_state_patch": {
                    "active_concept": "",
                    "pending_check": "",
                    "bridge_back_target": "",
                    "concept_updates": [],
                },
                "pacing_signal": {
                    "grasp_level": "emerging",
                    "reasoning_mode": "paraphrase",
                    "support_needed": "moderate",
                    "confusion_level": "medium",
                    "response_pattern": "direct",
                    "concept_closure": "not_ready",
                    "override_pace": "none",
                    "override_reason": "",
                    "recommended_next_step": "ask_same_level",
                },
                "objective_memory_patch": {
                    "summary": "",
                    "demonstrated_skills_add": [],
                    "active_gaps_current": [],
                    "next_focus": "",
                },
                "learner_memory_patch": {
                    "summary": "",
                    "strengths_add": [],
                    "support_needs_current": [],
                    "tendencies_current": [],
                    "successful_strategies_add": [],
                },
            },
        )

    async def reflect_on_assessment(
        self,
        *,
        history: List[Dict[str, str]],
        student_response: str,
        teaching_content: str,
        student_context: str,
        current_stage: str,
        active_objective: str,
        teaching_plan: Any,
        lesson_state: Optional[Dict[str, Any]] = None,
        misconception_state: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        prompt = self.assessment_prompt_builder(
            knowledge_context=teaching_content,
            student_context=student_context,
            current_stage=current_stage,
            active_objective=active_objective,
            teaching_plan=teaching_plan,
            lesson_state_context=self.lesson_state_formatter(lesson_state),
            misconception_state_context=self.misconception_state_formatter(
                misconception_state
            ),
        )
        transcript = self.transcript_formatter(history, student_response)
        response = await asyncio.to_thread(
            self.reasoning_client.chat,
            [
                {"role": "system", "content": prompt},
                {"role": "user", "content": transcript},
            ],
            0.0,
            ASSESSMENT_REFLECTOR_MAX_TOKENS,
            reasoning_effort=ASSESSMENT_REFLECTOR_REASONING_EFFORT,
        )
        return self.json_parser(
            response,
            fallback={
                "is_correct": False,
                "confidence": 0.0,
                "rationale": "",
                "misconception_events": [],
                "objective_memory_patch": {
                    "summary": "",
                    "demonstrated_skills_add": [],
                    "active_gaps_current": [],
                    "next_focus": "",
                },
                "learner_memory_patch": {
                    "summary": "",
                    "strengths_add": [],
                    "support_needs_current": [],
                    "tendencies_current": [],
                    "successful_strategies_add": [],
                },
            },
        )


class GraphProgressionOrchestrator:
    def __init__(
        self,
        *,
        reasoning_client,
        json_parser: Callable[[str, Dict[str, Any]], Dict[str, Any]],
    ) -> None:
        self.reasoning_client = reasoning_client
        self.json_parser = json_parser

    async def decide(
        self,
        *,
        graph_state: Optional[Dict[str, Any]],
        turn_analysis: Optional[Dict[str, Any]],
        lesson_state: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        fallback = fallback_graph_decision(graph_state, turn_analysis)
        response = await asyncio.to_thread(
            self.reasoning_client.chat,
            [
                {"role": "system", "content": GRAPH_ORCHESTRATOR_PROMPT},
                {
                    "role": "user",
                    "content": format_graph_orchestrator_input(
                        graph_state,
                        turn_analysis,
                        lesson_state,
                    ),
                },
            ],
            0.0,
            GRAPH_ORCHESTRATOR_MAX_TOKENS,
            reasoning_effort=GRAPH_ORCHESTRATOR_REASONING_EFFORT,
        )
        parsed = self.json_parser(response, fallback=fallback)
        return normalize_graph_decision(parsed, graph_state, turn_analysis)


class ResponseControlGuard:
    def __init__(self, *, guard_fn: Callable[..., Dict[str, Any]]) -> None:
        self.guard_fn = guard_fn

    def apply(
        self,
        *,
        current_stage: str,
        analysis: Dict[str, Any],
        lesson_state: Optional[Dict[str, Any]],
        pacing_state: Optional[Dict[str, Any]],
        misconception_state: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        return self.guard_fn(
            current_stage=current_stage,
            analysis=analysis,
            lesson_state=lesson_state,
            pacing_state=pacing_state,
            misconception_state=misconception_state,
        )


class LessonStateController:
    def __init__(
        self,
        *,
        preview_misconceptions: Callable[
            [str, Optional[List[Dict[str, Any]]]], Dict[str, Any]
        ],
        preview_pacing: Callable[[str, Optional[Dict[str, Any]]], Dict[str, Any]],
        preview_objective_memory: Callable[
            [Optional[Dict[str, Any]], Optional[Dict[str, Any]]], Dict[str, Any]
        ],
        response_guard: ResponseControlGuard,
        lesson_state_getter: Callable[[str], Optional[Dict[str, Any]]],
        misconception_state_getter: Callable[[str], Optional[Dict[str, Any]]],
        apply_misconceptions: Callable[..., Any],
        coerce_misconceptions: Callable[..., List[Dict[str, Any]]],
        increment_turn_count: Callable[[str], Any],
        apply_lesson_state_patch: Callable[[str, Optional[Dict[str, Any]]], Any],
        recompute_lesson_state: Callable[..., Any],
        apply_pacing_signal: Callable[[str, Optional[Dict[str, Any]]], Any],
        persist_session_cache: Callable[[str], Any],
        apply_memory_patches: Callable[..., Any],
        apply_mastery_judgment: Callable[..., Any],
        update_session_state: Callable[..., Any],
    ) -> None:
        self.preview_misconceptions = preview_misconceptions
        self.preview_pacing = preview_pacing
        self.preview_objective_memory = preview_objective_memory
        self.response_guard = response_guard
        self.lesson_state_getter = lesson_state_getter
        self.misconception_state_getter = misconception_state_getter
        self.apply_misconceptions = apply_misconceptions
        self.coerce_misconceptions = coerce_misconceptions
        self.increment_turn_count = increment_turn_count
        self.apply_lesson_state_patch = apply_lesson_state_patch
        self.recompute_lesson_state = recompute_lesson_state
        self.apply_pacing_signal = apply_pacing_signal
        self.persist_session_cache = persist_session_cache
        self.apply_memory_patches = apply_memory_patches
        self.apply_mastery_judgment = apply_mastery_judgment
        self.update_session_state = update_session_state

    async def apply_turn_analysis(
        self,
        *,
        student_id: str,
        session_id: str,
        objective_id: str,
        objective_text: str,
        current_stage: str,
        analysis: Dict[str, Any],
        bundle: Optional[Dict[str, Any]],
        ws_send,
    ) -> Dict[str, Any]:
        result = {"stage": current_stage, "stage_advanced": False}
        preview_misconception_state = self.preview_misconceptions(
            session_id,
            self.coerce_misconceptions(
                analysis,
                default_priority=(
                    "must_address_now"
                    if str(analysis.get("teaching_move", "") or "").strip().lower()
                    == "repair"
                    else "normal"
                ),
            ),
        )
        preview_pacing_state = self.preview_pacing(
            session_id,
            analysis.get("pacing_signal"),
        )
        preview_objective_memory = self.preview_objective_memory(
            (bundle or {}).get("objective_memory") or {},
            analysis.get("objective_memory_patch"),
        )
        guarded = self.response_guard.apply(
            current_stage=current_stage,
            analysis=analysis,
            lesson_state=self.lesson_state_getter(session_id),
            pacing_state=preview_pacing_state,
            misconception_state=preview_misconception_state,
        )

        await self.increment_turn_count(session_id)
        misconception_events = self.coerce_misconceptions(
            guarded,
            default_priority=(
                "must_address_now"
                if str(guarded.get("teaching_move", "") or "").strip().lower()
                == "repair"
                else "normal"
            ),
        )
        await self.apply_misconceptions(
            student_id=student_id,
            session_id=session_id,
            objective_id=objective_id,
            events=misconception_events,
        )

        self.apply_lesson_state_patch(
            session_id,
            guarded.get("lesson_state_patch"),
        )
        self.recompute_lesson_state(
            session_id,
            objective_memory=preview_objective_memory,
            misconception_state=self.misconception_state_getter(session_id),
        )
        self.apply_pacing_signal(
            session_id,
            guarded.get("pacing_signal"),
        )
        await self.persist_session_cache(session_id)

        await self.apply_memory_patches(
            student_id,
            objective_id,
            guarded.get("objective_memory_patch"),
            guarded.get("learner_memory_patch"),
            bundle=bundle,
        )

        mastery_signal = guarded.get("mastery_signal") or {}
        mastery_level = mastery_signal.get("level", "")
        if mastery_signal.get("should_update") and mastery_level in (
            "not_attempted",
            "misconception",
            "in_progress",
        ):
            mastery_result = await self.apply_mastery_judgment(
                student_id,
                objective_id,
                mastery_level,
                evidence_summary=mastery_signal.get("evidence_summary", ""),
                confidence=float(mastery_signal.get("confidence", 0.0) or 0.0),
            )
            if isinstance(mastery_result, dict):
                if mastery_result.get("updated"):
                    await ws_send(
                        {
                            "type": "mastery_update",
                            "objective_id": objective_id,
                            "objective_text": objective_text or objective_id,
                            "new_level": mastery_result.get(
                                "applied_level",
                                mastery_result.get("mastery_level", mastery_level),
                            ),
                        }
                    )
                elif mastery_result.get("denied"):
                    await ws_send(
                        {
                            "type": "mastery_denied",
                            "reason": mastery_result.get("reason", ""),
                        }
                    )

        result["analysis"] = guarded
        return result
