================================================================================
STEP 1: GENERATE TEACHING PLAN
================================================================================
Objective: Explain the structure of WCAG 2.2, including the POUR principles, guidelines, success criteria, and conformance levels A, AA, and AAA.

Time: 28.6s | Tokens: 884/2293 | Output: 10186 chars

1. objective_text
Explain the structure of WCAG 2.2, including the POUR principles, guidelines, success criteria, and conformance levels A, AA, and AAA.

2. plain_language_goal
Describe how WCAG 2.2 is organized: what the four principles are, what guidelines are under them, what success criteria are, and what the A/AA/AAA conformance levels mean.

3. mastery_definition
A learner has mastered this objective when they can:
- Correctly define each layer of WCAG 2.2 structure (principles, guidelines, success criteria) and distinguish their roles.
- Map a specific example criterion to its principle, guideline, and conformance level.
- Explain how conformance levels (A, AA, AAA) apply to success criteria and what meeting each level implies.
- Identify common misinterpretations (e.g., techniques vs. criteria, levels applied to guidelines vs. criteria) and correct them.

4. objective_type
- conceptual understanding
- hierarchy/structure
- classification
- comparison

5. prerequisite_knowledge
- essential prerequisites:
  - Very basic understanding of web content and accessibility purpose (high-level: making content usable for people with disabilities).
  - Awareness that WCAG is a standard from W3C for web accessibility.
- helpful but nonessential prerequisites:
  - Familiarity with how standards documents are structured (normative vs. informative).
  - Recognition of typical WCAG examples (e.g., alt text, keyboard access) without deep detail.
  - Awareness that organizations often target AA conformance.

6. prerequisite_gap_policy
- If the learner lacks the essential prerequisites:
  - Provide a brief orientation: what WCAG is and why it exists (1–2 sentence overview).
  - Confirm understanding with a quick diagnostic question (e.g., “What problem is WCAG trying to solve?”).
  - Only once that baseline is confirmed, proceed to the structural layers; avoid diving into technical examples.

7. concept_decomposition
- Purpose of WCAG (context for structure).
- Four POUR principles: define and role as top-level categories.
- Guidelines: definition and role (non-testable guidance under each principle).
- Success criteria: definition, role as testable statements, unique identifiers, and levels.
- Conformance levels A, AA, AAA: meaning and how they apply to success criteria and overall conformance.
- Normative vs. informative sections: standards vs. techniques/understanding docs (to prevent conflation).
- Example mapping: connecting a concrete success criterion to its principle, guideline, level.
- Scope of conformance: what meeting Level A/AA/AAA entails (cumulative nature).
- Common organizational targets (e.g., AA) and why (contextual understanding without policy detail).

8. dependency_order
- Purpose of WCAG → sets context for why structure matters.
- POUR principles → top-level buckets to frame subsequent layers.
- Guidelines → sit under principles; clarify role and non-testable nature.
- Success criteria → testable items under guidelines; introduce identifiers and levels.
- Conformance levels → explain A/AA/AAA as properties of success criteria and cumulative conformance.
- Normative vs. informative → distinguish criteria from techniques/understanding docs.
- Example mapping → apply hierarchy with a specific criterion to solidify structure.
- Scope of conformance → clarify how meeting levels aggregates across criteria.
Rationale: This moves from general to specific, establishing the hierarchy before discussing testability and levels. Only after the layers are clear do we contrast normative/informative and solidify with mapping and scope.

9. likely_misconceptions
- Believing guidelines are testable and carry levels (instead of success criteria).
- Thinking conformance levels apply to principles or entire guidelines directly.
- Assuming AAA is required for compliance or that AA excludes A requirements.
- Confusing techniques with success criteria (treating techniques as mandatory).
- Believing partial conformance to some pages equals full conformance claim for a site.
- Mixing WCAG with WAI-ARIA specifics as part of the structure.
- Assuming 2.2 fundamentally changes principles rather than adds/adjusts criteria.

10. explanation_vs_question_strategy
- Purpose of WCAG: brief explanation, then diagnostic question — sets baseline efficiently.
- POUR principles: guided questioning with contrastive examples — helps learners infer categories.
- Guidelines: brief explanation plus contrastive example (testable vs. non-testable) — avoids overgeneralization.
- Success criteria: worked example — concrete example shows testable, numbered nature.
- Conformance levels: guided questioning with contrastive example (A vs AA vs AAA) — elicits understanding of cumulative and strictness.
- Normative vs. informative: contrastive example — prevents conflating techniques with criteria.
- Example mapping: worked example — mapping a known criterion up the hierarchy anchors structure.
- Scope of conformance: diagnostic question followed by brief explanation — reveals assumptions about page/site conformance and cumulative levels.

11. socratic_question_goals
- Purpose of WCAG: diagnose prior knowledge; establish relevance.
- POUR principles: force comparison; check categorization logic for accessibility needs.
- Guidelines: reveal misconception about testability; justify why guidelines exist.
- Success criteria: check causal understanding of “testable”; justify how pass/fail would be determined.
- Conformance levels: force comparison (A vs AA vs AAA); justify cumulative nature; test boundaries (is AAA required?).
- Normative vs. informative: reveal misconception (techniques vs criteria); justify which is mandatory.
- Example mapping: check ability to classify and map; test transfer from a concrete item to hierarchy.
- Scope of conformance: test transfer to site-level claims; reveal misconceptions about partial coverage.

12. example_requirements
- Simplest introductory example: One clear success criterion with obvious mapping (e.g., a criterion requiring text alternatives; show its principle, guideline, and that it’s Level A).
- Contrastive example(s):
  - A guideline statement vs. a success criterion statement to highlight non-testable vs. testable.
  - A technique (e.g., using specific markup) vs. the success criterion it supports.
- Borderline/tricky case:
  - An AAA success criterion that is often desirable but not required for AA, illustrating optionality.
  - A criterion introduced or changed in WCAG 2.2 to show that principles stayed the same while criteria changed.
- Transfer scenario:
  - Given two criteria at different levels, ask which must be met for AA conformance and why.
  - Given a page that meets A and some AA criteria, determine conformance claim accuracy.

13. retrieval_requirements
- must-retrieve:
  - Authoritative definitions of “principle,” “guideline,” “success criterion,” and “conformance level” as used in WCAG 2.2.
  - A small set (2–3) of canonical success criteria examples with IDs and levels (e.g., one A, one AA, one AAA).
  - A clear statement from WCAG 2.2 on conformance claims and the cumulative nature of A/AA/AAA.
  - Clarification of normative vs. informative sections and the status of techniques/understanding docs.
- optional-supporting:
  - Brief note of what changed in 2.2 vs 2.1 at a high level (to anchor “structure unchanged, criteria evolved”).
  - Common organizational practice of targeting Level AA (for context).
  - Visual hierarchy diagram (principle → guideline → success criteria) for reference.

14. assessment_evidence
- Quick understanding checks:
  - Multiple-choice: Identify which layer a statement belongs to (principle/guideline/criterion).
  - True/false: “Conformance levels apply to guidelines.” (False)
- Application task:
  - Given a success criterion text with its ID, ask the learner to name its principle, guideline, and level.
- Transfer task:
  - Provide a list of criteria at various levels that a page meets; ask what conformance level the page can claim and why.
- Misconception check:
  - Present a technique and ask if failing it fails WCAG; require explanation distinguishing informative vs. normative content.

15. adaptation_notes
- Beginner:
  - Spend more time on the overall hierarchy; use fewer criteria examples (one per level).
  - Use visuals or structured lists; avoid jargon beyond defined terms.
  - More diagnostic questions to confirm differentiation between guideline and criterion.
