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
            return "risk_support"
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

        converted: List[Dict[str, Any]] = []
        for tool in GUIDED_WCAG_TOOL_DEFINITIONS:
            function = tool.get("function") or {}
            converted.append(
                {
                    "type": "function",
                    "name": function.get("name"),
                    "description": function.get("description", ""),
                    "parameters": function.get("parameters") or {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
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

    async def _retrieve_node_evidence_payload(
        self,
        *,
        objective_text: str,
        graph: TeachingGraphArtifact,
        node: Any,
    ) -> Dict[str, Any]:
        if not self.wcag_mcp:
            raise self.retrieval_error_cls(
                "Teaching graph node retrieval failed: WCAG MCP client unavailable."
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
                                    f"TARGET NODE:\n{json.dumps(node.to_dict(), indent=2)}",
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
                planned_calls.append(
                    {
                        "tool": tool_name,
                        "args": raw_args,
                        "kind": self._tool_kind_from_name(tool_name),
                        "grounding_note": rationale or f"Grounding for node {node.id}",
                        "category": "graph_node_grounding",
                        "source": "teaching_graph_node_retrieval",
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
                f"Teaching graph node retrieval finalization failed for {node.id}: {preview or 'empty response'}"
            ) from exc

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
            payload["node_id"] = node.id
            artifact = NodeEvidenceArtifact.from_dict(
                {
                    "objective_text": objective_text,
                    "graph_summary": {
                        "graph_type": graph.graph_type,
                        "node_ids": [node.id for node in graph.nodes],
                    },
                    "node_evidence": [
                        {
                            "node_id": node.id,
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
                raise self.retrieval_error_cls(
                    f"Teaching graph node retrieval failed for {node.id}: no grounded evidence was retrieved."
                )
            node_records.append(record.to_dict())

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
