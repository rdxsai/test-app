import pytest

from question_app.services.tutor.hybrid_system import (
    GUIDED_TUTOR_RESPONSE_MAX_TOKENS,
    GUIDED_TUTOR_RESPONSE_REASONING_EFFORT,
    HybridCrewAISocraticSystem,
)
from question_app.services.tutor.workers.turns import (
    ASSESSMENT_REFLECTOR_MAX_TOKENS,
    ASSESSMENT_REFLECTOR_REASONING_EFFORT,
    GRAPH_ORCHESTRATOR_MAX_TOKENS,
    GRAPH_ORCHESTRATOR_REASONING_EFFORT,
    TURN_ANALYZER_MAX_TOKENS,
    TURN_ANALYZER_REASONING_EFFORT,
    GraphProgressionOrchestrator,
    StructuredTurnAnalyzer,
)


class CapturingClient:
    def __init__(self):
        self.calls = []

    def chat(
        self,
        messages,
        temperature=0.7,
        max_tokens=1000,
        reasoning_effort=None,
        response_format=None,
    ):
        self.calls.append(
            {
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "reasoning_effort": reasoning_effort,
                "response_format": response_format,
            }
        )
        return "{}"


@pytest.mark.asyncio
async def test_turn_analyzer_uses_explicit_generous_reasoning_budget():
    client = CapturingClient()
    analyzer = StructuredTurnAnalyzer(
        reasoning_client=client,
        turn_prompt_builder=lambda **kwargs: "turn prompt",
        assessment_prompt_builder=lambda **kwargs: "assessment prompt",
        lesson_state_formatter=lambda value: "",
        pacing_state_formatter=lambda value: "",
        misconception_state_formatter=lambda value: "",
        transcript_formatter=lambda history, response: response,
        json_parser=lambda response, fallback: {"parsed": True},
    )

    result = await analyzer.analyze_turn(
        history=[],
        student_response="I am confused.",
        teaching_content="content",
        student_context="student",
        current_stage="introduction",
        active_objective="objective",
        teaching_plan={},
    )

    assert result == {"parsed": True}
    assert client.calls[-1]["max_tokens"] == TURN_ANALYZER_MAX_TOKENS
    assert client.calls[-1]["reasoning_effort"] == TURN_ANALYZER_REASONING_EFFORT


@pytest.mark.asyncio
async def test_assessment_reflector_uses_explicit_generous_reasoning_budget():
    client = CapturingClient()
    analyzer = StructuredTurnAnalyzer(
        reasoning_client=client,
        turn_prompt_builder=lambda **kwargs: "turn prompt",
        assessment_prompt_builder=lambda **kwargs: "assessment prompt",
        lesson_state_formatter=lambda value: "",
        pacing_state_formatter=lambda value: "",
        misconception_state_formatter=lambda value: "",
        transcript_formatter=lambda history, response: response,
        json_parser=lambda response, fallback: {"reflected": True},
    )

    result = await analyzer.reflect_on_assessment(
        history=[],
        student_response="My answer.",
        teaching_content="content",
        student_context="student",
        current_stage="mini_assessment",
        active_objective="objective",
        teaching_plan={},
    )

    assert result == {"reflected": True}
    assert client.calls[-1]["max_tokens"] == ASSESSMENT_REFLECTOR_MAX_TOKENS
    assert (
        client.calls[-1]["reasoning_effort"]
        == ASSESSMENT_REFLECTOR_REASONING_EFFORT
    )


@pytest.mark.asyncio
async def test_graph_orchestrator_uses_explicit_generous_reasoning_budget():
    client = CapturingClient()
    orchestrator = GraphProgressionOrchestrator(
        reasoning_client=client,
        json_parser=lambda response, fallback: fallback,
    )

    await orchestrator.decide(
        graph_state={
            "active_node_id": "n1",
            "primary_route": ["n1", "n2"],
            "node_labels": {"n1": "First", "n2": "Second"},
        },
        turn_analysis={"stage_action": "stay"},
        lesson_state={},
    )

    assert client.calls[-1]["max_tokens"] == GRAPH_ORCHESTRATOR_MAX_TOKENS
    assert client.calls[-1]["reasoning_effort"] == GRAPH_ORCHESTRATOR_REASONING_EFFORT


@pytest.mark.asyncio
async def test_guided_tutor_response_uses_explicit_generous_reasoning_budget(
    monkeypatch,
):
    client = CapturingClient()

    def capture_tutor_chat(*args, **kwargs):
        CapturingClient.chat(client, *args, **kwargs)
        return "Tutor response."

    client.chat = capture_tutor_chat
    system = HybridCrewAISocraticSystem.__new__(HybridCrewAISocraticSystem)
    system.client = client

    async def fake_progressive_send(text, ws_send):
        await ws_send({"type": "token", "content": text})

    monkeypatch.setattr(system, "_progressive_send", fake_progressive_send)
    events = []

    async def ws_send(event):
        events.append(event)

    result = await system._stream_response(
        [{"role": "user", "content": "question"}],
        ws_send,
    )

    assert result == "Tutor response."
    assert client.calls[-1]["max_tokens"] == GUIDED_TUTOR_RESPONSE_MAX_TOKENS
    assert client.calls[-1]["reasoning_effort"] == GUIDED_TUTOR_RESPONSE_REASONING_EFFORT
    assert events[0]["type"] == "stream_start"
