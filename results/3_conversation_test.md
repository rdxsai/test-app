# Conversation Test: Apply the five rules for using ARIA correctly

**Objective ID**: `038d7bf5-eb16-4ac0-a22b-42c8fa964d97`
**Student**: `test-conv-195112` (LLM-driven agent)
**Session**: `guided-test-195112`
**Run at**: 2026-04-08T19:58:09.773587
**Total turns**: 14
**Total tutor time**: 393.9s

---

## Pipeline Artifacts

### Teaching Plan (18170 chars)

```
## 1. objective_text
Apply the five rules for using ARIA correctly

## 2. plain_language_goal
Use the five main ARIA rules to decide when ARIA should or should not be added, and apply those rules correctly in realistic markup situations.

## 3. mastery_definition
A student has mastered this objective when they can:

- state or recognize the purpose of the five ARIA rules in practical terms
- inspect a small HTML example and identify whether ARIA is needed or unnecessary
- choose the correct action based on the rules:
  - use native HTML instead of ARIA when appropriate
  - avoid changing native semantics incorrectly
  - ensure required states/properties are present when a role is used
  - use only supported ARIA attributes for a given role
  - avoid redundant or conflicting ARIA that duplicates implicit semantics
- explain their choice by referencing the relevant rule
- correct at least one flawed example containing multiple ARIA misuse patterns

## 4. objective_type
- conceptual understanding
- decision-making
- application
- debugging/evaluation

## 5. prerequisite_knowledge

### essential prerequisites
- Basic understanding of HTML elements and attributes
- Basic distinction between native HTML semantics and presentational styling
- Recognition that assistive technologies rely on semantic information
- Familiarity with common semantic elements such as button, link, input, heading, nav, main, and form controls

### helpful but nonessential prerequisites
- Basic idea of what ARIA is and that it can add accessibility information
- Awareness of roles, states, and properties at a high level
- Experience reading simple code snippets
- Basic awareness of screen readers or accessibility trees

## 6. prerequisite_gap_policy
If the learner lacks essential prerequisites, the tutor should pause this objective and provide a very short prerequisite bridge before continuing. That bridge should cover only the minimum needed:

- what native HTML semantics are
- why semantic elements matter for assistive technologies
- the difference between an element’s built-in meaning and added ARIA

The tutor should not proceed into the five rules until the learner can correctly identify at least a few native semantic elements and explain why “use the right HTML element first” matters.

## 7. concept_decomposition
1. ARIA is supplemental accessibility metadata, not a replacement for correct HTML.
2. Native HTML elements already carry built-in semantics and behavior.
3. Rule 1: If a native HTML element or attribute can provide the needed semantics/behavior, prefer it over ARIA.
4. Rule 2: Do not change native semantics unless there is a very strong, valid reason.
5. Role usage can create obligations: some roles require particular states/properties.
6. Rule 3: All required ARIA states/properties for a chosen role must be present and valid.
7. ARIA attributes are role-dependent; not every attribute is valid on every role.
8. Rule 4: Use only ARIA states/properties supported for the role in question.
9. Some HTML elements already expose implicit roles/states.
10. Rule 5: Do not add redundant ARIA that repeats implicit native semantics.
11. Conflicts between native semantics and ARIA can harm accessibility rather than help it.
12. Applying the five rules often means deciding among: remove ARIA, replace custom markup with native HTML, add missing required ARIA, or revise invalid combinations.
13. A single snippet may violate more than one rule at once.
14. Correct application requires justification: identifying which rule applies and why.

## 8. dependency_order

### Ordered sequence with dependencies
1. **ARIA is supplemental accessibility metadata, not a replacement for correct HTML.**
   - No dependency
2. **Native HTML elements already carry built-in semantics and behavior.**
   - Depends on 1
3. **Rule 1: If a native HTML element or attribute can provide the needed semantics/behavior, prefer it over ARIA.**
   - Depends on 1, 2
4. **Rule 2: Do not change native semantics unless there is a very strong, valid reason.**
   - Depends on 2, 3
5. **Role usage can create obligations: some roles require particular states/properties.**
   - Depends on 1
6. **Rule 3: All required ARIA states/properties for a chosen role must be present and valid.**
   - Depends on 5
7. **ARIA attributes are role-dependent; not every attribute is valid on every role.**
   - Depends on 5
8. **Rule 4: Use only ARIA states/properties supported for the role in question.**
   - Depends on 7
9. **Some HTML elements already expose implicit roles/states.**
   - Depends on 2
10. **Rule 5: Do not add redundant ARIA that repeats implicit native semantics.**
   - Depends on 9
11. **Conflicts between native semantics and ARIA can harm accessibility rather than help it.**
   - Depends on 4, 8, 10
12. **Applying the five rules often means deciding among: remove ARIA, replace custom markup with native HTML, add missing required ARIA, or revise invalid combinations.**
   - Depends on 3, 4, 6, 8, 10, 11
13. **A single snippet may violate more than one rule at once.**
   - Depends on 12
14. **Correct application requires justification: identifying which rule applies and why.**
   - Depends on 12, 13

### Why this sequence is instructionally sound
- It starts with the foundational idea that ARIA is secondary to HTML, preventing later rule memorization without conceptual grounding.
- It introduces native semantics before rules that depend on recognizing proper HTML usage.
- It teaches the “prefer native” and “don’t override native” rules early because they are the highest-frequency and lowest-complexity decisions.
- It then moves into role-specific constraints, which are more technical and require understanding that ARIA choices create obligations.
- Redundancy is taught after implicit semantics, since students must first know what is already provided.
- Multi-rule diagnosis and justification are saved for the end to avoid overload and to support transfer.

## 9. likely_misconceptions
- “ARIA always improves accessibility.”
- “More ARIA is better.”
- “ARIA can fix poor HTML automatically.”
- “role='button' is equivalent to using a real button in all important ways.”
- “If code passes visual inspection, the ARIA is probably fine.”
- “Any ARIA attribute can be added to any element if it seems useful.”
- “If a role is valid, its required states/properties are optional.”
- “Adding explicit role='button' to a button is helpful.”
- “Changing a native element’s role is harmless if the UI looks right.”
- “ARIA rules are mainly about syntax, not user experience.”
- “If custom widgets use ARIA, they do not need complete semantic/state support.”
- Confusing native HTML attributes with ARIA attributes
- Confusing redundant ARIA with descriptive labeling
- Believing every exception or advanced pattern should be introduced in this objective

## 10. explanation_vs_question_strategy

### 1. ARIA is supplemental accessibility metadata, not a replacement for correct HTML.
- **Begin with:** brief explanation
- **Why:** This is a framing concept that students often do not already hold accurately; a concise setup prevents confusion.

### 2. Native HTML elements already carry built-in semantics and behavior.
- **Begin with:** guided questioning
- **Why:** Many learners can already name common elements and their purpose; questioning activates prior knowledge.

### 3. Rule 1: If a native HTML element or attribute can provide the needed semantics/behavior, prefer it over ARIA.
- **Begin with:** contrastive example
- **Why:** Comparing native HTML to ARIA-added custom markup makes the rule concrete and memorable.

### 4. Rule 2: Do not change native semantics unless there is a very strong, valid reason.
- **Begin with:** contrastive example
- **Why:** This rule is easiest to grasp when students see a native element with correct meaning versus one whose role is overridden.

### 5. Role usage can create obligations: some roles require particular states/properties.
- **Begin with:** brief explanation
- **Why:** This is a structural rule about ARIA mechanics that learners may not infer on their own.

### 6. Rule 3: All required ARIA states/properties for a chosen role must be present and valid.
- **Begin with:** worked example
- **Why:** Students need to see a role chosen and then checked for what must accompany it.

### 7. ARIA attributes are role-dependent; not every attribute is valid on every role.
- **Begin with:** diagnostic question
- **Why:** This exposes the common misconception that ARIA attributes are freely mix-and-match.

### 8. Rule 4: Use only ARIA states/properties supported for the role in question.
- **Begin with:** worked example
- **Why:** Learners benefit from seeing attribute-role compatibility checked in context.

### 9. Some HTML elements already expose implicit roles/states.
- **Begin with:** guided questioning
- **Why:** Students may already know examples like buttons, headings, and links; eliciting that knowledge reduces lecture load.

### 10. Rule 5: Do not add redundant ARIA that repeats implicit native semantics.
- **Begin with:** contrastive example
- **Why:** Redundancy is easiest to understand by comparing “native only” against “native plus unnecessary ARIA.”

### 11. Conflicts between native semantics and ARIA can harm accessibility rather than help it.
- **Begin with:** guided questioning
- **Why:** Socratic prompts can lead learners to reason about conflicting signals rather than passively accept the claim.

### 12. Applying the five rules often means deciding among: remove ARIA, replace custom markup with native HTML, add missing required ARIA, or revise invalid combinations.
- **Begin with:** worked example
- **Why:** This is practical synthesis and requires modeled decision-making.

### 13. A single snippet may violate more than one rule at once.
- **Begin with:** diagnostic question
- **Why:** Students often stop after spotting one issue; diagnosis reveals whether they can continue checking systematically.

### 14. Correct application requires justification: identifying which rule applies and why.
- **Begin with:** guided questioning
- **Why:** The goal is not just correction but reasoned explanation tied to rules.

## 11. socratic_question_goals

### Stage 1: foundational framing
- diagnose whether the learner sees ARIA as replacement vs supplement
- surface prior knowledge of semantic HTML
- confirm understanding that native elements carry meaning

### Stage 2: native-first decision making
- force comparison between native and ARIA-based solutions
- test whether the learner can justify choosing native HTML
- reveal the misconception that custom markup plus ARIA is equivalent to native controls

### Stage 3: preserving native semantics
- check causal understanding of why overriding native roles is risky
- reveal overconfidence in changing roles on semantic elements
- test ability to spot conflicts between built-in meaning and assigned role

### Stage 4: role obligations
- diagnose whether the learner understands that choosing a role creates requirements
- test whether they notice missing required states/properties
- require justification for why a snippet is incomplete, not merely “uses ARIA”

### Stage 5: supported vs unsupported attributes
- force comparison between valid and invalid role/attribute combinations
- reveal the misconception that all ARIA attributes are universally usable
- test lookup-style reasoning without requiring rote memorization

### Stage 6: redundancy and implicit semantics
- test whether the learner can identify what semantics are already present natively
- reveal the misconception that extra ARIA is harmless
- justify removal of redundant role/state assignments

### Stage 7: synthesis
- test transfer across mixed examples
- require the learner to decide the appropriate fix, not just name a rule
- check whether the learner can identify multiple simultaneous violations
- require rule-based justification for each correction

## 12. example_requirements

### simplest introductory example
- A very small comparison where a native semantic element solves the need directly, contrasted with a nonsemantic element using ARIA to imitate it.
- Purpose: support Rule 1 with minimal complexity.

### at least one contrastive example
- A pair showing:
  - a native element used correctly without extra ARIA
  - the same element with redundant or conflicting ARIA added
- Purpose: contrast “good because native” vs “worse because unnecessary/conflicting.”

### at least one borderline or tricky case
- A snippet where:
  - ARIA is not entirely wrong, but incomplete because required states/properties are missing
  - or a role is assigned correctly in principle, but an unsupported attribute is added
- Purpose: prevent shallow “ARIA bad / no ARIA good” overgeneralization.

### at least one transfer scenario
- A mixed snippet containing multiple issues, such as:
  - custom element with ARIA where native HTML should be used
  - overridden native semantics
  - missing required property
  - redundant role
- Purpose: assess integrated application across rules.

### additional example guidance
- Keep examples short enough for line-by-line inspection.
- Prefer realistic UI fragments over abstract isolated tags.
- Do not require advanced widget architecture beyond what is necessary to apply the rules.

## 13. retrieval_requirements

### must-retrieve
- The authoritative formulation of the five rules for using ARIA correctly
  - Needed so the lesson aligns exactly with accepted guidance.
- Accurate examples of native elements with implicit semantics
  - Needed for Rules 1, 2, and 5.
- Reliable examples of roles that require specific ARIA states/properties
  - Needed for Rule 3.
- Reliable role/state/property compatibility information
  - Needed for Rule 4.
- Examples of redundant ARIA on native elements
  - Needed for Rule 5.
- At least one example where ARIA conflicts with native semantics
  - Needed to demonstrate harm from misuse.

### optional-supporting
- Accessibility tree or assistive technology interpretation examples
  - Helpful to motivate why misuse matters.
- Linting or validator output examples
  - Helpful for debugging/evaluation framing, but not required.
- Brief references to common authoring mistakes in real codebases
  - Helpful for authenticity and transfer.
- A compact rule summary table
  - Helpful for review after reasoning practice.

## 14. assessment_evidence

### quick understanding checks
- Given a simple snippet, the learner identifies whether ARIA is needed.
- Given a native element with added ARIA, the learner says whether the ARIA is redundant, harmful, or necessary.
- Given a role, the learner recognizes that required states/properties may need checking.

### application task
- Provide a short code sample with 3–5 ARIA-related decisions.
- Ask the learner to mark each as:
  - keep
  - remove
  - replace with native HTML
  - add required ARIA
  - revise invalid ARIA
- Require a rule-based justification for each decision.

### transfer task
- Give a different UI pattern than the examples used in practice.
- Ask the learner to apply the same rules without cueing which rule to use.
- Evidence of mastery: the learner independently selects the applicable rule(s) and proposes an appropriate correction.

### misconception check
- Include at least one item designed to trigger each common misconception:
  - a native control with redundant role
  - a native element with conflicting role
  - a role missing required state/property
  - an unsupported state/property on a role
  - a custom element that should have been native HTML
- Mastery evidence: the learner does not merely flag “bad ARIA,” but identifies the specific rule being violated.

## 15. adaptation_notes

### beginner
- Spend more time on prerequisite bridging around semantic HTML.
- Use fewer technical terms at first; introduce role/state/property only when needed.
- Limit examples to common elements and small snippets.
- Emphasize Rule 1 and Rule 5 early, since they are accessible entry points.

### intermediate learner
- Move quickly through semantic HTML review.
- Use more mixed examples where multiple rules interact.
- Ask for explicit justification tied to the numbered rules.
- Include at least one case involving required states/properties and one involving unsupported attributes.

### advanced learner
- Minimize introductory explanation and begin with diagnosis through flawed examples.
- Emphasize nuanced distinctions:
  - valid in principle vs valid in context
  - technically present vs semantically complete
  - unnecessary vs harmful
- Use compact synthesis tasks where the learner audits snippets and explains prioritization of fixes.

## 16. boundaries_and_non_goals
This lesson should NOT attempt to teach:

- full ARIA specification details
- exhaustive memorization of all roles, states, and properties
- advanced custom widget authoring patterns in depth
- keyboard interaction implementation for custom widgets except where minimally needed to explain why native HTML is preferable
- accessible naming and labeling in general, unless directly needed for a retrieved example
- screen reader-specific behavior across different products
- full accessibility tree mechanics
- broad WCAG conformance beyond the narrow context of applying the five ARIA rules

## 17. concise_plan_summary
- Start by establishing that ARIA supplements HTML rather than replacing it.
- Activate prior knowledge of native semantics before introducing the rules.
- Teach the “prefer native HTML” and “don’t override native semantics” rules first, because they prevent the most common misuse.
- Then introduce the idea that choosing ARIA roles creates obligations and compatibility constraints.
- Teach redundancy only after learners understand implicit native semantics.
- Use short contrastive and worked examples rather than abstract rule recitation.
- End with mixed-code diagnosis tasks that require both correction and rule-based justification.
- Keep scope tight: apply the five rules accurately without expanding into full ARIA implementation theory.
```

### Evidence Pack (4173 chars)

````markdown
## CORE FACTS
### 4.1.2 Name, Role, Value
**Goal:** People using assistive technology understand all components.
**What to do:** Give components correct names, roles, states, and values.
**Why it's important:** Assistive technology only works well when code is done properly.

For all user interface components (including but not limited to: form elements, links and components generated by scripts), the name and role can be programmatically determined; states, properties, and values that can be set by the user can be programmatically set; and notification of changes to these items is available to user agents, including assistive technologies.

## DECISION BOUNDARIES
### Decision Boundaries for 4.1.2 Name, Role, Value
Intent of Name, Role, Value
 The intent of this success criterion is to ensure that Assistive Technologies (AT)
 can gather appropriate information about, activate (or set) and keep up to date on the status of
 user interface controls in the content.

When standard controls from accessible technologies are used, this process is straightforward.
 If the user interface elements are used according to specification the conditions
 of this provision will be met. (See examples of Success Criterion 4.1.2 below)

## TECHNIQUE PATTERNS
### Techniques for 4.1.2 Name, Role, Value
Sufficient techniques:
**Situation A: If using a standard user interface component in a markup language (e.g., HTML):**
 - **ARIA14**: Using aria-label to provide an accessible name where a visible label cannot be used
 - **ARIA16**: Using aria-labelledby to provide a name for user interface controls
 - **G108**: Using markup features to expose the name and role, allow user-settable properties to be directly set, and provide notification of changes
 - **H91**: Using HTML form controls and links
 - **H44**: Using label elements to associate text labels with form controls
 - **H64**: Using the title attribute of the iframe element
 - **H65**: Using the title attribute to identify form controls when the label element cannot be used
 - **H88**: Using HTML according to spec
**Situation B: If using script or code to re-purpose a standard user interface component in a markup language:**
 **Exposing the names and roles, allowing user-settable properties to be directly set, and providing notification of changes**
**Situation C: If using a standard user interface component in a programming technology:**
 - **G135**: Using the accessibility API features of a technology to expose names and...

### H88: Using HTML according to spec
# H88: Using HTML according to spec

**Technology:** html
**Types:** sufficient
**Applies to:** 1 success criteria

## Related Success Criteria

- **4.1.2** Name, Role, Value (Level A)

## Links

