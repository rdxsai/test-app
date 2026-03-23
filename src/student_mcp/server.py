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


# ─── READ TOOLS ──────────────────────────────────────────────────────────


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

    # Convert timestamps to ISO strings for JSON serialization
    for key in ("created_at", "last_session_at"):
        if result.get(key) is not None:
            result[key] = result[key].isoformat()

    result["found"] = True
    return json.dumps(result)


# ─── WRITE TOOLS ─────────────────────────────────────────────────────────


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

    If a profile already exists for this student_id, returns it unchanged
    (idempotent).

    Args:
        student_id:      Unique identifier for the student.
        technical_level: beginner | intermediate | advanced
        a11y_exposure:   none | awareness | working_knowledge | professional
        role_context:    developer | designer | content_author | qa_tester | manager | student
        learning_goal:   certification | job_requirement | personal_interest
    """
    result = await asyncio.to_thread(
        db.create_profile,
        student_id,
        technical_level,
        a11y_exposure,
        role_context,
        learning_goal,
    )

    for key in ("created_at", "last_session_at"):
        if result.get(key) is not None:
            result[key] = result[key].isoformat()

    return json.dumps(result)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    """Run the Student MCP server over stdio."""
    logger.info("Starting Student MCP server (stdio transport)")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
