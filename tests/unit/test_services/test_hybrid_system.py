import json

import pytest

from question_app.services.tutor.hybrid_system import (
    HybridCrewAISocraticSystem,
    TEACHING_PLAN_MAX_COMPLETION_TOKENS,
    TEACHING_PLAN_REASONING_EFFORT,
    TeachingPlanGenerationError,
)
from question_app.services.tutor.interfaces import VectorStoreInterface


class FakeVectorStore(VectorStoreInterface):
    async def search(self, query: str, n_results: int = 3):
        return []


class FakeAzureClient:
    def __init__(
        self,
        endpoint: str,
        deployment: str,
        api_key: str,
        api_version: str = "",
        content_filter_policy: str = "",
    ):
        self.endpoint = endpoint
        self.deployment = deployment
        self.api_key = api_key
        self.api_version = api_version
        self.content_filter_policy = content_filter_policy

    def chat(self, messages, temperature=0.7, max_tokens=1000, reasoning_effort=None, response_format=None):
        return ""

    async def chat_with_tools(
        self,
        messages,
        tools,
        temperature=0.3,
        max_tokens=300,
        tool_choice="auto",
        parallel_tool_calls=True,
        reasoning_effort=None,
    ):
        return {"role": "assistant", "content": "", "tool_calls": []}

    async def chat_stream_async(self, messages, temperature=0.7, max_tokens=1000):
        if False:
            yield ""


class FakeStudentService:
    def __init__(self, session_state, runtime_cache_store=None):
        self.session_state = session_state
        self.runtime_cache_store = runtime_cache_store or {}
        self.logged_misconceptions = []
        self.resolved_misconceptions = []
        self.objective_memory_upserts = []
        self.learner_memory_upserts = []

    async def get_active_session(self, student_id: str):
        return dict(self.session_state)

    async def get_session_runtime_cache(self, session_id: str):
        payload = self.runtime_cache_store.get(session_id)
        return dict(payload) if isinstance(payload, dict) else payload

    async def save_session_runtime_cache(self, session_id: str, runtime_cache):
        self.runtime_cache_store[session_id] = dict(runtime_cache)
        return dict(runtime_cache)

    async def clear_session_runtime_cache(self, session_id: str):
        self.runtime_cache_store[session_id] = {}
        return {}

    async def log_misconception(self, student_id: str, objective_id: str, misconception_text: str):
        self.logged_misconceptions.append((student_id, objective_id, misconception_text))
        return {"misconception_text": misconception_text}

    async def resolve_misconception(self, student_id: str, objective_id: str, misconception_text: str):
        self.resolved_misconceptions.append((student_id, objective_id, misconception_text))
        return {"misconception_text": misconception_text, "resolved": True}

    async def upsert_objective_memory(
        self,
        student_id: str,
        objective_id: str,
        summary: str = "",
        demonstrated_skills=None,
        active_gaps=None,
        next_focus: str = "",
    ):
        payload = {
            "student_id": student_id,
            "objective_id": objective_id,
            "summary": summary,
            "demonstrated_skills": demonstrated_skills or [],
            "active_gaps": active_gaps or [],
            "next_focus": next_focus,
        }
        self.objective_memory_upserts.append(payload)
        return payload

    async def upsert_learner_memory(
        self,
        student_id: str,
        summary: str = "",
        strengths=None,
        support_needs=None,
        tendencies=None,
        successful_strategies=None,
    ):
        payload = {
            "student_id": student_id,
            "summary": summary,
            "strengths": strengths or [],
            "support_needs": support_needs or [],
            "tendencies": tendencies or [],
            "successful_strategies": successful_strategies or [],
        }
        self.learner_memory_upserts.append(payload)
        return payload


class FakeWCAGClient:
    def __init__(self):
        self.calls = []

    async def execute_planned_tool_calls(self, planned_calls):
        self.calls.append(planned_calls)
        results = []
        for call in planned_calls:
            if call["tool"] == "list_principles":
                text = "WCAG has four principles: Perceivable, Operable, Understandable, Robust."
                status = "HIT"
            elif call["tool"] == "list_guidelines":
                text = "Guidelines sit under principles and organize success criteria."
                status = "HIT"
            else:
                text = ""
                status = "MISS"
            results.append(
                {
                    "tool": call["tool"],
                    "args": call["args"],
                    "category": call.get("category", "agentic"),
                    "result": text,
                    "chars": len(text),
                    "status": status,
                }
            )
        return results


class FakeGeneralChatService:
    def __init__(self, azure_config, vector_store_service, wcag_mcp_client=None, db_manager=None):
        self.azure_config = azure_config
        self.vector_store_service = vector_store_service
        self.wcag_mcp_client = wcag_mcp_client
        self.db_manager = db_manager
        self.ensure_calls = []
        self.start_calls = []
        self.handle_calls = []
        self.streaming_calls = []
        self._session_numbers = {}

    async def ensure_session(self, requested_session_id=None):
        self.ensure_calls.append(requested_session_id)
        session_id = requested_session_id or "chat-test"
        return {
            "session_id": session_id,
            "session_number": self._session_numbers.get(session_id, 0),
        }

    async def start_new_session(self, session_id):
        self.start_calls.append(session_id)
        self._session_numbers[session_id] = self._session_numbers.get(session_id, 0) + 1
        return {
            "session_id": session_id,
            "session_number": self._session_numbers[session_id],
        }

    async def handle_message(self, session_id, user_message):
        self.handle_calls.append(
            {"session_id": session_id, "user_message": user_message}
        )
        return {
            "response": "Delegated Instance A response.",
            "session_id": session_id,
            "session_metadata": {
                "session_number": self._session_numbers.get(session_id, 1),
                "intent_executed": "conceptual_question",
                "analysis": {},
                "progress": {},
            },
        }

    async def handle_message_streaming(self, session_id, user_message, ws_send):
        self.streaming_calls.append(
            {"session_id": session_id, "user_message": user_message}
        )
        await ws_send({"type": "stream_start"})
        await ws_send({"type": "token", "content": "Delegated stream"})
        metadata = {
            "session_number": self._session_numbers.get(session_id, 1),
            "intent_executed": "conceptual_question",
            "analysis": {},
            "progress": {},
        }
        await ws_send({"type": "stream_end", "metadata": metadata})
        return metadata


def _azure_config():
    return {
        "api_key": "test-key",
        "endpoint": "https://example.test",
        "deployment_name": "fallback-model",
        "tutor_deployment_name": "gpt-5.4-mini",
        "reasoning_deployment_name": "gpt-5.4",
        "api_version": "2025-01-01-preview",
    }


@pytest.fixture
def hybrid_system(monkeypatch):
    monkeypatch.setattr(
        "question_app.services.tutor.hybrid_system.AzureAPIMClient",
        FakeAzureClient,
    )
    monkeypatch.setattr(
        "question_app.services.tutor.hybrid_system.GeneralChatService",
        FakeGeneralChatService,
    )
    monkeypatch.setattr(
        HybridCrewAISocraticSystem,
        "_load_conversation_memory",
        lambda self: None,
    )
    monkeypatch.setattr(
        HybridCrewAISocraticSystem,
        "_save_conversation_memory",
        lambda self: None,
    )
    return HybridCrewAISocraticSystem(
        azure_config=_azure_config(),
        vector_store_service=FakeVectorStore(),
        db_manager=object(),
        student_mcp_client=FakeStudentService(
            {"current_stage": "introduction", "active_objective_id": "obj-1"}
        ),
    )


class TestHybridSystemModelRoles:
    def test_init_uses_split_model_roles(self, hybrid_system):
        assert hybrid_system.tutor_client.deployment == "gpt-5.4-mini"
        assert hybrid_system.reasoning_client.deployment == "gpt-5.4"
        assert hybrid_system.client is hybrid_system.tutor_client
        assert hybrid_system.coordinator_agent.client is hybrid_system.tutor_client
        assert hybrid_system.code_analyzer.client is hybrid_system.reasoning_client


