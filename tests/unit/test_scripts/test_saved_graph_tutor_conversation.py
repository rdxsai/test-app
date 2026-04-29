import importlib.util
from pathlib import Path

import pytest


SCRIPT_PATH = (
    Path(__file__).resolve().parents[3]
    / "scripts"
    / "run_saved_graph_tutor_conversation.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_saved_graph_tutor_conversation", SCRIPT_PATH
)
conversation = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(conversation)


@pytest.mark.asyncio
async def test_in_memory_student_service_maps_runtime_session_aliases():
    service = conversation.InMemoryStudentService(
        student_id="student-1",
        session_id="session-1",
        objective_id="objective-1",
    )

    session = await service.update_session_state(
        "session-1",
        stage="guided_practice",
        turns=4,
    )

    assert session["current_stage"] == "guided_practice"
    assert session["turns_on_objective"] == 4
    assert "stage" not in session
    assert "turns" not in session


@pytest.mark.asyncio
async def test_generate_student_reply_records_llm_metadata():
    class FakeClient:
        last_request_metadata = {}

        def chat(self, messages, temperature, max_tokens):
            self.last_request_metadata = {
                "api": "chat_completions",
                "deployment": "gpt-5.4",
                "status": "success",
                "attempts": 1,
                "usage": {"total_tokens": 42},
            }
            return "I think the alt text should explain the image purpose."

    result = await conversation.generate_student_reply(
        client=FakeClient(),
        objective_text="Evaluate text alternatives for non-text content.",
        turn=2,
        tutor_response="What should the alt text communicate?",
        history=[{"role": "assistant", "content": "What should it communicate?"}],
    )

    assert (
        result["response"] == "I think the alt text should explain the image purpose."
    )
    assert result["llm_request_metadata"]["deployment"] == "gpt-5.4"
    assert result["llm_request_metadata"]["attempts"] == 1
    assert result["llm_request_metadata"]["usage"]["total_tokens"] == 42
