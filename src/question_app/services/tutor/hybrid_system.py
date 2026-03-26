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


# (All other Agent classes are unchanged)
class ResponseAnalystAgent(SocraticAgent):
    def __init__(self, client: AzureAPIMClient):
        super().__init__(
            role="Socratic Response Analyst",
            goal="Analyze student responses to determine understanding level and appropriate Socratic interventions",
            backstory="""You are an expert at analyzing student responses using the Socratic method. 
            You determine response types (correct/partially_correct/incorrect/dont_know/frustrated),
            assess understanding levels (recall/understanding/application/analysis/synthesis),
            identify misconceptions and learning gaps, and recommend appropriate explanations and clarifications.""",
            client=client,
        )
    def analyze_response(
        self, student_response: str, profile: StudentProfile, context : str = "", history : Optional[List[Dict[str , str]]] = None
    ) -> Dict[str, Any]:
        task_description = f"""Analyze this student response following Socratic method principles:
        Student Profile:
        - Name: {profile.name}
        - Topic: {profile.current_topic}
        - Knowledge Level: {profile.knowledge_level.value}
        - Session Phase: {profile.session_phase.value}
        - Consecutive Correct: {profile.consecutive_correct}
        Student Response: "{student_response}"
        Return a JSON object with this exact structure:
        {{
            "response_type": "correct|partially_correct|incorrect|dont_know|frustrated",
            "understanding_level": "recall|understanding|application|analysis|synthesis",
            "reasoning_quality": "high|medium|low",
            "misconceptions": ["list of identified misconceptions"],
            "strengths": ["list of demonstrated strengths"],
            "warning_signs": ["list of concerns"],
            "intervention_needed": "probe_deeper|return_to_familiar|simplify|encourage|none",
            "engagement_indicators": "high|medium|low"
        }}"""
        try:
            response = self.execute_task(task_description , context=context, history=history)
            if hasattr(response, "__class__") and "MagicMock" in str(response.__class__):
                return {
                    "response_type": "partially_correct", "understanding_level": profile.knowledge_level.value,
                    "reasoning_quality": "medium", "misconceptions": [], "strengths": ["shows engagement"],
                    "warning_signs": [], "intervention_needed": "probe_deeper", "engagement_indicators": "medium",
                }
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return {
                    "response_type": "partially_correct", "understanding_level": profile.knowledge_level.value,
                    "reasoning_quality": "medium", "misconceptions": [], "strengths": ["shows engagement"],
                    "warning_signs": [], "intervention_needed": "probe_deeper", "engagement_indicators": "medium",
                }
        except Exception as e:
            logger.error(f"Response analysis failed: {e}")
            return {
                "response_type": "partially_correct", "understanding_level": profile.knowledge_level.value,
                "reasoning_quality": "medium", "misconceptions": [], "strengths": ["shows engagement"],
                "warning_signs": [], "intervention_needed": "probe_deeper", "engagement_indicators": "medium",
            }

class ProgressTrackerAgent(SocraticAgent):
    def __init__(self, client: AzureAPIMClient):
        super().__init__(
            role="Learning Progress Tracker",
            goal="Monitor student progression through knowledge levels and recommend session phase transitions",
            backstory="""You track student learning progression through educational taxonomy levels
            and monitor advancement criteria. You determine when students are ready to advance
            knowledge levels (3 consecutive correct responses) and when to transition session phases.
            You identify intervention needs and maintain optimal challenge levels.""",
            client=client,
        )
    def assess_progress(
        self, analysis: Dict[str, Any], profile: StudentProfile, context : str = "", history:Optional[List[Dict[str , str]]] = None
    ) -> Dict[str, Any]:
        task_description = f"""Assess learning progress based on response analysis:
        Current Student State:
        - Knowledge Level: {profile.knowledge_level.value}
        - Session Phase: {profile.session_phase.value}
        - Consecutive Correct: {profile.consecutive_correct}
        - Total Sessions: {profile.total_sessions}
        Response Analysis: {json.dumps(analysis, indent=2)}
        Determine:
        1. Should consecutive correct count be incremented?
        2. Is student ready to advance knowledge level? (3+ consecutive correct)
        3. Should session phase change?
        4. Any interventions needed?
        Return JSON with advancement recommendations."""
        try:
            response = self.execute_task(task_description , context=context, history=history)
            response_correct = analysis.get("response_type") in ["correct", "partially_correct"]
            new_consecutive = profile.consecutive_correct + 1 if response_correct else 0
            advancement_ready = new_consecutive >= 3
            progress_analysis = response
            if hasattr(response, "__class__") and "MagicMock" in str(response.__class__):
                progress_analysis = "Progress analysis completed"
            return {
                "advancement_ready": advancement_ready,
                "new_consecutive_correct": new_consecutive,
                "recommended_phase": self._recommend_phase(profile, advancement_ready),
                "intervention_needed": analysis.get("intervention_needed", "none"),
                "progress_analysis": progress_analysis,
            }
        except Exception as e:
            logger.error(f"Progress tracking failed: {e}")
            return {
                "advancement_ready": False, "new_consecutive_correct": profile.consecutive_correct,
                "recommended_phase": profile.session_phase.value,
                "intervention_needed": "none", "progress_analysis": "Progress tracking completed",
            }
    def _recommend_phase(self, profile: StudentProfile, advancement_ready: bool) -> str:
        if profile.total_sessions < 3:
            return SessionPhase.OPENING.value
        elif advancement_ready or profile.knowledge_level.value in ["application", "analysis"]:
            return SessionPhase.CONSOLIDATION.value
        else:
            return SessionPhase.DEVELOPMENT.value