class TestLegacyInstanceADelegation:
    @pytest.mark.asyncio
    async def test_conduct_socratic_session_delegates_to_general_chat_service(
        self, hybrid_system
    ):
        result = await hybrid_system.conduct_socratic_session(
            "student-1",
            "What is alt text?",
        )

        assert hybrid_system.instance_a_service.ensure_calls == ["student-1"]
        assert hybrid_system.instance_a_service.start_calls == ["student-1"]
        assert hybrid_system.instance_a_service.handle_calls == [
            {"session_id": "student-1", "user_message": "What is alt text?"}
        ]
        assert result["tutor_response"] == "Delegated Instance A response."
        assert result["session_metadata"]["intent_executed"] == "conceptual_question"

    @pytest.mark.asyncio
    async def test_conduct_socratic_session_bootstraps_legacy_session_once(
        self, hybrid_system
    ):
        await hybrid_system.conduct_socratic_session("student-1", "First turn")
        await hybrid_system.conduct_socratic_session("student-1", "Second turn")

        assert hybrid_system.instance_a_service.ensure_calls == [
            "student-1",
            "student-1",
        ]
        assert hybrid_system.instance_a_service.start_calls == ["student-1"]

    @pytest.mark.asyncio
    async def test_conduct_socratic_session_streaming_delegates_to_general_chat_service(
        self, hybrid_system
    ):
        events = []

        async def ws_send(payload):
            events.append(payload)

        metadata = await hybrid_system.conduct_socratic_session_streaming(
            "student-1",
            "What is alt text?",
            ws_send,
        )

        assert hybrid_system.instance_a_service.start_calls == ["student-1"]
        assert hybrid_system.instance_a_service.streaming_calls == [
            {"session_id": "student-1", "user_message": "What is alt text?"}
        ]
        assert [event["type"] for event in events] == [
            "stream_start",
            "token",
            "stream_end",
        ]
        assert metadata["intent_executed"] == "conceptual_question"


class TestGuidedTutorMessages:
    def test_guided_tutor_messages_include_turn_analysis_and_lesson_state(
        self, hybrid_system
    ):
        messages = hybrid_system._build_guided_tutor_messages(
            student_response="Is WCAG the same as Section 508?",
            history=[],
            teaching_content="Evidence pack",
            student_context="",
            current_stage="introduction",
            active_objective="Explain WCAG structure",
            teaching_plan="8. dependency_order\n1. Principles vs guidelines\n",
            lesson_state={
                "active_concept": "principles-vs-guidelines",
                "pending_check": "Explain what a guideline does",
                "bridge_back_target": "principles-vs-guidelines",
                "teaching_order": ["principles-vs-guidelines"],
                "concepts": [
                    {
                        "id": "principles-vs-guidelines",
                        "label": "Principles vs guidelines",
                        "status": "in_progress",
                    }
                ],
            },
            turn_analysis={
                "turn_route": "adjacent_topic",
                "answer_current_question_first": True,
                "student_question_to_answer": "Is WCAG the same as Section 508?",
                "teaching_move": "clarify",
                "target_stage": "introduction",
                "stage_action": "stay",
                "lesson_state_patch": {
                    "bridge_back_target": "principles-vs-guidelines"
                },
            },
            pacing_state={
                "current_pace": "slow",
                "pace_reason": "Recent turns show repeated confusion; slow down and re-scaffold.",
                "turns_at_current_pace": 2,
                "cooldown_remaining": 1,
                "recent_signals": [],
            },
        )

        assert "TURN ROUTING" in messages[0]["content"]
        assert "LESSON STATE:" in messages[0]["content"]
        turn_analysis_block = next(
            message["content"]
            for message in messages
            if message["role"] == "system" and message["content"].startswith("TURN ANALYSIS:")
        )
        pacing_block = next(
            message["content"]
            for message in messages
            if message["role"] == "system" and message["content"].startswith("ADAPTIVE PACING:")
        )
        constraints_block = next(
            message["content"]
            for message in messages
            if message["role"] == "system" and message["content"].startswith("RESPONSE CONSTRAINTS:")
        )
        assert "Route: adjacent_topic" in turn_analysis_block
        assert "Answer current question first: yes" in turn_analysis_block
        assert "Current pace: slow" in pacing_block
        assert "stay on the current concept" in pacing_block
        assert "Max new concepts: 0" in constraints_block
        assert "Max questions: 1" in constraints_block

    def test_guided_tutor_messages_include_active_misconception_repair_block(
        self, hybrid_system
    ):
        messages = hybrid_system._build_guided_tutor_messages(
            student_response="I think role alone is enough.",
            history=[],
            teaching_content="Evidence pack",
            student_context="",
            current_stage="exploration",
            active_objective="Apply the five rules for using ARIA correctly",
            teaching_plan="8. dependency_order\n1. Native first\n",
            lesson_state=None,
            turn_analysis={
                "misconception_events": [
                    {
                        "key": "role_alone_enough",
                        "text": "Believes a role alone is enough.",
                        "action": "still_active",
                        "repair_priority": "must_address_now",
                    }
                ]
            },
            pacing_state=None,
            misconception_state={
                "active_misconceptions": [
                    {
                        "key": "role_alone_enough",
                        "text": "Believes a role alone is enough.",
                        "repair_priority": "must_address_now",
                        "times_seen": 1,
                    }
                ],
                "recently_resolved": [],
            },
        )

        misconception_block = next(
            message["content"]
            for message in messages
            if message["role"] == "system"
            and message["content"].startswith("ACTIVE MISCONCEPTION REPAIR:")
        )
        assert "Believes a role alone is enough." in misconception_block
        assert "Repair the misconception explicitly" in misconception_block

    def test_guided_tutor_messages_force_full_sequence_repair_shape(
        self, hybrid_system
    ):
        messages = hybrid_system._build_guided_tutor_messages(
            student_response="I would just check aria-checked.",
            history=[],
            teaching_content="Evidence pack",
            student_context="",
            current_stage="exploration",
            active_objective="Apply the five rules for using ARIA correctly",
            teaching_plan="8. dependency_order\n1. Native first\n",
            lesson_state=None,
            turn_analysis={
                "misconception_events": [
                    {
                        "key": "full_rule_sequence_gap",
                        "text": "Stops after one local check instead of walking the full rule sequence.",
                        "action": "still_active",
                        "repair_priority": "must_address_now",
                        "repair_scope": "full_sequence",
                        "repair_pattern": "same_snippet_walkthrough",
                    }
                ],
                "pacing_signal": {
                    "recommended_next_step": "ask_same_level",
                },
                "stage_action": "stay",
            },
            pacing_state={"current_pace": "slow"},
            misconception_state={
                "active_misconceptions": [
                    {
                        "key": "full_rule_sequence_gap",
                        "text": "Stops after one local check instead of walking the full rule sequence.",
                        "repair_priority": "must_address_now",
                        "repair_scope": "full_sequence",
                        "repair_pattern": "same_snippet_walkthrough",
                        "times_seen": 1,
                    }
                ],
                "recently_resolved": [],
            },
        )

        constraints_block = next(
            message["content"]
            for message in messages
            if message["role"] == "system"
            and message["content"].startswith("RESPONSE CONSTRAINTS:")
        )
        misconception_block = next(
            message["content"]
            for message in messages
            if message["role"] == "system"
            and message["content"].startswith("ACTIVE MISCONCEPTION REPAIR:")
        )
        assert "Response shape: full_sequence_repair" in constraints_block
        assert "same snippet ordered walkthrough" in constraints_block
        assert "native-first" in constraints_block
        assert "Do not ask for a localized explanation" in misconception_block
        assert "Required order: native-first -> semantic override -> behavior -> focus -> required state/property." in misconception_block


class TestSessionRuntimeCachePersistence:
    @pytest.mark.asyncio
    async def test_restore_session_cache_from_persistence(self, hybrid_system):
        hybrid_system.student_mcp.runtime_cache_store["sess-restore"] = {
            "objective_id": "obj-1",
            "objective_text": "Explain WCAG structure",
            "rag_chunks": [],
            "wcag_context": "",
            "teaching_content": "Persisted evidence pack",
            "retrieval_bundle": {"version": 1},
            "teaching_plan": "8. dependency_order\n1. Principles vs guidelines\n",
            "lesson_state": {
                "active_concept": "principles-vs-guidelines",
                "pending_check": "Principles vs guidelines",
                "bridge_back_target": "principles-vs-guidelines",
                "teaching_order": ["principles-vs-guidelines"],
                "concepts": [
                    {
                        "id": "principles-vs-guidelines",
                        "label": "Principles vs guidelines",
                        "status": "in_progress",
                    }
                ],
            },
            "retrieved_at": "2026-04-08T12:00:00",
        }

        await hybrid_system._restore_session_cache("sess-restore", "obj-1")

        assert hybrid_system._session_cache.get_teaching_content("sess-restore") == (
            "Persisted evidence pack"
        )
        assert hybrid_system._session_cache.get_teaching_plan("sess-restore") == (
            "8. dependency_order\n1. Principles vs guidelines\n"
        )
        assert hybrid_system._session_cache.get_lesson_state("sess-restore")[
            "active_concept"
        ] == "principles-vs-guidelines"

    @pytest.mark.asyncio
    async def test_persist_session_cache_writes_runtime_cache(self, hybrid_system):
        hybrid_system._session_cache.store(
            "sess-1", "obj-1", "Explain WCAG structure", [], "", "Evidence pack"
        )
        hybrid_system._session_cache.store_teaching_plan(
            "sess-1",
            {
                "objective": "Explain WCAG structure",
                "concepts": [
                    {
                        "id": "c1",
                        "name": "Principles vs guidelines",
                        "status": "not_covered",
                    }
                ],
                "recommended_order": ["c1"],
            },
        )

        await hybrid_system._persist_session_cache("sess-1")

        persisted = hybrid_system.student_mcp.runtime_cache_store["sess-1"]
        assert persisted["objective_id"] == "obj-1"
        assert persisted["teaching_content"] == "Evidence pack"
        assert persisted["teaching_plan"]["objective"] == "Explain WCAG structure"
        assert persisted["lesson_state"]["active_concept"] == "c1"


