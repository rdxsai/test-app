"""
--- OBJECTIVE SEEDER ---

Reads 'objectives.md', parses Bloom's verbs (e.g., **Explain**),
and inserts new objectives into the 'learning_objective' table.
Skips duplicates by text — safe to run multiple times.

Usage:
    poetry run python scripts/seed_objectives.py
    # Or inside Docker:
    docker exec question-app-backend poetry run python scripts/seed_objectives.py
"""

import re
import uuid
from datetime import datetime
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

try:
    from src.question_app.services.database import get_database_manager
except ImportError as e:
    print(f"ImportError: {e}")
    print("Failed to import database module. Make sure you are in the project root folder.")
    print("Run as: poetry run python scripts/seed_objectives.py")
    sys.exit(1)

OBJECTIVES_DOC = "objectives.md"

BLOOM_MAP = {
    "identify": "remember", "list": "remember", "describe": "remember",
    "summarize": "understand", "explain": "understand", "differentiate": "understand",
    "outline": "understand",
    "compare": "analyze", "analyze": "analyze", "distinguish": "analyze",
    "map": "analyze", "interpret": "analyze", "categorize": "analyze",
    "assess": "evaluate", "evaluate": "evaluate", "justify": "evaluate",
    "recommend": "evaluate", "verify": "evaluate",
    "propose": "create", "construct": "create", "develop": "create",
    "establish": "create", "formulate": "create", "collaborate": "create",
    "integrate": "create",
    "apply": "apply", "implement": "apply", "demonstrate": "apply",
    "conduct": "apply", "use": "apply", "perform": "apply",
}


def get_blooms_level(verb: str) -> str:
    """Finds the matching Bloom's level, defaulting to 'understand'."""
    return BLOOM_MAP.get(verb.lower(), "understand")


def seed_database():
    print("--- Starting Objective Seeder ---")

    try:
        db = get_database_manager()
        print("DatabaseManager initialized.")
    except Exception as e:
        print(f"Failed to initialize DatabaseManager: {e}")
        return

    objective_regex = re.compile(r"^\d+\.\s+\*\*(.*?)\*\*(.*)")
    objectives_found = []

    try:
        with open(OBJECTIVES_DOC, 'r', encoding='utf-8') as f:
            for line in f:
                match = objective_regex.match(line.strip())
                if match:
                    verb = match.group(1).strip().split()[0].lower().rstrip(',')
                    text = f"{match.group(1).strip()} {match.group(2).strip()}"
                    objective = {
                        "text": text,
                        "blooms_level": get_blooms_level(verb),
                        "priority": "medium",
                        "id": str(uuid.uuid4()),
                        "created_at": datetime.now().isoformat()
                    }
                    objectives_found.append(objective)

    except FileNotFoundError:
        print(f"ERROR: '{OBJECTIVES_DOC}' not found in the project root.")
        print("Create it and paste objectives in the format: 1. **Verb** rest of objective text")
        return
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    print(f"Found {len(objectives_found)} objectives in '{OBJECTIVES_DOC}'.")
    if not objectives_found:
        print("No objectives found. Exiting.")
        return

    try:
        created = 0
        skipped = 0

        with db.get_connection(use_row_factory=False) as conn:
            cursor = conn.cursor()

            for obj in objectives_found:
                cursor.execute(
                    """
                    INSERT INTO learning_objective (id, text, created_at, blooms_level, priority)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (text) DO NOTHING
                    """,
                    (obj['id'], obj['text'], obj['created_at'], obj['blooms_level'], obj['priority'])
                )
                if cursor.rowcount > 0:
                    created += 1
                else:
                    skipped += 1

            conn.commit()

        print(f"\nResults: {created} new objectives added, {skipped} already existed.")
        print("--- Objective Seeding Complete! ---")

    except Exception as e:
        print(f"\nDATABASE ERROR: {e}")


if __name__ == "__main__":
    seed_database()
