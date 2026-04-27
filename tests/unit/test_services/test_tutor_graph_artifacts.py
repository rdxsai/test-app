import pytest

from question_app.services.tutor.artifacts import (
    ClaimLedgerArtifact,
    EvidenceCardSet,
    GroundingValidationArtifact,
    NodeContentArtifact,
    NodeEvidenceArtifact,
    TeachingGraphArtifact,
)


def test_teaching_graph_artifact_parses_and_validates():
    artifact = TeachingGraphArtifact.from_dict(
        {
            "objective_text": "Explain WCAG structure",
            "graph_type": "hierarchy",
            "entry_nodes": ["n1"],
            "integration_node": "n3",
            "primary_route": ["n1", "n2", "n3"],
            "nodes": [
                {"id": "n1", "label": "Principles exist", "kind": "core_concept"},
                {"id": "n2", "label": "Guidelines sit under principles", "kind": "core_concept"},
                {"id": "n3", "label": "Integrated structure", "kind": "integration"},
            ],
            "edges": [
                {
                    "from": "n1",
                    "to": "n2",
                    "type": "prerequisite",
                    "bridge_claim": "The learner needs the top level before the middle level.",
                },
                {
                    "from": "n2",
                    "to": "n3",
                    "type": "synthesizes_into",
                    "bridge_claim": "The learner combines the layers into one hierarchy.",
                },
            ],
        }
    )

    assert artifact.integration_node == "n3"
    assert artifact.primary_route[-1] == "n3"
    assert artifact.to_dict()["graph_type"] == "hierarchy"


def test_teaching_graph_accepts_decision_application_and_teachable_claim():
    artifact = TeachingGraphArtifact.from_dict(
        {
            "objective_text": "Apply ARIA rules",
            "graph_type": "decision_application",
            "entry_nodes": ["n1"],
            "integration_node": "n2",
            "primary_route": ["n1", "n2"],
            "nodes": [
                {
                    "id": "n1",
                    "label": "Native HTML first",
                    "kind": "core_concept",
                    "teachable_claim": "Prefer native HTML when it works.",
                },
                {"id": "n2", "label": "Apply the process", "kind": "integration"},
            ],
            "edges": [
                {
                    "from": "n1",
                    "to": "n2",
                    "type": "synthesizes_into",
                    "bridge_claim": "The native-first check carries into final application.",
                }
            ],
        }
    )

    assert artifact.graph_type == "decision_application"
    assert artifact.nodes[0].teachable_claim == "Prefer native HTML when it works."


def test_teaching_graph_artifact_rejects_primary_route_without_integration():
    with pytest.raises(ValueError):
        TeachingGraphArtifact.from_dict(
            {
                "objective_text": "Explain WCAG structure",
                "graph_type": "hierarchy",
                "entry_nodes": ["n1"],
                "integration_node": "n3",
                "primary_route": ["n1", "n2"],
                "nodes": [
                    {"id": "n1", "label": "Principles exist", "kind": "core_concept"},
                    {"id": "n2", "label": "Guidelines exist", "kind": "core_concept"},
                    {"id": "n3", "label": "Integrated structure", "kind": "integration"},
                ],
                "edges": [
                    {
                        "from": "n1",
                        "to": "n2",
                        "type": "prerequisite",
                        "bridge_claim": "One leads to the next.",
                    }
                ],
            }
        )


def test_node_content_artifact_requires_grounding_for_each_supporting_claim():
    with pytest.raises(ValueError):
        NodeContentArtifact.from_dict(
            {
                "objective_text": "Explain WCAG structure",
                "nodes": [
                    {
                        "id": "n1",
                        "label": "Principles exist",
                        "kind": "core_concept",
                        "core_claim": "WCAG has top-level principles.",
                        "supporting_claims": [
                            "Principles are the broadest layer.",
                            "There are four of them.",
                        ],
                        "canonical_example": {
                            "text": "Perceivable is one principle.",
                            "grounding_basis": ["item-1"],
                        },
                        "canonical_contrast": {
                            "text": "A conformance level is not a principle.",
                            "grounding_basis": ["item-2"],
                        },
                        "supporting_claim_grounding": [
                            {"claim_index": 0, "basis_item_ids": ["item-1"]}
                        ],
                    }
                ],
            }
        )


def test_node_evidence_artifact_requires_retrieved_items():
    with pytest.raises(ValueError):
        NodeEvidenceArtifact.from_dict(
            {
                "objective_text": "Explain WCAG structure",
                "graph_summary": {"graph_type": "hierarchy", "node_ids": ["n1"]},
                "node_evidence": [
                    {
                        "node_id": "n1",
                        "grounding_strength": "adequate",
                        "coverage_summary": {"has_definition_support": True},
                        "source_tools_used": [],
                        "retrieved_items": [],
                    }
                ],
            }
        )


