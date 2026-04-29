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
from dataclasses import asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from ...models.tutor import KnowledgeLevel, SessionPhase, StudentProfile
from ..general_chat_service import GeneralChatService
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
# SIMULATED CREWAI AGENTS
# ============================================================================


class SocraticAgent:
    # (This class is unchanged)
    def __init__(self, role: str, goal: str, backstory: str, client: AzureAPIMClient):
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.client = client
        logger.info(f"Initialized {role} agent")

    def execute_task(
        self,
        task_description: str,
        context: str = "",
        history: Optional[List[Dict[str, str]]] = None,
        reasoning_effort: Optional[str] = None,
    ) -> str:
        context_block = ""
        if context:
            context_block = f"""
KNOWLEDGE BASE CUES:
{context}
---
The cues above may contain two sections:
1. QUIZ KNOWLEDGE BASE: Course-specific quiz data, correct answers, misconceptions.
2. WCAG GUIDELINES REFERENCE: Authoritative WCAG 2.2 success criteria, techniques, understanding docs.

When both are present:
- Use the WCAG reference as your primary factual authority.
- Use the quiz data for course-specific misconceptions and expected answers.
- Cite specific WCAG criteria when relevant.
If only one source is present, use it fully.
Expand on the cues with your expertise. Do not just rephrase them.
If the cues mention a correct answer or misconception, teach *why* it is correct or incorrect.
"""
        system_prompt = f"""You are a {self.role}.
        Your goal: {self.goal}
        Background: {self.backstory}
        {context_block}
        Task: {task_description}
        Provide clear, direct and comprehensive responses."""
        messages = [
            {"role": "system", "content": system_prompt},
        ]
        if history:
            messages.extend(history[-4:])
        messages.append({"role": "user", "content": task_description})
        try:
            response = self.client.chat(
                messages, temperature=0.7, reasoning_effort=reasoning_effort
            )
            logger.info(f"{self.role} completed task successfully")
            return response
        except Exception as e:
            logger.error(f"{self.role} task failed: {e}")
            return f"Task processing error in {self.role}: {str(e)}"


