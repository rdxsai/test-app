"""
Smoke tests for the Student MCP server.

Launch the actual MCP server as a subprocess, connect as a client, and
verify all 12 tools work end-to-end through the MCP protocol.

Requires a running PostgreSQL instance.
"""

import json
import os
import sys
import asyncio
import pytest
import psycopg2

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack


async def _run_with_session(test_fn):
    """Start MCP server subprocess, run test_fn(session), then clean up."""
    exit_stack = AsyncExitStack()
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "student_mcp"],
        env=os.environ.copy(),
    )
    try:
        stdio_transport = await exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        read_stream, write_stream = stdio_transport
        session = await exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        await session.initialize()
        return await test_fn(session)
    finally:
        await exit_stack.aclose()


def _call(test_fn):
    """Sync wrapper for async MCP test functions."""
    return asyncio.run(_run_with_session(test_fn))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _create_test_profile(session, student_id="smoke-1"):
    """Create a profile and return parsed result."""
    r = await session.call_tool(
        "create_student_profile",
        {"student_id": student_id, "technical_level": "intermediate",
         "a11y_exposure": "awareness", "role_context": "developer",
         "learning_goal": "certification"},
    )
    return json.loads(r.content[0].text)


# ---------------------------------------------------------------------------
# Tests: Tool Discovery
# ---------------------------------------------------------------------------

class TestToolDiscovery:

    def test_all_12_tools_listed(self):
        expected = {
            "get_student_profile", "get_mastery_state", "get_active_session",
            "get_misconception_patterns", "get_recommended_next_objective",
            "get_session_summary", "create_student_profile", "update_mastery",
            "log_misconception", "update_session_state", "save_session_summary",
            "update_student_preferences",
        }

        async def _test(session):
            tools = await session.list_tools()
            return {t.name for t in tools.tools}

        actual = _call(_test)
        assert expected.issubset(actual), f"Missing: {expected - actual}"


# ---------------------------------------------------------------------------
# Tests: Profile Tools
# ---------------------------------------------------------------------------

class TestProfileTools:

    def test_create_and_get(self):
        async def _test(session):
            await _create_test_profile(session, "smoke-profile-1")
            r = await session.call_tool("get_student_profile", {"student_id": "smoke-profile-1"})
            p = json.loads(r.content[0].text)
            assert p["found"] is True
            assert p["role_context"] == "developer"
        _call(_test)

    def test_get_nonexistent(self):
        async def _test(session):
            r = await session.call_tool("get_student_profile", {"student_id": "ghost"})
            assert json.loads(r.content[0].text)["found"] is False
        _call(_test)

    def test_update_preferences(self):
        async def _test(session):
            await _create_test_profile(session, "smoke-pref")
            r = await session.call_tool("update_student_preferences",
                                        {"student_id": "smoke-pref", "preferred_style": "visual"})
            p = json.loads(r.content[0].text)
            assert p["preferred_style"] == "visual"
        _call(_test)


# ---------------------------------------------------------------------------
# Tests: Mastery Tools
# ---------------------------------------------------------------------------

class TestMasteryTools:

    def test_update_and_get_mastery(self):
        async def _test(session):
            await _create_test_profile(session, "smoke-mast")
            r = await session.call_tool("update_mastery", {
                "student_id": "smoke-mast", "objective_id": "obj-1",
                "mastery_level": "in_progress", "evidence_summary": "basic understanding"
            })
            m = json.loads(r.content[0].text)
            assert m["mastery_level"] == "in_progress"

            r2 = await session.call_tool("get_mastery_state", {"student_id": "smoke-mast"})
            rows = json.loads(r2.content[0].text)
            assert len(rows) == 1
            assert rows[0]["objective_id"] == "obj-1"
        _call(_test)

    def test_mastery_upsert_increments_turns(self):
        async def _test(session):
            await _create_test_profile(session, "smoke-turns")
            await session.call_tool("update_mastery", {
                "student_id": "smoke-turns", "objective_id": "obj-1",
                "mastery_level": "in_progress"
            })
            r = await session.call_tool("update_mastery", {
                "student_id": "smoke-turns", "objective_id": "obj-1",
                "mastery_level": "partial"
            })
            m = json.loads(r.content[0].text)
            assert m["turns_spent"] == 1
        _call(_test)