- Intermediate:
  - Introduce two contrasting criteria within the same guideline to deepen mapping skills.
  - Include a brief normative vs. informative check earlier to preempt confusion.
- Advanced:
  - Include a criterion added in 2.2 and discuss how it fits into existing structure.
  - Add a short task on edge cases in conformance claims (e.g., components vs. full pages) without deep policy dive.

16. boundaries_and_non_goals
- Do not teach how to implement specific criteria (e.g., how to code keyboard navigation).
- Do not cover detailed conformance claim process steps or required statements for public claims.
- Do not dive into WCAG 2.2 change log beyond small context.
- Do not cover related standards in depth (e.g., ATAG, UAAG, EN 301 549, ARIA specifics).
- Do not teach testing methodologies or tools; focus is on structure, not evaluation techniques.

17. concise_plan_summary
- Establish why WCAG exists, then introduce the four POUR principles as the top-level frame.
- Clarify that guidelines sit under principles and are not testable; success criteria are testable and carry levels.
- Explain conformance levels A/AA/AAA as properties of success criteria and cumulative for overall claims.
- Distinguish normative criteria from informative techniques/understanding content to avoid conflation.
- Use a concrete success criterion to map up the hierarchy and identify its level.
- Check understanding with contrastive examples (guideline vs criterion, technique vs criterion).
- Address common misconceptions (e.g., AAA requirement, levels applying to guidelines).
- Assess through classification, mapping, and a conformance-level determination task to demonstrate structural understanding.

================================================================================
STEP 2: GENERATE RETRIEVAL PLAN
================================================================================

Time: 54.9s | Tokens: 3824/4202 | Output: 11542 chars

1. retrieval_goal
Support accurate instruction on the structural hierarchy of WCAG 2.2 (POUR principles → guidelines → success criteria) and the meaning and application of conformance levels (A/AA/AAA), including the cumulative conformance rule and the distinction between normative success criteria and informative techniques.

2. instructional_intent_summary
- Introduce WCAG’s hierarchical structure (principles, guidelines, success criteria) and their roles.
- Map a specific success criterion to its principle, guideline, and level to solidify the hierarchy.
- Explain conformance levels A/AA/AAA as properties of success criteria and the cumulative rule for conformance.
- Clarify normative vs. informative content to avoid conflating techniques with requirements.
- Lesson type focus: structure/hierarchy, conceptual understanding, classification, comparison.

3. required_information_categories
- structural: Needed to establish the WCAG hierarchy (principles, guidelines, success criteria) and show how items nest.
- normative: Needed to present the official, testable success criteria and levels accurately.
- explanatory: Useful minimally via a full criterion context/Understanding excerpt to anchor the conformance roll-up rule and normative/informative distinction.
- techniques: Needed sparingly to show that techniques are informative and “sufficient,” not required (misconception guard).
- glossary: Needed for the “conformance” term to anchor conformance definition and, if present, the cumulative nature of levels.
- examples: Needed for 2–3 canonical success criteria (one A, one AA, one AAA) to exemplify mapping and levels.
- comparison data (optional): A brief “what’s new in WCAG 2.2” to reinforce that structure (POUR) is unchanged while criteria evolved.

4. tool_selection
- structural:
  - list_principles(): Retrieve all four POUR principles with descriptions; authoritative top-level structure.
  - list_guidelines(): Retrieve all guidelines under principles; shows middle layer and nesting.
  - list_success_criteria(principle?/guideline?): Retrieve SC under a selected guideline/principle to demonstrate nesting and that SC carry levels.
- normative:
  - get_criterion(ref_id): Retrieve full details for one chosen SC (e.g., 1.4.3) including Understanding; provides official SC text and context with level.
- explanatory (for roll-up and normative/informative cues):
  - get_full_criterion_context(ref_id): For the same SC, to surface any embedded statements about levels and the nature of techniques (informative).
- techniques:
  - get_technique("G18") (or another common technique tied to chosen SC): Shows “sufficient technique” labeling to contrast with normative requirements.
- glossary:
  - get_glossary_term("conformance"): Anchor definition; potential source for the cumulative conformance rule and claim context.
- examples:
  - get_criteria_by_level(level, include_lower?): Retrieve representative SC lists to pick one A, one AA, one AAA with IDs and levels.
- comparison data (optional):
  - whats_new_in_wcag22(): Briefly list new/changed SC to assert that principles remained the same.

Rationale: This is the smallest tool set that can provide verified hierarchy, concrete examples with levels, the conformance roll-up rule, and the techniques-vs-requirements distinction.

5. planned_tool_calls
Priority order:

1) list_principles()
- Purpose: Get the four POUR principles and descriptions.
- Instructional value: Core hierarchy anchor.

2) list_guidelines()
- Purpose: List all guidelines (optionally grouped by principle as returned).
- Instructional value: Shows middle layer under principles; emphasizes non-testable nature through context and placement.

3) get_criteria_by_level(level="A", include_lower=false)
- Purpose: Identify a clear Level A example (e.g., 1.1.1 Text Alternatives).
- Instructional value: Provide one canonical A-level SC with ID.

4) get_criteria_by_level(level="AA", include_lower=false)
- Purpose: Identify a clear Level AA example (e.g., 1.4.3 Contrast (Minimum)).
- Instructional value: Provide one canonical AA-level SC with ID.

5) get_criteria_by_level(level="AAA", include_lower=false)
- Purpose: Identify a clear Level AAA example (e.g., 1.4.6 Contrast (Enhanced)).
- Instructional value: Provide one canonical AAA-level SC with ID.

6) get_criterion(ref_id="1.4.3")  (or chosen AA example)
- Purpose: Retrieve full details for the chosen AA SC.
- Instructional value: Normative SC text, level, and Understanding context for mapping and potential conformance notes.

7) get_full_criterion_context(ref_id="1.4.3")
- Purpose: Get comprehensive context including techniques and glossary links.
- Instructional value: Evidence that techniques are informative and to extract any explicit statements on levels and conformance relationships.

8) list_success_criteria(guideline=<parent of 1.4.3>)  (after identifying parent via #6/#7)
- Purpose: Show SC listed under the selected guideline to demonstrate nesting (guideline → SC).
- Instructional value: Mapping support for hierarchy.

9) get_technique(id="G18")  (if 1.4.3 used; otherwise pick a technique matching the chosen AA SC)
- Purpose: Show a “sufficient technique” entry for contrast.
- Instructional value: Misconception guard that techniques are informative and not required.

10) get_glossary_term(term="conformance")
- Purpose: Retrieve the conformance definition and any notes about levels/claims.
- Instructional value: Anchor the conformance concept; attempt to capture the roll-up rule.

Optional (only if needed for 2.2 context):
11) whats_new_in_wcag22()
- Purpose: Provide brief list of new SC in 2.2.
- Instructional value: Support the point that principles are unchanged; criteria evolved.

Fallbacks (only if critical evidence is missing; see section 9):
- If roll-up rule not captured in #7 or #10, retrieve get_full_criterion_context for an additional widely cited SC (e.g., ref_id="1.1.1") to find an explicit statement.
- If techniques vs requirements distinction isn’t explicit from #7/#9, retrieve another technique (e.g., get_technique("G94")) to reinforce “sufficient technique” labeling.

6. must_have_vs_optional
- Must-have retrieval:
  - list_principles()
  - list_guidelines()
  - get_criteria_by_level for A, AA, AAA (three calls)
  - get_criterion for the chosen AA example (e.g., 1.4.3)
  - get_full_criterion_context for the same AA example
  - get_technique for a technique tied to the AA example (e.g., G18)
  - get_glossary_term("conformance")
