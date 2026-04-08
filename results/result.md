# Pipeline Trace: 16cd6f8c-4d85-4189-b698-a338681d6687

**Objective**: Explain the structure of WCAG 2.2 by identifying the four principles (POUR), guidelines, and success criteria levels (A, AA, AAA).
**Run at**: 2026-04-08T13:26:47.208665
**Total time**: 162.83s

## Timings

| Step | Time |
|------|------|
| teaching_plan | 78.65s |
| agentic_retrieval | 84.17s |
| build_bundle | 0.01s |
| render | 0.0s |
| total | 162.83s |

## Progress Log (WebSocket Events)

```json
[
  {
    "type": "stage",
    "stage": "searching",
    "detail": "Researching WCAG sources (round 1/4)...",
    "_ts": "2026-04-08T13:25:23.028231"
  },
  {
    "type": "stage",
    "stage": "searching",
    "detail": "Researching WCAG sources (round 2/4)...",
    "_ts": "2026-04-08T13:25:36.292307"
  },
  {
    "type": "stage",
    "stage": "searching",
    "detail": "Researching WCAG sources (round 3/4)...",
    "_ts": "2026-04-08T13:26:06.466407"
  },
  {
    "type": "stage",
    "stage": "searching",
    "detail": "Researching WCAG sources (round 4/4)...",
    "_ts": "2026-04-08T13:26:17.547421"
  }
]
```

## 1. Teaching Plan

**Type**: `str` | **Size**: 14938 chars