class TestMemoryPatchMerging:
    def test_preview_objective_memory_state_replaces_current_gap_snapshot(
        self, hybrid_system
    ):
        preview = hybrid_system._preview_objective_memory_state(
            existing_objective={
                "summary": "Old summary",
                "demonstrated_skills": ["uses native-first"],
                "active_gaps": ["stale earlier gap"],
                "next_focus": "Old focus",
            },
            objective_memory_patch={
                "summary": "Fresh summary",
                "demonstrated_skills_add": ["walks the full checklist"],
                "active_gaps_current": ["needs one same-snippet walkthrough"],
                "next_focus": "Behavior, focus, and required states",
            },
        )

        assert preview == {
            "summary": "Fresh summary",
            "demonstrated_skills": [
                "uses native-first",
                "walks the full checklist",
            ],
            "active_gaps": ["needs one same-snippet walkthrough"],
            "next_focus": "Behavior, focus, and required states",
        }

    @pytest.mark.asyncio
    async def test_memory_patches_replace_current_gap_and_support_snapshots(
        self, hybrid_system
    ):
        bundle = {
            "objective_memory": {
                "summary": "Old summary",
                "demonstrated_skills": ["uses native-first"],
                "active_gaps": ["old stale gap"],
                "next_focus": "Old focus",
            },
            "learner_memory": {
                "summary": "Old learner summary",
                "strengths": ["asks clarifying questions"],
                "support_needs": ["old support need"],
                "tendencies": ["old tendency"],
                "successful_strategies": ["contrastive examples"],
            },
        }

        await hybrid_system._apply_memory_patches(
            student_id="student-1",
            objective_id="obj-1",
            objective_memory_patch={
                "summary": "New summary",
                "demonstrated_skills_add": ["maps rules to examples"],
                "active_gaps_current": ["needs one more transfer check"],
                "next_focus": "Fresh focus",
            },
            learner_memory_patch={
                "summary": "New learner summary",
                "strengths_add": ["updates after correction"],
                "support_needs_current": ["brief transfer checks"],
                "tendencies_current": ["self-corrects after contrast"],
                "successful_strategies_add": ["short misconception checks"],
            },
            bundle=bundle,
        )

        objective_upsert = hybrid_system.student_mcp.objective_memory_upserts[-1]
        learner_upsert = hybrid_system.student_mcp.learner_memory_upserts[-1]

        assert objective_upsert["demonstrated_skills"] == [
            "uses native-first",
            "maps rules to examples",
        ]
        assert objective_upsert["active_gaps"] == ["needs one more transfer check"]
        assert learner_upsert["support_needs"] == ["brief transfer checks"]
        assert learner_upsert["tendencies"] == ["self-corrects after contrast"]
        assert learner_upsert["strengths"] == [
            "asks clarifying questions",
            "updates after correction",
        ]


