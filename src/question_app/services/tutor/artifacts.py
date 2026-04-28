from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional


@dataclass(frozen=True)
class TeachingPlanArtifact:
    objective_text: str
    plan: Any
    display_plan: str = ""
    extracted_concepts: Optional[List[Dict[str, str]]] = None


@dataclass(frozen=True)
class RetrievalRunArtifact:
    objective_text: str
    teaching_plan: Any
    results: List[Dict[str, Any]] = field(default_factory=list)
    coverage: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TeachingContentArtifact:
    objective_text: str
    teaching_plan: Any
    teaching_content: str
    display_content: str
    retrieval_bundle: Dict[str, Any]
    extracted_concepts: Optional[List[Dict[str, str]]] = None


@dataclass(frozen=True)
class TurnAnalysisArtifact:
    analysis: Dict[str, Any]
    display_analysis: str = ""


@dataclass(frozen=True)
class GuidedSessionStateArtifact:
    session_id: str
    objective_id: str
    objective_text: str
    teaching_plan: Any
    teaching_content: str
    retrieval_bundle: Dict[str, Any]
    lesson_state: Optional[Dict[str, Any]] = None
    pacing_state: Optional[Dict[str, Any]] = None
    misconception_state: Optional[Dict[str, Any]] = None
    student_context: str = ""
    bundle: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GuidedTurnResult:
    metadata: Dict[str, Any]
    final_text: str = ""
    final_stage: str = ""
    stage_advanced: bool = False
    assessment_metadata: Dict[str, Any] = field(default_factory=dict)


def _require_str(value: Any, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} must be a non-empty string")
    return text


def _ensure_string_list(values: Any, field_name: str) -> List[str]:
    if not isinstance(values, list) or not values:
        raise ValueError(f"{field_name} must be a non-empty list of strings")
    normalized = [_require_str(value, field_name) for value in values]
    return normalized


def _index_by(items: Iterable[Any], attr_name: str) -> Dict[str, Any]:
    indexed: Dict[str, Any] = {}
    for item in items:
        key = getattr(item, attr_name)
        if key in indexed:
            raise ValueError(f"Duplicate {attr_name}: {key}")
        indexed[key] = item
    return indexed


@dataclass(frozen=True)
class TeachingGraphNode:
    VALID_KINDS = {"core_concept", "support_prerequisite", "integration"}

    id: str
    label: str
    kind: str
    teachable_claim: str = ""

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "TeachingGraphNode":
        kind = _require_str(payload.get("kind"), "node.kind")
        if kind not in cls.VALID_KINDS:
            raise ValueError(f"Unsupported node.kind: {kind}")
        return cls(
            id=_require_str(payload.get("id"), "node.id"),
            label=_require_str(payload.get("label"), "node.label"),
            kind=kind,
            teachable_claim=str(payload.get("teachable_claim") or "").strip(),
        )

    def to_dict(self) -> Dict[str, Any]:
        payload = {"id": self.id, "label": self.label, "kind": self.kind}
        if self.teachable_claim:
            payload["teachable_claim"] = self.teachable_claim
        return payload


@dataclass(frozen=True)
class TeachingGraphEdge:
    VALID_TYPES = {
        "prerequisite",
        "refines",
        "contrasts_with",
        "applies_to",
        "synthesizes_into",
        "supports",
    }

    from_node: str
    to_node: str
    type: str
    bridge_claim: str

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "TeachingGraphEdge":
        edge_type = _require_str(payload.get("type"), "edge.type")
        if edge_type not in cls.VALID_TYPES:
            raise ValueError(f"Unsupported edge.type: {edge_type}")
        return cls(
            from_node=_require_str(payload.get("from"), "edge.from"),
            to_node=_require_str(payload.get("to"), "edge.to"),
            type=edge_type,
            bridge_claim=_require_str(payload.get("bridge_claim"), "edge.bridge_claim"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from": self.from_node,
            "to": self.to_node,
            "type": self.type,
            "bridge_claim": self.bridge_claim,
        }


@dataclass(frozen=True)
class TeachingGraphArtifact:
    VALID_GRAPH_TYPES = {
        "hierarchy",
        "comparison",
        "causal",
        "decision",
        "decision_application",
        "procedure",
        "causal_distinction_application",
    }

    objective_text: str
    graph_type: str
    entry_nodes: List[str]
    integration_node: str
    primary_route: List[str]
    nodes: List[TeachingGraphNode]
    edges: List[TeachingGraphEdge]

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "TeachingGraphArtifact":
        graph_type = _require_str(payload.get("graph_type"), "graph.graph_type")
        if graph_type not in cls.VALID_GRAPH_TYPES:
            raise ValueError(f"Unsupported graph.graph_type: {graph_type}")
        artifact = cls(
            objective_text=_require_str(
                payload.get("objective_text"), "graph.objective_text"
            ),
            graph_type=graph_type,
            entry_nodes=_ensure_string_list(payload.get("entry_nodes"), "graph.entry_nodes"),
            integration_node=_require_str(
                payload.get("integration_node"), "graph.integration_node"
            ),
            primary_route=_ensure_string_list(
                payload.get("primary_route"), "graph.primary_route"
            ),
            nodes=[
                TeachingGraphNode.from_dict(item)
                for item in (payload.get("nodes") or [])
            ],
            edges=[
                TeachingGraphEdge.from_dict(item)
                for item in (payload.get("edges") or [])
            ],
        )
        artifact.validate()
        return artifact

    def validate(self) -> None:
        if not self.nodes:
            raise ValueError("graph.nodes must not be empty")
        if not self.edges:
            raise ValueError("graph.edges must not be empty")
        node_lookup = _index_by(self.nodes, "id")
        if self.integration_node not in node_lookup:
            raise ValueError("graph.integration_node must reference an existing node")
        integration_node = node_lookup[self.integration_node]
        if integration_node.kind != "integration":
            raise ValueError("graph.integration_node must point to an integration node")
        for node_id in self.entry_nodes + self.primary_route:
            if node_id not in node_lookup:
                raise ValueError(f"Unknown node in route: {node_id}")
        if self.primary_route[-1] != self.integration_node:
            raise ValueError("graph.primary_route must end at graph.integration_node")
        for edge in self.edges:
            if edge.from_node not in node_lookup or edge.to_node not in node_lookup:
                raise ValueError("All edges must reference existing nodes")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "objective_text": self.objective_text,
            "graph_type": self.graph_type,
            "entry_nodes": list(self.entry_nodes),
            "integration_node": self.integration_node,
            "primary_route": list(self.primary_route),
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
        }


