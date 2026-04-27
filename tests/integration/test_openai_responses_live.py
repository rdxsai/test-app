import os

import pytest
from dotenv import load_dotenv

from question_app.services.tutor.openai_responses_client import OpenAIResponsesClient


def _response_text(response: dict) -> str:
    direct = str(response.get("output_text") or "").strip()
    if direct:
        return direct
    parts = []
    for item in response.get("output") or []:
        if item.get("type") != "message":
            continue
        for content in item.get("content") or []:
            text = str(content.get("text") or "").strip()
            if text:
                parts.append(text)
    return "\n".join(parts).strip()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_openai_responses_api_responds_with_openai_api_key():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY is required for the live Responses API check")

    client = OpenAIResponsesClient(
        api_key=api_key,
        model=os.getenv("OPENAI_RESPONSES_MODEL", "gpt-5.4-mini"),
        base_url=os.getenv("OPENAI_RESPONSES_BASE_URL", "https://api.openai.com/v1"),
    )

    response = await client.responses_create(
        instructions="Reply with exactly: OK",
        input=[
            {
                "role": "user",
                "content": [{"type": "input_text", "text": "Connectivity check."}],
            }
        ],
        max_output_tokens=32,
        store=False,
    )

    assert str(response.get("id") or "").startswith("resp")
    assert _response_text(response)
