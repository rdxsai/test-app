================================================================================
STEP 1: GENERATE TEACHING PLAN
================================================================================
Objective: Explain the structure of WCAG 2.2, including the POUR principles, guidelines, success criteria, and conformance levels A, AA, and AAA.

Time: 42.1s | Tokens: 884/3316 | Output: 12076 chars

1. objective_text
Explain the structure of WCAG 2.2, including the POUR principles, guidelines, success criteria, and conformance levels A, AA, and AAA.

2. plain_language_goal
Understand how WCAG 2.2 is organized—from its four high-level principles down to testable requirements—and what A, AA, and AAA conformance levels mean and how they relate to those requirements.

3. mastery_definition
A learner has mastered this objective if they can:
- Identify and name the four WCAG principles (POUR) and describe their role as top-level categories.
- Distinguish between guidelines and success criteria and state which layer is testable.
- Place a given item (e.g., “1.1.1 Non-text Content”) correctly within the hierarchy: Principle → Guideline → Success Criterion.
- Explain how conformance levels (A, AA, AAA) apply to success criteria and what it means to conform at Level A vs AA vs AAA (including the “includes all lower levels” rule).
- Given an example success criterion, correctly state its conformance level and how it affects overall conformance claims.
- Correct at least one common misconception (e.g., that guidelines are testable or that AAA is generally required).

4. objective_type
- terminology
- hierarchy/structure
- conceptual understanding
- classification
- comparison

5. prerequisite_knowledge
- essential prerequisites:
  - Awareness that WCAG is a W3C standard for web content accessibility.
  - Basic idea of what “conformance” means in standards (meeting stated requirements).
  - Familiarity with what a “web page” or “web content” is.
- helpful but nonessential prerequisites:
  - Difference between normative requirements and non-normative guidance.
  - Awareness that there are WCAG versions (2.0, 2.1, 2.2) and that 2.2 builds on earlier versions.
  - Examples of specific accessibility issues (e.g., alternative text, keyboard focus) for anchoring examples.

6. prerequisite_gap_policy
- If the learner lacks essential prerequisites:
  - Briefly elicit their current understanding with a diagnostic question (“What is WCAG for?”).
  - Provide a concise, 1–2 sentence primer on WCAG as a standard that sets testable requirements for web content accessibility and what “conformance” means.
  - Confirm understanding with a quick check before proceeding to structure.

7. concept_decomposition
- WCAG purpose (one-sentence refresher to anchor structure).
- The hierarchical layers:
  1) Principles (POUR) as the top-level categories.
  2) Guidelines under each principle (broad goals).
  3) Success Criteria (SC) under each guideline (testable requirements).
- Testability distinction: guidelines vs success criteria.
- SC numbering scheme (e.g., 1.1.1) and how it encodes principle and guideline.
- Conformance levels assigned to success criteria (A, AA, AAA).
- Conformance claims: what it means to conform at A/AA/AAA and the “includes all lower” rule.
- Scope of conformance (typically per web page).
- Normative vs non-normative materials (core spec vs Understanding/Techniques) as part of structure.
- WCAG 2.2 continuity with 2.x family (backwards-compatible layering; added/updated SCs but same structure).

8. dependency_order
- Anchor purpose → Hierarchical layers → Testability distinction → Numbering scheme → Conformance levels → Conformance claims and “includes all lower” rule → Scope of conformance → Normative vs non-normative → Continuity across versions.
- Dependencies and rationale:
  - Purpose anchors why structure matters.
  - Understanding layers (Principles → Guidelines → SC) is foundational before conformance.
  - Testability distinction clarifies why SC carry levels and guidelines do not.
  - Numbering scheme helps learners place items within the structure.
  - Conformance levels make sense only after SC are understood.
  - Conformance claims build on the levels and clarify their implications.
  - Scope clarifies what conformance applies to, contextualizing the structure in practice.
  - Normative vs non-normative explains which documents define structure vs provide guidance.
  - Version continuity prevents confusion about changes while reinforcing structure stability.

9. likely_misconceptions
- “Guidelines are testable” (confusing guidelines with success criteria).
- “You can pick and choose SC within a level” (not realizing AA includes all A-level SC).
- “AAA is required by default” or “AAA is better so always required” (conflating ambition with common practice).
- “Conformance is for a whole site only” (not recognizing per-page scope of claims).
- “Techniques are required to pass SC” (confusing non-normative techniques with normative SC).
- “WCAG 2.2 changed the entire structure from 2.1” (it didn’t; same layered structure).
- “Passing AA means you don’t need to meet A-level SC separately” (AA already includes A; misunderstanding persists).
- “SC levels indicate importance or priority” (they indicate testability difficulty/user impact and feasibility, not a strict priority order).
- “Numbering is arbitrary” (it encodes principle and guideline).

10. explanation_vs_question_strategy
- WCAG purpose: diagnostic question → brief explanation. Why: gauge baseline and keep primer minimal.
- Hierarchical layers (Principles → Guidelines → SC): guided questioning with a simple visual/analogy → brief explanation. Why: structure recognition benefits from construction by the learner.
- Testability distinction: contrastive example. Why: showing a guideline alongside an SC highlights the difference.
- Numbering scheme: brief explanation + quick identification exercise. Why: a small rule to learn, then immediate application.
- Conformance levels per SC: worked example with one SC at A and another at AA/AAA. Why: concrete mapping reduces abstraction.
- Conformance claims and “includes all lower” rule: guided questioning with a ladder metaphor. Why: elicits reasoning about set inclusion.
- Scope of conformance: diagnostic question → brief explanation. Why: many assume site-level; quick correction.
- Normative vs non-normative: brief explanation with one example of each. Why: avoids confusion without deep dive.
- Version continuity: brief explanation + single contrast (e.g., a 2.2-added SC). Why: situate 2.2 without overload.

11. socratic_question_goals
- WCAG purpose: diagnose prior knowledge; align on why structure matters.
- Hierarchical layers: check causal understanding; force comparison of broad vs specific.
- Testability distinction: reveal misconception that guidelines are testable; justify which is testable.
- Numbering scheme: check recognition; justify how numbering indicates location.
- Conformance levels: justify why levels attach to SC, not guidelines.
- “Includes all lower” rule: test logical reasoning; ensure understanding of set inclusion.
- Scope of conformance: reveal misconception (site vs page); check application to a specific scenario.
- Normative vs non-normative: check ability to classify a document or example.
- Version continuity: check transfer by placing a 2.2 SC within the existing structure.

12. example_requirements
- Simplest introductory example:
  - A small tree: Perceivable → Guideline “Text Alternatives” → SC 1.1.1 Non-text Content (Level A).
- Contrastive example:
  - Pair “Guideline 1.1 Text Alternatives” (not testable) with “1.1.1 Non-text Content (A)” (testable), and perhaps “1.4 Distinguishable” vs “1.4.3 Contrast (Minimum) (AA)”.
- Borderline/tricky case:
  - Two SC under same guideline with different levels (e.g., 2.4.11 Focus Not Obscured (Minimum) (AA) vs 2.4.12 Focus Not Obscured (Enhanced) (AAA) in WCAG 2.2).
  - Show that a AAA SC exists but is not required for AA conformance.
