#!/usr/bin/env python3
"""Run the full teaching content pipeline for a single objective and dump
every intermediate artifact to ``results/result.md``.

Usage:
    poetry run python scripts/run_pipeline.py [OBJECTIVE_ID]

If OBJECTIVE_ID is omitted, defaults to I.A.2 (WCAG structure & POUR).
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Project bootstrap
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
os.chdir(PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv()

from question_app.core.config import config
from question_app.services.tutor.azure_client import AzureAPIMClient
from question_app.api.pg_vector_store import VectorStoreService
from question_app.services.wcag_mcp_client import WCAGMCPClient
from question_app.services.tutor.hybrid_system import HybridCrewAISocraticSystem
from question_app.services.tutor.session_cache import SessionContentCache

RESULTS_DIR = PROJECT_ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def pretty_json(obj, indent=2):
    """JSON-safe pretty print (handles non-serializable objects)."""
    def _default(o):
        return repr(o)
    return json.dumps(obj, indent=indent, default=_default, ensure_ascii=False)


def section_header(title, level=2):
    return f"\n{'#' * level} {title}\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    objective_id = sys.argv[1] if len(sys.argv) > 1 else "I.A.2"

    # --- Init system (same as chat.py) ---
    azure_config = {
        "api_key": config.AZURE_OPENAI_SUBSCRIPTION_KEY,
        "endpoint": config.AZURE_OPENAI_ENDPOINT,
        "deployment_name": config.AZURE_OPENAI_DEPLOYMENT_ID,
        "tutor_deployment_name": config.AZURE_OPENAI_TUTOR_DEPLOYMENT_ID,
        "reasoning_deployment_name": config.AZURE_OPENAI_REASONING_DEPLOYMENT_ID,
        "api_version": config.AZURE_OPENAI_API_VERSION,
    }

    vector_service = VectorStoreService()

    azure_client = AzureAPIMClient(
        endpoint=azure_config["endpoint"],
        deployment=(
            azure_config.get("reasoning_deployment_name")
            or azure_config["deployment_name"]
        ),
        api_key=azure_config["api_key"],
        api_version=azure_config.get("api_version", "2024-02-15-preview"),
    )

    wcag_mcp = WCAGMCPClient(
        command=config.WCAG_MCP_COMMAND,
        azure_client=azure_client,
    ) if config.WCAG_MCP_ENABLED else None

    system = HybridCrewAISocraticSystem(
        azure_config=azure_config,
        vector_store_service=vector_service,
        wcag_mcp_client=wcag_mcp,
        student_mcp_client=None,  # not needed for pipeline
    )

    # --- Fetch objective ---
    objective = system._fetch_objective_by_id(objective_id)
    if not objective:
        print(f"Objective '{objective_id}' not found in DB.")
        sys.exit(1)
    objective_text = objective["text"]
    print(f"Objective: {objective_id} — {objective_text}\n")

    # --- Collectors ---
    progress_log = []
    timings = {}

    async def ws_send(data: dict):
        data["_ts"] = datetime.now().isoformat()
        progress_log.append(data)
        detail = data.get("detail", "")
        stage = data.get("stage", data.get("type", "?"))
        print(f"  [{stage}] {detail}")

    # === PIPELINE STEP 1: Teaching Plan ===
    print("Step 1: Generating teaching plan...")
    t0 = time.perf_counter()
    teaching_plan = await system._generate_teaching_plan(objective_text)
    timings["teaching_plan"] = round(time.perf_counter() - t0, 2)
    print(f"  Done ({timings['teaching_plan']}s, {len(str(teaching_plan))} chars)\n")

    # === PIPELINE STEP 2: Agentic Retrieval ===
    print("Step 2: Running agentic retrieval...")
    t0 = time.perf_counter()
    raw_results = await system._run_agentic_retrieval(
        objective_text=objective_text,
        teaching_plan=teaching_plan,
        ws_send=ws_send,
    )
    timings["agentic_retrieval"] = round(time.perf_counter() - t0, 2)
    hits = [r for r in raw_results if r.get("status") == "HIT"]
    misses = [r for r in raw_results if r.get("status") != "HIT"]
    print(f"  Done ({timings['agentic_retrieval']}s, {len(hits)} hits, {len(misses)} non-hits)\n")

    # === PIPELINE STEP 3: Build Retrieval Bundle ===
    print("Step 3: Building retrieval bundle...")
    t0 = time.perf_counter()
    retrieval_bundle = await system._build_retrieval_bundle(
        raw_results,
        objective_text=objective_text,
        teaching_plan=teaching_plan,
    )
    timings["build_bundle"] = round(time.perf_counter() - t0, 2)
    print(f"  Done ({timings['build_bundle']}s, {len(retrieval_bundle.get('raw_hits', []))} raw hits in bundle)\n")

    # === PIPELINE STEP 4: Render Evidence Pack ===
    print("Step 4: Rendering evidence pack...")
    t0 = time.perf_counter()
    teaching_content = system._render_retrieval_bundle(retrieval_bundle)
    timings["render"] = round(time.perf_counter() - t0, 2)
    print(f"  Done ({timings['render']}s, {len(teaching_content)} chars)\n")

    # === Build Lesson State ===
    print("Step 5: Building lesson state from teaching plan...")
    cache = SessionContentCache()
    cache.store("trace", objective_id, objective_text, [], "", teaching_content,
                retrieval_bundle=retrieval_bundle)
    cache.store_teaching_plan("trace", teaching_plan)
    lesson_state = cache.get_lesson_state("trace")

    # === Export slim payload (what would be persisted) ===
    slim_payload = cache.export_session("trace")

    # === Timings summary ===
    timings["total"] = round(sum(timings.values()), 2)
    print(f"Total pipeline time: {timings['total']}s")

    # ------------------------------------------------------------------
    # Write result.md
    # ------------------------------------------------------------------
    print("\nWriting results/result.md ...")

    lines = []
    lines.append(f"# Pipeline Trace: {objective_id}")
    lines.append(f"\n**Objective**: {objective_text}")
    lines.append(f"**Run at**: {datetime.now().isoformat()}")
    lines.append(f"**Total time**: {timings['total']}s")

    # --- Timings ---
    lines.append(section_header("Timings"))
    lines.append("| Step | Time |")
    lines.append("|------|------|")
    for step, t in timings.items():
        lines.append(f"| {step} | {t}s |")

    # --- Progress Log ---
    lines.append(section_header("Progress Log (WebSocket Events)"))
    lines.append("```json")
    lines.append(pretty_json(progress_log))
    lines.append("```")

    # --- 1. Teaching Plan ---
    lines.append(section_header("1. Teaching Plan"))
    lines.append(f"**Type**: `{type(teaching_plan).__name__}` | **Size**: {len(str(teaching_plan))} chars")
    lines.append("")
    if isinstance(teaching_plan, str):
        lines.append("```")
        lines.append(teaching_plan)
        lines.append("```")
    else:
        lines.append("```json")
        lines.append(pretty_json(teaching_plan))
        lines.append("```")

    # --- 2. Raw Retrieval Results ---
    lines.append(section_header("2. Raw Retrieval Results"))
    lines.append(f"**Total calls**: {len(raw_results)} | **Hits**: {len(hits)} | **Non-hits**: {len(misses)}")
    lines.append(f"**Total hit chars**: {sum(r.get('chars', 0) for r in hits)}")
    lines.append("")

    for i, result in enumerate(raw_results, 1):
        status = result.get("status", "?")
        tool = result.get("tool", "?")
        args = result.get("args", {})
        chars = result.get("chars", 0)
        rnd = result.get("round", "?")
        seq = result.get("sequence", "?")
        lines.append(f"### Result {i}: `{tool}` — {status}")
        lines.append(f"- **Round**: {rnd} | **Sequence**: {seq} | **Chars**: {chars}")
        lines.append(f"- **Args**: `{json.dumps(args)}`")
        preview = (result.get("result") or "")[:500]
        if preview:
            lines.append(f"\n<details><summary>Preview (first 500 chars)</summary>\n")
            lines.append(f"```\n{preview}\n```\n</details>\n")

    # --- 3. Retrieval Bundle ---
    lines.append(section_header("3. Retrieval Bundle (Structured)"))

    # Coverage
    coverage = retrieval_bundle.get("coverage", {})
    lines.append(section_header("Coverage Metadata", 3))
    lines.append("```json")
    lines.append(pretty_json(coverage))
    lines.append("```")

    # Sections
    sections = retrieval_bundle.get("sections", {})
    for section_name, items in sections.items():
        lines.append(section_header(f"Section: {section_name} ({len(items)} items)", 3))
        if not items:
            lines.append("*(empty)*\n")
            continue
        for j, item in enumerate(items, 1):
            lines.append(f"**Item {j}: {item.get('title', 'Untitled')}**")
            lines.append(f"- Source: `{item.get('source_tool', '?')}({json.dumps(item.get('source_args', {}))})`")
            content = item.get("content", "")
            lines.append(f"\n<details><summary>Content ({len(content)} chars)</summary>\n")
            lines.append(f"```\n{content}\n```\n</details>\n")

    # Raw hits summary
    raw_hits = retrieval_bundle.get("raw_hits", [])
    lines.append(section_header("Raw Hits Summary", 3))
    lines.append(f"**Count**: {len(raw_hits)}")
    lines.append("")
    lines.append("| # | Tool | Args | Round | Chars |")
    lines.append("|---|------|------|-------|-------|")
    for k, rh in enumerate(raw_hits, 1):
        lines.append(f"| {k} | `{rh.get('tool','')}` | `{json.dumps(rh.get('args',{}))}` | {rh.get('round','')} | {rh.get('chars',0)} |")

    # --- 4. Rendered Evidence Pack ---
    lines.append(section_header("4. Rendered Evidence Pack (teaching_content)"))
    lines.append(f"**Size**: {len(teaching_content)} chars")
    lines.append("")
    lines.append("This is the exact string injected into the tutor's system prompt as the VALIDATED EVIDENCE PACK.")
    lines.append("")
    lines.append("````markdown")
    lines.append(teaching_content)
    lines.append("````")

    # --- 5. Lesson State ---
    lines.append(section_header("5. Lesson State"))
    lines.append("Built from the teaching plan. This tracks concept-by-concept progress.")
    lines.append("")
    lines.append("```json")
    lines.append(pretty_json(lesson_state))
    lines.append("```")

    # --- 6. Slim Persisted Payload ---
    lines.append(section_header("6. Slim Persisted Payload (what goes to DB)"))
    lines.append("This is what `export_session()` produces for JSONB persistence.")
    lines.append(f"**Size**: {len(json.dumps(slim_payload, default=repr))} bytes")
    lines.append("")
    # Show keys and sizes, not full content (too large)
    lines.append("| Field | Size |")
    lines.append("|-------|------|")
    for key, val in (slim_payload or {}).items():
        size = len(json.dumps(val, default=repr)) if val else 0
        lines.append(f"| `{key}` | {size} bytes |")

    slim_bundle = (slim_payload or {}).get("retrieval_bundle")
    if slim_bundle:
        lines.append(section_header("Slim Bundle (no raw_hits, no round/sequence)", 3))
        lines.append("```json")
        # Show structure but truncate content
        slim_preview = {
            "version": slim_bundle.get("version"),
            "coverage": slim_bundle.get("coverage"),
            "sections": {},
        }
        for sname, sitems in slim_bundle.get("sections", {}).items():
            slim_preview["sections"][sname] = [
                {
                    "title": it.get("title", ""),
                    "content_length": len(it.get("content", "")),
                    "source_tool": it.get("source_tool", ""),
                }
                for it in sitems
            ]
        lines.append(pretty_json(slim_preview))
        lines.append("```")

    # --- Write ---
    result_path = RESULTS_DIR / "result.md"
    result_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Done! Written to {result_path} ({len(lines)} lines)")

    # Cleanup
    if wcag_mcp:
        await wcag_mcp.close()


if __name__ == "__main__":
    asyncio.run(main())
