"""
map_questions_to_objectives.py

Loops through (a subset of) questions and uses the Azure OpenAI API to identify
which learning objectives each question could be assessing.

Usage:
    poetry run python scripts/map_questions_to_objectives.py

Env vars required (read from .env):
    AZURE_OPENAI_ENDPOINT
    AZURE_OPENAI_DEPLOYMENT_ID
    AZURE_OPENAI_API_VERSION
    AZURE_OPENAI_SUBSCRIPTION_KEY

Output:
    exports/question_objective_mappings.json
"""

import json
import os
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

QUESTIONS_FILE = Path("exports/questions_markdown_export.json")
OBJECTIVES_FILE = Path("new_objectives.json")
OUTPUT_FILE = Path("exports/question_objective_mappings.json")

# How many questions to process (keep small for testing)
MAX_QUESTIONS = 5

# ---------------------------------------------------------------------------
# Load env
# ---------------------------------------------------------------------------

load_dotenv()

ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "").rstrip("/")
DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT_ID", "")
API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2023-12-01-preview")
SUBSCRIPTION_KEY = os.getenv("AZURE_OPENAI_SUBSCRIPTION_KEY", "")

if not all([ENDPOINT, DEPLOYMENT, SUBSCRIPTION_KEY]):
    sys.exit(
        "Missing Azure OpenAI config. "
        "Set AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT_ID, "
        "and AZURE_OPENAI_SUBSCRIPTION_KEY in .env"
    )

API_URL = f"{ENDPOINT}/deployments/{DEPLOYMENT}/chat/completions?api-version={API_VERSION}"
HEADERS = {
    "Content-Type": "application/json",
    "Ocp-Apim-Subscription-Key": SUBSCRIPTION_KEY,
}

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

questions_data = json.loads(QUESTIONS_FILE.read_text())
objectives: dict[str, str] = json.loads(OBJECTIVES_FILE.read_text())

questions = questions_data["questions"][:MAX_QUESTIONS]
print(f"Loaded {len(questions)} question(s) and {len(objectives)} objective(s).\n")

# ---------------------------------------------------------------------------
# Build objectives block (reused in every prompt)
# ---------------------------------------------------------------------------

objectives_block = "\n".join(
    f"  {code}: {desc}" for code, desc in objectives.items()
)

SYSTEM_PROMPT = textwrap.dedent("""\
    You are an instructional design expert specializing in web accessibility education.
    Your job is to map quiz questions to learning objectives.

    Given a question (with its answer choices and the correct answer marked), determine
    which of the provided learning objectives the question could be used to assess.
    A question may map to zero, one, or multiple objectives.

    Respond ONLY with a valid JSON object in this exact shape:
    {
      "matches": [
        {
          "objective_code": "<code>",
          "reasoning": "<one-sentence explanation>"
        }
      ]
    }

    If no objectives match, return {"matches": []}.
    Do not include any text outside the JSON object.
""")


def build_user_prompt(question: dict) -> str:
    q_text = question["question_text_markdown"].strip()

    answers_lines = []
    for a in question["answers"]:
        marker = "[CORRECT]" if a["is_correct"] else "[INCORRECT]"
        answers_lines.append(f"  {marker} {a['answer_text_markdown'].strip()}")
    answers_block = "\n".join(answers_lines)

    return textwrap.dedent(f"""\
        ## Question

        {q_text}

        ## Answer Choices

        {answers_block}

        ## Learning Objectives

        {objectives_block}

        Which of the above objectives does this question assess?
    """)


# ---------------------------------------------------------------------------
# Call API
# ---------------------------------------------------------------------------

def call_api(user_prompt: str) -> tuple[str, int, int]:
    """Returns (response_text, prompt_tokens, completion_tokens)."""
    payload = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0,
        "max_tokens": 400,
        "response_format": {"type": "json_object"},
    }

    resp = requests.post(API_URL, headers=HEADERS, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    content = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)

    return content, prompt_tokens, completion_tokens


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

total_prompt_tokens = 0
total_completion_tokens = 0

results = []

for i, question in enumerate(questions, start=1):
    q_id = question["question_id"]
    q_text_short = question["question_text_markdown"].strip()[:80].replace("\n", " ")
    print(f"{'=' * 70}")
    print(f"Question {i}: {q_text_short}...")
    print(f"  (id: {q_id})")

    user_prompt = build_user_prompt(question)

    try:
        raw_response, prompt_tok, completion_tok = call_api(user_prompt)
    except requests.HTTPError as e:
        print(f"  ERROR: {e}")
        results.append({
            "question_id": q_id,
            "question_text_markdown": question["question_text_markdown"],
            "matches": [],
            "error": str(e),
            "prompt_tokens": 0,
            "completion_tokens": 0,
        })
        continue

    total_prompt_tokens += prompt_tok
    total_completion_tokens += completion_tok

    try:
        result = json.loads(raw_response)
    except json.JSONDecodeError:
        print(f"  WARNING: Could not parse API response as JSON:")
        print(f"  {raw_response}")
        results.append({
            "question_id": q_id,
            "question_text_markdown": question["question_text_markdown"],
            "matches": [],
            "error": f"JSON parse failed: {raw_response}",
            "prompt_tokens": prompt_tok,
            "completion_tokens": completion_tok,
        })
        continue

    matches = result.get("matches", [])
    results.append({
        "question_id": q_id,
        "question_text_markdown": question["question_text_markdown"],
        "matches": matches,
        "prompt_tokens": prompt_tok,
        "completion_tokens": completion_tok,
    })

    if matches:
        print(f"  Matched objectives ({len(matches)}):")
        for m in matches:
            code = m.get("objective_code", "?")
            reason = m.get("reasoning", "")
            print(f"    [{code}] {reason}")
    else:
        print("  No matching objectives found.")

    print(f"  Tokens — prompt: {prompt_tok}, completion: {completion_tok}")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

print(f"\n{'=' * 70}")
print("TOTALS")
print(f"  Questions processed : {len(questions)}")
print(f"  Prompt tokens       : {total_prompt_tokens}")
print(f"  Completion tokens   : {total_completion_tokens}")
print(f"  Total tokens        : {total_prompt_tokens + total_completion_tokens}")

# ---------------------------------------------------------------------------
# Write results to file
# ---------------------------------------------------------------------------

output = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "questions_processed": len(results),
    "total_prompt_tokens": total_prompt_tokens,
    "total_completion_tokens": total_completion_tokens,
    "total_tokens": total_prompt_tokens + total_completion_tokens,
    "results": results,
}

OUTPUT_FILE.write_text(json.dumps(output, indent=2, ensure_ascii=False))
print(f"\nResults written to {OUTPUT_FILE}")
