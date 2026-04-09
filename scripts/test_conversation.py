#!/usr/bin/env python3
"""Run a full multi-turn conversation test with an LLM-driven student.

The student agent reads the tutor's response each turn and generates a
realistic reply — sometimes correct, sometimes with misconceptions,
sometimes asking for clarification.  This tests the tutor's ability to
adapt, not just follow a script.

Every intermediate artifact is captured: teaching plan, evidence pack,
turn analysis, lesson state patches, mastery signals, misconception log,
learner/objective memory, and the full conversation transcript.

Usage:
    poetry run python scripts/test_conversation.py [OBJECTIVE_ID] [MAX_TURNS]
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
os.chdir(PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv()

from question_app.core.config import config
from question_app.services.tutor.azure_client import AzureAPIMClient
from question_app.api.pg_vector_store import VectorStoreService
from question_app.services.wcag_mcp_client import WCAGMCPClient
from question_app.services.student_service import StudentService
from question_app.services.tutor.hybrid_system import HybridCrewAISocraticSystem

RESULTS_DIR = PROJECT_ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Student agent — LLM-driven, reads tutor output, responds realistically
# ---------------------------------------------------------------------------

STUDENT_SYSTEM_PROMPT = """\
You are a simulated student in a web accessibility tutoring session.
You are a frontend developer with intermediate JavaScript skills but
limited accessibility knowledge.  You've heard of ARIA but never
studied it formally.

Behavioral rules — follow these to create a realistic, rigorous test:

1. RESPOND TO WHAT THE TUTOR ACTUALLY SAID.  Read the tutor's message
   carefully and reply to their specific question or explanation.

2. Vary your response quality across turns to test the tutor:
   - Sometimes answer correctly and confidently.
   - Sometimes give a partial answer that's mostly right but missing a key detail.
   - Sometimes introduce a misconception (e.g., confuse ARIA with HTML semantics).
   - Sometimes ask a genuine clarification question about something you didn't understand.
   - Sometimes go slightly off-topic to test scope boundaries.
   - Occasionally try to summarize what you've learned so far.

3. Be natural.  Use casual language, make typos occasionally, show
   enthusiasm or confusion as appropriate.

4. Keep responses SHORT — 1-3 sentences typically.  Students don't write
   essays.

5. If the tutor asks you a specific question, ANSWER IT (correctly or
   incorrectly based on your simulated knowledge level).

6. If the tutor is teaching you something new, show engagement: ask a
   follow-up, connect it to something you know, or try to restate it.

7. Your knowledge should GROW over the conversation.  Early turns: more
   confusion and misconceptions.  Later turns: more correct answers and
   synthesis.

8. If the tutor asks an assessment question, give your best attempt
   based on what you've learned in the conversation.

You are NOT trying to be a perfect student.  You are trying to be a
REALISTIC student who tests the tutor's ability to handle varied inputs.\
"""


def pretty_json(obj, indent=2):
    def _default(o):
        return repr(o)
    return json.dumps(obj, indent=indent, default=_default, ensure_ascii=False)


class StudentAgent:
    """LLM-driven student that reads the conversation and responds."""

    def __init__(self, client: AzureAPIMClient, objective_text: str):
        self.client = client
        self.objective_text = objective_text
        self.conversation: list = []

    def generate_response(self, tutor_message: str, turn_num: int) -> str:
        """Generate a student response based on the tutor's message."""
        self.conversation.append({"role": "assistant", "content": tutor_message})

        # Build context with turn number so the student "grows"
        messages = [
            {"role": "system", "content": STUDENT_SYSTEM_PROMPT},
            {
                "role": "system",
                "content": (
                    f"Topic being taught: {self.objective_text}\n"
                    f"This is turn {turn_num} of the conversation.\n"
                    f"{'Early turns: be more confused, ask basic questions, make mistakes.' if turn_num <= 4 else ''}"
                    f"{'Mid turns: show growing understanding, still some gaps.' if 5 <= turn_num <= 8 else ''}"
                    f"{'Late turns: demonstrate good understanding, try to synthesize.' if turn_num > 8 else ''}"
                ),
            },
        ]
        # Add conversation history (tutor messages as "assistant", student as "user"
        # but from the student's perspective the tutor talks and student responds)
        for msg in self.conversation:
            if msg["role"] == "assistant":
                # Tutor's message — student sees it as incoming
                messages.append({"role": "user", "content": msg["content"]})
            else:
                # Student's own previous response
                messages.append({"role": "assistant", "content": msg["content"]})

        response = self.client.chat(messages, temperature=0.8, max_tokens=200)
        self.conversation.append({"role": "user", "content": response})
        return response

    def generate_first_message(self) -> str:
        """Generate the student's opening message."""
        messages = [
            {"role": "system", "content": STUDENT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"The tutor is about to teach you: {self.objective_text}\n"
                    "Generate your first message as the student. You're just "
                    "starting and don't know much about this topic yet. "
                    "Be eager but show your current (limited) understanding."
                ),
            },
        ]
        response = self.client.chat(messages, temperature=0.8, max_tokens=150)
        self.conversation.append({"role": "user", "content": response})
        return response


