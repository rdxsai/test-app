from unittest.mock import AsyncMock

import pytest

from question_app.services.general_chat_service import GeneralChatService


class FakeAzureClient:
    def __init__(self, endpoint: str, deployment: str, api_key: str, api_version: str = ""):
        self.endpoint = endpoint
        self.deployment = deployment
        self.api_key = api_key
        self.api_version = api_version

    def chat(
        self,
        messages,
        temperature=0.7,
        max_tokens=1000,
        reasoning_effort=None,
        response_format=None,
    ):
        system_prompt = messages[0]["content"]
        user_message = messages[-1]["content"]
        if "Classify it as one of three intents" in system_prompt:
            if "capital of france" in user_message.lower():
                return '{"intent": "off_topic"}'
            if "<button" in user_message.lower():
                return '{"intent": "code_analysis_request"}'
            return '{"intent": "conceptual_question"}'
        if "Hypothetical answer:" in user_message:
            return "Alt text describes the purpose of an image for users who cannot see it."
        if "expert web accessibility code reviewer" in system_prompt:
            return "The button is missing an accessible name."
        return "Generated accessibility answer."

    async def chat_stream_async(self, messages, temperature=0.7, max_tokens=1000):
        for token in ["Generated ", "accessibility ", "answer."]:
            yield token


class FakeVectorStore:
    def __init__(self):
        self.hybrid_search_calls = []

    async def hybrid_search(self, query: str, k: int = 3, bm25_query: str = ""):
        self.hybrid_search_calls.append(
            {"query": query, "k": k, "bm25_query": bm25_query}
        )
        return [
            {
                "content": "Alt text should convey the image's meaning or function.",
                "topic": "images",
                "question_id": "q-1",
                "chunk_type": "question",
                "distance": 0.11,
                "rrf_score": 0.3,
            }
        ]


class FakeWCAGClient:
    def __init__(self):
        self.queries = []

    async def get_wcag_context(self, student_query: str) -> str:
        self.queries.append(student_query)
        return "SC 1.1.1 Non-text Content"


@pytest.fixture
def service(monkeypatch):
    monkeypatch.setattr(
        "question_app.services.general_chat_service.AzureAPIMClient",
        FakeAzureClient,
    )
    return GeneralChatService(
        azure_config={
            "api_key": "test-key",
            "endpoint": "https://example.test",
            "deployment_name": "fallback-model",
            "instance_a_deployment_name": "gpt-5.4",
            "tutor_deployment_name": "gpt-5.4-mini",
            "reasoning_deployment_name": "gpt-5.4",
            "api_version": "2025-01-01-preview",
        },
        vector_store_service=FakeVectorStore(),
        wcag_mcp_client=FakeWCAGClient(),
        db_manager=None,
    )


@pytest.mark.asyncio
async def test_default_session_bootstrap_creates_ephemeral_session_ids(service):
    first = await service.ensure_session("default-student")
    second = await service.ensure_session("default-student")

    assert first["session_id"].startswith("chat-")
    assert second["session_id"].startswith("chat-")
    assert first["session_id"] != second["session_id"]


def test_instance_a_prefers_explicit_instance_a_deployment(service):
    assert service.chat_client.deployment == "gpt-5.4"
    assert service.reasoning_client.deployment == "gpt-5.4"


@pytest.mark.asyncio
async def test_handle_message_uses_session_memory_and_shared_sources(service):
    session = await service.ensure_session("chat-test")
    await service.start_new_session(session["session_id"])

    result = await service.handle_message(
        session_id=session["session_id"],
        user_message="What is alt text?",
    )

    stored = await service.sessions.get_session(session["session_id"])
    assert result["response"] == "Generated accessibility answer."
    assert result["session_metadata"]["session_number"] == 1
    assert result["session_metadata"]["intent_executed"] == "conceptual_question"
    assert len(stored.history) == 2
    assert stored.history[0]["role"] == "user"
    assert stored.history[1]["role"] == "assistant"
    assert service.vector_store.hybrid_search_calls
    assert service.wcag_mcp.queries == ["What is alt text?"]


@pytest.mark.asyncio
async def test_off_topic_message_skips_retrieval(service):
    session = await service.ensure_session("chat-test-off-topic")
    await service.start_new_session(session["session_id"])

    result = await service.handle_message(
        session_id=session["session_id"],
        user_message="What is the capital of France?",
    )

    assert result["session_metadata"]["intent_executed"] == "off_topic"
    assert "web accessibility" in result["response"]
    assert service.vector_store.hybrid_search_calls == []
    assert service.wcag_mcp.queries == []


