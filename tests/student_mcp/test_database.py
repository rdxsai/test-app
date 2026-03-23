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
