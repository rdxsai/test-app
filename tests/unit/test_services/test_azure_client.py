import pytest

from question_app.services.tutor.azure_client import (
    AzureAPIMClient,
    build_graph_responses_client,
)


class FakeResponse:
    status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return {"choices": [{"message": {"content": "", "tool_calls": []}}]}


@pytest.mark.asyncio
async def test_chat_with_tools_enables_parallel_tool_calls(monkeypatch):
    captured = {}

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, headers=None, params=None, json=None):
            captured["url"] = url
            captured["json"] = json
            return FakeResponse()

    monkeypatch.setattr(
        "question_app.services.tutor.azure_client.httpx.AsyncClient",
        FakeAsyncClient,
    )

    client = AzureAPIMClient(
        endpoint="https://example.test",
        deployment="gpt-5.4",
        api_key="test-key",
    )

    await client.chat_with_tools(
        messages=[{"role": "user", "content": "Research WCAG hierarchy"}],
        tools=[],
        tool_choice="required",
        parallel_tool_calls=True,
        reasoning_effort="medium",
    )

    assert captured["json"]["parallel_tool_calls"] is True
    assert captured["json"]["tool_choice"] == "required"
    assert captured["json"]["reasoning_effort"] == "medium"
    assert captured["json"]["max_completion_tokens"] == 1600


@pytest.mark.asyncio
async def test_chat_with_tools_includes_content_filter_policy_header(monkeypatch):
    captured = {}

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, headers=None, params=None, json=None):
            captured["headers"] = headers
            return FakeResponse()

    monkeypatch.setattr(
        "question_app.services.tutor.azure_client.httpx.AsyncClient",
        FakeAsyncClient,
    )

    client = AzureAPIMClient(
        endpoint="https://example.test",
        deployment="gpt-5.4",
        api_key="test-key",
        content_filter_policy="async-filter",
    )

    await client.chat_with_tools(
        messages=[{"role": "user", "content": "hello"}],
        tools=[],
    )

    assert captured["headers"]["x-policy-id"] == "async-filter"


def test_reasoning_completion_budget_defaults_to_tighter_low_effort_limit():
    client = AzureAPIMClient(
        endpoint="https://example.test",
        deployment="gpt-5.4",
        api_key="test-key",
    )

    assert client._resolve_reasoning_completion_tokens(120, "low") == 400
    assert client._resolve_reasoning_completion_tokens(300, "low") == 800
    assert client._resolve_reasoning_completion_tokens(500, "low") == 1200
    assert client._resolve_reasoning_completion_tokens(1000, "low") == 1200


def test_reasoning_completion_budget_scales_by_effort_with_cap():
    client = AzureAPIMClient(
        endpoint="https://example.test",
        deployment="gpt-5.4",
        api_key="test-key",
    )

    assert client._resolve_reasoning_completion_tokens(180, "medium") == 800
    assert client._resolve_reasoning_completion_tokens(900, "medium") == 1800
    assert client._resolve_reasoning_completion_tokens(180, "high") == 1200
    assert client._resolve_reasoning_completion_tokens(900, "high") == 2700
    assert client._resolve_reasoning_completion_tokens(3000, "high") == 9000
    assert client._resolve_reasoning_completion_tokens(6000, "high") == 12000


