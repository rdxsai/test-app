"""
Student MCP Server — manages student profiles, mastery tracking,
session state, and misconception logging for the Socratic tutor.

Runs as a subprocess over stdio. The FastAPI backend connects as a client
using the MCP client library (same pattern as wcag-guidelines-mcp).

All tools are called PROGRAMMATICALLY by the application, not by the LLM.
Read tools build the LLM's context window; write tools persist the LLM's
evaluation output.

Usage:
    python -m student_mcp.server          # from project root with PYTHONPATH=src
    poetry run student-mcp                # via pyproject.toml script entry

Environment variables (inherited from parent process):
    POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
    MAIN_DB_SCHEMA (default: prod) — the main app schema for cross-schema queries

Logging goes to stderr (stdout is reserved for JSON-RPC protocol).
"""

import asyncio
import json
import logging
import os
import sys

from mcp.server.fastmcp import FastMCP

from .database import StudentDatabase

# ---------------------------------------------------------------------------
# Logging — must go to stderr, stdout is JSON-RPC
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [student-mcp] %(levelname)s %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Database initialization
# ---------------------------------------------------------------------------
db = StudentDatabase(
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=int(os.getenv("POSTGRES_PORT", "5432")),
    dbname=os.getenv("POSTGRES_DB", "socratic_tutor"),
    user=os.getenv("POSTGRES_USER", "app_user"),
    password=os.getenv("POSTGRES_PASSWORD", "changeme_dev"),
    schema="student_mcp",
    main_schema=os.getenv("MAIN_DB_SCHEMA", "prod"),
)

# ---------------------------------------------------------------------------
# FastMCP server
# ---------------------------------------------------------------------------
mcp = FastMCP("student-mcp")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TIMESTAMP_KEYS = ("created_at", "last_session_at", "last_assessed_at",
                   "started_at", "identified_at", "resolved_at")


def _serialize(row: dict) -> str:
    """Convert a DB row dict to a JSON string, handling timestamps and lists."""
    for key in _TIMESTAMP_KEYS:
        val = row.get(key)
        if val is not None and hasattr(val, "isoformat"):
            row[key] = val.isoformat()
    # Convert any remaining non-serializable types
    return json.dumps(row, default=str)


def _serialize_list(rows: list) -> str:
    """Serialize a list of DB rows to JSON."""
    for row in rows:
        for key in _TIMESTAMP_KEYS:
            val = row.get(key)
            if val is not None and hasattr(val, "isoformat"):
                row[key] = val.isoformat()
    return json.dumps(rows, default=str)


# ═══════════════════════════════════════════════════════════════════════════
# READ TOOLS — called BEFORE the LLM to build the context window
# ═══════════════════════════════════════════════════════════════════════════


@mcp.tool()
async def get_student_profile(student_id: str) -> str:
    """Get full student profile with preferences.

    Returns a JSON object with the student's technical level, accessibility
    exposure, role context, learning goal, and preferred learning style.
    Returns {"found": false} if no profile exists for this student_id.
    """
    result = await asyncio.to_thread(db.get_profile, student_id)
    if result is None:
        return json.dumps({"found": False, "student_id": student_id})
    result["found"] = True
    return _serialize(result)


@mcp.tool()
async def get_mastery_state(student_id: str) -> str:
    """Get mastery levels for all objectives a student has engaged with.

    Returns a JSON array of mastery records, each containing:
    objective_id, mastery_level, evidence_summary, assessment scores,
    turns_spent, and last_assessed_at. Empty array if no records exist.
    """
    rows = await asyncio.to_thread(db.get_mastery_state, student_id)
    return _serialize_list(rows)


@mcp.tool()
async def get_active_session(student_id: str) -> str:
    """Get the most recent session state for a student.

    Returns: session_id, active_objective_id, current_stage, turns,
    readiness_score, assessment progress, and stage_summary.
    Returns {"found": false} if no session exists.
    """
    result = await asyncio.to_thread(db.get_active_session, student_id)
    if result is None:
        return json.dumps({"found": False, "student_id": student_id})
    result["found"] = True
    return _serialize(result)


@mcp.tool()
async def get_misconception_patterns(student_id: str) -> str:
    """Get unresolved misconceptions for a student.

    Returns a JSON array of misconception records with objective_id,
    misconception_text, source_question_id, and identified_at.
    Only includes misconceptions where resolved_at is NULL.
    """
    rows = await asyncio.to_thread(db.get_misconception_patterns, student_id)
    return _serialize_list(rows)


@mcp.tool()
async def get_recommended_next_objective(student_id: str) -> str:
    """Recommend the best next objective for a student.

    Cross-references the student's mastery records against the full
    objective list (from the main app schema). Prioritizes:
      1. In-progress objectives (resume work)
      2. Partial mastery (needs more work)
      3. Not-yet-attempted (new material)

    Returns {"found": false} if all objectives are mastered.
    """
    result = await asyncio.to_thread(db.get_recommended_next_objective, student_id)
    if result is None:
        return json.dumps({"found": False, "student_id": student_id})
    result["found"] = True
    return _serialize(result)


@mcp.tool()
async def get_session_summary(student_id: str, summary_type: str = "short") -> str:
    """Get the most recent session summary of a given type.

    Args:
        student_id:   The student to look up.
        summary_type: short | medium | long

    Returns the summary content JSONB, objectives covered, and mastery
    changes. Returns {"found": false} if no summary of that type exists.
    """
    result = await asyncio.to_thread(
        db.get_latest_session_summary, student_id, summary_type
    )
    if result is None:
        return json.dumps({"found": False, "student_id": student_id})
    result["found"] = True
    return _serialize(result)