- Additional example to illustrate numbering:
  - Decode “2.4.7 Focus Visible (AA)” as Principle 2 (Operable) → Guideline 2.4 (Navigable) → SC 7.
- Transfer scenario:
  - Present an unfamiliar SC title from 2.2 (e.g., 2.5.7 Dragging Movements (AA)), ask learner to place it in the hierarchy and state its level and implications for AA conformance.

13. retrieval_requirements
- must-retrieve:
  - Official WCAG 2.2 structure outline: list of four principles (POUR), example guidelines under each, and at least 4–6 example SC with their exact numbering and conformance levels (including one A, one AA, and one AAA).
  - Specific examples for 2.2-added/updated SC that demonstrate level differences under same guideline (e.g., 2.4.11/2.4.12 Focus Not Obscured; 2.5.7 Dragging Movements).
  - Definitions from the WCAG 2.2 conformance section: meaning of conformance levels and the “includes all lower” rule, and typical scope (per page).
  - Clarification of normative vs non-normative docs: identify which are “WCAG 2.2” vs “Understanding WCAG 2.2” vs “Techniques for WCAG 2.2”.
- optional-supporting:
  - A compact visual diagram of the WCAG hierarchy for one principle.
  - Brief notes on version continuity (2.0 → 2.1 → 2.2) emphasizing unchanged structure.
  - One or two common legal/policy references that typically require Level AA (purely to contextualize levels, not to teach policy).

14. assessment_evidence
- Quick understanding checks:
  - Multiple-choice: classify a statement as principle/guideline/success criterion.
  - Identify which item is testable among a pair (guideline vs SC).
- Application task:
  - Given “2.5.7 Dragging Movements (AA)”, place it within the hierarchy and state what conformance level(s) an organization must meet to claim AA.
  - Build a mini outline from a provided SC: name its principle and guideline.
- Transfer task:
  - Given an unfamiliar SC title and number, explain what its level implies for A vs AA vs AAA conformance, and whether it’s required for an AA claim.
- Misconception check:
  - True/false with justification: “Guidelines are testable requirements.” “AA conformance means you’ve met all A-level SC.” “Techniques are required to satisfy SC.”

15. adaptation_notes
- Beginner:
  - Use one principle (Perceivable) as the primary example before showing the full POUR list.
  - Limit to 2–3 SC examples, keep numbering decoding minimal.
  - Spend more time contrasting guideline vs SC and A vs AA.
  - Avoid deep normative vs non-normative discussion; one-sentence mention only.
- Intermediate:
  - Cover all four principles and at least one guideline + SC per principle.
  - Include the numbering scheme and one 2.2-added SC to show continuity.
  - Include a short segment on normative vs non-normative materials.
- Advanced:
  - Add brief notes on conformance claim nuances (e.g., complete processes, accessibility-supported technologies) as structural context without deep dive.
  - Include more tricky cases (AA vs AAA under same guideline) and how organizations set targets.
  - Invite classification of a few items without numbers (by content) to check structural reasoning.

16. boundaries_and_non_goals
- Do not teach how to implement or test specific SC (e.g., contrast ratios, ARIA usage).
- Do not cover the full conformance claim process (accessibility-supported, complete processes, statement formats) beyond basic scope and inclusion rule.
- Do not discuss legal requirements in depth or jurisdictional policy.
- Do not teach WCAG techniques in detail or imply they are mandatory.
- Do not cover non-web ICT or PDFs beyond acknowledging “web content” scope.

17. concise_plan_summary
- Begin with a quick diagnostic and a 1–2 sentence anchor on WCAG’s purpose.
- Build the hierarchy from top (POUR principles) to bottom (testable success criteria), highlighting distinctions.
- Use contrastive examples to separate guidelines (non-testable) from SC (testable).
- Teach the numbering scheme to help learners place items in the structure.
- Introduce conformance levels as properties of SC and explain the “includes all lower” rule for A/AA/AAA claims.
- Clarify scope (per page) and the role of normative vs non-normative documents.
- Use 2.2 examples (e.g., Focus Not Obscured) to illustrate level differences and version continuity.
- Assess through classification, placement, and reasoning about conformance implications, probing common misconceptions.

================================================================================
STEP 2: GENERATE RETRIEVAL PLAN
================================================================================

Time: 51.6s | Tokens: 5031/4431 | Output: 12814 chars

1) retrieval_goal
Support instruction on the WCAG 2.2 structure so the tutor can accurately teach:
- The POUR principles and how guidelines and success criteria (SC) sit beneath them.
- Which layer is testable (SC) versus not (guidelines).
- How SC are numbered and how numbering maps to principle → guideline → SC.
- How conformance levels (A, AA, AAA) attach to SC and the “includes all lower” rule for conformance claims.
- The typical scope of conformance (per web page).
- The distinction between normative requirements (SC) and non-normative techniques/understanding docs.
- Use a small set of concrete SC examples (including WCAG 2.2 additions) to illustrate.

2) instructional_intent_summary
- This lesson centers on hierarchy/structure and conceptual understanding, with light classification and comparison.
- Teach the POUR principles and show guidelines and SC under them.
- Emphasize testability at the SC layer and decode the numbering scheme.
- Explain conformance levels and the roll-up (AA includes all A, AAA includes A+AA+AAA).
- Clarify scope (per page) and differentiate normative SC from informative techniques.
- Use a few WCAG 2.2 examples (e.g., Focus Not Obscured, Dragging Movements).

3) required_information_categories
- structural: To present the WCAG hierarchy (principles → guidelines → SC) and numbering.
- normative: To provide the conformance levels and roll-up rule, and scope of conformance (per page).
- examples: To supply a concise set of SC exemplars with identifiers, levels, and titles (including 2.2 additions).
- techniques: To anchor the “techniques are informative/not required” distinction with a concrete technique reference.
- glossary: To define “conformance” and “web page” for conformance scope and basic terms.
- counts/summary statistics (optional): To quantify SC by level for context (not essential).

4) tool_selection
- structural:
  - list_principles: Retrieve the four principles (POUR) with descriptions.
  - list_guidelines (no filter): Retrieve guidelines across all principles compactly.
  - list_success_criteria (filtered): Retrieve SC lists for select guidelines if needed to show breadth without deep content.
  - get_success_criteria_detail: Retrieve normative text, number, title, and level for selected SC exemplars; avoids heavy “Understanding” docs.
- normative:
  - get_glossary_term("conformance"): Retrieve the conformance definition; may include scope and level descriptions.
  - get_glossary_term("web page"): Retrieve scope definition for per-page conformance.
  - get_full_criterion_context for one anchor SC (e.g., 1.1.1): As fallback/proof source for conformance and normative/informative distinctions in Understanding.
- examples:
  - get_success_criteria_detail for SC: 1.1.1 (A), 1.4.3 (AA), 2.4.11 (AA), 2.4.12 (AAA), 2.5.7 (AA). These cover A/AA/AAA, same-guideline level contrast, and a 2.2 addition.