async def main():
    objective_id = sys.argv[1] if len(sys.argv) > 1 else "038d7bf5-eb16-4ac0-a22b-42c8fa964d97"
    max_turns = int(sys.argv[2]) if len(sys.argv) > 2 else 14

    student_id = f"test-conv-{datetime.now().strftime('%H%M%S')}"
    session_id = f"guided-test-{datetime.now().strftime('%H%M%S')}"

    # --- Init system ---
    azure_config = {
        "api_key": config.AZURE_OPENAI_SUBSCRIPTION_KEY,
        "endpoint": config.AZURE_OPENAI_ENDPOINT,
        "deployment_name": config.AZURE_OPENAI_DEPLOYMENT_ID,
        "tutor_deployment_name": config.AZURE_OPENAI_TUTOR_DEPLOYMENT_ID,
        "reasoning_deployment_name": config.AZURE_OPENAI_REASONING_DEPLOYMENT_ID,
        "api_version": config.AZURE_OPENAI_API_VERSION,
    }

    vector_service = VectorStoreService()
    azure_client = AzureAPIMClient(
        endpoint=azure_config["endpoint"],
        deployment=azure_config.get("reasoning_deployment_name") or azure_config["deployment_name"],
        api_key=azure_config["api_key"],
        api_version=azure_config.get("api_version", "2024-02-15-preview"),
    )
    wcag_mcp = WCAGMCPClient(command=config.WCAG_MCP_COMMAND, azure_client=azure_client) if config.WCAG_MCP_ENABLED else None
    student_service = StudentService() if config.STUDENT_MCP_ENABLED else None

    system = HybridCrewAISocraticSystem(
        azure_config=azure_config,
        vector_store_service=vector_service,
        wcag_mcp_client=wcag_mcp,
        student_mcp_client=student_service,
    )

    # Student agent uses the tutor (mini) client for speed
    student_agent_client = AzureAPIMClient(
        endpoint=azure_config["endpoint"],
        deployment=azure_config.get("tutor_deployment_name") or azure_config["deployment_name"],
        api_key=azure_config["api_key"],
        api_version=azure_config.get("api_version", "2024-02-15-preview"),
    )

    # --- Fetch objective ---
    objective = system._fetch_objective_by_id(objective_id)
    if not objective:
        print(f"Objective '{objective_id}' not found in DB.")
        sys.exit(1)
    objective_text = objective["text"]

    student_agent = StudentAgent(student_agent_client, objective_text)

    print(f"{'='*70}")
    print(f"CONVERSATION TEST (LLM-driven student)")
    print(f"Objective: {objective_text}")
    print(f"Student:   {student_id}")
    print(f"Session:   {session_id}")
    print(f"Max turns: {max_turns}")
    print(f"{'='*70}\n")

    # --- Create student profile + session ---
    await student_service.create_profile(
        student_id=student_id,
        technical_level="intermediate",
        a11y_exposure="awareness",
        role_context="frontend developer",
        learning_goal="job requirement",
    )
    await student_service.update_session_state(
        session_id,
        student_id=student_id,
        stage="introduction",
        active_objective_id=objective_id,
    )
    print("Created profile and session.\n")

    # --- Collectors ---
    all_turns = []
    all_ws_events = []

    async def ws_send(data: dict):
        data["_ts"] = datetime.now().isoformat()
        all_ws_events.append(data)

    # --- Generate first student message ---
    first_msg = await asyncio.to_thread(student_agent.generate_first_message)

    # --- Run conversation turn by turn ---
    student_msg = first_msg

    for turn_num in range(1, max_turns + 1):
        print(f"\n{'─'*70}")

        # Get current session state
        session_state = await student_service.get_active_session(student_id)
        current_stage = (session_state or {}).get("current_stage", "?")
        turns_on_obj = (session_state or {}).get("turns_on_objective", 0)

        print(f"TURN {turn_num} | Stage: {current_stage} | Turn on obj: {turns_on_obj}")
        print(f"STUDENT: {student_msg}")

        turn_data = {
            "turn": turn_num,
            "student_message": student_msg,
            "stage_before": current_stage,
            "turns_on_objective_before": turns_on_obj,
            "ws_events": [],
            "tutor_response": "",
            "timings": {},
        }

        # Capture WS events for this turn
        ws_start_idx = len(all_ws_events)

        # --- Run tutor turn ---
        t0 = time.perf_counter()
        try:
            result = await system.conduct_guided_session_streaming(
                student_id=student_id,
                student_response=student_msg,
                session_id=session_id,
                ws_send=ws_send,
            )
            turn_data["result_metadata"] = result
        except Exception as e:
            print(f"  ERROR: {e}")
            turn_data["error"] = str(e)
            import traceback
            turn_data["traceback"] = traceback.format_exc()

        turn_data["timings"]["tutor"] = round(time.perf_counter() - t0, 2)

        # Extract tutor response
        history = system.get_conversation_history(student_id)
        tutor_response = ""
        if history and history[-1].get("role") == "assistant":
            tutor_response = history[-1]["content"]
        turn_data["tutor_response"] = tutor_response

        # Capture this turn's WS events (skip tokens for storage)
        turn_ws_events = [
            e for e in all_ws_events[ws_start_idx:]
            if e.get("type") != "token"
        ]
        turn_data["ws_events"] = turn_ws_events

        # Get post-turn state snapshots
        post_session = await student_service.get_active_session(student_id)
        turn_data["stage_after"] = (post_session or {}).get("current_stage", "?")
        turn_data["turns_on_objective_after"] = (post_session or {}).get("turns_on_objective", 0)
        turn_data["session_state_after"] = post_session

        import copy
        lesson_state = system._session_cache.get_lesson_state(session_id)
        turn_data["lesson_state_snapshot"] = copy.deepcopy(lesson_state)

        mastery = await student_service.get_mastery_state(student_id)
        turn_data["mastery_snapshot"] = mastery

        misconceptions = await student_service.get_misconception_patterns(student_id)
        turn_data["misconceptions_snapshot"] = misconceptions

        objective_mem = await student_service.get_objective_memory(student_id, objective_id)
        turn_data["objective_memory_snapshot"] = objective_mem

        learner_mem = await student_service.get_learner_memory(student_id)
        turn_data["learner_memory_snapshot"] = learner_mem

        all_turns.append(turn_data)

        # Print summary
        print(f"\nTUTOR: {tutor_response[:200]}{'...' if len(tutor_response) > 200 else ''}")
        print(f"  Time: {turn_data['timings']['tutor']}s | Stage: {turn_data['stage_before']} → {turn_data['stage_after']}")

        if lesson_state and lesson_state.get("concepts"):
            active = lesson_state.get("active_concept", "?")
            covered = sum(1 for c in lesson_state.get("concepts", []) if c.get("status") == "covered")
            total = len(lesson_state.get("concepts", []))
            print(f"  Concepts: {covered}/{total} covered | Active: {active}")

        if misconceptions:
            print(f"  Misconceptions: {len(misconceptions)} active")

        # --- Generate next student message ---
        if turn_num < max_turns and tutor_response:
            t0 = time.perf_counter()
            student_msg = await asyncio.to_thread(
                student_agent.generate_response, tutor_response, turn_num + 1,
            )
            turn_data["timings"]["student_agent"] = round(time.perf_counter() - t0, 2)
        else:
            break

    # ===================================================================
    # Write comprehensive results
    # ===================================================================
    print(f"\n{'='*70}")
    print("Writing results ...")

    # Collect final state
    final_session = await student_service.get_active_session(student_id)
    final_mastery = await student_service.get_mastery_state(student_id)
    final_misconceptions = await student_service.get_misconception_patterns(student_id)
    final_lesson_state = system._session_cache.get_lesson_state(session_id)
    final_learner_memory = await student_service.get_learner_memory(student_id)
    final_objective_memory = await student_service.get_objective_memory(student_id, objective_id)
    teaching_plan = system._session_cache.get_teaching_plan(session_id)
    teaching_content = system._session_cache.get_teaching_content(session_id)
    retrieval_bundle = system._session_cache.get_retrieval_bundle(session_id)
    slim_payload = system._session_cache.export_session(session_id)

    lines = []
    lines.append(f"# Conversation Test: {objective_text}")
    lines.append(f"\n**Objective ID**: `{objective_id}`")
    lines.append(f"**Student**: `{student_id}` (LLM-driven agent)")
    lines.append(f"**Session**: `{session_id}`")
    lines.append(f"**Run at**: {datetime.now().isoformat()}")
    lines.append(f"**Total turns**: {len(all_turns)}")
    total_time = sum(t.get("timings", {}).get("tutor", 0) for t in all_turns)
    lines.append(f"**Total tutor time**: {round(total_time, 1)}s")

    # --- Pipeline artifacts ---
    lines.append(f"\n---\n\n## Pipeline Artifacts\n")

    lines.append(f"### Teaching Plan ({len(str(teaching_plan))} chars)\n")
    lines.append("```")
    lines.append(str(teaching_plan) if teaching_plan else "(none)")
    lines.append("```")

    lines.append(f"\n### Evidence Pack ({len(teaching_content)} chars)\n")
    lines.append("````markdown")
    lines.append(teaching_content if teaching_content else "(none)")
    lines.append("````")

    if retrieval_bundle:
        lines.append(f"\n### Retrieval Bundle Coverage\n")
        lines.append("```json")
        lines.append(pretty_json(retrieval_bundle.get("coverage", {})))
        lines.append("```")

        lines.append(f"\n### Retrieval Bundle Sections\n")
        for section_name, items in retrieval_bundle.get("sections", {}).items():
            if items:
                lines.append(f"**{section_name}** ({len(items)} items):")
                for item in items:
                    lines.append(f"- `{item.get('source_tool', '?')}` → {item.get('title', '?')} ({len(item.get('content', ''))} chars)")
                lines.append("")

    lines.append(f"\n### Lesson State (initial)\n")
    initial_ls = all_turns[0].get("lesson_state_snapshot", {}) if all_turns else {}
    lines.append("```json")
    lines.append(pretty_json(initial_ls))
    lines.append("```")

    if slim_payload:
        lines.append(f"\n### Slim Persisted Payload\n")
        lines.append("| Field | Size |")
        lines.append("|-------|------|")
        for key, val in slim_payload.items():
            size = len(json.dumps(val, default=repr)) if val else 0
            lines.append(f"| `{key}` | {size} bytes |")

    # --- Turn-by-turn log ---
    lines.append(f"\n---\n\n## Turn-by-Turn Log\n")

    for turn in all_turns:
        tn = turn["turn"]
        lines.append(f"### Turn {tn}: {turn['stage_before']} → {turn['stage_after']}")
        lines.append(f"**Tutor time**: {turn['timings'].get('tutor', '?')}s | "
                      f"**Student agent time**: {turn['timings'].get('student_agent', '-')}s | "
                      f"**Turns on obj**: {turn.get('turns_on_objective_before', '?')} → {turn.get('turns_on_objective_after', '?')}")
        lines.append("")

        lines.append(f"**Student**:")
        lines.append(f"> {turn['student_message']}")
        lines.append("")

        lines.append(f"**Tutor**:")
        lines.append(f"> {turn.get('tutor_response', '(no response)')}")
        lines.append("")

        # WS events
        ws_events = turn.get("ws_events", [])
        if ws_events:
            lines.append("<details><summary>WebSocket Events ({} non-token)</summary>\n".format(len(ws_events)))
            lines.append("```json")
            lines.append(pretty_json(ws_events))
            lines.append("```\n</details>\n")

        # Lesson state
        ls = turn.get("lesson_state_snapshot")
        if ls and ls.get("concepts"):
            active = ls.get("active_concept", "?")
            concept_lines = []
            for c in ls.get("concepts", []):
                marker = {"covered": "done", "in_progress": "wip", "partially_covered": "partial"}.get(c["status"], "todo")
                concept_lines.append(f"`{c['id']}` [{marker}]")
            lines.append(f"**Lesson State**: active=`{active}`")
            lines.append(f"  {', '.join(concept_lines)}")
            lines.append("")

        # Misconceptions
        misconceptions = turn.get("misconceptions_snapshot")
        if misconceptions:
            lines.append(f"**Active Misconceptions** ({len(misconceptions)}):")
            for m in misconceptions:
                resolved = "resolved" if m.get("resolved_at") else "active"
                lines.append(f"- [{resolved}] {m.get('misconception_text', '?')}")
            lines.append("")

        # Mastery
        mastery = turn.get("mastery_snapshot")
        if mastery:
            for m in mastery:
                if m.get("objective_id") == objective_id:
                    lines.append(f"**Mastery**: level=`{m.get('mastery_level', '?')}` confidence={m.get('confidence', '?')}")
            lines.append("")

        # Objective memory (show diffs across turns)
        obj_mem = turn.get("objective_memory_snapshot")
        if obj_mem:
            lines.append("<details><summary>Objective Memory</summary>\n")
            lines.append("```json")
            lines.append(pretty_json(obj_mem))
            lines.append("```\n</details>\n")

        # Learner memory
        lrn_mem = turn.get("learner_memory_snapshot")
        if lrn_mem:
            lines.append("<details><summary>Learner Memory</summary>\n")
            lines.append("```json")
            lines.append(pretty_json(lrn_mem))
            lines.append("```\n</details>\n")

        if turn.get("error"):
            lines.append(f"**ERROR**: `{turn['error']}`")
            lines.append(f"```\n{turn.get('traceback', '')}\n```")

        lines.append("---\n")

    # --- Final state ---
    lines.append("## Final State\n")

    lines.append("### Session State\n```json")
    lines.append(pretty_json(final_session))
    lines.append("```\n")

    lines.append("### Mastery\n```json")
    lines.append(pretty_json(final_mastery))
    lines.append("```\n")

    lines.append("### Misconceptions\n```json")
    lines.append(pretty_json(final_misconceptions))
    lines.append("```\n")

    lines.append("### Lesson State (final)\n```json")
    lines.append(pretty_json(final_lesson_state))
    lines.append("```\n")

    lines.append("### Learner Memory\n```json")
    lines.append(pretty_json(final_learner_memory))
    lines.append("```\n")

    lines.append("### Objective Memory\n```json")
    lines.append(pretty_json(final_objective_memory))
    lines.append("```\n")

    # --- Full conversation transcript ---
    lines.append("---\n\n## Full Conversation Transcript\n")
    final_history = system.get_conversation_history(student_id)
    for i, msg in enumerate(final_history):
        role = msg.get("role", "?").upper()
        content = msg.get("content", "")
        lines.append(f"**{role}** (msg {i+1}):\n> {content}\n")

    result_path = RESULTS_DIR / "3_conversation_test.md"
    result_path.write_text("\n".join(lines), encoding="utf-8")
    size_kb = result_path.stat().st_size / 1024
    print(f"Written to {result_path} ({len(lines)} lines, {size_kb:.0f} KB)")

    # Also dump raw JSON for programmatic access
    raw_path = RESULTS_DIR / "3_conversation_test_raw.json"
    raw_data = {
        "objective_id": objective_id,
        "objective_text": objective_text,
        "student_id": student_id,
        "session_id": session_id,
        "turns": all_turns,
        "final_state": {
            "session": final_session,
            "mastery": final_mastery,
            "misconceptions": final_misconceptions,
            "lesson_state": final_lesson_state,
            "learner_memory": final_learner_memory,
            "objective_memory": final_objective_memory,
        },
        "pipeline": {
            "teaching_plan": str(teaching_plan) if teaching_plan else None,
            "teaching_content": teaching_content,
            "retrieval_bundle_coverage": retrieval_bundle.get("coverage") if retrieval_bundle else None,
        },
    }
    raw_path.write_text(pretty_json(raw_data), encoding="utf-8")
    print(f"Written to {raw_path} (raw JSON)")

    # Cleanup
    if wcag_mcp:
        try:
            await wcag_mcp.close()
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
