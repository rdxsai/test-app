#!/usr/bin/env python3
"""Run the graph-grounded retrieval pipeline from a saved Markdown graph.

The script writes a timestamped trace directory under results/ containing:
- every Azure Responses API request/response
- every Azure synthesis/validation chat request/response
- every planned WCAG MCP tool call and result
- every intermediate graph artifact
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
os.chdir(PROJECT_ROOT)

from dotenv import load_dotenv

load_dotenv()

from question_app.core.config import config
from question_app.services.tutor.artifacts import (
    TeachingGraphArtifact,
    TeachingGraphContentArtifact,
)
from question_app.services.tutor.azure_client import (
    AzureAPIMClient,
    build_graph_responses_client,
)
from question_app.services.tutor.hybrid_system import (
    TEACHING_GRAPH_EDGE_SYNTHESIS_MAX_COMPLETION_TOKENS,
    TEACHING_GRAPH_EDGE_SYNTHESIS_REASONING_EFFORT,
    TEACHING_GRAPH_NODE_RETRIEVAL_MAX_COMPLETION_TOKENS,
    TEACHING_GRAPH_NODE_RETRIEVAL_MAX_TOOL_CALLS,
    TEACHING_GRAPH_NODE_RETRIEVAL_REASONING_EFFORT,
    TEACHING_GRAPH_NODE_SYNTHESIS_MAX_COMPLETION_TOKENS,
    TEACHING_GRAPH_NODE_SYNTHESIS_REASONING_EFFORT,
    TEACHING_GRAPH_VALIDATION_MAX_COMPLETION_TOKENS,
    TEACHING_GRAPH_VALIDATION_REASONING_EFFORT,
    TeachingGraphGenerationError,
)
from question_app.services.tutor.workers.graph import (
    EdgeIntegrationSynthesizerWorker,
    GraphGroundingProjector,
    GroundingValidatorWorker,
    NodeContentSynthesizerWorker,
    NodeEvidenceRetrieverWorker,
)
from question_app.services.wcag_mcp_client import WCAGMCPClient


def _json_default(value: Any) -> str:
    return repr(value)


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    return slug.strip("_") or "event"


class TraceLogger:
    def __init__(self, trace_dir: Path) -> None:
        self.trace_dir = trace_dir
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._counter = 0
        self.index_path = self.trace_dir / "trace_index.jsonl"

    def write(self, kind: str, name: str, payload: Any, suffix: str = "json") -> Path:
        with self._lock:
            self._counter += 1
            sequence = self._counter
        filename = f"{sequence:04d}_{_safe_slug(kind)}_{_safe_slug(name)}.{suffix}"
        path = self.trace_dir / filename
        if suffix == "json":
            path.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False, default=_json_default)
                + "\n",
                encoding="utf-8",
            )
        else:
            path.write_text(str(payload), encoding="utf-8")
        entry = {
            "sequence": sequence,
            "kind": kind,
            "name": name,
            "path": str(path.relative_to(PROJECT_ROOT)),
            "timestamp": datetime.now().isoformat(),
        }
        with self._lock:
            with self.index_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return path


class TracedAzureResponsesClient:
    def __init__(self, inner: AzureAPIMClient, trace: TraceLogger) -> None:
        self.inner = inner
        self.trace = trace
        self.deployment = inner.deployment

    async def responses_create(self, **kwargs: Any) -> Dict[str, Any]:
        label = "responses_create"
        request_payload = {
            "deployment": self.inner.deployment,
            "endpoint": self.inner.endpoint,
            "kwargs": kwargs,
        }
        self.trace.write("llm_request", label, request_payload)
        started = time.perf_counter()
        try:
            response = await self.inner.responses_create(**kwargs)
        except Exception as exc:
            response_body = ""
            response_status = None
            response = getattr(exc, "response", None)
            if response is not None:
                response_status = getattr(response, "status_code", None)
                try:
                    response_body = response.text
                except Exception:
                    response_body = ""
            self.trace.write(
                "llm_error",
                label,
                {
                    "elapsed_seconds": round(time.perf_counter() - started, 3),
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "response_status": response_status,
                    "response_body": response_body,
                },
            )
            raise
        self.trace.write(
            "llm_response",
            label,
            {
                "elapsed_seconds": round(time.perf_counter() - started, 3),
                "response": response,
            },
        )
        return response


class TracedAzureChatClient:
    def __init__(self, inner: AzureAPIMClient, trace: TraceLogger) -> None:
        self.inner = inner
        self.trace = trace
        self.deployment = inner.deployment

    def chat(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        reasoning_effort: Optional[str] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        system_preview = ""
        if messages and isinstance(messages[0], dict):
            system_preview = str(messages[0].get("content") or "")[:80]
        label = f"azure_chat_{self.deployment}_{system_preview}"
        self.trace.write(
            "llm_request",
            label,
            {
                "deployment": self.deployment,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "reasoning_effort": reasoning_effort,
                "response_format": response_format,
                "messages": messages,
            },
        )
        started = time.perf_counter()
        response = self.inner.chat(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            reasoning_effort=reasoning_effort,
            response_format=response_format,
        )
        self.trace.write(
            "llm_response",
            label,
            {
                "elapsed_seconds": round(time.perf_counter() - started, 3),
                "response_text": response,
            },
        )
        return response


class TracedWCAGMCPClient:
    def __init__(self, inner: WCAGMCPClient, trace: TraceLogger) -> None:
        self.inner = inner
        self.trace = trace

    async def execute_planned_tool_calls(
        self, planned_calls: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        self.trace.write("mcp_request", "execute_planned_tool_calls", planned_calls)
        started = time.perf_counter()
        results = await self.inner.execute_planned_tool_calls(planned_calls)
        self.trace.write(
            "mcp_response",
            "execute_planned_tool_calls",
            {
                "elapsed_seconds": round(time.perf_counter() - started, 3),
                "results": results,
            },
        )
        return results

    async def close(self) -> None:
        await self.inner.close()


def _section(text: str, heading: str, next_heading_level: str = "##") -> str:
    pattern = rf"^## {re.escape(heading)}\s*$"
    match = re.search(pattern, text, flags=re.MULTILINE)
    if not match:
        return ""
    start = match.end()
    next_match = re.search(
        rf"^{re.escape(next_heading_level)}\s+", text[start:], flags=re.MULTILINE
    )
    end = start + next_match.start() if next_match else len(text)
    return text[start:end].strip()


def _first_nonempty_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _parse_nodes(nodes_text: str) -> List[Dict[str, str]]:
    nodes: List[Dict[str, str]] = []
    matches = list(
        re.finditer(r"^### `([^`]+)`: (.+)$", nodes_text, flags=re.MULTILINE)
    )
    for index, match in enumerate(matches):
        start = match.end()
        end = (
            matches[index + 1].start() if index + 1 < len(matches) else len(nodes_text)
        )
        body = nodes_text[start:end]
        kind_match = re.search(r"\*\*Kind:\*\*\s*([A-Za-z_]+)", body)
        claim_match = re.search(r"\*\*Teachable claim:\*\*\s*(.+)", body)
        node = {
            "id": match.group(1).strip(),
            "label": match.group(2).strip(),
            "kind": kind_match.group(1).strip() if kind_match else "core_concept",
        }
        if claim_match:
            node["teachable_claim"] = claim_match.group(1).strip()
        nodes.append(node)
    return nodes


def _parse_edges(edges_text: str) -> List[Dict[str, str]]:
    edges: List[Dict[str, str]] = []
    matches = list(
        re.finditer(
            r"^### `([^`]+)`\s*->\s*`([^`]+)`\s*$", edges_text, flags=re.MULTILINE
        )
    )
    for index, match in enumerate(matches):
        start = match.end()
        end = (
            matches[index + 1].start() if index + 1 < len(matches) else len(edges_text)
        )
        body = edges_text[start:end]
        type_match = re.search(r"\*\*Type:\*\*\s*([A-Za-z_]+)", body)
        bridge_match = re.search(r"\*\*Bridge claim:\*\*\s*(.+)", body)
        edges.append(
            {
                "from": match.group(1).strip(),
                "to": match.group(2).strip(),
                "type": type_match.group(1).strip() if type_match else "supports",
                "bridge_claim": bridge_match.group(1).strip()
                if bridge_match
                else f"{match.group(1)} connects to {match.group(2)}.",
            }
        )
    return edges


def _parse_primary_route(route_text: str) -> List[str]:
    route: List[str] = []
    for match in re.finditer(r"`([^`]+)`\s*:", route_text):
        route.append(match.group(1).strip())
    return route


def parse_markdown_graph(path: Path) -> TeachingGraphArtifact:
    text = path.read_text(encoding="utf-8")
    objective_text = _first_nonempty_line(_section(text, "Objective"))
    graph_type = _first_nonempty_line(_section(text, "Graph Type"))
    primary_route = _parse_primary_route(_section(text, "Primary Route"))
    nodes = _parse_nodes(_section(text, "Nodes"))
    edges = _parse_edges(_section(text, "Edges"))
    if not primary_route and nodes:
        primary_route = [node["id"] for node in nodes]
    integration_candidates = [
        node["id"] for node in nodes if node.get("kind") == "integration"
    ]
    integration_node = (
        integration_candidates[-1] if integration_candidates else primary_route[-1]
    )
    return TeachingGraphArtifact.from_dict(
        {
            "objective_text": objective_text,
            "graph_type": graph_type,
            "entry_nodes": [primary_route[0]],
            "integration_node": integration_node,
            "primary_route": primary_route,
            "nodes": nodes,
            "edges": edges,
        }
    )


async def run_demo(graph_path: Path, trace_dir: Path) -> Path:
    trace = TraceLogger(trace_dir)
    graph = parse_markdown_graph(graph_path)
    trace.write("input", "parsed_graph", graph.to_dict())

    azure_config = {
        "endpoint": config.AZURE_OPENAI_ENDPOINT,
        "deployment": (
            config.AZURE_OPENAI_REASONING_DEPLOYMENT_ID
            or config.AZURE_OPENAI_TUTOR_DEPLOYMENT_ID
            or config.AZURE_OPENAI_DEPLOYMENT_ID
        ),
        "api_key": config.AZURE_OPENAI_SUBSCRIPTION_KEY,
        "api_version": config.AZURE_OPENAI_API_VERSION,
        "content_filter_policy": config.AZURE_OPENAI_CONTENT_FILTER_POLICY,
    }
    azure_responses_client = build_graph_responses_client(
        azure_config={
            "endpoint": config.OPENAI_RESPONSES_ENDPOINT,
            "api_key": azure_config["api_key"],
            "api_version": config.OPENAI_RESPONSES_API_VERSION,
            "content_filter_policy": azure_config["content_filter_policy"],
        },
        responses_deployment=config.OPENAI_RESPONSES_MODEL,
        enabled=config.OPENAI_RESPONSES_ENABLED,
    )
    if azure_responses_client is None:
        raise RuntimeError("Responses API is disabled; graph retrieval cannot run.")
    responses_client = TracedAzureResponsesClient(azure_responses_client, trace)

    azure_client = TracedAzureChatClient(
        AzureAPIMClient(
            endpoint=azure_config["endpoint"],
            deployment=azure_config["deployment"],
            api_key=azure_config["api_key"],
            api_version=azure_config["api_version"],
            content_filter_policy=azure_config["content_filter_policy"],
        ),
        trace,
    )
    wcag_mcp = TracedWCAGMCPClient(
        WCAGMCPClient(command=config.WCAG_MCP_COMMAND, azure_client=azure_client),
        trace,
    )

    node_evidence_worker = NodeEvidenceRetrieverWorker(
        reasoning_client=responses_client,
        wcag_mcp=wcag_mcp,
        max_completion_tokens=TEACHING_GRAPH_NODE_RETRIEVAL_MAX_COMPLETION_TOKENS,
        reasoning_effort=TEACHING_GRAPH_NODE_RETRIEVAL_REASONING_EFFORT,
        max_tool_calls_per_node=TEACHING_GRAPH_NODE_RETRIEVAL_MAX_TOOL_CALLS,
        retrieval_error_cls=TeachingGraphGenerationError,
    )
    node_content_worker = NodeContentSynthesizerWorker(
        reasoning_client=azure_client,
        max_completion_tokens=TEACHING_GRAPH_NODE_SYNTHESIS_MAX_COMPLETION_TOKENS,
        reasoning_effort=TEACHING_GRAPH_NODE_SYNTHESIS_REASONING_EFFORT,
        synthesis_error_cls=TeachingGraphGenerationError,
    )
    edge_worker = EdgeIntegrationSynthesizerWorker(
        reasoning_client=azure_client,
        max_completion_tokens=TEACHING_GRAPH_EDGE_SYNTHESIS_MAX_COMPLETION_TOKENS,
        reasoning_effort=TEACHING_GRAPH_EDGE_SYNTHESIS_REASONING_EFFORT,
        synthesis_error_cls=TeachingGraphGenerationError,
    )
    validator = GroundingValidatorWorker(
        reasoning_client=azure_client,
        max_completion_tokens=TEACHING_GRAPH_VALIDATION_MAX_COMPLETION_TOKENS,
        reasoning_effort=TEACHING_GRAPH_VALIDATION_REASONING_EFFORT,
        validation_error_cls=TeachingGraphGenerationError,
    )

    try:
        node_evidence = await node_evidence_worker.build_graph_evidence(
            objective_text=graph.objective_text,
            graph=graph,
        )
        trace.write("artifact", "node_evidence", node_evidence.to_dict())

        node_content = await node_content_worker.build_node_content(
            objective_text=graph.objective_text,
            graph=graph,
            node_evidence=node_evidence,
        )
        trace.write("artifact", "node_content", node_content.to_dict())

        edge_integration = await edge_worker.build_edge_integration_content(
            objective_text=graph.objective_text,
            graph=graph,
            node_evidence=node_evidence,
            node_content=node_content,
        )
        trace.write("artifact", "edge_integration", edge_integration.to_dict())

        validation = await validator.validate(
            objective_text=graph.objective_text,
            graph=graph,
            node_evidence=node_evidence,
            node_content=node_content,
            edge_integration=edge_integration,
        )
        trace.write("artifact", "llm_validation", validation.to_dict())

        evidence_cards = GraphGroundingProjector.build_evidence_cards(
            objective_text=graph.objective_text,
            node_evidence=node_evidence,
        )
        trace.write("artifact", "evidence_cards", evidence_cards.to_dict())

        claim_ledger = GraphGroundingProjector.build_claim_ledger(
            objective_text=graph.objective_text,
            node_evidence=node_evidence,
            node_content=node_content,
            edge_integration=edge_integration,
            evidence_cards=evidence_cards,
        )
        trace.write("artifact", "claim_ledger", claim_ledger.to_dict())

        validation = GraphGroundingProjector.deterministic_validate(
            validation=validation,
            claim_ledger=claim_ledger,
            evidence_cards=evidence_cards,
        )
        trace.write("artifact", "deterministic_validation", validation.to_dict())
        if validation.overall_status != "pass":
            raise RuntimeError(
                "Graph-grounded content failed validation: "
                f"{validation.overall_status}"
            )

        tutor_content = GraphGroundingProjector.build_tutor_facing_content(
            objective_text=graph.objective_text,
            graph=graph,
            node_content=node_content,
            edge_integration=edge_integration,
            evidence_cards=evidence_cards,
            claim_ledger=claim_ledger,
            validation=validation,
        )
        trace.write("artifact", "tutor_facing_content", tutor_content.to_dict())
        trace.write(
            "artifact",
            "tutor_facing_content_rendered",
            GraphGroundingProjector.render_tutor_content(tutor_content) + "\n",
            suffix="md",
        )

        final_artifact = TeachingGraphContentArtifact(
            objective_text=graph.objective_text,
            graph=graph,
            node_evidence=node_evidence,
            node_content=node_content,
            edge_integration=edge_integration,
            validation=validation,
            evidence_cards=evidence_cards,
            claim_ledger=claim_ledger,
            tutor_facing_content=tutor_content,
        )
        trace.write("artifact", "final_graph_content", final_artifact.to_dict())
    except Exception as exc:
        trace.write(
            "error",
            "demo_failed",
            {
                "error_type": type(exc).__name__,
                "error": str(exc),
            },
        )
        raise
    finally:
        await wcag_mcp.close()

    return trace_dir


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--graph",
        default="teaching_graph_aria_rules.md",
        help="Path to the saved Markdown teaching graph.",
    )
    parser.add_argument(
        "--trace-dir",
        default="",
        help="Optional output directory. Defaults to results/graph_retrieval_demo_<timestamp>.",
    )
    args = parser.parse_args()

    graph_path = Path(args.graph).resolve()
    if args.trace_dir:
        trace_dir = Path(args.trace_dir).resolve()
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        trace_dir = PROJECT_ROOT / "results" / f"graph_retrieval_demo_{timestamp}"

    output_dir = asyncio.run(run_demo(graph_path, trace_dir))
    print(f"TRACE_DIR={output_dir}")


if __name__ == "__main__":
    main()