```
## 1. objective_text
Explain the structure of WCAG 2.2 by identifying the four principles (POUR), guidelines, and success criteria levels (A, AA, AAA).

## 2. plain_language_goal
Help the learner understand how WCAG 2.2 is organized: the four top-level principles, the guidelines under those principles, and the three conformance levels used for success criteria.

## 3. mastery_definition
A learner has mastered this objective when they can:

- Name the four WCAG principles and recognize the acronym POUR.
- Describe the hierarchy correctly: principles at the top, guidelines under principles, and success criteria under guidelines.
- Identify that success criteria are assigned conformance levels A, AA, or AAA.
- Correctly distinguish among the terms principle, guideline, and success criterion when shown examples or labels.
- Explain the structure without confusing it with techniques, laws, or testing methods.

## 4. objective_type
- terminology
- hierarchy/structure
- conceptual understanding
- classification

## 5. prerequisite_knowledge

### essential prerequisites
- Basic understanding that WCAG is a standard/guideline set related to web accessibility.
- Basic comfort with hierarchical organization, such as “category -> subcategory -> item.”

### helpful but nonessential prerequisites
- Prior exposure to accessibility concepts or common barriers.
- Familiarity with reading structured documentation.
- Awareness that accessibility standards may include different levels of conformance.

## 6. prerequisite_gap_policy
If the learner lacks the essential prerequisites, the tutor should briefly remediate before attempting this objective:

- If the learner does not know what WCAG is, establish only the minimum needed: that WCAG 2.2 is a structured accessibility standard for web content.
- If the learner struggles with hierarchy, use a simple non-domain analogy first, such as folder -> subfolder -> file or book -> chapter -> section.
- Do not proceed into naming POUR or levels until the learner can track a simple three-level structure.
- Keep remediation minimal and directly in service of this objective; avoid expanding into legal compliance, detailed accessibility issues, or testing procedures.

## 7. concept_decomposition
1. WCAG 2.2 has an intentional organizational structure, not just a flat list.
2. The highest structural layer is the four principles.
3. The four principles are summarized by the acronym POUR.
4. Each letter in POUR names one principle.
5. Guidelines are grouped under principles.
6. Guidelines are organizational statements within a principle, not testable requirements by themselves.
7. Success criteria sit under guidelines.
8. Success criteria are the level at which conformance levels are assigned.
9. Success criteria can be labeled A, AA, or AAA.
10. A, AA, and AAA are levels attached to success criteria, not to principles.
11. The learner must be able to distinguish principle vs guideline vs success criterion by position and role.
12. The learner must be able to describe the whole hierarchy in order.

## 8. dependency_order

### Recommended order with dependencies
1. **WCAG 2.2 has an intentional organizational structure**  
   - No dependency.
2. **The highest structural layer is the four principles**  
   - Depends on 1.
3. **The four principles are summarized by the acronym POUR**  
   - Depends on 2.
4. **Each letter in POUR names one principle**  
   - Depends on 3.
5. **Guidelines are grouped under principles**  
   - Depends on 2.
6. **Guidelines are organizational statements within a principle, not testable requirements by themselves**  
   - Depends on 5.
7. **Success criteria sit under guidelines**  
   - Depends on 5.
8. **Success criteria are the level at which conformance levels are assigned**  
   - Depends on 7.
9. **Success criteria can be labeled A, AA, or AAA**  
   - Depends on 8.
10. **A, AA, and AAA are levels attached to success criteria, not to principles**  
   - Depends on 9 and 2.
11. **Distinguish principle vs guideline vs success criterion by position and role**  
   - Depends on 4, 6, 7, 9.
12. **Describe the whole hierarchy in order**  
   - Depends on 11.

### Why this sequence is instructionally sound
- It starts with the simplest mental model: WCAG is organized hierarchically.
- It introduces top-level categories before lower-level parts, reducing cognitive load.
- POUR is introduced only after the learner understands that principles are the top level, so the acronym has a clear anchor.
- Guidelines are introduced before success criteria because they serve as the intermediate layer.
- Conformance levels are delayed until the learner knows what they apply to, preventing the common misconception that A/AA/AAA label whole principles.
- Final steps integrate terminology and structure into a complete explanation, which supports mastery and retrieval.

## 9. likely_misconceptions
- Thinking POUR itself is a separate standard rather than the acronym for the four principles.
- Confusing guidelines with success criteria.
- Believing principles are testable requirements in the same way success criteria are.
- Believing A, AA, and AAA are levels of guidelines or principles rather than of success criteria.
- Assuming AA means “twice as important” as A rather than a conformance level label.
- Treating WCAG as a flat checklist with no hierarchy.
- Confusing success criteria with techniques or examples.
- Assuming every structural layer is equally specific and testable.
- Mixing up the order as principle -> success criterion -> guideline.

## 10. explanation_vs_question_strategy

### 1. WCAG 2.2 has an intentional organizational structure
- **Begin with:** diagnostic question
- **Why:** Check whether the learner already sees standards as hierarchical or thinks of them as flat lists.

### 2. The highest structural layer is the four principles
- **Begin with:** brief explanation
- **Why:** This is foundational vocabulary that is efficient to establish explicitly before probing.

### 3. The four principles are summarized by the acronym POUR
- **Begin with:** guided questioning
- **Why:** Many learners may have seen POUR before; questioning can activate prior knowledge.

### 4. Each letter in POUR names one principle
- **Begin with:** guided questioning
- **Why:** Retrieval practice supports memorability while keeping load manageable.

### 5. Guidelines are grouped under principles
- **Begin with:** brief explanation
- **Why:** This introduces the middle layer of the hierarchy and benefits from direct structural framing.

### 6. Guidelines are organizational statements within a principle, not testable requirements by themselves
- **Begin with:** contrastive example
- **Why:** The difference between “organizational statement” and “testable requirement” is easier to grasp through comparison.

### 7. Success criteria sit under guidelines
- **Begin with:** brief explanation
- **Why:** Learners need the next layer in the structure clearly placed before deeper questioning.

### 8. Success criteria are the level at which conformance levels are assigned
- **Begin with:** worked example
- **Why:** A concrete structural example helps learners attach “levels” to the correct unit.

### 9. Success criteria can be labeled A, AA, or AAA
- **Begin with:** brief explanation
- **Why:** Simple terminology introduction; not conceptually difficult once placement is clear.

### 10. A, AA, and AAA are levels attached to success criteria, not to principles
- **Begin with:** contrastive example
- **Why:** This directly targets a high-probability misconception.

### 11. Distinguish principle vs guideline vs success criterion by position and role
- **Begin with:** guided questioning
- **Why:** Classification is best learned by having the learner sort and justify.

### 12. Describe the whole hierarchy in order
- **Begin with:** diagnostic question
- **Why:** At this stage the tutor should test integration and identify missing links.

## 11. socratic_question_goals

### Stage 1: Establish structure
- Diagnose whether the learner expects a hierarchy or a flat list.
- Elicit prior knowledge about how standards are organized.
- Prepare the learner to think in layers.

### Stage 2: Introduce principles and POUR
- Test recall of the acronym if previously known.
- Link acronym to the idea of top-level categories.
- Check whether the learner can map each letter to a named principle.

### Stage 3: Place guidelines under principles
- Force comparison between principle and guideline.
- Check whether the learner understands “under” as structural hierarchy, not importance.
- Reveal confusion between broad organizational statements and specific requirements.

### Stage 4: Place success criteria under guidelines
- Check causal/structural understanding of why another layer is needed.
- Test whether the learner can identify which layer is more specific.
- Reveal misconception that guidelines are directly the testable unit.

### Stage 5: Attach A/AA/AAA correctly
- Test classification of what the levels belong to.
- Reveal the misconception that principles or guidelines have A/AA/AAA labels.
- Force the learner to justify why the levels apply at the success-criteria layer.

### Stage 6: Integrate the full model
- Test ability to reconstruct the whole hierarchy from memory.
- Test transfer by asking the learner to place unfamiliar labels into the hierarchy.
- Check whether the learner can explain structure concisely and accurately.

## 12. example_requirements

### simplest introductory example
- A stripped-down representation of WCAG structure showing:
  - one principle
  - one guideline under it
  - one success criterion under that guideline
  - that success criterion labeled with a conformance level
- The example should be structurally accurate but minimal, to avoid overload.

### at least one contrastive example
- A side-by-side comparison of:
  - a principle statement
  - a guideline statement
  - a success criterion statement
- The goal is to help learners notice differences in scope and role.

### at least one borderline or tricky case
- An item that sounds like a requirement but is actually a guideline, or vice versa.
- A prompt that asks whether A/AA/AAA applies to the guideline or the success criterion.
- A case where the learner must distinguish between a success criterion and a technique/example.

### at least one transfer scenario if appropriate
- A non-WCAG hierarchy analogy such as policy -> section -> rule, or course -> module -> lesson, then map it back to principle -> guideline -> success criterion.
- Alternatively, present a new WCAG excerpt and ask the learner to identify which structural layer each item belongs to.

## 13. retrieval_requirements

### must-retrieve
- The exact names of the four WCAG 2.2 principles corresponding to POUR.
- Confirmation of the formal structural hierarchy in WCAG 2.2: principles, guidelines, success criteria.
- Accurate description of A, AA, and AAA as conformance levels assigned to success criteria.
- At least one authentic, correctly labeled example of:
  - a principle
  - a guideline under that principle
  - a success criterion under that guideline
- Terminology distinctions precise enough to avoid conflating success criteria with techniques.

### optional-supporting
- Official WCAG wording or diagram excerpts that visually show the hierarchy.
- Mnemonic support for remembering POUR.
- Brief note that techniques are separate supporting material, if needed to prevent confusion.
- One or two authentic excerpts from WCAG 2.2 that illustrate the difference in specificity across levels.

## 14. assessment_evidence

### quick understanding checks
- Learner names the four principles from POUR.
- Learner orders the structural layers correctly.
- Learner identifies which layer A/AA/AAA belongs to.
- Learner sorts 3–5 labels or excerpts into principle, guideline, or success criterion.

### application task
- Given a small WCAG excerpt set, the learner labels each item by structural level and indicates where conformance levels apply.

### transfer task
- Given a new or simplified standards hierarchy, the learner explains the analogy and maps it onto WCAG’s principle -> guideline -> success criterion organization.
- Or, given an unfamiliar WCAG fragment, the learner reconstructs its place in the hierarchy.

### misconception check
- Ask the learner whether a principle can be “AA.”
- Ask the learner whether guidelines are the directly testable layer.
- Ask the learner whether POUR and WCAG are two different frameworks.
- Ask the learner to distinguish a success criterion from a supporting technique/example.

## 15. adaptation_notes

### beginner
- Spend more time on hierarchy itself before introducing all terms.
- Use a single principle/guideline/success criterion chain first.
- Introduce POUR with memory support and repeated retrieval.
- Keep examples minimal and highly structured.

### intermediate learner
- Move more quickly through basic hierarchy.
- Use classification tasks earlier.
- Include contrastive examples that require distinguishing guidelines from success criteria by role.
- Add small recall demands without heavy scaffolding.

### advanced learner
- Compress prerequisite review and start with a diagnostic reconstruction task.
- Emphasize precise terminology and misconception correction.
- Use authentic WCAG excerpts rather than simplified placeholders.
- Require concise explanation of the structure with correct role distinctions.

## 16. boundaries_and_non_goals
Do not teach the following in this lesson unless minimally needed to prevent confusion:

- Detailed meaning of each individual WCAG guideline or success criterion.
- How to satisfy or test specific success criteria.
- Accessibility techniques, failures, or sufficient/advisory techniques in depth.
- Legal requirements or which jurisdictions require which level.
- The broader conformance model beyond identifying A, AA, AAA structurally.
- Differences between WCAG versions beyond naming the current objective’s version.
- Deep explanation of accessibility disabilities, user needs, or implementation patterns.

## 17. concise_plan_summary
- Start by establishing that WCAG 2.2 is organized as a hierarchy, not a flat list.
- Introduce principles first as the top level, then connect them to the POUR acronym.
- Ensure the learner can name and recognize the four principles before moving deeper.
- Place guidelines under principles and clarify that they are organizational, not the conformance-labeled unit.
- Introduce success criteria under guidelines as the more specific layer.
- Attach A, AA, and AAA only after success criteria are understood, to avoid misplacement.
- Use contrastive classification tasks to distinguish principle, guideline, and success criterion.
- Assess mastery through hierarchy reconstruction, term sorting, and correct placement of conformance levels.
```

