# Student MCP Server — Architecture

## Overview

A Python MCP (Model Context Protocol) server that provides student state management for the Socratic tutoring chatbot. It runs as a **subprocess** over stdio and is called **programmatically** by the FastAPI backend — unlike the WCAG MCP server which uses LLM-driven tool calling.

**Why a separate MCP server?**
- Process isolation: student state management runs independently
- Protocol standardization: any MCP client can interact with it
- Same proven pattern: connects identically to how wcag-guidelines-mcp works
- Clean separation: the main app doesn't need student-specific SQL

## How It Works

```
FastAPI Backend (parent process)
    │
    ├── StudentMCPClient
    │     └── stdio_client → subprocess
    │                          │
    │                     Student MCP Server
    │                          │
    │                     ┌────┴────┐
    │                     │ FastMCP │
    │                     │ (tools) │
    │                     └────┬────┘
    │                          │
    │                     StudentDatabase
    │                          │
    └─────────────────── PostgreSQL (student_mcp schema)
```

The backend calls tools directly via `session.call_tool()`. No LLM decides which tools to call — the application logic does:

1. **Before LLM call**: Read tools fetch student profile, mastery state, session info
2. **LLM generates**: Socratic response + evaluation JSON
3. **After LLM call**: Write tools persist mastery updates, misconceptions, session state

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

### Mastery Levels

```
not_attempted → misconception → in_progress → partial → mastered
```

### Session Stages

```
onboarding → introduction → exploration → readiness_check →
mini_assessment → mini_review → final_assessment → transition
```

## Tools (12/12 implemented)

### Read Tools (called before LLM → build context window)

| Tool | Args | Returns |
|------|------|---------|
| `get_student_profile` | `student_id` | Profile dict with `found: true/false` |
| `get_mastery_state` | `student_id` | Array of mastery records (objective_id, mastery_level, evidence, scores, turns) |
| `get_active_session` | `student_id` | Most recent session state with `found: true/false` |
| `get_misconception_patterns` | `student_id` | Array of unresolved misconceptions (resolved_at IS NULL) |
| `get_recommended_next_objective` | `student_id` | Next objective via cross-schema join with main app's `learning_objective` table. Prioritizes: in_progress > partial > not_attempted |
| `get_session_summary` | `student_id, summary_type` | Most recent summary of given type (short/medium/long) |

### Write Tools (called after LLM → persist evaluation)

| Tool | Args | Action |
|------|------|--------|
| `create_student_profile` | `student_id, technical_level, a11y_exposure, role_context, learning_goal` | INSERT (idempotent via ON CONFLICT) |
| `update_mastery` | `student_id, objective_id, mastery_level, evidence_summary` | UPSERT — increments turns_spent on update |
| `log_misconception` | `student_id, objective_id, misconception_text, source_question_id` | INSERT new misconception |
| `update_session_state` | `session_id, student_id, stage, active_objective_id, turns, readiness_score, assessment_progress, stage_summary` | Creates session if needed, then selectively updates non-empty fields |
| `save_session_summary` | `session_id, student_id, summary_type, content, objectives_covered, mastery_changes` | INSERT summary (content/mastery_changes as JSON strings, objectives_covered as JSON array) |
| `update_student_preferences` | `student_id, preferred_style` | UPDATE profile preferred_style + last_session_at |

### Tool Design Notes

- All tools return JSON strings (MCP TextContent). Timestamps are ISO 8601.
- Read tools return `{"found": false}` for missing records (not errors).
- Write tools use UPSERT/ON CONFLICT for idempotency where applicable.
- Complex params (JSONB) are passed as JSON strings and parsed server-side.
- DB calls use `asyncio.to_thread()` to avoid blocking the event loop.
- `get_recommended_next_objective` does a cross-schema query joining `{MAIN_DB_SCHEMA}.learning_objective` with `student_mcp.mastery_records`.

## Client Integration

The FastAPI backend connects to this server via `StudentMCPClient` (`src/question_app/services/student_mcp_client.py`). The client follows the same lifecycle pattern as `WCAGMCPClient`:

- **Lazy init**: subprocess starts on first tool call, not at import time
- **asyncio.Lock**: prevents double-initialization under concurrent requests
- **Auto-reconnect**: if the subprocess dies, the next `_call()` resets the session and reconnects
- **Direct calls**: `session.call_tool()` — no LLM function-calling layer

### Wiring

```
config.py          →  STUDENT_MCP_ENABLED (env var, default: true)
chat.py            →  StudentMCPClient(command=python, args=["-m", "student_mcp"])
                   →  passed to HybridCrewAISocraticSystem(student_mcp_client=...)
hybrid_system.py   →  self.student_mcp = student_mcp_client
                   →  read tools before LLM, write tools after LLM
```

### Read/Write Flow

```python
# Before LLM call (build context):
profile = await self.student_mcp.get_profile(student_id)
mastery = await self.student_mcp.get_mastery_state(student_id)
session = await self.student_mcp.get_active_session(student_id)

# After LLM call (persist evaluation):
await self.student_mcp.update_mastery(student_id, obj_id, level, evidence)
await self.student_mcp.update_session_state(session_id, stage=new_stage)
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

## Running

```bash
# Standalone (for testing)
PYTHONPATH=src python -m student_mcp

# Via poetry
poetry run student-mcp
```

## File Structure

```
src/student_mcp/
    __init__.py       # Package docstring
    __main__.py       # python -m entry point
    server.py         # FastMCP server + tool definitions
    database.py       # StudentDatabase class + all SQL
    ARCHITECTURE.md   # This file
```