class TestResponseGuards:
    def test_enforce_turn_response_controls_blocks_advance_on_open_misconception(
        self, hybrid_system
    ):
        guarded = hybrid_system._enforce_turn_response_controls(
            current_stage="exploration",
            analysis={
                "stage_action": "advance",
                "target_stage": "readiness_check",
                "stage_reason": "Learner looks ready.",
                "teaching_move": "continue",
                "misconception_events": [
                    {
                        "key": "role_alone_enough",
                        "text": "Believes role alone is enough.",
                        "action": "still_active",
                        "repair_priority": "must_address_now",
                    }
                ],
                "pacing_signal": {
                    "concept_closure": "ready",
                    "override_pace": "steady",
                    "override_reason": "",
                    "recommended_next_step": "advance",
                },
            },
            lesson_state={
                "concepts": [
                    {"id": "c1", "status": "covered"},
                    {"id": "c2", "status": "covered"},
                ]
            },
            pacing_state={"current_pace": "steady"},
            misconception_state={
                "active_misconceptions": [
                    {
                        "key": "role_alone_enough",
                        "text": "Believes role alone is enough.",
                        "repair_priority": "must_address_now",
                    }
                ]
            },
        )

        assert guarded["stage_action"] == "stay"
        assert guarded["target_stage"] == "exploration"
        assert guarded["pacing_signal"]["override_pace"] == "slow"
        assert guarded["pacing_signal"]["recommended_next_step"] == "ask_narrower"

    def test_enforce_turn_response_controls_does_not_block_on_stale_runtime_misconception(
        self, hybrid_system
    ):
        guarded = hybrid_system._enforce_turn_response_controls(
            current_stage="exploration",
            analysis={
                "stage_action": "advance",
                "target_stage": "readiness_check",
                "stage_reason": "Learner looks ready.",
                "teaching_move": "continue",
                "misconception_events": [
                    {
                        "key": "role_alone_enough",
                        "text": "Student now rejects role-only fixes on a fresh example.",
                        "action": "resolve_candidate",
                        "repair_priority": "normal",
                    }
                ],
                "pacing_signal": {
                    "concept_closure": "ready",
                    "override_pace": "steady",
                    "override_reason": "",
                    "recommended_next_step": "advance",
                },
            },
            lesson_state={
                "concepts": [
                    {"id": "c1", "status": "covered"},
                    {"id": "c2", "status": "covered"},
                    {"id": "c3", "status": "covered"},
                    {"id": "c4", "status": "covered"},
                ]
            },
            pacing_state={"current_pace": "slow"},
            misconception_state={
                "active_misconceptions": [
                    {
                        "key": "role_alone_enough",
                        "text": "Believes role alone is enough.",
                        "repair_priority": "must_address_now",
                    }
                ]
            },
        )

        assert guarded["stage_action"] == "advance"
        assert guarded["target_stage"] == "readiness_check"
        assert guarded["pacing_signal"]["override_pace"] == "steady"
        assert guarded["pacing_signal"]["recommended_next_step"] == "advance"

    def test_enforce_turn_response_controls_does_not_treat_resolve_candidate_as_open_lock(
        self, hybrid_system
    ):
        guarded = hybrid_system._enforce_turn_response_controls(
            current_stage="introduction",
            analysis={
                "stage_action": "advance",
                "target_stage": "exploration",
                "stage_reason": "Learner explained the tradeoff causally.",
                "teaching_move": "consolidate",
                "misconception_events": [
                    {
                        "key": "semantic_controls_as_more_control_for_developers",
                        "text": "Student now states that semantic controls provide built-in meaning and behavior.",
                        "action": "resolve_candidate",
                        "repair_priority": "must_address_now",
                    }
                ],
                "pacing_signal": {
                    "concept_closure": "almost_ready",
                    "reasoning_mode": "application",
                    "override_pace": "steady",
                    "override_reason": "",
                    "recommended_next_step": "advance",
                },
            },
            lesson_state={
                "concepts": [
                    {"id": "c1", "status": "covered"},
                    {"id": "c2", "status": "covered"},
                ]
            },
            pacing_state={"current_pace": "steady"},
            misconception_state={"active_misconceptions": []},
        )

        assert guarded["stage_action"] == "advance"
        assert guarded["target_stage"] == "exploration"

    def test_enforce_turn_response_controls_relaxes_intro_exit_on_causal_reasoning(
        self, hybrid_system
    ):
        guarded = hybrid_system._enforce_turn_response_controls(
            current_stage="introduction",
            analysis={
                "stage_action": "advance",
                "target_stage": "exploration",
                "stage_reason": "Learner explained the tradeoff in their own words.",
                "teaching_move": "consolidate",
                "misconception_events": [],
                "pacing_signal": {
                    "concept_closure": "almost_ready",
                    "reasoning_mode": "application",
                    "override_pace": "steady",
                    "override_reason": "",
                    "recommended_next_step": "advance",
                },
            },
            lesson_state={
                "concepts": [
                    {"id": "c1", "status": "covered"},
                    {"id": "c2", "status": "covered"},
                ]
            },
            pacing_state={"current_pace": "steady"},
            misconception_state={"active_misconceptions": []},
        )

        assert guarded["stage_action"] == "advance"
        assert guarded["target_stage"] == "exploration"

    def test_enforce_turn_response_controls_normalizes_stage_jumps(
        self, hybrid_system
    ):
        guarded = hybrid_system._enforce_turn_response_controls(
            current_stage="exploration",
            analysis={
                "stage_action": "advance",
                "target_stage": "mini_assessment",
                "stage_reason": "Learner looks ready for assessment.",
                "teaching_move": "consolidate",
                "misconception_events": [],
                "pacing_signal": {
                    "concept_closure": "ready",
                    "reasoning_mode": "transfer",
                    "override_pace": "steady",
                    "override_reason": "",
                    "recommended_next_step": "advance",
                },
            },
            lesson_state={
                "concepts": [
                    {"id": "c1", "status": "covered"},
                    {"id": "c2", "status": "covered"},
                    {"id": "c3", "status": "covered"},
                ]
            },
            pacing_state={"current_pace": "steady"},
            misconception_state={"active_misconceptions": []},
        )

        assert guarded["stage_action"] == "advance"
        assert guarded["target_stage"] == "readiness_check"
        assert "Stage order normalized" in guarded["stage_reason"]

    def test_enforce_turn_response_controls_escalates_repeated_sequence_repair_to_fresh_example(
        self, hybrid_system
    ):
        guarded = hybrid_system._enforce_turn_response_controls(
            current_stage="exploration",
            analysis={
                "stage_action": "stay",
                "target_stage": "exploration",
                "stage_reason": "Almost there.",
                "teaching_move": "repair",
                "misconception_events": [],
                "pacing_signal": {
                    "concept_closure": "almost_ready",
                    "reasoning_mode": "application",
                    "override_pace": "slow",
                    "override_reason": "",
                    "recommended_next_step": "ask_narrower",
                },
            },
            lesson_state={
                "concepts": [
                    {"id": "c1", "status": "covered"},
                    {"id": "c2", "status": "covered"},
                    {"id": "c3", "status": "covered"},
                ]
            },
            pacing_state={"current_pace": "slow"},
            misconception_state={
                "active_misconceptions": [
                    {
                        "key": "full_rule_sequence_gap",
                        "text": "Stops after one local check instead of walking the full rule sequence.",
                        "repair_priority": "must_address_now",
                        "repair_scope": "full_sequence",
                        "repair_pattern": "same_snippet_walkthrough",
                        "times_seen": 3,
                    }
                ]
            },
        )

        assert guarded["stage_action"] == "stay"
        assert guarded["target_stage"] == "exploration"
        assert guarded["pacing_signal"]["recommended_next_step"] == "give_example"
        assert guarded["pacing_signal"]["override_pace"] == "steady"
        assert "fresh transfer check" in guarded["pacing_signal"]["override_reason"]

    def test_enforce_turn_response_controls_advances_after_repeated_sequence_resolution(
        self, hybrid_system
    ):
        guarded = hybrid_system._enforce_turn_response_controls(
            current_stage="exploration",
            analysis={
                "stage_action": "stay",
                "target_stage": "exploration",
                "stage_reason": "Learner corrected the sequence.",
                "teaching_move": "consolidate",
                "misconception_events": [
                    {
                        "key": "full_rule_sequence_gap",
                        "text": "Stops after one local check instead of walking the full rule sequence.",
                        "action": "resolve_candidate",
                        "repair_priority": "normal",
                        "repair_scope": "full_sequence",
                        "repair_pattern": "same_snippet_walkthrough",
                    }
                ],
                "pacing_signal": {
                    "concept_closure": "ready",
                    "reasoning_mode": "transfer",
                    "override_pace": "slow",
                    "override_reason": "",
                    "recommended_next_step": "ask_same_level",
                },
            },
            lesson_state={
                "concepts": [
                    {"id": "c1", "status": "covered"},
                    {"id": "c2", "status": "covered"},
                    {"id": "c3", "status": "covered"},
                    {"id": "c4", "status": "not_covered"},
                ]
            },
            pacing_state={"current_pace": "slow"},
            misconception_state={
                "active_misconceptions": [],
                "recently_resolved": [
                    {
                        "key": "full_rule_sequence_gap",
                        "text": "Stops after one local check instead of walking the full rule sequence.",
                        "repair_priority": "must_address_now",
                        "repair_scope": "full_sequence",
                        "repair_pattern": "same_snippet_walkthrough",
                        "times_seen": 3,
                    }
                ],
            },
        )

        assert guarded["stage_action"] == "advance"
        assert guarded["target_stage"] == "readiness_check"
        assert guarded["pacing_signal"]["recommended_next_step"] == "advance"
        assert guarded["pacing_signal"]["override_pace"] == "steady"
        assert "resolved with application-level evidence" in guarded["pacing_signal"]["override_reason"]
        assert "Repeated full-sequence repair now looks stable" in guarded["stage_reason"]

    def test_enforce_turn_response_controls_promotes_fresh_example_after_causal_clarification(
        self, hybrid_system
    ):
        guarded = hybrid_system._enforce_turn_response_controls(
            current_stage="exploration",
            analysis={
                "stage_action": "stay",
                "target_stage": "exploration",
                "stage_reason": "Learner gets the mechanism but asked for clarification.",
                "teaching_move": "clarify",
                "answer_current_question_first": True,
                "misconception_events": [],
                "pacing_signal": {
                    "concept_closure": "almost_ready",
                    "reasoning_mode": "application",
                    "override_pace": "slow",
                    "override_reason": "",
                    "recommended_next_step": "ask_same_level",
                },
            },
            lesson_state={
                "concepts": [
                    {"id": "c1", "status": "covered"},
                    {"id": "c2", "status": "covered"},
                ]
            },
            pacing_state={"current_pace": "steady"},
            misconception_state={"active_misconceptions": []},
        )

        assert guarded["pacing_signal"]["recommended_next_step"] == "give_example"
        assert guarded["pacing_signal"]["override_pace"] == "steady"
        assert "fresh case" in guarded["pacing_signal"]["override_reason"]
        assert guarded["follow_up_question_policy"] == "optional_if_explanation_suffices"

    def test_response_constraints_prefer_fresh_example_after_repeated_sequence_repair(
        self, hybrid_system
    ):
        constraints = hybrid_system._format_response_constraints_for_tutor(
            pacing_state={"current_pace": "steady"},
            turn_analysis={
                "stage_action": "stay",
                "pacing_signal": {
                    "recommended_next_step": "give_example",
                },
                "misconception_events": [],
            },
            misconception_state={
                "active_misconceptions": [
                    {
                        "key": "full_rule_sequence_gap",
                        "text": "Stops after one local check instead of walking the full rule sequence.",
                        "repair_priority": "must_address_now",
                        "repair_scope": "full_sequence",
                        "repair_pattern": "same_snippet_walkthrough",
                        "times_seen": 2,
                    }
                ]
            },
        )

        assert "Response shape: example_then_check" in constraints
        assert "Prefer one fresh transfer example over another paraphrase recheck." in constraints

    def test_response_constraints_allow_clarify_without_token_recheck(
        self, hybrid_system
    ):
        constraints = hybrid_system._format_response_constraints_for_tutor(
            pacing_state={"current_pace": "steady"},
            turn_analysis={
                "teaching_move": "clarify",
                "answer_current_question_first": True,
                "stage_action": "stay",
                "pacing_signal": {
                    "recommended_next_step": "ask_same_level",
                },
                "misconception_events": [],
            },
            misconception_state={"active_misconceptions": []},
        )

        assert "Response shape: answer_then_optional_check" in constraints
        assert "Do not ask an answer-echo question" in constraints
        assert "you may end without a follow-up question" in constraints

    def test_response_constraints_require_fresh_case_after_repair(
        self, hybrid_system
    ):
        constraints = hybrid_system._format_response_constraints_for_tutor(
            pacing_state={"current_pace": "steady"},
            turn_analysis={
                "teaching_move": "repair",
                "stage_action": "stay",
                "pacing_signal": {
                    "recommended_next_step": "give_example",
                },
                "misconception_events": [],
            },
            misconception_state={"active_misconceptions": []},
        )

        assert "Do not ask an answer-echo question" in constraints
        assert "use one fresh case, comparison, or consequence check" in constraints

    def test_coerce_misconception_events_preserves_sequence_repair_metadata(
        self, hybrid_system
    ):
        events = hybrid_system._coerce_misconception_events(
            {
                "misconception_events": [
                    {
                        "key": "full_rule_sequence_gap",
                        "text": "Stops after one local check instead of walking the full rule sequence.",
                        "action": "still_active",
                        "repair_priority": "must_address_now",
                        "repair_scope": "full_sequence",
                        "repair_pattern": "same_snippet_walkthrough",
                    }
                ]
            }
        )

        assert events == [
            {
                "key": "full_rule_sequence_gap",
                "text": "Stops after one local check instead of walking the full rule sequence.",
                "action": "still_active",
                "repair_priority": "must_address_now",
                "repair_scope": "full_sequence",
                "repair_pattern": "same_snippet_walkthrough",
            }
        ]


