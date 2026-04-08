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

import copy
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _normalize_concept_id(label: str) -> str:
    raw = re.sub(r"[^a-z0-9]+", "-", (label or "").strip().lower()).strip("-")
    return raw or "concept"


def _clean_plan_line(line: str) -> str:
    cleaned = re.sub(r"^\s*[-*+]\s*", "", line.strip())
    cleaned = re.sub(r"^\s*\d+[.)]\s*", "", cleaned)
    return cleaned.strip()


def _parse_text_plan_sections(plan_text: str) -> Dict[str, str]:
    section_pattern = re.compile(
        r'(?:^|\n)(?:##?\s*)?(\d{1,2})\.\s*([a-z][\w_]*)\s*\n(.*?)(?=\n(?:##?\s*)?\d{1,2}\.\s*[a-z][\w_]*\s*\n|\Z)',
        re.DOTALL,
    )
    sections: Dict[str, str] = {}
    for match in section_pattern.finditer(plan_text or ""):
        sections[match.group(2).strip().lower()] = match.group(3).strip()
    return sections


def _extract_ordered_concepts_from_text_plan(plan_text: str) -> List[Dict[str, str]]:
    sections = _parse_text_plan_sections(plan_text)
    ordered_labels: List[str] = []

    dependency_body = sections.get("dependency_order", "")
    for raw_line in dependency_body.splitlines():
        line = _clean_plan_line(raw_line)
        if not line:
            continue
        if "->" in line or "→" in line:
            for part in re.split(r"\s*(?:->|→)\s*", line):
                cleaned = _clean_plan_line(part)
                if cleaned:
                    ordered_labels.append(cleaned)
        else:
            ordered_labels.append(line)

    if not ordered_labels:
        concept_body = sections.get("concept_decomposition", "")
        for raw_line in concept_body.splitlines():
            line = _clean_plan_line(raw_line)
            if not line or len(line.split()) < 2:
                continue
            ordered_labels.append(line)

    seen = set()
    concepts = []
    for label in ordered_labels:
        concept_id = _normalize_concept_id(label)
        if concept_id in seen:
            continue
        seen.add(concept_id)
        concepts.append({
            "id": concept_id,
            "label": label,
            "status": "not_covered",
        })
    return concepts


