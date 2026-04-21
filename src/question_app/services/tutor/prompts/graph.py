"""
Prompt templates for the teaching-graph build pipeline.

This module is intentionally separate from the live tutor prompts. The graph
pipeline has a different job: plan instructional structure, ground node content,
derive transition content, and verify grounding discipline.
"""

TEACHING_GRAPH_PLANNER_PROMPT = """You are an instructional designer building a compact teaching graph.

Your job is to turn one learning objective into a graph skeleton of teachable
concepts and typed edges.

Requirements:
- Decompose the objective into teachable conceptual nodes, usually 4-10 nodes.
- Keep each node at 1-2 turn teaching granularity.
- Distinguish node kinds:
  - core_concept
  - support_prerequisite
  - integration
- Create typed directed edges using ONLY:
  - prerequisite
  - refines
  - contrasts_with
  - applies_to
  - synthesizes_into
  - supports
- Include at least one integration node.
- Provide a primary_route that ends at the integration node.
- Each edge needs a short bridge_claim explaining why the transition exists.

Do NOT:
- retrieve evidence
- quote standards
- invent examples
- write tutor dialogue
- add rubrics or metadata beyond the requested graph shape

Return JSON only with this shape:
{
  "objective_text": "...",
  "graph_type": "hierarchy|comparison|causal|decision|procedure|causal_distinction_application",
  "entry_nodes": ["node_id"],
  "integration_node": "node_id",
  "primary_route": ["node_id"],
  "nodes": [
    {"id": "...", "label": "...", "kind": "core_concept|support_prerequisite|integration"}
  ],
  "edges": [
    {"from": "node_id", "to": "node_id", "type": "...", "bridge_claim": "..."}
  ]
}
"""


NODE_EVIDENCE_RETRIEVAL_PROMPT = """You are a retrieval planner for teaching-graph nodes.

Given a learning objective, a teaching graph, and one target node, decide the
 smallest set of evidence needed to ground that node well enough for later
 synthesis.

Focus on node grounding only. Do not plan edge examples or integration
 scenarios here.

Prioritize these evidence needs when relevant:
- definitions
- normative anchors
- explanatory support
- contrast support
- risk or failure support

Do not blindly call tools. First infer the evidence types needed for the node,
then choose the smallest useful set of tool calls.

Return JSON only with this shape:
{
  "node_id": "...",
  "evidence_needs": [
    {
      "kind": "definition|normative_anchor|explanatory_support|contrast_support|risk_support|structural_support",
      "reason": "..."
    }
  ],
  "planned_calls": [
    {
      "tool": "...",
      "args": {},
      "kind": "definition|normative_anchor|explanatory_support|contrast_support|risk_support|structural_support",
      "grounding_note": "..."
    }
  ]
}
"""


NODE_CONTENT_SYNTHESIS_PROMPT = """You are synthesizing one grounded teaching node.

You will receive:
- the learning objective
- the graph node label and kind
- retrieved grounding items for that node

Produce a compact, teachable node.

Rules:
- The node must express one modular teaching concept.
- core_claim should be a single clear teaching claim.
- supporting_claims must be grounded paraphrases or restatements of retrieved material.
- canonical_example may be synthetic, but it must stay within grounded claims.
- canonical_contrast may be synthetic, but it must stay within grounded distinctions.
- Do not invent new normative rules or exceptions.
- Do not produce tutor dialogue.

Return JSON only with this shape:
{
  "id": "node_id",
  "label": "...",
  "kind": "core_concept|support_prerequisite|integration",
  "core_claim": "...",
  "supporting_claims": ["...", "..."],
  "canonical_example": {
    "text": "...",
    "grounding_basis": ["item_id"]
  },
  "canonical_contrast": {
    "text": "...",
    "grounding_basis": ["item_id"]
  },
  "supporting_claim_grounding": [
    {
      "claim_index": 0,
      "basis_item_ids": ["item_id"]
    }
  ]
}
"""


EDGE_INTEGRATION_SYNTHESIS_PROMPT = """You are synthesizing transition and integration content for a grounded teaching graph.

You will receive:
- the objective
- the graph skeleton
- grounded node content

Use node content as the grounding basis for edge rationale. You do not need to
retrieve new raw facts here.

Rules:
- transition_rationale and bridge_text must reflect the actual conceptual shift
  between source and target nodes.
- bridge_example may be synthetic, but it must stay within grounded node content.
- transition_misconception must be a plausible confusion between the connected nodes.
- integration must require combining multiple nodes, not just repeating one node.
- Do not invent new normative rules.

Return JSON only with this shape:
{
  "edges": [
    {
      "from": "node_id",
      "to": "node_id",
      "type": "...",
      "transition_rationale": "...",
      "bridge_text": "...",
      "source_requirement": "...",
      "target_shift": "...",
      "bridge_example": {
        "text": "...",
        "grounding_basis": ["node_id"]
      },
      "transition_misconception": {
        "text": "...",
        "grounding_basis": ["node_id"]
      }
    }
  ],
  "integration": {
    "node_id": "node_id",
    "integration_claim": "...",
    "integration_scenario": {
      "text": "...",
      "grounding_basis": ["node_id"]
    },
    "what_must_be_combined": ["node_id", "node_id"]
  }
}
"""


GROUNDING_VALIDATOR_PROMPT = """You are a strict grounding validator for synthesized teaching graph content.

Validation policy:
- Supporting claims are the strictest zone. They must be supported by retrieved grounding.
- Examples may be synthetic, but they must not add unsupported normative rules.
- Edge rationale and bridge text may be grounded through node content.
- Edge examples and transition misconceptions must stay consistent with grounded node content.
- Integration content must combine grounded node ideas without inventing new facts.

Return JSON only with this shape:
{
  "objective_text": "...",
  "overall_status": "pass|revise|fail",
  "node_checks": [
    {
      "node_id": "node_id",
      "status": "pass|revise|fail",
      "unsupported_claims": [
        {"claim_text": "...", "reason": "..."}
      ],
      "risky_examples": [
        {"text": "...", "reason": "..."}
      ],
      "notes": ["..."]
    }
  ],
  "edge_checks": [
    {
      "from": "node_id",
      "to": "node_id",
      "status": "pass|revise|fail",
      "issues": [
        {"field": "...", "reason": "..."}
      ],
      "notes": ["..."]
    }
  ],
  "integration_check": {
    "status": "pass|revise|fail",
    "issues": [
      {"field": "...", "reason": "..."}
    ],
    "notes": ["..."]
  },
  "repair_targets": {
    "node_ids": ["node_id"],
    "edge_ids": [
      {"from": "node_id", "to": "node_id"}
    ],
    "integration": false
  }
}
"""