def test_node_evidence_accepts_new_graph_grounding_kinds():
    artifact = NodeEvidenceArtifact.from_dict(
        {
            "objective_text": "Apply ARIA rules",
            "graph_summary": {"graph_type": "decision_application", "node_ids": ["n1"]},
            "node_evidence": [
                {
                    "node_id": "n1",
                    "grounding_strength": "adequate",
                    "coverage_summary": {},
                    "source_tools_used": [{"tool": "search_techniques", "args": {}}],
                    "retrieved_items": [
                        {
                            "item_id": "item-1",
                            "tool": "search_techniques",
                            "args": {"query": "aria button"},
                            "kind": "implementation_support",
                            "title": "ARIA button technique",
                            "content": "Technique details",
                            "grounding_note": "Supports implementation example.",
                        },
                        {
                            "item_id": "item-2",
                            "tool": "get_technique",
                            "args": {"id": "F1"},
                            "kind": "failure_support",
                            "title": "Failure",
                            "content": "Failure details",
                            "grounding_note": "Supports failure example.",
                        },
                    ],
                }
            ],
        }
    )

    assert artifact.node_evidence[0].retrieved_items[0].kind == "implementation_support"


def test_evidence_card_set_rejects_unknown_raw_evidence_id():
    with pytest.raises(ValueError):
        EvidenceCardSet.from_dict(
            {
                "objective_text": "Apply ARIA rules",
                "raw_evidence": [
                    {
                        "raw_evidence_id": "raw-1",
                        "target_refs": ["node:n1"],
                        "source": "wcag_mcp",
                        "tool": "get_criterion",
                        "args": {"ref_id": "4.1.2"},
                        "status": "HIT",
                        "chars": 100,
                        "raw_result": "raw text",
                    }
                ],
                "evidence_cards": [
                    {
                        "evidence_id": "ev-1",
                        "raw_evidence_id": "raw-missing",
                        "target_refs": ["node:n1"],
                        "evidence_type": "normative_anchor",
                        "source_ref": "WCAG 4.1.2",
                        "title": "Name, Role, Value",
                        "usable_facts": [
                            {
                                "fact_id": "fact-1",
                                "text": "UI components need name and role.",
                                "supports_claim_types": ["normative_requirement"],
                            }
                        ],
                    }
                ],
            }
        )


def test_claim_ledger_requires_evidence_for_high_risk_claims():
    with pytest.raises(ValueError):
        ClaimLedgerArtifact.from_dict(
            {
                "objective_text": "Apply ARIA rules",
                "claims": [
                    {
                        "claim_id": "claim-1",
                        "scope": {"type": "node", "id": "n1", "field": "core_claim"},
                        "text": "Interactive ARIA controls need keyboard support.",
                        "claim_type": "keyboard_requirement",
                        "requires_evidence": True,
                        "evidence_ids": [],
                    }
                ],
            }
        )


def test_claim_ledger_rejects_unknown_evidence_reference():
    with pytest.raises(ValueError):
        ClaimLedgerArtifact.from_dict(
            {
                "objective_text": "Apply ARIA rules",
                "claims": [
                    {
                        "claim_id": "claim-1",
                        "scope": {"type": "node", "id": "n1", "field": "core_claim"},
                        "text": "Interactive controls need names.",
                        "claim_type": "accessible_name_requirement",
                        "requires_evidence": True,
                        "evidence_ids": ["ev-missing"],
                    }
                ],
            },
            known_evidence_ids={"ev-known"},
        )


def test_grounding_validation_artifact_parses_repair_targets():
    artifact = GroundingValidationArtifact.from_dict(
        {
            "objective_text": "Explain WCAG structure",
            "overall_status": "revise",
            "node_checks": [
                {
                    "node_id": "n1",
                    "status": "revise",
                    "unsupported_claims": [
                        {
                            "claim_text": "There are five principles.",
                            "reason": "Not supported by retrieved evidence.",
                        }
                    ],
                    "risky_examples": [],
                    "notes": ["Fix the claim count."],
                }
            ],
            "edge_checks": [],
            "integration_check": {
                "status": "pass",
                "issues": [],
                "notes": [],
            },
            "repair_targets": {
                "node_ids": ["n1"],
                "edge_ids": [{"from": "n1", "to": "n2"}],
                "integration": False,
            },
        }
    )

    assert artifact.overall_status == "revise"
    assert artifact.repair_targets.node_ids == ["n1"]
    assert artifact.repair_targets.edge_ids[0].to_node == "n2"
