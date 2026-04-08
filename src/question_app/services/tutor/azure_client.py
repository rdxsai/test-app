"""Shared Azure OpenAI APIM client for tutor services."""

import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx
import requests

logger = logging.getLogger(__name__)


class AzureAPIMClient:
    """Direct Azure OpenAI APIM client for chat completions and tool calls."""

    def __init__(
        self,
        endpoint: str,
        deployment: str,
        api_key: str,
        api_version: str = "2024-02-15-preview",
    ):
        self.endpoint = endpoint.rstrip("/")
        self.deployment = deployment
        self.api_key = api_key
        self.api_version = api_version
        self._reasoning = self._is_reasoning_model()
        if self._reasoning:
            logger.info(
                "Reasoning model detected: "
                f"{deployment} — using max_completion_tokens + reasoning_effort"
            )

    def _is_reasoning_model(self) -> bool:
        """Check if the deployment behaves like a reasoning model."""
        deployment = self.deployment.lower()
        return deployment.startswith(("gpt-5", "o1", "o3", "o4"))

    def chat(
        self,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        reasoning_effort: Optional[str] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Send a non-streaming chat completion request."""
        url = f"{self.endpoint}/deployments/{self.deployment}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Ocp-Apim-Subscription-Key": self.api_key,
        }
        params = {"api-version": self.api_version}

        payload: Dict[str, Any] = {"messages": messages}
        if self._reasoning:
            payload["max_completion_tokens"] = max(max_tokens * 5, 4000)
            payload["reasoning_effort"] = reasoning_effort or "low"
        else:
            payload["max_tokens"] = max_tokens
            payload["temperature"] = temperature

        if response_format:
            payload["response_format"] = response_format

        try:
            response = requests.post(
                url,
                headers=headers,
                params=params,
                json=payload,
                timeout=120,
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        except requests.exceptions.RequestException as exc:
            logger.error(f"Azure APIM request failed: {exc}")
            return (
                "I apologize, but I'm having trouble connecting right now. "
                "Please try again."
            )
        except (KeyError, IndexError) as exc:
            logger.error(f"Invalid response format: {exc}")
            return "I received an unexpected response format. Please try again."

    async def chat_stream_async(
        self,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AsyncGenerator[str, None]:
        """Yield streamed content deltas from Azure OpenAI."""
        url = f"{self.endpoint}/deployments/{self.deployment}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Ocp-Apim-Subscription-Key": self.api_key,
        }
        params = {"api-version": self.api_version}

        payload: Dict[str, Any] = {"messages": messages, "stream": True}
        if self._reasoning:
            payload["max_completion_tokens"] = max(max_tokens * 5, 4000)
            payload["reasoning_effort"] = "low"
            payload["stream_options"] = {"include_usage": True}
        else:
            payload["max_tokens"] = max_tokens
            payload["temperature"] = temperature

        try:
            timeout = httpx.Timeout(connect=10, read=120, write=10, pool=10)
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream(
                    "POST",
                    url,
                    headers=headers,
                    params=params,
                    json=payload,
                ) as response:
                    response.raise_for_status()
                    buffer = ""
                    async for raw_bytes in response.aiter_bytes():
                        buffer += raw_bytes.decode("utf-8", errors="replace")
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            line = line.strip()
                            if not line or not line.startswith("data: "):
                                continue
                            body = line[6:]
                            if body.strip() == "[DONE]":
                                return
                            try:
                                chunk = json.loads(body)
                                delta = chunk["choices"][0].get("delta", {})
                                content = delta.get("content")
                                if content:
                                    yield content
                            except (json.JSONDecodeError, KeyError, IndexError):
                                continue
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Azure streaming request failed with status "
                f"{exc.response.status_code}: {exc}"
            )
            yield (
                "I apologize, but I'm having trouble connecting right now. "
                "Please try again."
            )
        except Exception as exc:
            logger.error(f"Azure streaming request failed: {exc}")
            yield (
                "I apologize, but I'm having trouble connecting right now. "
                "Please try again."
            )

    async def chat_with_tools(
        self,
        messages: List[Dict],
        tools: List[Dict],
        temperature: float = 0.3,
        max_tokens: int = 300,
        tool_choice: str = "auto",
        parallel_tool_calls: bool = True,
        reasoning_effort: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send a tool-enabled chat completion request."""
        url = f"{self.endpoint}/deployments/{self.deployment}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Ocp-Apim-Subscription-Key": self.api_key,
        }
        params = {"api-version": self.api_version}
        payload: Dict[str, Any] = {
            "messages": messages,
            "tools": tools,
            "tool_choice": tool_choice,
            "parallel_tool_calls": parallel_tool_calls,
        }
        if self._reasoning:
            payload["max_completion_tokens"] = max(max_tokens * 5, 4000)
            payload["reasoning_effort"] = reasoning_effort or "low"
        else:
            payload["max_tokens"] = max_tokens
            payload["temperature"] = temperature

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                headers=headers,
                params=params,
                json=payload,
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]

    def make_request(self, prompt: str) -> Dict[str, Any]:
        """Compatibility helper for code paths expecting raw-like responses."""
        try:
            response = self.chat([{"role": "user", "content": prompt}])
            return {"choices": [{"message": {"content": response}}]}
        except Exception as exc:
            logger.error(f"Make request failed: {exc}")
            return {"choices": [{"message": {"content": f"Error: {exc}"}}]}
