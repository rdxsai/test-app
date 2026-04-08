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

        def fake_render_bundle(bundle):
            assert bundle["version"] == 1
            return "EVIDENCE PACK"

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

        teaching_plan, evidence_pack, retrieval_bundle = await hybrid_system._run_teaching_content_pipeline(
            objective_text="Explain the hierarchy of WCAG",
            session_id="sess-1",
            objective_id="obj-1",
            ws_send=ws_send,
        )

        assert teaching_plan.startswith("1. plain_language_goal")
        assert evidence_pack == "EVIDENCE PACK"
        assert retrieval_bundle["version"] == 1
