"""
WCAG MCP Client — LLM-driven tool calling integration.

Connects to the wcag-guidelines-mcp stdio server (Node.js) and uses
Azure OpenAI function calling to decide which tools to invoke based
on the student's query. The LLM semantically translates natural language
into precise MCP tool calls (e.g., "make images accessible" → SC 1.1.1).

The subprocess stays alive for the app lifetime; concurrent callers
are serialized by an asyncio.Lock so we never double-initialize.
"""

import asyncio
import json
import logging
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)

# Phrases that indicate "no results" from the MCP server
NO_RESULT_PHRASES = ("no success criteria found", "no techniques found", "no results")

# ---------------------------------------------------------------------------
# OpenAI function-calling tool definitions for the 3 MCP tools we use
# ---------------------------------------------------------------------------
WCAG_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_wcag",
            "description": (
                "Search WCAG 2.2 success criteria by keyword. Use for broad "
                "topic searches like 'color contrast', 'keyboard navigation', "
                "'text alternatives'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Keywords to search for in WCAG success criteria titles and descriptions",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_techniques",
            "description": (
                "Search WCAG techniques (e.g., H37, G94, ARIA1). Use when "
                "looking for implementation methods, HTML techniques, or ARIA patterns."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Keywords to search for in WCAG technique titles and descriptions",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_full_criterion_context",
            "description": (
                "Get the complete details of a specific WCAG success criterion "
                "by its number. Returns the full text, understanding docs, and "
                "related techniques. Use when you know the exact SC number."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ref_id": {
                        "type": "string",
                        "description": "The WCAG SC number, e.g. '1.1.1', '1.4.3', '2.1.1'",
                    }
                },
                "required": ["ref_id"],
            },
        },
    },
]

# Map OpenAI function names → (MCP tool name, param remapping function)
_TOOL_NAME_TO_MCP = {
    "search_wcag": ("search-wcag", lambda args: {"query": args["query"]}),
    "search_techniques": ("search-techniques", lambda args: {"query": args["query"]}),
    "get_full_criterion_context": ("get-full-criterion-context", lambda args: {"ref_id": args["ref_id"]}),
}


