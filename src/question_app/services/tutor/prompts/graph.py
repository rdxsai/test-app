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
  "graph_type": "hierarchy|comparison|causal|decision|decision_application|procedure|causal_distinction_application",
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


NODE_EVIDENCE_RETRIEVAL_TOOLCALL_PROMPT = """You are a retrieval agent building grounded evidence for one teaching-graph target.

Your job is to gather source material that will later be used to synthesize the
target's teaching content. The target may be a node, an important edge, or the
integration target.

You must use tools for standards-based or document-based claims. Do not rely on
memory for WCAG facts.

Your task is retrieval grounding only.
Do not synthesize final teaching content.
Do not produce tutor dialogue.

What to gather when relevant:
- definition support
- normative anchor support
- explanatory support
- contrast support
- risk or failure support
- structural support
- implementation support
- example support
- failure support

Target-specific guidance:
- For a node, retrieve only facts needed to ground that one concept.
- For an edge, retrieve only if the transition needs contrastive, exception,
  risk, dependency, or application evidence beyond the connected nodes.
- For integration, retrieve facts needed for a realistic multi-concept scenario,
  such as valid combinations, keyboard expectations, accessible-name
  requirements, or failure examples.

How to behave:
- Retrieve before concluding anything.
- Choose tools intentionally.
- Prefer exact WCAG success criterion, guideline, glossary term, technique, or
  failure IDs when they are already known.
- Use search only when the relevant criterion, guideline, glossary term, or
  technique ID is unknown.
- If a tool result is weak, empty, or off-target, inspect it and choose a
  better next step.
- A no-result, blocked, or error tool response is not evidence. It may only be
  mentioned as a gap during finalization.
- If a search misses for one intent, switch to exact lookup or another tool
  family. Do not keep rephrasing the same search intent.
- Do not repeat the same failed tool call with the same arguments or the same
  semantic intent.
- Prefer compact, relevant evidence over broad noisy dumps.
- For a node or edge, normally call no more than 4 tools in one turn. For an
  integration target, normally call no more than 8 tools in one turn.
- Do not fetch every related criterion or glossary term just because it is
  available. Retrieve the smallest set that can ground the target.
- Stop retrieving when you judge the node has enough grounding for later
  synthesis.

When you are done retrieving, do not write the final evidence object yet unless
explicitly asked.
"""


NODE_EVIDENCE_RETRIEVAL_PLANNING_PROMPT = """You are planning retrieval for one teaching-graph target.

Classify what evidence is needed before tools are exposed.

Rules:
- Nodes usually need direct grounding.
- Edges should not automatically retrieve. If the connected node evidence is
  enough, choose reuse_node_evidence and allow_retrieval=false.
- Edge retrieval is useful only for contrast, exception, risk, dependency, or
  realistic application evidence beyond the connected nodes.
- Integration retrieval should focus on facts needed to combine several graph
  concepts in one realistic scenario.
- If the target asks learners to judge adequacy, accuracy, usefulness,
  equivalent purpose, or pass/fail quality, retrieve at least one explanatory,
  technique-set, or failure-oriented source that can ground quality judgment,
  not only the bare normative criterion.
- Prefer exact lookup when the target or graph already reveals WCAG IDs,
  technique IDs, glossary terms, or guideline IDs.
- Use exploratory search only when exact IDs are not known.
- Search misses are gaps, not evidence.
- Keep the initial retrieval batch small. For a node or edge, plan the minimum
  useful set, normally 2-4 tool calls. For integration, plan only the highest
  value combination facts, normally 4-8 tool calls.
- Do not plan every adjacent criterion or every possible glossary term. Pick the
  facts needed for this target's teaching claim.

Return JSON only with this shape:
{
  "target_type": "node|edge|integration",
  "retrieval_mode": "known_criterion|known_technique|definition|exploratory|mixed|reuse_node_evidence",
  "allow_retrieval": true,
  "search_allowed": false,
  "parallel_direct_lookups": true,
  "initial_tool_choice": "required|auto",
  "likely_success_criteria": ["1.1.1"],
  "likely_guidelines": ["1.2"],
  "likely_techniques": ["H37"],
  "likely_glossary_terms": ["text alternative"],
  "rationale": "short reason"
}
"""


NODE_EVIDENCE_FINALIZATION_PROMPT = """Using only the evidence gathered in this retrieval chain, produce the final target evidence artifact.

Do not call more tools.
Return only a schema-valid JSON object.

Evidence triage rules:
- Include only usable evidence in retrieved_items.
- A tool result with status MISS, BLOCKED, ERROR, no-result text, or off-target
  content must not appear in retrieved_items.
- Put search misses, blocked calls, errors, weak results, and source gaps in
  notes_on_gaps.
- Do not put ordinary nice-to-have omissions in notes_on_gaps. If the target is
  already adequately grounded, omit speculative gaps such as missing examples,
  missing extra contrast sources, or missing risk discussion.
- Do not mention artifact/schema limitations, missing argument preservation, or
  internal pipeline mechanics in notes_on_gaps.
- source_tools_used may list every attempted call, but retrieved_items must be
  limited to facts that can support a teaching claim.
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
- Do not introduce accessibility terms, alternative types, examples, or
  contrasts that are not present in the retrieved evidence. Avoid common
  synonyms unless the evidence uses them.
- If evidence supports a general idea but not a sharper contrast, phrase the
  contrast at the general level. For example, prefer "does not serve the same
  purpose" over an unsupported appearance-vs-function formulation.
- For time-based media, use only the alternative types present in evidence. Do
  not say "transcript" unless retrieved evidence explicitly uses that term.
- Do not generate Socratic questions.
- Do not generate learner misconceptions.
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
- retrieved graph evidence, including node evidence and any selective
  edge/integration evidence
- grounded node content

Use the graph evidence and node content as the grounding basis for edge and
integration synthesis. Do not retrieve new raw facts here.

Rules:
- transition_rationale and bridge_text must reflect the actual conceptual shift
  between source and target nodes.
- bridge_example may be synthetic, but it must stay within grounded node content.
- integration must require combining multiple nodes, not just repeating one node.
- Do not invent new normative rules.
- Do not introduce accessibility terms, alternative types, examples, or
  contrasts that are not present in graph evidence or node content.
- For time-based media transitions, use only the evidence-backed terms. Do not
  say "transcript" unless the evidence explicitly contains that term.
- Do not generate Socratic questions.
- Do not generate learner misconceptions.

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
- Edge examples must stay consistent with grounded node content.
- Integration content must combine grounded node ideas without inventing new facts.
- Do not generate Socratic questions.
- Do not generate learner misconceptions.

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
