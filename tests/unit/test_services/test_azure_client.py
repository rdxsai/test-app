import pytest

from question_app.services.tutor.azure_client import AzureAPIMClient


class FakeResponse:
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
    assert client._resolve_reasoning_completion_tokens(900, "high") == 2400
    assert client._resolve_reasoning_completion_tokens(3000, "high") == 2400
