from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from .artifacts import GuidedSessionStateArtifact


class GuidedSessionStateRepository:
    def __init__(
        self,
        *,
        session_cache,
        restore_cache: Callable[[str, str], Any],
        persist_cache: Callable[[str], Any],
        load_student_bundle: Callable[[str, str], Any],
        format_student_context: Callable[..., str],
    ) -> None:
        self.session_cache = session_cache
        self.restore_cache = restore_cache
        self.persist_cache = persist_cache
        self.load_student_bundle = load_student_bundle
        self.format_student_context = format_student_context

    async def restore(self, session_id: str, objective_id: str = "") -> None:
        await self.restore_cache(session_id, objective_id)

    def needs_retrieval(self, session_id: str, objective_id: str) -> bool:
        return self.session_cache.needs_retrieval(session_id, objective_id)

    def store_pipeline_result(
        self,
        *,
        session_id: str,
        objective_id: str,
        objective_text: str,
        teaching_content: str,
        retrieval_bundle: Dict[str, Any],
        teaching_plan: Any,
        extracted_concepts=None,
    ) -> None:
        self.session_cache.store(
            session_id,
            objective_id,
            objective_text,
            [],
            "",
            teaching_content,
            retrieval_bundle=retrieval_bundle,
        )
        self.session_cache.store_teaching_plan(
            session_id,
            teaching_plan,
            extracted_concepts=extracted_concepts,
        )

    async def persist(self, session_id: str) -> None:
        await self.persist_cache(session_id)

    def get_teaching_content(self, session_id: str) -> str:
        return self.session_cache.get_teaching_content(session_id)

    def get_teaching_plan(self, session_id: str) -> Any:
        return self.session_cache.get_teaching_plan(session_id)

    def get_lesson_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self.session_cache.get_lesson_state(session_id)

    def get_pacing_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self.session_cache.get_pacing_state(session_id)

    def get_misconception_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self.session_cache.get_misconception_state(session_id)

    def get_cached_entry(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self.session_cache.get(session_id)

    async def load_guided_state(
        self,
        *,
        student_id: str,
        session_id: str,
        objective_id: str,
        objective_text: str,
    ) -> GuidedSessionStateArtifact:
        teaching_plan = self.session_cache.get_teaching_plan(session_id)
        teaching_content = self.session_cache.get_teaching_content(session_id)
        lesson_state = self.session_cache.get_lesson_state(session_id)
        pacing_state = self.session_cache.get_pacing_state(session_id)
        bundle = await self.load_student_bundle(student_id, objective_id)
        misconception_state = self.session_cache.seed_misconception_state(
            session_id,
            bundle.get("misconceptions", []),
        )
        student_context = self.format_student_context(
            bundle.get("profile"),
            bundle.get("mastery", []),
            bundle.get("session"),
            bundle.get("misconceptions", []),
            bundle.get("learner_memory"),
            bundle.get("objective_memory"),
        )
        return GuidedSessionStateArtifact(
            session_id=session_id,
            objective_id=objective_id,
            objective_text=objective_text,
            teaching_plan=teaching_plan,
            teaching_content=teaching_content,
            retrieval_bundle=self.session_cache.get_retrieval_bundle(session_id) or {},
            lesson_state=lesson_state,
            pacing_state=pacing_state,
            misconception_state=misconception_state,
            student_context=student_context,
            bundle=bundle,
        )

