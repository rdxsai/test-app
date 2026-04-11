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
import copy
import json
import os
import re
import sys
import time
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

Behavioral rules — follow these to create a RIGOROUS, CHALLENGING test:

1. RESPOND TO WHAT THE TUTOR ACTUALLY SAID.  Read the tutor's message
   carefully and reply to their specific question or explanation.

2. You MUST vary your response quality to stress-test the tutor's
   adaptive pacing.  Follow this pattern strictly:
   - Turns 1-3: Be genuinely confused.  Give wrong answers, say "I don't
     know", or mix up concepts.  Force the tutor to slow down.
   - Turns 4-5: Start to get it but still make mistakes.  Give partial
     answers with one wrong detail.
   - Turns 6-8: Show growing understanding.  Answer mostly correctly but
     ask clarification questions about edge cases.
   - Turns 9-11: Answer confidently and correctly.  Apply concepts to
     new examples.  Show transfer reasoning.  Force the tutor to speed up.
   - Turns 12-15: If not in assessment yet, surface one procedural mistake
     where you stop at a local check instead of applying the full checklist.
   - After the tutor repairs that procedural mistake, do the full walkthrough
     on the same snippet and then apply it to one fresh example.
   - During assessment, give your best answer, but occasionally get one wrong
     to test how the tutor handles it.

3. CHALLENGE THE TUTOR specifically:
   - At least once, give a WRONG answer confidently (misconception test)
   - At least once, say "I don't get it" or "can you explain that differently?"
   - At least once, ask about something adjacent but off-topic
   - At least once, try to summarize everything and get a detail wrong

4. Keep responses SHORT — 1-3 sentences.  Students don't write essays.

5. Be natural.  Use casual language.  Show frustration when confused,
   excitement when things click.

6. If the tutor asks an assessment question, give your best attempt
   but you're allowed to get ~30% wrong.

You are testing whether the tutor can ADAPT its pace — slowing down when
you struggle, speeding up when you're clearly getting it.\
"""


def pretty_json(obj, indent=2):
    def _default(o):
        return repr(o)
    return json.dumps(obj, indent=indent, default=_default, ensure_ascii=False)


def short_text(text: str, limit: int = 220) -> str:
    text = (text or "").strip().replace("\n", " ")
    return text if len(text) <= limit else text[: limit - 3] + "..."


def next_result_number(results_dir: Path) -> int:
    numbered = []
    pattern = re.compile(r"^(\d+)_conversation_test\.md$")
    for path in results_dir.glob("*_conversation_test.md"):
        match = pattern.match(path.name)
        if match:
            numbered.append(int(match.group(1)))
    return (max(numbered) + 1) if numbered else 1


def collect_run_diagnostics(turns: List[Dict[str, Any]], final_session: Dict[str, Any]) -> Dict[str, Any]:
    stage_sequence: List[str] = []
    procedural_repair_turns: List[int] = []
    procedural_resolution_turns: List[int] = []
    assessment_turns: List[int] = []
    readiness_turns: List[int] = []

    def _append_stage(stage: str) -> None:
        normalized = str(stage or "").strip()
        if normalized and normalized not in stage_sequence:
            stage_sequence.append(normalized)

    for turn in turns:
        _append_stage(turn.get("stage_before", ""))
        _append_stage(turn.get("stage_after", ""))
        if turn.get("stage_before") == "readiness_check" or turn.get("stage_after") == "readiness_check":
            readiness_turns.append(turn.get("turn"))
        if turn.get("stage_before") in {"mini_assessment", "final_assessment"} or turn.get("stage_after") in {"mini_assessment", "final_assessment"}:
            assessment_turns.append(turn.get("turn"))

        trace = (turn.get("internal_trace") or {}).get("events", []) or []
        for event in trace:
            payload = event.get("payload") or {}
            if event.get("name") not in {"turn_analysis", "assessment_reflection"}:
                continue
            for item in payload.get("misconception_events", []) or []:
                if not isinstance(item, dict):
                    continue
                scope = str(item.get("repair_scope", "") or "")
                pattern = str(item.get("repair_pattern", "") or "")
                if scope == "full_sequence" or pattern == "same_snippet_walkthrough":
                    if turn.get("turn") not in procedural_repair_turns:
                        procedural_repair_turns.append(turn.get("turn"))
                    if str(item.get("action", "") or "") == "resolve_candidate":
                        if turn.get("turn") not in procedural_resolution_turns:
                            procedural_resolution_turns.append(turn.get("turn"))

    _append_stage((final_session or {}).get("current_stage", ""))
    return {
        "stages_reached": stage_sequence,
        "readiness_turns": readiness_turns,
        "assessment_turns": assessment_turns,
        "procedural_repair_turns": procedural_repair_turns,
        "procedural_resolution_turns": procedural_resolution_turns,
    }


