"""
Integration tests for StudentDatabase.

These tests run against a real PostgreSQL instance (same as the app uses).
They use a dedicated test schema (`student_mcp_test`) that is created and
torn down per test session to avoid polluting production data.
"""

import os
import pytest

from student_mcp.database import StudentDatabase


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TEST_SCHEMA = "student_mcp_test"

# Module-level singleton — all tests share one connection pool
_db_instance = None


def _get_db():
    """Lazily create the StudentDatabase for this test module."""
    global _db_instance
    if _db_instance is None:
        _db_instance = StudentDatabase(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            dbname=os.getenv("POSTGRES_DB", "socratic_tutor"),
            user=os.getenv("POSTGRES_USER", "app_user"),
            password=os.getenv("POSTGRES_PASSWORD", "changeme_dev"),
            schema=TEST_SCHEMA,
            main_schema=os.getenv("MAIN_DB_SCHEMA", "prod"),
        )
    return _db_instance


@pytest.fixture
def db():
    """Provide the shared StudentDatabase instance."""
    return _get_db()


@pytest.fixture(autouse=True)
def clean_between_tests():
    """Truncate student_profiles (cascades to all child tables) between tests."""
    yield
    database = _get_db()
    with database.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE student_profiles CASCADE")
        conn.commit()


def teardown_module():
    """Drop the test schema after all tests complete."""
    database = _get_db()
    with database.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE")
        conn.commit()
    database.close()


# ---------------------------------------------------------------------------
# Tests: Schema initialization
# ---------------------------------------------------------------------------


class TestSchemaInit:
    """Verify that _init_tables() creates the expected schema and tables."""

    def test_schema_exists(self, db):
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
                    (TEST_SCHEMA,),
                )
                assert cur.fetchone() is not None

    def test_all_tables_exist(self, db):
        expected_tables = {
            "student_profiles",
            "mastery_records",
            "session_state",
            "session_summaries",
            "misconception_log",
        }
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = %s
                    """,
                    (TEST_SCHEMA,),
                )
                actual = {row["table_name"] for row in cur.fetchall()}
        assert expected_tables.issubset(actual), f"Missing tables: {expected_tables - actual}"

    def test_indexes_exist(self, db):
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT indexname FROM pg_indexes
                    WHERE schemaname = %s
                    """,
                    (TEST_SCHEMA,),
                )
                index_names = {row["indexname"] for row in cur.fetchall()}
        assert "idx_session_state_student" in index_names
        assert "idx_session_summaries_student" in index_names
        assert "idx_misconception_log_student" in index_names


# ---------------------------------------------------------------------------
# Tests: Profile CRUD
# ---------------------------------------------------------------------------


class TestProfileCRUD:
    """Test create and read operations for student profiles."""

    def test_create_profile_returns_all_fields(self, db):
        result = db.create_profile(
            student_id="test-student-1",
            technical_level="intermediate",
            a11y_exposure="awareness",
            role_context="developer",
            learning_goal="certification",
        )
        assert result["student_id"] == "test-student-1"
        assert result["technical_level"] == "intermediate"
        assert result["a11y_exposure"] == "awareness"
        assert result["role_context"] == "developer"
        assert result["learning_goal"] == "certification"
        assert result["preferred_style"] == "balanced"  # default
        assert result["created_at"] is not None

    def test_create_profile_defaults(self, db):
        result = db.create_profile(student_id="test-student-defaults")
        assert result["technical_level"] == "beginner"
        assert result["a11y_exposure"] == "none"
        assert result["role_context"] == ""
        assert result["learning_goal"] == ""

    def test_create_profile_idempotent(self, db):
        """Creating the same student_id twice returns the original profile."""
        first = db.create_profile(
            student_id="test-idempotent",
            technical_level="advanced",
        )
        second = db.create_profile(
            student_id="test-idempotent",
            technical_level="beginner",  # different value
        )
        # Should return the FIRST profile, not overwrite
        assert second["technical_level"] == "advanced"

    def test_get_profile_found(self, db):
        db.create_profile(student_id="test-get-1", role_context="designer")
        result = db.get_profile("test-get-1")
        assert result is not None
        assert result["role_context"] == "designer"

    def test_get_profile_not_found(self, db):
        result = db.get_profile("nonexistent-student")
        assert result is None

    def test_create_profile_persists(self, db):
        """Verify the profile is actually in the database, not just returned."""
        db.create_profile(student_id="test-persist", a11y_exposure="professional")

        # Read directly from DB to confirm
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT a11y_exposure FROM student_profiles WHERE student_id = %s",
                    ("test-persist",),
                )
                row = cur.fetchone()
        assert row["a11y_exposure"] == "professional"

    def test_update_preferences(self, db):
        db.create_profile(student_id="test-pref")
        result = db.update_preferences("test-pref", "code_examples")
        assert result["preferred_style"] == "code_examples"
        assert result["last_session_at"] is not None

    def test_update_preferences_nonexistent(self, db):
        result = db.update_preferences("ghost", "visual")
        assert result is None


