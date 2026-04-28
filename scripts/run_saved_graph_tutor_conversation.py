#!/usr/bin/env python3
"""Run a guided tutor conversation from a saved graph/content artifact.

This harness avoids retrieval entirely. It seeds the guided tutor runtime from
an existing graph-grounded content bundle, simulates a student over multiple
turns, and records the tutor, analyzer, graph-orchestrator, prompt, websocket,
and state artifacts for later inspection.
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import json
import os
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
os.chdir(PROJECT_ROOT)

from dotenv import load_dotenv

load_dotenv()

from question_app.core.config import config
from question_app.services.tutor.azure_client import AzureAPIMClient
from question_app.services.tutor.hybrid_system import HybridCrewAISocraticSystem
from question_app.services.tutor.interfaces import VectorStoreInterface

DEFAULT_ARTIFACT = (
    PROJECT_ROOT
    / "results"
    / "graph_retrieval_demo_20260427_201649"
    / "0157_artifact_final_graph_content.json"
)
DEFAULT_RENDERED_CONTENT = (
    PROJECT_ROOT
    / "results"
    / "graph_retrieval_demo_20260427_201649"
    / "0156_artifact_tutor_facing_content_rendered.md"
)
RESULTS_DIR = PROJECT_ROOT / "results"


STUDENT_SYSTEM_PROMPT = """You are simulating a student in a web accessibility tutoring session.

Profile:
- Frontend developer.
- Intermediate HTML/CSS/JS.
- Knows accessibility matters but is not confident applying WCAG.