@pytest.mark.asyncio
async def test_responses_create_uses_responses_payload_shape(monkeypatch):
    captured = {}

    class FakeResponsesPayload:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {"id": "resp_123", "output": []}

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, headers=None, params=None, json=None):
            captured["url"] = url
            captured["headers"] = headers
            captured["params"] = params
            captured["json"] = json
            return FakeResponsesPayload()

    monkeypatch.setattr(
        "question_app.services.tutor.azure_client.httpx.AsyncClient",
        FakeAsyncClient,
    )

    client = AzureAPIMClient(
        endpoint="https://example.test",
        deployment="gpt-5.4",
        api_key="test-key",
        api_version="2025-01-01-preview",
        content_filter_policy="resp-filter",
    )

    payload = await client.responses_create(
        instructions="Retrieve first.",
        input=[{"role": "user", "content": [{"type": "input_text", "text": "hello"}]}],
        tools=[
            {
                "type": "function",
                "name": "search_wcag",
                "description": "",
                "parameters": {"type": "object", "properties": {}, "required": []},
                "strict": True,
            }
        ],
        tool_choice="required",
        parallel_tool_calls=False,
        reasoning_effort="medium",
        max_output_tokens=500,
        previous_response_id="resp_prev",
        max_tool_calls=4,
        store=True,
    )

    assert payload["id"] == "resp_123"
    assert captured["url"] == "https://example.test/v1/responses"
    assert captured["params"] == {"api-version": "2025-01-01-preview"}
    assert "Authorization" not in captured["headers"]
    assert captured["headers"]["Ocp-Apim-Subscription-Key"] == "test-key"
    assert captured["headers"]["x-policy-id"] == "resp-filter"
    assert captured["json"]["model"] == "gpt-5.4"
    assert captured["json"]["tool_choice"] == "required"
    assert captured["json"]["parallel_tool_calls"] is False
    assert captured["json"]["reasoning"] == {"effort": "medium"}
    assert captured["json"]["max_output_tokens"] == 1600
    assert captured["json"]["previous_response_id"] == "resp_prev"
    assert captured["json"]["max_tool_calls"] == 4
    assert captured["json"]["store"] is True


def test_build_graph_responses_client_uses_dedicated_azure_gpt54_deployment():
    client = build_graph_responses_client(
        azure_config={
            "endpoint": "https://example.test",
            "api_key": "azure-key",
            "api_version": "2025-01-01-preview",
            "content_filter_policy": "resp-filter",
            "tutor_deployment_name": "gpt-5.4-mini",
            "reasoning_deployment_name": "some-other-model",
        },
        responses_deployment="gpt-5.4",
    )

    assert client is not None
    assert client.endpoint == "https://example.test"
    assert client.deployment == "gpt-5.4"
    assert client.api_key == "azure-key"
    assert client.api_version == "2025-01-01-preview"
    assert client.content_filter_policy == "resp-filter"


@pytest.mark.asyncio
async def test_responses_create_accepts_v1_base_endpoint(monkeypatch):
    captured = {}

    class FakeResponsesPayload:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {"id": "resp_123", "output": []}

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, headers=None, params=None, json=None):
            captured["url"] = url
            return FakeResponsesPayload()

    monkeypatch.setattr(
        "question_app.services.tutor.azure_client.httpx.AsyncClient",
        FakeAsyncClient,
    )

    client = AzureAPIMClient(
        endpoint="https://example.test/openai/v1",
        deployment="gpt-5.4",
        api_key="test-key",
        api_version="preview",
    )

    await client.responses_create(
        input=[{"role": "user", "content": [{"type": "input_text", "text": "hi"}]}],
    )

    assert captured["url"] == "https://example.test/openai/v1/responses"


@pytest.mark.asyncio
async def test_responses_create_accepts_full_responses_endpoint_without_api_version(
    monkeypatch,
):
    captured = {}

    class FakeResponsesPayload:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {"id": "resp_123", "output": []}

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, headers=None, params=None, json=None):
            captured["url"] = url
            captured["params"] = params
            return FakeResponsesPayload()

    monkeypatch.setattr(
        "question_app.services.tutor.azure_client.httpx.AsyncClient",
        FakeAsyncClient,
    )

    client = AzureAPIMClient(
        endpoint="https://example.test/v1/responses",
        deployment="gpt-5.4",
        api_key="test-key",
        api_version="",
    )

    await client.responses_create(input="Connectivity check.")

    assert captured["url"] == "https://example.test/v1/responses"
    assert captured["params"] is None
