"""
Vector Store API module for the Question App.

This module provides an interface for vector store operations,
including creating the vector store and performing semantic search.
It uses PostgreSQL + pgvector as the backend and Ollama for embeddings.
"""

import httpx
import logging
import asyncio
from typing import List, Dict, Any, Tuple
from fastapi import APIRouter, HTTPException, BackgroundTasks

from ..core import config, get_logger
from ..models import Question
from ..services.database import get_database_manager
from ..services.tutor.interfaces import VectorStoreInterface
from ..utils import (
    clean_question_text,
    extract_topic_from_text,
    load_questions,
    clean_answer_feedback
)

logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/vector-store", tags=["vector-store"])


# --- === OLLAMA EMBEDDING FUNCTION === ---
async def get_ollama_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Get embeddings from Ollama using the nomic-embed-text model.
    """
    embeddings = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, text in enumerate(texts):
            try:
                if not text.strip():
                    logger.warning(f"Empty text at index {i}, skipping.")
                    embeddings.append([0.0] * 768)
                    continue

                payload = {
                    "model": config.OLLAMA_EMBEDDING_MODEL,
                    "prompt": text.strip(),
                }
                response = await client.post(
                    f"{config.OLLAMA_HOST}/api/embeddings",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()

                result = response.json()
                if "embedding" not in result:
                    logger.error(f"No embedding in response for text {i}: {result}")
                    embeddings.append([0.0] * 768)
                    continue

                embeddings.append(result["embedding"])

                if i < len(texts) - 1:
                    await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Error generating embedding for text {i}: {e}")
                embeddings.append([0.0] * 768)

    logger.info(f"Generated {len(embeddings)} embeddings from {len(texts)} texts")
    return embeddings


def create_comprehensive_chunks(
    questions: List[Dict[str, Any]]
) -> Tuple[List[str], List[Dict[str, Any]], List[str]]:
    """
    Create comprehensive chunks from quiz questions for vector store processing.
    """
    documents = []
    metadatas = []
    ids = []

    for question in questions:
        question_id = str(question.get("id", "unknown"))
        question_text = clean_question_text(question.get("question_text", ""))

        general_feedback = clean_question_text(
            question.get("neutral_comments", "")
        )
        topic = question.get("topic", "Web Accessibility")
        tags = ", ".join(question.get("tags", []))
        learning_objective = question.get("learning_objective", "")
        question_type = question.get("question_type", "multiple_choice_question")

        # Create main question chunk
        if question_text:
            main_content = f"Question: {question_text}"
            if general_feedback:
                main_content += f"\n\nGeneral Feedback: {general_feedback}"
            if learning_objective:
                main_content += f"\n\nLearning Objective: {learning_objective}"

            documents.append(main_content)
            metadatas.append(
                {
                    "question_id": question_id,
                    "chunk_type": "question",
                    "topic": topic,
                    "tags": tags,
                    "question_type": question_type,
                    "learning_objective": learning_objective,
                }
            )
            ids.append(f"q_{question_id}_main")

        # Create answer-specific chunks
        answers = question.get("answers", [])
        for i, answer in enumerate(answers):
            answer_text = clean_question_text(answer.get("text", ""))
            answer_feedback = clean_answer_feedback(answer.get("feedback_text", ""))
            answer_feedback = clean_question_text(answer_feedback)

            if answer_text:
                answer_content = (
                    f"Question: {question_text}\n\nAnswer {i+1}: {answer_text}"
                )
                if answer_feedback:
                    answer_content += f"\n\nAnswer Feedback: {answer_feedback}"

                documents.append(answer_content)
                metadatas.append(
                    {
                        "question_id": question_id,
                        "chunk_type": "answer",
                        "answer_index": i,
                        "is_correct": answer.get("is_correct", False),
                        "topic": topic,
                        "tags": tags,
                        "question_type": question_type,
                        "learning_objective": learning_objective,
                    }
                )
                ids.append(f"q_{question_id}_answer_{i}")

    logger.info(
        f"Created {len(documents)} comprehensive chunks from {len(questions)} questions"
    )
    return documents, metadatas, ids


# --- === API Endpoints for the /vector-store router === ---

@router.post("/create")
async def create_vector_store_endpoint(background_tasks: BackgroundTasks):
    """
    API endpoint to create/update the vector store.
    """
    logger.info("Received request to create vector store.")
    try:
        from .pg_vector_store import VectorStoreService
        vector_service = VectorStoreService()
        result = await vector_service.create_vector_store()
        return result
    except Exception as e:
        logger.error(f"Endpoint /create failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search_vector_store_endpoint(query: str):
    """
    API endpoint to test semantic search.
    """
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    try:
        from .pg_vector_store import VectorStoreService
        vector_service = VectorStoreService()
        results = await vector_service.search(query, k=3)
        return {"results": results}
    except Exception as e:
        logger.error(f"Endpoint /search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_vector_store_status():
    """Get the current status of the vector store"""
    try:
        db_manager = get_database_manager()
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM question_embeddings")
            row = cursor.fetchone()
            count = row['cnt'] if row else 0
        return {
            "success": True,
            "status": "active" if count > 0 else "not_initialized",
            "collection_name": "question_embeddings",
            "document_count": count,
        }
    except Exception as e:
        logger.error(f"Error checking vector store status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to check vector store status: {str(e)}"
        )


@router.delete("/")
async def delete_vector_store():
    """Delete the entire vector store"""
    try:
        db_manager = get_database_manager()
        with db_manager.get_connection(use_row_factory=False) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM question_embeddings;")
            conn.commit()
        logger.info("Vector store embeddings deleted successfully")
        return {"success": True, "message": "Vector store deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting vector store: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete vector store: {str(e)}"
        )
