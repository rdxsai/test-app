"""
One-time migration script: public schema -> prod & dev schemas.

Copies all existing data from the public schema (where the SQLite migration
put it) into both 'prod' and 'dev' schemas so each starts with an identical
copy of the curated data.

Usage:
    poetry run python scripts/migrate_to_schemas.py
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv()

import psycopg2
import psycopg2.extras


# Tables to migrate, in FK-safe order
TABLES = [
    "student_profiles",
    "learning_objective",
    "question",
    "answer",
    "question_objective_association",
    "question_embeddings",
]


def get_postgres_dsn():
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "socratic_tutor")
    user = os.getenv("POSTGRES_USER", "app_user")
    password = os.getenv("POSTGRES_PASSWORD", "changeme_dev")
    return f"host={host} port={port} dbname={db} user={user} password={password}"


def get_create_table_sql():
    """Returns the CREATE TABLE statements (same as DatabaseManager._init_database)."""
    return [
        """
        CREATE TABLE IF NOT EXISTS student_profiles (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            current_topic TEXT,
            knowledge_level TEXT,
            session_phase TEXT,
            understanding_progression JSONB DEFAULT '[]'::jsonb,
            misconceptions JSONB DEFAULT '[]'::jsonb,
            strengths JSONB DEFAULT '[]'::jsonb,
            warning_signs JSONB DEFAULT '[]'::jsonb,
            consecutive_correct INTEGER DEFAULT 0,
            engagement_level TEXT DEFAULT 'high',
            last_solid_understanding TEXT,
            total_sessions INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS learning_objective (
            id TEXT PRIMARY KEY,
            text TEXT NOT NULL UNIQUE,
            created_at TEXT,
            blooms_level TEXT DEFAULT 'understand',
            priority TEXT DEFAULT 'medium'
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS question (
            id TEXT PRIMARY KEY,
            question_text TEXT NOT NULL,
            created_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS answer (
            id TEXT PRIMARY KEY,
            question_id TEXT NOT NULL,
            text TEXT NOT NULL,
            is_correct BOOLEAN NOT NULL DEFAULT FALSE,
            feedback_text TEXT,
            feedback_approved BOOLEAN NOT NULL DEFAULT FALSE,
            FOREIGN KEY (question_id) REFERENCES question (id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS question_objective_association (
            id TEXT PRIMARY KEY,
            question_id TEXT NOT NULL,
            objective_id TEXT NOT NULL,
            FOREIGN KEY (question_id) REFERENCES question (id) ON DELETE CASCADE,
            FOREIGN KEY (objective_id) REFERENCES learning_objective (id) ON DELETE CASCADE,
            UNIQUE(question_id, objective_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS question_embeddings (
            id TEXT PRIMARY KEY,
            question_id TEXT NOT NULL REFERENCES question(id) ON DELETE CASCADE,
            chunk_type TEXT NOT NULL,
            answer_index INTEGER,
            is_correct BOOLEAN,
            topic TEXT DEFAULT 'Web Accessibility',
            tags TEXT DEFAULT '',
            question_type TEXT DEFAULT 'multiple_choice_question',
            learning_objective TEXT DEFAULT '',
            content TEXT NOT NULL,
            embedding vector(768) NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
        """,
    ]


def create_schema_tables(cursor, schema):
    """Creates the schema and all tables inside it."""
    print(f"\n--- Creating schema '{schema}' and tables ---")
    cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema};")
    cursor.execute(f"SET search_path TO {schema}, public;")

    for sql in get_create_table_sql():
        cursor.execute(sql)
    print(f"  Tables created in '{schema}' schema.")


def copy_table(cursor, table, src_schema, dst_schema):
    """Copies all rows from src_schema.table to dst_schema.table."""
    # Check if source table has data
    cursor.execute(f"SELECT COUNT(*) FROM {src_schema}.{table}")
    count = cursor.fetchone()[0]

    if count == 0:
        print(f"  {table}: 0 rows (skipped)")
        return 0

    # Copy data
    cursor.execute(
        f"INSERT INTO {dst_schema}.{table} SELECT * FROM {src_schema}.{table} "
        f"ON CONFLICT DO NOTHING"
    )
    print(f"  {table}: {count} rows copied")
    return count


def verify_counts(cursor, schema):
    """Prints row counts for all tables in the given schema."""
    print(f"\n--- Verifying '{schema}' schema ---")
    for table in TABLES:
        cursor.execute(f"SELECT COUNT(*) FROM {schema}.{table}")
        count = cursor.fetchone()[0]
        print(f"  {table}: {count} rows")


def migrate():
    dsn = get_postgres_dsn()
    print(f"Connecting to PostgreSQL...")
    conn = psycopg2.connect(dsn)
    conn.autocommit = False
    cursor = conn.cursor()

    # Ensure pgvector extension exists
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    conn.commit()

    # Check that public schema has data to migrate
    try:
        cursor.execute("SELECT COUNT(*) FROM public.question")
        pub_count = cursor.fetchone()[0]
    except psycopg2.errors.UndefinedTable:
        conn.rollback()
        print("ERROR: No 'question' table found in public schema.")
        print("Run the SQLite-to-PostgreSQL migration first.")
        sys.exit(1)

    if pub_count == 0:
        print("WARNING: public.question has 0 rows. Nothing to migrate.")
        print("Run the SQLite-to-PostgreSQL migration first if needed.")

    print(f"Found {pub_count} questions in public schema.")

    # Create schemas and tables
    for schema in ("prod", "dev"):
        create_schema_tables(cursor, schema)
    conn.commit()

    # Copy data from public into both schemas
    for schema in ("prod", "dev"):
        print(f"\n--- Copying data into '{schema}' schema ---")
        for table in TABLES:
            try:
                copy_table(cursor, table, "public", schema)
            except psycopg2.errors.UndefinedTable:
                conn.rollback()
                print(f"  {table}: does not exist in public (skipped)")
                # Need to re-establish after rollback
                cursor = conn.cursor()
        conn.commit()

    # Verify
    for schema in ("prod", "dev"):
        verify_counts(cursor, schema)

    cursor.close()
    conn.close()

    print("\n=== Schema migration complete! ===")
    print("Set DB_SCHEMA=prod or DB_SCHEMA=dev in your .env to switch.")


if __name__ == "__main__":
    migrate()