class TestGuidedTurnOrdering:
    def test_render_turn_analysis_for_display_explains_fields(self, hybrid_system):
        rendered = hybrid_system._render_turn_analysis_for_display(
            {
                "turn_route": "objective_answer",
                "answer_current_question_first": True,
                "student_question_to_answer": "What goes under principles?",
                "teaching_move": "clarify",
                "stage_action": "stay",
                "target_stage": "introduction",
                "stage_reason": "Student still needs a clean distinction.",
                "pacing_signal": {
                    "grasp_level": "fragile",
                    "reasoning_mode": "paraphrase",
                    "support_needed": "heavy",
                    "confusion_level": "high",
                    "response_pattern": "hedging",
                    "concept_closure": "not_ready",
                    "override_pace": "slow",
                    "override_reason": "Student explicitly needs a slower pace.",
                    "recommended_next_step": "re-explain",
                },
                "mastery_signal": {
                    "should_update": False,
                    "level": "not_attempted",
                    "confidence": 0.0,
                    "evidence_summary": "",
                },
            }
        )

        # New compact markdown format — every input value must still appear.
        # Simple fields are bold-labelled and values render inline.
        assert "**Turn route:** objective_answer" in rendered
        assert "**Answer student question first:** **yes**" in rendered
        assert "What goes under principles?" in rendered  # student_question_to_answer
        assert "**Teaching move:** clarify" in rendered
        assert "**Stage:**" in rendered and "introduction" in rendered
        assert "Student still needs a clean distinction." in rendered  # stage_reason

        # Nested pacing block — all values present
        assert "**Pacing signal**" in rendered
        for value in ("fragile", "paraphrase", "heavy", "high", "hedging", "not_ready", "re-explain"):
            assert value in rendered, f"pacing value missing: {value}"
        assert "`slow`" in rendered  # override_pace
        assert "Student explicitly needs a slower pace." in rendered

        # Mastery block present with its values
        assert "**Mastery signal**" in rendered
        assert "not_attempted" in rendered
        assert "`0.0`" in rendered or "`0`" in rendered  # confidence

        # Boilerplate meta-prose must NOT appear any more
        assert "TURN ANALYSIS EXPLANATION" not in rendered
        assert "Current value:" not in rendered
        assert "It is computed" not in rendered

    @pytest.mark.asyncio
    async def test_guided_turn_runs_analyzer_before_tutor_and_write(
        self, hybrid_system, monkeypatch
    ):
        hybrid_system._session_cache.store(
            "sess-1", "obj-1", "Explain WCAG structure", [], "", "Evidence pack"
        )
        hybrid_system._session_cache.store_teaching_plan(
            "sess-1",
            {
                "objective": "Explain WCAG structure",
                "concepts": [
                    {
                        "id": "c1",
                        "name": "Principles vs guidelines",
                        "status": "not_covered",
                    }
                ],
                "recommended_order": ["c1"],
            },
        )

        monkeypatch.setattr(
            hybrid_system,
            "_fetch_objective_by_id",
            lambda objective_id: {"text": "Explain WCAG structure"},
        )

        async def fake_load_student_bundle(student_id, objective_id=""):
            return {}

        call_order = []

        async def fake_turn_analyzer(**kwargs):
            call_order.append("analyzer")
            return {
                "turn_route": "objective_answer",
                "answer_current_question_first": True,
                "student_question_to_answer": "What goes under principles?",
                "teaching_move": "clarify",
                "stage_action": "stay",
                "target_stage": "introduction",
                "stage_reason": "",
                "mastery_signal": {
                    "should_update": False,
                    "level": "not_attempted",
                    "confidence": 0.0,
                    "evidence_summary": "",
                },
                "misconception_events": [
                    {
                        "key": "principle_vs_guideline_confusion",
                        "text": "Confuses principles with guidelines.",
                        "action": "log",
                        "repair_priority": "must_address_now",
                    }
                ],
                "lesson_state_patch": {
                    "active_concept": "c1",
                    "pending_check": "Explain what a guideline does",
                    "bridge_back_target": "c1",
                    "concept_updates": [
                        {"concept_id": "c1", "status": "in_progress"}
                    ],
                },
                "pacing_signal": {
                    "grasp_level": "fragile",
                    "reasoning_mode": "paraphrase",
                    "support_needed": "heavy",
                    "confusion_level": "high",
                    "response_pattern": "hedging",
                    "concept_closure": "not_ready",
                    "override_pace": "slow",
                    "override_reason": "Student explicitly needs a slower pace.",
                    "recommended_next_step": "re-explain",
                },
                "objective_memory_patch": {
                    "summary": "",
                    "demonstrated_skills": [],
                    "active_gaps": [],
                    "next_focus": "",
                },
                "learner_memory_patch": {
                    "summary": "",
                    "strengths": [],
                    "support_needs": [],
                    "tendencies": [],
                    "successful_strategies": [],
                },
            }

        def fake_build_messages(**kwargs):
            call_order.append("build_messages")
            assert kwargs["turn_analysis"]["turn_route"] == "objective_answer"
            assert kwargs["pacing_state"]["current_pace"] == "slow"
            assert kwargs["misconception_state"]["active_misconceptions"][0]["key"] == (
                "principle_vs_guideline_confusion"
            )
            return [{"role": "system", "content": "test"}]

        async def fake_stream_response(messages, ws_send):
            call_order.append("tutor")
            return "Tutor response"

        async def fake_apply_updates(**kwargs):
            call_order.append("write")
            hybrid_system._session_cache.apply_pacing_signal(
                "sess-1",
                {
                    "override_pace": "slow",
                    "override_reason": "Student explicitly needs a slower pace.",
                    "recommended_next_step": "re-explain",
                    "grasp_level": "fragile",
                    "reasoning_mode": "paraphrase",
                    "support_needed": "heavy",
                    "confusion_level": "high",
                    "response_pattern": "hedging",
                    "concept_closure": "not_ready",
                },
            )
            hybrid_system._session_cache.apply_misconception_events(
                "sess-1",
                [
                    {
                        "key": "principle_vs_guideline_confusion",
                        "text": "Confuses principles with guidelines.",
                        "action": "log",
                        "repair_priority": "must_address_now",
                    }
                ],
            )
            return {"stage": "introduction", "stage_advanced": False}

        monkeypatch.setattr(hybrid_system, "_load_student_bundle", fake_load_student_bundle)
        monkeypatch.setattr(hybrid_system, "_run_turn_analyzer", fake_turn_analyzer)
        monkeypatch.setattr(hybrid_system, "_build_guided_tutor_messages", fake_build_messages)
        monkeypatch.setattr(hybrid_system, "_stream_response", fake_stream_response)
        monkeypatch.setattr(
            hybrid_system, "_apply_turn_analysis_updates", fake_apply_updates
        )

        ws_events = []

        async def ws_send(data):
            ws_events.append(data)

        result = await hybrid_system.conduct_guided_session_streaming(
            student_id="student-1",
            student_response="What goes under principles?",
            session_id="sess-1",
            ws_send=ws_send,
        )

        assert call_order.index("analyzer") < call_order.index("write")
        assert call_order.index("write") < call_order.index("tutor")
        assert result["stage"] == "introduction"
        assert [event["type"] for event in ws_events] == [
            "stage",
            "turn_analysis_generating",
            "turn_analysis",
            "stage",
            "stream_end",
        ]
        assert ws_events[2]["analysis"]["turn_route"] == "objective_answer"
        assert ws_events[2]["analysis"]["pacing_signal"]["override_pace"] == "slow"
        display = ws_events[2]["display_analysis"]
        # New compact markdown format: bold labels with inline values, no boilerplate.
        assert "**Turn route:** objective_answer" in display
        assert "**Pacing signal**" in display
        assert "re-explain" in display
        assert "TURN ANALYSIS EXPLANATION" not in display


