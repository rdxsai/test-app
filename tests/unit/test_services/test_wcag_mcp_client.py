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
