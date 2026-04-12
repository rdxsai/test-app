import asyncio
import importlib
import sys
import types

import pytest


fake_mcp = types.ModuleType("mcp")


class _ClientSession:
    pass


class _StdioServerParameters:
    def __init__(self, command="", args=None):
        self.command = command
        self.args = args or []


fake_mcp.ClientSession = _ClientSession
fake_mcp.StdioServerParameters = _StdioServerParameters
sys.modules.setdefault("mcp", fake_mcp)

fake_mcp_client = types.ModuleType("mcp.client")
fake_mcp_stdio = types.ModuleType("mcp.client.stdio")


def _unused_stdio_client(*args, **kwargs):
    raise AssertionError("stdio_client should not be used in this unit test")


fake_mcp_stdio.stdio_client = _unused_stdio_client
sys.modules.setdefault("mcp.client", fake_mcp_client)
sys.modules.setdefault("mcp.client.stdio", fake_mcp_stdio)

wcag_mcp_client = importlib.import_module("question_app.services.wcag_mcp_client")
GUIDED_WCAG_TOOL_DEFINITIONS = wcag_mcp_client.GUIDED_WCAG_TOOL_DEFINITIONS
WCAGMCPClient = wcag_mcp_client.WCAGMCPClient


def test_guided_tool_definitions_expose_richer_retrieval_tools():
    tool_names = {
        tool_def["function"]["name"] for tool_def in GUIDED_WCAG_TOOL_DEFINITIONS
    }

    assert "get_criterion" in tool_names
    assert "get_techniques_for_criterion" in tool_names
    assert "get_technique" in tool_names
    assert "search_glossary" in tool_names
    assert "list_glossary_terms" in tool_names


def test_deterministic_router_maps_common_instance_a_topics():
    client = WCAGMCPClient()

    alt_text_calls = client._build_deterministic_tool_calls(
        "How do I write effective alt text for informative images?"
    )
    keyboard_calls = client._build_deterministic_tool_calls(
        "How should keyboard navigation work in a custom menu?"
    )
    structure_calls = client._build_deterministic_tool_calls(
        "Can you explain how WCAG principles and guidelines are organized?"
    )

    assert alt_text_calls[0]["tool"] == "get_full_criterion_context"
    assert alt_text_calls[0]["args"] == {"ref_id": "1.1.1"}
    assert any(call["tool"] == "search_techniques" for call in alt_text_calls)
    assert keyboard_calls[0]["args"] == {"ref_id": "2.1.1"}
    assert [call["tool"] for call in structure_calls] == [
        "list_principles",
        "list_guidelines",
    ]


@pytest.mark.asyncio
async def test_get_wcag_context_prefers_deterministic_first_pass(monkeypatch):
    class FakeAzureClient:
        async def chat_with_tools(self, **kwargs):
            raise AssertionError("LLM planner should not run when deterministic routing hits")

    client = WCAGMCPClient(azure_client=FakeAzureClient())
    planned_calls_seen = []

    async def fake_execute(planned_calls):
        planned_calls_seen.append(planned_calls)
        return [
            {
                "tool": "get_full_criterion_context",
                "args": {"ref_id": "1.1.1"},
                "category": "deterministic",
                "result": "SC 1.1.1 Non-text Content",
                "chars": 26,
                "status": "HIT",
            }
        ]

    monkeypatch.setattr(client, "execute_planned_tool_calls", fake_execute)

    context = await client.get_wcag_context(
        "What makes alt text effective for informative images?"
    )

    assert "SC 1.1.1" in context
    assert planned_calls_seen
    assert planned_calls_seen[0][0]["tool"] == "get_full_criterion_context"


@pytest.mark.asyncio
async def test_get_wcag_context_falls_back_to_llm_when_deterministic_route_misses(
    monkeypatch,
):
    class FakeAzureClient:
        def __init__(self):
            self.calls = 0

        async def chat_with_tools(
            self,
            messages,
            tools,
            temperature=0.0,
            max_tokens=300,
            tool_choice="auto",
            parallel_tool_calls=True,
            reasoning_effort=None,
        ):
            self.calls += 1
            return {
                "tool_calls": [
                    {
                        "id": "call-1",
                        "function": {
                            "name": "get_full_criterion_context",
                            "arguments": '{"ref_id":"2.4.7"}',
                        },
                    }
                ]
            }

    azure_client = FakeAzureClient()
    client = WCAGMCPClient(azure_client=azure_client)

    async def fake_execute(planned_calls):
        if planned_calls and planned_calls[0].get("category") == "deterministic":
            return [
                {
                    "tool": planned_calls[0]["tool"],
                    "args": planned_calls[0]["args"],
                    "category": "deterministic",
                    "result": "",
                    "chars": 0,
                    "status": "MISS",
                }
            ]
        raise AssertionError("deterministic execution path should be monkeypatched directly")

    async def fake_execute_tool_calls(tool_calls):
        return [
            {
                "tool_call_id": "call-1",
                "fn_name": "get_full_criterion_context",
                "fn_args": {"ref_id": "2.4.7"},
                "mcp_result": "SC 2.4.7 Focus Visible",
                "is_empty": False,
            }
        ]

    monkeypatch.setattr(client, "execute_planned_tool_calls", fake_execute)
    monkeypatch.setattr(client, "_execute_tool_calls", fake_execute_tool_calls)

    context = await client.get_wcag_context("How do focus indicators work?")

    assert "SC 2.4.7" in context
    assert azure_client.calls == 1


@pytest.mark.asyncio
async def test_execute_planned_tool_calls_does_not_false_miss_embedded_no_results_text(monkeypatch):
    client = WCAGMCPClient()

    async def fake_call_tool(tool_name, arguments):
        return (
            "# 4.1.3 Status Messages\n\n"
            "Examples include status messages such as 'No results returned' after a search."
        )

    monkeypatch.setattr(client, "_call_tool", fake_call_tool)

    results = await client.execute_planned_tool_calls(
        [{"tool": "get_criterion", "args": {"ref_id": "4.1.3"}, "category": "agentic"}]
    )

    assert results[0]["status"] == "HIT"


@pytest.mark.asyncio
async def test_execute_planned_tool_calls_runs_concurrently(monkeypatch):
    client = WCAGMCPClient()
    both_started = asyncio.Event()
    active_calls = 0
    max_active_calls = 0
    started_calls = 0

    async def fake_call_tool(tool_name, arguments):
        nonlocal active_calls, max_active_calls, started_calls
        active_calls += 1
        started_calls += 1
        max_active_calls = max(max_active_calls, active_calls)
        if started_calls >= 2:
            both_started.set()
        await both_started.wait()
        await asyncio.sleep(0)
        active_calls -= 1
        return f"{tool_name}:{arguments}"

    monkeypatch.setattr(client, "_call_tool", fake_call_tool)

    results = await client.execute_planned_tool_calls(
        [
            {"tool": "list_principles", "args": {}, "category": "agentic"},
            {"tool": "list_guidelines", "args": {}, "category": "agentic"},
        ]
    )

    assert max_active_calls >= 2
    assert [result["tool"] for result in results] == [
        "list_principles",
        "list_guidelines",
    ]
    assert all(result["status"] == "HIT" for result in results)