# ═══════════════════════════════════════════════════════════════════════════
# WRITE TOOLS — called AFTER the LLM to persist evaluation results
# ═══════════════════════════════════════════════════════════════════════════


@mcp.tool()
async def create_student_profile(
    student_id: str,
    technical_level: str = "beginner",
    a11y_exposure: str = "none",
    role_context: str = "",
    learning_goal: str = "",
) -> str:
    """Create a new student profile after onboarding.

    Called once per student after the onboarding conversation gathers their
    technical background, accessibility experience, and learning goals.
    Idempotent — if profile already exists, returns it unchanged.

    Args:
        student_id:      Unique identifier for the student.
        technical_level: beginner | intermediate | advanced
        a11y_exposure:   none | awareness | working_knowledge | professional
        role_context:    developer | designer | content_author | qa_tester | manager | student
        learning_goal:   certification | job_requirement | personal_interest
    """
    result = await asyncio.to_thread(
        db.create_profile, student_id, technical_level,
        a11y_exposure, role_context, learning_goal,
    )
    return _serialize(result)


@mcp.tool()
async def update_mastery(
    student_id: str,
    objective_id: str,
    mastery_level: str,
    evidence_summary: str = "",
) -> str:
    """Update mastery record after an assessment or evaluation moment.

    Creates the record if it doesn't exist (upsert). On update, increments
    turns_spent and refreshes last_assessed_at.

    Args:
        student_id:       The student.
        objective_id:     The learning objective being assessed.
        mastery_level:    not_attempted | misconception | in_progress | partial | mastered
        evidence_summary: Brief text describing what the student demonstrated.
    """
    result = await asyncio.to_thread(
        db.upsert_mastery, student_id, objective_id,
        mastery_level, evidence_summary,
    )
    return _serialize(result)


@mcp.tool()
async def log_misconception(
    student_id: str,
    objective_id: str,
    misconception_text: str,
    source_question_id: str = "",
) -> str:
    """Log a newly detected misconception.

    Called when the LLM's evaluation detects that a student's response
    matches a known misconception pattern (from quiz wrong-answer feedback).

    Args:
        student_id:         The student.
        objective_id:       The objective where the misconception was detected.
        misconception_text: Description of the misconception.
        source_question_id: Optional quiz question ID that surfaced it.
    """
    result = await asyncio.to_thread(
        db.insert_misconception, student_id, objective_id,
        misconception_text, source_question_id,
    )
    return _serialize(result)


@mcp.tool()
async def update_session_state(
    session_id: str,
    student_id: str = "",
    stage: str = "",
    active_objective_id: str = "",
    turns: int = -1,
    readiness_score: float = -1.0,
    assessment_progress: str = "",
    stage_summary: str = "",
) -> str:
    """Update session state for stage transitions and progress tracking.

    Creates the session if it doesn't exist (requires student_id for creation).
    Only updates fields that are explicitly provided (non-empty/non-negative).

    Args:
        session_id:           The session to update.
        student_id:           Required only for session creation.
        stage:                Current stage name (e.g. 'introduction', 'mini_assessment').
        active_objective_id:  The objective currently being taught.
        turns:                Number of turns spent on current objective.
        readiness_score:      0.0-1.0 readiness estimate.
        assessment_progress:  JSON string like '{"asked": 2, "correct": 1}'.
        stage_summary:        Compressed summary of the completed stage.
    """
    # Ensure session exists before updating
    if student_id:
        await asyncio.to_thread(db.create_session, session_id, student_id)

    result = await asyncio.to_thread(
        db.update_session, session_id,
        stage=stage, active_objective_id=active_objective_id,
        turns=turns, readiness_score=readiness_score,
        assessment_progress=assessment_progress,
        stage_summary=stage_summary,
    )
    if result is None:
        return json.dumps({"error": "session not found", "session_id": session_id})
    return _serialize(result)


@mcp.tool()
async def save_session_summary(
    session_id: str,
    student_id: str,
    summary_type: str = "short",
    content: str = "{}",
    objectives_covered: str = "[]",
    mastery_changes: str = "{}",
) -> str:
    """Save a session summary at session end.

    Stores a tiered memory record (short/medium/long) summarizing what
    happened in the session — objectives covered, mastery changes, and
    a content blob with details.

    Args:
        session_id:         The session being summarized.
        student_id:         The student.
        summary_type:       short | medium | long
        content:            JSON string with summary details.
        objectives_covered: JSON array of objective IDs, e.g. '["obj-1", "obj-2"]'.
        mastery_changes:    JSON string with mastery deltas.
    """
    result = await asyncio.to_thread(
        db.insert_session_summary, session_id, student_id,
        summary_type, content, objectives_covered, mastery_changes,
    )
    return _serialize(result)


@mcp.tool()
async def update_student_preferences(
    student_id: str,
    preferred_style: str = "balanced",
) -> str:
    """Update student learning style preferences.

    Called periodically as the chatbot learns what teaching approach
    works best for a student (code examples, conceptual, visual, etc.).

    Args:
        student_id:      The student to update.
        preferred_style: code_examples | conceptual | visual | balanced
    """
    result = await asyncio.to_thread(
        db.update_preferences, student_id, preferred_style,
    )
    if result is None:
        return json.dumps({"error": "profile not found", "student_id": student_id})
    return _serialize(result)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    """Run the Student MCP server over stdio."""
    logger.info("Starting Student MCP server (stdio transport)")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
