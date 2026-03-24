"""
Stage Machine — enforces stage transitions and assessment thresholds.

The LLM suggests stage transitions via the eval JSON's `stage_recommendation`
field. This module applies business rules on top of those suggestions:

  - Readiness check thresholds (min turns, correct reasoning required)
  - Assessment scoring (2/3 mini, 4/5 final)
  - Confidence gating (only persist mastery changes when confidence > 0.7)
  - Stage transition enforcement (can't skip stages)

The stage machine reads eval data and writes to the Student MCP server.
It does NOT generate LLM responses — it only processes the evaluation
output and updates state accordingly.

Stage flow:
  ONBOARDING → INTRODUCTION → EXPLORATION → READINESS_CHECK →
  MINI_ASSESSMENT → FINAL_ASSESSMENT → TRANSITION → (next objective)

Loop-backs:
  MINI_ASSESSMENT (fail) → INTRODUCTION (different teaching approach)
  FINAL_ASSESSMENT (fail) → INTRODUCTION (re-teach)
"""

import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# Valid stage names (must match session_state.current_stage values)
STAGES = (
    "onboarding", "introduction", "exploration", "readiness_check",
    "mini_assessment", "mini_review", "final_assessment", "transition",
)

# Valid mastery levels (must match mastery_records.mastery_level values)
MASTERY_LEVELS = (
    "not_attempted", "misconception", "in_progress", "partial", "mastered",
)


