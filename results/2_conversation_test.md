# Conversation Test: Apply the five rules for using ARIA correctly

**Objective ID**: `038d7bf5-eb16-4ac0-a22b-42c8fa964d97`
**Student**: `test-conv-152804` (LLM-driven agent)
**Session**: `guided-test-152804`
**Run at**: 2026-04-08T15:36:15.224439
**Total turns**: 14
**Total tutor time**: 465.6s

---

## Pipeline Artifacts

### Teaching Plan (17099 chars)

```
## 1. objective_text
Compare the scope of WCAG (2.0, 2.1, 2.2), ATAG 2.0, and EN 301 549, and **identify** how each set of requirements influences web accessibility design.

## 2. plain_language_goal
Understand what each of these accessibility standards covers, how they differ, and how each one affects the way accessible websites and related tools are designed.

## 3. mastery_definition
A student has mastered this objective when they can:

- correctly distinguish WCAG 2.0, WCAG 2.1, WCAG 2.2, ATAG 2.0, and EN 301 549 by scope
- explain, at a high level, what kind of thing each standard applies to
- compare the WCAG versions in terms of expanding scope across versions without confusing them as separate unrelated standards
- identify whether a design scenario is primarily influenced by:
  - WCAG requirements for web content
  - ATAG requirements for authoring tools
  - EN 301 549 as a broader accessibility procurement/regulatory standard
- justify their classification using the scope of the standard, not memorized keywords
- avoid major category errors, such as treating ATAG as a web content standard or EN 301 549 as merely another WCAG version

## 4. objective_type
- conceptual understanding
- comparison
- classification
- decision-making
- application

## 5. prerequisite_knowledge

### essential prerequisites
- Basic understanding of what “web accessibility” means
- Awareness that accessibility guidance can apply to different targets, such as:
  - web content/pages
  - software/tools used to create content
  - broader ICT products/services or compliance frameworks
- Basic familiarity with the idea of a “standard” or “guideline” as a set of requirements used to guide design or evaluation

### helpful but nonessential prerequisites
- Prior exposure to WCAG’s name and purpose
- General awareness of legal/procurement compliance in accessibility
- Familiarity with roles in digital product work, such as designer, developer, evaluator, procurement/compliance lead
- Awareness that standards can evolve by version

## 6. prerequisite_gap_policy
If the learner lacks essential prerequisites, the tutor should pause the objective and briefly establish only the minimum framing needed:

- clarify what accessibility standards are for
- distinguish “what is being evaluated or designed”:
  - content
  - tools
  - broader ICT systems/procurement requirements
- confirm that the learner can reason about scope before introducing named standards

The tutor should not launch into detailed accessibility history or legal instruction. If the learner cannot yet distinguish target-of-application, the tutor should remediate that first because the objective depends on classification by scope.

## 7. concept_decomposition
1. A standard/guideline can be compared by the thing it applies to, not just by its title.
2. “Scope” means the domain, artifact, or context a set of requirements covers.
3. WCAG is a family of requirements aimed at accessibility of web content.
4. WCAG 2.0, 2.1, and 2.2 are successive versions within the same WCAG line.
5. Later WCAG versions extend prior coverage rather than representing unrelated standards.
6. ATAG 2.0 applies to authoring tools rather than to published web content itself.
7. Authoring tools influence accessibility both by being accessible to authors and by supporting production of accessible content.
8. EN 301 549 has broader scope than WCAG because it is not limited to web content alone.
9. EN 301 549 functions as a broader accessibility requirements framework often used in procurement/regulatory contexts.
10. A requirement set influences design differently depending on whether it targets:
   - content design
   - tool design
   - broader product/service/compliance design
11. In practical scenarios, the right standard can be identified by asking what is being designed, evaluated, or procured.
12. Some scenarios involve overlap, but one standard may be primary depending on the design decision being made.

## 8. dependency_order

### Recommended order with dependencies
1. **A standard can be compared by target/scope**  
   - foundational; depends only on prerequisite knowledge

2. **Meaning of “scope” in this objective**  
   - depends on 1

3. **WCAG as web content guidance family**  
   - depends on 1, 2

4. **WCAG 2.0/2.1/2.2 are versions in one line**  
   - depends on 3

5. **Later WCAG versions extend earlier coverage**  
   - depends on 4

6. **ATAG 2.0 as authoring tool guidance**  
   - depends on 1, 2

7. **How ATAG influences design: tool accessibility + support for accessible output**  
   - depends on 6

8. **EN 301 549 as broader accessibility requirements framework**  
   - depends on 1, 2

9. **How EN 301 549 influences design: broader product/service/procurement framing**  
   - depends on 8

10. **Compare all three families by scope**  
   - depends on 3, 5, 7, 9

11. **Classify practical scenarios by which standard most directly influences the design decision**  
   - depends on 10

12. **Handle overlap/borderline scenarios**  
   - depends on 11

### Why this sequence is instructionally sound
- It begins with the abstract comparison principle—scope—before introducing names.
- It introduces WCAG first because it is the most likely known anchor and easiest reference point.
- It treats the WCAG versions as related before comparison to other standards, reducing version confusion.
- It then contrasts ATAG and EN 301 549 by target, creating clean category boundaries.
- Only after the student has clear scope distinctions does it move to “influence on design,” which requires applying those distinctions to realistic decisions.
- Borderline overlap cases are deferred until after basic classification to avoid early overload.

## 9. likely_misconceptions
- Thinking WCAG 2.0, 2.1, and 2.2 are separate competing standards rather than versions in one lineage
- Assuming newer WCAG versions completely replace conceptual continuity with earlier versions
- Treating ATAG as rules for website pages rather than for tools used to create content
- Assuming ATAG only concerns whether the tool’s own interface is accessible, and not whether it supports creation of accessible content
- Treating EN 301 549 as just a European version of WCAG
- Assuming EN 301 549 only matters to lawyers or procurement teams and has no design implications
- Believing all accessibility requirements directly tell web page designers the same kinds of things
- Confusing “who uses the standard” with “what the standard applies to”
- Assuming “scope” means geographic scope only, rather than applicability to a type of artifact or system
- Overgeneralizing that any accessibility issue on a website must always be classified only under WCAG, even when the decision is about the content management tool or procurement framework

## 10. explanation_vs_question_strategy

### 1. A standard can be compared by target/scope
- **Start mode:** diagnostic question
- **Why:** reveals whether the learner can already distinguish standards by what they govern rather than by title recognition

### 2. Meaning of “scope” in this objective
- **Start mode:** brief explanation
- **Why:** terminology here needs a precise anchor to prevent confusion with legal/geographic scope

### 3. WCAG as web content guidance family
- **Start mode:** guided questioning
- **Why:** many learners have partial prior knowledge; questioning can activate it without overexplaining

### 4. WCAG 2.0/2.1/2.2 are versions in one line
- **Start mode:** brief explanation
- **Why:** version lineage is a compact fact structure that should be established cleanly to prevent false branching

### 5. Later WCAG versions extend earlier coverage
- **Start mode:** contrastive example
- **Why:** comparing “same family, later version” versus “different standard entirely” helps solidify the relationship

### 6. ATAG 2.0 as authoring tool guidance
- **Start mode:** guided questioning
- **Why:** students can often infer this from “authoring tool” once prompted; inference supports retention

### 7. How ATAG influences design: tool accessibility + support for accessible output
- **Start mode:** worked example
- **Why:** influence on design is easier to grasp through a concrete tool scenario than through abstract description

### 8. EN 301 549 as broader accessibility requirements framework
- **Start mode:** brief explanation
- **Why:** many learners are less likely to know this; concise framing reduces confusion

### 9. How EN 301 549 influences design: broader product/service/procurement framing
- **Start mode:** worked example
- **Why:** the indirect path from standard to design decision is clearer when tied to a procurement or product requirement example

### 10. Compare all three families by scope
- **Start mode:** contrastive example
- **Why:** side-by-side comparison is the core skill and benefits from explicit contrasts

### 11. Classify practical scenarios by primary design influence
- **Start mode:** guided questioning
- **Why:** classification with justification is the target performance and suits Socratic probing

### 12. Handle overlap/borderline scenarios
- **Start mode:** diagnostic question
- **Why:** tricky cases are best used to test whether the learner can reason beyond memorized labels

## 11. socratic_question_goals

### Stage 1: Scope as comparison lens
- diagnose prior knowledge about standards
- surface whether learner thinks titles/versions alone determine meaning
- establish the habit of asking “what does this apply to?”

### Stage 2: WCAG family framing
- confirm learner recognizes WCAG as content-focused
- test whether learner can distinguish versions from separate standards
- reveal misconceptions about versioning and extension

### Stage 3: ATAG
- prompt learner to infer target from the name/context
- check whether learner distinguishes tool requirements from content requirements
- reveal whether learner sees both dimensions of ATAG’s design influence

### Stage 4: EN 301 549
- test whether learner can recognize broader applicability
- reveal confusion between WCAG and procurement/regulatory frameworks
- check whether learner can identify indirect design influence through broader requirements

### Stage 5: Comparison across all standards
- force comparison by scope
- require learner to articulate one meaningful distinction at a time
- test whether learner can explain why a scenario belongs primarily to one standard

### Stage 6: Borderline and transfer
- test transfer to unfamiliar scenarios
- check reasoning when more than one standard seems relevant
- require justification of the “primary influence” rather than guessing

## 12. example_requirements

### simplest introductory example
- A simple public webpage design decision, such as making page content accessible, to anchor WCAG as content-focused

### at least one contrastive example
- A content design scenario versus an authoring tool design scenario
- Example pair:
  - designing a website page template
  - designing a CMS editor that helps authors add alternative text

### at least one borderline or tricky case
- A scenario where a website accessibility issue is partly caused by the authoring tool, requiring the learner to decide whether the primary influence is WCAG or ATAG
- A scenario where a public-sector procurement requirement references broader accessibility expectations, inviting EN 301 549 rather than only WCAG

### at least one transfer scenario
- A scenario involving selection or procurement of a platform, service, or ICT solution where the learner must identify EN 301 549 as the broader framework influencing design requirements
- A scenario involving updating from an earlier WCAG version to a later one, where the learner must reason about expanded coverage without treating the newer version as unrelated

### example design constraints
- Examples should stay high-level and scope-oriented
- Avoid requiring detailed memorization of individual success criteria or legal clauses
- Each example should clearly identify the artifact being designed: content, tool, or broader ICT/procurement context

## 13. retrieval_requirements

### must-retrieve
- High-level definitions/scope statements for:
  - WCAG 2.0
  - WCAG 2.1
  - WCAG 2.2
  - ATAG 2.0
  - EN 301 549  
  Reason: accurate scope comparison is the central learning task.
- Reliable statement that WCAG 2.1 and 2.2 build on prior WCAG versions within the same line  
  Reason: necessary to avoid version confusion.
- High-level description of ATAG’s dual focus:
  - accessibility of the authoring tool interface
  - support for creation of accessible content  
  Reason: core to understanding design influence.
- High-level description of EN 301 549 as broader accessibility requirements for ICT/procurement context  
  Reason: needed to contrast with WCAG and ATAG.
- A small set of accurate real-world scenario types illustrating:
  - web content design
  - authoring tool design
  - procurement/compliance-driven product selection/design  
  Reason: needed for classification and application.

### optional-supporting
- Official publication names/issuing bodies for credibility and precision
- A simple mapping note about how EN 301 549 may incorporate/reference web accessibility requirements  
  Reason: helps with overlap cases, but should not dominate the lesson.
- Timeline/version-release context for WCAG 2.0, 2.1, 2.2  
  Reason: useful for advanced learners, not essential to the objective.
- Role-based examples for designers, developers, tool vendors, and procurement teams  
  Reason: supports transfer to workplace contexts.

## 14. assessment_evidence

### quick understanding checks
- Ask the learner to match each standard/version to its primary scope
- Ask whether WCAG 2.1 is best understood as:
  - a separate category from WCAG
  - a later version in the WCAG family
- Ask which standard most directly applies to an authoring tool

### application task
- Provide 3–5 short design scenarios and require the learner to identify which standard most directly influences the design decision and explain why
- Scenarios should include:
  - content/page design
  - authoring tool behavior
  - procurement or broader ICT requirement

### transfer task
- Give a new scenario not previously discussed, such as selecting a platform under institutional accessibility requirements, and ask the learner to reason out which requirement set is primary and what kind of design influence it has
- Or ask the learner to compare how updating from WCAG 2.0 to 2.2 differs from switching from WCAG to ATAG

### misconception check
- Present statements for correction, such as:
  - “ATAG is mainly for checking whether a web page is accessible.”
  - “EN 301 549 is just another WCAG version.”
  - “WCAG 2.2 applies to a different kind of thing than WCAG 2.0.”
- Require explanation of what is wrong in each statement

## 15. adaptation_notes

### beginner
- Spend more time on the meaning of scope and target-of-application
- Use fewer standards in memory at once; establish WCAG first, then ATAG, then EN 301 549
- Keep examples concrete and role-based
- Avoid detailed compliance nuance

### intermediate learner
- Move more quickly through definitions
- Emphasize comparison and scenario classification
- Introduce overlap cases sooner
- Ask for justification using “what is being designed/evaluated/procured?”

### advanced learner
- Compress prerequisite review
- Use more ambiguous scenarios with overlapping applicability
- Probe reasoning about how broader frameworks can shape design decisions indirectly
- Invite concise comparison across versions and frameworks without drifting into legal detail

## 16. boundaries_and_non_goals
This lesson should **not** teach:

- detailed WCAG success criteria or conformance levels
- detailed legal requirements of specific jurisdictions
- full history of W3C accessibility standards
- UAAG or other accessibility standards not named in the objective
- deep implementation techniques for meeting any standard
- detailed procurement process mechanics
- exhaustive differences between WCAG 2.0, 2.1, and 2.2 at criterion level
- accessibility testing procedures in depth

These belong to separate objectives and would overload a scope-comparison lesson.

## 17. concise_plan_summary
- Start by anchoring comparison around **scope**: what each standard applies to.
- Establish WCAG first as a **web content** family, then clarify that 2.0/2.1/2.2 are **versions in one lineage**.
- Contrast ATAG as applying to **authoring tools**, not published web content.
- Introduce EN 301 549 as a **broader accessibility requirements framework** beyond just web content.
- Teach “influence on design” by connecting each standard to a different design target: content, tools, or broader product/procurement context.
- Use contrastive and scenario-based questioning to build classification skill.
- Delay overlap/borderline cases until after the learner can classify clear examples.
- Assess mastery through justified scenario classification and correction of common scope misconceptions.
```

### Evidence Pack (3213 chars)

````markdown
## CORE FACTS
### 1.1.1 Non-text Content
**Level:** A | **Principle:** 1 Perceivable | **Guideline:** 1.1 Text Alternatives

All non-text content that is presented to the user has a text alternative that serves the equivalent purpose, except for the situations listed below.

## TECHNIQUE PATTERNS
### Techniques for 1.1.1 Non-text Content
Sufficient techniques:
**Situation A: If a short description can serve the same purpose and present the same information as the non-text content:**
 - **G94**: Providing short text alternative for non-text content that serves the same purpose and presents the same information as the non-text content
 *Short text alternative techniques for Situation A*
 - **ARIA6**: Using aria-label to provide labels for objects
 - **ARIA10**: Using aria-labelledby to provide a text alternative for non-text content
 - **G196**: Using a text alternative on one item within a group of images that describes all items in the group
 - **H2**: Combining adjacent image and text links for the same resource
 - **H37**: Using alt attributes on img elements
 - **H53**: Using the body of the object element
 - **H86**: Providing text alternatives for emojis, emoticons, ASCII art, and leetspeak
 - **PDF1**: Applying text alternatives to images with the Alt entry in PDF documents
**Situation B: If a short description can not serve the same purpose and present the same information as the non-text content (e.g., a chart or diagram):**
 - **G95**: Providing short text alternatives that provide a brief description o...

## RISKS / MISUSE
### Failure and Misuse Notes for Techniques for 1.1.1 Non-text Content
Failure techniques:
- **F3**: Failure of Success Criterion 1.1.1 due to using CSS to include images that convey important information
- **F13**: Failure of Success Criterion 1.1.1 and 1.4.1 due to having a text alternative that does not include information that is conveyed by color differences in the image
- **F20**: Failure of Success Criterion 1.1.1 and 4.1.2 due to not updating text alternatives when changes to non-text content occur
- **F30**: Failure of Success Criterion 1.1.1 and 1.2.1 due to using text alternatives that are not alternatives (e.g., filenames or placeholder text)
- **F38**: Failure of Success Criterion 1.1.1 due to not marking up decorative images in HTML in a way that allows assistive technology to ignore them
- **F39**: Failure of Success Criterion 1.1.1 due to providing a text alternative that is not null (e.g., alt="spacer" or alt="image") for images that sho...

## STRUCTURE NOTES
### WCAG 2.2 Principles
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
````

### Retrieval Bundle Coverage

```json
{
  "hit_count": 5,
  "hit_chars": 13302,
  "missing_checks": [],
  "required_checks": {
    "conformance_rollup_rule": false,
    "techniques_vs_requirements": true
  },
  "budget_chars": 20000
}
```

### Retrieval Bundle Sections

**core_rules** (1 items):
- `get_success_criteria_detail` → 1.1.1 Non-text Content (233 chars)

**technique_patterns** (1 items):
- `get_techniques_for_criterion` → Techniques for 1.1.1 Non-text Content (2200 chars)

**risks** (1 items):
- `get_techniques_for_criterion` → Failure and Misuse Notes for Techniques for 1.1.1 Non-text Content (1400 chars)

**structural_context** (1 items):
- `list_principles` → WCAG 2.2 Principles (637 chars)


### Lesson State (initial)

```json
{
  "active_concept": "accessible_name_for_interactive_elements",
  "pending_check": "Can the student classify mixed examples by rule violated and say when ARIA is needed vs redundant?",
  "bridge_back_target": "recognize_unnecessary_aria",
  "teaching_order": [
    "aria_as_supplement",
    "native_html_semantics",
    "prefer_native_html",
    "recognize_unnecessary_aria",
    "accessible_name_for_interactive_elements",
    "keyboard_support_for_custom_controls",
    "presentation_none_misuse",
    "preserve_native_semantics",
    "diagnose_violated_rule",
    "revise_to_follow_rules",
    "handle_borderline_cases",
    "justify_rule_based_decisions"
  ],
  "concepts": [
    {
      "id": "aria_as_supplement",
      "label": "ARIA is a supplement, not a default replacement for native HTML",
      "status": "covered"
    },
    {
      "id": "native_html_semantics",
      "label": "Native HTML elements and attributes often already provide needed semantics and behavior",
      "status": "covered"
    },
    {
      "id": "prefer_native_html",
      "label": "Prefer native HTML when it can do the job",
      "status": "covered"
    },
    {
      "id": "recognize_unnecessary_aria",
      "label": "Recognize when ARIA is unnecessary, redundant, or harmful",
      "status": "covered"
    },
    {
      "id": "accessible_name_for_interactive_elements",
      "label": "Interactive elements must have an accessible name",
      "status": "not_covered"
    },
    {
      "id": "keyboard_support_for_custom_controls",
      "label": "Interactive ARIA controls require expected keyboard operability",
      "status": "not_covered"
    },
    {
      "id": "presentation_none_misuse",
      "label": "Do not use role=\"presentation\" or role=\"none\" on focusable or interactive elements",
      "status": "not_covered"
    },
    {
      "id": "preserve_native_semantics",
      "label": "Do not change native semantics unless justified and valid",
      "status": "not_covered"
    },
    {
      "id": "diagnose_violated_rule",
      "label": "Map a flawed example to the specific violated rule",
      "status": "not_covered"
    },
    {
      "id": "revise_to_follow_rules",
      "label": "Revise code or design choices to align with the rule",
      "status": "not_covered"
    },
    {
      "id": "handle_borderline_cases",
      "label": "Handle borderline cases where ARIA may be needed",
      "status": "not_covered"
    },
    {
      "id": "justify_rule_based_decisions",
      "label": "Justify decisions with rule-based reasoning",
      "status": "not_covered"
    }
  ]
}
```

### Slim Persisted Payload

| Field | Size |
|-------|------|
| `objective_id` | 38 bytes |
| `objective_text` | 153 bytes |
| `teaching_content` | 3270 bytes |
| `teaching_plan` | 17684 bytes |
| `lesson_state` | 2134 bytes |
| `retrieved_at` | 28 bytes |
| `retrieval_bundle` | 5635 bytes |

---

## Turn-by-Turn Log

### Turn 1: introduction → introduction
**Tutor time**: 147.04s | **Student agent time**: 1.56s | **Turns on obj**: 0 → 1

**Student**:
> Cool, I’ve heard ARIA mentioned a bunch but I’m kinda fuzzy on the actual rules. I’m ready — I mostly just know it’s for making stuff more accessible when normal HTML isn’t enough, right?

**Tutor**:
> Yes — that’s the right starting idea. ARIA is there to add accessibility information when native HTML doesn’t provide enough, not as the default way to build interactive things.

A good rule-of-thumb is: if HTML already gives you the meaning and behavior you need, ARIA usually shouldn’t be added on top. That matters because native elements often already carry semantics that support accessibility, while ARIA is extra metadata layered on when needed.

So let me test the mental model: if you have a real `<button>`, would adding `role="button"` usually help, or would it be unnecessary?

<details><summary>WebSocket Events (13 non-token)</summary>

```json
[
  {
    "type": "stage",
    "stage": "composing",
    "detail": "Creating teaching plan...",
    "_ts": "2026-04-08T15:28:07.293111"
  },
  {
    "type": "stage",
    "stage": "searching",
    "detail": "Researching WCAG content...",
    "_ts": "2026-04-08T15:29:38.295516"
  },
  {
    "type": "stage",
    "stage": "searching",
    "detail": "Researching WCAG sources (round 1/4)...",
    "_ts": "2026-04-08T15:29:38.297772"
  },
  {
    "type": "stage",
    "stage": "searching",
    "detail": "Researching WCAG sources (round 2/4)...",
    "_ts": "2026-04-08T15:29:49.644352"
  },
  {
    "type": "stage",
    "stage": "searching",
    "detail": "Researching WCAG sources (round 3/4)...",
    "_ts": "2026-04-08T15:30:00.594087"
  },
  {
    "type": "stage",
    "stage": "searching",
    "detail": "Validating evidence...",
    "_ts": "2026-04-08T15:30:12.627331"
  },
  {
    "type": "stage",
    "stage": "searching",
    "detail": "Teaching pack: 1526 chars from 5 sources",
    "_ts": "2026-04-08T15:30:12.628318"
  },
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Analyzing your response...",
    "_ts": "2026-04-08T15:30:12.667718"
  },
  {
    "type": "stage",
    "stage": "composing",
    "detail": "Generating response (introduction)...",
    "_ts": "2026-04-08T15:30:30.979683"
  },
  {
    "type": "stream_start",
    "_ts": "2026-04-08T15:30:33.222416"
  },
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Updating learning state...",
    "_ts": "2026-04-08T15:30:34.312252"
  },
  {
    "type": "mastery_update",
    "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
    "objective_text": "Apply the five rules for using ARIA correctly",
    "new_level": "in_progress",
    "_ts": "2026-04-08T15:30:34.330565"
  },
  {
    "type": "stream_end",
    "metadata": {
      "session_id": "guided-test-152804",
      "stage": "introduction",
      "stage_advanced": false,
      "assessment": {}
    },
    "_ts": "2026-04-08T15:30:34.330610"
  }
]
```
</details>