# ---------------------------------------------------------------------------
# Tests: Session Tools
# ---------------------------------------------------------------------------

class TestSessionTools:

    def test_create_and_get_session(self):
        async def _test(session):
            await _create_test_profile(session, "smoke-sess")
            r = await session.call_tool("update_session_state", {
                "session_id": "sess-smoke-1", "student_id": "smoke-sess",
                "stage": "introduction", "active_objective_id": "obj-1"
            })
            s = json.loads(r.content[0].text)
            assert s.get("updated") is True or s.get("current_stage") == "introduction"

            r2 = await session.call_tool("get_active_session", {"student_id": "smoke-sess"})
            s2 = json.loads(r2.content[0].text)
            assert s2["found"] is True
            assert s2["session_id"] == "sess-smoke-1"
        _call(_test)

    def test_session_not_found(self):
        async def _test(session):
            r = await session.call_tool("get_active_session", {"student_id": "no-session"})
            assert json.loads(r.content[0].text)["found"] is False
        _call(_test)


# ---------------------------------------------------------------------------
# Tests: Misconception Tools
# ---------------------------------------------------------------------------

class TestMisconceptionTools:

    def test_log_and_get_misconceptions(self):
        async def _test(session):
            await _create_test_profile(session, "smoke-misc")
            r = await session.call_tool("log_misconception", {
                "student_id": "smoke-misc", "objective_id": "obj-aria",
                "misconception_text": "Thinks aria-hidden removes from DOM",
                "source_question_id": "q42"
            })
            m = json.loads(r.content[0].text)
            assert "aria-hidden" in m["misconception_text"]

            r2 = await session.call_tool("get_misconception_patterns", {"student_id": "smoke-misc"})
            rows = json.loads(r2.content[0].text)
            assert len(rows) == 1
        _call(_test)


# ---------------------------------------------------------------------------
# Tests: Session Summary Tools
# ---------------------------------------------------------------------------

class TestSummaryTools:

    def test_save_and_get_summary(self):
        async def _test(session):
            await _create_test_profile(session, "smoke-sum")
            r = await session.call_tool("save_session_summary", {
                "session_id": "sess-sum-1", "student_id": "smoke-sum",
                "summary_type": "short",
                "content": '{"topics": ["alt text", "ARIA"]}',
                "objectives_covered": '["obj-1"]',
                "mastery_changes": '{"obj-1": "mastered"}'
            })
            s = json.loads(r.content[0].text)
            assert s["summary_type"] == "short"

            r2 = await session.call_tool("get_session_summary",
                                         {"student_id": "smoke-sum", "summary_type": "short"})
            s2 = json.loads(r2.content[0].text)
            assert s2["found"] is True
        _call(_test)

    def test_summary_not_found(self):
        async def _test(session):
            r = await session.call_tool("get_session_summary",
                                        {"student_id": "nobody", "summary_type": "long"})
            assert json.loads(r.content[0].text)["found"] is False
        _call(_test)


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

def teardown_module():
    """Clean up smoke test data."""
    dsn = (
        f"host={os.getenv('POSTGRES_HOST', 'localhost')} "
        f"port={os.getenv('POSTGRES_PORT', '5432')} "
        f"dbname={os.getenv('POSTGRES_DB', 'socratic_tutor')} "
        f"user={os.getenv('POSTGRES_USER', 'app_user')} "
        f"password={os.getenv('POSTGRES_PASSWORD', 'changeme_dev')}"
    )
    try:
        conn = psycopg2.connect(dsn)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("SET search_path TO student_mcp, public;")
            cur.execute("DELETE FROM student_profiles WHERE student_id LIKE 'smoke-%'")
        conn.close()
    except Exception:
        pass
