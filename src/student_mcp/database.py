"""
Student MCP Database Layer.

Self-contained PostgreSQL access for the Student MCP server. Uses its own
connection pool and operates in the `student_mcp` schema to avoid conflicts
with the main application's `prod` schema.

Mirrors the patterns from question_app/services/database.py but is fully
independent — no imports from the main app. This isolation is intentional:
the MCP server runs as a separate subprocess.
"""

import logging
import sys
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

import psycopg2
import psycopg2.extras
from psycopg2.pool import ThreadedConnectionPool

# All logging goes to stderr (stdout is reserved for JSON-RPC protocol)
logger = logging.getLogger(__name__)


class StudentDatabase:
    """PostgreSQL operations for student state management.

    Creates and manages 5 tables in the `student_mcp` schema:
      - student_profiles:   identity, background, preferences
      - mastery_records:    per-objective mastery tracking
      - session_state:      active session stage and progress
      - session_summaries:  tiered memory (short/medium/long)
      - misconception_log:  tracked misconceptions per objective
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        dbname: str = "socratic_tutor",
        user: str = "app_user",
        password: str = "changeme_dev",
        schema: str = "student_mcp",
        main_schema: str = "prod",
        min_conn: int = 1,
        max_conn: int = 5,
    ):
        self.schema = schema
        self.main_schema = main_schema

        dsn = f"host={host} port={port} dbname={dbname} user={user} password={password}"
        logger.info(f"Connecting to PostgreSQL (schema={schema})")

        self._pool = ThreadedConnectionPool(min_conn, max_conn, dsn)
        self._init_tables()

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    @contextmanager
    def get_connection(self):
        """Provide a dict-cursor connection scoped to the student_mcp schema."""
        conn = self._pool.getconn()
        try:
            conn.cursor_factory = psycopg2.extras.RealDictCursor
            with conn.cursor() as cur:
                cur.execute(f"SET search_path TO {self.schema}, public;")
            yield conn
        except Exception:
            conn.rollback()
            raise
        finally:
            self._pool.putconn(conn)

    def close(self):
        """Shut down the connection pool."""
        if self._pool:
            self._pool.closeall()
            logger.info("Student database connection pool closed.")

    # ------------------------------------------------------------------
    # Schema initialization
    # ------------------------------------------------------------------

    def _init_tables(self):
        """Create the student_mcp schema and all tables if they don't exist."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"CREATE SCHEMA IF NOT EXISTS {self.schema};")
                cur.execute(f"SET search_path TO {self.schema}, public;")

                # 1. Student Profiles
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS student_profiles (
                        student_id      TEXT PRIMARY KEY,
                        technical_level TEXT NOT NULL DEFAULT 'beginner',
                        a11y_exposure   TEXT NOT NULL DEFAULT 'none',
                        role_context    TEXT DEFAULT '',
                        learning_goal   TEXT DEFAULT '',
                        preferred_style TEXT DEFAULT 'balanced',
                        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        last_session_at TIMESTAMPTZ
                    )
                """)

                # 2. Mastery Records
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS mastery_records (
                        student_id              TEXT NOT NULL
                            REFERENCES student_profiles(student_id) ON DELETE CASCADE,
                        objective_id            TEXT NOT NULL,
                        mastery_level           TEXT NOT NULL DEFAULT 'not_attempted',
                        evidence_summary        TEXT DEFAULT '',
                        misconceptions          JSONB DEFAULT '[]'::jsonb,
                        mini_assessment_score   REAL,
                        final_assessment_score  REAL,
                        turns_spent             INTEGER DEFAULT 0,
                        last_assessed_at        TIMESTAMPTZ DEFAULT NOW(),
                        PRIMARY KEY (student_id, objective_id)
                    )
                """)

                # 3. Session State
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS session_state (
                        session_id                  TEXT PRIMARY KEY,
                        student_id                  TEXT NOT NULL
                            REFERENCES student_profiles(student_id) ON DELETE CASCADE,
                        active_objective_id         TEXT,
                        current_stage               TEXT NOT NULL DEFAULT 'onboarding',
                        turns_on_objective          INTEGER DEFAULT 0,
                        readiness_score             REAL,
                        mini_assessment_progress    JSONB DEFAULT '{}'::jsonb,
                        final_assessment_progress   JSONB DEFAULT '{}'::jsonb,
                        stage_summary               TEXT DEFAULT '',
                        started_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_session_state_student
                        ON session_state(student_id)
                """)

                # 4. Session Summaries
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS session_summaries (
                        id                  SERIAL PRIMARY KEY,
                        session_id          TEXT NOT NULL,
                        student_id          TEXT NOT NULL
                            REFERENCES student_profiles(student_id) ON DELETE CASCADE,
                        summary_type        TEXT NOT NULL DEFAULT 'short',
                        content             JSONB NOT NULL DEFAULT '{}'::jsonb,
                        objectives_covered  TEXT[] DEFAULT '{}',
                        mastery_changes     JSONB DEFAULT '{}'::jsonb,
                        created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_session_summaries_student
                        ON session_summaries(student_id)
                """)

                # 5. Misconception Log
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS misconception_log (
                        id                  SERIAL PRIMARY KEY,
                        student_id          TEXT NOT NULL
                            REFERENCES student_profiles(student_id) ON DELETE CASCADE,
                        objective_id        TEXT NOT NULL,
                        misconception_text  TEXT NOT NULL,
                        source_question_id  TEXT,
                        identified_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        resolved_at         TIMESTAMPTZ
                    )
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_misconception_log_student
                        ON misconception_log(student_id, objective_id)
                """)

                conn.commit()
                logger.info("Student MCP tables initialized successfully.")

    # ------------------------------------------------------------------
    # Read: Student Profiles
    # ------------------------------------------------------------------

    def get_profile(self, student_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a student profile by ID. Returns None if not found."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM student_profiles WHERE student_id = %s",
                    (student_id,),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    # ------------------------------------------------------------------
    # Write: Student Profiles
    # ------------------------------------------------------------------

    def create_profile(
        self,
        student_id: str,
        technical_level: str = "beginner",
        a11y_exposure: str = "none",
        role_context: str = "",
        learning_goal: str = "",
    ) -> Dict[str, Any]:
        """Create a new student profile. Returns the created row.

        Uses ON CONFLICT to safely handle duplicate student_ids — if the
        profile already exists, returns it unchanged.
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO student_profiles
                        (student_id, technical_level, a11y_exposure, role_context, learning_goal)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (student_id) DO NOTHING
                    RETURNING *
                    """,
                    (student_id, technical_level, a11y_exposure, role_context, learning_goal),
                )
                row = cur.fetchone()
                conn.commit()

                if row:
                    return dict(row)

                # Profile already existed — fetch and return it
                return self.get_profile(student_id)
