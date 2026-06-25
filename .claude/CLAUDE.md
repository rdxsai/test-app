# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> Verified against source. Where behavior is non-obvious, a `file:line` anchor is given. The codebase is **mid-migration** from a monolithic guided-tutor (`hybrid_system.py`) to a **LangGraph "teaching graph" runtime** (`orchestrators.py` + `workers/`); expect legacy/dead paths alongside live ones (see "Legacy & in-migration").

## Commands

```bash
poetry install                  # set up env (Python 3.11)

# Run
poetry run dev                  # uvicorn, port 8080, hot reload (disabled when DOCKER_ENV=true)
poetry run start                # production server, port 8080, no reload

# Tests
poetry run test                 # scripts.run_tests:main (full suite)
poetry run pytest               # direct
poetry run pytest -m unit       # markers: unit, integration, slow, ai, api  (pytest.ini, --strict-markers)
poetry run pytest tests/unit/test_services/test_hybrid_system.py            # one file
poetry run pytest tests/student_mcp/test_prompts.py::TestTutorPrompts::test_tutor_prompt_format   # one test
poetry run pytest --cov=src --cov-report=html                               # coverage
PYTHONPATH=src python -m pytest tests/student_mcp/ -q                       # student-state suite (intentionally standalone, no question_app import)

# Quality
poetry run lint                 # Black + Flake8 + isort (check)
poetry run format               # Black + isort (apply); line length 88, isort black profile
poetry run type-check           # mypy + pyright

# Docker (3 services: backend:8080, postgres pgvector pg16, ollama)
docker compose up -d --build
docker exec question-app-backend python scripts/rebuild_db_from_converted_exports.py --execute --wipe --add-extra-columns --schema dev
curl -X POST http://localhost:8080/vector-store/create   # build pgvector embeddings (must run after seeding)
```

## External dependency (not vendored)

The WCAG content tool is an **external npm package, `wcag-guidelines-mcp` (must be on PATH)** — spawned as a stdio MCP subprocess by `services/wcag_mcp_client.py`. It is NOT in this repo. Set `WCAG_MCP_COMMAND` / `WCAG_MCP_ENABLED` to configure. Embeddings require an **Ollama** server with `nomic-embed-text` (Docker auto-pulls it).

## Big picture

One FastAPI app (`question_app`) over **PostgreSQL + pgvector**, exposing three surfaces:

1. **Quiz management + AI authoring** — import questions from Canvas LMS (`api/canvas.py`), generate feedback / suggest & generate objectives via `AIGeneratorService` (`services/ai_service.py`), CRUD under `/questions`, `/objectives`.
2. **Instance A** (`/chat`) — stateless hybrid-RAG Q&A bot (`services/general_chat_service.py`).
3. **Instance B** (`/chat/guided`) — stateful, stage-based Socratic WCAG tutor with persisted learner state.

Both chatbots share **one retrieval implementation** (`api/pg_vector_store.py: hybrid_search`) and the **same Azure client** (`services/tutor/azure_client.py`).

### Boot model — read this first
The app is constructed at **import time as a side effect** (`main.py:67-72`): it connects the DB, configures logging (`core/app.py:16`), and `api/chat.py:46-127` eagerly builds the whole service graph (vector store, Azure client, WCAG client, both chat systems) inside a try/except that sets services to `None` on failure → endpoints return 503 / WebSocket closes 1011. There is **no lifespan, no middleware (no CORS/GZip), no `@app.on_event`**. Port 8080 and host 0.0.0.0 are hardcoded in all entry points; only reload is env-driven (`DOCKER_ENV`). 8 routers are registered in `core/app.py:65-72`. NOTE: `api/pg_vector_store.py` is **not** a router — it is `VectorStoreService` (a service mis-located in `api/`).

### Instance A flow (`services/general_chat_service.py`)
WS `/chat/ws` → `handle_message_streaming` (svc:785): intent classify → **HyDE** query rewrite (svc:272) → `hybrid_search(query=hyde, k=5, bm25_query=original)` (svc:542) + WCAG MCP context concurrently (`asyncio.gather`, svc:594) → filter to top 3 chunks → `build_instance_a_prompt` → drain Azure stream, then **re-emit token-by-token at 8 ms/token** (`asyncio.sleep(0.008)`, svc:642 — this drip-feed lives here, NOT in `azure_client.py`) → persist eval telemetry (`_capture_rag_sample`, svc:645). Conversation history is **in-memory only** (`InMemoryChatSessionStore`, 12-msg cap) — but eval rows ARE written to the DB.

### Instance B architecture (`services/tutor/`) — the core, and the messiest part
Three live layers:

```
HybridCrewAISocraticSystem   (hybrid_system.py:281 — a "compatibility facade", ~3000 lines)
  └─ GuidedTurnOrchestrator  (orchestrators.py:137 — the real per-turn driver)
       └─ LangGraph StateGraph (orchestrators.py:184 — compiled, invoked every normal turn)
```

- Entry: WS `/chat/guided/ws` → `conduct_guided_session_streaming` (hybrid_system.py:2856) → `run_guided_turn` (orchestrators.py:402).
- **A normal turn is 4 graph nodes / 3 LLM passes, reflector FIRST:** `analyze_turn` (reflector, `workers/turns.py:126`) → `apply_analysis_updates` (**deterministic** state writes + stage transition, `hybrid_system.py:2428`) → `decide_graph_progression` (`workers/turns.py:235`) → `compose_tutor_response` (tutor, `hybrid_system.py:2801`).
- **The tutor pass calls NO tools.** All learner-state mutation (log/resolve misconception, mastery, assessment scoring) is plain Python driven by the analyzer's structured JSON. There is no LLM tool-calling loop in the live turn.
- **Teaching graph:** built once per objective by `TeachingGraphBuildOrchestrator` (`orchestrators.py:42`) + workers in `workers/graph.py`. The evidence retriever (`NodeEvidenceRetrieverWorker`) is the one place that uses an LLM **tool loop**, via the Azure **Responses API** (`gpt-5.4`), calling WCAG retrieval tools (per-node budget `TEACHING_GRAPH_NODE_RETRIEVAL_MAX_TOOL_CALLS=4`, loop `max_rounds=8`).
- **Stage machine (7 lowercase stages):** `onboarding → introduction → exploration → readiness_check → mini_assessment → final_assessment → transition` (`hybrid_system.py:76`). Transitions are the reflector's recommendation, gated by deterministic guardrails (coverage < 0.6 blocks advance to assessment; single-step clamping `_normalize_stage_transition:1388`; `_enforce_turn_response_controls:1457`). Assessment stages advance as a side-effect of `record_assessment_answer` scoring.

### Prompts (`services/tutor/prompts/`)
The Instance B system prompt is assembled by **`build_instance_b_prompt` in `prompts/socratic_tutor.py:1698`** (NOT in `hybrid_system.py`) as `TUTOR_SYSTEM_PROMPT` (monolithic, :1054) `+` a `context_block` (student context → stage/objective → teaching plan → lesson state → misconception state → evidence pack). Graph prompts live in `prompts/graph.py`. Analyzer/reflector prompt: `TURN_ANALYZER_PROMPT` (:1420; `GUIDED_REFLECTOR_PROMPT` is an alias). The tutor's "next move" enum is `continue | clarify | repair | consolidate | redirect` (:1552).