class WCAGMCPClient:
    """Async wrapper around the wcag-guidelines-mcp MCP server with LLM-driven tool selection."""

    def __init__(self, command: str = "wcag-guidelines-mcp", azure_client=None):
        self._command = command
        self._azure_client = azure_client  # AzureAPIMClient for function calling
        self._session: Optional[ClientSession] = None
        self._exit_stack: Optional[AsyncExitStack] = None
        self._connect_lock = asyncio.Lock()
        self._available_tools: List[str] = []

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    async def _ensure_connected(self) -> ClientSession:
        """Lazily start the MCP subprocess and return the session."""
        if self._session is not None:
            return self._session

        async with self._connect_lock:
            # Double-check after acquiring lock
            if self._session is not None:
                return self._session

            logger.info(f"Starting WCAG MCP server: {self._command}")
            self._exit_stack = AsyncExitStack()

            server_params = StdioServerParameters(
                command=self._command,
                args=[],
            )

            stdio_transport = await self._exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read_stream, write_stream = stdio_transport
            self._session = await self._exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )

            await self._session.initialize()

            # Discover available tools
            tools_result = await self._session.list_tools()
            self._available_tools = [t.name for t in tools_result.tools]
            logger.info(f"WCAG MCP connected. Available tools: {self._available_tools}")

            return self._session

    async def close(self):
        """Shut down the MCP subprocess cleanly."""
        if self._exit_stack:
            try:
                await self._exit_stack.aclose()
            except Exception as e:
                logger.warning(f"Error closing WCAG MCP: {e}")
            finally:
                self._session = None
                self._exit_stack = None

    # ------------------------------------------------------------------
    # Low-level tool call
    # ------------------------------------------------------------------

    async def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[str]:
        """Call an MCP tool and return the raw text response. Returns None on failure."""
        try:
            session = await self._ensure_connected()
            logger.info(f"WCAG MCP: calling {tool_name}({arguments})")
            result = await session.call_tool(tool_name, arguments)

            if not result.content:
                logger.info(f"WCAG MCP: {tool_name} returned empty content")
                return None

            text = result.content[0].text
            logger.info(f"WCAG MCP: {tool_name} returned {len(text)} chars: {text[:300]}")
            return text

        except Exception as e:
            logger.warning(f"WCAG MCP tool '{tool_name}' failed: {e}")
            return None

    # ------------------------------------------------------------------
    # LLM-driven tool calling (multi-turn with retry)
    # ------------------------------------------------------------------

    async def _execute_tool_calls(self, tool_calls: List[Dict]) -> List[Dict]:
        """
        Execute tool_calls against MCP server concurrently.
        Returns list of {tool_call_id, fn_name, fn_args, mcp_result, is_empty}.
        """
        async def _execute_one(tc):
            fn_name = tc["function"]["name"]
            fn_args = json.loads(tc["function"]["arguments"])
            mapping = _TOOL_NAME_TO_MCP.get(fn_name)
            if not mapping:
                logger.warning(f"WCAG MCP: unknown function '{fn_name}'")
                return {"tool_call_id": tc["id"], "fn_name": fn_name, "fn_args": fn_args,
                        "mcp_result": None, "is_empty": True}
            mcp_tool_name, param_fn = mapping
            mcp_args = param_fn(fn_args)
            result = await self._call_tool(mcp_tool_name, mcp_args)
            is_empty = not result or any(p in result.lower() for p in NO_RESULT_PHRASES)
            return {"tool_call_id": tc["id"], "fn_name": fn_name, "fn_args": fn_args,
                    "mcp_result": result, "is_empty": is_empty}

        raw = await asyncio.gather(
            *[_execute_one(tc) for tc in tool_calls],
            return_exceptions=True,
        )
        # Replace exceptions with empty results
        results = []
        for r in raw:
            if isinstance(r, Exception):
                logger.warning(f"WCAG MCP: tool execution raised: {r}")
                results.append({"tool_call_id": "", "fn_name": "?", "fn_args": {},
                                "mcp_result": None, "is_empty": True})
            else:
                results.append(r)
        return results

    async def get_wcag_context(self, student_query: str) -> str:
        """
        Main entry point for hybrid_system.py.

        Multi-turn function calling:
        1. Send query + tool schemas to LLM → get tool_calls
        2. Execute tool_calls against MCP
        3. If ALL results were empty, feed failures back to LLM → retry once
        4. Collect successful results and return
        """
        if not self._azure_client:
            logger.warning("WCAG MCP: no azure_client configured, skipping")
            return ""

        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a WCAG 2.2 expert. Given a student's question about web accessibility, "
                        "decide which WCAG tools to call to find the most relevant official guidelines.\n\n"
                        "IMPORTANT: You know WCAG well. When you can map a topic to specific SC numbers, "
                        "ALWAYS use get_full_criterion_context — it returns the richest data. Examples:\n"
                        "- alt text / text alternatives / images → 1.1.1\n"
                        "- color contrast → 1.4.3 (minimum) and/or 1.4.6 (enhanced)\n"
                        "- keyboard navigation → 2.1.1\n"
                        "- focus visible → 2.4.7\n"
                        "- page title → 2.4.2\n"
                        "- link purpose → 2.4.4\n"
                        "- captions / subtitles (prerecorded) → 1.2.2\n"
                        "- captions (live) → 1.2.4\n"
                        "- audio description / media alternatives → 1.2.3 and 1.2.5\n"
                        "- audio-only / video-only → 1.2.1\n"
                        "- error identification → 3.3.1\n"
                        "- name role value → 4.1.2\n\n"
                        "Use search_wcag or search_techniques for broader/exploratory queries where you "
                        "don't know the exact SC. You may call multiple tools.\n\n"
                        "If the question is NOT about web accessibility, do not call any tools."
                    ),
                },
                {"role": "user", "content": student_query},
            ]

            max_rounds = 2  # initial + 1 retry
            all_successful_sections = []

            for round_num in range(max_rounds):
                # Round 1: force tool use. Round 2 (retry): let LLM decide.
                choice = "required" if round_num == 0 else "auto"
                logger.info(f"WCAG MCP: round {round_num + 1}/{max_rounds} (tool_choice={choice})")

                response_msg = await self._azure_client.chat_with_tools(
                    messages=messages,
                    tools=WCAG_TOOL_DEFINITIONS,
                    temperature=0.0,
                    max_tokens=300,
                    tool_choice=choice,
                )

                tool_calls = response_msg.get("tool_calls")
                if not tool_calls:
                    logger.info("WCAG MCP: LLM returned no tool calls (query may be off-topic)")
                    break

                logger.info(f"WCAG MCP: LLM requested {len(tool_calls)} tool call(s): "
                            f"{[tc['function']['name'] for tc in tool_calls]}")

                # Execute all tool calls
                exec_results = await self._execute_tool_calls(tool_calls)

                # Collect successes
                successes = [r for r in exec_results if not r["is_empty"]]
                failures = [r for r in exec_results if r["is_empty"]]

                for r in successes:
                    all_successful_sections.append(r["mcp_result"])

                # If we got some results, or this is already the retry round, stop
                if successes or round_num == max_rounds - 1:
                    if failures and not successes:
                        logger.info(f"WCAG MCP: all {len(failures)} tool call(s) returned no results")
                    break

                # All calls failed — feed results back to LLM for retry
                logger.info(f"WCAG MCP: all {len(failures)} tool call(s) returned no results, "
                            f"feeding back to LLM for retry")

                # Append the assistant's tool_calls message
                messages.append(response_msg)

                # Append tool result messages (one per tool call)
                for r in exec_results:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": r["tool_call_id"],
                        "content": r["mcp_result"] or "No results found.",
                    })

                # Nudge the LLM to change strategy on retry
                messages.append({
                    "role": "user",
                    "content": (
                        "The search returned no results. The search tool only does literal substring "
                        "matching on SC titles, so natural language queries often miss. "
                        "If you can identify the relevant WCAG SC number from your knowledge, "
                        "use get_full_criterion_context with the SC number instead."
                    ),
                })

            combined = "\n\n".join(all_successful_sections)

            if combined:
                logger.info(f"WCAG MCP: returning {len(combined)} chars of context")
            else:
                logger.info("WCAG MCP: no relevant WCAG context found")

            return combined

        except Exception as e:
            logger.error(f"WCAG MCP get_wcag_context failed: {e}")
            return ""
