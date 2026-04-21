from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Optional

from ..artifacts import (
    EdgeIntegrationArtifact,
    GroundingValidationArtifact,
    NodeEvidenceArtifact,
    NodeContentArtifact,
    TeachingGraphArtifact,
)
from ..prompts import (
    EDGE_INTEGRATION_SYNTHESIS_PROMPT,
    GROUNDING_VALIDATOR_PROMPT,
    NODE_CONTENT_SYNTHESIS_PROMPT,
    NODE_EVIDENCE_RETRIEVAL_PROMPT,
    TEACHING_GRAPH_PLANNER_PROMPT,
)
from .content import RetrievalWorker


class TeachingGraphPlannerWorker:
    def __init__(
        self,
        *,
        reasoning_client,
        max_completion_tokens: int,
        reasoning_effort: str,
        graph_error_cls: type[Exception],
    ) -> None:
        self.reasoning_client = reasoning_client
        self.max_completion_tokens = max_completion_tokens
        self.reasoning_effort = reasoning_effort
        self.graph_error_cls = graph_error_cls

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        stripped = (text or "").strip()
        if not stripped.startswith("```"):
            return stripped
        lines = stripped.splitlines()
        if len(lines) >= 2 and lines[-1].strip() == "```":
            return "\n".join(lines[1:-1]).strip()
        return "\n".join(lines[1:]).strip()

    async def generate(
        self,
        objective_text: str,
        *,
        learner_level: Optional[str] = None,
        prerequisite_assumptions: Optional[str] = None,
    ) -> TeachingGraphArtifact:
        user_lines = [f"OBJECTIVE:\n{objective_text.strip()}"]
        if learner_level:
            user_lines.append(f"LEARNER LEVEL:\n{learner_level.strip()}")
        if prerequisite_assumptions:
            user_lines.append(
                f"PREREQUISITE ASSUMPTIONS:\n{prerequisite_assumptions.strip()}"
            )

        response = await asyncio.to_thread(
            self.reasoning_client.chat,
            [
                {"role": "system", "content": TEACHING_GRAPH_PLANNER_PROMPT},
                {"role": "user", "content": "\n\n".join(user_lines)},
            ],
            0.1,
            self.max_completion_tokens,
            self.reasoning_effort,
            {"type": "json_object"},
        )

        try:
            payload = json.loads(self._strip_code_fences(response))
            return TeachingGraphArtifact.from_dict(payload)
        except Exception as exc:
            preview = self._strip_code_fences(response).replace("\n", " ").strip()
            if len(preview) > 200:
                preview = preview[:200] + "..."
            detail = preview or "empty response"
            raise self.graph_error_cls(
                "Teaching graph generation failed: "
                f"{detail}. Guided graph build cannot continue without a valid graph."
            ) from exc


