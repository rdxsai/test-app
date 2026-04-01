# WCAG Socratic Tutoring Platform

A web application for managing Canvas LMS quiz questions with AI-powered feedback generation and a **dual-instance Socratic tutoring chatbot** that teaches web accessibility through personalized, stage-based conversation.

**TLOS — Virginia Tech**

## System Overview

The platform combines quiz management with an intelligent tutoring system:

- **Quiz Management**: Import questions from Canvas LMS, generate AI feedback, manage learning objectives, associate questions to objectives
- **Instance A — Q&A Chatbot**: Student-driven Socratic conversations grounded in quiz data + WCAG guidelines
- **Instance B — Guided Learning**: Chatbot-driven structured learning with onboarding, stage-based teaching, assessment, and mastery tracking

**Stack**: FastAPI, PostgreSQL/pgvector, Ollama (nomic-embed-text), Azure OpenAI (GPT-4), WCAG MCP Server (Node.js), Custom Student MCP Server (Python), WebSocket streaming

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                           │
│                                                             │
│  Instance A (Q&A)          Instance B (Guided Learning)     │
│  /chat/ws                  /chat/guided/ws                  │
│       │                         │                           │
│       └────────┬────────────────┘                           │
│                │                                            │
│    ┌───────────┴───────────┐                                │
│    │  Socratic Prompts     │   Stage Machine                │
│    │  (SocraticLM +        │   (intro → explore →           │
│    │   SocraticMATH)       │    assess → master)            │
│    └───────────┬───────────┘                                │
│                │                                            │
│    ┌───────────┴───────────────────────┐                    │
│    │     Dual-Source Retrieval         │                    │
│    │  ┌──────────┐  ┌──────────────┐  │                    │
│    │  │ pgvector │  │  WCAG MCP    │  │                    │
│    │  │ RAG      │  │  Server      │  │                    │
│    │  │ (HyDE +  │  │  (Node.js)   │  │                    │
│    │  │  BM25)   │  │              │  │                    │
│    │  └──────────┘  └──────────────┘  │                    │
│    └──────────────────────────────────┘                    │
│                │                                            │
│    ┌───────────┴───────────┐                                │
│    │  Student MCP Server   │  PostgreSQL                    │
│    │  (Python, FastMCP)    │  + pgvector                    │
│    │  12 tools, 5 tables   │                                │
│    └───────────────────────┘                                │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | Purpose |
|-----------|---------|
| **Socratic Prompts** | Research-backed teaching (SocraticLM NeurIPS 2024, SocraticMATH CIKM 2024) — 6 cognitive states, 4 response modes, anti-patterns, termination rules |
| **WCAG MCP Server** | Authoritative WCAG 2.2 content via MCP tools — complete SC routing table (~86 criteria), `get_full_criterion_context` as primary tool |
| **Student MCP Server** | Custom Python MCP server — 12 tools for student profiles, mastery tracking, session state, misconception logging, session summaries |
| **Stage Machine** | Enforces learning progression: introduction → exploration → readiness check → mini assessment (2/3) → final assessment (4/5) → transition |
| **Session Content Cache** | Teaching content cached per objective — retrieved once, reused across all turns within that objective |
| **Eval Pipeline** | RAG triple capture, computed metrics (readability, ROUGE-L, BLEU), evaluation log with API |

## Quick Start (Docker)

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+

### Setup

```bash
git clone https://github.com/rdxsai/Merged-App.git
cd Merged-App

# Configure environment
cp .env.docker.template .env
# Edit .env with your Azure OpenAI and Canvas credentials

# Start all services
docker compose up -d --build

# Seed the database with gold dataset
docker exec question-app-backend python scripts/rebuild_db_from_converted_exports.py --execute --wipe --add-extra-columns --schema dev

# Build vector store (embeddings for RAG)
curl -X POST http://localhost:8080/vector-store/create
```

### Access

| URL | Description |
|-----|-------------|
| http://localhost:8080 | Home — Question management |
| http://localhost:8080/chat | Instance A — Q&A Chatbot |
| http://localhost:8080/chat/guided | Instance B — Guided Learning |
| http://localhost:8080/eval/logs | Evaluation pipeline API |

## Guided Learning (Instance B)

The guided learning chatbot provides personalized, stage-based accessibility education:

### Onboarding
Structured 3-step form (clickable options, not free text):
1. Technical background (developer, designer, student, etc.)
2. Accessibility experience (none → awareness → working knowledge → professional)
3. Learning motivation (certification, job requirement, personal interest)

### Level-Based Objective Selection

| Student Level | Starting Objective |
|--------------|-------------------|
| None | Explain the structure of WCAG 2.2 (POUR, guidelines, A/AA/AAA) |
| Awareness / Working knowledge | Understand how ARIA live region properties impact AT behavior |
| Professional | Analyze design elements (headings, landmarks, contrast) for diverse user groups |

### Stage-Based Learning Cycle

```
Introduction → Exploration → Readiness Check → Mini Assessment (2/3) →
Final Assessment (4/5) → Mastered → Transition to next objective
```

- **Smart max-turns**: After 8 exploration turns, decides based on student state (assess vs. re-explore)
- **Mastery caps**: Only assessment scoring can grant "partial" or "mastered" — prevents premature promotion
- **Misconception tracking**: Logged per objective, deduplicated, used to target teaching

### Multi-Student Sidebar
ChatGPT-style sidebar for managing multiple student sessions:
- Create new students with different experience levels
- Switch between sessions (chat persists via localStorage)
- Reset or delete individual sessions

## Student MCP Server

Custom Python MCP server (FastMCP, stdio transport) with 12 tools:

**Read tools** (before LLM call):
`get_student_profile`, `get_mastery_state`, `get_active_session`, `get_misconception_patterns`, `get_recommended_next_objective`, `get_session_summary`

**Write tools** (after LLM call):
`create_student_profile`, `update_mastery`, `log_misconception`, `update_session_state`, `save_session_summary`, `update_student_preferences`

5 tables in dedicated `student_mcp` schema: `student_profiles`, `mastery_records`, `session_state`, `session_summaries`, `misconception_log`

## Evaluation Pipeline

- **RAG Triple Capture**: Automatically captures (query, retrieved_contexts, response) for every chatbot interaction
- **Computed Metrics**: Flesch-Kincaid readability, ROUGE-L, BLEU-1, cross-reference consistency, question discriminability
- **Eval Log API**: `GET /eval/logs`, `GET /eval/summary/{type}`, `GET /eval/rag/samples`

## Project Structure

```
src/
  question_app/                    # Main FastAPI application
    api/                           # API routers (canvas, chat, eval, questions, objectives)
    core/                          # Config, logging, app setup
    models/                        # Pydantic models
    services/
      eval/                        # Evaluation pipeline (repository, metrics, thresholds)
      tutor/
        hybrid_system.py           # Main orchestrator (Instance A + B)
        stage_machine.py           # Stage transitions and assessment scoring
        session_cache.py           # Teaching content cache
        prompts/
          socratic_tutor.py        # Research-backed Socratic prompt templates
      database.py                  # PostgreSQL DatabaseManager
      student_mcp_client.py        # Client for Student MCP Server
      wcag_mcp_client.py           # Client for WCAG MCP Server
    utils/                         # Text processing, file utilities
  student_mcp/                     # Custom Student MCP Server (separate subprocess)
    server.py                      # FastMCP server + 12 tool definitions
    database.py                    # StudentDatabase (own connection pool, own schema)
templates/
  chat.html                        # Instance A frontend
  chat_guided.html                 # Instance B frontend (multi-student sidebar)
tests/
  student_mcp/                     # 155 tests (DB, MCP smoke, stage machine, prompts, eval, metrics)
```

## Development

```bash
# Run tests
PYTHONPATH=src python -m pytest tests/student_mcp/ -q

# Rebuild backend after code changes
docker compose up -d --build backend

# View guided learning logs
docker compose logs backend | grep "\[GUIDED\]\|\[ONBOARDING\]"
```

## Docker Services

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| backend | Custom (Python 3.11) | 8080 | FastAPI app + Student MCP subprocess |
| postgres | pgvector/pgvector:pg16 | 5432 | PostgreSQL with vector extension |
| ollama | ollama/ollama | 11434 | Embedding model (nomic-embed-text) |

## Authors

- **Bryce Kayanuma** — Initial quiz management app — [BrycePK@vt.edu](mailto:BrycePK@vt.edu)
- **Robert Fentress** — Project lead — [learn@vt.edu](mailto:learn@vt.edu)
- **Rudra Desai** — Socratic tutoring chatbot, Student MCP, evaluation pipeline — Gen AI Engineer, TLOS