**Lesson State**: active=`accessible_name_for_interactive_elements`
  `aria_as_supplement` [done], `native_html_semantics` [done], `prefer_native_html` [done], `recognize_unnecessary_aria` [done], `accessible_name_for_interactive_elements` [todo], `keyboard_support_for_custom_controls` [todo], `presentation_none_misuse` [todo], `preserve_native_semantics` [todo], `diagnose_violated_rule` [todo], `revise_to_follow_rules` [todo], `handle_borderline_cases` [todo], `justify_rule_based_decisions` [todo]

**Mastery**: level=`in_progress` confidence=?

<details><summary>Objective Memory</summary>

```json
{
  "student_id": "test-conv-152804",
  "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
  "summary": "Student already holds the basic mental model that ARIA is for cases where normal HTML is not enough.",
  "demonstrated_skills": [
    "Recognizes ARIA as supplemental rather than default"
  ],
  "active_gaps": [
    "Has not yet explained what native HTML already provides",
    "Has not yet applied the idea to examples"
  ],
  "next_focus": "Contrast native HTML semantics/behavior with ARIA so the learner can justify preferring native elements.",
  "updated_at": "datetime.datetime(2026, 4, 8, 15, 30, 34, 321279, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

<details><summary>Learner Memory</summary>

```json
{
  "student_id": "test-conv-152804",
  "summary": "Learner starts with partial prior knowledge and invites confirmation before going deeper.",
  "strengths": [
    "Comes in with relevant prior awareness",
    "States uncertainty clearly"
  ],
  "support_needs": [
    "Needs crisp confirmation plus refinement of partial mental models",
    "Needs example-based contrast to stabilize understanding"
  ],
  "tendencies": [
    "Uses tentative phrasing when unsure",
    "Engages readily at the start of a topic"
  ],
  "successful_strategies": [
    "Affirm then refine",
    "Use simple native-vs-ARIA contrasts"
  ],
  "updated_at": "datetime.datetime(2026, 4, 8, 15, 30, 34, 324856, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

---

### Turn 2: introduction → introduction
**Tutor time**: 16.28s | **Student agent time**: 1.78s | **Turns on obj**: 1 → 2

**Student**:
> Hmm, I think it’d be unnecessary? Like a real `<button>` already acts like a button, so adding `role="button"` seems kinda redundant. But does it ever help if the styling is weird?

**Tutor**:
> Right — for a real `<button>`, unusual styling does not make `role="button"` more helpful. The element already has button semantics and keyboard behavior, and CSS changes how it looks, not what it is.

So in that case, adding `role="button"` is redundant rather than useful. A better question is: what information do you think the native `<button>` already gives you that ARIA is trying to add?

<details><summary>WebSocket Events (6 non-token)</summary>

```json
[
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Analyzing your response...",
    "_ts": "2026-04-08T15:30:35.941816"
  },
  {
    "type": "stage",
    "stage": "composing",
    "detail": "Generating response (introduction)...",
    "_ts": "2026-04-08T15:30:49.506132"
  },
  {
    "type": "stream_start",
    "_ts": "2026-04-08T15:30:51.367865"
  },
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Updating learning state...",
    "_ts": "2026-04-08T15:30:52.149363"
  },
  {
    "type": "mastery_update",
    "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
    "objective_text": "Apply the five rules for using ARIA correctly",
    "new_level": "in_progress",
    "_ts": "2026-04-08T15:30:52.180213"
  },
  {
    "type": "stream_end",
    "metadata": {
      "session_id": "guided-test-152804",
      "stage": "introduction",
      "stage_advanced": false,
      "assessment": {}
    },
    "_ts": "2026-04-08T15:30:52.180258"
  }
]
```
</details>

**Lesson State**: active=`accessible_name_for_interactive_elements`
  `aria_as_supplement` [done], `native_html_semantics` [done], `prefer_native_html` [done], `recognize_unnecessary_aria` [done], `accessible_name_for_interactive_elements` [todo], `keyboard_support_for_custom_controls` [todo], `presentation_none_misuse` [todo], `preserve_native_semantics` [todo], `diagnose_violated_rule` [todo], `revise_to_follow_rules` [todo], `handle_borderline_cases` [todo], `justify_rule_based_decisions` [todo]

**Active Misconceptions** (1):
- [active] Styling might make adding an ARIA role to a native control helpful.

**Mastery**: level=`in_progress` confidence=?

<details><summary>Objective Memory</summary>

```json
{
  "student_id": "test-conv-152804",
  "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
  "summary": "Student identified role=\"button\" on a real <button> as unnecessary, with lingering uncertainty about whether styling changes that.",
  "demonstrated_skills": [
    "Recognizes ARIA as supplemental rather than default",
    "Spots redundant ARIA on native button",
    "Connects native element to built-in behavior"
  ],
  "active_gaps": [
    "Has not yet explained what native HTML already provides",
    "Has not yet applied the idea to examples",
    "Needs confirmation that CSS styling does not alter native semantics",
    "Has not yet contrasted native semantics and ARIA in broader examples"
  ],
  "next_focus": "Clarify that styling does not remove native semantics, then extend to native-vs-ARIA contrasts.",
  "updated_at": "datetime.datetime(2026, 4, 8, 15, 30, 52, 175851, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

<details><summary>Learner Memory</summary>

```json
{
  "student_id": "test-conv-152804",
  "summary": "Learner gives a plausible answer, then asks a targeted follow-up to test edge cases.",
  "strengths": [
    "Comes in with relevant prior awareness",
    "States uncertainty clearly",
    "Makes correct tentative judgments",
    "Surfaces uncertainty explicitly"
  ],
  "support_needs": [
    "Needs crisp confirmation plus refinement of partial mental models",
    "Needs example-based contrast to stabilize understanding",
    "Needs crisp clarification on edge cases before generalizing rules"
  ],
  "tendencies": [
    "Uses tentative phrasing when unsure",
    "Engages readily at the start of a topic",
    "Checks exceptions immediately after a rule-of-thumb"
  ],
  "successful_strategies": [
    "Affirm then refine",
    "Use simple native-vs-ARIA contrasts",
    "Affirm the correct core answer, then refine with a concrete edge-case clarification"
  ],
  "updated_at": "datetime.datetime(2026, 4, 8, 15, 30, 52, 177315, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

---

### Turn 3: introduction → exploration
**Tutor time**: 16.39s | **Student agent time**: 1.47s | **Turns on obj**: 2 → 3

**Student**:
> It already gives the role, keyboard support, focusability, and a built-in accessible name from its text content. So ARIA would just be repeating stuff the browser already knows.

**Tutor**:
> Exactly. That’s the core idea: native HTML already supplies semantics and behavior, so ARIA should not be used to restate what the browser already provides.

Now push that one step further: if a native element already does the job correctly, what rule would you use to decide whether ARIA belongs there at all?

<details><summary>WebSocket Events (7 non-token)</summary>

```json
[
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Analyzing your response...",
    "_ts": "2026-04-08T15:30:54.008490"
  },
  {
    "type": "stage",
    "stage": "composing",
    "detail": "Generating response (introduction)...",
    "_ts": "2026-04-08T15:31:08.289215"
  },
  {
    "type": "stream_start",
    "_ts": "2026-04-08T15:31:09.761016"
  },
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Updating learning state...",
    "_ts": "2026-04-08T15:31:10.343388"
  },
  {
    "type": "mastery_update",
    "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
    "objective_text": "Apply the five rules for using ARIA correctly",
    "new_level": "in_progress",
    "_ts": "2026-04-08T15:31:10.357917"
  },
  {
    "type": "stage_update",
    "stage": "exploration",
    "objective": "Apply the five rules for using ARIA correctly",
    "summary": "Student accurately explained multiple native button affordances and why ARIA would be redundant, showing reasoning beyond recall.",
    "_ts": "2026-04-08T15:31:10.360699"
  },
  {
    "type": "stream_end",
    "metadata": {
      "session_id": "guided-test-152804",
      "stage": "exploration",
      "stage_advanced": true,
      "assessment": {}
    },
    "_ts": "2026-04-08T15:31:10.360713"
  }
]
```
</details>

**Lesson State**: active=`accessible_name_for_interactive_elements`
  `aria_as_supplement` [done], `native_html_semantics` [done], `prefer_native_html` [done], `recognize_unnecessary_aria` [done], `accessible_name_for_interactive_elements` [todo], `keyboard_support_for_custom_controls` [todo], `presentation_none_misuse` [todo], `preserve_native_semantics` [todo], `diagnose_violated_rule` [todo], `revise_to_follow_rules` [todo], `handle_borderline_cases` [todo], `justify_rule_based_decisions` [todo]

**Active Misconceptions** (1):
- [active] Styling might make adding an ARIA role to a native control helpful.

**Mastery**: level=`in_progress` confidence=?

<details><summary>Objective Memory</summary>

```json
{
  "student_id": "test-conv-152804",
  "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
  "summary": "Student can now explain that a native button already provides role, keyboard support, focusability, and a text-derived accessible name, making redundant ARIA unnecessary.",
  "demonstrated_skills": [
    "Recognizes ARIA as supplemental rather than default",
    "Spots redundant ARIA on native button",
    "Connects native element to built-in behavior",
    "Explains what native HTML already provides",
    "Distinguishes native semantics from ARIA metadata",
    "Uses button example to justify why redundant ARIA is unnecessary"
  ],
  "active_gaps": [
    "Has not yet explained what native HTML already provides",
    "Has not yet applied the idea to examples",
    "Needs confirmation that CSS styling does not alter native semantics",
    "Has not yet contrasted native semantics and ARIA in broader examples",
    "Has not yet applied Rule 1 across contrasting native vs custom examples",
    "Has not yet mapped judgments to the named ARIA rules"
  ],
  "next_focus": "Use contrastive examples to apply the prefer-native rule.",
  "updated_at": "datetime.datetime(2026, 4, 8, 15, 31, 10, 350107, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

<details><summary>Learner Memory</summary>

```json
{
  "student_id": "test-conv-152804",
  "summary": "Learner responds well after a crisp clarification and can extend the idea by listing concrete native affordances.",
  "strengths": [
    "Comes in with relevant prior awareness",
    "States uncertainty clearly",
    "Makes correct tentative judgments",
    "Surfaces uncertainty explicitly",
    "Can articulate multiple built-in semantics once prompted",
    "Builds from examples to principle",
    "Reasons concretely about behavior and naming"
  ],
  "support_needs": [
    "Needs crisp confirmation plus refinement of partial mental models",
    "Needs example-based contrast to stabilize understanding",
    "Needs crisp clarification on edge cases before generalizing rules",
    "Needs continued example-based application to stabilize rule use",
    "Benefits from explicit connection between examples and named rules"
  ],
  "tendencies": [
    "Uses tentative phrasing when unsure",
    "Engages readily at the start of a topic",
    "Checks exceptions immediately after a rule-of-thumb",
    "Tests edge cases first, then integrates the clarification",
    "Gives compact but conceptually relevant answers"
  ],
  "successful_strategies": [
    "Affirm then refine",
    "Use simple native-vs-ARIA contrasts",
    "Affirm the correct core answer, then refine with a concrete edge-case clarification",
    "Ask what native HTML already provides",
    "Use a familiar element before contrasting with ARIA alternatives"
  ],
  "updated_at": "datetime.datetime(2026, 4, 8, 15, 31, 10, 352273, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

---

### Turn 4: exploration → readiness_check
**Tutor time**: 22.47s | **Student agent time**: 2.33s | **Turns on obj**: 3 → 4

**Student**:
> If native HTML already does it, don’t add ARIA there at all? I think the rule is basically “use ARIA only when you can’t use a proper HTML element,” but I’m not sure if there’s more to it.

**Tutor**:
> Yes — that’s the main rule. If a native HTML element can do the job, prefer it and don’t add ARIA just to replace it.

The extra nuance is that “can do the job” includes both meaning and built-in behavior, not just how it looks. CSS can change the appearance, but it doesn’t make the native element stop being a button, link, or input.

So here’s the next check: if you see `<div role="button">` with click behavior, what makes it different from a real `<button>` in a way that matters to this rule?

<details><summary>WebSocket Events (6 non-token)</summary>

```json
[
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Analyzing your response...",
    "_ts": "2026-04-08T15:31:11.866276"
  },
  {
    "type": "stage",
    "stage": "composing",
    "detail": "Generating response (exploration)...",
    "_ts": "2026-04-08T15:31:31.047541"
  },
  {
    "type": "stream_start",
    "_ts": "2026-04-08T15:31:33.205405"
  },
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Updating learning state...",
    "_ts": "2026-04-08T15:31:34.286717"
  },
  {
    "type": "stage_update",
    "stage": "readiness_check",
    "objective": "Apply the five rules for using ARIA correctly",
    "summary": "Student stated the prefer-native rule in practical terms and justified it from native semantics rather than recall.",
    "_ts": "2026-04-08T15:31:34.302284"
  },
  {
    "type": "stream_end",
    "metadata": {
      "session_id": "guided-test-152804",
      "stage": "readiness_check",
      "stage_advanced": true,
      "assessment": {}
    },
    "_ts": "2026-04-08T15:31:34.302306"
  }
]
```
</details>

**Lesson State**: active=`accessible_name_for_interactive_elements`
  `aria_as_supplement` [done], `native_html_semantics` [done], `prefer_native_html` [done], `recognize_unnecessary_aria` [done], `accessible_name_for_interactive_elements` [todo], `keyboard_support_for_custom_controls` [todo], `presentation_none_misuse` [todo], `preserve_native_semantics` [todo], `diagnose_violated_rule` [todo], `revise_to_follow_rules` [todo], `handle_borderline_cases` [todo], `justify_rule_based_decisions` [todo]

**Mastery**: level=`in_progress` confidence=?

<details><summary>Objective Memory</summary>

```json
{
  "student_id": "test-conv-152804",
  "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
  "summary": "Student can now state Rule 1 in practical terms: prefer native HTML and use ARIA only when native HTML cannot provide the needed semantics.",
  "demonstrated_skills": [
    "Recognizes ARIA as supplemental rather than default",
    "Spots redundant ARIA on native button",
    "Connects native element to built-in behavior",
    "Explains what native HTML already provides",
    "Distinguishes native semantics from ARIA metadata",
    "Uses button example to justify why redundant ARIA is unnecessary",
    "States the prefer-native rule in plain language",
    "Justifies redundant ARIA on native button",
    "Connects Rule 1 to native role, keyboard support, focusability, and naming",
    "Applies the rule despite unusual visual styling"
  ],
  "active_gaps": [
    "Has not yet explained what native HTML already provides",
    "Has not yet applied the idea to examples",
    "Needs confirmation that CSS styling does not alter native semantics",
    "Has not yet contrasted native semantics and ARIA in broader examples",
    "Has not yet applied Rule 1 across contrasting native vs custom examples",
    "Has not yet mapped judgments to the named ARIA rules",
    "Has not yet classified multiple contrasting examples",
    "Has not yet mapped flawed examples to specific ARIA rule violations beyond Rule 1"
  ],
  "next_focus": "Use contrastive examples to recognize unnecessary, redundant, or harmful ARIA and justify the rule used.",
  "updated_at": "datetime.datetime(2026, 4, 8, 15, 31, 34, 295226, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

<details><summary>Learner Memory</summary>

```json
{
  "student_id": "test-conv-152804",
  "summary": "Learner can generalize after a concrete example but still asks for confirmation before locking in the rule.",
  "strengths": [
    "Comes in with relevant prior awareness",
    "States uncertainty clearly",
    "Makes correct tentative judgments",
    "Surfaces uncertainty explicitly",
    "Can articulate multiple built-in semantics once prompted",
    "Builds from examples to principle",
    "Reasons concretely about behavior and naming",
    "Builds correct rule statements from examples",
    "Uses causal reasoning, not just recall",
    "Checks edge cases productively"
  ],
  "support_needs": [
    "Needs crisp confirmation plus refinement of partial mental models",
    "Needs example-based contrast to stabilize understanding",
    "Needs crisp clarification on edge cases before generalizing rules",
    "Needs continued example-based application to stabilize rule use",
    "Benefits from explicit connection between examples and named rules",
    "Brief confirmation when turning an example into a named rule",
    "More contrastive examples to stabilize transfer"
  ],
  "tendencies": [
    "Uses tentative phrasing when unsure",
    "Engages readily at the start of a topic",
    "Checks exceptions immediately after a rule-of-thumb",
    "Tests edge cases first, then integrates the clarification",
    "Gives compact but conceptually relevant answers",
    "Frames correct ideas tentatively",
    "Asks whether there is an exception or extra nuance"
  ],
  "successful_strategies": [
    "Affirm then refine",
    "Use simple native-vs-ARIA contrasts",
    "Affirm the correct core answer, then refine with a concrete edge-case clarification",
    "Ask what native HTML already provides",
    "Use a familiar element before contrasting with ARIA alternatives",
    "Confirm the core rule, then test it on contrasting markup examples",
    "Tie the example back to the named ARIA rule explicitly"
  ],
  "updated_at": "datetime.datetime(2026, 4, 8, 15, 31, 34, 296774, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

---

### Turn 5: readiness_check → mini_assessment
**Tutor time**: 17.24s | **Student agent time**: 1.66s | **Turns on obj**: 4 → 5

**Student**:
> A `<div role="button">` only gets the button label/role stuff from ARIA, but it still doesn’t get the native keyboard behavior or focus handling automatically like a real `<button>` does. So it’s more work and easier to mess up.

**Tutor**:
> Yes — that’s the key contrast. A `div` with `role="button"` can be made to announce as a button, but it does not automatically become a real button with the native behavior that comes for free with `<button>`.

So your rule-of-thumb is right: use native HTML when it can do the job, and treat ARIA as a fallback for cases where native HTML cannot express the needed meaning or behavior. Can you classify this one: `<span aria-label="Save">Save</span>` — unnecessary, redundant, or needed?

<details><summary>WebSocket Events (6 non-token)</summary>

```json
[
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Analyzing your response...",
    "_ts": "2026-04-08T15:31:36.676196"
  },
  {
    "type": "stage",
    "stage": "composing",
    "detail": "Generating response (readiness_check)...",
    "_ts": "2026-04-08T15:31:50.957900"
  },
  {
    "type": "stream_start",
    "_ts": "2026-04-08T15:31:52.830726"
  },
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Updating learning state...",
    "_ts": "2026-04-08T15:31:53.833862"
  },
  {
    "type": "stage_update",
    "stage": "mini_assessment",
    "objective": "Apply the five rules for using ARIA correctly",
    "summary": "Student gave comparative and causal reasoning: ARIA adds role/label semantics but not native keyboard/focus behavior, so a div button is riskier than a real button.",
    "_ts": "2026-04-08T15:31:53.877986"
  },
  {
    "type": "stream_end",
    "metadata": {
      "session_id": "guided-test-152804",
      "stage": "mini_assessment",
      "stage_advanced": true,
      "assessment": {}
    },
    "_ts": "2026-04-08T15:31:53.878020"
  }
]
```
</details>

**Lesson State**: active=`accessible_name_for_interactive_elements`
  `aria_as_supplement` [done], `native_html_semantics` [done], `prefer_native_html` [done], `recognize_unnecessary_aria` [done], `accessible_name_for_interactive_elements` [todo], `keyboard_support_for_custom_controls` [todo], `presentation_none_misuse` [todo], `preserve_native_semantics` [todo], `diagnose_violated_rule` [todo], `revise_to_follow_rules` [todo], `handle_borderline_cases` [todo], `justify_rule_based_decisions` [todo]

**Mastery**: level=`in_progress` confidence=?

<details><summary>Objective Memory</summary>

```json
{
  "student_id": "test-conv-152804",
  "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
  "summary": "Student can now compare a native button to a div with role=button and explain why the native element is preferred.",
  "demonstrated_skills": [
    "Recognizes ARIA as supplemental rather than default",
    "Spots redundant ARIA on native button",
    "Connects native element to built-in behavior",
    "Explains what native HTML already provides",
    "Distinguishes native semantics from ARIA metadata",
    "Uses button example to justify why redundant ARIA is unnecessary",
    "States the prefer-native rule in plain language",
    "Justifies redundant ARIA on native button",
    "Connects Rule 1 to native role, keyboard support, focusability, and naming",
    "Applies the rule despite unusual visual styling",
    "Explains that ARIA can add semantics but not native behavior",
    "Contrasts native keyboard/focus support with custom ARIA controls",
    "Justifies Rule 1 with practical implementation risk",
    "Recognizes redundant ARIA on native controls"
  ],
  "active_gaps": [
    "Has not yet explained what native HTML already provides",
    "Has not yet applied the idea to examples",
    "Needs confirmation that CSS styling does not alter native semantics",
    "Has not yet contrasted native semantics and ARIA in broader examples",
    "Has not yet applied Rule 1 across contrasting native vs custom examples",
    "Has not yet mapped judgments to the named ARIA rules",
    "Has not yet classified multiple contrasting examples",
    "Has not yet mapped flawed examples to specific ARIA rule violations beyond Rule 1",
    "Has not yet classified examples across the remaining ARIA rules",
    "Has not yet revise flawed examples using specific rule labels"
  ],
  "next_focus": "Give mixed examples that require naming the violated rule and deciding whether ARIA is redundant, harmful, or necessary.",
  "updated_at": "datetime.datetime(2026, 4, 8, 15, 31, 53, 866886, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

<details><summary>Learner Memory</summary>

```json
{
  "student_id": "test-conv-152804",
  "summary": "Learner reasons well from contrasts and can explain practical consequences, not just repeat the rule.",
  "strengths": [
    "Comes in with relevant prior awareness",
    "States uncertainty clearly",
    "Makes correct tentative judgments",
    "Surfaces uncertainty explicitly",
    "Can articulate multiple built-in semantics once prompted",
    "Builds from examples to principle",
    "Reasons concretely about behavior and naming",
    "Builds correct rule statements from examples",
    "Uses causal reasoning, not just recall",
    "Checks edge cases productively",
    "Uses causal reasoning",
    "Connects semantics to behavior",
    "Explains tradeoffs in implementation terms"
  ],
  "support_needs": [
    "Needs crisp confirmation plus refinement of partial mental models",
    "Needs example-based contrast to stabilize understanding",
    "Needs crisp clarification on edge cases before generalizing rules",
    "Needs continued example-based application to stabilize rule use",
    "Benefits from explicit connection between examples and named rules",
    "Brief confirmation when turning an example into a named rule",
    "More contrastive examples to stabilize transfer",
    "Needs brief confirmation before broader generalization across all rules"
  ],
  "tendencies": [
    "Uses tentative phrasing when unsure",
    "Engages readily at the start of a topic",
    "Checks exceptions immediately after a rule-of-thumb",
    "Tests edge cases first, then integrates the clarification",
    "Gives compact but conceptually relevant answers",
    "Frames correct ideas tentatively",
    "Asks whether there is an exception or extra nuance",
    "Responds strongly to native-vs-custom comparisons",
    "Frames answers around risk and extra implementation work"
  ],
  "successful_strategies": [
    "Affirm then refine",
    "Use simple native-vs-ARIA contrasts",
    "Affirm the correct core answer, then refine with a concrete edge-case clarification",
    "Ask what native HTML already provides",
    "Use a familiar element before contrasting with ARIA alternatives",
    "Confirm the core rule, then test it on contrasting markup examples",
    "Tie the example back to the named ARIA rule explicitly",
    "Use contrastive markup examples",
    "Ask what native HTML gives automatically"
  ],
  "updated_at": "datetime.datetime(2026, 4, 8, 15, 31, 53, 868127, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

---

### Turn 6: mini_assessment → mini_assessment
**Tutor time**: 19.46s | **Student agent time**: 1.57s | **Turns on obj**: 5 → 5

**Student**:
> Hmm, I think that’s redundant too, because the text already says “Save,” so `aria-label` is repeating it. Unless maybe the visible text is something weird and the label is different?

**Tutor**:
> You’re right that the text “Save” already gives a label, so in that sense `aria-label` would be redundant. The bigger issue, though, is that this is just a plain `span`: it isn’t an interactive control, so it doesn’t need an accessible name at all. That means the ARIA is unnecessary here, not just repetitive.

If we changed it to `<button aria-label="Save">Save</button>`, would the `aria-label` still be unnecessary, or would it serve a different purpose?

<details><summary>WebSocket Events (5 non-token)</summary>

```json
[
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Evaluating your assessment answer...",
    "_ts": "2026-04-08T15:31:55.590133"
  },
  {
    "type": "assessment_score",
    "asked": 1,
    "correct": 0,
    "total": 3,
    "passed": null,
    "_ts": "2026-04-08T15:32:11.878724"
  },
  {
    "type": "stage",
    "stage": "composing",
    "detail": "Generating response (mini_assessment)...",
    "_ts": "2026-04-08T15:32:11.912059"
  },
  {
    "type": "stream_start",
    "_ts": "2026-04-08T15:32:14.043056"
  },
  {
    "type": "stream_end",
    "metadata": {
      "session_id": "guided-test-152804",
      "stage": "mini_assessment",
      "stage_advanced": false,
      "assessment": {
        "recorded": true,
        "progress": {
          "asked": 1,
          "correct": 0,
          "total": 3
        },
        "completed": false
      }
    },
    "_ts": "2026-04-08T15:32:15.010768"
  }
]
```
</details>

**Lesson State**: active=`accessible_name_for_interactive_elements`
  `aria_as_supplement` [done], `native_html_semantics` [done], `prefer_native_html` [done], `recognize_unnecessary_aria` [done], `accessible_name_for_interactive_elements` [todo], `keyboard_support_for_custom_controls` [todo], `presentation_none_misuse` [todo], `preserve_native_semantics` [todo], `diagnose_violated_rule` [todo], `revise_to_follow_rules` [todo], `handle_borderline_cases` [todo], `justify_rule_based_decisions` [todo]

**Active Misconceptions** (2):
- [active] May overapply accessible-name reasoning to non-interactive generic elements
- [active] May treat duplicated aria-label as merely redundant without first asking whether the element needs ARIA at all

**Mastery**: level=`in_progress` confidence=?

<details><summary>Objective Memory</summary>

```json
{
  "student_id": "test-conv-152804",
  "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
  "summary": "Student correctly flags repeated text as redundant, but did not identify that aria-label on a plain span is unnecessary because the element is not an interactive control.",
  "demonstrated_skills": [
    "Recognizes ARIA as supplemental rather than default",
    "Spots redundant ARIA on native button",
    "Connects native element to built-in behavior",
    "Explains what native HTML already provides",
    "Distinguishes native semantics from ARIA metadata",
    "Uses button example to justify why redundant ARIA is unnecessary",
    "States the prefer-native rule in plain language",
    "Justifies redundant ARIA on native button",
    "Connects Rule 1 to native role, keyboard support, focusability, and naming",
    "Applies the rule despite unusual visual styling",
    "Explains that ARIA can add semantics but not native behavior",
    "Contrasts native keyboard/focus support with custom ARIA controls",
    "Justifies Rule 1 with practical implementation risk",
    "Recognizes redundant ARIA on native controls",
    "Recognizes when aria-label can duplicate visible text",
    "Applies prior rule-of-thumb that ARIA should not be added automatically"
  ],
  "active_gaps": [
    "Has not yet explained what native HTML already provides",
    "Has not yet applied the idea to examples",
    "Needs confirmation that CSS styling does not alter native semantics",
    "Has not yet contrasted native semantics and ARIA in broader examples",
    "Has not yet applied Rule 1 across contrasting native vs custom examples",
    "Has not yet mapped judgments to the named ARIA rules",
    "Has not yet classified multiple contrasting examples",
    "Has not yet mapped flawed examples to specific ARIA rule violations beyond Rule 1",
    "Has not yet classified examples across the remaining ARIA rules",
    "Has not yet revise flawed examples using specific rule labels",
    "Needs to distinguish unnecessary ARIA from redundant ARIA in mixed examples",
    "Needs firmer application of accessible-name requirements only to interactive elements",
    "Needs practice classifying examples by rule violated"
  ],
  "next_focus": "Use mixed examples to decide first whether ARIA is needed at all, especially for non-interactive elements versus controls.",
  "updated_at": "datetime.datetime(2026, 4, 8, 15, 32, 11, 872226, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

<details><summary>Learner Memory</summary>

```json
{
  "student_id": "test-conv-152804",
  "summary": "Learner gave a thoughtful but partial classification, showing caution and awareness of edge cases.",
  "strengths": [
    "Comes in with relevant prior awareness",
    "States uncertainty clearly",
    "Makes correct tentative judgments",
    "Surfaces uncertainty explicitly",
    "Can articulate multiple built-in semantics once prompted",
    "Builds from examples to principle",
    "Reasons concretely about behavior and naming",
    "Builds correct rule statements from examples",
    "Uses causal reasoning, not just recall",
    "Checks edge cases productively",
    "Uses causal reasoning",
    "Connects semantics to behavior",
    "Explains tradeoffs in implementation terms",
    "Spots duplicate labeling patterns",
    "Reasoned aloud instead of guessing"
  ],
  "support_needs": [
    "Needs crisp confirmation plus refinement of partial mental models",
    "Needs example-based contrast to stabilize understanding",
    "Needs crisp clarification on edge cases before generalizing rules",
    "Needs continued example-based application to stabilize rule use",
    "Benefits from explicit connection between examples and named rules",
    "Brief confirmation when turning an example into a named rule",
    "More contrastive examples to stabilize transfer",
    "Needs brief confirmation before broader generalization across all rules",
    "Needs help checking element purpose before evaluating ARIA naming",
    "Needs clearer distinction between unnecessary and redundant ARIA"
  ],
  "tendencies": [
    "Uses tentative phrasing when unsure",
    "Engages readily at the start of a topic",
    "Checks exceptions immediately after a rule-of-thumb",
    "Tests edge cases first, then integrates the clarification",
    "Gives compact but conceptually relevant answers",
    "Frames correct ideas tentatively",
    "Asks whether there is an exception or extra nuance",
    "Responds strongly to native-vs-custom comparisons",
    "Frames answers around risk and extra implementation work",
    "Adds exception cases before settling on the main classification"
  ],
  "successful_strategies": [
    "Affirm then refine",
    "Use simple native-vs-ARIA contrasts",
    "Affirm the correct core answer, then refine with a concrete edge-case clarification",
    "Ask what native HTML already provides",
    "Use a familiar element before contrasting with ARIA alternatives",
    "Confirm the core rule, then test it on contrasting markup examples",
    "Tie the example back to the named ARIA rule explicitly",
    "Use contrastive markup examples",
    "Ask what native HTML gives automatically",
    "Present simple mixed examples and ask first: is this element interactive?",
    "Tie each example to the specific ARIA rule being applied"
  ],
  "updated_at": "datetime.datetime(2026, 4, 8, 15, 32, 11, 873982, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

---

### Turn 7: mini_assessment → mini_assessment
**Tutor time**: 11.38s | **Student agent time**: 1.75s | **Turns on obj**: 5 → 5

**Student**:
> I think it’d still be unnecessary if the button text already says “Save,” since that’s already its accessible name. Maybe `aria-label` would only make sense if the visible text was unclear or just an icon?

**Tutor**:
> Correct. On a real `<button>`, visible text like “Save” already provides the accessible name, so `aria-label="Save"` is usually redundant. It becomes useful when the visible content doesn’t clearly name the control, like an icon-only button.

Here’s the next one: `<button><svg aria-hidden="true">...</svg></button>` — does this need an accessible name, and if so, how would you provide it?

<details><summary>WebSocket Events (5 non-token)</summary>

```json
[
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Evaluating your assessment answer...",
    "_ts": "2026-04-08T15:32:16.628018"
  },
  {
    "type": "assessment_score",
    "asked": 2,
    "correct": 1,
    "total": 3,
    "passed": null,
    "_ts": "2026-04-08T15:32:25.340358"
  },
  {
    "type": "stage",
    "stage": "composing",
    "detail": "Generating response (mini_assessment)...",
    "_ts": "2026-04-08T15:32:25.379069"
  },
  {
    "type": "stream_start",
    "_ts": "2026-04-08T15:32:27.168413"
  },
  {
    "type": "stream_end",
    "metadata": {
      "session_id": "guided-test-152804",
      "stage": "mini_assessment",
      "stage_advanced": false,
      "assessment": {
        "recorded": true,
        "progress": {
          "asked": 2,
          "correct": 1,
          "total": 3
        },
        "completed": false
      }
    },
    "_ts": "2026-04-08T15:32:27.975987"
  }
]
```
</details>

**Lesson State**: active=`accessible_name_for_interactive_elements`
  `aria_as_supplement` [done], `native_html_semantics` [done], `prefer_native_html` [done], `recognize_unnecessary_aria` [done], `accessible_name_for_interactive_elements` [todo], `keyboard_support_for_custom_controls` [todo], `presentation_none_misuse` [todo], `preserve_native_semantics` [todo], `diagnose_violated_rule` [todo], `revise_to_follow_rules` [todo], `handle_borderline_cases` [todo], `justify_rule_based_decisions` [todo]

**Active Misconceptions** (2):
- [active] May overapply accessible-name reasoning to non-interactive generic elements
- [active] May treat duplicated aria-label as merely redundant without first asking whether the element needs ARIA at all

**Mastery**: level=`in_progress` confidence=?

<details><summary>Objective Memory</summary>

```json
{
  "student_id": "test-conv-152804",
  "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
  "summary": "Student correctly applied accessible-name reasoning to a native button and recognized when aria-label is unnecessary versus useful.",
  "demonstrated_skills": [
    "Recognizes ARIA as supplemental rather than default",
    "Spots redundant ARIA on native button",
    "Connects native element to built-in behavior",
    "Explains what native HTML already provides",
    "Distinguishes native semantics from ARIA metadata",
    "Uses button example to justify why redundant ARIA is unnecessary",
    "States the prefer-native rule in plain language",
    "Justifies redundant ARIA on native button",
    "Connects Rule 1 to native role, keyboard support, focusability, and naming",
    "Applies the rule despite unusual visual styling",
    "Explains that ARIA can add semantics but not native behavior",
    "Contrasts native keyboard/focus support with custom ARIA controls",
    "Justifies Rule 1 with practical implementation risk",
    "Recognizes redundant ARIA on native controls",
    "Recognizes when aria-label can duplicate visible text",
    "Applies prior rule-of-thumb that ARIA should not be added automatically",
    "Identifies that visible button text provides the accessible name",
    "Recognizes redundant aria-label on a native button",
    "Distinguishes cases where aria-label may be needed, such as icon-only controls"
  ],
  "active_gaps": [
    "Has not yet explained what native HTML already provides",
    "Has not yet applied the idea to examples",
    "Needs confirmation that CSS styling does not alter native semantics",
    "Has not yet contrasted native semantics and ARIA in broader examples",
    "Has not yet applied Rule 1 across contrasting native vs custom examples",
    "Has not yet mapped judgments to the named ARIA rules",
    "Has not yet classified multiple contrasting examples",
    "Has not yet mapped flawed examples to specific ARIA rule violations beyond Rule 1",
    "Has not yet classified examples across the remaining ARIA rules",
    "Has not yet revise flawed examples using specific rule labels",
    "Needs to distinguish unnecessary ARIA from redundant ARIA in mixed examples",
    "Needs firmer application of accessible-name requirements only to interactive elements",
    "Needs practice classifying examples by rule violated",
    "Still needs broader rule classification across mixed examples",
    "Has not yet been assessed on keyboard requirements for custom ARIA widgets"
  ],
  "next_focus": "Check mixed examples for which ARIA rule is violated and when ARIA is needed versus redundant.",
  "updated_at": "datetime.datetime(2026, 4, 8, 15, 32, 25, 328003, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

<details><summary>Learner Memory</summary>

```json
{
  "student_id": "test-conv-152804",
  "summary": "Learner gave a concise, conceptually correct answer with an appropriate exception.",
  "strengths": [
    "Comes in with relevant prior awareness",
    "States uncertainty clearly",
    "Makes correct tentative judgments",
    "Surfaces uncertainty explicitly",
    "Can articulate multiple built-in semantics once prompted",
    "Builds from examples to principle",
    "Reasons concretely about behavior and naming",
    "Builds correct rule statements from examples",
    "Uses causal reasoning, not just recall",
    "Checks edge cases productively",
    "Uses causal reasoning",
    "Connects semantics to behavior",
    "Explains tradeoffs in implementation terms",
    "Spots duplicate labeling patterns",
    "Reasoned aloud instead of guessing",
    "Applies accessible-name concept correctly to native buttons",
    "Recognizes redundancy in ARIA usage",
    "Uses edge cases productively without losing the main rule"
  ],
  "support_needs": [
    "Needs crisp confirmation plus refinement of partial mental models",
    "Needs example-based contrast to stabilize understanding",
    "Needs crisp clarification on edge cases before generalizing rules",
    "Needs continued example-based application to stabilize rule use",
    "Benefits from explicit connection between examples and named rules",
    "Brief confirmation when turning an example into a named rule",
    "More contrastive examples to stabilize transfer",
    "Needs brief confirmation before broader generalization across all rules",
    "Needs help checking element purpose before evaluating ARIA naming",
    "Needs clearer distinction between unnecessary and redundant ARIA",
    "Needs continued practice classifying examples by specific ARIA rule",
    "Should reinforce distinction between unnecessary ARIA and redundant ARIA across element types"
  ],
  "tendencies": [
    "Uses tentative phrasing when unsure",
    "Engages readily at the start of a topic",
    "Checks exceptions immediately after a rule-of-thumb",
    "Tests edge cases first, then integrates the clarification",
    "Gives compact but conceptually relevant answers",
    "Frames correct ideas tentatively",
    "Asks whether there is an exception or extra nuance",
    "Responds strongly to native-vs-custom comparisons",
    "Frames answers around risk and extra implementation work",
    "Adds exception cases before settling on the main classification",
    "Adds sensible exceptions after stating the main answer"
  ],
  "successful_strategies": [
    "Affirm then refine",
    "Use simple native-vs-ARIA contrasts",
    "Affirm the correct core answer, then refine with a concrete edge-case clarification",
    "Ask what native HTML already provides",
    "Use a familiar element before contrasting with ARIA alternatives",
    "Confirm the core rule, then test it on contrasting markup examples",
    "Tie the example back to the named ARIA rule explicitly",
    "Use contrastive markup examples",
    "Ask what native HTML gives automatically",
    "Present simple mixed examples and ask first: is this element interactive?",
    "Tie each example to the specific ARIA rule being applied",
    "Contrast visible text buttons with icon-only buttons",
    "Ask whether the element already has an accessible name from native HTML"
  ],
  "updated_at": "datetime.datetime(2026, 4, 8, 15, 32, 25, 331128, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

---

### Turn 8: mini_assessment → final_assessment
**Tutor time**: 12.92s | **Student agent time**: 1.74s | **Turns on obj**: 5 → 5

**Student**:
> Yes, it still needs an accessible name, because the SVG is hidden from assistive tech. I’d probably give the button an `aria-label` like `aria-label="Search"` or whatever the icon means.

**Tutor**:
> Exactly — the button still needs a name, and `aria-label="Search"` is a valid way to give it one when the icon itself is hidden.

The important distinction is: the `svg` is not what gets named here; the `<button>` is the interactive element that must have the accessible name. What do you think would be the problem if we left the button unlabeled and assumed the icon alone was enough?

<details><summary>WebSocket Events (6 non-token)</summary>

```json
[
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Evaluating your assessment answer...",
    "_ts": "2026-04-08T15:32:29.769898"
  },
  {
    "type": "assessment_score",
    "asked": 3,
    "correct": 2,
    "total": 3,
    "passed": true,
    "_ts": "2026-04-08T15:32:40.134734"
  },
  {
    "type": "stage_update",
    "stage": "final_assessment",
    "objective": "Apply the five rules for using ARIA correctly",
    "summary": "Correctly identified missing accessible name and a valid way to provide it on an icon-only button.",
    "_ts": "2026-04-08T15:32:40.135839"
  },
  {
    "type": "stage",
    "stage": "composing",
    "detail": "Generating response (final_assessment)...",
    "_ts": "2026-04-08T15:32:40.166937"
  },
  {
    "type": "stream_start",
    "_ts": "2026-04-08T15:32:41.897217"
  },
  {
    "type": "stream_end",
    "metadata": {
      "session_id": "guided-test-152804",
      "stage": "final_assessment",
      "stage_advanced": true,
      "assessment": {
        "recorded": true,
        "progress": {
          "asked": 3,
          "correct": 2,
          "total": 3
        },
        "completed": true,
        "passed": true,
        "next_stage": "final_assessment"
      }
    },
    "_ts": "2026-04-08T15:32:42.654395"
  }
]
```
</details>

**Lesson State**: active=`accessible_name_for_interactive_elements`
  `aria_as_supplement` [done], `native_html_semantics` [done], `prefer_native_html` [done], `recognize_unnecessary_aria` [done], `accessible_name_for_interactive_elements` [todo], `keyboard_support_for_custom_controls` [todo], `presentation_none_misuse` [todo], `preserve_native_semantics` [todo], `diagnose_violated_rule` [todo], `revise_to_follow_rules` [todo], `handle_borderline_cases` [todo], `justify_rule_based_decisions` [todo]

**Active Misconceptions** (2):
- [active] May overapply accessible-name reasoning to non-interactive generic elements
- [active] May treat duplicated aria-label as merely redundant without first asking whether the element needs ARIA at all

**Mastery**: level=`in_progress` confidence=?

<details><summary>Objective Memory</summary>

```json
{
  "student_id": "test-conv-152804",
  "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
  "summary": "Student correctly applied Rule 5 to an icon-only button and chose a valid naming method.",
  "demonstrated_skills": [
    "Recognizes ARIA as supplemental rather than default",
    "Spots redundant ARIA on native button",
    "Connects native element to built-in behavior",
    "Explains what native HTML already provides",
    "Distinguishes native semantics from ARIA metadata",
    "Uses button example to justify why redundant ARIA is unnecessary",
    "States the prefer-native rule in plain language",
    "Justifies redundant ARIA on native button",
    "Connects Rule 1 to native role, keyboard support, focusability, and naming",
    "Applies the rule despite unusual visual styling",
    "Explains that ARIA can add semantics but not native behavior",
    "Contrasts native keyboard/focus support with custom ARIA controls",
    "Justifies Rule 1 with practical implementation risk",
    "Recognizes redundant ARIA on native controls",
    "Recognizes when aria-label can duplicate visible text",
    "Applies prior rule-of-thumb that ARIA should not be added automatically",
    "Identifies that visible button text provides the accessible name",
    "Recognizes redundant aria-label on a native button",
    "Distinguishes cases where aria-label may be needed, such as icon-only controls",
    "Recognizes that interactive elements need an accessible name",
    "Identifies that aria-hidden icon content does not name a button",
    "Chooses aria-label appropriately for an icon-only native button",
    "Distinguishes when ARIA naming is useful versus redundant"
  ],
  "active_gaps": [
    "Has not yet explained what native HTML already provides",
    "Has not yet applied the idea to examples",
    "Needs confirmation that CSS styling does not alter native semantics",
    "Has not yet contrasted native semantics and ARIA in broader examples",
    "Has not yet applied Rule 1 across contrasting native vs custom examples",
    "Has not yet mapped judgments to the named ARIA rules",
    "Has not yet classified multiple contrasting examples",
    "Has not yet mapped flawed examples to specific ARIA rule violations beyond Rule 1",
    "Has not yet classified examples across the remaining ARIA rules",
    "Has not yet revise flawed examples using specific rule labels",
    "Needs to distinguish unnecessary ARIA from redundant ARIA in mixed examples",
    "Needs firmer application of accessible-name requirements only to interactive elements",
    "Needs practice classifying examples by rule violated",
    "Still needs broader rule classification across mixed examples",
    "Has not yet been assessed on keyboard requirements for custom ARIA widgets",
    "Has not yet classified mixed examples across all five ARIA rules",
    "Has not yet demonstrated Rule 3 keyboard requirements for custom controls",
    "Has not yet demonstrated Rule 4 on presentation/none misuse",
    "Has not yet demonstrated Rule 2 about changing native semantics"
  ],
  "next_focus": "Classify mixed examples by which ARIA rule is violated and when ARIA is needed, redundant, or harmful.",
  "updated_at": "datetime.datetime(2026, 4, 8, 15, 32, 40, 125532, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

<details><summary>Learner Memory</summary>

```json
{
  "student_id": "test-conv-152804",
  "summary": "Learner gave a concise, accurate answer about naming an icon-only button.",
  "strengths": [
    "Comes in with relevant prior awareness",
    "States uncertainty clearly",
    "Makes correct tentative judgments",
    "Surfaces uncertainty explicitly",
    "Can articulate multiple built-in semantics once prompted",
    "Builds from examples to principle",
    "Reasons concretely about behavior and naming",
    "Builds correct rule statements from examples",
    "Uses causal reasoning, not just recall",
    "Checks edge cases productively",
    "Uses causal reasoning",
    "Connects semantics to behavior",
    "Explains tradeoffs in implementation terms",
    "Spots duplicate labeling patterns",
    "Reasoned aloud instead of guessing",
    "Applies accessible-name concept correctly to native buttons",
    "Recognizes redundancy in ARIA usage",
    "Uses edge cases productively without losing the main rule",
    "Applies accessible-name reasoning correctly",
    "Selects practical fixes",
    "Distinguishes hidden decorative content from usable labels"
  ],
  "support_needs": [
    "Needs crisp confirmation plus refinement of partial mental models",
    "Needs example-based contrast to stabilize understanding",
    "Needs crisp clarification on edge cases before generalizing rules",
    "Needs continued example-based application to stabilize rule use",
    "Benefits from explicit connection between examples and named rules",
    "Brief confirmation when turning an example into a named rule",
    "More contrastive examples to stabilize transfer",
    "Needs brief confirmation before broader generalization across all rules",
    "Needs help checking element purpose before evaluating ARIA naming",
    "Needs clearer distinction between unnecessary and redundant ARIA",
    "Needs continued practice classifying examples by specific ARIA rule",
    "Should reinforce distinction between unnecessary ARIA and redundant ARIA across element types",
    "Needs broader rule classification practice beyond naming cases"
  ],
  "tendencies": [
    "Uses tentative phrasing when unsure",
    "Engages readily at the start of a topic",
    "Checks exceptions immediately after a rule-of-thumb",
    "Tests edge cases first, then integrates the clarification",
    "Gives compact but conceptually relevant answers",
    "Frames correct ideas tentatively",
    "Asks whether there is an exception or extra nuance",
    "Responds strongly to native-vs-custom comparisons",
    "Frames answers around risk and extra implementation work",
    "Adds exception cases before settling on the main classification",
    "Adds sensible exceptions after stating the main answer",
    "Answers compactly but with correct core reasoning",
    "Uses concrete examples to justify decisions"
  ],
  "successful_strategies": [
    "Affirm then refine",
    "Use simple native-vs-ARIA contrasts",
    "Affirm the correct core answer, then refine with a concrete edge-case clarification",
    "Ask what native HTML already provides",
    "Use a familiar element before contrasting with ARIA alternatives",
    "Confirm the core rule, then test it on contrasting markup examples",
    "Tie the example back to the named ARIA rule explicitly",
    "Use contrastive markup examples",
    "Ask what native HTML gives automatically",
    "Present simple mixed examples and ask first: is this element interactive?",
    "Tie each example to the specific ARIA rule being applied",
    "Contrast visible text buttons with icon-only buttons",
    "Ask whether the element already has an accessible name from native HTML",
    "Use short code examples",
    "Ask whether the control has an accessible name without relying on hidden decorative content",
    "Contrast redundant ARIA with necessary ARIA"
  ],
  "updated_at": "datetime.datetime(2026, 4, 8, 15, 32, 40, 129853, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

---

### Turn 9: final_assessment → final_assessment
**Tutor time**: 12.43s | **Student agent time**: 1.79s | **Turns on obj**: 5 → 5

**Student**:
> Screen readers might just announce it as “button” with no clue what it does, so people wouldn’t know if it’s Search, Close, Menu, etc. That’d make it pretty unusable.

**Tutor**:
> Yes — that’s the core problem. Without an accessible name, the control may be announced only as “button,” which leaves its purpose unclear and makes the control hard to use.

Next one: `<button aria-label="Save">Save</button>` — is the `aria-label` needed here, or is it redundant?

<details><summary>WebSocket Events (5 non-token)</summary>

```json
[
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Evaluating your assessment answer...",
    "_ts": "2026-04-08T15:32:44.435566"
  },
  {
    "type": "assessment_score",
    "asked": 1,
    "correct": 1,
    "total": 5,
    "passed": null,
    "_ts": "2026-04-08T15:32:53.695079"
  },
  {
    "type": "stage",
    "stage": "composing",
    "detail": "Generating response (final_assessment)...",
    "_ts": "2026-04-08T15:32:53.724924"
  },
  {
    "type": "stream_start",
    "_ts": "2026-04-08T15:32:56.249497"
  },
  {
    "type": "stream_end",
    "metadata": {
      "session_id": "guided-test-152804",
      "stage": "final_assessment",
      "stage_advanced": false,
      "assessment": {
        "recorded": true,
        "progress": {
          "asked": 1,
          "correct": 1,
          "total": 5
        },
        "completed": false
      }
    },
    "_ts": "2026-04-08T15:32:56.833116"
  }
]
```
</details>

**Lesson State**: active=`accessible_name_for_interactive_elements`
  `aria_as_supplement` [done], `native_html_semantics` [done], `prefer_native_html` [done], `recognize_unnecessary_aria` [done], `accessible_name_for_interactive_elements` [todo], `keyboard_support_for_custom_controls` [todo], `presentation_none_misuse` [todo], `preserve_native_semantics` [todo], `diagnose_violated_rule` [todo], `revise_to_follow_rules` [todo], `handle_borderline_cases` [todo], `justify_rule_based_decisions` [todo]

**Active Misconceptions** (2):
- [active] May overapply accessible-name reasoning to non-interactive generic elements
- [active] May treat duplicated aria-label as merely redundant without first asking whether the element needs ARIA at all

**Mastery**: level=`in_progress` confidence=?

<details><summary>Objective Memory</summary>

```json
{
  "student_id": "test-conv-152804",
  "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
  "summary": "Student correctly applied Rule 5 by explaining why an icon-only button still needs an accessible name.",
  "demonstrated_skills": [
    "Recognizes ARIA as supplemental rather than default",
    "Spots redundant ARIA on native button",
    "Connects native element to built-in behavior",
    "Explains what native HTML already provides",
    "Distinguishes native semantics from ARIA metadata",
    "Uses button example to justify why redundant ARIA is unnecessary",
    "States the prefer-native rule in plain language",
    "Justifies redundant ARIA on native button",
    "Connects Rule 1 to native role, keyboard support, focusability, and naming",
    "Applies the rule despite unusual visual styling",
    "Explains that ARIA can add semantics but not native behavior",
    "Contrasts native keyboard/focus support with custom ARIA controls",
    "Justifies Rule 1 with practical implementation risk",
    "Recognizes redundant ARIA on native controls",
    "Recognizes when aria-label can duplicate visible text",
    "Applies prior rule-of-thumb that ARIA should not be added automatically",
    "Identifies that visible button text provides the accessible name",
    "Recognizes redundant aria-label on a native button",
    "Distinguishes cases where aria-label may be needed, such as icon-only controls",
    "Recognizes that interactive elements need an accessible name",
    "Identifies that aria-hidden icon content does not name a button",
    "Chooses aria-label appropriately for an icon-only native button",
    "Distinguishes when ARIA naming is useful versus redundant",
    "Explains that the interactive element itself must be named",
    "Identifies the usability impact of an unlabeled button for screen reader users",
    "Applies accessible-name reasoning correctly to icon-only buttons"
  ],
  "active_gaps": [
    "Has not yet explained what native HTML already provides",
    "Has not yet applied the idea to examples",
    "Needs confirmation that CSS styling does not alter native semantics",
    "Has not yet contrasted native semantics and ARIA in broader examples",
    "Has not yet applied Rule 1 across contrasting native vs custom examples",
    "Has not yet mapped judgments to the named ARIA rules",
    "Has not yet classified multiple contrasting examples",
    "Has not yet mapped flawed examples to specific ARIA rule violations beyond Rule 1",
    "Has not yet classified examples across the remaining ARIA rules",
    "Has not yet revise flawed examples using specific rule labels",
    "Needs to distinguish unnecessary ARIA from redundant ARIA in mixed examples",
    "Needs firmer application of accessible-name requirements only to interactive elements",
    "Needs practice classifying examples by rule violated",
    "Still needs broader rule classification across mixed examples",
    "Has not yet been assessed on keyboard requirements for custom ARIA widgets",
    "Has not yet classified mixed examples across all five ARIA rules",
    "Has not yet demonstrated Rule 3 keyboard requirements for custom controls",
    "Has not yet demonstrated Rule 4 on presentation/none misuse",
    "Has not yet demonstrated Rule 2 about changing native semantics",
    "Has not yet classified mixed examples by which ARIA rule is violated",
    "Has not yet demonstrated Rule 3, Rule 4, or Rule 2 in examples"
  ],
  "next_focus": "Check whether the learner can classify examples by rule and distinguish needed, redundant, and harmful ARIA.",
  "updated_at": "datetime.datetime(2026, 4, 8, 15, 32, 53, 687918, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

<details><summary>Learner Memory</summary>

```json
{
  "student_id": "test-conv-152804",
  "summary": "Learner gave a concise, correct explanation of the problem with leaving an icon-only button unlabeled.",
  "strengths": [
    "Comes in with relevant prior awareness",
    "States uncertainty clearly",
    "Makes correct tentative judgments",
    "Surfaces uncertainty explicitly",
    "Can articulate multiple built-in semantics once prompted",
    "Builds from examples to principle",
    "Reasons concretely about behavior and naming",
    "Builds correct rule statements from examples",
    "Uses causal reasoning, not just recall",
    "Checks edge cases productively",
    "Uses causal reasoning",
    "Connects semantics to behavior",
    "Explains tradeoffs in implementation terms",
    "Spots duplicate labeling patterns",
    "Reasoned aloud instead of guessing",
    "Applies accessible-name concept correctly to native buttons",
    "Recognizes redundancy in ARIA usage",
    "Uses edge cases productively without losing the main rule",
    "Applies accessible-name reasoning correctly",
    "Selects practical fixes",
    "Distinguishes hidden decorative content from usable labels",
    "Concise but conceptually accurate reasoning",
    "Connects missing accessible name to real user impact",
    "Applies prior clarification about naming the button, not the icon"
  ],
  "support_needs": [
    "Needs crisp confirmation plus refinement of partial mental models",
    "Needs example-based contrast to stabilize understanding",
    "Needs crisp clarification on edge cases before generalizing rules",
    "Needs continued example-based application to stabilize rule use",
    "Benefits from explicit connection between examples and named rules",
    "Brief confirmation when turning an example into a named rule",
    "More contrastive examples to stabilize transfer",
    "Needs brief confirmation before broader generalization across all rules",
    "Needs help checking element purpose before evaluating ARIA naming",
    "Needs clearer distinction between unnecessary and redundant ARIA",
    "Needs continued practice classifying examples by specific ARIA rule",
    "Should reinforce distinction between unnecessary ARIA and redundant ARIA across element types",
    "Needs broader rule classification practice beyond naming cases",
    "Needs broader practice classifying ARIA misuse across multiple rules"
  ],
  "tendencies": [
    "Uses tentative phrasing when unsure",
    "Engages readily at the start of a topic",
    "Checks exceptions immediately after a rule-of-thumb",
    "Tests edge cases first, then integrates the clarification",
    "Gives compact but conceptually relevant answers",
    "Frames correct ideas tentatively",
    "Asks whether there is an exception or extra nuance",
    "Responds strongly to native-vs-custom comparisons",
    "Frames answers around risk and extra implementation work",
    "Adds exception cases before settling on the main classification",
    "Adds sensible exceptions after stating the main answer",
    "Answers compactly but with correct core reasoning",
    "Uses concrete examples to justify decisions",
    "Gives compact answers",
    "Reasons from practical user impact",
    "Uses tentative phrasing when unsure but lands on correct concepts"
  ],
  "successful_strategies": [
    "Affirm then refine",
    "Use simple native-vs-ARIA contrasts",
    "Affirm the correct core answer, then refine with a concrete edge-case clarification",
    "Ask what native HTML already provides",
    "Use a familiar element before contrasting with ARIA alternatives",
    "Confirm the core rule, then test it on contrasting markup examples",
    "Tie the example back to the named ARIA rule explicitly",
    "Use contrastive markup examples",
    "Ask what native HTML gives automatically",
    "Present simple mixed examples and ask first: is this element interactive?",
    "Tie each example to the specific ARIA rule being applied",
    "Contrast visible text buttons with icon-only buttons",
    "Ask whether the element already has an accessible name from native HTML",
    "Use short code examples",
    "Ask whether the control has an accessible name without relying on hidden decorative content",
    "Contrast redundant ARIA with necessary ARIA",
    "Use concrete button examples",
    "Ask about likely screen reader output",
    "Contrast named vs unnamed interactive controls"
  ],
  "updated_at": "datetime.datetime(2026, 4, 8, 15, 32, 53, 691115, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

---

### Turn 10: final_assessment → final_assessment
**Tutor time**: 12.43s | **Student agent time**: 1.72s | **Turns on obj**: 5 → 5

**Student**:
> Redundant, because the visible text “Save” already gives the button its accessible name. I think it’s okay, but not needed unless we want the label to be different for some reason.

**Tutor**:
> Right — redundant. The visible text already names the button, so adding `aria-label` doesn’t improve anything here and can create a mismatch if the two labels ever diverge.

Next assessment question: `<div role="button">Submit</div>` — does this satisfy the rule about accessible names, and what other check would you want to make before calling it a valid button?

<details><summary>WebSocket Events (5 non-token)</summary>

```json
[
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Evaluating your assessment answer...",
    "_ts": "2026-04-08T15:32:58.673602"
  },
  {
    "type": "assessment_score",
    "asked": 2,
    "correct": 2,
    "total": 5,
    "passed": null,
    "_ts": "2026-04-08T15:33:08.598042"
  },
  {
    "type": "stage",
    "stage": "composing",
    "detail": "Generating response (final_assessment)...",
    "_ts": "2026-04-08T15:33:08.628991"
  },
  {
    "type": "stream_start",
    "_ts": "2026-04-08T15:33:10.388831"
  },
  {
    "type": "stream_end",
    "metadata": {
      "session_id": "guided-test-152804",
      "stage": "final_assessment",
      "stage_advanced": false,
      "assessment": {
        "recorded": true,
        "progress": {
          "asked": 2,
          "correct": 2,
          "total": 5
        },
        "completed": false
      }
    },
    "_ts": "2026-04-08T15:33:11.069139"
  }
]
```
</details>

**Lesson State**: active=`accessible_name_for_interactive_elements`
  `aria_as_supplement` [done], `native_html_semantics` [done], `prefer_native_html` [done], `recognize_unnecessary_aria` [done], `accessible_name_for_interactive_elements` [todo], `keyboard_support_for_custom_controls` [todo], `presentation_none_misuse` [todo], `preserve_native_semantics` [todo], `diagnose_violated_rule` [todo], `revise_to_follow_rules` [todo], `handle_borderline_cases` [todo], `justify_rule_based_decisions` [todo]

**Active Misconceptions** (2):
- [active] May overapply accessible-name reasoning to non-interactive generic elements
- [active] May treat duplicated aria-label as merely redundant without first asking whether the element needs ARIA at all

**Mastery**: level=`in_progress` confidence=?

<details><summary>Objective Memory</summary>

```json
{
  "student_id": "test-conv-152804",
  "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
  "summary": "Student correctly judged that aria-label on a text-labeled native button is redundant.",
  "demonstrated_skills": [
    "Recognizes ARIA as supplemental rather than default",
    "Spots redundant ARIA on native button",
    "Connects native element to built-in behavior",
    "Explains what native HTML already provides",
    "Distinguishes native semantics from ARIA metadata",
    "Uses button example to justify why redundant ARIA is unnecessary",
    "States the prefer-native rule in plain language",
    "Justifies redundant ARIA on native button",
    "Connects Rule 1 to native role, keyboard support, focusability, and naming",
    "Applies the rule despite unusual visual styling",
    "Explains that ARIA can add semantics but not native behavior",
    "Contrasts native keyboard/focus support with custom ARIA controls",
    "Justifies Rule 1 with practical implementation risk",
    "Recognizes redundant ARIA on native controls",
    "Recognizes when aria-label can duplicate visible text",
    "Applies prior rule-of-thumb that ARIA should not be added automatically",
    "Identifies that visible button text provides the accessible name",
    "Recognizes redundant aria-label on a native button",
    "Distinguishes cases where aria-label may be needed, such as icon-only controls",
    "Recognizes that interactive elements need an accessible name",
    "Identifies that aria-hidden icon content does not name a button",
    "Chooses aria-label appropriately for an icon-only native button",
    "Distinguishes when ARIA naming is useful versus redundant",
    "Explains that the interactive element itself must be named",
    "Identifies the usability impact of an unlabeled button for screen reader users",
    "Applies accessible-name reasoning correctly to icon-only buttons",
    "Identifies when ARIA is unnecessary on native controls",
    "Recognizes visible button text as an accessible name source",
    "Distinguishes needed versus redundant aria-label usage"
  ],
  "active_gaps": [
    "Has not yet explained what native HTML already provides",
    "Has not yet applied the idea to examples",
    "Needs confirmation that CSS styling does not alter native semantics",
    "Has not yet contrasted native semantics and ARIA in broader examples",
    "Has not yet applied Rule 1 across contrasting native vs custom examples",
    "Has not yet mapped judgments to the named ARIA rules",
    "Has not yet classified multiple contrasting examples",
    "Has not yet mapped flawed examples to specific ARIA rule violations beyond Rule 1",
    "Has not yet classified examples across the remaining ARIA rules",
    "Has not yet revise flawed examples using specific rule labels",
    "Needs to distinguish unnecessary ARIA from redundant ARIA in mixed examples",
    "Needs firmer application of accessible-name requirements only to interactive elements",
    "Needs practice classifying examples by rule violated",
    "Still needs broader rule classification across mixed examples",
    "Has not yet been assessed on keyboard requirements for custom ARIA widgets",
    "Has not yet classified mixed examples across all five ARIA rules",
    "Has not yet demonstrated Rule 3 keyboard requirements for custom controls",
    "Has not yet demonstrated Rule 4 on presentation/none misuse",
    "Has not yet demonstrated Rule 2 about changing native semantics",
    "Has not yet classified mixed examples by which ARIA rule is violated",
    "Has not yet demonstrated Rule 3, Rule 4, or Rule 2 in examples",
    "Has not yet demonstrated keyboard-support reasoning for custom ARIA controls",
    "Has not yet demonstrated Rule 4 about presentation/none on interactive elements",
    "Has not yet demonstrated Rule 2 about unjustified native semantic overrides"
  ],
  "next_focus": "Check broader rule classification across mixed examples, especially keyboard support and harmful ARIA.",
  "updated_at": "datetime.datetime(2026, 4, 8, 15, 33, 8, 590186, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

<details><summary>Learner Memory</summary>

```json
{
  "student_id": "test-conv-152804",
  "summary": "Learner gave a concise, correct redundancy judgment for aria-label on a text button.",
  "strengths": [
    "Comes in with relevant prior awareness",
    "States uncertainty clearly",
    "Makes correct tentative judgments",
    "Surfaces uncertainty explicitly",
    "Can articulate multiple built-in semantics once prompted",
    "Builds from examples to principle",
    "Reasons concretely about behavior and naming",
    "Builds correct rule statements from examples",
    "Uses causal reasoning, not just recall",
    "Checks edge cases productively",
    "Uses causal reasoning",
    "Connects semantics to behavior",
    "Explains tradeoffs in implementation terms",
    "Spots duplicate labeling patterns",
    "Reasoned aloud instead of guessing",
    "Applies accessible-name concept correctly to native buttons",
    "Recognizes redundancy in ARIA usage",
    "Uses edge cases productively without losing the main rule",
    "Applies accessible-name reasoning correctly",
    "Selects practical fixes",
    "Distinguishes hidden decorative content from usable labels",
    "Concise but conceptually accurate reasoning",
    "Connects missing accessible name to real user impact",
    "Applies prior clarification about naming the button, not the icon",
    "Applies accessible-name reasoning accurately to native buttons",
    "Makes compact, conceptually correct judgments",
    "Can explain why ARIA is unnecessary when HTML already provides the name"
  ],
  "support_needs": [
    "Needs crisp confirmation plus refinement of partial mental models",
    "Needs example-based contrast to stabilize understanding",
    "Needs crisp clarification on edge cases before generalizing rules",
    "Needs continued example-based application to stabilize rule use",
    "Benefits from explicit connection between examples and named rules",
    "Brief confirmation when turning an example into a named rule",
    "More contrastive examples to stabilize transfer",
    "Needs brief confirmation before broader generalization across all rules",
    "Needs help checking element purpose before evaluating ARIA naming",
    "Needs clearer distinction between unnecessary and redundant ARIA",
    "Needs continued practice classifying examples by specific ARIA rule",
    "Should reinforce distinction between unnecessary ARIA and redundant ARIA across element types",
    "Needs broader rule classification practice beyond naming cases",
    "Needs broader practice classifying ARIA misuse across multiple rules",
    "Needs refinement on when differing ARIA labels may be inappropriate despite being possible"
  ],
  "tendencies": [
    "Uses tentative phrasing when unsure",
    "Engages readily at the start of a topic",
    "Checks exceptions immediately after a rule-of-thumb",
    "Tests edge cases first, then integrates the clarification",
    "Gives compact but conceptually relevant answers",
    "Frames correct ideas tentatively",
    "Asks whether there is an exception or extra nuance",
    "Responds strongly to native-vs-custom comparisons",
    "Frames answers around risk and extra implementation work",
    "Adds exception cases before settling on the main classification",
    "Adds sensible exceptions after stating the main answer",
    "Answers compactly but with correct core reasoning",
    "Uses concrete examples to justify decisions",
    "Gives compact answers",
    "Reasons from practical user impact",
    "Uses tentative phrasing when unsure but lands on correct concepts",
    "Answers briefly but with relevant justification",
    "Adds cautious caveats about exceptions"
  ],
  "successful_strategies": [
    "Affirm then refine",
    "Use simple native-vs-ARIA contrasts",
    "Affirm the correct core answer, then refine with a concrete edge-case clarification",
    "Ask what native HTML already provides",
    "Use a familiar element before contrasting with ARIA alternatives",
    "Confirm the core rule, then test it on contrasting markup examples",
    "Tie the example back to the named ARIA rule explicitly",
    "Use contrastive markup examples",
    "Ask what native HTML gives automatically",
    "Present simple mixed examples and ask first: is this element interactive?",
    "Tie each example to the specific ARIA rule being applied",
    "Contrast visible text buttons with icon-only buttons",
    "Ask whether the element already has an accessible name from native HTML",
    "Use short code examples",
    "Ask whether the control has an accessible name without relying on hidden decorative content",
    "Contrast redundant ARIA with necessary ARIA",
    "Use concrete button examples",
    "Ask about likely screen reader output",
    "Contrast named vs unnamed interactive controls",
    "Use simple native button contrasts",
    "Ask whether native HTML already provides the needed name"
  ],
  "updated_at": "datetime.datetime(2026, 4, 8, 15, 33, 8, 594245, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

---

### Turn 11: final_assessment → final_assessment
**Tutor time**: 10.83s | **Student agent time**: 1.69s | **Turns on obj**: 5 → 5

**Student**:
> It has a name because of the text “Submit,” so that part seems okay. But I’d want to check keyboard behavior and focusability too, since a `div` doesn’t get those like a real button does.

**Tutor**:
> Correct. The text gives the `div` an accessible name, but that alone doesn’t make it a valid button — you’d still need to confirm it is focusable and operable from the keyboard, which is part of making an interactive ARIA control usable.

Next assessment question: if you see `<button role="presentation">Delete</button>`, which rule is being violated?

<details><summary>WebSocket Events (5 non-token)</summary>

```json
[
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Evaluating your assessment answer...",
    "_ts": "2026-04-08T15:33:12.830470"
  },
  {
    "type": "assessment_score",
    "asked": 3,
    "correct": 3,
    "total": 5,
    "passed": null,
    "_ts": "2026-04-08T15:33:21.034777"
  },
  {
    "type": "stage",
    "stage": "composing",
    "detail": "Generating response (final_assessment)...",
    "_ts": "2026-04-08T15:33:21.067104"
  },
  {
    "type": "stream_start",
    "_ts": "2026-04-08T15:33:22.943749"
  },
  {
    "type": "stream_end",
    "metadata": {
      "session_id": "guided-test-152804",
      "stage": "final_assessment",
      "stage_advanced": false,
      "assessment": {
        "recorded": true,
        "progress": {
          "asked": 3,
          "correct": 3,
          "total": 5
        },
        "completed": false
      }
    },
    "_ts": "2026-04-08T15:33:23.628883"
  }
]
```
</details>

**Lesson State**: active=`accessible_name_for_interactive_elements`
  `aria_as_supplement` [done], `native_html_semantics` [done], `prefer_native_html` [done], `recognize_unnecessary_aria` [done], `accessible_name_for_interactive_elements` [todo], `keyboard_support_for_custom_controls` [todo], `presentation_none_misuse` [todo], `preserve_native_semantics` [todo], `diagnose_violated_rule` [todo], `revise_to_follow_rules` [todo], `handle_borderline_cases` [todo], `justify_rule_based_decisions` [todo]

**Active Misconceptions** (2):
- [active] May overapply accessible-name reasoning to non-interactive generic elements
- [active] May treat duplicated aria-label as merely redundant without first asking whether the element needs ARIA at all

**Mastery**: level=`in_progress` confidence=?

<details><summary>Objective Memory</summary>

```json
{
  "student_id": "test-conv-152804",
  "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
  "summary": "Student correctly evaluated a custom ARIA button as named by its text and flagged missing native behavior checks.",
  "demonstrated_skills": [
    "Recognizes ARIA as supplemental rather than default",
    "Spots redundant ARIA on native button",
    "Connects native element to built-in behavior",
    "Explains what native HTML already provides",
    "Distinguishes native semantics from ARIA metadata",
    "Uses button example to justify why redundant ARIA is unnecessary",
    "States the prefer-native rule in plain language",
    "Justifies redundant ARIA on native button",
    "Connects Rule 1 to native role, keyboard support, focusability, and naming",
    "Applies the rule despite unusual visual styling",
    "Explains that ARIA can add semantics but not native behavior",
    "Contrasts native keyboard/focus support with custom ARIA controls",
    "Justifies Rule 1 with practical implementation risk",
    "Recognizes redundant ARIA on native controls",
    "Recognizes when aria-label can duplicate visible text",
    "Applies prior rule-of-thumb that ARIA should not be added automatically",
    "Identifies that visible button text provides the accessible name",
    "Recognizes redundant aria-label on a native button",
    "Distinguishes cases where aria-label may be needed, such as icon-only controls",
    "Recognizes that interactive elements need an accessible name",
    "Identifies that aria-hidden icon content does not name a button",
    "Chooses aria-label appropriately for an icon-only native button",
    "Distinguishes when ARIA naming is useful versus redundant",
    "Explains that the interactive element itself must be named",
    "Identifies the usability impact of an unlabeled button for screen reader users",
    "Applies accessible-name reasoning correctly to icon-only buttons",
    "Identifies when ARIA is unnecessary on native controls",
    "Recognizes visible button text as an accessible name source",
    "Distinguishes needed versus redundant aria-label usage",
    "Recognizes visible text can provide an accessible name for an interactive element",
    "Applies Rule 5 to a custom role=button example",
    "Connects custom ARIA controls to required keyboard operability",
    "Notes focusability as a necessary validity check for non-native controls"
  ],
  "active_gaps": [
    "Has not yet explained what native HTML already provides",
    "Has not yet applied the idea to examples",
    "Needs confirmation that CSS styling does not alter native semantics",
    "Has not yet contrasted native semantics and ARIA in broader examples",
    "Has not yet applied Rule 1 across contrasting native vs custom examples",
    "Has not yet mapped judgments to the named ARIA rules",
    "Has not yet classified multiple contrasting examples",
    "Has not yet mapped flawed examples to specific ARIA rule violations beyond Rule 1",
    "Has not yet classified examples across the remaining ARIA rules",
    "Has not yet revise flawed examples using specific rule labels",
    "Needs to distinguish unnecessary ARIA from redundant ARIA in mixed examples",
    "Needs firmer application of accessible-name requirements only to interactive elements",
    "Needs practice classifying examples by rule violated",
    "Still needs broader rule classification across mixed examples",
    "Has not yet been assessed on keyboard requirements for custom ARIA widgets",
    "Has not yet classified mixed examples across all five ARIA rules",
    "Has not yet demonstrated Rule 3 keyboard requirements for custom controls",
    "Has not yet demonstrated Rule 4 on presentation/none misuse",
    "Has not yet demonstrated Rule 2 about changing native semantics",
    "Has not yet classified mixed examples by which ARIA rule is violated",
    "Has not yet demonstrated Rule 3, Rule 4, or Rule 2 in examples",
    "Has not yet demonstrated keyboard-support reasoning for custom ARIA controls",
    "Has not yet demonstrated Rule 4 about presentation/none on interactive elements",
    "Has not yet demonstrated Rule 2 about unjustified native semantic overrides",
    "Has not yet classified mixed examples by specific rule violated beyond naming and keyboard/focus checks",
    "Has not yet addressed presentation/none misuse or native semantic override in assessment"
  ],
  "next_focus": "Check whether the learner can map flawed examples to the specific ARIA rule violated.",
  "updated_at": "datetime.datetime(2026, 4, 8, 15, 33, 21, 27771, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

<details><summary>Learner Memory</summary>

```json
{
  "student_id": "test-conv-152804",
  "summary": "Learner gave a concise, accurate judgment on a div with role=button, naming the accessible-name pass and the keyboard/focus follow-up checks.",
  "strengths": [
    "Comes in with relevant prior awareness",
    "States uncertainty clearly",
    "Makes correct tentative judgments",
    "Surfaces uncertainty explicitly",
    "Can articulate multiple built-in semantics once prompted",
    "Builds from examples to principle",
    "Reasons concretely about behavior and naming",
    "Builds correct rule statements from examples",
    "Uses causal reasoning, not just recall",
    "Checks edge cases productively",
    "Uses causal reasoning",
    "Connects semantics to behavior",
    "Explains tradeoffs in implementation terms",
    "Spots duplicate labeling patterns",
    "Reasoned aloud instead of guessing",
    "Applies accessible-name concept correctly to native buttons",
    "Recognizes redundancy in ARIA usage",
    "Uses edge cases productively without losing the main rule",
    "Applies accessible-name reasoning correctly",
    "Selects practical fixes",
    "Distinguishes hidden decorative content from usable labels",
    "Concise but conceptually accurate reasoning",
    "Connects missing accessible name to real user impact",
    "Applies prior clarification about naming the button, not the icon",
    "Applies accessible-name reasoning accurately to native buttons",
    "Makes compact, conceptually correct judgments",
    "Can explain why ARIA is unnecessary when HTML already provides the name",
    "Identifies accessible names from visible text",
    "Remembers custom controls need more than a role",
    "Connects non-native elements with missing built-in behavior"
  ],
  "support_needs": [
    "Needs crisp confirmation plus refinement of partial mental models",
    "Needs example-based contrast to stabilize understanding",
    "Needs crisp clarification on edge cases before generalizing rules",
    "Needs continued example-based application to stabilize rule use",
    "Benefits from explicit connection between examples and named rules",
    "Brief confirmation when turning an example into a named rule",
    "More contrastive examples to stabilize transfer",
    "Needs brief confirmation before broader generalization across all rules",
    "Needs help checking element purpose before evaluating ARIA naming",
    "Needs clearer distinction between unnecessary and redundant ARIA",
    "Needs continued practice classifying examples by specific ARIA rule",
    "Should reinforce distinction between unnecessary ARIA and redundant ARIA across element types",
    "Needs broader rule classification practice beyond naming cases",
    "Needs broader practice classifying ARIA misuse across multiple rules",
    "Needs refinement on when differing ARIA labels may be inappropriate despite being possible",
    "Needs broader rule-classification practice across mixed ARIA misuse examples"
  ],
  "tendencies": [
    "Uses tentative phrasing when unsure",
    "Engages readily at the start of a topic",
    "Checks exceptions immediately after a rule-of-thumb",
    "Tests edge cases first, then integrates the clarification",
    "Gives compact but conceptually relevant answers",
    "Frames correct ideas tentatively",
    "Asks whether there is an exception or extra nuance",
    "Responds strongly to native-vs-custom comparisons",
    "Frames answers around risk and extra implementation work",
    "Adds exception cases before settling on the main classification",
    "Adds sensible exceptions after stating the main answer",
    "Answers compactly but with correct core reasoning",
    "Uses concrete examples to justify decisions",
    "Gives compact answers",
    "Reasons from practical user impact",
    "Uses tentative phrasing when unsure but lands on correct concepts",
    "Answers briefly but with relevant justification",
    "Adds cautious caveats about exceptions",
    "Gives compact but conceptually complete answers",
    "Adds practical follow-up checks without prompting"
  ],
  "successful_strategies": [
    "Affirm then refine",
    "Use simple native-vs-ARIA contrasts",
    "Affirm the correct core answer, then refine with a concrete edge-case clarification",
    "Ask what native HTML already provides",
    "Use a familiar element before contrasting with ARIA alternatives",
    "Confirm the core rule, then test it on contrasting markup examples",
    "Tie the example back to the named ARIA rule explicitly",
    "Use contrastive markup examples",
    "Ask what native HTML gives automatically",
    "Present simple mixed examples and ask first: is this element interactive?",
    "Tie each example to the specific ARIA rule being applied",
    "Contrast visible text buttons with icon-only buttons",
    "Ask whether the element already has an accessible name from native HTML",
    "Use short code examples",
    "Ask whether the control has an accessible name without relying on hidden decorative content",
    "Contrast redundant ARIA with necessary ARIA",
    "Use concrete button examples",
    "Ask about likely screen reader output",
    "Contrast named vs unnamed interactive controls",
    "Use simple native button contrasts",
    "Ask whether native HTML already provides the needed name",
    "Use mixed native-vs-custom examples",
    "Ask for both the rule satisfied and the additional validation check"
  ],
  "updated_at": "datetime.datetime(2026, 4, 8, 15, 33, 21, 30501, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

---

### Turn 12: final_assessment → final_assessment
**Tutor time**: 13.75s | **Student agent time**: 1.53s | **Turns on obj**: 5 → 5

**Student**:
> That’s violating the “don’t override native semantics” rule. A real `<button>` already has button semantics, so `role="presentation"` would strip or fight that native meaning instead of helping.

**Tutor**:
> Close, but not the exact rule being tested. The issue here is specifically that `role="presentation"` must not be placed on a focusable or interactive element like a button — that’s the rule for presentation/none misuse, not the broader “don’t override native semantics” rule.

Next assessment question: which rule is violated by `<button role="presentation">Delete</button>`?

<details><summary>WebSocket Events (5 non-token)</summary>

```json
[
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Evaluating your assessment answer...",
    "_ts": "2026-04-08T15:33:25.369747"
  },
  {
    "type": "assessment_score",
    "asked": 4,
    "correct": 3,
    "total": 5,
    "passed": null,
    "_ts": "2026-04-08T15:33:36.152884"
  },
  {
    "type": "stage",
    "stage": "composing",
    "detail": "Generating response (final_assessment)...",
    "_ts": "2026-04-08T15:33:36.192342"
  },
  {
    "type": "stream_start",
    "_ts": "2026-04-08T15:33:38.372196"
  },
  {
    "type": "stream_end",
    "metadata": {
      "session_id": "guided-test-152804",
      "stage": "final_assessment",
      "stage_advanced": false,
      "assessment": {
        "recorded": true,
        "progress": {
          "asked": 4,
          "correct": 3,
          "total": 5
        },
        "completed": false
      }
    },
    "_ts": "2026-04-08T15:33:39.080461"
  }
]
```
</details>

**Lesson State**: active=`accessible_name_for_interactive_elements`
  `aria_as_supplement` [done], `native_html_semantics` [done], `prefer_native_html` [done], `recognize_unnecessary_aria` [done], `accessible_name_for_interactive_elements` [todo], `keyboard_support_for_custom_controls` [todo], `presentation_none_misuse` [todo], `preserve_native_semantics` [todo], `diagnose_violated_rule` [todo], `revise_to_follow_rules` [todo], `handle_borderline_cases` [todo], `justify_rule_based_decisions` [todo]

**Active Misconceptions** (3):
- [active] May classify role="presentation" on a button under generic semantic override instead of the specific Rule 4 prohibition.
- [active] May overapply accessible-name reasoning to non-interactive generic elements
- [active] May treat duplicated aria-label as merely redundant without first asking whether the element needs ARIA at all

**Mastery**: level=`in_progress` confidence=?

<details><summary>Objective Memory</summary>

```json
{
  "student_id": "test-conv-152804",
  "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
  "summary": "Learner recognized that role=\"presentation\" strips a button’s meaning, but did not map the example to the specific ARIA rule being tested.",
  "demonstrated_skills": [
    "Recognizes ARIA as supplemental rather than default",
    "Spots redundant ARIA on native button",
    "Connects native element to built-in behavior",
    "Explains what native HTML already provides",
    "Distinguishes native semantics from ARIA metadata",
    "Uses button example to justify why redundant ARIA is unnecessary",
    "States the prefer-native rule in plain language",
    "Justifies redundant ARIA on native button",
    "Connects Rule 1 to native role, keyboard support, focusability, and naming",
    "Applies the rule despite unusual visual styling",
    "Explains that ARIA can add semantics but not native behavior",
    "Contrasts native keyboard/focus support with custom ARIA controls",
    "Justifies Rule 1 with practical implementation risk",
    "Recognizes redundant ARIA on native controls",
    "Recognizes when aria-label can duplicate visible text",
    "Applies prior rule-of-thumb that ARIA should not be added automatically",
    "Identifies that visible button text provides the accessible name",
    "Recognizes redundant aria-label on a native button",
    "Distinguishes cases where aria-label may be needed, such as icon-only controls",
    "Recognizes that interactive elements need an accessible name",
    "Identifies that aria-hidden icon content does not name a button",
    "Chooses aria-label appropriately for an icon-only native button",
    "Distinguishes when ARIA naming is useful versus redundant",
    "Explains that the interactive element itself must be named",
    "Identifies the usability impact of an unlabeled button for screen reader users",
    "Applies accessible-name reasoning correctly to icon-only buttons",
    "Identifies when ARIA is unnecessary on native controls",
    "Recognizes visible button text as an accessible name source",
    "Distinguishes needed versus redundant aria-label usage",
    "Recognizes visible text can provide an accessible name for an interactive element",
    "Applies Rule 5 to a custom role=button example",
    "Connects custom ARIA controls to required keyboard operability",
    "Notes focusability as a necessary validity check for non-native controls",
    "Recognizes that native button semantics should not be stripped",
    "Understands role=\"presentation\" conflicts with meaningful interactive semantics"
  ],
  "active_gaps": [
    "Has not yet explained what native HTML already provides",
    "Has not yet applied the idea to examples",
    "Needs confirmation that CSS styling does not alter native semantics",
    "Has not yet contrasted native semantics and ARIA in broader examples",
    "Has not yet applied Rule 1 across contrasting native vs custom examples",
    "Has not yet mapped judgments to the named ARIA rules",
    "Has not yet classified multiple contrasting examples",
    "Has not yet mapped flawed examples to specific ARIA rule violations beyond Rule 1",
    "Has not yet classified examples across the remaining ARIA rules",
    "Has not yet revise flawed examples using specific rule labels",
    "Needs to distinguish unnecessary ARIA from redundant ARIA in mixed examples",
    "Needs firmer application of accessible-name requirements only to interactive elements",
    "Needs practice classifying examples by rule violated",
    "Still needs broader rule classification across mixed examples",
    "Has not yet been assessed on keyboard requirements for custom ARIA widgets",
    "Has not yet classified mixed examples across all five ARIA rules",
    "Has not yet demonstrated Rule 3 keyboard requirements for custom controls",
    "Has not yet demonstrated Rule 4 on presentation/none misuse",
    "Has not yet demonstrated Rule 2 about changing native semantics",
    "Has not yet classified mixed examples by which ARIA rule is violated",
    "Has not yet demonstrated Rule 3, Rule 4, or Rule 2 in examples",
    "Has not yet demonstrated keyboard-support reasoning for custom ARIA controls",
    "Has not yet demonstrated Rule 4 about presentation/none on interactive elements",
    "Has not yet demonstrated Rule 2 about unjustified native semantic overrides",
    "Has not yet classified mixed examples by specific rule violated beyond naming and keyboard/focus checks",
    "Has not yet addressed presentation/none misuse or native semantic override in assessment",
    "Needs to identify Rule 4 specifically for presentation/none on interactive or focusable elements",
    "Needs stronger rule-to-example mapping precision"
  ],
  "next_focus": "Practice classifying flawed ARIA examples by the exact rule violated.",
  "updated_at": "datetime.datetime(2026, 4, 8, 15, 33, 36, 146185, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

<details><summary>Learner Memory</summary>

```json
{
  "student_id": "test-conv-152804",
  "summary": "Learner gives conceptually relevant explanations but may choose a broader rule instead of the precise one requested.",
  "strengths": [
    "Comes in with relevant prior awareness",
    "States uncertainty clearly",
    "Makes correct tentative judgments",
    "Surfaces uncertainty explicitly",
    "Can articulate multiple built-in semantics once prompted",
    "Builds from examples to principle",
    "Reasons concretely about behavior and naming",
    "Builds correct rule statements from examples",
    "Uses causal reasoning, not just recall",
    "Checks edge cases productively",
    "Uses causal reasoning",
    "Connects semantics to behavior",
    "Explains tradeoffs in implementation terms",
    "Spots duplicate labeling patterns",
    "Reasoned aloud instead of guessing",
    "Applies accessible-name concept correctly to native buttons",
    "Recognizes redundancy in ARIA usage",
    "Uses edge cases productively without losing the main rule",
    "Applies accessible-name reasoning correctly",
    "Selects practical fixes",
    "Distinguishes hidden decorative content from usable labels",
    "Concise but conceptually accurate reasoning",
    "Connects missing accessible name to real user impact",
    "Applies prior clarification about naming the button, not the icon",
    "Applies accessible-name reasoning accurately to native buttons",
    "Makes compact, conceptually correct judgments",
    "Can explain why ARIA is unnecessary when HTML already provides the name",
    "Identifies accessible names from visible text",
    "Remembers custom controls need more than a role",
    "Connects non-native elements with missing built-in behavior",
    "Explains semantic harm clearly",
    "Connects native elements to built-in meaning"
  ],
  "support_needs": [
    "Needs crisp confirmation plus refinement of partial mental models",
    "Needs example-based contrast to stabilize understanding",
    "Needs crisp clarification on edge cases before generalizing rules",
    "Needs continued example-based application to stabilize rule use",
    "Benefits from explicit connection between examples and named rules",
    "Brief confirmation when turning an example into a named rule",
    "More contrastive examples to stabilize transfer",
    "Needs brief confirmation before broader generalization across all rules",
    "Needs help checking element purpose before evaluating ARIA naming",
    "Needs clearer distinction between unnecessary and redundant ARIA",
    "Needs continued practice classifying examples by specific ARIA rule",
    "Should reinforce distinction between unnecessary ARIA and redundant ARIA across element types",
    "Needs broader rule classification practice beyond naming cases",
    "Needs broader practice classifying ARIA misuse across multiple rules",
    "Needs refinement on when differing ARIA labels may be inappropriate despite being possible",
    "Needs broader rule-classification practice across mixed ARIA misuse examples",
    "More precise mapping from examples to exact ARIA rule numbers/concepts",
    "Reinforcement on Rule 4 as distinct from general semantic overrides"
  ],
  "tendencies": [
    "Uses tentative phrasing when unsure",
    "Engages readily at the start of a topic",
    "Checks exceptions immediately after a rule-of-thumb",
    "Tests edge cases first, then integrates the clarification",
    "Gives compact but conceptually relevant answers",
    "Frames correct ideas tentatively",
    "Asks whether there is an exception or extra nuance",
    "Responds strongly to native-vs-custom comparisons",
    "Frames answers around risk and extra implementation work",
    "Adds exception cases before settling on the main classification",
    "Adds sensible exceptions after stating the main answer",
    "Answers compactly but with correct core reasoning",
    "Uses concrete examples to justify decisions",
    "Gives compact answers",
    "Reasons from practical user impact",
    "Uses tentative phrasing when unsure but lands on correct concepts",
    "Answers briefly but with relevant justification",
    "Adds cautious caveats about exceptions",
    "Gives compact but conceptually complete answers",
    "Adds practical follow-up checks without prompting",
    "Answers with sound general reasoning even when the prompt requires finer rule distinction"
  ],
  "successful_strategies": [
    "Affirm then refine",
    "Use simple native-vs-ARIA contrasts",
    "Affirm the correct core answer, then refine with a concrete edge-case clarification",
    "Ask what native HTML already provides",
    "Use a familiar element before contrasting with ARIA alternatives",
    "Confirm the core rule, then test it on contrasting markup examples",
    "Tie the example back to the named ARIA rule explicitly",
    "Use contrastive markup examples",
    "Ask what native HTML gives automatically",
    "Present simple mixed examples and ask first: is this element interactive?",
    "Tie each example to the specific ARIA rule being applied",
    "Contrast visible text buttons with icon-only buttons",
    "Ask whether the element already has an accessible name from native HTML",
    "Use short code examples",
    "Ask whether the control has an accessible name without relying on hidden decorative content",
    "Contrast redundant ARIA with necessary ARIA",
    "Use concrete button examples",
    "Ask about likely screen reader output",
    "Contrast named vs unnamed interactive controls",
    "Use simple native button contrasts",
    "Ask whether native HTML already provides the needed name",
    "Use mixed native-vs-custom examples",
    "Ask for both the rule satisfied and the additional validation check",
    "Ask for the exact rule name/concept, then contrast it with nearby similar rules",
    "Use near-miss examples to sharpen classification precision"
  ],
  "updated_at": "datetime.datetime(2026, 4, 8, 15, 33, 36, 147798, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

---

### Turn 13: final_assessment → introduction
**Tutor time**: 9.9s | **Student agent time**: 1.64s | **Turns on obj**: 5 → 0

**Student**:
> Ah, got it — it violates the rule that `role="presentation"`/`none` should not be used on focusable or interactive elements. Since `<button>` is interactive, that role is invalid there.

**Tutor**:
> Exactly — that’s the rule.

You’ve now got the core decision pattern: use native HTML first, add ARIA only when it actually fills a gap, make sure interactive ARIA controls are usable by keyboard, give interactive elements an accessible name, and never use `presentation`/`none` on something the user can focus or activate.

You also made the important distinction between “native semantics” and “ARIA decoration,” which is what keeps these checks precise instead of turning into guesswork.

<details><summary>WebSocket Events (8 non-token)</summary>

```json
[
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Evaluating your assessment answer...",
    "_ts": "2026-04-08T15:33:40.673357"
  },
  {
    "type": "assessment_score",
    "asked": 5,
    "correct": 4,
    "total": 5,
    "passed": true,
    "_ts": "2026-04-08T15:33:47.629999"
  },
  {
    "type": "stage_update",
    "stage": "transition",
    "objective": "Apply the five rules for using ARIA correctly",
    "summary": "Correctly identified Rule 4 and explained that buttons are interactive/focusable, so presentation/none is invalid there.",
    "_ts": "2026-04-08T15:33:47.631996"
  },
  {
    "type": "mastery_update",
    "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
    "objective_text": "Apply the five rules for using ARIA correctly",
    "new_level": "mastered",
    "_ts": "2026-04-08T15:33:47.632010"
  },
  {
    "type": "stage",
    "stage": "composing",
    "detail": "Generating response (transition)...",
    "_ts": "2026-04-08T15:33:47.673935"
  },
  {
    "type": "stream_start",
    "_ts": "2026-04-08T15:33:49.614946"
  },
  {
    "type": "stage_update",
    "stage": "introduction",
    "objective": "Compare the scope of WCAG (2.0, 2.1, 2.2), ATAG 2.0, and EN 301 549, and **identify** how each set of requirements influences web accessibility design.",
    "summary": "Starting new objective: Compare the scope of WCAG (2.0, 2.1, 2.2), ATAG 2.0, and EN 301 549, and **identify** how each set of requirements influences web accessibility design.",
    "_ts": "2026-04-08T15:33:50.519555"
  },
  {
    "type": "stream_end",
    "metadata": {
      "session_id": "guided-test-152804",
      "stage": "introduction",
      "stage_advanced": true,
      "assessment": {
        "recorded": true,
        "progress": {
          "asked": 5,
          "correct": 4,
          "total": 5
        },
        "completed": true,
        "passed": true,
        "mastery_level": "mastered",
        "next_stage": "transition"
      }
    },
    "_ts": "2026-04-08T15:33:50.519607"
  }
]
```
</details>

**Active Misconceptions** (3):
- [active] May classify role="presentation" on a button under generic semantic override instead of the specific Rule 4 prohibition.
- [active] May overapply accessible-name reasoning to non-interactive generic elements
- [active] May treat duplicated aria-label as merely redundant without first asking whether the element needs ARIA at all

**Mastery**: level=`mastered` confidence=?

<details><summary>Objective Memory</summary>

```json
{
  "student_id": "test-conv-152804",
  "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
  "summary": "Learner correctly mapped role=\"presentation\" on a button to the specific prohibition against using presentation/none on interactive elements.",
  "demonstrated_skills": [
    "Recognizes ARIA as supplemental rather than default",
    "Spots redundant ARIA on native button",
    "Connects native element to built-in behavior",
    "Explains what native HTML already provides",
    "Distinguishes native semantics from ARIA metadata",
    "Uses button example to justify why redundant ARIA is unnecessary",
    "States the prefer-native rule in plain language",
    "Justifies redundant ARIA on native button",
    "Connects Rule 1 to native role, keyboard support, focusability, and naming",
    "Applies the rule despite unusual visual styling",
    "Explains that ARIA can add semantics but not native behavior",
    "Contrasts native keyboard/focus support with custom ARIA controls",
    "Justifies Rule 1 with practical implementation risk",
    "Recognizes redundant ARIA on native controls",
    "Recognizes when aria-label can duplicate visible text",
    "Applies prior rule-of-thumb that ARIA should not be added automatically",
    "Identifies that visible button text provides the accessible name",
    "Recognizes redundant aria-label on a native button",
    "Distinguishes cases where aria-label may be needed, such as icon-only controls",
    "Recognizes that interactive elements need an accessible name",
    "Identifies that aria-hidden icon content does not name a button",
    "Chooses aria-label appropriately for an icon-only native button",
    "Distinguishes when ARIA naming is useful versus redundant",
    "Explains that the interactive element itself must be named",
    "Identifies the usability impact of an unlabeled button for screen reader users",
    "Applies accessible-name reasoning correctly to icon-only buttons",
    "Identifies when ARIA is unnecessary on native controls",
    "Recognizes visible button text as an accessible name source",
    "Distinguishes needed versus redundant aria-label usage",
    "Recognizes visible text can provide an accessible name for an interactive element",
    "Applies Rule 5 to a custom role=button example",
    "Connects custom ARIA controls to required keyboard operability",
    "Notes focusability as a necessary validity check for non-native controls",
    "Recognizes that native button semantics should not be stripped",
    "Understands role=\"presentation\" conflicts with meaningful interactive semantics",
    "Maps a flawed ARIA example to the exact violated rule",
    "Recognizes that buttons are interactive/focusable elements",
    "Distinguishes Rule 4 from the broader native-semantics override rule"
  ],
  "active_gaps": [
    "Has not yet explained what native HTML already provides",
    "Has not yet applied the idea to examples",
    "Needs confirmation that CSS styling does not alter native semantics",
    "Has not yet contrasted native semantics and ARIA in broader examples",
    "Has not yet applied Rule 1 across contrasting native vs custom examples",
    "Has not yet mapped judgments to the named ARIA rules",
    "Has not yet classified multiple contrasting examples",
    "Has not yet mapped flawed examples to specific ARIA rule violations beyond Rule 1",
    "Has not yet classified examples across the remaining ARIA rules",
    "Has not yet revise flawed examples using specific rule labels",
    "Needs to distinguish unnecessary ARIA from redundant ARIA in mixed examples",
    "Needs firmer application of accessible-name requirements only to interactive elements",
    "Needs practice classifying examples by rule violated",
    "Still needs broader rule classification across mixed examples",
    "Has not yet been assessed on keyboard requirements for custom ARIA widgets",
    "Has not yet classified mixed examples across all five ARIA rules",
    "Has not yet demonstrated Rule 3 keyboard requirements for custom controls",
    "Has not yet demonstrated Rule 4 on presentation/none misuse",
    "Has not yet demonstrated Rule 2 about changing native semantics",
    "Has not yet classified mixed examples by which ARIA rule is violated",
    "Has not yet demonstrated Rule 3, Rule 4, or Rule 2 in examples",
    "Has not yet demonstrated keyboard-support reasoning for custom ARIA controls",
    "Has not yet demonstrated Rule 4 about presentation/none on interactive elements",
    "Has not yet demonstrated Rule 2 about unjustified native semantic overrides",
    "Has not yet classified mixed examples by specific rule violated beyond naming and keyboard/focus checks",
    "Has not yet addressed presentation/none misuse or native semantic override in assessment",
    "Needs to identify Rule 4 specifically for presentation/none on interactive or focusable elements",
    "Needs stronger rule-to-example mapping precision"
  ],
  "next_focus": "Check integrated classification across examples, especially when ARIA is unnecessary versus required.",
  "updated_at": "datetime.datetime(2026, 4, 8, 15, 33, 47, 618686, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

<details><summary>Learner Memory</summary>

```json
{
  "student_id": "test-conv-152804",
  "summary": "Learner refined an initially broad classification to the precise ARIA rule when prompted.",
  "strengths": [
    "Comes in with relevant prior awareness",
    "States uncertainty clearly",
    "Makes correct tentative judgments",
    "Surfaces uncertainty explicitly",
    "Can articulate multiple built-in semantics once prompted",
    "Builds from examples to principle",
    "Reasons concretely about behavior and naming",
    "Builds correct rule statements from examples",
    "Uses causal reasoning, not just recall",
    "Checks edge cases productively",
    "Uses causal reasoning",
    "Connects semantics to behavior",
    "Explains tradeoffs in implementation terms",
    "Spots duplicate labeling patterns",
    "Reasoned aloud instead of guessing",
    "Applies accessible-name concept correctly to native buttons",
    "Recognizes redundancy in ARIA usage",
    "Uses edge cases productively without losing the main rule",
    "Applies accessible-name reasoning correctly",
    "Selects practical fixes",
    "Distinguishes hidden decorative content from usable labels",
    "Concise but conceptually accurate reasoning",
    "Connects missing accessible name to real user impact",
    "Applies prior clarification about naming the button, not the icon",
    "Applies accessible-name reasoning accurately to native buttons",
    "Makes compact, conceptually correct judgments",
    "Can explain why ARIA is unnecessary when HTML already provides the name",
    "Identifies accessible names from visible text",
    "Remembers custom controls need more than a role",
    "Connects non-native elements with missing built-in behavior",
    "Explains semantic harm clearly",
    "Connects native elements to built-in meaning",
    "Understands core semantics of native interactive elements",
    "Can correct to the exact rule after brief feedback",
    "Gives concise rule-based explanations"
  ],
  "support_needs": [
    "Needs crisp confirmation plus refinement of partial mental models",
    "Needs example-based contrast to stabilize understanding",
    "Needs crisp clarification on edge cases before generalizing rules",
    "Needs continued example-based application to stabilize rule use",
    "Benefits from explicit connection between examples and named rules",
    "Brief confirmation when turning an example into a named rule",
    "More contrastive examples to stabilize transfer",
    "Needs brief confirmation before broader generalization across all rules",
    "Needs help checking element purpose before evaluating ARIA naming",
    "Needs clearer distinction between unnecessary and redundant ARIA",
    "Needs continued practice classifying examples by specific ARIA rule",
    "Should reinforce distinction between unnecessary ARIA and redundant ARIA across element types",
    "Needs broader rule classification practice beyond naming cases",
    "Needs broader practice classifying ARIA misuse across multiple rules",
    "Needs refinement on when differing ARIA labels may be inappropriate despite being possible",
    "Needs broader rule-classification practice across mixed ARIA misuse examples",
    "More precise mapping from examples to exact ARIA rule numbers/concepts",
    "Reinforcement on Rule 4 as distinct from general semantic overrides"
  ],
  "tendencies": [
    "Uses tentative phrasing when unsure",
    "Engages readily at the start of a topic",
    "Checks exceptions immediately after a rule-of-thumb",
    "Tests edge cases first, then integrates the clarification",
    "Gives compact but conceptually relevant answers",
    "Frames correct ideas tentatively",
    "Asks whether there is an exception or extra nuance",
    "Responds strongly to native-vs-custom comparisons",
    "Frames answers around risk and extra implementation work",
    "Adds exception cases before settling on the main classification",
    "Adds sensible exceptions after stating the main answer",
    "Answers compactly but with correct core reasoning",
    "Uses concrete examples to justify decisions",
    "Gives compact answers",
    "Reasons from practical user impact",
    "Uses tentative phrasing when unsure but lands on correct concepts",
    "Answers briefly but with relevant justification",
    "Adds cautious caveats about exceptions",
    "Gives compact but conceptually complete answers",
    "Adds practical follow-up checks without prompting",
    "Answers with sound general reasoning even when the prompt requires finer rule distinction",
    "May first choose a broader rule before selecting the specific one tested"
  ],
  "successful_strategies": [
    "Affirm then refine",
    "Use simple native-vs-ARIA contrasts",
    "Affirm the correct core answer, then refine with a concrete edge-case clarification",
    "Ask what native HTML already provides",
    "Use a familiar element before contrasting with ARIA alternatives",
    "Confirm the core rule, then test it on contrasting markup examples",
    "Tie the example back to the named ARIA rule explicitly",
    "Use contrastive markup examples",
    "Ask what native HTML gives automatically",
    "Present simple mixed examples and ask first: is this element interactive?",
    "Tie each example to the specific ARIA rule being applied",
    "Contrast visible text buttons with icon-only buttons",
    "Ask whether the element already has an accessible name from native HTML",
    "Use short code examples",
    "Ask whether the control has an accessible name without relying on hidden decorative content",
    "Contrast redundant ARIA with necessary ARIA",
    "Use concrete button examples",
    "Ask about likely screen reader output",
    "Contrast named vs unnamed interactive controls",
    "Use simple native button contrasts",
    "Ask whether native HTML already provides the needed name",
    "Use mixed native-vs-custom examples",
    "Ask for both the rule satisfied and the additional validation check",
    "Ask for the exact rule name/concept, then contrast it with nearby similar rules",
    "Use near-miss examples to sharpen classification precision",
    "Prompting for the exact rule name",
    "Using interactive native elements as concrete contrast cases"
  ],
  "updated_at": "datetime.datetime(2026, 4, 8, 15, 33, 47, 622491, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

---

### Turn 14: introduction → introduction
**Tutor time**: 143.04s | **Student agent time**: -s | **Turns on obj**: 0 → 1

**Student**:
> Yeah, that makes sense now. So the big pattern is: native HTML first, ARIA only when there’s a real gap, and if I build a custom interactive thing I have to handle name, focus, and keyboard myself.

**Tutor**:
> Yes — that’s the right rule of thumb for ARIA.

For this lesson, we’re going to use that same idea in a different way: instead of asking “what ARIA can I add?”, we ask “what thing does this standard apply to?” That “what thing it applies to” is the scope.

So here’s the next step: if a rule is about the page’s content, a rule about the tool used to create the page, and a rule about a broader product requirement, what are we comparing them by?

<details><summary>WebSocket Events (13 non-token)</summary>

```json
[
  {
    "type": "stage",
    "stage": "composing",
    "detail": "Creating teaching plan...",
    "_ts": "2026-04-08T15:33:52.171065"
  },
  {
    "type": "stage",
    "stage": "searching",
    "detail": "Researching WCAG content...",
    "_ts": "2026-04-08T15:35:20.294708"
  },
  {
    "type": "stage",
    "stage": "searching",
    "detail": "Researching WCAG sources (round 1/4)...",
    "_ts": "2026-04-08T15:35:20.296048"
  },
  {
    "type": "stage",
    "stage": "searching",
    "detail": "Researching WCAG sources (round 2/4)...",
    "_ts": "2026-04-08T15:35:31.984851"
  },
  {
    "type": "stage",
    "stage": "searching",
    "detail": "Researching WCAG sources (round 3/4)...",
    "_ts": "2026-04-08T15:35:45.435691"
  },
  {
    "type": "stage",
    "stage": "searching",
    "detail": "Validating evidence...",
    "_ts": "2026-04-08T15:36:01.758249"
  },
  {
    "type": "stage",
    "stage": "searching",
    "detail": "Teaching pack: 3213 chars from 5 sources",
    "_ts": "2026-04-08T15:36:01.759856"
  },
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Analyzing your response...",
    "_ts": "2026-04-08T15:36:01.841549"
  },
  {
    "type": "stage",
    "stage": "composing",
    "detail": "Generating response (introduction)...",
    "_ts": "2026-04-08T15:36:11.331551"
  },
  {
    "type": "stream_start",
    "_ts": "2026-04-08T15:36:14.222791"
  },
  {
    "type": "stage",
    "stage": "analyzing",
    "detail": "Updating learning state...",
    "_ts": "2026-04-08T15:36:15.189871"
  },
  {
    "type": "mastery_update",
    "objective_id": "27075442-6261-4c6d-ad8d-4c3de134b366",
    "objective_text": "Compare the scope of WCAG (2.0, 2.1, 2.2), ATAG 2.0, and EN 301 549, and **identify** how each set of requirements influences web accessibility design.",
    "new_level": "not_attempted",
    "_ts": "2026-04-08T15:36:15.211737"
  },
  {
    "type": "stream_end",
    "metadata": {
      "session_id": "guided-test-152804",
      "stage": "introduction",
      "stage_advanced": false,
      "assessment": {}
    },
    "_ts": "2026-04-08T15:36:15.211828"
  }
]
```
</details>

**Lesson State**: active=`scope_as_comparison_lens`
  `scope_as_comparison_lens` [todo], `meaning_of_scope` [todo], `wcag_web_content_family` [todo], `wcag_versions_one_line` [todo], `wcag_versions_extend_coverage` [todo], `atag_authoring_tool_guidance` [todo], `atag_influences_tool_design` [todo], `en301549_broader_framework` [todo], `en301549_influences_broader_design` [todo], `compare_all_three_families_by_scope` [todo], `classify_practical_scenarios` [todo], `handle_overlap_borderline_scenarios` [todo]

**Active Misconceptions** (3):
- [active] May classify role="presentation" on a button under generic semantic override instead of the specific Rule 4 prohibition.
- [active] May overapply accessible-name reasoning to non-interactive generic elements
- [active] May treat duplicated aria-label as merely redundant without first asking whether the element needs ARIA at all

**Mastery**: level=`mastered` confidence=?

<details><summary>Objective Memory</summary>

```json
{
  "student_id": "test-conv-152804",
  "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
  "summary": "Learner correctly mapped role=\"presentation\" on a button to the specific prohibition against using presentation/none on interactive elements.",
  "demonstrated_skills": [
    "Recognizes ARIA as supplemental rather than default",
    "Spots redundant ARIA on native button",
    "Connects native element to built-in behavior",
    "Explains what native HTML already provides",
    "Distinguishes native semantics from ARIA metadata",
    "Uses button example to justify why redundant ARIA is unnecessary",
    "States the prefer-native rule in plain language",
    "Justifies redundant ARIA on native button",
    "Connects Rule 1 to native role, keyboard support, focusability, and naming",
    "Applies the rule despite unusual visual styling",
    "Explains that ARIA can add semantics but not native behavior",
    "Contrasts native keyboard/focus support with custom ARIA controls",
    "Justifies Rule 1 with practical implementation risk",
    "Recognizes redundant ARIA on native controls",
    "Recognizes when aria-label can duplicate visible text",
    "Applies prior rule-of-thumb that ARIA should not be added automatically",
    "Identifies that visible button text provides the accessible name",
    "Recognizes redundant aria-label on a native button",
    "Distinguishes cases where aria-label may be needed, such as icon-only controls",
    "Recognizes that interactive elements need an accessible name",
    "Identifies that aria-hidden icon content does not name a button",
    "Chooses aria-label appropriately for an icon-only native button",
    "Distinguishes when ARIA naming is useful versus redundant",
    "Explains that the interactive element itself must be named",
    "Identifies the usability impact of an unlabeled button for screen reader users",
    "Applies accessible-name reasoning correctly to icon-only buttons",
    "Identifies when ARIA is unnecessary on native controls",
    "Recognizes visible button text as an accessible name source",
    "Distinguishes needed versus redundant aria-label usage",
    "Recognizes visible text can provide an accessible name for an interactive element",
    "Applies Rule 5 to a custom role=button example",
    "Connects custom ARIA controls to required keyboard operability",
    "Notes focusability as a necessary validity check for non-native controls",
    "Recognizes that native button semantics should not be stripped",
    "Understands role=\"presentation\" conflicts with meaningful interactive semantics",
    "Maps a flawed ARIA example to the exact violated rule",
    "Recognizes that buttons are interactive/focusable elements",
    "Distinguishes Rule 4 from the broader native-semantics override rule"
  ],
  "active_gaps": [
    "Has not yet explained what native HTML already provides",
    "Has not yet applied the idea to examples",
    "Needs confirmation that CSS styling does not alter native semantics",
    "Has not yet contrasted native semantics and ARIA in broader examples",
    "Has not yet applied Rule 1 across contrasting native vs custom examples",
    "Has not yet mapped judgments to the named ARIA rules",
    "Has not yet classified multiple contrasting examples",
    "Has not yet mapped flawed examples to specific ARIA rule violations beyond Rule 1",
    "Has not yet classified examples across the remaining ARIA rules",
    "Has not yet revise flawed examples using specific rule labels",
    "Needs to distinguish unnecessary ARIA from redundant ARIA in mixed examples",
    "Needs firmer application of accessible-name requirements only to interactive elements",
    "Needs practice classifying examples by rule violated",
    "Still needs broader rule classification across mixed examples",
    "Has not yet been assessed on keyboard requirements for custom ARIA widgets",
    "Has not yet classified mixed examples across all five ARIA rules",
    "Has not yet demonstrated Rule 3 keyboard requirements for custom controls",
    "Has not yet demonstrated Rule 4 on presentation/none misuse",
    "Has not yet demonstrated Rule 2 about changing native semantics",
    "Has not yet classified mixed examples by which ARIA rule is violated",
    "Has not yet demonstrated Rule 3, Rule 4, or Rule 2 in examples",
    "Has not yet demonstrated keyboard-support reasoning for custom ARIA controls",
    "Has not yet demonstrated Rule 4 about presentation/none on interactive elements",
    "Has not yet demonstrated Rule 2 about unjustified native semantic overrides",
    "Has not yet classified mixed examples by specific rule violated beyond naming and keyboard/focus checks",
    "Has not yet addressed presentation/none misuse or native semantic override in assessment",
    "Needs to identify Rule 4 specifically for presentation/none on interactive or focusable elements",
    "Needs stronger rule-to-example mapping precision"
  ],
  "next_focus": "Check integrated classification across examples, especially when ARIA is unnecessary versus required.",
  "updated_at": "datetime.datetime(2026, 4, 8, 15, 33, 47, 618686, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

<details><summary>Learner Memory</summary>

```json
{
  "student_id": "test-conv-152804",
  "summary": "Learner can restate a distilled rule pattern from the prior objective.",
  "strengths": [
    "Comes in with relevant prior awareness",
    "States uncertainty clearly",
    "Makes correct tentative judgments",
    "Surfaces uncertainty explicitly",
    "Can articulate multiple built-in semantics once prompted",
    "Builds from examples to principle",
    "Reasons concretely about behavior and naming",
    "Builds correct rule statements from examples",
    "Uses causal reasoning, not just recall",
    "Checks edge cases productively",
    "Uses causal reasoning",
    "Connects semantics to behavior",
    "Explains tradeoffs in implementation terms",
    "Spots duplicate labeling patterns",
    "Reasoned aloud instead of guessing",
    "Applies accessible-name concept correctly to native buttons",
    "Recognizes redundancy in ARIA usage",
    "Uses edge cases productively without losing the main rule",
    "Applies accessible-name reasoning correctly",
    "Selects practical fixes",
    "Distinguishes hidden decorative content from usable labels",
    "Concise but conceptually accurate reasoning",
    "Connects missing accessible name to real user impact",
    "Applies prior clarification about naming the button, not the icon",
    "Applies accessible-name reasoning accurately to native buttons",
    "Makes compact, conceptually correct judgments",
    "Can explain why ARIA is unnecessary when HTML already provides the name",
    "Identifies accessible names from visible text",
    "Remembers custom controls need more than a role",
    "Connects non-native elements with missing built-in behavior",
    "Explains semantic harm clearly",
    "Connects native elements to built-in meaning",
    "Understands core semantics of native interactive elements",
    "Can correct to the exact rule after brief feedback",
    "Gives concise rule-based explanations",
    "Summarizes core patterns compactly"
  ],
  "support_needs": [
    "Needs crisp confirmation plus refinement of partial mental models",
    "Needs example-based contrast to stabilize understanding",
    "Needs crisp clarification on edge cases before generalizing rules",
    "Needs continued example-based application to stabilize rule use",
    "Benefits from explicit connection between examples and named rules",
    "Brief confirmation when turning an example into a named rule",
    "More contrastive examples to stabilize transfer",
    "Needs brief confirmation before broader generalization across all rules",
    "Needs help checking element purpose before evaluating ARIA naming",
    "Needs clearer distinction between unnecessary and redundant ARIA",
    "Needs continued practice classifying examples by specific ARIA rule",
    "Should reinforce distinction between unnecessary ARIA and redundant ARIA across element types",
    "Needs broader rule classification practice beyond naming cases",
    "Needs broader practice classifying ARIA misuse across multiple rules",
    "Needs refinement on when differing ARIA labels may be inappropriate despite being possible",
    "Needs broader rule-classification practice across mixed ARIA misuse examples",
    "More precise mapping from examples to exact ARIA rule numbers/concepts",
    "Reinforcement on Rule 4 as distinct from general semantic overrides",
    "Needs clear transition when objective changes"
  ],
  "tendencies": [
    "Uses tentative phrasing when unsure",
    "Engages readily at the start of a topic",
    "Checks exceptions immediately after a rule-of-thumb",
    "Tests edge cases first, then integrates the clarification",
    "Gives compact but conceptually relevant answers",
    "Frames correct ideas tentatively",
    "Asks whether there is an exception or extra nuance",
    "Responds strongly to native-vs-custom comparisons",
    "Frames answers around risk and extra implementation work",
    "Adds exception cases before settling on the main classification",
    "Adds sensible exceptions after stating the main answer",
    "Answers compactly but with correct core reasoning",
    "Uses concrete examples to justify decisions",
    "Gives compact answers",
    "Reasons from practical user impact",
    "Uses tentative phrasing when unsure but lands on correct concepts",
    "Answers briefly but with relevant justification",
    "Adds cautious caveats about exceptions",
    "Gives compact but conceptually complete answers",
    "Adds practical follow-up checks without prompting",
    "Answers with sound general reasoning even when the prompt requires finer rule distinction",
    "May first choose a broader rule before selecting the specific one tested",
    "Echoes the just-learned rule set to confirm understanding"
  ],
  "successful_strategies": [
    "Affirm then refine",
    "Use simple native-vs-ARIA contrasts",
    "Affirm the correct core answer, then refine with a concrete edge-case clarification",
    "Ask what native HTML already provides",
    "Use a familiar element before contrasting with ARIA alternatives",
    "Confirm the core rule, then test it on contrasting markup examples",
    "Tie the example back to the named ARIA rule explicitly",
    "Use contrastive markup examples",
    "Ask what native HTML gives automatically",
    "Present simple mixed examples and ask first: is this element interactive?",
    "Tie each example to the specific ARIA rule being applied",
    "Contrast visible text buttons with icon-only buttons",
    "Ask whether the element already has an accessible name from native HTML",
    "Use short code examples",
    "Ask whether the control has an accessible name without relying on hidden decorative content",
    "Contrast redundant ARIA with necessary ARIA",
    "Use concrete button examples",
    "Ask about likely screen reader output",
    "Contrast named vs unnamed interactive controls",
    "Use simple native button contrasts",
    "Ask whether native HTML already provides the needed name",
    "Use mixed native-vs-custom examples",
    "Ask for both the rule satisfied and the additional validation check",
    "Ask for the exact rule name/concept, then contrast it with nearby similar rules",
    "Use near-miss examples to sharpen classification precision",
    "Prompting for the exact rule name",
    "Using interactive native elements as concrete contrast cases",
    "Use an explicit bridge from prior pattern to the new comparison task"
  ],
  "updated_at": "datetime.datetime(2026, 4, 8, 15, 36, 15, 204403, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```
</details>

---

## Final State

### Session State
```json
{
  "session_id": "guided-test-152804",
  "student_id": "test-conv-152804",
  "active_objective_id": "27075442-6261-4c6d-ad8d-4c3de134b366",
  "current_stage": "introduction",
  "turns_on_objective": 1,
  "readiness_score": null,
  "mini_assessment_progress": {
    "asked": 3,
    "correct": 2
  },
  "final_assessment_progress": {
    "asked": 5,
    "correct": 4
  },
  "stage_summary": "Final: 4/5 → mastered",
  "started_at": "datetime.datetime(2026, 4, 8, 15, 28, 4, 872875, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))",
  "runtime_cache": {
    "lesson_state": {
      "concepts": [
        {
          "id": "scope_as_comparison_lens",
          "label": "A standard can be compared by its target or scope",
          "status": "not_covered"
        },
        {
          "id": "meaning_of_scope",
          "label": "Meaning of scope in this objective",
          "status": "not_covered"
        },
        {
          "id": "wcag_web_content_family",
          "label": "WCAG as a web content guidance family",
          "status": "not_covered"
        },
        {
          "id": "wcag_versions_one_line",
          "label": "WCAG 2.0, 2.1, and 2.2 are versions in one line",
          "status": "not_covered"
        },
        {
          "id": "wcag_versions_extend_coverage",
          "label": "Later WCAG versions extend earlier coverage",
          "status": "not_covered"
        },
        {
          "id": "atag_authoring_tool_guidance",
          "label": "ATAG 2.0 as authoring tool guidance",
          "status": "not_covered"
        },
        {
          "id": "atag_influences_tool_design",
          "label": "How ATAG influences design: tool accessibility and support for accessible output",
          "status": "not_covered"
        },
        {
          "id": "en301549_broader_framework",
          "label": "EN 301 549 as a broader accessibility requirements framework",
          "status": "not_covered"
        },
        {
          "id": "en301549_influences_broader_design",
          "label": "How EN 301 549 influences design: broader product, service, and procurement framing",
          "status": "not_covered"
        },
        {
          "id": "compare_all_three_families_by_scope",
          "label": "Compare all three families by scope",
          "status": "not_covered"
        },
        {
          "id": "classify_practical_scenarios",
          "label": "Classify practical scenarios by primary design influence",
          "status": "not_covered"
        },
        {
          "id": "handle_overlap_borderline_scenarios",
          "label": "Handle overlap and borderline scenarios",
          "status": "not_covered"
        }
      ],
      "pending_check": "Can the learner compare standards by what they apply to rather than by title alone?",
      "active_concept": "scope_as_comparison_lens",
      "teaching_order": [
        "scope_as_comparison_lens",
        "meaning_of_scope",
        "wcag_web_content_family",
        "wcag_versions_one_line",
        "wcag_versions_extend_coverage",
        "atag_authoring_tool_guidance",
        "atag_influences_tool_design",
        "en301549_broader_framework",
        "en301549_influences_broader_design",
        "compare_all_three_families_by_scope",
        "classify_practical_scenarios",
        "handle_overlap_borderline_scenarios"
      ],
      "bridge_back_target": "scope_as_comparison_lens"
    },
    "objective_id": "27075442-6261-4c6d-ad8d-4c3de134b366",
    "retrieved_at": "2026-04-08T15:36:01.759944",
    "teaching_plan": "## 1. objective_text\nCompare the scope of WCAG (2.0, 2.1, 2.2), ATAG 2.0, and EN 301 549, and **identify** how each set of requirements influences web accessibility design.\n\n## 2. plain_language_goal\nUnderstand what each of these accessibility standards covers, how they differ, and how each one affects the way accessible websites and related tools are designed.\n\n## 3. mastery_definition\nA student has mastered this objective when they can:\n\n- correctly distinguish WCAG 2.0, WCAG 2.1, WCAG 2.2, ATAG 2.0, and EN 301 549 by scope\n- explain, at a high level, what kind of thing each standard applies to\n- compare the WCAG versions in terms of expanding scope across versions without confusing them as separate unrelated standards\n- identify whether a design scenario is primarily influenced by:\n  - WCAG requirements for web content\n  - ATAG requirements for authoring tools\n  - EN 301 549 as a broader accessibility procurement/regulatory standard\n- justify their classification using the scope of the standard, not memorized keywords\n- avoid major category errors, such as treating ATAG as a web content standard or EN 301 549 as merely another WCAG version\n\n## 4. objective_type\n- conceptual understanding\n- comparison\n- classification\n- decision-making\n- application\n\n## 5. prerequisite_knowledge\n\n### essential prerequisites\n- Basic understanding of what “web accessibility” means\n- Awareness that accessibility guidance can apply to different targets, such as:\n  - web content/pages\n  - software/tools used to create content\n  - broader ICT products/services or compliance frameworks\n- Basic familiarity with the idea of a “standard” or “guideline” as a set of requirements used to guide design or evaluation\n\n### helpful but nonessential prerequisites\n- Prior exposure to WCAG’s name and purpose\n- General awareness of legal/procurement compliance in accessibility\n- Familiarity with roles in digital product work, such as designer, developer, evaluator, procurement/compliance lead\n- Awareness that standards can evolve by version\n\n## 6. prerequisite_gap_policy\nIf the learner lacks essential prerequisites, the tutor should pause the objective and briefly establish only the minimum framing needed:\n\n- clarify what accessibility standards are for\n- distinguish “what is being evaluated or designed”:\n  - content\n  - tools\n  - broader ICT systems/procurement requirements\n- confirm that the learner can reason about scope before introducing named standards\n\nThe tutor should not launch into detailed accessibility history or legal instruction. If the learner cannot yet distinguish target-of-application, the tutor should remediate that first because the objective depends on classification by scope.\n\n## 7. concept_decomposition\n1. A standard/guideline can be compared by the thing it applies to, not just by its title.\n2. “Scope” means the domain, artifact, or context a set of requirements covers.\n3. WCAG is a family of requirements aimed at accessibility of web content.\n4. WCAG 2.0, 2.1, and 2.2 are successive versions within the same WCAG line.\n5. Later WCAG versions extend prior coverage rather than representing unrelated standards.\n6. ATAG 2.0 applies to authoring tools rather than to published web content itself.\n7. Authoring tools influence accessibility both by being accessible to authors and by supporting production of accessible content.\n8. EN 301 549 has broader scope than WCAG because it is not limited to web content alone.\n9. EN 301 549 functions as a broader accessibility requirements framework often used in procurement/regulatory contexts.\n10. A requirement set influences design differently depending on whether it targets:\n   - content design\n   - tool design\n   - broader product/service/compliance design\n11. In practical scenarios, the right standard can be identified by asking what is being designed, evaluated, or procured.\n12. Some scenarios involve overlap, but one standard may be primary depending on the design decision being made.\n\n## 8. dependency_order\n\n### Recommended order with dependencies\n1. **A standard can be compared by target/scope**  \n   - foundational; depends only on prerequisite knowledge\n\n2. **Meaning of “scope” in this objective**  \n   - depends on 1\n\n3. **WCAG as web content guidance family**  \n   - depends on 1, 2\n\n4. **WCAG 2.0/2.1/2.2 are versions in one line**  \n   - depends on 3\n\n5. **Later WCAG versions extend earlier coverage**  \n   - depends on 4\n\n6. **ATAG 2.0 as authoring tool guidance**  \n   - depends on 1, 2\n\n7. **How ATAG influences design: tool accessibility + support for accessible output**  \n   - depends on 6\n\n8. **EN 301 549 as broader accessibility requirements framework**  \n   - depends on 1, 2\n\n9. **How EN 301 549 influences design: broader product/service/procurement framing**  \n   - depends on 8\n\n10. **Compare all three families by scope**  \n   - depends on 3, 5, 7, 9\n\n11. **Classify practical scenarios by which standard most directly influences the design decision**  \n   - depends on 10\n\n12. **Handle overlap/borderline scenarios**  \n   - depends on 11\n\n### Why this sequence is instructionally sound\n- It begins with the abstract comparison principle—scope—before introducing names.\n- It introduces WCAG first because it is the most likely known anchor and easiest reference point.\n- It treats the WCAG versions as related before comparison to other standards, reducing version confusion.\n- It then contrasts ATAG and EN 301 549 by target, creating clean category boundaries.\n- Only after the student has clear scope distinctions does it move to “influence on design,” which requires applying those distinctions to realistic decisions.\n- Borderline overlap cases are deferred until after basic classification to avoid early overload.\n\n## 9. likely_misconceptions\n- Thinking WCAG 2.0, 2.1, and 2.2 are separate competing standards rather than versions in one lineage\n- Assuming newer WCAG versions completely replace conceptual continuity with earlier versions\n- Treating ATAG as rules for website pages rather than for tools used to create content\n- Assuming ATAG only concerns whether the tool’s own interface is accessible, and not whether it supports creation of accessible content\n- Treating EN 301 549 as just a European version of WCAG\n- Assuming EN 301 549 only matters to lawyers or procurement teams and has no design implications\n- Believing all accessibility requirements directly tell web page designers the same kinds of things\n- Confusing “who uses the standard” with “what the standard applies to”\n- Assuming “scope” means geographic scope only, rather than applicability to a type of artifact or system\n- Overgeneralizing that any accessibility issue on a website must always be classified only under WCAG, even when the decision is about the content management tool or procurement framework\n\n## 10. explanation_vs_question_strategy\n\n### 1. A standard can be compared by target/scope\n- **Start mode:** diagnostic question\n- **Why:** reveals whether the learner can already distinguish standards by what they govern rather than by title recognition\n\n### 2. Meaning of “scope” in this objective\n- **Start mode:** brief explanation\n- **Why:** terminology here needs a precise anchor to prevent confusion with legal/geographic scope\n\n### 3. WCAG as web content guidance family\n- **Start mode:** guided questioning\n- **Why:** many learners have partial prior knowledge; questioning can activate it without overexplaining\n\n### 4. WCAG 2.0/2.1/2.2 are versions in one line\n- **Start mode:** brief explanation\n- **Why:** version lineage is a compact fact structure that should be established cleanly to prevent false branching\n\n### 5. Later WCAG versions extend earlier coverage\n- **Start mode:** contrastive example\n- **Why:** comparing “same family, later version” versus “different standard entirely” helps solidify the relationship\n\n### 6. ATAG 2.0 as authoring tool guidance\n- **Start mode:** guided questioning\n- **Why:** students can often infer this from “authoring tool” once prompted; inference supports retention\n\n### 7. How ATAG influences design: tool accessibility + support for accessible output\n- **Start mode:** worked example\n- **Why:** influence on design is easier to grasp through a concrete tool scenario than through abstract description\n\n### 8. EN 301 549 as broader accessibility requirements framework\n- **Start mode:** brief explanation\n- **Why:** many learners are less likely to know this; concise framing reduces confusion\n\n### 9. How EN 301 549 influences design: broader product/service/procurement framing\n- **Start mode:** worked example\n- **Why:** the indirect path from standard to design decision is clearer when tied to a procurement or product requirement example\n\n### 10. Compare all three families by scope\n- **Start mode:** contrastive example\n- **Why:** side-by-side comparison is the core skill and benefits from explicit contrasts\n\n### 11. Classify practical scenarios by primary design influence\n- **Start mode:** guided questioning\n- **Why:** classification with justification is the target performance and suits Socratic probing\n\n### 12. Handle overlap/borderline scenarios\n- **Start mode:** diagnostic question\n- **Why:** tricky cases are best used to test whether the learner can reason beyond memorized labels\n\n## 11. socratic_question_goals\n\n### Stage 1: Scope as comparison lens\n- diagnose prior knowledge about standards\n- surface whether learner thinks titles/versions alone determine meaning\n- establish the habit of asking “what does this apply to?”\n\n### Stage 2: WCAG family framing\n- confirm learner recognizes WCAG as content-focused\n- test whether learner can distinguish versions from separate standards\n- reveal misconceptions about versioning and extension\n\n### Stage 3: ATAG\n- prompt learner to infer target from the name/context\n- check whether learner distinguishes tool requirements from content requirements\n- reveal whether learner sees both dimensions of ATAG’s design influence\n\n### Stage 4: EN 301 549\n- test whether learner can recognize broader applicability\n- reveal confusion between WCAG and procurement/regulatory frameworks\n- check whether learner can identify indirect design influence through broader requirements\n\n### Stage 5: Comparison across all standards\n- force comparison by scope\n- require learner to articulate one meaningful distinction at a time\n- test whether learner can explain why a scenario belongs primarily to one standard\n\n### Stage 6: Borderline and transfer\n- test transfer to unfamiliar scenarios\n- check reasoning when more than one standard seems relevant\n- require justification of the “primary influence” rather than guessing\n\n## 12. example_requirements\n\n### simplest introductory example\n- A simple public webpage design decision, such as making page content accessible, to anchor WCAG as content-focused\n\n### at least one contrastive example\n- A content design scenario versus an authoring tool design scenario\n- Example pair:\n  - designing a website page template\n  - designing a CMS editor that helps authors add alternative text\n\n### at least one borderline or tricky case\n- A scenario where a website accessibility issue is partly caused by the authoring tool, requiring the learner to decide whether the primary influence is WCAG or ATAG\n- A scenario where a public-sector procurement requirement references broader accessibility expectations, inviting EN 301 549 rather than only WCAG\n\n### at least one transfer scenario\n- A scenario involving selection or procurement of a platform, service, or ICT solution where the learner must identify EN 301 549 as the broader framework influencing design requirements\n- A scenario involving updating from an earlier WCAG version to a later one, where the learner must reason about expanded coverage without treating the newer version as unrelated\n\n### example design constraints\n- Examples should stay high-level and scope-oriented\n- Avoid requiring detailed memorization of individual success criteria or legal clauses\n- Each example should clearly identify the artifact being designed: content, tool, or broader ICT/procurement context\n\n## 13. retrieval_requirements\n\n### must-retrieve\n- High-level definitions/scope statements for:\n  - WCAG 2.0\n  - WCAG 2.1\n  - WCAG 2.2\n  - ATAG 2.0\n  - EN 301 549  \n  Reason: accurate scope comparison is the central learning task.\n- Reliable statement that WCAG 2.1 and 2.2 build on prior WCAG versions within the same line  \n  Reason: necessary to avoid version confusion.\n- High-level description of ATAG’s dual focus:\n  - accessibility of the authoring tool interface\n  - support for creation of accessible content  \n  Reason: core to understanding design influence.\n- High-level description of EN 301 549 as broader accessibility requirements for ICT/procurement context  \n  Reason: needed to contrast with WCAG and ATAG.\n- A small set of accurate real-world scenario types illustrating:\n  - web content design\n  - authoring tool design\n  - procurement/compliance-driven product selection/design  \n  Reason: needed for classification and application.\n\n### optional-supporting\n- Official publication names/issuing bodies for credibility and precision\n- A simple mapping note about how EN 301 549 may incorporate/reference web accessibility requirements  \n  Reason: helps with overlap cases, but should not dominate the lesson.\n- Timeline/version-release context for WCAG 2.0, 2.1, 2.2  \n  Reason: useful for advanced learners, not essential to the objective.\n- Role-based examples for designers, developers, tool vendors, and procurement teams  \n  Reason: supports transfer to workplace contexts.\n\n## 14. assessment_evidence\n\n### quick understanding checks\n- Ask the learner to match each standard/version to its primary scope\n- Ask whether WCAG 2.1 is best understood as:\n  - a separate category from WCAG\n  - a later version in the WCAG family\n- Ask which standard most directly applies to an authoring tool\n\n### application task\n- Provide 3–5 short design scenarios and require the learner to identify which standard most directly influences the design decision and explain why\n- Scenarios should include:\n  - content/page design\n  - authoring tool behavior\n  - procurement or broader ICT requirement\n\n### transfer task\n- Give a new scenario not previously discussed, such as selecting a platform under institutional accessibility requirements, and ask the learner to reason out which requirement set is primary and what kind of design influence it has\n- Or ask the learner to compare how updating from WCAG 2.0 to 2.2 differs from switching from WCAG to ATAG\n\n### misconception check\n- Present statements for correction, such as:\n  - “ATAG is mainly for checking whether a web page is accessible.”\n  - “EN 301 549 is just another WCAG version.”\n  - “WCAG 2.2 applies to a different kind of thing than WCAG 2.0.”\n- Require explanation of what is wrong in each statement\n\n## 15. adaptation_notes\n\n### beginner\n- Spend more time on the meaning of scope and target-of-application\n- Use fewer standards in memory at once; establish WCAG first, then ATAG, then EN 301 549\n- Keep examples concrete and role-based\n- Avoid detailed compliance nuance\n\n### intermediate learner\n- Move more quickly through definitions\n- Emphasize comparison and scenario classification\n- Introduce overlap cases sooner\n- Ask for justification using “what is being designed/evaluated/procured?”\n\n### advanced learner\n- Compress prerequisite review\n- Use more ambiguous scenarios with overlapping applicability\n- Probe reasoning about how broader frameworks can shape design decisions indirectly\n- Invite concise comparison across versions and frameworks without drifting into legal detail\n\n## 16. boundaries_and_non_goals\nThis lesson should **not** teach:\n\n- detailed WCAG success criteria or conformance levels\n- detailed legal requirements of specific jurisdictions\n- full history of W3C accessibility standards\n- UAAG or other accessibility standards not named in the objective\n- deep implementation techniques for meeting any standard\n- detailed procurement process mechanics\n- exhaustive differences between WCAG 2.0, 2.1, and 2.2 at criterion level\n- accessibility testing procedures in depth\n\nThese belong to separate objectives and would overload a scope-comparison lesson.\n\n## 17. concise_plan_summary\n- Start by anchoring comparison around **scope**: what each standard applies to.\n- Establish WCAG first as a **web content** family, then clarify that 2.0/2.1/2.2 are **versions in one lineage**.\n- Contrast ATAG as applying to **authoring tools**, not published web content.\n- Introduce EN 301 549 as a **broader accessibility requirements framework** beyond just web content.\n- Teach “influence on design” by connecting each standard to a different design target: content, tools, or broader product/procurement context.\n- Use contrastive and scenario-based questioning to build classification skill.\n- Delay overlap/borderline cases until after the learner can classify clear examples.\n- Assess mastery through justified scenario classification and correction of common scope misconceptions.",
    "objective_text": "Compare the scope of WCAG (2.0, 2.1, 2.2), ATAG 2.0, and EN 301 549, and **identify** how each set of requirements influences web accessibility design.",
    "retrieval_bundle": {
      "version": 1,
      "coverage": {
        "hit_chars": 13302,
        "hit_count": 5,
        "budget_chars": 20000,
        "missing_checks": [],
        "required_checks": {
          "conformance_rollup_rule": false,
          "techniques_vs_requirements": true
        }
      },
      "sections": {
        "risks": [
          {
            "title": "Failure and Misuse Notes for Techniques for 1.1.1 Non-text Content",
            "content": "Failure techniques:\n- **F3**: Failure of Success Criterion 1.1.1 due to using CSS to include images that convey important information\n- **F13**: Failure of Success Criterion 1.1.1 and 1.4.1 due to having a text alternative that does not include information that is conveyed by color differences in the image\n- **F20**: Failure of Success Criterion 1.1.1 and 4.1.2 due to not updating text alternatives when changes to non-text content occur\n- **F30**: Failure of Success Criterion 1.1.1 and 1.2.1 due to using text alternatives that are not alternatives (e.g., filenames or placeholder text)\n- **F38**: Failure of Success Criterion 1.1.1 due to not marking up decorative images in HTML in a way that allows assistive technology to ignore them\n- **F39**: Failure of Success Criterion 1.1.1 due to providing a text alternative that is not null (e.g., alt=\"spacer\" or alt=\"image\") for images that should be ignored by assistive technology\n- **F65**: Failure of Success Criterion 1.1.1 due to omitting the alt attribute or text alternative on img elements, area elements, and input elements of type \"image\"\n- **F67**: Failure of Success Criterion 1.1.1 and 1.2.1 due to providing long descriptions for non-text content that does not serve the same purpose or does not present the same information\n- **F71**: Failure of Success Criterion 1.1.1 due to using text look-alikes to represent text without pr...",
            "source_args": {
              "ref_id": "1.1.1"
            },
            "source_tool": "get_techniques_for_criterion"
          }
        ],
        "examples": [],
        "core_rules": [
          {
            "title": "1.1.1 Non-text Content",
            "content": "**Level:** A | **Principle:** 1 Perceivable | **Guideline:** 1.1 Text Alternatives\n\nAll non-text content that is presented to the user has a text alternative that serves the equivalent purpose, except for the situations listed below.",
            "source_args": {
              "ref_id": "1.1.1"
            },
            "source_tool": "get_success_criteria_detail"
          }
        ],
        "definitions": [],
        "contrast_cases": [],
        "decision_rules": [],
        "structural_context": [
          {
            "title": "WCAG 2.2 Principles",
            "content": "# WCAG 2.2 Principles\n\n**1. Perceivable**\nInformation and user interface components must be presentable to users in ways they can perceive.\nURL: https://www.w3.org/TR/WCAG22/#perceivable\n\n**2. Operable**\nUser interface components and navigation must be operable.\nURL: https://www.w3.org/TR/WCAG22/#operable\n\n**3. Understandable**\nInformation and the operation of the user interface must be understandable.\nURL: https://www.w3.org/TR/WCAG22/#understandable\n\n**4. Robust**\nContent must be robust enough that it can be interpreted by a wide variety of user agents, including assistive technologies.\nURL: https://www.w3.org/TR/WCAG22/#robust",
            "source_args": {},
            "source_tool": "list_principles"
          }
        ],
        "technique_patterns": [
          {
            "title": "Techniques for 1.1.1 Non-text Content",
            "content": "Sufficient techniques:\n**Situation A: If a short description can serve the same purpose and present the same information as the non-text content:**\n - **G94**: Providing short text alternative for non-text content that serves the same purpose and presents the same information as the non-text content\n *Short text alternative techniques for Situation A*\n - **ARIA6**: Using aria-label to provide labels for objects\n - **ARIA10**: Using aria-labelledby to provide a text alternative for non-text content\n - **G196**: Using a text alternative on one item within a group of images that describes all items in the group\n - **H2**: Combining adjacent image and text links for the same resource\n - **H37**: Using alt attributes on img elements\n - **H53**: Using the body of the object element\n - **H86**: Providing text alternatives for emojis, emoticons, ASCII art, and leetspeak\n - **PDF1**: Applying text alternatives to images with the Alt entry in PDF documents\n**Situation B: If a short description can not serve the same purpose and present the same information as the non-text content (e.g., a chart or diagram):**\n - **G95**: Providing short text alternatives that provide a brief description of the non-text content\n *Short text alternative techniques for Situation B*\n - **ARIA6**: Using aria-label to provide labels for objects\n - **ARIA10**: Using aria-labelledby to provide a text alternative for non-text content\n - **G196**: Using a text alternative on one item within a group of images that describes all items in the group\n - **H2**: Combining adjacent image and text links for the same resource\n - **H37**: Using alt attributes on img elements\n - **H53**: Using the body of the object element\n - **H86**: Providing text alternatives for emojis, emoticons, ASCII art, and leetspeak\n - **PDF1**: Applying text alternatives to images with the Alt entry in PDF documents\n *Long text alternative techniques for Situation B*\n - **ARIA15**: Using aria-describedby to provide descriptions of images\n - **G73**: Providing a long description in another location with a link to it that is immediately adjacent to the non-text content\n - **G74**: Providing a long description in text near the non...",
            "source_args": {
              "ref_id": "1.1.1"
            },
            "source_tool": "get_techniques_for_criterion"
          }
        ]
      },
      "objective_text": "Compare the scope of WCAG (2.0, 2.1, 2.2), ATAG 2.0, and EN 301 549, and **identify** how each set of requirements influences web accessibility design."
    },
    "teaching_content": "## CORE FACTS\n### 1.1.1 Non-text Content\n**Level:** A | **Principle:** 1 Perceivable | **Guideline:** 1.1 Text Alternatives\n\nAll non-text content that is presented to the user has a text alternative that serves the equivalent purpose, except for the situations listed below.\n\n## TECHNIQUE PATTERNS\n### Techniques for 1.1.1 Non-text Content\nSufficient techniques:\n**Situation A: If a short description can serve the same purpose and present the same information as the non-text content:**\n - **G94**: Providing short text alternative for non-text content that serves the same purpose and presents the same information as the non-text content\n *Short text alternative techniques for Situation A*\n - **ARIA6**: Using aria-label to provide labels for objects\n - **ARIA10**: Using aria-labelledby to provide a text alternative for non-text content\n - **G196**: Using a text alternative on one item within a group of images that describes all items in the group\n - **H2**: Combining adjacent image and text links for the same resource\n - **H37**: Using alt attributes on img elements\n - **H53**: Using the body of the object element\n - **H86**: Providing text alternatives for emojis, emoticons, ASCII art, and leetspeak\n - **PDF1**: Applying text alternatives to images with the Alt entry in PDF documents\n**Situation B: If a short description can not serve the same purpose and present the same information as the non-text content (e.g., a chart or diagram):**\n - **G95**: Providing short text alternatives that provide a brief description o...\n\n## RISKS / MISUSE\n### Failure and Misuse Notes for Techniques for 1.1.1 Non-text Content\nFailure techniques:\n- **F3**: Failure of Success Criterion 1.1.1 due to using CSS to include images that convey important information\n- **F13**: Failure of Success Criterion 1.1.1 and 1.4.1 due to having a text alternative that does not include information that is conveyed by color differences in the image\n- **F20**: Failure of Success Criterion 1.1.1 and 4.1.2 due to not updating text alternatives when changes to non-text content occur\n- **F30**: Failure of Success Criterion 1.1.1 and 1.2.1 due to using text alternatives that are not alternatives (e.g., filenames or placeholder text)\n- **F38**: Failure of Success Criterion 1.1.1 due to not marking up decorative images in HTML in a way that allows assistive technology to ignore them\n- **F39**: Failure of Success Criterion 1.1.1 due to providing a text alternative that is not null (e.g., alt=\"spacer\" or alt=\"image\") for images that sho...\n\n## STRUCTURE NOTES\n### WCAG 2.2 Principles\n# WCAG 2.2 Principles\n\n**1. Perceivable**\nInformation and user interface components must be presentable to users in ways they can perceive.\nURL: https://www.w3.org/TR/WCAG22/#perceivable\n\n**2. Operable**\nUser interface components and navigation must be operable.\nURL: https://www.w3.org/TR/WCAG22/#operable\n\n**3. Understandable**\nInformation and the operation of the user interface must be understandable.\nURL: https://www.w3.org/TR/WCAG22/#understandable\n\n**4. Robust**\nContent must be robust enough that it can be interpreted by a wide variety of user agents, including assistive technologies.\nURL: https://www.w3.org/TR/WCAG22/#robust"
  }
}
```

### Mastery
```json
[
  {
    "student_id": "test-conv-152804",
    "objective_id": "27075442-6261-4c6d-ad8d-4c3de134b366",
    "mastery_level": "not_attempted",
    "evidence_summary": "No demonstrated reasoning yet about WCAG/ATAG/EN 301 549 scope.",
    "misconceptions": [],
    "mini_assessment_score": null,
    "final_assessment_score": null,
    "turns_spent": 0,
    "last_assessed_at": "datetime.datetime(2026, 4, 8, 15, 36, 15, 209930, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
  },
  {
    "student_id": "test-conv-152804",
    "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
    "mastery_level": "mastered",
    "evidence_summary": "Final assessment 4/5",
    "misconceptions": [],
    "mini_assessment_score": null,
    "final_assessment_score": null,
    "turns_spent": 3,
    "last_assessed_at": "datetime.datetime(2026, 4, 8, 15, 33, 47, 627077, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
  }
]
```

### Misconceptions
```json
[
  {
    "id": 49,
    "student_id": "test-conv-152804",
    "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
    "misconception_text": "May classify role=\"presentation\" on a button under generic semantic override instead of the specific Rule 4 prohibition.",
    "source_question_id": null,
    "identified_at": "datetime.datetime(2026, 4, 8, 15, 33, 36, 135419, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))",
    "resolved_at": null
  },
  {
    "id": 48,
    "student_id": "test-conv-152804",
    "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
    "misconception_text": "May overapply accessible-name reasoning to non-interactive generic elements",
    "source_question_id": null,
    "identified_at": "datetime.datetime(2026, 4, 8, 15, 32, 11, 865633, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))",
    "resolved_at": null
  },
  {
    "id": 47,
    "student_id": "test-conv-152804",
    "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
    "misconception_text": "May treat duplicated aria-label as merely redundant without first asking whether the element needs ARIA at all",
    "source_question_id": null,
    "identified_at": "datetime.datetime(2026, 4, 8, 15, 32, 11, 861047, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))",
    "resolved_at": null
  }
]
```

### Lesson State (final)
```json
{
  "active_concept": "scope_as_comparison_lens",
  "pending_check": "Can the learner compare standards by what they apply to rather than by title alone?",
  "bridge_back_target": "scope_as_comparison_lens",
  "teaching_order": [
    "scope_as_comparison_lens",
    "meaning_of_scope",
    "wcag_web_content_family",
    "wcag_versions_one_line",
    "wcag_versions_extend_coverage",
    "atag_authoring_tool_guidance",
    "atag_influences_tool_design",
    "en301549_broader_framework",
    "en301549_influences_broader_design",
    "compare_all_three_families_by_scope",
    "classify_practical_scenarios",
    "handle_overlap_borderline_scenarios"
  ],
  "concepts": [
    {
      "id": "scope_as_comparison_lens",
      "label": "A standard can be compared by its target or scope",
      "status": "not_covered"
    },
    {
      "id": "meaning_of_scope",
      "label": "Meaning of scope in this objective",
      "status": "not_covered"
    },
    {
      "id": "wcag_web_content_family",
      "label": "WCAG as a web content guidance family",
      "status": "not_covered"
    },
    {
      "id": "wcag_versions_one_line",
      "label": "WCAG 2.0, 2.1, and 2.2 are versions in one line",
      "status": "not_covered"
    },
    {
      "id": "wcag_versions_extend_coverage",
      "label": "Later WCAG versions extend earlier coverage",
      "status": "not_covered"
    },
    {
      "id": "atag_authoring_tool_guidance",
      "label": "ATAG 2.0 as authoring tool guidance",
      "status": "not_covered"
    },
    {
      "id": "atag_influences_tool_design",
      "label": "How ATAG influences design: tool accessibility and support for accessible output",
      "status": "not_covered"
    },
    {
      "id": "en301549_broader_framework",
      "label": "EN 301 549 as a broader accessibility requirements framework",
      "status": "not_covered"
    },
    {
      "id": "en301549_influences_broader_design",
      "label": "How EN 301 549 influences design: broader product, service, and procurement framing",
      "status": "not_covered"
    },
    {
      "id": "compare_all_three_families_by_scope",
      "label": "Compare all three families by scope",
      "status": "not_covered"
    },
    {
      "id": "classify_practical_scenarios",
      "label": "Classify practical scenarios by primary design influence",
      "status": "not_covered"
    },
    {
      "id": "handle_overlap_borderline_scenarios",
      "label": "Handle overlap and borderline scenarios",
      "status": "not_covered"
    }
  ]
}
```

### Learner Memory
```json
{
  "student_id": "test-conv-152804",
  "summary": "Learner can restate a distilled rule pattern from the prior objective.",
  "strengths": [
    "Comes in with relevant prior awareness",
    "States uncertainty clearly",
    "Makes correct tentative judgments",
    "Surfaces uncertainty explicitly",
    "Can articulate multiple built-in semantics once prompted",
    "Builds from examples to principle",
    "Reasons concretely about behavior and naming",
    "Builds correct rule statements from examples",
    "Uses causal reasoning, not just recall",
    "Checks edge cases productively",
    "Uses causal reasoning",
    "Connects semantics to behavior",
    "Explains tradeoffs in implementation terms",
    "Spots duplicate labeling patterns",
    "Reasoned aloud instead of guessing",
    "Applies accessible-name concept correctly to native buttons",
    "Recognizes redundancy in ARIA usage",
    "Uses edge cases productively without losing the main rule",
    "Applies accessible-name reasoning correctly",
    "Selects practical fixes",
    "Distinguishes hidden decorative content from usable labels",
    "Concise but conceptually accurate reasoning",
    "Connects missing accessible name to real user impact",
    "Applies prior clarification about naming the button, not the icon",
    "Applies accessible-name reasoning accurately to native buttons",
    "Makes compact, conceptually correct judgments",
    "Can explain why ARIA is unnecessary when HTML already provides the name",
    "Identifies accessible names from visible text",
    "Remembers custom controls need more than a role",
    "Connects non-native elements with missing built-in behavior",
    "Explains semantic harm clearly",
    "Connects native elements to built-in meaning",
    "Understands core semantics of native interactive elements",
    "Can correct to the exact rule after brief feedback",
    "Gives concise rule-based explanations",
    "Summarizes core patterns compactly"
  ],
  "support_needs": [
    "Needs crisp confirmation plus refinement of partial mental models",
    "Needs example-based contrast to stabilize understanding",
    "Needs crisp clarification on edge cases before generalizing rules",
    "Needs continued example-based application to stabilize rule use",
    "Benefits from explicit connection between examples and named rules",
    "Brief confirmation when turning an example into a named rule",
    "More contrastive examples to stabilize transfer",
    "Needs brief confirmation before broader generalization across all rules",
    "Needs help checking element purpose before evaluating ARIA naming",
    "Needs clearer distinction between unnecessary and redundant ARIA",
    "Needs continued practice classifying examples by specific ARIA rule",
    "Should reinforce distinction between unnecessary ARIA and redundant ARIA across element types",
    "Needs broader rule classification practice beyond naming cases",
    "Needs broader practice classifying ARIA misuse across multiple rules",
    "Needs refinement on when differing ARIA labels may be inappropriate despite being possible",
    "Needs broader rule-classification practice across mixed ARIA misuse examples",
    "More precise mapping from examples to exact ARIA rule numbers/concepts",
    "Reinforcement on Rule 4 as distinct from general semantic overrides",
    "Needs clear transition when objective changes"
  ],
  "tendencies": [
    "Uses tentative phrasing when unsure",
    "Engages readily at the start of a topic",
    "Checks exceptions immediately after a rule-of-thumb",
    "Tests edge cases first, then integrates the clarification",
    "Gives compact but conceptually relevant answers",
    "Frames correct ideas tentatively",
    "Asks whether there is an exception or extra nuance",
    "Responds strongly to native-vs-custom comparisons",
    "Frames answers around risk and extra implementation work",
    "Adds exception cases before settling on the main classification",
    "Adds sensible exceptions after stating the main answer",
    "Answers compactly but with correct core reasoning",
    "Uses concrete examples to justify decisions",
    "Gives compact answers",
    "Reasons from practical user impact",
    "Uses tentative phrasing when unsure but lands on correct concepts",
    "Answers briefly but with relevant justification",
    "Adds cautious caveats about exceptions",
    "Gives compact but conceptually complete answers",
    "Adds practical follow-up checks without prompting",
    "Answers with sound general reasoning even when the prompt requires finer rule distinction",
    "May first choose a broader rule before selecting the specific one tested",
    "Echoes the just-learned rule set to confirm understanding"
  ],
  "successful_strategies": [
    "Affirm then refine",
    "Use simple native-vs-ARIA contrasts",
    "Affirm the correct core answer, then refine with a concrete edge-case clarification",
    "Ask what native HTML already provides",
    "Use a familiar element before contrasting with ARIA alternatives",
    "Confirm the core rule, then test it on contrasting markup examples",
    "Tie the example back to the named ARIA rule explicitly",
    "Use contrastive markup examples",
    "Ask what native HTML gives automatically",
    "Present simple mixed examples and ask first: is this element interactive?",
    "Tie each example to the specific ARIA rule being applied",
    "Contrast visible text buttons with icon-only buttons",
    "Ask whether the element already has an accessible name from native HTML",
    "Use short code examples",
    "Ask whether the control has an accessible name without relying on hidden decorative content",
    "Contrast redundant ARIA with necessary ARIA",
    "Use concrete button examples",
    "Ask about likely screen reader output",
    "Contrast named vs unnamed interactive controls",
    "Use simple native button contrasts",
    "Ask whether native HTML already provides the needed name",
    "Use mixed native-vs-custom examples",
    "Ask for both the rule satisfied and the additional validation check",
    "Ask for the exact rule name/concept, then contrast it with nearby similar rules",
    "Use near-miss examples to sharpen classification precision",
    "Prompting for the exact rule name",
    "Using interactive native elements as concrete contrast cases",
    "Use an explicit bridge from prior pattern to the new comparison task"
  ],
  "updated_at": "datetime.datetime(2026, 4, 8, 15, 36, 15, 204403, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```

### Objective Memory
```json
{
  "student_id": "test-conv-152804",
  "objective_id": "038d7bf5-eb16-4ac0-a22b-42c8fa964d97",
  "summary": "Learner correctly mapped role=\"presentation\" on a button to the specific prohibition against using presentation/none on interactive elements.",
  "demonstrated_skills": [
    "Recognizes ARIA as supplemental rather than default",
    "Spots redundant ARIA on native button",
    "Connects native element to built-in behavior",
    "Explains what native HTML already provides",
    "Distinguishes native semantics from ARIA metadata",
    "Uses button example to justify why redundant ARIA is unnecessary",
    "States the prefer-native rule in plain language",
    "Justifies redundant ARIA on native button",
    "Connects Rule 1 to native role, keyboard support, focusability, and naming",
    "Applies the rule despite unusual visual styling",
    "Explains that ARIA can add semantics but not native behavior",
    "Contrasts native keyboard/focus support with custom ARIA controls",
    "Justifies Rule 1 with practical implementation risk",
    "Recognizes redundant ARIA on native controls",
    "Recognizes when aria-label can duplicate visible text",
    "Applies prior rule-of-thumb that ARIA should not be added automatically",
    "Identifies that visible button text provides the accessible name",
    "Recognizes redundant aria-label on a native button",
    "Distinguishes cases where aria-label may be needed, such as icon-only controls",
    "Recognizes that interactive elements need an accessible name",
    "Identifies that aria-hidden icon content does not name a button",
    "Chooses aria-label appropriately for an icon-only native button",
    "Distinguishes when ARIA naming is useful versus redundant",
    "Explains that the interactive element itself must be named",
    "Identifies the usability impact of an unlabeled button for screen reader users",
    "Applies accessible-name reasoning correctly to icon-only buttons",
    "Identifies when ARIA is unnecessary on native controls",
    "Recognizes visible button text as an accessible name source",
    "Distinguishes needed versus redundant aria-label usage",
    "Recognizes visible text can provide an accessible name for an interactive element",
    "Applies Rule 5 to a custom role=button example",
    "Connects custom ARIA controls to required keyboard operability",
    "Notes focusability as a necessary validity check for non-native controls",
    "Recognizes that native button semantics should not be stripped",
    "Understands role=\"presentation\" conflicts with meaningful interactive semantics",
    "Maps a flawed ARIA example to the exact violated rule",
    "Recognizes that buttons are interactive/focusable elements",
    "Distinguishes Rule 4 from the broader native-semantics override rule"
  ],
  "active_gaps": [
    "Has not yet explained what native HTML already provides",
    "Has not yet applied the idea to examples",
    "Needs confirmation that CSS styling does not alter native semantics",
    "Has not yet contrasted native semantics and ARIA in broader examples",
    "Has not yet applied Rule 1 across contrasting native vs custom examples",
    "Has not yet mapped judgments to the named ARIA rules",
    "Has not yet classified multiple contrasting examples",
    "Has not yet mapped flawed examples to specific ARIA rule violations beyond Rule 1",
    "Has not yet classified examples across the remaining ARIA rules",
    "Has not yet revise flawed examples using specific rule labels",
    "Needs to distinguish unnecessary ARIA from redundant ARIA in mixed examples",
    "Needs firmer application of accessible-name requirements only to interactive elements",
    "Needs practice classifying examples by rule violated",
    "Still needs broader rule classification across mixed examples",
    "Has not yet been assessed on keyboard requirements for custom ARIA widgets",
    "Has not yet classified mixed examples across all five ARIA rules",
    "Has not yet demonstrated Rule 3 keyboard requirements for custom controls",
    "Has not yet demonstrated Rule 4 on presentation/none misuse",
    "Has not yet demonstrated Rule 2 about changing native semantics",
    "Has not yet classified mixed examples by which ARIA rule is violated",
    "Has not yet demonstrated Rule 3, Rule 4, or Rule 2 in examples",
    "Has not yet demonstrated keyboard-support reasoning for custom ARIA controls",
    "Has not yet demonstrated Rule 4 about presentation/none on interactive elements",
    "Has not yet demonstrated Rule 2 about unjustified native semantic overrides",
    "Has not yet classified mixed examples by specific rule violated beyond naming and keyboard/focus checks",
    "Has not yet addressed presentation/none misuse or native semantic override in assessment",
    "Needs to identify Rule 4 specifically for presentation/none on interactive or focusable elements",
    "Needs stronger rule-to-example mapping precision"
  ],
  "next_focus": "Check integrated classification across examples, especially when ARIA is unnecessary versus required.",
  "updated_at": "datetime.datetime(2026, 4, 8, 15, 33, 47, 618686, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=72000)))"
}
```

---

## Full Conversation Transcript

**USER** (msg 1):
> Redundant, because the visible text “Save” already gives the button its accessible name. I think it’s okay, but not needed unless we want the label to be different for some reason.

**ASSISTANT** (msg 2):
> Right — redundant. The visible text already names the button, so adding `aria-label` doesn’t improve anything here and can create a mismatch if the two labels ever diverge.

Next assessment question: `<div role="button">Submit</div>` — does this satisfy the rule about accessible names, and what other check would you want to make before calling it a valid button?

**USER** (msg 3):
> It has a name because of the text “Submit,” so that part seems okay. But I’d want to check keyboard behavior and focusability too, since a `div` doesn’t get those like a real button does.

**ASSISTANT** (msg 4):
> Correct. The text gives the `div` an accessible name, but that alone doesn’t make it a valid button — you’d still need to confirm it is focusable and operable from the keyboard, which is part of making an interactive ARIA control usable.

Next assessment question: if you see `<button role="presentation">Delete</button>`, which rule is being violated?

**USER** (msg 5):
> That’s violating the “don’t override native semantics” rule. A real `<button>` already has button semantics, so `role="presentation"` would strip or fight that native meaning instead of helping.

**ASSISTANT** (msg 6):
> Close, but not the exact rule being tested. The issue here is specifically that `role="presentation"` must not be placed on a focusable or interactive element like a button — that’s the rule for presentation/none misuse, not the broader “don’t override native semantics” rule.

Next assessment question: which rule is violated by `<button role="presentation">Delete</button>`?

**USER** (msg 7):
> Ah, got it — it violates the rule that `role="presentation"`/`none` should not be used on focusable or interactive elements. Since `<button>` is interactive, that role is invalid there.

**ASSISTANT** (msg 8):
> Exactly — that’s the rule.

You’ve now got the core decision pattern: use native HTML first, add ARIA only when it actually fills a gap, make sure interactive ARIA controls are usable by keyboard, give interactive elements an accessible name, and never use `presentation`/`none` on something the user can focus or activate.

You also made the important distinction between “native semantics” and “ARIA decoration,” which is what keeps these checks precise instead of turning into guesswork.

**USER** (msg 9):
> Yeah, that makes sense now. So the big pattern is: native HTML first, ARIA only when there’s a real gap, and if I build a custom interactive thing I have to handle name, focus, and keyboard myself.

**ASSISTANT** (msg 10):
> Yes — that’s the right rule of thumb for ARIA.

For this lesson, we’re going to use that same idea in a different way: instead of asking “what ARIA can I add?”, we ask “what thing does this standard apply to?” That “what thing it applies to” is the scope.

So here’s the next step: if a rule is about the page’s content, a rule about the tool used to create the page, and a rule about a broader product requirement, what are we comparing them by?
