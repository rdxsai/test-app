#!/usr/bin/env python3
"""Run the teaching-graph build pipeline for one objective and trace every worker.

Usage:
    poetry run python scripts/run_teaching_graph_trace.py "OBJECTIVE TEXT"

If no objective is provided, defaults to an ARIA objective not previously tested
in the current graph pipeline.
"""

from __future__ import annotations

import asyncio
import copy
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
os.chdir(PROJECT_ROOT)

from dotenv import load_dotenv

load_dotenv()

from question_app.core.config import config
from question_app.services.tutor.azure_client import AzureAPIMClient
from question_app.services.tutor.hybrid_system import HybridCrewAISocraticSystem
from question_app.services.tutor.interfaces import VectorStoreInterface
from question_app.services.wcag_mcp_client import WCAGMCPClient


DEFAULT_OBJECTIVE = (
    "Analyze how ARIA roles, states, and properties can communicate dynamic "
    "interface changes in complex web applications."
)


class NullVectorStore(VectorStoreInterface):
    async def search(self, query: str, n_results: int = 3):
        return []


def pretty_json(obj: Any, *, indent: int = 2) -> str:
    return json.dumps(obj, indent=indent, default=repr, ensure_ascii=False)


def shorten_text(text: str, *, max_chars: int = 1200) -> str:
    text = (text or "").strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def section_header(title: str, level: int = 2) -> str:
    return f"\n{'#' * level} {title}\n"


