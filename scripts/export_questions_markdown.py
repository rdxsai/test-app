"""
Export all questions and answers from the app database to structured JSON.

The export preserves question, answer, and feedback text as markdown-ready text.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.append(str(SRC_ROOT))

from question_app.services.database import get_database_manager
from question_app.utils.text_utils import html_to_markdown


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _as_markdown(text: str | None, raw: bool = False) -> str:
    if not text:
        return ""
    if raw:
        return text
    # Convert only when content looks like HTML; otherwise keep existing markdown/plain text.
    if "<" in text and ">" in text:
        return html_to_markdown(text)
    return text


def export_questions(output_path: Path, raw: bool = False) -> dict[str, Any]:
    db = get_database_manager()

    try:
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        q.id AS question_id,
                        q.canvas_id AS question_canvas_id,
                        q.created_at AS question_created_at,
                        q.question_text,
                        a.id AS answer_id,
                        a.canvas_id AS answer_canvas_id,
                        a.text AS answer_text,
                        a.is_correct,
                        a.feedback_text,
                        a.feedback_approved
                    FROM question q
                    LEFT JOIN answer a ON a.question_id = q.id
                    ORDER BY q.created_at DESC, q.id, a.id
                    """
                )
                rows = cursor.fetchall()

        question_map: dict[str, dict[str, Any]] = {}

        for row in rows:
            question_id = row["question_id"]
            if question_id not in question_map:
                question_map[question_id] = {
                    "question_id": question_id,
                    "question_canvas_id": row.get("question_canvas_id"),
                    "question_created_at": row.get("question_created_at"),
                    "question_text_markdown": _as_markdown(row.get("question_text"), raw=raw),
                    "answers": [],
                }

            if row.get("answer_id") is not None:
                question_map[question_id]["answers"].append(
                    {
                        "answer_id": row.get("answer_id"),
                        "answer_canvas_id": row.get("answer_canvas_id"),
                        "answer_text_markdown": _as_markdown(row.get("answer_text"), raw=raw),
                        "is_correct": bool(row.get("is_correct", False)),
                        "feedback_markdown": _as_markdown(row.get("feedback_text"), raw=raw),
                        "feedback_approved": bool(row.get("feedback_approved", False)),
                    }
                )

        questions = list(question_map.values())
        payload = {
            "exported_at": _now_utc_iso(),
            "source": "question_app_database",
            "format": "questions_with_answers_raw_v1" if raw else "questions_with_answers_markdown_v1",
            "question_count": len(questions),
            "questions": questions,
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

        return {
            "output_path": str(output_path),
            "question_count": len(questions),
        }
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export questions/answers/correctness/feedback as markdown-ready JSON."
    )
    parser.add_argument(
        "--output",
        default="exports/questions_markdown_export.json",
        help="Path to output JSON file (default: exports/questions_markdown_export.json)",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Skip HTML-to-markdown conversion; export raw text/HTML as stored in the database.",
    )
    args = parser.parse_args()

    result = export_questions(Path(args.output), raw=args.raw)
    print(
        f"Export complete: {result['question_count']} questions -> {result['output_path']}"
    )


if __name__ == "__main__":
    main()