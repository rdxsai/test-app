from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Optional

from ..artifacts import (
    ClaimLedgerArtifact,
    EdgeIntegrationArtifact,
    EvidenceCardSet,
    GroundingValidationArtifact,
    NodeEvidenceArtifact,
    NodeContentArtifact,
    TeachingGraphArtifact,
    TutorFacingTeachingContent,
)
from ..prompts import (
    EDGE_INTEGRATION_SYNTHESIS_PROMPT,
    GROUNDING_VALIDATOR_PROMPT,
    NODE_CONTENT_SYNTHESIS_PROMPT,
    NODE_EVIDENCE_FINALIZATION_PROMPT,
    NODE_EVIDENCE_RETRIEVAL_TOOLCALL_PROMPT,
    TEACHING_GRAPH_PLANNER_PROMPT,
)


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
        self.max_rounds = 4
        self.retrieval_error_cls = retrieval_error_cls

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        return TeachingGraphPlannerWorker._strip_code_fences(text)

    @staticmethod
    def _tool_kind_from_name(tool_name: str) -> str:
        if tool_name in {"get_glossary_term", "search_glossary", "list_glossary_terms"}:
            return "definition"
        if tool_name in {"get_success_criteria_detail", "get_full_criterion_context"}:
            return "normative_anchor"
        if tool_name in {"get_criterion", "get_guideline", "list_guidelines", "list_principles"}:
            return "explanatory_support"
        if tool_name in {"get_technique", "get_techniques_for_criterion", "search_techniques"}:
            return "implementation_support"
        if tool_name in {"search_wcag", "list_success_criteria", "get_criteria_by_level", "count_criteria"}:
            return "structural_support"
        return "explanatory_support"

    @staticmethod
    def _result_title(result: Dict[str, Any]) -> str:
        args = result.get("args") or {}
        for key in ("ref_id", "term", "level", "group_by", "query"):
            value = args.get(key)
            if value:
                return f"{result.get('tool', '')}: {value}"
        return str(result.get("tool") or "retrieved_item")

    @staticmethod
    def _response_text(response: Dict[str, Any]) -> str:
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

    @staticmethod
    def _extract_function_calls(response: Dict[str, Any]) -> List[Dict[str, Any]]:
        calls: List[Dict[str, Any]] = []
        for item in response.get("output") or []:
            if item.get("type") != "function_call":
                continue
            try:
                args = json.loads(item.get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            calls.append(
                {
                    "id": item.get("id"),
                    "call_id": item.get("call_id"),
                    "name": item.get("name"),
                    "arguments": args,
                }
            )
        return calls

    @staticmethod
    def _responses_tool_definitions() -> List[Dict[str, Any]]:
        from ...wcag_mcp_client import GUIDED_WCAG_TOOL_DEFINITIONS

        def _strict_parameters(parameters: Dict[str, Any]) -> Dict[str, Any]:
            normalized = json.loads(json.dumps(parameters or {}))
            normalized.setdefault("type", "object")
            properties = normalized.setdefault("properties", {})
            originally_required = set(normalized.get("required") or [])
            for name, schema in properties.items():
                if name in originally_required:
                    continue
                if "type" in schema and isinstance(schema["type"], str):
                    schema["type"] = [schema["type"], "null"]
                if "enum" in schema and None not in schema["enum"]:
                    schema["enum"] = list(schema["enum"]) + [None]
            normalized["required"] = list(properties.keys())
            normalized["additionalProperties"] = False
            return normalized

        converted: List[Dict[str, Any]] = []
        for tool in GUIDED_WCAG_TOOL_DEFINITIONS:
            function = tool.get("function") or {}
            converted.append(
                {
                    "type": "function",
                    "name": function.get("name"),
                    "description": function.get("description", ""),
                    "parameters": _strict_parameters(function.get("parameters") or {}),
                    "strict": True,
                }
            )
        return converted

    @staticmethod
    def _node_evidence_text_format() -> Dict[str, Any]:
        return {
            "format": {
                "type": "json_schema",
                "name": "node_evidence_artifact",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "node_id": {"type": "string"},
                        "grounding_strength": {
                            "type": "string",
                            "enum": ["thin", "adequate", "strong"],
                        },
                        "coverage_summary": {
                            "type": "object",
                            "properties": {
                                "has_definition_support": {"type": "boolean"},
                                "has_normative_anchor": {"type": "boolean"},
                                "has_explanatory_support": {"type": "boolean"},
                                "has_contrast_support": {"type": "boolean"},
                                "has_risk_support": {"type": "boolean"},
                            },
                            "required": [
                                "has_definition_support",
                                "has_normative_anchor",
                                "has_explanatory_support",
                                "has_contrast_support",
                                "has_risk_support",
                            ],
                            "additionalProperties": False,
                        },
                        "retrieval_summary": {"type": "string"},
                        "source_tools_used": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "tool": {"type": "string"},
                                    "args": {"type": "object", "additionalProperties": True},
                                },
                                "required": ["tool", "args"],
                                "additionalProperties": False,
                            },
                        },
                        "retrieved_items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "item_id": {"type": "string"},
                                    "tool": {"type": "string"},
                                    "args": {"type": "object", "additionalProperties": True},
                                    "kind": {
                                        "type": "string",
                                        "enum": [
                                            "definition",
                                            "normative_anchor",
                                            "explanatory_support",
                                            "contrast_support",
                                            "risk_support",
                                            "structural_support",
                                            "implementation_support",
                                            "example_support",
                                            "failure_support",
                                        ],
                                    },
                                    "title": {"type": "string"},
                                    "content": {"type": "string"},
                                    "grounding_note": {"type": "string"},
                                },
                                "required": [
                                    "item_id",
                                    "tool",
                                    "args",
                                    "kind",
                                    "title",
                                    "content",
                                    "grounding_note",
                                ],
                                "additionalProperties": False,
                            },
                        },
                        "notes_on_gaps": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": [
                        "node_id",
                        "grounding_strength",
                        "coverage_summary",
                        "retrieval_summary",
                        "source_tools_used",
                        "retrieved_items",
                        "notes_on_gaps",
                    ],
                    "additionalProperties": False,
                },
            }
        }

    async def _retrieve_evidence_payload(
        self,
        *,
        objective_text: str,
        graph: TeachingGraphArtifact,
        target_id: str,
        target_label: str,
        target_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        if not self.wcag_mcp:
            raise self.retrieval_error_cls(
                "Teaching graph retrieval failed: WCAG MCP client unavailable."
            )

        response = await self.reasoning_client.responses_create(
            instructions=NODE_EVIDENCE_RETRIEVAL_TOOLCALL_PROMPT,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "\n\n".join(
                                [
                                    f"OBJECTIVE:\n{objective_text}",
                                    f"GRAPH:\n{json.dumps(graph.to_dict(), indent=2)}",
                                    f"{target_label}:\n{json.dumps(target_payload, indent=2)}",
                                ]
                            ),
                        }
                    ],
                }
            ],
            tools=self._responses_tool_definitions(),
            tool_choice="required",
            parallel_tool_calls=False,
            reasoning_effort=self.reasoning_effort,
            max_output_tokens=self.max_completion_tokens,
            max_tool_calls=self.max_tool_calls_per_node,
            store=True,
        )
        rounds = 0
        while rounds < self.max_rounds:
            tool_calls = self._extract_function_calls(response)
            if not tool_calls:
                break
            planned_calls: List[Dict[str, Any]] = []
            for call in tool_calls:
                tool_name = str(call.get("name") or "").strip()
                if not tool_name:
                    continue
                raw_args = dict(call.get("arguments") or {})
                rationale = str(raw_args.pop("rationale", "")).strip()
                raw_args = {key: value for key, value in raw_args.items() if value is not None}
                planned_calls.append(
                    {
                        "tool": tool_name,
                        "args": raw_args,
                        "kind": self._tool_kind_from_name(tool_name),
                        "grounding_note": rationale or f"Grounding for {target_id}",
                        "category": "graph_target_grounding",
                        "source": "teaching_graph_target_retrieval",
                        "tool_call_id": call.get("call_id"),
                    }
                )

            if not planned_calls:
                break

            results = await self.wcag_mcp.execute_planned_tool_calls(planned_calls)
            tool_outputs = []
            for planned_call, result in zip(planned_calls, results):
                output_payload = {
                    "status": result.get("status"),
                    "tool": planned_call["tool"],
                    "args": planned_call["args"],
                    "kind": planned_call["kind"],
                    "grounding_note": planned_call["grounding_note"],
                    "title": self._result_title(result),
                    "content": result.get("result") or "",
                    "chars": result.get("chars", 0),
                }
                tool_outputs.append(
                    {
                        "type": "function_call_output",
                        "call_id": planned_call.get("tool_call_id") or "",
                        "output": json.dumps(output_payload),
                    }
                )

            response = await self.reasoning_client.responses_create(
                previous_response_id=response.get("id"),
                input=tool_outputs,
                tools=self._responses_tool_definitions(),
                tool_choice="auto",
                parallel_tool_calls=False,
                reasoning_effort=self.reasoning_effort,
                max_output_tokens=self.max_completion_tokens,
                max_tool_calls=self.max_tool_calls_per_node,
            )
            rounds += 1

        final_response = await self.reasoning_client.responses_create(
            previous_response_id=response.get("id"),
            instructions=NODE_EVIDENCE_FINALIZATION_PROMPT,
            input=[],
            text=self._node_evidence_text_format(),
            reasoning_effort=self.reasoning_effort,
            max_output_tokens=self.max_completion_tokens,
        )
        final_text = self._strip_code_fences(self._response_text(final_response))
        try:
            return json.loads(final_text)
        except Exception as exc:
            preview = final_text.replace("\n", " ").strip()
            if len(preview) > 200:
                preview = preview[:200] + "..."
            raise self.retrieval_error_cls(
                f"Teaching graph retrieval finalization failed for {target_id}: {preview or 'empty response'}"
            ) from exc

    async def _retrieve_node_evidence_payload(
        self,
        *,
        objective_text: str,
        graph: TeachingGraphArtifact,
        node: Any,
    ) -> Dict[str, Any]:
        return await self._retrieve_evidence_payload(
            objective_text=objective_text,
            graph=graph,
            target_id=node.id,
            target_label="TARGET NODE",
            target_payload=node.to_dict(),
        )

    @staticmethod
    def _edge_target_id(edge: Any) -> str:
        return f"edge:{edge.from_node}->{edge.to_node}"

    @staticmethod
    def _integration_target_id(graph: TeachingGraphArtifact) -> str:
        return f"integration:{graph.integration_node}"

    @staticmethod
    def _edge_needs_retrieval(edge: Any, graph: TeachingGraphArtifact) -> bool:
        if edge.type in {"contrasts_with", "applies_to", "synthesizes_into"}:
            return True
        graph_type = graph.graph_type
        return "decision" in graph_type or "application" in graph_type

    @classmethod
    def _edge_target_payload(cls, edge: Any) -> Dict[str, Any]:
        return {
            "id": cls._edge_target_id(edge),
            "kind": "edge",
            "from": edge.from_node,
            "to": edge.to_node,
            "type": edge.type,
            "bridge_claim": edge.bridge_claim,
            "retrieval_reason": (
                "Retrieve only if this edge needs contrastive, exception, risk, "
                "dependency, or application evidence beyond the connected nodes."
            ),
        }

    @classmethod
    def _integration_target_payload(cls, graph: TeachingGraphArtifact) -> Dict[str, Any]:
        return {
            "id": cls._integration_target_id(graph),
            "kind": "integration",
            "integration_node": graph.integration_node,
            "primary_route": list(graph.primary_route),
            "graph_type": graph.graph_type,
            "retrieval_reason": (
                "Retrieve facts needed to combine several graph concepts in one "
                "realistic scenario, including valid combinations, interaction "
                "expectations, accessible-name requirements, risks, or failures."
            ),
        }

    @staticmethod
    def _record_from_payload(
        *,
        objective_text: str,
        graph: TeachingGraphArtifact,
        target_id: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        payload["node_id"] = target_id
        artifact = NodeEvidenceArtifact.from_dict(
            {
                "objective_text": objective_text,
                "graph_summary": {
                    "graph_type": graph.graph_type,
                    "node_ids": [node.id for node in graph.nodes],
                },
                "node_evidence": [
                    {
                        "node_id": target_id,
                        "grounding_strength": payload["grounding_strength"],
                        "coverage_summary": payload["coverage_summary"],
                        "source_tools_used": payload.get("source_tools_used") or [],
                        "retrieved_items": payload.get("retrieved_items") or [],
                    }
                ],
            }
        )
        record = artifact.node_evidence[0]
        if not record.retrieved_items:
            raise ValueError("no grounded evidence was retrieved")
        return record.to_dict()

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
            payload = await self._retrieve_node_evidence_payload(
                objective_text=objective_text,
                graph=graph,
                node=node,
            )
            try:
                record = self._record_from_payload(
                    objective_text=objective_text,
                    graph=graph,
                    target_id=node.id,
                    payload=payload,
                )
            except Exception as exc:
                raise self.retrieval_error_cls(
                    f"Teaching graph node retrieval failed for {node.id}: no grounded evidence was retrieved."
                ) from exc
            node_records.append(record)

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

    async def build_graph_evidence(
        self,
        *,
        objective_text: str,
        graph: TeachingGraphArtifact,
    ) -> NodeEvidenceArtifact:
        node_artifact = await self.build_node_evidence(
            objective_text=objective_text,
            graph=graph,
        )
        records = [record.to_dict() for record in node_artifact.node_evidence]

        for edge in graph.edges:
            if not self._edge_needs_retrieval(edge, graph):
                continue
            target_id = self._edge_target_id(edge)
            payload = await self._retrieve_evidence_payload(
                objective_text=objective_text,
                graph=graph,
                target_id=target_id,
                target_label="TARGET EDGE",
                target_payload=self._edge_target_payload(edge),
            )
            try:
                records.append(
                    self._record_from_payload(
                        objective_text=objective_text,
                        graph=graph,
                        target_id=target_id,
                        payload=payload,
                    )
                )
            except Exception as exc:
                raise self.retrieval_error_cls(
                    f"Teaching graph edge retrieval failed for {target_id}: no grounded evidence was retrieved."
                ) from exc

        integration_id = self._integration_target_id(graph)
        integration_payload = await self._retrieve_evidence_payload(
            objective_text=objective_text,
            graph=graph,
            target_id=integration_id,
            target_label="TARGET INTEGRATION",
            target_payload=self._integration_target_payload(graph),
        )
        try:
            records.append(
                self._record_from_payload(
                    objective_text=objective_text,
                    graph=graph,
                    target_id=integration_id,
                    payload=integration_payload,
                )
            )
        except Exception as exc:
            raise self.retrieval_error_cls(
                f"Teaching graph integration retrieval failed for {integration_id}: no grounded evidence was retrieved."
            ) from exc

        return NodeEvidenceArtifact.from_dict(
            {
                "objective_text": objective_text,
                "graph_summary": {
                    "graph_type": graph.graph_type,
                    "node_ids": [node.id for node in graph.nodes],
                    "edge_evidence_ids": [
                        self._edge_target_id(edge)
                        for edge in graph.edges
                        if self._edge_needs_retrieval(edge, graph)
                    ],
                    "integration_evidence_id": integration_id,
                },
                "node_evidence": records,
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
        node_evidence: NodeEvidenceArtifact,
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
                            f"GRAPH EVIDENCE:\n{json.dumps(node_evidence.to_dict(), indent=2)}",
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


class GraphGroundingProjector:
    """Build deterministic grounding artifacts around graph worker outputs."""

    EVIDENCE_TO_CLAIM_TYPE = {
        "definition": "official_definition",
        "normative_anchor": "normative_requirement",
        "explanatory_support": "pedagogical_inference",
        "contrast_support": "pedagogical_inference",
        "risk_support": "failure_condition",
        "structural_support": "structural_fact",
        "implementation_support": "implementation_pattern",
        "example_support": "synthetic_example_judgment",
        "failure_support": "failure_condition",
    }

    @staticmethod
    def _node_evidence_lookup(node_evidence: NodeEvidenceArtifact) -> Dict[str, List[str]]:
        lookup: Dict[str, List[str]] = {}
        for record in node_evidence.node_evidence:
            lookup[record.node_id] = [item.item_id for item in record.retrieved_items]
        return lookup

    @staticmethod
    def _target_refs_for_record(record_id: str) -> List[str]:
        if record_id.startswith("edge:"):
            return [record_id]
        if record_id.startswith("integration:"):
            return [record_id]
        return [f"node:{record_id}"]

    @classmethod
    def build_evidence_cards(
        cls,
        *,
        objective_text: str,
        node_evidence: NodeEvidenceArtifact,
    ) -> EvidenceCardSet:
        raw_records: List[Dict[str, Any]] = []
        cards: List[Dict[str, Any]] = []
        raw_id_by_key: Dict[tuple[str, str, str], str] = {}

        for record in node_evidence.node_evidence:
            target_refs = cls._target_refs_for_record(record.node_id)
            for item in record.retrieved_items:
                raw_id = f"raw_{item.item_id}"
                raw_key = (item.tool, json.dumps(item.args, sort_keys=True), item.content)
                if raw_key in raw_id_by_key:
                    raw_id = raw_id_by_key[raw_key]
                else:
                    raw_id_by_key[raw_key] = raw_id
                    raw_records.append(
                        {
                            "raw_evidence_id": raw_id,
                            "target_refs": target_refs,
                            "source": "wcag_mcp",
                            "tool": item.tool,
                            "args": item.args,
                            "status": "HIT",
                            "chars": len(item.content),
                            "raw_result": item.content,
                        }
                    )
                claim_type = cls.EVIDENCE_TO_CLAIM_TYPE.get(
                    item.kind, "pedagogical_inference"
                )
                cards.append(
                    {
                        "evidence_id": item.item_id,
                        "raw_evidence_id": raw_id,
                        "target_refs": target_refs,
                        "evidence_type": item.kind,
                        "source_ref": item.title,
                        "title": item.title,
                        "usable_facts": [
                            {
                                "fact_id": f"fact_{item.item_id}",
                                "text": item.grounding_note or item.content[:400],
                                "supports_claim_types": [claim_type],
                            }
                        ],
                        "limitations": [],
                        "grounding_strength": record.grounding_strength,
                    }
                )

        return EvidenceCardSet.from_dict(
            {
                "objective_text": objective_text,
                "raw_evidence": raw_records,
                "evidence_cards": cards,
                "unsupported_gaps": [],
            }
        )

    @classmethod
    def build_claim_ledger(
        cls,
        *,
        objective_text: str,
        node_evidence: NodeEvidenceArtifact,
        node_content: NodeContentArtifact,
        edge_integration: EdgeIntegrationArtifact,
        evidence_cards: EvidenceCardSet,
    ) -> ClaimLedgerArtifact:
        evidence_by_node = cls._node_evidence_lookup(node_evidence)
        claims: List[Dict[str, Any]] = []

        for node in node_content.nodes:
            node_evidence_ids = evidence_by_node.get(node.id, [])
            claims.append(
                {
                    "claim_id": f"claim_{node.id}_core",
                    "scope": {"type": "node", "id": node.id, "field": "core_claim"},
                    "text": node.core_claim,
                    "claim_type": "pedagogical_inference",
                    "requires_evidence": bool(node_evidence_ids),
                    "evidence_ids": node_evidence_ids,
                    "generated": True,
                    "status": "pending_validation",
                }
            )
            for index, claim_text in enumerate(node.supporting_claims):
                grounding = next(
                    (
                        item
                        for item in node.supporting_claim_grounding
                        if item.claim_index == index
                    ),
                    None,
                )
                evidence_ids = grounding.basis_item_ids if grounding else node_evidence_ids
                claims.append(
                    {
                        "claim_id": f"claim_{node.id}_support_{index}",
                        "scope": {
                            "type": "node",
                            "id": node.id,
                            "field": f"supporting_claims[{index}]",
                        },
                        "text": claim_text,
                        "claim_type": "pedagogical_inference",
                        "requires_evidence": True,
                        "evidence_ids": evidence_ids,
                        "generated": True,
                        "status": "pending_validation",
                    }
                )
            claims.append(
                {
                    "claim_id": f"claim_{node.id}_example",
                    "scope": {
                        "type": "example",
                        "id": f"{node.id}:canonical_example",
                        "field": "canonical_example",
                    },
                    "text": node.canonical_example.text,
                    "claim_type": "synthetic_example_judgment",
                    "requires_evidence": True,
                    "evidence_ids": node.canonical_example.grounding_basis,
                    "generated": True,
                    "status": "pending_validation",
                }
            )

        for edge in edge_integration.edges:
            edge_id = f"{edge.from_node}->{edge.to_node}"
            edge_target_id = f"edge:{edge_id}"
            edge_evidence_ids = sorted(
                set(evidence_by_node.get(edge.from_node, []))
                | set(evidence_by_node.get(edge.to_node, []))
                | set(evidence_by_node.get(edge_target_id, []))
            )
            claims.append(
                {
                    "claim_id": f"claim_edge_{edge.from_node}_{edge.to_node}",
                    "scope": {"type": "edge", "id": edge_id, "field": "bridge_text"},
                    "text": edge.bridge_text,
                    "claim_type": "pedagogical_inference",
                    "requires_evidence": bool(edge_evidence_ids),
                    "evidence_ids": edge_evidence_ids,
                    "generated": True,
                    "status": "pending_validation",
                }
            )

        integration_evidence_ids: List[str] = []
        for node_id in edge_integration.integration.what_must_be_combined:
            integration_evidence_ids.extend(evidence_by_node.get(node_id, []))
        integration_evidence_ids.extend(
            evidence_by_node.get(f"integration:{edge_integration.integration.node_id}", [])
        )
        integration_evidence_ids = sorted(set(integration_evidence_ids))
        claims.append(
            {
                "claim_id": "claim_integration_core",
                "scope": {
                    "type": "integration",
                    "id": edge_integration.integration.node_id,
                    "field": "integration_claim",
                },
                "text": edge_integration.integration.integration_claim,
                "claim_type": "pedagogical_inference",
                "requires_evidence": bool(integration_evidence_ids),
                "evidence_ids": integration_evidence_ids,
                "generated": True,
                "status": "pending_validation",
            }
        )

        return ClaimLedgerArtifact.from_dict(
            {
                "objective_text": objective_text,
                "claims": claims,
            },
            known_evidence_ids={item.evidence_id for item in evidence_cards.evidence_cards},
        )

    @staticmethod
    def deterministic_validate(
        *,
        validation: GroundingValidationArtifact,
        claim_ledger: ClaimLedgerArtifact,
        evidence_cards: EvidenceCardSet,
    ) -> GroundingValidationArtifact:
        evidence_ids = {item.evidence_id for item in evidence_cards.evidence_cards}
        claim_checks: List[Dict[str, Any]] = []
        status = validation.overall_status
        for claim in claim_ledger.claims:
            missing = [item for item in claim.evidence_ids if item not in evidence_ids]
            if claim.requires_evidence and not claim.evidence_ids:
                status = "fail"
                claim_checks.append(
                    {
                        "claim_id": claim.claim_id,
                        "status": "fail",
                        "reason": "Evidence-required claim has no evidence IDs.",
                        "action": "Retrieve evidence or remove the claim.",
                    }
                )
            elif missing:
                status = "fail"
                claim_checks.append(
                    {
                        "claim_id": claim.claim_id,
                        "status": "fail",
                        "reason": f"Unknown evidence IDs: {', '.join(missing)}",
                        "action": "Fix evidence references before exposing content.",
                    }
                )
            else:
                claim_checks.append(
                    {
                        "claim_id": claim.claim_id,
                        "status": "pass",
                        "reason": "",
                        "action": "",
                    }
                )

        payload = validation.to_dict()
        payload["overall_status"] = status
        payload["claim_checks"] = claim_checks
        return GroundingValidationArtifact.from_dict(payload)

    @staticmethod
    def build_tutor_facing_content(
        *,
        objective_text: str,
        graph: TeachingGraphArtifact,
        node_content: NodeContentArtifact,
        edge_integration: EdgeIntegrationArtifact,
        evidence_cards: EvidenceCardSet,
        claim_ledger: ClaimLedgerArtifact,
        validation: GroundingValidationArtifact,
    ) -> TutorFacingTeachingContent:
        nodes = [
            {
                "id": node.id,
                "label": node.label,
                "core_claim": node.core_claim,
                "supporting_claims": list(node.supporting_claims),
                "canonical_example": node.canonical_example.text,
                "canonical_contrast": node.canonical_contrast.text,
            }
            for node in node_content.nodes
        ]
        edges = [
            {
                "from": edge.from_node,
                "to": edge.to_node,
                "type": edge.type,
                "bridge_text": edge.bridge_text,
                "source_requirement": edge.source_requirement,
                "target_shift": edge.target_shift,
            }
            for edge in edge_integration.edges
        ]
        integration = {
            "node_id": edge_integration.integration.node_id,
            "scenario": edge_integration.integration.integration_scenario.text,
            "integration_claim": edge_integration.integration.integration_claim,
            "what_must_be_combined": list(
                edge_integration.integration.what_must_be_combined
            ),
        }
        return TutorFacingTeachingContent.from_dict(
            {
                "objective_text": objective_text,
                "ordered_concept_path": graph.primary_route,
                "nodes": nodes,
                "edges": edges,
                "integration": integration,
                "internal_grounding": {
                    "validation_status": validation.overall_status,
                    "evidence_count": len(evidence_cards.evidence_cards),
                    "claim_count": len(claim_ledger.claims),
                },
            }
        )

    @staticmethod
    def render_tutor_content(content: TutorFacingTeachingContent) -> str:
        lines = [f"# Graph-Grounded Teaching Content", "", f"Objective: {content.objective_text}", ""]
        lines.append("## Ordered Concept Path")
        lines.extend(f"- {node_id}" for node_id in content.ordered_concept_path)
        lines.append("")
        lines.append("## Nodes")
        for node in content.nodes:
            lines.append(f"### {node.get('id')}: {node.get('label')}")
            lines.append(str(node.get("core_claim", "")).strip())
            supporting = node.get("supporting_claims") or []
            if supporting:
                lines.append("")
                lines.extend(f"- {item}" for item in supporting)
            example = str(node.get("canonical_example") or "").strip()
            if example:
                lines.append("")
                lines.append(f"Example: {example}")
            contrast = str(node.get("canonical_contrast") or "").strip()
            if contrast:
                lines.append(f"Contrast: {contrast}")
            lines.append("")
        lines.append("## Transitions")
        for edge in content.edges:
            lines.append(
                f"- {edge.get('from')} -> {edge.get('to')}: {edge.get('bridge_text')}"
            )
        lines.append("")
        lines.append("## Integration")
        lines.append(str(content.integration.get("integration_claim", "")).strip())
        scenario = str(content.integration.get("scenario") or "").strip()
        if scenario:
            lines.append("")
            lines.append(f"Scenario: {scenario}")
        return "\n".join(lines).strip()