@pytest.mark.asyncio
async def test_streaming_message_emits_instance_a_events(service):
    session = await service.ensure_session("chat-stream")
    await service.start_new_session(session["session_id"])
    events = []

    async def ws_send(payload):
        events.append(payload)

    metadata = await service.handle_message_streaming(
        session_id=session["session_id"],
        user_message="What is alt text?",
        ws_send=ws_send,
    )

    event_types = [event["type"] for event in events]
    rag_event = next(event for event in events if event["type"] == "rag_chunks")
    assert metadata["intent_executed"] == "conceptual_question"
    assert event_types[0] == "stage"
    assert "rag_chunks" in event_types
    assert "wcag_context" in event_types
    assert "stream_start" in event_types
    assert "stream_end" in event_types
    assert rag_event["chunks"][0]["source_label"] == "Quiz Source 1 | topic=images | question_id=q-1 | type=question"
    assert rag_event["chunks"][0]["summary"].startswith("Key point:")
    assert "content" not in rag_event["chunks"][0]


@pytest.mark.asyncio
async def test_get_rag_context_renders_compact_labeled_chunks(service):
    service.vector_store.hybrid_search = AsyncMock(
        return_value=[
            {
                "content": "First chunk about effective alt text for informative images.",
                "topic": "images",
                "question_id": "q-1",
                "chunk_type": "question",
                "distance": 0.08,
                "rrf_score": 0.33,
            },
            {
                "content": "Second chunk explains concise wording and avoiding redundancy.",
                "topic": "content",
                "question_id": "q-2",
                "chunk_type": "answer",
                "distance": 0.09,
                "rrf_score": 0.22,
            },
            {
                "content": "Third chunk covers decorative images and null alt usage.",
                "topic": "images",
                "question_id": "q-3",
                "chunk_type": "question",
                "distance": 0.12,
                "rrf_score": 0.18,
            },
            {
                "content": "Fourth chunk should not appear because only three prompt chunks are allowed.",
                "topic": "overflow",
                "question_id": "q-4",
                "chunk_type": "answer",
                "distance": 0.13,
                "rrf_score": 0.12,
            },
        ]
    )

    context, chunks = await service._get_rag_context("What is alt text?")

    assert len(chunks) == 3
    assert "Quiz Source 1 | topic=images | question_id=q-1 | type=question" in context
    assert "Key point:" in context
    assert "Quiz Source 2 | topic=content | question_id=q-2 | type=answer" in context
    assert "Quiz Source 3 | topic=images | question_id=q-3 | type=question" in context
    assert "q-4" not in context


@pytest.mark.asyncio
async def test_get_rag_context_truncates_long_chunk_content(service):
    long_content = "Alt text guidance " * 40
    service.vector_store.hybrid_search = AsyncMock(
        return_value=[
            {
                "content": long_content,
                "topic": "images",
                "question_id": "q-1",
                "chunk_type": "question",
                "distance": 0.08,
                "rrf_score": 0.33,
            }
        ]
    )

    context, _ = await service._get_rag_context("What is alt text?")

    assert len(context) < len(long_content)
    assert context.endswith("...")


@pytest.mark.asyncio
async def test_get_rag_context_reranks_by_query_relevance(service):
    service.vector_store.hybrid_search = AsyncMock(
        return_value=[
            {
                "content": "Decorative images can use empty alt attributes.",
                "topic": "images",
                "question_id": "q-1",
                "chunk_type": "answer",
                "is_correct": True,
                "distance": 0.2,
                "rrf_score": 0.4,
            },
            {
                "content": "Keyboard focus indicators should remain visible when tabbing through controls.",
                "topic": "focus",
                "question_id": "q-2",
                "chunk_type": "question",
                "distance": 0.12,
                "rrf_score": 0.12,
            },
        ]
    )

    _, chunks = await service._get_rag_context("How should keyboard focus visible work?")

    assert chunks[0]["question_id"] == "q-2"


def test_summarize_chunk_for_prompt_highlights_signal_and_tags(service):
    summary = service._summarize_chunk_for_prompt(
        {
            "content": (
                "Alt text should describe the purpose of the image rather than every visual detail. "
                "That keeps it useful for screen reader users."
            ),
            "chunk_type": "answer",
            "is_correct": True,
            "learning_objective": "Explain effective text alternatives",
            "tags": ["images", "alt text"],
        }
    )

    assert summary.startswith("Key point:")
    assert "Signal: correct answer example" in summary
    assert "Objective: Explain effective text alternatives" in summary
    assert "Tags: images, alt text" in summary


def test_build_rag_chunk_payload_matches_prompt_representation(service):
    payload = service._build_rag_chunk_payload(
        [
            {
                "content": "Alt text should describe the purpose of the image.",
                "topic": "images",
                "question_id": "q-1",
                "chunk_type": "answer",
                "is_correct": True,
                "distance": 0.0832,
                "rrf_score": 0.33119,
            }
        ]
    )

    assert payload == [
        {
            "source_label": "Quiz Source 1 | topic=images | question_id=q-1 | type=answer",
            "summary": "Key point: Alt text should describe the purpose of the image. | Signal: correct answer example",
            "topic": "images",
            "question_id": "q-1",
            "chunk_type": "answer",
            "distance": 0.083,
            "rrf_score": 0.3312,
        }
    ]