- Optional supporting retrieval:
  - list_success_criteria for the chosen guideline (mapping clarity)
  - whats_new_in_wcag22()
  - count_criteria(group_by="level") for context only (avoid if not needed)

7. exclusion_rules
- Do not retrieve:
  - Deep lists of techniques or all techniques for any SC (overload).
  - Full conformance claim process details or policy language (out of scope).
  - Implementation details, coding examples, or testing methodologies.
  - Adjacent WAI-ARIA, ATAG, UAAG, or other standards content.
  - Glossary lookups for structural terms like “principle,” “guideline,” “success criterion,” “conformance level,” or “Level A/AA/AAA” (not present in glossary).
  - All SC or all guidelines exhaustive listings (only enough to illustrate structure).

8. sufficiency_condition
Stop retrieval when the evidence pack contains:
- The four principles with descriptions (from list_principles).
- A full view of the guidelines list (from list_guidelines).
- Three concrete SC examples (one A, one AA, one AAA) with IDs and levels.
- One SC’s full context showing its principle and guideline mapping.
- An explicit statement or authoritative cue confirming the cumulative conformance rule (AA requires all A and AA).
- A clear anchor demonstrating techniques are informative/sufficient but not required.
If any of these six items is missing, execute the specified fallback retrieval only until the gap is closed.

9. required_evidence_checks
a. Conformance roll-up rule:
- Check: Does get_glossary_term("conformance") or get_full_criterion_context (for 1.4.3) explicitly state that to claim AA conformance you must meet all Level A and Level AA success criteria (and similarly for AAA)?
- If missing: Fallback — retrieve get_full_criterion_context for a second SC (e.g., ref_id="1.1.1") to locate an explicit statement, or another commonly cited SC’s Understanding that includes this rule.

b. Techniques vs requirements distinction:
- Check: Does get_full_criterion_context for the chosen SC indicate techniques are informative and labeled “sufficient,” or does get_technique("G18") clearly show “Sufficient Techniques” and non-normative status?
- If missing: Fallback — retrieve another technique tied to the SC (e.g., get_technique("G94")) to reinforce “sufficient technique” labeling or retrieve get_full_criterion_context for the A-level example (1.1.1) to capture an Understanding note about techniques being informative.

10. evidence_pack_structure
- hierarchy anchor: Output from list_principles and list_guidelines.
- official requirement: Normative text and level for the chosen SC (get_criterion).
- mapping example: Parent principle/guideline linkage for the chosen SC (from get_criterion/get_full_criterion_context and list_success_criteria under that guideline).
- core fact: Three SC examples (A, AA, AAA) with IDs and levels (from get_criteria_by_level).
- misconception guard:
  - techniques are not required: get_technique (e.g., G18) showing “sufficient technique.”
  - levels are cumulative: explicit statement captured from conformance glossary or Understanding/context.
- contrastive example: A guideline statement vs. SC list under it to show non-testable vs. testable.
- context note (optional): whats_new_in_wcag22 to affirm structure unchanged.

11. adaptation_notes_for_retrieval
- Beginner:
  - Keep to one SC per level (A: 1.1.1; AA: 1.4.3; AAA: 1.4.6).
  - Avoid count_criteria and extra techniques; rely on a single technique example (G18).
  - Ensure the conformance rule statement is present in as few sources as possible (prefer glossary + one SC context).
- Intermediate:
  - Add list_success_criteria for the chosen guideline to show multiple SC in the same bucket.
  - Optionally include whats_new_in_wcag22 for brief 2.2 context.
- Advanced:
  - Choose one SC added in 2.2 for the AA example (e.g., 2.4.11 Focus Not Obscured (Minimum) if present at AA) and retrieve its context to demonstrate integration into the existing structure.
  - Optionally include count_criteria(group_by="level") for analytical perspective.

12. final_retrieval_summary
- Retrieve POUR via list_principles and all guidelines via list_guidelines to anchor the hierarchy.
- Select three representative success criteria (one A, one AA, one AAA) via get_criteria_by_level.
- Deep-dive one AA criterion (e.g., 1.4.3) with get_criterion and get_full_criterion_context to show mapping and context.
- Retrieve get_glossary_term("conformance") to anchor conformance and check for the cumulative levels rule.
- Retrieve one technique for the chosen SC (e.g., get_technique("G18")) to demonstrate “sufficient” and informative status.
- Validate presence of two critical evidence items: cumulative conformance rule and techniques-vs-requirements distinction; execute fallbacks if missing.
- Optionally add whats_new_in_wcag22 to confirm that WCAG 2.2 changed criteria, not principles.
- Exclude exhaustive lists and implementation details; keep retrieval minimal and directly tied to structural teaching.

================================================================================
STEP 3: EXTRACT TOOL CALLS AS JSON
================================================================================

Time: 20.3s | Tokens: 2699/1596
Extracted 13 tool calls:
  1. [must_have] list_principles({})
  2. [must_have] list_guidelines({})
  3. [must_have] get_criteria_by_level({"level": "A", "include_lower": false})
  4. [must_have] get_criteria_by_level({"level": "AA", "include_lower": false})
  5. [must_have] get_criteria_by_level({"level": "AAA", "include_lower": false})
  6. [must_have] get_criterion({"ref_id": "1.4.3"})
  7. [must_have] get_full_criterion_context({"ref_id": "1.4.3"})
  8. [optional] list_success_criteria({"guideline": "1.4 Distinguishable"})
  9. [must_have] get_technique({"id": "G18"})
  10. [must_have] get_glossary_term({"term": "conformance"})
  11. [optional] whats_new_in_wcag22({})
  12. [fallback] get_full_criterion_context({"ref_id": "1.1.1"})
  13. [fallback] get_technique({"id": "G94"})

================================================================================
STEP 4: DETERMINISTIC TOOL EXECUTION (no LLM in loop)
================================================================================

[1] [HIT] [must_have] list_principles({}) -> 637 chars
[2] [HIT] [must_have] list_guidelines({}) -> 1550 chars
[3] [HIT] [must_have] get_criteria_by_level({"level": "A", "include_lower": false}) -> 1055 chars
[4] [HIT] [must_have] get_criteria_by_level({"level": "AA", "include_lower": false}) -> 858 chars
[5] [HIT] [must_have] get_criteria_by_level({"level": "AAA", "include_lower": false}) -> 1092 chars
[6] [HIT] [must_have] get_criterion({"ref_id": "1.4.3"}) -> 16374 chars
[7] [HIT] [must_have] get_full_criterion_context({"ref_id": "1.4.3"}) -> 653 chars
[8] [HIT] [optional] list_success_criteria({"guideline": "1.4 Distinguishable"}) -> 48 chars
[9] [HIT] [must_have] get_technique({"id": "G18"}) -> 424 chars
[10] [HIT] [must_have] get_glossary_term({"term": "conformance"}) -> 166 chars
[11] [HIT] [optional] whats_new_in_wcag22({}) -> 1785 chars
[12] [HIT] [fallback] get_full_criterion_context({"ref_id": "1.1.1"}) -> 687 chars
[13] [HIT] [fallback] get_technique({"id": "G94"}) -> 397 chars

--- Evidence Checks ---
Roll-up rule evidence: FOUND
Techniques vs requirements evidence: FOUND

--- Execution Summary ---
MCP execution time: 0.0s
Total calls: 13 (hits: 13, misses: 0)
Total chars: 25726 | Hit chars: 25726

================================================================================
STEP 6: TOOL CALL TRACES (full content)
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
[CALL 3] [HIT] [must_have] get_criteria_by_level({"level": "A", "include_lower": false})
Result: 1055 chars
----------------------------------------------------------------------
# WCAG 2.2 Level A

Total: 31 success criteria

