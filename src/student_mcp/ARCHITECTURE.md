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

## Tools (Phase 1: 2 of 12 implemented)

### Read Tools
- `get_student_profile(student_id)` — Fetch profile or `{"found": false}`

### Write Tools
- `create_student_profile(student_id, technical_level, a11y_exposure, role_context, learning_goal)` — Idempotent profile creation

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