class TestGuidedRetrieval:
    def test_retrieval_coverage_uses_fixed_caps_and_direct_checks(
        self, hybrid_system
    ):
        coverage = hybrid_system._assess_retrieval_coverage(
            objective_text="Explain WCAG conformance levels",
            teaching_plan="8. dependency_order\n1. Conformance levels\n",
            results=[
                {
                    "tool": "get_glossary_term",
                    "args": {"term": "conformance"},
                    "category": "agentic",
                    "result": "Conformance means satisfying all Level A and Level AA success criteria.",
                    "chars": 67,
                    "status": "HIT",
                },
                {
                    "tool": "count_criteria",
                    "args": {"group_by": "level"},
                    "category": "agentic",
                    "result": "Counts by level: A, AA, AAA.",
                    "chars": 29,
                    "status": "HIT",
                },
            ],
        )

        assert "objective_type" not in coverage
        assert coverage["required_checks"]["conformance_rollup_rule"] is True
        assert coverage["missing_checks"] == []
        assert coverage["budget_chars"] == 20000

    @pytest.mark.asyncio
    async def test_agentic_retrieval_keeps_ordered_tool_trace(self, hybrid_system, monkeypatch):
        hybrid_system.wcag_mcp = FakeWCAGClient()
        seen_tool_names = set()

        async def fake_chat_with_tools(**kwargs):
            nonlocal seen_tool_names
            seen_tool_names = {
                tool_def["function"]["name"] for tool_def in kwargs["tools"]
            }
            return {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call-1",
                        "type": "function",
                        "function": {"name": "list_principles", "arguments": "{}"},
                    },
                    {
                        "id": "call-2",
                        "type": "function",
                        "function": {"name": "list_guidelines", "arguments": "{}"},
                    },
                ],
            }

        monkeypatch.setattr(hybrid_system.reasoning_client, "chat_with_tools", fake_chat_with_tools)

        ws_events = []

        async def ws_send(data):
            ws_events.append(data)

        results = await hybrid_system._run_agentic_retrieval(
            objective_text="Explain the hierarchy of WCAG",
            teaching_plan=(
                "1. plain_language_goal\nExplain the hierarchy.\n\n"
                "8. dependency_order\n1. Principles\n2. Guidelines\n"
            ),
            ws_send=ws_send,
        )

        assert len(hybrid_system.wcag_mcp.calls) == 1
        assert [call["tool"] for call in hybrid_system.wcag_mcp.calls[0]] == [
            "list_principles",
            "list_guidelines",
        ]
        assert "get_criterion" in seen_tool_names
        assert "get_techniques_for_criterion" in seen_tool_names
        assert "get_technique" in seen_tool_names
        assert "search_glossary" in seen_tool_names
        assert results[0]["round"] == 1
        assert results[0]["sequence"] == 1
        assert results[1]["sequence"] == 2
        assert any(event["detail"].startswith("Researching WCAG sources") for event in ws_events)

    @pytest.mark.asyncio
    async def test_build_retrieval_bundle_and_renderer_create_structured_teaching_pack(
        self, hybrid_system
    ):
        bundle = await hybrid_system._build_retrieval_bundle(
            results=[
                {
                    "tool": "get_success_criteria_detail",
                    "args": {"ref_id": "4.1.3"},
                    "category": "agentic",
                    "result": (
                        "# 4.1.3 Status Messages\n\n"
                        "**Level:** AA\n"
                        "**Principle:** 4 Robust\n"
                        "**Guideline:** 4.1 Compatible\n\n"
                        "## Success Criterion\n\n"
                        "Status messages can be presented without receiving focus."
                    ),
                    "chars": 180,
                    "status": "HIT",
                },
                {
                    "tool": "search_glossary",
                    "args": {"query": "status message"},
                    "category": "agentic",
                    "result": "# Glossary Search Results for \"status message\" (1 found)",
                    "chars": 52,
                    "status": "HIT",
                },
                {
                    "tool": "get_glossary_term",
                    "args": {"term": "status message"},
                    "category": "agentic",
                    "result": (
                        "# status message\n\n"
                        "change in content that is not a change of context\n\n"
                        "[View in WCAG 2.2 Glossary](https://example.test)"
                    ),
                    "chars": 112,
                    "status": "HIT",
                },
                {
                    "tool": "get_criterion",
                    "args": {"ref_id": "4.1.3"},
                    "category": "agentic",
                    "result": (
                        "# 4.1.3 Status Messages\n\n"
                        "## In Brief\n\n"
                        "Use assistive technology announcements without moving focus.\n\n"
                        "## Description\n\n"
                        "Status messages are announced without receiving focus.\n\n"
                        "## Intent\n\n"
                        "The scope is specific to status messages and changes that are not delivered via a change of context.\n\n"
                        "## Examples\n\n"
                        "### Example 1\n\n"
                        "After a user presses Search, a message says 5 results returned.\n\n"
                        "### Example 2\n\n"
                        "Examples of Changes That Are Not Status Messages. An author displays an error message in a dialog. This does not meet the definition.\n\n"
                        "### Example 3\n\n"
                        "Other uses of live regions or alerts can make an application too chatty."
                    ),
                    "chars": 650,
                    "status": "HIT",
                },
                {
                    "tool": "get_techniques_for_criterion",
                    "args": {"ref_id": "4.1.3"},
                    "category": "agentic",
                    "result": (
                        "# Techniques for 4.1.3 Status Messages\n\n"
                        "## Sufficient Techniques\n\n"
                        "- **ARIA22**: Using role=status\n\n"
                        "## Failure Techniques\n\n"
                        "- **F103**: Messages not programmatically determined"
                    ),
                    "chars": 176,
                    "status": "HIT",
                },
            ],
            objective_text="Apply ARIA live regions to communicate updates without moving focus",
            teaching_plan="1. plain_language_goal\nExplain live regions.\n",
        )

        rendered = hybrid_system._render_retrieval_bundle(bundle)

        assert bundle["sections"]["definitions"]
        assert bundle["sections"]["core_rules"]
        assert bundle["sections"]["decision_rules"]
        assert bundle["sections"]["contrast_cases"]
        assert bundle["sections"]["technique_patterns"]
        assert "Glossary Search Results" not in rendered
        assert "## CORE FACTS" in rendered
        assert "## DEFINITIONS" in rendered
        assert "## DECISION BOUNDARIES" in rendered
        assert "## CONTRAST CASES" in rendered
        assert "## TECHNIQUE PATTERNS" in rendered
        assert "status message" in rendered
        assert "ARIA22" in rendered

    @pytest.mark.asyncio
    async def test_teaching_content_pipeline_uses_agentic_retrieval(self, hybrid_system, monkeypatch):
        async def fake_generate_teaching_plan(objective_text, teaching_content=""):
            return "1. plain_language_goal\nExplain the hierarchy.\n"

        async def fake_agentic_retrieval(objective_text, teaching_plan, ws_send):
            return [
                {
                    "tool": "list_principles",
                    "args": {},
                    "category": "agentic",
                    "result": "WCAG has four principles.",
                    "chars": 25,
                    "status": "HIT",
                }
            ]

        async def fake_build_bundle(results, objective_text="", teaching_plan=None):
            return {
                "version": 1,
                "sections": {"core_rules": []},
                "raw_hits": [],
            }

        def fake_render_bundle(bundle, for_display=False):
            assert bundle["version"] == 1
            return "EVIDENCE PACK (DISPLAY)" if for_display else "EVIDENCE PACK"

        def fail_if_called(*args, **kwargs):
            raise AssertionError("legacy retrieval planner path should not run")

        monkeypatch.setattr(hybrid_system, "_generate_teaching_plan", fake_generate_teaching_plan)
        monkeypatch.setattr(hybrid_system, "_run_agentic_retrieval", fake_agentic_retrieval)
        monkeypatch.setattr(hybrid_system, "_build_retrieval_bundle", fake_build_bundle)
        monkeypatch.setattr(hybrid_system, "_render_retrieval_bundle", fake_render_bundle)
        monkeypatch.setattr(hybrid_system, "_generate_retrieval_plan", fail_if_called)
        monkeypatch.setattr(hybrid_system, "_extract_tool_calls", fail_if_called)

        ws_events = []

        async def ws_send(data):
            ws_events.append(data)

        teaching_plan, evidence_pack, retrieval_bundle, extracted_concepts = (
            await hybrid_system._run_teaching_content_pipeline(
                objective_text="Explain the hierarchy of WCAG",
                session_id="sess-1",
                objective_id="obj-1",
                ws_send=ws_send,
            )
        )

        assert teaching_plan.startswith("1. plain_language_goal")
        assert evidence_pack == "EVIDENCE PACK"
        assert retrieval_bundle["version"] == 1
        assert [event["type"] for event in ws_events] == [
            "stage",
            "teaching_plan_generating",
            "teaching_plan",
            "stage",
            "teaching_content_generating",
            "stage",
            "teaching_content",
            "stage",
        ]
        assert ws_events[6]["content"] == evidence_pack
        # extracted_concepts may be None when the fake client doesn't
        # support response_format — that's the expected fallback.
        assert extracted_concepts is None or isinstance(extracted_concepts, list)

    @pytest.mark.asyncio
    async def test_generate_teaching_plan_uses_reasoning_client_budget(
        self, hybrid_system, monkeypatch
    ):
        captured = {}

        def fake_chat(
            messages,
            temperature=0.7,
            max_tokens=1000,
            reasoning_effort=None,
            response_format=None,
        ):
            captured["messages"] = messages
            captured["temperature"] = temperature
            captured["max_tokens"] = max_tokens
            captured["reasoning_effort"] = reasoning_effort
            captured["response_format"] = response_format
            return (
                "1. objective_text\nExplain WCAG structure\n\n"
                "2. plain_language_goal\nExplain WCAG simply.\n\n"
                "3. mastery_definition\nDescribe the hierarchy.\n\n"
                "7. concept_decomposition\n- Principles\n- Guidelines\n- Success criteria\n\n"
                "8. dependency_order\n1. Principles\n2. Guidelines\n3. Success criteria\n"
            )

        monkeypatch.setattr(hybrid_system.reasoning_client, "chat", fake_chat)

        plan = await hybrid_system._generate_teaching_plan(
            "Explain the structure of WCAG"
        )

        assert "plain_language_goal" in plan
        assert hybrid_system.reasoning_client.deployment == "gpt-5.4"
        assert captured["max_tokens"] == TEACHING_PLAN_MAX_COMPLETION_TOKENS
        assert captured["reasoning_effort"] == TEACHING_PLAN_REASONING_EFFORT

    @pytest.mark.asyncio
    async def test_generate_teaching_plan_raises_on_empty_response(
        self, hybrid_system, monkeypatch
    ):
        monkeypatch.setattr(hybrid_system.reasoning_client, "chat", lambda *args, **kwargs: "")

        with pytest.raises(TeachingPlanGenerationError):
            await hybrid_system._generate_teaching_plan(
                "Explain the structure of WCAG"
            )