## 2. Raw Retrieval Results

**Total calls**: 10 | **Hits**: 10 | **Non-hits**: 0
**Total hit chars**: 18289

### Result 1: `list_principles` — HIT
- **Round**: 1 | **Sequence**: 1 | **Chars**: 637
- **Args**: `{}`

<details><summary>Preview (first 500 chars)</summary>

```
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
Content must be robust enough
```
</details>

### Result 2: `list_guidelines` — HIT
- **Round**: 1 | **Sequence**: 2 | **Chars**: 1550
- **Args**: `{}`

<details><summary>Preview (first 500 chars)</summary>

```
# WCAG 2.2 Guidelines

## Principle 1: Perceivable

  **1.1 Text Alternatives**
  Provide text alternatives for any non-text content so that it can be changed into other forms people need, such as large print, braille, speech, symbols or simpler language.

  **1.2 Time-based Media**
  Provide alternatives for time-based media.

  **1.3 Adaptable**
  Create content that can be presented in different ways (for example simpler layout) without losing information or structure.

  **1.4 Distinguishabl
```
</details>

### Result 3: `count_criteria` — HIT
- **Round**: 1 | **Sequence**: 3 | **Chars**: 138
- **Args**: `{"group_by": "level"}`

<details><summary>Preview (first 500 chars)</summary>

