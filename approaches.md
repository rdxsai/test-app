# Approaches: Socratic Tutor Pipeline Improvements

## 1. WebSocket Streaming (replacing POST-based chat)

### Before
The chat used a standard POST endpoint. The browser sent a request, waited for the **entire** response to be generated (all 7-8 LLM calls), and then rendered it all at once. During that wait (often 15-30 seconds), the user saw a generic loading spinner with no indication of progress.

### After
A persistent WebSocket connection (`/chat/ws`) replaces the POST flow. The server pushes **stage updates** as each pipeline step executes (`classifying → searching → composing`), and the final response is streamed **word-by-word** with a typewriter effect (~30ms per word).

The frontend was redesigned:
- **Left panel**: chat with typing indicator that shows the current stage label (e.g., "Searching knowledge base...")
- **Right panel**: live knowledge-source sidebar — RAG chunks and WCAG references appear as soon as they're retrieved, before the response even starts generating
- **Markdown rendering** (via marked.js) + **syntax highlighting** (via highlight.js) for code blocks in responses

### Why it's better
| Aspect | POST | WebSocket |
|--------|------|-----------|
| Perceived latency | User stares at spinner for full duration | User sees progress stages immediately |
| Response delivery | All-at-once after final LLM call | Word-by-word streaming as soon as generation finishes |
| Knowledge sources | Not shown | Displayed in sidebar in real-time |
| Connection model | New HTTP request per message | Single persistent connection, server can push anytime |
| Error feedback | Generic 500 error | Granular `{"type": "error"}` messages mid-conversation |

### Key files
- `src/question_app/api/chat.py` — WebSocket endpoint, auth/message/ping protocol
- `templates/chat.html` — WebSocket client, stage indicators, right panel, markdown rendering
- `src/question_app/services/tutor/simple_system.py` — `chat_stream_async()` (httpx SSE streaming from Azure OpenAI)
- `src/question_app/services/tutor/hybrid_system.py` — `conduct_socratic_session_streaming()`, `_progressive_send()`
- `src/question_app/main.py` — `reload_dirs` for template hot-reloading

---

## 2. Vector DB & RAG Pipeline (answer-feedback chunks, HyDE, hybrid search)

### Before

