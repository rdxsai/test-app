"""
Re-import answer text from Canvas JSON, using the 'html' field
to preserve HTML code snippets with proper <> brackets.

For answers that have an 'html' field, converts Canvas HTML
(with syntax-highlighted <code> blocks) into clean markdown.
For answers without 'html', keeps the existing 'text' as-is.

Updates public, prod, and dev schemas.

Usage:
    poetry run python scripts/reimport_answers_from_canvas.py
"""

import json
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv()

import psycopg2

from src.question_app.utils.text_utils import html_to_markdown


QUESTIONS_JSON = os.path.join(PROJECT_ROOT, "data", "quiz_questions.json")


def get_postgres_dsn():
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "socratic_tutor")
    user = os.getenv("POSTGRES_USER", "app_user")
    password = os.getenv("POSTGRES_PASSWORD", "changeme_dev")
    return f"host={host} port={port} dbname={db} user={user} password={password}"


def reimport():
    # Load Canvas JSON
    print(f"Loading questions from {QUESTIONS_JSON}...")
    with open(QUESTIONS_JSON, "r") as f:
        questions = json.load(f)

    # Build a mapping: old_answer_text -> new_answer_text
    # We match by the stripped 'text' field since that's what was imported
    updates = {}
    for q in questions:
        for a in q.get("answers", []):
            if "html" in a and a["html"]:
                new_text = html_to_markdown(a["html"])
                old_text = a["text"]
                if new_text != old_text:
                    updates[old_text] = new_text

    print(f"Found {len(updates)} answers to update.")

    if not updates:
        print("Nothing to update.")
        return

    # Show a few examples
    shown = 0
    for old, new in updates.items():
        if shown >= 2:
            break
        print(f"\n--- Example {shown + 1} ---")
        print(f"OLD: {old[:100]}")
        print(f"NEW: {new[:100]}")
        shown += 1

    # Connect to PostgreSQL
    dsn = get_postgres_dsn()
    print(f"\nConnecting to PostgreSQL...")
    conn = psycopg2.connect(dsn)
    cursor = conn.cursor()

    # Update in all schemas: public, prod, dev
    for schema in ("public", "prod", "dev"):
        print(f"\n--- Updating '{schema}' schema ---")

        # Check if schema exists
        cursor.execute(
            "SELECT 1 FROM information_schema.schemata WHERE schema_name = %s",
            (schema,),
        )
        if not cursor.fetchone():
            print(f"  Schema '{schema}' does not exist, skipping.")
            continue

        updated = 0
        for old_text, new_text in updates.items():
            cursor.execute(
                f"UPDATE {schema}.answer SET text = %s WHERE text = %s",
                (new_text, old_text),
            )
            updated += cursor.rowcount

        conn.commit()
        print(f"  Updated {updated} answer rows.")

    cursor.close()
    conn.close()
    print("\n=== Re-import complete! ===")


if __name__ == "__main__":
    reimport()
