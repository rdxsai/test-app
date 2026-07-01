#!/usr/bin/env python3
"""
Hybrid CrewAI Socratic System
(This is the final, corrected version with off-topic detection)
"""

import asyncio
import copy
import json
import logging
import os
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from ...models.tutor import KnowledgeLevel, SessionPhase, StudentProfile
from .analyzer_schema import (
    canonical_progression,
    canonical_student_turn,
    canonical_tutor_handoff,
    canonical_to_trace_legacy,
    has_open_must_repair,
    normalize_analyzer_output,
    runtime_learner_memory_patch,
    runtime_lesson_state_patch,
    runtime_misconception_events,
    runtime_objective_memory_patch,
    runtime_pacing_signal,
)
from .azure_client import AzureAPIMClient
from .interfaces import VectorStoreInterface
from .orchestrators import GuidedTurnOrchestrator, TeachingGraphBuildOrchestrator
from .repositories import GuidedSessionStateRepository
from .workers.content import ConceptExtractionWorker, TeachingPlanWorker
from .workers.graph import (
    EdgeIntegrationSynthesizerWorker,
    GraphGroundingProjector,
    GroundingValidatorWorker,
    NodeContentSynthesizerWorker,
    NodeEvidenceRetrieverWorker,
    TeachingGraphPlannerWorker,
)
from .workers.turns import (
    GraphProgressionOrchestrator,
    StructuredTurnAnalyzer,
    TutorMessageBuilder,
)

load_dotenv()
from question_app.services.database import get_database_manager

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ClientConnectionClosedError(RuntimeError):
    """Raised when the client websocket disconnects mid-response."""


class TeachingPlanGenerationError(RuntimeError):
    """Raised when the guided tutor cannot obtain a valid teaching plan."""


class TeachingGraphGenerationError(RuntimeError):
    """Raised when the guided tutor cannot obtain a valid teaching graph."""


GUIDED_STAGE_SEQUENCE = [
    "onboarding",
    "introduction",
    "exploration",
    "readiness_check",
    "mini_assessment",
    "final_assessment",
    "transition",
]


