from __future__ import annotations

import json
import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from .artifacts import GuidedTurnResult, TeachingGraphContentArtifact
from .graph_runtime import (
    build_graph_runtime_patch,
    format_graph_runtime_context,
    format_orchestrator_directive,
)
from .workers.graph import GraphGroundingProjector

logger = logging.getLogger(__name__)


class _GuidedTurnWorkflowState(TypedDict, total=False):
    student_id: str
    student_response: str
    session_id: str
    current_stage: str
    objective_id: str
    objective_text: str
    history: List[Dict[str, str]]
    teaching_content: str
    guided_state: Any
    ws_send: Any
    turn_analysis: Dict[str, Any]
    guarded_turn_analysis: Dict[str, Any]
    analysis_result: Dict[str, Any]
    graph_decision: Dict[str, Any]
    graph_runtime_state: Dict[str, Any]
    final_text: str
    final_stage: str
    stage_advanced: bool


class TeachingGraphBuildOrchestrator:
    def __init__(
        self,
        *,
        planner,
        node_evidence_retriever,
        node_content_synthesizer,
        edge_integration_synthesizer,
        validator,
    ) -> None:
        self.planner = planner
        self.node_evidence_retriever = node_evidence_retriever
        self.node_content_synthesizer = node_content_synthesizer
        self.edge_integration_synthesizer = edge_integration_synthesizer
        self.validator = validator

    async def run(
        self,
        *,
        objective_text: str,
        learner_level: Optional[str] = None,
        prerequisite_assumptions: Optional[str] = None,
    ) -> TeachingGraphContentArtifact:
        graph = await self.planner.generate(
            objective_text,
            learner_level=learner_level,
            prerequisite_assumptions=prerequisite_assumptions,
        )
        node_evidence = await self.node_evidence_retriever.build_graph_evidence(
            objective_text=objective_text,
            graph=graph,
        )
        node_content = await self.node_content_synthesizer.build_node_content(
            objective_text=objective_text,
            graph=graph,
            node_evidence=node_evidence,
        )
        edge_integration = (
            await self.edge_integration_synthesizer.build_edge_integration_content(
                objective_text=objective_text,
                graph=graph,
                node_evidence=node_evidence,
                node_content=node_content,
            )
        )
        validation = await self.validator.validate(
            objective_text=objective_text,
            graph=graph,
            node_evidence=node_evidence,
            node_content=node_content,
            edge_integration=edge_integration,
        )
        evidence_cards = GraphGroundingProjector.build_evidence_cards(
            objective_text=objective_text,
            node_evidence=node_evidence,
        )
        claim_ledger = GraphGroundingProjector.build_claim_ledger(
            objective_text=objective_text,
            node_evidence=node_evidence,
            node_content=node_content,
            edge_integration=edge_integration,
            evidence_cards=evidence_cards,
        )
        validation = GraphGroundingProjector.deterministic_validate(
            validation=validation,
            claim_ledger=claim_ledger,
            evidence_cards=evidence_cards,
        )
        if validation.overall_status != "pass":
            raise RuntimeError(
                "Graph-grounded content failed validation: "
                f"{validation.overall_status}"
            )
        tutor_facing_content = GraphGroundingProjector.build_tutor_facing_content(
            objective_text=objective_text,
            graph=graph,
            node_content=node_content,
            edge_integration=edge_integration,
            evidence_cards=evidence_cards,
            claim_ledger=claim_ledger,
            validation=validation,
        )
        return TeachingGraphContentArtifact(
            objective_text=objective_text,
            graph=graph,
            node_evidence=node_evidence,
            node_content=node_content,
            edge_integration=edge_integration,
            validation=validation,
            evidence_cards=evidence_cards,
            claim_ledger=claim_ledger,
            tutor_facing_content=tutor_facing_content,
        )


