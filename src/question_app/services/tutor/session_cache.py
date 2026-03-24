"""
Session Content Cache — in-memory teaching content per objective.

Teaching content (RAG quiz chunks + WCAG MCP guidelines) is retrieved once
when a student starts working on an objective and reused across all turns
within that objective. This avoids redundant retrieval calls (~2-3s each)
for every turn during exploration, assessment, and review.

Lifecycle:
  - Populated on first turn of a new objective (after retrieval)
  - Read on every subsequent turn (zero-latency dict lookup)
  - Invalidated on objective change or session end
  - Evicted automatically — lives only as long as the process

This is NOT a persistent cache. It's a Python dict on the
HybridCrewAISocraticSystem instance, scoped to the process lifetime.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SessionContentCache:
    """In-memory cache for teaching content, keyed by session_id.

    Each entry stores the full retrieval results for one objective:
    RAG chunks (with quiz feedback), WCAG MCP content, and the combined
    formatted string ready for prompt injection.
    """

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get cached content for a session. Returns None if not cached."""
        return self._cache.get(session_id)

    def store(
        self,
        session_id: str,
        objective_id: str,
        objective_text: str,
        rag_chunks: List[Dict],
        wcag_context: str,
        teaching_content: str,
    ) -> None:
        """Cache teaching content for a session's active objective.

        Args:
            session_id:       The session this content belongs to.
            objective_id:     The objective this content teaches.
            objective_text:   Human-readable objective description.
            rag_chunks:       Full quiz chunks with feedback (for assessment rubrics).
            wcag_context:     Full WCAG MCP content (authoritative reference).
            teaching_content: Combined formatted string for prompt injection.
        """
        self._cache[session_id] = {
            "objective_id": objective_id,
            "objective_text": objective_text,
            "rag_chunks": rag_chunks,
            "wcag_context": wcag_context,
            "teaching_content": teaching_content,
            "retrieved_at": datetime.now().isoformat(),
        }
        logger.info(
            f"Cached teaching content for session={session_id} "
            f"objective={objective_id} ({len(teaching_content)} chars)"
        )

    def invalidate(self, session_id: str) -> None:
        """Clear cached content for a session (on objective change or session end)."""
        if session_id in self._cache:
            old = self._cache.pop(session_id)
            logger.info(
                f"Invalidated cache for session={session_id} "
                f"(was objective={old.get('objective_id')})"
            )

    def needs_retrieval(self, session_id: str, objective_id: str) -> bool:
        """Check if retrieval is needed for this session + objective.

        Returns True if:
          - No cached content for this session
          - Cached content is for a different objective
        """
        entry = self._cache.get(session_id)
        if entry is None:
            return True
        return entry.get("objective_id") != objective_id

    def get_rag_chunks(self, session_id: str) -> List[Dict]:
        """Get cached RAG chunks for assessment rubric use."""
        entry = self._cache.get(session_id)
        return entry.get("rag_chunks", []) if entry else []

    def get_teaching_content(self, session_id: str) -> str:
        """Get the combined teaching content string for prompt injection."""
        entry = self._cache.get(session_id)
        return entry.get("teaching_content", "") if entry else ""

    @property
    def size(self) -> int:
        """Number of sessions with cached content."""
        return len(self._cache)
