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
MAX_REASONING_COMPLETION_TOKENS = 12000
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
        self.last_request_metadata: Dict[str, Any] = {}
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

    def _build_chat_url(self) -> str:
        return f"{self.endpoint}/deployments/{self.deployment}/chat/completions"

    def _build_responses_urls(self) -> List[str]:
        base = self.endpoint.rstrip("/")
        if base.endswith("/responses"):
            candidates = [base]
        elif base.endswith("/v1"):
            candidates = [f"{base}/responses"]
        else:
            candidates = [
                f"{base}/v1/responses",
                f"{base}/openai/v1/responses",
                f"{base}/deployments/{self.deployment}/responses",
                f"{base}/openai/deployments/{self.deployment}/responses",
                f"{base}/responses",
            ]
        deduped: List[str] = []
        for candidate in candidates:
            if candidate not in deduped:
                deduped.append(candidate)
        return deduped

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
                return min(
                    max(requested * 2, SHORT_REASONING_COMPLETION_TOKENS),
                    MEDIUM_REASONING_COMPLETION_TOKENS,
                )
            if requested <= 400:
                return min(
                    max(requested * 2, MEDIUM_REASONING_COMPLETION_TOKENS),
                    DEFAULT_REASONING_COMPLETION_TOKENS,
                )
            return min(
                max(requested, DEFAULT_REASONING_COMPLETION_TOKENS),
                MAX_REASONING_COMPLETION_TOKENS,
            )
        if effort == "medium":
            if requested <= 200:
                return min(max(requested * 3, MEDIUM_REASONING_COMPLETION_TOKENS), 1600)
            return min(max(requested * 2, 1600), MAX_REASONING_COMPLETION_TOKENS)
        if requested <= 200:
            return min(
                max(requested * 4, DEFAULT_REASONING_COMPLETION_TOKENS),
                MAX_REASONING_COMPLETION_TOKENS,
            )
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
        started = time.perf_counter()
        url = self._build_chat_url()
        headers = self._build_headers()
        params = {"api-version": self.api_version}

        payload: Dict[str, Any] = {"messages": messages}
        if self._reasoning:
            normalized_effort = self._normalize_reasoning_effort(reasoning_effort)
            payload[
                "max_completion_tokens"
            ] = self._resolve_reasoning_completion_tokens(
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
        self.last_request_metadata = {
            "api": "chat_completions",
            "deployment": self.deployment,
            "endpoint": url,
            "api_version": self.api_version,
            "reasoning_model": self._reasoning,
            "reasoning_effort": payload.get("reasoning_effort"),
            "requested_max_tokens": max_tokens,
            "resolved_max_completion_tokens": payload.get("max_completion_tokens"),
            "resolved_max_tokens": payload.get("max_tokens"),
            "temperature": payload.get("temperature"),
            "message_count": len(messages),
            "response_format": response_format,
            "timeout": {
                "connect_seconds": DEFAULT_CONNECT_TIMEOUT_SECONDS,
                "read_seconds": DEFAULT_READ_TIMEOUT_SECONDS,
            },
            "attempts": 0,
            "retry_errors": [],
            "status": "started",
        }
        for attempt in range(1, AZURE_REQUEST_RETRY_ATTEMPTS + 1):
            self.last_request_metadata["attempts"] = attempt
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
                self.last_request_metadata.update(
                    {
                        "status": "success",
                        "http_status": response.status_code,
                        "finish_reason": choice.get("finish_reason"),
                        "usage": result.get("usage", {}),
                        "response_id": result.get("id"),
                        "content_chars": len(content),
                        "elapsed_seconds": round(time.perf_counter() - started, 2),
                    }
                )
                if not content:
                    logger.warning(
                        "Azure APIM returned empty content: deployment=%s finish_reason=%s usage=%s",
                        self.deployment,
                        choice.get("finish_reason"),
                        result.get("usage", {}),
                    )
                return content
            except (
                requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectionError,
            ) as exc:
                self.last_request_metadata.setdefault("retry_errors", []).append(
                    {
                        "attempt": attempt,
                        "type": exc.__class__.__name__,
                        "message": str(exc),
                    }
                )
                logger.warning(
                    "Azure APIM request attempt %d/%d failed for deployment=%s: %s",
                    attempt,
                    AZURE_REQUEST_RETRY_ATTEMPTS,
                    self.deployment,
                    exc,
                )
                if attempt == AZURE_REQUEST_RETRY_ATTEMPTS:
                    logger.error(f"Azure APIM request failed: {exc}")
                    self.last_request_metadata.update(
                        {
                            "status": "connection_error",
                            "fallback_returned": True,
                            "error": str(exc),
                            "elapsed_seconds": round(
                                time.perf_counter() - started,
                                2,
                            ),
                        }
                    )
                    return (
                        "I apologize, but I'm having trouble connecting right now. "
                        "Please try again."
                    )
                time.sleep(float(attempt))
            except requests.exceptions.RequestException as exc:
                logger.error(f"Azure APIM request failed: {exc}")
                self.last_request_metadata.update(
                    {
                        "status": "request_error",
                        "fallback_returned": True,
                        "error": str(exc),
                        "elapsed_seconds": round(time.perf_counter() - started, 2),
                    }
                )
                return (
                    "I apologize, but I'm having trouble connecting right now. "
                    "Please try again."
                )
            except (KeyError, IndexError) as exc:
                logger.error(f"Invalid response format: {exc}")
                self.last_request_metadata.update(
                    {
                        "status": "invalid_response",
                        "fallback_returned": True,
                        "error": str(exc),
                        "elapsed_seconds": round(time.perf_counter() - started, 2),
                    }
                )
                return "I received an unexpected response format. Please try again."

    async def chat_stream_async(
        self,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AsyncGenerator[str, None]:
        """Yield streamed content deltas from Azure OpenAI."""
        url = self._build_chat_url()
        headers = self._build_headers()
        params = {"api-version": self.api_version}

        payload: Dict[str, Any] = {"messages": messages, "stream": True}
        if self._reasoning:
            payload["reasoning_effort"] = "low"
            payload[
                "max_completion_tokens"
            ] = self._resolve_reasoning_completion_tokens(
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
            except (
                httpx.ReadTimeout,
                httpx.ConnectError,
                httpx.RemoteProtocolError,
            ) as exc:
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
        started = time.perf_counter()
        url = self._build_chat_url()
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
            payload[
                "max_completion_tokens"
            ] = self._resolve_reasoning_completion_tokens(
                max_tokens=max_tokens,
                reasoning_effort=normalized_effort,
            )
            payload["reasoning_effort"] = normalized_effort
        else:
            payload["max_tokens"] = max_tokens
            payload["temperature"] = temperature

        self.last_request_metadata = {
            "api": "chat_completions",
            "deployment": self.deployment,
            "endpoint": url,
            "api_version": self.api_version,
            "reasoning_model": self._reasoning,
            "reasoning_effort": payload.get("reasoning_effort"),
            "requested_max_tokens": max_tokens,
            "resolved_max_completion_tokens": payload.get("max_completion_tokens"),
            "resolved_max_tokens": payload.get("max_tokens"),
            "temperature": payload.get("temperature"),
            "message_count": len(messages),
            "tool_count": len(tools),
            "tool_choice": tool_choice,
            "parallel_tool_calls": parallel_tool_calls,
            "attempts": 1,
            "status": "started",
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    url,
                    headers=headers,
                    params=params,
                    json=payload,
                )
                response.raise_for_status()
                result = response.json()
                choice = result["choices"][0]
                message = choice["message"]
                self.last_request_metadata.update(
                    {
                        "status": "success",
                        "http_status": response.status_code,
                        "finish_reason": choice.get("finish_reason"),
                        "usage": result.get("usage", {}),
                        "response_id": result.get("id"),
                        "tool_call_count": len(message.get("tool_calls") or []),
                        "content_chars": len((message.get("content") or "").strip()),
                        "elapsed_seconds": round(time.perf_counter() - started, 2),
                    }
                )
                return message
            except (httpx.HTTPError, KeyError, IndexError) as exc:
                status_code = getattr(
                    getattr(exc, "response", None), "status_code", None
                )
                self.last_request_metadata.update(
                    {
                        "status": "error",
                        "http_status": status_code,
                        "error": str(exc),
                        "elapsed_seconds": round(time.perf_counter() - started, 2),
                    }
                )
                raise

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
        """Send a Responses API request via Azure APIM/OpenAI-compatible routing."""
        started = time.perf_counter()
        headers = self._build_headers()
        params = {"api-version": self.api_version} if self.api_version else None
        payload: Dict[str, Any] = {
            "model": self.deployment,
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
            payload["max_output_tokens"] = (
                self._resolve_reasoning_completion_tokens(
                    max_tokens=max_output_tokens,
                    reasoning_effort=reasoning_effort,
                )
                if self._reasoning
                else max_output_tokens
            )
        if self._reasoning:
            payload["reasoning"] = {
                "effort": self._normalize_reasoning_effort(reasoning_effort)
            }

        timeout = httpx.Timeout(
            connect=DEFAULT_CONNECT_TIMEOUT_SECONDS,
            read=DEFAULT_READ_TIMEOUT_SECONDS,
            write=DEFAULT_WRITE_TIMEOUT_SECONDS,
            pool=DEFAULT_POOL_TIMEOUT_SECONDS,
        )
        candidate_urls = self._build_responses_urls()
        self.last_request_metadata = {
            "api": "responses",
            "deployment": self.deployment,
            "api_version": self.api_version,
            "reasoning_model": self._reasoning,
            "reasoning_effort": payload.get("reasoning", {}).get("effort"),
            "requested_max_output_tokens": max_output_tokens,
            "resolved_max_output_tokens": payload.get("max_output_tokens"),
            "input_item_count": len(input),
            "tool_count": len(tools or []),
            "tool_choice": tool_choice,
            "parallel_tool_calls": parallel_tool_calls,
            "max_tool_calls": max_tool_calls,
            "store": store,
            "candidate_urls": candidate_urls,
            "attempted_urls": [],
            "attempts": 0,
            "retry_errors": [],
            "status": "started",
        }
        last_http_error: Optional[httpx.HTTPStatusError] = None
        async with httpx.AsyncClient(timeout=timeout) as client:
            for url in candidate_urls:
                self.last_request_metadata["attempts"] += 1
                self.last_request_metadata.setdefault("attempted_urls", []).append(url)
                try:
                    response = await client.post(
                        url,
                        headers=headers,
                        params=params,
                        json=payload,
                    )
                    response.raise_for_status()
                    result = response.json()
                    self.last_request_metadata.update(
                        {
                            "status": "success",
                            "endpoint": url,
                            "http_status": response.status_code,
                            "response_id": result.get("id"),
                            "usage": result.get("usage", {}),
                            "output_item_types": [
                                item.get("type")
                                for item in result.get("output", [])
                                if isinstance(item, dict)
                            ],
                            "elapsed_seconds": round(
                                time.perf_counter() - started,
                                2,
                            ),
                        }
                    )
                    return result
                except httpx.HTTPStatusError as exc:
                    last_http_error = exc
                    self.last_request_metadata.setdefault("retry_errors", []).append(
                        {
                            "url": url,
                            "status_code": exc.response.status_code,
                            "type": exc.__class__.__name__,
                            "message": str(exc),
                        }
                    )
                    if exc.response.status_code == 404:
                        logger.warning(
                            "Azure Responses request path not found for deployment=%s url=%s",
                            self.deployment,
                            url,
                        )
                        continue
                    self.last_request_metadata.update(
                        {
                            "status": "http_error",
                            "endpoint": url,
                            "http_status": exc.response.status_code,
                            "error": str(exc),
                            "elapsed_seconds": round(
                                time.perf_counter() - started,
                                2,
                            ),
                        }
                    )
                    raise
                except httpx.HTTPError as exc:
                    self.last_request_metadata.setdefault("retry_errors", []).append(
                        {
                            "url": url,
                            "type": exc.__class__.__name__,
                            "message": str(exc),
                        }
                    )
                    self.last_request_metadata.update(
                        {
                            "status": "transport_error",
                            "endpoint": url,
                            "error": str(exc),
                            "elapsed_seconds": round(
                                time.perf_counter() - started,
                                2,
                            ),
                        }
                    )
                    raise

        if last_http_error is not None:
            self.last_request_metadata.update(
                {
                    "status": "http_error",
                    "http_status": last_http_error.response.status_code,
                    "error": str(last_http_error),
                    "elapsed_seconds": round(time.perf_counter() - started, 2),
                }
            )
            raise last_http_error
        self.last_request_metadata.update(
            {
                "status": "runtime_error",
                "error": "No Responses API request was sent.",
                "elapsed_seconds": round(time.perf_counter() - started, 2),
            }
        )
        raise RuntimeError(
            "Azure Responses request failed before an HTTP response was returned."
        )

    def make_request(self, prompt: str) -> Dict[str, Any]:
        """Compatibility helper for code paths expecting raw-like responses."""
        try:
            response = self.chat([{"role": "user", "content": prompt}])
            return {"choices": [{"message": {"content": response}}]}
        except Exception as exc:
            logger.error(f"Make request failed: {exc}")
            return {"choices": [{"message": {"content": f"Error: {exc}"}}]}


def build_graph_responses_client(
    *,
    azure_config: Dict[str, Any],
    responses_deployment: str,
    enabled: bool = True,
) -> Optional[AzureAPIMClient]:
    """Build the Azure/APIM Responses client used by graph retrieval only."""
    if not enabled:
        return None
    return AzureAPIMClient(
        endpoint=azure_config["endpoint"],
        deployment=responses_deployment,
        api_key=azure_config["api_key"],
        api_version=azure_config.get("api_version", "2024-02-15-preview"),
        content_filter_policy=azure_config.get("content_filter_policy"),
    )
