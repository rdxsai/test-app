"""Compare raw vs markdown question exports and report text differences."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

raw_data = json.loads((ROOT / "exports/questions_raw_export.json").read_text())
md_data  = json.loads((ROOT / "exports/questions_markdown_export.json").read_text())

raw_qs = {q["question_id"]: q for q in raw_data["questions"]}
md_qs  = {q["question_id"]: q for q in md_data["questions"]}

diffs = []
for qid, rq in raw_qs.items():
    mq = md_qs.get(qid)
    if not mq:
        continue

    q_diff = rq["question_text_markdown"] != mq["question_text_markdown"]

    answer_diffs = []
    raw_answers = {a["answer_id"]: a for a in rq["answers"]}
    md_answers  = {a["answer_id"]: a for a in mq["answers"]}
    for aid, ra in raw_answers.items():
        ma = md_answers.get(aid)
        if ma and ra["answer_text_markdown"] != ma["answer_text_markdown"]:
            answer_diffs.append({
                "answer_id": aid,
                "raw": ra["answer_text_markdown"],
                "markdown": ma["answer_text_markdown"],
            })

    if q_diff or answer_diffs:
        entry = {"question_id": qid}
        if q_diff:
            entry["question_text_raw"] = rq["question_text_markdown"]
            entry["question_text_md"]  = mq["question_text_markdown"]
        if answer_diffs:
            entry["answer_diffs"] = answer_diffs
        diffs.append(entry)

print(f"Questions with differences: {len(diffs)}\n")
print(json.dumps(diffs, indent=2, ensure_ascii=False))