**Chunking**: Each quiz question produced **N+1 chunks** — 1 question chunk + 1 chunk per answer option. Most wrong-answer chunks were noise (e.g., `"Answer 3: div elements"` with no context about *why* it's wrong). The vector store was full of thin, low-signal fragments.

**Search**: Pure vector search using cosine similarity with a high threshold (`MIN_COSINE_SIMILARITY = 0.7`). A student's raw question (e.g., "what is alt text?") was embedded directly and compared against chunks. But the chunks were answer-shaped ("Alt text provides a text alternative for non-text content...") while the query was question-shaped — a fundamental **semantic mismatch** that degraded retrieval quality.

**No keyword fallback**: If the vector embedding missed a match (e.g., the student used different terminology), there was no fallback. Either the cosine similarity cleared 0.7 or the chunk was dropped entirely.

### After

**Chunking — answer-feedback focused**: Each question now produces **1 focused chunk** centered on the correct answer's feedback (the richest teaching signal). The chunk includes: question text as framing context, correct answer, its explanation/feedback, wrong answers listed as common misconceptions, and the learning objective. This is concise but informationally dense — the LLM expands on these cues at query time.

**HyDE (Hypothetical Document Embedding)**: Before searching, the system generates a **hypothetical correct answer** to the student's question (3-5 sentences, quiz-answer style). This answer-shaped text is embedded and matched against the answer-shaped chunks in the DB — resolving the question↔answer semantic gap. HyDE also resolves vague follow-ups ("can you explain more?") by using the last 4 conversation turns as context.

**Hybrid search (vector + BM25 via RRF)**: Search now combines:
1. **pgvector cosine similarity** on the HyDE embedding (semantic matching)
2. **PostgreSQL BM25** (`ts_rank_cd` on a `content_tsv` tsvector column) on the student's original words (keyword matching)

Results from both are fused using **Reciprocal Rank Fusion**: `rrf_score = 1/(60+vec_rank) + 1/(60+bm25_rank)`. This is rank-based (not score-based), making it robust to different score distributions between the two signals.

**Filtering**: Chunks are filtered by `MAX_COSINE_DISTANCE = 0.3` (tighter than before) and `MIN_RRF_SCORE = 0.01`. If nothing passes, the LLM answers from general knowledge rather than receiving garbage context.

### Why it's better
| Aspect | Before | After |
|--------|--------|-------|
| Chunks per question | N+1 (question + each answer) | 1 (focused on correct answer + feedback) |
| Chunk quality | Thin fragments, many noise answers | Dense teaching signal with misconceptions |
| Query embedding | Raw student question (question-shaped) | HyDE hypothetical answer (answer-shaped) |
| Search method | Vector-only (cosine similarity ≥ 0.7) | Hybrid: vector + BM25 via RRF |
| Keyword matching | None | BM25 with GIN-indexed tsvector column |
| Vague follow-ups | Missed (no context resolution) | Resolved via HyDE using conversation history |
| Bad match handling | Silent inclusion of low-quality chunks | Distance + RRF filtering, graceful fallback |

### Key files
- `src/question_app/api/vector_store.py` — `create_comprehensive_chunks()` rewritten for answer-feedback focused chunking
- `src/question_app/api/pg_vector_store.py` — `hybrid_search()` with RRF SQL query
- `src/question_app/services/tutor/interfaces.py` — `hybrid_search()` added to `VectorStoreInterface`
- `src/question_app/services/database.py` — `content_tsv` tsvector column, GIN index, auto-update trigger
- `src/question_app/services/tutor/hybrid_system.py` — `generate_hyde_query()`, `get_rag_context()` with HyDE + filtering

---

## 3. WCAG MCP Integration + Agent Pipeline Strip

### Before

**No authoritative source**: The tutor answered from LLM training data only. There was no way to cite specific WCAG 2.2 success criteria, techniques, or understanding documents. If the LLM's training data was stale or vague on a particular SC, the response would be too.

**8 LLM calls per query**: Every `conceptual_question` went through:
1. CoordinatorAgent — classify intent
2. HyDE — hypothetical answer for vector search
3. ResponseAnalystAgent — analyze student understanding (knowledge level, misconceptions)
4. ProgressTrackerAgent — assess learning progress (consecutive correct count, phase transitions)
5. QuestionGeneratorAgent — generate the answer
6. SessionOrchestratorAgent — polish the final response

Agents 3-6 existed to support a student mastery tracking system (knowledge levels, session phases, misconception tracking, advancement criteria). But this system was **not fully built** — the analysis/progress data wasn't surfaced anywhere meaningful. These 4 LLM calls burned API tokens on analysis that went unused.

### After

**WCAG MCP client**: A new `WCAGMCPClient` connects to the `wcag-guidelines-mcp` Node.js server via stdio (MCP protocol). It uses **LLM-driven tool selection** — Azure OpenAI function calling decides which tools to invoke based on the student's query:
- `search_wcag` — keyword search across SC titles/descriptions
- `search_techniques` — keyword search across WCAG techniques (H37, ARIA1, etc.)
- `get_full_criterion_context` — full SC details by number (richest data)

The system prompt includes **SC number mappings** (e.g., "captions/subtitles → 1.2.2") so the LLM can go directly to `get_full_criterion_context` instead of relying on substring search. A **multi-turn retry** feeds failures back to the LLM for a second attempt with a different tool strategy.

RAG and MCP run **concurrently** via `asyncio.gather()` in `get_combined_context()`, adding zero additional latency.

**Agent pipeline stripped to single call**: The 4-agent chain (analyst → progress → questioner → orchestrator) is replaced by a single `_generate_response()` method that takes the retrieved context (RAG + WCAG) + conversation history + student query and produces the response directly. All agent class definitions are preserved for future use.

### Why it's better
| Aspect | Before | After |
|--------|--------|-------|
| WCAG source | LLM training data (stale, uncitable) | Authoritative WCAG 2.2 via MCP (citable SCs) |
| LLM calls per query | 7-8 | 4-5 (classify + HyDE + MCP + response) |
| Response coherence | Telephone-game through 4 agents | Single direct generation from full context |
| API cost | ~8 calls × tokens | ~4 calls × tokens (~50% reduction) |
| Latency | Sequential agent chain | Concurrent RAG + MCP, then single response call |
| Mastery tracking agents | Called but output unused | Preserved as classes, not called until system is ready |

### LLM calls after change

| # | Call | Purpose |
|---|------|---------|
| 1 | CoordinatorAgent | Classify intent (`conceptual_question` / `code_analysis_request` / `off_topic`) |
| 2 | HyDE generation | Hypothetical answer for vector search embedding |
| 3 | WCAG MCP tool selection | LLM picks which MCP tools to call via function calling |
| 4 | (optional) WCAG retry | Retry with different tool if round 1 returned empty |
| 5 | `_generate_response()` | Single call: context + history → final response |

### Key files
- `src/question_app/services/wcag_mcp_client.py` — MCP client with LLM-driven tool selection and multi-turn retry
- `src/question_app/core/config.py` — `WCAG_MCP_ENABLED`, `WCAG_MCP_COMMAND` settings
- `Dockerfile` — Node.js + `wcag-guidelines-mcp` npm install
- `pyproject.toml` / `poetry.lock` — `mcp` dependency
- `src/question_app/services/tutor/hybrid_system.py` — `_generate_response()`, simplified session methods, `get_combined_context()` with concurrent RAG + MCP