## Level A (31 criteria)

- **1.1.1** Non-text Content
- **1.2.1** Audio-only and Video-only (Prerecorded)
- **1.2.2** Captions (Prerecorded)
- **1.2.3** Audio Description or Media Alternative (Prerecorded)
- **1.3.1** Info and Relationships
- **1.3.2** Meaningful Sequence
- **1.3.3** Sensory Characteristics
- **1.4.1** Use of Color
- **1.4.2** Audio Control
- **2.1.1** Keyboard
- **2.1.2** No Keyboard Trap
- **2.1.4** Character Key Shortcuts
- **2.2.1** Timing Adjustable
- **2.2.2** Pause, Stop, Hide
- **2.3.1** Three Flashes or Below Threshold
- **2.4.1** Bypass Blocks
- **2.4.2** Page Titled
- **2.4.3** Focus Order
- **2.4.4** Link Purpose (In Context)
- **2.5.1** Pointer Gestures
- **2.5.2** Pointer Cancellation
- **2.5.3** Label in Name
- **2.5.4** Motion Actuation
- **3.1.1** Language of Page
- **3.2.1** On Focus
- **3.2.2** On Input
- **3.2.6** Consistent Help
- **3.3.1** Error Identification
- **3.3.2** Labels or Instructions
- **3.3.7** Redundant Entry
- **4.1.2** Name, Role, Value



----------------------------------------------------------------------
[CALL 4] [HIT] [must_have] get_criteria_by_level({"level": "AA", "include_lower": false})
Result: 858 chars
----------------------------------------------------------------------
# WCAG 2.2 Level AA

Total: 24 success criteria

## Level AA (24 criteria)

- **1.2.4** Captions (Live)
- **1.2.5** Audio Description (Prerecorded)
- **1.3.4** Orientation
- **1.3.5** Identify Input Purpose
- **1.4.3** Contrast (Minimum)
- **1.4.4** Resize Text
- **1.4.5** Images of Text
- **1.4.10** Reflow
- **1.4.11** Non-text Contrast
- **1.4.12** Text Spacing
- **1.4.13** Content on Hover or Focus
- **2.4.5** Multiple Ways
- **2.4.6** Headings and Labels
- **2.4.7** Focus Visible
- **2.4.11** Focus Not Obscured (Minimum)
- **2.5.7** Dragging Movements
- **2.5.8** Target Size (Minimum)
- **3.1.2** Language of Parts
- **3.2.3** Consistent Navigation
- **3.2.4** Consistent Identification
- **3.3.3** Error Suggestion
- **3.3.4** Error Prevention (Legal, Financial, Data)
- **3.3.8** Accessible Authentication (Minimum)
- **4.1.3** Status Messages



----------------------------------------------------------------------
[CALL 5] [HIT] [must_have] get_criteria_by_level({"level": "AAA", "include_lower": false})
Result: 1092 chars
----------------------------------------------------------------------
# WCAG 2.2 Level AAA

Total: 31 success criteria

## Level AAA (31 criteria)

- **1.2.6** Sign Language (Prerecorded)
- **1.2.7** Extended Audio Description (Prerecorded)
- **1.2.8** Media Alternative (Prerecorded)
- **1.2.9** Audio-only (Live)
- **1.3.6** Identify Purpose
- **1.4.6** Contrast (Enhanced)
- **1.4.7** Low or No Background Audio
- **1.4.8** Visual Presentation
- **1.4.9** Images of Text (No Exception)
- **2.1.3** Keyboard (No Exception)
- **2.2.3** No Timing
- **2.2.4** Interruptions
- **2.2.5** Re-authenticating
- **2.2.6** Timeouts
- **2.3.2** Three Flashes
- **2.3.3** Animation from Interactions
- **2.4.8** Location
- **2.4.9** Link Purpose (Link Only)
- **2.4.10** Section Headings
- **2.4.12** Focus Not Obscured (Enhanced)
- **2.4.13** Focus Appearance
- **2.5.5** Target Size (Enhanced)
- **2.5.6** Concurrent Input Mechanisms
- **3.1.3** Unusual Words
- **3.1.4** Abbreviations
- **3.1.5** Reading Level
- **3.1.6** Pronunciation
- **3.2.5** Change on Request
- **3.3.5** Help
- **3.3.6** Error Prevention (All)
- **3.3.9** Accessible Authentication (Enhanced)



----------------------------------------------------------------------
[CALL 6] [HIT] [must_have] get_criterion({"ref_id": "1.4.3"})
Result: 16374 chars
----------------------------------------------------------------------
# 1.4.3 Contrast (Minimum)

**Level:** AA
**Principle:** 1 Perceivable
**Guideline:** 1.4 Distinguishable
**WCAG Versions:** 2.0, 2.1, 2.2

## In Brief

**Goal:** Text can be seen by more people.
**What to do:** Provide sufficient contrast between text and its background.
**Why it's important:** Some people cannot read faint text.

## Description

The visual presentation of text and images of text has a contrast ratio of at least 4.5:1, except for the following:

## Details

- **Large Text:** Large-scale text and images of large-scale text have a contrast ratio of at least 3:1;
- **Incidental:** Text or images of text that are part of an inactive user interface component, that are pure decoration, that are not visible to anyone, or that are part of a picture that contains significant other visual content, have no contrast requirement.
- **Logotypes:** Text that is part of a logo or brand name has no contrast requirement.

## Intent