class GuidedTurnOrchestrator:
    def __init__(
        self,
        *,
        student_mcp,
        state_repository,
        content_pipeline: Callable[..., Awaitable[tuple]],
        teaching_plan_error_cls: type[Exception],
        get_combined_context: Callable[..., Awaitable[tuple]],
        generate_teaching_plan: Callable[..., Awaitable[Any]],
        get_assessment_context: Callable[[str], Awaitable[str]],
        assessment_reflector: Callable[..., Awaitable[Dict[str, Any]]],
        turn_analyzer: Callable[..., Awaitable[Dict[str, Any]]],
        coerce_misconception_events: Callable[..., List[Dict[str, Any]]],
        apply_misconception_events: Callable[..., Awaitable[Dict[str, Any]]],
        apply_memory_patches: Callable[..., Awaitable[None]],
        apply_turn_analysis_updates: Callable[..., Awaitable[Dict[str, Any]]],
        decide_graph_progression: Callable[..., Awaitable[Dict[str, Any]]],
        build_tutor_messages: Callable[..., List[Dict[str, str]]],
        stream_response: Callable[..., Awaitable[str]],
        append_to_conversation: Callable[[str, str, str], None],
        advance_to_next_objective: Callable[..., Awaitable[Dict[str, Any]]],
        render_turn_analysis: Callable[[Dict[str, Any]], str],
        safe_serialize: Callable[[Any], Any],
    ) -> None:
        self.student_mcp = student_mcp
        self.state_repository = state_repository
        self.content_pipeline = content_pipeline
        self.teaching_plan_error_cls = teaching_plan_error_cls
        self.get_combined_context = get_combined_context
        self.generate_teaching_plan = generate_teaching_plan
        self.get_assessment_context = get_assessment_context
        self.assessment_reflector = assessment_reflector
        self.turn_analyzer = turn_analyzer
        self.coerce_misconception_events = coerce_misconception_events
        self.apply_misconception_events = apply_misconception_events
        self.apply_memory_patches = apply_memory_patches
        self.apply_turn_analysis_updates = apply_turn_analysis_updates
        self.decide_graph_progression = decide_graph_progression
        self.build_tutor_messages = build_tutor_messages
        self.stream_response = stream_response
        self.append_to_conversation = append_to_conversation
        self.advance_to_next_objective = advance_to_next_objective
        self.render_turn_analysis = render_turn_analysis
        self.safe_serialize = safe_serialize
        self._normal_turn_graph = self._build_normal_turn_graph()

    def _build_normal_turn_graph(self):
        workflow = StateGraph(_GuidedTurnWorkflowState)
        workflow.add_node("analyze_turn", self._graph_analyze_turn)
        workflow.add_node("apply_analysis_updates", self._graph_apply_analysis_updates)
        workflow.add_node("decide_graph_progression", self._graph_decide_progression)
        workflow.add_node("compose_tutor_response", self._graph_compose_tutor_response)
        workflow.add_edge(START, "analyze_turn")
        workflow.add_edge("analyze_turn", "apply_analysis_updates")
        workflow.add_edge("apply_analysis_updates", "decide_graph_progression")
        workflow.add_edge("decide_graph_progression", "compose_tutor_response")
        workflow.add_edge("compose_tutor_response", END)
        return workflow.compile()

    async def _graph_analyze_turn(
        self,
        state: _GuidedTurnWorkflowState,
    ) -> Dict[str, Any]:
        guided_state = state["guided_state"]
        graph_context = format_graph_runtime_context(
            guided_state.graph_runtime_state,
            guided_state.retrieval_bundle,
        )
        teaching_content = state["teaching_content"]
        if graph_context:
            teaching_content = f"{teaching_content}\n\n{graph_context}"

        await state["ws_send"](
            {
                "type": "stage",
                "stage": "analyzing",
                "detail": "Analyzing your response...",
            }
        )
        await state["ws_send"]({"type": "turn_analysis_generating"})
        turn_analysis = await self.turn_analyzer(
            history=state["history"],
            student_response=state["student_response"],
            teaching_content=teaching_content,
            student_context=guided_state.student_context,
            current_stage=state["current_stage"],
            active_objective=state["objective_text"],
            teaching_plan=guided_state.teaching_plan,
            lesson_state=guided_state.lesson_state,
            pacing_state=guided_state.pacing_state,
            misconception_state=guided_state.misconception_state,
        )
        await state["ws_send"](
            {
                "type": "turn_analysis",
                "analysis": self.safe_serialize(turn_analysis),
                "display_analysis": self.render_turn_analysis(turn_analysis),
            }
        )
        return {"turn_analysis": turn_analysis}

    async def _graph_apply_analysis_updates(
        self,
        state: _GuidedTurnWorkflowState,
    ) -> Dict[str, Any]:
        guided_state = state["guided_state"]
        analysis_result = await self.apply_turn_analysis_updates(
            student_id=state["student_id"],
            session_id=state["session_id"],
            objective_id=state["objective_id"],
            objective_text=state["objective_text"],
            current_stage=state["current_stage"],
            analysis=state["turn_analysis"],
            bundle=guided_state.bundle,
            ws_send=state["ws_send"],
        )
        return {
            "analysis_result": analysis_result,
            "guarded_turn_analysis": analysis_result.get(
                "analysis",
                state["turn_analysis"],
            ),
            "final_stage": analysis_result.get("stage", state["current_stage"]),
            "stage_advanced": analysis_result.get("stage_advanced", False),
        }

    async def _graph_decide_progression(
        self,
        state: _GuidedTurnWorkflowState,
    ) -> Dict[str, Any]:
        graph_state = self.state_repository.get_graph_runtime_state(state["session_id"])
        refreshed_lesson_state = self.state_repository.get_lesson_state(
            state["session_id"]
        )
        decision = await self.decide_graph_progression(
            graph_state=graph_state,
            turn_analysis=state.get("guarded_turn_analysis") or state["turn_analysis"],
            lesson_state=refreshed_lesson_state,
        )
        patch = build_graph_runtime_patch(graph_state, decision)
        updated_graph_state = self.state_repository.apply_graph_runtime_patch(
            state["session_id"],
            patch,
        )
        await self.state_repository.persist(state["session_id"])
        logger.info(
            "Graph progression decision session=%s action=%s active=%s move=%s",
            state["session_id"],
            decision.get("graph_action"),
            decision.get("active_node_id"),
            decision.get("allowed_teaching_move"),
        )
        return {
            "graph_decision": decision,
            "graph_runtime_state": updated_graph_state,
        }

    async def _graph_compose_tutor_response(
        self,
        state: _GuidedTurnWorkflowState,
    ) -> Dict[str, Any]:
        refreshed_state = await self.state_repository.load_guided_state(
            student_id=state["student_id"],
            session_id=state["session_id"],
            objective_id=state["objective_id"],
            objective_text=state["objective_text"],
        )
        graph_context = format_graph_runtime_context(
            state.get("graph_runtime_state") or refreshed_state.graph_runtime_state,
            refreshed_state.retrieval_bundle,
        )
        directive = format_orchestrator_directive(state.get("graph_decision"))
        await state["ws_send"](
            {
                "type": "stage",
                "stage": "composing",
                "detail": f"Generating response ({state['final_stage']})...",
            }
        )
        tutor_messages = self.build_tutor_messages(
            student_response=state["student_response"],
            history=state["history"],
            teaching_content=state["teaching_content"],
            student_context=refreshed_state.student_context,
            current_stage=state["final_stage"],
            active_objective=state["objective_text"],
            teaching_plan=refreshed_state.teaching_plan,
            lesson_state=refreshed_state.lesson_state,
            turn_analysis=state.get("guarded_turn_analysis") or state["turn_analysis"],
            pacing_state=refreshed_state.pacing_state,
            misconception_state=refreshed_state.misconception_state,
            extra_system_messages=[graph_context, directive],
        )
        final_text = await self.stream_response(tutor_messages, state["ws_send"])
        self.append_to_conversation(state["student_id"], "assistant", final_text)
        return {"final_text": final_text}

    async def ensure_content_ready(
        self,
        *,
        objective_text: str,
        student_response: str,
        history: List[Dict[str, str]],
        session_id: str,
        objective_id: str,
        ws_send,
    ) -> str:
        if self.state_repository.needs_retrieval(session_id, objective_id):
            try:
                (
                    teaching_plan,
                    teaching_content,
                    retrieval_bundle,
                    extracted_concepts,
                ) = await self.content_pipeline(
                    objective_text or student_response,
                    session_id,
                    objective_id,
                    ws_send,
                )
                self.state_repository.store_pipeline_result(
                    session_id=session_id,
                    objective_id=objective_id,
                    objective_text=objective_text,
                    teaching_content=teaching_content,
                    retrieval_bundle=retrieval_bundle,
                    teaching_plan=teaching_plan,
                    extracted_concepts=extracted_concepts,
                )
            except self.teaching_plan_error_cls:
                raise
            except Exception:
                logger.info("Falling back to RAG + WCAG MCP retrieval")
                await ws_send({"type": "teaching_content_generating"})
                rag_context, rag_chunks, wcag_context = await self.get_combined_context(
                    objective_text or student_response, history=history
                )
                teaching_content = rag_context
                if wcag_context:
                    teaching_content = (
                        f"{rag_context}\n\n{wcag_context}"
                        if rag_context
                        else wcag_context
                    )
                self.state_repository.session_cache.store(
                    session_id,
                    objective_id,
                    objective_text,
                    rag_chunks,
                    wcag_context,
                    teaching_content,
                )
                await ws_send({"type": "teaching_content", "content": teaching_content})
                teaching_plan = await self.generate_teaching_plan(
                    objective_text, teaching_content
                )
                self.state_repository.session_cache.store_teaching_plan(
                    session_id, teaching_plan
                )
            await self.state_repository.persist(session_id)
            return teaching_content

        return self.state_repository.get_teaching_content(session_id)

    async def run_guided_turn(
        self,
        *,
        student_id: str,
        student_response: str,
        session_id: str,
        session_state: Dict[str, Any],
        objective_id: str,
        objective_text: str,
        history: List[Dict[str, str]],
        ws_send,
    ) -> GuidedTurnResult:
        current_stage = (session_state or {}).get("current_stage", "introduction")

        teaching_content = await self.ensure_content_ready(
            objective_text=objective_text,
            student_response=student_response,
            history=history,
            session_id=session_id,
            objective_id=objective_id,
            ws_send=ws_send,
        )

        guided_state = await self.state_repository.load_guided_state(
            student_id=student_id,
            session_id=session_id,
            objective_id=objective_id,
            objective_text=objective_text,
        )
        if not guided_state.teaching_plan:
            raise RuntimeError(
                "No validated teaching plan is available for this objective. Guided tutoring cannot continue."
            )

        final_text = ""
        final_stage = current_stage
        stage_advanced = False
        assessment_metadata: Dict[str, Any] = {}

        if current_stage in ("mini_assessment", "final_assessment"):
            assessment_ctx = await self.get_assessment_context(objective_id)
            assessment_content = teaching_content
            if assessment_ctx:
                assessment_content = (
                    f"{teaching_content}\n\n{assessment_ctx}"
                    if teaching_content
                    else assessment_ctx
                )

            await ws_send(
                {
                    "type": "stage",
                    "stage": "analyzing",
                    "detail": "Evaluating your assessment answer...",
                }
            )
            assessment_reflection = await self.assessment_reflector(
                history=history,
                student_response=student_response,
                teaching_content=assessment_content,
                student_context=guided_state.student_context,
                current_stage=current_stage,
                active_objective=objective_text,
                teaching_plan=guided_state.teaching_plan,
                lesson_state=guided_state.lesson_state,
                misconception_state=guided_state.misconception_state,
            )
            assessment_misconception_events = self.coerce_misconception_events(
                assessment_reflection,
                default_priority=(
                    "must_address_now"
                    if not bool(assessment_reflection.get("is_correct", False))
                    else "normal"
                ),
            )
            misconception_state = await self.apply_misconception_events(
                student_id=student_id,
                session_id=session_id,
                objective_id=objective_id,
                events=assessment_misconception_events,
            )
            await self.state_repository.persist(session_id)
            await self.apply_memory_patches(
                student_id,
                objective_id,
                assessment_reflection.get("objective_memory_patch"),
                assessment_reflection.get("learner_memory_patch"),
                bundle=guided_state.bundle,
            )

            assessment_result = await self.student_mcp.record_assessment_answer(
                session_id,
                bool(assessment_reflection.get("is_correct", False)),
            )
            assessment_metadata = assessment_result or {}

            if isinstance(assessment_result, dict) and assessment_result.get(
                "recorded"
            ):
                await ws_send(
                    {
                        "type": "assessment_score",
                        **assessment_result.get("progress", {}),
                        "passed": assessment_result.get("passed"),
                    }
                )

            updated_session = await self.student_mcp.get_active_session(student_id)
            response_stage = (updated_session or {}).get("current_stage", current_stage)
            final_stage = response_stage

            if response_stage != current_stage:
                await ws_send(
                    {
                        "type": "stage_update",
                        "stage": response_stage,
                        "objective": objective_text or objective_id,
                        "summary": assessment_reflection.get("rationale", ""),
                    }
                )
                stage_advanced = True

            if isinstance(assessment_result, dict) and assessment_result.get(
                "mastery_level"
            ):
                await ws_send(
                    {
                        "type": "mastery_update",
                        "objective_id": objective_id,
                        "objective_text": objective_text or objective_id,
                        "new_level": assessment_result.get("mastery_level", ""),
                    }
                )

            refreshed_state = await self.state_repository.load_guided_state(
                student_id=student_id,
                session_id=session_id,
                objective_id=objective_id,
                objective_text=objective_text,
            )

            extra_messages = [
                (
                    "ASSESSMENT RESULT:\n"
                    f"- judged_correct: {bool(assessment_reflection.get('is_correct', False))}\n"
                    f"- confidence: {assessment_reflection.get('confidence', 0.0)}\n"
                    f"- rationale: {assessment_reflection.get('rationale', '')}\n"
                    f"- progress: {json.dumps((assessment_result or {}).get('progress', {}))}\n"
                    f"- current_stage_after_scoring: {response_stage}"
                )
            ]
            if isinstance(assessment_result, dict) and assessment_result.get(
                "completed"
            ):
                next_stage = assessment_result.get("next_stage", response_stage)
                if next_stage == "final_assessment":
                    extra_messages.append(
                        "The mini assessment is complete and the student passed. Briefly reinforce the answer, then ask exactly one deeper final-assessment question."
                    )
                elif next_stage == "transition":
                    extra_messages.append(
                        "The assessment is complete and the objective is finished. Celebrate, summarize the learning, and bridge naturally. Do not ask another assessment question."
                    )
                elif next_stage == "introduction":
                    extra_messages.append(
                        "The assessment showed important gaps. Explain the key issue warmly and return to teaching this objective. Do not ask another assessment question in this response."
                    )
            else:
                extra_messages.append(
                    "The assessment is still in progress. Briefly explain why the answer was correct or incorrect, then ask exactly one next assessment question."
                )

            await ws_send(
                {
                    "type": "stage",
                    "stage": "composing",
                    "detail": f"Generating response ({response_stage})...",
                }
            )
            tutor_messages = self.build_tutor_messages(
                student_response=student_response,
                history=history,
                teaching_content=assessment_content,
                student_context=refreshed_state.student_context,
                current_stage=response_stage,
                active_objective=objective_text,
                teaching_plan=refreshed_state.teaching_plan,
                lesson_state=refreshed_state.lesson_state,
                pacing_state=refreshed_state.pacing_state,
                misconception_state=misconception_state,
                extra_system_messages=extra_messages,
            )
            final_text = await self.stream_response(tutor_messages, ws_send)
            self.append_to_conversation(student_id, "assistant", final_text)

            if response_stage == "transition":
                transition_result = await self.advance_to_next_objective(
                    student_id, session_id, ws_send
                )
                if transition_result.get("advanced"):
                    final_stage = transition_result.get("stage", response_stage)

        else:
            workflow_result = await self._normal_turn_graph.ainvoke(
                {
                    "student_id": student_id,
                    "student_response": student_response,
                    "session_id": session_id,
                    "current_stage": current_stage,
                    "objective_id": objective_id,
                    "objective_text": objective_text,
                    "history": history,
                    "teaching_content": teaching_content,
                    "guided_state": guided_state,
                    "ws_send": ws_send,
                    "final_stage": current_stage,
                    "stage_advanced": False,
                }
            )
            final_text = workflow_result.get("final_text", "")
            final_stage = workflow_result.get("final_stage", current_stage)
            stage_advanced = workflow_result.get("stage_advanced", False)

        cached = self.state_repository.get_cached_entry(session_id)
        return GuidedTurnResult(
            metadata={
                "session_id": session_id,
                "stage": final_stage,
                "stage_advanced": stage_advanced,
                "assessment": self.safe_serialize(assessment_metadata),
                "cached_entry": cached,
            },
            final_text=final_text,
            final_stage=final_stage,
            stage_advanced=stage_advanced,
            assessment_metadata=assessment_metadata,
        )

    async def start_first_teaching_turn(
        self,
        *,
        student_id: str,
        session_id: str,
        objective_id: str,
        objective_text: str,
        ws_send,
    ) -> GuidedTurnResult:
        await self.state_repository.restore(session_id, objective_id)

        if self.state_repository.needs_retrieval(session_id, objective_id):
            (
                teaching_plan,
                teaching_content,
                retrieval_bundle,
                extracted_concepts,
            ) = await self.content_pipeline(
                objective_text,
                session_id,
                objective_id,
                ws_send,
            )
            self.state_repository.store_pipeline_result(
                session_id=session_id,
                objective_id=objective_id,
                objective_text=objective_text,
                teaching_content=teaching_content,
                retrieval_bundle=retrieval_bundle,
                teaching_plan=teaching_plan,
                extracted_concepts=extracted_concepts,
            )
            await self.state_repository.persist(session_id)

        guided_state = await self.state_repository.load_guided_state(
            student_id=student_id,
            session_id=session_id,
            objective_id=objective_id,
            objective_text=objective_text,
        )
        if not guided_state.teaching_plan:
            raise RuntimeError(
                "No validated teaching plan available for the first turn."
            )

        await ws_send(
            {
                "type": "stage",
                "stage": "composing",
                "detail": "Opening the lesson...",
            }
        )
        tutor_messages = self.build_tutor_messages(
            student_response=None,
            history=None,
            teaching_content=guided_state.teaching_content or "",
            student_context=guided_state.student_context,
            current_stage="introduction",
            active_objective=objective_text,
            teaching_plan=guided_state.teaching_plan,
            lesson_state=guided_state.lesson_state,
            pacing_state=guided_state.pacing_state,
            misconception_state=guided_state.misconception_state,
            extra_system_messages=[
                format_graph_runtime_context(
                    guided_state.graph_runtime_state,
                    guided_state.retrieval_bundle,
                )
            ],
            first_turn=True,
        )
        final_text = await self.stream_response(tutor_messages, ws_send)
        self.append_to_conversation(student_id, "assistant", final_text)

        await self.student_mcp.increment_turn_count(session_id)
        return GuidedTurnResult(
            metadata={
                "session_id": session_id,
                "stage": "introduction",
                "stage_advanced": False,
                "first_turn": True,
            },
            final_text=final_text,
            final_stage="introduction",
            stage_advanced=False,
        )
