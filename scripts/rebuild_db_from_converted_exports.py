"""
Rebuild database content from converted export-style JSON files.

This script is designed for the files produced by:
- scripts/convert_external_to_app_format.py

Input files:
- data/objectives_from_resources.json
- exports/questions_from_attachments.json
- exports/question_objective_mappings_from_gold.json

What it can do:
1. Optionally wipe core content tables
2. Optionally add columns to preserve extra metadata
3. Reinsert objectives, questions, answers, and question-objective associations
4. Preserve FK integrity by inserting parent rows first and linking associations

Usage examples:
- Dry run (no DB writes):
    poetry run python scripts/rebuild_db_from_converted_exports.py

- Execute rebuild with wipe + extra columns:
    poetry run python scripts/rebuild_db_from_converted_exports.py --execute --wipe --add-extra-columns

- Docker:
    docker exec question-app-backend poetry run python scripts/rebuild_db_from_converted_exports.py --execute --wipe --add-extra-columns
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv()

import psycopg2
import psycopg2.extras


def get_postgres_dsn() -> str:
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "socratic_tutor")
    user = os.getenv("POSTGRES_USER", "app_user")
    password = os.getenv("POSTGRES_PASSWORD", "changeme_dev")
    return f"host={host} port={port} dbname={db} user={user} password={password}"


def load_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def add_extra_columns(cursor) -> None:
    # learning_objective extras
    cursor.execute("ALTER TABLE learning_objective ADD COLUMN IF NOT EXISTS objective_code TEXT;")
    cursor.execute("ALTER TABLE learning_objective ADD COLUMN IF NOT EXISTS cognitive_level TEXT;")
    cursor.execute("ALTER TABLE learning_objective ADD COLUMN IF NOT EXISTS source_ids JSONB;")
    cursor.execute("ALTER TABLE learning_objective ADD COLUMN IF NOT EXISTS rationale TEXT;")
    cursor.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_learning_objective_objective_code "
        "ON learning_objective (objective_code) WHERE objective_code IS NOT NULL;"
    )

    # question extras
    cursor.execute("ALTER TABLE question ADD COLUMN IF NOT EXISTS source_tag TEXT;")

    # question_objective_association extras
    cursor.execute("ALTER TABLE question_objective_association ADD COLUMN IF NOT EXISTS mapping_reasoning TEXT;")
    cursor.execute("ALTER TABLE question_objective_association ADD COLUMN IF NOT EXISTS is_primary BOOLEAN;")
    cursor.execute("ALTER TABLE question_objective_association ADD COLUMN IF NOT EXISTS mapping_confidence TEXT;")
    cursor.execute("ALTER TABLE question_objective_association ADD COLUMN IF NOT EXISTS gold_id TEXT;")
    cursor.execute("ALTER TABLE question_objective_association ADD COLUMN IF NOT EXISTS mapping_source TEXT;")


def wipe_core_tables(cursor) -> None:
    cursor.execute(
        """
        TRUNCATE TABLE
            question_objective_association,
            answer,
            question_embeddings,
            question,
            learning_objective
        CASCADE;
        """
    )


def table_has_column(cursor, table_name: str, column_name: str) -> bool:
    cursor.execute(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = %s
          AND column_name = %s
        LIMIT 1;
        """,
        (table_name, column_name),
    )
    return cursor.fetchone() is not None