class StudentProbeScenario:
    """Turn planner for a richer, more diagnostic student simulation."""

    TARGETS: Dict[str, Dict[str, Any]] = {
        "baseline_confusion": {
            "label": "Baseline confusion",
            "instruction": (
                "Be genuinely unsure about the concept. Answer briefly, but show that you do not yet "
                "have a stable mental model."
            ),
            "validator": [r"\b(not sure|don't know|i guess|maybe|i think)\b"],
            "retry_on_fail": False,
        },
        "explicit_slow_down": {
            "label": "Explicit slow-down request",
            "instruction": (
                "Tell the tutor you are lost or that they are moving too fast. Ask them to slow down "
                "or explain it differently while still engaging with the topic."
            ),
            "validator": [r"\bslow\b", r"\bexplain (that )?differently\b", r"\b(i'?m|i am) lost\b", r"\bdon't get it\b"],
            "retry_on_fail": True,
        },
        "confident_misconception": {
            "label": "Confident misconception",
            "instruction": (
                "Give a concise but confidently stated wrong interpretation of the tutor's point. "
                "Do not hedge too much."
            ),
            "validator": [r"\b(definitely|pretty sure|basically|so that means)\b"],
            "retry_on_fail": False,
        },
        "partial_with_error": {
            "label": "Partial understanding with one wrong detail",
            "instruction": (
                "Show partial understanding, but include one detail that is still wrong or incomplete."
            ),
            "validator": [r"\b(i think|maybe|so)\b"],
            "retry_on_fail": False,
        },
        "ask_for_example": {
            "label": "Ask for a concrete example",
            "instruction": (
                "Ask the tutor for a concrete example, snippet, or comparison to make the concept clearer."
            ),
            "validator": [r"\bexample\b", r"\bsnippet\b", r"\bshow me\b", r"\bconcrete\b"],
            "retry_on_fail": True,
        },
        "adjacent_topic": {
            "label": "Adjacent-topic detour",
            "instruction": (
                "Ask one adjacent accessibility question that is related but not the exact current objective. "
                "Examples: keyboard accessibility, color contrast, screen readers, headings."
            ),
            "validator": [r"\b(keyboard|contrast|screen reader|heading|focus)\b"],
            "retry_on_fail": True,
        },
        "rephrase_request": {
            "label": "Ask for rephrasing",
            "instruction": (
                "Say the tutor's explanation did not fully click and ask for a simpler rephrase."
            ),
            "validator": [r"\brephrase\b", r"\bsimpler\b", r"\bplain english\b", r"\bexplain (it )?another way\b"],
            "retry_on_fail": True,
        },
        "transfer_reasoning": {
            "label": "Transfer to a nearby example",
            "instruction": (
                "Apply the concept to a fresh but nearby case and reason it through briefly."
            ),
            "validator": [r"\blike if\b", r"\bfor example\b", r"\bif i had\b", r"\bso in a\b"],
            "retry_on_fail": False,
        },
        "meta_faster": {
            "label": "Meta request to move faster",
            "instruction": (
                "Tell the tutor this part now makes sense and ask if they can move a little faster or test you."
            ),
            "validator": [r"\bfaster\b", r"\bmove on\b", r"\btest me\b", r"\bskip ahead\b"],
            "retry_on_fail": True,
        },
        "bad_summary": {
            "label": "Summary with one wrong detail",
            "instruction": (
                "Try to summarize the rule so far in your own words, but include one detail that is slightly wrong."
            ),
            "validator": [r"\bso basically\b", r"\bso the rule is\b", r"\bi think the idea is\b"],
            "retry_on_fail": False,
        },
        "strong_transfer": {
            "label": "Strong transfer reasoning",
            "instruction": (
                "Answer confidently and apply the concept to a new example with clear cause-and-effect reasoning."
            ),
            "validator": [r"\bbecause\b", r"\bwould\b", r"\bif\b"],
            "retry_on_fail": False,
        },
        "procedural_misconception": {
            "label": "Procedural misconception",
            "instruction": (
                "Answer as if one local ARIA check is enough. Do not walk the whole checklist. "
                "For example, stop at role/state validity and skip behavior or focus."
            ),
            "validator": [r"\b(just|only)\b", r"\b(role|aria-|state)\b"],
            "retry_on_fail": True,
        },
        "post_repair_walkthrough": {
            "label": "Post-repair same-snippet walkthrough",
            "instruction": (
                "Follow the tutor's repaired checklist on the SAME snippet in order. Explicitly walk native-first, "
                "semantic override, behavior, focus, and required state/property."
            ),
            "validator": [
                r"\bnative\b",
                r"\bbehavior\b",
                r"\bfocus\b",
                r"\b(role|state|aria-)\b",
            ],
            "retry_on_fail": True,
        },
        "post_repair_transfer": {
            "label": "Post-repair transfer",
            "instruction": (
                "Now apply the repaired full checklist to one fresh example and reason briefly why."
            ),
            "validator": [r"\bif i had\b", r"\bfor example\b", r"\bbecause\b", r"\bwould\b"],
            "retry_on_fail": False,
        },
        "assessment_best_effort": {
            "label": "Assessment best effort",
            "instruction": (
                "Give your best direct answer to the assessment question. Be concise and committed."
            ),
            "validator": [],
            "retry_on_fail": False,
        },
        "assessment_incorrect": {
            "label": "Assessment miss",
            "instruction": (
                "Give your best attempt, but allow one plausible mistake so we can test the tutor's recovery."
            ),
            "validator": [],
            "retry_on_fail": False,
        },
    }

    PHASES = [
        {
            "name": "destabilize",
            "start": 1,
            "end": 3,
            "default_target": "baseline_confusion",
            "priority_targets": [
                "baseline_confusion",
                "explicit_slow_down",
                "confident_misconception",
            ],
            "goal": "Force the tutor to slow down and re-scaffold.",
        },
        {
            "name": "repair",
            "start": 4,
            "end": 6,
            "default_target": "partial_with_error",
            "priority_targets": [
                "partial_with_error",
                "ask_for_example",
                "rephrase_request",
            ],
            "goal": "Show partial recovery but still surface unstable understanding.",
        },
        {
            "name": "variation",
            "start": 7,
            "end": 9,
            "default_target": "transfer_reasoning",
            "priority_targets": [
                "adjacent_topic",
                "transfer_reasoning",
                "bad_summary",
            ],
            "goal": "Test routing, clarification, and recovery from mixed-quality reasoning.",
        },
        {
            "name": "acceleration",
            "start": 10,
            "end": 12,
            "default_target": "strong_transfer",
            "priority_targets": [
                "meta_faster",
                "strong_transfer",
                "bad_summary",
            ],
            "goal": "Create evidence that the tutor can now safely speed up.",
        },
        {
            "name": "late_repair",
            "start": 13,
            "end": 15,
            "default_target": "procedural_misconception",
            "priority_targets": [
                "procedural_misconception",
                "post_repair_walkthrough",
            ],
            "goal": "Trigger a late procedural repair about applying the full checklist.",
        },
        {
            "name": "post_repair_validation",
            "start": 16,
            "end": 18,
            "default_target": "post_repair_transfer",
            "priority_targets": [
                "post_repair_walkthrough",
                "post_repair_transfer",
                "meta_faster",
            ],
            "goal": "Verify the repair holds on the same snippet and then on transfer.",
        },
        {
            "name": "readiness_push",
            "start": 19,
            "end": 24,
            "default_target": "strong_transfer",
            "priority_targets": [
                "post_repair_transfer",
                "meta_faster",
                "strong_transfer",
            ],
            "goal": "Keep moving until readiness and assessment are exercised.",
        },
    ]

    def __init__(self, objective_text: str):
        self.objective_text = objective_text
        self.completed_targets: List[str] = []
        self.turn_plans: List[Dict[str, Any]] = []

    def _phase_for_turn(self, turn_num: int, current_stage: str) -> Dict[str, Any]:
        if current_stage in {"mini_assessment", "final_assessment"}:
            return {
                "name": "assessment",
                "default_target": "assessment_best_effort",
                "priority_targets": [
                    "assessment_incorrect",
                    "assessment_best_effort",
                ],
                "goal": "Test answer evaluation and assessment recovery.",
            }
        for phase in self.PHASES:
            if phase["start"] <= turn_num <= phase["end"]:
                return phase
        return self.PHASES[-1]

    @staticmethod
    def _tutor_requests_full_walkthrough(tutor_message: str) -> bool:
        text = (tutor_message or "").lower()
        patterns = (
            r"walk .* through",
            r"same snippet",
            r"in order",
            r"full checklist",
            r"native-first",
            r"native first",
            r"behavior",
            r"required state",
        )
        return any(re.search(pattern, text) for pattern in patterns)

    def build_turn_plan(
        self,
        turn_num: int,
        current_stage: str,
        tutor_message: str = "",
    ) -> Dict[str, Any]:
        phase = self._phase_for_turn(turn_num, current_stage)
        target = phase["default_target"]
        for candidate in phase.get("priority_targets", []):
            if candidate not in self.completed_targets:
                target = candidate
                break

        if (
            current_stage not in {"mini_assessment", "final_assessment"}
            and self._tutor_requests_full_walkthrough(tutor_message)
            and "post_repair_walkthrough" not in self.completed_targets
        ):
            target = "post_repair_walkthrough"
        elif (
            current_stage == "readiness_check"
            and "post_repair_transfer" not in self.completed_targets
        ):
            target = "post_repair_transfer"

        target_info = self.TARGETS[target]
        directive = (
            f"Probe phase: {phase['name']}. Goal: {phase['goal']}\n"
            f"Primary target: {target_info['label']}.\n"
            f"{target_info['instruction']}\n"
            "Always respond to what the tutor actually just said. Keep it to 1-3 sentences."
        )
        plan = {
            "turn": turn_num,
            "stage": current_stage,
            "phase": phase["name"],
            "phase_goal": phase["goal"],
            "target": target,
            "target_label": target_info["label"],
            "directive": directive,
            "retry_on_fail": bool(target_info.get("retry_on_fail")),
            "validator_patterns": list(target_info.get("validator", [])),
            "tutor_message_excerpt": short_text(tutor_message),
        }
        self.turn_plans.append(copy.deepcopy(plan))
        return plan

    def validate_response(self, plan: Dict[str, Any], response: str) -> Dict[str, Any]:
        patterns = plan.get("validator_patterns", []) or []
        if not patterns:
            passed = True
            matched = []
        else:
            matched = [
                pattern for pattern in patterns
                if re.search(pattern, response or "", re.IGNORECASE)
            ]
            passed = bool(matched)

        if passed and plan.get("target") not in self.completed_targets:
            self.completed_targets.append(plan["target"])

        return {
            "passed": passed,
            "matched_patterns": matched,
        }

    def summary(self) -> Dict[str, Any]:
        remaining = [
            key for key in self.TARGETS.keys()
            if key not in self.completed_targets
        ]
        return {
            "completed_targets": list(self.completed_targets),
            "remaining_targets": remaining,
            "turn_plans": copy.deepcopy(self.turn_plans),
        }


