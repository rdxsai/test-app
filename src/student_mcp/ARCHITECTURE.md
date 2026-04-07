# Student State Architecture

## Overview

The current application uses `StudentService` for direct DB access to guided-tutor
learner state. The source of truth is the PostgreSQL `student_mcp` schema, and
`StudentDatabase` is the shared data layer behind that service.

## How It Works

```
FastAPI Backend
    │
    ├── StudentService
    │     └── StudentDatabase
    │
    └────────────────────────── PostgreSQL (student_mcp schema)
```

Guided tutoring now uses a tutor/reflector runtime rather than a single
tool-calling agent loop:

1. **Tutor pass**: produce the learner-facing response
2. **Reflector pass**: produce structured judgments about evidence, stage movement, and memory updates
3. **Application writes**: persist state deterministically through `StudentService`

## Database Schema

Uses a dedicated `student_mcp` schema in the same PostgreSQL instance as the main app. This avoids conflicts with the existing `prod.student_profiles` table.

### Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `student_profiles` | Identity and preferences | student_id (PK), technical_level, a11y_exposure, role_context, learning_goal, preferred_style |
| `mastery_records` | Per-objective mastery tracking | (student_id, objective_id) PK, mastery_level, evidence, assessment scores |
| `session_state` | Active session stage and progress | session_id (PK), current_stage, turns, readiness_score, assessment progress |
| `session_summaries` | Tiered memory (short/medium/long) | student_id, summary_type, content JSONB, objectives_covered |
| `misconception_log` | Tracked misconceptions | student_id, objective_id, misconception_text, resolved_at |
| `learner_memory` | Cross-objective personalization memory | student_id (PK), summary, strengths, support_needs, tendencies |
| `objective_memory` | Durable memory for one student/objective pair | (student_id, objective_id) PK, summary, demonstrated_skills, active_gaps, next_focus |

### Mastery Levels

```
not_attempted → misconception → in_progress → partial → mastered
```

### Session Stages

```
onboarding → introduction → exploration → readiness_check →
mini_assessment → final_assessment → transition
```

## Service Surface

The learner-state layer currently exposes these high-value operations through
`StudentService`:

- `get_profile`
- `get_mastery_state`
- `get_active_session`
- `get_misconception_patterns`
- `get_recommended_next_objective`
- `get_session_summary`
- `get_learner_memory`
- `get_objective_memory`
- `get_memory_bundle`
- `create_profile`
- `apply_mastery_judgment`
- `log_misconception`
- `resolve_misconception`
- `update_session_state`
- `save_session_summary`
- `upsert_learner_memory`
- `upsert_objective_memory`
- `record_assessment_answer`

## Client Integration

Current production wiring:

- `chat.py` creates `StudentService`
- `HybridCrewAISocraticSystem` receives it as `student_mcp_client`
- guided turns load learner state before the tutor pass and apply reflector outputs after generation

### Wiring

```
config.py          →  STUDENT_MCP_ENABLED (env var, default: true)
chat.py            →  StudentService()
                   →  passed to HybridCrewAISocraticSystem(student_mcp_client=...)
hybrid_system.py   →  self.student_mcp = student_mcp_client
                   →  load memory bundle before tutor pass
                   →  apply reflector judgments after tutor pass
```

### Guided Turn Flow

```python
bundle = await self.student_mcp.get_memory_bundle(student_id, objective_id)
tutor_response = run_tutor_pass(bundle, history, objective, stage)
reflection = run_reflector_pass(bundle, history, tutor_response)
await apply_reflection_updates(reflection)
```

## Pipeline Integration

The student context is loaded in parallel with intent classification, adding zero latency to the pipeline:

```
conduct_socratic_session_streaming()
    │
    ├── asyncio.create_task(_load_student_context)  ← parallel
    │     └── asyncio.gather(profile, mastery, session, misconceptions)
    │
    ├── Stage 1: classify intent (concurrent with above)
    │
    ├── await student_context_task  ← ready by now (DB reads are fast)
    │
    ├── Stage 2: RAG + WCAG MCP search
    │
    ├── Stage 3: _build_response_messages(student_context=...)
    │     └── system prompt now includes:
    │           STUDENT PROFILE: level, role, style
    │           ACTIVE SESSION: stage, objective, turns
    │           MASTERY STATE: per-objective levels
    │           ACTIVE MISCONCEPTIONS: unresolved items
    │           ---
    │           KNOWLEDGE BASE CONTEXT: RAG + WCAG
    │
    └── Stream response
```

### Context Window Composition

```
System prompt + stage instructions           (~500 tok)
Student profile (from MCP)                   (~100 tok)
Session state + mastery (from MCP)           (~250 tok)
Active misconceptions (from MCP)             (~100 tok)
Stage summary (compressed, from MCP)         (~200 tok)
Last 6 raw messages (conversational flow)    (~600 tok)
Retrieved content (RAG + WCAG MCP)          (~1500 tok)
─────────────────────────────────────────────────────
Total                                       (~3250 tok)
```

## Configuration

Environment variables (inherited from parent process):

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_HOST` | localhost | PostgreSQL host |
| `POSTGRES_PORT` | 5432 | PostgreSQL port |
| `POSTGRES_DB` | socratic_tutor | Database name |
| `POSTGRES_USER` | app_user | Database user |
| `POSTGRES_PASSWORD` | changeme_dev | Database password |
| `MAIN_DB_SCHEMA` | prod | Main app schema (for cross-schema queries) |

## File Structure

```
src/student_mcp/
    __init__.py       # Package docstring
    database.py       # StudentDatabase class + all SQL
    ARCHITECTURE.md   # This file
```
