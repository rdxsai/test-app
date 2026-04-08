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

# Prefixes that indicate "no results" from the MCP server.
# These are checked against the start of the response only; deep WCAG content
# can legitimately contain phrases like "No results returned" in examples.
NO_RESULT_PREFIXES = (
    "no success criteria found",
    "no techniques found",
    "no glossary terms found",
    "no glossary term found",
    "no results",
)


def is_no_result_text(text: Optional[str]) -> bool:
    """Return True only when the MCP response is an actual empty-result payload."""
    if not text:
        return True
    normalized = text.strip().lower()
    return any(normalized.startswith(prefix) for prefix in NO_RESULT_PREFIXES)

# ---------------------------------------------------------------------------
# OpenAI function-calling tool definitions
# ---------------------------------------------------------------------------

# Instance A keeps a narrower lookup-oriented tool surface.
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
    {
        "type": "function",
        "function": {
            "name": "list_principles",
            "description": (
                "Lists all four WCAG 2.2 principles (Perceivable, Operable, "
                "Understandable, Robust) with their descriptions. Use for "
                "structural/overview questions about WCAG organization."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_guidelines",
            "description": (
                "Lists WCAG 2.2 guidelines, optionally filtered by principle "
                "number (1=Perceivable, 2=Operable, 3=Understandable, 4=Robust). "
                "Use to show the guideline structure under a principle."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "principle": {
                        "type": "string",
                        "description": "Filter by principle number (1-4). Omit to list all.",
                        "enum": ["1", "2", "3", "4"],
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_criteria_by_level",
            "description": (
                "Gets all success criteria for a specific conformance level "
                "(A, AA, or AAA). Use to show what each level requires."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {
                        "type": "string",
                        "description": "Conformance level to retrieve",
                        "enum": ["A", "AA", "AAA"],
                    },
                    "include_lower": {
                        "type": "boolean",
                        "description": "If true, includes criteria from lower levels (e.g., AA returns both A and AA)",
                    },
                },
                "required": ["level"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "count_criteria",
            "description": (
                "Returns counts of success criteria grouped by level, principle, "
                "or guideline. Use for quick statistical overview of WCAG structure."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "group_by": {
                        "type": "string",
                        "description": "How to group the counts",
                        "enum": ["level", "principle", "guideline"],
                    }
                },
                "required": ["group_by"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_guideline",
            "description": (
                "Gets full details for a specific WCAG guideline including "
                "its description and all success criteria under it. "
                "Use when you need detail on a specific guideline (e.g., '1.1', '2.4')."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ref_id": {
                        "type": "string",
                        "description": "Guideline reference number, e.g. '1.1', '2.4', '4.1'",
                    }
                },
                "required": ["ref_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_glossary_term",
            "description": (
                "Gets the official WCAG definition of a glossary term. "
                "Use for precise definitions of terms like 'programmatically determined', "
                "'text alternative', 'conformance', etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "term": {
                        "type": "string",
                        "description": "The term to look up, e.g. 'conformance', 'text alternative'",
                    }
                },
                "required": ["term"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "whats_new_in_wcag22",
            "description": (
                "Lists all success criteria that were added in WCAG 2.2 "
                "(not in 2.1 or 2.0). Use for questions about WCAG version differences."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]

# Instance B guided retrieval needs the richer tool surface already exposed by
# the MCP server so it can gather deeper teaching evidence when needed.
GUIDED_WCAG_TOOL_DEFINITIONS = WCAG_TOOL_DEFINITIONS + [
    {
        "type": "function",
        "function": {
            "name": "list_success_criteria",
            "description": (
                "Lists success criteria, optionally filtered by level, guideline, "
                "or principle. Use for structural overviews or compact SC lists."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {
                        "type": "string",
                        "description": "Optional conformance level filter",
                        "enum": ["A", "AA", "AAA"],
                    },
                    "guideline": {
                        "type": "string",
                        "description": "Optional guideline reference, e.g. '1.1' or '4.1'",
                    },
                    "principle": {
                        "type": "string",
                        "description": "Optional principle number filter (1-4)",
                        "enum": ["1", "2", "3", "4"],
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_success_criteria_detail",
            "description": (
                "Gets the normative text and basic metadata for a specific WCAG "
                "success criterion. Use for compact SC detail without the full "
                "Understanding document."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ref_id": {
                        "type": "string",
                        "description": "The WCAG SC number, e.g. '4.1.3'",
                    }
                },
                "required": ["ref_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_criterion",
            "description": (
                "Gets the full WCAG success criterion detail including richer "
                "Understanding content, examples, intent, and boundaries. Use when "
                "the lesson needs deep explanatory support for a specific SC."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ref_id": {
                        "type": "string",
                        "description": "The WCAG SC number, e.g. '4.1.3'",
                    }
                },
                "required": ["ref_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_techniques_for_criterion",
            "description": (
                "Gets the technique set for a specific WCAG success criterion, "
                "including sufficient, advisory, and failure techniques."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ref_id": {
                        "type": "string",
                        "description": "The WCAG SC number, e.g. '4.1.3'",
                    }
                },
                "required": ["ref_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_technique",
            "description": (
                "Gets details for a specific WCAG technique or failure by ID, "
                "such as 'ARIA22' or 'F103'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "Technique or failure ID, e.g. 'ARIA22' or 'F103'",
                    }
                },
                "required": ["id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_glossary",
            "description": (
                "Searches the WCAG glossary by keyword. Use to discover official "
                "glossary terms before fetching one directly."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Keywords to search for in glossary terms and definitions",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_glossary_terms",
            "description": (
                "Lists glossary terms available in WCAG. Use only when you need a "
                "broad glossary inventory."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]

# Map OpenAI function names → (MCP tool name, param remapping function)
_TOOL_NAME_TO_MCP = {
    "search_wcag": ("search-wcag", lambda args: {"query": args["query"]}),
    "search_techniques": ("search-techniques", lambda args: {"query": args["query"]}),
    "get_full_criterion_context": ("get-full-criterion-context", lambda args: {"ref_id": args["ref_id"]}),
    "list_principles": ("list-principles", lambda args: {}),
    "list_guidelines": ("list-guidelines", lambda args: {k: v for k, v in args.items() if v}),
    "get_criteria_by_level": ("get-criteria-by-level", lambda args: args),
    "count_criteria": ("count-criteria", lambda args: args),
    "get_guideline": ("get-guideline", lambda args: {"ref_id": args["ref_id"]}),
    "get_glossary_term": ("get-glossary-term", lambda args: {"term": args["term"]}),
    "whats_new_in_wcag22": ("whats-new-in-wcag22", lambda args: {}),
    "list_success_criteria": ("list-success-criteria", lambda args: {k: v for k, v in args.items() if v}),
    "get_success_criteria_detail": ("get-success-criteria-detail", lambda args: {"ref_id": args["ref_id"]}),
    "get_criterion": ("get-criterion", lambda args: {"ref_id": args["ref_id"]}),
    "get_technique": ("get-technique", lambda args: {"id": args.get("id", args.get("ref_id", ""))}),
    "get_techniques_for_criterion": ("get-techniques-for-criterion", lambda args: {"ref_id": args["ref_id"]}),
    "search_glossary": ("search-glossary", lambda args: {"query": args["query"]}),
    "list_glossary_terms": ("list-glossary-terms", lambda args: {}),
}


"""
Deterministic filters for retrieval pipeline.

These prevent known-bad tool calls from wasting MCP round trips.
The WCAG glossary only contains specialized technical terms, NOT
structural vocabulary. This blocklist is maintained from observed
failures in pipeline traces.
"""

# Terms that are NOT in the WCAG 2.2 glossary and will always return
# "Not found". Kept as lowercase for case-insensitive matching.
GLOSSARY_BLOCKLIST = frozenset({
    "principle",
    "guideline",
    "success criterion",
    "success criteria",
    "conformance level",
    "level a",
    "level aa",
    "level aaa",
    "sufficient techniques",
    "sufficient technique",
    "advisory techniques",
    "advisory technique",
    "failure techniques",
    "failure technique",
    "normative",
    "informative",
})


def filter_glossary_call(term: str) -> bool:
    """Return True if the glossary term is safe to call, False if it's in the blocklist."""
    return term.strip().lower() not in GLOSSARY_BLOCKLIST


def normalize_tool_args(fn_name: str, fn_args: dict) -> dict:
    """Normalize tool call arguments to prevent common LLM formatting errors.

    Fixes observed in pipeline traces:
    - list_success_criteria(guideline="1.4 Distinguishable") → guideline="1.4"
    - get_guideline(ref_id="1.4 Distinguishable") → ref_id="1.4"
    - get_criterion(ref_id="SC 1.4.3") → ref_id="1.4.3"
    - get_criterion(id="1.4.3") → ref_id="1.4.3"  (wrong key name)
    - get_technique(ref_id="H37") → id="H37"  (wrong key name)
    """
    import re
    args = dict(fn_args)  # don't mutate the original

    # Fix wrong key names: LLM sometimes uses "id" instead of "ref_id" or vice versa
    # Tools that expect ref_id: get_criterion, get_guideline, get_success_criteria_detail,
    #   get_full_criterion_context, get_techniques_for_criterion, get_failures_for_criterion
    # Tools that expect id: get_technique
    NEEDS_REF_ID = {
        "get_criterion", "get_guideline", "get_success_criteria_detail",
        "get_full_criterion_context", "get_techniques_for_criterion",
        "get_failures_for_criterion",
    }
    NEEDS_ID = {"get_technique"}

    if fn_name in NEEDS_REF_ID and "id" in args and "ref_id" not in args:
        args["ref_id"] = args.pop("id")
    elif fn_name in NEEDS_ID and "ref_id" in args and "id" not in args:
        args["id"] = args.pop("ref_id")

    # Strip descriptive text from ref_id and guideline args
    # "1.4 Distinguishable" → "1.4", "SC 1.4.3" → "1.4.3"
    for key in ("ref_id", "guideline"):
        if key in args and isinstance(args[key], str):
            # Extract the WCAG-style numeric ref (e.g., 1.4.3, 2.1, 1.4)
            match = re.search(r'\b(\d+(?:\.\d+){1,2})\b', args[key])
            if match:
                args[key] = match.group(1)

    return args


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
    # Deterministic tool execution (plan-driven, no LLM in loop)
    # ------------------------------------------------------------------

    async def execute_planned_tool_calls(
        self, planned_calls: List[Dict],
    ) -> List[Dict]:
        """Execute pre-planned tool calls deterministically against WCAG MCP.

        Unlike get_wcag_context() which uses an LLM to choose tools, this
        method takes an explicit list from the retrieval planner and executes
        them directly. No LLM is involved.

        Args:
            planned_calls: List of dicts, each with:
                - "tool": function name (e.g., "search_wcag", "get_criterion")
                - "args": dict of arguments
                - "category": "must_have" | "fallback" | "optional" (for logging)

        Returns:
            List of result dicts with:
                tool, args, category, result (str), chars (int),
                status ("HIT" | "MISS" | "BLOCKED" | "ERROR")
        """
        async def _execute_one(i: int, tc: Dict[str, Any]) -> Dict[str, Any]:
            fn_name = tc.get("tool", "")
            fn_args = tc.get("args", {})
            category = tc.get("category", "must_have")

            # Glossary blocklist
            if fn_name == "get_glossary_term" and "term" in fn_args:
                if not filter_glossary_call(fn_args["term"]):
                    logger.info(f"Pipeline: blocked glossary lookup '{fn_args['term']}' (blocklist)")
                    return {
                        "tool": fn_name, "args": fn_args, "category": category,
                        "result": f"BLOCKED: '{fn_args['term']}' not in WCAG glossary",
                        "chars": 0, "status": "BLOCKED",
                    }

            # Normalize args (id<->ref_id, strip descriptive text)
            fn_args = normalize_tool_args(fn_name, fn_args)

            # Look up MCP mapping
            mapping = _TOOL_NAME_TO_MCP.get(fn_name)
            if not mapping:
                logger.warning(f"Pipeline: unknown tool '{fn_name}', skipping")
                return {
                    "tool": fn_name, "args": fn_args, "category": category,
                    "result": f"Unknown tool: {fn_name}", "chars": 0, "status": "ERROR",
                }

            mcp_tool_name, param_fn = mapping
            mcp_args = param_fn(fn_args)

            # Execute against MCP server
            text = await self._call_tool(mcp_tool_name, mcp_args)
            if text is None:
                text = ""

            is_empty = is_no_result_text(text)
            status = "MISS" if is_empty else "HIT"

            result = {
                "tool": fn_name, "args": fn_args, "category": category,
                "result": text, "chars": len(text), "status": status,
            }
            logger.info(
                f"Pipeline [{i+1}/{len(planned_calls)}] [{status}] "
                f"{fn_name}({fn_args}) -> {len(text)} chars"
            )
            return result

        if not planned_calls:
            return []

        raw_results = await asyncio.gather(
            *[_execute_one(i, tc) for i, tc in enumerate(planned_calls)],
            return_exceptions=True,
        )

        results = []
        for i, raw in enumerate(raw_results):
            if isinstance(raw, Exception):
                logger.warning(f"Pipeline tool execution raised: {raw}")
                tc = planned_calls[i]
                results.append(
                    {
                        "tool": tc.get("tool", ""),
                        "args": tc.get("args", {}),
                        "category": tc.get("category", "must_have"),
                        "result": f"Execution error: {raw}",
                        "chars": 0,
                        "status": "ERROR",
                    }
                )
            else:
                results.append(raw)

        return results

    # ------------------------------------------------------------------
    # LLM-driven tool calling (multi-turn with retry) — used by Instance A
    # ------------------------------------------------------------------

    async def _execute_tool_calls(self, tool_calls: List[Dict]) -> List[Dict]:
        """
        Execute tool_calls against MCP server concurrently.
        Returns list of {tool_call_id, fn_name, fn_args, mcp_result, is_empty}.

        Applies deterministic filters before execution:
        - Blocks glossary lookups for terms known to not exist in WCAG glossary
        - Normalizes tool arguments (strips descriptive text from ref_ids)
        """
        async def _execute_one(tc):
            fn_name = tc["function"]["name"]
            fn_args = json.loads(tc["function"]["arguments"])

            # --- Deterministic filter: block known-bad glossary calls ---
            if fn_name == "get_glossary_term" and "term" in fn_args:
                if not filter_glossary_call(fn_args["term"]):
                    logger.info(f"WCAG MCP: blocked glossary lookup for '{fn_args['term']}' (in blocklist)")
                    return {"tool_call_id": tc["id"], "fn_name": fn_name, "fn_args": fn_args,
                            "mcp_result": None, "is_empty": True,
                            "blocked": True, "block_reason": f"'{fn_args['term']}' is not in the WCAG glossary"}

            # --- Normalize arguments (fix LLM formatting errors) ---
            fn_args = normalize_tool_args(fn_name, fn_args)

            mapping = _TOOL_NAME_TO_MCP.get(fn_name)
            if not mapping:
                logger.warning(f"WCAG MCP: unknown function '{fn_name}'")
                return {"tool_call_id": tc["id"], "fn_name": fn_name, "fn_args": fn_args,
                        "mcp_result": None, "is_empty": True}
            mcp_tool_name, param_fn = mapping
            mcp_args = param_fn(fn_args)
            result = await self._call_tool(mcp_tool_name, mcp_args)
            is_empty = is_no_result_text(result)
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