- techniques:
  - get_technique("G18"): Provide a concrete technique entry to demonstrate “sufficient” technique and that techniques are not required for conformance.
- counts/summary statistics (optional):
  - count_criteria(group_by="level"): Provide high-level numbers for A/AA/AAA distribution (contextual only).
- version continuity (optional):
  - whats_new_in_wcag22: Compact list of added SC to illustrate continuity and new examples.

Why these tools:
- They deliver minimal, high-signal structural and normative anchors without overloading (limit deep docs to one anchor if needed).
- Comply with glossary limitations by avoiding structural terms not present there.

5) planned_tool_calls
Priority order and purpose:

Must-have
1. list_principles()
   - Purpose: Get the POUR principles and descriptions.
   - Instructional value: Top-level hierarchy anchor.

2. list_guidelines()
   - Purpose: Get all guidelines with identifiers/titles under each principle.
   - Instructional value: Mid-level hierarchy; supports “guidelines are not testable” contrast.

3. get_success_criteria_detail("1.1.1")
   - Purpose: Normative text and level for 1.1.1 Non-text Content (A).
   - Instructional value: Foundational A-level example; shows numbering mapping to Principle 1 → Guideline 1.1.

4. get_success_criteria_detail("1.4.3")
   - Purpose: Normative text and level for 1.4.3 Contrast (Minimum) (AA).
   - Instructional value: AA example under Perceivable to contrast A vs AA.

5. get_success_criteria_detail("2.4.11")
   - Purpose: Normative text and level for 2.4.11 Focus Not Obscured (Minimum) (AA) — WCAG 2.2.
   - Instructional value: AA example showing 2.2 additions; pairs with 2.4.12 for level contrast.

6. get_success_criteria_detail("2.4.12")
   - Purpose: Normative text and level for 2.4.12 Focus Not Obscured (Enhanced) (AAA) — WCAG 2.2.
   - Instructional value: AAA contrast under the same guideline.

7. get_success_criteria_detail("2.5.7")
   - Purpose: Normative text and level for 2.5.7 Dragging Movements (AA) — WCAG 2.2.
   - Instructional value: Transfer example and 2.2 continuity.

8. get_glossary_term("conformance")
   - Purpose: Official definition; seek explicit level meanings and roll-up details.
   - Instructional value: Supports conformance level explanation and roll-up rule (if present).

9. get_glossary_term("web page")
   - Purpose: Definition to establish per-page scope of conformance claims.
   - Instructional value: Corrects misconception that conformance is site-only.

10. get_technique("G18")
    - Purpose: Technique details (Sufficient, General) and typical note that techniques are informative/not required.
    - Instructional value: Anchor for techniques vs requirements distinction.

Fallbacks for critical evidence (execute in order only if needed)
11. get_full_criterion_context("1.1.1")
    - Purpose: Access Understanding + techniques context to extract explicit statement that techniques are informative and success criteria are normative; may also reference conformance levels contextually.
    - Instructional value: Strong evidence for normative vs informative and structural placement.

12. search_wcag("conformance level AA requirements all level A criteria")
    - Purpose: Attempt to retrieve text references to roll-up if glossary did not provide; limited effectiveness but required by fallback chain.
    - Instructional value: Satisfy evidence check if other sources fail (last resort per requirements).

Optional supporting
13. count_criteria(group_by="level")
    - Purpose: Provide counts per level.
    - Instructional value: Contextual comparison for levels.

14. whats_new_in_wcag22()
    - Purpose: List of new SC in 2.2.
    - Instructional value: Version continuity anchor.

6) must_have_vs_optional
- Must-have:
  - list_principles
  - list_guidelines
  - get_success_criteria_detail for 1.1.1, 1.4.3, 2.4.11, 2.4.12, 2.5.7
  - get_glossary_term("conformance")
  - get_glossary_term("web page")
  - get_technique("G18")
  - Fallback: get_full_criterion_context("1.1.1") if techniques/requirements distinction or conformance roll-up not evidenced.
  - Fallback: search_wcag("conformance level AA requirements all level A criteria") if roll-up still not evidenced.

- Optional:
  - count_criteria(group_by="level")
  - whats_new_in_wcag22
  - list_success_criteria for a specific guideline to show breadth if needed (e.g., list_success_criteria(guideline="1.4"))

7) exclusion_rules
- Do not retrieve:
  - get_criterion for multiple SC (Understanding docs are heavy; limit to one fallback anchor only if needed).
  - get_full_criterion_context for more than one SC.
  - Deep technique lists (get_techniques_for_criterion, search_techniques broadly) beyond the single “G18” anchor.
  - Detailed conformance claim procedures (e.g., complete processes, accessibility-supported technologies) beyond basic per-page scope and roll-up rule.
  - Implementation details for SC (no testing procedures or measurement specifics).
  - Legal/policy specifics; at most a mention that many policies target AA (no retrieval needed).

8) sufficiency_condition
Stop retrieval when we have:
- The four principles with descriptions.
- A compact list of guidelines across principles.
- Five SC exemplars (1.1.1 A; 1.4.3 AA; 2.4.11 AA; 2.4.12 AAA; 2.5.7 AA) with numbers, titles, and levels via get_success_criteria_detail.
- Glossary definitions for “conformance” and “web page.”
- One concrete technique record (G18) demonstrating techniques are informative/not required.
- Explicit evidence for the AA roll-up rule (AA requires all A+AA) from the conformance definition or fallback, and explicit evidence that techniques are not required (from technique or Understanding).
Once these are verified, cease additional retrieval.

9) required_evidence_checks
a. Conformance roll-up rule
- Target evidence: An explicit statement that Level AA conformance requires meeting all Level A and Level AA SC (and analogous for AAA).
- Primary attempt: get_glossary_term("conformance") — check for the roll-up language.
- Fallback chain (execute in order until found):
  1) search_wcag("conformance requirements level AA must meet all Level A") or equivalent query: "conformance level AA requirements all level A criteria".
  2) get_full_criterion_context("1.1.1") — scan Understanding for conformance discussion referencing levels and roll-up.
  3) If still not found, add search_wcag("WCAG conformance requirement full pages") to surface related references, while noting the tool’s limitations.

b. Techniques vs requirements distinction
- Target evidence: An explicit statement that success criteria are normative conformance requirements and techniques are informative, not required.
- Primary attempt: get_technique("G18") — look for “sufficient” label and any text indicating techniques are informative/not required.
- Fallback chain:
  1) search_wcag("techniques are informative not required for conformance").
  2) get_full_criterion_context("1.1.1") — Understanding often explicitly states techniques are informative and not required for conformance.

If either (a) or (b) is not evidenced after the primary calls, the specific fallback call(s) above become MUST-HAVE before concluding retrieval.