class NodeEvidenceRetrieverWorker:
    AVAILABLE_TOOLS_TEXT = RetrievalWorker.AVAILABLE_TOOLS_TEXT

    def __init__(
        self,
        *,
        reasoning_client,
        wcag_mcp,
        max_completion_tokens: int,
        reasoning_effort: str,
        max_tool_calls_per_node: int,
        retrieval_error_cls: type[Exception],
    ) -> None:
        self.reasoning_client = reasoning_client
        self.wcag_mcp = wcag_mcp
        self.max_completion_tokens = max_completion_tokens
        self.reasoning_effort = reasoning_effort
        self.max_tool_calls_per_node = max_tool_calls_per_node
        self.retrieval_error_cls = retrieval_error_cls

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        return TeachingGraphPlannerWorker._strip_code_fences(text)

    @staticmethod
    def _normalize_planned_calls(
        node_id: str, payload: Dict[str, Any], max_tool_calls: int
    ) -> List[Dict[str, Any]]:
        planned_calls: List[Dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for item in payload.get("planned_calls") or []:
            tool = str(item.get("tool") or "").strip()
            if not tool:
                continue
            args = dict(item.get("args") or {})
            dedupe_key = (tool, json.dumps(args, sort_keys=True))
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            planned_calls.append(
                {
                    "tool": tool,
                    "args": args,
                    "kind": str(item.get("kind") or "explanatory_support").strip(),
                    "grounding_note": str(item.get("grounding_note") or "").strip()
                    or str(item.get("reason") or "").strip()
                    or f"Grounding for node {node_id}",
                    "category": "graph_node_grounding",
                    "source": "teaching_graph_node_retrieval",
                }
            )
            if len(planned_calls) >= max_tool_calls:
                break
        return planned_calls

    @staticmethod
    def _coverage_summary_from_items(items: List[Dict[str, Any]]) -> Dict[str, bool]:
        kinds = {item.get("kind", "") for item in items}
        return {
            "has_definition_support": "definition" in kinds,
            "has_normative_anchor": "normative_anchor" in kinds,
            "has_explanatory_support": "explanatory_support" in kinds
            or "structural_support" in kinds,
            "has_contrast_support": "contrast_support" in kinds,
            "has_risk_support": "risk_support" in kinds,
        }

    @staticmethod
    def _grounding_strength(items: List[Dict[str, Any]]) -> str:
        if not items:
            return "thin"
        kinds = {item.get("kind", "") for item in items}
        if (
            "normative_anchor" in kinds
            and "explanatory_support" in kinds
            and len(kinds) >= 3
        ):
            return "strong"
        if len(items) >= 2:
            return "adequate"
        return "thin"

    @staticmethod
    def _result_title(result: Dict[str, Any]) -> str:
        args = result.get("args") or {}
        for key in ("ref_id", "term", "level", "group_by", "query"):
            value = args.get(key)
            if value:
                return f"{result.get('tool', '')}: {value}"
        return str(result.get("tool") or "retrieved_item")

    async def _plan_node_calls(
        self,
        *,
        objective_text: str,
        graph: TeachingGraphArtifact,
        node: Any,
    ) -> List[Dict[str, Any]]:
        if not self.wcag_mcp:
            raise self.retrieval_error_cls(
                "Teaching graph node retrieval failed: WCAG MCP client unavailable."
            )

        response = await asyncio.to_thread(
            self.reasoning_client.chat,
            [
                {"role": "system", "content": NODE_EVIDENCE_RETRIEVAL_PROMPT},
                {
                    "role": "user",
                    "content": "\n\n".join(
                        [
                            f"OBJECTIVE:\n{objective_text}",
                            f"GRAPH:\n{json.dumps(graph.to_dict(), indent=2)}",
                            f"TARGET NODE:\n{json.dumps(node.to_dict(), indent=2)}",
                            f"{self.AVAILABLE_TOOLS_TEXT}",
                        ]
                    ),
                },
            ],
            0.1,
            self.max_completion_tokens,
            self.reasoning_effort,
            {"type": "json_object"},
        )
        try:
            payload = json.loads(self._strip_code_fences(response))
        except Exception as exc:
            raise self.retrieval_error_cls(
                f"Teaching graph node retrieval planning failed for {node.id}: invalid JSON response."
            ) from exc

        planned_calls = self._normalize_planned_calls(
            node.id, payload, self.max_tool_calls_per_node
        )
        if not planned_calls:
            raise self.retrieval_error_cls(
                f"Teaching graph node retrieval planning failed for {node.id}: no usable MCP calls were produced."
            )
        return planned_calls

    async def build_node_evidence(
        self,
        *,
        objective_text: str,
        graph: TeachingGraphArtifact,
    ) -> NodeEvidenceArtifact:
        if not self.wcag_mcp:
            raise self.retrieval_error_cls(
                "Teaching graph node retrieval failed: WCAG MCP client unavailable."
            )

        node_records: List[Dict[str, Any]] = []
        for node in graph.nodes:
            planned_calls = await self._plan_node_calls(
                objective_text=objective_text,
                graph=graph,
                node=node,
            )
            results = await self.wcag_mcp.execute_planned_tool_calls(planned_calls)
            retrieved_items: List[Dict[str, Any]] = []
            for index, (planned_call, result) in enumerate(zip(planned_calls, results), start=1):
                content = str(result.get("result") or "").strip()
                if result.get("status") != "HIT" or not content:
                    continue
                retrieved_items.append(
                    {
                        "item_id": f"{node.id}-item-{index}",
                        "tool": planned_call["tool"],
                        "args": dict(planned_call.get("args") or {}),
                        "kind": planned_call.get("kind") or "explanatory_support",
                        "title": self._result_title(result),
                        "content": content,
                        "grounding_note": planned_call.get("grounding_note")
                        or f"Grounding for node {node.id}",
                    }
                )

            if not retrieved_items:
                raise self.retrieval_error_cls(
                    f"Teaching graph node retrieval failed for {node.id}: no grounded evidence was retrieved."
                )

            node_records.append(
                {
                    "node_id": node.id,
                    "grounding_strength": self._grounding_strength(retrieved_items),
                    "coverage_summary": self._coverage_summary_from_items(retrieved_items),
                    "source_tools_used": [
                        {"tool": planned_call["tool"], "args": dict(planned_call.get("args") or {})}
                        for planned_call in planned_calls
                    ],
                    "retrieved_items": retrieved_items,
                }
            )

        return NodeEvidenceArtifact.from_dict(
            {
                "objective_text": objective_text,
                "graph_summary": {
                    "graph_type": graph.graph_type,
                    "node_ids": [node.id for node in graph.nodes],
                },
                "node_evidence": node_records,
            }
        )


class NodeContentSynthesizerWorker:
    def __init__(
        self,
        *,
        reasoning_client,
        max_completion_tokens: int,
        reasoning_effort: str,
        synthesis_error_cls: type[Exception],
    ) -> None:
        self.reasoning_client = reasoning_client
        self.max_completion_tokens = max_completion_tokens
        self.reasoning_effort = reasoning_effort
        self.synthesis_error_cls = synthesis_error_cls

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        return TeachingGraphPlannerWorker._strip_code_fences(text)

    async def build_node_content(
        self,
        *,
        objective_text: str,
        graph: TeachingGraphArtifact,
        node_evidence: NodeEvidenceArtifact,
    ) -> NodeContentArtifact:
        evidence_by_node = {item.node_id: item for item in node_evidence.node_evidence}
        node_payloads: List[Dict[str, Any]] = []

        for node in graph.nodes:
            evidence = evidence_by_node.get(node.id)
            if evidence is None:
                raise self.synthesis_error_cls(
                    f"Teaching graph node synthesis failed for {node.id}: missing node grounding."
                )

            response = await asyncio.to_thread(
                self.reasoning_client.chat,
                [
                    {"role": "system", "content": NODE_CONTENT_SYNTHESIS_PROMPT},
                    {
                        "role": "user",
                        "content": "\n\n".join(
                            [
                                f"OBJECTIVE:\n{objective_text}",
                                f"NODE:\n{json.dumps(node.to_dict(), indent=2)}",
                                f"NODE EVIDENCE:\n{json.dumps(evidence.to_dict(), indent=2)}",
                            ]
                        ),
                    },
                ],
                0.1,
                self.max_completion_tokens,
                self.reasoning_effort,
                {"type": "json_object"},
            )

            try:
                payload = json.loads(self._strip_code_fences(response))
                payload.setdefault("id", node.id)
                payload.setdefault("label", node.label)
                payload.setdefault("kind", node.kind)
                record = NodeContentArtifact.from_dict(
                    {
                        "objective_text": objective_text,
                        "nodes": [payload],
                    }
                ).nodes[0]
                if record.id != node.id:
                    raise ValueError("synthesized node id mismatch")
                node_payloads.append(record.to_dict())
            except Exception as exc:
                preview = self._strip_code_fences(response).replace("\n", " ").strip()
                if len(preview) > 200:
                    preview = preview[:200] + "..."
                raise self.synthesis_error_cls(
                    f"Teaching graph node synthesis failed for {node.id}: {preview or 'empty response'}"
                ) from exc

        return NodeContentArtifact.from_dict(
            {
                "objective_text": objective_text,
                "nodes": node_payloads,
            }
        )


class EdgeIntegrationSynthesizerWorker:
    def __init__(
        self,
        *,
        reasoning_client,
        max_completion_tokens: int,
        reasoning_effort: str,
        synthesis_error_cls: type[Exception],
    ) -> None:
        self.reasoning_client = reasoning_client
        self.max_completion_tokens = max_completion_tokens
        self.reasoning_effort = reasoning_effort
        self.synthesis_error_cls = synthesis_error_cls

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        return TeachingGraphPlannerWorker._strip_code_fences(text)

    async def build_edge_integration_content(
        self,
        *,
        objective_text: str,
        graph: TeachingGraphArtifact,
        node_content: NodeContentArtifact,
    ) -> EdgeIntegrationArtifact:
        response = await asyncio.to_thread(
            self.reasoning_client.chat,
            [
                {"role": "system", "content": EDGE_INTEGRATION_SYNTHESIS_PROMPT},
                {
                    "role": "user",
                    "content": "\n\n".join(
                        [
                            f"OBJECTIVE:\n{objective_text}",
                            f"GRAPH:\n{json.dumps(graph.to_dict(), indent=2)}",
                            f"NODE CONTENT:\n{json.dumps(node_content.to_dict(), indent=2)}",
                        ]
                    ),
                },
            ],
            0.1,
            self.max_completion_tokens,
            self.reasoning_effort,
            {"type": "json_object"},
        )
        try:
            payload = json.loads(self._strip_code_fences(response))
            payload["objective_text"] = objective_text
            return EdgeIntegrationArtifact.from_dict(payload)
        except Exception as exc:
            preview = self._strip_code_fences(response).replace("\n", " ").strip()
            if len(preview) > 240:
                preview = preview[:240] + "..."
            raise self.synthesis_error_cls(
                "Teaching graph edge/integration synthesis failed: "
                f"{preview or 'empty response'}"
            ) from exc


class GroundingValidatorWorker:
    def __init__(
        self,
        *,
        reasoning_client,
        max_completion_tokens: int,
        reasoning_effort: str,
        validation_error_cls: type[Exception],
    ) -> None:
        self.reasoning_client = reasoning_client
        self.max_completion_tokens = max_completion_tokens
        self.reasoning_effort = reasoning_effort
        self.validation_error_cls = validation_error_cls

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        return TeachingGraphPlannerWorker._strip_code_fences(text)

    async def validate(
        self,
        *,
        objective_text: str,
        graph: TeachingGraphArtifact,
        node_evidence: NodeEvidenceArtifact,
        node_content: NodeContentArtifact,
        edge_integration: EdgeIntegrationArtifact,
    ) -> GroundingValidationArtifact:
        response = await asyncio.to_thread(
            self.reasoning_client.chat,
            [
                {"role": "system", "content": GROUNDING_VALIDATOR_PROMPT},
                {
                    "role": "user",
                    "content": "\n\n".join(
                        [
                            f"OBJECTIVE:\n{objective_text}",
                            f"GRAPH:\n{json.dumps(graph.to_dict(), indent=2)}",
                            f"NODE EVIDENCE:\n{json.dumps(node_evidence.to_dict(), indent=2)}",
                            f"NODE CONTENT:\n{json.dumps(node_content.to_dict(), indent=2)}",
                            f"EDGE INTEGRATION:\n{json.dumps(edge_integration.to_dict(), indent=2)}",
                        ]
                    ),
                },
            ],
            0.0,
            self.max_completion_tokens,
            self.reasoning_effort,
            {"type": "json_object"},
        )
        try:
            payload = json.loads(self._strip_code_fences(response))
            payload["objective_text"] = objective_text
            return GroundingValidationArtifact.from_dict(payload)
        except Exception as exc:
            preview = self._strip_code_fences(response).replace("\n", " ").strip()
            if len(preview) > 240:
                preview = preview[:240] + "..."
            raise self.validation_error_cls(
                f"Teaching graph validation failed: {preview or 'empty response'}"
            ) from exc
