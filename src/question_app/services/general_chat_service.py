"""Lightweight runtime for Instance A general accessibility Q&A."""

import asyncio
import re
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .tutor.azure_client import AzureAPIMClient
from .tutor.interfaces import VectorStoreInterface
from .tutor.prompts import build_instance_a_prompt
from ..core import get_logger


logger = get_logger(__name__)

DEFAULT_SESSION_ID = "default-student"
MAX_COSINE_DISTANCE = 0.3
MIN_RRF_SCORE = 0.01
MAX_PROMPT_RAG_CHUNKS = 3
MAX_PROMPT_CHUNK_CHARS = 280
MAX_PROMPT_SUMMARY_CHARS = 180
INSTANCE_A_RESPONSE_MAX_TOKENS = 600


@dataclass
class ChatSessionState:
    """Ephemeral session state for Instance A."""

    session_id: str
    session_number: int = 0
    history: List[Dict[str, str]] = field(default_factory=list)
    last_seen_at: float = field(default_factory=time.time)


class InMemoryChatSessionStore:
    """Small in-memory session store for browser-scoped chat state."""

    def __init__(self, max_history_messages: int = 12):
        self._max_history_messages = max_history_messages
        self._sessions: Dict[str, ChatSessionState] = {}
        self._lock = asyncio.Lock()

    @staticmethod
    def _new_session_id() -> str:
        return f"chat-{uuid.uuid4().hex[:12]}"

    async def ensure_session(
        self,
        requested_session_id: Optional[str] = None,
    ) -> ChatSessionState:
        async with self._lock:
            session = None
            normalized = (requested_session_id or "").strip()

            if normalized and normalized != DEFAULT_SESSION_ID:
                session = self._sessions.get(normalized)
                if session is None:
                    session = ChatSessionState(session_id=normalized)
                    self._sessions[normalized] = session
            else:
                session = ChatSessionState(session_id=self._new_session_id())
                self._sessions[session.session_id] = session

            session.last_seen_at = time.time()
            return ChatSessionState(
                session_id=session.session_id,
                session_number=session.session_number,
                history=list(session.history),
                last_seen_at=session.last_seen_at,
            )

    async def get_session(self, session_id: str) -> ChatSessionState:
        async with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                session = ChatSessionState(session_id=session_id or self._new_session_id())
                self._sessions[session.session_id] = session
            session.last_seen_at = time.time()
            return ChatSessionState(
                session_id=session.session_id,
                session_number=session.session_number,
                history=list(session.history),
                last_seen_at=session.last_seen_at,
            )

    async def start_new_session(self, session_id: str) -> ChatSessionState:
        async with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                session = ChatSessionState(session_id=session_id or self._new_session_id())
                self._sessions[session.session_id] = session
            session.session_number += 1
            session.history = []
            session.last_seen_at = time.time()
            return ChatSessionState(
                session_id=session.session_id,
                session_number=session.session_number,
                history=[],
                last_seen_at=session.last_seen_at,
            )

    async def get_history(self, session_id: str) -> List[Dict[str, str]]:
        session = await self.get_session(session_id)
        return list(session.history)

    async def append_message(self, session_id: str, role: str, content: str) -> None:
        async with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                session = ChatSessionState(session_id=session_id or self._new_session_id())
                self._sessions[session.session_id] = session
            session.history.append({"role": role, "content": content})
            session.history = session.history[-self._max_history_messages :]
            session.last_seen_at = time.time()


