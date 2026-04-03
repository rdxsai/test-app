"""
Student MCP Database Layer.

Self-contained PostgreSQL access for the Student MCP server. Uses its own
connection pool and operates in the `student_mcp` schema to avoid conflicts
with the main application's `prod` schema.

Mirrors the patterns from question_app/services/database.py but is fully
independent — no imports from the main app. This isolation is intentional:
the MCP server runs as a separate subprocess.
"""

import json
import logging
import sys
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

import psycopg2
import psycopg2.extras
from psycopg2.pool import ThreadedConnectionPool

# All logging goes to stderr (stdout is reserved for JSON-RPC protocol)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Stage + assessment constants (validation rules for agentic tool calling)
# ---------------------------------------------------------------------------

VALID_TRANSITIONS = {
    "onboarding": ["introduction"],
    "introduction": ["exploration", "readiness_check", "mini_assessment"],
    "exploration": ["readiness_check", "mini_assessment", "exploration"],
    "readiness_check": ["mini_assessment"],
    "mini_assessment": ["final_assessment", "introduction"],
    "final_assessment": ["transition", "introduction"],
    "transition": ["introduction"],
}

STAGE_MASTERY_CAP = {
    "onboarding": "not_attempted",
    "introduction": "in_progress",
    "exploration": "in_progress",
    "readiness_check": "in_progress",
    "mini_assessment": "in_progress",
    "final_assessment": "in_progress",
    "transition": "mastered",
}

MASTERY_LEVELS = ("not_attempted", "misconception", "in_progress", "partial", "mastered")

