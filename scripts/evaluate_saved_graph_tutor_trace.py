#!/usr/bin/env python3
"""Evaluate a saved graph-tutor conversation trace with a reasoning model."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
os.chdir(PROJECT_ROOT)

from dotenv import load_dotenv

load_dotenv()

from question_app.core.config import config
from question_app.services.tutor.azure_client import AzureAPIMClient

RESULTS_DIR = PROJECT_ROOT / "results"
TRACE_PATTERN = "saved_graph_tutor_conversation_*.json"


EVALUATION_SCHEMA: Dict[str, Any] = {
    "type": "json_schema",
    "name": "saved_graph_tutor_trace_evaluation",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "overall_score",
            "verdict",
            "teaching_sufficiency",
            "model_or_prompt_failures",
            "mcp_source_gaps",
            "tool_call_failures",
            "overdoing",
            "underdoing",
            "orchestrator_behavior",
            "tutor_behavior",
            "analyzer_behavior",
            "reasoning_quality",
            "prompt_or_agent_fixes",
            "per_turn_notes",
            "residual_risks",
        ],
        "properties": {
            "overall_score": {"type": "number"},
            "verdict": {"type": "string"},
            "teaching_sufficiency": {
                "type": "object",
                "additionalProperties": False,
                "required": ["is_enough_for_teaching", "score", "rationale"],
                "properties": {
                    "is_enough_for_teaching": {"type": "boolean"},
                    "score": {"type": "number"},
                    "rationale": {"type": "string"},
                },
            },
            "model_or_prompt_failures": {
                "type": "array",
                "items": {"$ref": "#/$defs/finding"},
            },
            "mcp_source_gaps": {
                "type": "array",
                "items": {"$ref": "#/$defs/finding"},
            },
            "tool_call_failures": {
                "type": "array",
                "items": {"$ref": "#/$defs/tool_failure"},
            },
            "overdoing": {"type": "array", "items": {"$ref": "#/$defs/finding"}},
            "underdoing": {"type": "array", "items": {"$ref": "#/$defs/finding"}},
            "orchestrator_behavior": {"$ref": "#/$defs/component_eval"},
            "tutor_behavior": {"$ref": "#/$defs/component_eval"},
            "analyzer_behavior": {"$ref": "#/$defs/component_eval"},
            "reasoning_quality": {"$ref": "#/$defs/component_eval"},
            "prompt_or_agent_fixes": {
                "type": "array",
                "items": {"$ref": "#/$defs/fix"},
            },
            "per_turn_notes": {
                "type": "array",
                "items": {"$ref": "#/$defs/turn_note"},
            },
            "residual_risks": {"type": "array", "items": {"type": "string"}},
        },
        "$defs": {
            "finding": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "severity",
                    "turns",
                    "summary",
                    "evidence",
                    "likely_cause",
                ],
                "properties": {
                    "severity": {
                        "type": "string",
                        "enum": ["critical", "high", "medium", "low"],
                    },
                    "turns": {"type": "array", "items": {"type": "integer"}},
                    "summary": {"type": "string"},
                    "evidence": {"type": "string"},
                    "likely_cause": {"type": "string"},
                },
            },
            "tool_failure": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "turns",
                    "tool_or_step",
                    "what_went_wrong",
                    "wrong_parameter",
                    "reasoning_failure",
                    "missing_call",
                    "evidence",
                ],
                "properties": {
                    "turns": {"type": "array", "items": {"type": "integer"}},
                    "tool_or_step": {"type": "string"},
                    "what_went_wrong": {"type": "string"},
                    "wrong_parameter": {"type": "boolean"},
                    "reasoning_failure": {"type": "boolean"},
                    "missing_call": {"type": "boolean"},
                    "evidence": {"type": "string"},
                },
            },
            "component_eval": {
                "type": "object",
                "additionalProperties": False,
                "required": ["score", "strengths", "weaknesses", "evidence"],
                "properties": {
                    "score": {"type": "number"},
                    "strengths": {"type": "array", "items": {"type": "string"}},
                    "weaknesses": {"type": "array", "items": {"type": "string"}},
                    "evidence": {"type": "string"},
                },
            },
            "fix": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "priority",
                    "target",
                    "change",
                    "why_this_matches_agent_best_practices",
                    "expected_effect",
                ],
                "properties": {
                    "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                    "target": {"type": "string"},
                    "change": {"type": "string"},
                    "why_this_matches_agent_best_practices": {"type": "string"},
                    "expected_effect": {"type": "string"},
                },
            },
            "turn_note": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "turn",
                    "orchestrator",
                    "analyzer",
                    "tutor",
                    "student_learning_value",
                ],
                "properties": {
                    "turn": {"type": "integer"},
                    "orchestrator": {"type": "string"},
                    "analyzer": {"type": "string"},
                    "tutor": {"type": "string"},
                    "student_learning_value": {"type": "string"},
                },
            },
        },
    },
    "strict": True,
}


def latest_trace_path(results_dir: Path = RESULTS_DIR) -> Path:
    candidates = sorted(results_dir.glob(TRACE_PATTERN), key=lambda path: path.stat().st_mtime)
    if not candidates:
        raise FileNotFoundError(f"No saved tutor traces found in {results_dir}")
    return candidates[-1]


def _truncate(value: Any, limit: int = 1800) -> Any:
    if isinstance(value, str):
        if len(value) <= limit:
            return value
        return value[:limit].rstrip() + "... [truncated]"
    if isinstance(value, list):
        return [_truncate(item, limit) for item in value]
    if isinstance(value, dict):
        return {key: _truncate(item, limit) for key, item in value.items()}
    return value


def _ws_turn_analysis(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    for event in reversed(events):
        if event.get("type") == "turn_analysis":
            analysis = event.get("analysis")
            return analysis if isinstance(analysis, dict) else {}
    return {}


def compact_trace(trace: Dict[str, Any]) -> Dict[str, Any]:
    turns = []
    for turn in trace.get("turns") or []:
        ws_events = turn.get("ws_events") or []
        trace_events = (turn.get("trace") or {}).get("events") or []
        turns.append(
            {
                "turn": turn.get("turn"),
                "student_message": _truncate(turn.get("student_message"), 900),
                "tutor_response": _truncate(turn.get("tutor_response"), 1400),
                "stage_before": turn.get("stage_before"),
                "stage_after": turn.get("stage_after"),
                "turn_analysis": _truncate(_ws_turn_analysis(ws_events), 2200),
                "graph_decision": _truncate(turn.get("graph_decision") or {}, 1800),
                "graph_state_after": _truncate(turn.get("graph_state_after") or {}, 1200),
                "lesson_state_after": _truncate(turn.get("lesson_state_after") or {}, 1200),
                "pacing_state_after": _truncate(turn.get("pacing_state_after") or {}, 1200),
                "trace_event_names": [
                    str(event.get("name") or event.get("type") or "")
                    for event in trace_events
                ],
                "timings": (turn.get("trace") or {}).get("timings") or {},
            }
        )
    return {
        "run_id": trace.get("run_id"),
        "objective_id": trace.get("objective_id"),
        "objective_text": trace.get("objective_text"),
        "models": trace.get("models") or {},
        "started_at": trace.get("started_at"),
        "ended_at": trace.get("ended_at"),
        "turns": turns,
    }


def build_evaluator_prompt(compacted_trace: Dict[str, Any]) -> str:
    return "\n\n".join(
        [
            "Evaluate this graph-guided tutor conversation trace in depth.",
            (
                "Separate shortcomings into two categories: "
                "model/prompt/agent behavior failures that can be improved by tuning, "
                "and information-source gaps caused by missing or weak MCP evidence."
            ),
            (
                "For tool-call or workflow failures, identify whether the problem was a "
                "wrong parameter, poor model reasoning, missing tool call, or tool/API misbehavior."
            ),
            (
                "Check whether the analyzer, orchestrator, or tutor is overdoing or "
                "underdoing anything. Evaluate whether the content is enough for real teaching."
            ),
            (
                "When recommending fixes, do not propose deterministic backend-driven "
                "instructional rules. Prefer prompt contracts, structured outputs, trace "
                "evaluators, orchestrator-worker boundaries, and evaluator-optimizer style "
                "loops consistent with the OpenAI/Anthropic agent guidance already selected "
                "for this project."
            ),
            "Return only JSON matching the provided schema.",
            "COMPACT TRACE:",
            json.dumps(compacted_trace, indent=2, ensure_ascii=False),
        ]
    )


def response_text(response: Dict[str, Any]) -> str:
    direct = str(response.get("output_text") or "").strip()
    if direct:
        return direct
    parts: List[str] = []
    for item in response.get("output") or []:
        if item.get("type") != "message":
            continue
        for content in item.get("content") or []:
            text = str(content.get("text") or "").strip()
            if text:
                parts.append(text)
    return "\n".join(parts).strip()


def parse_json_response(text: str) -> Dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.startswith("json"):
            stripped = stripped[4:].strip()
    return json.loads(stripped)


def render_markdown(report: Dict[str, Any], trace_path: Path, output_json: Path) -> str:
    lines = [
        "# Saved Graph Tutor Trace Evaluation",
        "",
        f"- Trace: `{trace_path}`",
        f"- JSON report: `{output_json}`",
        f"- Overall score: `{report.get('overall_score')}`",
        f"- Verdict: {report.get('verdict', '')}",
        "",
        "## Teaching Sufficiency",
        "",
        report.get("teaching_sufficiency", {}).get("rationale", ""),
        "",
        "## Model Or Prompt Failures",
    ]
    for finding in report.get("model_or_prompt_failures") or []:
        lines.append(
            f"- `{finding.get('severity')}` turns {finding.get('turns')}: "
            f"{finding.get('summary')} Evidence: {finding.get('evidence')}"
        )
    lines.extend(["", "## MCP Source Gaps"])
    for finding in report.get("mcp_source_gaps") or []:
        lines.append(
            f"- `{finding.get('severity')}` turns {finding.get('turns')}: "
            f"{finding.get('summary')} Evidence: {finding.get('evidence')}"
        )
    lines.extend(["", "## Tool Call Failures"])
    for failure in report.get("tool_call_failures") or []:
        lines.append(
            f"- turns {failure.get('turns')} `{failure.get('tool_or_step')}`: "
            f"{failure.get('what_went_wrong')}"
        )
    lines.extend(["", "## Recommended Prompt Or Agent Fixes"])
    for fix in report.get("prompt_or_agent_fixes") or []:
        lines.append(
            f"- `{fix.get('priority')}` {fix.get('target')}: {fix.get('change')} "
            f"Expected effect: {fix.get('expected_effect')}"
        )
    lines.extend(["", "## Per-Turn Notes"])
    for note in report.get("per_turn_notes") or []:
        lines.append(
            f"- Turn {note.get('turn')}: orchestrator={note.get('orchestrator')} "
            f"analyzer={note.get('analyzer')} tutor={note.get('tutor')} "
            f"learning={note.get('student_learning_value')}"
        )
    lines.append("")
    return "\n".join(lines)


def build_responses_client(model: str) -> AzureAPIMClient:
    return AzureAPIMClient(
        endpoint=config.OPENAI_RESPONSES_ENDPOINT,
        deployment=model,
        api_key=config.AZURE_OPENAI_SUBSCRIPTION_KEY,
        api_version=config.OPENAI_RESPONSES_API_VERSION,
        content_filter_policy=config.AZURE_OPENAI_CONTENT_FILTER_POLICY,
    )


async def evaluate_trace(trace_path: Path, *, model: str) -> Dict[str, Any]:
    trace = json.loads(trace_path.read_text())
    compacted = compact_trace(trace)
    prompt = build_evaluator_prompt(compacted)
    response = await build_responses_client(model).responses_create(
        instructions=(
            "You are a rigorous evaluator for an agentic tutoring system. "
            "Be specific, evidence-driven, and separate model behavior failures "
            "from missing source-information gaps."
        ),
        input=[
            {
                "role": "user",
                "content": [{"type": "input_text", "text": prompt}],
            }
        ],
        text={"format": EVALUATION_SCHEMA},
        reasoning_effort="medium",
        max_output_tokens=3000,
    )
    report = parse_json_response(response_text(response))
    report["trace_file"] = str(trace_path)
    report["evaluated_at"] = datetime.now().isoformat(timespec="seconds")
    report["evaluator_model"] = model
    return report


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace", type=Path, default=None)
    parser.add_argument("--model", default=config.OPENAI_RESPONSES_MODEL)
    parser.add_argument("--output-dir", type=Path, default=RESULTS_DIR)
    args = parser.parse_args()

    trace_path = args.trace or latest_trace_path(args.output_dir)
    report = await evaluate_trace(trace_path, model=args.model)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = args.output_dir / f"saved_graph_tutor_trace_evaluation_{timestamp}.json"
    output_md = args.output_dir / f"saved_graph_tutor_trace_evaluation_{timestamp}.md"
    output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    output_md.write_text(render_markdown(report, trace_path, output_json))
    print(f"Wrote {output_json}")
    print(f"Wrote {output_md}")


if __name__ == "__main__":
    asyncio.run(main())
