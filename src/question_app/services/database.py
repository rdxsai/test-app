"""
Database Manager
Handles all PostgreSQL database operations for the Socratic Tutor.
Uses psycopg2 with connection pooling and pgvector for embeddings.
"""
import logging
import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import List, Dict, Optional, Any

import psycopg2
import psycopg2.extras
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import Json

from ..models import QuestionUpdate
from ..models.tutor import (
    StudentProfile, KnowledgeLevel, SessionPhase,
)
from ..utils.text_utils import html_to_markdown

from ..core.config import config

logger = logging.getLogger(__name__)


def get_database_manager():
    """Creates and returns a DatabaseManager using config.postgres_dsn."""
    return DatabaseManager(dsn=config.postgres_dsn, schema=config.DB_SCHEMA)


class DatabaseManager:
    def __init__(self, dsn: str, min_conn: int = 2, max_conn: int = 10, schema: str = "prod"):
        self.dsn = dsn
        self.schema = schema
        logger.info(f"Initializing PostgreSQL Database Manager (schema={schema})")
        self._pool = ThreadedConnectionPool(min_conn, max_conn, dsn)
        self._init_database()

    @contextmanager
    def get_connection(self, use_row_factory: bool = True):
        """
        Provides a database connection from the pool.
        Uses RealDictCursor by default for dict-like access.
        Sets search_path to the configured schema so all queries
        resolve to the correct namespace.
        """
        conn = self._pool.getconn()
        try:
            if use_row_factory:
                conn.cursor_factory = psycopg2.extras.RealDictCursor
            else:
                conn.cursor_factory = psycopg2.extensions.cursor
            cur = conn.cursor()
            cur.execute(f"SET search_path TO {self.schema}, public;")
            cur.close()
            yield conn
        except Exception:
            conn.rollback()
            raise
        finally:
            self._pool.putconn(conn)

    def close(self):
        if self._pool:
            self._pool.closeall()

    def _init_database(self):
        """
        Initializes all tables in PostgreSQL with proper types.
        Creates the schema if it doesn't exist, then sets search_path
        so all CREATE TABLE statements land in the correct schema.
        """
        with self.get_connection(use_row_factory=False) as conn:
            cursor = conn.cursor()

            # Enable pgvector extension (lives in public schema)
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")

            # Create the target schema and set search_path
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {self.schema};")
            cursor.execute(f"SET search_path TO {self.schema}, public;")

            # 1. Student Profiles Table
            cursor.execute(
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
            """
            )

            # 2. Learning Objective Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS learning_objective (
                    id TEXT PRIMARY KEY,
                    text TEXT NOT NULL UNIQUE,
                    created_at TEXT,
                    blooms_level TEXT DEFAULT 'understand',
                    priority TEXT DEFAULT 'medium'
                )
            """
            )

            # 3. Question Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS question (
                    id TEXT PRIMARY KEY,
                    question_text TEXT NOT NULL,
                    created_at TEXT
                )
            """
            )

            # 4. Answer Table
            cursor.execute(
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
            """
            )

            # 5. Association Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS question_objective_association (
                    id TEXT PRIMARY KEY,
                    question_id TEXT NOT NULL,
                    objective_id TEXT NOT NULL,
                    FOREIGN KEY (question_id) REFERENCES question (id) ON DELETE CASCADE,
                    FOREIGN KEY (objective_id) REFERENCES learning_objective (id) ON DELETE CASCADE,
                    UNIQUE(question_id, objective_id)
                )
            """
            )

            # 6. Question Embeddings Table (pgvector)
            cursor.execute(
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
            """
            )

            # Add canvas_id columns for Canvas dedup (idempotent)
            cursor.execute("ALTER TABLE question ADD COLUMN IF NOT EXISTS canvas_id INTEGER UNIQUE;")
            cursor.execute("ALTER TABLE answer ADD COLUMN IF NOT EXISTS canvas_id INTEGER UNIQUE;")

            # BM25 full-text search: tsvector column + GIN index + auto-update trigger
            cursor.execute(
                "ALTER TABLE question_embeddings ADD COLUMN IF NOT EXISTS content_tsv tsvector;"
            )
            cursor.execute(
                "UPDATE question_embeddings SET content_tsv = to_tsvector('english', content) WHERE content_tsv IS NULL;"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_question_embeddings_gin ON question_embeddings USING gin(content_tsv);"
            )
            cursor.execute(
                f"""
                CREATE OR REPLACE FUNCTION {self.schema}.update_content_tsv()
                RETURNS trigger AS $func$
                BEGIN
                    NEW.content_tsv := to_tsvector('english', NEW.content);
                    RETURN NEW;
                END;
                $func$ LANGUAGE plpgsql;
                """
            )
            cursor.execute(
                f"""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_content_tsv'
                    ) THEN
                        CREATE TRIGGER trg_content_tsv
                        BEFORE INSERT OR UPDATE OF content ON {self.schema}.question_embeddings
                        FOR EACH ROW EXECUTE FUNCTION {self.schema}.update_content_tsv();
                    END IF;
                END $$;
                """
            )

            # IVFFlat index for approximate nearest neighbor search
            # Only create if table has rows (IVFFlat requires data)
            cursor.execute(
                f"""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_indexes
                        WHERE schemaname = '{self.schema}'
                          AND indexname = 'idx_question_embeddings_cosine'
                    ) THEN
                        IF (SELECT COUNT(*) FROM question_embeddings) > 0 THEN
                            CREATE INDEX idx_question_embeddings_cosine
                            ON question_embeddings USING ivfflat (embedding vector_cosine_ops)
                            WITH (lists = 100);
                        END IF;
                    END IF;
                END $$;
            """
            )

            # 7. Evaluation Log Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS eval_log (
                    id TEXT PRIMARY KEY,
                    content_type TEXT NOT NULL,
                    content_id TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value FLOAT,
                    details JSONB DEFAULT '{}'::jsonb,
                    evaluated_at TIMESTAMPTZ DEFAULT NOW(),
                    evaluator TEXT DEFAULT 'auto',
                    batch_id TEXT
                )
            """)
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_eval_log_content ON eval_log(content_type, content_id);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_eval_log_metric ON eval_log(metric_name, evaluated_at);"
            )

            # 8. RAG Evaluation Samples Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rag_eval_samples (
                    id TEXT PRIMARY KEY,
                    query TEXT NOT NULL,
                    retrieved_contexts JSONB NOT NULL DEFAULT '[]'::jsonb,
                    response TEXT NOT NULL,
                    ground_truth TEXT,
                    student_id TEXT,
                    session_id TEXT,
                    intent TEXT,
                    instance TEXT DEFAULT 'a',
                    captured_at TIMESTAMPTZ DEFAULT NOW(),
                    evaluated BOOLEAN DEFAULT FALSE
                )
            """)
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_rag_samples_evaluated ON rag_eval_samples(evaluated, captured_at);"
            )

            conn.commit()
            logger.info("PostgreSQL database tables initialized successfully.")

    # --- Question & Answer CRUD ---

    def get_answers_for_questions(self, question_id: str) -> List[Dict]:
        """Gets all answers for a given question ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM answer WHERE question_id = %s ORDER BY id",
                (question_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def load_question_details(self, question_id: str) -> Optional[Dict[str, Any]]:
        """
        Loads a single question, its answers, and its associated
        objective IDs. Returns a dictionary.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM question WHERE id = %s", (question_id,))
                question_row = cursor.fetchone()
                if not question_row:
                    return None

                question = dict(question_row)
                question['answers'] = self.get_answers_for_questions(question_id)

                cursor.execute(
                    "SELECT objective_id FROM question_objective_association WHERE question_id = %s",
                    (question_id,)
                )
                objective_rows = cursor.fetchall()
                question['objective_ids'] = [row['objective_id'] for row in objective_rows]
                return question
        except Exception as e:
            logger.error(f"Error loading question details for {question_id}: {e}", exc_info=True)
            return None

    def list_all_questions(self) -> List[Dict]:
        """
        Fetches all questions from the database for the home page.
        Joins with association table for objective count.
        """
        logger.info("Fetching all questions from database for home page...")
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                query = """
                    SELECT
                        q.id,
                        q.question_text,
                        q.created_at,
                        COUNT(qoa.objective_id) AS objective_count
                    FROM
                        question q
                    LEFT JOIN
                        question_objective_association qoa ON q.id = qoa.question_id
                    GROUP BY
                        q.id, q.question_text, q.created_at
                    ORDER BY
                        q.created_at DESC;
                """
                cursor.execute(query)
                questions = [dict(row) for row in cursor.fetchall()]
                logger.info(f"Found {len(questions)} questions.")
                return questions
        except Exception as e:
            logger.error(f"Error listing all questions: {e}", exc_info=True)
            return []

    def update_question_and_answers(self, question_id: str, data: QuestionUpdate) -> bool:
        """Updates a question and its answers from the Pydantic model."""
        try:
            with self.get_connection(use_row_factory=False) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE question SET question_text = %s WHERE id = %s",
                    (data.question_text, question_id)
                )

                for answer in data.answers:
                    cursor.execute(
                        """
                        UPDATE answer
                        SET text = %s, is_correct = %s, feedback_text = %s, feedback_approved = %s
                        WHERE id = %s AND question_id = %s
                        """,
                        (
                            answer.text,
                            answer.is_correct,
                            answer.feedback_text,
                            answer.feedback_approved,
                            answer.id,
                            question_id
                        )
                    )

                cursor.execute(
                    "DELETE FROM question_objective_association WHERE question_id = %s",
                    (question_id,)
                )
                if data.objective_ids:
                    for obj_id in data.objective_ids:
                        if obj_id:
                            cursor.execute(
                                "INSERT INTO question_objective_association (id, question_id, objective_id) VALUES (%s, %s, %s)",
                                (str(uuid.uuid4()), question_id, obj_id)
                            )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating question {question_id}: {e}", exc_info=True)
            return False

    def update_answer_feedback(self, answer_id: str, feedback_text: str) -> bool:
        """Updates ONLY the feedback for a single answer."""
        try:
            with self.get_connection(use_row_factory=False) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE answer SET feedback_text = %s WHERE id = %s",
                    (feedback_text, answer_id)
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating feedback for answer {answer_id}: {e}", exc_info=True)
            return False

    def delete_question(self, question_id: str) -> bool:
        """Deletes a question. ON DELETE CASCADE handles answers/associations."""
        try:
            with self.get_connection(use_row_factory=False) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM question WHERE id = %s", (question_id,)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting question {question_id}: {e}", exc_info=True)
            return False

    # --- Learning Objective CRUD ---

    def list_all_objectives(self) -> List[Dict]:
        """Gets all objectives for dropdowns."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, text FROM learning_objective ORDER BY text"
            )
            return [dict(row) for row in cursor.fetchall()]

    def list_all_objectives_with_counts(self) -> List[Dict]:
        """Fetches all objectives and counts their associated questions."""
        logger.info("Fetching all objectives with question counts...")
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                query = """
                    SELECT
                        lo.id,
                        lo.text,
                        lo.created_at,
                        lo.blooms_level,
                        lo.priority,
                        COUNT(qoa.question_id) AS question_count
                    FROM
                        learning_objective lo
                    LEFT JOIN
                        question_objective_association qoa ON lo.id = qoa.objective_id
                    GROUP BY
                        lo.id, lo.text, lo.created_at, lo.blooms_level, lo.priority
                    ORDER BY
                        lo.created_at ASC;
                """
                cursor.execute(query)
                objectives = [dict(row) for row in cursor.fetchall()]
                logger.info(f"Found {len(objectives)} objectives.")
                return objectives
        except Exception as e:
            logger.error(f"Error listing all objectives: {e}", exc_info=True)
            return []

    def create_objective(self, text: str, blooms_level: str, priority: str) -> Dict:
        """Creates a new objective and returns it."""
        logger.info(f"Creating new objective...")
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                new_id = str(uuid.uuid4())
                created_at = datetime.now().isoformat()
                cursor.execute(
                    """
                    INSERT INTO learning_objective (id, text, created_at, blooms_level, priority)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (new_id, text, created_at, blooms_level, priority)
                )
                conn.commit()
                return {
                    "id": new_id, "text": text, "created_at": created_at,
                    "blooms_level": blooms_level, "priority": priority, "question_count": 0
                }
        except Exception as e:
            logger.error(f"Error creating objective in DB: {e}", exc_info=True)
            raise

    def get_objective(self, obj_id: str) -> Optional[Dict]:
        """Fetches a single objective by its ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM learning_objective WHERE id = %s", (obj_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting objective {obj_id}: {e}", exc_info=True)
            return None

    def update_objective(self, obj_id: str, text: str, blooms_level: str, priority: str) -> bool:
        """Updates an existing objective."""
        try:
            with self.get_connection(use_row_factory=False) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE learning_objective
                    SET text = %s, blooms_level = %s, priority = %s
                    WHERE id = %s
                    """,
                    (text, blooms_level, priority, obj_id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating objective {obj_id}: {e}", exc_info=True)
            return False

    def delete_objective(self, obj_id: str) -> bool:
        """Deletes an objective. ON DELETE CASCADE handles associations."""
        try:
            with self.get_connection(use_row_factory=False) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM learning_objective WHERE id = %s", (obj_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting objective {obj_id}: {e}", exc_info=True)
            return False

    def create_question_from_ai(self, question_data: Dict, objective_id: str) -> str:
        """Saves an AI-generated question and its answers to the DB."""
        try:
            with self.get_connection(use_row_factory=False) as conn:
                cursor = conn.cursor()

                new_q_id = str(uuid.uuid4())
                created_at = datetime.now().isoformat()
                cursor.execute(
                    "INSERT INTO question (id, question_text, created_at) VALUES (%s, %s, %s)",
                    (new_q_id, question_data['question_text'], created_at)
                )

                for ans in question_data['answers']:
                    new_a_id = str(uuid.uuid4())
                    cursor.execute(
                        """
                        INSERT INTO answer (id, question_id, text, is_correct, feedback_text, feedback_approved)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (new_a_id, new_q_id, ans['text'], ans['is_correct'], "Generated by AI.", False)
                    )

                new_assoc_id = str(uuid.uuid4())
                cursor.execute(
                    "INSERT INTO question_objective_association (id, question_id, objective_id) VALUES (%s, %s, %s)",
                    (new_assoc_id, new_q_id, objective_id)
                )

                conn.commit()
                logger.info(f"AI-generated question {new_q_id} saved and linked to objective {objective_id}")
                return new_q_id
        except Exception as e:
            logger.error(f"Error saving AI-generated question: {e}", exc_info=True)
            raise

    # --- Student Profile Methods ---

    def load_student_profile(self, student_id: str) -> Optional[StudentProfile]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM student_profiles WHERE id = %s", (student_id,)
                )
                row = cursor.fetchone()
                if row:
                    return StudentProfile(
                        id=row["id"],
                        name=row["name"],
                        current_topic=row["current_topic"],
                        knowledge_level=KnowledgeLevel(row["knowledge_level"]),
                        session_phase=SessionPhase(row["session_phase"]),
                        understanding_progression=row["understanding_progression"] or [],
                        misconceptions=row["misconceptions"] or [],
                        strengths=row["strengths"] or [],
                        warning_signs=row["warning_signs"] or [],
                        consecutive_correct=row["consecutive_correct"],
                        engagement_level=row["engagement_level"],
                        last_solid_understanding=row["last_solid_understanding"],
                        total_sessions=row["total_sessions"],
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                    )
                return None
        except Exception as e:
            logger.error(f"Error loading student profile {student_id}: {e}", exc_info=True)
            return None

    def save_student_profile(self, profile: StudentProfile) -> bool:
        try:
            profile.updated_at = datetime.now().isoformat()
            with self.get_connection(use_row_factory=False) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO student_profiles
                    (id, name, current_topic, knowledge_level, session_phase,
                     understanding_progression, misconceptions, strengths, warning_signs,
                     consecutive_correct, engagement_level, last_solid_understanding,
                     total_sessions, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        current_topic = EXCLUDED.current_topic,
                        knowledge_level = EXCLUDED.knowledge_level,
                        session_phase = EXCLUDED.session_phase,
                        understanding_progression = EXCLUDED.understanding_progression,
                        misconceptions = EXCLUDED.misconceptions,
                        strengths = EXCLUDED.strengths,
                        warning_signs = EXCLUDED.warning_signs,
                        consecutive_correct = EXCLUDED.consecutive_correct,
                        engagement_level = EXCLUDED.engagement_level,
                        last_solid_understanding = EXCLUDED.last_solid_understanding,
                        total_sessions = EXCLUDED.total_sessions,
                        created_at = EXCLUDED.created_at,
                        updated_at = EXCLUDED.updated_at
                """,
                    (
                        profile.id,
                        profile.name,
                        profile.current_topic,
                        profile.knowledge_level.value,
                        profile.session_phase.value,
                        Json(profile.understanding_progression),
                        Json(profile.misconceptions),
                        Json(profile.strengths),
                        Json(profile.warning_signs),
                        profile.consecutive_correct,
                        profile.engagement_level,
                        profile.last_solid_understanding,
                        profile.total_sessions,
                        profile.created_at,
                        profile.updated_at,
                    ),
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving student profile: {e}", exc_info=True)
            return False

    def list_all_students(self) -> List[Dict]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, name, current_topic, knowledge_level, session_phase,
                           total_sessions, updated_at
                    FROM student_profiles
                    ORDER BY updated_at DESC
                """
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error listing students: {e}", exc_info=True)
            return []

    def create_question_with_answers(self, data) -> str:
        """Creates a new question with answers and objective associations."""
        new_question_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        with self.get_connection(use_row_factory=False) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO question (id, question_text, created_at) VALUES (%s, %s, %s)",
                (new_question_id, data.question_text, created_at)
            )
            for answer in data.answers:
                if answer.text.strip():
                    cursor.execute(
                        """INSERT INTO answer (id, question_id, text, is_correct, feedback_text, feedback_approved)
                        VALUES (%s, %s, %s, %s, %s, %s)""",
                        (str(uuid.uuid4()), new_question_id, answer.text, answer.is_correct, '', False)
                    )
            if data.objective_ids:
                for obj_id in data.objective_ids:
                    if obj_id:
                        cursor.execute(
                            "INSERT INTO question_objective_association (id, question_id, objective_id) VALUES (%s, %s, %s)",
                            (str(uuid.uuid4()), new_question_id, obj_id)
                        )
            conn.commit()
        return new_question_id

    def replace_question_objectives(self, question_id: str, objective_ids: List[str]) -> bool:
        """Replaces all objective associations for a question."""
        try:
            with self.get_connection(use_row_factory=False) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM question_objective_association WHERE question_id = %s",
                    (question_id,)
                )
                for obj_id in objective_ids:
                    if obj_id:
                        cursor.execute(
                            "INSERT INTO question_objective_association (id, question_id, objective_id) VALUES (%s, %s, %s)",
                            (str(uuid.uuid4()), question_id, obj_id)
                        )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error replacing objectives for question {question_id}: {e}", exc_info=True)
            return False

    def bulk_upsert_from_canvas(self, canvas_questions: List[Dict]) -> Dict[str, Any]:
        """
        Insert Canvas questions into the DB with dedup by canvas_id.
        Returns stats dict with inserted/skipped counts and new_question_ids.
        """
        inserted = 0
        skipped = 0
        total_answers_inserted = 0
        new_question_ids = []

        try:
            with self.get_connection(use_row_factory=False) as conn:
                cursor = conn.cursor()

                # Fetch all existing canvas_ids in one query
                cursor.execute("SELECT canvas_id FROM question WHERE canvas_id IS NOT NULL")
                existing_canvas_ids = {row[0] for row in cursor.fetchall()}

                for cq in canvas_questions:
                    canvas_q_id = cq.get("id")
                    if canvas_q_id is None:
                        continue

                    if canvas_q_id in existing_canvas_ids:
                        skipped += 1
                        continue

                    # Clean the question text (already cleaned by fetch_all_questions,
                    # but the raw question_text from Canvas JSON may still have HTML)
                    question_text = cq.get("question_text", "")

                    new_q_id = str(uuid.uuid4())
                    created_at = datetime.now().isoformat()

                    cursor.execute(
                        """INSERT INTO question (id, question_text, created_at, canvas_id)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (canvas_id) DO NOTHING""",
                        (new_q_id, question_text, created_at, canvas_q_id)
                    )

                    if cursor.rowcount == 0:
                        # Race condition: another process inserted it
                        skipped += 1
                        continue

                    # Insert answers
                    for a in cq.get("answers", []):
                        # Prefer html field with html_to_markdown conversion
                        if a.get("html"):
                            answer_text = html_to_markdown(a["html"])
                        else:
                            answer_text = a.get("text", "")

                        is_correct = a.get("weight", 0) > 0
                        canvas_a_id = a.get("id")

                        new_a_id = str(uuid.uuid4())
                        cursor.execute(
                            """INSERT INTO answer (id, question_id, text, is_correct, feedback_text, feedback_approved, canvas_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (canvas_id) DO NOTHING""",
                            (new_a_id, new_q_id, answer_text, is_correct, "", False, canvas_a_id)
                        )
                        if cursor.rowcount > 0:
                            total_answers_inserted += 1

                    inserted += 1
                    new_question_ids.append(new_q_id)
                    existing_canvas_ids.add(canvas_q_id)

                conn.commit()

        except Exception as e:
            logger.error(f"Error in bulk_upsert_from_canvas: {e}", exc_info=True)
            raise

        logger.info(
            f"Canvas upsert: {inserted} inserted, {skipped} skipped, "
            f"{total_answers_inserted} answers inserted"
        )
        return {
            "inserted": inserted,
            "skipped": skipped,
            "total_answers_inserted": total_answers_inserted,
            "new_question_ids": new_question_ids,
        }