MINI_QUESTIONS = 3
MINI_PASS = 2
FINAL_QUESTIONS = 5
FINAL_MASTERY = 4
FINAL_PARTIAL = 3
MIN_TURNS = 3
CONFIDENCE_THRESHOLD = 0.7


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

    def update_preferences(self, student_id: str, preferred_style: str) -> Optional[Dict[str, Any]]:
        """Update a student's learning style preference."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE student_profiles
                    SET preferred_style = %s, last_session_at = NOW()
                    WHERE student_id = %s
                    RETURNING *
                    """,
                    (preferred_style, student_id),
                )
                row = cur.fetchone()
                conn.commit()
                return dict(row) if row else None

    # ------------------------------------------------------------------
    # Read: Mastery Records
    # ------------------------------------------------------------------

    def get_mastery_state(self, student_id: str) -> List[Dict[str, Any]]:
        """Get mastery levels for all objectives a student has engaged with."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT * FROM mastery_records
                    WHERE student_id = %s
                    ORDER BY last_assessed_at DESC
                    """,
                    (student_id,),
                )
                return [dict(row) for row in cur.fetchall()]

    # ------------------------------------------------------------------
    # Write: Mastery Records
    # ------------------------------------------------------------------

    def upsert_mastery(
        self,
        student_id: str,
        objective_id: str,
        mastery_level: str,
        evidence_summary: str = "",
    ) -> Dict[str, Any]:
        """Insert or update a mastery record for a student-objective pair.

        On conflict (same student + objective), updates the mastery level,
        appends evidence, and increments turns_spent.
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO mastery_records
                        (student_id, objective_id, mastery_level, evidence_summary)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (student_id, objective_id) DO UPDATE SET
                        mastery_level    = EXCLUDED.mastery_level,
                        evidence_summary = EXCLUDED.evidence_summary,
                        turns_spent      = mastery_records.turns_spent + 1,
                        last_assessed_at = NOW()
                    RETURNING *
                    """,
                    (student_id, objective_id, mastery_level, evidence_summary),
                )
                row = cur.fetchone()
                conn.commit()
                return dict(row)

    # ------------------------------------------------------------------
    # Read: Session State
    # ------------------------------------------------------------------

    def get_active_session(self, student_id: str) -> Optional[Dict[str, Any]]:
        """Get the most recent session for a student."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT * FROM session_state
                    WHERE student_id = %s
                    ORDER BY started_at DESC
                    LIMIT 1
                    """,
                    (student_id,),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    # ------------------------------------------------------------------
    # Write: Session State
    # ------------------------------------------------------------------

    def create_session(self, session_id: str, student_id: str) -> Dict[str, Any]:
        """Create a new session. Returns existing session if ID conflicts."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO session_state (session_id, student_id)
                    VALUES (%s, %s)
                    ON CONFLICT (session_id) DO NOTHING
                    RETURNING *
                    """,
                    (session_id, student_id),
                )
                row = cur.fetchone()
                conn.commit()
                if row:
                    return dict(row)
                return self.get_active_session(student_id)

    def update_session(
        self,
        session_id: str,
        stage: str = "",
        active_objective_id: str = "",
        turns: int = -1,
        readiness_score: float = -1.0,
        assessment_progress: str = "",
        stage_summary: str = "",
    ) -> Optional[Dict[str, Any]]:
        """Update specific fields of a session. Only non-empty values are applied.

        This selective update approach avoids requiring all fields on every call.
        Pass only the fields you want to change.
        """
        updates = []
        params = []

        if stage:
            updates.append("current_stage = %s")
            params.append(stage)
        if active_objective_id:
            updates.append("active_objective_id = %s")
            params.append(active_objective_id)
        if turns >= 0:
            updates.append("turns_on_objective = %s")
            params.append(turns)
        if readiness_score >= 0.0:
            updates.append("readiness_score = %s")
            params.append(readiness_score)
        if assessment_progress:
            # Determine which assessment field to update based on current stage
            # The caller passes JSON; we store in the appropriate column
            updates.append("mini_assessment_progress = %s::jsonb")
            params.append(assessment_progress)
        if stage_summary:
            updates.append("stage_summary = %s")
            params.append(stage_summary)

        if not updates:
            # No fields to update — return current state by looking up via session_id
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT * FROM session_state WHERE session_id = %s",
                        (session_id,),
                    )
                    row = cur.fetchone()
                    return dict(row) if row else None

        params.append(session_id)
        set_clause = ", ".join(updates)

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE session_state SET {set_clause} WHERE session_id = %s RETURNING *",
                    params,
                )
                row = cur.fetchone()
                conn.commit()
                return dict(row) if row else None

    # ------------------------------------------------------------------
    # Read: Misconceptions
    # ------------------------------------------------------------------

    def get_misconception_patterns(self, student_id: str) -> List[Dict[str, Any]]:
        """Get unresolved misconceptions for a student, newest first."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT * FROM misconception_log
                    WHERE student_id = %s AND resolved_at IS NULL
                    ORDER BY identified_at DESC
                    """,
                    (student_id,),
                )
                return [dict(row) for row in cur.fetchall()]

    # ------------------------------------------------------------------
    # Write: Misconceptions
    # ------------------------------------------------------------------

    def insert_misconception(
        self,
        student_id: str,
        objective_id: str,
        misconception_text: str,
        source_question_id: str = "",
    ) -> Dict[str, Any]:
        """Log a newly detected misconception. Deduplicates by text.

        If the same misconception text already exists (unresolved) for this
        student + objective, returns the existing record instead of inserting.
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Check for existing unresolved duplicate
                cur.execute(
                    """
                    SELECT * FROM misconception_log
                    WHERE student_id = %s AND objective_id = %s
                      AND misconception_text = %s AND resolved_at IS NULL
                    LIMIT 1
                    """,
                    (student_id, objective_id, misconception_text),
                )
                existing = cur.fetchone()
                if existing:
                    return dict(existing)

                cur.execute(
                    """
                    INSERT INTO misconception_log
                        (student_id, objective_id, misconception_text, source_question_id)
                    VALUES (%s, %s, %s, %s)
                    RETURNING *
                    """,
                    (student_id, objective_id, misconception_text, source_question_id or None),
                )
                row = cur.fetchone()
                conn.commit()
                return dict(row)

    # ------------------------------------------------------------------
    # Read: Session Summaries
    # ------------------------------------------------------------------

    def get_latest_session_summary(
        self, student_id: str, summary_type: str = "short"
    ) -> Optional[Dict[str, Any]]:
        """Get the most recent session summary of a given type."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT * FROM session_summaries
                    WHERE student_id = %s AND summary_type = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (student_id, summary_type),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    # ------------------------------------------------------------------
    # Write: Session Summaries
    # ------------------------------------------------------------------

    def insert_session_summary(
        self,
        session_id: str,
        student_id: str,
        summary_type: str = "short",
        content: str = "{}",
        objectives_covered: str = "[]",
        mastery_changes: str = "{}",
    ) -> Dict[str, Any]:
        """Store a session summary. Content fields are JSON strings."""
        # Parse objectives_covered from JSON string to Python list for TEXT[] column
        try:
            obj_list = json.loads(objectives_covered) if objectives_covered else []
        except (json.JSONDecodeError, TypeError):
            obj_list = []

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO session_summaries
                        (session_id, student_id, summary_type, content,
                         objectives_covered, mastery_changes)
                    VALUES (%s, %s, %s, %s::jsonb, %s, %s::jsonb)
                    RETURNING *
                    """,
                    (session_id, student_id, summary_type, content,
                     obj_list, mastery_changes),
                )
                row = cur.fetchone()
                conn.commit()
                return dict(row)

    # ------------------------------------------------------------------
    # Read: Recommended Next Objective (cross-schema)
    # ------------------------------------------------------------------

    def get_recommended_next_objective(self, student_id: str) -> Optional[Dict[str, Any]]:
        """Recommend the next objective based on mastery state.

        Joins against the main app's learning_objective table (cross-schema)
        to find objectives the student hasn't mastered yet. Prioritizes:
          1. Objectives with mastery_level = 'in_progress' (resume work)
          2. Objectives with mastery_level = 'partial' (needs more work)
          3. Objectives not yet attempted (new material)

        Within each priority group, orders by the objective's priority field.
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT
                        lo.id AS objective_id,
                        lo.text AS objective_text,
                        lo.blooms_level,
                        lo.priority,
                        mr.mastery_level,
                        mr.turns_spent
                    FROM {self.main_schema}.learning_objective lo
                    LEFT JOIN mastery_records mr
                        ON lo.id = mr.objective_id AND mr.student_id = %s
                    WHERE mr.mastery_level IS NULL
                       OR mr.mastery_level NOT IN ('mastered')
                    ORDER BY
                        CASE
                            WHEN mr.mastery_level = 'in_progress' THEN 1
                            WHEN mr.mastery_level = 'partial' THEN 2
                            WHEN mr.mastery_level = 'misconception' THEN 3
                            WHEN mr.mastery_level IS NULL THEN 4
                            ELSE 5
                        END,
                        CASE lo.priority
                            WHEN 'high' THEN 1
                            WHEN 'medium' THEN 2
                            WHEN 'low' THEN 3
                            ELSE 4
                        END
                    LIMIT 1
                    """,
                    (student_id,),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    # ------------------------------------------------------------------
    # Write: Increment turn count
    # ------------------------------------------------------------------

    def increment_turn_count(self, session_id: str) -> int:
        """Increment turns_on_objective by 1. Returns the new turn count."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE session_state
                       SET turns_on_objective = turns_on_objective + 1
                       WHERE session_id = %s
                       RETURNING turns_on_objective""",
                    (session_id,),
                )
                row = cur.fetchone()
                conn.commit()
                return row["turns_on_objective"] if row else 0

    # ------------------------------------------------------------------
    # Validation: Stage transitions (for agentic tool calling)
    # ------------------------------------------------------------------

    def validate_stage_transition(
        self, session_id: str, target_stage: str,
    ) -> Dict[str, Any]:
        """Check if a stage transition is valid for the given session.

        Enforces VALID_TRANSITIONS map and minimum turn requirements.
        Returns {"valid": True} or {"valid": False, "reason": "..."}.
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM session_state WHERE session_id = %s",
                    (session_id,),
                )
                row = cur.fetchone()
                if not row:
                    return {"valid": False, "reason": "Session not found"}
                session = dict(row)

        current_stage = session.get("current_stage", "")
        turns = session.get("turns_on_objective", 0)
        valid_targets = VALID_TRANSITIONS.get(current_stage, [])

        if target_stage not in valid_targets:
            return {
                "valid": False,
                "reason": f"Cannot transition from {current_stage} to {target_stage}",
                "valid_targets": valid_targets,
            }

        if current_stage in ("exploration", "introduction") and target_stage in (
            "readiness_check", "mini_assessment"
        ):
            if turns < MIN_TURNS:
                return {
                    "valid": False,
                    "reason": f"Need at least {MIN_TURNS} turns (currently {turns})",
                    "current_turns": turns,
                }

        return {"valid": True}

    # ------------------------------------------------------------------
    # Write: Resolve misconception (for agentic tool calling)
    # ------------------------------------------------------------------

    def resolve_misconception(
        self, student_id: str, objective_id: str, misconception_text: str,
    ) -> Optional[Dict[str, Any]]:
        """Mark a misconception as resolved. Uses ILIKE for case-insensitive matching."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE misconception_log
                    SET resolved_at = NOW()
                    WHERE student_id = %s AND objective_id = %s
                      AND misconception_text ILIKE %s
                      AND resolved_at IS NULL
                    RETURNING *
                    """,
                    (student_id, objective_id, f"%{misconception_text}%"),
                )
                row = cur.fetchone()
                conn.commit()
                return dict(row) if row else None

    # ------------------------------------------------------------------
    # Write: Record assessment answer (for agentic tool calling)
    # ------------------------------------------------------------------

    def record_assessment_answer(
        self, session_id: str, is_correct: bool,
    ) -> Dict[str, Any]:
        """Record a single assessment answer and auto-transition on completion.

        Reads current_stage to determine which progress column to use
        (mini_assessment_progress or final_assessment_progress).
        Auto-computes pass/fail and transitions stage when all questions asked.
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM session_state WHERE session_id = %s",
                    (session_id,),
                )
                row = cur.fetchone()
                if not row:
                    return {"error": "Session not found"}
                session = dict(row)

                current_stage = session.get("current_stage", "")
                student_id = session.get("student_id", "")
                objective_id = session.get("active_objective_id", "")

                if current_stage == "mini_assessment":
                    progress_col = "mini_assessment_progress"
                    total_questions = MINI_QUESTIONS
                    pass_threshold = MINI_PASS
                elif current_stage == "final_assessment":
                    progress_col = "final_assessment_progress"
                    total_questions = FINAL_QUESTIONS
                    pass_threshold = FINAL_MASTERY
                else:
                    return {"error": f"Not in assessment stage (current: {current_stage})"}

                progress = session.get(progress_col, {})
                if isinstance(progress, str):
                    try:
                        progress = json.loads(progress)
                    except (json.JSONDecodeError, TypeError):
                        progress = {}

                asked = progress.get("asked", 0) + 1
                correct = progress.get("correct", 0) + (1 if is_correct else 0)
                new_progress = json.dumps({"asked": asked, "correct": correct})

                cur.execute(
                    f"UPDATE session_state SET {progress_col} = %s::jsonb WHERE session_id = %s",
                    (new_progress, session_id),
                )

                result = {
                    "recorded": True,
                    "progress": {"asked": asked, "correct": correct, "total": total_questions},
                    "completed": asked >= total_questions,
                }

                if asked >= total_questions:
                    passed = correct >= pass_threshold
                    result["passed"] = passed

                    if current_stage == "mini_assessment":
                        next_stage = "final_assessment" if passed else "introduction"
                        summary = f"Mini {'passed' if passed else 'failed'}: {correct}/{total_questions}"
                        extra = ", final_assessment_progress = '{\"asked\": 0, \"correct\": 0}'::jsonb" if passed else ", turns_on_objective = 0"
                        cur.execute(
                            f"""UPDATE session_state
                                SET current_stage = %s, stage_summary = %s{extra}
                                WHERE session_id = %s""",
                            (next_stage, summary, session_id),
                        )
                        result["next_stage"] = next_stage

                    elif current_stage == "final_assessment":
                        if correct >= FINAL_MASTERY:
                            mastery_level = "mastered"
                        elif correct >= FINAL_PARTIAL:
                            mastery_level = "partial"
                        else:
                            mastery_level = "in_progress"

                        result["mastery_level"] = mastery_level
                        if objective_id:
                            self.upsert_mastery(
                                student_id, objective_id, mastery_level,
                                f"Final assessment {correct}/{total_questions}",
                            )

                        next_stage = "transition" if correct >= FINAL_PARTIAL else "introduction"
                        cur.execute(
                            """UPDATE session_state
                               SET current_stage = %s, turns_on_objective = 0,
                                   stage_summary = %s
                               WHERE session_id = %s""",
                            (next_stage, f"Final: {correct}/{total_questions} → {mastery_level}", session_id),
                        )
                        result["next_stage"] = next_stage

                conn.commit()
                return result
