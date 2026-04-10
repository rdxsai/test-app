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


_PACING_SIGNAL_WINDOW = 4
_PACE_CHANGE_COOLDOWN = 2


def _normalize_concept_id(label: str) -> str:
    raw = re.sub(r"[^a-z0-9]+", "-", (label or "").strip().lower()).strip("-")
    return raw or "concept"


def _concept_match_key(text: str) -> str:
    """Collapse a concept ID or label to a canonical match key.

    Strips all non-alphanumeric characters and lowercases so that
    ``prefer_native_html``, ``prefer-native-html``, and
    ``Prefer native HTML`` all produce the same key.
    """
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())


def _normalize_runtime_key(text: str) -> str:
    raw = re.sub(r"[^a-z0-9]+", "_", (text or "").strip().lower()).strip("_")
    return raw or "item"


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


_BOLD_RE = re.compile(r"^\*\*(.+?)\*\*\s*$")
_NOISE_RE = re.compile(
    r"^(?:#{2,}\s|depends on |no dependency)",
    re.IGNORECASE,
)


def _extract_ordered_concepts_from_text_plan(plan_text: str) -> List[Dict[str, str]]:
    sections = _parse_text_plan_sections(plan_text)
    ordered_labels: List[str] = []

    dependency_body = sections.get("dependency_order", "")
    for raw_line in dependency_body.splitlines():
        line = _clean_plan_line(raw_line)
        if not line:
            continue

        # Arrow-separated chains (e.g., "A → B → C")
        if "->" in line or "→" in line:
            for part in re.split(r"\s*(?:->|→)\s*", line):
                cleaned = _clean_plan_line(part)
                if cleaned and not _NOISE_RE.match(cleaned):
                    # Unwrap bold if present
                    m = _BOLD_RE.match(cleaned)
                    ordered_labels.append(m.group(1) if m else cleaned)
            continue

        # Skip sub-headings and dependency annotations
        if _NOISE_RE.match(line):
            continue

        # Prefer bold-wrapped concept names; accept plain numbered items
        # only when they look like concept labels (short, no trailing period).
        m = _BOLD_RE.match(line)
        if m:
            ordered_labels.append(m.group(1))
        elif len(line.split()) >= 2 and not line.endswith("."):
            ordered_labels.append(line)

    if not ordered_labels:
        concept_body = sections.get("concept_decomposition", "")
        for raw_line in concept_body.splitlines():
            line = _clean_plan_line(raw_line)
            if not line or len(line.split()) < 2:
                continue
            m = _BOLD_RE.match(line)
            ordered_labels.append(m.group(1) if m else line)

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


