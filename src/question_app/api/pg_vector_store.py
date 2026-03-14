"""
Vector Store Service using PostgreSQL + pgvector.
"""

import logging
import uuid
from typing import List, Dict, Any

from pgvector.psycopg2 import register_vector

from ..core import config, get_logger
from ..services.database import get_database_manager
from ..services.tutor.interfaces import VectorStoreInterface
from .vector_store import get_ollama_embeddings, create_comprehensive_chunks

logger = get_logger(__name__)


class VectorStoreService(VectorStoreInterface):
    """
    Vector store service backed by PostgreSQL + pgvector.
    """

    def __init__(self):
        self.db = get_database_manager()
        logger.info("VectorStoreService initialized")

    async def search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        Perform semantic search using pgvector cosine distance.
        Returns results as list of dicts with content and metadata.
        """
        try:
            query_embeddings = await get_ollama_embeddings([query])
            if not query_embeddings or not query_embeddings[0]:
                logger.error("Failed to generate query embedding")
                return []

            query_vector = query_embeddings[0]

            with self.db.get_connection() as conn:
                register_vector(conn)
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, question_id, chunk_type, answer_index, is_correct,
                           topic, tags, question_type, learning_objective, content,
                           embedding <=> %s::vector AS distance
                    FROM question_embeddings
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (str(query_vector), str(query_vector), k)
                )
                rows = cursor.fetchall()

            results = []
            for r in rows:
                chunk = {
                    'question_id': r['question_id'],
                    'chunk_type': r['chunk_type'],
                    'topic': r['topic'],
                    'tags': r['tags'],
                    'question_type': r['question_type'],
                    'learning_objective': r['learning_objective'],
                    'content': r['content'],
                    'distance': r['distance'],
                }
                if r['answer_index'] is not None:
                    chunk['answer_index'] = r['answer_index']
                if r['is_correct'] is not None:
                    chunk['is_correct'] = r['is_correct']
                results.append(chunk)

            logger.info(f"pgvector search returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"pgvector search failed: {e}", exc_info=True)
            return []

    async def hybrid_search(self, query: str, k: int = 3, bm25_query: str = "") -> List[Dict[str, Any]]:
        """
        Hybrid search combining pgvector cosine + BM25 ts_rank_cd via
        Reciprocal Rank Fusion (RRF). Returns top-k results scored by
        rrf_score = 1/(60+vec_rank) + 1/(60+bm25_rank).

        query: text to embed for vector search (e.g. HyDE hypothetical answer)
        bm25_query: separate text for BM25 keyword matching (e.g. original student words).
                    Falls back to query if not provided.
        """
        bm25_text = bm25_query or query
        try:
            query_embeddings = await get_ollama_embeddings([query])
            if not query_embeddings or not query_embeddings[0]:
                logger.error("Failed to generate query embedding for hybrid search")
                return []

            query_vector = query_embeddings[0]
            pool_size = k * 3

            with self.db.get_connection() as conn:
                register_vector(conn)
                cursor = conn.cursor()
                cursor.execute(
                    """
                    WITH vector_results AS (
                        SELECT id, question_id, chunk_type, answer_index, is_correct,
                               topic, tags, question_type, learning_objective, content,
                               embedding <=> %(vec)s::vector AS distance,
                               ROW_NUMBER() OVER (ORDER BY embedding <=> %(vec)s::vector) AS vec_rank
                        FROM question_embeddings
                        ORDER BY embedding <=> %(vec)s::vector
                        LIMIT %(pool)s
                    ),
                    bm25_results AS (
                        SELECT id, question_id, chunk_type, answer_index, is_correct,
                               topic, tags, question_type, learning_objective, content,
                               ts_rank_cd(content_tsv, plainto_tsquery('english', %(q)s)) AS bm25_score,
                               ROW_NUMBER() OVER (
                                   ORDER BY ts_rank_cd(content_tsv, plainto_tsquery('english', %(q)s)) DESC
                               ) AS bm25_rank
                        FROM question_embeddings
                        WHERE content_tsv @@ plainto_tsquery('english', %(q)s)
                        ORDER BY bm25_score DESC
                        LIMIT %(pool)s
                    ),
                    combined AS (
                        SELECT
                            COALESCE(v.id, b.id) AS id,
                            COALESCE(v.question_id, b.question_id) AS question_id,
                            COALESCE(v.chunk_type, b.chunk_type) AS chunk_type,
                            COALESCE(v.answer_index, b.answer_index) AS answer_index,
                            COALESCE(v.is_correct, b.is_correct) AS is_correct,
                            COALESCE(v.topic, b.topic) AS topic,
                            COALESCE(v.tags, b.tags) AS tags,
                            COALESCE(v.question_type, b.question_type) AS question_type,
                            COALESCE(v.learning_objective, b.learning_objective) AS learning_objective,
                            COALESCE(v.content, b.content) AS content,
                            v.distance,
                            v.vec_rank,
                            b.bm25_rank,
                            COALESCE(1.0 / (60 + v.vec_rank), 0)
                              + COALESCE(1.0 / (60 + b.bm25_rank), 0) AS rrf_score
                        FROM vector_results v
                        FULL OUTER JOIN bm25_results b ON v.id = b.id
                    )
                    SELECT * FROM combined
                    ORDER BY rrf_score DESC
                    LIMIT %(k)s
                    """,
                    {"vec": str(query_vector), "q": bm25_text, "pool": pool_size, "k": k},
                )
                rows = cursor.fetchall()

            results = []
            for r in rows:
                chunk = {
                    'question_id': r['question_id'],
                    'chunk_type': r['chunk_type'],
                    'topic': r['topic'],
                    'tags': r['tags'],
                    'question_type': r['question_type'],
                    'learning_objective': r['learning_objective'],
                    'content': r['content'],
                    'distance': r['distance'],
                    'rrf_score': float(r['rrf_score']) if r['rrf_score'] else 0.0,
                }
                if r['answer_index'] is not None:
                    chunk['answer_index'] = r['answer_index']
                if r['is_correct'] is not None:
                    chunk['is_correct'] = r['is_correct']
                results.append(chunk)

            logger.info(f"Hybrid search returned {len(results)} results (RRF)")
            return results

        except Exception as e:
            logger.error(f"Hybrid search failed: {e}", exc_info=True)
            # Fall back to vector-only search
            logger.info("Falling back to vector-only search")
            return await self.search(query, k)

    async def embed_single_question(self, question_id: str) -> int:
        """Generate and store embeddings for a single question + its answers.
        Returns number of chunks embedded."""
        q_detail = self.db.load_question_details(question_id)
        if not q_detail:
            logger.warning(f"Question {question_id} not found, skipping embedding.")
            return 0

        documents, metadatas, ids = create_comprehensive_chunks([q_detail])
        if not documents:
            logger.warning(f"No chunks created for question {question_id}.")
            return 0

        embeddings = await get_ollama_embeddings(documents)

        with self.db.get_connection(use_row_factory=False) as conn:
            register_vector(conn)
            cursor = conn.cursor()

            # Delete existing embeddings for this question (handles edit/re-embed)
            cursor.execute(
                "DELETE FROM question_embeddings WHERE question_id = %s",
                (question_id,)
            )

            for doc, meta, emb, chunk_id in zip(documents, metadatas, embeddings, ids):
                cursor.execute(
                    """
                    INSERT INTO question_embeddings
                    (id, question_id, chunk_type, answer_index, is_correct,
                     topic, tags, question_type, learning_objective, content, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::vector)
                    """,
                    (
                        chunk_id,
                        meta.get('question_id', ''),
                        meta.get('chunk_type', 'question'),
                        meta.get('answer_index'),
                        meta.get('is_correct'),
                        meta.get('topic', 'Web Accessibility'),
                        meta.get('tags', ''),
                        meta.get('question_type', 'multiple_choice_question'),
                        meta.get('learning_objective', ''),
                        doc,
                        str(emb),
                    )
                )

            conn.commit()

        logger.info(f"Embedded {len(documents)} chunks for question {question_id}")
        return len(documents)

    async def create_vector_store(self) -> Dict[str, Any]:
        """
        Fetch all questions from DB, generate embeddings, store in question_embeddings table.
        """
        try:
            logger.info("Starting pgvector vector store creation...")

            db_manager = get_database_manager()
            questions_from_db = db_manager.list_all_questions()

            if not questions_from_db:
                logger.warning("No questions found in database.")
                return {"message": "No questions found in database.", "count": 0}

            logger.info(f"Fetched {len(questions_from_db)} questions from database.")

            full_questions_data = []
            for q_header in questions_from_db:
                q_detail = db_manager.load_question_details(q_header['id'])
                if q_detail:
                    full_questions_data.append(q_detail)

            logger.info("Creating comprehensive chunks...")
            documents, metadatas, ids = create_comprehensive_chunks(full_questions_data)
            logger.info(f"Created {len(documents)} document chunks")

            logger.info("Generating embeddings via Ollama...")
            embeddings = await get_ollama_embeddings(documents)
            logger.info(f"Generated {len(embeddings)} embeddings")

            with self.db.get_connection(use_row_factory=False) as conn:
                register_vector(conn)
                cursor = conn.cursor()

                # Clear existing embeddings
                cursor.execute("DELETE FROM question_embeddings;")

                for doc, meta, emb, chunk_id in zip(documents, metadatas, embeddings, ids):
                    cursor.execute(
                        """
                        INSERT INTO question_embeddings
                        (id, question_id, chunk_type, answer_index, is_correct,
                         topic, tags, question_type, learning_objective, content, embedding)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::vector)
                        """,
                        (
                            chunk_id,
                            meta.get('question_id', ''),
                            meta.get('chunk_type', 'question'),
                            meta.get('answer_index'),
                            meta.get('is_correct'),
                            meta.get('topic', 'Web Accessibility'),
                            meta.get('tags', ''),
                            meta.get('question_type', 'multiple_choice_question'),
                            meta.get('learning_objective', ''),
                            doc,
                            str(emb),
                        )
                    )

                conn.commit()

            # Recreate IVFFlat index now that we have data
            with self.db.get_connection(use_row_factory=False) as conn:
                cursor = conn.cursor()
                cursor.execute("DROP INDEX IF EXISTS idx_question_embeddings_cosine;")
                row_count_result = cursor.execute("SELECT COUNT(*) FROM question_embeddings")
                row_count = cursor.fetchone()[0]
                if row_count > 0:
                    # lists should be <= sqrt(row_count), min 1
                    lists = min(100, max(1, int(row_count ** 0.5)))
                    cursor.execute(
                        f"""
                        CREATE INDEX idx_question_embeddings_cosine
                        ON question_embeddings USING ivfflat (embedding vector_cosine_ops)
                        WITH (lists = {lists});
                        """
                    )
                conn.commit()

            logger.info("pgvector vector store created successfully.")

            return {
                "message": "Vector store created successfully.",
                "stats": {
                    "total_documents": len(documents),
                    "embedding_model": config.OLLAMA_EMBEDDING_MODEL,
                }
            }

        except Exception as e:
            logger.error(f"Failed to create pgvector vector store: {e}", exc_info=True)
            from fastapi import HTTPException
            raise HTTPException(
                status_code=500, detail=f"Failed to create vector store: {e}"
            )
