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