10) evidence_pack_structure
Organize retrieved material for the tutor as:
- hierarchy anchor: list_principles output; list_guidelines output.
- core fact: Each selected SC’s number, title, and conformance level via get_success_criteria_detail.
- official requirement: Glossary “conformance” (and explicit roll-up rule if present).
- definition: Glossary “web page” for scope of conformance.
- contrastive example: Pair of SC under same guideline with different levels (2.4.11 AA vs 2.4.12 AAA).
- simple example: 1.1.1 (A) under Guideline 1.1 as the basic testable SC.
- misconception guard: Technique G18 entry highlighting techniques are informative/not required; any explicit statements from Understanding (if retrieved).
- assessment support: Optional counts by level for quick comparison; whats_new_in_wcag22 for version continuity.

11) adaptation_notes_for_retrieval
- Beginner:
  - Use list_principles and list_guidelines.
  - Limit SC exemplars to 1.1.1 (A), 1.4.3 (AA), and one Focus Not Obscured SC (AA or AAA).
  - Retain glossary “conformance” and “web page”.
  - Keep technique evidence (G18) but avoid any deep Understanding retrieval unless needed for the techniques distinction.
- Intermediate:
  - Include all five SC exemplars (1.1.1, 1.4.3, 2.4.11, 2.4.12, 2.5.7).
  - Optionally add count_criteria(group_by="level") or whats_new_in_wcag22 for context.
- Advanced:
  - Add whats_new_in_wcag22 and optionally count_criteria.
  - If discussing nuance briefly, allow one get_full_criterion_context (1.1.1) to reference normative/informative and conformance notes as structural context.
  - Consider list_success_criteria for one additional guideline to illustrate hierarchy breadth.

12) final_retrieval_summary
- Use list_principles and list_guidelines to anchor the POUR hierarchy and guidelines layer.
- Pull five targeted SC via get_success_criteria_detail to illustrate A, AA, AAA and numbering, including WCAG 2.2 additions and same-guideline level contrasts.
- Retrieve glossary terms “conformance” and “web page” to ground conformance scope and (ideally) the roll-up rule.
- Retrieve one technique (G18) to show techniques are informative and not required; if ambiguous, backstop with get_full_criterion_context for 1.1.1.
- Include explicit checks for the AA roll-up rule and techniques vs requirements; run fallbacks if not evidenced.
- Keep optional enrichment minimal: counts by level and whats_new_in_wcag22 for version continuity.
- Avoid deep Understanding docs except for a single fallback anchor if necessary.
- Stop once hierarchy, exemplar SC, conformance scope and roll-up, and techniques vs requirements are all explicitly evidenced.

================================================================================
STEP 3: EXTRACT TOOL CALLS AS JSON
================================================================================

Time: 19.2s | Tokens: 3148/1649
Extracted 17 tool calls:
  1. [must_have] list_principles({})
  2. [must_have] list_guidelines({})
  3. [must_have] get_success_criteria_detail({"ref_id": "1.1.1"})
  4. [must_have] get_success_criteria_detail({"ref_id": "1.4.3"})
  5. [must_have] get_success_criteria_detail({"ref_id": "2.4.11"})
  6. [must_have] get_success_criteria_detail({"ref_id": "2.4.12"})
  7. [must_have] get_success_criteria_detail({"ref_id": "2.5.7"})
  8. [must_have] get_glossary_term({"term": "conformance"})
  9. [must_have] get_glossary_term({"term": "web page"})
  10. [must_have] get_technique({"id": "G18"})
  11. [fallback] search_wcag({"query": "conformance level AA requirements all level A criteria"})
  12. [fallback] get_full_criterion_context({"ref_id": "1.1.1"})
  13. [fallback] search_wcag({"query": "WCAG conformance requirement full pages"})
  14. [fallback] search_wcag({"query": "techniques are informative not required for conformance"})
  15. [optional] count_criteria({"group_by": "level"})
  16. [optional] whats_new_in_wcag22({})
  17. [optional] list_success_criteria({"guideline": "1.4"})

================================================================================
STEP 4: DETERMINISTIC TOOL EXECUTION
  Glossary blocklist + arg normalization (id<->ref_id) active
================================================================================

[1] [HIT] [must_have] list_principles({}) -> 637 chars
[2] [HIT] [must_have] list_guidelines({}) -> 1550 chars
[3] [HIT] [must_have] get_success_criteria_detail({"ref_id": "1.1.1"}) -> 2021 chars
[4] [HIT] [must_have] get_success_criteria_detail({"ref_id": "1.4.3"}) -> 1000 chars
[5] [HIT] [must_have] get_success_criteria_detail({"ref_id": "2.4.11"}) -> 1059 chars
[6] [HIT] [must_have] get_success_criteria_detail({"ref_id": "2.4.12"}) -> 563 chars
[7] [HIT] [must_have] get_success_criteria_detail({"ref_id": "2.5.7"}) -> 844 chars
[8] [HIT] [must_have] get_glossary_term({"term": "conformance"}) -> 166 chars
[9] [HIT] [must_have] get_glossary_term({"term": "web page"}) -> 1529 chars
[10] [HIT] [must_have] get_technique({"id": "G18"}) -> 424 chars
[11] [HIT] [fallback] search_wcag({"query": "conformance level AA requirements all level A criteria"}) -> 92 chars
[12] [HIT] [fallback] get_full_criterion_context({"ref_id": "1.1.1"}) -> 687 chars
[13] [HIT] [fallback] search_wcag({"query": "WCAG conformance requirement full pages"}) -> 77 chars
[14] [HIT] [fallback] search_wcag({"query": "techniques are informative not required for conformance"}) -> 93 chars
[15] [HIT] [optional] count_criteria({"group_by": "level"}) -> 138 chars
[16] [HIT] [optional] whats_new_in_wcag22({}) -> 1785 chars
[17] [HIT] [optional] list_success_criteria({"guideline": "1.4"}) -> 992 chars

--- Evidence Checks ---
Conformance roll-up rule: FOUND
Techniques vs requirements: FOUND

--- Execution Summary ---
MCP time: 0.0s
Total: 17 (hits: 17, misses: 0, blocked: 0)
Hit chars: 13657

================================================================================
STEP 6: TOOL CALL TRACES
================================================================================

----------------------------------------------------------------------
[CALL 1] [HIT] [must_have] list_principles({})
Result: 637 chars
----------------------------------------------------------------------
# WCAG 2.2 Principles

**1. Perceivable**
Information and user interface components must be presentable to users in ways they can perceive.
URL: https://www.w3.org/TR/WCAG22/#perceivable

**2. Operable**
User interface components and navigation must be operable.
URL: https://www.w3.org/TR/WCAG22/#operable

**3. Understandable**
Information and the operation of the user interface must be understandable.
URL: https://www.w3.org/TR/WCAG22/#understandable

**4. Robust**
Content must be robust enough that it can be interpreted by a wide variety of user agents, including assistive technologies.
URL: https://www.w3.org/TR/WCAG22/#robust

----------------------------------------------------------------------
[CALL 2] [HIT] [must_have] list_guidelines({})
Result: 1550 chars
----------------------------------------------------------------------
# WCAG 2.2 Guidelines