class TestToolActivityRationale:
    """Cover the rationale capture / tool_activity emission path."""

    def test_extract_planned_calls_strips_rationale_and_stashes_it(self, hybrid_system):
        tool_calls = [
            {
                "id": "call-1",
                "type": "function",
                "function": {
                    "name": "get_criterion",
                    "arguments": (
                        '{"ref_id": "1.1.1", '
                        '"rationale": "Need normative anchor for alt-text concept."}'
                    ),
                },
            }
        ]

        planned = hybrid_system._extract_agentic_planned_calls(
            tool_calls=tool_calls,
            round_number=1,
            seen_calls=set(),
            max_new_calls=4,
        )

        assert len(planned) == 1
        # Rationale was lifted onto the planned_call dict...
        assert planned[0]["rationale"] == "Need normative anchor for alt-text concept."
        # ...and stripped from the args that flow to the MCP server.
        assert "rationale" not in planned[0]["args"]
        assert planned[0]["args"] == {"ref_id": "1.1.1"}

    def test_extract_planned_calls_defaults_rationale_to_empty_string(self, hybrid_system):
        """Schema noncompliance must not block the call — surface as empty."""
        tool_calls = [
            {
                "id": "call-1",
                "type": "function",
                "function": {
                    "name": "list_principles",
                    "arguments": "{}",
                },
            }
        ]

        planned = hybrid_system._extract_agentic_planned_calls(
            tool_calls=tool_calls,
            round_number=1,
            seen_calls=set(),
            max_new_calls=4,
        )

        assert planned[0]["rationale"] == ""

    def test_extract_planned_calls_ignores_non_string_rationale(self, hybrid_system):
        """If the model emits something other than a string, fall back to empty
        rather than crashing on a downstream .strip() / JSON serialize."""
        tool_calls = [
            {
                "id": "call-1",
                "type": "function",
                "function": {
                    "name": "list_principles",
                    "arguments": '{"rationale": 42}',
                },
            }
        ]

        planned = hybrid_system._extract_agentic_planned_calls(
            tool_calls=tool_calls,
            round_number=1,
            seen_calls=set(),
            max_new_calls=4,
        )

        assert planned[0]["rationale"] == ""
        assert "rationale" not in planned[0]["args"]

    def test_annotate_retrieval_results_propagates_rationale(self, hybrid_system):
        planned = [
            {
                "tool_call_id": "call-1",
                "tool": "get_criterion",
                "args": {"ref_id": "1.1.1"},
                "rationale": "Need normative anchor.",
                "round": 1,
                "sequence": 1,
                "source": "guided_retrieval",
            }
        ]
        results = [
            {
                "tool": "get_criterion",
                "args": {"ref_id": "1.1.1"},
                "category": "agentic",
                "result": "...",
                "chars": 3,
                "status": "HIT",
            }
        ]

        annotated = hybrid_system._annotate_retrieval_results(planned, results)
        assert annotated[0]["rationale"] == "Need normative anchor."
        assert annotated[0]["round"] == 1
        assert annotated[0]["sequence"] == 1

    def test_build_tool_description_lookup_maps_name_to_description(
        self, hybrid_system
    ):
        defs = [
            {
                "type": "function",
                "function": {
                    "name": "search_wcag",
                    "description": "Searches WCAG  content.\n  Use for queries.",
                },
            },
            {"type": "function", "function": {"name": "no_desc"}},
            {"type": "function", "function": {}},  # malformed but tolerated
        ]
        lookup = hybrid_system._build_tool_description_lookup(defs)
        # Whitespace normalised
        assert lookup["search_wcag"] == "Searches WCAG content. Use for queries."
        assert lookup["no_desc"] == ""
        # No name → not surfaced
        assert len(lookup) == 2

    def test_summarise_tool_result_branches(self, hybrid_system):
        s = hybrid_system._summarise_tool_result
        assert s({"status": "HIT", "chars": 892}) == "892 chars"
        assert s({"status": "MISS", "chars": 0}) == "miss (0 chars)"
        assert s({"status": "BLOCKED", "chars": 0}) == "blocked"
        assert s({"status": "ERROR", "result": "boom"}).startswith("error: boom")
        assert s({"status": "HIT"}) == "hit"

    @pytest.mark.asyncio
    async def test_run_agentic_retrieval_emits_tool_activity_events(
        self, hybrid_system, monkeypatch
    ):
        """End-to-end: each tool call produces one calling event and one
        completed event with description (from def) and rationale (from model)."""
        hybrid_system.wcag_mcp = FakeWCAGClient()

        async def fake_chat_with_tools(**kwargs):
            return {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call-1",
                        "type": "function",
                        "function": {
                            "name": "list_principles",
                            "arguments": (
                                '{"rationale": "Anchor on top-level WCAG structure."}'
                            ),
                        },
                    },
                ],
            }

        monkeypatch.setattr(
            hybrid_system.reasoning_client, "chat_with_tools", fake_chat_with_tools
        )

        events = []

        async def ws_send(payload):
            events.append(payload)

        await hybrid_system._run_agentic_retrieval(
            objective_text="Explain the structure of WCAG",
            teaching_plan=(
                "1. plain_language_goal\nExplain hierarchy.\n\n"
                "8. dependency_order\n1. Principles\n"
            ),
            ws_send=ws_send,
        )

        tool_events = [e for e in events if e.get("type") == "tool_activity"]
        # One calling + one completed for the single tool call
        assert [e["status"] for e in tool_events] == ["calling", "completed"]
        for evt in tool_events:
            assert evt["phase"] == "retrieval"
            assert evt["name"] == "list_principles"
            assert evt["rationale"] == "Anchor on top-level WCAG structure."
            # Description sourced from the tool definition (non-empty)
            assert evt["description"]
            # Params do not leak the rationale
            assert "rationale" not in evt["params"]

        completed = tool_events[1]
        assert completed["result_status"] == "HIT"
        assert "chars" in completed["result_summary"]


