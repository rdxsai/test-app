#!/usr/bin/env python3
"""
Hybrid CrewAI Socratic System
(This is the final, corrected version with off-topic detection)
"""

import asyncio
import json
import logging
import os
import uuid
from dataclasses import asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from .interfaces import VectorStoreInterface

load_dotenv()

from .simple_system import (
    AzureAPIMClient,
    KnowledgeLevel,
    SessionPhase,
    SocraticTutoringEngine,
    StudentProfile,
)
from question_app.services.database import get_database_manager

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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
class HybridCrewAISocraticSystem:
    def __init__(
        self, azure_config: Dict[str, str], vector_store_service : VectorStoreInterface,
        db_manager=None, wcag_mcp_client=None, student_mcp_client=None
    ):
        self.client = AzureAPIMClient(
            endpoint=azure_config["endpoint"],
            deployment=azure_config["deployment_name"],
            api_key=azure_config["api_key"],
            api_version=azure_config.get("api_version", "2024-02-15-preview"),

        )
        self.vector_store = vector_store_service
        self.db = db_manager or get_database_manager()
        self.wcag_mcp = wcag_mcp_client
        self.student_mcp = student_mcp_client
        # Session content cache: teaching material cached per objective (zero-latency reuse)
        from .session_cache import SessionContentCache
        self._session_cache = SessionContentCache()
        self.memory_file = "conversation_memory.json"
        self.conversation_memory : Dict[str, List[Dict[str , str]]] = {}
        self._load_conversation_memory()
        self.coordinator_agent = CoordinatorAgent(self.client)
        self.code_analyzer = CodeAnalyzerAgent(self.client)
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
        return self.conversation_memory.get(student_id, [])

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

    def _build_guided_tutor_messages(
        self,
        student_response: str,
        history: Optional[List[Dict[str, str]]],
        teaching_content: str,
        student_context: str,
        current_stage: str,
        active_objective: str,
        teaching_plan: Any,
        extra_system_messages: Optional[List[str]] = None,
    ) -> List[Dict[str, str]]:
        """Build tutor-pass messages for guided learning."""
        from .prompts import build_instance_b_prompt

        system_prompt = build_instance_b_prompt(
            knowledge_context=teaching_content,
            student_context=student_context,
            current_stage=current_stage,
            active_objective=active_objective,
            teaching_plan=teaching_plan,
        )
        messages = [{"role": "system", "content": system_prompt}]
        for extra in extra_system_messages or []:
            if extra:
                messages.append({"role": "system", "content": extra})
        if history:
            messages.extend(history[-6:])
        messages.append({"role": "user", "content": student_response})
        return messages

    async def _run_guided_reflector(
        self,
        history: List[Dict[str, str]],
        student_response: str,
        tutor_response: str,
        teaching_content: str,
        student_context: str,
        current_stage: str,
        active_objective: str,
        teaching_plan: Any,
    ) -> Dict[str, Any]:
        """Run the structured reflection pass for a normal teaching turn."""
        from .prompts import build_guided_reflector_prompt

        prompt = build_guided_reflector_prompt(
            knowledge_context=teaching_content,
            student_context=student_context,
            current_stage=current_stage,
            active_objective=active_objective,
            teaching_plan=teaching_plan,
        )
        transcript = self._format_reflection_transcript(
            history, student_response, tutor_response
        )
        response = await asyncio.to_thread(
            self.client.chat,
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
                "stage_action": "stay",
                "target_stage": current_stage,
                "stage_reason": "",
                "mastery_signal": {
                    "should_update": False,
                    "level": "not_attempted",
                    "confidence": 0.0,
                    "evidence_summary": "",
                },
                "misconceptions_to_log": [],
                "misconceptions_to_resolve": [],
                "objective_memory_patch": {
                    "summary": "",
                    "demonstrated_skills": [],
                    "active_gaps": [],
                    "next_focus": "",
                },
                "learner_memory_patch": {
                    "summary": "",
                    "strengths": [],
                    "support_needs": [],
                    "tendencies": [],
                    "successful_strategies": [],
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
    ) -> Dict[str, Any]:
        """Run the structured reflection pass for an assessment answer."""
        from .prompts import build_assessment_reflector_prompt

        prompt = build_assessment_reflector_prompt(
            knowledge_context=teaching_content,
            student_context=student_context,
            current_stage=current_stage,
            active_objective=active_objective,
            teaching_plan=teaching_plan,
        )
        transcript = self._format_reflection_transcript(history, student_response)
        response = await asyncio.to_thread(
            self.client.chat,
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
                "misconceptions_to_log": [],
                "misconceptions_to_resolve": [],
                "objective_memory_patch": {
                    "summary": "",
                    "demonstrated_skills": [],
                    "active_gaps": [],
                    "next_focus": "",
                },
                "learner_memory_patch": {
                    "summary": "",
                    "strengths": [],
                    "support_needs": [],
                    "tendencies": [],
                    "successful_strategies": [],
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
            demonstrated_skills = self._merge_unique(
                existing_objective.get("demonstrated_skills", []),
                objective_memory_patch.get("demonstrated_skills", []),
            )
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
            strengths = self._merge_unique(
                existing_learner.get("strengths", []),
                learner_memory_patch.get("strengths", []),
            )
            support_needs = self._merge_unique(
                existing_learner.get("support_needs", []),
                learner_memory_patch.get("support_needs", []),
            )
            tendencies = self._merge_unique(
                existing_learner.get("tendencies", []),
                learner_memory_patch.get("tendencies", []),
            )
            successful_strategies = self._merge_unique(
                existing_learner.get("successful_strategies", []),
                learner_memory_patch.get("successful_strategies", []),
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

    async def _apply_reflection_updates(
        self,
        student_id: str,
        session_id: str,
        objective_id: str,
        objective_text: str,
        current_stage: str,
        reflection: Dict[str, Any],
        bundle: Optional[Dict[str, Any]],
        ws_send,
    ) -> Dict[str, Any]:
        """Apply deterministic state changes from the structured reflector."""
        result = {"stage": current_stage, "stage_advanced": False}

        await self.student_mcp.increment_turn_count(session_id)

        for misconception in reflection.get("misconceptions_to_log", []):
            await self.student_mcp.log_misconception(
                student_id, objective_id, misconception
            )

        for misconception in reflection.get("misconceptions_to_resolve", []):
            await self.student_mcp.resolve_misconception(
                student_id, objective_id, misconception
            )

        await self._apply_memory_patches(
            student_id,
            objective_id,
            reflection.get("objective_memory_patch"),
            reflection.get("learner_memory_patch"),
            bundle=bundle,
        )

        mastery_signal = reflection.get("mastery_signal") or {}
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

        stage_action = reflection.get("stage_action", "stay")
        target_stage = reflection.get("target_stage", current_stage)
        stage_reason = reflection.get("stage_reason", "")
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
    # Response message builder
    # ------------------------------------------------------------------

    def _build_response_messages(
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

    def _generate_response(self, student_response: str, context: str, history: Optional[List[Dict[str, str]]] = None, student_context: str = "") -> str:
        """
        Single LLM call: context + history + student query → tutor response.
        Used by the non-streaming POST endpoint.
        """
        messages = self._build_response_messages(student_response, context, history, student_context=student_context)
        try:
            return self.client.chat(messages, temperature=0.7, max_tokens=1000)
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return "I apologize, but I'm having trouble right now. Could you rephrase your question?"

    async def conduct_socratic_session(self, student_id : str , student_response : str) -> Dict[str, Any]:
            profile = self.db.load_student_profile(student_id)
            if not profile:
                raise ValueError(f"Student {student_id} not found")
            logger.info(f"Starting Session for {profile.name}")
            profile.total_sessions +=1 # Moved this here, was incrementing even on "START_SESSION"
            history = self.get_conversation_history(student_id)
            self.append_to_conversation(student_id, "user", student_response)

            try:
                intent = self.coordinator_agent.decide_intent(student_response, history=history)

                final_response = ""
                analysis = {}
                progress = {}
                rag_context = ""

                if intent == "conceptual_question":
                    logger.info("Executing conceptual workflow")
                    rag_context, _, _ = await self.get_combined_context(student_response, history=history)
                    final_response = self._generate_response(student_response, rag_context, history)

                elif intent == "code_analysis_request":
                    logger.info("Executing code analysis workflow")
                    code_analysis_result = self.code_analyzer.analyze_code_snippet(student_response)
                    search_query = student_response + "\n" + code_analysis_result
                    rag_context, _, _ = await self.get_combined_context(search_query, history=history)
                    combined = rag_context
                    if code_analysis_result:
                        combined = f"CODE ANALYSIS:\n{code_analysis_result}\n\n{rag_context}"
                    final_response = self._generate_response(student_response, combined, history)
                
                # --- === FIX 3: HANDLE THE NEW 'off_topic' INTENT === ---
                elif intent == "off_topic":
                    logger.info("Handling 'off_topic' intent. Skipping RAG and AI workflow.")
                    # We skip all AI agents and just give a default response
                    final_response = "That's an interesting question! However, I'm a Socratic tutor focused on web accessibility. Do you have a question related to that topic I can help with?"
                    analysis = {"response_type": "off_topic"}
                    progress = {} # No progress change
                # --- === END OF FIX 3 === ---

                logger.info(f"Triage session completed successfully for {profile.name}")
                
                # Save the updated profile (session count, etc.)
                self.db.save_student_profile(profile)
                self.append_to_conversation(student_id, "assistant", final_response)

                return {
                    "tutor_response" : final_response,
                    "student_profile" : asdict(profile),
                    "session_metadata" : {
                        "session_number" : profile.total_sessions,
                        "intent_executed" : intent,
                        "analysis" : safe_serialize(analysis),
                        "progress" : safe_serialize(progress),
                    },
                    "status" : "success"
                }
            except Exception as e:
                logger.error(f"Triage Session execution failed : {e}", exc_info=True)
                return{
                    "tutor_response" : "I apologize, but I'm having a small issue. Could you rephrase that?",
                    "error" : str(e) , "fallback" : True , "status" : "error"
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
        Stream LLM response via WebSocket with smooth drip-feed.

        Azure APIM buffers the full SSE response before forwarding, so tokens
        always arrive in a burst regardless of model.  We collect them, then
        drip-feed to the client for a smooth typing effect.

        Falls back to sync chat() + _progressive_send on failure.
        """
        full_response: List[str] = []

        try:
            async for token in self.client.chat_stream_async(messages, max_tokens=1000):
                full_response.append(token)
        except Exception as e:
            logger.error(f"Streaming failed: {e}, falling back to sync response")
            if not full_response:
                sync_response = await asyncio.to_thread(
                    self.client.chat, messages, 0.7, 1000
                )
                await ws_send({"type": "stream_start"})
                await self._progressive_send(sync_response, ws_send)
                return sync_response

        result = "".join(full_response)
        if not result:
            logger.warning("Stream returned empty response, falling back to sync call")
            sync_response = await asyncio.to_thread(
                self.client.chat, messages, 0.7, 1000
            )
            await ws_send({"type": "stream_start"})
            await self._progressive_send(sync_response, ws_send)
            return sync_response

        # Drip-feed tokens for smooth visual streaming
        await ws_send({"type": "stream_start"})
        for token in full_response:
            await ws_send({"type": "token", "content": token})
            await asyncio.sleep(0.008)

        logger.info(f"Streamed {len(full_response)} tokens ({len(result)} chars)")
        return result

    async def conduct_socratic_session_streaming(self, student_id: str, student_response: str, ws_send):
        """
        Streaming version of conduct_socratic_session. Sends stage updates
        and streams the final response word-by-word via ws_send callback.

        ws_send: async callable that sends a JSON-serializable dict to the client.
        """
        profile = self.db.load_student_profile(student_id)
        if not profile:
            raise ValueError(f"Student {student_id} not found")

        logger.info(f"Starting streaming session for {profile.name}")
        profile.total_sessions += 1
        history = self.get_conversation_history(student_id)
        self.append_to_conversation(student_id, "user", student_response)

        try:
            # Stage 0: Load student context from Student MCP (parallel with intent)
            student_context_task = asyncio.create_task(
                self._load_student_context(student_id)
            )

            # Stage 1: Classify intent
            await ws_send({"type": "stage", "stage": "classifying"})
            intent = await asyncio.to_thread(
                self.coordinator_agent.decide_intent, student_response, history
            )

            # Await student context (should be done by now — DB reads are fast)
            student_context = await student_context_task
            if student_context:
                logger.info(f"Student MCP context loaded ({len(student_context)} chars)")

            analysis = {}
            progress = {}
            rag_context = ""

            retrieved_chunks_data = []

            if intent == "conceptual_question":
                # Stage 2: Search (RAG + WCAG MCP concurrently)
                await ws_send({"type": "stage", "stage": "searching", "detail": "Searching quiz bank and WCAG guidelines..."})
                rag_context, retrieved_chunks_data, wcag_context = await self.get_combined_context(student_response, history=history)

                # Send retrieval stats
                n_chunks = len(retrieved_chunks_data) if retrieved_chunks_data else 0
                await ws_send({"type": "stage", "stage": "searching", "detail": f"Found {n_chunks} quiz matches{' + WCAG references' if wcag_context else ''}"})

                # Send retrieved chunks to frontend for display
                if retrieved_chunks_data:
                    await ws_send({
                        "type": "rag_chunks",
                        "chunks": [
                            {
                                "content": c.get("content", ""),
                                "topic": c.get("topic", ""),
                                "question_id": c.get("question_id", ""),
                                "distance": round(c.get("distance", 0), 3) if c.get("distance") is not None else None,
                                "rrf_score": round(c.get("rrf_score", 0), 4) if c.get("rrf_score") else 0,
                            }
                            for c in retrieved_chunks_data
                        ],
                    })

                # Send WCAG context to frontend
                if wcag_context:
                    await ws_send({"type": "wcag_context", "content": wcag_context})

                # Stage 3: Compose — stream response token-by-token
                await ws_send({"type": "stage", "stage": "composing", "detail": "Generating response..."})

                # Build messages for streaming (with student context injected)
                response_messages = self._build_response_messages(
                    student_response, rag_context, history, student_context=student_context
                )
                final_response = await self._stream_response(response_messages, ws_send)

            elif intent == "code_analysis_request":
                await ws_send({"type": "stage", "stage": "analyzing", "detail": "Analyzing code snippet..."})
                code_analysis_result = await asyncio.to_thread(
                    self.code_analyzer.analyze_code_snippet, student_response
                )
                search_query = student_response + "\n" + code_analysis_result

                await ws_send({"type": "stage", "stage": "searching", "detail": "Searching quiz bank and WCAG guidelines..."})
                rag_context, retrieved_chunks_data, wcag_context = await self.get_combined_context(search_query, history=history)

                n_chunks = len(retrieved_chunks_data) if retrieved_chunks_data else 0
                await ws_send({"type": "stage", "stage": "searching", "detail": f"Found {n_chunks} quiz matches{' + WCAG references' if wcag_context else ''}"})

                if retrieved_chunks_data:
                    await ws_send({
                        "type": "rag_chunks",
                        "chunks": [
                            {
                                "content": c.get("content", ""),
                                "topic": c.get("topic", ""),
                                "question_id": c.get("question_id", ""),
                                "distance": round(c.get("distance", 0), 3) if c.get("distance") is not None else None,
                                "rrf_score": round(c.get("rrf_score", 0), 4) if c.get("rrf_score") else 0,
                            }
                            for c in retrieved_chunks_data
                        ],
                    })

                if wcag_context:
                    await ws_send({"type": "wcag_context", "content": wcag_context})

                await ws_send({"type": "stage", "stage": "composing", "detail": "Generating response..."})
                combined = rag_context
                if code_analysis_result:
                    combined = f"CODE ANALYSIS:\n{code_analysis_result}\n\n{rag_context}"

                response_messages = self._build_response_messages(
                    student_response, combined, history, student_context=student_context
                )
                final_response = await self._stream_response(response_messages, ws_send)

            elif intent == "off_topic":
                await ws_send({"type": "stream_start"})
                final_response = "That's an interesting question! However, I'm a Socratic tutor focused on web accessibility. Do you have a question related to that topic I can help with?"
                await ws_send({"type": "token", "content": final_response})
                analysis = {"response_type": "off_topic"}
                progress = {}
            else:
                await ws_send({"type": "stream_start"})
                final_response = "Could you rephrase that? I'd like to help with your web accessibility question."
                await ws_send({"type": "token", "content": final_response})

            # Save profile and conversation
            self.db.save_student_profile(profile)
            self.append_to_conversation(student_id, "assistant", final_response)

            # Fire-and-forget RAG triple capture for evaluation pipeline
            if retrieved_chunks_data and intent != "off_topic":
                try:
                    from ..services.eval.repository import EvalRepository
                    eval_repo = EvalRepository(db=self.db)
                    eval_repo.capture_rag_sample(
                        query=student_response,
                        retrieved_contexts=[c.get("content", "") for c in retrieved_chunks_data],
                        response=final_response,
                        student_id=student_id, intent=intent, instance="a",
                    )
                except Exception as e:
                    logger.warning(f"RAG capture failed (non-critical): {e}")

            metadata = {
                "session_number": profile.total_sessions,
                "intent_executed": intent,
                "analysis": safe_serialize(analysis),
                "progress": safe_serialize(progress),
            }
            await ws_send({"type": "stream_end", "metadata": metadata})
            return metadata

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
        import os
        if os.getenv("GUIDED_MODE") == "legacy":
            return await self._legacy_guided_session_streaming(
                student_id, student_response, session_id, ws_send
            )

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

            # Step 2: Check session content cache — run pipeline if needed
            if self._session_cache.needs_retrieval(session_id, objective_id):
                try:
                    teaching_plan, evidence_pack = await self._run_teaching_content_pipeline(
                        objective_text or student_response,
                        session_id, objective_id, ws_send,
                    )
                    # Cache results
                    self._session_cache.store(
                        session_id, objective_id, objective_text,
                        [], "", evidence_pack,  # no RAG chunks or wcag_context in new pipeline
                    )
                    self._session_cache.store_teaching_plan(session_id, teaching_plan)
                    teaching_content = evidence_pack
                except Exception as e:
                    logger.error(f"Teaching content pipeline failed: {e}", exc_info=True)
                    # Fallback: try old retrieval path
                    logger.info("Falling back to RAG + WCAG MCP retrieval")
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
                    try:
                        teaching_plan = await self._generate_teaching_plan(
                            objective_text, teaching_content
                        )
                        self._session_cache.store_teaching_plan(session_id, teaching_plan)
                    except Exception as plan_err:
                        logger.warning(f"Fallback teaching plan failed: {plan_err}")
            else:
                teaching_content = self._session_cache.get_teaching_content(session_id)

            teaching_plan = self._session_cache.get_teaching_plan(session_id)
            bundle = await self._load_student_bundle(student_id, objective_id)
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
                )

                for misconception in assessment_reflection.get(
                    "misconceptions_to_log", []
                ):
                    await self.student_mcp.log_misconception(
                        student_id, objective_id, misconception
                    )
                for misconception in assessment_reflection.get(
                    "misconceptions_to_resolve", []
                ):
                    await self.student_mcp.resolve_misconception(
                        student_id, objective_id, misconception
                    )
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
                        "stage": "composing",
                        "detail": f"Generating response ({current_stage})...",
                    }
                )
                tutor_messages = self._build_guided_tutor_messages(
                    student_response=student_response,
                    history=history,
                    teaching_content=teaching_content,
                    student_context=student_context,
                    current_stage=current_stage,
                    active_objective=objective_text,
                    teaching_plan=teaching_plan,
                )
                final_text = await self._stream_response(tutor_messages, ws_send)
                self.append_to_conversation(student_id, "assistant", final_text)

                await ws_send(
                    {
                        "type": "stage",
                        "stage": "analyzing",
                        "detail": "Updating learning state...",
                    }
                )
                reflection = await self._run_guided_reflector(
                    history=history,
                    student_response=student_response,
                    tutor_response=final_text,
                    teaching_content=teaching_content,
                    student_context=student_context,
                    current_stage=current_stage,
                    active_objective=objective_text,
                    teaching_plan=teaching_plan,
                )
                reflection_result = await self._apply_reflection_updates(
                    student_id=student_id,
                    session_id=session_id,
                    objective_id=objective_id,
                    objective_text=objective_text,
                    current_stage=current_stage,
                    reflection=reflection,
                    bundle=bundle,
                    ws_send=ws_send,
                )
                final_stage = reflection_result.get("stage", current_stage)
                stage_advanced = reflection_result.get("stage_advanced", False)

            # Fire-and-forget RAG triple capture
            cached = self._session_cache.get(session_id)
            if cached and cached.get("rag_chunks"):
                try:
                    from ..services.eval.repository import EvalRepository
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

        except Exception as e:
            logger.error(f"Guided session failed: {e}", exc_info=True)
            await ws_send({"type": "error", "message": str(e)})
            return {}

    async def _legacy_guided_session_streaming(
        self, student_id: str, student_response: str,
        session_id: str, ws_send,
    ) -> Dict[str, Any]:
        """Legacy Instance B: single LLM call + eval JSON + stage machine.
        Kept as fallback via GUIDED_MODE=legacy env var.
        """
        # This is a stub — the full legacy code has been replaced.
        # If needed, it can be restored from git history.
        logger.warning("Legacy guided session mode — use GUIDED_MODE=legacy only for debugging")
        await ws_send({"type": "error", "message": "Legacy mode not available. Remove GUIDED_MODE env var."})
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

        # Level 1: some awareness / working knowledge — applied concepts
        "awareness": "I.D.10",
        "working_knowledge": "I.D.10",
        # "Apply ARIA live regions to communicate dynamic content updates
        #  without moving keyboard focus"

        # Level 2: professional — analysis-level challenges
        "professional": "I.H.2",
        # "Analyze how design elements such as headings, landmarks, and color
        #  contrast affect accessibility for diverse user groups"
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
            "You already have some familiarity with accessibility concepts, so let's "
            "build on that with something practical — **ARIA live regions**. These are "
            "how dynamic content updates get announced to screen reader users, and "
            "they're one of the trickier parts of accessibility to get right."
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

        # Verify the objective exists and get its text
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

    # ------------------------------------------------------------------
    # Assessment context (fetch quiz questions for an objective)
    # ------------------------------------------------------------------

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
        response = await asyncio.to_thread(
            self.client.chat, messages, 0.3, 2500  # increased from 800 for 17-section plan
        )

        # Try JSON first (legacy format compatibility)
        try:
            plan = json.loads(response)
            logger.info(
                f"Teaching plan generated (legacy JSON): "
                f"{len(plan.get('concepts', []))} concepts, "
                f"order: {plan.get('recommended_order', [])}"
            )
            return plan
        except (json.JSONDecodeError, TypeError):
            pass

        # New format: structured text with numbered sections
        if response and len(response) > 100:
            logger.info(
                f"Teaching plan generated (structured text): "
                f"{len(response)} chars"
            )
            return response

        # Fallback
        logger.warning("Teaching plan generation returned empty/short response, using fallback")
        return {
            "objective": objective_text,
            "concepts": [
                {"id": "c1", "name": "Core concept", "description": objective_text,
                 "prerequisites": [], "key_points": [], "status": "not_covered"}
            ],
            "recommended_order": ["c1"],
        }

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
15. whats_new_in_wcag22() — Lists all SC added in WCAG 2.2.
"""

    async def _run_teaching_content_pipeline(
        self, objective_text: str, session_id: str, objective_id: str, ws_send,
    ) -> tuple:
        """Run the plan-first teaching content pipeline for Instance B.

        Steps:
        1. Generate teaching plan from objective (LLM)
        2. Generate retrieval plan from teaching plan (LLM)
        3. Extract tool calls as JSON (LLM)
        4. Execute tool calls deterministically (MCP, no LLM)
        5. Evidence checks + fallbacks
        6. Return (teaching_plan, evidence_pack)

        This replaces the old get_combined_context() + _generate_teaching_plan()
        flow for Instance B. Instance A still uses the old flow.
        """
        # Step 1: Teaching plan
        await ws_send({"type": "stage", "stage": "composing",
                       "detail": "Creating teaching plan..."})
        teaching_plan = await self._generate_teaching_plan(objective_text)
        logger.info(f"Pipeline step 1: teaching plan ({len(str(teaching_plan))} chars)")

        # Step 2: Retrieval plan
        await ws_send({"type": "stage", "stage": "searching",
                       "detail": "Planning content retrieval..."})
        retrieval_plan = await self._generate_retrieval_plan(
            objective_text, teaching_plan
        )
        logger.info(f"Pipeline step 2: retrieval plan ({len(retrieval_plan)} chars)")

        # Step 3: Extract tool calls
        await ws_send({"type": "stage", "stage": "searching",
                       "detail": "Extracting tool calls..."})
        planned_calls = await self._extract_tool_calls(retrieval_plan)
        logger.info(f"Pipeline step 3: extracted {len(planned_calls)} tool calls")

        # Step 4: Execute deterministically
        await ws_send({"type": "stage", "stage": "searching",
                       "detail": f"Retrieving WCAG content ({len(planned_calls)} calls)..."})
        results = await self.wcag_mcp.execute_planned_tool_calls(planned_calls)
        hits = [r for r in results if r["status"] == "HIT"]
        logger.info(
            f"Pipeline step 4: {len(hits)}/{len(results)} hits, "
            f"{sum(r['chars'] for r in hits)} chars"
        )

        # Step 5: Evidence checks + fallbacks
        await ws_send({"type": "stage", "stage": "searching",
                       "detail": "Validating evidence..."})
        evidence_pack = await self._build_evidence_pack(results)
        logger.info(f"Pipeline step 5: evidence pack ({len(evidence_pack)} chars)")

        await ws_send({"type": "stage", "stage": "searching",
                       "detail": f"Evidence pack: {len(evidence_pack)} chars from {len(hits)} sources"})

        return teaching_plan, evidence_pack

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
            self.client.chat, messages, 0.3, 2500
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
            self.client.chat, messages, 0.0, 1500
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

    async def _build_evidence_pack(self, results: list) -> str:
        """Build the evidence pack from tool call results, with evidence checks.

        Checks for two critical evidence items:
        - Conformance roll-up rule (AA = all A + all AA)
        - Techniques vs requirements distinction

        Runs fallback tool calls if either is missing.
        """
        # Collect hit content
        hit_content = "\n".join(r["result"] for r in results if r["status"] == "HIT")

        # Evidence check: conformance roll-up rule
        rollup_phrases = [
            "all level a and level aa", "all a and aa", "satisfying all",
            "all a and all aa", "meet all level a",
            "all level a success criteria",
        ]
        has_rollup = any(p in hit_content.lower() for p in rollup_phrases)

        # Evidence check: techniques vs requirements
        technique_phrases = [
            "sufficient technique", "advisory technique", "informative",
            "techniques are not required", "sufficient and advisory",
        ]
        has_techniques = any(p in hit_content.lower() for p in technique_phrases)

        # Fallback calls if evidence is missing
        fallback_calls = []
        if not has_rollup:
            logger.info("Evidence check: roll-up rule MISSING, running fallbacks")
            fallback_calls.extend([
                {"tool": "get_glossary_term", "args": {"term": "conformance"}, "category": "fallback"},
                {"tool": "get_criterion", "args": {"ref_id": "1.1.1"}, "category": "fallback"},
            ])
        if not has_techniques:
            logger.info("Evidence check: techniques distinction MISSING, running fallbacks")
            fallback_calls.extend([
                {"tool": "get_technique", "args": {"id": "H37"}, "category": "fallback"},
                {"tool": "get_glossary_term", "args": {"term": "accessibility supported"}, "category": "fallback"},
            ])

        if fallback_calls and self.wcag_mcp:
            fallback_results = await self.wcag_mcp.execute_planned_tool_calls(fallback_calls)
            results.extend(fallback_results)

        # Build final evidence pack from all hits (deduplicated)
        seen = set()
        sections = []
        for r in results:
            if r["status"] != "HIT":
                continue
            key = (r["tool"], json.dumps(r["args"], sort_keys=True))
            if key in seen:
                continue
            seen.add(key)
            sections.append(r["result"])

        return "\n\n---\n\n".join(sections)

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
    # ------------------------------------------------------------------
    # Post-turn lifecycle check (application-managed stage transitions)
    # ------------------------------------------------------------------

    async def _post_turn_lifecycle_check(
        self, student_id: str, session_id: str,
        current_stage: str, objective_id: str, ws_send,
    ) -> Dict[str, Any]:
        """Application-side stage management. Runs after every agent turn.

        1. Increments turn count (always)
        2. Evaluates stage-specific advancement criteria
        3. Advances stage if criteria met
        4. Sends stage_update to frontend
        5. Invalidates cache on objective change

        The LLM does NOT manage stages — this method does.
        """
        result = {"advanced": False, "new_stage": current_stage}

        try:
            # 1. Increment turn count
            turn_result = await self.student_mcp.increment_turn_count(session_id)
            turns = (turn_result or {}).get("turns", 0)
            logger.info(f"[LIFECYCLE] stage={current_stage} turns={turns}")

            # 2. Get current mastery for advancement decisions
            mastery_records = await self.student_mcp.get_mastery_state(student_id)
            current_mastery = "not_attempted"
            for mr in (mastery_records or []):
                if mr.get("objective_id") == objective_id:
                    current_mastery = mr.get("mastery_level", "not_attempted")
                    break

            # 3. Evaluate stage criteria
            new_stage = None

            if current_stage == "introduction":
                if turns >= 3 and current_mastery in ("in_progress", "partial", "mastered"):
                    new_stage = "exploration"
                elif turns >= 5:  # hard cap
                    new_stage = "exploration"

            elif current_stage == "exploration":
                # Check teaching plan coverage
                plan = self._session_cache.get_teaching_plan(session_id)
                covered = 0
                total = 0
                if plan:
                    for c in plan.get("concepts", []):
                        total += 1
                        if c.get("status") in ("covered", "partially_covered"):
                            covered += 1
                majority_covered = total > 0 and covered >= total / 2

                if turns >= 4 and majority_covered:
                    new_stage = "readiness_check"
                elif turns >= 6:  # hard cap
                    new_stage = "readiness_check"

            elif current_stage == "readiness_check":
                # Always advance after 1 turn
                new_stage = "mini_assessment"

            elif current_stage == "transition":
                # Select next objective and start new cycle
                next_obj = await self.student_mcp.get_recommended_next_objective(student_id)
                if next_obj:
                    new_objective_id = next_obj.get("objective_id", "")
                    new_objective_text = next_obj.get("objective_text", "")
                    await self.student_mcp.update_session_state(
                        session_id, stage="introduction",
                        active_objective_id=new_objective_id,
                        turns=0,
                    )
                    self._session_cache.invalidate(session_id)
                    await ws_send({
                        "type": "stage_update",
                        "stage": "introduction",
                        "objective": new_objective_text,
                        "summary": f"Starting new objective: {new_objective_text}",
                    })
                    result.update(advanced=True, new_stage="introduction")
                    logger.info(f"[LIFECYCLE] transition → introduction (new objective: {new_objective_id})")
                return result

            # mini_assessment and final_assessment: handled by record_assessment_answer auto-transition

            # 4. Apply stage change if criteria met
            if new_stage and new_stage != current_stage:
                await self.student_mcp.update_session_state(
                    session_id, stage=new_stage,
                    stage_summary=f"Auto-advanced from {current_stage} after {turns} turns",
                )

                # Reset assessment progress when entering assessment
                if new_stage == "mini_assessment":
                    await self.student_mcp.update_session_state(
                        session_id,
                        assessment_progress='{"asked": 0, "correct": 0}',
                    )

                await ws_send({
                    "type": "stage_update",
                    "stage": new_stage,
                    "objective": objective_id,
                    "summary": f"Advanced from {current_stage} to {new_stage}",
                })

                if new_stage == "introduction" and current_stage != "introduction":
                    self._session_cache.invalidate(session_id)

                result.update(advanced=True, new_stage=new_stage)
                logger.info(f"[LIFECYCLE] {current_stage} → {new_stage} (turns={turns}, mastery={current_mastery})")

        except Exception as e:
            logger.warning(f"[LIFECYCLE] check failed (non-critical): {e}")

        return result

    # ------------------------------------------------------------------
    # Agent tool schemas + execution (Phase 3 agentic loop)
    # ------------------------------------------------------------------

    def _build_agent_tool_schemas(self) -> List[Dict]:
        """Build OpenAI function-calling tool definitions for the LLM agent.

        Exposes 8 Student MCP tools: 3 read + 5 write.
        NOT exposed: create_student_profile, get_student_profile,
        get_recommended_next_objective, save_session_summary,
        update_student_preferences, get_session_summary (application-managed).
        """
        return [
            # --- Read tools ---
            {"type": "function", "function": {
                "name": "get_mastery_state",
                "description": "CALL THIS before calling update_mastery or when deciding if the student is ready to advance stages. Returns current mastery levels for all objectives the student has engaged with.",
                "parameters": {"type": "object", "properties": {
                    "student_id": {"type": "string", "description": "The student's ID"},
                }, "required": ["student_id"]},
            }},
            {"type": "function", "function": {
                "name": "get_misconception_patterns",
                "description": "CALL THIS when the student says something incorrect or reveals a misunderstanding. Returns all unresolved misconceptions so you can check whether this error is already tracked before logging a new one.",
                "parameters": {"type": "object", "properties": {
                    "student_id": {"type": "string", "description": "The student's ID"},
                }, "required": ["student_id"]},
            }},
            # --- Write tools ---
            {"type": "function", "function": {
                "name": "log_misconception",
                "description": "CALL THIS whenever the student reveals a misconception that isn't already tracked. You MUST call this every time you detect a factual error — do not just address it in your response and move on. Format the text as: 'Student believes X (actual: Y from context)'. Deduplicates automatically.",
                "parameters": {"type": "object", "properties": {
                    "student_id": {"type": "string"},
                    "objective_id": {"type": "string"},
                    "misconception_text": {"type": "string", "description": "Format: 'Student believes X (actual: Y from context)'"},
                }, "required": ["student_id", "objective_id", "misconception_text"]},
            }},
            {"type": "function", "function": {
                "name": "resolve_misconception",
                "description": "CALL THIS when the student demonstrates they have corrected a previously logged misconception. If they now state the correct understanding of something they previously got wrong, resolve it.",
                "parameters": {"type": "object", "properties": {
                    "student_id": {"type": "string"},
                    "objective_id": {"type": "string"},
                    "misconception_text": {"type": "string", "description": "Text of the misconception to resolve (partial match OK)"},
                }, "required": ["student_id", "objective_id", "misconception_text"]},
            }},
            {"type": "function", "function": {
                "name": "update_mastery",
                "description": "CALL THIS after the student demonstrates understanding (or a clear lack of it). Every turn where the student shows they understand or misunderstand a concept, you should update their mastery. Include your confidence (0.0-1.0). System enforces stage-based caps automatically — just report what you observed. Never request 'mastered' or 'partial' — those are granted only by assessment scoring.",
                "parameters": {"type": "object", "properties": {
                    "student_id": {"type": "string"},
                    "objective_id": {"type": "string"},
                    "mastery_level": {"type": "string", "enum": ["not_attempted", "misconception", "in_progress"]},
                    "evidence_summary": {"type": "string", "description": "Brief description of what the student demonstrated"},
                    "confidence": {"type": "number", "description": "0.0-1.0 confidence in the assessment (threshold: 0.7)"},
                }, "required": ["student_id", "objective_id", "mastery_level", "confidence"]},
            }},
            {"type": "function", "function": {
                "name": "record_assessment_answer",
                "description": "CALL THIS during mini_assessment or final_assessment stages after evaluating each student answer as correct or incorrect. Auto-tracks progress (asked/correct counts), auto-computes pass/fail, auto-transitions stage when all questions are answered. Call once per assessment question.",
                "parameters": {"type": "object", "properties": {
                    "session_id": {"type": "string"},
                    "is_correct": {"type": "boolean", "description": "Whether the student's answer was correct"},
                }, "required": ["session_id", "is_correct"]},
            }},
        ]

    async def _execute_agent_tool(self, tool_call: Dict) -> Any:
        """Execute a tool call from the LLM and return the result.

        Routes OpenAI function-calling tool_calls to the correct
        StudentService method. Returns the result as a dict (or None).
        """
        fn_name = tool_call["function"]["name"]
        try:
            fn_args = json.loads(tool_call["function"]["arguments"])
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse tool args: {tool_call['function']['arguments']}")
            return {"error": "Invalid arguments"}

        logger.info(f"[AGENT] Tool call: {fn_name}({fn_args})")

        try:
            if fn_name == "get_mastery_state":
                return await self.student_mcp.get_mastery_state(fn_args["student_id"])
            elif fn_name == "get_misconception_patterns":
                return await self.student_mcp.get_misconception_patterns(fn_args["student_id"])
            elif fn_name == "log_misconception":
                return await self.student_mcp.log_misconception(
                    fn_args["student_id"], fn_args["objective_id"],
                    fn_args["misconception_text"],
                )
            elif fn_name == "resolve_misconception":
                return await self.student_mcp.resolve_misconception(
                    fn_args["student_id"], fn_args["objective_id"],
                    fn_args["misconception_text"],
                )
            elif fn_name == "update_mastery":
                return await self.student_mcp._call("update_mastery", fn_args)
            elif fn_name == "record_assessment_answer":
                return await self.student_mcp.record_assessment_answer(
                    fn_args["session_id"], fn_args["is_correct"],
                )
            else:
                logger.warning(f"[AGENT] Unknown tool: {fn_name}")
                return {"error": f"Unknown tool: {fn_name}"}
        except Exception as e:
            logger.error(f"[AGENT] Tool execution failed: {fn_name}: {e}")
            return {"error": str(e)}

    # ==================================================================
    # End of Instance B methods
    # ==================================================================
    # ==================================================================

    def _update_student_profile(
        self,
        profile: StudentProfile,
        analysis: Dict[str, Any],
        progress: Dict[str, Any],
    ):
        # (This method is unchanged)
        if "new_consecutive_correct" in progress:
            profile.consecutive_correct = progress["new_consecutive_correct"]
        if progress.get("advancement_ready", False):
            current_level = profile.knowledge_level
            if current_level == KnowledgeLevel.RECALL:
                profile.knowledge_level = KnowledgeLevel.UNDERSTANDING
                profile.understanding_progression.append(
                    f"Advanced to Understanding at session {profile.total_sessions}"
                )
            elif current_level == KnowledgeLevel.UNDERSTANDING:
                profile.knowledge_level = KnowledgeLevel.APPLICATION
                profile.understanding_progression.append(
                    f"Advanced to Application at session {profile.total_sessions}"
                )
            elif current_level == KnowledgeLevel.APPLICATION:
                profile.knowledge_level = KnowledgeLevel.ANALYSIS
                profile.understanding_progression.append(
                    f"Advanced to Analysis at session {profile.total_sessions}"
                )
            profile.consecutive_correct = 0 
        if "recommended_phase" in progress:
            new_phase = progress["recommended_phase"]
            if new_phase != profile.session_phase.value:
                profile.session_phase = SessionPhase(new_phase)
        engagement = analysis.get("engagement_indicators", "medium")
        profile.engagement_level = engagement
        if analysis.get("misconceptions"):
            for misconception in analysis["misconceptions"]:
                if misconception not in profile.misconceptions:
                    profile.misconceptions.append(misconception)
        if analysis.get("strengths"):
            for strength in analysis["strengths"]:
                if strength not in profile.strengths:
                    profile.strengths.append(strength)
        if analysis.get("warning_signs"):
            for warning_sign in analysis["warning_signs"]:
                profile.warning_signs.append(warning_sign)
        profile.updated_at = datetime.now().isoformat()

    def list_students(self) -> List[Dict]:
        # (This method is unchanged)
        return self.db.list_all_students()

    def get_student_analytics(self, student_id: str) -> Dict[str, Any]:
        # (This method is unchanged)
        profile = self.db.load_student_profile(student_id)
        if not profile:
            return {"error": "Student not found"}
        return {
            "student_info": {
                "id": profile.id, "name": profile.name, "topic": profile.current_topic,
                "knowledge_level": profile.knowledge_level.value, "session_phase": profile.session_phase.value,
                "total_sessions": profile.total_sessions, "engagement_level": profile.engagement_level,
            },
            "progress_metrics": {
                "consecutive_correct": profile.consecutive_correct,
                "understanding_progression": profile.understanding_progression,
                "misconceptions": profile.misconceptions, "strengths": profile.strengths,
                "warning_signs": profile.warning_signs,
            },
        }