Intent of Contrast (Minimum)

      The intent of this success criterion is to provide enough contrast between text and its background, so that it can be read by people with moderately low vision or impaired contrast perception, without the use of contrast-enhancing assistive technology.
      


      For all consumers of visual content, adequate light-dark contrast is needed between the relative luminance of text and its background for good readability.
         Many different visual impairments can substantially impact contrast sensitivity, requiring more light-dark contrast, regardless of color (hue).
         For people with color vision deficiency who are not able to distinguish certain shades of color, hue and saturation have minimal or no effect on legibility as assessed by reading performance.
         Further, the inability to distinguish certain shades of color does not negatively affect light-dark contrast perception.
         Therefore, in the recommendation, contrast is calculated in such a way that color (hue) is not a key factor.
      



      Text that is decorative and conveys no information is excluded. For example, if random
         words are used to create a background and the words could be rearranged or substituted
         without changing meaning, then it would be decorative and would not need to meet this
         criterion.
      



      Text that is larger and has wider character strokes is easier to read at lower contrast.
         The contrast requirement for larger text is therefore lower. This allows authors to
         use a wider range of color choices for large text, which is helpful for design of
         pages, particularly titles. 18 point text or 14 point bold text is judged to be large
         enough to require a lower contrast ratio. (See The American Printing House for the
         Blind Guidelines for Large Printing and The Library of Congress Guidelines for Large
         Print under
         Resources). "18 point" and "bold" can both have different meanings in
         different fonts but, except for very thin or unusual fonts, they should be sufficient. Since there
         are so many different fonts, the general measures are used and a note regarding thin or unusual
         fonts is included in the definition for large-scale text.
      



      
         When evaluating this Success Criterion, the font size in points should be obtained
            from the user agent or calculated on font metrics in the way that user agents do.
            Point sizes are based on the CSS `pt` size as defined in
            CSS3 Values. The ratio between
            sizes in points and CSS pixels is `1pt = 1.333px`, therefore `14pt`
            and `18pt` are equivalent to approximately `18.5px` and `24px`.
         


         Because different image editing applications default to different pixel densities
            (e.g., `72ppi` or `96ppi`), specifying point sizes for fonts from within an
            image editing application can be unreliable when it comes to presenting text at a specific size.
            When creating images of large-scale text, authors should ensure that the text in the
            resulting image is roughly equivalent to 1.2 and 1.5 em or to 120% or 150% of the
            default size for body text. For example, for a `72ppi` image, an author would need
            to use approximately 19pt and 24pt font sizes in order to successfully present images
            of large-scale text to a user.
         


         The 3:1 and 4.5:1 contrast ratios referenced in this success criterion are intended to be
            treated as threshold values. When comparing the computed contrast ratio to the Success Criterion
            ratio, the computed values should not be rounded (e.g., 4.499:1 would not meet the 4.5:1 threshold).


      



      
         Because authors do not have control over user settings for font smoothing/anti-aliasing, when evaluating this
            Success Criterion, refer to the foreground and background colors obtained from the user agent, or the underlying
            markup and stylesheets, rather than the text as presented on screen.


         Due to anti-aliasing, particularly thin or unusual fonts may be rendered by user agents with a much fainter
            color than the actual text color defined in the underlying CSS. This can lead to situations where text has
            a contrast ratio that nominally passes the Success Criterion, but has a much lower contrast in practice.
            In these cases, best practice would be for authors to choose a font with stronger/thicker lines,
            or to aim for a foreground/background color combination that exceeds the normative requirements
            of this success criterion.
         


      



      The contrast requirements for text also apply to images of text
         (text that has been rendered into pixels and then stored in an image format) - see
         Success Criterion 1.4.5: Images of Text.
      



      This requirement applies to situations in which images of text were intended to be
         understood as text. Incidental text, such as in photographs that happen to include
         a street sign, are not included. Nor is text that for some reason is designed to be
         invisible to all viewers. Stylized text, such as in corporate logos, should be treated
         in terms of its function on the page, which may or may not warrant including the content
         in the text alternative. Corporate visual guidelines beyond logo and logotype are
         not included in the exception.
      



      In this provision there is an exception that reads "that are part of a picture that
         contains significant other visual content,". This exception is intended to separate
         pictures that have text in them from images of text that are done to replace text
         in order to get a particular look.
      



      
         Images of text do not scale as well as text because they tend to pixelate. It is also
            harder to change foreground and background contrast and color combinations for images
            of text, which is necessary for some users. Therefore, we suggest using text wherever
            possible, and when not, consider supplying an image of higher resolution.
         


      



      This success criterion applies to text in the page, including
         placeholder text and text that is shown when a pointer is hovering over an object
         or when an object has keyboard focus. If any of these are used in a page, the text
         needs to provide sufficient contrast.
      



      Although this success criterion only applies to text, similar issues occur for content presented
         in charts, graphs, diagrams, and other non-text-based information, which is covered by
         Success Criterion 1.4.11 Non-Text Contrast.
      



      See also
         1.4.6: Contrast (Enhanced).
      



      
         Rationale for the Ratios Chosen

         A contrast ratio of 3:1 is the minimum level recommended by [[ISO-9241-3]] and [[ANSI-HFES-100-1988]]
            for standard text and vision. The 4.5:1 ratio is used in this success criterion to account
            for the loss in contrast that results from moderately low visual acuity, congenital
            or acquired color deficiencies, or the loss of contrast sensitivity that typically
            accompanies aging.
         



         The rationale is based on a) adoption of the 3:1 contrast ratio for minimum acceptable
            contrast for normal observers, in the ANSI standard, and b) the empirical finding
            that in the population, visual acuity of 20/40 is associated with a contrast sensitivity
            loss of roughly 1.5 [[ARDITI-FAYE]]. A user with 20/40 would thus require a contrast ratio of
            `3 * 1.5 = 4.5 to 1`. Following analogous empirical findings and the same logic,
            the user with 20/80 visual acuity would require contrast of about 7:1. This ratio is used in
            Success Criterion 1.4.6.
         



         Hues are perceived differently by users with color vision deficiencies (both congenital
            and acquired) resulting in different colors and relative luminance contrasts than
            for normally sighted users. Because of this, effective contrast and readability are
            different for this population. However, color deficiencies are so diverse that prescribing
            effective general use color pairs (for contrast) based on quantitative data is not
            feasible. Requiring good luminance contrast accommodates this by requiring contrast
            that is independent of color perception. Fortunately, most of the luminance contribution
            is from the mid and long wave receptors which largely overlap in their spectral responses.
            The result is that effective luminance contrast can generally be computed without
            regard to specific color deficiency, except for the use of predominantly long wavelength
            colors against darker colors (generally appearing black) for those who have protanopia.
            (We provide an advisory technique on avoiding red on black for that reason). For more
            information see [[ARDITI-KNOBLAUCH-1994]]
            [[ARDITI-KNOBLAUCH-1996]]
            [[ARDITI]].
         


         
            Some people with cognitive disabilities require color combinations or hues that have
               low contrast, and therefore we allow and encourage authors to provide mechanisms to
               adjust the foreground and background colors of the content. Some of the combinations
               that could be chosen may have contrast levels that will be lower than those those
               specified here. This is not a violation of this Success Criterion, provided
               there is a mechanism that will return to the required values set out here.
            


         


         The contrast ratio of 4.5:1 was chosen for level AA because it compensated for the
            loss in contrast sensitivity usually experienced by users with vision loss equivalent
            to approximately 20/40 vision. (20/40 calculates to approximately 4.5:1.) 20/40 is
            commonly reported as typical visual acuity of elders at roughly age 80. [[GITTINGS-FOZARD]]
         


         The contrast ratio of 7:1 was chosen for level AAA because it compensated for the
            loss in contrast sensitivity usually experienced by users with vision loss equivalent
            to approximately 20/80 vision. People with more than this degree of vision loss usually
            use assistive technologies to access their content (and the assistive technologies
            usually have contrast enhancing, as well as magnification capability built into them).
            The 7:1 level therefore generally provides compensation for the loss in contrast sensitivity
            experienced by users with low vision who do not use assistive technology and provides
            contrast enhancement for color deficiency as well.
         


         
            Calculations in [[ISO-9241-3]] and [[ANSI-HFES-100-1988]] are for body text. A relaxed contrast
               ratio is provided for text that is much larger.


         


      
      
         Notes on formula
         Conversion from nonlinear to linear RGB values is based on IEC/4WD 61966-2-1 [[IEC-4WD]].


         The formula (`L1/L2`) for contrast is based on [[ISO-9241-3]] and [[ANSI-HFES-100-1988]] standards.


         The ANSI/HFS 100-1988 standard calls for the contribution from ambient light to be
            included in the calculation of L1 and L2. The `.05` value used is based on Typical Viewing
            Flare from [[IEC-4WD]].
         


         This success criterion and its definitions use the terms "contrast ratio" and "relative
            luminance" rather than "luminance" to reflect the fact that web content does not emit
            light itself. The contrast ratio gives a measure of the relative luminance that would
            result when displayed. (Because it is a ratio, it is dimensionless.)
         


         
            
               Refer to
               related resources for a list of tools that utilize the contrast ratio
               to analyze the contrast of web content.
            


            See also
               2.4.7: Focus Visible for techniques for indicating keyboard focus.

## Benefits

- People with low vision often have difficulty reading text that does not contrast with
            its background. This can be exacerbated if the person has a color vision deficiency
            that lowers the contrast even further. Providing a minimum luminance contrast ratio
            between the text and its background can make the text more readable even if the person
            does not see the full range of colors. It also works for the rare individuals who
            see no color.

## Resources

