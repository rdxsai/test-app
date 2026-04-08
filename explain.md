# How the Guided Tutoring Pipeline Works

This document explains the entire flow of Instance B (guided learning) — from a student connecting for the first time to receiving their first tutor message, and everything that happens in between.

---

## The Big Picture

The system teaches WCAG accessibility objectives through a Socratic tutoring approach. For each objective, it:

1. **Plans** what to teach (LLM generates a curriculum)
2. **Retrieves** grounded WCAG evidence (agentic multi-round tool calling)
3. **Organizes** that evidence into a structured bundle (deterministic normalization)
4. **Renders** a compact evidence pack for the tutor's prompt (presentation layer)
5. **Caches** everything so subsequent turns are instant
6. **Teaches** using the evidence pack + teaching plan + student state

The key design choice: **plan first, then retrieve**. The teaching plan tells the retrieval agent what evidence to look for, not the other way around. This inverts typical RAG.

---

## Phase 1: Student Connects

**File**: `src/question_app/api/chat.py`

A student opens the guided learning page and connects via WebSocket.

```
Client connects → server sends {"type": "connected"}
Client sends    → {"type": "auth", "student_id": "alice"}
Server checks   → does this student have a profile in the DB?
```

- **New student**: enters onboarding (Phase 2)
- **Returning student**: resumes where they left off (skips to Phase 3)

Every WebSocket connection gets a fresh `session_id` (e.g., `guided-a1b2c3d4e5f6`). This matters for caching later.

---

## Phase 2: Onboarding (New Students Only)

**File**: `src/question_app/services/tutor/hybrid_system.py` — `_handle_onboarding()`

Three clickable form questions:

| Step | Question | Options |
|------|----------|---------|
| 1 | Technical background | Developer, Designer, QA, Student, Manager |
| 2 | Accessibility exposure | None, Awareness, Working Knowledge, Professional |
| 3 | Learning goal | Certification, Job requirement, Personal interest |

No LLM needed — answers are structured form responses parsed directly.

After all three answers:

1. **Create student profile** in DB (technical_level, a11y_exposure, role, goal)
2. **Select starting objective** based on exposure level:
   - None → `I.A.2` (WCAG structure & POUR principles)
   - Awareness/Working → `I.D.10` (ARIA live regions)
   - Professional → `I.H.2` (Design analysis)
3. **Create session** in DB (stage=introduction, objective=selected)
4. **Stream a personalized intro** message to the student
5. **Auto-trigger the first teaching turn** — this enters Phase 3 immediately

---

## Phase 3: The Teaching Turn

**File**: `src/question_app/services/tutor/hybrid_system.py` — `conduct_guided_session_streaming()`

This is the core loop. Every student message goes through these steps:

### Step 3.1: Load State

```
Load conversation history (in-memory)
Load session state from DB (stage, objective, turn count)
Restore session cache from DB if not already in memory
```

The cache restore is the reconnect mechanism. If the server restarted or the WebSocket dropped, the cache is rehydrated from the DB so the pipeline doesn't need to re-run.

### Step 3.2: Check if Teaching Content Pipeline Needs to Run

```python
if session_cache.needs_retrieval(session_id, objective_id):
    # Cache miss — run the full pipeline
else:
    # Cache hit — use cached teaching_content, teaching_plan, lesson_state
```

Cache miss happens when:
- First turn on a new objective
- Objective changed since last cached content

Cache hit means: skip the entire pipeline, go straight to building the tutor response. This is the fast path (~0ms vs ~10-15s).

---

## The Teaching Content Pipeline (Cache Miss Only)

**File**: `src/question_app/services/tutor/hybrid_system.py` — `_run_teaching_content_pipeline()`

This is the expensive path that only runs once per objective. Four steps:

### Pipeline Step 1: Generate Teaching Plan

**Function**: `_generate_teaching_plan()`
**LLM call**: Azure reasoning model, temperature=0.3, max 2500 tokens

