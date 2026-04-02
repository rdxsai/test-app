"""
Tests for MCP tool validation logic (Phase 3, Commit 1).

Tests the validation rules moved from stage_machine.py into the MCP tools:
mastery caps, confidence gating, stage transitions, assessment scoring.

Uses real PostgreSQL via StudentDatabase (same pattern as test_database.py).
"""

import json
import os
import pytest

from student_mcp.database import (
    StudentDatabase, VALID_TRANSITIONS, STAGE_MASTERY_CAP,
    MASTERY_LEVELS, MINI_QUESTIONS, MINI_PASS, FINAL_QUESTIONS,
    FINAL_MASTERY, FINAL_PARTIAL, MIN_TURNS, CONFIDENCE_THRESHOLD,
)


TEST_SCHEMA = "student_mcp_validation_test"
_db = None


def _get_db():
    global _db
    if _db is None:
        _db = StudentDatabase(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            dbname=os.getenv("POSTGRES_DB", "socratic_tutor"),
            user=os.getenv("POSTGRES_USER", "app_user"),
            password=os.getenv("POSTGRES_PASSWORD", "changeme_dev"),
            schema=TEST_SCHEMA,
            main_schema=os.getenv("MAIN_DB_SCHEMA", "dev"),
        )
    return _db


@pytest.fixture
def db():
    return _get_db()


@pytest.fixture(autouse=True)
def clean():
    yield
    database = _get_db()
    with database.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE student_profiles CASCADE")
        conn.commit()


def teardown_module():
    database = _get_db()
    with database.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE")
        conn.commit()
    database.close()


def _setup_student_session(db, student_id="stu-1", session_id="sess-1",
                            stage="exploration", turns=5, objective="obj-1"):
    """Helper: create a student + session for testing."""
    db.create_profile(student_id=student_id)
    db.create_session(session_id, student_id)
    db.update_session(session_id, stage=stage, turns=turns,
                      active_objective_id=objective)


# ---------------------------------------------------------------------------
# Tests: Stage transition validation
# ---------------------------------------------------------------------------

class TestStageTransitionValidation:

    def test_valid_transition(self, db):
        _setup_student_session(db, stage="exploration", turns=5)
        result = db.validate_stage_transition("sess-1", "readiness_check")
        assert result["valid"] is True

    def test_invalid_transition(self, db):
        _setup_student_session(db, stage="introduction", turns=5)
        result = db.validate_stage_transition("sess-1", "final_assessment")
        assert result["valid"] is False
        assert "Cannot transition" in result["reason"]
        assert "valid_targets" in result

    def test_min_turns_enforced(self, db):
        _setup_student_session(db, stage="exploration", turns=1)
        result = db.validate_stage_transition("sess-1", "readiness_check")
        assert result["valid"] is False
        assert "turns" in result["reason"].lower()

    def test_min_turns_met(self, db):
        _setup_student_session(db, stage="exploration", turns=3)
        result = db.validate_stage_transition("sess-1", "readiness_check")
        assert result["valid"] is True

    def test_session_not_found(self, db):
        result = db.validate_stage_transition("nonexistent", "exploration")
        assert result["valid"] is False

    def test_readiness_always_to_mini(self, db):
        _setup_student_session(db, stage="readiness_check")
        result = db.validate_stage_transition("sess-1", "mini_assessment")
        assert result["valid"] is True


# ---------------------------------------------------------------------------
# Tests: Resolve misconception
# ---------------------------------------------------------------------------

class TestResolveMisconception:

    def test_resolve_existing(self, db):
        _setup_student_session(db)
        db.insert_misconception("stu-1", "obj-1", "Wrong about aria-live")
        result = db.resolve_misconception("stu-1", "obj-1", "aria-live")
        assert result is not None
        assert result["resolved_at"] is not None

    def test_resolve_not_found(self, db):
        _setup_student_session(db)
        result = db.resolve_misconception("stu-1", "obj-1", "nonexistent misconception")
        assert result is None

    def test_case_insensitive(self, db):
        _setup_student_session(db)
        db.insert_misconception("stu-1", "obj-1", "ARIA-LIVE is wrong")
        result = db.resolve_misconception("stu-1", "obj-1", "aria-live")
        assert result is not None

    def test_only_resolves_unresolved(self, db):
        _setup_student_session(db)
        db.insert_misconception("stu-1", "obj-1", "Wrong about X")
        db.resolve_misconception("stu-1", "obj-1", "Wrong about X")
        # Try resolving again — should return None (already resolved)
        result = db.resolve_misconception("stu-1", "obj-1", "Wrong about X")
        assert result is None