## Principle 1: Perceivable

  **1.1 Text Alternatives**
  Provide text alternatives for any non-text content so that it can be changed into other forms people need, such as large print, braille, speech, symbols or simpler language.

  **1.2 Time-based Media**
  Provide alternatives for time-based media.

  **1.3 Adaptable**
  Create content that can be presented in different ways (for example simpler layout) without losing information or structure.

  **1.4 Distinguishable**
  Make it easier for users to see and hear content including separating foreground from background.

---

## Principle 2: Operable

  **2.1 Keyboard Accessible**
  Make all functionality available from a keyboard.

  **2.2 Enough Time**
  Provide users enough time to read and use content.

  **2.3 Seizures and Physical Reactions**
  Do not design content in a way that is known to cause seizures or physical reactions.

  **2.4 Navigable**
  Provide ways to help users navigate, find content, and determine where they are.

  **2.5 Input Modalities**
  Make it easier for users to operate functionality through various inputs beyond keyboard.

---

## Principle 3: Understandable

  **3.1 Readable**
  Make text content readable and understandable.

  **3.2 Predictable**
  Make web pages appear and operate in predictable ways.

  **3.3 Input Assistance**
  Help users avoid and correct mistakes.

---

## Principle 4: Robust

  **4.1 Compatible**
  Maximize compatibility with current and future user agents, including assistive technologies.

----------------------------------------------------------------------
[CALL 3] [HIT] [must_have] get_success_criteria_detail({"ref_id": "1.1.1"})
Result: 2021 chars
----------------------------------------------------------------------
# 1.1.1 Non-text Content

**Level:** A
**Principle:** 1 Perceivable
**Guideline:** 1.1 Text Alternatives
**WCAG Versions:** 2.0, 2.1, 2.2

## Success Criterion

All non-text content that is presented to the user has a text alternative that serves the equivalent purpose, except for the situations listed below.

## Details

- **Controls, Input:** If non-text content is a control or accepts user input, then it has a name that describes its purpose. (Refer to Success Criterion 4.1.2 for additional requirements for controls and content that accepts user input.)
- **Time-Based Media:** If non-text content is time-based media, then text alternatives at least provide descriptive identification of the non-text content. (Refer to Guideline 1.2 for additional requirements for media.)
- **Test:** If non-text content is a test or exercise that would be invalid if presented in text, then text alternatives at least provide descriptive identification of the non-text content.
- **Sensory:** If non-text content is primarily intended to create a specific sensory experience, then text alternatives at least provide descriptive identification of the non-text content.
- **CAPTCHA:** If the purpose of non-text content is to confirm that content is being accessed by a person rather than a computer, then text alternatives that identify and describe the purpose of the non-text content are provided, and alternative forms of CAPTCHA using output modes for different types of sensory perception are provided to accommodate different disabilities.
- **Decoration, Formatting, Invisible:** If non-text content is pure decoration, is used only for visual formatting, or is not presented to users, then it is implemented in a way that it can be ignored by assistive technology.

## Links