def _build_lesson_state(
    plan: Any,
    extracted_concepts: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    concepts: List[Dict[str, str]] = []

    # Priority 1: LLM-extracted concept list (structured, no regex needed)
    if extracted_concepts:
        seen: set = set()
        for item in extracted_concepts:
            cid = str(
                item.get("id")
                or _normalize_concept_id(item.get("label", ""))
            )
            if cid in seen:
                continue
            seen.add(cid)
            concepts.append({
                "id": cid,
                "label": item.get("label", cid),
                "status": "not_covered",
            })

    # Priority 2: Legacy JSON plan with concepts array
    if not concepts and isinstance(plan, dict) and plan.get("concepts"):
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

    # Priority 3: Regex fallback for text plans
    if not concepts and isinstance(plan, str):
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
            "pacing_state": self._normalize_pacing_state(
                entry.get("pacing_state")
            ),
            "misconception_state": self._normalize_misconception_state(
                entry.get("misconception_state")
            ),
            "retrieved_at": str(
                entry.get("retrieved_at") or datetime.now().isoformat()
            ),
        }
        if "teaching_plan" in entry:
            restored["teaching_plan"] = entry.get("teaching_plan")
        self._cache[session_id] = copy.deepcopy(restored)

    # Fields persisted to durable storage.  The retrieval_bundle is included
    # (slimmed) so the structured evidence can be re-rendered, audited, or
    # fed to different prompts without re-running retrieval.  Legacy fields
    # (rag_chunks, wcag_context) are never persisted.
    _PERSIST_FIELDS = (
        "objective_id",
        "objective_text",
        "teaching_content",
        "teaching_plan",
        "lesson_state",
        "pacing_state",
        "misconception_state",
        "retrieved_at",
        "retrieval_bundle",
    )

    # Per-item keys stripped from retrieval_bundle sections before persistence.
    # These are retrieval-order diagnostics that aren't needed for re-rendering
    # or audit — the content itself is what matters.
    _BUNDLE_STRIP_KEYS = ("round", "sequence")

    @classmethod
    def _slim_bundle(cls, bundle: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Return a persistence-friendly copy of the retrieval bundle.

        Drops ``raw_hits`` (redundant diagnostic metadata already represented
        in sections) and per-item retrieval-order fields to cut ~40% of the
        JSONB size while preserving the structured evidence for re-rendering
        and audit.
        """
        if not bundle or not isinstance(bundle, dict):
            return bundle
        slim = {k: v for k, v in bundle.items() if k != "raw_hits"}
        sections = slim.get("sections")
        if isinstance(sections, dict):
            slim["sections"] = {
                name: [
                    {k: v for k, v in item.items() if k not in cls._BUNDLE_STRIP_KEYS}
                    for item in items
                ]
                for name, items in sections.items()
                if isinstance(items, list)
            }
        return slim

    def export_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Return a slim, JSON-safe snapshot of the cache entry for persistence.

        Includes a slimmed retrieval_bundle (no raw_hits, no per-item
        round/sequence) so structured evidence survives restarts.  Legacy
        fields (rag_chunks, wcag_context) are omitted.
        """
        entry = self._cache.get(session_id)
        if not entry:
            return None
        snapshot = {k: entry[k] for k in self._PERSIST_FIELDS if k in entry}
        if "retrieval_bundle" in snapshot:
            snapshot["retrieval_bundle"] = self._slim_bundle(snapshot["retrieval_bundle"])
        return copy.deepcopy(snapshot)

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
            "pacing_state": self._default_pacing_state(),
            "misconception_state": self._default_misconception_state(),
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
    # Adaptive pacing runtime state
    # ------------------------------------------------------------------

    @staticmethod
    def _default_pacing_state() -> Dict[str, Any]:
        return {
            "current_pace": "steady",
            "pace_reason": "Default steady pace until enough recent evidence accumulates.",
            "turns_at_current_pace": 0,
            "cooldown_remaining": 0,
            "recent_signals": [],
        }

    @classmethod
    def _normalize_pacing_state(
        cls, pacing_state: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        normalized = cls._default_pacing_state()
        if not pacing_state or not isinstance(pacing_state, dict):
            return normalized

        pace = str(pacing_state.get("current_pace", "") or "").strip().lower()
        if pace in {"slow", "steady", "fast"}:
            normalized["current_pace"] = pace

        reason = str(pacing_state.get("pace_reason", "") or "").strip()
        if reason:
            normalized["pace_reason"] = reason

        try:
            normalized["turns_at_current_pace"] = max(
                0, int(pacing_state.get("turns_at_current_pace", 0) or 0)
            )
        except (TypeError, ValueError):
            normalized["turns_at_current_pace"] = 0

        try:
            normalized["cooldown_remaining"] = max(
                0, int(pacing_state.get("cooldown_remaining", 0) or 0)
            )
        except (TypeError, ValueError):
            normalized["cooldown_remaining"] = 0

        normalized["recent_signals"] = [
            cls._compact_pacing_signal(signal)
            for signal in (pacing_state.get("recent_signals", []) or [])
            if isinstance(signal, dict)
        ][-_PACING_SIGNAL_WINDOW:]
        return normalized

    @staticmethod
    def _compact_pacing_signal(signal: Optional[Dict[str, Any]]) -> Dict[str, str]:
        if not signal or not isinstance(signal, dict):
            return {}

        allowed = {
            "grasp_level": {"fragile", "emerging", "solid"},
            "reasoning_mode": {
                "guessing", "recall", "paraphrase", "application", "transfer",
            },
            "support_needed": {"heavy", "moderate", "light", "none"},
            "confusion_level": {"high", "medium", "low"},
            "response_pattern": {
                "guessing", "hedging", "direct", "self_correcting",
            },
            "concept_closure": {"not_ready", "almost_ready", "ready"},
            "override_pace": {"none", "slow", "steady", "fast"},
            "override_reason": None,
            "recommended_next_step": {
                "re-explain", "give_example", "ask_narrower",
                "ask_same_level", "advance",
            },
        }

        compact: Dict[str, str] = {}
        for key, valid_values in allowed.items():
            value = str(signal.get(key, "") or "").strip()
            if not value:
                continue
            if valid_values is not None:
                normalized = value.lower()
                if normalized not in valid_values:
                    continue
                compact[key] = normalized
            else:
                compact[key] = value
        if "override_pace" not in compact:
            compact["override_pace"] = "none"
        return compact

    @classmethod
    def _is_strong_confusion_signal(cls, signal: Optional[Dict[str, Any]]) -> bool:
        compact = cls._compact_pacing_signal(signal)
        return (
            compact.get("override_pace") == "slow"
            or compact.get("confusion_level") == "high"
            or compact.get("support_needed") == "heavy"
        )

    @classmethod
    def _count_matching(
        cls,
        signals: List[Dict[str, str]],
        key: str,
        values: Any,
    ) -> int:
        allowed = {values} if isinstance(values, str) else set(values or [])
        return sum(1 for signal in signals if signal.get(key) in allowed)

    @classmethod
    def _determine_target_pace(
        cls,
        current_pace: str,
        window: List[Dict[str, str]],
    ) -> Dict[str, str]:
        if len(window) < 3:
            return {
                "target_pace": current_pace or "steady",
                "pace_reason": "Collecting more turns before changing pace.",
            }

        n = len(window)
        solid = cls._count_matching(window, "grasp_level", "solid")
        fragile = cls._count_matching(window, "grasp_level", "fragile")
        app_transfer = cls._count_matching(
            window, "reasoning_mode", {"application", "transfer"}
        )
        low_reasoning = cls._count_matching(
            window, "reasoning_mode", {"guessing", "recall", "paraphrase"}
        )
        heavy_support = cls._count_matching(
            window, "support_needed", {"heavy", "moderate"}
        )
        high_confusion = cls._count_matching(window, "confusion_level", "high")
        medium_or_high_confusion = cls._count_matching(
            window, "confusion_level", {"high", "medium"}
        )
        ready = cls._count_matching(window, "concept_closure", "ready")
        guessing_or_hedging = cls._count_matching(
            window, "response_pattern", {"guessing", "hedging"}
        )

        if (
            high_confusion >= 2
            or heavy_support >= max(2, n - 1)
            or fragile >= 2
            or guessing_or_hedging >= 2
            or (low_reasoning >= max(2, n - 1) and ready == 0)
        ):
            if high_confusion >= 2:
                reason = "Recent turns show repeated confusion; slow down and re-scaffold."
            elif heavy_support >= max(2, n - 1):
                reason = "Recent turns needed repeated support; keep the pace slower."
            elif fragile >= 2 or guessing_or_hedging >= 2:
                reason = "Understanding looks fragile across recent turns; consolidate before advancing."
            else:
                reason = "Recent answers stayed at recall/paraphrase; narrow the next step before moving on."
            return {"target_pace": "slow", "pace_reason": reason}

        if (
            solid >= max(3, n - 1)
            and app_transfer >= max(2, n - 1)
            and heavy_support == 0
            and medium_or_high_confusion <= 1
            and ready >= max(2, n - 1)
        ):
            return {
                "target_pace": "fast",
                "pace_reason": (
                    "Recent turns show stable application with little support; pace can increase."
                ),
            }

        return {
            "target_pace": "steady",
            "pace_reason": "Recent turns are mixed; keep a steady pace and keep checking understanding.",
        }

    @classmethod
    def _roll_pacing_state(
        cls,
        pacing_state: Optional[Dict[str, Any]],
        signal: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        state = cls._normalize_pacing_state(pacing_state)
        compact_signal = cls._compact_pacing_signal(signal)
        recent = list(state.get("recent_signals", []) or [])
        if compact_signal:
            recent.append(compact_signal)
        recent = recent[-_PACING_SIGNAL_WINDOW:]

        current_pace = state.get("current_pace", "steady")
        cooldown = max(0, int(state.get("cooldown_remaining", 0) or 0))
        turns = max(0, int(state.get("turns_at_current_pace", 0) or 0))
        current_reason = state.get("pace_reason", "") or ""

        override_pace = compact_signal.get("override_pace", "none")
        if override_pace in {"slow", "steady", "fast"}:
            target_pace = override_pace
            target_reason = (
                compact_signal.get("override_reason")
                or "Immediate pacing override from the latest turn."
            )
            forced = True
        else:
            decision = cls._determine_target_pace(current_pace, recent)
            target_pace = decision["target_pace"]
            target_reason = decision["pace_reason"]
            forced = False

        next_cooldown = max(0, cooldown - 1)
        next_pace = current_pace
        next_reason = current_reason or target_reason
        next_turns = turns + 1

        if target_pace != current_pace:
            allow_change = False
            if forced or cooldown == 0:
                allow_change = True
            elif target_pace == "slow" and cls._is_strong_confusion_signal(compact_signal):
                allow_change = True

            if allow_change:
                next_pace = target_pace
                next_reason = target_reason
                next_turns = 1
                next_cooldown = _PACE_CHANGE_COOLDOWN

        elif target_reason:
            next_reason = target_reason

        return {
            "current_pace": next_pace,
            "pace_reason": next_reason,
            "turns_at_current_pace": next_turns,
            "cooldown_remaining": next_cooldown,
            "recent_signals": recent,
        }

    def get_pacing_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        entry = self._cache.get(session_id)
        if not entry:
            return None
        pacing_state = entry.get("pacing_state")
        if not pacing_state:
            pacing_state = self._default_pacing_state()
            entry["pacing_state"] = pacing_state
        return copy.deepcopy(self._normalize_pacing_state(pacing_state))

    def preview_pacing_state(
        self,
        session_id: str,
        signal: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        entry = self._cache.get(session_id)
        if not entry:
            return None
        return self._roll_pacing_state(entry.get("pacing_state"), signal)

    def apply_pacing_signal(
        self,
        session_id: str,
        signal: Optional[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        entry = self._cache.get(session_id)
        if not entry:
            return None
        rolled = self._roll_pacing_state(entry.get("pacing_state"), signal)
        entry["pacing_state"] = rolled
        return copy.deepcopy(rolled)

    # ------------------------------------------------------------------
    # Misconception runtime state
    # ------------------------------------------------------------------

    @staticmethod
    def _default_misconception_state() -> Dict[str, Any]:
        return {
            "active_misconceptions": [],
            "recently_resolved": [],
        }

    @classmethod
    def _normalize_misconception_state(
        cls, misconception_state: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        normalized = cls._default_misconception_state()
        if not misconception_state or not isinstance(misconception_state, dict):
            return normalized

        def _normalize_item(item: Any) -> Optional[Dict[str, Any]]:
            if not isinstance(item, dict):
                return None
            text = str(item.get("text", "") or "").strip()
            key = str(item.get("key", "") or "").strip()
            normalized_key = _normalize_runtime_key(key or text)
            if not normalized_key:
                return None
            priority = str(item.get("repair_priority", "") or "").strip().lower()
            if priority not in {"normal", "must_address_now"}:
                priority = "normal"
            try:
                times_seen = max(0, int(item.get("times_seen", 0) or 0))
            except (TypeError, ValueError):
                times_seen = 0
            return {
                "key": normalized_key,
                "text": text or normalized_key.replace("_", " "),
                "repair_priority": priority,
                "times_seen": times_seen,
            }

        normalized["active_misconceptions"] = [
            item
            for item in (
                _normalize_item(raw)
                for raw in (misconception_state.get("active_misconceptions", []) or [])
            )
            if item
        ]
        normalized["recently_resolved"] = [
            item
            for item in (
                _normalize_item(raw)
                for raw in (misconception_state.get("recently_resolved", []) or [])
            )
            if item
        ][-6:]
        return normalized

    @staticmethod
    def _compact_misconception_event(
        event: Optional[Dict[str, Any]],
    ) -> Dict[str, str]:
        if not event or not isinstance(event, dict):
            return {}
        action = str(event.get("action", "") or "").strip().lower()
        if action not in {"log", "still_active", "resolve_candidate"}:
            return {}
        text = str(event.get("text", "") or "").strip()
        key = str(event.get("key", "") or "").strip()
        normalized_key = _normalize_runtime_key(key or text)
        if not normalized_key:
            return {}
        priority = str(event.get("repair_priority", "") or "").strip().lower()
        if priority not in {"normal", "must_address_now"}:
            priority = "normal"
        return {
            "key": normalized_key,
            "text": text,
            "action": action,
            "repair_priority": priority,
        }

    @classmethod
    def _roll_misconception_state(
        cls,
        misconception_state: Optional[Dict[str, Any]],
        events: Optional[List[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        state = cls._normalize_misconception_state(misconception_state)
        active_order = [
            item.get("key")
            for item in state.get("active_misconceptions", [])
            if item.get("key")
        ]
        active_map = {
            item["key"]: dict(item)
            for item in state.get("active_misconceptions", [])
            if item.get("key")
        }
        resolved_map = {
            item["key"]: dict(item)
            for item in state.get("recently_resolved", [])
            if item.get("key")
        }

        for raw_event in (events or []):
            event = cls._compact_misconception_event(raw_event)
            if not event:
                continue
            key = event["key"]
            text = event.get("text", "") or key.replace("_", " ")
            action = event["action"]
            priority = event.get("repair_priority", "normal")

            if action in {"log", "still_active"}:
                item = active_map.get(key, {
                    "key": key,
                    "text": text,
                    "repair_priority": priority,
                    "times_seen": 0,
                })
                item["text"] = text or item.get("text", key.replace("_", " "))
                if priority == "must_address_now":
                    item["repair_priority"] = "must_address_now"
                item["times_seen"] = int(item.get("times_seen", 0) or 0) + 1
                active_map[key] = item
                if key not in active_order:
                    active_order.append(key)
                resolved_map.pop(key, None)
            elif action == "resolve_candidate":
                item = active_map.pop(key, None)
                if key in active_order:
                    active_order = [existing for existing in active_order if existing != key]
                resolved_map[key] = {
                    "key": key,
                    "text": text or (item or {}).get("text", key.replace("_", " ")),
                    "repair_priority": priority,
                    "times_seen": int((item or {}).get("times_seen", 0) or 0),
                }

        return {
            "active_misconceptions": [
                active_map[key]
                for key in active_order
                if key in active_map
            ],
            "recently_resolved": list(resolved_map.values())[-6:],
        }

    def get_misconception_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        entry = self._cache.get(session_id)
        if not entry:
            return None
        misconception_state = entry.get("misconception_state")
        if not misconception_state:
            misconception_state = self._default_misconception_state()
            entry["misconception_state"] = misconception_state
        return copy.deepcopy(self._normalize_misconception_state(misconception_state))

    def preview_misconception_state(
        self,
        session_id: str,
        events: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[Dict[str, Any]]:
        entry = self._cache.get(session_id)
        if not entry:
            return None
        return self._roll_misconception_state(
            entry.get("misconception_state"),
            events,
        )

    def apply_misconception_events(
        self,
        session_id: str,
        events: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[Dict[str, Any]]:
        entry = self._cache.get(session_id)
        if not entry:
            return None
        rolled = self._roll_misconception_state(
            entry.get("misconception_state"),
            events,
        )
        entry["misconception_state"] = rolled
        return copy.deepcopy(rolled)

    def seed_misconception_state(
        self,
        session_id: str,
        misconceptions: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[Dict[str, Any]]:
        entry = self._cache.get(session_id)
        if not entry:
            return None
        current = self._normalize_misconception_state(
            entry.get("misconception_state")
        )
        if current.get("active_misconceptions"):
            return copy.deepcopy(current)
        seed_events = []
        for misconception in (misconceptions or []):
            if not isinstance(misconception, dict):
                continue
            text = str(misconception.get("misconception_text", "") or "").strip()
            if not text:
                continue
            seed_events.append(
                {
                    "text": text,
                    "action": "log",
                    "repair_priority": "normal",
                }
            )
        rolled = self._roll_misconception_state(current, seed_events)
        entry["misconception_state"] = rolled
        return copy.deepcopy(rolled)

    # ------------------------------------------------------------------
    # Teaching plan (concept decomposition)
    # ------------------------------------------------------------------

    def store_teaching_plan(
        self,
        session_id: str,
        plan,
        extracted_concepts: Optional[List[Dict[str, str]]] = None,
    ) -> None:
        """Store a teaching plan for the active objective.

        Args:
            session_id: Session identifier.
            plan: Either a dict (legacy JSON) or str (17-section text).
            extracted_concepts: Pre-extracted concept list from a
                lightweight LLM call.  When provided, ``_build_lesson_state``
                uses it directly instead of regex-parsing the text plan.
        """
        entry = self._cache.get(session_id)
        if entry:
            entry["teaching_plan"] = plan
            entry["lesson_state"] = _build_lesson_state(plan, extracted_concepts)
            n = len(entry["lesson_state"].get("concepts", []))
            if isinstance(plan, dict):
                detail = f"{len(plan.get('concepts', []))} concepts"
            else:
                detail = f"{len(str(plan))} chars"
            logger.info(
                "Teaching plan stored for session=%s (%s, %d lesson concepts)",
                session_id, detail, n,
            )

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

        # Build a fuzzy lookup so the turn analyzer's concept IDs
        # (which may use hyphens, underscores, or raw labels) match
        # the canonical concepts from the LLM extraction.
        fuzzy_lookup: Dict[str, Dict[str, str]] = {}
        for concept in concepts:
            key = _concept_match_key(concept.get("id", ""))
            if key:
                fuzzy_lookup[key] = concept
            label_key = _concept_match_key(concept.get("label", ""))
            if label_key and label_key not in fuzzy_lookup:
                fuzzy_lookup[label_key] = concept

        for update in patch.get("concept_updates", []) or []:
            concept_id = str(update.get("concept_id", "")).strip()
            if not concept_id:
                continue
            status = str(update.get("status", "")).strip() or "in_progress"
            label = str(update.get("label", concept_id)).strip() or concept_id

            # Try exact match first, then fuzzy match by ID, then by label
            existing = next(
                (c for c in concepts if c.get("id") == concept_id),
                None,
            )
            if not existing:
                match_key = _concept_match_key(concept_id)
                existing = fuzzy_lookup.get(match_key)
            if not existing:
                label_key = _concept_match_key(label)
                existing = fuzzy_lookup.get(label_key)

            if existing:
                existing["status"] = status
            else:
                concepts.append({"id": concept_id, "label": label, "status": status})
                order = lesson_state.setdefault("teaching_order", [])
                if concept_id not in order:
                    order.append(concept_id)
                # Register in fuzzy lookup for subsequent updates in same patch
                key = _concept_match_key(concept_id)
                if key:
                    fuzzy_lookup[key] = concepts[-1]

        for field in ("active_concept", "bridge_back_target"):
            value = str(patch.get(field, "") or "").strip()
            if not value:
                continue
            # Resolve to a canonical concept ID via fuzzy match
            resolved = fuzzy_lookup.get(_concept_match_key(value))
            lesson_state[field] = resolved["id"] if resolved else value

        pending = str(patch.get("pending_check", "") or "").strip()
        if pending:
            lesson_state["pending_check"] = pending

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
