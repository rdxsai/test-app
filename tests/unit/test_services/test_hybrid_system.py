import pytest

from question_app.services.tutor.hybrid_system import HybridCrewAISocraticSystem
from question_app.services.tutor.interfaces import VectorStoreInterface


class FakeVectorStore(VectorStoreInterface):
    async def search(self, query: str, n_results: int = 3):
        return []


class FakeAzureClient:
    def __init__(self, endpoint: str, deployment: str, api_key: str, api_version: str = ""):
        self.endpoint = endpoint
        self.deployment = deployment
        self.api_key = api_key
        self.api_version = api_version

    def chat(self, messages, temperature=0.7, max_tokens=1000, reasoning_effort=None):
        return ""

    async def chat_stream_async(self, messages, temperature=0.7, max_tokens=1000):
        if False:
            yield ""


class FakeStudentService:
    def __init__(self, session_state):
        self.session_state = session_state

    async def get_active_session(self, student_id: str):
        return dict(self.session_state)


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
        )

        assert "TURN ROUTING" in messages[0]["content"]
        assert "LESSON STATE:" in messages[0]["content"]
        turn_analysis_block = next(
            message["content"]
            for message in messages
            if message["role"] == "system" and message["content"].startswith("TURN ANALYSIS:")
        )
        assert "Route: adjacent_topic" in turn_analysis_block
        assert "Answer current question first: yes" in turn_analysis_block


class TestGuidedTurnOrdering:
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
                "misconceptions_to_log": [],
                "misconceptions_to_resolve": [],
                "lesson_state_patch": {
                    "active_concept": "c1",
                    "pending_check": "Explain what a guideline does",
                    "bridge_back_target": "c1",
                    "concept_updates": [
                        {"concept_id": "c1", "status": "in_progress"}
                    ],
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
            return [{"role": "system", "content": "test"}]

        async def fake_stream_response(messages, ws_send):
            call_order.append("tutor")
            return "Tutor response"

        async def fake_apply_updates(**kwargs):
            call_order.append("write")
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

        assert call_order.index("analyzer") < call_order.index("tutor")
        assert call_order.index("tutor") < call_order.index("write")
        assert result["stage"] == "introduction"