The LLM receives `CONCEPT_DECOMPOSITION_PROMPT` — a curriculum designer prompt that produces a 17-section structured text plan:

```
1.  objective_text           — the objective unchanged
2.  plain_language_goal      — simplified version
3.  mastery_definition       — what the student must demonstrate
4.  objective_type           — terminology / conceptual / procedural / etc.
5.  prerequisite_knowledge   — what the student should already know
6.  prerequisite_gap_policy  — how to handle missing prerequisites
7.  concept_decomposition    — atomic sub-concepts to teach
8.  dependency_order         — teaching sequence with explicit dependencies
9.  likely_misconceptions    — common confusions to watch for
10. explanation_vs_question_strategy — when to explain vs. question per concept
11. socratic_question_goals  — purposes of questions (diagnose, reveal, check)
12. example_requirements     — types of examples needed
13. retrieval_requirements   — must-retrieve vs. nice-to-have evidence
14. assessment_evidence      — what demonstrates mastery
15. adaptation_notes         — adjustments for beginner/intermediate/advanced
16. boundaries_and_non_goals — what NOT to teach
17. concise_plan_summary     — 5-8 bullet synthesis
```

The plan is used for two things:
- **Guiding retrieval** (step 2) — tells the retrieval agent what evidence to look for
- **Runtime teaching structure** — the tutor references it every turn to know what concepts to cover and in what order

### Pipeline Step 2: Agentic Retrieval

**Function**: `_run_agentic_retrieval()`
**LLM calls**: Azure reasoning model with tool calling, up to 4 rounds

This is a multi-round agent loop where the LLM decides which WCAG tools to call:

```
Round 1 (forced tool use):
  LLM reads the objective + teaching plan
  LLM decides: "I need SC 1.1.1, the alt text glossary term, and techniques for 1.1.1"
  → Calls 3 WCAG tools via MCP server
  → Gets results back
  → Coverage assessment: "Got core rules, but missing technique details"

Round 2 (auto):
  LLM sees feedback + previous results
  LLM decides: "I need technique H37 and the conformance glossary term"
  → Calls 2 more tools
  → Coverage assessment: "All required checks pass"

Round 3: LLM decides it has enough → stops
```

**Budget constraints**:
- Max 4 rounds
- Max 10 tool calls total
- ~20,000 character budget
- Deduplication: seen calls are skipped

**Available tools** (17 total via WCAG MCP server):
- Lookups: `get_criterion`, `get_technique`, `get_glossary_term`, `get_guideline`
- Search: `search_wcag`, `search_techniques`, `search_glossary`
- Navigation: `list_principles`, `list_guidelines`, `list_success_criteria`
- Detail: `get_full_criterion_context`, `get_techniques_for_criterion`, `get_success_criteria_detail`
- Meta: `get_criteria_by_level`, `count_criteria`, `whats_new_in_wcag22`

**Output**: A flat list of tool results, each tagged with `status: "HIT" | "MISS" | "BLOCKED" | "ERROR"`.

### Pipeline Step 3: Build Retrieval Bundle (Normalization)

**Function**: `_build_retrieval_bundle()`
**No LLM** — this is fully deterministic

This is the normalization layer. It takes messy raw tool results and produces a structured artifact:

```python
bundle = {
    "version": 1,
    "objective_text": "...",
    "coverage": {
        "hit_count": 7,
        "hit_chars": 15000,
        "required_checks": {"conformance_rollup_rule": True, "techniques_vs_requirements": True},
    },
    "sections": {
        "core_rules":         [...],  # Success criteria text
        "definitions":        [...],  # Glossary terms
        "decision_rules":     [...],  # When X applies vs. when Y applies
        "examples":           [...],  # Code/content examples
        "contrast_cases":     [...],  # "This passes, this fails"
        "technique_patterns": [...],  # WCAG techniques (H37, ARIA1, etc.)
        "risks":              [...],  # Failure conditions and misuse notes
        "structural_context": [...],  # POUR principles, guideline hierarchy
    },
    "raw_hits": [...]  # Diagnostic metadata (not persisted)
}
```

