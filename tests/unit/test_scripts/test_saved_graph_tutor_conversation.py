import importlib.util
from pathlib import Path

import pytest


SCRIPT_PATH = (
    Path(__file__).resolve().parents[3] / "scripts" / "run_saved_graph_tutor_conversation.py"
)
SPEC = importlib.util.spec_from_file_location("run_saved_graph_tutor_conversation", SCRIPT_PATH)
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