### RAG (`api/pg_vector_store.py`, `services/embeddings.py`)
Build: 1 chunk per question → Ollama `nomic-embed-text` (**768-dim**) → `question_embeddings vector(768)` + IVFFlat cosine index. Query (`hybrid_search`): a CTE merging pgvector cosine (`<=>`) with Postgres full-text `ts_rank_cd` (labeled "BM25" but it's `ts_rank_cd`, not Okapi) via **Reciprocal Rank Fusion, k=60**; falls back to vector-only on error; then distance/RRF filtering → top 3. **HyDE** is implemented in both runtimes (`hybrid_system.py:648`, `general_chat_service.py:272` — duplicated logic).

### Learner state (`services/student_service.py`, `src/student_mcp/database.py`)
`StudentService` is an **async wrapper** (every method → `asyncio.to_thread`) over `StudentDatabase`, which owns its **own** connection pool and the **`student_mcp` schema** (7 tables: `student_profiles`, `mastery_records`, `session_state`, `session_summaries`, `misconception_log`, `learner_memory`, `objective_memory`), with cross-schema reads into `prod.learning_objective`. Mastery promotion is gated in **`apply_mastery_judgment`** (`student_service.py:181`): `confidence ≥ 0.7` (`CONFIDENCE_THRESHOLD`) + `STAGE_MASTERY_CAP`. Stage transitions are validated by `validate_stage_transition` against `VALID_TRANSITIONS` (`database.py:30`). Assessment scoring: mini 3 (pass 2), final 5 (mastery 4 / partial 3).

> The "MCP" in `student_mcp` is **vestigial** — the MCP server, stdio client, and entry point were deleted (commit `fe5a632`). The live path is direct psycopg2 via `StudentService`. The `student_mcp_client` kwarg passed to the tutor (`chat.py:114`) is just a label for a plain `StudentService`.

### Eval pipeline (`services/eval/`)
Tables `eval_log` + `rag_eval_samples` (`services/database.py:243-281`). `EvalRepository` capture is **awaited inline** (not a background task) and **conditional** (needs a DB connection + non-empty retrieved chunks; Instance B also needs cached `rag_chunks`), wrapped in try/except so failures don't break a turn. Real wired metrics: `flesch_kincaid` (textstat), `rouge_l`, `bleu_1` (`computed_metrics.py`), exposed via `POST /eval/compute/*` and the offline `instance_a_benchmark.py` (which adds an LLM judge). 11 `/eval/*` endpoints total.

### Frontend (`templates/`)
`chat.html` → WS `/chat/ws` (no persistence). `chat_guided.html` → WS `/chat/guided/ws` with a **multi-student sidebar** and **localStorage** persistence (roster `guided_students`, active `guided_active`, per-student `chat_${id}` history + mastery/teaching panels); ~26 inbound message types (`stage_update`, `mastery_update`, `teaching_plan`, `node_evidence`, `turn_analysis`, …).

## Configuration (`core/config.py`)
Loaded from `.env`. Key vars (defaults in parens): `DB_SCHEMA` (**`prod`** — selects the data partition via `SET search_path`), `POSTGRES_*`, `OLLAMA_HOST` (`localhost:11434`) / `OLLAMA_EMBEDDING_MODEL` (`nomic-embed-text`), `AZURE_OPENAI_ENDPOINT/DEPLOYMENT_ID/SUBSCRIPTION_KEY`, plus separate deployments: `AZURE_OPENAI_TUTOR_DEPLOYMENT_ID`, `AZURE_OPENAI_REASONING_DEPLOYMENT_ID` (auto-derived by stripping `-mini`), `AZURE_OPENAI_INSTANCE_A_DEPLOYMENT_ID`, and the **Responses API** path `AZURE_OPENAI_RESPONSES_DEPLOYMENT_ID` (`gpt-5.4`) / `OPENAI_RESPONSES_ENABLED` (`true`). Toggles: `WCAG_MCP_ENABLED`, `STUDENT_MCP_ENABLED`. `_is_reasoning_model` (`azure_client.py:81`) matches `gpt-5/o1/o3/o4` and switches to `max_completion_tokens` + `reasoning_effort`, dropping `temperature`.

## Database schemas
- **`dev` / `prod`** (chosen by `DB_SCHEMA`): `question`, `answer`, `learning_objective`, `question_objective_association`, `question_embeddings`, `eval_log`, `rag_eval_samples`.
- **`student_mcp`** (always): the 7 learner-state tables above.

## Legacy & in-migration (do NOT build on these)
- The class name `HybridCrewAISocraticSystem` is **vestigial** — it's a compatibility facade over the worker/orchestrator stack; there is no `crewai` dependency (the old simulated `SocraticAgent`/`CoordinatorAgent`/`CodeAnalyzerAgent` and the legacy `conduct_socratic_session*` Instance-A wrappers have been removed). Rename candidate.
- `AGENT_TOOL_INSTRUCTIONS` + the "6 LLM-callable MCP tools" are **prompt prose only** (intentionally deferred for a v2 student-model integration; never injected into the live prompt, never serialized as function tools — `test_agent_tools.py` enforces this). State changes are deterministic Python. The bare, unvalidated `StudentService.update_mastery` is the intended future handler; the live path is the validated `apply_mastery_judgment`.
- `graph_runtime.py` is **misnamed** — it holds runtime-state helpers + `GRAPH_ORCHESTRATOR_PROMPT`, NOT the LangGraph graph (that's in `orchestrators.py`).

## Tests & scripts
Pytest with `asyncio_mode` (pytest-asyncio). The `tests/student_mcp/` suite is standalone (`PYTHONPATH=src`, no `question_app` import). `tests/unit/` covers tutor/guided core, azure client, wcag client, analyzer schema, eval; `tests/integration/` and `tests/e2e/` exist; live Azure tests gate on `RUN_LIVE_AZURE_RESPONSES_TEST=true`. `scripts/` (≈37) split into: DB rebuild/seed/import-export (`rebuild_db_from_converted_exports.py` is primary, dry-run by default), one-off migrations, eval/benchmark, trace/demo replays, and dev tooling (`lint_code.py`, etc. — the `poetry run` script targets).

## Conventions
Black (88) + isort (black profile); explicit names for service/worker classes; tests `test_*.py` / `Test*` / `test_*`. Commits use scoped imperative subjects (e.g. `guided-runtime: handle websocket disconnects cleanly`); keep generated `results/` artifacts out of source commits.