def rebuild(schema: str, execute: bool, wipe: bool, add_columns: bool) -> None:
    objectives_path = PROJECT_ROOT / "data/objectives_from_resources.json"
    questions_path = PROJECT_ROOT / "exports/questions_from_attachments.json"
    mappings_path = PROJECT_ROOT / "exports/question_objective_mappings_from_gold.json"

    objectives_data = load_json(objectives_path)
    questions_data = load_json(questions_path)
    mappings_data = load_json(mappings_path)

    objectives = objectives_data.get("objectives", [])
    questions = questions_data.get("questions", [])
    mapping_results = mappings_data.get("results", [])

    print("Loaded input files:")
    print(f"  objectives: {len(objectives)}")
    print(f"  questions: {len(questions)}")
    print(f"  mapping result rows: {len(mapping_results)}")

    if not execute:
        print("\nDry run only (no DB changes).")
        print(f"Would target schema: {schema}")
        print(f"Would wipe core tables: {wipe}")
        print(f"Would add extra columns: {add_columns}")
        return

    dsn = get_postgres_dsn()
    conn = psycopg2.connect(dsn)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        cursor.execute(f"SET search_path TO {schema}, public;")

        if add_columns:
            add_extra_columns(cursor)
            print("Added/verified extra columns.")

        if wipe:
            wipe_core_tables(cursor)
            print("Wiped core tables.")

        has_obj_code_col = table_has_column(cursor, "learning_objective", "objective_code")
        has_obj_cognitive_col = table_has_column(cursor, "learning_objective", "cognitive_level")
        has_obj_source_ids_col = table_has_column(cursor, "learning_objective", "source_ids")
        has_obj_rationale_col = table_has_column(cursor, "learning_objective", "rationale")

        has_assoc_reasoning_col = table_has_column(cursor, "question_objective_association", "mapping_reasoning")
        has_assoc_primary_col = table_has_column(cursor, "question_objective_association", "is_primary")
        has_assoc_confidence_col = table_has_column(cursor, "question_objective_association", "mapping_confidence")
        has_assoc_gold_id_col = table_has_column(cursor, "question_objective_association", "gold_id")
        has_assoc_source_col = table_has_column(cursor, "question_objective_association", "mapping_source")

        # Insert objectives
        objective_code_to_id: dict[str, str] = {}
        objectives_inserted = 0
        objectives_skipped = 0

        for obj in objectives:
            obj_id = obj.get("id") or str(uuid.uuid4())
            obj_text = obj.get("text")
            if not obj_text:
                objectives_skipped += 1
                continue

            columns = ["id", "text", "created_at", "blooms_level", "priority"]
            values = [
                obj_id,
                obj_text,
                obj.get("created_at"),
                obj.get("blooms_level", "understand"),
                obj.get("priority", "medium"),
            ]

            if has_obj_code_col:
                columns.append("objective_code")
                values.append(obj.get("objective_code"))
            if has_obj_cognitive_col:
                columns.append("cognitive_level")
                values.append(obj.get("cognitive_level"))
            if has_obj_source_ids_col:
                columns.append("source_ids")
                values.append(json.dumps(obj.get("source_ids")) if obj.get("source_ids") is not None else None)
            if has_obj_rationale_col:
                columns.append("rationale")
                values.append(obj.get("rationale"))

            col_list = ", ".join(columns)
            placeholders = ", ".join(["%s"] * len(values))

            cursor.execute(
                f"INSERT INTO learning_objective ({col_list}) VALUES ({placeholders}) "
                "ON CONFLICT (id) DO NOTHING",
                tuple(values),
            )

            if cursor.rowcount > 0:
                objectives_inserted += 1
            else:
                objectives_skipped += 1

            code = obj.get("objective_code") or obj.get("id")
            if code:
                objective_code_to_id[code] = obj_id

        # Build fallback code->id from DB objective_code column if available
        if has_obj_code_col:
            cursor.execute("SELECT id, objective_code FROM learning_objective WHERE objective_code IS NOT NULL")
            for row in cursor.fetchall():
                objective_code_to_id[row["objective_code"]] = row["id"]

        # Insert questions + answers
        question_id_exists: set[str] = set()
        questions_inserted = 0
        questions_skipped = 0
        answers_inserted = 0
        answers_skipped = 0

        for q in questions:
            question_id = q.get("question_id")
            question_text = q.get("question_text_markdown")
            if not question_id or not question_text:
                questions_skipped += 1
                continue

            cursor.execute(
                """
                INSERT INTO question (id, question_text, created_at, canvas_id)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (
                    question_id,
                    question_text,
                    q.get("question_created_at"),
                    q.get("question_canvas_id"),
                ),
            )
            if cursor.rowcount > 0:
                questions_inserted += 1
            else:
                questions_skipped += 1

            question_id_exists.add(question_id)

            for a in q.get("answers", []):
                answer_id = a.get("answer_id") or str(uuid.uuid4())
                answer_text = a.get("answer_text_markdown", "")
                cursor.execute(
                    """
                    INSERT INTO answer (id, question_id, text, is_correct, feedback_text, feedback_approved, canvas_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (
                        answer_id,
                        question_id,
                        answer_text,
                        bool(a.get("is_correct", False)),
                        a.get("feedback_markdown", ""),
                        bool(a.get("feedback_approved", False)),
                        a.get("answer_canvas_id"),
                    ),
                )
                if cursor.rowcount > 0:
                    answers_inserted += 1
                else:
                    answers_skipped += 1

        # Insert objective associations from mapping file
        assoc_inserted = 0
        assoc_skipped = 0
        missing_questions = 0
        missing_objectives = 0

        for row in mapping_results:
            question_id = row.get("question_id")
            matches = row.get("matches", [])
            if not question_id:
                assoc_skipped += 1
                continue
            if question_id not in question_id_exists:
                missing_questions += 1
                continue

            for match in matches:
                code = match.get("objective_code")
                objective_id = objective_code_to_id.get(code)
                if not objective_id:
                    missing_objectives += 1
                    continue

                assoc_id = str(uuid.uuid4())

                columns = ["id", "question_id", "objective_id"]
                values: list[Any] = [assoc_id, question_id, objective_id]

                if has_assoc_reasoning_col:
                    columns.append("mapping_reasoning")
                    values.append(match.get("reasoning"))
                if has_assoc_primary_col:
                    columns.append("is_primary")
                    values.append(bool(match.get("is_primary", False)))
                if has_assoc_confidence_col:
                    columns.append("mapping_confidence")
                    values.append(row.get("confidence"))
                if has_assoc_gold_id_col:
                    columns.append("gold_id")
                    values.append(row.get("gold_id"))
                if has_assoc_source_col:
                    columns.append("mapping_source")
                    values.append("gold_mapping_external")

                col_list = ", ".join(columns)
                placeholders = ", ".join(["%s"] * len(values))

                cursor.execute(
                    f"INSERT INTO question_objective_association ({col_list}) VALUES ({placeholders}) "
                    "ON CONFLICT (question_id, objective_id) DO NOTHING",
                    tuple(values),
                )

                if cursor.rowcount > 0:
                    assoc_inserted += 1
                else:
                    assoc_skipped += 1

        conn.commit()

        print("\nRebuild complete:")
        print(f"  objectives inserted/skipped: {objectives_inserted}/{objectives_skipped}")
        print(f"  questions inserted/skipped: {questions_inserted}/{questions_skipped}")
        print(f"  answers inserted/skipped: {answers_inserted}/{answers_skipped}")
        print(f"  associations inserted/skipped: {assoc_inserted}/{assoc_skipped}")
        print(f"  mapping rows with missing question in imported set: {missing_questions}")
        print(f"  mapping matches with missing objective code: {missing_objectives}")

    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild DB from converted export JSON files")
    parser.add_argument("--schema", default="prod", help="Target DB schema (default: prod)")
    parser.add_argument("--execute", action="store_true", help="Actually execute DB writes")
    parser.add_argument("--wipe", action="store_true", help="Truncate core tables before import")
    parser.add_argument(
        "--add-extra-columns",
        action="store_true",
        help="Add optional columns to store extra metadata from converted files",
    )
    args = parser.parse_args()

    if args.execute and not args.wipe:
        print("ERROR: --execute requires --wipe for this rebuild workflow.")
        sys.exit(2)

    rebuild(
        schema=args.schema,
        execute=args.execute,
        wipe=args.wipe,
        add_columns=args.add_extra_columns,
    )


if __name__ == "__main__":
    main()
