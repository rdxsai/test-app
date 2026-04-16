"""Shared Azure OpenAI APIM client for tutor services."""

import asyncio
import json
import logging
import time
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx
import requests

logger = logging.getLogger(__name__)

DEFAULT_REASONING_COMPLETION_TOKENS = 1200
MAX_REASONING_COMPLETION_TOKENS = 6000
SHORT_REASONING_COMPLETION_TOKENS = 400
MEDIUM_REASONING_COMPLETION_TOKENS = 800
DEFAULT_CONNECT_TIMEOUT_SECONDS = 10
DEFAULT_READ_TIMEOUT_SECONDS = 180
DEFAULT_WRITE_TIMEOUT_SECONDS = 10
DEFAULT_POOL_TIMEOUT_SECONDS = 10
AZURE_REQUEST_RETRY_ATTEMPTS = 2


class AzureAPIMClient:
    """Direct Azure OpenAI APIM client for chat completions and tool calls."""

    def __init__(
        self,
        endpoint: str,
        deployment: str,
        api_key: str,
        api_version: str = "2024-02-15-preview",
        content_filter_policy: Optional[str] = None,
    ):
        self.endpoint = endpoint.rstrip("/")
        self.deployment = deployment
        self.api_key = api_key
        self.api_version = api_version
        self.content_filter_policy = (content_filter_policy or "").strip() or None
        self._reasoning = self._is_reasoning_model()
        if self._reasoning:
            logger.info(
                "Reasoning model detected: "
                f"{deployment} — using max_completion_tokens + reasoning_effort"
            )

    def _build_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Ocp-Apim-Subscription-Key": self.api_key,
        }
        if self.content_filter_policy:
            headers["x-policy-id"] = self.content_filter_policy
        return headers

    def _is_reasoning_model(self) -> bool:
        """Check if the deployment behaves like a reasoning model."""
        deployment = self.deployment.lower()
        return deployment.startswith(("gpt-5", "o1", "o3", "o4"))

    @staticmethod
    def _normalize_reasoning_effort(reasoning_effort: Optional[str]) -> str:
        effort = (reasoning_effort or "low").strip().lower()
        if effort not in {"low", "medium", "high"}:
            return "low"
        return effort

    def _resolve_reasoning_completion_tokens(
        self,
        max_tokens: int,
        reasoning_effort: Optional[str] = None,
    ) -> int:
        effort = self._normalize_reasoning_effort(reasoning_effort)
        requested = max(1, int(max_tokens or 0))
        if effort == "low":
            if requested <= 150:
                return min(max(requested * 2, SHORT_REASONING_COMPLETION_TOKENS), MEDIUM_REASONING_COMPLETION_TOKENS)
            if requested <= 400:
                return min(max(requested * 2, MEDIUM_REASONING_COMPLETION_TOKENS), DEFAULT_REASONING_COMPLETION_TOKENS)
            return min(max(requested, DEFAULT_REASONING_COMPLETION_TOKENS), MAX_REASONING_COMPLETION_TOKENS)
        if effort == "medium":
            if requested <= 200:
                return min(max(requested * 3, MEDIUM_REASONING_COMPLETION_TOKENS), 1600)
            return min(max(requested * 2, 1600), MAX_REASONING_COMPLETION_TOKENS)
        if requested <= 200:
            return min(max(requested * 4, DEFAULT_REASONING_COMPLETION_TOKENS), MAX_REASONING_COMPLETION_TOKENS)
        return min(max(requested * 3, 2000), MAX_REASONING_COMPLETION_TOKENS)

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
        headers = self._build_headers()
        params = {"api-version": self.api_version}

        payload: Dict[str, Any] = {"messages": messages}
        if self._reasoning:
            normalized_effort = self._normalize_reasoning_effort(reasoning_effort)
            payload["max_completion_tokens"] = self._resolve_reasoning_completion_tokens(
                max_tokens=max_tokens,
                reasoning_effort=normalized_effort,
            )
            payload["reasoning_effort"] = normalized_effort
        else:
            payload["max_tokens"] = max_tokens
            payload["temperature"] = temperature

        if response_format:
            payload["response_format"] = response_format

        timeout = (DEFAULT_CONNECT_TIMEOUT_SECONDS, DEFAULT_READ_TIMEOUT_SECONDS)
        for attempt in range(1, AZURE_REQUEST_RETRY_ATTEMPTS + 1):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    params=params,
                    json=payload,
                    timeout=timeout,
                )
                response.raise_for_status()
                result = response.json()
                choice = result["choices"][0]
                message = choice["message"]
                content = (message.get("content") or "").strip()
                if not content:
                    logger.warning(
                        "Azure APIM returned empty content: deployment=%s finish_reason=%s usage=%s",
                        self.deployment,
                        choice.get("finish_reason"),
                        result.get("usage", {}),
                    )
                return content
            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as exc:
                logger.warning(
                    "Azure APIM request attempt %d/%d failed for deployment=%s: %s",
                    attempt,
                    AZURE_REQUEST_RETRY_ATTEMPTS,
                    self.deployment,
                    exc,
                )
                if attempt == AZURE_REQUEST_RETRY_ATTEMPTS:
                    logger.error(f"Azure APIM request failed: {exc}")
                    return (
                        "I apologize, but I'm having trouble connecting right now. "
                        "Please try again."
                    )
                time.sleep(float(attempt))
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
        headers = self._build_headers()
        params = {"api-version": self.api_version}

        payload: Dict[str, Any] = {"messages": messages, "stream": True}
        if self._reasoning:
            payload["reasoning_effort"] = "low"
            payload["max_completion_tokens"] = self._resolve_reasoning_completion_tokens(
                max_tokens=max_tokens,
                reasoning_effort=payload["reasoning_effort"],
            )
            payload["stream_options"] = {"include_usage": True}
        else:
            payload["max_tokens"] = max_tokens
            payload["temperature"] = temperature

        timeout = httpx.Timeout(
            connect=DEFAULT_CONNECT_TIMEOUT_SECONDS,
            read=DEFAULT_READ_TIMEOUT_SECONDS,
            write=DEFAULT_WRITE_TIMEOUT_SECONDS,
            pool=DEFAULT_POOL_TIMEOUT_SECONDS,
        )
        for attempt in range(1, AZURE_REQUEST_RETRY_ATTEMPTS + 1):
            try:
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
                return
            except (httpx.ReadTimeout, httpx.ConnectError, httpx.RemoteProtocolError) as exc:
                logger.warning(
                    "Azure streaming request attempt %d/%d failed for deployment=%s: %s",
                    attempt,
                    AZURE_REQUEST_RETRY_ATTEMPTS,
                    self.deployment,
                    exc,
                )
                if attempt == AZURE_REQUEST_RETRY_ATTEMPTS:
                    logger.error(f"Azure streaming request failed: {exc}")
                    yield (
                        "I apologize, but I'm having trouble connecting right now. "
                        "Please try again."
                    )
                    return
                await asyncio.sleep(float(attempt))
            except httpx.HTTPStatusError as exc:
                logger.error(
                    "Azure streaming request failed with status "
                    f"{exc.response.status_code}: {exc}"
                )
                yield (
                    "I apologize, but I'm having trouble connecting right now. "
                    "Please try again."
                )
                return
            except Exception as exc:
                logger.error(f"Azure streaming request failed: {exc}")
                yield (
                    "I apologize, but I'm having trouble connecting right now. "
                    "Please try again."
                )
                return

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
        headers = self._build_headers()
        params = {"api-version": self.api_version}
        payload: Dict[str, Any] = {
            "messages": messages,
            "tools": tools,
            "tool_choice": tool_choice,
            "parallel_tool_calls": parallel_tool_calls,
        }
        if self._reasoning:
            normalized_effort = self._normalize_reasoning_effort(reasoning_effort)
            payload["max_completion_tokens"] = self._resolve_reasoning_completion_tokens(
                max_tokens=max_tokens,
                reasoning_effort=normalized_effort,
            )
            payload["reasoning_effort"] = normalized_effort
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