class QuestionGeneratorAgent(SocraticAgent):
    def __init__(self, client: AzureAPIMClient):
        super().__init__(
            role="Master Socratic Questioner",
            goal="Generate strategic Socratic questions that guide students to discover knowledge",
            backstory="""You are a master of strategic Socratic questioning. You craft questions that:
            1. Clear definations and explanations.
            2. Practical examples when helpful.
            3. Step by step breakdown for complex topics.
            4. Direct answers to questions without unnecessary explanations.
            5. References to WCAG guidelines when relevant
            You communicate in a friendly but professional tone, ensuring the student understands the concept fully.""",
            client=client,
        )
    def generate_questions(
        self,
        analysis: Dict[str, Any],
        progress: Dict[str, Any],
        profile: StudentProfile,
        student_response: str,
        context : str = "",
        history:Optional[List[Dict[str, str]]] = None
    ) -> str:
        task_description = f"""Provide a clear, direct answer based on the student's question:
        Student Context:
        - Topic: {profile.current_topic}
        - Knowledge Level: {profile.knowledge_level.value}
        - Session Phase: {profile.session_phase.value}
        - Response: "{student_response}"
        Response Analysis:
        - Type: {analysis.get('response_type', 'unknown')}
        - Understanding Level: {analysis.get('understanding_level', 'recall')}
        - Intervention Needed: {analysis.get('intervention_needed', 'none')}
        Progress Assessment:
        - Advancement Ready: {progress.get('advancement_ready', False)}
        - Recommended Phase: {progress.get('recommended_phase', 'opening')}
        Generate 1-2 strategic Socratic questions that:
        1. Answer the question directly and clearly
        2. Use the knowledge base context provided above
        3. Adjust complexity based on their knowledge level ({profile.knowledge_level.value})
        4. Include practical examples if helpful
        5.  Keep the response concise but complete (2-4 sentences typically)
        6. If they're incorrect, gently correct and explain the right answer
        IMPORTANT: Provide the answer directly. Do not ask questions back."""
        try:
            response = self.execute_task(task_description , context = context, history=history)
            if hasattr(response, "__class__") and "MagicMock" in str(response.__class__):
                return "What makes you think that? Can you tell me more about your reasoning?"
            return response
        except Exception as e:
            logger.error(f"Question generation failed: {e}")
            return "What makes you think that? Can you tell me more about your reasoning?"