# ---------------------------------------------------------------------------
# Tests: Mastery Records
# ---------------------------------------------------------------------------


class TestMasteryRecords:
    """Test mastery tracking operations."""

    def test_upsert_creates_new(self, db):
        db.create_profile(student_id="mastery-1")
        result = db.upsert_mastery(
            "mastery-1", "obj-semantic-html", "in_progress",
            "Student understands basic div vs nav distinction",
        )
        assert result["student_id"] == "mastery-1"
        assert result["objective_id"] == "obj-semantic-html"
        assert result["mastery_level"] == "in_progress"
        assert result["turns_spent"] == 0  # first insert

    def test_upsert_updates_existing(self, db):
        db.create_profile(student_id="mastery-2")
        db.upsert_mastery("mastery-2", "obj-1", "in_progress", "initial")
        result = db.upsert_mastery("mastery-2", "obj-1", "partial", "improved")
        assert result["mastery_level"] == "partial"
        assert result["evidence_summary"] == "improved"
        assert result["turns_spent"] == 1  # incremented

    def test_get_mastery_state_empty(self, db):
        db.create_profile(student_id="mastery-empty")
        result = db.get_mastery_state("mastery-empty")
        assert result == []

    def test_get_mastery_state_multiple(self, db):
        db.create_profile(student_id="mastery-multi")
        db.upsert_mastery("mastery-multi", "obj-1", "mastered", "")
        db.upsert_mastery("mastery-multi", "obj-2", "in_progress", "")
        result = db.get_mastery_state("mastery-multi")
        assert len(result) == 2
        levels = {r["objective_id"]: r["mastery_level"] for r in result}
        assert levels["obj-1"] == "mastered"
        assert levels["obj-2"] == "in_progress"


# ---------------------------------------------------------------------------
# Tests: Session State
# ---------------------------------------------------------------------------


class TestSessionState:
    """Test session management operations."""

    def test_create_session(self, db):
        db.create_profile(student_id="sess-1")
        result = db.create_session("session-abc", "sess-1")
        assert result["session_id"] == "session-abc"
        assert result["current_stage"] == "onboarding"
        assert result["turns_on_objective"] == 0

    def test_get_active_session(self, db):
        db.create_profile(student_id="sess-2")
        db.create_session("session-xyz", "sess-2")
        result = db.get_active_session("sess-2")
        assert result is not None
        assert result["session_id"] == "session-xyz"

    def test_get_active_session_not_found(self, db):
        db.create_profile(student_id="sess-none")
        result = db.get_active_session("sess-none")
        assert result is None

    def test_update_session_stage(self, db):
        db.create_profile(student_id="sess-upd")
        db.create_session("session-upd", "sess-upd")
        result = db.update_session("session-upd", stage="introduction")
        assert result["current_stage"] == "introduction"

    def test_update_session_turns(self, db):
        db.create_profile(student_id="sess-turns")
        db.create_session("session-turns", "sess-turns")
        result = db.update_session("session-turns", turns=5)
        assert result["turns_on_objective"] == 5

    def test_update_session_multiple_fields(self, db):
        db.create_profile(student_id="sess-multi")
        db.create_session("session-multi", "sess-multi")
        result = db.update_session(
            "session-multi",
            stage="mini_assessment",
            active_objective_id="obj-1",
            turns=3,
            readiness_score=0.75,
            stage_summary="Student explored headings and landmarks.",
        )
        assert result["current_stage"] == "mini_assessment"
        assert result["active_objective_id"] == "obj-1"
        assert result["turns_on_objective"] == 3
        assert result["readiness_score"] == pytest.approx(0.75)
        assert "headings" in result["stage_summary"]

    def test_update_session_no_changes(self, db):
        """Calling update with no fields returns the current state."""
        db.create_profile(student_id="sess-noop")
        db.create_session("session-noop", "sess-noop")
        result = db.update_session("session-noop")
        assert result is not None

    def test_save_and_get_session_runtime_cache(self, db):
        db.create_profile(student_id="sess-cache")
        db.create_session("session-cache", "sess-cache")

        payload = {
            "objective_id": "obj-1",
            "teaching_content": "Persisted evidence pack",
            "lesson_state": {"active_concept": "c1"},
        }
        db.save_session_runtime_cache("session-cache", payload)

        result = db.get_session_runtime_cache("session-cache")
        assert result is not None
        assert result["objective_id"] == "obj-1"
        assert result["lesson_state"]["active_concept"] == "c1"

    def test_create_session_copies_runtime_cache_from_previous_session(self, db):
        db.create_profile(student_id="sess-copy")
        db.create_session("session-old", "sess-copy")
        db.save_session_runtime_cache(
            "session-old",
            {"objective_id": "obj-1", "teaching_content": "Warm cache"},
        )

        result = db.create_session("session-new", "sess-copy")

        assert result["session_id"] == "session-new"
        assert result["current_stage"] == "onboarding"
        assert result["runtime_cache"]["objective_id"] == "obj-1"
        assert result["runtime_cache"]["teaching_content"] == "Warm cache"


