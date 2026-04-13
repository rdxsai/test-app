"""
Evaluation Repository — database operations for the eval pipeline.

Manages two tables:
  - eval_log: stores metric results (readability, faithfulness, etc.)
  - rag_eval_samples: captured RAG triples (query, contexts, response)
"""

import json
import logging
import uuid
from typing import Any, Dict, List, Optional

from ..database import DatabaseManager, get_database_manager

logger = logging.getLogger(__name__)


class EvalRepository:
    """Database operations for evaluation tables.

    Follows the same connection pattern as DatabaseManager — uses
    get_connection() context manager with schema isolation.
    """

    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or get_database_manager()

    # ------------------------------------------------------------------
    # eval_log operations
    # ------------------------------------------------------------------

    def log_eval(
        self,
        content_type: str,
        content_id: str,
        metric_name: str,
        metric_value: float,
        details: Optional[Dict] = None,
        evaluator: str = "auto",
        batch_id: Optional[str] = None,
    ) -> str:
        """Log an evaluation result. Returns the eval_log ID."""
        eval_id = str(uuid.uuid4())
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO eval_log
                        (id, content_type, content_id, metric_name, metric_value,
                         details, evaluator, batch_id)
                    VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s)
                    """,
                    (eval_id, content_type, content_id, metric_name, metric_value,
                     json.dumps(details or {}), evaluator, batch_id),
                )
            conn.commit()
        logger.info(f"Eval logged: {metric_name}={metric_value:.3f} for {content_type}/{content_id}")
        return eval_id

    def get_eval_logs(
        self,
        content_type: Optional[str] = None,
        content_id: Optional[str] = None,
        metric_name: Optional[str] = None,
        batch_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Query eval logs with optional filters."""
        conditions = []
        params = []

        if content_type:
            conditions.append("content_type = %s")
            params.append(content_type)
        if content_id:
            conditions.append("content_id = %s")
            params.append(content_id)
        if metric_name:
            conditions.append("metric_name = %s")
            params.append(metric_name)
        if batch_id:
            conditions.append("batch_id = %s")
            params.append(batch_id)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        params.extend([limit, offset])

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT * FROM eval_log
                    {where}
                    ORDER BY evaluated_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    params,
                )
                return [dict(row) for row in cur.fetchall()]

    def get_eval_summary(
        self,
        content_type: str,
        metric_name: Optional[str] = None,
        batch_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Aggregated summary: avg, min, max, count per metric for a content type."""
        conditions = ["content_type = %s"]
        params = [content_type]
        if metric_name:
            conditions.append("metric_name = %s")
            params.append(metric_name)
        if batch_id:
            conditions.append("batch_id = %s")
            params.append(batch_id)

        where = " AND ".join(conditions)

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT metric_name,
                           COUNT(*) as sample_count,
                           AVG(metric_value) as avg_value,
                           MIN(metric_value) as min_value,
                           MAX(metric_value) as max_value
                    FROM eval_log
                    WHERE {where}
                    GROUP BY metric_name
                    ORDER BY metric_name
                    """,
                    params,
                )
                rows = [dict(row) for row in cur.fetchall()]

        return {
            "content_type": content_type,
            "batch_id": batch_id,
            "metrics": {
                row["metric_name"]: {
                    "avg": float(row["avg_value"]) if row["avg_value"] else 0,
                    "min": float(row["min_value"]) if row["min_value"] else 0,
                    "max": float(row["max_value"]) if row["max_value"] else 0,
                    "count": row["sample_count"],
                }
                for row in rows
            },
        }

    # ------------------------------------------------------------------
    # rag_eval_samples operations
    # ------------------------------------------------------------------

    def capture_rag_sample(
        self,
        query: str,
        retrieved_contexts: List[str],
        response: str,
        ground_truth: Optional[str] = None,
        student_id: Optional[str] = None,
        session_id: Optional[str] = None,
        intent: Optional[str] = None,
        instance: str = "a",
    ) -> str:
        """Capture a RAG triple for later evaluation. Returns sample ID."""
        sample_id = str(uuid.uuid4())
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO rag_eval_samples
                        (id, query, retrieved_contexts, response,
                         ground_truth, student_id, session_id, intent, instance)
                    VALUES (%s, %s, %s::jsonb, %s, %s, %s, %s, %s, %s)
                    """,
                    (sample_id, query, json.dumps(retrieved_contexts),
                     response, ground_truth, student_id, session_id, intent, instance),
                )
            conn.commit()
        logger.info(f"RAG sample captured: {sample_id} ({len(retrieved_contexts)} contexts)")
        return sample_id

    def get_rag_samples(
        self, evaluated: Optional[bool] = None, limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List captured RAG samples, optionally filtered by evaluation status."""
        conditions = []
        params = []
        if evaluated is not None:
            conditions.append("evaluated = %s")
            params.append(evaluated)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        params.append(limit)

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT * FROM rag_eval_samples
                    {where}
                    ORDER BY captured_at DESC
                    LIMIT %s
                    """,
                    params,
                )
                return [dict(row) for row in cur.fetchall()]

    def get_rag_sample(self, sample_id: str) -> Optional[Dict[str, Any]]:
        """Get a single RAG sample by ID."""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM rag_eval_samples WHERE id = %s",
                    (sample_id,),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def get_rag_sample_with_eval(self, sample_id: str) -> Optional[Dict[str, Any]]:
        """Get a RAG sample plus its attached eval metrics."""
        sample = self.get_rag_sample(sample_id)
        if not sample:
            return None

        eval_logs = self.get_eval_logs(
            content_type="rag_sample",
            content_id=sample_id,
            limit=100,
        )
        sample["eval_metrics"] = eval_logs
        sample["eval_metrics_by_name"] = {
            row["metric_name"]: {
                "value": row["metric_value"],
                "details": row.get("details", {}),
                "evaluated_at": row.get("evaluated_at"),
                "evaluator": row.get("evaluator"),
            }
            for row in eval_logs
        }
        return sample

    def get_batch_rag_samples_with_eval(
        self,
        batch_id: str,
        instance: Optional[str] = None,
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        """Get all RAG samples associated with a benchmark/eval batch."""
        conditions = [
            "e.batch_id = %s",
            "e.content_type = 'rag_sample'",
        ]
        params: List[Any] = [batch_id]
        if instance:
            conditions.append("s.instance = %s")
            params.append(instance)
        params.append(limit)

        where = " AND ".join(conditions)

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT DISTINCT s.*
                    FROM rag_eval_samples s
                    JOIN eval_log e ON e.content_id = s.id
                    WHERE {where}
                    ORDER BY s.captured_at DESC
                    LIMIT %s
                    """,
                    params,
                )
                samples = [dict(row) for row in cur.fetchall()]

        eval_logs = self.get_eval_logs(
            content_type="rag_sample",
            batch_id=batch_id,
            limit=max(limit * 50, 200),
        )
        logs_by_content_id: Dict[str, List[Dict[str, Any]]] = {}
        for row in eval_logs:
            logs_by_content_id.setdefault(row["content_id"], []).append(row)

        for sample in samples:
            sample_logs = logs_by_content_id.get(sample["id"], [])
            sample["eval_metrics"] = sample_logs
            sample["eval_metrics_by_name"] = {
                row["metric_name"]: {
                    "value": row["metric_value"],
                    "details": row.get("details", {}),
                    "evaluated_at": row.get("evaluated_at"),
                    "evaluator": row.get("evaluator"),
                    "batch_id": row.get("batch_id"),
                }
                for row in sample_logs
            }

        return samples

    def mark_evaluated(self, sample_id: str) -> bool:
        """Mark a RAG sample as evaluated."""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE rag_eval_samples SET evaluated = TRUE WHERE id = %s",
                    (sample_id,),
                )
            conn.commit()
            return cur.rowcount > 0