def _build_lesson_state(plan: Any) -> Dict[str, Any]:
    concepts: List[Dict[str, str]] = []

    if isinstance(plan, dict) and plan.get("concepts"):
        order = plan.get("recommended_order") or []
        concepts_by_id = {}
        for concept in plan.get("concepts", []):
            concept_id = str(concept.get("id") or _normalize_concept_id(concept.get("name", "")))
            concepts_by_id[concept_id] = {
                "id": concept_id,
                "label": concept.get("name", concept_id),
                "status": concept.get("status", "not_covered"),
            }
        for concept_id in order:
            normalized = str(concept_id)
            if normalized in concepts_by_id:
                concepts.append(concepts_by_id.pop(normalized))
        concepts.extend(concepts_by_id.values())
    elif isinstance(plan, str):
        concepts = _extract_ordered_concepts_from_text_plan(plan)

    if not concepts:
        return {}

    active = next(
        (concept for concept in concepts if concept.get("status") != "covered"),
        concepts[0],
    )
    return {
        "active_concept": active["id"],
        "pending_check": active["label"],
        "bridge_back_target": active["id"],
        "teaching_order": [concept["id"] for concept in concepts],
        "concepts": concepts,
    }


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

    def restore(self, session_id: str, entry: Dict[str, Any]) -> None:
        """Restore a previously persisted cache entry."""
        if not entry:
            return
        restored = {
            "objective_id": str(entry.get("objective_id", "") or ""),
            "objective_text": str(entry.get("objective_text", "") or ""),
            "rag_chunks": list(entry.get("rag_chunks", []) or []),
            "wcag_context": str(entry.get("wcag_context", "") or ""),
            "teaching_content": str(entry.get("teaching_content", "") or ""),
            "retrieval_bundle": entry.get("retrieval_bundle"),
            "lesson_state": dict(entry.get("lesson_state", {}) or {}),
            "retrieved_at": str(
                entry.get("retrieved_at") or datetime.now().isoformat()
            ),
        }
        if "teaching_plan" in entry:
            restored["teaching_plan"] = entry.get("teaching_plan")
        self._cache[session_id] = copy.deepcopy(restored)

    def export_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Return a JSON-safe snapshot of the cache entry for persistence."""
        entry = self._cache.get(session_id)
        return copy.deepcopy(entry) if entry else None

    def store(
        self,
        session_id: str,
        objective_id: str,
        objective_text: str,
        rag_chunks: List[Dict],
        wcag_context: str,
        teaching_content: str,
        retrieval_bundle: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Cache teaching content for a session's active objective.

        Args:
            session_id:       The session this content belongs to.
            objective_id:     The objective this content teaches.
            objective_text:   Human-readable objective description.
            rag_chunks:       Full quiz chunks with feedback (for assessment rubrics).
            wcag_context:     Full WCAG MCP content (authoritative reference).
            teaching_content: Combined formatted string for prompt injection.
            retrieval_bundle: Structured retrieval artifact used to build the
                compact teaching content for guided sessions.
        """
        self._cache[session_id] = {
            "objective_id": objective_id,
            "objective_text": objective_text,
            "rag_chunks": rag_chunks,
            "wcag_context": wcag_context,
            "teaching_content": teaching_content,
            "retrieval_bundle": retrieval_bundle,
            "lesson_state": {},
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

    def get_retrieval_bundle(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get the structured retrieval bundle for the active objective."""
        entry = self._cache.get(session_id)
        bundle = entry.get("retrieval_bundle") if entry else None
        return bundle if bundle else None

    # ------------------------------------------------------------------
    # Teaching plan (concept decomposition)
    # ------------------------------------------------------------------

    def store_teaching_plan(self, session_id: str, plan) -> None:
        """Store a teaching plan for the active objective.

        Accepts either a dict (legacy JSON format) or str (new 17-section text format).
        """
        entry = self._cache.get(session_id)
        if entry:
            entry["teaching_plan"] = plan
            entry["lesson_state"] = _build_lesson_state(plan)
            if isinstance(plan, dict):
                detail = f"{len(plan.get('concepts', []))} concepts"
            else:
                detail = f"{len(str(plan))} chars"
            logger.info(f"Teaching plan stored for session={session_id} ({detail})")

    def get_teaching_plan(self, session_id: str):
        """Get the teaching plan for the current objective. Returns None if not set."""
        entry = self._cache.get(session_id)
        return entry.get("teaching_plan") if entry else None

    def update_concept_status(
        self, session_id: str, concept_id: str, status: str,
    ) -> None:
        """Mark a concept as covered/partially_covered/not_covered.

        Updates both the legacy plan structure (when present) and the structured
        lesson state used by the guided runtime.
        """
        plan = self.get_teaching_plan(session_id)
        if plan and isinstance(plan, dict):
            for concept in plan.get("concepts", []):
                if concept.get("id") == concept_id:
                    concept["status"] = status
                    logger.debug(f"Concept {concept_id} → {status}")
                    break
        lesson_state = self.get_lesson_state(session_id)
        if not lesson_state:
            return
        for concept in lesson_state.get("concepts", []):
            if concept.get("id") == concept_id:
                concept["status"] = status
                break
        self._sync_active_concept(lesson_state)

    def get_lesson_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        entry = self._cache.get(session_id)
        state = entry.get("lesson_state") if entry else None
        return state if state else None

    def apply_lesson_state_patch(
        self, session_id: str, patch: Optional[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        if not patch:
            return self.get_lesson_state(session_id)
        entry = self._cache.get(session_id)
        if not entry:
            return None
        lesson_state = entry.setdefault("lesson_state", {})
        concepts = lesson_state.setdefault("concepts", [])

        for update in patch.get("concept_updates", []) or []:
            concept_id = str(update.get("concept_id", "")).strip()
            if not concept_id:
                continue
            status = str(update.get("status", "")).strip() or "in_progress"
            label = str(update.get("label", concept_id)).strip() or concept_id
            existing = next(
                (concept for concept in concepts if concept.get("id") == concept_id),
                None,
            )
            if existing:
                existing["status"] = status
                if label:
                    existing["label"] = label
            else:
                concepts.append({"id": concept_id, "label": label, "status": status})
                order = lesson_state.setdefault("teaching_order", [])
                if concept_id not in order:
                    order.append(concept_id)

        for field in ("active_concept", "pending_check", "bridge_back_target"):
            value = str(patch.get(field, "") or "").strip()
            if value:
                lesson_state[field] = value

        self._sync_active_concept(lesson_state)
        return lesson_state

    @staticmethod
    def _sync_active_concept(lesson_state: Dict[str, Any]) -> None:
        concepts = lesson_state.get("concepts", [])
        if not concepts:
            return
        concepts_by_id = {concept.get("id"): concept for concept in concepts}
        teaching_order = lesson_state.get("teaching_order") or [
            concept.get("id") for concept in concepts
        ]
        next_active = None
        for concept_id in teaching_order:
            concept = concepts_by_id.get(concept_id)
            if concept and concept.get("status") != "covered":
                next_active = concept
                break
        if not next_active:
            next_active = concepts[0]
        if lesson_state.get("bridge_back_target") not in concepts_by_id:
            lesson_state["bridge_back_target"] = next_active.get("id", "")
        if not str(lesson_state.get("pending_check", "") or "").strip():
            lesson_state["pending_check"] = next_active.get("label", "")
        current_active = concepts_by_id.get(lesson_state.get("active_concept"))
        if not current_active or current_active.get("status") == "covered":
            lesson_state["active_concept"] = next_active.get("id", "")

    @property
    def size(self) -> int:
        """Number of sessions with cached content."""
        return len(self._cache)