Each section item looks like:
```python
{
    "title": "SC 1.1.1 Non-text Content",
    "content": "All non-text content that is presented to the user has a text alternative...",
    "source_tool": "get_criterion",
    "source_args": {"ref_id": "1.1.1"},
}
```

**Why this layer matters**:

1. **Deterministic fallback checks** — Before the bundle is finalized, `_assess_retrieval_coverage()` checks if the LLM missed critical evidence. If the objective mentions conformance and the agent didn't fetch it, the builder automatically calls `get_glossary_term("conformance")` + `get_criterion("1.1.1")` as fallbacks. This is a safety gate that prevents the tutor from teaching without required evidence.

2. **Deduplication** — Same title+content won't appear twice in a section.

3. **Semantic organization** — Raw tool results are categorized by their teaching role (rule vs. definition vs. example vs. risk), not by which tool returned them.

4. **Separation of concerns** — The bundle is a testable, inspectable intermediate artifact. You can verify "did we get the right evidence?" independently from "did we render it well?"

### Pipeline Step 4: Render Evidence Pack (Presentation)

**Function**: `_render_retrieval_bundle()`
**No LLM** — deterministic string formatting

Takes the structured bundle and compresses it into compact markdown for prompt injection:

```python
section_specs = [
    ("CORE FACTS",           core_rules,         max_items=2, max_chars=1400),
    ("DEFINITIONS",          definitions,         3, 600),
    ("DECISION BOUNDARIES",  decision_rules,      2, 1400),
    ("EXAMPLES",             examples,            2, 1400),
    ("CONTRAST CASES",       contrast_cases,      2, 1200),
    ("TECHNIQUE PATTERNS",   technique_patterns,  3, 1200),
    ("RISKS / MISUSE",       risks,               2, 900),
    ("STRUCTURE NOTES",      structural_context,  2, 1200),
]
```

Each section is truncated to its budget. The output is a ~3-5K character markdown string — the **teaching_content** that gets injected into the tutor's system prompt as the "VALIDATED EVIDENCE PACK".

**Why this layer matters**:
- Predictable prompt size (bounded per-section budgets)
- The tutor never sees raw tool output — only curated, truncated content
- Section order is controlled (core facts first, structure notes last)

---

## What Gets Cached and Persisted

After the pipeline completes, four artifacts exist:

| Artifact | What it is | Size |
|----------|-----------|------|
| `teaching_plan` | 17-section curriculum plan | ~2-4K chars |
| `teaching_content` | Rendered evidence pack (compact markdown) | ~3-5K chars |
| `retrieval_bundle` | Structured evidence with 8 sections | ~10-15K chars |
| `lesson_state` | Concept tracking (active concept, order, status per concept) | ~500 bytes |

### Two-Layer Caching

**Layer 1: In-Memory Cache** (`SessionContentCache`)

```python
# Stored in a Python dict, keyed by session_id
self._session_cache._cache[session_id] = {
    "objective_id": "I.A.2",
    "teaching_content": "## CORE FACTS\n### SC 1.1.1...",
    "teaching_plan": "## 1. objective_text\n...",
    "retrieval_bundle": { full bundle with raw_hits },
    "lesson_state": { "active_concept": "pour-principles", "concepts": [...] },
    ...
}
```

- Access: zero-latency dict lookup
- Lifetime: process lifetime (lost on server restart)
- Updated: lesson_state patched every turn, everything else stable per objective

**Layer 2: Durable DB Cache** (`session_state.runtime_cache` JSONB column)

```python
# Persisted via student_mcp.save_session_runtime_cache(session_id, payload)
# Stored as JSONB in the session_state table
```

- Access: ~50-100ms DB query
- Lifetime: survives server restarts, inherited on WebSocket reconnect
- Updated: after pipeline completes + after every lesson_state patch

