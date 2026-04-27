import pytest

from question_app.services.tutor.openai_responses_client import OpenAIResponsesClient


@pytest.mark.asyncio
async def test_responses_create_uses_openai_responses_endpoint(monkeypatch):
    captured = {}

    class FakeResponse:
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

        async def post(self, url, headers=None, json=None):
            captured["url"] = url
            captured["headers"] = headers
            captured["json"] = json
            return FakeResponse()

    monkeypatch.setattr(
        "question_app.services.tutor.openai_responses_client.httpx.AsyncClient",
        FakeAsyncClient,
    )

    client = OpenAIResponsesClient(
        api_key="test-key",
        model="gpt-5.4",
        base_url="https://api.openai.com/v1/",
    )

    payload = await client.responses_create(
        instructions="Retrieve first.",
        input=[{"role": "user", "content": [{"type": "input_text", "text": "hi"}]}],
        tools=[{"type": "function", "name": "search_wcag"}],
        tool_choice="required",
        parallel_tool_calls=False,
        reasoning_effort="low",
        max_output_tokens=500,
        previous_response_id="resp_prev",
        max_tool_calls=3,
        store=True,
    )

    assert payload["id"] == "resp_123"
    assert captured["url"] == "https://api.openai.com/v1/responses"
    assert captured["headers"]["Authorization"] == "Bearer test-key"
    assert "Ocp-Apim-Subscription-Key" not in captured["headers"]
    assert captured["json"]["model"] == "gpt-5.4"
    assert captured["json"]["previous_response_id"] == "resp_prev"
    assert captured["json"]["reasoning"] == {"effort": "low"}
    assert captured["json"]["max_output_tokens"] == 500
    assert captured["json"]["max_tool_calls"] == 3
