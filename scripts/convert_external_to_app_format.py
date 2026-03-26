"""
Convert externally-created resource files into the same JSON format produced
by the app's built-in export scripts.

Source files (created outside the app):
  resources/objectives_deeper_assessment_optimized_plus_gaps.json
  resources/deep/chat_attachments_combined/questions_combined_from_chat_attachments.json
  resources/gold_mapping.json

Output files (same schema as app exports):
  data/objectives_from_resources.json       ← mirrors data/objectives_export.json
  exports/questions_from_attachments.json   ← mirrors exports/questions_markdown_export.json
  exports/question_objective_mappings_from_gold.json  ← mirrors exports/question_objective_mappings.json

Schema notes (properties present in the app export but not in source files):
  objectives:
    - id            → uses the objective code (e.g. "I.A.1") since source has no UUIDs;
                      the DB column is TEXT PRIMARY KEY so any text is valid.
    - blooms_level  → mapped from cognitive_level (Analyze→analyze, Apply→apply,
                      Evaluate→evaluate, Explain→understand, Identify→remember).
    - priority      → defaults to "medium" (actively used in the UI; not present
                      in the source file). Review and update manually if needed.
  question_objective_mappings:
    - prompt_tokens / completion_tokens / total_* → set to null (manual mappings
      have no token counts; these fields are generated-only and not read by the app).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# Bloom's level mapping  (source cognitive_level → app blooms_level)
# Valid app values: remember, understand, apply, analyze, evaluate, create
# ---------------------------------------------------------------------------
COGNITIVE_TO_BLOOMS: dict[str, str] = {
    "remember": "remember",
    "understand": "understand",
    "apply": "apply",
    "analyze": "analyze",
    "evaluate": "evaluate",
    "create": "create",
    # values found in the source file that need mapping
    "explain": "understand",
    "identify": "remember",
    "describe": "understand",
    "differentiate": "analyze",
    "compare": "analyze",
    "assess": "evaluate",
    "demonstrate": "apply",
    "interpret": "understand",
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _get_primary_code(entry: dict) -> str | None:
    """Return the primary objective code, handling old and new gold_mapping formats."""
    return entry.get("primary_objective_id") or entry.get("primary") or None


def _get_secondary_codes(entry: dict) -> list[str]:
    """Return secondary objective codes, handling old and new gold_mapping formats."""
    return entry.get("secondary_objective_ids") or entry.get("secondary") or []


# ---------------------------------------------------------------------------
# 1. Objectives
# ---------------------------------------------------------------------------

def convert_objectives() -> None:
    src_path = ROOT / "resources/objectives_deeper_assessment_optimized_plus_gaps.json"
    gold_path = ROOT / "resources/gold_mapping.json"
    q_path = ROOT / "resources/deep/chat_attachments_combined/questions_combined_from_chat_attachments.json"
    out_path = ROOT / "data/objectives_from_resources.json"

    raw_objectives: dict = json.loads(src_path.read_text(encoding="utf-8"))
    gold: list[dict] = json.loads(gold_path.read_text(encoding="utf-8"))
    q_data: dict = json.loads(q_path.read_text(encoding="utf-8"))

    # Build lookup: objective_code → objective_text
    obj_text_by_code: dict[str, str] = {
        code: obj["text"]
        for code, obj in raw_objectives.items()
        if isinstance(obj, dict) and "text" in obj
    }

    # Build lookup: question_id → question record
    q_by_id: dict[str, dict] = {
        q["question_id"]: q for q in q_data["questions"]
    }

    # Convert objectives array
    objectives = []
    for code, obj in raw_objectives.items():
        if not isinstance(obj, dict):
            continue
        cognitive = obj.get("cognitive_level", "understand").lower()
        blooms = COGNITIVE_TO_BLOOMS.get(cognitive, "understand")

        record: dict = {
            "id": code,           # code used as text primary key (no UUID in source)
            "objective_code": code,  # extra field: the structured code
            "text": obj["text"],
            "blooms_level": blooms,
            "priority": "medium", # default: source has no priority; field IS used in app UI
        }
        # Preserve extra source fields
        if obj.get("source_ids"):
            record["source_ids"] = obj["source_ids"]
        if obj.get("rationale"):
            record["rationale"] = obj["rationale"]

        objectives.append(record)

    # Build associations from gold_mapping
    associations_by_canvas_id: list[dict] = []
    associations_by_text: list[dict] = []
    seen_canvas: set[tuple] = set()
    seen_text: set[tuple] = set()

    for entry in gold:
        qid = entry.get("question_id")
        if not qid:
            continue

        q = q_by_id.get(qid, {})
        question_text: str = entry.get("question_text") or q.get("question_text_markdown") or ""
        canvas_id = q.get("question_canvas_id")

        primary_code = _get_primary_code(entry)
        secondary_codes = _get_secondary_codes(entry)

        all_codes = []
        if primary_code:
            all_codes.append(primary_code)
        all_codes.extend(c for c in secondary_codes if c and c != primary_code)

        for code in all_codes:
            obj_text = obj_text_by_code.get(code, code)  # fall back to code if text missing
            if canvas_id is not None:
                key = (canvas_id, code)
                if key not in seen_canvas:
                    seen_canvas.add(key)
                    associations_by_canvas_id.append({
                        "canvas_id": canvas_id,
                        "question_preview": question_text[:80],
                        "objective_text": obj_text,
                    })
            elif question_text:
                key = (question_text[:120], code)
                if key not in seen_text:
                    seen_text.add(key)
                    associations_by_text.append({
                        "question_text": question_text,
                        "objective_text": obj_text,
                    })

    result = {
        "schema": "external",
        "objectives": objectives,
        "associations_by_canvas_id": associations_by_canvas_id,
        "associations_by_text": associations_by_text,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Objectives written → {out_path}")
    print(f"  {len(objectives)} objectives")
    print(f"  {len(associations_by_canvas_id)} associations by canvas_id")
    print(f"  {len(associations_by_text)} associations by text")


# ---------------------------------------------------------------------------
# 2. Questions
# ---------------------------------------------------------------------------

def convert_questions() -> None:
    src_path = ROOT / "resources/deep/chat_attachments_combined/questions_combined_from_chat_attachments.json"
    out_path = ROOT / "exports/questions_from_attachments.json"

    raw: dict = json.loads(src_path.read_text(encoding="utf-8"))

    # The source format is already compatible with questions_markdown_export.json.
    # We just normalize the top-level header fields to match the app export schema.
    result = {
        "exported_at": _now_utc(),
        "source": "external_chat_attachments",   # distinguishes from DB exports
        "format": raw.get("format", "questions_with_answers_markdown_v1"),
        # Extra field from source — retained as extra property per user request
        "source_files": raw.get("source_files", []),
        "question_count": raw.get("question_count", len(raw.get("questions", []))),
        "questions": raw.get("questions", []),
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Questions written → {out_path}")
    print(f"  {result['question_count']} questions")


# ---------------------------------------------------------------------------
# 3. Question → Objective Mappings
# ---------------------------------------------------------------------------

def convert_mappings() -> None:
    gold_path = ROOT / "resources/gold_mapping.json"
    q_path = ROOT / "resources/deep/chat_attachments_combined/questions_combined_from_chat_attachments.json"
    out_path = ROOT / "exports/question_objective_mappings_from_gold.json"

    gold: list[dict] = json.loads(gold_path.read_text(encoding="utf-8"))
    q_data: dict = json.loads(q_path.read_text(encoding="utf-8"))

    q_by_id: dict[str, dict] = {
        q["question_id"]: q for q in q_data["questions"]
    }

    results = []
    for entry in gold:
        qid = entry.get("question_id")
        if not qid:
            continue

        # Keep mappings aligned with the exported question set.
        # If a gold-mapping row points to a removed/missing question, skip it.
        q = q_by_id.get(qid)
        if not q:
            continue

        question_text: str = entry.get("question_text") or q.get("question_text_markdown") or ""
        rationale: str = entry.get("rationale") or ""

        primary_code = _get_primary_code(entry)
        secondary_codes = _get_secondary_codes(entry)

        matches = []
        if primary_code:
            matches.append({
                "objective_code": primary_code,
                "reasoning": rationale,
                "is_primary": True,    # extra field: distinguishes primary from secondary
            })
        for code in secondary_codes:
            if code:
                matches.append({
                    "objective_code": code,
                    "reasoning": "",   # secondary matches have no separate rationale
                    "is_primary": False,
                })

        result: dict = {
            "question_id": qid,
            "question_text_markdown": question_text,
            "matches": matches,
            # Extra fields from gold_mapping retained as additional properties
            "gold_id": entry.get("id"),
            "confidence": entry.get("confidence"),
            # Token counts are not available for manual mappings
            # (these fields are generated-only; the app does not read them)
            "prompt_tokens": None,
            "completion_tokens": None,
        }
        results.append(result)

    # Count questions with at least one match
    mapped = sum(1 for r in results if r["matches"])

    output = {
        "generated_at": _now_utc(),
        "source": "gold_mapping_external",   # extra: distinguishes from AI-generated file
        "questions_processed": len(results),
        "questions_with_matches": mapped,     # extra field
        # Token totals not applicable for manual mappings
        "total_prompt_tokens": None,
        "total_completion_tokens": None,
        "total_tokens": None,
        "results": results,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Mappings written → {out_path}")
    print(f"  {len(results)} total entries, {mapped} with at least one objective match")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Converting external files to app export format ===\n")
    convert_objectives()
    print()
    convert_questions()
    print()
    convert_mappings()
    print("\nDone.")