class SessionOrchestratorAgent(SocraticAgent):
    def __init__(self, client: AzureAPIMClient):
        super().__init__(
            role="Socratic Session Orchestrator",
            goal="Coordinate complete Socratic dialogue flow and maintain optimal learning conditions",
            backstory="""You coordinate tutoring sessions by synthesizing insights from
        response analysis and expert answers. You create clear, friendly responses that
        directly address the student's questions while maintaining engagement and understanding.""",
            client=client,
        )
    def orchestrate_response(
        self,
        analysis: Dict[str, Any],
        progress: Dict[str, Any],
        questions: str,
        profile: StudentProfile,
        context : str = "",
        history:Optional[List[Dict[str, str]]] = None
    ) -> str:
        task_description = f"""Create a complete tutoring response by synthesizing:

Response Analysis: {json.dumps(analysis, indent=2)}
Progress Assessment: {json.dumps(progress, indent=2)}
Expert Answer: {questions}  # ← This now contains the answer, not questions

Student Context:
- Name: {profile.name}
- Topic: {profile.current_topic}
- Knowledge Level: {profile.knowledge_level.value}
- Engagement: {analysis.get('engagement_indicators', 'medium')}

Create a response that:
1. Provides the answer clearly and directly
2. Uses a friendly, encouraging tone
3. Acknowledges their question or attempt
4. Includes the expert answer seamlessly
5. Keeps the response natural and conversational

IMPORTANT: Provide direct answers. Do not end with questions."""
        try:
            response = self.execute_task(task_description , context = context, history=history)
            if hasattr(response, "__class__") and "MagicMock" in str(response.__class__):
                return questions 
            return response
        except Exception as e:
            logger.error(f"Session orchestration failed: {e}")
            return questions

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
        # Stage machine: enforces transitions and thresholds for Instance B
        if student_mcp_client:
            from .stage_machine import StageMachine
            self._stage_machine = StageMachine(student_mcp_client)
        else:
            self._stage_machine = None
        self.memory_file = "conversation_memory.json"
        self.conversation_memory : Dict[str, List[Dict[str , str]]] = {}
        self._load_conversation_memory()
        self.coordinator_agent = CoordinatorAgent(self.client)
        self.response_analyst = ResponseAnalystAgent(self.client)
        self.progress_tracker = ProgressTrackerAgent(self.client)
        self.code_analyzer = CodeAnalyzerAgent(self.client)
        self.question_generator = QuestionGeneratorAgent(self.client)
        self.session_orchestrator = SessionOrchestratorAgent(self.client)
        self.analyst_agent = self.response_analyst
        self.progress_agent = self.progress_tracker
        self.questioner_agent = self.question_generator
        self.orchestrator_agent = self.session_orchestrator
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
        if initial_assessment:
            logger.info(f"Conducting initial assessment for {name}")
            try:
                analysis = self.response_analyst.analyze_response(
                    initial_assessment, profile, context="" 
                )
                if "understanding" in str(analysis).lower():
                    profile.knowledge_level = KnowledgeLevel.UNDERSTANDING
                logger.info(f"Initial assessment completed for {name}")
            except Exception as e:
                logger.error(f"Initial assessment failed: {e}")
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

    async def _load_student_context(self, student_id: str) -> str:
        """Load student state from the Student MCP server and format for the LLM.

        Calls read tools in parallel: profile, mastery, active session,
        misconceptions. Returns a formatted text block for the system prompt,
        or empty string if the Student MCP client is not available.
        """
        if not self.student_mcp:
            return ""

        try:
            profile, mastery, session, misconceptions = await asyncio.gather(
                self.student_mcp.get_profile(student_id),
                self.student_mcp.get_mastery_state(student_id),
                self.student_mcp.get_active_session(student_id),
                self.student_mcp.get_misconception_patterns(student_id),
            )
            return self._format_student_context(profile, mastery, session, misconceptions)
        except Exception as e:
            logger.warning(f"Failed to load student context from MCP: {e}")
            return ""

    def _format_student_context(
        self, profile: Optional[Dict], mastery: List[Dict],
        session: Optional[Dict], misconceptions: List[Dict],
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

        if not parts:
            return ""

        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Eval JSON parser (Instance B)
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_eval_json(response: str) -> tuple:
        """Extract conversational text and eval JSON from an Instance B response.

        The LLM outputs the Socratic response first, then a ```json block
        containing the structured evaluation. This method splits them apart.

        Returns:
            (conversational_text, eval_dict) if JSON found and valid
            (response, None) if no JSON block or parse error
        """
        import re

        # Match ```json ... ``` block (possibly with whitespace around it)
        pattern = r"```json\s*\n?(.*?)\n?\s*```"
        match = re.search(pattern, response, re.DOTALL)

        if not match:
            logger.debug("No eval JSON block found in response")
            return response.strip(), None

        json_str = match.group(1).strip()
        # Everything before the JSON block is the conversational response
        conversational = response[:match.start()].strip()

        try:
            eval_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse eval JSON: {e}")
            return conversational or response.strip(), None

        # Validate expected keys
        expected_keys = {"detected_state", "response_mode", "stage_recommendation", "confidence"}
        if not expected_keys.issubset(eval_data.keys()):
            missing = expected_keys - eval_data.keys()
            logger.warning(f"Eval JSON missing keys: {missing}")
            # Still return what we have — partial data is better than none
            return conversational, eval_data

        return conversational, eval_data

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
        """Instance B: Stage-aware guided learning with eval-driven state updates.

        Per-turn flow:
        1. Load student context from MCP (profile, mastery, session, misconceptions)
        2. Check session content cache — hit → skip retrieval, miss → retrieve + cache
        3. Build Instance B prompt (stage-aware, includes eval JSON schema)
        4. Single LLM call → Socratic response + eval JSON
        5. Stream conversational text to client (strip eval JSON before streaming)
        6. Parse eval JSON from full response
        7. Stage machine processes eval → MCP write-backs
        8. Send stage/mastery updates to client via WebSocket
        """
        if not self.student_mcp:
            await ws_send({"type": "error", "message": "Student MCP not available"})
            return {}

        history = self.get_conversation_history(student_id)
        self.append_to_conversation(student_id, "user", student_response)

        try:
            # Load student context from MCP
            await ws_send({"type": "stage", "stage": "loading", "detail": "Loading your learning profile..."})
            student_context = await self._load_student_context(student_id)
            session_state = await self.student_mcp.get_active_session(student_id)

            # Handle onboarding (no profile yet or stage is onboarding)
            current_stage = (session_state or {}).get("current_stage", "onboarding")
            if not session_state or current_stage == "onboarding":
                return await self._handle_onboarding(
                    student_id, student_response, session_id, ws_send, history,
                )

            objective_id = session_state.get("active_objective_id", "")
            objective_text = ""

            # Resolve objective text by looking up the active objective ID
            if objective_id:
                try:
                    obj = await asyncio.to_thread(self._fetch_objective_by_id, objective_id)
                    if obj:
                        objective_text = obj.get("text", "")
                except Exception as e:
                    logger.warning(f"Failed to fetch objective text for {objective_id}: {e}")

            # Check session content cache — retrieve only if needed
            if self._session_cache.needs_retrieval(session_id, objective_id):
                await ws_send({"type": "stage", "stage": "searching",
                               "detail": "Retrieving teaching content for this objective..."})
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
                # Send chunks to frontend
                if rag_chunks:
                    await ws_send({
                        "type": "rag_chunks",
                        "chunks": [
                            {"content": c.get("content", ""), "topic": c.get("topic", ""),
                             "question_id": c.get("question_id", ""),
                             "distance": round(c.get("distance", 0), 3) if c.get("distance") is not None else None,
                             "rrf_score": round(c.get("rrf_score", 0), 4) if c.get("rrf_score") else 0}
                            for c in rag_chunks
                        ],
                    })
            else:
                teaching_content = self._session_cache.get_teaching_content(session_id)

            # For assessment stages, inject quiz questions as templates
            if current_stage in ("mini_assessment", "final_assessment"):
                assessment_ctx = await self._get_assessment_context(objective_id)
                if assessment_ctx:
                    teaching_content = f"{teaching_content}\n\n{assessment_ctx}"

            # Build Instance B prompt
            await ws_send({"type": "stage", "stage": "composing",
                           "detail": f"Generating response ({current_stage})..."})

            from .prompts import build_instance_b_prompt
            system_prompt = build_instance_b_prompt(
                knowledge_context=teaching_content,
                student_context=student_context,
                current_stage=current_stage,
                active_objective=objective_text,
            )
            messages = [{"role": "system", "content": system_prompt}]
            if history:
                messages.extend(history[-6:])
            messages.append({"role": "user", "content": student_response})
            # Force eval JSON output by adding a prefill hint as a partial assistant message.
            # This technique makes GPT-4 continue the response and append the JSON block.
            # We DON'T actually add an assistant message (Azure doesn't support prefill),
            # but we reinforce via a system reminder at the end.
            messages.append({"role": "system", "content": (
                "IMPORTANT: After your conversational response, you MUST output an evaluation "
                "JSON block wrapped in ```json ... ```. This is required for every response. "
                "The system will malfunction without it. Include detected_state, response_mode, "
                "stage_recommendation, mastery_evidence, mastery_level_change, "
                "misconceptions_detected, stage_summary, and confidence."
            )})

            # Single LLM call — collect full response then parse
            full_response = await self._stream_response(messages, ws_send)

            # Parse eval JSON from the response
            conversational_text, eval_data = self._parse_eval_json(full_response)

            # --- Diagnostic logging ---
            if eval_data:
                logger.info(
                    f"[GUIDED] Eval JSON parsed: stage={current_stage} "
                    f"detected_state={eval_data.get('detected_state')} "
                    f"recommendation={eval_data.get('stage_recommendation')} "
                    f"mastery_change={eval_data.get('mastery_level_change')} "
                    f"confidence={eval_data.get('confidence')}"
                )
            else:
                logger.warning(
                    f"[GUIDED] No eval JSON in response! stage={current_stage} "
                    f"response_length={len(full_response)} chars. "
                    f"Last 200 chars: ...{full_response[-200:]}"
                )

            # Save conversation (conversational part only, not eval JSON)
            self.append_to_conversation(student_id, "assistant", conversational_text)

            # Fire-and-forget RAG triple capture for evaluation pipeline
            cached = self._session_cache.get(session_id)
            if cached and cached.get("rag_chunks"):
                try:
                    from ..services.eval.repository import EvalRepository
                    eval_repo = EvalRepository(db=self.db)
                    eval_repo.capture_rag_sample(
                        query=student_response,
                        retrieved_contexts=[c.get("content", "") for c in cached["rag_chunks"]],
                        response=conversational_text,
                        student_id=student_id, session_id=session_id,
                        intent="guided", instance="b",
                    )
                except Exception as e:
                    logger.warning(f"RAG capture failed (non-critical): {e}")

            # Process eval through stage machine
            stage_result = {}
            if eval_data and self._stage_machine:
                stage_result = await self._stage_machine.process_eval(
                    student_id, session_id, session_state, eval_data,
                )
                logger.info(
                    f"[GUIDED] Stage machine result: changed={stage_result.get('stage_changed')} "
                    f"new_stage={stage_result.get('new_stage')} "
                    f"mastery={stage_result.get('mastery_updated')} "
                    f"assessment={stage_result.get('assessment_result')}"
                )

                # Invalidate cache if objective changed
                if stage_result.get("new_stage") == "introduction" and stage_result.get("stage_changed"):
                    self._session_cache.invalidate(session_id)

                # Send stage updates to client
                if stage_result.get("stage_changed"):
                    await ws_send({
                        "type": "stage_update",
                        "stage": stage_result["new_stage"],
                        "objective": objective_id,
                        "summary": stage_result.get("stage_summary", ""),
                    })

                if stage_result.get("mastery_updated"):
                    await ws_send({
                        "type": "mastery_update",
                        "objective_id": objective_id,
                        "objective_text": objective_text or objective_id,
                        "new_level": stage_result.get("new_mastery_level", ""),
                    })

                if stage_result.get("assessment_result"):
                    await ws_send({
                        "type": "assessment_score",
                        **stage_result["assessment_result"],
                    })

            metadata = {
                "session_id": session_id,
                "stage": current_stage,
                "eval_data": eval_data,
                "stage_result": stage_result,
            }
            await ws_send({"type": "stream_end", "metadata": metadata})
            return metadata

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
    _STARTING_OBJECTIVES = {
        # Level 0: no prior accessibility knowledge — start with WCAG structure
        "none": "c3df6637-125f-4fbf-b4ab-1adc102b8641",
        # "Explain the structure of WCAG 2.2 by identifying the four principles (POUR),
        #  guidelines, and success criteria levels (A, AA, AAA)"

        # Level 1: some awareness / working knowledge — applied concepts
        "awareness": "653bc9b8-9cc2-42e8-aa4f-c94c21012f62",
        "working_knowledge": "653bc9b8-9cc2-42e8-aa4f-c94c21012f62",
        # "Understand how ARIA live region properties and values impact AT behavior" (3 questions)

        # Level 2: professional — analysis-level challenges
        "professional": "07003c38-5181-4e6d-88ba-f22f198f4986",
        # "Analyze design elements (headings, landmarks, color contrast) to determine
        #  their impact on diverse user groups" (3 questions)
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