```
# WCAG 2.2 Success Criteria by Level

Total: 87 success criteria

- **Level **: 1
- **Level A**: 31
- **Level AA**: 24
- **Level AAA**: 31
```
</details>

### Result 4: `get_guideline` — HIT
- **Round**: 1 | **Sequence**: 4 | **Chars**: 528
- **Args**: `{"ref_id": "1.1"}`

<details><summary>Preview (first 500 chars)</summary>

```
# Guideline 1.1: Text Alternatives

**Principle:** 1 Perceivable

## Description

Provide text alternatives for any non-text content so that it can be changed into other forms people need, such as large print, braille, speech, symbols or simpler language.

**URL:** https://www.w3.org/TR/WCAG22/#text-alternatives

## Success Criteria (1)

### 1.1.1 Non-text Content (Level A)
All non-text content that is presented to the user has a text alternative that serves the equivalent purpose, except for th
```
</details>

### Result 5: `get_success_criteria_detail` — HIT
- **Round**: 2 | **Sequence**: 1 | **Chars**: 2021
- **Args**: `{"ref_id": "1.1.1"}`

<details><summary>Preview (first 500 chars)</summary>

```
# 1.1.1 Non-text Content

**Level:** A
**Principle:** 1 Perceivable
**Guideline:** 1.1 Text Alternatives
**WCAG Versions:** 2.0, 2.1, 2.2

## Success Criterion

All non-text content that is presented to the user has a text alternative that serves the equivalent purpose, except for the situations listed below.

## Details

- **Controls, Input:** If non-text content is a control or accepts user input, then it has a name that describes its purpose. (Refer to Success Criterion 4.1.2 for additional r
```
</details>

### Result 6: `get_criteria_by_level` — HIT
- **Round**: 2 | **Sequence**: 2 | **Chars**: 1890
- **Args**: `{"level": "AA", "include_lower": true}`

<details><summary>Preview (first 500 chars)</summary>

```
# WCAG 2.2 Level AA (including lower levels)

Total: 55 success criteria

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
- **2.1.4** Cha
```
</details>

### Result 7: `get_techniques_for_criterion` — HIT
- **Round**: 2 | **Sequence**: 3 | **Chars**: 7047
- **Args**: `{"ref_id": "1.1.1"}`

<details><summary>Preview (first 500 chars)</summary>

```
# Techniques for 1.1.1 Non-text Content

## Sufficient Techniques

**Situation A: If a short description can serve the same purpose and present the same information as the non-text content:**
  - **G94**: Providing short text alternative for non-text content that serves the same purpose and presents the same information as the non-text content
  *Short text alternative techniques for Situation A*
    - **ARIA6**: Using aria-label to provide labels for objects
    - **ARIA10**: Using aria-labelle
```
</details>

### Result 8: `search_glossary` — HIT
- **Round**: 2 | **Sequence**: 4 | **Chars**: 1379
- **Args**: `{"query": "conformance"}`

<details><summary>Preview (first 500 chars)</summary>

```
# Glossary Search Results for "conformance" (8 found)

**accessibility supported**
supported by users' assistive technologies as well as the accessibility features in browsers and other user agents To qualify as an accessibility-supp...

---

**conformance**
satisfying all the requirements of a given standard, guideline or specification

---

**conforming alternate version**
version that conforms at the designated level, and provides all of the same information and functionality in the same huma
```
</details>

### Result 9: `get_glossary_term` — HIT
- **Round**: 3 | **Sequence**: 1 | **Chars**: 166
- **Args**: `{"term": "conformance"}`

<details><summary>Preview (first 500 chars)</summary>

```
# conformance

satisfying all the requirements of a given standard, guideline or specification

[View in WCAG 2.2 Glossary](https://www.w3.org/TR/WCAG22/#dfn-conform)
```
</details>

### Result 10: `get_criteria_by_level` — HIT
- **Round**: 4 | **Sequence**: 1 | **Chars**: 2933
- **Args**: `{"level": "AAA", "include_lower": true}`

<details><summary>Preview (first 500 chars)</summary>

```
# WCAG 2.2 Level AAA (including lower levels)

Total: 86 success criteria

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
- **2.1.4** Ch
```
</details>


## 3. Retrieval Bundle (Structured)


### Coverage Metadata