class StageMachine:
    """Processes eval JSON and enforces stage transitions with thresholds.

    All state mutations go through the Student MCP client. The stage machine
    is stateless — it reads session_state from the MCP on each call and
    writes updates back.
    """

    # --- Thresholds (configurable per deployment) ---
    MIN_TURNS_FOR_READINESS = 3
    MAX_TURNS_BEFORE_OFFER = 8
    MINI_ASSESSMENT_QUESTIONS = 3
    MINI_PASS_THRESHOLD = 2        # 2 out of 3
    FINAL_ASSESSMENT_QUESTIONS = 5
    FINAL_MASTERY_THRESHOLD = 4    # 4/5 → mastered
    FINAL_PARTIAL_THRESHOLD = 3    # 3/5 → partial
    CONFIDENCE_THRESHOLD = 0.7

    def __init__(self, student_mcp_client):
        self.mcp = student_mcp_client

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    async def process_eval(
        self,
        student_id: str,
        session_id: str,
        session_state: Dict[str, Any],
        eval_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Process eval JSON and apply state changes.

        This is called after every LLM response in Instance B.
        Reads the eval data, enforces thresholds, and writes updates
        to the Student MCP server.

        Args:
            student_id:    The student.
            session_id:    The active session.
            session_state: Current session state from MCP (stage, turns, scores).
            eval_data:     Parsed eval JSON from the LLM response.

        Returns:
            Dict describing all actions taken:
            {
                "stage_changed": bool,
                "new_stage": str or None,
                "mastery_updated": bool,
                "new_mastery_level": str or None,
                "misconceptions_logged": [str],
                "stage_summary": str or None,
                "assessment_result": {"asked", "correct", "total", "passed"} or None,
                "turns_incremented": bool,
            }
        """
        current_stage = session_state.get("current_stage", "introduction")
        objective_id = session_state.get("active_objective_id", "")
        recommendation = eval_data.get("stage_recommendation", "stay")
        confidence = eval_data.get("confidence", 0.0)

        result = {
            "stage_changed": False,
            "new_stage": None,
            "mastery_updated": False,
            "new_mastery_level": None,
            "misconceptions_logged": [],
            "stage_summary": None,
            "assessment_result": None,
            "turns_incremented": False,
        }

        # 1. Increment turns on the current objective
        turns = session_state.get("turns_on_objective", 0) + 1
        await self.mcp.update_session_state(session_id, turns=turns)
        result["turns_incremented"] = True

        # 2. Log misconceptions (if any, regardless of confidence)
        misconceptions = eval_data.get("misconceptions_detected", [])
        if misconceptions and objective_id:
            result["misconceptions_logged"] = await self._log_misconceptions(
                student_id, objective_id, eval_data
            )

        # 3. Apply mastery change (if confidence meets threshold)
        if confidence >= self.CONFIDENCE_THRESHOLD:
            mastery_changed = await self._apply_mastery_change(
                student_id, objective_id, eval_data
            )
            result["mastery_updated"] = mastery_changed
            if mastery_changed:
                result["new_mastery_level"] = eval_data.get(
                    "mastery_level_change", ""
                ).split("→")[-1].strip() if "→" in eval_data.get("mastery_level_change", "") else None

        # 4. Evaluate stage transition
        if current_stage in ("introduction", "exploration"):
            result.update(
                await self._handle_exploration_stage(
                    session_id, session_state, eval_data, turns, recommendation
                )
            )
        elif current_stage == "readiness_check":
            result.update(
                await self._handle_readiness_check(
                    session_id, eval_data, recommendation
                )
            )
        elif current_stage == "mini_assessment":
            result.update(
                await self._handle_assessment(
                    student_id, session_id, session_state, eval_data,
                    assessment_type="mini"
                )
            )
        elif current_stage == "final_assessment":
            result.update(
                await self._handle_assessment(
                    student_id, session_id, session_state, eval_data,
                    assessment_type="final"
                )
            )
        elif current_stage == "transition":
            result.update(
                await self._handle_transition(student_id, session_id)
            )

        return result

    # ------------------------------------------------------------------
    # Stage-specific handlers
    # ------------------------------------------------------------------

    async def _handle_exploration_stage(
        self, session_id: str, session_state: Dict,
        eval_data: Dict, turns: int, recommendation: str,
    ) -> Dict[str, Any]:
        """Handle INTRODUCTION and EXPLORATION stages.

        Transition to READINESS_CHECK when:
          - LLM recommends it AND turns >= MIN_TURNS AND evidence of correct reasoning
          - OR turns >= MAX_TURNS (force offer assessment)
        """
        result = {"stage_changed": False, "new_stage": None, "stage_summary": None}

        has_evidence = bool(eval_data.get("mastery_evidence"))
        detected_correct = eval_data.get("detected_state") == "CORRECT"

        if recommendation == "advance_to_readiness_check":
            if turns >= self.MIN_TURNS_FOR_READINESS and (has_evidence or detected_correct):
                stage_summary = eval_data.get("stage_summary", "")
                await self.mcp.update_session_state(
                    session_id, stage="readiness_check",
                    stage_summary=stage_summary,
                )
                result.update(stage_changed=True, new_stage="readiness_check",
                              stage_summary=stage_summary)
                logger.info(f"Stage transition: exploration → readiness_check (turns={turns})")
            else:
                logger.info(
                    f"Readiness check denied: turns={turns} (min={self.MIN_TURNS_FOR_READINESS}), "
                    f"evidence={has_evidence}, correct={detected_correct}"
                )

        elif turns >= self.MAX_TURNS_BEFORE_OFFER:
            # Force transition — student has been exploring long enough
            stage_summary = eval_data.get("stage_summary", "Max turns reached, offering assessment.")
            await self.mcp.update_session_state(
                session_id, stage="readiness_check",
                stage_summary=stage_summary,
            )
            result.update(stage_changed=True, new_stage="readiness_check",
                          stage_summary=stage_summary)
            logger.info(f"Stage transition: exploration → readiness_check (max turns={turns})")

        return result

    async def _handle_readiness_check(
        self, session_id: str, eval_data: Dict, recommendation: str,
    ) -> Dict[str, Any]:
        """Handle READINESS_CHECK stage.

        Student accepts → MINI_ASSESSMENT
        Student declines → back to EXPLORATION
        """
        result = {"stage_changed": False, "new_stage": None, "stage_summary": None}

        if recommendation == "advance_to_mini_assessment":
            await self.mcp.update_session_state(
                session_id, stage="mini_assessment",
                assessment_progress='{"asked": 0, "correct": 0}',
            )
            result.update(stage_changed=True, new_stage="mini_assessment")
            logger.info("Stage transition: readiness_check → mini_assessment")

        elif recommendation in ("loop_back_to_introduction", "stay"):
            # Student not ready or declined
            await self.mcp.update_session_state(session_id, stage="exploration")
            result.update(stage_changed=True, new_stage="exploration")
            logger.info("Stage transition: readiness_check → exploration (student not ready)")

        return result

    async def _handle_assessment(
        self, student_id: str, session_id: str,
        session_state: Dict, eval_data: Dict,
        assessment_type: str,
    ) -> Dict[str, Any]:
        """Handle MINI_ASSESSMENT and FINAL_ASSESSMENT stages.

        Tracks score per question. When all questions asked, determines
        pass/fail and transitions accordingly.
        """
        result = {
            "stage_changed": False, "new_stage": None,
            "stage_summary": None, "assessment_result": None,
        }

        # Read current progress
        if assessment_type == "mini":
            progress_key = "mini_assessment_progress"
            total_questions = self.MINI_ASSESSMENT_QUESTIONS
            pass_threshold = self.MINI_PASS_THRESHOLD
        else:
            progress_key = "final_assessment_progress"
            total_questions = self.FINAL_ASSESSMENT_QUESTIONS
            pass_threshold = self.FINAL_MASTERY_THRESHOLD

        progress = session_state.get(progress_key, {})
        if isinstance(progress, str):
            try:
                progress = json.loads(progress)
            except (json.JSONDecodeError, TypeError):
                progress = {}

        asked = progress.get("asked", 0) + 1
        is_correct = eval_data.get("detected_state") == "CORRECT"
        correct = progress.get("correct", 0) + (1 if is_correct else 0)

        new_progress = {"asked": asked, "correct": correct}
        await self.mcp.update_session_state(
            session_id, assessment_progress=json.dumps(new_progress),
        )

        # Check if all questions have been asked
        if asked >= total_questions:
            result["assessment_result"] = {
                "asked": asked, "correct": correct,
                "total": total_questions, "passed": correct >= pass_threshold,
            }

            objective_id = session_state.get("active_objective_id", "")

            if assessment_type == "mini":
                if correct >= pass_threshold:
                    # Passed mini → advance to final
                    await self.mcp.update_session_state(
                        session_id, stage="final_assessment",
                        assessment_progress='{"asked": 0, "correct": 0}',
                        stage_summary=f"Mini assessment: {correct}/{total_questions}",
                    )
                    result.update(stage_changed=True, new_stage="final_assessment",
                                  stage_summary=f"Mini assessment passed: {correct}/{total_questions}")
                    logger.info(f"Mini assessment PASSED ({correct}/{total_questions}) → final_assessment")
                else:
                    # Failed mini → loop back with different approach
                    await self.mcp.update_session_state(
                        session_id, stage="introduction", turns=0,
                        stage_summary=f"Mini assessment: {correct}/{total_questions} — re-teaching",
                    )
                    if objective_id:
                        await self.mcp.update_mastery(
                            student_id, objective_id, "in_progress",
                            f"Mini assessment {correct}/{total_questions}",
                        )
                    result.update(stage_changed=True, new_stage="introduction",
                                  stage_summary=f"Mini assessment failed: {correct}/{total_questions}")
                    logger.info(f"Mini assessment FAILED ({correct}/{total_questions}) → introduction")

            else:  # final assessment
                if correct >= self.FINAL_MASTERY_THRESHOLD:
                    mastery_level = "mastered"
                elif correct >= self.FINAL_PARTIAL_THRESHOLD:
                    mastery_level = "partial"
                else:
                    mastery_level = "in_progress"

                if objective_id:
                    await self.mcp.update_mastery(
                        student_id, objective_id, mastery_level,
                        f"Final assessment {correct}/{total_questions}",
                    )
                    result["mastery_updated"] = True
                    result["new_mastery_level"] = mastery_level

                if correct >= self.FINAL_PARTIAL_THRESHOLD:
                    # Passed (mastered or partial) → transition to next objective
                    await self.mcp.update_session_state(
                        session_id, stage="transition",
                        stage_summary=f"Final assessment: {correct}/{total_questions} → {mastery_level}",
                    )
                    result.update(stage_changed=True, new_stage="transition",
                                  stage_summary=f"Final: {correct}/{total_questions} → {mastery_level}")
                    logger.info(f"Final assessment → {mastery_level} ({correct}/{total_questions})")
                else:
                    # Failed final → loop back
                    await self.mcp.update_session_state(
                        session_id, stage="introduction", turns=0,
                        stage_summary=f"Final assessment: {correct}/{total_questions} — re-teaching",
                    )
                    result.update(stage_changed=True, new_stage="introduction",
                                  stage_summary=f"Final failed: {correct}/{total_questions}")
                    logger.info(f"Final assessment FAILED ({correct}/{total_questions}) → introduction")
        else:
            # More questions remain
            result["assessment_result"] = {
                "asked": asked, "correct": correct,
                "total": total_questions, "passed": None,
            }

        return result

    async def _handle_transition(
        self, student_id: str, session_id: str,
    ) -> Dict[str, Any]:
        """Handle TRANSITION stage — select next objective and begin."""
        result = {"stage_changed": False, "new_stage": None, "stage_summary": None}

        next_obj = await self.mcp.get_recommended_next_objective(student_id)
        if next_obj:
            await self.mcp.update_session_state(
                session_id,
                stage="introduction",
                active_objective_id=next_obj.get("objective_id", ""),
                turns=0,
                assessment_progress='{"asked": 0, "correct": 0}',
                stage_summary="",
            )
            result.update(
                stage_changed=True,
                new_stage="introduction",
                stage_summary=f"Starting new objective: {next_obj.get('objective_text', '')}",
            )
            logger.info(f"Transition → introduction (new objective: {next_obj.get('objective_id')})")
        else:
            logger.info("All objectives mastered — no next objective available")
            result["stage_summary"] = "All objectives mastered!"

        return result

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    async def _apply_mastery_change(
        self, student_id: str, objective_id: str, eval_data: Dict,
    ) -> bool:
        """Write mastery update if eval indicates a change."""
        level_change = eval_data.get("mastery_level_change", "no_change")
        if level_change == "no_change" or not objective_id:
            return False

        # Extract the target level from "old→new" format
        new_level = level_change.split("→")[-1].strip() if "→" in level_change else level_change
        if new_level not in MASTERY_LEVELS:
            logger.warning(f"Invalid mastery level: {new_level}")
            return False

        evidence = eval_data.get("mastery_evidence", "")
        await self.mcp.update_mastery(student_id, objective_id, new_level, evidence)
        logger.info(f"Mastery updated: {objective_id} → {new_level}")
        return True

    async def _log_misconceptions(
        self, student_id: str, objective_id: str, eval_data: Dict,
    ) -> List[str]:
        """Log any detected misconceptions."""
        misconceptions = eval_data.get("misconceptions_detected", [])
        logged = []
        for text in misconceptions:
            if text and isinstance(text, str):
                await self.mcp.log_misconception(student_id, objective_id, text)
                logged.append(text)
        if logged:
            logger.info(f"Logged {len(logged)} misconception(s) for {objective_id}")
        return logged
