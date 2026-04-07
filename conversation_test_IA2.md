# Conversation Test: I.A.2 — GPT-5.4-mini with Full Pipeline

> **Model**: gpt-5.4-mini
> **Date**: 2026-04-07
> **Student**: test-mini-fix-1775583482 (beginner, student, no a11y exposure, certification goal)
> **Objective**: Explain the structure of WCAG 2.2, including the POUR principles, guidelines, success criteria, and conformance levels A, AA, and AAA.
>
> **First test with full pipeline working end-to-end** (session_cache fix + token bump).
> All previous conversation tests were running the fallback path (tutor teaching blind).

---

## Pipeline Execution (Turn 1, one-time per objective)

```
Pipeline step 1: teaching plan (12,260 chars)
Pipeline step 2: retrieval plan (11,549 chars)
Pipeline step 3: extracted 18 tool calls
Pipeline step 4: 14/18 hits, 8,495 chars
Pipeline step 5: evidence pack (11,411 chars)
Teaching plan stored: 12,260 chars
```

---

## Conversation (6 turns)

### Turn 1 (46.1s — includes pipeline)

**STUDENT**: Hi, I need to understand how WCAG is structured for my cert. Where do we start?

**TUTOR** (stage=introduction):
Imagine you're looking at a WCAG success criterion like **1.1.1 Non-text Content**. Would you expect that to sit on the same level as **Perceivable**, or underneath it?

---

### Turn 2 (5.9s)

**STUDENT**: I think it's some kind of checklist for making websites accessible?

**TUTOR** (stage=introduction):
We start with the big picture: **WCAG is a hierarchy, not a flat list**. That means some items are broad organizing layers, and other items sit underneath them as more specific requirements.

For example, **Perceivable** is a top-level principle, while **1.1.1 Non-text Content** is a more specific success criterion under **1.1 Text Alternatives**, which sits under that principle. So the structure goes from general to specific.

If you had to place **1.1.1 Non-text Content** in that structure, would you say it is a principle, a guideline, or a success criterion?

---

### Turn 3 (7.6s)

**STUDENT**: So the four principles are like Level A, Level AA, Level AAA, and something else?

**TUTOR** (stage=introduction):
That's a reasonable first guess — WCAG does function like a checklist in practice, but its structure is more organized than that. The important idea here is that it's a **hierarchy**: broad principles at the top, then guidelines, then specific success criteria underneath.

So for **1.1.1 Non-text Content**, which layer do you think it belongs to?

---

### Turn 4 (9.4s)

**STUDENT**: Oh the principles are Perceivable, Operable, Understandable and Robust — categories not levels. But what goes under them?

**TUTOR** (stage=introduction):
That's a common mix-up, but no — **the four principles are Perceivable, Operable, Understandable, and Robust**. **A, AA, and AAA** are **conformance levels**, not principles, so they sit in a different part of the structure.

A good way to think about it is: principles are the **top-level organizing ideas**, and the levels tell you **how strict the conformance requirement is**. With that in mind, where would you place **A, AA, and AAA**: as principles, guidelines, success criteria, or conformance levels?

---

### Turn 5 (6.5s)

**STUDENT**: Is WCAG the same as Section 508?

**TUTOR** (stage=introduction):
Exactly — those are the top-level categories.

What goes under each principle are **guidelines**. For example, under **Perceivable** you have guidelines like **1.1 Text Alternatives** and **1.4 Distinguishable**. Those guidelines are broader goals that organize the more specific requirements below them.

Can you tell me, in your own words, what a guideline is doing in the WCAG structure?

---

### Turn 6 (6.4s)

**STUDENT**: If my site passes all AAA criteria, it's automatically AA compliant too right?

**TUTOR** (stage=introduction):
Not the same. WCAG is the accessibility standard we're studying here; Section 508 is a separate U.S. accessibility law/regulation that often refers to WCAG, but they aren't identical.

Bringing it back to the structure: under each principle, the next layer is **guidelines**. What do you think the guideline layer does that's different from the principle layer?

---

## Student Model State (after 6 turns)

### Session
- Stage: `introduction` (stayed — correct for beginner still learning basics)
- Turns on objective: 6
- Active objective: I.A.2

### Mastery
- Level: `not_attempted`
- Evidence: "Student has not demonstrated any understanding of WCAG structure."

### Misconceptions

| Misconception | Identified | Resolved |
|---|---|---|
| WCAG viewed only as a generic checklist rather than a hierarchy | 17:43:03 | (unresolved) |
| WCAG viewed mainly as a generic checklist rather than a hierarchy | 17:43:13 | 17:43:26 |
| Confusing the four principles with conformance levels A, AA, and AAA | 17:43:13 | (unresolved) |

### Objective Memory (I.A.2)

```json
{
  "summary": "Student now knows POUR are the four top-level principles and A/AA/AAA are conformance levels; guideline layer still not explained.",
  "demonstrated_skills": [
    "recognizes WCAG is related to accessibility",
    "identified POUR as the four principles",
    "separated principles from A/AA/AAA",
    "distinguished principles from conformance levels",
    "asked for the next layer in the structure"
  ],
  "active_gaps": [
    "hierarchy understanding",
    "placement of success criteria",
    "no explanation of the guideline layer",
    "no evidence of hierarchy beyond top-level categories"
  ],
  "next_focus": "Define guidelines as the layer under principles and contrast them with success criteria."
}
```

### Learner Memory (cross-objective)

```json
{
  "summary": "Beginner who benefits from explicit hierarchy framing and short contrast checks; asks clarifying comparison questions when unsure.",
  "strengths": [
    "motivated by certification",
    "asks clarifying questions",
    "can revise an incorrect categorization",
    "can correct one category mix-up when prompted"
  ],
  "support_needs": [
    "clear orientation",
    "simple hierarchy language",
    "brief contrast examples",
    "brief comparison between layers"
  ],
  "tendencies": [
    "defaults to checklist framing when unsure",
    "mixes structural layers at first",
    "responds well to corrective framing",
    "may branch to related standards for comparison"
  ],
  "successful_strategies": [
    "brief framing before questioning",
    "guided comparison between layers",
    "contrast between principles and conformance levels",
    "stepwise category prompts",
    "direct category-placing questions"
  ]
}
```

---

## Model Comparison (same 6 student turns)

| | gpt-5 (blind) | gpt-5.4-mini (blind) | gpt-5.4-mini (with pipeline) |
|---|---|---|---|
| Per-turn speed | ~15s | 5-7s | **5-9s** |
| Evidence grounding | None | None | **Real SC refs from evidence pack** |
| Misconceptions tracked | 2 (both resolved) | 2 (not resolved) | **3 (1 resolved)** |
| Mastery signal | None | not_attempted | **not_attempted with evidence** |
| Objective memory | None | Generic | **Specific skills + gaps + next_focus** |
| Learner memory | None | Generic tendencies | **Detailed strategies + support needs** |
| Stage after 6 turns | introduction | exploration | **introduction (correct)** |