```json
{
  "hit_count": 12,
  "hit_chars": 31442,
  "missing_checks": [
    "conformance_rollup_rule"
  ],
  "required_checks": {
    "conformance_rollup_rule": true,
    "techniques_vs_requirements": true
  },
  "budget_chars": 20000
}
```

### Section: core_rules (2 items)

**Item 1: 1.1.1 Non-text Content**
- Source: `get_success_criteria_detail({"ref_id": "1.1.1"})`

<details><summary>Content (233 chars)</summary>

```
**Level:** A | **Principle:** 1 Perceivable | **Guideline:** 1.1 Text Alternatives

All non-text content that is presented to the user has a text alternative that serves the equivalent purpose, except for the situations listed below.
```
</details>

**Item 2: 1.1.1 Non-text Content**
- Source: `get_criterion({"ref_id": "1.1.1"})`

<details><summary>Content (371 chars)</summary>

```
**Goal:** Non-text information is available to more people.
**What to do:** Create a text alternative for visual and auditory content.
**Why it's important:** People who can’t fully see or hear content can understand it.

All non-text content that is presented to the user has a text alternative that serves the equivalent purpose, except for the situations listed below.
```
</details>


### Section: definitions (1 items)

**Item 1: conformance**
- Source: `get_glossary_term({"term": "conformance"})`

<details><summary>Content (79 chars)</summary>

```
satisfying all the requirements of a given standard, guideline or specification
```
</details>


### Section: decision_rules (1 items)

**Item 1: Decision Boundaries for 1.1.1 Non-text Content**
- Source: `get_criterion({"ref_id": "1.1.1"})`

<details><summary>Content (589 chars)</summary>

```
Note on alternatives matching the language of content
 Text alternatives and equivalents should match the human language of the original content (normally the default human language of the page). The 5.2 Conformance Requirements section, through the defined terms used there, states that success criteria be met through accessibility-supported ways (5.2.4), where the technology is used “in the human language of the content.” Where an alternative version is used (5.2.1), it is defined as something that “provides all of the same information and functionality in the same human language.”
```
</details>


### Section: examples (0 items)

*(empty)*


### Section: contrast_cases (0 items)

*(empty)*


### Section: technique_patterns (1 items)

**Item 1: Techniques for 1.1.1 Non-text Content**
- Source: `get_techniques_for_criterion({"ref_id": "1.1.1"})`

<details><summary>Content (2200 chars)</summary>

```
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
 - **G95**: Providing short text alternatives that provide a brief description of the non-text content
 *Short text alternative techniques for Situation B*
 - **ARIA6**: Using aria-label to provide labels for objects
 - **ARIA10**: Using aria-labelledby to provide a text alternative for non-text content
 - **G196**: Using a text alternative on one item within a group of images that describes all items in the group
 - **H2**: Combining adjacent image and text links for the same resource
 - **H37**: Using alt attributes on img elements
 - **H53**: Using the body of the object element
 - **H86**: Providing text alternatives for emojis, emoticons, ASCII art, and leetspeak
 - **PDF1**: Applying text alternatives to images with the Alt entry in PDF documents
 *Long text alternative techniques for Situation B*
 - **ARIA15**: Using aria-describedby to provide descriptions of images
 - **G73**: Providing a long description in another location with a link to it that is immediately adjacent to the non-text content
 - **G74**: Providing a long description in text near the non...
```
</details>


### Section: risks (1 items)

**Item 1: Failure and Misuse Notes for Techniques for 1.1.1 Non-text Content**
- Source: `get_techniques_for_criterion({"ref_id": "1.1.1"})`

<details><summary>Content (1400 chars)</summary>

```
Failure techniques:
- **F3**: Failure of Success Criterion 1.1.1 due to using CSS to include images that convey important information
- **F13**: Failure of Success Criterion 1.1.1 and 1.4.1 due to having a text alternative that does not include information that is conveyed by color differences in the image
- **F20**: Failure of Success Criterion 1.1.1 and 4.1.2 due to not updating text alternatives when changes to non-text content occur
- **F30**: Failure of Success Criterion 1.1.1 and 1.2.1 due to using text alternatives that are not alternatives (e.g., filenames or placeholder text)
- **F38**: Failure of Success Criterion 1.1.1 due to not marking up decorative images in HTML in a way that allows assistive technology to ignore them
- **F39**: Failure of Success Criterion 1.1.1 due to providing a text alternative that is not null (e.g., alt="spacer" or alt="image") for images that should be ignored by assistive technology
- **F65**: Failure of Success Criterion 1.1.1 due to omitting the alt attribute or text alternative on img elements, area elements, and input elements of type "image"
- **F67**: Failure of Success Criterion 1.1.1 and 1.2.1 due to providing long descriptions for non-text content that does not serve the same purpose or does not present the same information
- **F71**: Failure of Success Criterion 1.1.1 due to using text look-alikes to represent text without pr...
```
</details>


### Section: structural_context (6 items)

**Item 1: WCAG 2.2 Principles**
- Source: `list_principles({})`

