"""
Export objectives and question-objective associations to a portable JSON file.

Uses canvas_id as the stable question identifier so the data can be
imported into any fresh instance after a Canvas fetch.

Usage:
    poetry run python scripts/export_objectives.py
    # Or from host against Docker:
    # docker exec question-app-postgres psql ... (see below for SQL-only alternative)

Outputs: data/objectives_export.json
"""

import json
import os
import sys

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


def export_objectives(schema="prod"):
    dsn = get_postgres_dsn()
    conn = psycopg2.connect(dsn)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(f"SET search_path TO {schema}, public;")

    # 1. Export all objectives
    cursor.execute("SELECT id, text, blooms_level, priority FROM learning_objective ORDER BY text")
    objectives = [dict(row) for row in cursor.fetchall()]
    print(f"Exported {len(objectives)} objectives from '{schema}'.")

    # 2. Export associations with canvas_id as the question key
    cursor.execute("""
        SELECT
            q.canvas_id,
            LEFT(q.question_text, 80) AS question_preview,
            lo.text AS objective_text
        FROM question_objective_association qoa
        JOIN question q ON qoa.question_id = q.id
        JOIN learning_objective lo ON qoa.objective_id = lo.id
        WHERE q.canvas_id IS NOT NULL
        ORDER BY q.canvas_id, lo.text
    """)
    associations = [dict(row) for row in cursor.fetchall()]
    print(f"Exported {len(associations)} associations (canvas_id-based).")

    # 3. Also export associations for questions without canvas_id (by question text)
    cursor.execute("""
        SELECT
            q.question_text,
            lo.text AS objective_text
        FROM question_objective_association qoa
        JOIN question q ON qoa.question_id = q.id
        JOIN learning_objective lo ON qoa.objective_id = lo.id
        WHERE q.canvas_id IS NULL
        ORDER BY q.question_text, lo.text
    """)
    text_associations = [dict(row) for row in cursor.fetchall()]
    if text_associations:
        print(f"Exported {len(text_associations)} associations for questions without canvas_id (text-matched).")

    cursor.close()
    conn.close()

    export_data = {
        "schema": schema,
        "objectives": objectives,
        "associations_by_canvas_id": associations,
        "associations_by_text": text_associations,
    }

    output_path = os.path.join(PROJECT_ROOT, "data", "objectives_export.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    print(f"\nExported to {output_path}")
    return output_path


if __name__ == "__main__":
    schema = sys.argv[1] if len(sys.argv) > 1 else "prod"
    export_objectives(schema)