- [Colour Contrast Analyser application](https://www.tpgi.com/color-contrast-checker/)
- [Luminosity Colour Contrast Ratio Analyser](https://juicystudio.com/services/luminositycontrastratio.php)
- [Colour Contrast Check](https://snook.ca/technical/colour_contrast/colour.html)
- [Contrast Ratio Calculator](https://www.msfw.com/Services/ContrastRatioCalculator)
- [Adobe Color - Color Contrast Analyzer Tool](https://color.adobe.com/create/color-contrast-analyzer)
- [Atypical colour response](https://www.w3.org/Graphics/atypical-color-response)
- [Colors On the Web Color Contrast Analyzer](http://www.colorsontheweb.com/colorcontrast.asp)
- [Tool to convert images based on color loss](https://www.vischeck.com/daltonize/runDaltonize.php)
- [List of color contrast tools](https://www.456bereastreet.com/archive/200709/10_colour_contrast_checking_tools_to_improve_the_accessibility_of_your_design/)
- [The American Printing House for the Blind Guidelines for Large Printing](https://www.aph.org/resources/large-print-guidelines/)
- [National Library Service for the Blind and Physically Handicapped (NLS), The Library of Congress reference guide on large print materials](https://www.loc.gov/nls/resources/general-resources-on-disabilities/large-print-materials/)
- [Types of Color Vision Deficiency, National Eye Institute (NEI), National Institutes of Health (NIH), U.S. Department of Health and Human Services (HHS)](https://www.nei.nih.gov/learn-about-eye-health/eye-conditions-and-diseases/color-blindness/types-color-vision-deficiency)
- [Effects of chromatic and luminance contrast on reading, Knoblauch et al., 1991](https://doi.org/10.1364/JOSAA.8.000428)
- [Achromatic luminance contrast sensitivity in X-linked color-deficient observers: an addition to the debate, Márta Janáky et al., 2013](https://pubmed.ncbi.nlm.nih.gov/24103453/)
- [Contrast sensitivity of patients with congenital color vision deficiency, Cagri Ilhan et al., 2018](https://link.springer.com/article/10.1007/s10792-018-0881-7)

## Links

- [WCAG Specification](https://www.w3.org/TR/WCAG22/#contrast-minimum)
- [Understanding 1.4.3](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
- [How to Meet 1.4.3](https://www.w3.org/WAI/WCAG22/quickref/#contrast-minimum)


----------------------------------------------------------------------
[CALL 7] [HIT] [must_have] get_full_criterion_context({"ref_id": "1.4.3"})
Result: 653 chars
----------------------------------------------------------------------
# Complete Context: 1.4.3 Contrast (Minimum)

## Overview

**Level:** AA
**Principle:** 1 Perceivable
**Guideline:** 1.4 Distinguishable
**WCAG Versions:** 2.0, 2.1, 2.2

The visual presentation of text and images of text has a contrast ratio of at least 4.5:1, except for the following:

## Techniques Summary

- **Sufficient:** 6 techniques
- **Advisory:** 1 techniques
- **Failure:** 2 techniques

## Links

- [WCAG Specification](https://www.w3.org/TR/WCAG22/#contrast-minimum)
- [Understanding 1.4.3](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
- [How to Meet 1.4.3](https://www.w3.org/WAI/WCAG22/quickref/#contrast-minimum)


----------------------------------------------------------------------
[CALL 8] [HIT] [optional] list_success_criteria({"guideline": "1.4 Distinguishable"})
Result: 48 chars
----------------------------------------------------------------------
No success criteria found matching your filters.

----------------------------------------------------------------------
[CALL 9] [HIT] [must_have] get_technique({"id": "G18"})
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
[CALL 10] [HIT] [must_have] get_glossary_term({"term": "conformance"})
Result: 166 chars
----------------------------------------------------------------------
# conformance

satisfying all the requirements of a given standard, guideline or specification

[View in WCAG 2.2 Glossary](https://www.w3.org/TR/WCAG22/#dfn-conform)

----------------------------------------------------------------------
[CALL 11] [HIT] [optional] whats_new_in_wcag22({})
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
[CALL 13] [HIT] [fallback] get_technique({"id": "G94"})
Result: 397 chars
----------------------------------------------------------------------
# G94: Providing short text alternative for non-text content that serves the same purpose and presents the same information as the non-text content

**Technology:** general
**Types:** sufficient
**Applies to:** 1 success criteria

## Related Success Criteria

- **1.1.1** Non-text Content (Level A)

## Links

- [Full Technique Documentation](https://www.w3.org/WAI/WCAG22/Techniques/general/G94)


================================================================================
STEP 7: FINAL TEACHING CONTENT (deduplicated hits)
================================================================================

Unique hit sections: 13
Final content: 25810 chars

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

# WCAG 2.2 Level A

Total: 31 success criteria

## Level A (31 criteria)

- **1.1.1** Non-text Content
- **1.2.1** Audio-only and Video-only (Prerecorded)
- **1.2.2** Captions (Prerecorded)
- **1.2.3** Audio Description or Media Alternative (Prerecorded)
- **1.3.1** Info and Relationships
- **1.3.2** Meaningful Sequence
- **1.3.3** Sensory Characteristics
- **1.4.1** Use of Color
- **1.4.2** Audio Control
- **2.1.1** Keyboard
- **2.1.2** No Keyboard Trap
- **2.1.4** Character Key Shortcuts
- **2.2.1** Timing Adjustable
- **2.2.2** Pause, Stop, Hide
- **2.3.1** Three Flashes or Below Threshold
- **2.4.1** Bypass Blocks
- **2.4.2** Page Titled
- **2.4.3** Focus Order
- **2.4.4** Link Purpose (In Context)
- **2.5.1** Pointer Gestures
- **2.5.2** Pointer Cancellation
- **2.5.3** Label in Name
- **2.5.4** Motion Actuation
- **3.1.1** Language of Page
- **3.2.1** On Focus
- **3.2.2** On Input
- **3.2.6** Consistent Help
- **3.3.1** Error Identification
- **3.3.2** Labels or Instructions
- **3.3.7** Redundant Entry
- **4.1.2** Name, Role, Value



---

# WCAG 2.2 Level AA

Total: 24 success criteria

## Level AA (24 criteria)

- **1.2.4** Captions (Live)
- **1.2.5** Audio Description (Prerecorded)
- **1.3.4** Orientation
- **1.3.5** Identify Input Purpose
- **1.4.3** Contrast (Minimum)
- **1.4.4** Resize Text
- **1.4.5** Images of Text
- **1.4.10** Reflow
- **1.4.11** Non-text Contrast
- **1.4.12** Text Spacing
- **1.4.13** Content on Hover or Focus
- **2.4.5** Multiple Ways
- **2.4.6** Headings and Labels
- **2.4.7** Focus Visible
- **2.4.11** Focus Not Obscured (Minimum)
- **2.5.7** Dragging Movements
- **2.5.8** Target Size (Minimum)
- **3.1.2** Language of Parts
- **3.2.3** Consistent Navigation
- **3.2.4** Consistent Identification
- **3.3.3** Error Suggestion
- **3.3.4** Error Prevention (Legal, Financial, Data)
- **3.3.8** Accessible Authentication (Minimum)
- **4.1.3** Status Messages



---

# WCAG 2.2 Level AAA

Total: 31 success criteria

## Level AAA (31 criteria)

- **1.2.6** Sign Language (Prerecorded)
- **1.2.7** Extended Audio Description (Prerecorded)
- **1.2.8** Media Alternative (Prerecorded)
- **1.2.9** Audio-only (Live)
- **1.3.6** Identify Purpose
- **1.4.6** Contrast (Enhanced)
- **1.4.7** Low or No Background Audio
- **1.4.8** Visual Presentation
- **1.4.9** Images of Text (No Exception)
- **2.1.3** Keyboard (No Exception)
- **2.2.3** No Timing
- **2.2.4** Interruptions
- **2.2.5** Re-authenticating
- **2.2.6** Timeouts
- **2.3.2** Three Flashes
- **2.3.3** Animation from Interactions
- **2.4.8** Location
- **2.4.9** Link Purpose (Link Only)
- **2.4.10** Section Headings
- **2.4.12** Focus Not Obscured (Enhanced)
- **2.4.13** Focus Appearance
- **2.5.5** Target Size (Enhanced)
- **2.5.6** Concurrent Input Mechanisms
- **3.1.3** Unusual Words
- **3.1.4** Abbreviations
- **3.1.5** Reading Level
- **3.1.6** Pronunciation
- **3.2.5** Change on Request
- **3.3.5** Help
- **3.3.6** Error Prevention (All)
- **3.3.9** Accessible Authentication (Enhanced)



---

# 1.4.3 Contrast (Minimum)

**Level:** AA
**Principle:** 1 Perceivable
**Guideline:** 1.4 Distinguishable
**WCAG Versions:** 2.0, 2.1, 2.2

## In Brief

**Goal:** Text can be seen by more people.
**What to do:** Provide sufficient contrast between text and its background.
**Why it's important:** Some people cannot read faint text.

## Description

The visual presentation of text and images of text has a contrast ratio of at least 4.5:1, except for the following:

## Details

- **Large Text:** Large-scale text and images of large-scale text have a contrast ratio of at least 3:1;
- **Incidental:** Text or images of text that are part of an inactive user interface component, that are pure decoration, that are not visible to anyone, or that are part of a picture that contains significant other visual content, have no contrast requirement.
- **Logotypes:** Text that is part of a logo or brand name has no contrast requirement.

## Intent

Intent of Contrast (Minimum)

      The intent of this success criterion is to provide enough contrast between text and its background, so that it can be read by people with moderately low vision or impaired contrast perception, without the use of contrast-enhancing assistive technology.
      


      For all consumers of visual content, adequate light-dark contrast is needed between the relative luminance of text and its background for good readability.
         Many different visual impairments can substantially impact contrast sensitivity, requiring more light-dark contrast, regardless of color (hue).
         For people with color vision deficiency who are not able to distinguish certain shades of color, hue and saturation have minimal or no effect on legibility as assessed by reading performance.
         Further, the inability to distinguish certain shades of color does not negatively affect light-dark contrast perception.
         Therefore, in the recommendation, contrast is calculated in such a way that color (hue) is not a key factor.
      



      Text that is decorative and conveys no information is excluded. For example, if random
         words are used to create a background and the words could be rearranged or substituted
         without changing meaning, then it would be decorative and would not need to meet this
         criterion.
      



      Text that is larger and has wider character strokes is easier to read at lower contrast.
         The contrast requirement for larger text is therefore lower. This allows authors to
         use a wider range of color choices for large text, which is helpful for design of
         pages, particularly titles. 18 point text or 14 point bold text is judged to be large
         enough to require a lower contrast ratio. (See The American Printing House for the
         Blind Guidelines for Large Printing and The Library of Congress Guidelines for Large
         Print under
         Resources). "18 point" and "bold" can both have different meanings in
         different fonts but, except for very thin or unusual fonts, they should be sufficient. Since there
         are so many different fonts, the general measures are used and a note regarding thin or unusual
         fonts is included in the definition for large-scale text.
      



      
         When evaluating this Success Criterion, the font size in points should be obtained
            from the user agent or calculated on font metrics in the way that user agents do.
            Point sizes are based on the CSS `pt` size as defined in
            CSS3 Values. The ratio between
            sizes in points and CSS pixels is `1pt = 1.333px`, therefore `14pt`
            and `18pt` are equivalent to approximately `18.5px` and `24px`.
         


         Because different image editing applications default to different pixel densities
            (e.g., `72ppi` or `96ppi`), specifying point sizes for fonts from within an
            image editing application can be unreliable when it comes to presenting text at a specific size.
            When creating images of large-scale text, authors should ensure that the text in the
            resulting image is roughly equivalent to 1.2 and 1.5 em or to 120% or 150% of the
            default size for body text. For example, for a `72ppi` image, an author would need
            to use approximately 19pt and 24pt font sizes in order to successfully present images
            of large-scale text to a user.
         


         The 3:1 and 4.5:1 contrast ratios referenced in this success criterion are intended to be
            treated as threshold values. When comparing the computed contrast ratio to the Success Criterion
            ratio, the computed values should not be rounded (e.g., 4.499:1 would not meet the 4.5:1 threshold).


      



      
         Because authors do not have control over user settings for font smoothing/anti-aliasing, when evaluating this
            Success Criterion, refer to the foreground and background colors obtained from the user agent, or the underlying
            markup and stylesheets, rather than the text as presented on screen.


         Due to anti-aliasing, particularly thin or unusual fonts may be rendered by user agents with a much fainter
            color than the actual text color defined in the underlying CSS. This can lead to situations where text has
            a contrast ratio that nominally passes the Success Criterion, but has a much lower contrast in practice.
            In these cases, best practice would be for authors to choose a font with stronger/thicker lines,
            or to aim for a foreground/background color combination that exceeds the normative requirements
            of this success criterion.
         


      



      The contrast requirements for text also apply to images of text
         (text that has been rendered into pixels and then stored in an image format) - see
         Success Criterion 1.4.5: Images of Text.
      



      This requirement applies to situations in which images of text were intended to be
         understood as text. Incidental text, such as in photographs that happen to include
         a street sign, are not included. Nor is text that for some reason is designed to be
         invisible to all viewers. Stylized text, such as in corporate logos, should be treated
         in terms of its function on the page, which may or may not warrant including the content
         in the text alternative. Corporate visual guidelines beyond logo and logotype are
         not included in the exception.
      



      In this provision there is an exception that reads "that are part of a picture that
         contains significant other visual content,". This exception is intended to separate
         pictures that have text in them from images of text that are done to replace text
         in order to get a particular look.
      



      
         Images of text do not scale as well as text because they tend to pixelate. It is also
            harder to change foreground and background contrast and color combinations for images
            of text, which is necessary for some users. Therefore, we suggest using text wherever
            possible, and when not, consider supplying an image of higher resolution.
         


      



      This success criterion applies to text in the page, including
         placeholder text and text that is shown when a pointer is hovering over an object
         or when an object has keyboard focus. If any of these are used in a page, the text
         needs to provide sufficient contrast.
      



      Although this success criterion only applies to text, similar issues occur for content presented
         in charts, graphs, diagrams, and other non-text-based information, which is covered by
         Success Criterion 1.4.11 Non-Text Contrast.
      



      See also
         1.4.6: Contrast (Enhanced).
      



      
         Rationale for the Ratios Chosen

         A contrast ratio of 3:1 is the minimum level recommended by [[ISO-9241-3]] and [[ANSI-HFES-100-1988]]
            for standard text and vision. The 4.5:1 ratio is used in this success criterion to account
            for the loss in contrast that results from moderately low visual acuity, congenital
            or acquired color deficiencies, or the loss of contrast sensitivity that typically
            accompanies aging.
         



         The rationale is based on a) adoption of the 3:1 contrast ratio for minimum acceptable
            contrast for normal observers, in the ANSI standard, and b) the empirical finding
            that in the population, visual acuity of 20/40 is associated with a contrast sensitivity
            loss of roughly 1.5 [[ARDITI-FAYE]]. A user with 20/40 would thus require a contrast ratio of
            `3 * 1.5 = 4.5 to 1`. Following analogous empirical findings and the same logic,
            the user with 20/80 visual acuity would require contrast of about 7:1. This ratio is used in
            Success Criterion 1.4.6.
         



         Hues are perceived differently by users with color vision deficiencies (both congenital
            and acquired) resulting in different colors and relative luminance contrasts than
            for normally sighted users. Because of this, effective contrast and readability are
            different for this population. However, color deficiencies are so diverse that prescribing
            effective general use color pairs (for contrast) based on quantitative data is not
            feasible. Requiring good luminance contrast accommodates this by requiring contrast
            that is independent of color perception. Fortunately, most of the luminance contribution
            is from the mid and long wave receptors which largely overlap in their spectral responses.
            The result is that effective luminance contrast can generally be computed without
            regard to specific color deficiency, except for the use of predominantly long wavelength
            colors against darker colors (generally appearing black) for those who have protanopia.
            (We provide an advisory technique on avoiding red on black for that reason). For more
            information see [[ARDITI-KNOBLAUCH-1994]]
            [[ARDITI-KNOBLAUCH-1996]]
            [[ARDITI]].
         


         
            Some people with cognitive disabilities require color combinations or hues that have
               low contrast, and therefore we allow and encourage authors to provide mechanisms to
               adjust the foreground and background colors of the content. Some of the combinations
               that could be chosen may have contrast levels that will be lower than those those
               specified here. This is not a violation of this Success Criterion, provided
               there is a mechanism that will return to the required values set out here.
            


         


         The contrast ratio of 4.5:1 was chosen for level AA because it compensated for the
            loss in contrast sensitivity usually experienced by users with vision loss equivalent
            to approximately 20/40 vision. (20/40 calculates to approximately 4.5:1.) 20/40 is
            commonly reported as typical visual acuity of elders at roughly age 80. [[GITTINGS-FOZARD]]
         


         The contrast ratio of 7:1 was chosen for level AAA because it compensated for the
            loss in contrast sensitivity usually experienced by users with vision loss equivalent
            to approximately 20/80 vision. People with more than this degree of vision loss usually
            use assistive technologies to access their content (and the assistive technologies
            usually have contrast enhancing, as well as magnification capability built into them).
            The 7:1 level therefore generally provides compensation for the loss in contrast sensitivity
            experienced by users with low vision who do not use assistive technology and provides
            contrast enhancement for color deficiency as well.
         


         
            Calculations in [[ISO-9241-3]] and [[ANSI-HFES-100-1988]] are for body text. A relaxed contrast
               ratio is provided for text that is much larger.


         


      
      
         Notes on formula
         Conversion from nonlinear to linear RGB values is based on IEC/4WD 61966-2-1 [[IEC-4WD]].


         The formula (`L1/L2`) for contrast is based on [[ISO-9241-3]] and [[ANSI-HFES-100-1988]] standards.


         The ANSI/HFS 100-1988 standard calls for the contribution from ambient light to be
            included in the calculation of L1 and L2. The `.05` value used is based on Typical Viewing
            Flare from [[IEC-4WD]].
         


         This success criterion and its definitions use the terms "contrast ratio" and "relative
            luminance" rather than "luminance" to reflect the fact that web content does not emit
            light itself. The contrast ratio gives a measure of the relative luminance that would
            result when displayed. (Because it is a ratio, it is dimensionless.)
         


         
            
               Refer to
               related resources for a list of tools that utilize the contrast ratio
               to analyze the contrast of web content.
            


            See also
               2.4.7: Focus Visible for techniques for indicating keyboard focus.

## Benefits

- People with low vision often have difficulty reading text that does not contrast with
            its background. This can be exacerbated if the person has a color vision deficiency
            that lowers the contrast even further. Providing a minimum luminance contrast ratio
            between the text and its background can make the text more readable even if the person
            does not see the full range of colors. It also works for the rare individuals who
            see no color.

## Resources

- [Colour Contrast Analyser application](https://www.tpgi.com/color-contrast-checker/)
- [Luminosity Colour Contrast Ratio Analyser](https://juicystudio.com/services/luminositycontrastratio.php)
- [Colour Contrast Check](https://snook.ca/technical/colour_contrast/colour.html)
- [Contrast Ratio Calculator](https://www.msfw.com/Services/ContrastRatioCalculator)
- [Adobe Color - Color Contrast Analyzer Tool](https://color.adobe.com/create/color-contrast-analyzer)
- [Atypical colour response](https://www.w3.org/Graphics/atypical-color-response)
- [Colors On the Web Color Contrast Analyzer](http://www.colorsontheweb.com/colorcontrast.asp)
- [Tool to convert images based on color loss](https://www.vischeck.com/daltonize/runDaltonize.php)
- [List of color contrast tools](https://www.456bereastreet.com/archive/200709/10_colour_contrast_checking_tools_to_improve_the_accessibility_of_your_design/)
- [The American Printing House for the Blind Guidelines for Large Printing](https://www.aph.org/resources/large-print-guidelines/)
- [National Library Service for the Blind and Physically Handicapped (NLS), The Library of Congress reference guide on large print materials](https://www.loc.gov/nls/resources/general-resources-on-disabilities/large-print-materials/)
- [Types of Color Vision Deficiency, National Eye Institute (NEI), National Institutes of Health (NIH), U.S. Department of Health and Human Services (HHS)](https://www.nei.nih.gov/learn-about-eye-health/eye-conditions-and-diseases/color-blindness/types-color-vision-deficiency)
- [Effects of chromatic and luminance contrast on reading, Knoblauch et al., 1991](https://doi.org/10.1364/JOSAA.8.000428)
- [Achromatic luminance contrast sensitivity in X-linked color-deficient observers: an addition to the debate, Márta Janáky et al., 2013](https://pubmed.ncbi.nlm.nih.gov/24103453/)
- [Contrast sensitivity of patients with congenital color vision deficiency, Cagri Ilhan et al., 2018](https://link.springer.com/article/10.1007/s10792-018-0881-7)

## Links

- [WCAG Specification](https://www.w3.org/TR/WCAG22/#contrast-minimum)
- [Understanding 1.4.3](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
- [How to Meet 1.4.3](https://www.w3.org/WAI/WCAG22/quickref/#contrast-minimum)


---

# Complete Context: 1.4.3 Contrast (Minimum)

## Overview

**Level:** AA
**Principle:** 1 Perceivable
**Guideline:** 1.4 Distinguishable
**WCAG Versions:** 2.0, 2.1, 2.2

The visual presentation of text and images of text has a contrast ratio of at least 4.5:1, except for the following:

## Techniques Summary

- **Sufficient:** 6 techniques
- **Advisory:** 1 techniques
- **Failure:** 2 techniques

## Links

- [WCAG Specification](https://www.w3.org/TR/WCAG22/#contrast-minimum)
- [Understanding 1.4.3](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
- [How to Meet 1.4.3](https://www.w3.org/WAI/WCAG22/quickref/#contrast-minimum)


---

No success criteria found matching your filters.

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

# conformance

satisfying all the requirements of a given standard, guideline or specification

[View in WCAG 2.2 Glossary](https://www.w3.org/TR/WCAG22/#dfn-conform)

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

# G94: Providing short text alternative for non-text content that serves the same purpose and presents the same information as the non-text content

**Technology:** general
**Types:** sufficient
**Applies to:** 1 success criteria

## Related Success Criteria

- **1.1.1** Non-text Content (Level A)

## Links

- [Full Technique Documentation](https://www.w3.org/WAI/WCAG22/Techniques/general/G94)


================================================================================
PIPELINE TOTALS
================================================================================
LLM calls: 3 (teaching plan + retrieval plan + JSON extraction)
LLM time: 103.8s
LLM tokens: prompt=7407 completion=8091 total=15498
MCP calls: 13 (hits: 13, misses: 0)
MCP time: 0.0s
Final content: 13 unique sections, 25810 chars