<details><summary>Content (637 chars)</summary>

```
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
```
</details>

**Item 2: WCAG 2.2 Guidelines**
- Source: `list_guidelines({})`

<details><summary>Content (1524 chars)</summary>

```
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
```
</details>

**Item 3: WCAG 2.2 Success Criteria by Level**
- Source: `count_criteria({"group_by": "level"})`

<details><summary>Content (138 chars)</summary>

```
# WCAG 2.2 Success Criteria by Level

Total: 87 success criteria

- **Level **: 1
- **Level A**: 31
- **Level AA**: 24
- **Level AAA**: 31
```
</details>

**Item 4: Guideline 1.1: Text Alternatives**
- Source: `get_guideline({"ref_id": "1.1"})`

<details><summary>Content (526 chars)</summary>

```
# Guideline 1.1: Text Alternatives

**Principle:** 1 Perceivable

## Description

Provide text alternatives for any non-text content so that it can be changed into other forms people need, such as large print, braille, speech, symbols or simpler language.

**URL:** https://www.w3.org/TR/WCAG22/#text-alternatives

## Success Criteria (1)

### 1.1.1 Non-text Content (Level A)
All non-text content that is presented to the user has a text alternative that serves the equivalent purpose, except for the situations listed below.
```
</details>

**Item 5: WCAG 2.2 Level AA (including lower levels)**
- Source: `get_criteria_by_level({"level": "AA", "include_lower": true})`

<details><summary>Content (1600 chars)</summary>

```
# WCAG 2.2 Level AA (including lower levels)

Total: 55 success criteria

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
- *...
```
</details>

**Item 6: WCAG 2.2 Level AAA (including lower levels)**
- Source: `get_criteria_by_level({"level": "AAA", "include_lower": true})`

<details><summary>Content (1599 chars)</summary>

```
# WCAG 2.2 Level AAA (including lower levels)

Total: 86 success criteria

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
-...
```
</details>


### Raw Hits Summary

**Count**: 11

| # | Tool | Args | Round | Chars |
|---|------|------|-------|-------|
| 1 | `list_principles` | `{}` | 1 | 637 |
| 2 | `list_guidelines` | `{}` | 1 | 1550 |
| 3 | `count_criteria` | `{"group_by": "level"}` | 1 | 138 |
| 4 | `get_guideline` | `{"ref_id": "1.1"}` | 1 | 528 |
| 5 | `get_success_criteria_detail` | `{"ref_id": "1.1.1"}` | 2 | 2021 |
| 6 | `get_criteria_by_level` | `{"level": "AA", "include_lower": true}` | 2 | 1890 |
| 7 | `get_techniques_for_criterion` | `{"ref_id": "1.1.1"}` | 2 | 7047 |
| 8 | `search_glossary` | `{"query": "conformance"}` | 2 | 1379 |
| 9 | `get_glossary_term` | `{"term": "conformance"}` | 3 | 166 |
| 10 | `get_criteria_by_level` | `{"level": "AAA", "include_lower": true}` | 4 | 2933 |
| 11 | `get_criterion` | `{"ref_id": "1.1.1"}` | None | 12987 |

## 4. Rendered Evidence Pack (teaching_content)

**Size**: 5616 chars

This is the exact string injected into the tutor's system prompt as the VALIDATED EVIDENCE PACK.

````markdown
## CORE FACTS
### 1.1.1 Non-text Content
**Level:** A | **Principle:** 1 Perceivable | **Guideline:** 1.1 Text Alternatives

All non-text content that is presented to the user has a text alternative that serves the equivalent purpose, except for the situations listed below.

### 1.1.1 Non-text Content
**Goal:** Non-text information is available to more people.
**What to do:** Create a text alternative for visual and auditory content.
**Why it's important:** People who can’t fully see or hear content can understand it.

All non-text content that is presented to the user has a text alternative that serves the equivalent purpose, except for the situations listed below.

## DEFINITIONS
### conformance
satisfying all the requirements of a given standard, guideline or specification

## DECISION BOUNDARIES
### Decision Boundaries for 1.1.1 Non-text Content
Note on alternatives matching the language of content
 Text alternatives and equivalents should match the human language of the original content (normally the default human language of the page). The 5.2 Conformance Requirements section, through the defined terms used there, states that success criteria be met through accessibility-supported ways (5.2.4), where the technology is used “in the human language of the content.” Where an alternative version is used (5.2.1), it is defined as something that “provides all of the same information and functionality in the same human language.”

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

### WCAG 2.2 Guidelines
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
 Make text...
````

## 5. Lesson State

Built from the teaching plan. This tracks concept-by-concept progress.

