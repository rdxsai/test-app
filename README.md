# WCAG Socratic Tutoring Platform

A web application for managing Canvas LMS quiz questions with AI-powered feedback generation and a **dual-instance Socratic tutoring chatbot** that teaches web accessibility through personalized, stage-based conversation.

**TLOS — Virginia Tech**

## System Overview

The platform combines quiz management with an intelligent tutoring system:

- **Quiz Management**: Import questions from Canvas LMS, generate AI feedback, manage learning objectives, associate questions to objectives
- **Instance A — Q&A Chatbot**: Student-driven Socratic conversations grounded in quiz data + WCAG guidelines
- **Instance B — Guided Learning**: Chatbot-driven structured learning with onboarding, stage-based teaching, assessment, and mastery tracking

**Stack**: FastAPI, PostgreSQL/pgvector, Ollama (nomic-embed-text), Azure OpenAI, WCAG MCP Server (Node.js), learner-state persistence in PostgreSQL, WebSocket streaming

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
│    │  Tutor + Reflector    │   Guided stages                │
│    │  prompts              │   (intro → explore →          │
│    │                       │    assessment → transition)    │
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
│    │ Learner state layer   │  PostgreSQL                    │
│    │ (StudentService by    │  + pgvector                    │
│    │  default, MCP compat) │                                │
│    └───────────────────────┘                                │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | Purpose |
|-----------|---------|
| **Socratic Prompts** | Research-backed teaching (SocraticLM NeurIPS 2024, SocraticMATH CIKM 2024) — 6 cognitive states, 4 response modes, anti-patterns, termination rules |
| **WCAG MCP Server** | Authoritative WCAG 2.2 content via MCP tools — complete SC routing table (~86 criteria), `get_full_criterion_context` as primary tool |
| **Learner State Layer** | Direct `StudentService` runtime over the `student_mcp` schema, with optional MCP compatibility path retained in the repo |
| **Guided Runtime** | Tutor-pass plus reflector-pass flow for stage movement, misconception tracking, mastery updates, and memory writes |
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
cp .env.template .env
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

- **Reflector-led stage movement**: Stage changes are judged from learner evidence rather than fixed turn thresholds
- **Mastery caps**: Only assessment scoring can grant "partial" or "mastered" — prevents premature promotion
- **Misconception tracking**: Logged per objective, deduplicated, used to target teaching

### Multi-Student Sidebar
ChatGPT-style sidebar for managing multiple student sessions:
- Create new students with different experience levels
- Switch between sessions (chat persists via localStorage)
- Reset or delete individual sessions

## Student State Layer

Guided tutoring persists learner state in a dedicated `student_mcp` PostgreSQL schema.
The current FastAPI runtime uses `StudentService` for direct DB access. The MCP
server and client still exist in the repo as compatibility infrastructure, but
they are not the default runtime path.

Core persisted tables:
- `student_profiles`
- `mastery_records`
- `session_state`
- `session_summaries`
- `misconception_log`
- `learner_memory`
- `objective_memory`

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
        session_cache.py           # Teaching content cache
        prompts/
          socratic_tutor.py        # Guided tutor + reflector prompt templates
      embeddings.py                # Shared Ollama embedding helper
      database.py                  # PostgreSQL DatabaseManager
      student_service.py           # Direct student-state DB service used by runtime
      wcag_mcp_client.py           # Client for WCAG MCP Server
    utils/                         # Text processing, file utilities
  student_mcp/                     # Learner-state database layer
    database.py                    # StudentDatabase (own connection pool, own schema)
templates/
  chat.html                        # Instance A frontend
  chat_guided.html                 # Instance B frontend (multi-student sidebar)
tests/
  student_mcp/                     # Guided tutor + learner-state tests
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
| backend | Custom (Python 3.11) | 8080 | FastAPI app |
| postgres | pgvector/pgvector:pg16 | 5432 | PostgreSQL with vector extension |
| ollama | ollama/ollama | 11434 | Embedding model (nomic-embed-text) |

## Authors

- **Bryce Kayanuma** — Initial quiz management app — [BrycePK@vt.edu](mailto:BrycePK@vt.edu)
- **Robert Fentress** — Project lead — [learn@vt.edu](mailto:learn@vt.edu)
- **Rudra Desai** — Socratic tutoring chatbot, Student MCP, evaluation pipeline — Gen AI Engineer, TLOS
