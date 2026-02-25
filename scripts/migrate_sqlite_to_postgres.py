"""
One-time migration script: SQLite -> PostgreSQL
Reads every row from all 5 SQLite tables and inserts into PostgreSQL.
Preserves all IDs, timestamps, and foreign key relationships.

Usage:
    poetry run python scripts/migrate_sqlite_to_postgres.py
"""

import json
import os
import sys
import sqlite3

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

import psycopg2
import psycopg2.extras
from psycopg2.extras import Json


def get_postgres_dsn():
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "socratic_tutor")
    user = os.getenv("POSTGRES_USER", "app_user")
    password = os.getenv("POSTGRES_PASSWORD", "changeme_dev")
    return f"host={host} port={port} dbname={db} user={user} password={password}"


def migrate():
    sqlite_path = os.path.join(PROJECT_ROOT, "data", "socratic_tutor.db")
    if not os.path.exists(sqlite_path):
        print(f"ERROR: SQLite database not found at {sqlite_path}")
        sys.exit(1)

    print(f"Connecting to SQLite: {sqlite_path}")
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row

    dsn = get_postgres_dsn()
    print(f"Connecting to PostgreSQL...")
    pg_conn = psycopg2.connect(dsn)
    pg_cursor = pg_conn.cursor()

    # Enable pgvector extension
    pg_cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    pg_conn.commit()

    # --- Initialize PostgreSQL tables ---
    from src.question_app.services.database import DatabaseManager
    from src.question_app.core.config import config
    pg_db = DatabaseManager(dsn=config.postgres_dsn)
    print("PostgreSQL schema initialized.")

    # --- Migration order (respecting FK constraints) ---

    # 1. learning_objective (no FKs)
    print("\n--- Migrating learning_objective ---")
    rows = sqlite_conn.execute("SELECT * FROM learning_objective").fetchall()
    count = 0
    for row in rows:
        pg_cursor.execute(
            """INSERT INTO learning_objective (id, text, created_at, blooms_level, priority)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING""",
            (row["id"], row["text"], row["created_at"],
             row["blooms_level"] if "blooms_level" in row.keys() else "understand",
             row["priority"] if "priority" in row.keys() else "medium")
        )
        count += 1
    pg_conn.commit()
    print(f"  Migrated {count} learning objectives.")

    # 2. question (no FKs)
    print("\n--- Migrating question ---")
    rows = sqlite_conn.execute("SELECT * FROM question").fetchall()
    count = 0
    for row in rows:
        pg_cursor.execute(
            """INSERT INTO question (id, question_text, created_at)
            VALUES (%s, %s, %s)
            ON CONFLICT (id) DO NOTHING""",
            (row["id"], row["question_text"], row["created_at"])
        )
        count += 1
    pg_conn.commit()
    print(f"  Migrated {count} questions.")

    # 3. answer (FK -> question)
    print("\n--- Migrating answer ---")
    rows = sqlite_conn.execute("SELECT * FROM answer").fetchall()
    count = 0
    for row in rows:
        pg_cursor.execute(
            """INSERT INTO answer (id, question_id, text, is_correct, feedback_text, feedback_approved)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING""",
            (row["id"], row["question_id"], row["text"],
             bool(row["is_correct"]),  # Convert SQLite 0/1 to Python bool
             row["feedback_text"],
             bool(row["feedback_approved"]))  # Convert SQLite 0/1 to Python bool
        )
        count += 1
    pg_conn.commit()
    print(f"  Migrated {count} answers.")

    # 4. question_objective_association (FK -> question, FK -> learning_objective)
    print("\n--- Migrating question_objective_association ---")
    rows = sqlite_conn.execute("SELECT * FROM question_objective_association").fetchall()
    count = 0
    for row in rows:
        pg_cursor.execute(
            """INSERT INTO question_objective_association (id, question_id, objective_id)
            VALUES (%s, %s, %s)
            ON CONFLICT (id) DO NOTHING""",
            (row["id"], row["question_id"], row["objective_id"])
        )
        count += 1
    pg_conn.commit()
    print(f"  Migrated {count} question-objective associations.")

    # 5. student_profiles (no FKs, but has JSON fields)
    print("\n--- Migrating student_profiles ---")
    rows = sqlite_conn.execute("SELECT * FROM student_profiles").fetchall()
    count = 0
    for row in rows:
        pg_cursor.execute(
            """INSERT INTO student_profiles
            (id, name, current_topic, knowledge_level, session_phase,
             understanding_progression, misconceptions, strengths, warning_signs,
             consecutive_correct, engagement_level, last_solid_understanding,
             total_sessions, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING""",
            (
                row["id"], row["name"], row["current_topic"],
                row["knowledge_level"], row["session_phase"],
                Json(json.loads(row["understanding_progression"] or "[]")),
                Json(json.loads(row["misconceptions"] or "[]")),
                Json(json.loads(row["strengths"] or "[]")),
                Json(json.loads(row["warning_signs"] or "[]")),
                row["consecutive_correct"], row["engagement_level"],
                row["last_solid_understanding"], row["total_sessions"],
                row["created_at"], row["updated_at"]
            )
        )
        count += 1
    pg_conn.commit()
    print(f"  Migrated {count} student profiles.")

    # Cleanup
    sqlite_conn.close()
    pg_cursor.close()
    pg_conn.close()
    pg_db.close()

    print("\n=== Migration complete! ===")
    print("Run scripts/validate_migration.py to verify.")


if __name__ == "__main__":
    migrate()
