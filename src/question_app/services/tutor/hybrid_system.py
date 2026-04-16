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

from .interfaces import VectorStoreInterface
from .azure_client import AzureAPIMClient
from ..general_chat_service import GeneralChatService
from ...models.tutor import KnowledgeLevel, SessionPhase, StudentProfile

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

    def execute_task(self, task_description: str, context: str = "", history : Optional[List[Dict[str , str]]] = None, reasoning_effort: Optional[str] = None) -> str:
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
        messages.append({"role": "user" , "content": task_description})
        try:
            response = self.client.chat(messages, temperature=0.7, reasoning_effort=reasoning_effort)
            logger.info(f"{self.role} completed task successfully")
            return response
        except Exception as e:
            logger.error(f"{self.role} task failed: {e}")
            return f"Task processing error in {self.role}: {str(e)}"


class CoordinatorAgent(SocraticAgent):

    def __init__(self , client = AzureAPIMClient) -> None:
        super().__init__(
            role = "Socratic Session Coordinator",
            # --- === FIX 1: UPDATE THE GOAL === ---
            goal = "Analyze the user's input to determine its primary intent: 'conceptual_question', 'code_analysis_request', or 'off_topic'.",
            backstory = """You are the central "brain" of a tutoring system focused *only* on web accessibility.
            You do not answer the student. Your job is to classify the user's
            input so it can be routed to the correct specialist agent.""",
            # --- === END OF FIX 1 === ---
            client = client
        )

    def decide_intent(self, student_response : str, history:Optional[List[Dict[str, str]]] = None) -> str:
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
            repsonse_json = self.execute_task(task_description , context = "", history=history, reasoning_effort="low")
            intent = json.loads(repsonse_json).get("intent" , "conceptual_question")

            # Add the new intent to the valid list
            if intent not in ["conceptual_question" , "code_analysis_request", "off_topic"]:
                logger.warning(f"CoordinatorAgent returned non-standard intent: {intent}")
                return "conceptual_question" # Default to this if confused
            
            logger.info(f"CoordinatorAgent decided intent : {intent}")
            return intent

        except Exception as e:
            logger.error(f"CoordinatorAgent failed : {e} , Defaulting to 'conceptual_question'")
            return "conceptual_question"


class CodeAnalyzerAgent(SocraticAgent):
    def __init__(self, client:AzureAPIMClient):
        super().__init__(
            role = "Expert Web Accessibility Code Analyst",
            goal = "Analyze a snippet of HTML, CSS, or JS and identify potential accessibility issues. Provide your analysis in a structured list.",
            backstory = """You are an expert on WCAG and web accessibility. 
            You do not talk to the student. You are a tool that provides technical analysis.
            Your job is to find common errors like missing alt text, non-semantic HTML (e.g., div used as a button), or poor color contrast hints.""",
            client = client
        )
    def analyze_code_snippet(self, code_snippet:str):
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
#If the min cosine similarity is set to 0, the RAG pipeline will just use the vector DB
#If the min cosine similarity is set to 1, the RAG pipeline will default to using LLM's general knowledge.
MIN_COSINE_SIMILARITY = 0.7
TEACHING_PLAN_MAX_COMPLETION_TOKENS = 5000
TEACHING_PLAN_REASONING_EFFORT = "low"