class CoordinatorAgent(SocraticAgent):
    def __init__(self, client=AzureAPIMClient) -> None:
        super().__init__(
            role="Socratic Session Coordinator",
            # --- === FIX 1: UPDATE THE GOAL === ---
            goal="Analyze the user's input to determine its primary intent: 'conceptual_question', 'code_analysis_request', or 'off_topic'.",
            backstory="""You are the central "brain" of a tutoring system focused *only* on web accessibility.
            You do not answer the student. Your job is to classify the user's
            input so it can be routed to the correct specialist agent.""",
            # --- === END OF FIX 1 === ---
            client=client,
        )

    def decide_intent(
        self, student_response: str, history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        # --- === FIX 2: UPDATE THE TASK PROMPT === ---
        task_description = f"""
Analyze the following user input in the context of the ongoing conversation. Classify it as one of three intents:

1. 'conceptual_question': For general questions, statements, answers, or follow-up requests about web accessibility concepts. 
   This includes:
   - Direct questions (e.g., "what is alt text?")
   - Follow-up clarifications (e.g., "can you explain more simply?", "give me an example")
   - Requests to change response style (e.g., "answer directly", "be more detailed")
   - Statements or partial answers (e.g., "I think it's for screen readers")

2. 'code_analysis_request': If the user has included a code snippet (HTML, CSS, JS) for review or has asked a question directly about a piece of code.

3. 'off_topic': ONLY if the user is asking about something completely unrelated to web accessibility AND it's not a follow-up to the current discussion (e.g., "what is the capital of France?", "tell me about cooking recipes").

IMPORTANT: If this appears to be a follow-up or continuation of the previous conversation, classify it as 'conceptual_question' even if it doesn't explicitly mention web accessibility.

User Input: "{student_response}"

Respond with ONLY a JSON object in this exact format:
{{"intent": "YOUR_CLASSIFICATION_HERE"}}
"""
        # --- === END OF FIX 2 === ---
        try:
            repsonse_json = self.execute_task(
                task_description, context="", history=history, reasoning_effort="low"
            )
            intent = json.loads(repsonse_json).get("intent", "conceptual_question")

            # Add the new intent to the valid list
            if intent not in [
                "conceptual_question",
                "code_analysis_request",
                "off_topic",
            ]:
                logger.warning(
                    f"CoordinatorAgent returned non-standard intent: {intent}"
                )
                return "conceptual_question"  # Default to this if confused

            logger.info(f"CoordinatorAgent decided intent : {intent}")
            return intent

        except Exception as e:
            logger.error(
                f"CoordinatorAgent failed : {e} , Defaulting to 'conceptual_question'"
            )
            return "conceptual_question"


class CodeAnalyzerAgent(SocraticAgent):
    def __init__(self, client: AzureAPIMClient):
        super().__init__(
            role="Expert Web Accessibility Code Analyst",
            goal="Analyze a snippet of HTML, CSS, or JS and identify potential accessibility issues. Provide your analysis in a structured list.",
            backstory="""You are an expert on WCAG and web accessibility.
            You do not talk to the student. You are a tool that provides technical analysis.
            Your job is to find common errors like missing alt text, non-semantic HTML (e.g., div used as a button), or poor color contrast hints.""",
            client=client,
        )

    def analyze_code_snippet(self, code_snippet: str):
        task_description = f"""
        Analyze the following code snippet for potential accessibility errors.
        List 1-3 potential issues you find. Be concise and return your analysis as a simple string.
        If no errors are found, respond with "No obvious accessibility errors found."
        Code Snippet:
        ```
        {code_snippet}
        ```
        Your Analysis:
        """
        try:
            analysis = self.execute_task(task_description, context="")
            logger.info("CodeAnalyzerAgent completed analysis")
            return analysis
        except Exception as e:
            logger.error(f"CodeAnalyzerAgent fauled : {e}")
            return "Error during code analysis"


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


class HybridCrewAISocraticSystem:
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
        self.instance_a_service = GeneralChatService(
            azure_config=azure_config,
            vector_store_service=vector_store_service,
            wcag_mcp_client=wcag_mcp_client,
            db_manager=self.db,
        )
        self._legacy_instance_a_bootstrapped_sessions: set[str] = set()
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
        self.coordinator_agent = CoordinatorAgent(self.tutor_client)
        self.code_analyzer = CodeAnalyzerAgent(self.reasoning_client)
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
            for item in HybridCrewAISocraticSystem._coerce_misconception_events(
                turn_analysis
            )
            if isinstance(item, dict)
            and HybridCrewAISocraticSystem._is_open_must_repair_event(item)
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
            if HybridCrewAISocraticSystem._is_procedural_full_sequence_repair(item):
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
            tutor[
                "one_turn_goal"
            ] = "Learner already shows causal footing; use a fresh case instead of another same-level restatement check."

        if (
            not must_repair_now
            and teaching_move == "clarify"
            and guarded["student_turn"].get("answer_first")
        ):
            tutor[
                "one_turn_goal"
            ] = f"{tutor.get('one_turn_goal', '')} If the explanation fully resolves the question, a follow-up check is optional.".strip()

        if not must_repair_now and repeated_active_sequence and supports_repair_exit:
            tutor["move"] = "clarify"
            tutor["support_level"] = "light"
            tutor[
                "one_turn_goal"
            ] = "Repeated full-sequence repair now has enough evidence for a fresh transfer check."

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
            and HybridCrewAISocraticSystem._is_open_must_repair_event(item)
            for item in misconception_events
        )
        requires_procedural_full_sequence_repair = any(
            isinstance(item, dict)
            and HybridCrewAISocraticSystem._is_open_must_repair_event(item)
            and HybridCrewAISocraticSystem._is_procedural_full_sequence_repair(item)
            for item in misconception_events
        )
        requires_conceptual_sequence_completion = any(
            isinstance(item, dict)
            and HybridCrewAISocraticSystem._is_open_must_repair_event(item)
            and not HybridCrewAISocraticSystem._is_procedural_full_sequence_repair(item)
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
            HybridCrewAISocraticSystem._has_repeated_full_sequence_signal(
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

    # ------------------------------------------------------------------
    # Legacy Instance A quarantine
    # ------------------------------------------------------------------

    async def _ensure_instance_a_legacy_session(
        self, student_id: str
    ) -> Dict[str, Any]:
        session = await self.instance_a_service.ensure_session(student_id)
        session_id = session["session_id"]
        if session_id not in self._legacy_instance_a_bootstrapped_sessions:
            session = await self.instance_a_service.start_new_session(session_id)
            self._legacy_instance_a_bootstrapped_sessions.add(session_id)
        return session

    def _load_legacy_student_profile(self, student_id: str) -> Optional[Any]:
        load_profile = getattr(self.db, "load_student_profile", None)
        if not callable(load_profile):
            return None
        profile = load_profile(student_id)
        if profile is None:
            raise ValueError(f"Student {student_id} not found")
        return profile

    def _serialize_legacy_student_profile(
        self, profile: Optional[Any], student_id: str
    ) -> Dict[str, Any]:
        if profile is None:
            return {"id": student_id}
        try:
            return asdict(profile)
        except TypeError:
            if isinstance(profile, dict):
                return dict(profile)
            return {"id": student_id}

    def _build_legacy_instance_a_response_messages(
        self,
        student_response: str,
        context: str,
        history: Optional[List[Dict[str, str]]] = None,
        student_context: str = "",
    ) -> List[Dict]:
        """Build the messages list for response generation.

        Uses the research-backed Socratic prompt (Instance A) which includes:
        - 6 cognitive state detection (SocraticLM)
        - 4 response modes (SocraticMATH)
        - Termination rules and anti-patterns
        - 4 few-shot examples
        """
        from .prompts import build_instance_a_prompt

        system_prompt = build_instance_a_prompt(
            knowledge_context=context,
            student_context=student_context,
        )

        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history[-6:])
        messages.append({"role": "user", "content": student_response})
        return messages

    def _generate_legacy_instance_a_response(
        self,
        student_response: str,
        context: str,
        history: Optional[List[Dict[str, str]]] = None,
        student_context: str = "",
    ) -> str:
        """
        Single LLM call: context + history + student query → tutor response.
        Used by the non-streaming POST endpoint.
        """
        messages = self._build_legacy_instance_a_response_messages(
            student_response, context, history, student_context=student_context
        )
        try:
            return self.client.chat(messages, temperature=0.7, max_tokens=1000)
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return "I apologize, but I'm having trouble right now. Could you rephrase your question?"

    async def conduct_socratic_session(
        self, student_id: str, student_response: str
    ) -> Dict[str, Any]:
        profile = self._load_legacy_student_profile(student_id)
        session = await self._ensure_instance_a_legacy_session(student_id)
        logger.warning(
            "Legacy Instance A entrypoint conduct_socratic_session() is delegating to GeneralChatService."
        )

        try:
            result = await self.instance_a_service.handle_message(
                session_id=session["session_id"],
                user_message=student_response,
            )
            return {
                "tutor_response": result.get("response", ""),
                "student_profile": self._serialize_legacy_student_profile(
                    profile,
                    student_id,
                ),
                "session_metadata": result.get("session_metadata", {}),
                "status": "success",
            }
        except Exception as e:
            logger.error(f"Triage Session execution failed : {e}", exc_info=True)
            return {
                "tutor_response": "I apologize, but I'm having a small issue. Could you rephrase that?",
                "error": str(e),
                "fallback": True,
                "status": "error",
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

    async def conduct_socratic_session_streaming(
        self, student_id: str, student_response: str, ws_send
    ):
        """
        Legacy compatibility wrapper for Instance A streaming calls.
        Active Instance A behavior now lives in GeneralChatService.
        """
        self._load_legacy_student_profile(student_id)
        session = await self._ensure_instance_a_legacy_session(student_id)
        logger.warning(
            "Legacy Instance A entrypoint conduct_socratic_session_streaming() is delegating to GeneralChatService."
        )

        try:
            return await self.instance_a_service.handle_message_streaming(
                session_id=session["session_id"],
                user_message=student_response,
                ws_send=ws_send,
            )
        except ClientConnectionClosedError:
            logger.info(
                "Instance A client disconnected during streaming (session_id=%s)",
                session["session_id"],
            )
            return {}
        except Exception as e:
            logger.error(f"Streaming session failed: {e}", exc_info=True)
            await ws_send({"type": "error", "message": str(e)})
            return {}

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
            current_stage = (session_state or {}).get("current_stage", "onboarding")
            if not session_state or current_stage == "onboarding":
                return await self._handle_onboarding(
                    student_id,
                    student_response,
                    session_id,
                    ws_send,
                    history,
                )

            objective_id = session_state.get("active_objective_id", "")
            objective_text = ""
            if objective_id:
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
    # Onboarding handler (Instance B — first 2-3 turns)
    # ------------------------------------------------------------------

    # Structured onboarding questions — sent as clickable forms, not free text
    _ONBOARDING_QUESTIONS = [
        {
            "question": "What's your technical background?",
            "description": "This helps us tailor examples and vocabulary to your role.",
            "field": "role_context",
            "options": [
                {"label": "Developer", "value": "developer"},
                {"label": "Designer", "value": "designer"},
                {"label": "Content Author", "value": "content_author"},
                {"label": "QA Tester", "value": "qa_tester"},
                {"label": "Student", "value": "student"},
                {"label": "Manager", "value": "manager"},
            ],
            "allow_other": True,
        },
        {
            "question": "How much experience do you have with web accessibility?",
            "description": "We'll match the starting topic to your level.",
            "field": "a11y_exposure",
            "options": [
                {
                    "label": "None",
                    "value": "none",
                    "description": "I'm just getting started",
                },
                {
                    "label": "Some awareness",
                    "value": "awareness",
                    "description": "I've heard of WCAG but haven't applied it",
                },
                {
                    "label": "Working knowledge",
                    "value": "working_knowledge",
                    "description": "I've worked on accessible websites",
                },
                {
                    "label": "Professional",
                    "value": "professional",
                    "description": "Deep a11y expertise or certification",
                },
            ],
            "allow_other": False,
        },
        {
            "question": "What's driving your interest in accessibility?",
            "description": "Last question — helps us focus on what matters to you.",
            "field": "learning_goal",
            "options": [
                {"label": "Certification prep", "value": "certification"},
                {"label": "Job requirement", "value": "job_requirement"},
                {"label": "Personal interest", "value": "personal_interest"},
            ],
            "allow_other": True,
        },
    ]

    # Legacy text prompts (kept for conversation history readability)
    _ONBOARDING_PROMPTS = [
        "Welcome! What's your technical background?",
        "How much experience do you have with web accessibility?",
        "What's driving your interest in accessibility?",
    ]

    async def _handle_onboarding(
        self,
        student_id: str,
        student_response: str,
        session_id: str,
        ws_send,
        history: List[Dict],
    ) -> Dict[str, Any]:
        """Handle onboarding (first 2-3 turns before guided learning begins).

        Gathers technical background, a11y experience, and learning goals
        through a structured conversational flow. After the final turn,
        creates the student profile and selects the first objective.
        """
        # Count how many assistant messages we've sent (= onboarding turn)
        assistant_turns = sum(1 for m in history if m.get("role") == "assistant")
        logger.info(
            f"[ONBOARDING] student={student_id} assistant_turns={assistant_turns} "
            f"history_len={len(history)} student_said='{student_response[:80]}'"
        )

        if assistant_turns < 3:
            # Send the next structured onboarding question
            prompt_idx = min(assistant_turns, 2)
            question_data = self._ONBOARDING_QUESTIONS[prompt_idx]
            prompt_text = self._ONBOARDING_PROMPTS[prompt_idx]
            logger.info(
                f"[ONBOARDING] Sending question #{prompt_idx + 1} of 3: {question_data['field']}"
            )

            # Send as structured form question
            await ws_send(
                {
                    "type": "onboarding_question",
                    "step": assistant_turns + 1,
                    "total_steps": 3,
                    **question_data,
                }
            )
            self.append_to_conversation(student_id, "assistant", prompt_text)

            return {"stage": "onboarding", "step": assistant_turns + 1}

        # Final turn — parse structured answers into profile
        logger.info(f"[ONBOARDING] All 3 prompts answered — creating profile")
        profile_data = self._extract_onboarding_profile(history, student_response)

        # Create profile via MCP
        await self.student_mcp.create_profile(
            student_id=student_id,
            technical_level=profile_data.get("technical_level", "beginner"),
            a11y_exposure=profile_data.get("a11y_exposure", "none"),
            role_context=profile_data.get("role_context", ""),
            learning_goal=profile_data.get("learning_goal", ""),
        )

        # Select first objective based on student's assessed level
        objective_id, objective_text = await self._select_starting_objective(
            student_id, profile_data.get("a11y_exposure", "none")
        )

        # Create session and transition to introduction
        await self.student_mcp.update_session_state(
            session_id,
            student_id=student_id,
            stage="introduction",
            active_objective_id=objective_id,
            turns=0,
        )

        # Notify frontend of onboarding completion and stage change
        a11y_exposure = profile_data.get("a11y_exposure", "none")
        await ws_send(
            {
                "type": "onboarding_complete",
                "profile": profile_data,
                "first_objective": objective_text,
            }
        )
        await ws_send(
            {
                "type": "stage_update",
                "stage": "introduction",
                "objective": objective_text,
                "summary": "",
            }
        )

        # Send level-appropriate objective introduction
        intro_text = self._OBJECTIVE_INTROS.get(
            a11y_exposure, self._OBJECTIVE_INTROS["none"]
        )
        intro_msg = f"{intro_text}\n\nLet's begin!"
        await ws_send({"type": "stream_start"})
        await self._progressive_send(intro_msg, ws_send)
        await ws_send({"type": "stream_end", "metadata": {"stage": "introduction"}})
        self.append_to_conversation(student_id, "assistant", intro_msg)

        # Start the first teaching turn directly. No synthetic student
        # message is fabricated — the tutor opens the lesson on its own,
        # the analyzer is skipped (nothing to interpret yet), and only the
        # tutor's reply is appended to conversation history.
        await self._start_first_teaching_turn(
            student_id=student_id,
            session_id=session_id,
            objective_id=objective_id,
            objective_text=objective_text,
            ws_send=ws_send,
        )
        return {"stage": "introduction", "objective": objective_text}

    def _extract_onboarding_profile(
        self,
        history: List[Dict],
        final_response: str,
    ) -> Dict[str, str]:
        """Extract structured profile from onboarding answers.

        Since onboarding uses structured form inputs (clickable options),
        the user responses are the raw option values. Parse them directly
        from conversation history — no LLM needed.
        """
        # User responses are at indices 1, 3, 5 in history (after each assistant prompt)
        user_answers = [m["content"] for m in history if m.get("role") == "user"]
        # Add the final response (3rd answer)
        user_answers.append(final_response)

        # Map answers to profile fields using the onboarding question definitions
        profile = {
            "technical_level": "beginner",
            "a11y_exposure": "none",
            "role_context": "student",
            "learning_goal": "personal_interest",
        }

        for i, question in enumerate(self._ONBOARDING_QUESTIONS):
            if i >= len(user_answers):
                break
            answer = user_answers[i].strip().lower()
            field = question["field"]

            # Check if answer matches any option value
            matched = False
            for opt in question["options"]:
                if answer == opt["value"] or answer == opt["label"].lower():
                    if field == "role_context":
                        profile["role_context"] = opt["value"]
                    elif field == "a11y_exposure":
                        profile["a11y_exposure"] = opt["value"]
                    elif field == "learning_goal":
                        profile["learning_goal"] = opt["value"]
                    matched = True
                    break

            if not matched and answer:
                # "Other" or free-text — use as-is
                profile[field] = answer

        # Derive technical_level from a11y_exposure
        exposure = profile.get("a11y_exposure", "none")
        if exposure in ("none", "awareness"):
            profile["technical_level"] = "beginner"
        elif exposure == "working_knowledge":
            profile["technical_level"] = "intermediate"
        elif exposure == "professional":
            profile["technical_level"] = "advanced"

        logger.info(f"[ONBOARDING] Profile extracted: {profile}")
        return profile

    # ------------------------------------------------------------------
    # Starting objective selection (level-based)
    # ------------------------------------------------------------------

    # Maps a11y_exposure from onboarding to a specific starting objective.
    # IDs match the gold dataset imported via rebuild_db_from_converted_exports.
    _STARTING_OBJECTIVES = {
        # Level 0: no prior accessibility knowledge — start with WCAG structure
        "none": "I.A.2",
        # "Explain the structure of WCAG 2.2, including the POUR principles,
        #  guidelines, success criteria, and conformance levels"
        # Level 1: some awareness — semantic controls vs generic elements
        "awareness": "I.B.4",
        "working_knowledge": "I.D.10",
        # I.B.4: "Distinguish between semantic HTML controls and non-semantic
        #         elements in terms of built-in accessibility."
        # I.D.10: "Apply ARIA live regions to communicate dynamic content
        #          updates without moving keyboard focus."
        # Level 2: professional — analysis-level challenges
        "professional": "I.H.2",
        # "Analyze how design elements such as headings, landmarks, and color
        #  contrast affect accessibility for diverse user groups"
    }

    _STARTING_OBJECTIVE_TEXTS = {
        "none": (
            "Explain the structure of WCAG 2.2 by identifying the four principles "
            "(POUR), guidelines, and success criteria levels (A, AA, AAA)."
        ),
        "awareness": (
            "Distinguish between semantic HTML controls (e.g., `<button>`, `<a>`) "
            "and generic elements (e.g., `<div>`) in terms of built-in accessibility."
        ),
    }

    # Level-specific introductions — shown before the first teaching turn
    _OBJECTIVE_INTROS = {
        "none": (
            "Since you're just getting started with accessibility, we'll begin with "
            "the foundations — **the structure of WCAG 2.2**. This is the international "
            "standard for web accessibility, and understanding how it's organized will "
            "give you a framework for everything else you'll learn."
        ),
        "awareness": (
            "You already have some familiarity with accessibility concepts, so we'll "
            "start with a practical HTML foundation — **semantic controls vs generic "
            "elements**. This is where accessibility often succeeds or fails before "
            "ARIA even enters the picture."
        ),
        "working_knowledge": (
            "With your hands-on experience, you're ready for a deeper dive. We'll "
            "explore **ARIA live regions** — how different properties and values affect "
            "what assistive technologies announce to users when content changes dynamically."
        ),
        "professional": (
            "Given your expertise, let's go straight to analysis-level work. We'll "
            "examine **how design elements like headings, landmarks, and color contrast "
            "impact diverse user groups** — the kind of evaluation you'd do in a "
            "real audit."
        ),
    }

    async def _select_starting_objective(
        self,
        student_id: str,
        a11y_exposure: str,
    ) -> tuple:
        """Select the first objective based on the student's assessed level.

        Returns (objective_id, objective_text). Falls back to
        get_recommended_next_objective if the level-specific objective
        is not found or already mastered.
        """
        target_id = self._STARTING_OBJECTIVES.get(
            a11y_exposure, self._STARTING_OBJECTIVES["none"]
        )
        target_text = self._STARTING_OBJECTIVE_TEXTS.get(a11y_exposure, "")

        # Prefer a direct text match when configured. The runtime DB stores UUID
        # primary keys, so curriculum codes like I.A.2 do not resolve directly.
        if target_text:
            try:
                obj = await asyncio.to_thread(
                    self._fetch_objective_by_text, target_text
                )
                if obj:
                    logger.info(
                        f"[ONBOARDING] Level-based objective selected by text: "
                        f"exposure={a11y_exposure} → {obj['id']} ({obj['text'][:60]})"
                    )
                    return obj["id"], obj["text"]
            except Exception as e:
                logger.warning(
                    f"Failed to fetch starting objective by text for exposure={a11y_exposure}: {e}"
                )

        # Backward-compatible fallback for environments where IDs happen to be
        # stored as curriculum codes.
        try:
            obj = await asyncio.to_thread(self._fetch_objective_by_id, target_id)
            if obj:
                logger.info(
                    f"[ONBOARDING] Level-based objective selected: "
                    f"exposure={a11y_exposure} → {target_id} ({obj['text'][:60]})"
                )
                return target_id, obj["text"]
        except Exception as e:
            logger.warning(f"Failed to fetch starting objective {target_id}: {e}")

        # Fallback to generic recommendation
        next_obj = await self.student_mcp.get_recommended_next_objective(student_id)
        if next_obj:
            return next_obj.get("objective_id", ""), next_obj.get(
                "objective_text", "web accessibility fundamentals"
            )
        return "", "web accessibility fundamentals"

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
        artifact = await self._build_teaching_graph_content(
            objective_text=objective_text,
        )
        teaching_plan = artifact.graph.to_dict()
        display_plan = json.dumps(teaching_plan, indent=2)
        await ws_send(
            {
                "type": "teaching_plan",
                "plan": teaching_plan,
                "display_plan": display_plan,
            }
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
            {"id": node.id, "label": node.label} for node in artifact.graph.nodes
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