```json
{
  "active_concept": "recommended-order-with-dependencies",
  "pending_check": "### Recommended order with dependencies",
  "bridge_back_target": "recommended-order-with-dependencies",
  "teaching_order": [
    "recommended-order-with-dependencies",
    "wcag-2-2-has-an-intentional-organizational-structure",
    "no-dependency",
    "the-highest-structural-layer-is-the-four-principles",
    "depends-on-1",
    "the-four-principles-are-summarized-by-the-acronym-pour",
    "depends-on-2",
    "each-letter-in-pour-names-one-principle",
    "depends-on-3",
    "guidelines-are-grouped-under-principles",
    "guidelines-are-organizational-statements-within-a-principle-not-testable-requirements-by-themselves",
    "depends-on-5",
    "success-criteria-sit-under-guidelines",
    "success-criteria-are-the-level-at-which-conformance-levels-are-assigned",
    "depends-on-7",
    "success-criteria-can-be-labeled-a-aa-or-aaa",
    "depends-on-8",
    "a-aa-and-aaa-are-levels-attached-to-success-criteria-not-to-principles",
    "depends-on-9-and-2",
    "distinguish-principle-vs-guideline-vs-success-criterion-by-position-and-role",
    "depends-on-4-6-7-9",
    "describe-the-whole-hierarchy-in-order",
    "depends-on-11",
    "why-this-sequence-is-instructionally-sound",
    "it-starts-with-the-simplest-mental-model-wcag-is-organized-hierarchically",
    "it-introduces-top-level-categories-before-lower-level-parts-reducing-cognitive-load",
    "pour-is-introduced-only-after-the-learner-understands-that-principles-are-the-top-level-so-the-acronym-has-a-clear-anchor",
    "guidelines-are-introduced-before-success-criteria-because-they-serve-as-the-intermediate-layer",
    "conformance-levels-are-delayed-until-the-learner-knows-what-they-apply-to-preventing-the-common-misconception-that-a-aa-aaa-label-whole-principles",
    "final-steps-integrate-terminology-and-structure-into-a-complete-explanation-which-supports-mastery-and-retrieval"
  ],
  "concepts": [
    {
      "id": "recommended-order-with-dependencies",
      "label": "### Recommended order with dependencies",
      "status": "not_covered"
    },
    {
      "id": "wcag-2-2-has-an-intentional-organizational-structure",
      "label": "**WCAG 2.2 has an intentional organizational structure**",
      "status": "not_covered"
    },
    {
      "id": "no-dependency",
      "label": "No dependency.",
      "status": "not_covered"
    },
    {
      "id": "the-highest-structural-layer-is-the-four-principles",
      "label": "**The highest structural layer is the four principles**",
      "status": "not_covered"
    },
    {
      "id": "depends-on-1",
      "label": "Depends on 1.",
      "status": "not_covered"
    },
    {
      "id": "the-four-principles-are-summarized-by-the-acronym-pour",
      "label": "**The four principles are summarized by the acronym POUR**",
      "status": "not_covered"
    },
    {
      "id": "depends-on-2",
      "label": "Depends on 2.",
      "status": "not_covered"
    },
    {
      "id": "each-letter-in-pour-names-one-principle",
      "label": "**Each letter in POUR names one principle**",
      "status": "not_covered"
    },
    {
      "id": "depends-on-3",
      "label": "Depends on 3.",
      "status": "not_covered"
    },
    {
      "id": "guidelines-are-grouped-under-principles",
      "label": "**Guidelines are grouped under principles**",
      "status": "not_covered"
    },
    {
      "id": "guidelines-are-organizational-statements-within-a-principle-not-testable-requirements-by-themselves",
      "label": "**Guidelines are organizational statements within a principle, not testable requirements by themselves**",
      "status": "not_covered"
    },
    {
      "id": "depends-on-5",
      "label": "Depends on 5.",
      "status": "not_covered"
    },
    {
      "id": "success-criteria-sit-under-guidelines",
      "label": "**Success criteria sit under guidelines**",
      "status": "not_covered"
    },
    {
      "id": "success-criteria-are-the-level-at-which-conformance-levels-are-assigned",
      "label": "**Success criteria are the level at which conformance levels are assigned**",
      "status": "not_covered"
    },
    {
      "id": "depends-on-7",
      "label": "Depends on 7.",
      "status": "not_covered"
    },
    {
      "id": "success-criteria-can-be-labeled-a-aa-or-aaa",
      "label": "**Success criteria can be labeled A, AA, or AAA**",
      "status": "not_covered"
    },
    {
      "id": "depends-on-8",
      "label": "Depends on 8.",
      "status": "not_covered"
    },
    {
      "id": "a-aa-and-aaa-are-levels-attached-to-success-criteria-not-to-principles",
      "label": "**A, AA, and AAA are levels attached to success criteria, not to principles**",
      "status": "not_covered"
    },
    {
      "id": "depends-on-9-and-2",
      "label": "Depends on 9 and 2.",
      "status": "not_covered"
    },
    {
      "id": "distinguish-principle-vs-guideline-vs-success-criterion-by-position-and-role",
      "label": "**Distinguish principle vs guideline vs success criterion by position and role**",
      "status": "not_covered"
    },
    {
      "id": "depends-on-4-6-7-9",
      "label": "Depends on 4, 6, 7, 9.",
      "status": "not_covered"
    },
    {
      "id": "describe-the-whole-hierarchy-in-order",
      "label": "**Describe the whole hierarchy in order**",
      "status": "not_covered"
    },
    {
      "id": "depends-on-11",
      "label": "Depends on 11.",
      "status": "not_covered"
    },
    {
      "id": "why-this-sequence-is-instructionally-sound",
      "label": "### Why this sequence is instructionally sound",
      "status": "not_covered"
    },
    {
      "id": "it-starts-with-the-simplest-mental-model-wcag-is-organized-hierarchically",
      "label": "It starts with the simplest mental model: WCAG is organized hierarchically.",
      "status": "not_covered"
    },
    {
      "id": "it-introduces-top-level-categories-before-lower-level-parts-reducing-cognitive-load",
      "label": "It introduces top-level categories before lower-level parts, reducing cognitive load.",
      "status": "not_covered"
    },
    {
      "id": "pour-is-introduced-only-after-the-learner-understands-that-principles-are-the-top-level-so-the-acronym-has-a-clear-anchor",
      "label": "POUR is introduced only after the learner understands that principles are the top level, so the acronym has a clear anchor.",
      "status": "not_covered"
    },
    {
      "id": "guidelines-are-introduced-before-success-criteria-because-they-serve-as-the-intermediate-layer",
      "label": "Guidelines are introduced before success criteria because they serve as the intermediate layer.",
      "status": "not_covered"
    },
    {
      "id": "conformance-levels-are-delayed-until-the-learner-knows-what-they-apply-to-preventing-the-common-misconception-that-a-aa-aaa-label-whole-principles",
      "label": "Conformance levels are delayed until the learner knows what they apply to, preventing the common misconception that A/AA/AAA label whole principles.",
      "status": "not_covered"
    },
    {
      "id": "final-steps-integrate-terminology-and-structure-into-a-complete-explanation-which-supports-mastery-and-retrieval",
      "label": "Final steps integrate terminology and structure into a complete explanation, which supports mastery and retrieval.",
      "status": "not_covered"
    }
  ]
}
```