class HybridCrewAISocraticSystem:
    def __init__(
        self, azure_config: Dict[str, str], vector_store_service : VectorStoreInterface,
        db_manager=None, wcag_mcp_client=None, student_mcp_client=None
    ):
        tutor_deployment = (
            azure_config.get("tutor_deployment_name")
            or azure_config.get("deployment_name")
        )
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
        self.memory_file = "conversation_memory.json"
        self.conversation_memory : Dict[str, List[Dict[str , str]]] = {}
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
        student_id_override: str | None = None
    ) -> Dict[str, Any]:
        try:
            student_id = student_id_override or str(uuid.uuid4())[:8]
            profile = self.create_student(
                student_id=student_id,
                name=name,
                topic=topic,
                initial_assessment=initial_assessment
            )
            return {
                "student_id": profile.id, # Corrected to profile.id
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
                    "session_id": "session-1", "student_id": student_id,
                    "timestamp": datetime.now().isoformat(), "response": "Sample response",
                    "tutor_response": "Sample tutor response",
                }
            ]
        except Exception as e:
            logger.error(f"Failed to get session history: {e}")
            return []

    # --- (This is the corrected create_student function from last time) ---
    def create_student(
        self, 
        student_id: str,
        name: str, 
        topic: str, 
        initial_assessment: str = ""
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
        self.conversation_memory[student_id] = self.conversation_memory[student_id][-10:]
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
            context_str = "Recent conversation:\n" + "\n".join(
                f"{m['role']}: {m['content']}" for m in recent
            ) + "\n\n"

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
                        f"Student's question: \"{query}\"\n\n"
                        "Hypothetical correct answer:"
                    ),
                },
            ]
            hyde_answer = self.client.chat(messages, temperature=0.3, max_tokens=300, reasoning_effort="low")
            hyde_answer = hyde_answer.strip()
            if hyde_answer and len(hyde_answer) > 10:
                logger.info(f"HyDE generated ({len(hyde_answer)} chars): '{hyde_answer[:80]}...'")
                return hyde_answer
        except Exception as e:
            logger.warning(f"HyDE generation failed, using original query: {e}")

        return query

    async def get_rag_context(self, query: str, history: Optional[List[Dict[str, str]]] = None) -> tuple:
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
                distance = chunk.get('distance')
                rrf = chunk.get('rrf_score', 0)
                # Accept if: good RRF score AND reasonable vector distance
                if distance is not None and distance > MAX_COSINE_DISTANCE:
                    logger.debug(f"Rejected chunk (distance={distance:.3f}): {chunk.get('content', '')[:60]}")
                    continue
                if rrf < MIN_RRF_SCORE:
                    continue
                high_quality_chunks.append(chunk)

            if not high_quality_chunks:
                logger.info("No high-quality chunks found. LLM will rely on general knowledge.")
                return "", []

            context_for_agents = "\n--\n".join(c.get('content', '') for c in high_quality_chunks)
            logger.info(f"RAG context: {len(high_quality_chunks)} chunks passed to agents")
            return context_for_agents, high_quality_chunks

    async def get_combined_context(self, query: str, history: Optional[List[Dict[str, str]]] = None) -> tuple:
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

        logger.info(f"Combined context: RAG={len(rag_context)} chars, WCAG MCP={len(wcag_context)} chars")

        # Build combined context with labeled sections
        parts = []
        if rag_context:
            parts.append(f"--- QUIZ KNOWLEDGE BASE ---\n{rag_context}")
        if wcag_context:
            parts.append(f"--- WCAG GUIDELINES REFERENCE (authoritative) ---\n{wcag_context}")

        combined = "\n\n".join(parts)
        return combined, quiz_chunks, wcag_context

    # ------------------------------------------------------------------
    # Student MCP context helpers
    # ------------------------------------------------------------------

    async def _load_student_bundle(
        self, student_id: str, objective_id: str = "",
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
        self, student_id: str, objective_id: str = "",
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
        self, session_id: str, objective_id: str = "",
    ) -> None:
        """Rehydrate the in-memory session cache from durable storage if available."""
        if self._session_cache.get(session_id):
            return
        if not self.student_mcp or not hasattr(self.student_mcp, "get_session_runtime_cache"):
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
        if not self.student_mcp or not hasattr(self.student_mcp, "save_session_runtime_cache"):
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
        if not self.student_mcp or not hasattr(self.student_mcp, "clear_session_runtime_cache"):
            return
        try:
            await self.student_mcp.clear_session_runtime_cache(session_id)
        except Exception as e:
            logger.warning(f"Failed to clear session runtime cache: {e}")

    def _format_student_context(
        self, profile: Optional[Dict], mastery: List[Dict],
        session: Optional[Dict], misconceptions: List[Dict],
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
                    + (f" ({m.get('evidence_summary', '')})" if m.get('evidence_summary') else "")
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
                    "  Gaps: "
                    + ", ".join(objective_memory.get("active_gaps", [])[:5])
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
                    "  Strengths: "
                    + ", ".join(learner_memory.get("strengths", [])[:5])
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
    def _parse_json_response(text: str, fallback: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Parse a JSON object from a model response, stripping code fences."""
        fallback = fallback or {}
        raw = (text or "").strip()
        if raw.startswith("```"):
            lines = raw.splitlines()
            if len(lines) >= 2:
                raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
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
            priority = str(
                raw_event.get("repair_priority", "") or default_priority
            ).strip().lower()
            if priority not in {"normal", "must_address_now"}:
                priority = default_priority
            repair_scope = str(
                raw_event.get("repair_scope", "") or ""
            ).strip().lower()
            if repair_scope not in {"fact", "distinction", "full_sequence"}:
                repair_scope = "fact"
            repair_pattern = str(
                raw_event.get("repair_pattern", "") or ""
            ).strip().lower()
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
            for item in (((turn_analysis or {}).get("misconception_events", []) or []))
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
                repair_scope = str(
                    item.get("repair_scope", "") or ""
                ).strip().lower()
                repair_pattern = str(
                    item.get("repair_pattern", "") or ""
                ).strip().lower()
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
            1 for concept in concepts
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
            if (
                times_seen >= min_times_seen
                and (
                    scope == "full_sequence"
                    or pattern == "same_snippet_walkthrough"
                )
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
        if (
            repair_scope != "full_sequence"
            and repair_pattern != "same_snippet_walkthrough"
        ):
            return False
        combined = " ".join(
            str(item.get(field, "") or "").lower()
            for field in ("key", "text")
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
        )
        return any(marker in combined for marker in procedural_markers)

    @staticmethod
    def _supports_repair_exit(pacing_signal: Optional[Dict[str, Any]]) -> bool:
        pacing_signal = pacing_signal or {}
        concept_closure = str(
            pacing_signal.get("concept_closure", "") or ""
        ).strip().lower()
        reasoning_mode = str(
            pacing_signal.get("reasoning_mode", "") or ""
        ).strip().lower()
        return (
            concept_closure in {"almost_ready", "ready"}
            and reasoning_mode in {"application", "transfer"}
        )

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
        concept_closure = str(
            pacing_signal.get("concept_closure", "") or ""
        ).strip().lower()
        reasoning_mode = str(
            pacing_signal.get("reasoning_mode", "") or ""
        ).strip().lower()
        return (
            concept_closure in {"almost_ready", "ready"}
            and reasoning_mode in {"application", "transfer"}
        )

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
        guarded = copy.deepcopy(analysis or {})
        if not guarded:
            return {}

        pacing_signal = guarded.setdefault("pacing_signal", {})
        current_pace = str(
            (pacing_state or {}).get("current_pace", "") or ""
        ).strip().lower()
        teaching_move = str(
            guarded.get("teaching_move", "") or ""
        ).strip().lower()
        answer_current_question_first = bool(
            guarded.get("answer_current_question_first")
        )
        concept_closure = str(
            pacing_signal.get("concept_closure", "") or ""
        ).strip().lower()
        reasoning_mode = str(
            pacing_signal.get("reasoning_mode", "") or ""
        ).strip().lower()
        guarded["stage_action"], guarded["target_stage"], guarded["stage_reason"] = (
            cls._normalize_stage_transition(
                current_stage=current_stage,
                stage_action=guarded.get("stage_action", ""),
                target_stage=guarded.get("target_stage", current_stage),
                stage_reason=guarded.get("stage_reason", ""),
            )
        )
        stage_action_value = str(guarded.get("stage_action", "") or "").strip().lower()
        target_stage = str(guarded.get("target_stage", "") or "").strip()

        current_turn_misconceptions = [
            item
            for item in ((guarded.get("misconception_events", []) or []))
            if isinstance(item, dict)
        ]
        must_repair_now = any(
            cls._is_open_must_repair_event(item)
            for item in current_turn_misconceptions
        )
        repeated_active_sequence = cls._has_repeated_full_sequence_signal(
            misconception_state,
            "active_misconceptions",
        )
        repeated_resolved_sequence = cls._has_repeated_full_sequence_signal(
            misconception_state,
            "recently_resolved",
        )
        supports_repair_exit = cls._supports_repair_exit(pacing_signal)

        reasons: List[str] = []
        if must_repair_now:
            reasons.append("Open must-repair misconception still needs explicit correction.")
        if (
            stage_action_value == "advance"
            and concept_closure != "ready"
            and not cls._allows_intro_exit_with_partial_closure(
                current_stage=current_stage,
                target_stage=target_stage,
                pacing_signal=pacing_signal,
            )
        ):
            reasons.append("Concept closure is not ready yet.")
        coverage_ratio = cls._lesson_coverage_ratio(lesson_state)
        if (
            stage_action_value == "advance"
            and target_stage in {"readiness_check", "mini_assessment", "final_assessment"}
            and coverage_ratio < 0.6
        ):
            reasons.append("Objective coverage is still too low for the next stage.")

        if reasons:
            guarded["stage_action"] = "stay"
            guarded["target_stage"] = current_stage
            existing_reason = str(guarded.get("stage_reason", "") or "").strip()
            joined = " ".join(reasons)
            guarded["stage_reason"] = (
                f"{existing_reason} {joined}".strip()
                if existing_reason
                else joined
            )
            if must_repair_now and str(
                guarded.get("teaching_move", "") or ""
            ).strip().lower() not in {"repair", "clarify"}:
                guarded["teaching_move"] = "repair"
            if must_repair_now:
                pacing_signal["override_pace"] = "slow"
                pacing_signal["override_reason"] = (
                    "Active misconception requires explicit repair before moving on."
                )
                if pacing_signal.get("recommended_next_step") == "advance":
                    pacing_signal["recommended_next_step"] = "ask_narrower"

        if (
            not must_repair_now
            and teaching_move in {"repair", "clarify"}
            and not repeated_active_sequence
            and reasoning_mode in {"application", "transfer"}
            and str(pacing_signal.get("recommended_next_step", "") or "").strip().lower()
            in {"ask_narrower", "ask_same_level"}
        ):
            pacing_signal["recommended_next_step"] = "give_example"
            pacing_signal["override_pace"] = "steady"
            pacing_signal["override_reason"] = (
                "Learner already shows causal footing; use a fresh case instead of another same-level restatement check."
            )

        if (
            not must_repair_now
            and teaching_move == "clarify"
            and answer_current_question_first
        ):
            guarded["follow_up_question_policy"] = "optional_if_explanation_suffices"

        if (
            not must_repair_now
            and repeated_active_sequence
            and supports_repair_exit
            and str(pacing_signal.get("recommended_next_step", "") or "").strip().lower()
            == "ask_narrower"
        ):
            pacing_signal["recommended_next_step"] = "give_example"
            pacing_signal["override_pace"] = "steady"
            pacing_signal["override_reason"] = (
                "Repeated full-sequence repair now has enough evidence for a fresh transfer check."
            )

        if (
            not must_repair_now
            and repeated_resolved_sequence
            and supports_repair_exit
            and str(guarded.get("stage_action", "") or "").strip().lower() != "advance"
        ):
            next_stage = cls._suggest_next_stage_after_repair(
                current_stage=current_stage,
                coverage_ratio=coverage_ratio,
            )
            if next_stage:
                guarded["stage_action"] = "advance"
                guarded["target_stage"] = next_stage
                existing_reason = str(guarded.get("stage_reason", "") or "").strip()
                repair_reason = (
                    "Repeated full-sequence repair now looks stable after transfer-level reasoning."
                )
                guarded["stage_reason"] = (
                    f"{existing_reason} {repair_reason}".strip()
                    if existing_reason
                    else repair_reason
                )
                if str(pacing_signal.get("recommended_next_step", "") or "").strip().lower() in {
                    "ask_narrower",
                    "ask_same_level",
                    "give_example",
                }:
                    pacing_signal["recommended_next_step"] = "advance"
                pacing_signal["override_pace"] = "steady"
                pacing_signal["override_reason"] = (
                    "Repeated full-sequence repair was resolved with application-level evidence."
                )

        return guarded

    @staticmethod
    def _format_response_constraints_for_tutor(
        pacing_state: Optional[Dict[str, Any]],
        turn_analysis: Optional[Dict[str, Any]] = None,
        misconception_state: Optional[Dict[str, Any]] = None,
    ) -> str:
        pace = str((pacing_state or {}).get("current_pace", "") or "").strip().lower()
        if pace not in {"slow", "steady", "fast"}:
            pace = "steady"

        must_repair = any(
            isinstance(item, dict)
            and HybridCrewAISocraticSystem._is_open_must_repair_event(item)
            for item in (((turn_analysis or {}).get("misconception_events", []) or []))
        )
        requires_procedural_full_sequence_repair = any(
            isinstance(item, dict)
            and HybridCrewAISocraticSystem._is_open_must_repair_event(item)
            and HybridCrewAISocraticSystem._is_procedural_full_sequence_repair(item)
            for item in (((turn_analysis or {}).get("misconception_events", []) or []))
        )
        requires_conceptual_sequence_completion = any(
            isinstance(item, dict)
            and HybridCrewAISocraticSystem._is_open_must_repair_event(item)
            and not HybridCrewAISocraticSystem._is_procedural_full_sequence_repair(item)
            and (
                str(item.get("repair_scope", "") or "") == "full_sequence"
                or str(item.get("repair_pattern", "") or "") == "same_snippet_walkthrough"
            )
            for item in (((turn_analysis or {}).get("misconception_events", []) or []))
        )
        pacing_signal = (turn_analysis or {}).get("pacing_signal", {}) or {}
        recommended_next_step = str(
            pacing_signal.get("recommended_next_step", "") or ""
        ).strip().lower()
        teaching_move = str(
            (turn_analysis or {}).get("teaching_move", "") or ""
        ).strip().lower()
        answer_current_question_first = bool(
            (turn_analysis or {}).get("answer_current_question_first")
        )
        repeated_active_sequence = HybridCrewAISocraticSystem._has_repeated_full_sequence_signal(
            misconception_state,
            "active_misconceptions",
        )

        response_shape = "question_only"
        if requires_procedural_full_sequence_repair:
            response_shape = "full_sequence_repair"
        elif requires_conceptual_sequence_completion:
            response_shape = "repair_and_check"
        elif teaching_move == "clarify" and answer_current_question_first and not must_repair:
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
            and recommended_next_step in {"ask_narrower", "ask_same_level", "give_example"}
        ):
            response_shape = "example_then_check"

        max_new_concepts = 0 if pace == "slow" or must_repair else 1
        max_setup_sentences = 2 if pace == "fast" else 4 if pace == "slow" else 3

        lines = ["RESPONSE CONSTRAINTS:"]
        lines.append(f"- Response shape: {response_shape}")
        lines.append(f"- Max new concepts: {max_new_concepts}")
        lines.append("- Max questions: 1")
        lines.append(f"- Max setup sentences before the question: {max_setup_sentences}")
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
            lines.append("- Repair pattern: exact ordered completion on the same example.")
            lines.append(
                "- Hard requirement: require one complete ordered restatement with the missing named step(s) and final label."
            )
            lines.append("- Do not expand into a new concept before the exact completion check.")
        elif teaching_move == "repair":
            lines.append(
                "- After correcting the misconception, use one fresh case, comparison, or consequence check, not a restatement of your correction."
            )
        elif (
            not must_repair
            and repeated_active_sequence
            and response_shape == "example_then_check"
        ):
            lines.append("- Prefer one fresh transfer example over another paraphrase recheck.")
        if must_repair:
            lines.append("- Advancement lock: open misconception")
        elif str((turn_analysis or {}).get("stage_action", "") or "") != "advance":
            lines.append("- Advancement lock: stay on the current stage for this response")
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

        lines = ["TURN ANALYSIS:"]
        route = turn_analysis.get("turn_route", "")
        if route:
            lines.append(f"- Route: {route}")
        answer_first = turn_analysis.get("answer_current_question_first")
        if answer_first is not None:
            lines.append(
                f"- Answer current question first: {'yes' if answer_first else 'no'}"
            )
        if turn_analysis.get("student_question_to_answer"):
            lines.append(
                f"- Student question to answer: {turn_analysis['student_question_to_answer']}"
            )
        if turn_analysis.get("teaching_move"):
            lines.append(f"- Teaching move: {turn_analysis['teaching_move']}")
        lesson_patch = turn_analysis.get("lesson_state_patch") or {}
        bridge_target = lesson_patch.get("bridge_back_target", "")
        if bridge_target:
            lines.append(f"- Bridge back target: {bridge_target}")
        target_stage = turn_analysis.get("target_stage", "")
        if target_stage:
            lines.append(
                f"- Stage recommendation: {turn_analysis.get('stage_action', 'stay')} -> {target_stage}"
            )
        pacing_signal = turn_analysis.get("pacing_signal") or {}
        if pacing_signal:
            parts = []
            for key in (
                "grasp_level",
                "reasoning_mode",
                "support_needed",
                "confusion_level",
                "concept_closure",
            ):
                value = pacing_signal.get(key)
                if value:
                    parts.append(f"{key}={value}")
            if parts:
                lines.append(f"- Pacing signal: {', '.join(parts)}")
            if pacing_signal.get("recommended_next_step"):
                lines.append(
                    f"- Pacing next step: {pacing_signal['recommended_next_step']}"
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
                return "`\"\"`"
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

    @classmethod
    def _render_turn_analysis_for_display(
        cls, turn_analysis: Optional[Dict[str, Any]]
    ) -> str:
        if not turn_analysis:
            return ""

        lines = [
            "TURN ANALYSIS EXPLANATION",
            (
                "This is the analyzer's interpreted state for the latest student turn. "
                "Each item below explains what the field means, what it affects, how it is computed, "
                "and the value being used on this turn."
            ),
            "",
        ]

        simple_field_specs = [
            (
                "turn_route",
                "This field classifies what kind of turn the student just produced.",
                "It controls which response path the tutor should follow next.",
                "from the latest student message, recent transcript context, and the active objective",
            ),
            (
                "answer_current_question_first",
                "This flag says whether the tutor must answer the student's live question before doing anything else.",
                "It affects response ordering and prevents the tutor from skipping over an active question.",
                "by checking whether the student asked a real unresolved question in this turn",
            ),
            (
                "student_question_to_answer",
                "This field captures the specific student question that should be answered first when one exists.",
                "It gives the tutor a concrete bridge-back target instead of relying on vague memory.",
                "by extracting the most actionable question-like request from the student's latest message",
            ),
            (
                "teaching_move",
                "This field chooses the instructional move for the next tutor response, such as continue, clarify, repair, consolidate, or redirect.",
                "It shapes the tone and structure of the next tutor turn.",
                "from the learner's understanding signal, misconception state, and the current lesson need",
            ),
            (
                "stage_action",
                "This field says whether the lesson stage should stay where it is, advance, or regress.",
                "It controls stage transitions before the next tutor response is composed.",
                "from the student's demonstrated understanding, coverage, and misconception guardrails",
            ),
            (
                "target_stage",
                "This field names the stage the analyzer wants the lesson to be in after this turn.",
                "It determines the pedagogical mode the tutor will use next when a transition is allowed.",
                "by combining the analyzer recommendation with deterministic stage-order and coverage rules",
            ),
            (
                "stage_reason",
                "This field records the explanation for the current stage decision.",
                "It makes the stage transition logic inspectable instead of leaving it implicit.",
                "from the analyzer's rationale plus any deterministic guardrails that override or normalize the move",
            ),
            (
                "follow_up_question_policy",
                "This field gives an extra rule for whether the tutor should ask a follow-up question after answering.",
                "It prevents low-value answer-echo checks when a direct clarification already resolved the turn.",
                "by response-control rules after the analyzer output is checked against pacing and misconception state",
            ),
        ]

        for key, meaning, role, computation in simple_field_specs:
            if key in turn_analysis:
                lines.append(
                    cls._render_turn_analysis_field(
                        key, turn_analysis.get(key), meaning, role, computation
                    )
                )
                lines.append("")

        compound_specs = {
            "mastery_signal": (
                "This block summarizes whether the learner's mastery record should change on this turn.",
                "It affects persistence of mastery state and confidence tracking.",
                "from the analyzer's evidence judgment, bounded mastery policy, and later runtime enforcement",
                [
                    (
                        "should_update",
                        "This flag says whether a mastery write should happen now.",
                        "It decides whether the runtime attempts to persist a mastery judgment for this turn.",
                        "from whether the analyzer believes the evidence is strong enough for a bounded mastery update",
                    ),
                    (
                        "level",
                        "This field names the mastery level the analyzer currently believes fits the learner.",
                        "It provides the candidate mastery state for persistence or later inspection.",
                        "from the learner's demonstrated understanding and the allowed mastery levels for the current stage",
                    ),
                    (
                        "confidence",
                        "This field gives the analyzer's numeric confidence in the mastery judgment.",
                        "It communicates how strongly the system trusts the level decision.",
                        "from the analyzer's internal assessment of evidence strength on this turn",
                    ),
                    (
                        "evidence_summary",
                        "This field is the compact justification for the mastery judgment.",
                        "It explains what evidence the analyzer thinks supports the mastery call.",
                        "by summarizing the strongest demonstrated evidence from the student's latest response",
                    ),
                ],
            ),
            "misconception_events": (
                "This block logs misconception updates raised by the analyzer on this turn.",
                "It controls whether misconceptions are logged, kept active, or marked as resolved candidates.",
                "from the student's latest reasoning compared against the expected concept model",
                [
                    (
                        "key",
                        "This field is the stable identifier for the misconception pattern.",
                        "It lets the runtime track the same misconception across multiple turns.",
                        "from the analyzer's attempt to match the current issue to an existing or reusable misconception label",
                    ),
                    (
                        "text",
                        "This field is the human-readable description of the misconception event.",
                        "It makes the tracked issue understandable in logs and memory.",
                        "by summarizing the incorrect or repaired idea in plain language",
                    ),
                    (
                        "action",
                        "This field says whether the misconception should be logged, kept active, or treated as a resolve candidate.",
                        "It controls the durable misconception state update applied after analysis.",
                        "from whether the learner is still expressing the issue or appears to have repaired it",
                    ),
                    (
                        "repair_priority",
                        "This field indicates how urgently the misconception must be handled.",
                        "It can lock stage advancement when the issue is marked as must-address-now.",
                        "from the severity of the misunderstanding and whether moving on would be unsafe",
                    ),
                    (
                        "repair_scope",
                        "This field defines whether the repair is about a fact, a distinction, or a full ordered sequence.",
                        "It determines how broad the required repair needs to be.",
                        "from the shape of the learner's error and whether missing one piece breaks the whole concept path",
                    ),
                    (
                        "repair_pattern",
                        "This field says what kind of repair check should happen next, such as a direct recheck, same-snippet walkthrough, or fresh transfer case.",
                        "It shapes the next tutor move after the misconception is identified.",
                        "from the mismatch pattern the analyzer believes will best test whether the repair really landed",
                    ),
                ],
            ),
            "lesson_state_patch": (
                "This block is the analyzer's proposed update to the structured lesson state.",
                "It keeps the session anchored to the active concept, next check, and concept coverage map.",
                "from the current concept focus plus what the learner demonstrated in this turn",
                [
                    (
                        "active_concept",
                        "This field names the concept the lesson should now be centered on.",
                        "It keeps the tutor from drifting across concepts without a visible reason.",
                        "from the teaching plan order and the concept the student's response most directly engaged",
                    ),
                    (
                        "pending_check",
                        "This field states the next understanding check the system still wants before moving on.",
                        "It gives the tutor a concrete next checkpoint for the current concept.",
                        "from the remaining uncertainty after analyzing the learner's answer",
                    ),
                    (
                        "bridge_back_target",
                        "This field records what the tutor should bridge back to after answering a side question or clarification.",
                        "It preserves lesson continuity across digressions or repairs.",
                        "from the current lesson focus that should remain primary after the immediate response is handled",
                    ),
                    (
                        "concept_updates",
                        "This field contains status patches for concepts in the plan, such as not covered, in progress, or covered.",
                        "It updates the visible and internal coverage map used for pacing and stage decisions.",
                        "from the analyzer's judgment about how much of each concept the learner has actually demonstrated",
                    ),
                ],
            ),
            "pacing_signal": (
                "This block is the analyzer's pacing read on the learner for this turn.",
                "It controls how much scaffold, difficulty, and forward movement the tutor should use next.",
                "from the learner's response quality, stability, confusion, and reasoning depth",
                [
                    (
                        "grasp_level",
                        "This field gives a coarse read of how solid the learner's understanding currently is.",
                        "It influences how cautious or ambitious the next tutor move should be.",
                        "from the overall strength and stability of the learner's answer on this turn",
                    ),
                    (
                        "reasoning_mode",
                        "This field identifies the kind of reasoning the learner showed, such as guessing, recall, paraphrase, application, or transfer.",
                        "It helps the system distinguish shallow repetition from real conceptual use.",
                        "from the structure of the student's response rather than just whether the answer sounds correct",
                    ),
                    (
                        "support_needed",
                        "This field estimates how much scaffold the learner still needs right now.",
                        "It affects whether the tutor should explain more, narrow the check, or move faster.",
                        "from the learner's clarity, precision, and independence in the latest response",
                    ),
                    (
                        "confusion_level",
                        "This field estimates how confused or stable the learner seems on the current concept.",
                        "It helps determine whether to repair, clarify, or keep pushing forward.",
                        "from signs of contradiction, hesitation, misclassification, or direct confusion in the response",
                    ),
                    (
                        "response_pattern",
                        "This field captures the style of the learner's response, such as guessing, hedging, direct answering, or self-correction.",
                        "It gives the tutor another signal about how reliable the visible understanding really is.",
                        "from the wording pattern and confidence cues in the student's latest turn",
                    ),
                    (
                        "concept_closure",
                        "This field says whether the current concept looks not ready, almost ready, or ready to close.",
                        "It directly affects whether the lesson can move on from the current concept or stage.",
                        "from the completeness and stability of the learner's demonstrated understanding on the active concept",
                    ),
                    (
                        "override_pace",
                        "This field is the runtime pace the system wants to enforce next, such as slow, steady, or fast.",
                        "It calibrates how aggressively the tutor should advance or scaffold.",
                        "from analyzer pacing judgment plus deterministic runtime guardrails",
                    ),
                    (
                        "override_reason",
                        "This field records why the current pace is being overridden or held.",
                        "It makes pacing changes inspectable instead of opaque.",
                        "from the strongest pacing-relevant condition detected on this turn",
                    ),
                    (
                        "recommended_next_step",
                        "This field is the analyzer's recommended instructional next step, such as re-explain, give an example, ask narrower, stay at the same level, or advance.",
                        "It is one of the strongest direct steering signals for the next tutor response.",
                        "from the combination of understanding quality, confusion level, and what evidence is still missing",
                    ),
                ],
            ),
            "objective_memory_patch": (
                "This block proposes updates to the durable memory for this learner on the current objective.",
                "It keeps a concise running record of demonstrated skills, active gaps, and the next focus.",
                "from the stable instructional takeaways of this turn rather than a transcript dump",
                [
                    (
                        "summary",
                        "This field is the compact durable summary of the learner's current state on this objective.",
                        "It gives later turns a concise memory of where the learner stands.",
                        "by compressing the turn into the most instructionally important state update",
                    ),
                    (
                        "demonstrated_skills_add",
                        "This field lists skills that should be added to the learner's demonstrated skills for this objective.",
                        "It accumulates evidence of what the learner can now reliably do.",
                        "from behaviors or explanations the learner successfully demonstrated on this turn",
                    ),
                    (
                        "active_gaps_current",
                        "This field lists the gaps the system believes are still currently active for this objective.",
                        "It prevents the tutor from treating repaired or irrelevant gaps as still open.",
                        "from the unresolved weaknesses that remain after analyzing the learner's latest response",
                    ),
                    (
                        "next_focus",
                        "This field states the next concept or distinction the tutor should prioritize for this objective.",
                        "It gives the next turn a concrete instructional target.",
                        "from the most important remaining gap after the current turn is interpreted",
                    ),
                ],
            ),
            "learner_memory_patch": (
                "This block proposes updates to the learner-level memory that can carry across objectives.",
                "It captures stable tendencies, strengths, support needs, and strategies that matter beyond one lesson.",
                "from repeated or instructionally meaningful behavior shown in the latest turn",
                [
                    (
                        "summary",
                        "This field is the compact durable summary of the learner's broader behavior or need.",
                        "It helps future objectives start with a more tailored teaching posture.",
                        "by compressing the most reusable learner-level takeaway from the turn",
                    ),
                    (
                        "strengths_add",
                        "This field lists strengths that should be added to the learner profile.",
                        "It preserves positive capabilities the tutor can rely on later.",
                        "from stable evidence of what the learner did well in this turn",
                    ),
                    (
                        "support_needs_current",
                        "This field lists the support needs that appear to be currently active for the learner.",
                        "It keeps the tutor aligned with the learner's real instructional needs right now.",
                        "from the kind of scaffold the learner still needed during the turn",
                    ),
                    (
                        "tendencies_current",
                        "This field lists current response tendencies the system wants to remember, such as hedging or asking clarifying questions.",
                        "It helps the tutor adapt to the learner's recurring interaction pattern.",
                        "from visible response style patterns in the learner's latest turn",
                    ),
                    (
                        "successful_strategies_add",
                        "This field lists teaching strategies that worked well for this learner and should be remembered.",
                        "It helps future turns and future objectives reuse effective scaffolds.",
                        "from the teaching move that appeared to help the learner make progress on this turn",
                    ),
                ],
            ),
        }

        for field, (meaning, role, computation, nested_specs) in compound_specs.items():
            if field not in turn_analysis:
                continue
            field_value = turn_analysis.get(field)
            lines.append(
                cls._render_turn_analysis_field(
                    field,
                    field_value,
                    meaning,
                    role,
                    computation,
                )
            )
            nested_value = field_value
            if isinstance(nested_value, dict):
                for nested_key, n_meaning, n_role, n_computation in nested_specs:
                    if nested_key in nested_value:
                        lines.append(
                            cls._render_turn_analysis_field(
                                f"{field}.{nested_key}",
                                nested_value.get(nested_key),
                                n_meaning,
                                n_role,
                                n_computation,
                            )
                        )
            elif isinstance(nested_value, list):
                for index, item in enumerate(nested_value, 1):
                    item_name = f"{field}[{index}]"
                    lines.append(
                        cls._render_turn_analysis_field(
                            item_name,
                            item,
                            "This entry is one item inside the list-valued analysis block.",
                            "It carries one concrete event or patch inside the larger field.",
                            "from the analyzer's structured decision for this turn",
                        )
                    )
                    if isinstance(item, dict):
                        for nested_key, n_meaning, n_role, n_computation in nested_specs:
                            if nested_key in item:
                                lines.append(
                                    cls._render_turn_analysis_field(
                                        f"{item_name}.{nested_key}",
                                        item.get(nested_key),
                                        n_meaning,
                                        n_role,
                                        n_computation,
                                    )
                                )
            lines.append("")

        return "\n".join(lines).strip()

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
        student_response: str,
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
    ) -> List[Dict[str, str]]:
        """Build tutor-pass messages for guided learning."""
        from .prompts import (
            build_instance_b_prompt,
            format_lesson_state,
            format_misconception_state,
        )

        system_prompt = build_instance_b_prompt(
            knowledge_context=teaching_content,
            student_context=student_context,
            current_stage=current_stage,
            active_objective=active_objective,
            teaching_plan=teaching_plan,
            lesson_state_context=format_lesson_state(lesson_state),
            misconception_state_context=format_misconception_state(
                misconception_state
            ),
        )
        messages = [{"role": "system", "content": system_prompt}]
        turn_analysis_block = self._format_turn_analysis_for_tutor(turn_analysis)
        if turn_analysis_block:
            messages.append({"role": "system", "content": turn_analysis_block})
        pacing_block = self._format_adaptive_pacing_for_tutor(pacing_state)
        if pacing_block:
            messages.append({"role": "system", "content": pacing_block})
        response_constraints_block = self._format_response_constraints_for_tutor(
            pacing_state=pacing_state,
            turn_analysis=turn_analysis,
            misconception_state=misconception_state,
        )
        if response_constraints_block:
            messages.append({"role": "system", "content": response_constraints_block})
        misconception_block = self._format_active_misconception_guidance(
            turn_analysis,
            misconception_state
        )
        if misconception_block:
            messages.append({"role": "system", "content": misconception_block})
        for extra in extra_system_messages or []:
            if extra:
                messages.append({"role": "system", "content": extra})
        if history:
            messages.extend(history[-6:])
        messages.append({"role": "user", "content": student_response})
        return messages

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
        """Run the structured turn-analysis pass before the tutor responds."""
        from .prompts import (
            build_turn_analyzer_prompt,
            format_lesson_state,
            format_misconception_state,
            format_pacing_state,
        )

        prompt = build_turn_analyzer_prompt(
            knowledge_context=teaching_content,
            student_context=student_context,
            current_stage=current_stage,
            active_objective=active_objective,
            teaching_plan=teaching_plan,
            lesson_state_context=format_lesson_state(lesson_state),
            pacing_state_context=format_pacing_state(pacing_state),
            misconception_state_context=format_misconception_state(
                misconception_state
            ),
        )
        transcript = self._format_reflection_transcript(history, student_response)
        response = await asyncio.to_thread(
            self.reasoning_client.chat,
            [
                {"role": "system", "content": prompt},
                {"role": "user", "content": transcript},
            ],
            0.0,
            1200,
        )
        return self._parse_json_response(
            response,
            fallback={
                "turn_route": "objective_answer",
                "answer_current_question_first": True,
                "student_question_to_answer": student_response[:160],
                "teaching_move": "continue",
                "stage_action": "stay",
                "target_stage": current_stage,
                "stage_reason": "",
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
        """Run the structured reflection pass for an assessment answer."""
        from .prompts import (
            build_assessment_reflector_prompt,
            format_lesson_state,
            format_misconception_state,
        )

        prompt = build_assessment_reflector_prompt(
            knowledge_context=teaching_content,
            student_context=student_context,
            current_stage=current_stage,
            active_objective=active_objective,
            teaching_plan=teaching_plan,
            lesson_state_context=format_lesson_state(lesson_state),
            misconception_state_context=format_misconception_state(
                misconception_state
            ),
        )
        transcript = self._format_reflection_transcript(history, student_response)
        response = await asyncio.to_thread(
            self.reasoning_client.chat,
            [
                {"role": "system", "content": prompt},
                {"role": "user", "content": transcript},
            ],
            0.0,
            900,
        )
        return self._parse_json_response(
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
            summary = (
                objective_memory_patch.get("summary")
                or existing_objective.get("summary", "")
            )
            next_focus = (
                objective_memory_patch.get("next_focus")
                or existing_objective.get("next_focus", "")
            )
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
            summary = (
                learner_memory_patch.get("summary")
                or existing_learner.get("summary", "")
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
                    tracked_text = str(
                        active_lookup[key].get("text", "") or ""
                    ).strip()
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
        preview_misconception_state = self._session_cache.preview_misconception_state(
            session_id,
            self._coerce_misconception_events(
                analysis,
                default_priority=(
                    "must_address_now"
                    if str(analysis.get("teaching_move", "") or "").strip().lower()
                    == "repair"
                    else "normal"
                ),
            ),
        )
        preview_pacing_state = self._session_cache.preview_pacing_state(
            session_id,
            analysis.get("pacing_signal"),
        )
        preview_objective_memory = self._preview_objective_memory_state(
            (bundle or {}).get("objective_memory") or {},
            analysis.get("objective_memory_patch"),
        )
        analysis = self._enforce_turn_response_controls(
            current_stage=current_stage,
            analysis=analysis,
            lesson_state=self._session_cache.get_lesson_state(session_id),
            pacing_state=preview_pacing_state,
            misconception_state=preview_misconception_state,
        )

        await self.student_mcp.increment_turn_count(session_id)
        misconception_events = self._coerce_misconception_events(
            analysis,
            default_priority=(
                "must_address_now"
                if str(analysis.get("teaching_move", "") or "").strip().lower()
                == "repair"
                else "normal"
            ),
        )
        await self._apply_misconception_events(
            student_id=student_id,
            session_id=session_id,
            objective_id=objective_id,
            events=misconception_events,
        )

        self._session_cache.apply_lesson_state_patch(
            session_id,
            analysis.get("lesson_state_patch"),
        )
        self._session_cache.recompute_lesson_state(
            session_id,
            objective_memory=preview_objective_memory,
            misconception_state=self._session_cache.get_misconception_state(
                session_id
            ),
        )
        self._session_cache.apply_pacing_signal(
            session_id,
            analysis.get("pacing_signal"),
        )
        await self._persist_session_cache(session_id)

        await self._apply_memory_patches(
            student_id,
            objective_id,
            analysis.get("objective_memory_patch"),
            analysis.get("learner_memory_patch"),
            bundle=bundle,
        )

        mastery_signal = analysis.get("mastery_signal") or {}
        mastery_level = mastery_signal.get("level", "")
        if mastery_signal.get("should_update") and mastery_level in (
            "not_attempted",
            "misconception",
            "in_progress",
        ):
            mastery_result = await self.student_mcp.apply_mastery_judgment(
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

        stage_action = analysis.get("stage_action", "stay")
        target_stage = analysis.get("target_stage", current_stage)
        stage_reason = analysis.get("stage_reason", "")

        # Guardrail: block premature assessment if concept coverage is too low.
        # The turn analyzer may recommend assessment after a strong answer on
        # one concept, but if the teaching plan still has uncovered knowledge
        # concepts, the student hasn't been taught enough material yet.
        if (
            stage_action == "advance"
            and target_stage in ("mini_assessment", "final_assessment")
        ):
            lesson_state = self._session_cache.get_lesson_state(session_id)
            concepts = (lesson_state or {}).get("concepts", [])
            if concepts:
                covered = sum(
                    1 for c in concepts if c.get("status") == "covered"
                )
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
        self, student_id: str, session_id: str, ws_send,
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
        self, student_response: str, context: str,
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
        messages = self._build_legacy_instance_a_response_messages(student_response, context, history, student_context=student_context)
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
            self.client.chat, messages, 0.7, 1000
        )
        await ws_send({"type": "stream_start"})
        await self._progressive_send(result, ws_send)
        logger.info(f"Sent non-streamed tutor response ({len(result)} chars)")
        return result

    async def conduct_socratic_session_streaming(self, student_id: str, student_response: str, ws_send):
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
        self, student_id: str, student_response: str,
        session_id: str, ws_send,
    ) -> Dict[str, Any]:
        """Instance B: tutor pass + structured reflection pass."""
        if not self.student_mcp:
            await ws_send({"type": "error", "message": "Student MCP not available"})
            return {}

        history = self.get_conversation_history(student_id)
        self.append_to_conversation(student_id, "user", student_response)

        try:
            session_state = await self.student_mcp.get_active_session(student_id)

            # Handle onboarding (no profile yet or stage is onboarding)
            current_stage = (session_state or {}).get("current_stage", "onboarding")
            if not session_state or current_stage == "onboarding":
                return await self._handle_onboarding(
                    student_id, student_response, session_id, ws_send, history,
                )

            objective_id = session_state.get("active_objective_id", "")
            objective_text = ""

            # Resolve objective text
            if objective_id:
                try:
                    obj = await asyncio.to_thread(self._fetch_objective_by_id, objective_id)
                    if obj:
                        objective_text = obj.get("text", "")
                except Exception as e:
                    logger.warning(f"Failed to fetch objective text for {objective_id}: {e}")

            await self._restore_session_cache(session_id, objective_id)

            # Step 2: Check session content cache — run pipeline if needed
            if self._session_cache.needs_retrieval(session_id, objective_id):
                try:
                    teaching_plan, teaching_content, retrieval_bundle, extracted_concepts = (
                        await self._run_teaching_content_pipeline(
                            objective_text or student_response,
                            session_id, objective_id, ws_send,
                        )
                    )
                    # Cache results
                    self._session_cache.store(
                        session_id, objective_id, objective_text,
                        [], "", teaching_content,  # no RAG chunks or wcag_context in new pipeline
                        retrieval_bundle=retrieval_bundle,
                    )
                    self._session_cache.store_teaching_plan(
                        session_id, teaching_plan,
                        extracted_concepts=extracted_concepts,
                    )
                except TeachingPlanGenerationError as e:
                    logger.error(
                        "Teaching plan generation failed for objective=%s: %s",
                        objective_id,
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
                except Exception as e:
                    logger.error(f"Teaching content pipeline failed: {e}", exc_info=True)
                    # Fallback: try old retrieval path
                    logger.info("Falling back to RAG + WCAG MCP retrieval")
                    await ws_send({"type": "teaching_content_generating"})
                    rag_context, rag_chunks, wcag_context = await self.get_combined_context(
                        objective_text or student_response, history=history
                    )
                    teaching_content = rag_context
                    if wcag_context:
                        teaching_content = f"{rag_context}\n\n{wcag_context}" if rag_context else wcag_context
                    self._session_cache.store(
                        session_id, objective_id, objective_text,
                        rag_chunks, wcag_context, teaching_content,
                    )
                    await ws_send(
                        {
                            "type": "teaching_content",
                            "content": teaching_content,
                        }
                    )
                    try:
                        teaching_plan = await self._generate_teaching_plan(
                            objective_text, teaching_content
                        )
                        self._session_cache.store_teaching_plan(session_id, teaching_plan)
                    except TeachingPlanGenerationError as plan_err:
                        logger.error(
                            "Fallback teaching plan generation failed for objective=%s: %s",
                            objective_id,
                            plan_err,
                            exc_info=True,
                        )
                        await ws_send(
                            {
                                "type": "error",
                                "message": (
                                    "Teaching plan generation failed after retrieval "
                                    "fallback. Guided tutoring stopped before continuing "
                                    "without a validated plan."
                                ),
                            }
                        )
                        return {}
                await self._persist_session_cache(session_id)
            else:
                teaching_content = self._session_cache.get_teaching_content(session_id)

            teaching_plan = self._session_cache.get_teaching_plan(session_id)
            if not teaching_plan:
                logger.error(
                    "Guided session missing teaching plan after retrieval for session=%s objective=%s",
                    session_id,
                    objective_id,
                )
                await ws_send(
                    {
                        "type": "error",
                        "message": (
                            "No validated teaching plan is available for this objective. "
                            "Guided tutoring cannot continue."
                        ),
                    }
                )
                return {}
            lesson_state = self._session_cache.get_lesson_state(session_id)
            pacing_state = self._session_cache.get_pacing_state(session_id)
            bundle = await self._load_student_bundle(student_id, objective_id)
            misconception_state = self._session_cache.seed_misconception_state(
                session_id,
                bundle.get("misconceptions", []),
            )
            student_context = self._format_student_context(
                bundle.get("profile"),
                bundle.get("mastery", []),
                bundle.get("session"),
                bundle.get("misconceptions", []),
                bundle.get("learner_memory"),
                bundle.get("objective_memory"),
            )

            final_text = ""
            final_stage = current_stage
            stage_advanced = False
            assessment_metadata: Dict[str, Any] = {}

            if current_stage in ("mini_assessment", "final_assessment"):
                assessment_ctx = await self._get_assessment_context(objective_id)
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
                assessment_reflection = await self._run_assessment_reflector(
                    history=history,
                    student_response=student_response,
                    teaching_content=assessment_content,
                    student_context=student_context,
                    current_stage=current_stage,
                    active_objective=objective_text,
                    teaching_plan=teaching_plan,
                    lesson_state=lesson_state,
                    misconception_state=misconception_state,
                )
                assessment_misconception_events = self._coerce_misconception_events(
                    assessment_reflection,
                    default_priority=(
                        "must_address_now"
                        if not bool(assessment_reflection.get("is_correct", False))
                        else "normal"
                    ),
                )
                misconception_state = await self._apply_misconception_events(
                    student_id=student_id,
                    session_id=session_id,
                    objective_id=objective_id,
                    events=assessment_misconception_events,
                )
                await self._persist_session_cache(session_id)
                await self._apply_memory_patches(
                    student_id,
                    objective_id,
                    assessment_reflection.get("objective_memory_patch"),
                    assessment_reflection.get("learner_memory_patch"),
                    bundle=bundle,
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
                response_stage = (updated_session or {}).get(
                    "current_stage", current_stage
                )
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

                if (
                    isinstance(assessment_result, dict)
                    and assessment_result.get("mastery_level")
                ):
                    await ws_send(
                        {
                            "type": "mastery_update",
                            "objective_id": objective_id,
                            "objective_text": objective_text or objective_id,
                            "new_level": assessment_result.get("mastery_level", ""),
                        }
                    )

                refreshed_bundle = await self._load_student_bundle(
                    student_id, objective_id
                )
                refreshed_context = self._format_student_context(
                    refreshed_bundle.get("profile"),
                    refreshed_bundle.get("mastery", []),
                    refreshed_bundle.get("session"),
                    refreshed_bundle.get("misconceptions", []),
                    refreshed_bundle.get("learner_memory"),
                    refreshed_bundle.get("objective_memory"),
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
                            "The mini assessment is complete and the student passed. "
                            "Briefly reinforce the answer, then ask exactly one deeper "
                            "final-assessment question."
                        )
                    elif next_stage == "transition":
                        extra_messages.append(
                            "The assessment is complete and the objective is finished. "
                            "Celebrate, summarize the learning, and bridge naturally. "
                            "Do not ask another assessment question."
                        )
                    elif next_stage == "introduction":
                        extra_messages.append(
                            "The assessment showed important gaps. Explain the key issue "
                            "warmly and return to teaching this objective. Do not ask "
                            "another assessment question in this response."
                        )
                else:
                    extra_messages.append(
                        "The assessment is still in progress. Briefly explain why the "
                        "answer was correct or incorrect, then ask exactly one next "
                        "assessment question."
                    )

                await ws_send(
                    {
                        "type": "stage",
                        "stage": "composing",
                        "detail": f"Generating response ({response_stage})...",
                    }
                )
                tutor_messages = self._build_guided_tutor_messages(
                    student_response=student_response,
                    history=history,
                    teaching_content=assessment_content,
                    student_context=refreshed_context,
                    current_stage=response_stage,
                    active_objective=objective_text,
                    teaching_plan=teaching_plan,
                    lesson_state=lesson_state,
                    pacing_state=pacing_state,
                    misconception_state=misconception_state,
                    extra_system_messages=extra_messages,
                )
                final_text = await self._stream_response(tutor_messages, ws_send)
                self.append_to_conversation(student_id, "assistant", final_text)

                if response_stage == "transition":
                    transition_result = await self._advance_to_next_objective(
                        student_id, session_id, ws_send
                    )
                    if transition_result.get("advanced"):
                        final_stage = transition_result.get("stage", response_stage)

            else:
                await ws_send(
                    {
                        "type": "stage",
                        "stage": "analyzing",
                        "detail": "Analyzing your response...",
                    }
                )
                await ws_send({"type": "turn_analysis_generating"})
                turn_analysis = await self._run_turn_analyzer(
                    history=history,
                    student_response=student_response,
                    teaching_content=teaching_content,
                    student_context=student_context,
                    current_stage=current_stage,
                    active_objective=objective_text,
                    teaching_plan=teaching_plan,
                    lesson_state=lesson_state,
                    pacing_state=pacing_state,
                    misconception_state=misconception_state,
                )
                preview_misconception_state = self._session_cache.preview_misconception_state(
                    session_id,
                    self._coerce_misconception_events(
                        turn_analysis,
                        default_priority=(
                            "must_address_now"
                            if str(turn_analysis.get("teaching_move", "") or "").strip().lower()
                            == "repair"
                            else "normal"
                        ),
                    ),
                )
                preview_pacing_state = self._session_cache.preview_pacing_state(
                    session_id,
                    turn_analysis.get("pacing_signal"),
                )
                turn_analysis = self._enforce_turn_response_controls(
                    current_stage=current_stage,
                    analysis=turn_analysis,
                    lesson_state=lesson_state,
                    pacing_state=preview_pacing_state,
                    misconception_state=preview_misconception_state,
                )
                preview_pacing_state = self._session_cache.preview_pacing_state(
                    session_id,
                    turn_analysis.get("pacing_signal"),
                )
                await ws_send(
                    {
                        "type": "turn_analysis",
                        "analysis": safe_serialize(turn_analysis),
                        "display_analysis": self._render_turn_analysis_for_display(
                            turn_analysis
                        ),
                    }
                )

                analysis_result = await self._apply_turn_analysis_updates(
                    student_id=student_id,
                    session_id=session_id,
                    objective_id=objective_id,
                    objective_text=objective_text,
                    current_stage=current_stage,
                    analysis=turn_analysis,
                    bundle=bundle,
                    ws_send=ws_send,
                )
                final_stage = analysis_result.get("stage", current_stage)
                stage_advanced = analysis_result.get("stage_advanced", False)

                refreshed_bundle = await self._load_student_bundle(
                    student_id, objective_id
                )
                refreshed_context = self._format_student_context(
                    refreshed_bundle.get("profile"),
                    refreshed_bundle.get("mastery", []),
                    refreshed_bundle.get("session"),
                    refreshed_bundle.get("misconceptions", []),
                    refreshed_bundle.get("learner_memory"),
                    refreshed_bundle.get("objective_memory"),
                )
                lesson_state = self._session_cache.get_lesson_state(session_id)
                pacing_state = self._session_cache.get_pacing_state(session_id)
                misconception_state = self._session_cache.get_misconception_state(
                    session_id
                )

                await ws_send(
                    {
                        "type": "stage",
                        "stage": "composing",
                        "detail": f"Generating response ({final_stage})...",
                    }
                )
                tutor_messages = self._build_guided_tutor_messages(
                    student_response=student_response,
                    history=history,
                    teaching_content=teaching_content,
                    student_context=refreshed_context,
                    current_stage=final_stage,
                    active_objective=objective_text,
                    teaching_plan=teaching_plan,
                    lesson_state=lesson_state,
                    turn_analysis=turn_analysis,
                    pacing_state=pacing_state,
                    misconception_state=misconception_state,
                )
                final_text = await self._stream_response(tutor_messages, ws_send)
                self.append_to_conversation(student_id, "assistant", final_text)

            # Fire-and-forget RAG triple capture
            cached = self._session_cache.get(session_id)
            if cached and cached.get("rag_chunks"):
                try:
                    from ..eval.repository import EvalRepository
                    eval_repo = EvalRepository(db=self.db)
                    eval_repo.capture_rag_sample(
                        query=student_response,
                        retrieved_contexts=[c.get("content", "") for c in cached["rag_chunks"]],
                        response=final_text,
                        student_id=student_id, session_id=session_id,
                        intent="guided", instance="b",
                    )
                except Exception as e:
                    logger.warning(f"RAG capture failed (non-critical): {e}")

            metadata = {
                "session_id": session_id,
                "stage": final_stage,
                "stage_advanced": stage_advanced,
                "assessment": safe_serialize(assessment_metadata),
            }
            await ws_send({"type": "stream_end", "metadata": metadata})
            return metadata

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
                {"label": "None", "value": "none", "description": "I'm just getting started"},
                {"label": "Some awareness", "value": "awareness", "description": "I've heard of WCAG but haven't applied it"},
                {"label": "Working knowledge", "value": "working_knowledge", "description": "I've worked on accessible websites"},
                {"label": "Professional", "value": "professional", "description": "Deep a11y expertise or certification"},
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
        self, student_id: str, student_response: str,
        session_id: str, ws_send, history: List[Dict],
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
            logger.info(f"[ONBOARDING] Sending question #{prompt_idx + 1} of 3: {question_data['field']}")

            # Send as structured form question
            await ws_send({
                "type": "onboarding_question",
                "step": assistant_turns + 1,
                "total_steps": 3,
                **question_data,
            })
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
            session_id, student_id=student_id,
            stage="introduction", active_objective_id=objective_id, turns=0,
        )

        # Notify frontend of onboarding completion and stage change
        a11y_exposure = profile_data.get("a11y_exposure", "none")
        await ws_send({"type": "onboarding_complete", "profile": profile_data,
                       "first_objective": objective_text})
        await ws_send({"type": "stage_update", "stage": "introduction",
                       "objective": objective_text, "summary": ""})

        # Send level-appropriate objective introduction
        intro_text = self._OBJECTIVE_INTROS.get(a11y_exposure, self._OBJECTIVE_INTROS["none"])
        intro_msg = f"{intro_text}\n\nLet's begin!"
        await ws_send({"type": "stream_start"})
        await self._progressive_send(intro_msg, ws_send)
        await ws_send({"type": "stream_end", "metadata": {"stage": "introduction"}})
        self.append_to_conversation(student_id, "assistant", intro_msg)

        # Automatically start the first teaching turn — the tutor drives Instance B.
        await self.conduct_guided_session_streaming(
            student_id=student_id,
            student_response=f"I'm ready to learn about {objective_text}. Please introduce this topic.",
            session_id=session_id,
            ws_send=ws_send,
        )
        return {"stage": "introduction", "objective": objective_text}

    def _extract_onboarding_profile(
        self, history: List[Dict], final_response: str,
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
        "awareness": "I.B.1",
        "working_knowledge": "I.D.10",
        # "Distinguish between semantic HTML controls (e.g., <button>, <a>)
        #  and generic elements (e.g., <div>) in terms of built-in accessibility."
        # "Apply ARIA live regions to communicate dynamic content updates
        #  without moving keyboard focus"

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
        self, student_id: str, a11y_exposure: str,
    ) -> tuple:
        """Select the first objective based on the student's assessed level.

        Returns (objective_id, objective_text). Falls back to
        get_recommended_next_objective if the level-specific objective
        is not found or already mastered.
        """
        target_id = self._STARTING_OBJECTIVES.get(a11y_exposure, self._STARTING_OBJECTIVES["none"])
        target_text = self._STARTING_OBJECTIVE_TEXTS.get(a11y_exposure, "")

        # Prefer a direct text match when configured. The runtime DB stores UUID
        # primary keys, so curriculum codes like I.A.2 do not resolve directly.
        if target_text:
            try:
                obj = await asyncio.to_thread(self._fetch_objective_by_text, target_text)
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
            return next_obj.get("objective_id", ""), next_obj.get("objective_text", "web accessibility fundamentals")
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
        """Return True when the plan contains the required numbered sections."""
        section_pattern = re.compile(
            r'(?:^|\n)(?:##?\s*)?\d{1,2}\.\s*([a-z][\w_]*)\s*\n',
            re.IGNORECASE,
        )
        section_names = {
            match.group(1).strip().lower()
            for match in section_pattern.finditer(plan_text or "")
        }
        required = {
            "objective_text",
            "plain_language_goal",
            "mastery_definition",
            "concept_decomposition",
            "dependency_order",
        }
        return required.issubset(section_names)

    @staticmethod
    def _is_valid_legacy_teaching_plan(plan: Dict[str, Any]) -> bool:
        """Return True when the legacy JSON plan contains usable concept order data."""
        concepts = plan.get("concepts", []) if isinstance(plan, dict) else []
        recommended_order = (
            plan.get("recommended_order", []) if isinstance(plan, dict) else []
        )
        return bool(isinstance(concepts, list) and concepts and recommended_order)

    async def _generate_teaching_plan(
        self, objective_text: str, teaching_content: str = "",
    ):
        """Generate a structured teaching plan for an objective.

        Called once per objective (during first retrieval). The new
        instructional designer prompt outputs structured text with 17
        sections (not JSON). The raw text is stored in session cache
        and later compressed by format_teaching_plan() for the system
        prompt.

        Args:
            objective_text: The learning objective text.
            teaching_content: Optional teaching content for context
                (may be empty in the new pipeline where retrieval
                happens AFTER planning).

        Returns:
            str or dict: The teaching plan. New format returns str
            (structured text). Legacy format returns dict (JSON).
        """
        from .prompts import CONCEPT_DECOMPOSITION_PROMPT

        user_content = f"Objective: {objective_text}"
        if teaching_content:
            user_content += f"\n\nTeaching content:\n{teaching_content[:3000]}"

        messages = [
            {"role": "system", "content": CONCEPT_DECOMPOSITION_PROMPT},
            {"role": "user", "content": user_content},
        ]
        logger.info(
            "Generating teaching plan with deployment=%s effort=%s requested_tokens=%d",
            getattr(self.reasoning_client, "deployment", "unknown"),
            TEACHING_PLAN_REASONING_EFFORT,
            TEACHING_PLAN_MAX_COMPLETION_TOKENS,
        )
        response = await asyncio.to_thread(
            self.reasoning_client.chat,
            messages,
            0.3,
            TEACHING_PLAN_MAX_COMPLETION_TOKENS,
            TEACHING_PLAN_REASONING_EFFORT,
        )

        # Try JSON first (legacy format compatibility)
        try:
            plan = json.loads(response)
            if self._is_valid_legacy_teaching_plan(plan):
                logger.info(
                    f"Teaching plan generated (legacy JSON): "
                    f"{len(plan.get('concepts', []))} concepts, "
                    f"order: {plan.get('recommended_order', [])}"
                )
                return plan
            raise TeachingPlanGenerationError(
                "Planner returned legacy JSON without concepts or teaching order."
            )
        except (json.JSONDecodeError, TypeError):
            pass

        # New format: structured text with numbered sections
        if response and len(response) > 100 and self._is_valid_structured_teaching_plan(response):
            logger.info(
                f"Teaching plan generated (structured text): "
                f"{len(response)} chars"
            )
            return response

        response_preview = (response or "").strip().replace("\n", " ")
        if len(response_preview) > 180:
            response_preview = response_preview[:180] + "..."
        detail = "empty response"
        if response_preview:
            detail = f"invalid response preview={response_preview!r}"
        raise TeachingPlanGenerationError(
            "Teaching plan generation failed on gpt-5.4: "
            f"{detail}. Guided tutoring will not continue without a valid plan."
        )

    async def _extract_concept_order(self, teaching_plan: str) -> Optional[List[Dict[str, str]]]:
        """Use a lightweight LLM call to extract the ordered concept list
        from a free-text teaching plan.

        Returns a list of ``{"id": "...", "label": "..."}`` dicts in
        teaching order, or *None* if extraction fails.
        """
        if not teaching_plan or not isinstance(teaching_plan, str):
            return None

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a precise extraction tool. Given a teaching plan, "
                    "extract the ordered list of teachable concepts from the "
                    "dependency_order or concept_decomposition section.\n\n"
                    "Rules:\n"
                    "- Return ONLY the teachable concepts, in teaching order.\n"
                    "- Each concept should have a short snake_case 'id' and a "
                    "human-readable 'label'.\n"
                    "- Do NOT include dependency annotations, section headings, "
                    "or explanatory text.\n"
                    "- Merge closely related sub-concepts into one entry. For "
                    "example, 'roles require states' and 'required states must "
                    "be present' is one concept, not two.\n"
                    "- Do NOT include application/assessment tasks like "
                    "'diagnose violations' or 'justify choices' — those are "
                    "tested in assessment, not taught as concepts.\n"
                    "- Target 6-10 concepts. Fewer than 6 is too coarse, more "
                    "than 10 is over-decomposed.\n"
                    "- Output JSON: {\"concepts\": [{\"id\": \"...\", \"label\": \"...\"}]}"
                ),
            },
            {"role": "user", "content": teaching_plan},
        ]

        try:
            raw = await asyncio.to_thread(
                self.tutor_client.chat,
                messages,
                0.0,
                800,
                response_format={"type": "json_object"},
            )
            parsed = json.loads(raw)
            concepts = parsed.get("concepts", [])
            if concepts and isinstance(concepts, list):
                if len(concepts) > 10:
                    logger.info(
                        "Concept extraction (LLM): %d concepts, "
                        "capping to 10",
                        len(concepts),
                    )
                    concepts = concepts[:10]
                logger.info(
                    "Concept extraction (LLM): %d concepts from teaching plan",
                    len(concepts),
                )
                return concepts
        except (json.JSONDecodeError, TypeError, KeyError) as exc:
            logger.warning("Concept extraction LLM call failed to parse: %s", exc)
        except Exception as exc:
            logger.warning("Concept extraction LLM call failed: %s", exc)

        return None

    # ------------------------------------------------------------------
    # Plan-first teaching content pipeline (Instance B)
    # ------------------------------------------------------------------

    _AVAILABLE_TOOLS_TEXT = """
Available WCAG MCP tools:
1. list_principles() — Lists all 4 WCAG 2.2 principles with descriptions.
2. list_guidelines(principle?) — Lists guidelines, optionally filtered by principle (1-4).
3. list_success_criteria(level?, guideline?, principle?) — Lists SC with optional filters.
4. get_success_criteria_detail(ref_id) — Gets normative SC text only (~500-2000 chars).
5. get_criterion(ref_id) — Gets full SC details including Understanding docs (~5K-18K chars).
6. get_guideline(ref_id) — Gets full guideline details including all its SC.
7. search_wcag(query, level?) — Searches SC titles/descriptions by keyword.
8. get_criteria_by_level(level, include_lower?) — Gets all SC for a conformance level.
9. count_criteria(group_by) — Returns counts grouped by level, principle, or guideline.
10. get_full_criterion_context(ref_id) — Gets comprehensive SC context + techniques + glossary.
11. get_techniques_for_criterion(ref_id) — Gets all techniques for a specific SC.
12. get_technique(id) — Gets details for a specific technique by ID.
13. search_techniques(query) — Searches techniques by keyword.
14. get_glossary_term(term) — Gets official WCAG definition of a glossary term.
15. search_glossary(query) — Searches glossary terms by keyword.
16. list_glossary_terms() — Lists glossary terms available in WCAG.
17. whats_new_in_wcag22() — Lists all SC added in WCAG 2.2.
"""

    def _assess_retrieval_coverage(
        self, objective_text: str, teaching_plan: Any, results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        hits = [result for result in results if result.get("status") == "HIT"]
        hit_content = "\n".join(result.get("result", "") for result in hits).lower()
        context = f"{objective_text}\n{str(teaching_plan)[:3000]}".lower()

        require_rollup = any(
            marker in context
            for marker in (
                "conformance",
                "level aa",
                "level aaa",
                "level a",
                "criteria by level",
            )
        )
        require_techniques = any(
            marker in context
            for marker in (
                "technique",
                "techniques",
                "sufficient",
                "advisory",
                "informative",
                "normative",
                "requirement",
                "requirements",
            )
        )

        rollup_phrases = [
            "all level a and level aa",
            "all a and aa",
            "all a and all aa",
            "meet all level a",
            "all level a success criteria",
        ]
        technique_phrases = [
            "sufficient technique",
            "advisory technique",
            "informative",
            "techniques are not required",
            "sufficient and advisory",
        ]

        missing_checks = []
        if require_rollup and not any(phrase in hit_content for phrase in rollup_phrases):
            missing_checks.append("conformance_rollup_rule")
        if require_techniques and not any(phrase in hit_content for phrase in technique_phrases):
            missing_checks.append("techniques_vs_requirements")

        budget_chars = 20000

        return {
            "hit_count": len(hits),
            "hit_chars": sum(result.get("chars", 0) for result in hits),
            "missing_checks": missing_checks,
            "required_checks": {
                "conformance_rollup_rule": require_rollup,
                "techniques_vs_requirements": require_techniques,
            },
            "budget_chars": budget_chars,
        }

    @staticmethod
    def _build_retrieval_feedback_message(
        coverage: Dict[str, Any], remaining_calls: int, budget_chars: int,
    ) -> str:
        lines = [
            f"Research status: hits={coverage['hit_count']}, chars={coverage['hit_chars']}.",
        ]
        if coverage.get("missing_checks"):
            lines.append(
                "Still missing explicit evidence for: "
                + ", ".join(coverage["missing_checks"])
                + "."
            )
        else:
            lines.append(
                "No deterministic evidence checks are currently failing, but you may "
                "continue retrieving if the teaching plan still needs more support."
            )
        lines.append(
            f"Remaining budget: {remaining_calls} tool calls, about "
            f"{max(budget_chars - coverage['hit_chars'], 0)} chars."
        )
        lines.append(
            "Do not repeat prior tool calls. Prefer smaller, more targeted tools "
            "before deep criterion fetches. Stop only when you judge the teaching plan "
            "has enough supporting evidence."
        )
        return "\n".join(lines)

    @staticmethod
    def _annotate_retrieval_results(
        planned_calls: List[Dict[str, Any]], results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        annotated = []
        for planned_call, result in zip(planned_calls, results):
            enriched = dict(result)
            for field in ("tool_call_id", "round", "sequence", "source", "rationale"):
                value = planned_call.get(field)
                if value not in (None, ""):
                    enriched[field] = value
            annotated.append(enriched)
        return annotated

    def _extract_agentic_planned_calls(
        self,
        tool_calls: List[Dict[str, Any]],
        round_number: int,
        seen_calls: set,
        max_new_calls: int,
    ) -> List[Dict[str, Any]]:
        try:
            from ..wcag_mcp_client import normalize_tool_args
        except ModuleNotFoundError:
            normalize_tool_args = lambda _fn_name, fn_args: dict(fn_args)

        planned_calls = []
        for tool_call in tool_calls:
            if len(planned_calls) >= max_new_calls:
                break

            function = tool_call.get("function", {})
            fn_name = function.get("name", "")
            if not fn_name:
                continue

            args_text = function.get("arguments", "") or "{}"
            try:
                fn_args = json.loads(args_text)
            except (json.JSONDecodeError, TypeError):
                logger.warning(
                    "Guided retrieval: invalid tool arguments for %s: %s",
                    fn_name,
                    args_text,
                )
                continue

            # Strip the developer-facing `rationale` arg before the call
            # ever reaches normalisation or the MCP server. The string is
            # captured here so the retrieval loop can surface it to the UI.
            rationale = ""
            if isinstance(fn_args, dict) and "rationale" in fn_args:
                raw_rationale = fn_args.pop("rationale")
                if isinstance(raw_rationale, str):
                    rationale = raw_rationale.strip()

            normalized_args = normalize_tool_args(fn_name, fn_args)
            dedupe_key = (fn_name, json.dumps(normalized_args, sort_keys=True))
            if dedupe_key in seen_calls:
                logger.info(
                    "Guided retrieval: skipping duplicate call %s(%s)",
                    fn_name,
                    normalized_args,
                )
                continue
            seen_calls.add(dedupe_key)

            planned_calls.append(
                {
                    "tool_call_id": tool_call.get("id", ""),
                    "tool": fn_name,
                    "args": fn_args,
                    "rationale": rationale,
                    "category": "agentic",
                    "round": round_number,
                    "sequence": len(planned_calls) + 1,
                    "source": "guided_retrieval",
                }
            )

        return planned_calls

    @staticmethod
    def _build_tool_description_lookup(tool_definitions: List[Dict[str, Any]]) -> Dict[str, str]:
        """Map tool name → its `function.description` from an OpenAI tool spec list.

        Used to enrich `tool_activity` WS events so the frontend doesn't need to
        carry a duplicate copy of every tool's purpose.
        """
        lookup: Dict[str, str] = {}
        for tool in tool_definitions or []:
            fn = tool.get("function") or {}
            name = fn.get("name")
            description = fn.get("description") or ""
            if name:
                lookup[name] = " ".join(str(description).split())
        return lookup

    @staticmethod
    def _summarise_tool_result(result: Dict[str, Any]) -> str:
        """Build a short human label for a completed tool call result."""
        status = result.get("status") or "?"
        chars = result.get("chars")
        if status == "BLOCKED":
            return "blocked"
        if status == "ERROR":
            raw = result.get("result") or ""
            return f"error: {raw[:80]}"
        if isinstance(chars, int):
            label = f"{chars} chars"
            if status == "MISS":
                return f"miss ({label})"
            return label
        return str(status).lower()

    async def _run_agentic_retrieval(
        self, objective_text: str, teaching_plan: Any, ws_send,
    ) -> List[Dict[str, Any]]:
        from .prompts import build_guided_retrieval_agent_prompt

        try:
            from ..wcag_mcp_client import GUIDED_WCAG_TOOL_DEFINITIONS
        except ModuleNotFoundError:
            GUIDED_WCAG_TOOL_DEFINITIONS = getattr(self.wcag_mcp, "tool_definitions", [])

        if not self.wcag_mcp:
            logger.warning("Guided retrieval skipped: WCAG MCP client unavailable")
            return []

        tool_description_lookup = self._build_tool_description_lookup(
            GUIDED_WCAG_TOOL_DEFINITIONS
        )

        base_prompt = build_guided_retrieval_agent_prompt(
            objective_text=objective_text,
            teaching_plan=teaching_plan,
        )
        coverage = self._assess_retrieval_coverage(
            objective_text, teaching_plan, []
        )
        budget_chars = coverage["budget_chars"]
        max_rounds = 4
        max_tool_calls = 10

        messages = [
            {"role": "system", "content": base_prompt},
            {
                "role": "user",
                "content": (
                    "Research the WCAG evidence needed for this guided lesson. "
                    "Use tools until you judge the teaching plan has enough supporting "
                    "evidence, then stop. "
                    f"Current retrieval budget: about {budget_chars} characters."
                ),
            },
        ]

        all_results: List[Dict[str, Any]] = []
        seen_calls = set()
        total_tool_calls = 0

        for round_number in range(1, max_rounds + 1):
            remaining_calls = max_tool_calls - total_tool_calls
            if remaining_calls <= 0:
                logger.info("Guided retrieval: tool-call budget exhausted")
                break

            await ws_send(
                {
                    "type": "stage",
                    "stage": "searching",
                    "detail": f"Researching WCAG sources (round {round_number}/{max_rounds})...",
                }
            )
            response_msg = await self.reasoning_client.chat_with_tools(
                messages=messages,
                tools=GUIDED_WCAG_TOOL_DEFINITIONS,
                temperature=0.0,
                max_tokens=500,
                tool_choice="required" if round_number == 1 else "auto",
                reasoning_effort="medium",
            )
            tool_calls = response_msg.get("tool_calls") or []
            messages.append(response_msg)

            if not tool_calls:
                logger.info(
                    "Guided retrieval: model stopped after round %s with no tool calls",
                    round_number,
                )
                break

            planned_calls = self._extract_agentic_planned_calls(
                tool_calls=tool_calls,
                round_number=round_number,
                seen_calls=seen_calls,
                max_new_calls=remaining_calls,
            )
            if not planned_calls:
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "You repeated prior tool calls or produced invalid tool "
                            "arguments. Choose a different retrieval strategy or stop "
                            "if you judge the existing evidence is already enough."
                        ),
                    }
                )
                continue

            for planned_call in planned_calls:
                tool_name = planned_call.get("tool", "")
                await ws_send(
                    {
                        "type": "tool_activity",
                        "phase": "retrieval",
                        "round": planned_call.get("round", round_number),
                        "sequence": planned_call.get("sequence"),
                        "name": tool_name,
                        "params": planned_call.get("args") or {},
                        "description": tool_description_lookup.get(tool_name, ""),
                        "rationale": planned_call.get("rationale", ""),
                        "status": "calling",
                    }
                )

            round_results = await self.wcag_mcp.execute_planned_tool_calls(planned_calls)
            round_results = self._annotate_retrieval_results(planned_calls, round_results)
            all_results.extend(round_results)
            total_tool_calls += len(planned_calls)

            for planned_call, result in zip(planned_calls, round_results):
                tool_name = planned_call.get("tool", "")
                await ws_send(
                    {
                        "type": "tool_activity",
                        "phase": "retrieval",
                        "round": planned_call.get("round", round_number),
                        "sequence": planned_call.get("sequence"),
                        "name": tool_name,
                        "params": planned_call.get("args") or {},
                        "description": tool_description_lookup.get(tool_name, ""),
                        "rationale": planned_call.get("rationale", ""),
                        "status": "completed",
                        "result_status": result.get("status", ""),
                        "result_summary": self._summarise_tool_result(result),
                    }
                )

            for result in round_results:
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": result.get("tool_call_id", ""),
                        "content": result.get("result") or "No results found.",
                    }
                )

            coverage = self._assess_retrieval_coverage(
                objective_text, teaching_plan, all_results
            )
            logger.info(
                "Guided retrieval round %s: %s hits, %s chars, missing=%s",
                round_number,
                coverage["hit_count"],
                coverage["hit_chars"],
                coverage["missing_checks"],
            )
            if coverage["hit_chars"] >= budget_chars:
                logger.info("Guided retrieval: content budget reached")
                break

            messages.append(
                {
                    "role": "user",
                    "content": self._build_retrieval_feedback_message(
                        coverage=coverage,
                        remaining_calls=max_tool_calls - total_tool_calls,
                        budget_chars=budget_chars,
                    ),
                }
            )

        return all_results

    async def _run_teaching_content_pipeline(
        self, objective_text: str, session_id: str, objective_id: str, ws_send,
    ) -> tuple:
        """Run the plan-first teaching content pipeline for Instance B.

        Steps:
        1. Generate teaching plan from objective (LLM reasoning)
        2. In parallel:
           a. Run bounded agentic WCAG retrieval (LLM + tools)
           b. Extract ordered concept list (lightweight LLM, JSON mode)
        3. Evidence checks + deterministic fallbacks
        4. Build deterministic retrieval bundle + compact teaching pack
        5. Return (teaching_plan, teaching_content, retrieval_bundle,
           extracted_concepts)

        This replaces the old get_combined_context() + _generate_teaching_plan()
        flow for Instance B. Instance A now routes through GeneralChatService.
        """
        from .prompts import format_teaching_plan_for_display

        # Step 1: Teaching plan
        await ws_send({"type": "stage", "stage": "composing",
                       "detail": "Creating teaching plan..."})
        await ws_send({"type": "teaching_plan_generating"})
        teaching_plan = await self._generate_teaching_plan(objective_text)
        await ws_send(
            {
                "type": "teaching_plan",
                "plan": teaching_plan,
                "display_plan": format_teaching_plan_for_display(teaching_plan),
            }
        )
        logger.info(f"Pipeline step 1: teaching plan ({len(str(teaching_plan))} chars)")

        # Step 2: Agentic retrieval + concept extraction (parallel)
        await ws_send({"type": "stage", "stage": "searching",
                       "detail": "Researching WCAG content..."})
        await ws_send({"type": "teaching_content_generating"})
        retrieval_coro = self._run_agentic_retrieval(
            objective_text=objective_text,
            teaching_plan=teaching_plan,
            ws_send=ws_send,
        )
        # Lightweight LLM call on tutor_client (gpt-5.4-mini) to extract
        # the ordered concept list — runs in parallel with retrieval.
        extract_coro = self._extract_concept_order(teaching_plan)
        results, extracted_concepts = await asyncio.gather(
            retrieval_coro, extract_coro,
        )
        hits = [r for r in results if r["status"] == "HIT"]
        logger.info(
            f"Pipeline step 2: {len(hits)}/{len(results)} hits, "
            f"{sum(r['chars'] for r in hits)} chars"
        )

        # Step 3: Evidence checks + fallbacks
        await ws_send({"type": "stage", "stage": "searching",
                       "detail": "Validating evidence..."})
        retrieval_bundle = await self._build_retrieval_bundle(
            results,
            objective_text=objective_text,
            teaching_plan=teaching_plan,
        )
        teaching_content = self._render_retrieval_bundle(retrieval_bundle)
        logger.info(
            "Pipeline step 3: teaching pack (%s chars, %s raw hits)",
            len(teaching_content),
            len(retrieval_bundle.get("raw_hits", [])),
        )
        await ws_send(
            {
                "type": "teaching_content",
                "content": teaching_content,
            }
        )

        await ws_send({"type": "stage", "stage": "searching",
                       "detail": f"Teaching pack: {len(teaching_content)} chars from {len(hits)} sources"})

        return teaching_plan, teaching_content, retrieval_bundle, extracted_concepts

    async def _generate_retrieval_plan(
        self, objective_text: str, teaching_plan,
    ) -> str:
        """Generate a retrieval plan from the teaching plan (LLM call)."""
        from .prompts import RETRIEVAL_PLANNER_PROMPT

        plan_text = str(teaching_plan) if teaching_plan else ""
        messages = [
            {"role": "system", "content": RETRIEVAL_PLANNER_PROMPT},
            {"role": "user", "content": (
                f"LEARNING OBJECTIVE:\n{objective_text}\n\n"
                f"{self._AVAILABLE_TOOLS_TEXT}\n\n"
                f"TEACHING PLAN:\n{plan_text}"
            )},
        ]
        response = await asyncio.to_thread(
            self.reasoning_client.chat, messages, 0.3, 2500
        )
        return response or ""

    async def _extract_tool_calls(self, retrieval_plan: str) -> list:
        """Extract planned tool calls from retrieval plan as JSON (LLM call)."""
        from .prompts import TOOL_CALL_EXTRACTION_PROMPT

        messages = [
            {"role": "system", "content": TOOL_CALL_EXTRACTION_PROMPT},
            {"role": "user", "content": retrieval_plan},
        ]
        response = await asyncio.to_thread(
            self.reasoning_client.chat, messages, 0.0, 1500
        )

        # Parse JSON — strip markdown fences if present
        text = (response or "").strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(
                lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
            )

        try:
            calls = json.loads(text)
            if isinstance(calls, list):
                return calls
        except (json.JSONDecodeError, TypeError):
            logger.warning(f"Tool call extraction failed to parse JSON, using fallback")

        # Fallback: minimal safe calls
        return [
            {"tool": "list_principles", "args": {}, "category": "must_have"},
            {"tool": "list_guidelines", "args": {}, "category": "must_have"},
            {"tool": "get_glossary_term", "args": {"term": "conformance"}, "category": "must_have"},
        ]

    @staticmethod
    def _truncate_text(text: str, max_chars: int) -> str:
        text = (text or "").strip()
        if len(text) <= max_chars:
            return text
        return text[: max_chars - 3].rstrip() + "..."

    @staticmethod
    def _normalize_excerpt(text: str) -> str:
        cleaned = (text or "").replace("\t", " ")
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        cleaned = re.sub(r"[ ]{2,}", " ", cleaned)
        return cleaned.strip()

    @staticmethod
    def _first_markdown_heading(text: str) -> str:
        for line in (text or "").splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                return stripped.lstrip("#").strip()
        return ""

    @staticmethod
    def _parse_markdown_sections(text: str) -> Dict[str, str]:
        sections: Dict[str, List[str]] = {}
        current: Optional[str] = None
        for line in (text or "").splitlines():
            if line.startswith("## "):
                current = line[3:].strip()
                sections[current] = []
                continue
            if current is not None:
                sections[current].append(line)
        return {
            name: "\n".join(lines).strip()
            for name, lines in sections.items()
            if "\n".join(lines).strip()
        }

    def _add_bundle_item(
        self,
        bucket: List[Dict[str, Any]],
        *,
        title: str,
        content: str,
        result: Dict[str, Any],
    ) -> None:
        normalized_title = (title or "").strip()
        normalized_content = self._normalize_excerpt(content)
        if not normalized_content:
            return
        dedupe_key = (
            normalized_title.lower(),
            re.sub(r"\s+", " ", normalized_content).strip().lower(),
        )
        for existing in bucket:
            existing_key = (
                str(existing.get("title", "")).strip().lower(),
                re.sub(r"\s+", " ", str(existing.get("content", ""))).strip().lower(),
            )
            if existing_key == dedupe_key:
                return
        bucket.append(
            {
                "title": normalized_title,
                "content": normalized_content,
                "source_tool": result.get("tool", ""),
                "source_args": result.get("args", {}),
                "round": result.get("round"),
                "sequence": result.get("sequence"),
            }
        )

    def _extract_glossary_definition_item(self, result: Dict[str, Any]) -> Optional[Dict[str, str]]:
        text = result.get("result", "") or ""
        title = self._first_markdown_heading(text)
        body = text
        if "\n\n" in text:
            body = text.split("\n\n", 1)[1]
        body = body.split("\n\n[View in", 1)[0].strip()
        body = self._normalize_excerpt(body)
        if not body:
            return None
        return {"title": title or result.get("args", {}).get("term", "Glossary term"), "content": body}

    def _extract_success_criteria_detail_item(self, result: Dict[str, Any]) -> Optional[Dict[str, str]]:
        text = result.get("result", "") or ""
        title = self._first_markdown_heading(text) or result.get("args", {}).get("ref_id", "Success Criterion")
        sections = self._parse_markdown_sections(text)
        meta_lines = []
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("**Level:**") or stripped.startswith("**Principle:**") or stripped.startswith("**Guideline:**"):
                meta_lines.append(stripped)
        body_parts = []
        if meta_lines:
            body_parts.append(" | ".join(meta_lines))
        if sections.get("Success Criterion"):
            body_parts.append(sections["Success Criterion"])
        elif sections.get("Description"):
            body_parts.append(sections["Description"])
        content = self._normalize_excerpt("\n\n".join(body_parts))
        if not content:
            return None
        return {"title": title, "content": self._truncate_text(content, 1200)}

    def _extract_criterion_items(
        self, result: Dict[str, Any]
    ) -> Dict[str, Optional[Dict[str, str]]]:
        text = result.get("result", "") or ""
        title = self._first_markdown_heading(text) or result.get("args", {}).get("ref_id", "Success Criterion")
        sections = self._parse_markdown_sections(text)

        core_parts = []
        if sections.get("In Brief"):
            core_parts.append(sections["In Brief"])
        if sections.get("Description"):
            core_parts.append(sections["Description"])
        core_content = self._normalize_excerpt("\n\n".join(core_parts))

        intent_text = sections.get("Intent", "")
        intent_blocks = [
            self._normalize_excerpt(block)
            for block in re.split(r"\n\s*\n", intent_text)
            if self._normalize_excerpt(block)
        ]
        decision_blocks = [
            block for block in intent_blocks
            if any(
                marker in block.lower()
                for marker in (
                    "scope",
                    "criteria",
                    "change of context",
                    "without receiving focus",
                    "not considered",
                    "do not need",
                    "not within the scope",
                    "does not meet",
                )
            )
        ] or intent_blocks[:2]
        decision_content = self._normalize_excerpt("\n\n".join(decision_blocks[:3]))

        examples_text = sections.get("Examples", "")
        example_blocks = [
            self._normalize_excerpt(block)
            for block in re.split(r"\n###\s+Example\s+\d+\s*\n", examples_text)
            if self._normalize_excerpt(block)
        ]
        positive_blocks = []
        contrast_blocks = []
        risk_blocks = []
        for block in example_blocks:
            lowered = block.lower()
            if any(
                marker in lowered
                for marker in (
                    "too \"chatty\"",
                    "too chatty",
                    "unnecessarily interrupt",
                    "best practices but are not requirements",
                    "not to force authors",
                )
            ):
                risk_blocks.append(block)
                continue
            if any(
                marker in lowered
                for marker in (
                    "not status messages",
                    "do not meet the definition",
                    "not required",
                    "does not meet the definition",
                    "does not need",
                    "excepted from this success criterion",
                )
            ):
                contrast_blocks.append(block)
                continue
            positive_blocks.append(block)

        return {
            "core": {
                "title": title,
                "content": self._truncate_text(core_content, 1600),
            } if core_content else None,
            "decision": {
                "title": f"Decision Boundaries for {title}",
                "content": self._truncate_text(decision_content, 1800),
            } if decision_content else None,
            "examples": {
                "title": f"Examples from {title}",
                "content": self._truncate_text("\n\n".join(positive_blocks[:2]), 1800),
            } if positive_blocks else None,
            "contrast": {
                "title": f"Contrast Cases from {title}",
                "content": self._truncate_text("\n\n".join(contrast_blocks[:2]), 1500),
            } if contrast_blocks else None,
            "risks": {
                "title": f"Risks and Misuse Notes for {title}",
                "content": self._truncate_text("\n\n".join(risk_blocks[:2]), 1200),
            } if risk_blocks else None,
        }

    def _extract_technique_items(
        self, result: Dict[str, Any]
    ) -> Dict[str, Optional[Dict[str, str]]]:
        text = result.get("result", "") or ""
        title = self._first_markdown_heading(text) or "Technique guidance"
        sections = self._parse_markdown_sections(text)

        technique_parts = []
        if sections.get("Sufficient Techniques"):
            technique_parts.append("Sufficient techniques:\n" + sections["Sufficient Techniques"])
        if sections.get("Advisory Techniques"):
            technique_parts.append("Advisory techniques:\n" + sections["Advisory Techniques"])
        technique_content = self._normalize_excerpt("\n\n".join(technique_parts))

        risk_parts = []
        if sections.get("Failure Techniques"):
            risk_parts.append("Failure techniques:\n" + sections["Failure Techniques"])
        if "role=\"alert\" or aria-live=\"assertive\"" in text:
            risk_parts.append('Use of role="alert" or aria-live="assertive" on non-urgent content is a misuse risk.')
        risk_content = self._normalize_excerpt("\n\n".join(risk_parts))

        return {
            "techniques": {
                "title": title,
                "content": self._truncate_text(technique_content, 2200),
            } if technique_content else None,
            "risks": {
                "title": f"Failure and Misuse Notes for {title}",
                "content": self._truncate_text(risk_content, 1400),
            } if risk_content else None,
        }

    @staticmethod
    def _summarize_raw_hit(result: Dict[str, Any]) -> Dict[str, Any]:
        preview = (result.get("result") or "").strip()
        preview = preview[:240] + ("..." if len(preview) > 240 else "")
        return {
            "tool": result.get("tool", ""),
            "args": result.get("args", {}),
            "round": result.get("round"),
            "sequence": result.get("sequence"),
            "chars": result.get("chars", 0),
            "preview": preview,
        }

    async def _build_retrieval_bundle(
        self,
        results: list,
        objective_text: str = "",
        teaching_plan: Any = None,
    ) -> Dict[str, Any]:
        """Build a structured retrieval bundle from raw tool results.

        Runs deterministic evidence checks and targeted fallback tool calls
        if required evidence is still missing for the current objective.
        """
        coverage = self._assess_retrieval_coverage(
            objective_text, teaching_plan, results
        )

        fallback_calls = []
        if "conformance_rollup_rule" in coverage["missing_checks"]:
            logger.info("Evidence check: roll-up rule MISSING, running fallbacks")
            fallback_calls.extend([
                {"tool": "get_glossary_term", "args": {"term": "conformance"}, "category": "fallback"},
                {"tool": "get_criterion", "args": {"ref_id": "1.1.1"}, "category": "fallback"},
            ])
        if "techniques_vs_requirements" in coverage["missing_checks"]:
            logger.info("Evidence check: techniques distinction MISSING, running fallbacks")
            fallback_calls.extend([
                {"tool": "get_technique", "args": {"id": "H37"}, "category": "fallback"},
                {"tool": "get_glossary_term", "args": {"term": "accessibility supported"}, "category": "fallback"},
            ])

        working_results = list(results)
        if fallback_calls and self.wcag_mcp:
            fallback_results = await self.wcag_mcp.execute_planned_tool_calls(fallback_calls)
            working_results.extend(self._annotate_retrieval_results(fallback_calls, fallback_results))
            coverage = self._assess_retrieval_coverage(
                objective_text, teaching_plan, working_results
            )

        hits = []
        seen = set()
        for result in working_results:
            if result.get("status") != "HIT":
                continue
            key = (result.get("tool"), json.dumps(result.get("args", {}), sort_keys=True))
            if key in seen:
                continue
            seen.add(key)
            hits.append(result)

        bundle = {
            "version": 1,
            "objective_text": objective_text,
            "coverage": coverage,
            "sections": {
                "core_rules": [],
                "definitions": [],
                "decision_rules": [],
                "examples": [],
                "contrast_cases": [],
                "technique_patterns": [],
                "risks": [],
                "structural_context": [],
            },
            "raw_hits": [self._summarize_raw_hit(result) for result in hits],
        }

        glossary_terms = {
            str(result.get("args", {}).get("term", "")).strip().lower()
            for result in hits
            if result.get("tool") == "get_glossary_term"
        }

        for result in hits:
            tool = result.get("tool", "")
            args = result.get("args", {})

            if tool == "search_glossary":
                query = str(args.get("query", "")).strip().lower()
                if query in glossary_terms:
                    continue
                continue

            if tool == "get_glossary_term":
                item = self._extract_glossary_definition_item(result)
                if item:
                    self._add_bundle_item(
                        bundle["sections"]["definitions"],
                        title=item["title"],
                        content=item["content"],
                        result=result,
                    )
                continue

            if tool in {"list_principles", "list_guidelines", "list_success_criteria", "get_guideline", "get_criteria_by_level", "count_criteria"}:
                self._add_bundle_item(
                    bundle["sections"]["structural_context"],
                    title=self._first_markdown_heading(result.get("result", "")) or tool.replace("_", " ").title(),
                    content=self._truncate_text(result.get("result", ""), 1600),
                    result=result,
                )
                continue

            if tool == "get_success_criteria_detail":
                item = self._extract_success_criteria_detail_item(result)
                if item:
                    self._add_bundle_item(
                        bundle["sections"]["core_rules"],
                        title=item["title"],
                        content=item["content"],
                        result=result,
                    )
                continue

            if tool == "get_criterion":
                items = self._extract_criterion_items(result)
                if items.get("core"):
                    self._add_bundle_item(bundle["sections"]["core_rules"], result=result, **items["core"])
                if items.get("decision"):
                    self._add_bundle_item(bundle["sections"]["decision_rules"], result=result, **items["decision"])
                if items.get("examples"):
                    self._add_bundle_item(bundle["sections"]["examples"], result=result, **items["examples"])
                if items.get("contrast"):
                    self._add_bundle_item(bundle["sections"]["contrast_cases"], result=result, **items["contrast"])
                if items.get("risks"):
                    self._add_bundle_item(bundle["sections"]["risks"], result=result, **items["risks"])
                continue

            if tool == "get_full_criterion_context":
                item = self._extract_success_criteria_detail_item(result)
                if item:
                    self._add_bundle_item(
                        bundle["sections"]["core_rules"],
                        title=item["title"],
                        content=item["content"],
                        result=result,
                    )
                continue

            if tool == "get_techniques_for_criterion":
                items = self._extract_technique_items(result)
                if items.get("techniques"):
                    self._add_bundle_item(bundle["sections"]["technique_patterns"], result=result, **items["techniques"])
                if items.get("risks"):
                    self._add_bundle_item(bundle["sections"]["risks"], result=result, **items["risks"])
                continue

            if tool in {"get_technique", "search_techniques"}:
                self._add_bundle_item(
                    bundle["sections"]["technique_patterns"],
                    title=self._first_markdown_heading(result.get("result", "")) or str(args.get("id", args.get("query", "Technique"))),
                    content=self._truncate_text(result.get("result", ""), 1200),
                    result=result,
                )
                continue

            if tool == "search_wcag":
                self._add_bundle_item(
                    bundle["sections"]["core_rules"],
                    title=f"Search Results for {args.get('query', '')}".strip(),
                    content=self._truncate_text(result.get("result", ""), 1200),
                    result=result,
                )

        return bundle

    def _render_retrieval_bundle(self, bundle: Dict[str, Any]) -> str:
        """Render a compact tutor-facing teaching pack from a retrieval bundle."""
        if not bundle:
            return ""

        sections = bundle.get("sections", {})
        section_specs = [
            ("CORE FACTS", sections.get("core_rules", []), 2, 1400),
            ("DEFINITIONS", sections.get("definitions", []), 3, 600),
            ("DECISION BOUNDARIES", sections.get("decision_rules", []), 2, 1400),
            ("EXAMPLES", sections.get("examples", []), 2, 1400),
            ("CONTRAST CASES", sections.get("contrast_cases", []), 2, 1200),
            ("TECHNIQUE PATTERNS", sections.get("technique_patterns", []), 3, 1200),
            ("RISKS / MISUSE", sections.get("risks", []), 2, 900),
            ("STRUCTURE NOTES", sections.get("structural_context", []), 2, 1200),
        ]

        rendered_sections = []
        for heading, items, max_items, max_chars in section_specs:
            if not items:
                continue
            lines = [f"## {heading}"]
            for item in items[:max_items]:
                title = str(item.get("title", "")).strip()
                content = self._truncate_text(str(item.get("content", "")).strip(), max_chars)
                if title:
                    lines.append(f"### {title}")
                lines.append(content)
                lines.append("")
            rendered_sections.append("\n".join(lines).strip())

        return "\n\n".join(section for section in rendered_sections if section)

    async def _build_evidence_pack(
        self,
        results: list,
        objective_text: str = "",
        teaching_plan: Any = None,
    ) -> str:
        """Build a compact tutor-facing pack from deterministic bundle output."""
        bundle = await self._build_retrieval_bundle(
            results,
            objective_text=objective_text,
            teaching_plan=teaching_plan,
        )
        return self._render_retrieval_bundle(bundle)

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

            lines = ["ASSESSMENT REFERENCE QUESTIONS (use as templates, do NOT reuse verbatim):"]
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
