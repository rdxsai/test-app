"""
Student Service — direct database access for student state management.

Replaces the Student MCP subprocess (student_mcp_client.py + student_mcp/server.py)
with direct calls to StudentDatabase. Same interface as StudentMCPClient so
hybrid_system.py and chat.py can switch with minimal changes.

All methods are async (using asyncio.to_thread for DB calls) to maintain
compatibility with the async calling code.
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class StudentService:
    """Direct database access for student state management.

    Drop-in replacement for StudentMCPClient. Same method signatures,
    same return types. No subprocess, no JSON-RPC, no MCP protocol.
    """

    def __init__(
        self,
        host: str = "",
        port: int = 0,
        dbname: str = "",
        user: str = "",
        password: str = "",
        schema: str = "student_mcp",
        main_schema: str = "",
    ):
        # Import here to avoid circular imports at module level
        from student_mcp.database import StudentDatabase

        self._db = StudentDatabase(
            host=host or os.environ.get("POSTGRES_HOST", "localhost"),
            port=port or int(os.environ.get("POSTGRES_PORT", "5432")),
            dbname=dbname or os.environ.get("POSTGRES_DB", "socratic_tutor"),
            user=user or os.environ.get("POSTGRES_USER", "app_user"),
            password=password or os.environ.get("POSTGRES_PASSWORD", "changeme_dev"),
            schema=schema,
            main_schema=main_schema or os.environ.get("DB_SCHEMA", "prod"),
        )
        logger.info("StudentService initialized (direct DB access)")

    def close(self):
        """Shut down the database connection pool."""
        self._db.close()

    # ------------------------------------------------------------------
    # Helper: run sync DB calls in thread pool
    # ------------------------------------------------------------------

    async def _run(self, fn, *args, **kwargs):
        """Run a synchronous database method in a thread."""
        try:
            return await asyncio.to_thread(fn, *args, **kwargs)
        except Exception as e:
            logger.error(f"StudentService error in {fn.__name__}: {e}")
            return None

    # ------------------------------------------------------------------
    # Read methods (called BEFORE LLM to build context)
    # ------------------------------------------------------------------

    async def get_profile(self, student_id: str) -> Optional[Dict]:
        """Get student profile. Returns None if not found."""
        return await self._run(self._db.get_profile, student_id)

    async def get_mastery_state(self, student_id: str) -> List[Dict]:
        """Get mastery levels for all objectives. Returns empty list on error."""
        result = await self._run(self._db.get_mastery_state, student_id)
        return result if isinstance(result, list) else []

    async def get_active_session(self, student_id: str) -> Optional[Dict]:
        """Get current session state. Returns None if no session exists."""
        return await self._run(self._db.get_active_session, student_id)

    async def get_misconception_patterns(self, student_id: str) -> List[Dict]:
        """Get unresolved misconceptions. Returns empty list on error."""
        result = await self._run(self._db.get_misconception_patterns, student_id)
        return result if isinstance(result, list) else []

    async def get_recommended_next_objective(self, student_id: str) -> Optional[Dict]:
        """Get the best next objective. Returns None if all mastered."""
        return await self._run(self._db.get_recommended_next_objective, student_id)

    async def get_session_summary(self, student_id: str, summary_type: str = "short") -> Optional[Dict]:
        """Get the most recent session summary. Returns None if none exists."""
        return await self._run(
            self._db.get_latest_session_summary, student_id, summary_type
        )

    # ------------------------------------------------------------------
    # Write methods (called AFTER LLM to persist evaluation)
    # ------------------------------------------------------------------

    async def create_profile(
        self, student_id: str, technical_level: str = "beginner",
        a11y_exposure: str = "none", role_context: str = "",
        learning_goal: str = "",
    ) -> Optional[Dict]:
        """Create a student profile after onboarding. Idempotent."""
        return await self._run(
            self._db.create_profile,
            student_id, technical_level, a11y_exposure, role_context, learning_goal,
        )

    async def update_mastery(
        self, student_id: str, objective_id: str,
        mastery_level: str, evidence_summary: str = "",
    ) -> Optional[Dict]:
        """Update mastery after assessment. Upserts."""
        return await self._run(
            self._db.upsert_mastery,
            student_id, objective_id, mastery_level, evidence_summary,
        )

    async def log_misconception(
        self, student_id: str, objective_id: str,
        misconception_text: str, source_question_id: str = "",
    ) -> Optional[Dict]:
        """Log a detected misconception."""
        return await self._run(
            self._db.insert_misconception,
            student_id, objective_id, misconception_text, source_question_id,
        )

    async def update_session_state(
        self, session_id: str, student_id: str = "",
        stage: str = "", active_objective_id: str = "",
        turns: int = -1, readiness_score: float = -1.0,
        assessment_progress: str = "", stage_summary: str = "",
    ) -> Optional[Dict]:
        """Update session state. Creates session if student_id is provided."""
        # Create session if student_id provided (same as MCP server logic)
        if student_id:
            await self._run(self._db.create_session, session_id, student_id)

        # Validate stage transition if stage is being changed
        if stage:
            validation = await self._run(
                self._db.validate_stage_transition, session_id, stage
            )
            if validation and not validation.get("valid", False):
                return {"denied": True, "reason": validation.get("reason", "Invalid transition")}

        return await self._run(
            self._db.update_session,
            session_id, stage, active_objective_id, turns,
            readiness_score, assessment_progress, stage_summary,
        )

    async def save_session_summary(
        self, session_id: str, student_id: str,
        summary_type: str = "short", content: str = "{}",
        objectives_covered: str = "[]", mastery_changes: str = "{}",
    ) -> Optional[Dict]:
        """Save a session summary."""
        return await self._run(
            self._db.insert_session_summary,
            session_id, student_id, summary_type,
            content, objectives_covered, mastery_changes,
        )

    async def update_preferences(self, student_id: str, preferred_style: str) -> Optional[Dict]:
        """Update learning style preferences."""
        return await self._run(
            self._db.update_preferences, student_id, preferred_style,
        )

    async def increment_turn_count(self, session_id: str) -> Optional[Dict]:
        """Increment the turn counter for the active session."""
        result = await self._run(self._db.increment_turn_count, session_id)
        if isinstance(result, int):
            return {"turns": result}
        return result

    async def resolve_misconception(
        self, student_id: str, objective_id: str, misconception_text: str,
    ) -> Optional[Dict]:
        """Mark a misconception as resolved."""
        result = await self._run(
            self._db.resolve_misconception,
            student_id, objective_id, misconception_text,
        )
        if result:
            return {"resolved": True, **result}
        return {"not_found": True}

    async def record_assessment_answer(
        self, session_id: str, is_correct: bool,
    ) -> Optional[Dict]:
        """Record an assessment answer and get progress/completion status."""
        return await self._run(
            self._db.record_assessment_answer, session_id, is_correct,
        )