# ---------------------------------------------------------------------------
# Tests: Personalized Memory
# ---------------------------------------------------------------------------


class TestPersonalizedMemory:
    """Test learner-level and objective-level memory storage."""

    def test_upsert_and_get_learner_memory(self, db):
        db.create_profile(student_id="mem-1")
        db.upsert_learner_memory(
            "mem-1",
            summary="Learns best from contrastive examples",
            strengths=["classification"],
            support_needs=["slower pacing"],
            tendencies=["answers cautiously"],
            successful_strategies=["contrastive examples"],
        )
        result = db.get_learner_memory("mem-1")
        assert result is not None
        assert result["summary"] == "Learns best from contrastive examples"
        assert "classification" in result["strengths"]
        assert "slower pacing" in result["support_needs"]

    def test_upsert_and_get_objective_memory(self, db):
        db.create_profile(student_id="mem-2")
        db.upsert_objective_memory(
            "mem-2",
            "obj-aria",
            summary="Understands polite vs assertive distinction",
            demonstrated_skills=["compares urgency correctly"],
            active_gaps=["still weak on aria-atomic"],
            next_focus="Teach when updates should interrupt",
        )
        result = db.get_objective_memory("mem-2", "obj-aria")
        assert result is not None
        assert result["summary"] == "Understands polite vs assertive distinction"
        assert "compares urgency correctly" in result["demonstrated_skills"]
        assert "still weak on aria-atomic" in result["active_gaps"]
        assert result["next_focus"] == "Teach when updates should interrupt"


# ---------------------------------------------------------------------------
# Tests: Misconceptions
# ---------------------------------------------------------------------------


class TestMisconceptions:
    """Test misconception logging and retrieval."""

    def test_insert_misconception(self, db):
        db.create_profile(student_id="misc-1")
        result = db.insert_misconception(
            "misc-1", "obj-aria", "Thinks aria-hidden removes from DOM",
            source_question_id="q42",
        )
        assert result["misconception_text"] == "Thinks aria-hidden removes from DOM"
        assert result["source_question_id"] == "q42"
        assert result["resolved_at"] is None

    def test_get_misconception_patterns_empty(self, db):
        db.create_profile(student_id="misc-empty")
        result = db.get_misconception_patterns("misc-empty")
        assert result == []

    def test_insert_deduplicates(self, db):
        """Same misconception text for same student+objective returns existing, not duplicate."""
        db.create_profile(student_id="misc-dedup")
        first = db.insert_misconception("misc-dedup", "obj-1", "same misconception")
        second = db.insert_misconception("misc-dedup", "obj-1", "same misconception")
        assert first["id"] == second["id"]  # same record returned
        # Verify only 1 exists
        patterns = db.get_misconception_patterns("misc-dedup")
        assert len(patterns) == 1

    def test_get_misconception_patterns_filters_resolved(self, db):
        db.create_profile(student_id="misc-filt")
        db.insert_misconception("misc-filt", "obj-1", "misconception A")
        db.insert_misconception("misc-filt", "obj-1", "misconception B")

        # Resolve one
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE misconception_log SET resolved_at = NOW()
                       WHERE student_id = 'misc-filt'
                       AND misconception_text = 'misconception A'"""
                )
            conn.commit()

        result = db.get_misconception_patterns("misc-filt")
        assert len(result) == 1
        assert result[0]["misconception_text"] == "misconception B"


# ---------------------------------------------------------------------------
# Tests: Session Summaries
# ---------------------------------------------------------------------------


class TestSessionSummaries:
    """Test session summary storage and retrieval."""

    def test_insert_and_get_summary(self, db):
        db.create_profile(student_id="sum-1")
        db.insert_session_summary(
            session_id="sess-sum-1",
            student_id="sum-1",
            summary_type="short",
            content='{"topics": ["alt text"]}',
            objectives_covered='["obj-alt-text"]',
            mastery_changes='{"obj-alt-text": "mastered"}',
        )
        result = db.get_latest_session_summary("sum-1", "short")
        assert result is not None
        assert result["summary_type"] == "short"
        assert result["content"]["topics"] == ["alt text"]
        assert "obj-alt-text" in result["objectives_covered"]

    def test_get_summary_not_found(self, db):
        db.create_profile(student_id="sum-none")
        result = db.get_latest_session_summary("sum-none", "long")
        assert result is None

    def test_get_latest_returns_most_recent(self, db):
        db.create_profile(student_id="sum-latest")
        db.insert_session_summary(
            "sess-old", "sum-latest", "short", '{"n": 1}',
        )
        db.insert_session_summary(
            "sess-new", "sum-latest", "short", '{"n": 2}',
        )
        result = db.get_latest_session_summary("sum-latest", "short")
        assert result["content"]["n"] == 2
