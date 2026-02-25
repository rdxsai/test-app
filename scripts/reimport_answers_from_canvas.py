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
from bs4 import BeautifulSoup, NavigableString


QUESTIONS_JSON = os.path.join(PROJECT_ROOT, "data", "quiz_questions.json")


def _convert_inline(element):
    """Convert children of a block element, preserving inline <code> as backticks."""
    parts = []
    for child in element.children:
        if isinstance(child, NavigableString):
            parts.append(str(child))
        elif child.name in ("code", "kbd"):
            parts.append("`" + child.get_text() + "`")
        elif child.name == "br":
            parts.append("\n")
        elif child.name in ("strong", "b"):
            parts.append("**" + child.get_text() + "**")
        elif child.name in ("em", "i"):
            parts.append("*" + child.get_text() + "*")
        elif hasattr(child, "get_text"):
            parts.append(child.get_text())
    return "".join(parts)


def html_to_markdown(html_str):
    """
    Converts Canvas HTML (with syntax-highlighted code blocks)
    into clean markdown text with proper code fences.
    Keeps inline elements (code, strong, em) on the same line
    as surrounding text.
    """
    soup = BeautifulSoup(html_str, "html.parser")

    # Remove Canvas boilerplate (stylesheet + script injections)
    for tag in soup.find_all(["link", "script"]):
        tag.decompose()

    result = []
    inline_buf = []

    def flush_inline():
        if inline_buf:
            result.append("".join(inline_buf).strip())
            inline_buf.clear()

    for element in soup.children:
        if isinstance(element, NavigableString):
            text = str(element)
            if text.strip():
                inline_buf.append(text)
        elif element.name == "pre":
            flush_inline()
            code_text = element.get_text()
            result.append("```\n" + code_text.strip() + "\n```")
        elif element.name == "p":
            flush_inline()
            inline_buf.append(_convert_inline(element))
            flush_inline()
        elif element.name in ("code", "kbd"):
            # Inline code/keyboard — keep in the buffer with surrounding text
            inline_buf.append("`" + element.get_text() + "`")
        elif element.name == "br":
            inline_buf.append("\n")
        elif element.name in ("strong", "b", "em", "i", "span", "a"):
            inline_buf.append(element.get_text())
        elif hasattr(element, "get_text"):
            text = element.get_text().strip()
            if text:
                flush_inline()
                result.append(text)

    flush_inline()
    return "\n\n".join(p for p in result if p)


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
