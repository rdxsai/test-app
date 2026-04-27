"""OpenAI-native Responses API client for graph-grounded retrieval.

This client is intentionally narrow. The rest of the tutor continues using the
Azure/APIM chat-completions client; only retrieval workers that need Responses
API tool-loop state should depend on this class.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

DEFAULT_CONNECT_TIMEOUT_SECONDS = 10
DEFAULT_READ_TIMEOUT_SECONDS = 180
DEFAULT_WRITE_TIMEOUT_SECONDS = 10
DEFAULT_POOL_TIMEOUT_SECONDS = 10


class OpenAIResponsesClient:
    """Small adapter exposing the same responses_create API used by graph workers."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str = "https://api.openai.com/v1",
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    def _build_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _build_url(self) -> str:
        return f"{self.base_url}/responses"

    async def responses_create(
        self,
        *,
        input: List[Dict[str, Any]],
        instructions: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        parallel_tool_calls: Optional[bool] = None,
        reasoning_effort: Optional[str] = None,
        max_output_tokens: Optional[int] = None,
        previous_response_id: Optional[str] = None,
        text: Optional[Dict[str, Any]] = None,
        include: Optional[List[str]] = None,
        store: Optional[bool] = None,
        max_tool_calls: Optional[int] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": self.model,
            "input": input,
        }
        if instructions is not None:
            payload["instructions"] = instructions
        if tools is not None:
            payload["tools"] = tools
        if tool_choice is not None:
            payload["tool_choice"] = tool_choice
        if parallel_tool_calls is not None:
            payload["parallel_tool_calls"] = parallel_tool_calls
        if previous_response_id is not None:
            payload["previous_response_id"] = previous_response_id
        if text is not None:
            payload["text"] = text
        if include is not None:
            payload["include"] = include
        if store is not None:
            payload["store"] = store
        if max_tool_calls is not None:
            payload["max_tool_calls"] = max_tool_calls
        if max_output_tokens is not None:
            payload["max_output_tokens"] = max_output_tokens
        if reasoning_effort is not None:
            payload["reasoning"] = {"effort": reasoning_effort}

        timeout = httpx.Timeout(
            connect=DEFAULT_CONNECT_TIMEOUT_SECONDS,
            read=DEFAULT_READ_TIMEOUT_SECONDS,
            write=DEFAULT_WRITE_TIMEOUT_SECONDS,
            pool=DEFAULT_POOL_TIMEOUT_SECONDS,
        )
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                self._build_url(),
                headers=self._build_headers(),
                json=payload,
            )
            response.raise_for_status()
            return response.json()