class TestFirstTeachingTurn:
    """Cover the no-synthetic-message kickoff path (Option B)."""

    def test_build_guided_tutor_messages_first_turn_omits_history_and_user_turn(
        self, hybrid_system
    ):
        from question_app.services.tutor.prompts import FIRST_TURN_INSTRUCTION

        messages = hybrid_system._build_guided_tutor_messages(
            student_response=None,
            history=[
                {"role": "user", "content": "stale earlier turn"},
                {"role": "assistant", "content": "stale earlier reply"},
            ],
            teaching_content="evidence",
            student_context="ctx",
            current_stage="introduction",
            active_objective="obj",
            teaching_plan={"recommended_order": ["c1"], "concepts": [{"id": "c1", "name": "C1"}]},
            first_turn=True,
        )

        # No real history echoed back into a first-turn payload.
        assert "stale earlier turn" not in json.dumps(messages)
        # The first-turn instruction is present as a system block.
        assert any(
            m["role"] == "system" and FIRST_TURN_INSTRUCTION in m["content"]
            for m in messages
        )
        # Ends with exactly one ephemeral user nudge.
        assert messages[-1] == {"role": "user", "content": "Begin the lesson."}
        assert sum(1 for m in messages if m["role"] == "user") == 1

    def test_build_guided_tutor_messages_normal_turn_unchanged(self, hybrid_system):
        from question_app.services.tutor.prompts import FIRST_TURN_INSTRUCTION

        messages = hybrid_system._build_guided_tutor_messages(
            student_response="A real student message.",
            history=[{"role": "assistant", "content": "previous tutor turn"}],
            teaching_content="evidence",
            student_context="ctx",
            current_stage="introduction",
            active_objective="obj",
            teaching_plan={"recommended_order": ["c1"], "concepts": [{"id": "c1", "name": "C1"}]},
        )
        # No first-turn instruction, real student message at the end.
        assert all(FIRST_TURN_INSTRUCTION not in m["content"] for m in messages)
        assert messages[-1] == {"role": "user", "content": "A real student message."}
        assert any(
            m["role"] == "assistant" and m["content"] == "previous tutor turn"
            for m in messages
        )

    @pytest.mark.asyncio
    async def test_start_first_teaching_turn_skips_analyzer_and_appends_only_assistant(
        self, hybrid_system, monkeypatch
    ):
        # Fail loudly if the analyzer is ever called on the kickoff turn.
        async def explode_analyzer(**kwargs):
            raise AssertionError("analyzer must NOT run on first teaching turn")

        monkeypatch.setattr(hybrid_system, "_run_turn_analyzer", explode_analyzer)

        # Stub teaching content pipeline so we don't call the real LLM stack.
        teaching_plan = {
            "recommended_order": ["c1"],
            "concepts": [
                {"id": "c1", "name": "Principles vs guidelines", "status": "not_covered"}
            ],
        }
        teaching_content = "evidence pack body"

        async def fake_pipeline(objective_text, session_id, objective_id, ws_send):
            return teaching_plan, teaching_content, {}, []

        monkeypatch.setattr(
            hybrid_system, "_run_teaching_content_pipeline", fake_pipeline
        )

        async def fake_load_bundle(student_id, objective_id=""):
            return {}

        monkeypatch.setattr(hybrid_system, "_load_student_bundle", fake_load_bundle)

        stream_calls = []

        async def fake_stream(messages, ws_send):
            stream_calls.append(messages)
            return "Lesson opener: principles ground guidelines. Quick check — name one principle."

        monkeypatch.setattr(hybrid_system, "_stream_response", fake_stream)

        # FakeStudentService does not implement increment_turn_count; add a stub.
        increments = []

        async def fake_increment(session_id):
            increments.append(session_id)
            return None

        hybrid_system.student_mcp.increment_turn_count = fake_increment

        events = []

        async def ws_send(payload):
            events.append(payload)

        result = await hybrid_system._start_first_teaching_turn(
            student_id="student-1",
            session_id="sess-1",
            objective_id="obj-1",
            objective_text="Explain WCAG structure",
            ws_send=ws_send,
        )

        # Streamed exactly one tutor response.
        assert len(stream_calls) == 1
        # Conversation memory got ONE assistant entry and zero user entries.
        history = hybrid_system.get_conversation_history("student-1")
        assert [m["role"] for m in history] == ["assistant"]
        assert "Lesson opener" in history[0]["content"]
        # Turn count incremented exactly once.
        assert increments == ["sess-1"]
        # No analyzer-related WS events were ever emitted.
        event_types = [e.get("type") for e in events]
        assert "turn_analysis_generating" not in event_types
        assert "turn_analysis" not in event_types
        # The closing event marks this as a first turn.
        assert any(
            e.get("type") == "stream_end"
            and e.get("metadata", {}).get("first_turn") is True
            for e in events
        )
        # Returned metadata is honest about being a first turn at introduction.
        assert result["stage"] == "introduction"
        assert result["first_turn"] is True
        # The cache now holds a lesson_state with active_concept set from the plan.
        lesson_state = hybrid_system._session_cache.get_lesson_state("sess-1")
        assert lesson_state.get("active_concept") == "c1"


class TestTurnAnalysisRenderEdgeCases:
    """Cover the angle-bracket-eats-text and concept_updates-truncation bugs."""

    def test_string_values_escape_html_tags(self, hybrid_system):
        rendered = hybrid_system._render_turn_analysis_for_display(
            {
                "mastery_signal": {
                    "should_update": True,
                    "level": "in_progress",
                    "confidence": 0.8,
                    "evidence_summary": (
                        "Correctly identified <button> as a control and <div> "
                        "as a generic container."
                    ),
                },
                "objective_memory_patch": {
                    "summary": "Classified <button> vs <div> correctly.",
                },
                "learner_memory_patch": {
                    "successful_strategies_add": [
                        "Use simple tag contrasts like <button> vs <div>"
                    ],
                },
            }
        )

        # Raw angle brackets must be escaped so marked.parse doesn't render
        # them as empty HTML elements (which silently drops the visible text).
        assert "<button>" not in rendered
        assert "<div>" not in rendered
        assert "&lt;button&gt;" in rendered
        assert "&lt;div&gt;" in rendered
        # The surrounding prose must still be intact.
        assert "Correctly identified" in rendered
        assert "as a control and" in rendered
        assert "as a generic container" in rendered
        assert "Use simple tag contrasts like" in rendered

    def test_concept_updates_list_of_dicts_renders_as_sublist_no_truncation(
        self, hybrid_system
    ):
        long_label = (
            "Started learning what semantic means in this context "
            "(built-in meaning vs styling, not just visual appearance)"
        )
        rendered = hybrid_system._render_turn_analysis_for_display(
            {
                "lesson_state_patch": {
                    "concept_updates": [
                        {
                            "concept_id": "interactive_purpose_vs_generic_structure",
                            "status": "covered",
                            "label": "Distinguishes control from generic container",
                        },
                        {
                            "concept_id": "semantic_controls_and_builtin_meaning",
                            "status": "in_progress",
                            "label": long_label,
                        },
                    ],
                },
            }
        )

        # No truncation marker: every label must survive in full.
        assert "…" not in rendered
        assert long_label in rendered
        # Both concepts present and rendered as a sublist (not a JSON dump).
        assert "interactive_purpose_vs_generic_structure" in rendered
        assert "semantic_controls_and_builtin_meaning" in rendered
        assert "concept_id=`interactive_purpose_vs_generic_structure`" in rendered
        assert "status=`covered`" in rendered
        assert "status=`in_progress`" in rendered
        # The output is a real markdown sublist, not a single inline JSON blob.
        assert "[{" not in rendered

    def test_list_of_scalars_still_comma_joins(self, hybrid_system):
        rendered = hybrid_system._render_turn_analysis_for_display(
            {
                "objective_memory_patch": {
                    "demonstrated_skills_add": ["names <button>", "explains semantic"],
                    "active_gaps_current": ["keyboard support"],
                },
            }
        )
        assert "names &lt;button&gt;, explains semantic" in rendered
        assert "keyboard support" in rendered


class TestTeachingContentDisplay:
    """The side panel needs the FULL teaching pack; the tutor LLM gets a
    truncated copy so the prompt fits its context budget."""

    def _bundle_with_long_items(self):
        long_text = "x" * 5000
        return {
            "sections": {
                "core_rules": [
                    {"title": "Core A", "content": long_text},
                    {"title": "Core B", "content": long_text},
                    {"title": "Core C", "content": long_text},  # past max_items=2
                ],
                "definitions": [
                    {"title": "Def A", "content": long_text},
                ],
            }
        }

    def test_render_retrieval_bundle_default_truncates_for_tutor(self, hybrid_system):
        bundle = self._bundle_with_long_items()
        tutor_text = hybrid_system._render_retrieval_bundle(bundle)

        # Item caps applied — "Core C" must NOT appear (max_items=2 for CORE FACTS)
        assert "Core C" not in tutor_text
        # Per-item char truncation applied — content gets the … suffix
        assert "..." in tutor_text or "…" in tutor_text
        # Tutor text length is well below the raw content length
        assert len(tutor_text) < 5000 * 3

    def test_render_retrieval_bundle_for_display_keeps_everything(self, hybrid_system):
        bundle = self._bundle_with_long_items()
        display_text = hybrid_system._render_retrieval_bundle(
            bundle, for_display=True
        )

        # All three items present (no max_items cap)
        assert "Core A" in display_text and "Core B" in display_text and "Core C" in display_text
        # No char truncation — the literal long_text appears intact
        assert ("x" * 5000) in display_text
        # No truncation marker on the items
        assert "..." not in display_text and "…" not in display_text
        # Display text is materially larger than the tutor text
        tutor_text = hybrid_system._render_retrieval_bundle(bundle)
        assert len(display_text) > len(tutor_text) * 2