class StudentAgent:
    """LLM-driven student that reads the conversation and responds."""

    def __init__(self, client: AzureAPIMClient, objective_text: str):
        self.client = client
        self.objective_text = objective_text
        self.conversation: list = []

    def _phase_hint(self, turn_num: int, current_stage: str) -> str:
        if current_stage in {"mini_assessment", "final_assessment"}:
            return "ASSESSMENT PHASE: answer directly, but occasional mistakes are allowed."
        if turn_num <= 3:
            return "CONFUSED PHASE: be confused, mix things up, and force the tutor to slow down."
        if 4 <= turn_num <= 6:
            return "REPAIR PHASE: show partial understanding, but still make at least one mistake or ask for more support."
        if 7 <= turn_num <= 9:
            return "VARIATION PHASE: start connecting ideas, ask edge-case or adjacent questions, and test the tutor's routing."
        if 10 <= turn_num <= 12:
            return "ACCELERATION PHASE: respond confidently, transfer to new examples, and sometimes ask the tutor to move faster."
        return "LATE PHASE: answer naturally based on the tutor's latest response."

    def _build_messages(
        self,
        turn_num: int,
        current_stage: str,
        directive: str,
        tutor_message: str = "",
        retry_note: str = "",
        opening: bool = False,
    ) -> List[Dict[str, str]]:
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": STUDENT_SYSTEM_PROMPT},
            {
                "role": "system",
                "content": (
                    f"Topic being taught: {self.objective_text}\n"
                    f"This is turn {turn_num} of the conversation.\n"
                    f"Current tutor stage: {current_stage}\n"
                    f"{self._phase_hint(turn_num, current_stage)}\n"
                    f"Turn directive:\n{directive}\n"
                    f"{retry_note}"
                ).strip(),
            },
        ]

        if opening:
            messages.append(
                {
                    "role": "user",
                    "content": (
                        f"The tutor is about to teach you: {self.objective_text}\n"
                        "Generate your first message as the student. You're just "
                        "starting and don't know much about this topic yet. "
                        "Be eager but show your current limited understanding."
                    ),
                }
            )
            return messages

        self.conversation.append({"role": "assistant", "content": tutor_message})
        for msg in self.conversation:
            if msg["role"] == "assistant":
                messages.append({"role": "user", "content": msg["content"]})
            else:
                messages.append({"role": "assistant", "content": msg["content"]})
        return messages

    def _generate_with_trace(
        self,
        *,
        turn_num: int,
        current_stage: str,
        directive_plan: Dict[str, Any],
        tutor_message: str = "",
        opening: bool = False,
    ) -> Dict[str, Any]:
        attempts: List[Dict[str, Any]] = []
        final_response = ""

        for attempt_num in range(1, 3):
            retry_note = ""
            if attempt_num > 1:
                retry_note = (
                    "The previous reply missed the requested probe behavior. Keep the same topic response, "
                    "but satisfy the directive more explicitly."
                )

            messages = self._build_messages(
                turn_num=turn_num,
                current_stage=current_stage,
                directive=directive_plan["directive"],
                tutor_message=tutor_message,
                retry_note=retry_note,
                opening=opening,
            )
            response = self.client.chat(
                messages, temperature=0.8, max_tokens=200 if not opening else 150
            )
            validation = directive_plan["scenario"].validate_response(
                directive_plan, response
            )
            attempts.append(
                {
                    "attempt": attempt_num,
                    "response": response,
                    "validation": validation,
                    "messages_used": len(messages),
                    "retry_note": retry_note,
                }
            )
            final_response = response

            if validation["passed"] or not directive_plan.get("retry_on_fail"):
                break

            if not opening and self.conversation and self.conversation[-1].get("role") == "assistant":
                self.conversation.pop()

        self.conversation.append({"role": "user", "content": final_response})
        return {
            "response": final_response,
            "directive_plan": {
                key: value
                for key, value in directive_plan.items()
                if key != "scenario"
            },
            "attempts": attempts,
        }

    def generate_response(
        self,
        tutor_message: str,
        turn_num: int,
        current_stage: str,
        directive_plan: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate a student response based on the tutor's message."""
        return self._generate_with_trace(
            turn_num=turn_num,
            current_stage=current_stage,
            directive_plan=directive_plan,
            tutor_message=tutor_message,
            opening=False,
        )

    def generate_first_message(
        self,
        turn_num: int,
        current_stage: str,
        directive_plan: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate the student's opening message."""
        return self._generate_with_trace(
            turn_num=turn_num,
            current_stage=current_stage,
            directive_plan=directive_plan,
            opening=True,
        )


class InstrumentedHybridCrewAISocraticSystem(HybridCrewAISocraticSystem):
    """Guided tutor with per-turn internal artifact capture for analysis."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._current_turn_trace: Dict[str, Any] = {}

    def begin_turn_trace(
        self,
        turn_num: int,
        student_message: str,
        stage_before: str,
    ) -> None:
        self._current_turn_trace = {
            "turn": turn_num,
            "student_message": student_message,
            "stage_before": stage_before,
            "events": [],
            "timings": {},
        }

    def get_turn_trace(self) -> Dict[str, Any]:
        return copy.deepcopy(self._current_turn_trace)

    def _record_trace_event(self, name: str, payload: Dict[str, Any]) -> None:
        self._current_turn_trace.setdefault("events", []).append(
            {"name": name, "payload": copy.deepcopy(payload)}
        )

    async def _run_turn_analyzer(self, *args, **kwargs):
        history = kwargs.get("history") or []
        student_response = kwargs.get("student_response", "")
        lesson_state = kwargs.get("lesson_state")
        pacing_state = kwargs.get("pacing_state")
        start = time.perf_counter()
        self._record_trace_event(
            "turn_analyzer_input",
            {
                "current_stage": kwargs.get("current_stage"),
                "active_objective": kwargs.get("active_objective"),
                "lesson_state_before": copy.deepcopy(lesson_state),
                "pacing_state_before": copy.deepcopy(pacing_state),
                "transcript": self._format_reflection_transcript(history, student_response),
            },
        )
        result = await super()._run_turn_analyzer(*args, **kwargs)
        self._current_turn_trace.setdefault("timings", {})["turn_analyzer"] = round(
            time.perf_counter() - start, 2
        )
        self._record_trace_event("turn_analysis", result)
        return result

    async def _run_assessment_reflector(self, *args, **kwargs):
        history = kwargs.get("history") or []
        student_response = kwargs.get("student_response", "")
        start = time.perf_counter()
        self._record_trace_event(
            "assessment_reflector_input",
            {
                "current_stage": kwargs.get("current_stage"),
                "active_objective": kwargs.get("active_objective"),
                "transcript": self._format_reflection_transcript(history, student_response),
            },
        )
        result = await super()._run_assessment_reflector(*args, **kwargs)
        self._current_turn_trace.setdefault("timings", {})[
            "assessment_reflector"
        ] = round(time.perf_counter() - start, 2)
        self._record_trace_event("assessment_reflection", result)
        return result

    def _build_guided_tutor_messages(self, *args, **kwargs):
        messages = super()._build_guided_tutor_messages(*args, **kwargs)
        system_blocks = [
            m["content"] for m in messages
            if m.get("role") == "system"
        ]
        self._record_trace_event(
            "tutor_message_build",
            {
                "message_count": len(messages),
                "system_block_count": len(system_blocks),
                "system_block_char_counts": [len(block) for block in system_blocks],
                "turn_analysis_block": next(
                    (block for block in system_blocks if block.startswith("TURN ANALYSIS:")),
                    "",
                ),
                "adaptive_pacing_block": next(
                    (block for block in system_blocks if block.startswith("ADAPTIVE PACING:")),
                    "",
                ),
                "extra_system_blocks": [
                    block for block in system_blocks
                    if not block.startswith("TURN ANALYSIS:")
                    and not block.startswith("ADAPTIVE PACING:")
                ][1:],
            },
        )
        return messages

    async def _apply_turn_analysis_updates(self, *args, **kwargs):
        start = time.perf_counter()
        self._record_trace_event(
            "apply_turn_analysis_updates_input",
            {"analysis": copy.deepcopy(kwargs.get("analysis", {}))},
        )
        result = await super()._apply_turn_analysis_updates(*args, **kwargs)
        self._current_turn_trace.setdefault("timings", {})[
            "apply_turn_analysis_updates"
        ] = round(time.perf_counter() - start, 2)
        self._record_trace_event("apply_turn_analysis_updates_result", result)
        return result


async def main():
    objective_id = sys.argv[1] if len(sys.argv) > 1 else "038d7bf5-eb16-4ac0-a22b-42c8fa964d97"
    max_turns = int(sys.argv[2]) if len(sys.argv) > 2 else 24

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

    system = InstrumentedHybridCrewAISocraticSystem(
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
    probe_scenario = StudentProbeScenario(objective_text)

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
    first_plan = probe_scenario.build_turn_plan(
        turn_num=1,
        current_stage="introduction",
        tutor_message="",
    )
    first_plan["scenario"] = probe_scenario
    first_student = await asyncio.to_thread(
        student_agent.generate_first_message,
        1,
        "introduction",
        first_plan,
    )

    # --- Run conversation turn by turn ---
    student_msg = first_student["response"]
    pending_student_trace = first_student

    turn_num = 1
    max_turns_hard = max_turns + 4
    extended_for_assessment = False

    while turn_num <= max_turns:
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
            "student_probe": copy.deepcopy(pending_student_trace),
            "stage_before": current_stage,
            "turns_on_objective_before": turns_on_obj,
            "ws_events": [],
            "tutor_response": "",
            "timings": {},
        }

        # Capture WS events for this turn
        ws_start_idx = len(all_ws_events)
        system.begin_turn_trace(turn_num, student_msg, current_stage)

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

        lesson_state = system._session_cache.get_lesson_state(session_id)
        turn_data["lesson_state_snapshot"] = copy.deepcopy(lesson_state)

        pacing_state = system._session_cache.get_pacing_state(session_id)
        turn_data["pacing_state_snapshot"] = copy.deepcopy(pacing_state)
        turn_data["internal_trace"] = system.get_turn_trace()

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
        probe = turn_data.get("student_probe", {}).get("directive_plan", {})
        if probe:
            print(f"  Student probe: {probe.get('phase')} / {probe.get('target')} | {probe.get('target_label')}")

        if lesson_state and lesson_state.get("concepts"):
            active = lesson_state.get("active_concept", "?")
            covered = sum(1 for c in lesson_state.get("concepts", []) if c.get("status") == "covered")
            total = len(lesson_state.get("concepts", []))
            print(f"  Concepts: {covered}/{total} covered | Active: {active}")

        if pacing_state:
            pace = pacing_state.get("current_pace", "?")
            pace_turns = pacing_state.get("turns_at_current_pace", 0)
            cooldown = pacing_state.get("cooldown_remaining", 0)
            recent = pacing_state.get("recent_signals", [])
            last_grasp = recent[-1].get("grasp_level", "?") if recent else "?"
            last_closure = recent[-1].get("concept_closure", "?") if recent else "?"
            print(f"  Pacing: {pace} (turns={pace_turns}, cd={cooldown}) | last: grasp={last_grasp} closure={last_closure}")

        if misconceptions:
            print(f"  Misconceptions: {len(misconceptions)} active")

        if (
            turn_num == max_turns
            and not extended_for_assessment
            and turn_num < max_turns_hard
        ):
            seen_assessment = any(
                stage in {"mini_assessment", "final_assessment"}
                for stage in [
                    turn_data.get("stage_after"),
                    *(turn.get("stage_after") for turn in all_turns),
                ]
            )
            if not seen_assessment:
                max_turns = min(max_turns + 4, max_turns_hard)
                extended_for_assessment = True
                print(
                    f"  Extending run to {max_turns} turns to exercise readiness/assessment."
                )

        # --- Generate next student message ---
        if turn_num < max_turns and tutor_response:
            t0 = time.perf_counter()
            next_plan = probe_scenario.build_turn_plan(
                turn_num=turn_num + 1,
                current_stage=turn_data["stage_after"],
                tutor_message=tutor_response,
            )
            next_plan["scenario"] = probe_scenario
            pending_student_trace = await asyncio.to_thread(
                student_agent.generate_response,
                tutor_response,
                turn_num + 1,
                turn_data["stage_after"],
                next_plan,
            )
            student_msg = pending_student_trace["response"]
            turn_data["timings"]["student_agent"] = round(time.perf_counter() - t0, 2)
        else:
            break

        turn_num += 1

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
    final_pacing_state = system._session_cache.get_pacing_state(session_id)
    final_learner_memory = await student_service.get_learner_memory(student_id)
    final_objective_memory = await student_service.get_objective_memory(student_id, objective_id)
    teaching_plan = system._session_cache.get_teaching_plan(session_id)
    teaching_content = system._session_cache.get_teaching_content(session_id)
    retrieval_bundle = system._session_cache.get_retrieval_bundle(session_id)
    slim_payload = system._session_cache.export_session(session_id)
    probe_summary = probe_scenario.summary()
    diagnostics = collect_run_diagnostics(all_turns, final_session)
    result_number = next_result_number(RESULTS_DIR)

    lines = []
    lines.append(f"# Conversation Test: {objective_text}")
    lines.append(f"\n**Objective ID**: `{objective_id}`")
    lines.append(f"**Student**: `{student_id}` (LLM-driven agent)")
    lines.append(f"**Session**: `{session_id}`")
    lines.append(f"**Run at**: {datetime.now().isoformat()}")
    lines.append(f"**Total turns**: {len(all_turns)}")
    total_time = sum(t.get("timings", {}).get("tutor", 0) for t in all_turns)
    lines.append(f"**Total tutor time**: {round(total_time, 1)}s")
    lines.append(f"**Probe coverage**: {len(probe_summary['completed_targets'])}/{len(StudentProbeScenario.TARGETS)} targets hit")
    lines.append(f"**Stages reached**: {', '.join(diagnostics['stages_reached']) or '(none)'}")
    lines.append(
        f"**Procedural repair turns**: {diagnostics['procedural_repair_turns'] or 'none'} | "
        f"**Procedural resolution turns**: {diagnostics['procedural_resolution_turns'] or 'none'}"
    )
    lines.append(
        f"**Assessment turns**: {diagnostics['assessment_turns'] or 'none'}"
    )

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

    lines.append(f"\n### Probe Scenario Summary\n")
    lines.append("```json")
    lines.append(pretty_json({
        "completed_targets": probe_summary["completed_targets"],
        "remaining_targets": probe_summary["remaining_targets"],
        "diagnostics": diagnostics,
    }))
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

        probe = turn.get("student_probe") or {}
        directive_plan = probe.get("directive_plan") or {}
        if directive_plan:
            lines.append(
                f"**Student Probe**: phase=`{directive_plan.get('phase', '?')}` "
                f"target=`{directive_plan.get('target', '?')}` "
                f"({directive_plan.get('target_label', '')})"
            )
            lines.append(f"  Goal: {directive_plan.get('phase_goal', '')}")
            lines.append(f"  Directive: {directive_plan.get('directive', '')}")
            attempts = probe.get("attempts", [])
            if attempts:
                lines.append(f"  Attempts: {len(attempts)}")
                for attempt in attempts:
                    validation = attempt.get("validation", {})
                    lines.append(
                        f"  - attempt {attempt.get('attempt')}: "
                        f"passed={validation.get('passed')} "
                        f"matched={validation.get('matched_patterns', [])} "
                        f"response={short_text(attempt.get('response', ''), 160)}"
                    )
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

        # Pacing state
        ps = turn.get("pacing_state_snapshot")
        if ps:
            pace = ps.get("current_pace", "?")
            pace_turns = ps.get("turns_at_current_pace", 0)
            cooldown = ps.get("cooldown_remaining", 0)
            reason = ps.get("pace_reason", "")
            recent = ps.get("recent_signals", [])
            lines.append(f"**Pacing**: `{pace}` (turns={pace_turns}, cooldown={cooldown})")
            if reason:
                lines.append(f"  Reason: {reason}")
            if recent:
                last = recent[-1]
                sig_parts = [f"{k}={v}" for k, v in last.items() if v and k != "override_reason"]
                lines.append(f"  Last signal: {', '.join(sig_parts)}")
            lines.append("")

        internal_trace = turn.get("internal_trace") or {}
        if internal_trace:
            lines.append("<details><summary>Internal Tutor Trace</summary>\n")
            lines.append("```json")
            lines.append(pretty_json(internal_trace))
            lines.append("```\n</details>\n")

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

    lines.append("### Pacing State (final)\n```json")
    lines.append(pretty_json(final_pacing_state))
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

    result_path = RESULTS_DIR / f"{result_number}_conversation_test.md"
    result_path.write_text("\n".join(lines), encoding="utf-8")
    size_kb = result_path.stat().st_size / 1024
    print(f"Written to {result_path} ({len(lines)} lines, {size_kb:.0f} KB)")

    # Also dump raw JSON for programmatic access
    raw_path = RESULTS_DIR / f"{result_number}_conversation_test_raw.json"
    raw_data = {
        "objective_id": objective_id,
        "objective_text": objective_text,
        "student_id": student_id,
        "session_id": session_id,
        "turns": all_turns,
        "probe_summary": probe_summary,
        "diagnostics": diagnostics,
        "final_state": {
            "session": final_session,
            "mastery": final_mastery,
            "misconceptions": final_misconceptions,
            "lesson_state": final_lesson_state,
            "pacing_state": final_pacing_state,
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