# ---------------------------------------------------------------------------
# Tests: Record assessment answer
# ---------------------------------------------------------------------------

class TestRecordAssessmentAnswer:

    def test_mini_tracks_progress(self, db):
        _setup_student_session(db, stage="mini_assessment")
        result = db.record_assessment_answer("sess-1", True)
        assert result["recorded"] is True
        assert result["progress"]["asked"] == 1
        assert result["progress"]["correct"] == 1
        assert result["completed"] is False

    def test_mini_pass_at_threshold(self, db):
        _setup_student_session(db, stage="mini_assessment")
        db.record_assessment_answer("sess-1", True)   # 1/1
        db.record_assessment_answer("sess-1", True)    # 2/2
        result = db.record_assessment_answer("sess-1", False)  # 2/3
        assert result["completed"] is True
        assert result["passed"] is True
        assert result["next_stage"] == "final_assessment"

    def test_mini_fail(self, db):
        _setup_student_session(db, stage="mini_assessment")
        db.record_assessment_answer("sess-1", False)
        db.record_assessment_answer("sess-1", False)
        result = db.record_assessment_answer("sess-1", True)  # 1/3
        assert result["completed"] is True
        assert result["passed"] is False
        assert result["next_stage"] == "introduction"

    def test_final_mastered(self, db):
        _setup_student_session(db, stage="final_assessment")
        for _ in range(4):
            db.record_assessment_answer("sess-1", True)
        result = db.record_assessment_answer("sess-1", False)  # 4/5
        assert result["completed"] is True
        assert result["mastery_level"] == "mastered"
        assert result["next_stage"] == "transition"

    def test_final_partial(self, db):
        _setup_student_session(db, stage="final_assessment")
        for _ in range(3):
            db.record_assessment_answer("sess-1", True)
        for _ in range(2):
            result = db.record_assessment_answer("sess-1", False)
        assert result["completed"] is True
        assert result["mastery_level"] == "partial"
        assert result["next_stage"] == "transition"

    def test_final_fail(self, db):
        _setup_student_session(db, stage="final_assessment")
        for _ in range(2):
            db.record_assessment_answer("sess-1", True)
        for _ in range(3):
            result = db.record_assessment_answer("sess-1", False)
        assert result["completed"] is True
        assert result["mastery_level"] == "in_progress"
        assert result["next_stage"] == "introduction"

    def test_not_in_assessment_stage(self, db):
        _setup_student_session(db, stage="exploration")
        result = db.record_assessment_answer("sess-1", True)
        assert "error" in result

    def test_session_not_found(self, db):
        result = db.record_assessment_answer("nonexistent", True)
        assert "error" in result


# ---------------------------------------------------------------------------
# Tests: Constants
# ---------------------------------------------------------------------------

class TestConstants:

    def test_valid_transitions_complete(self):
        for stage in ("introduction", "exploration", "readiness_check",
                       "mini_assessment", "final_assessment", "transition"):
            assert stage in VALID_TRANSITIONS

    def test_mastery_cap_complete(self):
        for stage in ("onboarding", "introduction", "exploration",
                       "readiness_check", "mini_assessment", "final_assessment", "transition"):
            assert stage in STAGE_MASTERY_CAP

    def test_thresholds(self):
        assert MINI_QUESTIONS == 3
        assert MINI_PASS == 2
        assert FINAL_QUESTIONS == 5
        assert FINAL_MASTERY == 4
        assert FINAL_PARTIAL == 3
        assert MIN_TURNS == 3
        assert CONFIDENCE_THRESHOLD == 0.7
