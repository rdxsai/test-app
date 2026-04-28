import os

import pytest
from dotenv import load_dotenv

from question_app.services.tutor.azure_client import AzureAPIMClient


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
async def test_azure_responses_api_responds_with_gpt54_deployment():
    load_dotenv()
    if os.getenv("RUN_LIVE_AZURE_RESPONSES_TEST", "").lower() != "true":
        pytest.skip("Set RUN_LIVE_AZURE_RESPONSES_TEST=true to call Azure live.")

    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_SUBSCRIPTION_KEY")
    if not endpoint or not api_key:
        pytest.skip("Azure endpoint and subscription key are required.")

    client = AzureAPIMClient(
        endpoint=os.getenv("AZURE_OPENAI_RESPONSES_ENDPOINT", endpoint),
        deployment=os.getenv(
            "AZURE_OPENAI_RESPONSES_DEPLOYMENT_ID",
            os.getenv("OPENAI_RESPONSES_MODEL", "gpt-5.4"),
        ),
        api_key=api_key,
        api_version=os.getenv("AZURE_OPENAI_RESPONSES_API_VERSION", "preview"),
        content_filter_policy=os.getenv("AZURE_OPENAI_CONTENT_FILTER_POLICY"),
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
