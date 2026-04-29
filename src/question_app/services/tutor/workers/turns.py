from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, List, Optional

from ..analyzer_schema import default_analyzer_output, normalize_analyzer_output
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
        parsed = self.json_parser(
            response,
            fallback=default_analyzer_output(
                student_response=student_response,
                current_stage=current_stage,
            ),
        )
        return normalize_analyzer_output(
            parsed,
            student_response=student_response,
            current_stage=current_stage,
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