**What gets slimmed for persistence**:

The `export_session()` method produces a slim payload for DB storage:
- `retrieval_bundle` is included BUT slimmed: `raw_hits` array is dropped (redundant diagnostics), and per-item `round`/`sequence` metadata is stripped. This cuts ~40% of the bundle size while keeping the structured evidence available for re-rendering or audit.
- Legacy fields (`rag_chunks`, `wcag_context`) are omitted entirely.

### Reconnect / Restart Flow

When a WebSocket drops and the student reconnects:

```
1. New WebSocket connection → new session_id generated
2. create_session() in DB → queries the student's MOST RECENT previous session
   → copies its runtime_cache to the new session row
3. Next student message triggers conduct_guided_session_streaming()
4. _restore_session_cache() → loads inherited cache from DB into memory
5. needs_retrieval() returns False (cache valid for same objective)
6. Pipeline skipped → instant response
```

The inheritance happens at the DB level: `create_session()` always copies the last session's `runtime_cache` for that student. This means a server restart or network blip doesn't cost a 10-15 second pipeline re-run.

---

## Phase 3 Continued: Building the Tutor Response

Back in the main teaching turn, after the pipeline has run (or cache was hit):

### Step 3.3: Load Student State

**Function**: `_load_student_bundle()` — reads from DB:
- Student profile (technical level, a11y exposure, role)
- Mastery records (per-objective level + confidence)
- Active misconceptions (logged but not yet resolved)
- Learner memory (strengths, support needs, tendencies, strategies)
- Objective memory (summary, demonstrated skills, gaps, next focus)

This is formatted into a human-readable `student_context` string for prompt injection.

### Step 3.4: Run Turn Analyzer (LLM Call)

**Function**: `_run_turn_analyzer()`
**LLM call**: Azure reasoning model, temperature=0.0, max 1200 tokens

Before the tutor responds, a separate reasoning pass analyzes the student's message. This produces a structured JSON output:

```json
{
    "turn_route": "objective_answer",
    "teaching_move": "continue",
    "lesson_state_patch": {
        "active_concept": "decorative-vs-informative",
        "concept_updates": [{"concept_id": "alt-text-basics", "status": "covered"}]
    },
    "mastery_signal": {
        "should_update": true,
        "level": "in_progress",
        "confidence": 0.6
    },
    "misconceptions_to_log": [],
    "misconceptions_to_resolve": ["Student believes alt text is only for screen readers"],
    "objective_memory_patch": { ... },
    "learner_memory_patch": { ... }
}
```

This is NOT shown to the student. It's an internal reasoning step that:
- Routes the conversation (on-topic? off-topic? clarification needed?)
- Decides the teaching move (continue, pivot, revisit, simplify, deepen)
- Produces patches for the lesson state, mastery, misconceptions, and memory
- Decides whether the stage should advance

### Step 3.5: Build Tutor Messages

**Function**: `_build_guided_tutor_messages()`

Assembles the full message array for the tutor LLM:

```
System message = build_instance_b_prompt():
  ├─ TUTOR_SYSTEM_PROMPT (role, response modes, anti-patterns, few-shot examples)
  ├─ STUDENT CONTEXT (profile, mastery, misconceptions, memory)
  ├─ CURRENT STAGE: INTRODUCTION
  ├─ ACTIVE OBJECTIVE: Understand WCAG 2.2 structure and POUR principles
  ├─ TEACHING PLAN (formatted: goal, mastery criteria, concepts, order, strategy)
  ├─ LESSON STATE (active concept, pending check, concept order with status markers)
  └─ VALIDATED EVIDENCE PACK (the rendered teaching_content)

+ Turn analysis block (the JSON from step 3.4, injected as a second system message)
+ Last 6 turns of conversation history
+ Current student message
```

### Step 3.6: Stream Response

**Function**: `_stream_response()`
**LLM call**: Azure chat model, temperature=0.7, max 1000 tokens