def safe_serialize(obj):
    # (This function is unchanged)
    if hasattr(obj, "__class__") and "MagicMock" in str(obj.__class__):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: safe_serialize(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [safe_serialize(item) for item in obj]
    else:
        return obj


# ============================================================================
# HYBRID CREWAI SYSTEM
# ============================================================================
# If the min cosine similarity is set to 0, the RAG pipeline will just use the vector DB
# If the min cosine similarity is set to 1, the RAG pipeline will default to using LLM's general knowledge.
MIN_COSINE_SIMILARITY = 0.7
TEACHING_PLAN_MAX_COMPLETION_TOKENS = 5000
TEACHING_PLAN_REASONING_EFFORT = "low"
TEACHING_GRAPH_MAX_COMPLETION_TOKENS = 5000
TEACHING_GRAPH_REASONING_EFFORT = "low"
TEACHING_GRAPH_NODE_RETRIEVAL_MAX_COMPLETION_TOKENS = 3500
TEACHING_GRAPH_NODE_RETRIEVAL_REASONING_EFFORT = "low"
TEACHING_GRAPH_NODE_RETRIEVAL_MAX_TOOL_CALLS = 4
TEACHING_GRAPH_NODE_SYNTHESIS_MAX_COMPLETION_TOKENS = 3500
TEACHING_GRAPH_NODE_SYNTHESIS_REASONING_EFFORT = "low"
TEACHING_GRAPH_EDGE_SYNTHESIS_MAX_COMPLETION_TOKENS = 5000
TEACHING_GRAPH_EDGE_SYNTHESIS_REASONING_EFFORT = "low"
TEACHING_GRAPH_VALIDATION_MAX_COMPLETION_TOKENS = 4000
TEACHING_GRAPH_VALIDATION_REASONING_EFFORT = "low"
GUIDED_TUTOR_RESPONSE_MAX_TOKENS = 3500
GUIDED_TUTOR_RESPONSE_REASONING_EFFORT = "medium"


class GuidedTutorSystem:
    """Compatibility facade over the guided tutor worker/orchestrator stack."""

    def __init__(
        self,
        azure_config: Dict[str, str],
        vector_store_service: VectorStoreInterface,
        db_manager=None,
        wcag_mcp_client=None,
        student_mcp_client=None,
        graph_responses_client=None,
    ):
        tutor_deployment = azure_config.get(
            "tutor_deployment_name"
        ) or azure_config.get("deployment_name")
        reasoning_deployment = azure_config.get("reasoning_deployment_name")
        if (
            not reasoning_deployment
            and tutor_deployment
            and tutor_deployment.endswith("-mini")
        ):
            reasoning_deployment = tutor_deployment[:-5]
        reasoning_deployment = reasoning_deployment or tutor_deployment

        self.tutor_client = AzureAPIMClient(
            endpoint=azure_config["endpoint"],
            deployment=tutor_deployment,
            api_key=azure_config["api_key"],
            api_version=azure_config.get("api_version", "2024-02-15-preview"),
            content_filter_policy=azure_config.get("content_filter_policy"),
        )
        if reasoning_deployment == tutor_deployment:
            self.reasoning_client = self.tutor_client
        else:
            self.reasoning_client = AzureAPIMClient(
                endpoint=azure_config["endpoint"],
                deployment=reasoning_deployment,
                api_key=azure_config["api_key"],
                api_version=azure_config.get("api_version", "2024-02-15-preview"),
                content_filter_policy=azure_config.get("content_filter_policy"),
            )
            logger.info(
                "Using split model roles: tutor=%s reasoning=%s",
                tutor_deployment,
                reasoning_deployment,
            )
        logger.info(
            "Teaching plan generation will use reasoning deployment=%s",
            reasoning_deployment,
        )

        self.client = self.tutor_client
        self.vector_store = vector_store_service
        self.db = db_manager or get_database_manager()
        self.wcag_mcp = wcag_mcp_client
        self.student_mcp = student_mcp_client
        self.graph_responses_client = graph_responses_client or self.reasoning_client
        # Session content cache: teaching material cached per objective (zero-latency reuse)
        from .session_cache import SessionContentCache

        self._session_cache = SessionContentCache()
        from .prompts import (
            FIRST_TURN_INSTRUCTION,
            build_assessment_reflector_prompt,
            build_instance_b_prompt,
            build_turn_analyzer_prompt,
            format_lesson_state,
            format_misconception_state,
            format_pacing_state,
            format_teaching_plan_for_display,
        )

        self._teaching_plan_worker = TeachingPlanWorker(
            reasoning_client=self.reasoning_client,
            display_formatter=format_teaching_plan_for_display,
            max_completion_tokens=TEACHING_PLAN_MAX_COMPLETION_TOKENS,
            reasoning_effort=TEACHING_PLAN_REASONING_EFFORT,
            plan_error_cls=TeachingPlanGenerationError,
        )
        self._teaching_graph_planner_worker = TeachingGraphPlannerWorker(
            reasoning_client=self.reasoning_client,
            max_completion_tokens=TEACHING_GRAPH_MAX_COMPLETION_TOKENS,
            reasoning_effort=TEACHING_GRAPH_REASONING_EFFORT,
            graph_error_cls=TeachingGraphGenerationError,
        )
        self._graph_node_evidence_worker = NodeEvidenceRetrieverWorker(
            reasoning_client=self.graph_responses_client,
            wcag_mcp=self.wcag_mcp,
            max_completion_tokens=TEACHING_GRAPH_NODE_RETRIEVAL_MAX_COMPLETION_TOKENS,
            reasoning_effort=TEACHING_GRAPH_NODE_RETRIEVAL_REASONING_EFFORT,
            max_tool_calls_per_node=TEACHING_GRAPH_NODE_RETRIEVAL_MAX_TOOL_CALLS,
            retrieval_error_cls=TeachingGraphGenerationError,
        )
        self._graph_node_content_worker = NodeContentSynthesizerWorker(
            reasoning_client=self.reasoning_client,
            max_completion_tokens=TEACHING_GRAPH_NODE_SYNTHESIS_MAX_COMPLETION_TOKENS,
            reasoning_effort=TEACHING_GRAPH_NODE_SYNTHESIS_REASONING_EFFORT,
            synthesis_error_cls=TeachingGraphGenerationError,
        )
        self._graph_edge_integration_worker = EdgeIntegrationSynthesizerWorker(
            reasoning_client=self.reasoning_client,
            max_completion_tokens=TEACHING_GRAPH_EDGE_SYNTHESIS_MAX_COMPLETION_TOKENS,
            reasoning_effort=TEACHING_GRAPH_EDGE_SYNTHESIS_REASONING_EFFORT,
            synthesis_error_cls=TeachingGraphGenerationError,
        )
        self._graph_validator_worker = GroundingValidatorWorker(
            reasoning_client=self.reasoning_client,
            max_completion_tokens=TEACHING_GRAPH_VALIDATION_MAX_COMPLETION_TOKENS,
            reasoning_effort=TEACHING_GRAPH_VALIDATION_REASONING_EFFORT,
            validation_error_cls=TeachingGraphGenerationError,
        )
        self._teaching_graph_build_orchestrator = TeachingGraphBuildOrchestrator(
            planner=self._teaching_graph_planner_worker,
            node_evidence_retriever=self._graph_node_evidence_worker,
            node_content_synthesizer=self._graph_node_content_worker,
            edge_integration_synthesizer=self._graph_edge_integration_worker,
            validator=self._graph_validator_worker,
        )
        self._teaching_content_pipeline = self._run_teaching_content_pipeline
        self._concept_extraction_worker = ConceptExtractionWorker(
            tutor_client=self.tutor_client,
        )
        self._tutor_message_builder = TutorMessageBuilder(
            prompt_builder=build_instance_b_prompt,
            lesson_state_formatter=format_lesson_state,
            misconception_state_formatter=format_misconception_state,
            turn_analysis_formatter=self._format_turn_analysis_for_tutor,
            pacing_formatter=self._format_adaptive_pacing_for_tutor,
            response_constraints_formatter=self._format_response_constraints_for_tutor,
            active_misconception_formatter=self._format_active_misconception_guidance,
            first_turn_instruction=FIRST_TURN_INSTRUCTION,
        )
        self._structured_turn_analyzer = StructuredTurnAnalyzer(
            reasoning_client=self.reasoning_client,
            turn_prompt_builder=build_turn_analyzer_prompt,
            assessment_prompt_builder=build_assessment_reflector_prompt,
            lesson_state_formatter=format_lesson_state,
            pacing_state_formatter=format_pacing_state,
            misconception_state_formatter=format_misconception_state,
            transcript_formatter=self._format_reflection_transcript,
            json_parser=self._parse_json_response,
        )
        self._graph_progression_orchestrator = GraphProgressionOrchestrator(
            reasoning_client=self.reasoning_client,
            json_parser=self._parse_json_response,
        )
        self._session_state_repository = GuidedSessionStateRepository(
            session_cache=self._session_cache,
            restore_cache=lambda *args, **kwargs: self._restore_session_cache(
                *args,
                **kwargs,
            ),
            persist_cache=lambda *args, **kwargs: self._persist_session_cache(
                *args,
                **kwargs,
            ),
            load_student_bundle=lambda *args, **kwargs: self._load_student_bundle(
                *args,
                **kwargs,
            ),
            format_student_context=lambda *args, **kwargs: self._format_student_context(
                *args,
                **kwargs,
            ),
        )
        self._guided_turn_orchestrator = GuidedTurnOrchestrator(
            student_mcp=self.student_mcp,
            state_repository=self._session_state_repository,
            content_pipeline=lambda *args, **kwargs: self._run_teaching_content_pipeline(
                *args,
                **kwargs,
            ),
            teaching_plan_error_cls=TeachingPlanGenerationError,
            get_combined_context=lambda *args, **kwargs: self.get_combined_context(
                *args,
                **kwargs,
            ),
            generate_teaching_plan=lambda *args, **kwargs: self._generate_teaching_plan(
                *args,
                **kwargs,
            ),
            get_assessment_context=lambda *args, **kwargs: self._get_assessment_context(
                *args,
                **kwargs,
            ),
            assessment_reflector=lambda *args, **kwargs: self._run_assessment_reflector(
                *args,
                **kwargs,
            ),
            turn_analyzer=lambda *args, **kwargs: self._run_turn_analyzer(
                *args,
                **kwargs,
            ),
            coerce_misconception_events=lambda *args, **kwargs: self._coerce_misconception_events(
                *args,
                **kwargs,
            ),
            apply_misconception_events=lambda *args, **kwargs: self._apply_misconception_events(
                *args,
                **kwargs,
            ),
            apply_memory_patches=lambda *args, **kwargs: self._apply_memory_patches(
                *args,
                **kwargs,
            ),
            apply_turn_analysis_updates=lambda *args, **kwargs: self._apply_turn_analysis_updates(
                *args,
                **kwargs,
            ),
            decide_graph_progression=lambda *args, **kwargs: self._decide_graph_progression(
                *args,
                **kwargs,
            ),
            build_tutor_messages=lambda *args, **kwargs: self._build_guided_tutor_messages(
                *args,
                **kwargs,
            ),
            stream_response=lambda *args, **kwargs: self._stream_response(
                *args,
                **kwargs,
            ),
            append_to_conversation=self.append_to_conversation,
            advance_to_next_objective=lambda *args, **kwargs: self._advance_to_next_objective(
                *args,
                **kwargs,
            ),
            render_turn_analysis=lambda *args, **kwargs: self._render_turn_analysis_for_display(
                *args,
                **kwargs,
            ),
            safe_serialize=safe_serialize,
        )
        self.memory_file = "conversation_memory.json"
        self.conversation_memory: Dict[str, List[Dict[str, str]]] = {}
        self._load_conversation_memory()
        logger.info("Hybrid CrewAI Socratic System initialized successfully")

    # --- (This is the corrected create_student_profile function from last time) ---
    def create_student_profile(
        self,
        name: str,
        topic: str,
        initial_assessment: str = "",
        student_id_override: str | None = None,
    ) -> Dict[str, Any]:
        try:
            student_id = student_id_override or str(uuid.uuid4())[:8]
            profile = self.create_student(
                student_id=student_id,
                name=name,
                topic=topic,
                initial_assessment=initial_assessment,
            )
            return {
                "student_id": profile.id,  # Corrected to profile.id
                "name": profile.name,
                "topic": profile.current_topic,
                "status": "success",
            }
        except Exception as e:
            logger.error(f"Failed to create student profile: {e}", exc_info=True)
            return {"error": str(e)}

    def get_student_profile(self, student_id: str) -> Optional[StudentProfile]:
        # (This method is unchanged)
        try:
            return self.db.load_student_profile(student_id)
        except Exception as e:
            logger.error(f"Failed to get student profile: {e}")
            return None

    def update_student_progress(
        self,
        student_id: str,
        knowledge_level: KnowledgeLevel,
        session_phase: SessionPhase,
    ) -> Dict[str, Any]:
        # (This method is unchanged)
        try:
            profile = self.db.load_student_profile(student_id)
            if not profile:
                return {"error": "Student not found"}
            profile.knowledge_level = knowledge_level
            profile.session_phase = session_phase
            profile.updated_at = datetime.now().isoformat()
            if self.db.save_student_profile(profile):
                return {"status": "success"}
            else:
                return {"error": "Failed to save profile"}
        except Exception as e:
            logger.error(f"Failed to update student progress: {e}")
            return {"error": str(e)}

    def get_session_history(self, student_id: str) -> List[Dict[str, Any]]:
        # (This method is unchanged)
        try:
            return [
                {
                    "session_id": "session-1",
                    "student_id": student_id,
                    "timestamp": datetime.now().isoformat(),
                    "response": "Sample response",
                    "tutor_response": "Sample tutor response",
                }
            ]
        except Exception as e:
            logger.error(f"Failed to get session history: {e}")
            return []

    # --- (This is the corrected create_student function from last time) ---
    def create_student(
        self, student_id: str, name: str, topic: str, initial_assessment: str = ""
    ) -> StudentProfile:
        profile = StudentProfile(
            id=student_id,
            name=name,
            current_topic=topic,
            knowledge_level=KnowledgeLevel.RECALL,
            session_phase=SessionPhase.OPENING,
        )
        if self.db.save_student_profile(profile):
            logger.info(f"Created student: {name} (ID: {student_id})")
            return profile
        else:
            raise RuntimeError(f"Failed to save student profile for {name}")

        # -----------------------------------------------------------------------

    # MEMORY MANAGEMENT
    # -----------------------------------------------------------------------
    def _save_conversation_memory(self):
        try:
            with open(self.memory_file, "w") as f:
                json.dump(self.conversation_memory, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")

    def _load_conversation_memory(self):
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r") as f:
                    self.conversation_memory = json.load(f)
                    logger.info("Loaded persistent conversation memory.")
            except Exception as e:
                logger.error(f"Failed to load memory: {e}")

    def get_conversation_history(self, student_id: str) -> List[Dict[str, str]]:
        return copy.deepcopy(self.conversation_memory.get(student_id, []))

    def append_to_conversation(self, student_id: str, role: str, content: str):
        self.conversation_memory.setdefault(student_id, [])
        self.conversation_memory[student_id].append({"role": role, "content": content})
        # keep only last 10 turns
        self.conversation_memory[student_id] = self.conversation_memory[student_id][
            -10:
        ]
        self._save_conversation_memory()

    def generate_hyde_query(self, query: str, history: List[Dict[str, str]]) -> str:
        """
        HyDE (Hypothetical Document Embedding): generate a hypothetical
        correct-answer-style response to the student's question.
        This answer-shaped text is then embedded and matched against our
        feedback-centered chunks in the vector DB.

        Also resolves vague references ("this", "that") using conversation history.
        Replaces the old query-rewriting step.
        """
        recent = history[-4:] if history else []
        context_str = ""
        if recent:
            context_str = (
                "Recent conversation:\n"
                + "\n".join(f"{m['role']}: {m['content']}" for m in recent)
                + "\n\n"
            )

        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a web accessibility expert. Given a student's question "
                        "(and optionally recent conversation for context), write a short "
                        "factual answer (3-5 sentences) as if you were explaining the correct "
                        "answer on a quiz. Include specific terms, WCAG references, and "
                        "common misconceptions where relevant.\n"
                        "Output ONLY the hypothetical answer, nothing else."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"{context_str}"
                        f'Student\'s question: "{query}"\n\n'
                        "Hypothetical correct answer:"
                    ),
                },
            ]
            hyde_answer = self.client.chat(
                messages, temperature=0.3, max_tokens=300, reasoning_effort="low"
            )
            hyde_answer = hyde_answer.strip()
            if hyde_answer and len(hyde_answer) > 10:
                logger.info(
                    f"HyDE generated ({len(hyde_answer)} chars): '{hyde_answer[:80]}...'"
                )
                return hyde_answer
        except Exception as e:
            logger.warning(f"HyDE generation failed, using original query: {e}")

        return query

    async def get_rag_context(
        self, query: str, history: Optional[List[Dict[str, str]]] = None
    ) -> tuple:
        """
        Retrieve RAG context using HyDE + hybrid search.

        1. Generate a hypothetical answer (answer-shaped, context-resolved)
        2. Embed it and search against feedback-centered chunks via RRF
        3. Filter by cosine distance threshold to reject garbage matches
        4. Return (context_string, filtered_chunks_list)
        """
        logger.info(f"Retrieving Context for : {query[:50]}...")

        # HyDE: generate answer-shaped text for better embedding match
        hyde_query = self.generate_hyde_query(query, history or [])

        # Hybrid search: vector (on HyDE embedding) + BM25 (on original student words)
        # HyDE text matches answer-shaped feedback in embedding space
        # Original query provides keyword signal for BM25
        retrieved_chunks = await self.vector_store.hybrid_search(
            query=hyde_query, k=5, bm25_query=query
        )

        # Filter: reject chunks where vector distance is too high
        # 0.3 keeps direct hits + close adjacents, rejects unrelated noise
        MAX_COSINE_DISTANCE = 0.3
        MIN_RRF_SCORE = 0.01
        high_quality_chunks = []
        for chunk in retrieved_chunks:
            distance = chunk.get("distance")
            rrf = chunk.get("rrf_score", 0)
            # Accept if: good RRF score AND reasonable vector distance
            if distance is not None and distance > MAX_COSINE_DISTANCE:
                logger.debug(
                    f"Rejected chunk (distance={distance:.3f}): {chunk.get('content', '')[:60]}"
                )
                continue
            if rrf < MIN_RRF_SCORE:
                continue
            high_quality_chunks.append(chunk)

        if not high_quality_chunks:
            logger.info(
                "No high-quality chunks found. LLM will rely on general knowledge."
            )
            return "", []

        context_for_agents = "\n--\n".join(
            c.get("content", "") for c in high_quality_chunks
        )
        logger.info(f"RAG context: {len(high_quality_chunks)} chunks passed to agents")
        return context_for_agents, high_quality_chunks

    async def get_combined_context(
        self, query: str, history: Optional[List[Dict[str, str]]] = None
    ) -> tuple:
        """
        Run RAG + MCP concurrently.
        Returns (combined_context_str, quiz_chunks_list, wcag_context_str).
        """
        # Build tasks
        rag_coro = self.get_rag_context(query, history)
        if self.wcag_mcp:
            mcp_coro = self.wcag_mcp.get_wcag_context(query)
        else:

            async def _empty():
                return ""

            mcp_coro = _empty()

        (rag_context, quiz_chunks), wcag_context = await asyncio.gather(
            rag_coro, mcp_coro
        )

        logger.info(
            f"Combined context: RAG={len(rag_context)} chars, WCAG MCP={len(wcag_context)} chars"
        )

        # Build combined context with labeled sections
        parts = []
        if rag_context:
            parts.append(f"--- QUIZ KNOWLEDGE BASE ---\n{rag_context}")
        if wcag_context:
            parts.append(
                f"--- WCAG GUIDELINES REFERENCE (authoritative) ---\n{wcag_context}"
            )

        combined = "\n\n".join(parts)
        return combined, quiz_chunks, wcag_context

    # ------------------------------------------------------------------
    # Student MCP context helpers
    # ------------------------------------------------------------------

    async def _load_student_bundle(
        self,
        student_id: str,
        objective_id: str = "",
    ) -> Dict[str, Any]:
        """Load the complete learner-state bundle for guided tutoring."""
        if not self.student_mcp:
            return {}

        try:
            if hasattr(self.student_mcp, "get_memory_bundle"):
                bundle = await self.student_mcp.get_memory_bundle(
                    student_id, objective_id
                )
                return bundle if isinstance(bundle, dict) else {}

            profile, mastery, session, misconceptions = await asyncio.gather(
                self.student_mcp.get_profile(student_id),
                self.student_mcp.get_mastery_state(student_id),
                self.student_mcp.get_active_session(student_id),
                self.student_mcp.get_misconception_patterns(student_id),
            )
            learner_memory = None
            objective_memory = None
            if hasattr(self.student_mcp, "get_learner_memory"):
                learner_memory = await self.student_mcp.get_learner_memory(student_id)
            if objective_id and hasattr(self.student_mcp, "get_objective_memory"):
                objective_memory = await self.student_mcp.get_objective_memory(
                    student_id, objective_id
                )
            return {
                "profile": profile,
                "mastery": mastery,
                "session": session,
                "misconceptions": misconceptions,
                "learner_memory": learner_memory,
                "objective_memory": objective_memory,
            }
        except Exception as e:
            logger.warning(f"Failed to load student bundle: {e}")
            return {}

    async def _load_student_context(
        self,
        student_id: str,
        objective_id: str = "",
    ) -> str:
        """Load learner state and format it for tutor or reflector prompts."""
        bundle = await self._load_student_bundle(student_id, objective_id)
        if not bundle:
            return ""
        return self._format_student_context(
            bundle.get("profile"),
            bundle.get("mastery", []),
            bundle.get("session"),
            bundle.get("misconceptions", []),
            bundle.get("learner_memory"),
            bundle.get("objective_memory"),
        )

    async def _restore_session_cache(
        self,
        session_id: str,
        objective_id: str = "",
    ) -> None:
        """Rehydrate the in-memory session cache from durable storage if available."""
        if self._session_cache.get(session_id):
            return
        if not self.student_mcp or not hasattr(
            self.student_mcp, "get_session_runtime_cache"
        ):
            return
        try:
            payload = await self.student_mcp.get_session_runtime_cache(session_id)
        except Exception as e:
            logger.warning(f"Failed to restore session runtime cache: {e}")
            return
        if not payload or not isinstance(payload, dict):
            return
        cached_objective = str(payload.get("objective_id", "") or "")
        if objective_id and cached_objective and cached_objective != objective_id:
            logger.info(
                "Skipping persisted runtime cache for session=%s because objective changed "
                "(cached=%s current=%s)",
                session_id,
                cached_objective,
                objective_id,
            )
            return
        self._session_cache.restore(session_id, payload)
        logger.info(
            "Restored session runtime cache for session=%s objective=%s",
            session_id,
            cached_objective or objective_id,
        )

    async def _persist_session_cache(self, session_id: str) -> None:
        """Persist the current in-memory session cache payload when supported."""
        if not self.student_mcp or not hasattr(
            self.student_mcp, "save_session_runtime_cache"
        ):
            return
        payload = self._session_cache.export_session(session_id)
        if not payload:
            return
        try:
            await self.student_mcp.save_session_runtime_cache(session_id, payload)
        except Exception as e:
            logger.warning(f"Failed to persist session runtime cache: {e}")

    async def _clear_persisted_session_cache(self, session_id: str) -> None:
        """Remove any durable runtime cache for a session."""
        if not self.student_mcp or not hasattr(
            self.student_mcp, "clear_session_runtime_cache"
        ):
            return
        try:
            await self.student_mcp.clear_session_runtime_cache(session_id)
        except Exception as e:
            logger.warning(f"Failed to clear session runtime cache: {e}")

    def _format_student_context(
        self,
        profile: Optional[Dict],
        mastery: List[Dict],
        session: Optional[Dict],
        misconceptions: List[Dict],
        learner_memory: Optional[Dict] = None,
        objective_memory: Optional[Dict] = None,
    ) -> str:
        """Format student MCP data into a concise text block for the system prompt."""
        parts = []

        if profile:
            parts.append(
                f"STUDENT PROFILE:\n"
                f"  Level: {profile.get('technical_level', 'unknown')} | "
                f"A11y experience: {profile.get('a11y_exposure', 'unknown')} | "
                f"Role: {profile.get('role_context', 'unknown')} | "
                f"Style: {profile.get('preferred_style', 'balanced')}"
            )

        if session:
            stage = session.get("current_stage", "unknown")
            objective = session.get("active_objective_id", "none")
            turns = session.get("turns_on_objective", 0)
            summary = session.get("stage_summary", "")
            session_block = (
                f"ACTIVE SESSION:\n"
                f"  Stage: {stage} | Objective: {objective} | Turns: {turns}"
            )
            if summary:
                session_block += f"\n  Previous stage summary: {summary}"
            parts.append(session_block)

        if mastery:
            mastery_lines = []
            for m in mastery[:10]:  # cap to avoid token bloat
                mastery_lines.append(
                    f"  {m.get('objective_id', '?')}: {m.get('mastery_level', '?')}"
                    + (
                        f" ({m.get('evidence_summary', '')})"
                        if m.get("evidence_summary")
                        else ""
                    )
                )
            parts.append("MASTERY STATE:\n" + "\n".join(mastery_lines))

        if misconceptions:
            misc_lines = [
                f"  - {m.get('misconception_text', '?')} (objective: {m.get('objective_id', '?')})"
                for m in misconceptions[:5]  # cap to avoid token bloat
            ]
            parts.append("ACTIVE MISCONCEPTIONS:\n" + "\n".join(misc_lines))

        if objective_memory:
            obj_lines = []
            if objective_memory.get("summary"):
                obj_lines.append(f"  Summary: {objective_memory['summary']}")
            if objective_memory.get("demonstrated_skills"):
                obj_lines.append(
                    "  Demonstrated: "
                    + ", ".join(objective_memory.get("demonstrated_skills", [])[:5])
                )
            if objective_memory.get("active_gaps"):
                obj_lines.append(
                    "  Gaps: " + ", ".join(objective_memory.get("active_gaps", [])[:5])
                )
            if objective_memory.get("next_focus"):
                obj_lines.append(f"  Next focus: {objective_memory['next_focus']}")
            if obj_lines:
                parts.append("OBJECTIVE MEMORY:\n" + "\n".join(obj_lines))

        if learner_memory:
            learner_lines = []
            if learner_memory.get("summary"):
                learner_lines.append(f"  Summary: {learner_memory['summary']}")
            if learner_memory.get("strengths"):
                learner_lines.append(
                    "  Strengths: " + ", ".join(learner_memory.get("strengths", [])[:5])
                )
            if learner_memory.get("support_needs"):
                learner_lines.append(
                    "  Support needs: "
                    + ", ".join(learner_memory.get("support_needs", [])[:5])
                )
            if learner_memory.get("tendencies"):
                learner_lines.append(
                    "  Tendencies: "
                    + ", ".join(learner_memory.get("tendencies", [])[:5])
                )
            if learner_memory.get("successful_strategies"):
                learner_lines.append(
                    "  Works well: "
                    + ", ".join(learner_memory.get("successful_strategies", [])[:5])
                )
            if learner_lines:
                parts.append("LEARNER MEMORY:\n" + "\n".join(learner_lines))

        if not parts:
            return ""

        return "\n".join(parts)

    @staticmethod
    def _parse_json_response(
        text: str, fallback: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Parse a JSON object from a model response, stripping code fences."""
        fallback = fallback or {}
        raw = (text or "").strip()
        if raw.startswith("```"):
            lines = raw.splitlines()
            if len(lines) >= 2:
                raw = "\n".join(
                    lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
                )
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else fallback
        except (json.JSONDecodeError, TypeError):
            logger.warning(f"Failed to parse model JSON: {raw[:200]}")
            return fallback

    @staticmethod
    def _merge_unique(existing: Any, incoming: Any) -> List[str]:
        """Merge two list-like values while preserving order and uniqueness."""
        merged = []
        seen = set()
        for source in (existing or [], incoming or []):
            if isinstance(source, str):
                source = [source]
            for item in source:
                if not item:
                    continue
                normalized = str(item).strip()
                if not normalized or normalized in seen:
                    continue
                seen.add(normalized)
                merged.append(normalized)
        return merged

    @classmethod
    def _merge_unique_capped(
        cls,
        existing: Any,
        incoming: Any,
        limit: int = 8,
    ) -> List[str]:
        merged = cls._merge_unique(existing, incoming)
        if limit > 0 and len(merged) > limit:
            merged = merged[-limit:]
        return merged

    @staticmethod
    def _normalize_memory_list(value: Any, limit: int = 8) -> List[str]:
        items = []
        seen = set()
        source = value or []
        if isinstance(source, str):
            source = [source]
        for item in source:
            normalized = str(item or "").strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            items.append(normalized)
        if limit > 0 and len(items) > limit:
            items = items[:limit]
        return items

    @staticmethod
    def _normalize_misconception_key(text: str = "", key: str = "") -> str:
        raw = (key or text or "").strip().lower()
        raw = re.sub(r"[^a-z0-9]+", "_", raw).strip("_")
        return raw or "misconception"

    @classmethod
    def _coerce_misconception_events(
        cls,
        payload: Optional[Dict[str, Any]],
        default_priority: str = "normal",
    ) -> List[Dict[str, str]]:
        if default_priority not in {"normal", "must_address_now"}:
            default_priority = "normal"

        events: List[Dict[str, str]] = []
        seen = set()
        payload = payload or {}
        if isinstance(payload, dict) and "student_turn" in payload:
            raw_events = runtime_misconception_events(payload)
        else:
            raw_events = payload.get("misconception_events", []) or []

        if isinstance(raw_events, dict):
            raw_events = [raw_events]

        for raw_event in raw_events:
            if not isinstance(raw_event, dict):
                continue
            action = str(raw_event.get("action", "") or "").strip().lower()
            if action not in {"log", "still_active", "resolve_candidate"}:
                continue
            text = str(raw_event.get("text", "") or "").strip()
            key = cls._normalize_misconception_key(
                text=text,
                key=str(raw_event.get("key", "") or ""),
            )
            priority = (
                str(raw_event.get("repair_priority", "") or default_priority)
                .strip()
                .lower()
            )
            if priority not in {"normal", "must_address_now"}:
                priority = default_priority
            repair_scope = str(raw_event.get("repair_scope", "") or "").strip().lower()
            if repair_scope not in {"fact", "distinction", "full_sequence"}:
                repair_scope = "fact"
            repair_pattern = (
                str(raw_event.get("repair_pattern", "") or "").strip().lower()
            )
            if repair_pattern not in {
                "direct_recheck",
                "same_snippet_walkthrough",
                "fresh_transfer",
            }:
                repair_pattern = "direct_recheck"
            identity = (key, action, text)
            if identity in seen:
                continue
            seen.add(identity)
            events.append(
                {
                    "key": key,
                    "text": text,
                    "action": action,
                    "repair_priority": priority,
                    "repair_scope": repair_scope,
                    "repair_pattern": repair_pattern,
                }
            )

        legacy_log_priority = default_priority
        for text in payload.get("misconceptions_to_log", []) or []:
            normalized = str(text or "").strip()
            if not normalized:
                continue
            key = cls._normalize_misconception_key(text=normalized)
            identity = (key, "log", normalized)
            if identity in seen:
                continue
            seen.add(identity)
            events.append(
                {
                    "key": key,
                    "text": normalized,
                    "action": "log",
                    "repair_priority": legacy_log_priority,
                    "repair_scope": "fact",
                    "repair_pattern": "direct_recheck",
                }
            )

        for text in payload.get("misconceptions_to_resolve", []) or []:
            normalized = str(text or "").strip()
            if not normalized:
                continue
            key = cls._normalize_misconception_key(text=normalized)
            identity = (key, "resolve_candidate", normalized)
            if identity in seen:
                continue
            seen.add(identity)
            events.append(
                {
                    "key": key,
                    "text": normalized,
                    "action": "resolve_candidate",
                    "repair_priority": "normal",
                    "repair_scope": "fact",
                    "repair_pattern": "direct_recheck",
                }
            )

        return events

    @staticmethod
    def _format_active_misconception_guidance(
        turn_analysis: Optional[Dict[str, Any]],
        misconception_state: Optional[Dict[str, Any]],
    ) -> str:
        must_address = [
            item
            for item in GuidedTutorSystem._coerce_misconception_events(
                turn_analysis
            )
            if isinstance(item, dict)
            and GuidedTutorSystem._is_open_must_repair_event(item)
        ]
        if not must_address:
            return ""

        lines = ["ACTIVE MISCONCEPTION REPAIR:"]
        procedural_sequence_repair = False
        conceptual_sequence_repair = False
        for item in must_address[:2]:
            text = str(item.get("text", "") or item.get("key", "")).strip()
            if text:
                lines.append(f"- Open misconception: {text}")
            if GuidedTutorSystem._is_procedural_full_sequence_repair(item):
                procedural_sequence_repair = True
            else:
                repair_scope = str(item.get("repair_scope", "") or "").strip().lower()
                repair_pattern = (
                    str(item.get("repair_pattern", "") or "").strip().lower()
                )
                if (
                    repair_scope == "full_sequence"
                    or repair_pattern == "same_snippet_walkthrough"
                ):
                    conceptual_sequence_repair = True
        if procedural_sequence_repair:
            lines.append(
                "- This is a procedural repair: keep the same snippet and require the learner to walk the full checklist in order."
            )
            lines.append(
                "- Required order: native-first -> semantic override -> behavior -> focus -> required state/property."
            )
            lines.append(
                "- Do not ask for a localized explanation or the next single check."
            )
            lines.append(
                "- Ask for one end-to-end walkthrough question only, then wait for the learner's full pass."
            )
            return "\n".join(lines)
        if conceptual_sequence_repair:
            lines.append(
                "- This is an exact-sequence completion repair: keep the same example and require one complete ordered pass."
            )
            lines.append(
                "- Require the missing named step(s) and the final label explicitly."
            )
            lines.append(
                "- Ask for one exact restatement only; do not broaden into a new concept."
            )
            return "\n".join(lines)
        lines.append(
            "- Repair the misconception explicitly before introducing a new concept."
        )
        lines.append(
            "- Contrast the incorrect model with the correct one, use one concrete example, and ask one narrow check."
        )
        return "\n".join(lines)

    @staticmethod
    def _lesson_coverage_ratio(lesson_state: Optional[Dict[str, Any]]) -> float:
        if not lesson_state or not isinstance(lesson_state, dict):
            return 0.0
        concepts = lesson_state.get("concepts", []) or []
        if not concepts:
            return 0.0
        covered = sum(
            1
            for concept in concepts
            if isinstance(concept, dict) and concept.get("status") == "covered"
        )
        return covered / len(concepts)

    @staticmethod
    def _has_repeated_full_sequence_signal(
        misconception_state: Optional[Dict[str, Any]],
        bucket: str,
        min_times_seen: int = 2,
    ) -> bool:
        if not misconception_state or not isinstance(misconception_state, dict):
            return False
        items = misconception_state.get(bucket, []) or []
        for item in items:
            if not isinstance(item, dict):
                continue
            scope = str(item.get("repair_scope", "") or "").strip().lower()
            pattern = str(item.get("repair_pattern", "") or "").strip().lower()
            try:
                times_seen = int(item.get("times_seen", 0) or 0)
            except (TypeError, ValueError):
                times_seen = 0
            if times_seen >= min_times_seen and (
                scope == "full_sequence" or pattern == "same_snippet_walkthrough"
            ):
                return True
        return False

    @staticmethod
    def _is_procedural_full_sequence_repair(
        item: Optional[Dict[str, Any]],
    ) -> bool:
        if not item or not isinstance(item, dict):
            return False
        repair_scope = str(item.get("repair_scope", "") or "").strip().lower()
        repair_pattern = str(item.get("repair_pattern", "") or "").strip().lower()
        combined = " ".join(
            str(item.get(field, "") or "").lower() for field in ("key", "text")
        )
        procedural_markers = (
            "aria",
            "native-first",
            "native first",
            "semantic override",
            "behavior",
            "focus",
            "required state",
            "state/property",
            "audit",
            "debug",
            "walkthrough",
            "checklist",
            "rule sequence",
            "full rule sequence",
        )
        return (
            repair_scope == "full_sequence"
            or repair_pattern == "same_snippet_walkthrough"
            or any(marker in combined for marker in procedural_markers)
        )

    @staticmethod
    def _supports_repair_exit(pacing_signal: Optional[Dict[str, Any]]) -> bool:
        pacing_signal = pacing_signal or {}
        concept_closure = (
            str(pacing_signal.get("concept_closure", "") or "").strip().lower()
        )
        reasoning_mode = (
            str(pacing_signal.get("reasoning_mode", "") or "").strip().lower()
        )
        return concept_closure in {"almost_ready", "ready"} and reasoning_mode in {
            "application",
            "transfer",
        }

    @staticmethod
    def _is_open_must_repair_event(item: Optional[Dict[str, Any]]) -> bool:
        if not isinstance(item, dict):
            return False
        if str(item.get("repair_priority", "") or "") != "must_address_now":
            return False
        action = str(item.get("action", "") or "").strip().lower()
        return action != "resolve_candidate"

    @staticmethod
    def _allows_intro_exit_with_partial_closure(
        current_stage: str,
        target_stage: str,
        pacing_signal: Optional[Dict[str, Any]],
    ) -> bool:
        if (
            str(current_stage or "").strip().lower() != "introduction"
            or str(target_stage or "").strip().lower() != "exploration"
        ):
            return False
        pacing_signal = pacing_signal or {}
        concept_closure = (
            str(pacing_signal.get("concept_closure", "") or "").strip().lower()
        )
        reasoning_mode = (
            str(pacing_signal.get("reasoning_mode", "") or "").strip().lower()
        )
        return concept_closure in {"almost_ready", "ready"} and reasoning_mode in {
            "application",
            "transfer",
        }

    @classmethod
    def _normalize_stage_transition(
        cls,
        current_stage: str,
        stage_action: str,
        target_stage: str,
        stage_reason: str = "",
    ) -> tuple[str, str, str]:
        current = str(current_stage or "").strip().lower()
        action = str(stage_action or "").strip().lower()
        target = str(target_stage or "").strip().lower()
        reason = str(stage_reason or "").strip()
        if (
            action not in {"advance", "regress"}
            or current not in GUIDED_STAGE_SEQUENCE
            or target not in GUIDED_STAGE_SEQUENCE
            or current == target
        ):
            return stage_action, target_stage, stage_reason

        current_index = GUIDED_STAGE_SEQUENCE.index(current)
        target_index = GUIDED_STAGE_SEQUENCE.index(target)
        normalized_target = target
        note = ""
        if action == "advance" and target_index > current_index + 1:
            normalized_target = GUIDED_STAGE_SEQUENCE[current_index + 1]
            note = (
                f"Stage order normalized: move from {current} to "
                f"{normalized_target} before {target}."
            )
        elif action == "regress" and target_index < current_index - 1:
            normalized_target = GUIDED_STAGE_SEQUENCE[current_index - 1]
            note = (
                f"Stage order normalized: regress from {current} to "
                f"{normalized_target} before {target}."
            )

        if note:
            reason = f"{reason} {note}".strip() if reason else note
            return action, normalized_target, reason
        return stage_action, target_stage, stage_reason

    @classmethod
    def _suggest_next_stage_after_repair(
        cls,
        current_stage: str,
        coverage_ratio: float,
    ) -> Optional[str]:
        stage = str(current_stage or "").strip().lower()
        if stage == "introduction":
            return "exploration"
        if stage == "exploration" and coverage_ratio >= 0.6:
            return "readiness_check"
        if stage == "readiness_check" and coverage_ratio >= 0.6:
            return "mini_assessment"
        return None

    @staticmethod
    def _append_one_turn_goal(goal: str, addition: str) -> str:
        goal = str(goal or "").strip()
        addition = str(addition or "").strip()
        if not addition:
            return goal
        if not goal:
            return addition
        if addition.lower() in goal.lower():
            return goal
        return f"{goal} {addition}".strip()

    @classmethod
    def _enforce_turn_response_controls(
        cls,
        current_stage: str,
        analysis: Optional[Dict[str, Any]],
        lesson_state: Optional[Dict[str, Any]],
        pacing_state: Optional[Dict[str, Any]],
        misconception_state: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        return_legacy_shape = not (
            isinstance(analysis, dict) and "student_turn" in analysis
        )
        guarded = normalize_analyzer_output(analysis, current_stage=current_stage)
        if not guarded:
            return {}

        tutor = guarded["next_tutor_handoff"]
        progression = guarded["progression_recommendation"]
        consistency = guarded["consistency_check"]
        teaching_move = str(tutor.get("move", "") or "").strip().lower()
        concept_closure = (
            str(progression.get("closure_state", "") or "").strip().lower()
        )
        evidence_quality = (
            str(progression.get("evidence_quality", "") or "").strip().lower()
        )
        (
            progression["stage_action"],
            progression["target_stage"],
            progression["progression_blocker"],
        ) = cls._normalize_stage_transition(
            current_stage=current_stage,
            stage_action=progression.get("stage_action", ""),
            target_stage=progression.get("target_stage", current_stage),
            stage_reason=progression.get("progression_blocker", ""),
        )
        if progression["progression_blocker"] not in {
            "none",
            "open_question",
            "misconception",
            "weak_evidence",
            "coverage_gap",
            "terminal_node",
            "source_uncertainty",
        }:
            existing_conflict = str(consistency.get("conflict", "") or "").strip()
            normalization_note = str(progression["progression_blocker"] or "").strip()
            consistency["conflict"] = (
                f"{existing_conflict} {normalization_note}".strip()
                if existing_conflict
                else normalization_note
            )
            progression["progression_blocker"] = "none"
        stage_action_value = (
            str(progression.get("stage_action", "") or "").strip().lower()
        )
        target_stage = str(progression.get("target_stage", "") or "").strip()

        must_repair_now = has_open_must_repair(guarded)
        repeated_active_sequence = cls._has_repeated_full_sequence_signal(
            misconception_state,
            "active_misconceptions",
        )
        repeated_resolved_sequence = cls._has_repeated_full_sequence_signal(
            misconception_state,
            "recently_resolved",
        )
        supports_repair_exit = concept_closure in {
            "almost_ready",
            "ready",
        } and evidence_quality in {
            "partial",
            "strong",
        }

        reasons: List[str] = []
        if must_repair_now:
            reasons.append(
                "Open must-repair misconception still needs explicit correction."
            )
        if (
            stage_action_value == "advance"
            and concept_closure != "ready"
            and not cls._allows_intro_exit_with_partial_closure(
                current_stage=current_stage,
                target_stage=target_stage,
                pacing_signal=runtime_pacing_signal(guarded),
            )
        ):
            reasons.append("Concept closure is not ready yet.")
        coverage_ratio = cls._lesson_coverage_ratio(lesson_state)
        if (
            stage_action_value == "advance"
            and target_stage
            in {"readiness_check", "mini_assessment", "final_assessment"}
            and coverage_ratio < 0.6
        ):
            reasons.append("Objective coverage is still too low for the next stage.")

        if reasons:
            progression["stage_action"] = "stay"
            progression["target_stage"] = current_stage
            existing_reason = str(consistency.get("conflict", "") or "").strip()
            joined = " ".join(reasons)
            consistency["status"] = "needs_repair"
            consistency["conflict"] = (
                f"{existing_reason} {joined}".strip() if existing_reason else joined
            )
            consistency[
                "repair_instruction"
            ] = "Use the conservative stay/clarify interpretation for this turn."
            if must_repair_now and teaching_move not in {"repair", "clarify"}:
                tutor["move"] = "repair"
            if must_repair_now:
                tutor["support_level"] = "heavy"
                tutor[
                    "one_turn_goal"
                ] = "Active misconception requires explicit repair before moving on."

        if (
            not must_repair_now
            and teaching_move in {"repair", "clarify"}
            and not repeated_active_sequence
            and evidence_quality in {"partial", "strong"}
        ):
            tutor["support_level"] = "light"
            tutor["one_turn_goal"] = cls._append_one_turn_goal(
                tutor.get("one_turn_goal", ""),
                "Learner already shows causal footing; use a fresh case instead of another same-level restatement check.",
            )

        if (
            not must_repair_now
            and teaching_move == "clarify"
            and guarded["student_turn"].get("answer_first")
        ):
            tutor["one_turn_goal"] = cls._append_one_turn_goal(
                tutor.get("one_turn_goal", ""),
                "If the explanation fully resolves the question, a follow-up check is optional.",
            )

        if not must_repair_now and repeated_active_sequence and supports_repair_exit:
            tutor["move"] = "clarify"
            tutor["support_level"] = "light"
            tutor["one_turn_goal"] = cls._append_one_turn_goal(
                tutor.get("one_turn_goal", ""),
                "Repeated full-sequence repair now has enough evidence for a fresh transfer check.",
            )

        if (
            not must_repair_now
            and repeated_resolved_sequence
            and supports_repair_exit
            and str(progression.get("stage_action", "") or "").strip().lower()
            != "advance"
        ):
            next_stage = cls._suggest_next_stage_after_repair(
                current_stage=current_stage,
                coverage_ratio=coverage_ratio,
            )
            if next_stage:
                progression["stage_action"] = "advance"
                progression["target_stage"] = next_stage
                existing_reason = str(consistency.get("conflict", "") or "").strip()
                repair_reason = "Repeated full-sequence repair now looks stable after transfer-level reasoning."
                consistency["conflict"] = (
                    f"{existing_reason} {repair_reason}".strip()
                    if existing_reason
                    else repair_reason
                )
                tutor["move"] = "consolidate"
                tutor["support_level"] = "light"
                tutor[
                    "one_turn_goal"
                ] = "Repeated full-sequence repair was resolved with application-level evidence."

        guarded = normalize_analyzer_output(guarded, current_stage=current_stage)
        if return_legacy_shape:
            return canonical_to_trace_legacy(guarded)
        return guarded

    @staticmethod
    def _format_response_constraints_for_tutor(
        pacing_state: Optional[Dict[str, Any]],
        turn_analysis: Optional[Dict[str, Any]] = None,
        misconception_state: Optional[Dict[str, Any]] = None,
    ) -> str:
        canonical_analysis = normalize_analyzer_output(turn_analysis)
        pace = str((pacing_state or {}).get("current_pace", "") or "").strip().lower()
        if pace not in {"slow", "steady", "fast"}:
            pace = "steady"

        misconception_events = runtime_misconception_events(canonical_analysis)
        must_repair = any(
            isinstance(item, dict)
            and GuidedTutorSystem._is_open_must_repair_event(item)
            for item in misconception_events
        )
        requires_procedural_full_sequence_repair = any(
            isinstance(item, dict)
            and GuidedTutorSystem._is_open_must_repair_event(item)
            and GuidedTutorSystem._is_procedural_full_sequence_repair(item)
            for item in misconception_events
        )
        requires_conceptual_sequence_completion = any(
            isinstance(item, dict)
            and GuidedTutorSystem._is_open_must_repair_event(item)
            and not GuidedTutorSystem._is_procedural_full_sequence_repair(item)
            and (
                str(item.get("repair_scope", "") or "") == "full_sequence"
                or str(item.get("repair_pattern", "") or "")
                == "same_snippet_walkthrough"
            )
            for item in misconception_events
        )
        pacing_signal = runtime_pacing_signal(canonical_analysis)
        recommended_next_step = (
            str(pacing_signal.get("recommended_next_step", "") or "").strip().lower()
        )
        teaching_move = canonical_tutor_handoff(canonical_analysis).get("move", "")
        answer_current_question_first = bool(
            canonical_student_turn(canonical_analysis).get("answer_first")
        )
        repeated_active_sequence = (
            GuidedTutorSystem._has_repeated_full_sequence_signal(
                misconception_state,
                "active_misconceptions",
            )
        )

        response_shape = "question_only"
        if requires_procedural_full_sequence_repair:
            response_shape = "full_sequence_repair"
        elif requires_conceptual_sequence_completion:
            response_shape = "repair_and_check"
        elif (
            teaching_move == "clarify"
            and answer_current_question_first
            and not must_repair
        ):
            response_shape = "answer_then_optional_check"
        elif must_repair or recommended_next_step in {"re-explain", "ask_narrower"}:
            response_shape = "repair_and_check"
        elif recommended_next_step == "give_example":
            response_shape = "example_then_check"
        elif pace == "fast":
            response_shape = "brief_test"

        if (
            not must_repair
            and repeated_active_sequence
            and recommended_next_step
            in {"ask_narrower", "ask_same_level", "give_example"}
        ):
            response_shape = "example_then_check"

        max_new_concepts = 0 if pace == "slow" or must_repair else 1
        max_setup_sentences = 2 if pace == "fast" else 4 if pace == "slow" else 3

        lines = ["RESPONSE CONSTRAINTS:"]
        lines.append(f"- Response shape: {response_shape}")
        lines.append(f"- Max new concepts: {max_new_concepts}")
        lines.append("- Max questions: 1")
        lines.append(
            f"- Max setup sentences before the question: {max_setup_sentences}"
        )
        if teaching_move in {"repair", "clarify"}:
            lines.append(
                "- Do not ask an answer-echo question whose answer you just stated explicitly."
            )
        if response_shape == "answer_then_optional_check":
            lines.append(
                "- Answer the student's current question directly. If the explanation fully resolves it, you may end without a follow-up question."
            )
            lines.append(
                "- If you do ask a follow-up, make it a fresh application/comparison check, not a recap of your explanation."
            )
        if requires_procedural_full_sequence_repair:
            lines.append("- Repair pattern: same snippet ordered walkthrough")
            lines.append(
                "- Hard requirement: require the learner to walk native-first, semantic override, behavior, focus, and required state/property in order."
            )
            lines.append("- Do not reduce the repair to one local sub-question.")
        elif requires_conceptual_sequence_completion:
            lines.append(
                "- Repair pattern: exact ordered completion on the same example."
            )
            lines.append(
                "- Hard requirement: require one complete ordered restatement with the missing named step(s) and final label."
            )
            lines.append(
                "- Do not expand into a new concept before the exact completion check."
            )
        elif teaching_move == "repair":
            lines.append(
                "- After correcting the misconception, use one fresh case, comparison, or consequence check, not a restatement of your correction."
            )
        elif (
            not must_repair
            and repeated_active_sequence
            and response_shape == "example_then_check"
        ):
            lines.append(
                "- Prefer one fresh transfer example over another paraphrase recheck."
            )
        if must_repair:
            lines.append("- Advancement lock: open misconception")
        elif canonical_progression(canonical_analysis).get("stage_action") != "advance":
            lines.append(
                "- Advancement lock: stay on the current stage for this response"
            )
        else:
            lines.append("- Advancement lock: none")
        return "\n".join(lines)

    def _format_reflection_transcript(
        self,
        history: Optional[List[Dict[str, str]]],
        student_response: str,
        tutor_response: Optional[str] = None,
    ) -> str:
        """Format the recent exchange for the reflector model."""
        lines = []
        for msg in (history or [])[-6:]:
            role = "TUTOR" if msg.get("role") == "assistant" else "STUDENT"
            lines.append(f"{role}: {msg.get('content', '')}")
        lines.append(f"STUDENT: {student_response}")
        if tutor_response is not None:
            lines.append(f"TUTOR: {tutor_response}")
        return "\n".join(lines)

    @staticmethod
    def _format_turn_analysis_for_tutor(turn_analysis: Optional[Dict[str, Any]]) -> str:
        if not turn_analysis:
            return ""

        turn_analysis = normalize_analyzer_output(turn_analysis)
        lines = ["TURN ANALYSIS:"]
        student_turn = turn_analysis.get("student_turn") or {}
        tutor = turn_analysis.get("next_tutor_handoff") or {}
        progression = turn_analysis.get("progression_recommendation") or {}
        graph = turn_analysis.get("graph_handoff") or {}
        route = student_turn.get("route", "")
        if route:
            lines.append(f"- Route: {route}")
        answer_first = student_turn.get("answer_first")
        if answer_first is not None:
            lines.append(
                f"- Answer current question first: {'yes' if answer_first else 'no'}"
            )
        if student_turn.get("question_to_answer"):
            lines.append(
                f"- Student question to answer: {student_turn['question_to_answer']}"
            )
        if student_turn.get("open_question_type"):
            lines.append(f"- Open question type: {student_turn['open_question_type']}")
        if tutor.get("move"):
            lines.append(f"- Tutor move: {tutor['move']}")
        if tutor.get("support_level"):
            lines.append(f"- Support level: {tutor['support_level']}")
        if tutor.get("one_turn_goal"):
            lines.append(f"- One-turn goal: {tutor['one_turn_goal']}")
        if progression:
            lines.append(
                "- Progression: "
                f"{progression.get('stage_action', 'stay')} -> "
                f"{progression.get('target_stage', '')}; "
                f"closure={progression.get('closure_state', '')}; "
                f"evidence={progression.get('evidence_quality', '')}; "
                f"blocker={progression.get('progression_blocker', '')}"
            )
        if graph.get("bridge_mode"):
            lines.append(
                "- Graph handoff: "
                f"{graph.get('bridge_mode')} "
                f"current={graph.get('current_node_id', '')} "
                f"candidate={graph.get('candidate_next_node_id', '')}"
            )
        return "\n".join(lines)

    @staticmethod
    def _format_analysis_value_for_display(value: Any, max_chars: int = 220) -> str:
        if value is None:
            return "`null`"
        if isinstance(value, bool):
            return f"`{'true' if value else 'false'}`"
        if isinstance(value, (int, float)):
            return f"`{value}`"
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return '`""`'
            if len(text) > max_chars:
                text = f"{text[:max_chars - 3]}..."
            return f"`{text}`"
        try:
            text = json.dumps(value, ensure_ascii=True)
        except Exception:
            text = str(value)
        if len(text) > max_chars:
            text = f"{text[:max_chars - 3]}..."
        return f"`{text}`"

    @classmethod
    def _render_turn_analysis_field(
        cls,
        key: str,
        value: Any,
        meaning: str,
        role: str,
        computation: str,
    ) -> str:
        return (
            f"{key}\n"
            f"{meaning} {role} It is computed {computation}. "
            f"Current value: {cls._format_analysis_value_for_display(value)}."
        )

    @staticmethod
    def _ta_escape_for_md(text: str) -> str:
        """Neutralise stray HTML tags inside analyzer prose so the side panel
        markdown renderer doesn't treat ``<button>`` / ``<div>`` as real
        elements and silently swallow them. Only escapes ``<`` and ``>`` —
        leaves ``&`` alone so existing entities (e.g. ``&amp;``) survive a
        single-pass innerHTML decode."""
        return text.replace("<", "&lt;").replace(">", "&gt;")

    @classmethod
    def _ta_format_value(cls, value: Any, max_chars: int = 800) -> str:
        """Render a single analysis value as a compact display string.

        Strings are escaped for markdown (angle brackets only) so HTML
        examples like ``<button>`` survive the side panel render. Lists of
        dicts are rendered as bullet sublists rather than truncated JSON
        blobs so structured fields like ``concept_updates`` stay readable.
        """
        if value is None:
            return "_—_"
        if isinstance(value, bool):
            return "**yes**" if value else "no"
        if isinstance(value, (int, float)):
            return f"`{value}`"
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return "_—_"
            if len(text) > max_chars:
                text = text[: max_chars - 1] + "…"
            return cls._ta_escape_for_md(text)
        if isinstance(value, list):
            if not value:
                return "_none_"
            simple = [v for v in value if isinstance(v, (str, int, float, bool))]
            if len(simple) == len(value):
                joined = ", ".join(cls._ta_escape_for_md(str(v)) for v in simple)
                if len(joined) > max_chars:
                    joined = joined[: max_chars - 1] + "…"
                return joined
            if all(isinstance(v, dict) for v in value):
                # Render a list of dicts as a markdown sublist; keeps every
                # field intact instead of clipping a JSON dump mid-string.
                rows = []
                for item in value:
                    pairs = []
                    for k, v in item.items():
                        if v is None or v == "":
                            continue
                        if isinstance(v, (str, int, float, bool)):
                            v_text = cls._ta_escape_for_md(str(v))
                        else:
                            try:
                                v_text = cls._ta_escape_for_md(
                                    json.dumps(v, ensure_ascii=True)
                                )
                            except Exception:
                                v_text = cls._ta_escape_for_md(str(v))
                        if len(v_text) > 220:
                            v_text = v_text[:219] + "…"
                        pairs.append(f"{k}=`{v_text}`")
                    rows.append("  - " + " · ".join(pairs))
                return "\n" + "\n".join(rows)
            try:
                text = json.dumps(value, ensure_ascii=True)
            except Exception:
                text = str(value)
            if len(text) > max_chars:
                text = text[: max_chars - 1] + "…"
            return f"`{cls._ta_escape_for_md(text)}`"
        if isinstance(value, dict):
            if not value:
                return "_empty_"
            try:
                text = json.dumps(value, ensure_ascii=True)
            except Exception:
                text = str(value)
            if len(text) > max_chars:
                text = text[: max_chars - 1] + "…"
            return f"`{cls._ta_escape_for_md(text)}`"
        return f"`{cls._ta_escape_for_md(str(value))}`"

    @classmethod
    def _ta_kv_lines(
        cls, source: Dict[str, Any], items: List[tuple], indent: str = "- "
    ) -> List[str]:
        """Build `- **label:** value` lines for fields present in source."""
        out = []
        for key, label in items:
            if key not in source:
                continue
            out.append(f"{indent}**{label}:** {cls._ta_format_value(source.get(key))}")
        return out

    @classmethod
    def _render_turn_analysis_for_display(
        cls, turn_analysis: Optional[Dict[str, Any]]
    ) -> str:
        """Render the analyzer's per-turn output as compact, scannable markdown.

        Loses the per-field meta-prose ("This field controls…") that was
        identical every turn anyway, keeps every value, groups related fields,
        and uses bold labels + inline values so the side panel reads at a
        glance instead of as a wall of text.
        """
        if not turn_analysis:
            return ""

        turn_analysis = normalize_analyzer_output(turn_analysis)
        sections: List[str] = []
        student = turn_analysis.get("student_turn") or {}
        tutor = turn_analysis.get("next_tutor_handoff") or {}
        progression = turn_analysis.get("progression_recommendation") or {}
        graph = turn_analysis.get("graph_handoff") or {}
        state_patch = turn_analysis.get("state_patch") or {}
        mastery = turn_analysis.get("mastery_signal") or {}
        memory = turn_analysis.get("memory_patch") or {}
        consistency = turn_analysis.get("consistency_check") or {}

        sections.append(
            "  \n".join(
                [
                    f"**Route:** {cls._ta_format_value(student.get('route'))}",
                    f"**Answer first:** {cls._ta_format_value(student.get('answer_first'))}",
                    f"**Open question type:** {cls._ta_format_value(student.get('open_question_type'))}",
                    f"**Question:** _{cls._ta_format_value(student.get('question_to_answer'), max_chars=180)}_",
                ]
            )
        )
        sections.append(
            "**Next tutor handoff**\n"
            + "\n".join(
                cls._ta_kv_lines(
                    tutor,
                    [
                        ("move", "move"),
                        ("support_level", "support"),
                        ("one_turn_goal", "one-turn goal"),
                        ("source_certainty_needed", "source certainty needed"),
                    ],
                )
            )
        )
        sections.append(
            "**Progression recommendation**\n"
            + "\n".join(
                cls._ta_kv_lines(
                    progression,
                    [
                        ("stage_action", "stage action"),
                        ("target_stage", "target stage"),
                        ("closure_state", "closure"),
                        ("evidence_quality", "evidence quality"),
                        ("progression_blocker", "blocker"),
                    ],
                )
            )
        )
        sections.append(
            "**Graph handoff**\n"
            + "\n".join(
                cls._ta_kv_lines(
                    graph,
                    [
                        ("bridge_mode", "bridge mode"),
                        ("current_node_id", "current node"),
                        ("candidate_next_node_id", "candidate next"),
                        ("return_to_current_node", "return to current"),
                    ],
                )
            )
        )
        state_lines = cls._ta_kv_lines(
            state_patch,
            [
                ("active_concept_id", "active concept"),
                ("pending_check", "pending check"),
                ("concept_updates", "concept updates"),
            ],
        )
        if state_lines:
            sections.append("**State patch**\n" + "\n".join(state_lines))
        misconceptions = turn_analysis.get("misconceptions") or []
        if misconceptions:
            sections.append(
                f"**Misconceptions** ({len(misconceptions)})\n"
                + cls._ta_format_value(misconceptions)
            )
        sections.append(
            "**Mastery and memory**\n"
            + "\n".join(
                cls._ta_kv_lines(
                    mastery,
                    [("update", "mastery update"), ("level", "level")],
                )
                + cls._ta_kv_lines(
                    memory,
                    [
                        ("objective_summary", "objective summary"),
                        ("learner_summary", "learner summary"),
                        ("next_focus", "next focus"),
                    ],
                )
            )
        )
        sections.append(
            "**Consistency check**\n"
            + "\n".join(
                cls._ta_kv_lines(
                    consistency,
                    [
                        ("status", "status"),
                        ("conflict", "conflict"),
                        ("repair_instruction", "repair instruction"),
                    ],
                )
            )
        )
        return "\n\n".join(section for section in sections if section.strip())

    @staticmethod
    def _format_adaptive_pacing_for_tutor(
        pacing_state: Optional[Dict[str, Any]]
    ) -> str:
        if not pacing_state:
            return ""

        pace = str(pacing_state.get("current_pace", "") or "").strip().lower()
        if pace not in {"slow", "steady", "fast"}:
            return ""

        lines = ["ADAPTIVE PACING:"]
        lines.append(f"- Current pace: {pace}")
        if pacing_state.get("pace_reason"):
            lines.append(f"- Reason: {pacing_state['pace_reason']}")
        lines.append(
            f"- Turns at current pace: {int(pacing_state.get('turns_at_current_pace', 0) or 0)}"
        )

        if pace == "slow":
            lines.append(
                "- Response calibration: stay on the current concept, add concrete scaffold, and ask a narrower check."
            )
            lines.append(
                "- Advancement rule: do not treat a single good answer as enough to move on."
            )
            lines.append(
                "- Hard limit: do not introduce a new concept in this response."
            )
        elif pace == "steady":
            lines.append(
                "- Response calibration: keep normal concept flow with one focused explanation or one focused question."
            )
            lines.append(
                "- Advancement rule: advance only after a clear sign of understanding."
            )
            lines.append(
                "- Hard limit: keep the response inside one concept and one question."
            )
        else:
            lines.append(
                "- Response calibration: use shorter setup and prefer application, comparison, or transfer."
            )
            lines.append(
                "- Advancement rule: you may move faster, but still keep to one concept and one question."
            )
            lines.append(
                "- Hard limit: keep setup brief and do not bundle multiple new rules together."
            )

        lines.append("- If pacing and instinct conflict, bias slightly slower.")
        return "\n".join(lines)

    def _build_guided_tutor_messages(
        self,
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
        return self._tutor_message_builder.build(
            student_response=student_response,
            history=history,
            teaching_content=teaching_content,
            student_context=student_context,
            current_stage=current_stage,
            active_objective=active_objective,
            teaching_plan=teaching_plan,
            lesson_state=lesson_state,
            turn_analysis=turn_analysis,
            pacing_state=pacing_state,
            misconception_state=misconception_state,
            extra_system_messages=extra_system_messages,
            first_turn=first_turn,
        )

    async def _run_turn_analyzer(
        self,
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
        return await self._structured_turn_analyzer.analyze_turn(
            history=history,
            student_response=student_response,
            teaching_content=teaching_content,
            student_context=student_context,
            current_stage=current_stage,
            active_objective=active_objective,
            teaching_plan=teaching_plan,
            lesson_state=lesson_state,
            pacing_state=pacing_state,
            misconception_state=misconception_state,
        )

    async def _run_assessment_reflector(
        self,
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
        return await self._structured_turn_analyzer.reflect_on_assessment(
            history=history,
            student_response=student_response,
            teaching_content=teaching_content,
            student_context=student_context,
            current_stage=current_stage,
            active_objective=active_objective,
            teaching_plan=teaching_plan,
            lesson_state=lesson_state,
            misconception_state=misconception_state,
        )

    async def _decide_graph_progression(
        self,
        *,
        graph_state: Optional[Dict[str, Any]],
        turn_analysis: Optional[Dict[str, Any]],
        lesson_state: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        return await self._graph_progression_orchestrator.decide(
            graph_state=graph_state,
            turn_analysis=turn_analysis,
            lesson_state=lesson_state,
        )

    async def _apply_memory_patches(
        self,
        student_id: str,
        objective_id: str,
        objective_memory_patch: Optional[Dict[str, Any]],
        learner_memory_patch: Optional[Dict[str, Any]],
        bundle: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Persist merged learner and objective memory patches."""
        bundle = bundle or {}
        existing_objective = bundle.get("objective_memory") or {}
        existing_learner = bundle.get("learner_memory") or {}

        if objective_memory_patch and objective_id:
            demonstrated_skills = self._merge_unique_capped(
                existing_objective.get("demonstrated_skills", []),
                objective_memory_patch.get(
                    "demonstrated_skills_add",
                    objective_memory_patch.get("demonstrated_skills", []),
                ),
            )
            if "active_gaps_current" in objective_memory_patch:
                active_gaps = self._normalize_memory_list(
                    objective_memory_patch.get("active_gaps_current", []),
                )
            else:
                active_gaps = self._merge_unique(
                    existing_objective.get("active_gaps", []),
                    objective_memory_patch.get("active_gaps", []),
                )
            summary = objective_memory_patch.get("summary") or existing_objective.get(
                "summary", ""
            )
            next_focus = objective_memory_patch.get(
                "next_focus"
            ) or existing_objective.get("next_focus", "")
            await self.student_mcp.upsert_objective_memory(
                student_id,
                objective_id,
                summary=summary,
                demonstrated_skills=demonstrated_skills,
                active_gaps=active_gaps,
                next_focus=next_focus,
            )

        if learner_memory_patch:
            strengths = self._merge_unique_capped(
                existing_learner.get("strengths", []),
                learner_memory_patch.get(
                    "strengths_add",
                    learner_memory_patch.get("strengths", []),
                ),
            )
            if "support_needs_current" in learner_memory_patch:
                support_needs = self._normalize_memory_list(
                    learner_memory_patch.get("support_needs_current", []),
                )
            else:
                support_needs = self._merge_unique(
                    existing_learner.get("support_needs", []),
                    learner_memory_patch.get("support_needs", []),
                )
            if "tendencies_current" in learner_memory_patch:
                tendencies = self._normalize_memory_list(
                    learner_memory_patch.get("tendencies_current", []),
                )
            else:
                tendencies = self._merge_unique(
                    existing_learner.get("tendencies", []),
                    learner_memory_patch.get("tendencies", []),
                )
            successful_strategies = self._merge_unique_capped(
                existing_learner.get("successful_strategies", []),
                learner_memory_patch.get(
                    "successful_strategies_add",
                    learner_memory_patch.get("successful_strategies", []),
                ),
            )
            summary = learner_memory_patch.get("summary") or existing_learner.get(
                "summary", ""
            )
            await self.student_mcp.upsert_learner_memory(
                student_id,
                summary=summary,
                strengths=strengths,
                support_needs=support_needs,
                tendencies=tendencies,
                successful_strategies=successful_strategies,
            )

    def _preview_objective_memory_state(
        self,
        existing_objective: Optional[Dict[str, Any]],
        objective_memory_patch: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        existing_objective = existing_objective or {}
        objective_memory_patch = objective_memory_patch or {}

        demonstrated_skills = self._merge_unique_capped(
            existing_objective.get("demonstrated_skills", []),
            objective_memory_patch.get(
                "demonstrated_skills_add",
                objective_memory_patch.get("demonstrated_skills", []),
            ),
        )
        if "active_gaps_current" in objective_memory_patch:
            active_gaps = self._normalize_memory_list(
                objective_memory_patch.get("active_gaps_current", []),
            )
        else:
            active_gaps = self._merge_unique(
                existing_objective.get("active_gaps", []),
                objective_memory_patch.get("active_gaps", []),
            )

        return {
            "summary": (
                objective_memory_patch.get("summary")
                or existing_objective.get("summary", "")
            ),
            "demonstrated_skills": demonstrated_skills,
            "active_gaps": active_gaps,
            "next_focus": (
                objective_memory_patch.get("next_focus")
                or existing_objective.get("next_focus", "")
            ),
        }

    async def _apply_misconception_events(
        self,
        student_id: str,
        session_id: str,
        objective_id: str,
        events: Optional[List[Dict[str, Any]]],
    ) -> Optional[Dict[str, Any]]:
        """Apply misconception state changes to runtime cache and durable log."""
        events = events or []
        if not events:
            return self._session_cache.get_misconception_state(session_id)

        existing_state = self._session_cache.get_misconception_state(session_id) or {}
        active_lookup = {
            item.get("key"): item
            for item in (existing_state.get("active_misconceptions", []) or [])
            if isinstance(item, dict) and item.get("key")
        }

        for event in events:
            if not isinstance(event, dict):
                continue
            action = str(event.get("action", "") or "").strip().lower()
            key = str(event.get("key", "") or "").strip()
            text = str(event.get("text", "") or "").strip()

            if action == "log":
                # Only create one durable record per live misconception key.
                if key and key in active_lookup:
                    continue
                if text:
                    await self.student_mcp.log_misconception(
                        student_id,
                        objective_id,
                        text,
                    )
            elif action == "resolve_candidate":
                resolve_targets: List[str] = []
                if key and key in active_lookup:
                    tracked_text = str(active_lookup[key].get("text", "") or "").strip()
                    if tracked_text:
                        resolve_targets.append(tracked_text)
                if text and text not in resolve_targets:
                    resolve_targets.append(text)
                for resolve_text in resolve_targets:
                    await self.student_mcp.resolve_misconception(
                        student_id,
                        objective_id,
                        resolve_text,
                    )

        updated_state = self._session_cache.apply_misconception_events(
            session_id,
            events,
        )
        return updated_state

    async def _apply_turn_analysis_updates(
        self,
        student_id: str,
        session_id: str,
        objective_id: str,
        objective_text: str,
        current_stage: str,
        analysis: Dict[str, Any],
        bundle: Optional[Dict[str, Any]],
        ws_send,
    ) -> Dict[str, Any]:
        """Apply deterministic state changes from the structured turn analyzer."""
        result = {"stage": current_stage, "stage_advanced": False}
        canonical_analysis = normalize_analyzer_output(
            analysis,
            current_stage=current_stage,
        )
        tutor_handoff = canonical_tutor_handoff(canonical_analysis)
        preview_misconception_state = self._session_cache.preview_misconception_state(
            session_id,
            self._coerce_misconception_events(
                canonical_analysis,
                default_priority=(
                    "must_address_now"
                    if str(tutor_handoff.get("move", "") or "").strip().lower()
                    == "repair"
                    else "normal"
                ),
            ),
        )
        preview_pacing_state = self._session_cache.preview_pacing_state(
            session_id,
            runtime_pacing_signal(canonical_analysis),
        )
        preview_objective_memory = self._preview_objective_memory_state(
            (bundle or {}).get("objective_memory") or {},
            runtime_objective_memory_patch(canonical_analysis),
        )
        canonical_analysis = self._enforce_turn_response_controls(
            current_stage=current_stage,
            analysis=canonical_analysis,
            lesson_state=self._session_cache.get_lesson_state(session_id),
            pacing_state=preview_pacing_state,
            misconception_state=preview_misconception_state,
        )
        tutor_handoff = canonical_tutor_handoff(canonical_analysis)
        result["analysis"] = copy.deepcopy(canonical_analysis)

        await self.student_mcp.increment_turn_count(session_id)
        misconception_events = self._coerce_misconception_events(
            canonical_analysis,
            default_priority=(
                "must_address_now"
                if str(tutor_handoff.get("move", "") or "").strip().lower() == "repair"
                else "normal"
            ),
        )
        await self._apply_misconception_events(
            student_id=student_id,
            session_id=session_id,
            objective_id=objective_id,
            events=misconception_events,
        )

        lesson_state_before = self._session_cache.get_lesson_state(session_id)
        lesson_patch = runtime_lesson_state_patch(canonical_analysis)
        patched_lesson_state = self._session_cache.apply_lesson_state_patch(
            session_id,
            lesson_patch,
        )
        recomputed_lesson_state = self._session_cache.recompute_lesson_state(
            session_id,
            objective_memory=preview_objective_memory,
            misconception_state=self._session_cache.get_misconception_state(session_id),
        )
        lesson_state_after = self._session_cache.get_lesson_state(session_id)
        result["state_commit"] = {
            "lesson_state_patch": copy.deepcopy(lesson_patch or {}),
            "lesson_state_before": copy.deepcopy(lesson_state_before or {}),
            "lesson_state_after_patch": copy.deepcopy(patched_lesson_state or {}),
            "lesson_state_after_recompute": copy.deepcopy(
                recomputed_lesson_state or {}
            ),
            "lesson_state_after": copy.deepcopy(lesson_state_after or {}),
            "commit_status": (
                "applied" if lesson_state_after is not None else "missing_lesson_state"
            ),
        }
        self._session_cache.apply_pacing_signal(
            session_id,
            runtime_pacing_signal(canonical_analysis),
        )
        await self._persist_session_cache(session_id)

        await self._apply_memory_patches(
            student_id,
            objective_id,
            runtime_objective_memory_patch(canonical_analysis),
            runtime_learner_memory_patch(canonical_analysis),
            bundle=bundle,
        )

        mastery_signal = canonical_analysis.get("mastery_signal") or {}
        mastery_level = mastery_signal.get("level", "")
        if mastery_signal.get("update") and mastery_level in (
            "not_attempted",
            "misconception",
            "in_progress",
        ):
            mastery_result = await self.student_mcp.apply_mastery_judgment(
                student_id,
                objective_id,
                mastery_level,
                evidence_summary=canonical_analysis.get("memory_patch", {}).get(
                    "objective_summary",
                    "",
                ),
                confidence=0.0,
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

        progression = canonical_progression(canonical_analysis)
        stage_action = progression.get("stage_action", "stay")
        target_stage = progression.get("target_stage", current_stage)
        stage_reason = canonical_analysis.get("consistency_check", {}).get(
            "conflict"
        ) or progression.get("progression_blocker", "")

        # Guardrail: block premature assessment if concept coverage is too low.
        # The turn analyzer may recommend assessment after a strong answer on
        # one concept, but if the teaching plan still has uncovered knowledge
        # concepts, the student hasn't been taught enough material yet.
        if stage_action == "advance" and target_stage in (
            "mini_assessment",
            "final_assessment",
        ):
            lesson_state = self._session_cache.get_lesson_state(session_id)
            concepts = (lesson_state or {}).get("concepts", [])
            if concepts:
                covered = sum(1 for c in concepts if c.get("status") == "covered")
                ratio = covered / len(concepts)
                if ratio < 0.6:
                    logger.info(
                        "Assessment guardrail: denied %s → %s "
                        "(coverage %d/%d = %.0f%%, threshold 60%%)",
                        current_stage,
                        target_stage,
                        covered,
                        len(concepts),
                        ratio * 100,
                    )
                    await ws_send(
                        {
                            "type": "stage",
                            "stage": "analyzing",
                            "detail": (
                                f"Continuing exploration "
                                f"({covered}/{len(concepts)} concepts covered)"
                            ),
                        }
                    )
                    # Override: stay in current stage
                    stage_action = "stay"
                    target_stage = current_stage

        if (
            stage_action in ("advance", "regress")
            and target_stage
            and target_stage != current_stage
        ):
            stage_result = await self.student_mcp.update_session_state(
                session_id,
                stage=target_stage,
                stage_summary=stage_reason,
            )
            if isinstance(stage_result, dict) and not stage_result.get("denied"):
                if target_stage == "mini_assessment":
                    await self.student_mcp.update_session_state(
                        session_id,
                        assessment_progress='{"asked": 0, "correct": 0}',
                    )
                await ws_send(
                    {
                        "type": "stage_update",
                        "stage": target_stage,
                        "objective": objective_text or objective_id,
                        "summary": stage_reason,
                    }
                )
                result.update(stage=target_stage, stage_advanced=True)
        return result

    async def _advance_to_next_objective(
        self,
        student_id: str,
        session_id: str,
        ws_send,
    ) -> Dict[str, Any]:
        """Move from transition to the next recommended objective."""
        next_obj = await self.student_mcp.get_recommended_next_objective(student_id)
        if not next_obj:
            return {"advanced": False}

        new_objective_id = next_obj.get("objective_id", "")
        new_objective_text = next_obj.get("objective_text", "")
        await self.student_mcp.update_session_state(
            session_id,
            stage="introduction",
            active_objective_id=new_objective_id,
            turns=0,
        )
        self._session_cache.invalidate(session_id)
        await self._clear_persisted_session_cache(session_id)
        await ws_send(
            {
                "type": "stage_update",
                "stage": "introduction",
                "objective": new_objective_text,
                "summary": f"Starting new objective: {new_objective_text}",
            }
        )
        return {
            "advanced": True,
            "stage": "introduction",
            "objective_id": new_objective_id,
            "objective_text": new_objective_text,
        }

    async def _progressive_send(self, text: str, ws_send):
        """
        Send text to the client progressively in small word-chunks.
        Fallback for non-streaming code paths (e.g. POST endpoint).
        """
        words = text.split(" ")
        for i, word in enumerate(words):
            chunk = word if i == 0 else " " + word
            await ws_send({"type": "token", "content": chunk})
            await asyncio.sleep(0.03)

    async def _stream_response(self, messages: List[Dict], ws_send) -> str:
        """
        Send tutor responses over the websocket with local drip-feed.

        Azure APIM buffers SSE responses before forwarding, so the app does not
        gain true token streaming from Azure. Using the non-streaming chat API
        removes the unstable long-lived SSE transport while preserving the same
        user-facing progressive render in the browser.
        """
        result = await asyncio.to_thread(
            self.client.chat,
            messages,
            0.7,
            GUIDED_TUTOR_RESPONSE_MAX_TOKENS,
            reasoning_effort=GUIDED_TUTOR_RESPONSE_REASONING_EFFORT,
        )
        await ws_send({"type": "stream_start"})
        await self._progressive_send(result, ws_send)
        logger.info(f"Sent non-streamed tutor response ({len(result)} chars)")
        return result

    # ==================================================================
    # Instance B: Guided Learning Session
    # ==================================================================

    async def conduct_guided_session_streaming(
        self,
        student_id: str,
        student_response: str,
        session_id: str,
        ws_send,
    ) -> Dict[str, Any]:
        """Instance B: tutor pass + structured reflection pass."""
        if not self.student_mcp:
            await ws_send({"type": "error", "message": "Student MCP not available"})
            return {}

        history = self.get_conversation_history(student_id)
        self.append_to_conversation(student_id, "user", student_response)

        try:
            session_state = await self.student_mcp.get_active_session(student_id)
            current_stage = (session_state or {}).get("current_stage", "")
            if not session_state or not current_stage or current_stage == "onboarding":
                # Pre-objective state: re-emit the picker and bail.
                logger.info(
                    "Guided session message arrived before objective was chosen "
                    "(student_id=%s session_id=%s); re-sending picker.",
                    student_id,
                    session_id,
                )
                await ws_send(self.get_objective_picker_payload())
                return {"stage": "selecting_objective"}

            objective_id = session_state.get("active_objective_id", "")
            objective_text = self.resolve_objective_text(objective_id)
            if not objective_text and objective_id:
                try:
                    obj = await asyncio.to_thread(
                        self._fetch_objective_by_id, objective_id
                    )
                    if obj:
                        objective_text = obj.get("text", "")
                except Exception as e:
                    logger.warning(
                        f"Failed to fetch objective text for {objective_id}: {e}"
                    )

            await self._session_state_repository.restore(session_id, objective_id)
            turn_result = await self._guided_turn_orchestrator.run_guided_turn(
                student_id=student_id,
                student_response=student_response,
                session_id=session_id,
                session_state=session_state,
                objective_id=objective_id,
                objective_text=objective_text,
                history=history,
                ws_send=ws_send,
            )

            cached = turn_result.metadata.pop("cached_entry", None)
            if cached and cached.get("rag_chunks"):
                try:
                    from ..eval.repository import EvalRepository

                    eval_repo = EvalRepository(db=self.db)
                    eval_repo.capture_rag_sample(
                        query=student_response,
                        retrieved_contexts=[
                            c.get("content", "") for c in cached["rag_chunks"]
                        ],
                        response=turn_result.final_text,
                        student_id=student_id,
                        session_id=session_id,
                        intent="guided",
                        instance="b",
                    )
                except Exception as e:
                    logger.warning(f"RAG capture failed (non-critical): {e}")

            await ws_send({"type": "stream_end", "metadata": turn_result.metadata})
            return turn_result.metadata

        except TeachingPlanGenerationError as e:
            logger.error(
                "Teaching plan generation failed during guided session for session=%s: %s",
                session_id,
                e,
                exc_info=True,
            )
            await ws_send(
                {
                    "type": "error",
                    "message": (
                        "Teaching plan generation failed. Guided tutoring "
                        "stopped before continuing without a validated plan."
                    ),
                }
            )
            return {}
        except ClientConnectionClosedError:
            logger.info(
                "Guided client disconnected during session processing "
                "(student_id=%s session_id=%s)",
                student_id,
                session_id,
            )
            return {}
        except Exception as e:
            logger.error(f"Guided session failed: {e}", exc_info=True)
            await ws_send({"type": "error", "message": str(e)})
            return {}

    # ------------------------------------------------------------------
    # First teaching turn (no synthetic student message)
    # ------------------------------------------------------------------

    async def _start_first_teaching_turn(
        self,
        student_id: str,
        session_id: str,
        objective_id: str,
        objective_text: str,
        ws_send,
    ) -> Dict[str, Any]:
        if not self.student_mcp:
            await ws_send({"type": "error", "message": "Student MCP not available"})
            return {}

        try:
            turn_result = (
                await self._guided_turn_orchestrator.start_first_teaching_turn(
                    student_id=student_id,
                    session_id=session_id,
                    objective_id=objective_id,
                    objective_text=objective_text,
                    ws_send=ws_send,
                )
            )
            await ws_send({"type": "stream_end", "metadata": turn_result.metadata})
            return turn_result.metadata
        except TeachingPlanGenerationError as e:
            logger.error(
                "First-turn teaching plan generation failed for objective=%s: %s",
                objective_id,
                e,
                exc_info=True,
            )
            await ws_send(
                {
                    "type": "error",
                    "message": (
                        "Teaching plan generation failed. Guided tutoring "
                        "stopped before the first lesson turn."
                    ),
                }
            )
            return {}
        except Exception as e:
            logger.error(
                "First-turn teaching content pipeline failed: %s",
                e,
                exc_info=True,
            )
            await ws_send(
                {
                    "type": "error",
                    "message": "Teaching content pipeline failed before first turn.",
                }
            )
            return {}

    # ------------------------------------------------------------------
    # Objective picker (Instance B session start)
    # ------------------------------------------------------------------

    DEMO_SAVED_GRAPH_OBJECTIVE_ID = "demo:non-text-alt"
    _SAVED_DEMO_ARTIFACT_PATH = (
        "results/graph_retrieval_demo_20260427_201649/"
        "0157_artifact_final_graph_content.json"
    )
    _SAVED_DEMO_ARTIFACT_CACHE: Optional[Dict[str, Any]] = None

    GUIDED_OBJECTIVE_OPTIONS: List[Dict[str, Any]] = [
        {
            "id": "I.A.2",
            "label": "Intro to WCAG (POUR + structure)",
            "description": (
                "The big picture: the four POUR principles, guidelines, "
                "success criteria, and conformance levels."
            ),
            "graph_source": "live",
            "graph_available": False,
            "objective_text": (
                "Explain the structure of WCAG 2.2 by identifying the four "
                "principles (POUR), guidelines, and success criteria levels "
                "(A, AA, AAA)."
            ),
        },
        {
            "id": "I.B.4",
            "label": "Semantic HTML controls vs generic elements",
            "description": (
                "Why a real <button> behaves differently from a styled "
                "<div> for keyboard and assistive-tech users."
            ),
            "graph_source": "live",
            "graph_available": False,
            "objective_text": (
                "Distinguish between semantic HTML controls (e.g., "
                "`<button>`, `<a>`) and generic elements (e.g., `<div>`) "
                "in terms of built-in accessibility."
            ),
        },
        {
            "id": DEMO_SAVED_GRAPH_OBJECTIVE_ID,
            "label": "Evaluating text alternatives for non-text content",
            "description": (
                "Decide when an image, chart, or media item needs a text "
                "alternative — and judge whether the alternative is any good."
            ),
            "graph_source": "saved",
            "graph_available": True,
            "objective_text": (
                "Evaluate web content to determine whether text alternatives "
                "are provided for images, video, and other non-text content."
            ),
        },
    ]

    DEFAULT_NEW_STUDENT_PROFILE: Dict[str, str] = {
        "technical_level": "beginner",
        "a11y_exposure": "none",
        "role_context": "student",
        "learning_goal": "personal_interest",
    }

    @classmethod
    def _objective_picker_payload(cls) -> Dict[str, Any]:
        return {
            "type": "objective_picker",
            "options": [
                {
                    key: value
                    for key, value in option.items()
                    if key != "objective_text"
                }
                for option in cls.GUIDED_OBJECTIVE_OPTIONS
            ],
        }

    @classmethod
    def get_objective_picker_payload(cls) -> Dict[str, Any]:
        """Public accessor used by the WS handler to send the picker."""
        return cls._objective_picker_payload()

    @classmethod
    def _objective_option(cls, objective_id: str) -> Optional[Dict[str, Any]]:
        for option in cls.GUIDED_OBJECTIVE_OPTIONS:
            if option["id"] == objective_id:
                return option
        return None

    @classmethod
    def _load_saved_demo_artifact(cls) -> Dict[str, Any]:
        """Load and cache the saved teaching-graph artifact from disk."""
        if cls._SAVED_DEMO_ARTIFACT_CACHE is not None:
            return cls._SAVED_DEMO_ARTIFACT_CACHE
        path = os.path.join(os.getcwd(), cls._SAVED_DEMO_ARTIFACT_PATH)
        if not os.path.exists(path):
            raise TeachingGraphGenerationError(
                f"Saved demo artifact not found at {path}. "
                "Cannot seed the non-text-content objective."
            )
        with open(path, "r", encoding="utf-8") as f:
            cls._SAVED_DEMO_ARTIFACT_CACHE = json.load(f)
        return cls._SAVED_DEMO_ARTIFACT_CACHE

    async def _run_pipeline_for_graph(
        self,
        *,
        objective_text: str,
        graph_artifact,
        ws_send,
    ):
        """Run retrieval + content synthesis + validation for a pre-built graph.

        Emits staged WS events between phases so the frontend can render the
        graph, retrieval trace, and teaching content as each completes.
        Returns the assembled :class:`TeachingGraphContentArtifact`.
        """
        from .artifacts import TeachingGraphContentArtifact

        await ws_send(
            {
                "type": "stage",
                "stage": "searching",
                "detail": "Running retrieval over the graph...",
            }
        )
        node_evidence_artifact = await self._build_graph_node_evidence(
            objective_text=objective_text,
            graph=graph_artifact,
        )
        await ws_send(
            {
                "type": "node_evidence",
                "node_evidence": node_evidence_artifact.to_dict(),
            }
        )

        await ws_send(
            {
                "type": "stage",
                "stage": "composing",
                "detail": "Synthesizing teaching content from retrieved evidence...",
            }
        )
        node_content_artifact = await self._build_graph_node_content(
            objective_text=objective_text,
            graph=graph_artifact,
            node_evidence=node_evidence_artifact,
        )
        edge_integration_artifact = await self._build_graph_edge_integration(
            objective_text=objective_text,
            graph=graph_artifact,
            node_evidence=node_evidence_artifact,
            node_content=node_content_artifact,
        )
        await ws_send(
            {
                "type": "teaching_graph_details",
                "node_content": node_content_artifact.to_dict(),
                "edge_integration": edge_integration_artifact.to_dict(),
            }
        )

        validation_artifact = await self._validate_teaching_graph_content(
            objective_text=objective_text,
            graph=graph_artifact,
            node_evidence=node_evidence_artifact,
            node_content=node_content_artifact,
            edge_integration=edge_integration_artifact,
        )
        evidence_cards = GraphGroundingProjector.build_evidence_cards(
            objective_text=objective_text,
            node_evidence=node_evidence_artifact,
        )
        claim_ledger = GraphGroundingProjector.build_claim_ledger(
            objective_text=objective_text,
            node_evidence=node_evidence_artifact,
            node_content=node_content_artifact,
            edge_integration=edge_integration_artifact,
            evidence_cards=evidence_cards,
        )
        validation_artifact = GraphGroundingProjector.deterministic_validate(
            validation=validation_artifact,
            claim_ledger=claim_ledger,
            evidence_cards=evidence_cards,
        )
        if validation_artifact.overall_status == "fail":
            try:
                failed_claims = [
                    c.to_dict()
                    for c in validation_artifact.claim_checks
                    if c.status == "fail"
                ]
                node_issues = [
                    n.to_dict()
                    for n in validation_artifact.node_checks
                    if n.status == "fail"
                ]
            except Exception:
                failed_claims, node_issues = [], []
            logger.error(
                "Graph-grounded content validation hard-failed: failed_claims=%s "
                "node_issues=%s",
                failed_claims,
                node_issues,
            )
            raise TeachingGraphGenerationError(
                "Graph-grounded content failed validation: fail"
            )
        if validation_artifact.overall_status != "pass":
            try:
                node_revisions = [
                    {"node_id": n.node_id, "status": n.status, "notes": list(n.notes)}
                    for n in validation_artifact.node_checks
                    if n.status != "pass"
                ]
                edge_revisions = [
                    {
                        "from": e.from_node,
                        "to": e.to_node,
                        "status": e.status,
                        "notes": list(e.notes),
                    }
                    for e in validation_artifact.edge_checks
                    if e.status != "pass"
                ]
                integration_revision = (
                    validation_artifact.integration_check.to_dict()
                    if validation_artifact.integration_check.status != "pass"
                    else None
                )
            except Exception:
                node_revisions, edge_revisions, integration_revision = [], [], None
            logger.warning(
                "Graph-grounded content returned validator status=%s; proceeding. "
                "node_revisions=%s edge_revisions=%s integration_revision=%s",
                validation_artifact.overall_status,
                node_revisions,
                edge_revisions,
                integration_revision,
            )
        tutor_facing_content = GraphGroundingProjector.build_tutor_facing_content(
            objective_text=objective_text,
            graph=graph_artifact,
            node_content=node_content_artifact,
            edge_integration=edge_integration_artifact,
            evidence_cards=evidence_cards,
            claim_ledger=claim_ledger,
            validation=validation_artifact,
        )
        return TeachingGraphContentArtifact(
            objective_text=objective_text,
            graph=graph_artifact,
            node_evidence=node_evidence_artifact,
            node_content=node_content_artifact,
            edge_integration=edge_integration_artifact,
            validation=validation_artifact,
            evidence_cards=evidence_cards,
            claim_ledger=claim_ledger,
            tutor_facing_content=tutor_facing_content,
        )

    async def _seed_session_from_saved_artifact(
        self,
        *,
        session_id: str,
        objective_id: str,
        objective_text: str,
        ws_send,
    ) -> None:
        """Seed the session from the saved graph; run retrieval + content live.

        Only the *graph* is taken from the saved artifact — that piece is
        treated as pre-built. The retrieval pipeline (NodeEvidenceRetriever,
        synthesizers, validator, projector) all run live so the user can watch
        the retrieval process and see freshly grounded teaching content.
        """
        from .artifacts import TeachingGraphArtifact

        saved_artifact = self._load_saved_demo_artifact()
        saved_graph = saved_artifact.get("graph") or {}
        if not saved_graph:
            raise TeachingGraphGenerationError(
                "Saved demo artifact is missing the graph payload."
            )

        await ws_send(
            {
                "type": "stage",
                "stage": "composing",
                "detail": "Loading pre-built teaching graph...",
            }
        )
        await ws_send({"type": "teaching_plan_generating"})
        display_plan = json.dumps(saved_graph, indent=2)
        await ws_send(
            {
                "type": "teaching_plan",
                "plan": saved_graph,
                "display_plan": display_plan,
            }
        )

        graph_artifact = TeachingGraphArtifact.from_dict(saved_graph)
        artifact = await self._run_pipeline_for_graph(
            objective_text=objective_text,
            graph_artifact=graph_artifact,
            ws_send=ws_send,
        )
        teaching_content = GraphGroundingProjector.render_tutor_content(
            artifact.tutor_facing_content
        )

        await ws_send({"type": "teaching_content_generating"})
        await ws_send(
            {
                "type": "teaching_content",
                "content": teaching_content,
                "display_content": teaching_content,
            }
        )

        extracted_concepts = [
            {"id": node["id"], "label": node.get("label", node["id"])}
            for node in saved_graph.get("nodes", [])
        ]
        self._session_state_repository.store_pipeline_result(
            session_id=session_id,
            objective_id=objective_id,
            objective_text=objective_text,
            teaching_content=teaching_content,
            retrieval_bundle=artifact.to_dict(),
            teaching_plan=saved_graph,
            extracted_concepts=extracted_concepts,
        )
        await self._session_state_repository.persist(session_id)

    async def ensure_default_profile(self, student_id: str) -> Dict[str, Any]:
        """Create a baseline profile for a brand-new student if missing."""
        existing = await self.student_mcp.get_profile(student_id)
        if existing:
            return existing
        await self.student_mcp.create_profile(
            student_id=student_id,
            **self.DEFAULT_NEW_STUDENT_PROFILE,
        )
        return await self.student_mcp.get_profile(student_id) or {}

    def resolve_objective_text(self, objective_id: str) -> str:
        """Resolve an objective id to its display text.

        Tries the picker option table first (covers synthetic demo ids and the
        curriculum codes I.A.2 / I.B.4), then falls back to the live DB.
        """
        option = self._objective_option(objective_id)
        if option:
            return option["objective_text"]
        try:
            obj = self._fetch_objective_by_id(objective_id)
            if obj and obj.get("text"):
                return obj["text"]
        except Exception as exc:
            logger.warning(
                "Failed to resolve objective text for %s: %s",
                objective_id,
                exc,
            )
        return objective_id

    async def start_guided_session_with_objective(
        self,
        *,
        student_id: str,
        session_id: str,
        objective_id: str,
        ws_send,
    ) -> Dict[str, Any]:
        """Bootstrap a brand-new guided session around the chosen objective.

        Creates a default profile if needed, opens the session at the
        introduction stage, seeds the teaching graph (saved artifact when
        available, otherwise the live build pipeline), and fires the first
        teaching turn.
        """
        if not self.student_mcp:
            await ws_send(
                {"type": "error", "message": "Student MCP not available"}
            )
            return {}

        option = self._objective_option(objective_id)
        if option is None:
            await ws_send(
                {
                    "type": "error",
                    "message": f"Unknown objective: {objective_id}",
                }
            )
            return {}

        objective_text = option["objective_text"]
        await self.ensure_default_profile(student_id)
        await self.student_mcp.update_session_state(
            session_id,
            student_id=student_id,
            stage="introduction",
            active_objective_id=objective_id,
            turns=0,
        )

        await ws_send(
            {
                "type": "stage_update",
                "stage": "introduction",
                "objective": objective_text,
                "summary": "",
            }
        )

        try:
            if option["graph_source"] == "saved":
                await self._seed_session_from_saved_artifact(
                    session_id=session_id,
                    objective_id=objective_id,
                    objective_text=objective_text,
                    ws_send=ws_send,
                )
            await self._start_first_teaching_turn(
                student_id=student_id,
                session_id=session_id,
                objective_id=objective_id,
                objective_text=objective_text,
                ws_send=ws_send,
            )
        except TeachingPlanGenerationError as exc:
            logger.error(
                "Teaching plan generation failed for objective=%s: %s",
                objective_id,
                exc,
                exc_info=True,
            )
            await ws_send(
                {
                    "type": "error",
                    "message": (
                        "Teaching plan generation failed. Please pick another "
                        "objective or retry."
                    ),
                }
            )
            return {}
        except TeachingGraphGenerationError as exc:
            logger.error(
                "Teaching graph generation failed for objective=%s: %s",
                objective_id,
                exc,
                exc_info=True,
            )
            await ws_send(
                {
                    "type": "error",
                    "message": (
                        "Teaching graph generation failed. Please pick another "
                        "objective or retry."
                    ),
                }
            )
            return {}

        return {
            "stage": "introduction",
            "objective_id": objective_id,
            "objective_text": objective_text,
            "graph_source": option["graph_source"],
        }

    # Legacy onboarding constants retained as no-ops so older imports do not
    # KeyError. The picker flow above replaces these entirely.
    _ONBOARDING_QUESTIONS: List[Dict[str, Any]] = []
    _ONBOARDING_PROMPTS: List[str] = []

    def _fetch_objective_by_id(self, objective_id: str) -> Optional[Dict]:
        """Fetch a single learning objective by ID from the main DB."""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, text, blooms_level, priority FROM learning_objective WHERE id = %s",
                    (objective_id,),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def _fetch_objective_by_text(self, objective_text: str) -> Optional[Dict]:
        """Fetch a learning objective by exact text from the main DB."""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, text, blooms_level, priority "
                    "FROM learning_objective WHERE text = %s",
                    (objective_text,),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    # ------------------------------------------------------------------
    # Assessment context (fetch quiz questions for an objective)
    # ------------------------------------------------------------------

    @staticmethod
    def _is_valid_structured_teaching_plan(plan_text: str) -> bool:
        return TeachingPlanWorker.is_valid_structured_plan(plan_text)

    @staticmethod
    def _is_valid_legacy_teaching_plan(plan: Dict[str, Any]) -> bool:
        return TeachingPlanWorker.is_valid_legacy_plan(plan)

    async def _generate_teaching_plan(
        self,
        objective_text: str,
        teaching_content: str = "",
    ):
        artifact = await self._teaching_plan_worker.generate(
            objective_text,
            teaching_content=teaching_content,
        )
        return artifact.plan

    async def _build_teaching_graph(
        self,
        objective_text: str,
        *,
        learner_level: Optional[str] = None,
        prerequisite_assumptions: Optional[str] = None,
    ):
        return await self._teaching_graph_planner_worker.generate(
            objective_text,
            learner_level=learner_level,
            prerequisite_assumptions=prerequisite_assumptions,
        )

    async def _build_graph_node_evidence(
        self,
        *,
        objective_text: str,
        graph,
    ):
        return await self._graph_node_evidence_worker.build_node_evidence(
            objective_text=objective_text,
            graph=graph,
        )

    async def _build_graph_node_content(
        self,
        *,
        objective_text: str,
        graph,
        node_evidence,
    ):
        return await self._graph_node_content_worker.build_node_content(
            objective_text=objective_text,
            graph=graph,
            node_evidence=node_evidence,
        )

    async def _build_graph_edge_integration(
        self,
        *,
        objective_text: str,
        graph,
        node_evidence,
        node_content,
    ):
        return await self._graph_edge_integration_worker.build_edge_integration_content(
            objective_text=objective_text,
            graph=graph,
            node_evidence=node_evidence,
            node_content=node_content,
        )

    async def _validate_teaching_graph_content(
        self,
        *,
        objective_text: str,
        graph,
        node_evidence,
        node_content,
        edge_integration,
    ):
        return await self._graph_validator_worker.validate(
            objective_text=objective_text,
            graph=graph,
            node_evidence=node_evidence,
            node_content=node_content,
            edge_integration=edge_integration,
        )

    async def _build_teaching_graph_content(
        self,
        objective_text: str,
        *,
        learner_level: Optional[str] = None,
        prerequisite_assumptions: Optional[str] = None,
    ):
        return await self._teaching_graph_build_orchestrator.run(
            objective_text=objective_text,
            learner_level=learner_level,
            prerequisite_assumptions=prerequisite_assumptions,
        )

    async def _extract_concept_order(
        self, teaching_plan: str
    ) -> Optional[List[Dict[str, str]]]:
        return await self._concept_extraction_worker.extract(teaching_plan)

    # ------------------------------------------------------------------
    # Graph-grounded teaching content pipeline (Instance B)
    # ------------------------------------------------------------------

    async def _run_teaching_content_pipeline(
        self,
        objective_text: str,
        session_id: str,
        objective_id: str,
        ws_send,
    ) -> tuple:
        await ws_send(
            {
                "type": "stage",
                "stage": "composing",
                "detail": "Building teaching graph...",
            }
        )
        await ws_send({"type": "teaching_plan_generating"})
        graph_artifact = await self._build_teaching_graph(
            objective_text=objective_text,
        )
        teaching_plan = graph_artifact.to_dict()
        display_plan = json.dumps(teaching_plan, indent=2)
        await ws_send(
            {
                "type": "teaching_plan",
                "plan": teaching_plan,
                "display_plan": display_plan,
            }
        )
        artifact = await self._run_pipeline_for_graph(
            objective_text=objective_text,
            graph_artifact=graph_artifact,
            ws_send=ws_send,
        )
        if not artifact.tutor_facing_content:
            raise TeachingGraphGenerationError(
                "Graph-grounded pipeline did not produce tutor-facing content."
            )
        teaching_content = GraphGroundingProjector.render_tutor_content(
            artifact.tutor_facing_content
        )
        await ws_send({"type": "teaching_content_generating"})
        await ws_send(
            {
                "type": "teaching_content",
                "content": teaching_content,
                "display_content": teaching_content,
            }
        )
        extracted_concepts = [
            {"id": node.id, "label": node.label} for node in graph_artifact.nodes
        ]
        return (
            teaching_plan,
            teaching_content,
            artifact.to_dict(),
            extracted_concepts,
        )

    async def _get_assessment_context(self, objective_id: str) -> str:
        """Fetch quiz questions mapped to an objective for assessment generation.

        The LLM uses these as templates to generate rephrased assessment
        questions. Includes answer text and feedback so the LLM can evaluate
        student responses against rubrics.
        """
        if not objective_id:
            return ""

        try:
            # Query questions associated with this objective
            questions = await asyncio.to_thread(
                self._fetch_questions_for_objective, objective_id
            )
            if not questions:
                return ""

            lines = [
                "ASSESSMENT REFERENCE QUESTIONS (use as templates, do NOT reuse verbatim):"
            ]
            for i, q in enumerate(questions[:5], 1):  # max 5 questions
                lines.append(f"\nQ{i}: {q.get('question_text', '')}")
                for a in q.get("answers", []):
                    marker = "✓" if a.get("is_correct") else "✗"
                    lines.append(f"  {marker} {a.get('text', '')}")
                    if a.get("feedback_text"):
                        lines.append(f"    Feedback: {a['feedback_text']}")
            return "\n".join(lines)
        except Exception as e:
            logger.warning(f"Failed to fetch assessment context: {e}")
            return ""

    def _fetch_questions_for_objective(self, objective_id: str) -> List[Dict]:
        """Synchronous DB query for questions mapped to an objective."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT q.id, q.question_text
                FROM question q
                JOIN question_objective_association qoa ON q.id = qoa.question_id
                WHERE qoa.objective_id = %s
                """,
                (objective_id,),
            )
            questions = [dict(row) for row in cursor.fetchall()]

        # Load answers for each question
        for q in questions:
            q["answers"] = self.db.get_answers_for_questions(q["id"])
        return questions

    # ==================================================================
    # End of Instance B methods
    # ==================================================================
    # ==================================================================
