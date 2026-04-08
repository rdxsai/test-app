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