@dataclass(frozen=True)
class NodeEvidenceCoverageSummary:
    has_definition_support: bool = False
    has_normative_anchor: bool = False
    has_explanatory_support: bool = False
    has_contrast_support: bool = False
    has_risk_support: bool = False

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "NodeEvidenceCoverageSummary":
        return cls(
            has_definition_support=bool(payload.get("has_definition_support", False)),
            has_normative_anchor=bool(payload.get("has_normative_anchor", False)),
            has_explanatory_support=bool(payload.get("has_explanatory_support", False)),
            has_contrast_support=bool(payload.get("has_contrast_support", False)),
            has_risk_support=bool(payload.get("has_risk_support", False)),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "has_definition_support": self.has_definition_support,
            "has_normative_anchor": self.has_normative_anchor,
            "has_explanatory_support": self.has_explanatory_support,
            "has_contrast_support": self.has_contrast_support,
            "has_risk_support": self.has_risk_support,
        }


@dataclass(frozen=True)
class ToolInvocationRecord:
    tool: str
    args: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "ToolInvocationRecord":
        return cls(
            tool=_require_str(payload.get("tool"), "tool_call.tool"),
            args=dict(payload.get("args") or {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {"tool": self.tool, "args": dict(self.args)}


@dataclass(frozen=True)
class NodeEvidenceItem:
    VALID_KINDS = {
        "definition",
        "normative_anchor",
        "explanatory_support",
        "contrast_support",
        "risk_support",
        "structural_support",
        "implementation_support",
        "example_support",
        "failure_support",
    }

    item_id: str
    tool: str
    args: Dict[str, Any]
    kind: str
    title: str
    content: str
    grounding_note: str

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "NodeEvidenceItem":
        kind = _require_str(payload.get("kind"), "node_evidence_item.kind")
        if kind not in cls.VALID_KINDS:
            raise ValueError(f"Unsupported node_evidence_item.kind: {kind}")
        return cls(
            item_id=_require_str(payload.get("item_id"), "node_evidence_item.item_id"),
            tool=_require_str(payload.get("tool"), "node_evidence_item.tool"),
            args=dict(payload.get("args") or {}),
            kind=kind,
            title=_require_str(payload.get("title"), "node_evidence_item.title"),
            content=_require_str(payload.get("content"), "node_evidence_item.content"),
            grounding_note=_require_str(
                payload.get("grounding_note"), "node_evidence_item.grounding_note"
            ),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "tool": self.tool,
            "args": dict(self.args),
            "kind": self.kind,
            "title": self.title,
            "content": self.content,
            "grounding_note": self.grounding_note,
        }


@dataclass(frozen=True)
class NodeEvidenceRecord:
    VALID_GROUNDING_STRENGTH = {"thin", "adequate", "strong"}

    node_id: str
    grounding_strength: str
    coverage_summary: NodeEvidenceCoverageSummary
    source_tools_used: List[ToolInvocationRecord] = field(default_factory=list)
    retrieved_items: List[NodeEvidenceItem] = field(default_factory=list)
    notes_on_gaps: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "NodeEvidenceRecord":
        grounding_strength = _require_str(
            payload.get("grounding_strength"), "node_evidence.grounding_strength"
        )
        if grounding_strength not in cls.VALID_GROUNDING_STRENGTH:
            raise ValueError(
                f"Unsupported node_evidence.grounding_strength: {grounding_strength}"
            )
        record = cls(
            node_id=_require_str(payload.get("node_id"), "node_evidence.node_id"),
            grounding_strength=grounding_strength,
            coverage_summary=NodeEvidenceCoverageSummary.from_dict(
                dict(payload.get("coverage_summary") or {})
            ),
            source_tools_used=[
                ToolInvocationRecord.from_dict(item)
                for item in (payload.get("source_tools_used") or [])
            ],
            retrieved_items=[
                NodeEvidenceItem.from_dict(item)
                for item in (payload.get("retrieved_items") or [])
            ],
            notes_on_gaps=[
                str(item).strip()
                for item in (payload.get("notes_on_gaps") or [])
                if str(item).strip()
            ],
        )
        if not record.retrieved_items:
            raise ValueError("node_evidence.retrieved_items must not be empty")
        return record

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "grounding_strength": self.grounding_strength,
            "coverage_summary": self.coverage_summary.to_dict(),
            "source_tools_used": [item.to_dict() for item in self.source_tools_used],
            "retrieved_items": [item.to_dict() for item in self.retrieved_items],
            "notes_on_gaps": list(self.notes_on_gaps),
        }


@dataclass(frozen=True)
class NodeEvidenceArtifact:
    objective_text: str
    graph_summary: Dict[str, Any]
    node_evidence: List[NodeEvidenceRecord]

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "NodeEvidenceArtifact":
        artifact = cls(
            objective_text=_require_str(
                payload.get("objective_text"), "node_evidence_artifact.objective_text"
            ),
            graph_summary=dict(payload.get("graph_summary") or {}),
            node_evidence=[
                NodeEvidenceRecord.from_dict(item)
                for item in (payload.get("node_evidence") or [])
            ],
        )
        if not artifact.node_evidence:
            raise ValueError("node_evidence_artifact.node_evidence must not be empty")
        _index_by(artifact.node_evidence, "node_id")
        return artifact

    def to_dict(self) -> Dict[str, Any]:
        return {
            "objective_text": self.objective_text,
            "graph_summary": dict(self.graph_summary),
            "node_evidence": [item.to_dict() for item in self.node_evidence],
        }


@dataclass(frozen=True)
class RawEvidenceRecord:
    raw_evidence_id: str
    target_refs: List[str]
    source: str
    tool: str
    args: Dict[str, Any]
    status: str
    chars: int
    raw_result: str

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "RawEvidenceRecord":
        status = _require_str(payload.get("status"), "raw_evidence.status")
        if status not in {"HIT", "MISS", "BLOCKED", "ERROR"}:
            raise ValueError(f"Unsupported raw_evidence.status: {status}")
        chars = payload.get("chars", 0)
        if not isinstance(chars, int) or chars < 0:
            raise ValueError("raw_evidence.chars must be a non-negative integer")
        return cls(
            raw_evidence_id=_require_str(
                payload.get("raw_evidence_id"), "raw_evidence.raw_evidence_id"
            ),
            target_refs=_ensure_string_list(
                payload.get("target_refs"), "raw_evidence.target_refs"
            ),
            source=_require_str(payload.get("source"), "raw_evidence.source"),
            tool=_require_str(payload.get("tool"), "raw_evidence.tool"),
            args=dict(payload.get("args") or {}),
            status=status,
            chars=chars,
            raw_result=str(payload.get("raw_result") or ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_evidence_id": self.raw_evidence_id,
            "target_refs": list(self.target_refs),
            "source": self.source,
            "tool": self.tool,
            "args": dict(self.args),
            "status": self.status,
            "chars": self.chars,
            "raw_result": self.raw_result,
        }


@dataclass(frozen=True)
class EvidenceFact:
    fact_id: str
    text: str
    supports_claim_types: List[str]

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "EvidenceFact":
        return cls(
            fact_id=_require_str(payload.get("fact_id"), "evidence_fact.fact_id"),
            text=_require_str(payload.get("text"), "evidence_fact.text"),
            supports_claim_types=_ensure_string_list(
                payload.get("supports_claim_types"),
                "evidence_fact.supports_claim_types",
            ),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fact_id": self.fact_id,
            "text": self.text,
            "supports_claim_types": list(self.supports_claim_types),
        }


@dataclass(frozen=True)
class EvidenceCard:
    VALID_TYPES = NodeEvidenceItem.VALID_KINDS
    VALID_STRENGTHS = {"thin", "adequate", "strong"}

    evidence_id: str
    raw_evidence_id: str
    target_refs: List[str]
    evidence_type: str
    source_ref: str
    title: str
    usable_facts: List[EvidenceFact]
    limitations: List[str] = field(default_factory=list)
    grounding_strength: str = "adequate"

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "EvidenceCard":
        evidence_type = _require_str(
            payload.get("evidence_type"), "evidence_card.evidence_type"
        )
        if evidence_type not in cls.VALID_TYPES:
            raise ValueError(f"Unsupported evidence_card.evidence_type: {evidence_type}")
        grounding_strength = str(payload.get("grounding_strength") or "adequate").strip()
        if grounding_strength not in cls.VALID_STRENGTHS:
            raise ValueError(
                f"Unsupported evidence_card.grounding_strength: {grounding_strength}"
            )
        facts = [
            EvidenceFact.from_dict(item)
            for item in (payload.get("usable_facts") or [])
        ]
        if not facts:
            raise ValueError("evidence_card.usable_facts must not be empty")
        return cls(
            evidence_id=_require_str(
                payload.get("evidence_id"), "evidence_card.evidence_id"
            ),
            raw_evidence_id=_require_str(
                payload.get("raw_evidence_id"), "evidence_card.raw_evidence_id"
            ),
            target_refs=_ensure_string_list(
                payload.get("target_refs"), "evidence_card.target_refs"
            ),
            evidence_type=evidence_type,
            source_ref=_require_str(
                payload.get("source_ref"), "evidence_card.source_ref"
            ),
            title=_require_str(payload.get("title"), "evidence_card.title"),
            usable_facts=facts,
            limitations=[
                str(item).strip()
                for item in (payload.get("limitations") or [])
                if str(item).strip()
            ],
            grounding_strength=grounding_strength,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "raw_evidence_id": self.raw_evidence_id,
            "target_refs": list(self.target_refs),
            "evidence_type": self.evidence_type,
            "source_ref": self.source_ref,
            "title": self.title,
            "usable_facts": [item.to_dict() for item in self.usable_facts],
            "limitations": list(self.limitations),
            "grounding_strength": self.grounding_strength,
        }


@dataclass(frozen=True)
class EvidenceCardSet:
    objective_text: str
    raw_evidence: List[RawEvidenceRecord]
    evidence_cards: List[EvidenceCard]
    unsupported_gaps: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "EvidenceCardSet":
        card_set = cls(
            objective_text=_require_str(
                payload.get("objective_text"), "evidence_card_set.objective_text"
            ),
            raw_evidence=[
                RawEvidenceRecord.from_dict(item)
                for item in (payload.get("raw_evidence") or [])
            ],
            evidence_cards=[
                EvidenceCard.from_dict(item)
                for item in (payload.get("evidence_cards") or [])
            ],
            unsupported_gaps=[
                str(item).strip()
                for item in (payload.get("unsupported_gaps") or [])
                if str(item).strip()
            ],
        )
        _index_by(card_set.raw_evidence, "raw_evidence_id")
        _index_by(card_set.evidence_cards, "evidence_id")
        raw_ids = {item.raw_evidence_id for item in card_set.raw_evidence}
        for card in card_set.evidence_cards:
            if card.raw_evidence_id not in raw_ids:
                raise ValueError(
                    f"Evidence card references unknown raw evidence: {card.raw_evidence_id}"
                )
        return card_set

    def to_dict(self) -> Dict[str, Any]:
        return {
            "objective_text": self.objective_text,
            "raw_evidence": [item.to_dict() for item in self.raw_evidence],
            "evidence_cards": [item.to_dict() for item in self.evidence_cards],
            "unsupported_gaps": list(self.unsupported_gaps),
        }


@dataclass(frozen=True)
class GroundedTextSpan:
    text: str
    grounding_basis: List[str]

    @classmethod
    def from_dict(cls, payload: Dict[str, Any], *, field_name: str) -> "GroundedTextSpan":
        return cls(
            text=_require_str(payload.get("text"), f"{field_name}.text"),
            grounding_basis=_ensure_string_list(
                payload.get("grounding_basis"), f"{field_name}.grounding_basis"
            ),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {"text": self.text, "grounding_basis": list(self.grounding_basis)}


@dataclass(frozen=True)
class SupportingClaimGrounding:
    claim_index: int
    basis_item_ids: List[str]

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "SupportingClaimGrounding":
        claim_index = payload.get("claim_index")
        if not isinstance(claim_index, int) or claim_index < 0:
            raise ValueError("supporting_claim_grounding.claim_index must be >= 0")
        return cls(
            claim_index=claim_index,
            basis_item_ids=_ensure_string_list(
                payload.get("basis_item_ids"),
                "supporting_claim_grounding.basis_item_ids",
            ),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_index": self.claim_index,
            "basis_item_ids": list(self.basis_item_ids),
        }


@dataclass(frozen=True)
class NodeContentRecord:
    id: str
    label: str
    kind: str
    core_claim: str
    supporting_claims: List[str]
    canonical_example: GroundedTextSpan
    canonical_contrast: GroundedTextSpan
    supporting_claim_grounding: List[SupportingClaimGrounding]

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "NodeContentRecord":
        record = cls(
            id=_require_str(payload.get("id"), "node_content.id"),
            label=_require_str(payload.get("label"), "node_content.label"),
            kind=_require_str(payload.get("kind"), "node_content.kind"),
            core_claim=_require_str(payload.get("core_claim"), "node_content.core_claim"),
            supporting_claims=_ensure_string_list(
                payload.get("supporting_claims"), "node_content.supporting_claims"
            ),
            canonical_example=GroundedTextSpan.from_dict(
                dict(payload.get("canonical_example") or {}),
                field_name="node_content.canonical_example",
            ),
            canonical_contrast=GroundedTextSpan.from_dict(
                dict(payload.get("canonical_contrast") or {}),
                field_name="node_content.canonical_contrast",
            ),
            supporting_claim_grounding=[
                SupportingClaimGrounding.from_dict(item)
                for item in (payload.get("supporting_claim_grounding") or [])
            ],
        )
        if len(record.supporting_claim_grounding) != len(record.supporting_claims):
            raise ValueError(
                "node_content.supporting_claim_grounding must match supporting_claims length"
            )
        return record

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "kind": self.kind,
            "core_claim": self.core_claim,
            "supporting_claims": list(self.supporting_claims),
            "canonical_example": self.canonical_example.to_dict(),
            "canonical_contrast": self.canonical_contrast.to_dict(),
            "supporting_claim_grounding": [
                item.to_dict() for item in self.supporting_claim_grounding
            ],
        }


@dataclass(frozen=True)
class NodeContentArtifact:
    objective_text: str
    nodes: List[NodeContentRecord]

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "NodeContentArtifact":
        artifact = cls(
            objective_text=_require_str(
                payload.get("objective_text"), "node_content_artifact.objective_text"
            ),
            nodes=[
                NodeContentRecord.from_dict(item)
                for item in (payload.get("nodes") or [])
            ],
        )
        if not artifact.nodes:
            raise ValueError("node_content_artifact.nodes must not be empty")
        _index_by(artifact.nodes, "id")
        return artifact

    def to_dict(self) -> Dict[str, Any]:
        return {
            "objective_text": self.objective_text,
            "nodes": [item.to_dict() for item in self.nodes],
        }


@dataclass(frozen=True)
class EdgeContentRecord:
    from_node: str
    to_node: str
    type: str
    transition_rationale: str
    bridge_text: str
    source_requirement: str
    target_shift: str
    bridge_example: GroundedTextSpan
    transition_misconception: GroundedTextSpan

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "EdgeContentRecord":
        transition_misconception = dict(payload.get("transition_misconception") or {})
        if not transition_misconception:
            transition_misconception = {
                "text": "No generated learner misconception.",
                "grounding_basis": [payload.get("from") or "edge"],
            }
        return cls(
            from_node=_require_str(payload.get("from"), "edge_content.from"),
            to_node=_require_str(payload.get("to"), "edge_content.to"),
            type=_require_str(payload.get("type"), "edge_content.type"),
            transition_rationale=_require_str(
                payload.get("transition_rationale"),
                "edge_content.transition_rationale",
            ),
            bridge_text=_require_str(payload.get("bridge_text"), "edge_content.bridge_text"),
            source_requirement=_require_str(
                payload.get("source_requirement"),
                "edge_content.source_requirement",
            ),
            target_shift=_require_str(payload.get("target_shift"), "edge_content.target_shift"),
            bridge_example=GroundedTextSpan.from_dict(
                dict(payload.get("bridge_example") or {}),
                field_name="edge_content.bridge_example",
            ),
            transition_misconception=GroundedTextSpan.from_dict(
                transition_misconception,
                field_name="edge_content.transition_misconception",
            ),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from": self.from_node,
            "to": self.to_node,
            "type": self.type,
            "transition_rationale": self.transition_rationale,
            "bridge_text": self.bridge_text,
            "source_requirement": self.source_requirement,
            "target_shift": self.target_shift,
            "bridge_example": self.bridge_example.to_dict(),
        }


@dataclass(frozen=True)
class IntegrationContent:
    node_id: str
    integration_claim: str
    integration_scenario: GroundedTextSpan
    what_must_be_combined: List[str]

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "IntegrationContent":
        combined = _ensure_string_list(
            payload.get("what_must_be_combined"),
            "integration.what_must_be_combined",
        )
        if len(combined) < 2:
            raise ValueError(
                "integration.what_must_be_combined must include at least two node ids"
            )
        return cls(
            node_id=_require_str(payload.get("node_id"), "integration.node_id"),
            integration_claim=_require_str(
                payload.get("integration_claim"), "integration.integration_claim"
            ),
            integration_scenario=GroundedTextSpan.from_dict(
                dict(payload.get("integration_scenario") or {}),
                field_name="integration.integration_scenario",
            ),
            what_must_be_combined=combined,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "integration_claim": self.integration_claim,
            "integration_scenario": self.integration_scenario.to_dict(),
            "what_must_be_combined": list(self.what_must_be_combined),
        }


@dataclass(frozen=True)
class EdgeIntegrationArtifact:
    objective_text: str
    edges: List[EdgeContentRecord]
    integration: IntegrationContent

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "EdgeIntegrationArtifact":
        artifact = cls(
            objective_text=_require_str(
                payload.get("objective_text"),
                "edge_integration_artifact.objective_text",
            ),
            edges=[
                EdgeContentRecord.from_dict(item)
                for item in (payload.get("edges") or [])
            ],
            integration=IntegrationContent.from_dict(
                dict(payload.get("integration") or {})
            ),
        )
        if not artifact.edges:
            raise ValueError("edge_integration_artifact.edges must not be empty")
        return artifact

    def to_dict(self) -> Dict[str, Any]:
        return {
            "objective_text": self.objective_text,
            "edges": [item.to_dict() for item in self.edges],
            "integration": self.integration.to_dict(),
        }


@dataclass(frozen=True)
class ClaimScope:
    VALID_TYPES = {"node", "edge", "integration", "example", "scenario", "reasoning_path"}

    type: str
    id: str
    field: str = ""

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "ClaimScope":
        scope_type = _require_str(payload.get("type"), "claim_scope.type")
        if scope_type not in cls.VALID_TYPES:
            raise ValueError(f"Unsupported claim_scope.type: {scope_type}")
        return cls(
            type=scope_type,
            id=_require_str(payload.get("id"), "claim_scope.id"),
            field=str(payload.get("field") or "").strip(),
        )

    def to_dict(self) -> Dict[str, Any]:
        payload = {"type": self.type, "id": self.id}
        if self.field:
            payload["field"] = self.field
        return payload


@dataclass(frozen=True)
class ClaimRecord:
    VALID_TYPES = {
        "normative_requirement",
        "official_definition",
        "aria_semantics",
        "keyboard_requirement",
        "accessible_name_requirement",
        "failure_condition",
        "implementation_pattern",
        "structural_fact",
        "pedagogical_inference",
        "synthetic_example_judgment",
    }
    EVIDENCE_REQUIRED_TYPES = {
        "normative_requirement",
        "official_definition",
        "aria_semantics",
        "keyboard_requirement",
        "accessible_name_requirement",
        "failure_condition",
        "implementation_pattern",
        "structural_fact",
        "synthetic_example_judgment",
    }

    claim_id: str
    scope: ClaimScope
    text: str
    claim_type: str
    requires_evidence: bool
    evidence_ids: List[str] = field(default_factory=list)
    generated: bool = True
    status: str = "pending_validation"

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "ClaimRecord":
        claim_type = _require_str(payload.get("claim_type"), "claim.claim_type")
        if claim_type not in cls.VALID_TYPES:
            raise ValueError(f"Unsupported claim.claim_type: {claim_type}")
        requires_evidence = bool(
            payload.get(
                "requires_evidence",
                claim_type in cls.EVIDENCE_REQUIRED_TYPES,
            )
        )
        evidence_ids = [
            str(item).strip()
            for item in (payload.get("evidence_ids") or [])
            if str(item).strip()
        ]
        if requires_evidence and not evidence_ids:
            raise ValueError(
                f"Evidence-required claim has no evidence_ids: {payload.get('claim_id')}"
            )
        return cls(
            claim_id=_require_str(payload.get("claim_id"), "claim.claim_id"),
            scope=ClaimScope.from_dict(dict(payload.get("scope") or {})),
            text=_require_str(payload.get("text"), "claim.text"),
            claim_type=claim_type,
            requires_evidence=requires_evidence,
            evidence_ids=evidence_ids,
            generated=bool(payload.get("generated", True)),
            status=str(payload.get("status") or "pending_validation").strip(),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "scope": self.scope.to_dict(),
            "text": self.text,
            "claim_type": self.claim_type,
            "requires_evidence": self.requires_evidence,
            "evidence_ids": list(self.evidence_ids),
            "generated": self.generated,
            "status": self.status,
        }


@dataclass(frozen=True)
class ClaimLedgerArtifact:
    objective_text: str
    claims: List[ClaimRecord]

    @classmethod
    def from_dict(
        cls,
        payload: Dict[str, Any],
        *,
        known_evidence_ids: Optional[Iterable[str]] = None,
    ) -> "ClaimLedgerArtifact":
        ledger = cls(
            objective_text=_require_str(
                payload.get("objective_text"), "claim_ledger.objective_text"
            ),
            claims=[
                ClaimRecord.from_dict(item)
                for item in (payload.get("claims") or [])
            ],
        )
        _index_by(ledger.claims, "claim_id")
        if known_evidence_ids is not None:
            ledger.validate_evidence_references(set(known_evidence_ids))
        return ledger

    def validate_evidence_references(self, known_evidence_ids: set[str]) -> None:
        for claim in self.claims:
            for evidence_id in claim.evidence_ids:
                if evidence_id not in known_evidence_ids:
                    raise ValueError(
                        f"Claim {claim.claim_id} references unknown evidence_id: {evidence_id}"
                    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "objective_text": self.objective_text,
            "claims": [item.to_dict() for item in self.claims],
        }


@dataclass(frozen=True)
class TutorFacingTeachingContent:
    objective_text: str
    ordered_concept_path: List[str]
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    integration: Dict[str, Any]
    internal_grounding: Dict[str, Any]

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "TutorFacingTeachingContent":
        return cls(
            objective_text=_require_str(
                payload.get("objective_text"), "tutor_content.objective_text"
            ),
            ordered_concept_path=_ensure_string_list(
                payload.get("ordered_concept_path"),
                "tutor_content.ordered_concept_path",
            ),
            nodes=[dict(item) for item in (payload.get("nodes") or [])],
            edges=[dict(item) for item in (payload.get("edges") or [])],
            integration=dict(payload.get("integration") or {}),
            internal_grounding=dict(payload.get("internal_grounding") or {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "objective_text": self.objective_text,
            "ordered_concept_path": list(self.ordered_concept_path),
            "nodes": [dict(item) for item in self.nodes],
            "edges": [dict(item) for item in self.edges],
            "integration": dict(self.integration),
            "internal_grounding": dict(self.internal_grounding),
        }


@dataclass(frozen=True)
class UnsupportedClaimIssue:
    claim_text: str
    reason: str

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "UnsupportedClaimIssue":
        return cls(
            claim_text=_require_str(
                payload.get("claim_text"), "unsupported_claim.claim_text"
            ),
            reason=_require_str(payload.get("reason"), "unsupported_claim.reason"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {"claim_text": self.claim_text, "reason": self.reason}


@dataclass(frozen=True)
class RiskyExampleIssue:
    text: str
    reason: str

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "RiskyExampleIssue":
        return cls(
            text=_require_str(payload.get("text"), "risky_example.text"),
            reason=_require_str(payload.get("reason"), "risky_example.reason"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {"text": self.text, "reason": self.reason}


@dataclass(frozen=True)
class NodeValidationCheck:
    node_id: str
    status: str
    unsupported_claims: List[UnsupportedClaimIssue] = field(default_factory=list)
    risky_examples: List[RiskyExampleIssue] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "NodeValidationCheck":
        status = _require_str(payload.get("status"), "node_check.status")
        if status not in {"pass", "revise", "fail"}:
            raise ValueError(f"Unsupported node_check.status: {status}")
        return cls(
            node_id=_require_str(payload.get("node_id"), "node_check.node_id"),
            status=status,
            unsupported_claims=[
                UnsupportedClaimIssue.from_dict(item)
                for item in (payload.get("unsupported_claims") or [])
            ],
            risky_examples=[
                RiskyExampleIssue.from_dict(item)
                for item in (payload.get("risky_examples") or [])
            ],
            notes=[str(item).strip() for item in (payload.get("notes") or []) if str(item).strip()],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "status": self.status,
            "unsupported_claims": [item.to_dict() for item in self.unsupported_claims],
            "risky_examples": [item.to_dict() for item in self.risky_examples],
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class EdgeValidationIssue:
    field: str
    reason: str

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "EdgeValidationIssue":
        return cls(
            field=_require_str(payload.get("field"), "edge_issue.field"),
            reason=_require_str(payload.get("reason"), "edge_issue.reason"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {"field": self.field, "reason": self.reason}


@dataclass(frozen=True)
class EdgeValidationCheck:
    from_node: str
    to_node: str
    status: str
    issues: List[EdgeValidationIssue] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "EdgeValidationCheck":
        status = _require_str(payload.get("status"), "edge_check.status")
        if status not in {"pass", "revise", "fail"}:
            raise ValueError(f"Unsupported edge_check.status: {status}")
        return cls(
            from_node=_require_str(payload.get("from"), "edge_check.from"),
            to_node=_require_str(payload.get("to"), "edge_check.to"),
            status=status,
            issues=[
                EdgeValidationIssue.from_dict(item)
                for item in (payload.get("issues") or [])
            ],
            notes=[str(item).strip() for item in (payload.get("notes") or []) if str(item).strip()],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from": self.from_node,
            "to": self.to_node,
            "status": self.status,
            "issues": [item.to_dict() for item in self.issues],
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class IntegrationValidationCheck:
    status: str
    issues: List[EdgeValidationIssue] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "IntegrationValidationCheck":
        status = _require_str(payload.get("status"), "integration_check.status")
        if status not in {"pass", "revise", "fail"}:
            raise ValueError(f"Unsupported integration_check.status: {status}")
        return cls(
            status=status,
            issues=[
                EdgeValidationIssue.from_dict(item)
                for item in (payload.get("issues") or [])
            ],
            notes=[str(item).strip() for item in (payload.get("notes") or []) if str(item).strip()],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "issues": [item.to_dict() for item in self.issues],
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class ClaimValidationCheck:
    claim_id: str
    status: str
    reason: str = ""
    action: str = ""

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "ClaimValidationCheck":
        status = _require_str(payload.get("status"), "claim_check.status")
        if status not in {"pass", "revise", "fail"}:
            raise ValueError(f"Unsupported claim_check.status: {status}")
        return cls(
            claim_id=_require_str(payload.get("claim_id"), "claim_check.claim_id"),
            status=status,
            reason=str(payload.get("reason") or "").strip(),
            action=str(payload.get("action") or "").strip(),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "status": self.status,
            "reason": self.reason,
            "action": self.action,
        }


@dataclass(frozen=True)
class EdgeRepairTarget:
    from_node: str
    to_node: str

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "EdgeRepairTarget":
        return cls(
            from_node=_require_str(payload.get("from"), "repair_edge.from"),
            to_node=_require_str(payload.get("to"), "repair_edge.to"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {"from": self.from_node, "to": self.to_node}


@dataclass(frozen=True)
class RepairTargets:
    node_ids: List[str] = field(default_factory=list)
    edge_ids: List[EdgeRepairTarget] = field(default_factory=list)
    integration: bool = False

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "RepairTargets":
        return cls(
            node_ids=[str(item).strip() for item in (payload.get("node_ids") or []) if str(item).strip()],
            edge_ids=[
                EdgeRepairTarget.from_dict(item)
                for item in (payload.get("edge_ids") or [])
            ],
            integration=bool(payload.get("integration", False)),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_ids": list(self.node_ids),
            "edge_ids": [item.to_dict() for item in self.edge_ids],
            "integration": self.integration,
        }


@dataclass(frozen=True)
class GroundingValidationArtifact:
    objective_text: str
    overall_status: str
    node_checks: List[NodeValidationCheck]
    edge_checks: List[EdgeValidationCheck]
    integration_check: IntegrationValidationCheck
    repair_targets: RepairTargets
    claim_checks: List[ClaimValidationCheck] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "GroundingValidationArtifact":
        overall_status = _require_str(
            payload.get("overall_status"), "validation.overall_status"
        )
        if overall_status not in {"pass", "revise", "fail"}:
            raise ValueError(
                f"Unsupported validation.overall_status: {overall_status}"
            )
        artifact = cls(
            objective_text=_require_str(
                payload.get("objective_text"), "validation.objective_text"
            ),
            overall_status=overall_status,
            node_checks=[
                NodeValidationCheck.from_dict(item)
                for item in (payload.get("node_checks") or [])
            ],
            edge_checks=[
                EdgeValidationCheck.from_dict(item)
                for item in (payload.get("edge_checks") or [])
            ],
            integration_check=IntegrationValidationCheck.from_dict(
                dict(payload.get("integration_check") or {})
            ),
            repair_targets=RepairTargets.from_dict(
                dict(payload.get("repair_targets") or {})
            ),
            claim_checks=[
                ClaimValidationCheck.from_dict(item)
                for item in (payload.get("claim_checks") or [])
            ],
        )
        return artifact

    def to_dict(self) -> Dict[str, Any]:
        return {
            "objective_text": self.objective_text,
            "overall_status": self.overall_status,
            "node_checks": [item.to_dict() for item in self.node_checks],
            "edge_checks": [item.to_dict() for item in self.edge_checks],
            "integration_check": self.integration_check.to_dict(),
            "repair_targets": self.repair_targets.to_dict(),
            "claim_checks": [item.to_dict() for item in self.claim_checks],
        }


@dataclass(frozen=True)
class TeachingGraphContentArtifact:
    objective_text: str
    graph: TeachingGraphArtifact
    node_evidence: NodeEvidenceArtifact
    node_content: NodeContentArtifact
    edge_integration: EdgeIntegrationArtifact
    validation: GroundingValidationArtifact
    evidence_cards: Optional[EvidenceCardSet] = None
    claim_ledger: Optional[ClaimLedgerArtifact] = None
    tutor_facing_content: Optional[TutorFacingTeachingContent] = None

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "objective_text": self.objective_text,
            "graph": self.graph.to_dict(),
            "node_evidence": self.node_evidence.to_dict(),
            "node_content": self.node_content.to_dict(),
            "edge_integration": self.edge_integration.to_dict(),
            "validation": self.validation.to_dict(),
        }
        if self.evidence_cards is not None:
            payload["evidence_cards"] = self.evidence_cards.to_dict()
        if self.claim_ledger is not None:
            payload["claim_ledger"] = self.claim_ledger.to_dict()
        if self.tutor_facing_content is not None:
            payload["tutor_facing_content"] = self.tutor_facing_content.to_dict()
        return payload