class GeneralChatService:
    """Instance A runtime: general accessibility Q&A with session-only memory."""

    def __init__(
        self,
        azure_config: Dict[str, str],
        vector_store_service: VectorStoreInterface,
        wcag_mcp_client=None,
        db_manager=None,
    ):
        chat_deployment = (
            azure_config.get("instance_a_deployment_name")
            or azure_config.get("reasoning_deployment_name")
            or azure_config.get("tutor_deployment_name")
            or azure_config.get("deployment_name")
        )
        reasoning_deployment = (
            azure_config.get("tutor_deployment_name")
            or azure_config.get("deployment_name")
            or chat_deployment
        )
        reasoning_deployment = (
            azure_config.get("reasoning_deployment_name")
            or reasoning_deployment
        )

        self.chat_client = AzureAPIMClient(
            endpoint=azure_config["endpoint"],
            deployment=chat_deployment,
            api_key=azure_config["api_key"],
            api_version=azure_config.get("api_version", "2024-02-15-preview"),
        )
        if reasoning_deployment == chat_deployment:
            self.reasoning_client = self.chat_client
        else:
            self.reasoning_client = AzureAPIMClient(
                endpoint=azure_config["endpoint"],
                deployment=reasoning_deployment,
                api_key=azure_config["api_key"],
                api_version=azure_config.get("api_version", "2024-02-15-preview"),
            )

        self.vector_store = vector_store_service
        self.wcag_mcp = wcag_mcp_client
        self.db = db_manager
        self.sessions = InMemoryChatSessionStore()

    async def ensure_session(
        self,
        requested_session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        session = await self.sessions.ensure_session(requested_session_id)
        return {
            "session_id": session.session_id,
            "session_number": session.session_number,
        }

    async def start_new_session(self, session_id: str) -> Dict[str, Any]:
        session = await self.sessions.start_new_session(session_id)
        return {
            "session_id": session.session_id,
            "session_number": session.session_number,
        }

    def _decide_intent(
        self,
        user_message: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        task_description = f"""
Analyze the following user input in the context of the ongoing conversation. Classify it as one of three intents:

1. 'conceptual_question': For general questions, statements, answers, or follow-up requests about web accessibility concepts.
2. 'code_analysis_request': If the user has included a code snippet (HTML, CSS, JS) for review or asked directly about a piece of code.
3. 'off_topic': ONLY if the user is asking about something completely unrelated to web accessibility and not as a follow-up.

IMPORTANT: If this appears to be a follow-up or continuation of the previous conversation, classify it as 'conceptual_question' even if it doesn't explicitly mention web accessibility.

User Input: "{user_message}"

Respond with ONLY a JSON object in this exact format:
{{"intent": "YOUR_CLASSIFICATION_HERE"}}
"""
        messages = [{"role": "system", "content": task_description}]
        if history:
            messages.extend(history[-4:])
        messages.append({"role": "user", "content": user_message})

        try:
            response = self.reasoning_client.chat(
                messages,
                temperature=0.0,
                max_tokens=120,
                reasoning_effort="low",
            )
            import json

            intent = json.loads(response).get("intent", "conceptual_question")
            if intent in {"conceptual_question", "code_analysis_request", "off_topic"}:
                return intent
        except Exception as exc:
            logger.warning(f"Instance A intent classification failed: {exc}")
        return "conceptual_question"

    def _analyze_code_snippet(self, code_snippet: str) -> str:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert web accessibility code reviewer. "
                    "List 1-3 likely accessibility issues in the snippet. "
                    "Be concise. If none are obvious, say 'No obvious accessibility errors found.'"
                ),
            },
            {"role": "user", "content": code_snippet},
        ]
        try:
            return self.reasoning_client.chat(
                messages,
                temperature=0.2,
                max_tokens=300,
                reasoning_effort="low",
            )
        except Exception as exc:
            logger.warning(f"Instance A code analysis failed: {exc}")
            return "Error during code analysis."

    def _build_response_messages(
        self,
        user_message: str,
        context: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> List[Dict[str, str]]:
        system_prompt = build_instance_a_prompt(
            knowledge_context=context,
            student_context="",
        )
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history[-6:])
        messages.append({"role": "user", "content": user_message})
        return messages

    def _generate_hyde_query(
        self,
        query: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        recent = history[-4:] if history else []
        context_block = ""
        if recent:
            context_block = "Recent conversation:\n" + "\n".join(
                f"{item['role']}: {item['content']}" for item in recent
            )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a web accessibility expert. Write a short factual answer "
                    "that would likely answer the user's accessibility question well. "
                    "Use 3-5 sentences. Output only the hypothetical answer."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"{context_block}\n\n"
                    f"User question: {query}\n\n"
                    "Hypothetical answer:"
                ).strip(),
            },
        ]
        try:
            hyde_answer = self.chat_client.chat(
                messages,
                temperature=0.3,
                max_tokens=300,
                reasoning_effort="low",
            ).strip()
            if len(hyde_answer) > 10:
                return hyde_answer
        except Exception as exc:
            logger.warning(f"HyDE generation failed: {exc}")
        return query

    @staticmethod
    def _compact_chunk_content(content: str) -> str:
        normalized = " ".join((content or "").split())
        if len(normalized) <= MAX_PROMPT_CHUNK_CHARS:
            return normalized
        return normalized[: MAX_PROMPT_CHUNK_CHARS - 3].rstrip() + "..."

    @staticmethod
    def _tokenize_text(value: str) -> set[str]:
        return {
            token
            for token in re.findall(r"[a-z0-9]+", (value or "").lower())
            if len(token) >= 3
        }

    @staticmethod
    def _build_chunk_source_label(index: int, chunk: Dict[str, Any]) -> str:
        topic = (chunk.get("topic") or "").strip() or "untitled"
        question_id = (chunk.get("question_id") or "").strip() or "unknown"
        chunk_type = (chunk.get("chunk_type") or "").strip()
        parts = [f"Quiz Source {index}", f"topic={topic}", f"question_id={question_id}"]
        if chunk_type:
            parts.append(f"type={chunk_type}")
        return " | ".join(parts)

    def _summarize_chunk_for_prompt(self, chunk: Dict[str, Any]) -> str:
        compact_content = self._compact_chunk_content(chunk.get("content", ""))
        if not compact_content:
            return ""

        primary_sentence = re.split(r"(?<=[.!?])\s+", compact_content, maxsplit=1)[0]
        if len(primary_sentence) > MAX_PROMPT_SUMMARY_CHARS:
            primary_sentence = (
                primary_sentence[: MAX_PROMPT_SUMMARY_CHARS - 3].rstrip() + "..."
            )

        chunk_type = (chunk.get("chunk_type") or "").strip()
        learning_objective = (chunk.get("learning_objective") or "").strip()
        tags = chunk.get("tags") or []
        summary_parts = [f"Key point: {primary_sentence}"]
        if chunk_type == "answer" and chunk.get("is_correct") is True:
            summary_parts.append("Signal: correct answer example")
        elif chunk_type == "answer" and chunk.get("is_correct") is False:
            summary_parts.append("Signal: distractor or misconception")
        if learning_objective:
            summary_parts.append(f"Objective: {learning_objective}")
        if tags:
            rendered_tags = ", ".join(str(tag).strip() for tag in tags[:3] if str(tag).strip())
            if rendered_tags:
                summary_parts.append(f"Tags: {rendered_tags}")
        return " | ".join(summary_parts)

    def _score_chunk_relevance(self, query: str, chunk: Dict[str, Any]) -> float:
        query_tokens = self._tokenize_text(query)
        content_tokens = self._tokenize_text(chunk.get("content", ""))
        topic_tokens = self._tokenize_text(chunk.get("topic", ""))
        objective_tokens = self._tokenize_text(chunk.get("learning_objective", ""))
        tag_tokens = self._tokenize_text(" ".join(str(tag) for tag in (chunk.get("tags") or [])))

        lexical_overlap = len(query_tokens & content_tokens)
        metadata_overlap = len(query_tokens & (topic_tokens | objective_tokens | tag_tokens))
        rrf_score = float(chunk.get("rrf_score") or 0.0)
        distance = chunk.get("distance")
        distance_bonus = 0.0
        if distance is not None:
            distance_bonus = max(0.0, MAX_COSINE_DISTANCE - float(distance))

        return (lexical_overlap * 4.0) + (metadata_overlap * 2.0) + (rrf_score * 10.0) + distance_bonus

    def _select_prompt_chunks(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        ranked_chunks = sorted(
            chunks,
            key=lambda chunk: (
                self._score_chunk_relevance(query, chunk),
                float(chunk.get("rrf_score") or 0.0),
                -(float(chunk.get("distance")) if chunk.get("distance") is not None else 999.0),
            ),
            reverse=True,
        )
        return ranked_chunks[:MAX_PROMPT_RAG_CHUNKS]

    def _render_compact_rag_context(self, chunks: List[Dict[str, Any]]) -> str:
        rendered_chunks: List[str] = []
        for index, chunk in enumerate(chunks[:MAX_PROMPT_RAG_CHUNKS], start=1):
            summary = self._summarize_chunk_for_prompt(chunk)
            if not summary:
                continue
            rendered_chunks.append(
                f"[{self._build_chunk_source_label(index, chunk)}]\n{summary}"
            )
        return "\n\n".join(rendered_chunks)

    def _build_rag_chunk_payload(
        self,
        chunks: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        payload: List[Dict[str, Any]] = []
        for index, chunk in enumerate(chunks[:MAX_PROMPT_RAG_CHUNKS], start=1):
            payload.append(
                {
                    "source_label": self._build_chunk_source_label(index, chunk),
                    "summary": self._summarize_chunk_for_prompt(chunk),
                    "topic": chunk.get("topic", ""),
                    "question_id": chunk.get("question_id", ""),
                    "chunk_type": chunk.get("chunk_type", ""),
                    "distance": (
                        round(chunk.get("distance", 0), 3)
                        if chunk.get("distance") is not None
                        else None
                    ),
                    "rrf_score": (
                        round(chunk.get("rrf_score", 0), 4)
                        if chunk.get("rrf_score") is not None
                        else 0
                    ),
                }
            )
        return payload

    def _extract_success_criteria_refs(self, text: str) -> List[str]:
        refs = re.findall(r"\b\d\.\d\.\d\b", text or "")
        return sorted(set(refs))

    def _compute_wcag_grounding_score(
        self,
        response_refs: List[str],
        wcag_refs: List[str],
    ) -> float:
        if not response_refs:
            return 0.0
        if not wcag_refs:
            return 0.0
        grounded_refs = set(response_refs) & set(wcag_refs)
        return len(grounded_refs) / len(set(response_refs))

    def _compute_query_overlap_score(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
    ) -> float:
        query_tokens = self._tokenize_text(query)
        if not query_tokens or not retrieved_chunks:
            return 0.0

        chunk_tokens: set[str] = set()
        for chunk in retrieved_chunks:
            chunk_tokens.update(self._tokenize_text(chunk.get("content", "")))
            chunk_tokens.update(self._tokenize_text(chunk.get("topic", "")))
            chunk_tokens.update(self._tokenize_text(chunk.get("learning_objective", "")))
            chunk_tokens.update(
                self._tokenize_text(" ".join(str(tag) for tag in (chunk.get("tags") or [])))
            )

        if not chunk_tokens:
            return 0.0
        return len(query_tokens & chunk_tokens) / len(query_tokens)

    def _build_eval_metrics(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        response: str,
        wcag_context: str = "",
    ) -> List[Dict[str, Any]]:
        query_overlap = self._compute_query_overlap_score(query, retrieved_chunks)
        response_refs = self._extract_success_criteria_refs(response)
        wcag_refs = self._extract_success_criteria_refs(wcag_context)
        grounded_refs = sorted(set(response_refs) & set(wcag_refs))
        grounding_score = self._compute_wcag_grounding_score(response_refs, wcag_refs)

        return [
            {
                "metric_name": "retrieval_context_count",
                "metric_value": float(len(retrieved_chunks)),
                "details": {
                    "question_ids": [chunk.get("question_id", "") for chunk in retrieved_chunks],
                    "topics": [chunk.get("topic", "") for chunk in retrieved_chunks],
                },
            },
            {
                "metric_name": "retrieval_query_overlap",
                "metric_value": round(query_overlap, 4),
                "details": {
                    "query": query,
                    "chunk_count": len(retrieved_chunks),
                },
            },
            {
                "metric_name": "wcag_context_used",
                "metric_value": 1.0 if wcag_context.strip() else 0.0,
                "details": {
                    "wcag_refs": wcag_refs,
                },
            },
            {
                "metric_name": "response_wcag_citation_present",
                "metric_value": 1.0 if response_refs else 0.0,
                "details": {
                    "response_refs": response_refs,
                    "wcag_refs": wcag_refs,
                },
            },
            {
                "metric_name": "response_wcag_citation_grounded",
                "metric_value": round(grounding_score, 4),
                "details": {
                    "response_refs": response_refs,
                    "wcag_refs": wcag_refs,
                    "grounded_refs": grounded_refs,
                },
            },
        ]

    async def _get_rag_context(
        self,
        query: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> tuple[str, List[Dict[str, Any]]]:
        hyde_query = self._generate_hyde_query(query, history or [])
        retrieved_chunks: List[Dict[str, Any]] = []

        try:
            if hasattr(self.vector_store, "hybrid_search"):
                retrieved_chunks = await self.vector_store.hybrid_search(
                    query=hyde_query,
                    k=5,
                    bm25_query=query,
                )
            elif hasattr(self.vector_store, "search"):
                try:
                    retrieved_chunks = await self.vector_store.search(
                        query=hyde_query,
                        k=5,
                    )
                except TypeError:
                    retrieved_chunks = await self.vector_store.search(
                        hyde_query,
                        5,
                    )
        except Exception as exc:
            logger.warning(f"Instance A RAG retrieval failed: {exc}")
            return "", []

        high_quality_chunks = []
        for chunk in retrieved_chunks or []:
            distance = chunk.get("distance")
            rrf_score = chunk.get("rrf_score", 1.0)
            if distance is not None and distance > MAX_COSINE_DISTANCE:
                continue
            if chunk.get("rrf_score") is not None and rrf_score < MIN_RRF_SCORE:
                continue
            high_quality_chunks.append(chunk)

        if not high_quality_chunks:
            return "", []

        selected_chunks = self._select_prompt_chunks(query, high_quality_chunks)
        context = self._render_compact_rag_context(selected_chunks)
        return context, selected_chunks

    async def _get_combined_context(
        self,
        query: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> tuple[str, List[Dict[str, Any]], str]:
        rag_coro = self._get_rag_context(query, history)

        async def _empty_wcag() -> str:
            return ""

        wcag_coro = (
            self.wcag_mcp.get_wcag_context(query)
            if self.wcag_mcp
            else _empty_wcag()
        )
        (rag_context, quiz_chunks), wcag_context = await asyncio.gather(
            rag_coro,
            wcag_coro,
        )

        parts = []
        if rag_context:
            parts.append(f"--- QUIZ KNOWLEDGE BASE ---\n{rag_context}")
        if wcag_context:
            parts.append(f"--- WCAG GUIDELINES REFERENCE (authoritative) ---\n{wcag_context}")
        return "\n\n".join(parts), quiz_chunks, wcag_context

    async def _stream_response(self, messages: List[Dict[str, str]], ws_send) -> str:
        full_response: List[str] = []
        try:
            async for token in self.chat_client.chat_stream_async(
                messages,
                max_tokens=INSTANCE_A_RESPONSE_MAX_TOKENS,
            ):
                full_response.append(token)
        except Exception as exc:
            logger.warning(f"Instance A streaming failed, using sync response: {exc}")
            if not full_response:
                sync_response = await asyncio.to_thread(
                    self.chat_client.chat,
                    messages,
                    0.7,
                    INSTANCE_A_RESPONSE_MAX_TOKENS,
                )
                await ws_send({"type": "stream_start"})
                await ws_send({"type": "token", "content": sync_response})
                return sync_response

        result = "".join(full_response)
        if not result:
            result = await asyncio.to_thread(
                self.chat_client.chat,
                messages,
                0.7,
                INSTANCE_A_RESPONSE_MAX_TOKENS,
            )
            await ws_send({"type": "stream_start"})
            await ws_send({"type": "token", "content": result})
            return result

        await ws_send({"type": "stream_start"})
        for token in full_response:
            await ws_send({"type": "token", "content": token})
            await asyncio.sleep(0.008)
        return result

    async def _capture_rag_sample(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        response: str,
        session_id: str,
        intent: str,
        wcag_context: str = "",
    ) -> None:
        if not self.db or not retrieved_chunks:
            return
        try:
            from .eval.repository import EvalRepository

            eval_repo = EvalRepository(db=self.db)
            sample_id = eval_repo.capture_rag_sample(
                query=query,
                retrieved_contexts=[chunk.get("content", "") for chunk in retrieved_chunks],
                response=response,
                student_id=session_id,
                intent=intent,
                instance="a",
            )
            for metric in self._build_eval_metrics(
                query=query,
                retrieved_chunks=retrieved_chunks,
                response=response,
                wcag_context=wcag_context,
            ):
                eval_repo.log_eval(
                    content_type="rag_sample",
                    content_id=sample_id,
                    metric_name=metric["metric_name"],
                    metric_value=metric["metric_value"],
                    details=metric["details"],
                    evaluator="auto",
                )
        except Exception as exc:
            logger.warning(f"Instance A RAG capture failed: {exc}")

    async def handle_message(
        self,
        session_id: str,
        user_message: str,
    ) -> Dict[str, Any]:
        session = await self.sessions.get_session(session_id)
        history = list(session.history)
        await self.sessions.append_message(session_id, "user", user_message)

        intent = await asyncio.to_thread(self._decide_intent, user_message, history)
        retrieved_chunks: List[Dict[str, Any]] = []
        response = ""
        wcag_context = ""

        if intent == "off_topic":
            response = (
                "That's outside what I can help with — I'm focused on web accessibility. "
                "What would you like to explore?"
            )
        else:
            search_query = user_message
            combined_context = ""
            code_analysis = ""

            if intent == "code_analysis_request":
                code_analysis = await asyncio.to_thread(
                    self._analyze_code_snippet,
                    user_message,
                )
                search_query = f"{user_message}\n{code_analysis}"

            combined_context, retrieved_chunks, wcag_context = await self._get_combined_context(
                search_query,
                history=history,
            )
            if code_analysis:
                combined_context = f"CODE ANALYSIS:\n{code_analysis}\n\n{combined_context}".strip()

            messages = self._build_response_messages(
                user_message,
                combined_context,
                history=history,
            )
            response = await asyncio.to_thread(
                self.chat_client.chat,
                messages,
                0.7,
                INSTANCE_A_RESPONSE_MAX_TOKENS,
            )

        await self.sessions.append_message(session_id, "assistant", response)
        await self._capture_rag_sample(
            query=user_message,
            retrieved_chunks=retrieved_chunks,
            response=response,
            session_id=session_id,
            intent=intent,
            wcag_context=wcag_context if intent != "off_topic" else "",
        )

        updated = await self.sessions.get_session(session_id)
        return {
            "response": response,
            "session_id": updated.session_id,
            "session_metadata": {
                "session_number": updated.session_number,
                "intent_executed": intent,
                "analysis": {},
                "progress": {},
            },
        }

    async def handle_message_streaming(
        self,
        session_id: str,
        user_message: str,
        ws_send,
    ) -> Dict[str, Any]:
        session = await self.sessions.get_session(session_id)
        history = list(session.history)
        await self.sessions.append_message(session_id, "user", user_message)

        await ws_send({"type": "stage", "stage": "classifying"})
        intent = await asyncio.to_thread(self._decide_intent, user_message, history)

        response = ""
        retrieved_chunks: List[Dict[str, Any]] = []

        if intent == "off_topic":
            response = (
                "That's outside what I can help with — I'm focused on web accessibility. "
                "What would you like to explore?"
            )
            await ws_send({"type": "stream_start"})
            await ws_send({"type": "token", "content": response})
        else:
            search_query = user_message
            code_analysis = ""
            if intent == "code_analysis_request":
                await ws_send({"type": "stage", "stage": "analyzing", "detail": "Analyzing code snippet..."})
                code_analysis = await asyncio.to_thread(self._analyze_code_snippet, user_message)
                search_query = f"{user_message}\n{code_analysis}"

            await ws_send({"type": "stage", "stage": "searching", "detail": "Searching knowledge base..."})
            combined_context, retrieved_chunks, wcag_context = await self._get_combined_context(
                search_query,
                history=history,
            )

            await ws_send(
                {
                    "type": "stage",
                    "stage": "searching",
                    "detail": (
                        f"Found {len(retrieved_chunks)} quiz matches"
                        f"{' + WCAG references' if wcag_context else ''}"
                    ),
                }
            )
            await ws_send(
                {
                    "type": "rag_chunks",
                    "chunks": self._build_rag_chunk_payload(retrieved_chunks),
                }
            )
            if wcag_context:
                await ws_send({"type": "wcag_context", "content": wcag_context})

            if code_analysis:
                combined_context = f"CODE ANALYSIS:\n{code_analysis}\n\n{combined_context}".strip()

            await ws_send({"type": "stage", "stage": "composing", "detail": "Generating response..."})
            messages = self._build_response_messages(
                user_message,
                combined_context,
                history=history,
            )
            response = await self._stream_response(messages, ws_send)

        await self.sessions.append_message(session_id, "assistant", response)
        await self._capture_rag_sample(
            query=user_message,
            retrieved_chunks=retrieved_chunks,
            response=response,
            session_id=session_id,
            intent=intent,
            wcag_context=wcag_context if intent != "off_topic" else "",
        )

        updated = await self.sessions.get_session(session_id)
        metadata = {
            "session_number": updated.session_number,
            "intent_executed": intent,
            "analysis": {},
            "progress": {},
        }
        await ws_send({"type": "stream_end", "metadata": metadata})
        return metadata
