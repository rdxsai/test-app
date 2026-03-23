"""
Student MCP Client — programmatic tool calling for student state management.

Unlike WCAGMCPClient (which uses LLM-driven tool selection via OpenAI
function calling), this client makes direct session.call_tool() calls.
The application code decides WHICH tool to call and WHEN:

  Before LLM call:  read tools build the context window
  After LLM call:   write tools persist evaluation results

The subprocess stays alive for the app lifetime. Concurrent callers
are serialized by an asyncio.Lock so we never double-initialize.
If the subprocess dies, the next call auto-reconnects.
"""

import asyncio
import json
import logging
import sys
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class StudentMCPClient:
    """Async client for the student-mcp subprocess server.

    Mirrors the connection lifecycle of WCAGMCPClient (lazy init,
    asyncio.Lock, AsyncExitStack) but all tool calls are direct —
    no LLM function-calling layer in between.
    """

    def __init__(self, command: str = sys.executable, args: Optional[List[str]] = None):
        """
        Args:
            command: Path to the Python interpreter.
            args:    Arguments to run the server, e.g. ["-m", "student_mcp"].
        """
        self._command = command
        self._args = args or ["-m", "student_mcp"]
        self._session: Optional[ClientSession] = None
        self._exit_stack: Optional[AsyncExitStack] = None
        self._connect_lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    async def _ensure_connected(self) -> ClientSession:
        """Lazily start the MCP subprocess and return the session."""
        if self._session is not None:
            return self._session

        async with self._connect_lock:
            if self._session is not None:
                return self._session

            logger.info(f"Starting Student MCP server: {self._command} {' '.join(self._args)}")
            self._exit_stack = AsyncExitStack()

            server_params = StdioServerParameters(
                command=self._command,
                args=self._args,
                env=None,  # inherit parent env (DB creds, etc.)
            )

            stdio_transport = await self._exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read_stream, write_stream = stdio_transport
            self._session = await self._exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            await self._session.initialize()

            tools_result = await self._session.list_tools()
            tool_names = [t.name for t in tools_result.tools]
            logger.info(f"Student MCP connected. Tools: {tool_names}")

            return self._session

    async def close(self):
        """Shut down the MCP subprocess."""
        if self._exit_stack:
            try:
                await self._exit_stack.aclose()
            except Exception as e:
                logger.warning(f"Error closing Student MCP: {e}")
            finally:
                self._session = None
                self._exit_stack = None

    # ------------------------------------------------------------------
    # Low-level call
    # ------------------------------------------------------------------

    async def _call(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call an MCP tool and return parsed JSON.

        Returns None on failure. If the subprocess has died, resets the
        session so the next call triggers reconnection.
        """
        try:
            session = await self._ensure_connected()
            result = await session.call_tool(tool_name, arguments)
            if not result.content:
                return None
            return json.loads(result.content[0].text)
        except Exception as e:
            logger.error(f"Student MCP tool '{tool_name}' failed: {e}")
            # Reset session so next call reconnects
            self._session = None
            return None

    # ------------------------------------------------------------------
    # Read methods (called BEFORE LLM to build context)
    # ------------------------------------------------------------------

    async def get_profile(self, student_id: str) -> Optional[Dict]:
        """Get student profile. Returns None if not found or on error."""
        result = await self._call("get_student_profile", {"student_id": student_id})
        if result and result.get("found") is False:
            return None
        return result

    async def get_mastery_state(self, student_id: str) -> List[Dict]:
        """Get mastery levels for all objectives. Returns empty list on error."""
        result = await self._call("get_mastery_state", {"student_id": student_id})
        return result if isinstance(result, list) else []

    async def get_active_session(self, student_id: str) -> Optional[Dict]:
        """Get current session state. Returns None if no session exists."""
        result = await self._call("get_active_session", {"student_id": student_id})
        if result and result.get("found") is False:
            return None
        return result

    async def get_misconception_patterns(self, student_id: str) -> List[Dict]:
        """Get unresolved misconceptions. Returns empty list on error."""
        result = await self._call("get_misconception_patterns", {"student_id": student_id})
        return result if isinstance(result, list) else []

    async def get_recommended_next_objective(self, student_id: str) -> Optional[Dict]:
        """Get the best next objective. Returns None if all mastered."""
        result = await self._call("get_recommended_next_objective", {"student_id": student_id})
        if result and result.get("found") is False:
            return None
        return result

    async def get_session_summary(self, student_id: str, summary_type: str = "short") -> Optional[Dict]:
        """Get the most recent session summary. Returns None if none exists."""
        result = await self._call("get_session_summary", {
            "student_id": student_id, "summary_type": summary_type,
        })
        if result and result.get("found") is False:
            return None
        return result

    # ------------------------------------------------------------------
    # Write methods (called AFTER LLM to persist evaluation)
    # ------------------------------------------------------------------

    async def create_profile(
        self, student_id: str, technical_level: str = "beginner",
        a11y_exposure: str = "none", role_context: str = "",
        learning_goal: str = "",
    ) -> Optional[Dict]:
        """Create a student profile after onboarding. Idempotent."""
        return await self._call("create_student_profile", {
            "student_id": student_id,
            "technical_level": technical_level,
            "a11y_exposure": a11y_exposure,
            "role_context": role_context,
            "learning_goal": learning_goal,
        })

    async def update_mastery(
        self, student_id: str, objective_id: str,
        mastery_level: str, evidence_summary: str = "",
    ) -> Optional[Dict]:
        """Update mastery after assessment. Upserts."""
        return await self._call("update_mastery", {
            "student_id": student_id,
            "objective_id": objective_id,
            "mastery_level": mastery_level,
            "evidence_summary": evidence_summary,
        })

    async def log_misconception(
        self, student_id: str, objective_id: str,
        misconception_text: str, source_question_id: str = "",
    ) -> Optional[Dict]:
        """Log a detected misconception."""
        return await self._call("log_misconception", {
            "student_id": student_id,
            "objective_id": objective_id,
            "misconception_text": misconception_text,
            "source_question_id": source_question_id,
        })

    async def update_session_state(
        self, session_id: str, student_id: str = "",
        stage: str = "", active_objective_id: str = "",
        turns: int = -1, readiness_score: float = -1.0,
        assessment_progress: str = "", stage_summary: str = "",
    ) -> Optional[Dict]:
        """Update session state. Creates session if student_id is provided."""
        args = {"session_id": session_id}
        if student_id:
            args["student_id"] = student_id
        if stage:
            args["stage"] = stage
        if active_objective_id:
            args["active_objective_id"] = active_objective_id
        if turns >= 0:
            args["turns"] = turns
        if readiness_score >= 0.0:
            args["readiness_score"] = readiness_score
        if assessment_progress:
            args["assessment_progress"] = assessment_progress
        if stage_summary:
            args["stage_summary"] = stage_summary
        return await self._call("update_session_state", args)

    async def save_session_summary(
        self, session_id: str, student_id: str,
        summary_type: str = "short", content: str = "{}",
        objectives_covered: str = "[]", mastery_changes: str = "{}",
    ) -> Optional[Dict]:
        """Save a session summary."""
        return await self._call("save_session_summary", {
            "session_id": session_id,
            "student_id": student_id,
            "summary_type": summary_type,
            "content": content,
            "objectives_covered": objectives_covered,
            "mastery_changes": mastery_changes,
        })

    async def update_preferences(self, student_id: str, preferred_style: str) -> Optional[Dict]:
        """Update learning style preferences."""
        return await self._call("update_student_preferences", {
            "student_id": student_id,
            "preferred_style": preferred_style,
        })