Conversation behavior:
- Reply to the tutor's exact last question or instruction.
- Do not be too polished. Sound like a real learner.
- Keep each reply to 1-5 sentences unless asked for a checklist.
- Turns 1-3: be confused or partially wrong.
- Turns 4-6: start improving, but ask edge-case questions.
- Turns 7-10: apply the concepts to examples and occasionally overgeneralize.
- Turns 11-14: attempt a full evaluation process and ask for correction.
- Ask clarifying questions when the tutor response creates a useful next step.
- Do not mention that you are simulated.
"""


class NullVectorStore(VectorStoreInterface):
    async def search(self, query: str, n_results: int = 3):
        return []


class NullDatabase:
    pass


class InMemoryStudentService:
    def __init__(self, *, student_id: str, session_id: str, objective_id: str) -> None:
        self.student_id = student_id
        self.session_id = session_id
        self.profile = {
            "student_id": student_id,
            "technical_level": "intermediate",
            "a11y_exposure": "beginner",
            "role_context": "frontend developer",
            "learning_goal": "learn to evaluate non-text content alternatives",
        }
        self.session = {
            "session_id": session_id,
            "student_id": student_id,
            "current_stage": "introduction",
            "active_objective_id": objective_id,
            "turns_on_objective": 0,
            "assessment_progress": "{}",
        }
        self.mastery: List[Dict[str, Any]] = []
        self.misconceptions: List[Dict[str, Any]] = []
        self.learner_memory: Dict[str, Any] = {}
        self.objective_memory: Dict[str, Dict[str, Any]] = {}
        self.runtime_cache: Dict[str, Dict[str, Any]] = {}

    async def get_memory_bundle(
        self,
        student_id: str,
        objective_id: str = "",
    ) -> Dict[str, Any]:
        return {
            "profile": copy.deepcopy(self.profile),
            "mastery": copy.deepcopy(self.mastery),
            "session": copy.deepcopy(self.session),
            "misconceptions": copy.deepcopy(self.misconceptions),
            "learner_memory": copy.deepcopy(self.learner_memory),
            "objective_memory": copy.deepcopy(
                self.objective_memory.get(objective_id, {})
            ),
        }

    async def get_active_session(self, student_id: str) -> Dict[str, Any]:
        return copy.deepcopy(self.session)

    async def update_session_state(self, session_id: str, **kwargs) -> Dict[str, Any]:
        self.session.update(kwargs)
        self.session["session_id"] = session_id
        return copy.deepcopy(self.session)

    async def increment_turn_count(self, session_id: str) -> None:
        self.session["turns_on_objective"] = (
            int(self.session.get("turns_on_objective", 0) or 0) + 1
        )

    async def get_session_runtime_cache(self, session_id: str) -> Dict[str, Any]:
        return copy.deepcopy(self.runtime_cache.get(session_id, {}))

    async def save_session_runtime_cache(
        self,
        session_id: str,
        payload: Dict[str, Any],
    ) -> None:
        self.runtime_cache[session_id] = copy.deepcopy(payload)

    async def clear_session_runtime_cache(self, session_id: str) -> None:
        self.runtime_cache.pop(session_id, None)

    async def upsert_objective_memory(
        self,
        student_id: str,
        objective_id: str,
        **payload,
    ) -> None:
        self.objective_memory[objective_id] = copy.deepcopy(payload)

    async def upsert_learner_memory(self, student_id: str, **payload) -> None:
        self.learner_memory = copy.deepcopy(payload)

    async def get_objective_memory(
        self,
        student_id: str,
        objective_id: str,
    ) -> Dict[str, Any]:
        return copy.deepcopy(self.objective_memory.get(objective_id, {}))

    async def get_learner_memory(self, student_id: str) -> Dict[str, Any]:
        return copy.deepcopy(self.learner_memory)

    async def get_mastery_state(self, student_id: str) -> List[Dict[str, Any]]:
        return copy.deepcopy(self.mastery)

    async def apply_mastery_judgment(
        self,
        student_id: str,
        objective_id: str,
        mastery_level: str,
        *,
        evidence_summary: str = "",
        confidence: float = 0.0,
    ) -> Dict[str, Any]:
        record = {
            "objective_id": objective_id,
            "mastery_level": mastery_level,
            "evidence_summary": evidence_summary,
            "confidence": confidence,
        }
        self.mastery = [
            item for item in self.mastery if item.get("objective_id") != objective_id
        ]
        self.mastery.append(record)
        return {"updated": True, "applied_level": mastery_level, **record}

    async def get_misconception_patterns(
        self,
        student_id: str,
    ) -> List[Dict[str, Any]]:
        return copy.deepcopy(self.misconceptions)

    async def log_misconception(
        self,
        student_id: str,
        objective_id: str,
        text: str,
    ) -> None:
        self.misconceptions.append(
            {"objective_id": objective_id, "misconception_text": text}
        )

    async def resolve_misconception(
        self,
        student_id: str,
        objective_id: str,
        text: str,
    ) -> None:
        self.misconceptions = [
            item
            for item in self.misconceptions
            if item.get("misconception_text") != text
        ]

    async def record_assessment_answer(
        self,
        session_id: str,
        correct: bool,
    ) -> Dict[str, Any]:
        return {
            "recorded": True,
            "passed": bool(correct),
            "progress": {"asked": 1, "correct": 1 if correct else 0},
        }

    async def get_recommended_next_objective(self, student_id: str):
        return None


class InstrumentedSavedGraphTutor(HybridCrewAISocraticSystem):
    def __init__(self, *args, objective_text: str, objective_id: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.objective_text = objective_text
        self.objective_id = objective_id
        self.current_turn_trace: Dict[str, Any] = {}

    def _fetch_objective_by_id(self, objective_id: str) -> Dict[str, str]:
        return {"id": self.objective_id, "text": self.objective_text}

    def begin_turn_trace(
        self,
        *,
        turn: int,
        student_message: str,
        stage_before: str,
    ) -> None:
        self.current_turn_trace = {
            "turn": turn,
            "student_message": student_message,
            "stage_before": stage_before,
            "events": [],
            "timings": {},
        }

    def get_turn_trace(self) -> Dict[str, Any]:
        return copy.deepcopy(self.current_turn_trace)

    def _record_trace_event(self, name: str, payload: Any) -> None:
        self.current_turn_trace.setdefault("events", []).append(
            {"name": name, "payload": copy.deepcopy(payload)}
        )

    async def _run_turn_analyzer(self, *args, **kwargs):
        started = time.perf_counter()
        self._record_trace_event(
            "turn_analyzer_input",
            {
                "current_stage": kwargs.get("current_stage"),
                "active_objective": kwargs.get("active_objective"),
                "student_response": kwargs.get("student_response"),
                "lesson_state": kwargs.get("lesson_state"),
                "pacing_state": kwargs.get("pacing_state"),
                "misconception_state": kwargs.get("misconception_state"),
                "history": kwargs.get("history"),
            },
        )
        result = await super()._run_turn_analyzer(*args, **kwargs)
        self.current_turn_trace.setdefault("timings", {})["turn_analyzer"] = round(
            time.perf_counter() - started,
            2,
        )
        self._record_trace_event("turn_analyzer_output", result)
        return result

    async def _apply_turn_analysis_updates(self, *args, **kwargs):
        started = time.perf_counter()
        self._record_trace_event(
            "turn_analysis_update_input",
            {"analysis": kwargs.get("analysis")},
        )
        result = await super()._apply_turn_analysis_updates(*args, **kwargs)
        self.current_turn_trace.setdefault("timings", {})[
            "turn_analysis_update"
        ] = round(time.perf_counter() - started, 2)
        self._record_trace_event("turn_analysis_update_output", result)
        return result

    async def _decide_graph_progression(self, *args, **kwargs):
        started = time.perf_counter()
        self._record_trace_event("graph_orchestrator_input", kwargs)
        result = await super()._decide_graph_progression(*args, **kwargs)
        self.current_turn_trace.setdefault("timings", {})["graph_orchestrator"] = round(
            time.perf_counter() - started, 2
        )
        self._record_trace_event("graph_orchestrator_output", result)
        return result

    def _build_guided_tutor_messages(self, *args, **kwargs):
        messages = super()._build_guided_tutor_messages(*args, **kwargs)
        self._record_trace_event(
            "tutor_message_builder_output",
            {
                "kwargs": kwargs,
                "messages": messages,
            },
        )
        return messages


def build_azure_config() -> Dict[str, str]:
    tutor_model = os.getenv("GUIDED_REPLAY_TUTOR_MODEL", "gpt-5.4")
    reasoning_model = os.getenv("GUIDED_REPLAY_REASONING_MODEL", "gpt-5.4")
    return {
        "api_key": config.AZURE_OPENAI_SUBSCRIPTION_KEY,
        "endpoint": config.AZURE_OPENAI_ENDPOINT,
        "deployment_name": tutor_model,
        "tutor_deployment_name": tutor_model,
        "reasoning_deployment_name": reasoning_model,
        "api_version": config.AZURE_OPENAI_API_VERSION,
        "content_filter_policy": config.AZURE_OPENAI_CONTENT_FILTER_POLICY,
    }


def seed_saved_graph_content(
    *,
    system: InstrumentedSavedGraphTutor,
    session_id: str,
    objective_id: str,
    artifact: Dict[str, Any],
    teaching_content: str,
) -> None:
    graph = artifact["graph"]
    extracted_concepts = [
        {"id": node["id"], "label": node.get("label", node["id"])}
        for node in graph.get("nodes", [])
    ]
    system._session_cache.store(
        session_id,
        objective_id,
        artifact.get("objective_text", ""),
        [],
        "",
        teaching_content,
        retrieval_bundle=artifact,
    )
    system._session_cache.store_teaching_plan(
        session_id,
        graph,
        extracted_concepts=extracted_concepts,
    )


def compact_text(text: str, limit: int = 500) -> str:
    normalized = " ".join((text or "").split())
    return normalized if len(normalized) <= limit else normalized[: limit - 3] + "..."


def write_markdown_log(path: Path, payload: Dict[str, Any]) -> None:
    lines = [
        "# Saved-Graph Tutor Conversation",
        "",
        f"- Objective: {payload['objective_text']}",
        f"- Student turns: {len(payload['turns'])}",
        f"- Tutor model: {payload['models']['tutor']}",
        f"- Reasoning model: {payload['models']['reasoning']}",
        f"- Started: {payload['started_at']}",
        "",
    ]
    for turn in payload["turns"]:
        lines.extend(
            [
                f"## Turn {turn['turn']}",
                "",
                f"- Stage: {turn['stage_before']} -> {turn['stage_after']}",
                f"- Active graph node after: {turn.get('graph_state_after', {}).get('active_node_id', '')}",
                f"- Elapsed: {turn['elapsed_seconds']}s",
                "",
                "### Student",
                "",
                turn["student_message"],
                "",
                "### Tutor",
                "",
                turn["tutor_response"],
                "",
            ]
        )
        graph_decision = turn.get("graph_decision")
        if graph_decision:
            lines.extend(
                [
                    "### Graph Decision",
                    "",
                    "```json",
                    json.dumps(graph_decision, indent=2, ensure_ascii=True),
                    "```",
                    "",
                ]
            )
    path.write_text("\n".join(lines), encoding="utf-8")


async def generate_student_reply(
    *,
    client: AzureAPIMClient,
    objective_text: str,
    turn: int,
    tutor_response: str,
    history: List[Dict[str, str]],
) -> Dict[str, Any]:
    prompt = {
        "turn": turn,
        "objective": objective_text,
        "recent_history": history[-8:],
        "last_tutor_response": tutor_response,
        "task": "Write the next student reply only.",
    }
    messages = [
        {"role": "system", "content": STUDENT_SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(prompt, indent=2)},
    ]
    started = time.perf_counter()
    response = await asyncio.to_thread(
        client.chat,
        messages,
        0.7,
        450,
    )
    return {
        "messages": messages,
        "response": response.strip(),
        "elapsed_seconds": round(time.perf_counter() - started, 2),
    }


def extract_trace_event(trace: Dict[str, Any], name: str) -> Optional[Any]:
    for event in reversed(trace.get("events", [])):
        if event.get("name") == name:
            return event.get("payload")
    return None


async def run_conversation(args: argparse.Namespace) -> Dict[str, Any]:
    artifact = json.loads(Path(args.artifact).read_text(encoding="utf-8"))
    teaching_content = Path(args.content).read_text(encoding="utf-8")
    objective_text = artifact["objective_text"]
    objective_id = args.objective_id or "saved-non-text-content-objective"
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    student_id = f"saved-graph-student-{run_id}"
    session_id = f"saved-graph-session-{run_id}"

    student_service = InMemoryStudentService(
        student_id=student_id,
        session_id=session_id,
        objective_id=objective_id,
    )
    azure_config = build_azure_config()
    system = InstrumentedSavedGraphTutor(
        azure_config=azure_config,
        vector_store_service=NullVectorStore(),
        db_manager=NullDatabase(),
        wcag_mcp_client=None,
        student_mcp_client=student_service,
        objective_text=objective_text,
        objective_id=objective_id,
    )
    seed_saved_graph_content(
        system=system,
        session_id=session_id,
        objective_id=objective_id,
        artifact=artifact,
        teaching_content=teaching_content,
    )
    await system._session_state_repository.persist(session_id)

    student_client = AzureAPIMClient(
        endpoint=config.AZURE_OPENAI_ENDPOINT,
        deployment=os.getenv("GUIDED_REPLAY_STUDENT_MODEL", "gpt-5.4"),
        api_key=config.AZURE_OPENAI_SUBSCRIPTION_KEY,
        api_version=config.AZURE_OPENAI_API_VERSION,
        content_filter_policy=config.AZURE_OPENAI_CONTENT_FILTER_POLICY,
    )

    payload: Dict[str, Any] = {
        "run_id": run_id,
        "started_at": datetime.now().isoformat(),
        "artifact": str(Path(args.artifact)),
        "content": str(Path(args.content)),
        "objective_id": objective_id,
        "objective_text": objective_text,
        "student_id": student_id,
        "session_id": session_id,
        "models": {
            "tutor": azure_config["tutor_deployment_name"],
            "reasoning": azure_config["reasoning_deployment_name"],
            "student": student_client.deployment,
        },
        "turns": [],
    }

    student_message = (
        "I need to evaluate whether non-text content has good alternatives. "
        "I know images sometimes need alt text, but I am not sure how to decide "
        "what counts as good or when something should be ignored."
    )
    pending_student_generation: Optional[Dict[str, Any]] = None
    all_ws_events: List[Dict[str, Any]] = []

    async def ws_send(event: Dict[str, Any]) -> None:
        event_copy = copy.deepcopy(event)
        event_copy["_logged_at"] = datetime.now().isoformat()
        all_ws_events.append(event_copy)

    for turn in range(1, args.turns + 1):
        session_before = await student_service.get_active_session(student_id)
        stage_before = session_before.get("current_stage", "introduction")
        ws_start = len(all_ws_events)
        system.begin_turn_trace(
            turn=turn,
            student_message=student_message,
            stage_before=stage_before,
        )
        print(f"\nTURN {turn} | {stage_before}")
        print(f"STUDENT: {compact_text(student_message, 220)}")
        started = time.perf_counter()
        result = await system.conduct_guided_session_streaming(
            student_id=student_id,
            student_response=student_message,
            session_id=session_id,
            ws_send=ws_send,
        )
        elapsed = round(time.perf_counter() - started, 2)
        history = system.get_conversation_history(student_id)
        tutor_response = ""
        if history and history[-1].get("role") == "assistant":
            tutor_response = history[-1].get("content", "")
        session_after = await student_service.get_active_session(student_id)
        trace = system.get_turn_trace()
        graph_state_after = system._session_cache.get_graph_runtime_state(session_id)
        graph_decision = extract_trace_event(trace, "graph_orchestrator_output")
        turn_record = {
            "turn": turn,
            "student_message": student_message,
            "student_generation": copy.deepcopy(pending_student_generation),
            "tutor_response": tutor_response,
            "result_metadata": result,
            "stage_before": stage_before,
            "stage_after": session_after.get("current_stage", stage_before),
            "elapsed_seconds": elapsed,
            "ws_events": all_ws_events[ws_start:],
            "trace": trace,
            "lesson_state_after": system._session_cache.get_lesson_state(session_id),
            "pacing_state_after": system._session_cache.get_pacing_state(session_id),
            "misconception_state_after": system._session_cache.get_misconception_state(
                session_id
            ),
            "graph_state_after": graph_state_after,
            "graph_decision": graph_decision,
            "student_service_state_after": {
                "session": copy.deepcopy(student_service.session),
                "mastery": copy.deepcopy(student_service.mastery),
                "misconceptions": copy.deepcopy(student_service.misconceptions),
                "learner_memory": copy.deepcopy(student_service.learner_memory),
                "objective_memory": copy.deepcopy(student_service.objective_memory),
            },
        }
        payload["turns"].append(turn_record)
        print(f"TUTOR:   {compact_text(tutor_response, 260)}")
        if graph_decision:
            print(
                "GRAPH:   "
                f"{graph_decision.get('graph_action')} | "
                f"{graph_decision.get('active_node_id')} | "
                f"{graph_decision.get('allowed_teaching_move')}"
            )
        print(f"TIME:    {elapsed}s")

        if turn < args.turns:
            pending_student_generation = await generate_student_reply(
                client=student_client,
                objective_text=objective_text,
                turn=turn + 1,
                tutor_response=tutor_response,
                history=history,
            )
            student_message = pending_student_generation["response"]

    payload["ended_at"] = datetime.now().isoformat()
    payload["all_ws_events"] = all_ws_events
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", default=str(DEFAULT_ARTIFACT))
    parser.add_argument("--content", default=str(DEFAULT_RENDERED_CONTENT))
    parser.add_argument("--turns", type=int, default=14)
    parser.add_argument("--objective-id", default="")
    args = parser.parse_args()

    RESULTS_DIR.mkdir(exist_ok=True)
    payload = asyncio.run(run_conversation(args))
    output_base = RESULTS_DIR / f"saved_graph_tutor_conversation_{payload['run_id']}"
    json_path = output_base.with_suffix(".json")
    md_path = output_base.with_suffix(".md")
    json_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8"
    )
    write_markdown_log(md_path, payload)
    print("\nWrote logs:")
    print(f"- {json_path}")
    print(f"- {md_path}")


if __name__ == "__main__":
    main()