The tutor generates its response using all the assembled context. Tokens are streamed to the client via WebSocket:

```
{"type": "stream_start"}
{"type": "token", "content": "Let"}
{"type": "token", "content": " me"}
{"type": "token", "content": " explain"}
...
{"type": "stream_end", "metadata": {session_id, stage, ...}}
```

Because Azure APIM buffers SSE responses, the system uses a drip-feed workaround — collecting the full response and then sending tokens at ~8ms intervals.

### Step 3.7: Apply State Updates

**Function**: `_apply_turn_analysis_updates()`

After the response is streamed, the turn analysis patches are applied:

1. **Increment turn count** in DB
2. **Log new misconceptions** to DB (if any detected)
3. **Resolve misconceptions** in DB (if student corrected themselves)
4. **Patch lesson state** in memory (advance active concept, mark concepts covered)
5. **Persist updated cache** to DB (so lesson state survives reconnect)
6. **Upsert learner memory** in DB (strengths, tendencies, strategies)
7. **Upsert objective memory** in DB (skills demonstrated, gaps, next focus)
8. **Apply mastery judgment** in DB (if confidence threshold met)

---

## LLM Calls Summary

Each teaching turn involves 2-3 LLM calls (after the first turn on an objective which adds 2 more):

| Call | When | Model | Purpose | Output |
|------|------|-------|---------|--------|
| Teaching Plan | First turn per objective | Reasoning (temp 0.3) | Curriculum design | 17-section text |
| Agentic Retrieval | First turn per objective (1-4 rounds) | Reasoning (temp 0.0) + tools | Decide what WCAG evidence to fetch | Tool call decisions |
| Turn Analyzer | Every turn | Reasoning (temp 0.0) | Analyze student response | JSON patches |
| Tutor Response | Every turn | Chat (temp 0.7) | Generate teaching response | Streamed text |

First turn on a new objective: ~4-6 LLM calls, ~10-15 seconds.
Subsequent turns on the same objective: 2 LLM calls, ~5-8 seconds (no pipeline).

---

## Design Choices and Why

### Plan-first, then retrieve
The teaching plan tells the retrieval agent what to look for. This means retrieval is targeted — it fetches evidence the curriculum actually needs, rather than doing a generic semantic search and hoping the results are useful.

### Normalization layer (bundle) separate from presentation (render)
The bundle builder handles validation, fallbacks, and deduplication. The renderer handles truncation and formatting. This means you can change how evidence is presented without touching the validation logic, and you can test evidence quality independently of prompt formatting.

### Deterministic fallbacks in the bundle builder
The agentic retrieval loop is smart but not perfect. The bundle builder runs deterministic checks — "does the evidence include conformance rules? technique patterns?" — and fills gaps with hardcoded fallback tool calls. This guarantees the tutor always has critical evidence even if the LLM agent missed it.

### Two-layer cache (memory + DB)
In-memory gives zero-latency access during a session. DB persistence means a server restart or WebSocket reconnect doesn't force a 10-15 second pipeline re-run. The `export_session()` method slims the payload before DB writes (dropping diagnostic metadata and legacy fields) to keep the JSONB bounded at ~6-10K.

### Turn analyzer as a separate reasoning pass
Instead of asking the tutor to both analyze the student AND respond in one call, the system splits this into two LLM calls. The analyzer produces structured JSON (routing, misconceptions, mastery signals, state patches). The tutor then receives these decisions as context and focuses purely on generating a good teaching response. This separation means teaching quality doesn't degrade when the analysis is complex.

### Lesson state as a mutable runtime structure
The lesson state (which concept is active, which are covered, what's the teaching order) is built from the teaching plan but lives separately as a patchable dict. The turn analyzer can update it every turn, and those patches are both cached in memory and persisted to DB. This lets the tutor adapt its teaching order based on how the student is actually progressing, not just follow the original plan rigidly.
