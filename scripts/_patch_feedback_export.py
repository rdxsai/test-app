#!/usr/bin/env python3
"""Patch feedback_markdown in questions_markdown_export.json with raw values where they differ."""
import json

RAW = "exports/questions_raw_export.json"
MARKDOWN = "exports/questions_markdown_export.json"

with open(RAW) as f:
    raw_data = json.load(f)
with open(MARKDOWN) as f:
    md_data = json.load(f)

raw_by_id = {q["question_id"]: q for q in raw_data["questions"]}

questions_updated = 0
feedbacks_updated = 0

for q in md_data["questions"]:
    qid = q["question_id"]
    raw_q = raw_by_id.get(qid)
    if not raw_q:
        continue
    raw_answers = {a["answer_id"]: a for a in raw_q.get("answers", [])}
    for a in q.get("answers", []):
        aid = a["answer_id"]
        raw_a = raw_answers.get(aid)
        if not raw_a:
            continue
        md_fb = a.get("feedback_markdown") or ""
        raw_fb = raw_a.get("feedback_markdown") or ""
        if md_fb != raw_fb:
            a["feedback_markdown"] = raw_fb
            feedbacks_updated += 1
            if feedbacks_updated == 1 or questions_updated == 0:
                questions_updated_set = set()
            questions_updated_set.add(qid)

questions_updated = len(questions_updated_set) if feedbacks_updated > 0 else 0

with open(MARKDOWN, "w") as f:
    json.dump(md_data, f, indent=2, ensure_ascii=False)

print(f"Done. Questions updated: {questions_updated}, feedback fields updated: {feedbacks_updated}")
