"""
Backfill canvas_id values for existing questions and answers.

Matches existing DB questions to Canvas JSON by question_text,
then sets canvas_id on both question and answer rows.

This ensures existing questions are recognized as duplicates
on subsequent Canvas fetches.

Usage:
    poetry run python scripts/backfill_canvas_ids.py
"""

import json
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv()

import psycopg2


QUESTIONS_JSON = os.path.join(PROJECT_ROOT, "data", "quiz_questions.json")


def get_postgres_dsn():
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "socratic_tutor")
    user = os.getenv("POSTGRES_USER", "app_user")
    password = os.getenv("POSTGRES_PASSWORD", "changeme_dev")
    return f"host={host} port={port} dbname={db} user={user} password={password}"


def normalize(text):
    """Normalize text for matching: strip and collapse whitespace."""
    if not text:
        return ""
    return " ".join(text.split()).strip()


def backfill():
    # Load Canvas JSON
    print(f"Loading questions from {QUESTIONS_JSON}...")
    with open(QUESTIONS_JSON, "r") as f:
        canvas_questions = json.load(f)

    # Build lookup: normalized question_text -> canvas question dict
    canvas_lookup = {}
    for cq in canvas_questions:
        key = normalize(cq.get("question_text", ""))
        if key:
            canvas_lookup[key] = cq

    print(f"Loaded {len(canvas_questions)} Canvas questions, {len(canvas_lookup)} unique by text.")

    # Connect to PostgreSQL
    dsn = get_postgres_dsn()
    print(f"Connecting to PostgreSQL...")
    conn = psycopg2.connect(dsn)
    cursor = conn.cursor()

    for schema in ("prod", "dev"):
        print(f"\n--- Backfilling '{schema}' schema ---")

        # Check if schema exists
        cursor.execute(
            "SELECT 1 FROM information_schema.schemata WHERE schema_name = %s",
            (schema,),
        )
        if not cursor.fetchone():
            print(f"  Schema '{schema}' does not exist, skipping.")
            continue

        # Check if canvas_id column exists
        cursor.execute(
            """SELECT 1 FROM information_schema.columns
               WHERE table_schema = %s AND table_name = 'question' AND column_name = 'canvas_id'""",
            (schema,),
        )
        if not cursor.fetchone():
            print(f"  Column 'canvas_id' not found on {schema}.question, adding it...")
            cursor.execute(f"ALTER TABLE {schema}.question ADD COLUMN IF NOT EXISTS canvas_id INTEGER UNIQUE;")
            cursor.execute(f"ALTER TABLE {schema}.answer ADD COLUMN IF NOT EXISTS canvas_id INTEGER UNIQUE;")
            conn.commit()

        # Get all DB questions without canvas_id
        cursor.execute(
            f"SELECT id, question_text FROM {schema}.question WHERE canvas_id IS NULL"
        )
        db_questions = cursor.fetchall()
        print(f"  Found {len(db_questions)} questions without canvas_id.")

        matched_q = 0
        matched_a = 0

        for db_q_id, db_q_text in db_questions:
            key = normalize(db_q_text)
            cq = canvas_lookup.get(key)
            if not cq:
                continue

            canvas_q_id = cq.get("id")
            if canvas_q_id is None:
                continue

            # Set canvas_id on question
            cursor.execute(
                f"UPDATE {schema}.question SET canvas_id = %s WHERE id = %s AND canvas_id IS NULL",
                (canvas_q_id, db_q_id),
            )
            if cursor.rowcount > 0:
                matched_q += 1

            # Match answers by normalized text
            canvas_answers = {normalize(a.get("text", "")): a for a in cq.get("answers", [])}

            cursor.execute(
                f"SELECT id, text FROM {schema}.answer WHERE question_id = %s AND canvas_id IS NULL",
                (db_q_id,),
            )
            db_answers = cursor.fetchall()

            for db_a_id, db_a_text in db_answers:
                a_key = normalize(db_a_text)
                ca = canvas_answers.get(a_key)
                if ca and ca.get("id") is not None:
                    cursor.execute(
                        f"UPDATE {schema}.answer SET canvas_id = %s WHERE id = %s AND canvas_id IS NULL",
                        (ca["id"], db_a_id),
                    )
                    if cursor.rowcount > 0:
                        matched_a += 1

        conn.commit()
        print(f"  Matched {matched_q} questions and {matched_a} answers.")

    cursor.close()
    conn.close()
    print("\n=== Backfill complete! ===")


if __name__ == "__main__":
    backfill()
