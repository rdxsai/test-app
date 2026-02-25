"""
Post-migration validation script.
Compares row counts for all 5 tables between SQLite and PostgreSQL.
Spot-checks random records for field equality.

Usage:
    poetry run python scripts/validate_migration.py
"""

import json
import os
import sys
import sqlite3
import random

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

import psycopg2
import psycopg2.extras


def get_postgres_dsn():
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "socratic_tutor")
    user = os.getenv("POSTGRES_USER", "app_user")
    password = os.getenv("POSTGRES_PASSWORD", "changeme_dev")
    return f"host={host} port={port} dbname={db} user={user} password={password}"


TABLES = [
    "learning_objective",
    "question",
    "answer",
    "question_objective_association",
    "student_profiles",
]


def validate():
    sqlite_path = os.path.join(PROJECT_ROOT, "data", "socratic_tutor.db")
    if not os.path.exists(sqlite_path):
        print(f"ERROR: SQLite database not found at {sqlite_path}")
        sys.exit(1)

    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row

    dsn = get_postgres_dsn()
    pg_conn = psycopg2.connect(dsn)
    pg_cursor = pg_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    all_passed = True

    print("=" * 60)
    print("POST-MIGRATION VALIDATION")
    print("=" * 60)

    # --- Row count comparison ---
    for table in TABLES:
        sqlite_count = sqlite_conn.execute(f"SELECT COUNT(*) as cnt FROM {table}").fetchone()["cnt"]
        pg_cursor.execute(f"SELECT COUNT(*) as cnt FROM {table}")
        pg_count = pg_cursor.fetchone()["cnt"]

        status = "PASS" if sqlite_count == pg_count else "FAIL"
        if status == "FAIL":
            all_passed = False
        print(f"  [{status}] {table}: SQLite={sqlite_count}, PostgreSQL={pg_count}")

    # --- Spot-check: random question ---
    print("\n--- Spot-checking random records ---")

    sqlite_questions = sqlite_conn.execute("SELECT id FROM question").fetchall()
    if sqlite_questions:
        random_q = random.choice(sqlite_questions)
        q_id = random_q["id"]

        sqlite_row = dict(sqlite_conn.execute("SELECT * FROM question WHERE id = ?", (q_id,)).fetchone())
        pg_cursor.execute("SELECT * FROM question WHERE id = %s", (q_id,))
        pg_row = dict(pg_cursor.fetchone())

        if sqlite_row["question_text"] == pg_row["question_text"]:
            print(f"  [PASS] Question {q_id[:8]}... text matches")
        else:
            print(f"  [FAIL] Question {q_id[:8]}... text mismatch!")
            all_passed = False

        # Check answers for this question
        sqlite_answers = sqlite_conn.execute(
            "SELECT id, text, is_correct FROM answer WHERE question_id = ? ORDER BY id", (q_id,)
        ).fetchall()
        pg_cursor.execute(
            "SELECT id, text, is_correct FROM answer WHERE question_id = %s ORDER BY id", (q_id,)
        )
        pg_answers = pg_cursor.fetchall()

        if len(sqlite_answers) == len(pg_answers):
            print(f"  [PASS] Answer count matches ({len(sqlite_answers)})")
        else:
            print(f"  [FAIL] Answer count: SQLite={len(sqlite_answers)}, PG={len(pg_answers)}")
            all_passed = False

    # --- Spot-check: random objective ---
    sqlite_objectives = sqlite_conn.execute("SELECT id FROM learning_objective").fetchall()
    if sqlite_objectives:
        random_obj = random.choice(sqlite_objectives)
        obj_id = random_obj["id"]

        sqlite_row = dict(sqlite_conn.execute("SELECT * FROM learning_objective WHERE id = ?", (obj_id,)).fetchone())
        pg_cursor.execute("SELECT * FROM learning_objective WHERE id = %s", (obj_id,))
        pg_row = dict(pg_cursor.fetchone())

        if sqlite_row["text"] == pg_row["text"]:
            print(f"  [PASS] Objective {obj_id[:8]}... text matches")
        else:
            print(f"  [FAIL] Objective {obj_id[:8]}... text mismatch!")
            all_passed = False

    # Cleanup
    sqlite_conn.close()
    pg_cursor.close()
    pg_conn.close()

    print("\n" + "=" * 60)
    if all_passed:
        print("ALL VALIDATIONS PASSED")
    else:
        print("SOME VALIDATIONS FAILED -- review above")
    print("=" * 60)


if __name__ == "__main__":
    validate()