## 6. Slim Persisted Payload (what goes to DB)

This is what `export_session()` produces for JSONB persistence.
**Size**: 41204 bytes

| Field | Size |
|-------|------|
| `objective_id` | 38 bytes |
| `objective_text` | 132 bytes |
| `teaching_content` | 5757 bytes |
| `teaching_plan` | 15312 bytes |
| `lesson_state` | 6442 bytes |
| `retrieved_at` | 28 bytes |
| `retrieval_bundle` | 13358 bytes |

### Slim Bundle (no raw_hits, no round/sequence)

```json
{
  "version": 1,
  "coverage": {
    "hit_count": 12,
    "hit_chars": 31442,
    "missing_checks": [
      "conformance_rollup_rule"
    ],
    "required_checks": {
      "conformance_rollup_rule": true,
      "techniques_vs_requirements": true
    },
    "budget_chars": 20000
  },
  "sections": {
    "core_rules": [
      {
        "title": "1.1.1 Non-text Content",
        "content_length": 233,
        "source_tool": "get_success_criteria_detail"
      },
      {
        "title": "1.1.1 Non-text Content",
        "content_length": 371,
        "source_tool": "get_criterion"
      }
    ],
    "definitions": [
      {
        "title": "conformance",
        "content_length": 79,
        "source_tool": "get_glossary_term"
      }
    ],
    "decision_rules": [
      {
        "title": "Decision Boundaries for 1.1.1 Non-text Content",
        "content_length": 589,
        "source_tool": "get_criterion"
      }
    ],
    "examples": [],
    "contrast_cases": [],
    "technique_patterns": [
      {
        "title": "Techniques for 1.1.1 Non-text Content",
        "content_length": 2200,
        "source_tool": "get_techniques_for_criterion"
      }
    ],
    "risks": [
      {
        "title": "Failure and Misuse Notes for Techniques for 1.1.1 Non-text Content",
        "content_length": 1400,
        "source_tool": "get_techniques_for_criterion"
      }
    ],
    "structural_context": [
      {
        "title": "WCAG 2.2 Principles",
        "content_length": 637,
        "source_tool": "list_principles"
      },
      {
        "title": "WCAG 2.2 Guidelines",
        "content_length": 1524,
        "source_tool": "list_guidelines"
      },
      {
        "title": "WCAG 2.2 Success Criteria by Level",
        "content_length": 138,
        "source_tool": "count_criteria"
      },
      {
        "title": "Guideline 1.1: Text Alternatives",
        "content_length": 526,
        "source_tool": "get_guideline"
      },
      {
        "title": "WCAG 2.2 Level AA (including lower levels)",
        "content_length": 1600,
        "source_tool": "get_criteria_by_level"
      },
      {
        "title": "WCAG 2.2 Level AAA (including lower levels)",
        "content_length": 1599,
        "source_tool": "get_criteria_by_level"
      }
    ]
  }
}
```