def safe_payload(obj: Any) -> Any:
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if isinstance(obj, dict):
        return {key: safe_payload(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [safe_payload(value) for value in obj]
    return obj


async def main() -> None:
    objective_text = sys.argv[1].strip() if len(sys.argv) > 1 else DEFAULT_OBJECTIVE

    azure_config = {
        "api_key": config.AZURE_OPENAI_SUBSCRIPTION_KEY,
        "endpoint": config.AZURE_OPENAI_ENDPOINT,
        "deployment_name": config.AZURE_OPENAI_DEPLOYMENT_ID,
        "tutor_deployment_name": config.AZURE_OPENAI_TUTOR_DEPLOYMENT_ID,
        "reasoning_deployment_name": config.AZURE_OPENAI_REASONING_DEPLOYMENT_ID,
        "api_version": config.AZURE_OPENAI_API_VERSION,
    }

    vector_service = NullVectorStore()
    azure_client = AzureAPIMClient(
        endpoint=azure_config["endpoint"],
        deployment=(
            azure_config.get("reasoning_deployment_name")
            or azure_config["deployment_name"]
        ),
        api_key=azure_config["api_key"],
        api_version=azure_config.get("api_version", "2024-02-15-preview"),
        content_filter_policy=azure_config.get("content_filter_policy"),
    )
    wcag_mcp = (
        WCAGMCPClient(command=config.WCAG_MCP_COMMAND, azure_client=azure_client)
        if config.WCAG_MCP_ENABLED
        else None
    )

    system = HybridCrewAISocraticSystem(
        azure_config=azure_config,
        vector_store_service=vector_service,
        db_manager=object(),
        wcag_mcp_client=wcag_mcp,
        student_mcp_client=None,
    )

    trace: Dict[str, Any] = {
        "objective_text": objective_text,
        "run_started_at": datetime.now().isoformat(),
        "workers": [],
        "mcp_calls": [],
        "final_artifact": {},
        "timings": {},
    }
    worker_stack: List[str] = []

    original_chat = system.reasoning_client.chat
    original_execute = wcag_mcp.execute_planned_tool_calls if wcag_mcp else None

    def current_worker_entry() -> Dict[str, Any] | None:
        if not worker_stack:
            return None
        active = worker_stack[-1]
        for entry in reversed(trace["workers"]):
            if entry["worker"] == active and entry.get("status") == "running":
                return entry
        return None

    def traced_chat(
        messages,
        temperature=0.7,
        max_tokens=1000,
        reasoning_effort=None,
        response_format=None,
    ):
        started = time.perf_counter()
        result = original_chat(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            reasoning_effort=reasoning_effort,
            response_format=response_format,
        )
        elapsed = round(time.perf_counter() - started, 2)
        entry = current_worker_entry()
        llm_call = {
            "message_count": len(messages or []),
            "temperature": temperature,
            "max_tokens": max_tokens,
            "reasoning_effort": reasoning_effort,
            "response_format": response_format,
            "messages": copy.deepcopy(messages),
            "response_preview": shorten_text(result, max_chars=2500),
            "response_chars": len(result or ""),
            "elapsed_seconds": elapsed,
        }
        if entry is not None:
            entry.setdefault("llm_calls", []).append(llm_call)
        else:
            trace.setdefault("unscoped_llm_calls", []).append(llm_call)
        return result

    async def traced_execute(planned_calls):
        started = time.perf_counter()
        results = await original_execute(planned_calls)
        trace["mcp_calls"].append(
            {
                "worker": worker_stack[-1] if worker_stack else "",
                "planned_calls": copy.deepcopy(planned_calls),
                "results": copy.deepcopy(results),
                "elapsed_seconds": round(time.perf_counter() - started, 2),
            }
        )
        entry = current_worker_entry()
        if entry is not None:
            entry.setdefault("mcp_batches", []).append(
                {
                    "planned_calls": copy.deepcopy(planned_calls),
                    "results": copy.deepcopy(results),
                }
            )
        return results

    system.reasoning_client.chat = traced_chat
    if wcag_mcp and original_execute:
        wcag_mcp.execute_planned_tool_calls = traced_execute

    def wrap_async_method(label: str, obj: Any, method_name: str):
        original = getattr(obj, method_name)

        async def wrapped(*args, **kwargs):
            entry = {
                "worker": label,
                "method": method_name,
                "input": {
                    "args": safe_payload(list(args)),
                    "kwargs": safe_payload(kwargs),
                },
                "status": "running",
                "started_at": datetime.now().isoformat(),
            }
            trace["workers"].append(entry)
            worker_stack.append(label)
            started = time.perf_counter()
            try:
                result = await original(*args, **kwargs)
                entry["output"] = safe_payload(result)
                entry["status"] = "completed"
                return result
            except Exception as exc:
                entry["status"] = "failed"
                entry["error"] = repr(exc)
                raise
            finally:
                entry["elapsed_seconds"] = round(time.perf_counter() - started, 2)
                worker_stack.pop()

        setattr(obj, method_name, wrapped)

    wrap_async_method(
        "teaching_graph_planner",
        system._teaching_graph_planner_worker,
        "generate",
    )
    wrap_async_method(
        "node_evidence_retriever",
        system._graph_node_evidence_worker,
        "build_node_evidence",
    )
    wrap_async_method(
        "node_content_synthesizer",
        system._graph_node_content_worker,
        "build_node_content",
    )
    wrap_async_method(
        "edge_integration_synthesizer",
        system._graph_edge_integration_worker,
        "build_edge_integration_content",
    )
    wrap_async_method(
        "grounding_validator",
        system._graph_validator_worker,
        "validate",
    )

    results_dir = PROJECT_ROOT / "results"
    results_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = "teaching_graph_trace"
    json_path = results_dir / f"{slug}_{timestamp}.json"
    md_path = results_dir / f"{slug}_{timestamp}.md"
    run_error: str | None = None
    try:
        started = time.perf_counter()
        artifact = await system._build_teaching_graph_content(objective_text)
        trace["timings"]["total_seconds"] = round(time.perf_counter() - started, 2)
        trace["final_artifact"] = safe_payload(artifact)
    except Exception as exc:
        trace["timings"]["total_seconds"] = round(
            time.perf_counter() - started, 2
        )
        trace["error"] = repr(exc)
        run_error = repr(exc)
    finally:
        trace["run_finished_at"] = datetime.now().isoformat()

        json_path.write_text(pretty_json(trace) + "\n", encoding="utf-8")

        lines: List[str] = []
        lines.append(f"# Teaching Graph Trace")
        lines.append(f"\n**Objective**: {objective_text}")
        lines.append(f"**Run Started**: {trace['run_started_at']}")
        lines.append(f"**Run Finished**: {trace['run_finished_at']}")
        lines.append(f"**Total Time**: {trace['timings']['total_seconds']}s")
        if run_error:
            lines.append(f"**Run Error**: `{run_error}`")

        lines.append(section_header("Worker Summary"))
        lines.append("| Worker | Status | Time | LLM Calls | MCP Batches |")
        lines.append("|---|---:|---:|---:|---:|")
        for worker in trace["workers"]:
            lines.append(
                f"| {worker['worker']} | {worker['status']} | {worker.get('elapsed_seconds', 0)}s | "
                f"{len(worker.get('llm_calls', []))} | {len(worker.get('mcp_batches', []))} |"
            )

        for worker in trace["workers"]:
            lines.append(section_header(worker["worker"], level=2))
            lines.append(f"**Status**: {worker['status']}")
            lines.append(f"**Elapsed**: {worker.get('elapsed_seconds', 0)}s")

            lines.append(section_header("Input", level=3))
            lines.append("```json")
            lines.append(pretty_json(worker["input"]))
            lines.append("```")

            for idx, llm_call in enumerate(worker.get("llm_calls", []), start=1):
                lines.append(section_header(f"LLM Call {idx}", level=3))
                lines.append(
                    f"- max_tokens: `{llm_call['max_tokens']}`\n"
                    f"- reasoning_effort: `{llm_call['reasoning_effort']}`\n"
                    f"- response_format: `{llm_call['response_format']}`\n"
                    f"- elapsed: `{llm_call['elapsed_seconds']}s`"
                )
                lines.append("```json")
                lines.append(pretty_json(llm_call["messages"]))
                lines.append("```")
                lines.append("**Response Preview**")
                lines.append("```")
                lines.append(llm_call["response_preview"])
                lines.append("```")

            for idx, batch in enumerate(worker.get("mcp_batches", []), start=1):
                lines.append(section_header(f"MCP Batch {idx}", level=3))
                lines.append("**Planned Calls**")
                lines.append("```json")
                lines.append(pretty_json(batch["planned_calls"]))
                lines.append("```")
                lines.append("**Results**")
                lines.append("```json")
                lines.append(pretty_json(batch["results"]))
                lines.append("```")

            if worker.get("output"):
                lines.append(section_header("Output", level=3))
                lines.append("```json")
                lines.append(pretty_json(worker["output"]))
                lines.append("```")

            if worker.get("error"):
                lines.append(section_header("Error", level=3))
                lines.append("```")
                lines.append(worker["error"])
                lines.append("```")

        lines.append(section_header("Final Artifact"))
        lines.append("```json")
        lines.append(pretty_json(trace["final_artifact"]))
        lines.append("```")

        md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        print(f"Trace JSON: {json_path}")
        print(f"Trace Markdown: {md_path}")

    if run_error:
        raise RuntimeError(run_error)


if __name__ == "__main__":
    asyncio.run(main())
