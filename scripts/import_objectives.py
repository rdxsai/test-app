"""
Import objectives and question-objective associations from a portable JSON file.

Run this AFTER 'Fetch Questions' so questions exist with canvas_id.
Matches associations by canvas_id (stable across instances).

Usage:
    poetry run python scripts/import_objectives.py [schema]
    # Default schema: prod

Reads: data/objectives_export.json
"""

import json
import os
import sys
import uuid

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv()

import psycopg2
import psycopg2.extras


def get_postgres_dsn():
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "socratic_tutor")
    user = os.getenv("POSTGRES_USER", "app_user")
    password = os.getenv("POSTGRES_PASSWORD", "changeme_dev")
    return f"host={host} port={port} dbname={db} user={user} password={password}"


def import_objectives(schema="prod"):
    input_path = os.path.join(PROJECT_ROOT, "data", "objectives_export.json")
    if not os.path.exists(input_path):
        print(f"ERROR: {input_path} not found. Run export_objectives.py first.")
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    objectives = data["objectives"]
    assoc_by_canvas = data.get("associations_by_canvas_id", [])
    assoc_by_text = data.get("associations_by_text", [])

    print(f"Loaded {len(objectives)} objectives, "
          f"{len(assoc_by_canvas)} canvas_id associations, "
          f"{len(assoc_by_text)} text-based associations.")

    dsn = get_postgres_dsn()
    conn = psycopg2.connect(dsn)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(f"SET search_path TO {schema}, public;")

    # Step 1: Upsert objectives (dedup by text)
    created = 0
    skipped = 0
    obj_text_to_id = {}

    # First, load existing objectives
    cursor.execute("SELECT id, text FROM learning_objective")
    for row in cursor.fetchall():
        obj_text_to_id[row["text"]] = row["id"]

    from datetime import datetime
    now = datetime.now().isoformat()

    for obj in objectives:
        if obj["text"] in obj_text_to_id:
            skipped += 1
            continue
        new_id = str(uuid.uuid4())
        cursor.execute(
            """INSERT INTO learning_objective (id, text, created_at, blooms_level, priority)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (text) DO NOTHING""",
            (new_id, obj["text"], now, obj.get("blooms_level", "understand"), obj.get("priority", "medium"))
        )
        if cursor.rowcount > 0:
            obj_text_to_id[obj["text"]] = new_id
            created += 1
        else:
            skipped += 1

    conn.commit()
    print(f"Objectives: {created} created, {skipped} already existed.")

    # Step 2: Build canvas_id -> question_id lookup
    cursor.execute("SELECT id, canvas_id FROM question WHERE canvas_id IS NOT NULL")
    canvas_to_qid = {row["canvas_id"]: row["id"] for row in cursor.fetchall()}

    # Step 3: Create associations by canvas_id
    assoc_created = 0
    assoc_skipped = 0

    for assoc in assoc_by_canvas:
        canvas_id = assoc["canvas_id"]
        obj_text = assoc["objective_text"]

        question_id = canvas_to_qid.get(canvas_id)
        objective_id = obj_text_to_id.get(obj_text)

        if not question_id:
            print(f"  WARN: No question with canvas_id={canvas_id}, skipping.")
            assoc_skipped += 1
            continue
        if not objective_id:
            print(f"  WARN: No objective matching '{obj_text[:50]}...', skipping.")
            assoc_skipped += 1
            continue

        cursor.execute(
            """INSERT INTO question_objective_association (id, question_id, objective_id)
            VALUES (%s, %s, %s)
            ON CONFLICT (question_id, objective_id) DO NOTHING""",
            (str(uuid.uuid4()), question_id, objective_id)
        )
        if cursor.rowcount > 0:
            assoc_created += 1
        else:
            assoc_skipped += 1

    # Step 4: Create associations by text match (for questions without canvas_id)
    if assoc_by_text:
        # Build question_text -> question_id lookup
        cursor.execute("SELECT id, question_text FROM question")
        text_to_qid = {}
        for row in cursor.fetchall():
            text_to_qid[row["question_text"]] = row["id"]

        for assoc in assoc_by_text:
            q_text = assoc["question_text"]
            obj_text = assoc["objective_text"]

            question_id = text_to_qid.get(q_text)
            objective_id = obj_text_to_id.get(obj_text)

            if not question_id or not objective_id:
                assoc_skipped += 1
                continue

            cursor.execute(
                """INSERT INTO question_objective_association (id, question_id, objective_id)
                VALUES (%s, %s, %s)
                ON CONFLICT (question_id, objective_id) DO NOTHING""",
                (str(uuid.uuid4()), question_id, objective_id)
            )
            if cursor.rowcount > 0:
                assoc_created += 1
            else:
                assoc_skipped += 1

    conn.commit()
    print(f"Associations: {assoc_created} created, {assoc_skipped} skipped.")

    cursor.close()
    conn.close()
    print(f"\nImport into '{schema}' complete!")


if __name__ == "__main__":
    schema = sys.argv[1] if len(sys.argv) > 1 else "prod"
    import_objectives(schema)
