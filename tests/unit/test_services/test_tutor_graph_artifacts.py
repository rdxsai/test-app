import pytest

from question_app.services.tutor.artifacts import (
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
