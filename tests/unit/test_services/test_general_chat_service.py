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
    assert metadata["intent_executed"] == "conceptual_question"
    assert event_types[0] == "stage"
    assert "rag_chunks" in event_types
    assert "wcag_context" in event_types
    assert "stream_start" in event_types
    assert "stream_end" in event_types