- [WCAG Specification](https://www.w3.org/TR/WCAG22/#non-text-content)
- [Understanding 1.1.1](https://www.w3.org/WAI/WCAG22/Understanding/non-text-content.html)
- [How to Meet 1.1.1](https://www.w3.org/WAI/WCAG22/quickref/#non-text-content)


----------------------------------------------------------------------
[CALL 4] [HIT] [must_have] get_success_criteria_detail({"ref_id": "1.4.3"})
Result: 1000 chars
----------------------------------------------------------------------
# 1.4.3 Contrast (Minimum)

**Level:** AA
**Principle:** 1 Perceivable
**Guideline:** 1.4 Distinguishable
**WCAG Versions:** 2.0, 2.1, 2.2

## Success Criterion

The visual presentation of text and images of text has a contrast ratio of at least 4.5:1, except for the following:

## Details

- **Large Text:** Large-scale text and images of large-scale text have a contrast ratio of at least 3:1;
- **Incidental:** Text or images of text that are part of an inactive user interface component, that are pure decoration, that are not visible to anyone, or that are part of a picture that contains significant other visual content, have no contrast requirement.
- **Logotypes:** Text that is part of a logo or brand name has no contrast requirement.

## Links

- [WCAG Specification](https://www.w3.org/TR/WCAG22/#contrast-minimum)
- [Understanding 1.4.3](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
- [How to Meet 1.4.3](https://www.w3.org/WAI/WCAG22/quickref/#contrast-minimum)


----------------------------------------------------------------------
[CALL 5] [HIT] [must_have] get_success_criteria_detail({"ref_id": "2.4.11"})
Result: 1059 chars
----------------------------------------------------------------------
# 2.4.11 Focus Not Obscured (Minimum)

**Level:** AA
**Principle:** 2 Operable
**Guideline:** 2.4 Navigable
**WCAG Versions:** 2.2

## Success Criterion

When a user interface component receives keyboard focus, the component is not entirely hidden due to author-created content.

## Details

> **Note 1:** Where content in a configurable interface can be repositioned by the user, then only the initial positions of user-movable content are considered for testing and conformance of this success criterion.

> **Note 2:** Content opened by the <em>user</em> may obscure the component receiving focus. If the user can reveal the focused component without advancing the keyboard focus, the component with focus is not considered visually hidden due to author-created content.

## Links

- [WCAG Specification](https://www.w3.org/TR/WCAG22/#focus-not-obscured-minimum)
- [Understanding 2.4.11](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html)
- [How to Meet 2.4.11](https://www.w3.org/WAI/WCAG22/quickref/#focus-not-obscured-minimum)


----------------------------------------------------------------------
[CALL 6] [HIT] [must_have] get_success_criteria_detail({"ref_id": "2.4.12"})
Result: 563 chars
----------------------------------------------------------------------
# 2.4.12 Focus Not Obscured (Enhanced)

**Level:** AAA
**Principle:** 2 Operable
**Guideline:** 2.4 Navigable
**WCAG Versions:** 2.2

## Success Criterion

When a user interface component receives keyboard focus, no part of the component is hidden by author-created content.

## Links

- [WCAG Specification](https://www.w3.org/TR/WCAG22/#focus-not-obscured-enhanced)
- [Understanding 2.4.12](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-enhanced.html)
- [How to Meet 2.4.12](https://www.w3.org/WAI/WCAG22/quickref/#focus-not-obscured-enhanced)


----------------------------------------------------------------------
[CALL 7] [HIT] [must_have] get_success_criteria_detail({"ref_id": "2.5.7"})
Result: 844 chars
----------------------------------------------------------------------
# 2.5.7 Dragging Movements

**Level:** AA
**Principle:** 2 Operable
**Guideline:** 2.5 Input Modalities
**WCAG Versions:** 2.2

## Success Criterion

All functionality that uses a dragging movement for operation can be achieved by a single pointer without dragging, unless dragging is essential or the functionality is determined by the user agent and not modified by the author.

## Details

> **Note:** This requirement applies to web content that interprets pointer actions (i.e., this does not apply to actions that are required to operate the user agent or assistive technology).

## Links

- [WCAG Specification](https://www.w3.org/TR/WCAG22/#dragging-movements)
- [Understanding 2.5.7](https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements.html)
- [How to Meet 2.5.7](https://www.w3.org/WAI/WCAG22/quickref/#dragging-movements)


----------------------------------------------------------------------
[CALL 8] [HIT] [must_have] get_glossary_term({"term": "conformance"})
Result: 166 chars
----------------------------------------------------------------------
# conformance

satisfying all the requirements of a given standard, guideline or specification

[View in WCAG 2.2 Glossary](https://www.w3.org/TR/WCAG22/#dfn-conform)

----------------------------------------------------------------------
[CALL 9] [HIT] [must_have] get_glossary_term({"term": "web page"})
Result: 1529 chars
----------------------------------------------------------------------
# web page

a non-embedded resource obtained from a single URI using HTTP plus any other resources that are used in the rendering or intended to be rendered together with it by a user agent Note 1Although any "other resources" would be rendered together with the primary resource, they would not necessarily be rendered simultaneously with each other. Note 2For the purposes of conformance with these guidelines, a resource must be "non-embedded" within the scope of conformance to be considered a web page. Example 1A web resource including all embedded images and media. Example 2A web mail program built using Asynchronous JavaScript and XML (AJAX). The program lives entirely at http://example.com/mail, but includes an inbox, a contacts area and a calendar. Links or buttons are provided that cause the inbox, contacts, or calendar to display, but do not change the URI of the page as a whole. Example 3A customizable portal site, where users can choose content to display from a set of different content modules. Example 4When you enter "http://shopping.example.com/" in your browser, you enter a movie-like interactive shopping environment where you visually move around in a store dragging products off of the shelves around you and into a visual shopping cart in front of you. Clicking on a product causes it to be demonstrated with a specification sheet floating alongside. This might be a single-page website or just one page within a website.

[View in WCAG 2.2 Glossary](https://www.w3.org/TR/WCAG22/#dfn-web-page-s)

----------------------------------------------------------------------
[CALL 10] [HIT] [must_have] get_technique({"id": "G18"})
Result: 424 chars
----------------------------------------------------------------------
# G18: Ensuring that a contrast ratio of at least 4.5:1 exists between text (and images of text) and background behind the text

**Technology:** general
**Types:** sufficient
**Applies to:** 2 success criteria

## Related Success Criteria

- **1.4.3** Contrast (Minimum) (Level AA)
- **1.4.6** Contrast (Enhanced) (Level AAA)

## Links

- [Full Technique Documentation](https://www.w3.org/WAI/WCAG22/Techniques/general/G18)


----------------------------------------------------------------------
[CALL 11] [HIT] [fallback] search_wcag({"query": "conformance level AA requirements all level A criteria"})
Result: 92 chars
----------------------------------------------------------------------
No success criteria found matching "conformance level AA requirements all level A criteria".

----------------------------------------------------------------------
[CALL 12] [HIT] [fallback] get_full_criterion_context({"ref_id": "1.1.1"})
Result: 687 chars
----------------------------------------------------------------------
# Complete Context: 1.1.1 Non-text Content

## Overview

**Level:** A
**Principle:** 1 Perceivable
**Guideline:** 1.1 Text Alternatives
**WCAG Versions:** 2.0, 2.1, 2.2

All non-text content that is presented to the user has a text alternative that serves the equivalent purpose, except for the situations listed below.

## Techniques Summary

- **Sufficient:** 46 techniques
- **Advisory:** 1 techniques
- **Failure:** 10 techniques

## Links

- [WCAG Specification](https://www.w3.org/TR/WCAG22/#non-text-content)
- [Understanding 1.1.1](https://www.w3.org/WAI/WCAG22/Understanding/non-text-content.html)
- [How to Meet 1.1.1](https://www.w3.org/WAI/WCAG22/quickref/#non-text-content)


----------------------------------------------------------------------
[CALL 13] [HIT] [fallback] search_wcag({"query": "WCAG conformance requirement full pages"})
Result: 77 chars
----------------------------------------------------------------------
No success criteria found matching "WCAG conformance requirement full pages".

----------------------------------------------------------------------
[CALL 14] [HIT] [fallback] search_wcag({"query": "techniques are informative not required for conformance"})
Result: 93 chars
----------------------------------------------------------------------
No success criteria found matching "techniques are informative not required for conformance".

----------------------------------------------------------------------
[CALL 15] [HIT] [optional] count_criteria({"group_by": "level"})
Result: 138 chars
----------------------------------------------------------------------
# WCAG 2.2 Success Criteria by Level

Total: 87 success criteria

- **Level **: 1
- **Level A**: 31
- **Level AA**: 24
- **Level AAA**: 31

----------------------------------------------------------------------
[CALL 16] [HIT] [optional] whats_new_in_wcag22({})
Result: 1785 chars
----------------------------------------------------------------------
# What's New in WCAG 2.2

WCAG 2.2 added 9 new success criteria:

## Level A

### 3.2.6 Consistent Help
If a web page contains any of the following help mechanisms, and those mechanisms are repeated on multiple web pages within a set of web pages, they occur in the same order relative to other page cont...

### 3.3.7 Redundant Entry
Information previously entered by or provided to the user that is required to be entered again in the same process is either:

## Level AA

### 2.4.11 Focus Not Obscured (Minimum)
When a user interface component receives keyboard focus, the component is not entirely hidden due to author-created content.

### 2.5.7 Dragging Movements
All functionality that uses a dragging movement for operation can be achieved by a single pointer without dragging, unless dragging is essential or the functionality is determined by the user agent an...

### 2.5.8 Target Size (Minimum)
The size of the target for pointer inputs is at least 24 by 24 CSS pixels, except when:

### 3.3.8 Accessible Authentication (Minimum)
A cognitive function test (such as remembering a password or solving a puzzle) is not required for any step in an authentication process unless that step provides at least one of the following:

## Level AAA

### 2.4.12 Focus Not Obscured (Enhanced)
When a user interface component receives keyboard focus, no part of the component is hidden by author-created content.

### 2.4.13 Focus Appearance
When the keyboard focus indicator is visible, an area of the focus indicator meets all the following:

### 3.3.9 Accessible Authentication (Enhanced)
A cognitive function test (such as remembering a password or solving a puzzle) is not required for any step in an authentication process unless that step provides at least one of the following:



----------------------------------------------------------------------
[CALL 17] [HIT] [optional] list_success_criteria({"guideline": "1.4"})
Result: 992 chars
----------------------------------------------------------------------
# WCAG 2.2 Success Criteria (13 found)

Filters: Guideline: 1.4

**1.4.1 Use of Color** (Level A)
Guideline: 1.4 Distinguishable

**1.4.2 Audio Control** (Level A)
Guideline: 1.4 Distinguishable

**1.4.3 Contrast (Minimum)** (Level AA)
Guideline: 1.4 Distinguishable

**1.4.4 Resize Text** (Level AA)
Guideline: 1.4 Distinguishable

**1.4.5 Images of Text** (Level AA)
Guideline: 1.4 Distinguishable

**1.4.6 Contrast (Enhanced)** (Level AAA)
Guideline: 1.4 Distinguishable

**1.4.7 Low or No Background Audio** (Level AAA)
Guideline: 1.4 Distinguishable

**1.4.8 Visual Presentation** (Level AAA)
Guideline: 1.4 Distinguishable

**1.4.9 Images of Text (No Exception)** (Level AAA)
Guideline: 1.4 Distinguishable

**1.4.10 Reflow** (Level AA)
Guideline: 1.4 Distinguishable

**1.4.11 Non-text Contrast** (Level AA)
Guideline: 1.4 Distinguishable

**1.4.12 Text Spacing** (Level AA)
Guideline: 1.4 Distinguishable

**1.4.13 Content on Hover or Focus** (Level AA)
Guideline: 1.4 Distinguishable

================================================================================
STEP 7: FINAL TEACHING CONTENT
================================================================================

Unique hit sections: 17
Final content: 13769 chars

# WCAG 2.2 Principles

**1. Perceivable**
Information and user interface components must be presentable to users in ways they can perceive.
URL: https://www.w3.org/TR/WCAG22/#perceivable

**2. Operable**
User interface components and navigation must be operable.
URL: https://www.w3.org/TR/WCAG22/#operable

**3. Understandable**
Information and the operation of the user interface must be understandable.
URL: https://www.w3.org/TR/WCAG22/#understandable

**4. Robust**
Content must be robust enough that it can be interpreted by a wide variety of user agents, including assistive technologies.
URL: https://www.w3.org/TR/WCAG22/#robust

---

# WCAG 2.2 Guidelines

## Principle 1: Perceivable

  **1.1 Text Alternatives**
  Provide text alternatives for any non-text content so that it can be changed into other forms people need, such as large print, braille, speech, symbols or simpler language.

  **1.2 Time-based Media**
  Provide alternatives for time-based media.

  **1.3 Adaptable**
  Create content that can be presented in different ways (for example simpler layout) without losing information or structure.

  **1.4 Distinguishable**
  Make it easier for users to see and hear content including separating foreground from background.

---

## Principle 2: Operable

  **2.1 Keyboard Accessible**
  Make all functionality available from a keyboard.

  **2.2 Enough Time**
  Provide users enough time to read and use content.

  **2.3 Seizures and Physical Reactions**
  Do not design content in a way that is known to cause seizures or physical reactions.

  **2.4 Navigable**
  Provide ways to help users navigate, find content, and determine where they are.

  **2.5 Input Modalities**
  Make it easier for users to operate functionality through various inputs beyond keyboard.

---

## Principle 3: Understandable

  **3.1 Readable**
  Make text content readable and understandable.

  **3.2 Predictable**
  Make web pages appear and operate in predictable ways.

  **3.3 Input Assistance**
  Help users avoid and correct mistakes.

---

## Principle 4: Robust

  **4.1 Compatible**
  Maximize compatibility with current and future user agents, including assistive technologies.

---

# 1.1.1 Non-text Content

**Level:** A
**Principle:** 1 Perceivable
**Guideline:** 1.1 Text Alternatives
**WCAG Versions:** 2.0, 2.1, 2.2

## Success Criterion

All non-text content that is presented to the user has a text alternative that serves the equivalent purpose, except for the situations listed below.

## Details

- **Controls, Input:** If non-text content is a control or accepts user input, then it has a name that describes its purpose. (Refer to Success Criterion 4.1.2 for additional requirements for controls and content that accepts user input.)
- **Time-Based Media:** If non-text content is time-based media, then text alternatives at least provide descriptive identification of the non-text content. (Refer to Guideline 1.2 for additional requirements for media.)
- **Test:** If non-text content is a test or exercise that would be invalid if presented in text, then text alternatives at least provide descriptive identification of the non-text content.
- **Sensory:** If non-text content is primarily intended to create a specific sensory experience, then text alternatives at least provide descriptive identification of the non-text content.
- **CAPTCHA:** If the purpose of non-text content is to confirm that content is being accessed by a person rather than a computer, then text alternatives that identify and describe the purpose of the non-text content are provided, and alternative forms of CAPTCHA using output modes for different types of sensory perception are provided to accommodate different disabilities.
- **Decoration, Formatting, Invisible:** If non-text content is pure decoration, is used only for visual formatting, or is not presented to users, then it is implemented in a way that it can be ignored by assistive technology.

## Links

- [WCAG Specification](https://www.w3.org/TR/WCAG22/#non-text-content)
- [Understanding 1.1.1](https://www.w3.org/WAI/WCAG22/Understanding/non-text-content.html)
- [How to Meet 1.1.1](https://www.w3.org/WAI/WCAG22/quickref/#non-text-content)


---

# 1.4.3 Contrast (Minimum)

**Level:** AA
**Principle:** 1 Perceivable
**Guideline:** 1.4 Distinguishable
**WCAG Versions:** 2.0, 2.1, 2.2

## Success Criterion

The visual presentation of text and images of text has a contrast ratio of at least 4.5:1, except for the following:

## Details

- **Large Text:** Large-scale text and images of large-scale text have a contrast ratio of at least 3:1;
- **Incidental:** Text or images of text that are part of an inactive user interface component, that are pure decoration, that are not visible to anyone, or that are part of a picture that contains significant other visual content, have no contrast requirement.
- **Logotypes:** Text that is part of a logo or brand name has no contrast requirement.

## Links

- [WCAG Specification](https://www.w3.org/TR/WCAG22/#contrast-minimum)
- [Understanding 1.4.3](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
- [How to Meet 1.4.3](https://www.w3.org/WAI/WCAG22/quickref/#contrast-minimum)


---

# 2.4.11 Focus Not Obscured (Minimum)

**Level:** AA
**Principle:** 2 Operable
**Guideline:** 2.4 Navigable
**WCAG Versions:** 2.2

## Success Criterion

When a user interface component receives keyboard focus, the component is not entirely hidden due to author-created content.

## Details

> **Note 1:** Where content in a configurable interface can be repositioned by the user, then only the initial positions of user-movable content are considered for testing and conformance of this success criterion.

> **Note 2:** Content opened by the <em>user</em> may obscure the component receiving focus. If the user can reveal the focused component without advancing the keyboard focus, the component with focus is not considered visually hidden due to author-created content.

## Links

- [WCAG Specification](https://www.w3.org/TR/WCAG22/#focus-not-obscured-minimum)
- [Understanding 2.4.11](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html)
- [How to Meet 2.4.11](https://www.w3.org/WAI/WCAG22/quickref/#focus-not-obscured-minimum)


---

# 2.4.12 Focus Not Obscured (Enhanced)

**Level:** AAA
**Principle:** 2 Operable
**Guideline:** 2.4 Navigable
**WCAG Versions:** 2.2

## Success Criterion

When a user interface component receives keyboard focus, no part of the component is hidden by author-created content.

## Links

- [WCAG Specification](https://www.w3.org/TR/WCAG22/#focus-not-obscured-enhanced)
- [Understanding 2.4.12](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-enhanced.html)
- [How to Meet 2.4.12](https://www.w3.org/WAI/WCAG22/quickref/#focus-not-obscured-enhanced)


---

# 2.5.7 Dragging Movements

**Level:** AA
**Principle:** 2 Operable
**Guideline:** 2.5 Input Modalities
**WCAG Versions:** 2.2

## Success Criterion

All functionality that uses a dragging movement for operation can be achieved by a single pointer without dragging, unless dragging is essential or the functionality is determined by the user agent and not modified by the author.

## Details

> **Note:** This requirement applies to web content that interprets pointer actions (i.e., this does not apply to actions that are required to operate the user agent or assistive technology).

## Links

- [WCAG Specification](https://www.w3.org/TR/WCAG22/#dragging-movements)
- [Understanding 2.5.7](https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements.html)
- [How to Meet 2.5.7](https://www.w3.org/WAI/WCAG22/quickref/#dragging-movements)


---

# conformance

satisfying all the requirements of a given standard, guideline or specification

[View in WCAG 2.2 Glossary](https://www.w3.org/TR/WCAG22/#dfn-conform)

---

# web page

a non-embedded resource obtained from a single URI using HTTP plus any other resources that are used in the rendering or intended to be rendered together with it by a user agent Note 1Although any "other resources" would be rendered together with the primary resource, they would not necessarily be rendered simultaneously with each other. Note 2For the purposes of conformance with these guidelines, a resource must be "non-embedded" within the scope of conformance to be considered a web page. Example 1A web resource including all embedded images and media. Example 2A web mail program built using Asynchronous JavaScript and XML (AJAX). The program lives entirely at http://example.com/mail, but includes an inbox, a contacts area and a calendar. Links or buttons are provided that cause the inbox, contacts, or calendar to display, but do not change the URI of the page as a whole. Example 3A customizable portal site, where users can choose content to display from a set of different content modules. Example 4When you enter "http://shopping.example.com/" in your browser, you enter a movie-like interactive shopping environment where you visually move around in a store dragging products off of the shelves around you and into a visual shopping cart in front of you. Clicking on a product causes it to be demonstrated with a specification sheet floating alongside. This might be a single-page website or just one page within a website.

[View in WCAG 2.2 Glossary](https://www.w3.org/TR/WCAG22/#dfn-web-page-s)

---

# G18: Ensuring that a contrast ratio of at least 4.5:1 exists between text (and images of text) and background behind the text

**Technology:** general
**Types:** sufficient
**Applies to:** 2 success criteria

## Related Success Criteria

- **1.4.3** Contrast (Minimum) (Level AA)
- **1.4.6** Contrast (Enhanced) (Level AAA)

## Links

- [Full Technique Documentation](https://www.w3.org/WAI/WCAG22/Techniques/general/G18)


---

No success criteria found matching "conformance level AA requirements all level A criteria".

---

# Complete Context: 1.1.1 Non-text Content

## Overview

**Level:** A
**Principle:** 1 Perceivable
**Guideline:** 1.1 Text Alternatives
**WCAG Versions:** 2.0, 2.1, 2.2

All non-text content that is presented to the user has a text alternative that serves the equivalent purpose, except for the situations listed below.

## Techniques Summary

- **Sufficient:** 46 techniques
- **Advisory:** 1 techniques
- **Failure:** 10 techniques

## Links

- [WCAG Specification](https://www.w3.org/TR/WCAG22/#non-text-content)
- [Understanding 1.1.1](https://www.w3.org/WAI/WCAG22/Understanding/non-text-content.html)
- [How to Meet 1.1.1](https://www.w3.org/WAI/WCAG22/quickref/#non-text-content)


---

No success criteria found matching "WCAG conformance requirement full pages".

---

No success criteria found matching "techniques are informative not required for conformance".

---

# WCAG 2.2 Success Criteria by Level

Total: 87 success criteria

- **Level **: 1
- **Level A**: 31
- **Level AA**: 24
- **Level AAA**: 31

---

# What's New in WCAG 2.2

WCAG 2.2 added 9 new success criteria:

## Level A

### 3.2.6 Consistent Help
If a web page contains any of the following help mechanisms, and those mechanisms are repeated on multiple web pages within a set of web pages, they occur in the same order relative to other page cont...

### 3.3.7 Redundant Entry
Information previously entered by or provided to the user that is required to be entered again in the same process is either:

## Level AA

### 2.4.11 Focus Not Obscured (Minimum)
When a user interface component receives keyboard focus, the component is not entirely hidden due to author-created content.

### 2.5.7 Dragging Movements
All functionality that uses a dragging movement for operation can be achieved by a single pointer without dragging, unless dragging is essential or the functionality is determined by the user agent an...

### 2.5.8 Target Size (Minimum)
The size of the target for pointer inputs is at least 24 by 24 CSS pixels, except when:

### 3.3.8 Accessible Authentication (Minimum)
A cognitive function test (such as remembering a password or solving a puzzle) is not required for any step in an authentication process unless that step provides at least one of the following:

## Level AAA

### 2.4.12 Focus Not Obscured (Enhanced)
When a user interface component receives keyboard focus, no part of the component is hidden by author-created content.

### 2.4.13 Focus Appearance
When the keyboard focus indicator is visible, an area of the focus indicator meets all the following:

### 3.3.9 Accessible Authentication (Enhanced)
A cognitive function test (such as remembering a password or solving a puzzle) is not required for any step in an authentication process unless that step provides at least one of the following:



---

# WCAG 2.2 Success Criteria (13 found)

Filters: Guideline: 1.4

**1.4.1 Use of Color** (Level A)
Guideline: 1.4 Distinguishable

**1.4.2 Audio Control** (Level A)
Guideline: 1.4 Distinguishable

**1.4.3 Contrast (Minimum)** (Level AA)
Guideline: 1.4 Distinguishable

**1.4.4 Resize Text** (Level AA)
Guideline: 1.4 Distinguishable

**1.4.5 Images of Text** (Level AA)
Guideline: 1.4 Distinguishable

**1.4.6 Contrast (Enhanced)** (Level AAA)
Guideline: 1.4 Distinguishable

**1.4.7 Low or No Background Audio** (Level AAA)
Guideline: 1.4 Distinguishable

**1.4.8 Visual Presentation** (Level AAA)
Guideline: 1.4 Distinguishable

**1.4.9 Images of Text (No Exception)** (Level AAA)
Guideline: 1.4 Distinguishable

**1.4.10 Reflow** (Level AA)
Guideline: 1.4 Distinguishable

**1.4.11 Non-text Contrast** (Level AA)
Guideline: 1.4 Distinguishable

**1.4.12 Text Spacing** (Level AA)
Guideline: 1.4 Distinguishable

**1.4.13 Content on Hover or Focus** (Level AA)
Guideline: 1.4 Distinguishable

================================================================================
PIPELINE TOTALS
================================================================================
LLM calls: 3 | LLM time: 112.9s
LLM tokens: prompt=9063 completion=9396 total=18459
MCP calls: 17 (hits: 17, misses: 0, blocked: 0)
MCP time: 0.0s
Final content: 17 sections, 13769 chars