- [Full Technique Documentation](https://www.w3.org/WAI/WCAG22/Techniques/html/H88)

### H91: Using HTML form controls and links
# H91: Using HTML form controls and links

**Technology:** html
**Types:** sufficient
**Applies to:** 2 success criteria

## Related Success Criteria

- **2.1.1** Keyboard (Level A)
- **4.1.2** Name, Role, Value (Level A)

## Links

- [Full Technique Documentation](https://www.w3.org/WAI/WCAG22/Techniques/html/H91)

## RISKS / MISUSE
### Failure and Misuse Notes for Techniques for 4.1.2 Name, Role, Value
Failure techniques:
- **F59**: Failure of Success Criterion 4.1.2 due to using script to make div or span a user interface control in HTML without providing a role for the control
- **F15**: Failure of Success Criterion 4.1.2 due to implementing custom controls that do not use an accessibility API for the technology, or do so incompletely
- **F20**: Failure of Success Criterion 1.1.1 and 4.1.2 due to not updating text alternatives when changes to non-text content occur
- **F42**: Failure of Success Criteria 1.3.1, 2.1.1, 2.1.3, or 4.1.2 when emulating links
- **F68**: Failure of Success Criterion 4.1.2 due to a user interface control not having a programmatically determined name
- **F79**: Failure of Success Criterion 4.1.2 due to the focus state of a user interface component not being programmatically determinable or no notification of change of focus state available
- **F86**: Failu...
````

### Retrieval Bundle Coverage

```json
{
  "hit_count": 6,
  "hit_chars": 8946,
  "missing_checks": [],
  "required_checks": {
    "conformance_rollup_rule": false,
    "techniques_vs_requirements": false
  },
  "budget_chars": 20000
}
```

### Retrieval Bundle Sections

**core_rules** (1 items):
- `get_criterion` → 4.1.2 Name, Role, Value (606 chars)

**decision_rules** (1 items):
- `get_criterion` → Decision Boundaries for 4.1.2 Name, Role, Value (509 chars)

**technique_patterns** (5 items):
- `get_techniques_for_criterion` → Techniques for 4.1.2 Name, Role, Value (2096 chars)
- `get_technique` → H88: Using HTML according to spec (279 chars)
- `get_technique` → H91: Using HTML form controls and links (316 chars)
- `get_technique` → ARIA4: Using a WAI-ARIA role to expose the role of a user interface component (325 chars)
- `get_technique` → ARIA5: Using WAI-ARIA state and property attributes to expose the state of a user interface component (349 chars)

**risks** (1 items):
- `get_techniques_for_criterion` → Failure and Misuse Notes for Techniques for 4.1.2 Name, Role, Value (1304 chars)


### Lesson State (initial)

```json
{
  "active_concept": "avoid_redundant_aria",
  "pending_check": "Can the student identify when ARIA on a native element is redundant versus when it serves a real purpose?",
  "bridge_back_target": "implicit_native_roles_states",
  "teaching_order": [
    "aria_supplemental_metadata",
    "native_html_semantics_behavior",
    "prefer_native_over_aria",
    "preserve_native_semantics",
    "roles_create_requirements",
    "include_required_role_states",
    "aria_is_role_dependent",
    "use_supported_role_attributes",
    "implicit_native_roles_states",
    "avoid_redundant_aria",
    "native_aria_conflicts_harm",
    "choose_correct_aria_fix",
    "multiple_rule_violations",
    "justify_rule_based_choices"
  ],
  "concepts": [
    {
      "id": "aria_supplemental_metadata",
      "label": "ARIA is supplemental accessibility metadata, not a replacement for correct HTML",
      "status": "covered"
    },
    {
      "id": "native_html_semantics_behavior",
      "label": "Native HTML elements already carry built-in semantics and behavior",
      "status": "covered"
    },
    {
      "id": "prefer_native_over_aria",
      "label": "If native HTML can provide the needed semantics or behavior, prefer it over ARIA",
      "status": "covered"
    },
    {
      "id": "preserve_native_semantics",
      "label": "Do not change native semantics unless there is a very strong, valid reason",
      "status": "covered"
    },
    {
      "id": "roles_create_requirements",
      "label": "Some ARIA roles require particular states or properties",
      "status": "covered"
    },
    {
      "id": "include_required_role_states",
      "label": "All required ARIA states and properties for a chosen role must be present and valid",
      "status": "covered"
    },
    {
      "id": "aria_is_role_dependent",
      "label": "ARIA attributes are role-dependent and not every attribute is valid on every role",
      "status": "covered"
    },
    {
      "id": "use_supported_role_attributes",
      "label": "Use only ARIA states and properties supported for the role in question",
      "status": "covered"
    },
    {
      "id": "implicit_native_roles_states",
      "label": "Some HTML elements already expose implicit roles and states",
      "status": "covered"
    },
    {
      "id": "avoid_redundant_aria",
      "label": "Do not add redundant ARIA that repeats implicit native semantics",
      "status": "in_progress"
    },
    {
      "id": "native_aria_conflicts_harm",
      "label": "Conflicts between native semantics and ARIA can harm accessibility",
      "status": "not_covered"
    },
    {
      "id": "choose_correct_aria_fix",
      "label": "Apply the rules by removing ARIA, replacing custom markup with native HTML, adding missing required ARIA, or revising invalid combinations",
      "status": "not_covered"
    },
    {
      "id": "multiple_rule_violations",
      "label": "A single snippet may violate more than one rule at once",
      "status": "not_covered"
    },
    {
      "id": "justify_rule_based_choices",
      "label": "Correct application requires identifying which rule applies and why",
      "status": "not_covered"
    }
  ]
}
```

### Slim Persisted Payload

| Field | Size |
|-------|------|
| `objective_id` | 38 bytes |
| `objective_text` | 47 bytes |
| `teaching_content` | 4251 bytes |
| `teaching_plan` | 18774 bytes |
| `lesson_state` | 2723 bytes |
| `retrieved_at` | 28 bytes |
| `retrieval_bundle` | 7527 bytes |

---

## Turn-by-Turn Log

### Turn 1: introduction → introduction
**Tutor time**: 148.18s | **Student agent time**: 1.9s | **Turns on obj**: 0 → 1

**Student**:
> Cool, I’ve heard ARIA is for making stuff more accessible, but I don’t really know the rules yet. I’m ready to learn — is it mostly about adding labels and roles to buttons and menus?

**Tutor**:
> Partly, yes — labels and roles are two common things ARIA can add, but ARIA is broader than that. It also covers states and values, and WCAG 4.1.2 says assistive technologies need components to have the right name, role, states, properties, and values so they can understand and keep track of them.

The key idea for this lesson is: ARIA is supplemental accessibility metadata, not a replacement for correct HTML. So before asking “should I add ARIA?”, we first ask whether the native HTML already gives us the needed semantics and behavior.

If a native element already does the job, what do you think is usually the better first choice: adding ARIA, or using the right HTML element?

<details><summary>WebSocket Events (13 non-token)</summary>

```json
[
  {
    "type": "stage",
    "stage": "composing",
    "detail": "Creating teaching plan...",
    "_ts": "2026-04-08T19:51:14.184144"
  },
  {
    "type": "stage",
    "stage": "searching",
    "detail": "Researching WCAG content...",
    "_ts": "2026-04-08T19:52:41.040342"
  },
  {
    "type": "stage",
    "stage": "searching",
    "detail": "Researching WCAG sources (round 1/4)...",
    "_ts": "2026-04-08T19:52:41.046031"
  },
  {
    "type": "stage",
    "stage": "searching",
    "detail": "Researching WCAG sources (round 2/4)...",
    "_ts": "2026-04-08T19:52:56.561167"
  },
  {
    "type": "stage",
    "stage": "searching",
    "detail": "Researching WCAG sources (round 3/4)...",
    "_ts": "2026-04-08T19:53:10.302067"
  },
  {
    "type": "stage",
    "stage": "searching",
    "detail": "Validating evidence...",
    "_ts": "2026-04-08T19:53:25.537838"
  },
  {
    "type": "stage",
    "stage": "searching",
    "detail": "Teaching pack: 4173 chars from 6 sources",
    "_ts": "2026-04-08T19:53:25.540252"
  },
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Analyzing your response...",
    "_ts": "2026-04-08T19:53:25.583100"
  },
  {
    "type": "stage",
    "stage": "composing",
    "detail": "Generating response (introduction)...",
    "_ts": "2026-04-08T19:53:38.973490"
  },
  {
    "type": "stream_start",
    "_ts": "2026-04-08T19:53:40.982894"
  },
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Updating learning state...",
    "_ts": "2026-04-08T19:53:42.333117"
  },
  {
    "type": "mastery_denied",
    "reason": "Confidence 0.4 below threshold 0.7",
    "_ts": "2026-04-08T19:53:42.356119"
  },
  {
    "type": "stream_end",
    "metadata": {
      "session_id": "guided-test-195112",
      "stage": "introduction",
      "stage_advanced": false,
      "assessment": {}
    },
    "_ts": "2026-04-08T19:53:42.356167"
  }
]
```
</details>

**Lesson State**: active=`avoid_redundant_aria`
  `aria_supplemental_metadata` [done], `native_html_semantics_behavior` [done], `prefer_native_over_aria` [done], `preserve_native_semantics` [done], `roles_create_requirements` [done], `include_required_role_states` [done], `aria_is_role_dependent` [done], `use_supported_role_attributes` [done], `implicit_native_roles_states` [done], `avoid_redundant_aria` [wip], `native_aria_conflicts_harm` [todo], `choose_correct_aria_fix` [todo], `multiple_rule_violations` [todo], `justify_rule_based_choices` [todo]

<details><summary>Objective Memory</summary>

```json
{
  "student_id": "test-conv-195112",
  "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
  "summary": "Student has heard ARIA improves accessibility but is unsure of the rule set and asks whether it is mainly about labels and roles.",
  "demonstrated_skills": [
    "Activates prior knowledge",
    "Asks a relevant framing question"
  ],
  "active_gaps": [
    "Does not yet distinguish ARIA from correct native HTML",
    "May over-associate ARIA with adding labels and roles"
  ],
  "next_focus": "Clarify ARIA's supplemental role and contrast it with using correct native HTML first.",
  "updated_at": "datetime.datetime(2026, 4, 8, 19, 53, 42, 349690, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

<details><summary>Learner Memory</summary>

```json
{
  "student_id": "test-conv-195112",
  "summary": "Learner is open, engaged, and comfortable surfacing uncertainty early.",
  "strengths": [
    "Readiness to engage",
    "Asks focused questions"
  ],
  "support_needs": [
    "Clear framing before rule details",
    "Contrastive examples to separate native HTML from ARIA"
  ],
  "tendencies": [
    "Starts from broad practical assumptions",
    "Seeks a big-picture mental model first"
  ],
  "successful_strategies": [
    "Answer the current framing question directly",
    "Use concise contrasts between native HTML and ARIA"
  ],
  "updated_at": "datetime.datetime(2026, 4, 8, 19, 53, 42, 353233, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

---

### Turn 2: introduction → exploration
**Tutor time**: 16.49s | **Student agent time**: 1.38s | **Turns on obj**: 1 → 2

**Student**:
> Using the right HTML element, I think. Like a `<button>` instead of making a div act like one? That makes sense — ARIA sounds more like a backup when HTML doesn’t cover it.

**Tutor**:
> Exactly — that’s the right instinct. A real `<button>` already carries built-in semantics and behavior, so ARIA is not there to replace that; it’s there to supplement when native HTML isn’t enough.

To make that concrete: if you can choose between a `<button>` and a `<div>` with ARIA pretending to be a button, which one would you expect to be safer and more reliable for assistive technologies?

<details><summary>WebSocket Events (7 non-token)</summary>

```json
[
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Analyzing your response...",
    "_ts": "2026-04-08T19:53:44.298901"
  },
  {
    "type": "stage",
    "stage": "composing",
    "detail": "Generating response (introduction)...",
    "_ts": "2026-04-08T19:53:58.263899"
  },
  {
    "type": "stream_start",
    "_ts": "2026-04-08T19:53:59.945715"
  },
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Updating learning state...",
    "_ts": "2026-04-08T19:54:00.727035"
  },
  {
    "type": "mastery_update",
    "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
    "objective_text": "Apply the five rules for using ARIA correctly",
    "new_level": "in_progress",
    "_ts": "2026-04-08T19:54:00.749548"
  },
  {
    "type": "stage_update",
    "stage": "exploration",
    "objective": "Apply the five rules for using ARIA correctly",
    "summary": "Student correctly applies the framing idea to a concrete example and contrasts native HTML with ARIA.",
    "_ts": "2026-04-08T19:54:00.752758"
  },
  {
    "type": "stream_end",
    "metadata": {
      "session_id": "guided-test-195112",
      "stage": "exploration",
      "stage_advanced": true,
      "assessment": {}
    },
    "_ts": "2026-04-08T19:54:00.752816"
  }
]
```
</details>

**Lesson State**: active=`avoid_redundant_aria`
  `aria_supplemental_metadata` [done], `native_html_semantics_behavior` [done], `prefer_native_over_aria` [done], `preserve_native_semantics` [done], `roles_create_requirements` [done], `include_required_role_states` [done], `aria_is_role_dependent` [done], `use_supported_role_attributes` [done], `implicit_native_roles_states` [done], `avoid_redundant_aria` [wip], `native_aria_conflicts_harm` [todo], `choose_correct_aria_fix` [todo], `multiple_rule_violations` [todo], `justify_rule_based_choices` [todo]

**Mastery**: level=`in_progress` confidence=?

<details><summary>Objective Memory</summary>

```json
{
  "student_id": "test-conv-195112",
  "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
  "summary": "Student now states that the right native element should come before ARIA and gives button vs div as the example.",
  "demonstrated_skills": [
    "Activates prior knowledge",
    "Asks a relevant framing question",
    "Contrasts native HTML with ARIA use",
    "Applies the supplemental-ARIA idea to a concrete control example"
  ],
  "active_gaps": [
    "Does not yet distinguish ARIA from correct native HTML",
    "May over-associate ARIA with adding labels and roles",
    "Has not yet articulated what built-in semantics/behavior native elements provide",
    "Has not yet worked through the explicit ARIA rules"
  ],
  "next_focus": "Elicit what native HTML already provides and connect that to Rule 1.",
  "updated_at": "datetime.datetime(2026, 4, 8, 19, 54, 0, 740053, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

<details><summary>Learner Memory</summary>

```json
{
  "student_id": "test-conv-195112",
  "summary": "Learner responds well to concise framing and can extend the idea with a practical example.",
  "strengths": [
    "Readiness to engage",
    "Asks focused questions",
    "Uses concrete frontend examples",
    "Shows early conceptual uptake"
  ],
  "support_needs": [
    "Clear framing before rule details",
    "Contrastive examples to separate native HTML from ARIA",
    "Keep building from practical native-vs-custom comparisons"
  ],
  "tendencies": [
    "Starts from broad practical assumptions",
    "Seeks a big-picture mental model first",
    "Tests understanding by paraphrasing with examples"
  ],
  "successful_strategies": [
    "Answer the current framing question directly",
    "Use concise contrasts between native HTML and ARIA",
    "Ask contrastive questions",
    "Use familiar controls like button vs div"
  ],
  "updated_at": "datetime.datetime(2026, 4, 8, 19, 54, 0, 742500, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

---

### Turn 3: exploration → exploration
**Tutor time**: 18.55s | **Student agent time**: 1.37s | **Turns on obj**: 2 → 3

**Student**:
> The `<button>`, for sure. A div with ARIA feels like it’d be easier to mess up, especially with keyboard support and stuff.

**Tutor**:
> Yes — that’s the danger. A real `<button>` gives you built-in behavior and semantics that assistive tech can work with straight away, and WCAG 4.1.2 emphasizes that components need their name, role, and user-settable states/values to be programmatically determinable.

So the practical rule is: if the native element already provides what you need, prefer it over ARIA. What’s one other thing, besides keyboard support, that a native `<button>` gives you “for free” that a `<div>` would need extra work to match?

<details><summary>WebSocket Events (6 non-token)</summary>

```json
[
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Analyzing your response...",
    "_ts": "2026-04-08T19:54:02.193047"
  },
  {
    "type": "stage",
    "stage": "composing",
    "detail": "Generating response (exploration)...",
    "_ts": "2026-04-08T19:54:17.141728"
  },
  {
    "type": "stream_start",
    "_ts": "2026-04-08T19:54:19.586247"
  },
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Updating learning state...",
    "_ts": "2026-04-08T19:54:20.631797"
  },
  {
    "type": "mastery_update",
    "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
    "objective_text": "Apply the five rules for using ARIA correctly",
    "new_level": "in_progress",
    "_ts": "2026-04-08T19:54:20.694147"
  },
  {
    "type": "stream_end",
    "metadata": {
      "session_id": "guided-test-195112",
      "stage": "exploration",
      "stage_advanced": false,
      "assessment": {}
    },
    "_ts": "2026-04-08T19:54:20.694206"
  }
]
```
</details>

**Lesson State**: active=`avoid_redundant_aria`
  `aria_supplemental_metadata` [done], `native_html_semantics_behavior` [done], `prefer_native_over_aria` [done], `preserve_native_semantics` [done], `roles_create_requirements` [done], `include_required_role_states` [done], `aria_is_role_dependent` [done], `use_supported_role_attributes` [done], `implicit_native_roles_states` [done], `avoid_redundant_aria` [wip], `native_aria_conflicts_harm` [todo], `choose_correct_aria_fix` [todo], `multiple_rule_violations` [todo], `justify_rule_based_choices` [todo]

**Mastery**: level=`in_progress` confidence=?

<details><summary>Objective Memory</summary>

```json
{
  "student_id": "test-conv-195112",
  "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
  "summary": "Student now says native controls are safer and more reliable than ARIA-repurposed divs, specifically because custom versions are easier to get wrong and may miss keyboard behavior.",
  "demonstrated_skills": [
    "Activates prior knowledge",
    "Asks a relevant framing question",
    "Contrasts native HTML with ARIA use",
    "Applies the supplemental-ARIA idea to a concrete control example",
    "Uses native-vs-custom comparison",
    "Gives causal justification for preferring native HTML",
    "Connects accessibility choice to implementation reliability"
  ],
  "active_gaps": [
    "Does not yet distinguish ARIA from correct native HTML",
    "May over-associate ARIA with adding labels and roles",
    "Has not yet articulated what built-in semantics/behavior native elements provide",
    "Has not yet worked through the explicit ARIA rules",
    "Has not yet explicitly stated Rule 1",
    "Has not yet named built-in semantics and behavior beyond keyboard support",
    "Has not yet applied the rule across multiple examples"
  ],
  "next_focus": "Make Rule 1 explicit and test it on simple markup choices.",
  "updated_at": "datetime.datetime(2026, 4, 8, 19, 54, 20, 685061, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

<details><summary>Learner Memory</summary>

```json
{
  "student_id": "test-conv-195112",
  "summary": "Learner can move from framing to practical reasoning and responds well to concrete native-vs-custom examples.",
  "strengths": [
    "Readiness to engage",
    "Asks focused questions",
    "Uses concrete frontend examples",
    "Shows early conceptual uptake",
    "Reasones causally from examples",
    "Connects concepts to frontend implementation risk",
    "Comfortable using familiar controls like buttons"
  ],
  "support_needs": [
    "Clear framing before rule details",
    "Contrastive examples to separate native HTML from ARIA",
    "Keep building from practical native-vs-custom comparisons",
    "Help making implicit reasoning explicit as a named rule",
    "More examples beyond buttons to stabilize the concept"
  ],
  "tendencies": [
    "Starts from broad practical assumptions",
    "Seeks a big-picture mental model first",
    "Tests understanding by paraphrasing with examples",
    "Paraphrases understanding through practical tradeoffs",
    "Brings in implementation concerns like keyboard support"
  ],
  "successful_strategies": [
    "Answer the current framing question directly",
    "Use concise contrasts between native HTML and ARIA",
    "Ask contrastive questions",
    "Use familiar controls like button vs div",
    "Use contrastive markup examples",
    "Ask why native is safer, not just which is preferred"
  ],
  "updated_at": "datetime.datetime(2026, 4, 8, 19, 54, 20, 688658, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

---

### Turn 4: exploration → exploration
**Tutor time**: 18.31s | **Student agent time**: 1.67s | **Turns on obj**: 3 → 4

**Student**:
> The accessible name maybe? Like the text inside the button becomes the label automatically. Also I guess it has the right role already, so screen readers know it’s a button without extra ARIA.

**Tutor**:
> Yes — that’s a solid answer. A native `<button>` already exposes its role, and its visible text can serve as its accessible name, so you don’t need to bolt ARIA onto it just to make it “understandable.”

So the takeaway for Rule 1 is: if the native HTML element already provides the needed semantics or behavior, use it instead of ARIA. Can you state that rule in your own words, using the button example?

<details><summary>WebSocket Events (6 non-token)</summary>

```json
[
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Analyzing your response...",
    "_ts": "2026-04-08T19:54:22.123775"
  },
  {
    "type": "stage",
    "stage": "composing",
    "detail": "Generating response (exploration)...",
    "_ts": "2026-04-08T19:54:37.882573"
  },
  {
    "type": "stream_start",
    "_ts": "2026-04-08T19:54:39.518643"
  },
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Updating learning state...",
    "_ts": "2026-04-08T19:54:40.356243"
  },
  {
    "type": "mastery_update",
    "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
    "objective_text": "Apply the five rules for using ARIA correctly",
    "new_level": "in_progress",
    "_ts": "2026-04-08T19:54:40.378545"
  },
  {
    "type": "stream_end",
    "metadata": {
      "session_id": "guided-test-195112",
      "stage": "exploration",
      "stage_advanced": false,
      "assessment": {}
    },
    "_ts": "2026-04-08T19:54:40.378614"
  }
]
```
</details>

**Lesson State**: active=`avoid_redundant_aria`
  `aria_supplemental_metadata` [done], `native_html_semantics_behavior` [done], `prefer_native_over_aria` [done], `preserve_native_semantics` [done], `roles_create_requirements` [done], `include_required_role_states` [done], `aria_is_role_dependent` [done], `use_supported_role_attributes` [done], `implicit_native_roles_states` [done], `avoid_redundant_aria` [wip], `native_aria_conflicts_harm` [todo], `choose_correct_aria_fix` [todo], `multiple_rule_violations` [todo], `justify_rule_based_choices` [todo]

**Mastery**: level=`in_progress` confidence=?

<details><summary>Objective Memory</summary>

```json
{
  "student_id": "test-conv-195112",
  "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
  "summary": "Student explicitly justified preferring native HTML by noting a button already exposes an accessible name from its text and the correct implicit role.",
  "demonstrated_skills": [
    "Activates prior knowledge",
    "Asks a relevant framing question",
    "Contrasts native HTML with ARIA use",
    "Applies the supplemental-ARIA idea to a concrete control example",
    "Uses native-vs-custom comparison",
    "Gives causal justification for preferring native HTML",
    "Connects accessibility choice to implementation reliability",
    "Names built-in native semantics",
    "Connects native elements to assistive technology reliability",
    "Justifies Rule 1 with concrete markup reasoning"
  ],
  "active_gaps": [
    "Does not yet distinguish ARIA from correct native HTML",
    "May over-associate ARIA with adding labels and roles",
    "Has not yet articulated what built-in semantics/behavior native elements provide",
    "Has not yet worked through the explicit ARIA rules",
    "Has not yet explicitly stated Rule 1",
    "Has not yet named built-in semantics and behavior beyond keyboard support",
    "Has not yet applied the rule across multiple examples",
    "Has not yet worked through Rule 2 about not overriding native semantics",
    "Has not yet handled examples involving invalid or redundant ARIA beyond button/div comparison"
  ],
  "next_focus": "Introduce Rule 2 with a native element whose role is overridden unnecessarily.",
  "updated_at": "datetime.datetime(2026, 4, 8, 19, 54, 40, 371775, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

<details><summary>Learner Memory</summary>

```json
{
  "student_id": "test-conv-195112",
  "summary": "Learner can supply concrete native-element benefits when prompted and grounds reasoning in practical implementation details.",
  "strengths": [
    "Readiness to engage",
    "Asks focused questions",
    "Uses concrete frontend examples",
    "Shows early conceptual uptake",
    "Reasones causally from examples",
    "Connects concepts to frontend implementation risk",
    "Comfortable using familiar controls like buttons",
    "Uses concrete examples",
    "Can name implicit role/name benefits",
    "Reasons from assistive-tech impact"
  ],
  "support_needs": [
    "Clear framing before rule details",
    "Contrastive examples to separate native HTML from ARIA",
    "Keep building from practical native-vs-custom comparisons",
    "Help making implicit reasoning explicit as a named rule",
    "More examples beyond buttons to stabilize the concept",
    "Keep prompting for explicit rule naming",
    "Use contrastive markup to extend beyond familiar button examples"
  ],
  "tendencies": [
    "Starts from broad practical assumptions",
    "Seeks a big-picture mental model first",
    "Tests understanding by paraphrasing with examples",
    "Paraphrases understanding through practical tradeoffs",
    "Brings in implementation concerns like keyboard support",
    "Answers cautiously but accurately",
    "Builds understanding through practical frontend tradeoffs"
  ],
  "successful_strategies": [
    "Answer the current framing question directly",
    "Use concise contrasts between native HTML and ARIA",
    "Ask contrastive questions",
    "Use familiar controls like button vs div",
    "Use contrastive markup examples",
    "Ask why native is safer, not just which is preferred",
    "Ask what native elements provide for free",
    "Use direct native-vs-ARIA contrasts"
  ],
  "updated_at": "datetime.datetime(2026, 4, 8, 19, 54, 40, 373771, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

---

### Turn 5: exploration → exploration
**Tutor time**: 20.02s | **Student agent time**: 1.7s | **Turns on obj**: 4 → 5

**Student**:
> If HTML already gives me the right meaning and behavior, I should use that instead of adding ARIA on top. So I’d use a `<button>` for a button, not a `<div role="button">` unless I really can’t use native HTML.

**Tutor**:
> That’s the right rule, and you’re saying it in the right direction.

Now push one step further: if you already have a real `<button>`, what do you think goes wrong when someone adds `role="link"` or `role="presentation"` to it just because they want a different visual or styling effect?

<details><summary>WebSocket Events (6 non-token)</summary>

```json
[
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Analyzing your response...",
    "_ts": "2026-04-08T19:54:42.444794"
  },
  {
    "type": "stage",
    "stage": "composing",
    "detail": "Generating response (exploration)...",
    "_ts": "2026-04-08T19:54:59.958962"
  },
  {
    "type": "stream_start",
    "_ts": "2026-04-08T19:55:01.515497"
  },
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Updating learning state...",
    "_ts": "2026-04-08T19:55:02.097917"
  },
  {
    "type": "mastery_update",
    "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
    "objective_text": "Apply the five rules for using ARIA correctly",
    "new_level": "in_progress",
    "_ts": "2026-04-08T19:55:02.112984"
  },
  {
    "type": "stream_end",
    "metadata": {
      "session_id": "guided-test-195112",
      "stage": "exploration",
      "stage_advanced": false,
      "assessment": {}
    },
    "_ts": "2026-04-08T19:55:02.113019"
  }
]
```
</details>

**Lesson State**: active=`avoid_redundant_aria`
  `aria_supplemental_metadata` [done], `native_html_semantics_behavior` [done], `prefer_native_over_aria` [done], `preserve_native_semantics` [done], `roles_create_requirements` [done], `include_required_role_states` [done], `aria_is_role_dependent` [done], `use_supported_role_attributes` [done], `implicit_native_roles_states` [done], `avoid_redundant_aria` [wip], `native_aria_conflicts_harm` [todo], `choose_correct_aria_fix` [todo], `multiple_rule_violations` [todo], `justify_rule_based_choices` [todo]

**Mastery**: level=`in_progress` confidence=?

<details><summary>Objective Memory</summary>

```json
{
  "student_id": "test-conv-195112",
  "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
  "summary": "Student can now state Rule 1 in their own words and apply it to button vs div role=button.",
  "demonstrated_skills": [
    "Activates prior knowledge",
    "Asks a relevant framing question",
    "Contrasts native HTML with ARIA use",
    "Applies the supplemental-ARIA idea to a concrete control example",
    "Uses native-vs-custom comparison",
    "Gives causal justification for preferring native HTML",
    "Connects accessibility choice to implementation reliability",
    "Names built-in native semantics",
    "Connects native elements to assistive technology reliability",
    "Justifies Rule 1 with concrete markup reasoning",
    "Restates Rule 1 accurately",
    "Uses concrete markup comparison",
    "Connects native HTML to built-in meaning and behavior"
  ],
  "active_gaps": [
    "Does not yet distinguish ARIA from correct native HTML",
    "May over-associate ARIA with adding labels and roles",
    "Has not yet articulated what built-in semantics/behavior native elements provide",
    "Has not yet worked through the explicit ARIA rules",
    "Has not yet explicitly stated Rule 1",
    "Has not yet named built-in semantics and behavior beyond keyboard support",
    "Has not yet applied the rule across multiple examples",
    "Has not yet worked through Rule 2 about not overriding native semantics",
    "Has not yet handled examples involving invalid or redundant ARIA beyond button/div comparison",
    "Has not yet explained why changing native semantics is risky",
    "Has not yet worked through Rule 2 examples",
    "Has not yet covered role-required states/properties or redundant ARIA"
  ],
  "next_focus": "Introduce Rule 2 with a native element whose role is unnecessarily overridden.",
  "updated_at": "datetime.datetime(2026, 4, 8, 19, 55, 2, 105985, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

<details><summary>Learner Memory</summary>

```json
{
  "student_id": "test-conv-195112",
  "summary": "Learner paraphrases rules effectively when grounded in concrete HTML examples.",
  "strengths": [
    "Readiness to engage",
    "Asks focused questions",
    "Uses concrete frontend examples",
    "Shows early conceptual uptake",
    "Reasones causally from examples",
    "Connects concepts to frontend implementation risk",
    "Comfortable using familiar controls like buttons",
    "Uses concrete examples",
    "Can name implicit role/name benefits",
    "Reasons from assistive-tech impact",
    "Applies ideas to familiar frontend markup",
    "States rules in practical language",
    "Reasons from implementation consequences"
  ],
  "support_needs": [
    "Clear framing before rule details",
    "Contrastive examples to separate native HTML from ARIA",
    "Keep building from practical native-vs-custom comparisons",
    "Help making implicit reasoning explicit as a named rule",
    "More examples beyond buttons to stabilize the concept",
    "Keep prompting for explicit rule naming",
    "Use contrastive markup to extend beyond familiar button examples",
    "Need explicit contrastive examples for new rules",
    "Need help moving from prefer-native reasoning to preserve-native reasoning"
  ],
  "tendencies": [
    "Starts from broad practical assumptions",
    "Seeks a big-picture mental model first",
    "Tests understanding by paraphrasing with examples",
    "Paraphrases understanding through practical tradeoffs",
    "Brings in implementation concerns like keyboard support",
    "Answers cautiously but accurately",
    "Builds understanding through practical frontend tradeoffs",
    "Uses button-vs-div examples to test understanding",
    "Frames understanding around practical reliability"
  ],
  "successful_strategies": [
    "Answer the current framing question directly",
    "Use concise contrasts between native HTML and ARIA",
    "Ask contrastive questions",
    "Use familiar controls like button vs div",
    "Use contrastive markup examples",
    "Ask why native is safer, not just which is preferred",
    "Ask what native elements provide for free",
    "Use direct native-vs-ARIA contrasts",
    "Ask for rule restatement in their own words",
    "Use concrete native-vs-custom comparisons"
  ],
  "updated_at": "datetime.datetime(2026, 4, 8, 19, 55, 2, 107100, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

---

### Turn 6: exploration → exploration
**Tutor time**: 19.92s | **Student agent time**: 2.21s | **Turns on obj**: 5 → 6

**Student**:
> It can confuse assistive tech because you’re basically overriding the button’s real meaning. So the screen reader might announce the wrong role, and people could expect link behavior or lose the button semantics entirely.

**Tutor**:
> Exactly. That’s why this rule exists: changing native semantics can create conflicting signals, and assistive tech may no longer get the reliable role and behavior it expects.

A strong reason would have to be exceptional and well-justified — not just styling or convenience. In practice, the safer default is to preserve the native meaning and behavior.

What would you say is the core risk of overriding a native element’s role, in one sentence?

<details><summary>WebSocket Events (6 non-token)</summary>

```json
[
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Analyzing your response...",
    "_ts": "2026-04-08T19:55:03.856749"
  },
  {
    "type": "stage",
    "stage": "composing",
    "detail": "Generating response (exploration)...",
    "_ts": "2026-04-08T19:55:20.928053"
  },
  {
    "type": "stream_start",
    "_ts": "2026-04-08T19:55:22.932693"
  },
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Updating learning state...",
    "_ts": "2026-04-08T19:55:23.725138"
  },
  {
    "type": "mastery_update",
    "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
    "objective_text": "Apply the five rules for using ARIA correctly",
    "new_level": "in_progress",
    "_ts": "2026-04-08T19:55:23.737198"
  },
  {
    "type": "stream_end",
    "metadata": {
      "session_id": "guided-test-195112",
      "stage": "exploration",
      "stage_advanced": false,
      "assessment": {}
    },
    "_ts": "2026-04-08T19:55:23.737254"
  }
]
```
</details>

**Lesson State**: active=`avoid_redundant_aria`
  `aria_supplemental_metadata` [done], `native_html_semantics_behavior` [done], `prefer_native_over_aria` [done], `preserve_native_semantics` [done], `roles_create_requirements` [done], `include_required_role_states` [done], `aria_is_role_dependent` [done], `use_supported_role_attributes` [done], `implicit_native_roles_states` [done], `avoid_redundant_aria` [wip], `native_aria_conflicts_harm` [todo], `choose_correct_aria_fix` [todo], `multiple_rule_violations` [todo], `justify_rule_based_choices` [todo]

**Mastery**: level=`in_progress` confidence=?

<details><summary>Objective Memory</summary>

```json
{
  "student_id": "test-conv-195112",
  "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
  "summary": "Student can now explain both preferring native HTML and why overriding native semantics is risky.",
  "demonstrated_skills": [
    "Activates prior knowledge",
    "Asks a relevant framing question",
    "Contrasts native HTML with ARIA use",
    "Applies the supplemental-ARIA idea to a concrete control example",
    "Uses native-vs-custom comparison",
    "Gives causal justification for preferring native HTML",
    "Connects accessibility choice to implementation reliability",
    "Names built-in native semantics",
    "Connects native elements to assistive technology reliability",
    "Justifies Rule 1 with concrete markup reasoning",
    "Restates Rule 1 accurately",
    "Uses concrete markup comparison",
    "Connects native HTML to built-in meaning and behavior",
    "Explains risk of overriding native roles",
    "Connects semantics to assistive technology output",
    "Reasons about mismatched user expectations"
  ],
  "active_gaps": [
    "Does not yet distinguish ARIA from correct native HTML",
    "May over-associate ARIA with adding labels and roles",
    "Has not yet articulated what built-in semantics/behavior native elements provide",
    "Has not yet worked through the explicit ARIA rules",
    "Has not yet explicitly stated Rule 1",
    "Has not yet named built-in semantics and behavior beyond keyboard support",
    "Has not yet applied the rule across multiple examples",
    "Has not yet worked through Rule 2 about not overriding native semantics",
    "Has not yet handled examples involving invalid or redundant ARIA beyond button/div comparison",
    "Has not yet explained why changing native semantics is risky",
    "Has not yet worked through Rule 2 examples",
    "Has not yet covered role-required states/properties or redundant ARIA",
    "Has not yet worked with ARIA roles that require specific states or properties",
    "Has not yet checked role-attribute compatibility",
    "Has not yet applied redundancy and conflict rules beyond button examples"
  ],
  "next_focus": "Show that once a non-native ARIA role is chosen, required states/properties may also be needed.",
  "updated_at": "datetime.datetime(2026, 4, 8, 19, 55, 23, 732200, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

<details><summary>Learner Memory</summary>

```json
{
  "student_id": "test-conv-195112",
  "summary": "Learner gives concise causal explanations when asked to predict what goes wrong in concrete markup changes.",
  "strengths": [
    "Readiness to engage",
    "Asks focused questions",
    "Uses concrete frontend examples",
    "Shows early conceptual uptake",
    "Reasones causally from examples",
    "Connects concepts to frontend implementation risk",
    "Comfortable using familiar controls like buttons",
    "Uses concrete examples",
    "Can name implicit role/name benefits",
    "Reasons from assistive-tech impact",
    "Applies ideas to familiar frontend markup",
    "States rules in practical language",
    "Reasons from implementation consequences",
    "Explains cause and effect clearly",
    "Uses assistive-tech perspective appropriately",
    "Transfers from button example to role override risk"
  ],
  "support_needs": [
    "Clear framing before rule details",
    "Contrastive examples to separate native HTML from ARIA",
    "Keep building from practical native-vs-custom comparisons",
    "Help making implicit reasoning explicit as a named rule",
    "More examples beyond buttons to stabilize the concept",
    "Keep prompting for explicit rule naming",
    "Use contrastive markup to extend beyond familiar button examples",
    "Need explicit contrastive examples for new rules",
    "Need help moving from prefer-native reasoning to preserve-native reasoning",
    "Needs continued concrete examples to extend beyond native-vs-custom comparisons",
    "Needs help linking role choice to required ARIA follow-through"
  ],
  "tendencies": [
    "Starts from broad practical assumptions",
    "Seeks a big-picture mental model first",
    "Tests understanding by paraphrasing with examples",
    "Paraphrases understanding through practical tradeoffs",
    "Brings in implementation concerns like keyboard support",
    "Answers cautiously but accurately",
    "Builds understanding through practical frontend tradeoffs",
    "Uses button-vs-div examples to test understanding",
    "Frames understanding around practical reliability",
    "Answers strongest when prompted with a practical failure mode",
    "Frames understanding in terms of user expectations and screen reader output"
  ],
  "successful_strategies": [
    "Answer the current framing question directly",
    "Use concise contrasts between native HTML and ARIA",
    "Ask contrastive questions",
    "Use familiar controls like button vs div",
    "Use contrastive markup examples",
    "Ask why native is safer, not just which is preferred",
    "Ask what native elements provide for free",
    "Use direct native-vs-ARIA contrasts",
    "Ask for rule restatement in their own words",
    "Use concrete native-vs-custom comparisons",
    "Use contrastive examples with native elements",
    "Ask what breaks when semantics are changed",
    "Move from simple controls into concrete ARIA obligations"
  ],
  "updated_at": "datetime.datetime(2026, 4, 8, 19, 55, 23, 733287, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

---

### Turn 7: exploration → exploration
**Tutor time**: 18.03s | **Student agent time**: 1.63s | **Turns on obj**: 6 → 7

**Student**:
> The core risk is that you break the element’s built-in semantics and confuse assistive technologies, so users get the wrong expectations or behavior.

**Tutor**:
> Good — that’s the idea.

Now let’s switch to a different kind of ARIA decision: sometimes choosing a role creates obligations. For example, if you say an element is one thing, what do you think must also be true so assistive technology can actually use it correctly?

<details><summary>WebSocket Events (6 non-token)</summary>

```json
[
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Analyzing your response...",
    "_ts": "2026-04-08T19:55:25.998011"
  },
  {
    "type": "stage",
    "stage": "composing",
    "detail": "Generating response (exploration)...",
    "_ts": "2026-04-08T19:55:41.907677"
  },
  {
    "type": "stream_start",
    "_ts": "2026-04-08T19:55:43.280053"
  },
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Updating learning state...",
    "_ts": "2026-04-08T19:55:43.812074"
  },
  {
    "type": "mastery_update",
    "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
    "objective_text": "Apply the five rules for using ARIA correctly",
    "new_level": "in_progress",
    "_ts": "2026-04-08T19:55:43.984400"
  },
  {
    "type": "stream_end",
    "metadata": {
      "session_id": "guided-test-195112",
      "stage": "exploration",
      "stage_advanced": false,
      "assessment": {}
    },
    "_ts": "2026-04-08T19:55:43.984459"
  }
]
```
</details>

**Lesson State**: active=`avoid_redundant_aria`
  `aria_supplemental_metadata` [done], `native_html_semantics_behavior` [done], `prefer_native_over_aria` [done], `preserve_native_semantics` [done], `roles_create_requirements` [done], `include_required_role_states` [done], `aria_is_role_dependent` [done], `use_supported_role_attributes` [done], `implicit_native_roles_states` [done], `avoid_redundant_aria` [wip], `native_aria_conflicts_harm` [todo], `choose_correct_aria_fix` [todo], `multiple_rule_violations` [todo], `justify_rule_based_choices` [todo]

**Mastery**: level=`in_progress` confidence=?

<details><summary>Objective Memory</summary>

```json
{
  "student_id": "test-conv-195112",
  "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
  "summary": "Student can state Rule 1 in their own words and explain the core risk of overriding native roles.",
  "demonstrated_skills": [
    "Activates prior knowledge",
    "Asks a relevant framing question",
    "Contrasts native HTML with ARIA use",
    "Applies the supplemental-ARIA idea to a concrete control example",
    "Uses native-vs-custom comparison",
    "Gives causal justification for preferring native HTML",
    "Connects accessibility choice to implementation reliability",
    "Names built-in native semantics",
    "Connects native elements to assistive technology reliability",
    "Justifies Rule 1 with concrete markup reasoning",
    "Restates Rule 1 accurately",
    "Uses concrete markup comparison",
    "Connects native HTML to built-in meaning and behavior",
    "Explains risk of overriding native roles",
    "Connects semantics to assistive technology output",
    "Reasons about mismatched user expectations",
    "States prefer-native rule in own words",
    "Explains why changing a native role harms accessibility",
    "Uses causal reasoning about assistive tech and user expectations"
  ],
  "active_gaps": [
    "Does not yet distinguish ARIA from correct native HTML",
    "May over-associate ARIA with adding labels and roles",
    "Has not yet articulated what built-in semantics/behavior native elements provide",
    "Has not yet worked through the explicit ARIA rules",
    "Has not yet explicitly stated Rule 1",
    "Has not yet named built-in semantics and behavior beyond keyboard support",
    "Has not yet applied the rule across multiple examples",
    "Has not yet worked through Rule 2 about not overriding native semantics",
    "Has not yet handled examples involving invalid or redundant ARIA beyond button/div comparison",
    "Has not yet explained why changing native semantics is risky",
    "Has not yet worked through Rule 2 examples",
    "Has not yet covered role-required states/properties or redundant ARIA",
    "Has not yet worked with ARIA roles that require specific states or properties",
    "Has not yet checked role-attribute compatibility",
    "Has not yet applied redundancy and conflict rules beyond button examples",
    "Has not yet explained that selecting an ARIA role creates required state/property obligations",
    "Has not yet worked through Rule 3 examples"
  ],
  "next_focus": "Introduce that once a non-native role is chosen, required ARIA states/properties may also be needed.",
  "updated_at": "datetime.datetime(2026, 4, 8, 19, 55, 43, 967329, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

<details><summary>Learner Memory</summary>

```json
{
  "student_id": "test-conv-195112",
  "summary": "Learner gives stable one-sentence causal summaries when asked to name the accessibility risk in a concrete example.",
  "strengths": [
    "Readiness to engage",
    "Asks focused questions",
    "Uses concrete frontend examples",
    "Shows early conceptual uptake",
    "Reasones causally from examples",
    "Connects concepts to frontend implementation risk",
    "Comfortable using familiar controls like buttons",
    "Uses concrete examples",
    "Can name implicit role/name benefits",
    "Reasons from assistive-tech impact",
    "Applies ideas to familiar frontend markup",
    "States rules in practical language",
    "Reasons from implementation consequences",
    "Explains cause and effect clearly",
    "Uses assistive-tech perspective appropriately",
    "Transfers from button example to role override risk",
    "Concise causal explanations",
    "Good native-vs-ARIA contrast reasoning"
  ],
  "support_needs": [
    "Clear framing before rule details",
    "Contrastive examples to separate native HTML from ARIA",
    "Keep building from practical native-vs-custom comparisons",
    "Help making implicit reasoning explicit as a named rule",
    "More examples beyond buttons to stabilize the concept",
    "Keep prompting for explicit rule naming",
    "Use contrastive markup to extend beyond familiar button examples",
    "Need explicit contrastive examples for new rules",
    "Need help moving from prefer-native reasoning to preserve-native reasoning",
    "Needs continued concrete examples to extend beyond native-vs-custom comparisons",
    "Needs help linking role choice to required ARIA follow-through",
    "Prompting to extend from rule idea to technical role obligations"
  ],
  "tendencies": [
    "Starts from broad practical assumptions",
    "Seeks a big-picture mental model first",
    "Tests understanding by paraphrasing with examples",
    "Paraphrases understanding through practical tradeoffs",
    "Brings in implementation concerns like keyboard support",
    "Answers cautiously but accurately",
    "Builds understanding through practical frontend tradeoffs",
    "Uses button-vs-div examples to test understanding",
    "Frames understanding around practical reliability",
    "Answers strongest when prompted with a practical failure mode",
    "Frames understanding in terms of user expectations and screen reader output",
    "Repeats a solid answer verbatim when confident"
  ],
  "successful_strategies": [
    "Answer the current framing question directly",
    "Use concise contrasts between native HTML and ARIA",
    "Ask contrastive questions",
    "Use familiar controls like button vs div",
    "Use contrastive markup examples",
    "Ask why native is safer, not just which is preferred",
    "Ask what native elements provide for free",
    "Use direct native-vs-ARIA contrasts",
    "Ask for rule restatement in their own words",
    "Use concrete native-vs-custom comparisons",
    "Use contrastive examples with native elements",
    "Ask what breaks when semantics are changed",
    "Move from simple controls into concrete ARIA obligations",
    "Ask for one-sentence risk summaries",
    "Bridge from concrete misuse to the next rule"
  ],
  "updated_at": "datetime.datetime(2026, 4, 8, 19, 55, 43, 974625, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

---

### Turn 8: exploration → exploration
**Tutor time**: 19.4s | **Student agent time**: 1.65s | **Turns on obj**: 7 → 8

**Student**:
> I think the behavior and states have to match the role, like if you call something a checkbox it should act like one and expose checked/unchecked properly. Otherwise ARIA is kinda lying about what it is.

**Tutor**:
> Yes — that’s the key point.

If you choose a role, you’re not just naming it; you’re also taking on the ARIA states and properties that role needs. Your checkbox example is good: if it’s announced as a checkbox, it must expose the checked state correctly, or assistive tech gets an incomplete or misleading control.

What do you think happens to accessibility if a role is present but one of its required states is missing?

<details><summary>WebSocket Events (6 non-token)</summary>

```json
[
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Analyzing your response...",
    "_ts": "2026-04-08T19:55:45.678347"
  },
  {
    "type": "stage",
    "stage": "composing",
    "detail": "Generating response (exploration)...",
    "_ts": "2026-04-08T19:56:02.221204"
  },
  {
    "type": "stream_start",
    "_ts": "2026-04-08T19:56:04.209780"
  },
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Updating learning state...",
    "_ts": "2026-04-08T19:56:05.014831"
  },
  {
    "type": "mastery_update",
    "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
    "objective_text": "Apply the five rules for using ARIA correctly",
    "new_level": "in_progress",
    "_ts": "2026-04-08T19:56:05.028569"
  },
  {
    "type": "stream_end",
    "metadata": {
      "session_id": "guided-test-195112",
      "stage": "exploration",
      "stage_advanced": false,
      "assessment": {}
    },
    "_ts": "2026-04-08T19:56:05.028591"
  }
]
```
</details>

**Lesson State**: active=`avoid_redundant_aria`
  `aria_supplemental_metadata` [done], `native_html_semantics_behavior` [done], `prefer_native_over_aria` [done], `preserve_native_semantics` [done], `roles_create_requirements` [done], `include_required_role_states` [done], `aria_is_role_dependent` [done], `use_supported_role_attributes` [done], `implicit_native_roles_states` [done], `avoid_redundant_aria` [wip], `native_aria_conflicts_harm` [todo], `choose_correct_aria_fix` [todo], `multiple_rule_violations` [todo], `justify_rule_based_choices` [todo]

**Mastery**: level=`in_progress` confidence=?

<details><summary>Objective Memory</summary>

```json
{
  "student_id": "test-conv-195112",
  "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
  "summary": "Student now explains that assigning an ARIA role creates obligations for matching behavior and exposed states.",
  "demonstrated_skills": [
    "Activates prior knowledge",
    "Asks a relevant framing question",
    "Contrasts native HTML with ARIA use",
    "Applies the supplemental-ARIA idea to a concrete control example",
    "Uses native-vs-custom comparison",
    "Gives causal justification for preferring native HTML",
    "Connects accessibility choice to implementation reliability",
    "Names built-in native semantics",
    "Connects native elements to assistive technology reliability",
    "Justifies Rule 1 with concrete markup reasoning",
    "Restates Rule 1 accurately",
    "Uses concrete markup comparison",
    "Connects native HTML to built-in meaning and behavior",
    "Explains risk of overriding native roles",
    "Connects semantics to assistive technology output",
    "Reasons about mismatched user expectations",
    "States prefer-native rule in own words",
    "Explains why changing a native role harms accessibility",
    "Uses causal reasoning about assistive tech and user expectations",
    "Causal explanation of role mismatch risk",
    "Transfers concept to checkbox example",
    "Connects role choice to required state exposure"
  ],
  "active_gaps": [
    "Does not yet distinguish ARIA from correct native HTML",
    "May over-associate ARIA with adding labels and roles",
    "Has not yet articulated what built-in semantics/behavior native elements provide",
    "Has not yet worked through the explicit ARIA rules",
    "Has not yet explicitly stated Rule 1",
    "Has not yet named built-in semantics and behavior beyond keyboard support",
    "Has not yet applied the rule across multiple examples",
    "Has not yet worked through Rule 2 about not overriding native semantics",
    "Has not yet handled examples involving invalid or redundant ARIA beyond button/div comparison",
    "Has not yet explained why changing native semantics is risky",
    "Has not yet worked through Rule 2 examples",
    "Has not yet covered role-required states/properties or redundant ARIA",
    "Has not yet worked with ARIA roles that require specific states or properties",
    "Has not yet checked role-attribute compatibility",
    "Has not yet applied redundancy and conflict rules beyond button examples",
    "Has not yet explained that selecting an ARIA role creates required state/property obligations",
    "Has not yet worked through Rule 3 examples",
    "Has not yet worked through explicit required-state examples",
    "Has not yet checked validity/completeness of required ARIA properties in markup",
    "Has not yet addressed role-dependent attribute support or redundancy rules"
  ],
  "next_focus": "Teach Rule 3 with a concrete example where a role is present but required state/property is missing.",
  "updated_at": "datetime.datetime(2026, 4, 8, 19, 56, 5, 22752, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

<details><summary>Learner Memory</summary>

```json
{
  "student_id": "test-conv-195112",
  "summary": "Learner reasons well from concrete widget examples and can extend a rule to a new role with a concise causal explanation.",
  "strengths": [
    "Readiness to engage",
    "Asks focused questions",
    "Uses concrete frontend examples",
    "Shows early conceptual uptake",
    "Reasones causally from examples",
    "Connects concepts to frontend implementation risk",
    "Comfortable using familiar controls like buttons",
    "Uses concrete examples",
    "Can name implicit role/name benefits",
    "Reasons from assistive-tech impact",
    "Applies ideas to familiar frontend markup",
    "States rules in practical language",
    "Reasons from implementation consequences",
    "Explains cause and effect clearly",
    "Uses assistive-tech perspective appropriately",
    "Transfers from button example to role override risk",
    "Concise causal explanations",
    "Good native-vs-ARIA contrast reasoning",
    "Transfer from prior rule to new ARIA concept",
    "Uses concrete control examples",
    "Explains risks in user-impact terms"
  ],
  "support_needs": [
    "Clear framing before rule details",
    "Contrastive examples to separate native HTML from ARIA",
    "Keep building from practical native-vs-custom comparisons",
    "Help making implicit reasoning explicit as a named rule",
    "More examples beyond buttons to stabilize the concept",
    "Keep prompting for explicit rule naming",
    "Use contrastive markup to extend beyond familiar button examples",
    "Need explicit contrastive examples for new rules",
    "Need help moving from prefer-native reasoning to preserve-native reasoning",
    "Needs continued concrete examples to extend beyond native-vs-custom comparisons",
    "Needs help linking role choice to required ARIA follow-through",
    "Prompting to extend from rule idea to technical role obligations",
    "Worked examples to move from general principle to exact required ARIA states/properties",
    "Help distinguishing broad behavior matching from specific rule checks"
  ],
  "tendencies": [
    "Starts from broad practical assumptions",
    "Seeks a big-picture mental model first",
    "Tests understanding by paraphrasing with examples",
    "Paraphrases understanding through practical tradeoffs",
    "Brings in implementation concerns like keyboard support",
    "Answers cautiously but accurately",
    "Builds understanding through practical frontend tradeoffs",
    "Uses button-vs-div examples to test understanding",
    "Frames understanding around practical reliability",
    "Answers strongest when prompted with a practical failure mode",
    "Frames understanding in terms of user expectations and screen reader output",
    "Repeats a solid answer verbatim when confident",
    "Paraphrases concepts through practical implementation examples",
    "Frames incorrect ARIA as misleading semantics"
  ],
  "successful_strategies": [
    "Answer the current framing question directly",
    "Use concise contrasts between native HTML and ARIA",
    "Ask contrastive questions",
    "Use familiar controls like button vs div",
    "Use contrastive markup examples",
    "Ask why native is safer, not just which is preferred",
    "Ask what native elements provide for free",
    "Use direct native-vs-ARIA contrasts",
    "Ask for rule restatement in their own words",
    "Use concrete native-vs-custom comparisons",
    "Use contrastive examples with native elements",
    "Ask what breaks when semantics are changed",
    "Move from simple controls into concrete ARIA obligations",
    "Ask for one-sentence risk summaries",
    "Bridge from concrete misuse to the next rule",
    "Ask for one-step transfer to a familiar control",
    "Use concrete role examples like checkbox",
    "Follow principle with markup-based checking"
  ],
  "updated_at": "datetime.datetime(2026, 4, 8, 19, 56, 5, 24392, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

---

### Turn 9: exploration → exploration
**Tutor time**: 17.35s | **Student agent time**: 1.45s | **Turns on obj**: 8 → 9

**Student**:
> Then the control is basically broken or incomplete for assistive tech, right? Like it might still get read as a checkbox but users won’t know its actual state, so they can’t use it properly.

**Tutor**:
> Exactly. For 4.1.2 Name, Role, Value, the control has to expose the information assistive tech needs to understand and interact with it: the right role, and the right state/value when that role requires one.

So the practical rule is: if you use a role, check whether that role comes with required state or property information, and make sure it’s present and valid.

If I give you a snippet with `role="checkbox"` but no `aria-checked`, would you treat that as a complete checkbox for assistive tech, or not?

<details><summary>WebSocket Events (6 non-token)</summary>

```json
[
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Analyzing your response...",
    "_ts": "2026-04-08T19:56:06.719503"
  },
  {
    "type": "stage",
    "stage": "composing",
    "detail": "Generating response (exploration)...",
    "_ts": "2026-04-08T19:56:21.149351"
  },
  {
    "type": "stream_start",
    "_ts": "2026-04-08T19:56:22.964383"
  },
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Updating learning state...",
    "_ts": "2026-04-08T19:56:24.006521"
  },
  {
    "type": "mastery_update",
    "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
    "objective_text": "Apply the five rules for using ARIA correctly",
    "new_level": "in_progress",
    "_ts": "2026-04-08T19:56:24.030252"
  },
  {
    "type": "stream_end",
    "metadata": {
      "session_id": "guided-test-195112",
      "stage": "exploration",
      "stage_advanced": false,
      "assessment": {}
    },
    "_ts": "2026-04-08T19:56:24.030340"
  }
]
```
</details>

**Lesson State**: active=`avoid_redundant_aria`
  `aria_supplemental_metadata` [done], `native_html_semantics_behavior` [done], `prefer_native_over_aria` [done], `preserve_native_semantics` [done], `roles_create_requirements` [done], `include_required_role_states` [done], `aria_is_role_dependent` [done], `use_supported_role_attributes` [done], `implicit_native_roles_states` [done], `avoid_redundant_aria` [wip], `native_aria_conflicts_harm` [todo], `choose_correct_aria_fix` [todo], `multiple_rule_violations` [todo], `justify_rule_based_choices` [todo]

**Mastery**: level=`in_progress` confidence=?

<details><summary>Objective Memory</summary>

```json
{
  "student_id": "test-conv-195112",
  "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
  "summary": "Student explains that if a role is present but a required state is missing, the control is incomplete or broken for assistive tech because users cannot determine its actual state.",
  "demonstrated_skills": [
    "Activates prior knowledge",
    "Asks a relevant framing question",
    "Contrasts native HTML with ARIA use",
    "Applies the supplemental-ARIA idea to a concrete control example",
    "Uses native-vs-custom comparison",
    "Gives causal justification for preferring native HTML",
    "Connects accessibility choice to implementation reliability",
    "Names built-in native semantics",
    "Connects native elements to assistive technology reliability",
    "Justifies Rule 1 with concrete markup reasoning",
    "Restates Rule 1 accurately",
    "Uses concrete markup comparison",
    "Connects native HTML to built-in meaning and behavior",
    "Explains risk of overriding native roles",
    "Connects semantics to assistive technology output",
    "Reasons about mismatched user expectations",
    "States prefer-native rule in own words",
    "Explains why changing a native role harms accessibility",
    "Uses causal reasoning about assistive tech and user expectations",
    "Causal explanation of role mismatch risk",
    "Transfers concept to checkbox example",
    "Connects role choice to required state exposure",
    "Explains causal impact of missing required ARIA state",
    "Connects role/state mismatch to user-facing accessibility failure",
    "Uses checkbox as a transfer example"
  ],
  "active_gaps": [
    "Does not yet distinguish ARIA from correct native HTML",
    "May over-associate ARIA with adding labels and roles",
    "Has not yet articulated what built-in semantics/behavior native elements provide",
    "Has not yet worked through the explicit ARIA rules",
    "Has not yet explicitly stated Rule 1",
    "Has not yet named built-in semantics and behavior beyond keyboard support",
    "Has not yet applied the rule across multiple examples",
    "Has not yet worked through Rule 2 about not overriding native semantics",
    "Has not yet handled examples involving invalid or redundant ARIA beyond button/div comparison",
    "Has not yet explained why changing native semantics is risky",
    "Has not yet worked through Rule 2 examples",
    "Has not yet covered role-required states/properties or redundant ARIA",
    "Has not yet worked with ARIA roles that require specific states or properties",
    "Has not yet checked role-attribute compatibility",
    "Has not yet applied redundancy and conflict rules beyond button examples",
    "Has not yet explained that selecting an ARIA role creates required state/property obligations",
    "Has not yet worked through Rule 3 examples",
    "Has not yet worked through explicit required-state examples",
    "Has not yet checked validity/completeness of required ARIA properties in markup",
    "Has not yet addressed role-dependent attribute support or redundancy rules",
    "Has not yet diagnosed missing required states/properties in markup",
    "Has not yet named Rule 3 explicitly"
  ],
  "next_focus": "Give a concrete snippet with a role and ask the student to identify the missing required state/property and the correct fix.",
  "updated_at": "datetime.datetime(2026, 4, 8, 19, 56, 24, 20668, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

<details><summary>Learner Memory</summary>

```json
{
  "student_id": "test-conv-195112",
  "summary": "Learner continues to reason accurately from concrete controls and explains accessibility impact in user-centered terms.",
  "strengths": [
    "Readiness to engage",
    "Asks focused questions",
    "Uses concrete frontend examples",
    "Shows early conceptual uptake",
    "Reasones causally from examples",
    "Connects concepts to frontend implementation risk",
    "Comfortable using familiar controls like buttons",
    "Uses concrete examples",
    "Can name implicit role/name benefits",
    "Reasons from assistive-tech impact",
    "Applies ideas to familiar frontend markup",
    "States rules in practical language",
    "Reasons from implementation consequences",
    "Explains cause and effect clearly",
    "Uses assistive-tech perspective appropriately",
    "Transfers from button example to role override risk",
    "Concise causal explanations",
    "Good native-vs-ARIA contrast reasoning",
    "Transfer from prior rule to new ARIA concept",
    "Uses concrete control examples",
    "Explains risks in user-impact terms",
    "Causal reasoning",
    "Concrete transfer from examples",
    "Connects code choices to assistive-tech consequences"
  ],
  "support_needs": [
    "Clear framing before rule details",
    "Contrastive examples to separate native HTML from ARIA",
    "Keep building from practical native-vs-custom comparisons",
    "Help making implicit reasoning explicit as a named rule",
    "More examples beyond buttons to stabilize the concept",
    "Keep prompting for explicit rule naming",
    "Use contrastive markup to extend beyond familiar button examples",
    "Need explicit contrastive examples for new rules",
    "Need help moving from prefer-native reasoning to preserve-native reasoning",
    "Needs continued concrete examples to extend beyond native-vs-custom comparisons",
    "Needs help linking role choice to required ARIA follow-through",
    "Prompting to extend from rule idea to technical role obligations",
    "Worked examples to move from general principle to exact required ARIA states/properties",
    "Help distinguishing broad behavior matching from specific rule checks",
    "Practice spotting issues directly in markup",
    "Help tying intuitive explanation to formal rule names"
  ],
  "tendencies": [
    "Starts from broad practical assumptions",
    "Seeks a big-picture mental model first",
    "Tests understanding by paraphrasing with examples",
    "Paraphrases understanding through practical tradeoffs",
    "Brings in implementation concerns like keyboard support",
    "Answers cautiously but accurately",
    "Builds understanding through practical frontend tradeoffs",
    "Uses button-vs-div examples to test understanding",
    "Frames understanding around practical reliability",
    "Answers strongest when prompted with a practical failure mode",
    "Frames understanding in terms of user expectations and screen reader output",
    "Repeats a solid answer verbatim when confident",
    "Paraphrases concepts through practical implementation examples",
    "Frames incorrect ARIA as misleading semantics",
    "Answers by paraphrasing the consequence in practical terms",
    "Uses familiar widgets to test understanding"
  ],
  "successful_strategies": [
    "Answer the current framing question directly",
    "Use concise contrasts between native HTML and ARIA",
    "Ask contrastive questions",
    "Use familiar controls like button vs div",
    "Use contrastive markup examples",
    "Ask why native is safer, not just which is preferred",
    "Ask what native elements provide for free",
    "Use direct native-vs-ARIA contrasts",
    "Ask for rule restatement in their own words",
    "Use concrete native-vs-custom comparisons",
    "Use contrastive examples with native elements",
    "Ask what breaks when semantics are changed",
    "Move from simple controls into concrete ARIA obligations",
    "Ask for one-sentence risk summaries",
    "Bridge from concrete misuse to the next rule",
    "Ask for one-step transfer to a familiar control",
    "Use concrete role examples like checkbox",
    "Follow principle with markup-based checking",
    "Short worked examples",
    "Concrete role-plus-state scenarios",
    "Ask for the practical consequence before naming the rule"
  ],
  "updated_at": "datetime.datetime(2026, 4, 8, 19, 56, 24, 24349, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

---

### Turn 10: exploration → exploration
**Tutor time**: 18.15s | **Student agent time**: 1.44s | **Turns on obj**: 9 → 10

**Student**:
> No, I wouldn’t treat it as complete. A checkbox role without `aria-checked` is missing a required state, so AT wouldn’t get the full info it needs.

**Tutor**:
> Right. That’s the rule in action: a role isn’t complete unless its required state or property is there and valid.

Let’s make it concrete: if you saw `<div role="checkbox"></div>`, what would be the smallest fix to make it a valid checkbox for assistive tech?

<details><summary>WebSocket Events (6 non-token)</summary>

```json
[
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Analyzing your response...",
    "_ts": "2026-04-08T19:56:25.527375"
  },
  {
    "type": "stage",
    "stage": "composing",
    "detail": "Generating response (exploration)...",
    "_ts": "2026-04-08T19:56:41.667707"
  },
  {
    "type": "stream_start",
    "_ts": "2026-04-08T19:56:43.074591"
  },
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Updating learning state...",
    "_ts": "2026-04-08T19:56:43.617197"
  },
  {
    "type": "mastery_update",
    "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
    "objective_text": "Apply the five rules for using ARIA correctly",
    "new_level": "in_progress",
    "_ts": "2026-04-08T19:56:43.634488"
  },
  {
    "type": "stream_end",
    "metadata": {
      "session_id": "guided-test-195112",
      "stage": "exploration",
      "stage_advanced": false,
      "assessment": {}
    },
    "_ts": "2026-04-08T19:56:43.634514"
  }
]
```
</details>

**Lesson State**: active=`avoid_redundant_aria`
  `aria_supplemental_metadata` [done], `native_html_semantics_behavior` [done], `prefer_native_over_aria` [done], `preserve_native_semantics` [done], `roles_create_requirements` [done], `include_required_role_states` [done], `aria_is_role_dependent` [done], `use_supported_role_attributes` [done], `implicit_native_roles_states` [done], `avoid_redundant_aria` [wip], `native_aria_conflicts_harm` [todo], `choose_correct_aria_fix` [todo], `multiple_rule_violations` [todo], `justify_rule_based_choices` [todo]

**Mastery**: level=`in_progress` confidence=?

<details><summary>Objective Memory</summary>

```json
{
  "student_id": "test-conv-195112",
  "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
  "summary": "Student now recognizes that a chosen role can be incomplete if its required state is missing, and applies this to checkbox plus aria-checked.",
  "demonstrated_skills": [
    "Activates prior knowledge",
    "Asks a relevant framing question",
    "Contrasts native HTML with ARIA use",
    "Applies the supplemental-ARIA idea to a concrete control example",
    "Uses native-vs-custom comparison",
    "Gives causal justification for preferring native HTML",
    "Connects accessibility choice to implementation reliability",
    "Names built-in native semantics",
    "Connects native elements to assistive technology reliability",
    "Justifies Rule 1 with concrete markup reasoning",
    "Restates Rule 1 accurately",
    "Uses concrete markup comparison",
    "Connects native HTML to built-in meaning and behavior",
    "Explains risk of overriding native roles",
    "Connects semantics to assistive technology output",
    "Reasons about mismatched user expectations",
    "States prefer-native rule in own words",
    "Explains why changing a native role harms accessibility",
    "Uses causal reasoning about assistive tech and user expectations",
    "Causal explanation of role mismatch risk",
    "Transfers concept to checkbox example",
    "Connects role choice to required state exposure",
    "Explains causal impact of missing required ARIA state",
    "Connects role/state mismatch to user-facing accessibility failure",
    "Uses checkbox as a transfer example",
    "Identifies missing required ARIA state in a concrete snippet",
    "Explains user impact of incomplete role/state exposure",
    "Applies Rule 3 reasoning to checkbox example"
  ],
  "active_gaps": [
    "Does not yet distinguish ARIA from correct native HTML",
    "May over-associate ARIA with adding labels and roles",
    "Has not yet articulated what built-in semantics/behavior native elements provide",
    "Has not yet worked through the explicit ARIA rules",
    "Has not yet explicitly stated Rule 1",
    "Has not yet named built-in semantics and behavior beyond keyboard support",
    "Has not yet applied the rule across multiple examples",
    "Has not yet worked through Rule 2 about not overriding native semantics",
    "Has not yet handled examples involving invalid or redundant ARIA beyond button/div comparison",
    "Has not yet explained why changing native semantics is risky",
    "Has not yet worked through Rule 2 examples",
    "Has not yet covered role-required states/properties or redundant ARIA",
    "Has not yet worked with ARIA roles that require specific states or properties",
    "Has not yet checked role-attribute compatibility",
    "Has not yet applied redundancy and conflict rules beyond button examples",
    "Has not yet explained that selecting an ARIA role creates required state/property obligations",
    "Has not yet worked through Rule 3 examples",
    "Has not yet worked through explicit required-state examples",
    "Has not yet checked validity/completeness of required ARIA properties in markup",
    "Has not yet addressed role-dependent attribute support or redundancy rules",
    "Has not yet diagnosed missing required states/properties in markup",
    "Has not yet named Rule 3 explicitly",
    "Has not yet distinguished required role states from merely supported attributes",
    "Has not yet checked whether a given ARIA attribute is valid for a specific role",
    "Has not yet worked through redundancy and conflict rules"
  ],
  "next_focus": "Test whether the learner can spot an ARIA state/property that is invalid for a role, not just missing.",
  "updated_at": "datetime.datetime(2026, 4, 8, 19, 56, 43, 625488, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

<details><summary>Learner Memory</summary>

```json
{
  "student_id": "test-conv-195112",
  "summary": "Learner reasons reliably from concrete examples and explains failures in terms of incomplete information for assistive tech.",
  "strengths": [
    "Readiness to engage",
    "Asks focused questions",
    "Uses concrete frontend examples",
    "Shows early conceptual uptake",
    "Reasones causally from examples",
    "Connects concepts to frontend implementation risk",
    "Comfortable using familiar controls like buttons",
    "Uses concrete examples",
    "Can name implicit role/name benefits",
    "Reasons from assistive-tech impact",
    "Applies ideas to familiar frontend markup",
    "States rules in practical language",
    "Reasons from implementation consequences",
    "Explains cause and effect clearly",
    "Uses assistive-tech perspective appropriately",
    "Transfers from button example to role override risk",
    "Concise causal explanations",
    "Good native-vs-ARIA contrast reasoning",
    "Transfer from prior rule to new ARIA concept",
    "Uses concrete control examples",
    "Explains risks in user-impact terms",
    "Causal reasoning",
    "Concrete transfer from examples",
    "Connects code choices to assistive-tech consequences",
    "Concrete causal reasoning",
    "Applies rule to markup examples",
    "Frames issues in user-impact terms"
  ],
  "support_needs": [
    "Clear framing before rule details",
    "Contrastive examples to separate native HTML from ARIA",
    "Keep building from practical native-vs-custom comparisons",
    "Help making implicit reasoning explicit as a named rule",
    "More examples beyond buttons to stabilize the concept",
    "Keep prompting for explicit rule naming",
    "Use contrastive markup to extend beyond familiar button examples",
    "Need explicit contrastive examples for new rules",
    "Need help moving from prefer-native reasoning to preserve-native reasoning",
    "Needs continued concrete examples to extend beyond native-vs-custom comparisons",
    "Needs help linking role choice to required ARIA follow-through",
    "Prompting to extend from rule idea to technical role obligations",
    "Worked examples to move from general principle to exact required ARIA states/properties",
    "Help distinguishing broad behavior matching from specific rule checks",
    "Practice spotting issues directly in markup",
    "Help tying intuitive explanation to formal rule names",
    "Keep examples concrete and role-specific",
    "Help separate required attributes from valid-but-optional ones"
  ],
  "tendencies": [
    "Starts from broad practical assumptions",
    "Seeks a big-picture mental model first",
    "Tests understanding by paraphrasing with examples",
    "Paraphrases understanding through practical tradeoffs",
    "Brings in implementation concerns like keyboard support",
    "Answers cautiously but accurately",
    "Builds understanding through practical frontend tradeoffs",
    "Uses button-vs-div examples to test understanding",
    "Frames understanding around practical reliability",
    "Answers strongest when prompted with a practical failure mode",
    "Frames understanding in terms of user expectations and screen reader output",
    "Repeats a solid answer verbatim when confident",
    "Paraphrases concepts through practical implementation examples",
    "Frames incorrect ARIA as misleading semantics",
    "Answers by paraphrasing the consequence in practical terms",
    "Uses familiar widgets to test understanding",
    "Answers directly and accurately when given a specific snippet",
    "Uses concise practical language rather than formal rule names"
  ],
  "successful_strategies": [
    "Answer the current framing question directly",
    "Use concise contrasts between native HTML and ARIA",
    "Ask contrastive questions",
    "Use familiar controls like button vs div",
    "Use contrastive markup examples",
    "Ask why native is safer, not just which is preferred",
    "Ask what native elements provide for free",
    "Use direct native-vs-ARIA contrasts",
    "Ask for rule restatement in their own words",
    "Use concrete native-vs-custom comparisons",
    "Use contrastive examples with native elements",
    "Ask what breaks when semantics are changed",
    "Move from simple controls into concrete ARIA obligations",
    "Ask for one-sentence risk summaries",
    "Bridge from concrete misuse to the next rule",
    "Ask for one-step transfer to a familiar control",
    "Use concrete role examples like checkbox",
    "Follow principle with markup-based checking",
    "Short worked examples",
    "Concrete role-plus-state scenarios",
    "Ask for the practical consequence before naming the rule",
    "Snippet-based checks",
    "Ask whether AT has enough information",
    "Use familiar controls like checkbox"
  ],
  "updated_at": "datetime.datetime(2026, 4, 8, 19, 56, 43, 628751, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

---

### Turn 11: exploration → exploration
**Tutor time**: 19.43s | **Student agent time**: 2.0s | **Turns on obj**: 10 → 11

**Student**:
> Add `aria-checked`, probably `aria-checked="false"` or `"true"` depending on state. So like `<div role="checkbox" aria-checked="false"></div>`.

**Tutor**:
> Yes — that’s the right kind of fix. For a checkbox role, `aria-checked` is a valid required state, and it must reflect the current state.

Now let’s test the next rule: if you had `role="button" aria-checked="true"`, would you accept that pairing, or would you reject it?

<details><summary>WebSocket Events (6 non-token)</summary>

```json
[
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Analyzing your response...",
    "_ts": "2026-04-08T19:56:45.112803"
  },
  {
    "type": "stage",
    "stage": "composing",
    "detail": "Generating response (exploration)...",
    "_ts": "2026-04-08T19:57:01.917915"
  },
  {
    "type": "stream_start",
    "_ts": "2026-04-08T19:57:03.869846"
  },
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Updating learning state...",
    "_ts": "2026-04-08T19:57:04.494188"
  },
  {
    "type": "mastery_update",
    "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
    "objective_text": "Apply the five rules for using ARIA correctly",
    "new_level": "in_progress",
    "_ts": "2026-04-08T19:57:04.515023"
  },
  {
    "type": "stream_end",
    "metadata": {
      "session_id": "guided-test-195112",
      "stage": "exploration",
      "stage_advanced": false,
      "assessment": {}
    },
    "_ts": "2026-04-08T19:57:04.515093"
  }
]
```
</details>

**Lesson State**: active=`avoid_redundant_aria`
  `aria_supplemental_metadata` [done], `native_html_semantics_behavior` [done], `prefer_native_over_aria` [done], `preserve_native_semantics` [done], `roles_create_requirements` [done], `include_required_role_states` [done], `aria_is_role_dependent` [done], `use_supported_role_attributes` [done], `implicit_native_roles_states` [done], `avoid_redundant_aria` [wip], `native_aria_conflicts_harm` [todo], `choose_correct_aria_fix` [todo], `multiple_rule_violations` [todo], `justify_rule_based_choices` [todo]

**Mastery**: level=`in_progress` confidence=?

<details><summary>Objective Memory</summary>

```json
{
  "student_id": "test-conv-195112",
  "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
  "summary": "Student can now repair a checkbox role by adding the required aria-checked state and explains why missing state leaves AT with incomplete information.",
  "demonstrated_skills": [
    "Activates prior knowledge",
    "Asks a relevant framing question",
    "Contrasts native HTML with ARIA use",
    "Applies the supplemental-ARIA idea to a concrete control example",
    "Uses native-vs-custom comparison",
    "Gives causal justification for preferring native HTML",
    "Connects accessibility choice to implementation reliability",
    "Names built-in native semantics",
    "Connects native elements to assistive technology reliability",
    "Justifies Rule 1 with concrete markup reasoning",
    "Restates Rule 1 accurately",
    "Uses concrete markup comparison",
    "Connects native HTML to built-in meaning and behavior",
    "Explains risk of overriding native roles",
    "Connects semantics to assistive technology output",
    "Reasons about mismatched user expectations",
    "States prefer-native rule in own words",
    "Explains why changing a native role harms accessibility",
    "Uses causal reasoning about assistive tech and user expectations",
    "Causal explanation of role mismatch risk",
    "Transfers concept to checkbox example",
    "Connects role choice to required state exposure",
    "Explains causal impact of missing required ARIA state",
    "Connects role/state mismatch to user-facing accessibility failure",
    "Uses checkbox as a transfer example",
    "Identifies missing required ARIA state in a concrete snippet",
    "Explains user impact of incomplete role/state exposure",
    "Applies Rule 3 reasoning to checkbox example",
    "Applies required-state reasoning to role=\"checkbox\"",
    "Suggests a minimal valid ARIA fix",
    "Explains impact on assistive tech in causal terms"
  ],
  "active_gaps": [
    "Does not yet distinguish ARIA from correct native HTML",
    "May over-associate ARIA with adding labels and roles",
    "Has not yet articulated what built-in semantics/behavior native elements provide",
    "Has not yet worked through the explicit ARIA rules",
    "Has not yet explicitly stated Rule 1",
    "Has not yet named built-in semantics and behavior beyond keyboard support",
    "Has not yet applied the rule across multiple examples",
    "Has not yet worked through Rule 2 about not overriding native semantics",
    "Has not yet handled examples involving invalid or redundant ARIA beyond button/div comparison",
    "Has not yet explained why changing native semantics is risky",
    "Has not yet worked through Rule 2 examples",
    "Has not yet covered role-required states/properties or redundant ARIA",
    "Has not yet worked with ARIA roles that require specific states or properties",
    "Has not yet checked role-attribute compatibility",
    "Has not yet applied redundancy and conflict rules beyond button examples",
    "Has not yet explained that selecting an ARIA role creates required state/property obligations",
    "Has not yet worked through Rule 3 examples",
    "Has not yet worked through explicit required-state examples",
    "Has not yet checked validity/completeness of required ARIA properties in markup",
    "Has not yet addressed role-dependent attribute support or redundancy rules",
    "Has not yet diagnosed missing required states/properties in markup",
    "Has not yet named Rule 3 explicitly",
    "Has not yet distinguished required role states from merely supported attributes",
    "Has not yet checked whether a given ARIA attribute is valid for a specific role",
    "Has not yet worked through redundancy and conflict rules",
    "Has not yet shown that some ARIA attributes are invalid for some roles",
    "Has not yet named or applied Rule 4 explicitly",
    "Has not yet worked with implicit native semantics or redundant ARIA"
  ],
  "next_focus": "Test whether the learner can spot and reject an unsupported ARIA state/property for a role.",
  "updated_at": "datetime.datetime(2026, 4, 8, 19, 57, 4, 506316, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

<details><summary>Learner Memory</summary>

```json
{
  "student_id": "test-conv-195112",
  "summary": "Learner continues to reason well from concrete markup and can propose minimal fixes that preserve accessibility meaning.",
  "strengths": [
    "Readiness to engage",
    "Asks focused questions",
    "Uses concrete frontend examples",
    "Shows early conceptual uptake",
    "Reasones causally from examples",
    "Connects concepts to frontend implementation risk",
    "Comfortable using familiar controls like buttons",
    "Uses concrete examples",
    "Can name implicit role/name benefits",
    "Reasons from assistive-tech impact",
    "Applies ideas to familiar frontend markup",
    "States rules in practical language",
    "Reasons from implementation consequences",
    "Explains cause and effect clearly",
    "Uses assistive-tech perspective appropriately",
    "Transfers from button example to role override risk",
    "Concise causal explanations",
    "Good native-vs-ARIA contrast reasoning",
    "Transfer from prior rule to new ARIA concept",
    "Uses concrete control examples",
    "Explains risks in user-impact terms",
    "Causal reasoning",
    "Concrete transfer from examples",
    "Connects code choices to assistive-tech consequences",
    "Concrete causal reasoning",
    "Applies rule to markup examples",
    "Frames issues in user-impact terms",
    "Concrete markup reasoning",
    "Causal explanation about AT information needs",
    "Practical repair-oriented thinking"
  ],
  "support_needs": [
    "Clear framing before rule details",
    "Contrastive examples to separate native HTML from ARIA",
    "Keep building from practical native-vs-custom comparisons",
    "Help making implicit reasoning explicit as a named rule",
    "More examples beyond buttons to stabilize the concept",
    "Keep prompting for explicit rule naming",
    "Use contrastive markup to extend beyond familiar button examples",
    "Need explicit contrastive examples for new rules",
    "Need help moving from prefer-native reasoning to preserve-native reasoning",
    "Needs continued concrete examples to extend beyond native-vs-custom comparisons",
    "Needs help linking role choice to required ARIA follow-through",
    "Prompting to extend from rule idea to technical role obligations",
    "Worked examples to move from general principle to exact required ARIA states/properties",
    "Help distinguishing broad behavior matching from specific rule checks",
    "Practice spotting issues directly in markup",
    "Help tying intuitive explanation to formal rule names",
    "Keep examples concrete and role-specific",
    "Help separate required attributes from valid-but-optional ones",
    "Examples that contrast missing required ARIA with invalid ARIA",
    "Explicit naming of the rule after successful reasoning"
  ],
  "tendencies": [
    "Starts from broad practical assumptions",
    "Seeks a big-picture mental model first",
    "Tests understanding by paraphrasing with examples",
    "Paraphrases understanding through practical tradeoffs",
    "Brings in implementation concerns like keyboard support",
    "Answers cautiously but accurately",
    "Builds understanding through practical frontend tradeoffs",
    "Uses button-vs-div examples to test understanding",
    "Frames understanding around practical reliability",
    "Answers strongest when prompted with a practical failure mode",
    "Frames understanding in terms of user expectations and screen reader output",
    "Repeats a solid answer verbatim when confident",
    "Paraphrases concepts through practical implementation examples",
    "Frames incorrect ARIA as misleading semantics",
    "Answers by paraphrasing the consequence in practical terms",
    "Uses familiar widgets to test understanding",
    "Answers directly and accurately when given a specific snippet",
    "Uses concise practical language rather than formal rule names",
    "Answers with implementation-ready examples",
    "Understands completeness of role/state relationships through practical consequences"
  ],
  "successful_strategies": [
    "Answer the current framing question directly",
    "Use concise contrasts between native HTML and ARIA",
    "Ask contrastive questions",
    "Use familiar controls like button vs div",
    "Use contrastive markup examples",
    "Ask why native is safer, not just which is preferred",
    "Ask what native elements provide for free",
    "Use direct native-vs-ARIA contrasts",
    "Ask for rule restatement in their own words",
    "Use concrete native-vs-custom comparisons",
    "Use contrastive examples with native elements",
    "Ask what breaks when semantics are changed",
    "Move from simple controls into concrete ARIA obligations",
    "Ask for one-sentence risk summaries",
    "Bridge from concrete misuse to the next rule",
    "Ask for one-step transfer to a familiar control",
    "Use concrete role examples like checkbox",
    "Follow principle with markup-based checking",
    "Short worked examples",
    "Concrete role-plus-state scenarios",
    "Ask for the practical consequence before naming the rule",
    "Snippet-based checks",
    "Ask whether AT has enough information",
    "Use familiar controls like checkbox",
    "Use short code snippets",
    "Ask for the smallest valid fix",
    "Contrast complete vs incomplete control semantics"
  ],
  "updated_at": "datetime.datetime(2026, 4, 8, 19, 57, 4, 508732, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

---

### Turn 12: exploration → exploration
**Tutor time**: 21.69s | **Student agent time**: 1.49s | **Turns on obj**: 11 → 12

**Student**:
> I’d reject it — `aria-checked` doesn’t belong on a button. If you need a checked state, it should probably be a checkbox or toggle button with the right state like `aria-pressed` instead.

**Tutor**:
> Good. You rejected it for the right reason: ARIA states and properties are role-dependent, so you can’t mix an attribute with a role just because it sounds semantically related.

One small precision: the exact alternative state depends on the control’s real purpose, but the key rule is that the state must be supported by that role. So if the role is `button`, you would not use `aria-checked` unless the role supports it.

Can you restate the rule in one sentence: what should you check before adding an ARIA state or property to a role?

<details><summary>WebSocket Events (6 non-token)</summary>

```json
[
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Analyzing your response...",
    "_ts": "2026-04-08T19:57:06.569065"
  },
  {
    "type": "stage",
    "stage": "composing",
    "detail": "Generating response (exploration)...",
    "_ts": "2026-04-08T19:57:24.755102"
  },
  {
    "type": "stream_start",
    "_ts": "2026-04-08T19:57:27.151791"
  },
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Updating learning state...",
    "_ts": "2026-04-08T19:57:28.200590"
  },
  {
    "type": "mastery_update",
    "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
    "objective_text": "Apply the five rules for using ARIA correctly",
    "new_level": "in_progress",
    "_ts": "2026-04-08T19:57:28.214828"
  },
  {
    "type": "stream_end",
    "metadata": {
      "session_id": "guided-test-195112",
      "stage": "exploration",
      "stage_advanced": false,
      "assessment": {}
    },
    "_ts": "2026-04-08T19:57:28.214869"
  }
]
```
</details>

**Lesson State**: active=`avoid_redundant_aria`
  `aria_supplemental_metadata` [done], `native_html_semantics_behavior` [done], `prefer_native_over_aria` [done], `preserve_native_semantics` [done], `roles_create_requirements` [done], `include_required_role_states` [done], `aria_is_role_dependent` [done], `use_supported_role_attributes` [done], `implicit_native_roles_states` [done], `avoid_redundant_aria` [wip], `native_aria_conflicts_harm` [todo], `choose_correct_aria_fix` [todo], `multiple_rule_violations` [todo], `justify_rule_based_choices` [todo]

**Mastery**: level=`in_progress` confidence=?

<details><summary>Objective Memory</summary>

```json
{
  "student_id": "test-conv-195112",
  "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
  "summary": "Student now rejects unsupported ARIA role/attribute pairings, not just missing required states.",
  "demonstrated_skills": [
    "Activates prior knowledge",
    "Asks a relevant framing question",
    "Contrasts native HTML with ARIA use",
    "Applies the supplemental-ARIA idea to a concrete control example",
    "Uses native-vs-custom comparison",
    "Gives causal justification for preferring native HTML",
    "Connects accessibility choice to implementation reliability",
    "Names built-in native semantics",
    "Connects native elements to assistive technology reliability",
    "Justifies Rule 1 with concrete markup reasoning",
    "Restates Rule 1 accurately",
    "Uses concrete markup comparison",
    "Connects native HTML to built-in meaning and behavior",
    "Explains risk of overriding native roles",
    "Connects semantics to assistive technology output",
    "Reasons about mismatched user expectations",
    "States prefer-native rule in own words",
    "Explains why changing a native role harms accessibility",
    "Uses causal reasoning about assistive tech and user expectations",
    "Causal explanation of role mismatch risk",
    "Transfers concept to checkbox example",
    "Connects role choice to required state exposure",
    "Explains causal impact of missing required ARIA state",
    "Connects role/state mismatch to user-facing accessibility failure",
    "Uses checkbox as a transfer example",
    "Identifies missing required ARIA state in a concrete snippet",
    "Explains user impact of incomplete role/state exposure",
    "Applies Rule 3 reasoning to checkbox example",
    "Applies required-state reasoning to role=\"checkbox\"",
    "Suggests a minimal valid ARIA fix",
    "Explains impact on assistive tech in causal terms",
    "Rejects invalid role/state combinations",
    "Explains why unsupported ARIA is not acceptable",
    "Offers a more suitable semantic alternative"
  ],
  "active_gaps": [
    "Does not yet distinguish ARIA from correct native HTML",
    "May over-associate ARIA with adding labels and roles",
    "Has not yet articulated what built-in semantics/behavior native elements provide",
    "Has not yet worked through the explicit ARIA rules",
    "Has not yet explicitly stated Rule 1",
    "Has not yet named built-in semantics and behavior beyond keyboard support",
    "Has not yet applied the rule across multiple examples",
    "Has not yet worked through Rule 2 about not overriding native semantics",
    "Has not yet handled examples involving invalid or redundant ARIA beyond button/div comparison",
    "Has not yet explained why changing native semantics is risky",
    "Has not yet worked through Rule 2 examples",
    "Has not yet covered role-required states/properties or redundant ARIA",
    "Has not yet worked with ARIA roles that require specific states or properties",
    "Has not yet checked role-attribute compatibility",
    "Has not yet applied redundancy and conflict rules beyond button examples",
    "Has not yet explained that selecting an ARIA role creates required state/property obligations",
    "Has not yet worked through Rule 3 examples",
    "Has not yet worked through explicit required-state examples",
    "Has not yet checked validity/completeness of required ARIA properties in markup",
    "Has not yet addressed role-dependent attribute support or redundancy rules",
    "Has not yet diagnosed missing required states/properties in markup",
    "Has not yet named Rule 3 explicitly",
    "Has not yet distinguished required role states from merely supported attributes",
    "Has not yet checked whether a given ARIA attribute is valid for a specific role",
    "Has not yet worked through redundancy and conflict rules",
    "Has not yet shown that some ARIA attributes are invalid for some roles",
    "Has not yet named or applied Rule 4 explicitly",
    "Has not yet worked with implicit native semantics or redundant ARIA",
    "Has not yet worked through redundancy with native implicit semantics",
    "Has not yet diagnosed multi-rule snippets systematically",
    "Has not yet justified choices across the full five-rule set"
  ],
  "next_focus": "Practice supported vs unsupported ARIA on more examples, then move into implicit native semantics and redundant ARIA.",
  "updated_at": "datetime.datetime(2026, 4, 8, 19, 57, 28, 209489, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

<details><summary>Learner Memory</summary>

```json
{
  "student_id": "test-conv-195112",
  "summary": "Learner handles contrastive markup well and can transfer from required-state checks to invalid attribute-role pairings.",
  "strengths": [
    "Readiness to engage",
    "Asks focused questions",
    "Uses concrete frontend examples",
    "Shows early conceptual uptake",
    "Reasones causally from examples",
    "Connects concepts to frontend implementation risk",
    "Comfortable using familiar controls like buttons",
    "Uses concrete examples",
    "Can name implicit role/name benefits",
    "Reasons from assistive-tech impact",
    "Applies ideas to familiar frontend markup",
    "States rules in practical language",
    "Reasons from implementation consequences",
    "Explains cause and effect clearly",
    "Uses assistive-tech perspective appropriately",
    "Transfers from button example to role override risk",
    "Concise causal explanations",
    "Good native-vs-ARIA contrast reasoning",
    "Transfer from prior rule to new ARIA concept",
    "Uses concrete control examples",
    "Explains risks in user-impact terms",
    "Causal reasoning",
    "Concrete transfer from examples",
    "Connects code choices to assistive-tech consequences",
    "Concrete causal reasoning",
    "Applies rule to markup examples",
    "Frames issues in user-impact terms",
    "Concrete markup reasoning",
    "Causal explanation about AT information needs",
    "Practical repair-oriented thinking",
    "Applies rules to concrete snippets",
    "Reasons by comparing better semantic alternatives",
    "Gives concise, technically relevant explanations"
  ],
  "support_needs": [
    "Clear framing before rule details",
    "Contrastive examples to separate native HTML from ARIA",
    "Keep building from practical native-vs-custom comparisons",
    "Help making implicit reasoning explicit as a named rule",
    "More examples beyond buttons to stabilize the concept",
    "Keep prompting for explicit rule naming",
    "Use contrastive markup to extend beyond familiar button examples",
    "Need explicit contrastive examples for new rules",
    "Need help moving from prefer-native reasoning to preserve-native reasoning",
    "Needs continued concrete examples to extend beyond native-vs-custom comparisons",
    "Needs help linking role choice to required ARIA follow-through",
    "Prompting to extend from rule idea to technical role obligations",
    "Worked examples to move from general principle to exact required ARIA states/properties",
    "Help distinguishing broad behavior matching from specific rule checks",
    "Practice spotting issues directly in markup",
    "Help tying intuitive explanation to formal rule names",
    "Keep examples concrete and role-specific",
    "Help separate required attributes from valid-but-optional ones",
    "Examples that contrast missing required ARIA with invalid ARIA",
    "Explicit naming of the rule after successful reasoning",
    "More examples spanning different rule types",
    "Help separating role support rules from redundancy/conflict rules"
  ],
  "tendencies": [
    "Starts from broad practical assumptions",
    "Seeks a big-picture mental model first",
    "Tests understanding by paraphrasing with examples",
    "Paraphrases understanding through practical tradeoffs",
    "Brings in implementation concerns like keyboard support",
    "Answers cautiously but accurately",
    "Builds understanding through practical frontend tradeoffs",
    "Uses button-vs-div examples to test understanding",
    "Frames understanding around practical reliability",
    "Answers strongest when prompted with a practical failure mode",
    "Frames understanding in terms of user expectations and screen reader output",
    "Repeats a solid answer verbatim when confident",
    "Paraphrases concepts through practical implementation examples",
    "Frames incorrect ARIA as misleading semantics",
    "Answers by paraphrasing the consequence in practical terms",
    "Uses familiar widgets to test understanding",
    "Answers directly and accurately when given a specific snippet",
    "Uses concise practical language rather than formal rule names",
    "Answers with implementation-ready examples",
    "Understands completeness of role/state relationships through practical consequences",
    "Responds well to yes/no plus why diagnostics",
    "Uses practical replacement suggestions to test understanding"
  ],
  "successful_strategies": [
    "Answer the current framing question directly",
    "Use concise contrasts between native HTML and ARIA",
    "Ask contrastive questions",
    "Use familiar controls like button vs div",
    "Use contrastive markup examples",
    "Ask why native is safer, not just which is preferred",
    "Ask what native elements provide for free",
    "Use direct native-vs-ARIA contrasts",
    "Ask for rule restatement in their own words",
    "Use concrete native-vs-custom comparisons",
    "Use contrastive examples with native elements",
    "Ask what breaks when semantics are changed",
    "Move from simple controls into concrete ARIA obligations",
    "Ask for one-sentence risk summaries",
    "Bridge from concrete misuse to the next rule",
    "Ask for one-step transfer to a familiar control",
    "Use concrete role examples like checkbox",
    "Follow principle with markup-based checking",
    "Short worked examples",
    "Concrete role-plus-state scenarios",
    "Ask for the practical consequence before naming the rule",
    "Snippet-based checks",
    "Ask whether AT has enough information",
    "Use familiar controls like checkbox",
    "Use short code snippets",
    "Ask for the smallest valid fix",
    "Contrast complete vs incomplete control semantics",
    "Contrast invalid pairing with an appropriate control pattern",
    "Use small markup snippets with one focused decision"
  ],
  "updated_at": "datetime.datetime(2026, 4, 8, 19, 57, 28, 211214, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

---

### Turn 13: exploration → exploration
**Tutor time**: 19.82s | **Student agent time**: 1.64s | **Turns on obj**: 12 → 13

**Student**:
> I should check that the state or property is actually supported by that role and that it matches the control’s real behavior. So basically: don’t slap on ARIA attributes just because they seem related.

**Tutor**:
> Exactly. That’s the rule: only use ARIA states and properties that the chosen role supports, and make sure they describe the control’s real behavior.

Now let’s shift to something that often gets missed: many native HTML elements already expose the role or state you’d otherwise try to add. What do you think is the danger of putting extra ARIA on a native element that already has the semantics built in?

<details><summary>WebSocket Events (6 non-token)</summary>

```json
[
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Analyzing your response...",
    "_ts": "2026-04-08T19:57:29.748691"
  },
  {
    "type": "stage",
    "stage": "composing",
    "detail": "Generating response (exploration)...",
    "_ts": "2026-04-08T19:57:47.095376"
  },
  {
    "type": "stream_start",
    "_ts": "2026-04-08T19:57:48.769872"
  },
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Updating learning state...",
    "_ts": "2026-04-08T19:57:49.515558"
  },
  {
    "type": "mastery_update",
    "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
    "objective_text": "Apply the five rules for using ARIA correctly",
    "new_level": "in_progress",
    "_ts": "2026-04-08T19:57:49.527550"
  },
  {
    "type": "stream_end",
    "metadata": {
      "session_id": "guided-test-195112",
      "stage": "exploration",
      "stage_advanced": false,
      "assessment": {}
    },
    "_ts": "2026-04-08T19:57:49.527582"
  }
]
```
</details>

**Lesson State**: active=`avoid_redundant_aria`
  `aria_supplemental_metadata` [done], `native_html_semantics_behavior` [done], `prefer_native_over_aria` [done], `preserve_native_semantics` [done], `roles_create_requirements` [done], `include_required_role_states` [done], `aria_is_role_dependent` [done], `use_supported_role_attributes` [done], `implicit_native_roles_states` [done], `avoid_redundant_aria` [wip], `native_aria_conflicts_harm` [todo], `choose_correct_aria_fix` [todo], `multiple_rule_violations` [todo], `justify_rule_based_choices` [todo]

**Mastery**: level=`in_progress` confidence=?

<details><summary>Objective Memory</summary>

```json
{
  "student_id": "test-conv-195112",
  "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
  "summary": "Student can now restate Rule 4 in practical terms: only use ARIA states/properties supported by the role and aligned with actual behavior.",
  "demonstrated_skills": [
    "Activates prior knowledge",
    "Asks a relevant framing question",
    "Contrasts native HTML with ARIA use",
    "Applies the supplemental-ARIA idea to a concrete control example",
    "Uses native-vs-custom comparison",
    "Gives causal justification for preferring native HTML",
    "Connects accessibility choice to implementation reliability",
    "Names built-in native semantics",
    "Connects native elements to assistive technology reliability",
    "Justifies Rule 1 with concrete markup reasoning",
    "Restates Rule 1 accurately",
    "Uses concrete markup comparison",
    "Connects native HTML to built-in meaning and behavior",
    "Explains risk of overriding native roles",
    "Connects semantics to assistive technology output",
    "Reasons about mismatched user expectations",
    "States prefer-native rule in own words",
    "Explains why changing a native role harms accessibility",
    "Uses causal reasoning about assistive tech and user expectations",
    "Causal explanation of role mismatch risk",
    "Transfers concept to checkbox example",
    "Connects role choice to required state exposure",
    "Explains causal impact of missing required ARIA state",
    "Connects role/state mismatch to user-facing accessibility failure",
    "Uses checkbox as a transfer example",
    "Identifies missing required ARIA state in a concrete snippet",
    "Explains user impact of incomplete role/state exposure",
    "Applies Rule 3 reasoning to checkbox example",
    "Applies required-state reasoning to role=\"checkbox\"",
    "Suggests a minimal valid ARIA fix",
    "Explains impact on assistive tech in causal terms",
    "Rejects invalid role/state combinations",
    "Explains why unsupported ARIA is not acceptable",
    "Offers a more suitable semantic alternative",
    "Restates rule from principle rather than memorized wording",
    "Connects attribute-role support to real control behavior",
    "Rejects arbitrary ARIA pairings"
  ],
  "active_gaps": [
    "Does not yet distinguish ARIA from correct native HTML",
    "May over-associate ARIA with adding labels and roles",
    "Has not yet articulated what built-in semantics/behavior native elements provide",
    "Has not yet worked through the explicit ARIA rules",
    "Has not yet explicitly stated Rule 1",
    "Has not yet named built-in semantics and behavior beyond keyboard support",
    "Has not yet applied the rule across multiple examples",
    "Has not yet worked through Rule 2 about not overriding native semantics",
    "Has not yet handled examples involving invalid or redundant ARIA beyond button/div comparison",
    "Has not yet explained why changing native semantics is risky",
    "Has not yet worked through Rule 2 examples",
    "Has not yet covered role-required states/properties or redundant ARIA",
    "Has not yet worked with ARIA roles that require specific states or properties",
    "Has not yet checked role-attribute compatibility",
    "Has not yet applied redundancy and conflict rules beyond button examples",
    "Has not yet explained that selecting an ARIA role creates required state/property obligations",
    "Has not yet worked through Rule 3 examples",
    "Has not yet worked through explicit required-state examples",
    "Has not yet checked validity/completeness of required ARIA properties in markup",
    "Has not yet addressed role-dependent attribute support or redundancy rules",
    "Has not yet diagnosed missing required states/properties in markup",
    "Has not yet named Rule 3 explicitly",
    "Has not yet distinguished required role states from merely supported attributes",
    "Has not yet checked whether a given ARIA attribute is valid for a specific role",
    "Has not yet worked through redundancy and conflict rules",
    "Has not yet shown that some ARIA attributes are invalid for some roles",
    "Has not yet named or applied Rule 4 explicitly",
    "Has not yet worked with implicit native semantics or redundant ARIA",
    "Has not yet worked through redundancy with native implicit semantics",
    "Has not yet diagnosed multi-rule snippets systematically",
    "Has not yet justified choices across the full five-rule set",
    "Has not yet worked through implicit native roles/states",
    "Has not yet addressed redundant ARIA on native elements",
    "Has not yet practiced multi-rule diagnosis"
  ],
  "next_focus": "Move from supported-role checks to native elements' implicit semantics and when ARIA becomes redundant.",
  "updated_at": "datetime.datetime(2026, 4, 8, 19, 57, 49, 522495, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

<details><summary>Learner Memory</summary>

```json
{
  "student_id": "test-conv-195112",
  "summary": "Learner gives compact rule paraphrases that preserve the causal idea, not just syntax.",
  "strengths": [
    "Readiness to engage",
    "Asks focused questions",
    "Uses concrete frontend examples",
    "Shows early conceptual uptake",
    "Reasones causally from examples",
    "Connects concepts to frontend implementation risk",
    "Comfortable using familiar controls like buttons",
    "Uses concrete examples",
    "Can name implicit role/name benefits",
    "Reasons from assistive-tech impact",
    "Applies ideas to familiar frontend markup",
    "States rules in practical language",
    "Reasons from implementation consequences",
    "Explains cause and effect clearly",
    "Uses assistive-tech perspective appropriately",
    "Transfers from button example to role override risk",
    "Concise causal explanations",
    "Good native-vs-ARIA contrast reasoning",
    "Transfer from prior rule to new ARIA concept",
    "Uses concrete control examples",
    "Explains risks in user-impact terms",
    "Causal reasoning",
    "Concrete transfer from examples",
    "Connects code choices to assistive-tech consequences",
    "Concrete causal reasoning",
    "Applies rule to markup examples",
    "Frames issues in user-impact terms",
    "Concrete markup reasoning",
    "Causal explanation about AT information needs",
    "Practical repair-oriented thinking",
    "Applies rules to concrete snippets",
    "Reasons by comparing better semantic alternatives",
    "Gives concise, technically relevant explanations",
    "Concise rule restatement",
    "Connects rules to intended behavior",
    "Handles contrastive ARIA examples well"
  ],
  "support_needs": [
    "Clear framing before rule details",
    "Contrastive examples to separate native HTML from ARIA",
    "Keep building from practical native-vs-custom comparisons",
    "Help making implicit reasoning explicit as a named rule",
    "More examples beyond buttons to stabilize the concept",
    "Keep prompting for explicit rule naming",
    "Use contrastive markup to extend beyond familiar button examples",
    "Need explicit contrastive examples for new rules",
    "Need help moving from prefer-native reasoning to preserve-native reasoning",
    "Needs continued concrete examples to extend beyond native-vs-custom comparisons",
    "Needs help linking role choice to required ARIA follow-through",
    "Prompting to extend from rule idea to technical role obligations",
    "Worked examples to move from general principle to exact required ARIA states/properties",
    "Help distinguishing broad behavior matching from specific rule checks",
    "Practice spotting issues directly in markup",
    "Help tying intuitive explanation to formal rule names",
    "Keep examples concrete and role-specific",
    "Help separate required attributes from valid-but-optional ones",
    "Examples that contrast missing required ARIA with invalid ARIA",
    "Explicit naming of the rule after successful reasoning",
    "More examples spanning different rule types",
    "Help separating role support rules from redundancy/conflict rules",
    "More examples that pivot from ARIA validation to native HTML semantics",
    "Help naming implicit native semantics explicitly"
  ],
  "tendencies": [
    "Starts from broad practical assumptions",
    "Seeks a big-picture mental model first",
    "Tests understanding by paraphrasing with examples",
    "Paraphrases understanding through practical tradeoffs",
    "Brings in implementation concerns like keyboard support",
    "Answers cautiously but accurately",
    "Builds understanding through practical frontend tradeoffs",
    "Uses button-vs-div examples to test understanding",
    "Frames understanding around practical reliability",
    "Answers strongest when prompted with a practical failure mode",
    "Frames understanding in terms of user expectations and screen reader output",
    "Repeats a solid answer verbatim when confident",
    "Paraphrases concepts through practical implementation examples",
    "Frames incorrect ARIA as misleading semantics",
    "Answers by paraphrasing the consequence in practical terms",
    "Uses familiar widgets to test understanding",
    "Answers directly and accurately when given a specific snippet",
    "Uses concise practical language rather than formal rule names",
    "Answers with implementation-ready examples",
    "Understands completeness of role/state relationships through practical consequences",
    "Responds well to yes/no plus why diagnostics",
    "Uses practical replacement suggestions to test understanding",
    "Summarizes with practical heuristics",
    "Reasons from implementation intent"
  ],
  "successful_strategies": [
    "Answer the current framing question directly",
    "Use concise contrasts between native HTML and ARIA",
    "Ask contrastive questions",
    "Use familiar controls like button vs div",
    "Use contrastive markup examples",
    "Ask why native is safer, not just which is preferred",
    "Ask what native elements provide for free",
    "Use direct native-vs-ARIA contrasts",
    "Ask for rule restatement in their own words",
    "Use concrete native-vs-custom comparisons",
    "Use contrastive examples with native elements",
    "Ask what breaks when semantics are changed",
    "Move from simple controls into concrete ARIA obligations",
    "Ask for one-sentence risk summaries",
    "Bridge from concrete misuse to the next rule",
    "Ask for one-step transfer to a familiar control",
    "Use concrete role examples like checkbox",
    "Follow principle with markup-based checking",
    "Short worked examples",
    "Concrete role-plus-state scenarios",
    "Ask for the practical consequence before naming the rule",
    "Snippet-based checks",
    "Ask whether AT has enough information",
    "Use familiar controls like checkbox",
    "Use short code snippets",
    "Ask for the smallest valid fix",
    "Contrast complete vs incomplete control semantics",
    "Contrast invalid pairing with an appropriate control pattern",
    "Use small markup snippets with one focused decision",
    "Ask for one-sentence rule restatements",
    "Use paired examples of valid vs invalid semantics"
  ],
  "updated_at": "datetime.datetime(2026, 4, 8, 19, 57, 49, 523944, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

---

### Turn 14: exploration → exploration
**Tutor time**: 18.59s | **Student agent time**: -s | **Turns on obj**: 13 → 14

**Student**:
> You can end up duplicating or even conflicting with the native semantics, which can confuse screen readers. So like, instead of helping, the extra ARIA might override the built-in info or make it less reliable.

**Tutor**:
> Yes — that’s the danger. Native elements already expose information to assistive technologies, and adding redundant or conflicting ARIA can muddy that signal rather than improve it.

So the next rule is: if the HTML already provides the meaning or state, don’t add ARIA that just repeats it. For example, a real `<button>` already has button semantics, so adding `role="button"` to it is unnecessary.

What would you do with `<button role="button">Save</button>`: keep the ARIA or remove it?

<details><summary>WebSocket Events (6 non-token)</summary>

```json
[
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Analyzing your response...",
    "_ts": "2026-04-08T19:57:51.210789"
  },
  {
    "type": "stage",
    "stage": "composing",
    "detail": "Generating response (exploration)...",
    "_ts": "2026-04-08T19:58:07.065292"
  },
  {
    "type": "stream_start",
    "_ts": "2026-04-08T19:58:08.771094"
  },
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Updating learning state...",
    "_ts": "2026-04-08T19:58:09.741955"
  },
  {
    "type": "mastery_update",
    "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
    "objective_text": "Apply the five rules for using ARIA correctly",
    "new_level": "in_progress",
    "_ts": "2026-04-08T19:58:09.762618"
  },
  {
    "type": "stream_end",
    "metadata": {
      "session_id": "guided-test-195112",
      "stage": "exploration",
      "stage_advanced": false,
      "assessment": {}
    },
    "_ts": "2026-04-08T19:58:09.762675"
  }
]
```
</details>

**Lesson State**: active=`avoid_redundant_aria`
  `aria_supplemental_metadata` [done], `native_html_semantics_behavior` [done], `prefer_native_over_aria` [done], `preserve_native_semantics` [done], `roles_create_requirements` [done], `include_required_role_states` [done], `aria_is_role_dependent` [done], `use_supported_role_attributes` [done], `implicit_native_roles_states` [done], `avoid_redundant_aria` [wip], `native_aria_conflicts_harm` [todo], `choose_correct_aria_fix` [todo], `multiple_rule_violations` [todo], `justify_rule_based_choices` [todo]

**Mastery**: level=`in_progress` confidence=?

<details><summary>Objective Memory</summary>

```json
{
  "student_id": "test-conv-195112",
  "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
  "summary": "Student now explains that native elements already expose semantics and that extra ARIA can be redundant or conflicting.",
  "demonstrated_skills": [
    "Activates prior knowledge",
    "Asks a relevant framing question",
    "Contrasts native HTML with ARIA use",
    "Applies the supplemental-ARIA idea to a concrete control example",
    "Uses native-vs-custom comparison",
    "Gives causal justification for preferring native HTML",
    "Connects accessibility choice to implementation reliability",
    "Names built-in native semantics",
    "Connects native elements to assistive technology reliability",
    "Justifies Rule 1 with concrete markup reasoning",
    "Restates Rule 1 accurately",
    "Uses concrete markup comparison",
    "Connects native HTML to built-in meaning and behavior",
    "Explains risk of overriding native roles",
    "Connects semantics to assistive technology output",
    "Reasons about mismatched user expectations",
    "States prefer-native rule in own words",
    "Explains why changing a native role harms accessibility",
    "Uses causal reasoning about assistive tech and user expectations",
    "Causal explanation of role mismatch risk",
    "Transfers concept to checkbox example",
    "Connects role choice to required state exposure",
    "Explains causal impact of missing required ARIA state",
    "Connects role/state mismatch to user-facing accessibility failure",
    "Uses checkbox as a transfer example",
    "Identifies missing required ARIA state in a concrete snippet",
    "Explains user impact of incomplete role/state exposure",
    "Applies Rule 3 reasoning to checkbox example",
    "Applies required-state reasoning to role=\"checkbox\"",
    "Suggests a minimal valid ARIA fix",
    "Explains impact on assistive tech in causal terms",
    "Rejects invalid role/state combinations",
    "Explains why unsupported ARIA is not acceptable",
    "Offers a more suitable semantic alternative",
    "Restates rule from principle rather than memorized wording",
    "Connects attribute-role support to real control behavior",
    "Rejects arbitrary ARIA pairings",
    "Rejects unsupported role-state pairings",
    "Restates Rule 4 accurately",
    "Reasons causally about native semantics versus added ARIA",
    "Anticipates AT confusion from redundant or conflicting ARIA"
  ],
  "active_gaps": [
    "Does not yet distinguish ARIA from correct native HTML",
    "May over-associate ARIA with adding labels and roles",
    "Has not yet articulated what built-in semantics/behavior native elements provide",
    "Has not yet worked through the explicit ARIA rules",
    "Has not yet explicitly stated Rule 1",
    "Has not yet named built-in semantics and behavior beyond keyboard support",
    "Has not yet applied the rule across multiple examples",
    "Has not yet worked through Rule 2 about not overriding native semantics",
    "Has not yet handled examples involving invalid or redundant ARIA beyond button/div comparison",
    "Has not yet explained why changing native semantics is risky",
    "Has not yet worked through Rule 2 examples",
    "Has not yet covered role-required states/properties or redundant ARIA",
    "Has not yet worked with ARIA roles that require specific states or properties",
    "Has not yet checked role-attribute compatibility",
    "Has not yet applied redundancy and conflict rules beyond button examples",
    "Has not yet explained that selecting an ARIA role creates required state/property obligations",
    "Has not yet worked through Rule 3 examples",
    "Has not yet worked through explicit required-state examples",
    "Has not yet checked validity/completeness of required ARIA properties in markup",
    "Has not yet addressed role-dependent attribute support or redundancy rules",
    "Has not yet diagnosed missing required states/properties in markup",
    "Has not yet named Rule 3 explicitly",
    "Has not yet distinguished required role states from merely supported attributes",
    "Has not yet checked whether a given ARIA attribute is valid for a specific role",
    "Has not yet worked through redundancy and conflict rules",
    "Has not yet shown that some ARIA attributes are invalid for some roles",
    "Has not yet named or applied Rule 4 explicitly",
    "Has not yet worked with implicit native semantics or redundant ARIA",
    "Has not yet worked through redundancy with native implicit semantics",
    "Has not yet diagnosed multi-rule snippets systematically",
    "Has not yet justified choices across the full five-rule set",
    "Has not yet worked through implicit native roles/states",
    "Has not yet addressed redundant ARIA on native elements",
    "Has not yet practiced multi-rule diagnosis",
    "Has not yet applied Rule 5 to concrete native-element examples",
    "Has not yet distinguished redundant ARIA from legitimate naming/labeling cases",
    "Has not yet diagnosed multi-rule snippets"
  ],
  "next_focus": "Use concrete native HTML examples to identify redundant ARIA and justify removal.",
  "updated_at": "datetime.datetime(2026, 4, 8, 19, 58, 9, 754183, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

<details><summary>Learner Memory</summary>

```json
{
  "student_id": "test-conv-195112",
  "summary": "Learner gives compact causal explanations and transfers rules to nearby cases without much prompting.",
  "strengths": [
    "Readiness to engage",
    "Asks focused questions",
    "Uses concrete frontend examples",
    "Shows early conceptual uptake",
    "Reasones causally from examples",
    "Connects concepts to frontend implementation risk",
    "Comfortable using familiar controls like buttons",
    "Uses concrete examples",
    "Can name implicit role/name benefits",
    "Reasons from assistive-tech impact",
    "Applies ideas to familiar frontend markup",
    "States rules in practical language",
    "Reasons from implementation consequences",
    "Explains cause and effect clearly",
    "Uses assistive-tech perspective appropriately",
    "Transfers from button example to role override risk",
    "Concise causal explanations",
    "Good native-vs-ARIA contrast reasoning",
    "Transfer from prior rule to new ARIA concept",
    "Uses concrete control examples",
    "Explains risks in user-impact terms",
    "Causal reasoning",
    "Concrete transfer from examples",
    "Connects code choices to assistive-tech consequences",
    "Concrete causal reasoning",
    "Applies rule to markup examples",
    "Frames issues in user-impact terms",
    "Concrete markup reasoning",
    "Causal explanation about AT information needs",
    "Practical repair-oriented thinking",
    "Applies rules to concrete snippets",
    "Reasons by comparing better semantic alternatives",
    "Gives concise, technically relevant explanations",
    "Concise rule restatement",
    "Connects rules to intended behavior",
    "Handles contrastive ARIA examples well",
    "Concise paraphrasing",
    "Good native-vs-ARIA comparisons"
  ],
  "support_needs": [
    "Clear framing before rule details",
    "Contrastive examples to separate native HTML from ARIA",
    "Keep building from practical native-vs-custom comparisons",
    "Help making implicit reasoning explicit as a named rule",
    "More examples beyond buttons to stabilize the concept",
    "Keep prompting for explicit rule naming",
    "Use contrastive markup to extend beyond familiar button examples",
    "Need explicit contrastive examples for new rules",
    "Need help moving from prefer-native reasoning to preserve-native reasoning",
    "Needs continued concrete examples to extend beyond native-vs-custom comparisons",
    "Needs help linking role choice to required ARIA follow-through",
    "Prompting to extend from rule idea to technical role obligations",
    "Worked examples to move from general principle to exact required ARIA states/properties",
    "Help distinguishing broad behavior matching from specific rule checks",
    "Practice spotting issues directly in markup",
    "Help tying intuitive explanation to formal rule names",
    "Keep examples concrete and role-specific",
    "Help separate required attributes from valid-but-optional ones",
    "Examples that contrast missing required ARIA with invalid ARIA",
    "Explicit naming of the rule after successful reasoning",
    "More examples spanning different rule types",
    "Help separating role support rules from redundancy/conflict rules",
    "More examples that pivot from ARIA validation to native HTML semantics",
    "Help naming implicit native semantics explicitly",
    "Concrete example checks to stabilize rule boundaries",
    "Explicit contrast between redundant ARIA and valid labeling uses"
  ],
  "tendencies": [
    "Starts from broad practical assumptions",
    "Seeks a big-picture mental model first",
    "Tests understanding by paraphrasing with examples",
    "Paraphrases understanding through practical tradeoffs",
    "Brings in implementation concerns like keyboard support",
    "Answers cautiously but accurately",
    "Builds understanding through practical frontend tradeoffs",
    "Uses button-vs-div examples to test understanding",
    "Frames understanding around practical reliability",
    "Answers strongest when prompted with a practical failure mode",
    "Frames understanding in terms of user expectations and screen reader output",
    "Repeats a solid answer verbatim when confident",
    "Paraphrases concepts through practical implementation examples",
    "Frames incorrect ARIA as misleading semantics",
    "Answers by paraphrasing the consequence in practical terms",
    "Uses familiar widgets to test understanding",
    "Answers directly and accurately when given a specific snippet",
    "Uses concise practical language rather than formal rule names",
    "Answers with implementation-ready examples",
    "Understands completeness of role/state relationships through practical consequences",
    "Responds well to yes/no plus why diagnostics",
    "Uses practical replacement suggestions to test understanding",
    "Summarizes with practical heuristics",
    "Reasons from implementation intent",
    "Answers with practical impact on screen readers and reliability",
    "Generalizes rules into actionable heuristics"
  ],
  "successful_strategies": [
    "Answer the current framing question directly",
    "Use concise contrasts between native HTML and ARIA",
    "Ask contrastive questions",
    "Use familiar controls like button vs div",
    "Use contrastive markup examples",
    "Ask why native is safer, not just which is preferred",
    "Ask what native elements provide for free",
    "Use direct native-vs-ARIA contrasts",
    "Ask for rule restatement in their own words",
    "Use concrete native-vs-custom comparisons",
    "Use contrastive examples with native elements",
    "Ask what breaks when semantics are changed",
    "Move from simple controls into concrete ARIA obligations",
    "Ask for one-sentence risk summaries",
    "Bridge from concrete misuse to the next rule",
    "Ask for one-step transfer to a familiar control",
    "Use concrete role examples like checkbox",
    "Follow principle with markup-based checking",
    "Short worked examples",
    "Concrete role-plus-state scenarios",
    "Ask for the practical consequence before naming the rule",
    "Snippet-based checks",
    "Ask whether AT has enough information",
    "Use familiar controls like checkbox",
    "Use short code snippets",
    "Ask for the smallest valid fix",
    "Contrast complete vs incomplete control semantics",
    "Contrast invalid pairing with an appropriate control pattern",
    "Use small markup snippets with one focused decision",
    "Ask for one-sentence rule restatements",
    "Use paired examples of valid vs invalid semantics",
    "Ask for the danger or consequence of a markup choice",
    "Use native element examples with optional ARIA additions",
    "Prompt for brief rule justification"
  ],
  "updated_at": "datetime.datetime(2026, 4, 8, 19, 58, 9, 757876, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

---

## Final State

### Session State
```json
{
  "session_id": "guided-test-195112",
  "student_id": "test-conv-195112",
  "active_objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
  "current_stage": "exploration",
  "turns_on_objective": 14,
  "readiness_score": null,
  "mini_assessment_progress": {},
  "final_assessment_progress": {},
  "stage_summary": "Student correctly applies the framing idea to a concrete example and contrasts native HTML with ARIA.",
  "started_at": "datetime.datetime(2026, 4, 8, 19, 51, 12, 417193, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))",
  "runtime_cache": {
    "lesson_state": {
      "concepts": [
        {
          "id": "aria_supplemental_metadata",
          "label": "ARIA is supplemental accessibility metadata, not a replacement for correct HTML",
          "status": "covered"
        },
        {
          "id": "native_html_semantics_behavior",
          "label": "Native HTML elements already carry built-in semantics and behavior",
          "status": "covered"
        },
        {
          "id": "prefer_native_over_aria",
          "label": "If native HTML can provide the needed semantics or behavior, prefer it over ARIA",
          "status": "covered"
        },
        {
          "id": "preserve_native_semantics",
          "label": "Do not change native semantics unless there is a very strong, valid reason",
          "status": "covered"
        },
        {
          "id": "roles_create_requirements",
          "label": "Some ARIA roles require particular states or properties",
          "status": "covered"
        },
        {
          "id": "include_required_role_states",
          "label": "All required ARIA states and properties for a chosen role must be present and valid",
          "status": "covered"
        },
        {
          "id": "aria_is_role_dependent",
          "label": "ARIA attributes are role-dependent and not every attribute is valid on every role",
          "status": "covered"
        },
        {
          "id": "use_supported_role_attributes",
          "label": "Use only ARIA states and properties supported for the role in question",
          "status": "covered"
        },
        {
          "id": "implicit_native_roles_states",
          "label": "Some HTML elements already expose implicit roles and states",
          "status": "covered"
        },
        {
          "id": "avoid_redundant_aria",
          "label": "Do not add redundant ARIA that repeats implicit native semantics",
          "status": "in_progress"
        },
        {
          "id": "native_aria_conflicts_harm",
          "label": "Conflicts between native semantics and ARIA can harm accessibility",
          "status": "not_covered"
        },
        {
          "id": "choose_correct_aria_fix",
          "label": "Apply the rules by removing ARIA, replacing custom markup with native HTML, adding missing required ARIA, or revising invalid combinations",
          "status": "not_covered"
        },
        {
          "id": "multiple_rule_violations",
          "label": "A single snippet may violate more than one rule at once",
          "status": "not_covered"
        },
        {
          "id": "justify_rule_based_choices",
          "label": "Correct application requires identifying which rule applies and why",
          "status": "not_covered"
        }
      ],
      "pending_check": "Can the student identify when ARIA on a native element is redundant versus when it serves a real purpose?",
      "active_concept": "avoid_redundant_aria",
      "teaching_order": [
        "aria_supplemental_metadata",
        "native_html_semantics_behavior",
        "prefer_native_over_aria",
        "preserve_native_semantics",
        "roles_create_requirements",
        "include_required_role_states",
        "aria_is_role_dependent",
        "use_supported_role_attributes",
        "implicit_native_roles_states",
        "avoid_redundant_aria",
        "native_aria_conflicts_harm",
        "choose_correct_aria_fix",
        "multiple_rule_violations",
        "justify_rule_based_choices"
      ],
      "bridge_back_target": "implicit_native_roles_states"
    },
    "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
    "retrieved_at": "2026-04-08T19:53:25.540308",
    "teaching_plan": "## 1. objective_text\nApply the five rules for using ARIA correctly\n\n## 2. plain_language_goal\nUse the five main ARIA rules to decide when ARIA should or should not be added, and apply those rules correctly in realistic markup situations.\n\n## 3. mastery_definition\nA student has mastered this objective when they can:\n\n- state or recognize the purpose of the five ARIA rules in practical terms\n- inspect a small HTML example and identify whether ARIA is needed or unnecessary\n- choose the correct action based on the rules:\n  - use native HTML instead of ARIA when appropriate\n  - avoid changing native semantics incorrectly\n  - ensure required states/properties are present when a role is used\n  - use only supported ARIA attributes for a given role\n  - avoid redundant or conflicting ARIA that duplicates implicit semantics\n- explain their choice by referencing the relevant rule\n- correct at least one flawed example containing multiple ARIA misuse patterns\n\n## 4. objective_type\n- conceptual understanding\n- decision-making\n- application\n- debugging/evaluation\n\n## 5. prerequisite_knowledge\n\n### essential prerequisites\n- Basic understanding of HTML elements and attributes\n- Basic distinction between native HTML semantics and presentational styling\n- Recognition that assistive technologies rely on semantic information\n- Familiarity with common semantic elements such as button, link, input, heading, nav, main, and form controls\n\n### helpful but nonessential prerequisites\n- Basic idea of what ARIA is and that it can add accessibility information\n- Awareness of roles, states, and properties at a high level\n- Experience reading simple code snippets\n- Basic awareness of screen readers or accessibility trees\n\n## 6. prerequisite_gap_policy\nIf the learner lacks essential prerequisites, the tutor should pause this objective and provide a very short prerequisite bridge before continuing. That bridge should cover only the minimum needed:\n\n- what native HTML semantics are\n- why semantic elements matter for assistive technologies\n- the difference between an element’s built-in meaning and added ARIA\n\nThe tutor should not proceed into the five rules until the learner can correctly identify at least a few native semantic elements and explain why “use the right HTML element first” matters.\n\n## 7. concept_decomposition\n1. ARIA is supplemental accessibility metadata, not a replacement for correct HTML.\n2. Native HTML elements already carry built-in semantics and behavior.\n3. Rule 1: If a native HTML element or attribute can provide the needed semantics/behavior, prefer it over ARIA.\n4. Rule 2: Do not change native semantics unless there is a very strong, valid reason.\n5. Role usage can create obligations: some roles require particular states/properties.\n6. Rule 3: All required ARIA states/properties for a chosen role must be present and valid.\n7. ARIA attributes are role-dependent; not every attribute is valid on every role.\n8. Rule 4: Use only ARIA states/properties supported for the role in question.\n9. Some HTML elements already expose implicit roles/states.\n10. Rule 5: Do not add redundant ARIA that repeats implicit native semantics.\n11. Conflicts between native semantics and ARIA can harm accessibility rather than help it.\n12. Applying the five rules often means deciding among: remove ARIA, replace custom markup with native HTML, add missing required ARIA, or revise invalid combinations.\n13. A single snippet may violate more than one rule at once.\n14. Correct application requires justification: identifying which rule applies and why.\n\n## 8. dependency_order\n\n### Ordered sequence with dependencies\n1. **ARIA is supplemental accessibility metadata, not a replacement for correct HTML.**\n   - No dependency\n2. **Native HTML elements already carry built-in semantics and behavior.**\n   - Depends on 1\n3. **Rule 1: If a native HTML element or attribute can provide the needed semantics/behavior, prefer it over ARIA.**\n   - Depends on 1, 2\n4. **Rule 2: Do not change native semantics unless there is a very strong, valid reason.**\n   - Depends on 2, 3\n5. **Role usage can create obligations: some roles require particular states/properties.**\n   - Depends on 1\n6. **Rule 3: All required ARIA states/properties for a chosen role must be present and valid.**\n   - Depends on 5\n7. **ARIA attributes are role-dependent; not every attribute is valid on every role.**\n   - Depends on 5\n8. **Rule 4: Use only ARIA states/properties supported for the role in question.**\n   - Depends on 7\n9. **Some HTML elements already expose implicit roles/states.**\n   - Depends on 2\n10. **Rule 5: Do not add redundant ARIA that repeats implicit native semantics.**\n   - Depends on 9\n11. **Conflicts between native semantics and ARIA can harm accessibility rather than help it.**\n   - Depends on 4, 8, 10\n12. **Applying the five rules often means deciding among: remove ARIA, replace custom markup with native HTML, add missing required ARIA, or revise invalid combinations.**\n   - Depends on 3, 4, 6, 8, 10, 11\n13. **A single snippet may violate more than one rule at once.**\n   - Depends on 12\n14. **Correct application requires justification: identifying which rule applies and why.**\n   - Depends on 12, 13\n\n### Why this sequence is instructionally sound\n- It starts with the foundational idea that ARIA is secondary to HTML, preventing later rule memorization without conceptual grounding.\n- It introduces native semantics before rules that depend on recognizing proper HTML usage.\n- It teaches the “prefer native” and “don’t override native” rules early because they are the highest-frequency and lowest-complexity decisions.\n- It then moves into role-specific constraints, which are more technical and require understanding that ARIA choices create obligations.\n- Redundancy is taught after implicit semantics, since students must first know what is already provided.\n- Multi-rule diagnosis and justification are saved for the end to avoid overload and to support transfer.\n\n## 9. likely_misconceptions\n- “ARIA always improves accessibility.”\n- “More ARIA is better.”\n- “ARIA can fix poor HTML automatically.”\n- “role='button' is equivalent to using a real button in all important ways.”\n- “If code passes visual inspection, the ARIA is probably fine.”\n- “Any ARIA attribute can be added to any element if it seems useful.”\n- “If a role is valid, its required states/properties are optional.”\n- “Adding explicit role='button' to a button is helpful.”\n- “Changing a native element’s role is harmless if the UI looks right.”\n- “ARIA rules are mainly about syntax, not user experience.”\n- “If custom widgets use ARIA, they do not need complete semantic/state support.”\n- Confusing native HTML attributes with ARIA attributes\n- Confusing redundant ARIA with descriptive labeling\n- Believing every exception or advanced pattern should be introduced in this objective\n\n## 10. explanation_vs_question_strategy\n\n### 1. ARIA is supplemental accessibility metadata, not a replacement for correct HTML.\n- **Begin with:** brief explanation\n- **Why:** This is a framing concept that students often do not already hold accurately; a concise setup prevents confusion.\n\n### 2. Native HTML elements already carry built-in semantics and behavior.\n- **Begin with:** guided questioning\n- **Why:** Many learners can already name common elements and their purpose; questioning activates prior knowledge.\n\n### 3. Rule 1: If a native HTML element or attribute can provide the needed semantics/behavior, prefer it over ARIA.\n- **Begin with:** contrastive example\n- **Why:** Comparing native HTML to ARIA-added custom markup makes the rule concrete and memorable.\n\n### 4. Rule 2: Do not change native semantics unless there is a very strong, valid reason.\n- **Begin with:** contrastive example\n- **Why:** This rule is easiest to grasp when students see a native element with correct meaning versus one whose role is overridden.\n\n### 5. Role usage can create obligations: some roles require particular states/properties.\n- **Begin with:** brief explanation\n- **Why:** This is a structural rule about ARIA mechanics that learners may not infer on their own.\n\n### 6. Rule 3: All required ARIA states/properties for a chosen role must be present and valid.\n- **Begin with:** worked example\n- **Why:** Students need to see a role chosen and then checked for what must accompany it.\n\n### 7. ARIA attributes are role-dependent; not every attribute is valid on every role.\n- **Begin with:** diagnostic question\n- **Why:** This exposes the common misconception that ARIA attributes are freely mix-and-match.\n\n### 8. Rule 4: Use only ARIA states/properties supported for the role in question.\n- **Begin with:** worked example\n- **Why:** Learners benefit from seeing attribute-role compatibility checked in context.\n\n### 9. Some HTML elements already expose implicit roles/states.\n- **Begin with:** guided questioning\n- **Why:** Students may already know examples like buttons, headings, and links; eliciting that knowledge reduces lecture load.\n\n### 10. Rule 5: Do not add redundant ARIA that repeats implicit native semantics.\n- **Begin with:** contrastive example\n- **Why:** Redundancy is easiest to understand by comparing “native only” against “native plus unnecessary ARIA.”\n\n### 11. Conflicts between native semantics and ARIA can harm accessibility rather than help it.\n- **Begin with:** guided questioning\n- **Why:** Socratic prompts can lead learners to reason about conflicting signals rather than passively accept the claim.\n\n### 12. Applying the five rules often means deciding among: remove ARIA, replace custom markup with native HTML, add missing required ARIA, or revise invalid combinations.\n- **Begin with:** worked example\n- **Why:** This is practical synthesis and requires modeled decision-making.\n\n### 13. A single snippet may violate more than one rule at once.\n- **Begin with:** diagnostic question\n- **Why:** Students often stop after spotting one issue; diagnosis reveals whether they can continue checking systematically.\n\n### 14. Correct application requires justification: identifying which rule applies and why.\n- **Begin with:** guided questioning\n- **Why:** The goal is not just correction but reasoned explanation tied to rules.\n\n## 11. socratic_question_goals\n\n### Stage 1: foundational framing\n- diagnose whether the learner sees ARIA as replacement vs supplement\n- surface prior knowledge of semantic HTML\n- confirm understanding that native elements carry meaning\n\n### Stage 2: native-first decision making\n- force comparison between native and ARIA-based solutions\n- test whether the learner can justify choosing native HTML\n- reveal the misconception that custom markup plus ARIA is equivalent to native controls\n\n### Stage 3: preserving native semantics\n- check causal understanding of why overriding native roles is risky\n- reveal overconfidence in changing roles on semantic elements\n- test ability to spot conflicts between built-in meaning and assigned role\n\n### Stage 4: role obligations\n- diagnose whether the learner understands that choosing a role creates requirements\n- test whether they notice missing required states/properties\n- require justification for why a snippet is incomplete, not merely “uses ARIA”\n\n### Stage 5: supported vs unsupported attributes\n- force comparison between valid and invalid role/attribute combinations\n- reveal the misconception that all ARIA attributes are universally usable\n- test lookup-style reasoning without requiring rote memorization\n\n### Stage 6: redundancy and implicit semantics\n- test whether the learner can identify what semantics are already present natively\n- reveal the misconception that extra ARIA is harmless\n- justify removal of redundant role/state assignments\n\n### Stage 7: synthesis\n- test transfer across mixed examples\n- require the learner to decide the appropriate fix, not just name a rule\n- check whether the learner can identify multiple simultaneous violations\n- require rule-based justification for each correction\n\n## 12. example_requirements\n\n### simplest introductory example\n- A very small comparison where a native semantic element solves the need directly, contrasted with a nonsemantic element using ARIA to imitate it.\n- Purpose: support Rule 1 with minimal complexity.\n\n### at least one contrastive example\n- A pair showing:\n  - a native element used correctly without extra ARIA\n  - the same element with redundant or conflicting ARIA added\n- Purpose: contrast “good because native” vs “worse because unnecessary/conflicting.”\n\n### at least one borderline or tricky case\n- A snippet where:\n  - ARIA is not entirely wrong, but incomplete because required states/properties are missing\n  - or a role is assigned correctly in principle, but an unsupported attribute is added\n- Purpose: prevent shallow “ARIA bad / no ARIA good” overgeneralization.\n\n### at least one transfer scenario\n- A mixed snippet containing multiple issues, such as:\n  - custom element with ARIA where native HTML should be used\n  - overridden native semantics\n  - missing required property\n  - redundant role\n- Purpose: assess integrated application across rules.\n\n### additional example guidance\n- Keep examples short enough for line-by-line inspection.\n- Prefer realistic UI fragments over abstract isolated tags.\n- Do not require advanced widget architecture beyond what is necessary to apply the rules.\n\n## 13. retrieval_requirements\n\n### must-retrieve\n- The authoritative formulation of the five rules for using ARIA correctly\n  - Needed so the lesson aligns exactly with accepted guidance.\n- Accurate examples of native elements with implicit semantics\n  - Needed for Rules 1, 2, and 5.\n- Reliable examples of roles that require specific ARIA states/properties\n  - Needed for Rule 3.\n- Reliable role/state/property compatibility information\n  - Needed for Rule 4.\n- Examples of redundant ARIA on native elements\n  - Needed for Rule 5.\n- At least one example where ARIA conflicts with native semantics\n  - Needed to demonstrate harm from misuse.\n\n### optional-supporting\n- Accessibility tree or assistive technology interpretation examples\n  - Helpful to motivate why misuse matters.\n- Linting or validator output examples\n  - Helpful for debugging/evaluation framing, but not required.\n- Brief references to common authoring mistakes in real codebases\n  - Helpful for authenticity and transfer.\n- A compact rule summary table\n  - Helpful for review after reasoning practice.\n\n## 14. assessment_evidence\n\n### quick understanding checks\n- Given a simple snippet, the learner identifies whether ARIA is needed.\n- Given a native element with added ARIA, the learner says whether the ARIA is redundant, harmful, or necessary.\n- Given a role, the learner recognizes that required states/properties may need checking.\n\n### application task\n- Provide a short code sample with 3–5 ARIA-related decisions.\n- Ask the learner to mark each as:\n  - keep\n  - remove\n  - replace with native HTML\n  - add required ARIA\n  - revise invalid ARIA\n- Require a rule-based justification for each decision.\n\n### transfer task\n- Give a different UI pattern than the examples used in practice.\n- Ask the learner to apply the same rules without cueing which rule to use.\n- Evidence of mastery: the learner independently selects the applicable rule(s) and proposes an appropriate correction.\n\n### misconception check\n- Include at least one item designed to trigger each common misconception:\n  - a native control with redundant role\n  - a native element with conflicting role\n  - a role missing required state/property\n  - an unsupported state/property on a role\n  - a custom element that should have been native HTML\n- Mastery evidence: the learner does not merely flag “bad ARIA,” but identifies the specific rule being violated.\n\n## 15. adaptation_notes\n\n### beginner\n- Spend more time on prerequisite bridging around semantic HTML.\n- Use fewer technical terms at first; introduce role/state/property only when needed.\n- Limit examples to common elements and small snippets.\n- Emphasize Rule 1 and Rule 5 early, since they are accessible entry points.\n\n### intermediate learner\n- Move quickly through semantic HTML review.\n- Use more mixed examples where multiple rules interact.\n- Ask for explicit justification tied to the numbered rules.\n- Include at least one case involving required states/properties and one involving unsupported attributes.\n\n### advanced learner\n- Minimize introductory explanation and begin with diagnosis through flawed examples.\n- Emphasize nuanced distinctions:\n  - valid in principle vs valid in context\n  - technically present vs semantically complete\n  - unnecessary vs harmful\n- Use compact synthesis tasks where the learner audits snippets and explains prioritization of fixes.\n\n## 16. boundaries_and_non_goals\nThis lesson should NOT attempt to teach:\n\n- full ARIA specification details\n- exhaustive memorization of all roles, states, and properties\n- advanced custom widget authoring patterns in depth\n- keyboard interaction implementation for custom widgets except where minimally needed to explain why native HTML is preferable\n- accessible naming and labeling in general, unless directly needed for a retrieved example\n- screen reader-specific behavior across different products\n- full accessibility tree mechanics\n- broad WCAG conformance beyond the narrow context of applying the five ARIA rules\n\n## 17. concise_plan_summary\n- Start by establishing that ARIA supplements HTML rather than replacing it.\n- Activate prior knowledge of native semantics before introducing the rules.\n- Teach the “prefer native HTML” and “don’t override native semantics” rules first, because they prevent the most common misuse.\n- Then introduce the idea that choosing ARIA roles creates obligations and compatibility constraints.\n- Teach redundancy only after learners understand implicit native semantics.\n- Use short contrastive and worked examples rather than abstract rule recitation.\n- End with mixed-code diagnosis tasks that require both correction and rule-based justification.\n- Keep scope tight: apply the five rules accurately without expanding into full ARIA implementation theory.",
    "objective_text": "Apply the five rules for using ARIA correctly",
    "retrieval_bundle": {
      "version": 1,
      "coverage": {
        "hit_chars": 8946,
        "hit_count": 6,
        "budget_chars": 20000,
        "missing_checks": [],
        "required_checks": {
          "conformance_rollup_rule": false,
          "techniques_vs_requirements": false
        }
      },
      "sections": {
        "risks": [
          {
            "title": "Failure and Misuse Notes for Techniques for 4.1.2 Name, Role, Value",
            "content": "Failure techniques:\n- **F59**: Failure of Success Criterion 4.1.2 due to using script to make div or span a user interface control in HTML without providing a role for the control\n- **F15**: Failure of Success Criterion 4.1.2 due to implementing custom controls that do not use an accessibility API for the technology, or do so incompletely\n- **F20**: Failure of Success Criterion 1.1.1 and 4.1.2 due to not updating text alternatives when changes to non-text content occur\n- **F42**: Failure of Success Criteria 1.3.1, 2.1.1, 2.1.3, or 4.1.2 when emulating links\n- **F68**: Failure of Success Criterion 4.1.2 due to a user interface control not having a programmatically determined name\n- **F79**: Failure of Success Criterion 4.1.2 due to the focus state of a user interface component not being programmatically determinable or no notification of change of focus state available\n- **F86**: Failure of Success Criterion 4.1.2 due to not providing names for each part of a multi-part form field, such as a US telephone number\n- **F89**: Failure of Success Criteria 2.4.4, 2.4.9 and 4.1.2 due to not providing an accessible name for an image which is the only content in a link\n- **F111**: Failure of Success Criteria 1.3.1, 2.5.3, and 4.1.2 due to a control with visible label text but no accessible name",
            "source_args": {
              "ref_id": "4.1.2"
            },
            "source_tool": "get_techniques_for_criterion"
          }
        ],
        "examples": [],
        "core_rules": [
          {
            "title": "4.1.2 Name, Role, Value",
            "content": "**Goal:** People using assistive technology understand all components.\n**What to do:** Give components correct names, roles, states, and values.\n**Why it's important:** Assistive technology only works well when code is done properly.\n\nFor all user interface components (including but not limited to: form elements, links and components generated by scripts), the name and role can be programmatically determined; states, properties, and values that can be set by the user can be programmatically set; and notification of changes to these items is available to user agents, including assistive technologies.",
            "source_args": {
              "ref_id": "4.1.2"
            },
            "source_tool": "get_criterion"
          }
        ],
        "definitions": [],
        "contrast_cases": [],
        "decision_rules": [
          {
            "title": "Decision Boundaries for 4.1.2 Name, Role, Value",
            "content": "Intent of Name, Role, Value\n The intent of this success criterion is to ensure that Assistive Technologies (AT)\n can gather appropriate information about, activate (or set) and keep up to date on the status of\n user interface controls in the content.\n\nWhen standard controls from accessible technologies are used, this process is straightforward.\n If the user interface elements are used according to specification the conditions\n of this provision will be met. (See examples of Success Criterion 4.1.2 below)",
            "source_args": {
              "ref_id": "4.1.2"
            },
            "source_tool": "get_criterion"
          }
        ],
        "structural_context": [],
        "technique_patterns": [
          {
            "title": "Techniques for 4.1.2 Name, Role, Value",
            "content": "Sufficient techniques:\n**Situation A: If using a standard user interface component in a markup language (e.g., HTML):**\n - **ARIA14**: Using aria-label to provide an accessible name where a visible label cannot be used\n - **ARIA16**: Using aria-labelledby to provide a name for user interface controls\n - **G108**: Using markup features to expose the name and role, allow user-settable properties to be directly set, and provide notification of changes\n - **H91**: Using HTML form controls and links\n - **H44**: Using label elements to associate text labels with form controls\n - **H64**: Using the title attribute of the iframe element\n - **H65**: Using the title attribute to identify form controls when the label element cannot be used\n - **H88**: Using HTML according to spec\n**Situation B: If using script or code to re-purpose a standard user interface component in a markup language:**\n **Exposing the names and roles, allowing user-settable properties to be directly set, and providing notification of changes**\n**Situation C: If using a standard user interface component in a programming technology:**\n - **G135**: Using the accessibility API features of a technology to expose names and roles, to allow user-settable properties to be directly set, and to provide notification of changes\n - **PDF10**: Providing labels for interactive form controls in PDF documents\n - **PDF12**: Providing name, role, value information for form fields in PDF documents\n**Situation D: If creating your own user interface component in a programming language:**\n - **G10**: Creating components using a technology that supports the accessibility API features of the platforms on which the user agents will be run to expose the names and roles, allow user-settable properties to be directly set, and provide notification of changes\n - **ARIA4**: Using a WAI-ARIA role to expose the role of a user interface component\n - **ARIA5**: Using WAI-ARIA state and property attributes to expose the state of a user interface component\n - **ARIA16**: Using aria-labelledby to provide a name for user interface controls",
            "source_args": {
              "ref_id": "4.1.2"
            },
            "source_tool": "get_techniques_for_criterion"
          },
          {
            "title": "H88: Using HTML according to spec",
            "content": "# H88: Using HTML according to spec\n\n**Technology:** html\n**Types:** sufficient\n**Applies to:** 1 success criteria\n\n## Related Success Criteria\n\n- **4.1.2** Name, Role, Value (Level A)\n\n## Links\n\n- [Full Technique Documentation](https://www.w3.org/WAI/WCAG22/Techniques/html/H88)",
            "source_args": {
              "id": "H88"
            },
            "source_tool": "get_technique"
          },
          {
            "title": "H91: Using HTML form controls and links",
            "content": "# H91: Using HTML form controls and links\n\n**Technology:** html\n**Types:** sufficient\n**Applies to:** 2 success criteria\n\n## Related Success Criteria\n\n- **2.1.1** Keyboard (Level A)\n- **4.1.2** Name, Role, Value (Level A)\n\n## Links\n\n- [Full Technique Documentation](https://www.w3.org/WAI/WCAG22/Techniques/html/H91)",
            "source_args": {
              "id": "H91"
            },
            "source_tool": "get_technique"
          },
          {
            "title": "ARIA4: Using a WAI-ARIA role to expose the role of a user interface component",
            "content": "# ARIA4: Using a WAI-ARIA role to expose the role of a user interface component\n\n**Technology:** aria\n**Types:** sufficient\n**Applies to:** 1 success criteria\n\n## Related Success Criteria\n\n- **4.1.2** Name, Role, Value (Level A)\n\n## Links\n\n- [Full Technique Documentation](https://www.w3.org/WAI/WCAG22/Techniques/aria/ARIA4)",
            "source_args": {
              "id": "ARIA4"
            },
            "source_tool": "get_technique"
          },
          {
            "title": "ARIA5: Using WAI-ARIA state and property attributes to expose the state of a user interface component",
            "content": "# ARIA5: Using WAI-ARIA state and property attributes to expose the state of a user interface component\n\n**Technology:** aria\n**Types:** sufficient\n**Applies to:** 1 success criteria\n\n## Related Success Criteria\n\n- **4.1.2** Name, Role, Value (Level A)\n\n## Links\n\n- [Full Technique Documentation](https://www.w3.org/WAI/WCAG22/Techniques/aria/ARIA5)",
            "source_args": {
              "id": "ARIA5"
            },
            "source_tool": "get_technique"
          }
        ]
      },
      "objective_text": "Apply the five rules for using ARIA correctly"
    },
    "teaching_content": "## CORE FACTS\n### 4.1.2 Name, Role, Value\n**Goal:** People using assistive technology understand all components.\n**What to do:** Give components correct names, roles, states, and values.\n**Why it's important:** Assistive technology only works well when code is done properly.\n\nFor all user interface components (including but not limited to: form elements, links and components generated by scripts), the name and role can be programmatically determined; states, properties, and values that can be set by the user can be programmatically set; and notification of changes to these items is available to user agents, including assistive technologies.\n\n## DECISION BOUNDARIES\n### Decision Boundaries for 4.1.2 Name, Role, Value\nIntent of Name, Role, Value\n The intent of this success criterion is to ensure that Assistive Technologies (AT)\n can gather appropriate information about, activate (or set) and keep up to date on the status of\n user interface controls in the content.\n\nWhen standard controls from accessible technologies are used, this process is straightforward.\n If the user interface elements are used according to specification the conditions\n of this provision will be met. (See examples of Success Criterion 4.1.2 below)\n\n## TECHNIQUE PATTERNS\n### Techniques for 4.1.2 Name, Role, Value\nSufficient techniques:\n**Situation A: If using a standard user interface component in a markup language (e.g., HTML):**\n - **ARIA14**: Using aria-label to provide an accessible name where a visible label cannot be used\n - **ARIA16**: Using aria-labelledby to provide a name for user interface controls\n - **G108**: Using markup features to expose the name and role, allow user-settable properties to be directly set, and provide notification of changes\n - **H91**: Using HTML form controls and links\n - **H44**: Using label elements to associate text labels with form controls\n - **H64**: Using the title attribute of the iframe element\n - **H65**: Using the title attribute to identify form controls when the label element cannot be used\n - **H88**: Using HTML according to spec\n**Situation B: If using script or code to re-purpose a standard user interface component in a markup language:**\n **Exposing the names and roles, allowing user-settable properties to be directly set, and providing notification of changes**\n**Situation C: If using a standard user interface component in a programming technology:**\n - **G135**: Using the accessibility API features of a technology to expose names and...\n\n### H88: Using HTML according to spec\n# H88: Using HTML according to spec\n\n**Technology:** html\n**Types:** sufficient\n**Applies to:** 1 success criteria\n\n## Related Success Criteria\n\n- **4.1.2** Name, Role, Value (Level A)\n\n## Links\n\n- [Full Technique Documentation](https://www.w3.org/WAI/WCAG22/Techniques/html/H88)\n\n### H91: Using HTML form controls and links\n# H91: Using HTML form controls and links\n\n**Technology:** html\n**Types:** sufficient\n**Applies to:** 2 success criteria\n\n## Related Success Criteria\n\n- **2.1.1** Keyboard (Level A)\n- **4.1.2** Name, Role, Value (Level A)\n\n## Links\n\n- [Full Technique Documentation](https://www.w3.org/WAI/WCAG22/Techniques/html/H91)\n\n## RISKS / MISUSE\n### Failure and Misuse Notes for Techniques for 4.1.2 Name, Role, Value\nFailure techniques:\n- **F59**: Failure of Success Criterion 4.1.2 due to using script to make div or span a user interface control in HTML without providing a role for the control\n- **F15**: Failure of Success Criterion 4.1.2 due to implementing custom controls that do not use an accessibility API for the technology, or do so incompletely\n- **F20**: Failure of Success Criterion 1.1.1 and 4.1.2 due to not updating text alternatives when changes to non-text content occur\n- **F42**: Failure of Success Criteria 1.3.1, 2.1.1, 2.1.3, or 4.1.2 when emulating links\n- **F68**: Failure of Success Criterion 4.1.2 due to a user interface control not having a programmatically determined name\n- **F79**: Failure of Success Criterion 4.1.2 due to the focus state of a user interface component not being programmatically determinable or no notification of change of focus state available\n- **F86**: Failu..."
  }
}
```

### Mastery
```json
[
  {
    "student_id": "test-conv-195112",
    "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
    "mastery_level": "in_progress",
    "evidence_summary": "Correctly explained that extra ARIA on native elements can duplicate or conflict with built-in semantics and harm reliability for AT.",
    "misconceptions": [],
    "mini_assessment_score": null,
    "final_assessment_score": null,
    "turns_spent": 12,
    "last_assessed_at": "datetime.datetime(2026, 4, 8, 19, 58, 9, 761560, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
  }
]
```

### Misconceptions
```json
[]
```

### Lesson State (final)
```json
{
  "active_concept": "avoid_redundant_aria",
  "pending_check": "Can the student identify when ARIA on a native element is redundant versus when it serves a real purpose?",
  "bridge_back_target": "implicit_native_roles_states",
  "teaching_order": [
    "aria_supplemental_metadata",
    "native_html_semantics_behavior",
    "prefer_native_over_aria",
    "preserve_native_semantics",
    "roles_create_requirements",
    "include_required_role_states",
    "aria_is_role_dependent",
    "use_supported_role_attributes",
    "implicit_native_roles_states",
    "avoid_redundant_aria",
    "native_aria_conflicts_harm",
    "choose_correct_aria_fix",
    "multiple_rule_violations",
    "justify_rule_based_choices"
  ],
  "concepts": [
    {
      "id": "aria_supplemental_metadata",
      "label": "ARIA is supplemental accessibility metadata, not a replacement for correct HTML",
      "status": "covered"
    },
    {
      "id": "native_html_semantics_behavior",
      "label": "Native HTML elements already carry built-in semantics and behavior",
      "status": "covered"
    },
    {
      "id": "prefer_native_over_aria",
      "label": "If native HTML can provide the needed semantics or behavior, prefer it over ARIA",
      "status": "covered"
    },
    {
      "id": "preserve_native_semantics",
      "label": "Do not change native semantics unless there is a very strong, valid reason",
      "status": "covered"
    },
    {
      "id": "roles_create_requirements",
      "label": "Some ARIA roles require particular states or properties",
      "status": "covered"
    },
    {
      "id": "include_required_role_states",
      "label": "All required ARIA states and properties for a chosen role must be present and valid",
      "status": "covered"
    },
    {
      "id": "aria_is_role_dependent",
      "label": "ARIA attributes are role-dependent and not every attribute is valid on every role",
      "status": "covered"
    },
    {
      "id": "use_supported_role_attributes",
      "label": "Use only ARIA states and properties supported for the role in question",
      "status": "covered"
    },
    {
      "id": "implicit_native_roles_states",
      "label": "Some HTML elements already expose implicit roles and states",
      "status": "covered"
    },
    {
      "id": "avoid_redundant_aria",
      "label": "Do not add redundant ARIA that repeats implicit native semantics",
      "status": "in_progress"
    },
    {
      "id": "native_aria_conflicts_harm",
      "label": "Conflicts between native semantics and ARIA can harm accessibility",
      "status": "not_covered"
    },
    {
      "id": "choose_correct_aria_fix",
      "label": "Apply the rules by removing ARIA, replacing custom markup with native HTML, adding missing required ARIA, or revising invalid combinations",
      "status": "not_covered"
    },
    {
      "id": "multiple_rule_violations",
      "label": "A single snippet may violate more than one rule at once",
      "status": "not_covered"
    },
    {
      "id": "justify_rule_based_choices",
      "label": "Correct application requires identifying which rule applies and why",
      "status": "not_covered"
    }
  ]
}
```

### Learner Memory
```json
{
  "student_id": "test-conv-195112",
  "summary": "Learner gives compact causal explanations and transfers rules to nearby cases without much prompting.",
  "strengths": [
    "Readiness to engage",
    "Asks focused questions",
    "Uses concrete frontend examples",
    "Shows early conceptual uptake",
    "Reasones causally from examples",
    "Connects concepts to frontend implementation risk",
    "Comfortable using familiar controls like buttons",
    "Uses concrete examples",
    "Can name implicit role/name benefits",
    "Reasons from assistive-tech impact",
    "Applies ideas to familiar frontend markup",
    "States rules in practical language",
    "Reasons from implementation consequences",
    "Explains cause and effect clearly",
    "Uses assistive-tech perspective appropriately",
    "Transfers from button example to role override risk",
    "Concise causal explanations",
    "Good native-vs-ARIA contrast reasoning",
    "Transfer from prior rule to new ARIA concept",
    "Uses concrete control examples",
    "Explains risks in user-impact terms",
    "Causal reasoning",
    "Concrete transfer from examples",
    "Connects code choices to assistive-tech consequences",
    "Concrete causal reasoning",
    "Applies rule to markup examples",
    "Frames issues in user-impact terms",
    "Concrete markup reasoning",
    "Causal explanation about AT information needs",
    "Practical repair-oriented thinking",
    "Applies rules to concrete snippets",
    "Reasons by comparing better semantic alternatives",
    "Gives concise, technically relevant explanations",
    "Concise rule restatement",
    "Connects rules to intended behavior",
    "Handles contrastive ARIA examples well",
    "Concise paraphrasing",
    "Good native-vs-ARIA comparisons"
  ],
  "support_needs": [
    "Clear framing before rule details",
    "Contrastive examples to separate native HTML from ARIA",
    "Keep building from practical native-vs-custom comparisons",
    "Help making implicit reasoning explicit as a named rule",
    "More examples beyond buttons to stabilize the concept",
    "Keep prompting for explicit rule naming",
    "Use contrastive markup to extend beyond familiar button examples",
    "Need explicit contrastive examples for new rules",
    "Need help moving from prefer-native reasoning to preserve-native reasoning",
    "Needs continued concrete examples to extend beyond native-vs-custom comparisons",
    "Needs help linking role choice to required ARIA follow-through",
    "Prompting to extend from rule idea to technical role obligations",
    "Worked examples to move from general principle to exact required ARIA states/properties",
    "Help distinguishing broad behavior matching from specific rule checks",
    "Practice spotting issues directly in markup",
    "Help tying intuitive explanation to formal rule names",
    "Keep examples concrete and role-specific",
    "Help separate required attributes from valid-but-optional ones",
    "Examples that contrast missing required ARIA with invalid ARIA",
    "Explicit naming of the rule after successful reasoning",
    "More examples spanning different rule types",
    "Help separating role support rules from redundancy/conflict rules",
    "More examples that pivot from ARIA validation to native HTML semantics",
    "Help naming implicit native semantics explicitly",
    "Concrete example checks to stabilize rule boundaries",
    "Explicit contrast between redundant ARIA and valid labeling uses"
  ],
  "tendencies": [
    "Starts from broad practical assumptions",
    "Seeks a big-picture mental model first",
    "Tests understanding by paraphrasing with examples",
    "Paraphrases understanding through practical tradeoffs",
    "Brings in implementation concerns like keyboard support",
    "Answers cautiously but accurately",
    "Builds understanding through practical frontend tradeoffs",
    "Uses button-vs-div examples to test understanding",
    "Frames understanding around practical reliability",
    "Answers strongest when prompted with a practical failure mode",
    "Frames understanding in terms of user expectations and screen reader output",
    "Repeats a solid answer verbatim when confident",
    "Paraphrases concepts through practical implementation examples",
    "Frames incorrect ARIA as misleading semantics",
    "Answers by paraphrasing the consequence in practical terms",
    "Uses familiar widgets to test understanding",
    "Answers directly and accurately when given a specific snippet",
    "Uses concise practical language rather than formal rule names",
    "Answers with implementation-ready examples",
    "Understands completeness of role/state relationships through practical consequences",
    "Responds well to yes/no plus why diagnostics",
    "Uses practical replacement suggestions to test understanding",
    "Summarizes with practical heuristics",
    "Reasons from implementation intent",
    "Answers with practical impact on screen readers and reliability",
    "Generalizes rules into actionable heuristics"
  ],
  "successful_strategies": [
    "Answer the current framing question directly",
    "Use concise contrasts between native HTML and ARIA",
    "Ask contrastive questions",
    "Use familiar controls like button vs div",
    "Use contrastive markup examples",
    "Ask why native is safer, not just which is preferred",
    "Ask what native elements provide for free",
    "Use direct native-vs-ARIA contrasts",
    "Ask for rule restatement in their own words",
    "Use concrete native-vs-custom comparisons",
    "Use contrastive examples with native elements",
    "Ask what breaks when semantics are changed",
    "Move from simple controls into concrete ARIA obligations",
    "Ask for one-sentence risk summaries",
    "Bridge from concrete misuse to the next rule",
    "Ask for one-step transfer to a familiar control",
    "Use concrete role examples like checkbox",
    "Follow principle with markup-based checking",
    "Short worked examples",
    "Concrete role-plus-state scenarios",
    "Ask for the practical consequence before naming the rule",
    "Snippet-based checks",
    "Ask whether AT has enough information",
    "Use familiar controls like checkbox",
    "Use short code snippets",
    "Ask for the smallest valid fix",
    "Contrast complete vs incomplete control semantics",
    "Contrast invalid pairing with an appropriate control pattern",
    "Use small markup snippets with one focused decision",
    "Ask for one-sentence rule restatements",
    "Use paired examples of valid vs invalid semantics",
    "Ask for the danger or consequence of a markup choice",
    "Use native element examples with optional ARIA additions",
    "Prompt for brief rule justification"
  ],
  "updated_at": "datetime.datetime(2026, 4, 8, 19, 58, 9, 757876, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```

### Objective Memory
```json
{
  "student_id": "test-conv-195112",
  "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
  "summary": "Student now explains that native elements already expose semantics and that extra ARIA can be redundant or conflicting.",
  "demonstrated_skills": [
    "Activates prior knowledge",
    "Asks a relevant framing question",
    "Contrasts native HTML with ARIA use",
    "Applies the supplemental-ARIA idea to a concrete control example",
    "Uses native-vs-custom comparison",
    "Gives causal justification for preferring native HTML",
    "Connects accessibility choice to implementation reliability",
    "Names built-in native semantics",
    "Connects native elements to assistive technology reliability",
    "Justifies Rule 1 with concrete markup reasoning",
    "Restates Rule 1 accurately",
    "Uses concrete markup comparison",
    "Connects native HTML to built-in meaning and behavior",
    "Explains risk of overriding native roles",
    "Connects semantics to assistive technology output",
    "Reasons about mismatched user expectations",
    "States prefer-native rule in own words",
    "Explains why changing a native role harms accessibility",
    "Uses causal reasoning about assistive tech and user expectations",
    "Causal explanation of role mismatch risk",
    "Transfers concept to checkbox example",
    "Connects role choice to required state exposure",
    "Explains causal impact of missing required ARIA state",
    "Connects role/state mismatch to user-facing accessibility failure",
    "Uses checkbox as a transfer example",
    "Identifies missing required ARIA state in a concrete snippet",
    "Explains user impact of incomplete role/state exposure",
    "Applies Rule 3 reasoning to checkbox example",
    "Applies required-state reasoning to role=\"checkbox\"",
    "Suggests a minimal valid ARIA fix",
    "Explains impact on assistive tech in causal terms",
    "Rejects invalid role/state combinations",
    "Explains why unsupported ARIA is not acceptable",
    "Offers a more suitable semantic alternative",
    "Restates rule from principle rather than memorized wording",
    "Connects attribute-role support to real control behavior",
    "Rejects arbitrary ARIA pairings",
    "Rejects unsupported role-state pairings",
    "Restates Rule 4 accurately",
    "Reasons causally about native semantics versus added ARIA",
    "Anticipates AT confusion from redundant or conflicting ARIA"
  ],
  "active_gaps": [
    "Does not yet distinguish ARIA from correct native HTML",
    "May over-associate ARIA with adding labels and roles",
    "Has not yet articulated what built-in semantics/behavior native elements provide",
    "Has not yet worked through the explicit ARIA rules",
    "Has not yet explicitly stated Rule 1",
    "Has not yet named built-in semantics and behavior beyond keyboard support",
    "Has not yet applied the rule across multiple examples",
    "Has not yet worked through Rule 2 about not overriding native semantics",
    "Has not yet handled examples involving invalid or redundant ARIA beyond button/div comparison",
    "Has not yet explained why changing native semantics is risky",
    "Has not yet worked through Rule 2 examples",
    "Has not yet covered role-required states/properties or redundant ARIA",
    "Has not yet worked with ARIA roles that require specific states or properties",
    "Has not yet checked role-attribute compatibility",
    "Has not yet applied redundancy and conflict rules beyond button examples",
    "Has not yet explained that selecting an ARIA role creates required state/property obligations",
    "Has not yet worked through Rule 3 examples",
    "Has not yet worked through explicit required-state examples",
    "Has not yet checked validity/completeness of required ARIA properties in markup",
    "Has not yet addressed role-dependent attribute support or redundancy rules",
    "Has not yet diagnosed missing required states/properties in markup",
    "Has not yet named Rule 3 explicitly",
    "Has not yet distinguished required role states from merely supported attributes",
    "Has not yet checked whether a given ARIA attribute is valid for a specific role",
    "Has not yet worked through redundancy and conflict rules",
    "Has not yet shown that some ARIA attributes are invalid for some roles",
    "Has not yet named or applied Rule 4 explicitly",
    "Has not yet worked with implicit native semantics or redundant ARIA",
    "Has not yet worked through redundancy with native implicit semantics",
    "Has not yet diagnosed multi-rule snippets systematically",
    "Has not yet justified choices across the full five-rule set",
    "Has not yet worked through implicit native roles/states",
    "Has not yet addressed redundant ARIA on native elements",
    "Has not yet practiced multi-rule diagnosis",
    "Has not yet applied Rule 5 to concrete native-element examples",
    "Has not yet distinguished redundant ARIA from legitimate naming/labeling cases",
    "Has not yet diagnosed multi-rule snippets"
  ],
  "next_focus": "Use concrete native HTML examples to identify redundant ARIA and justify removal.",
  "updated_at": "datetime.datetime(2026, 4, 8, 19, 58, 9, 754183, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```

---

## Full Conversation Transcript

**USER** (msg 1):
> No, I wouldn’t treat it as complete. A checkbox role without `aria-checked` is missing a required state, so AT wouldn’t get the full info it needs.

**ASSISTANT** (msg 2):
> Right. That’s the rule in action: a role isn’t complete unless its required state or property is there and valid.

Let’s make it concrete: if you saw `<div role="checkbox"></div>`, what would be the smallest fix to make it a valid checkbox for assistive tech?

**USER** (msg 3):
> Add `aria-checked`, probably `aria-checked="false"` or `"true"` depending on state. So like `<div role="checkbox" aria-checked="false"></div>`.

**ASSISTANT** (msg 4):
> Yes — that’s the right kind of fix. For a checkbox role, `aria-checked` is a valid required state, and it must reflect the current state.

Now let’s test the next rule: if you had `role="button" aria-checked="true"`, would you accept that pairing, or would you reject it?

**USER** (msg 5):
> I’d reject it — `aria-checked` doesn’t belong on a button. If you need a checked state, it should probably be a checkbox or toggle button with the right state like `aria-pressed` instead.

**ASSISTANT** (msg 6):
> Good. You rejected it for the right reason: ARIA states and properties are role-dependent, so you can’t mix an attribute with a role just because it sounds semantically related.

One small precision: the exact alternative state depends on the control’s real purpose, but the key rule is that the state must be supported by that role. So if the role is `button`, you would not use `aria-checked` unless the role supports it.

Can you restate the rule in one sentence: what should you check before adding an ARIA state or property to a role?

**USER** (msg 7):
> I should check that the state or property is actually supported by that role and that it matches the control’s real behavior. So basically: don’t slap on ARIA attributes just because they seem related.

**ASSISTANT** (msg 8):
> Exactly. That’s the rule: only use ARIA states and properties that the chosen role supports, and make sure they describe the control’s real behavior.

Now let’s shift to something that often gets missed: many native HTML elements already expose the role or state you’d otherwise try to add. What do you think is the danger of putting extra ARIA on a native element that already has the semantics built in?

**USER** (msg 9):
> You can end up duplicating or even conflicting with the native semantics, which can confuse screen readers. So like, instead of helping, the extra ARIA might override the built-in info or make it less reliable.

**ASSISTANT** (msg 10):
> Yes — that’s the danger. Native elements already expose information to assistive technologies, and adding redundant or conflicting ARIA can muddy that signal rather than improve it.

So the next rule is: if the HTML already provides the meaning or state, don’t add ARIA that just repeats it. For example, a real `<button>` already has button semantics, so adding `role="button"` to it is unnecessary.

What would you do with `<button role="button">Save</button>`: keep the ARIA or remove it?
