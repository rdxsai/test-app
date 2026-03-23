"""
Smoke tests for the Student MCP server.

These tests launch the actual MCP server as a subprocess, connect to it
as a client, and verify the tools work end-to-end. This validates:
  - The server starts without errors
  - Tools are listed correctly
  - Tool calls execute and return valid JSON
  - Data round-trips through MCP → DB → MCP

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


SMOKE_SCHEMA = "student_mcp_smoke"


async def _run_with_session(test_fn):
    """Helper: start MCP server, run test_fn(session), then clean up."""
    exit_stack = AsyncExitStack()

    env = os.environ.copy()
    # The server reads POSTGRES_* from env; schema is hardcoded in server.py
    # but we can't override it easily, so we'll just use the default schema

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "student_mcp"],
        env=env,
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


class TestServerSmoke:
    """Smoke tests that launch the actual MCP server subprocess."""

    def test_tools_listed(self):
        async def _test(session):
            tools = await session.list_tools()
            tool_names = [t.name for t in tools.tools]
            assert "get_student_profile" in tool_names
            assert "create_student_profile" in tool_names
            return tool_names

        result = asyncio.run(_run_with_session(_test))
        assert len(result) >= 2

    def test_create_then_get_profile(self):
        async def _test(session):
            # Create a profile
            create_result = await session.call_tool(
                "create_student_profile",
                {
                    "student_id": "smoke-test-1",
                    "technical_level": "intermediate",
                    "a11y_exposure": "awareness",
                    "role_context": "developer",
                    "learning_goal": "certification",
                },
            )
            created = json.loads(create_result.content[0].text)
            assert created["student_id"] == "smoke-test-1"
            assert created["technical_level"] == "intermediate"

            # Read it back
            get_result = await session.call_tool(
                "get_student_profile",
                {"student_id": "smoke-test-1"},
            )
            profile = json.loads(get_result.content[0].text)
            assert profile["found"] is True
            assert profile["role_context"] == "developer"

        asyncio.run(_run_with_session(_test))

    def test_get_nonexistent_profile(self):
        async def _test(session):
            result = await session.call_tool(
                "get_student_profile",
                {"student_id": "does-not-exist-smoke"},
            )
            profile = json.loads(result.content[0].text)
            assert profile["found"] is False

        asyncio.run(_run_with_session(_test))

    def test_create_idempotent(self):
        async def _test(session):
            # First create
            await session.call_tool(
                "create_student_profile",
                {"student_id": "smoke-idempotent", "technical_level": "advanced"},
            )
            # Second create with different level
            result = await session.call_tool(
                "create_student_profile",
                {"student_id": "smoke-idempotent", "technical_level": "beginner"},
            )
            profile = json.loads(result.content[0].text)
            assert profile["technical_level"] == "advanced"

        asyncio.run(_run_with_session(_test))


def teardown_module():
    """Clean up any profiles created during smoke tests."""
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
            cur.execute(
                "DELETE FROM student_profiles WHERE student_id LIKE 'smoke-%'"
            )
        conn.close()
    except Exception:
        pass  # Best-effort cleanup
