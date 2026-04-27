from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any, Callable, Dict, List, Optional

from ..artifacts import TeachingPlanArtifact

logger = logging.getLogger(__name__)


class TeachingPlanWorker:
    def __init__(
        self,
        *,
        reasoning_client,
        display_formatter: Callable[[Any], str],
        max_completion_tokens: int,
        reasoning_effort: str,
        plan_error_cls: type[Exception],
    ) -> None:
        self.reasoning_client = reasoning_client
        self.display_formatter = display_formatter
        self.max_completion_tokens = max_completion_tokens
        self.reasoning_effort = reasoning_effort
        self.plan_error_cls = plan_error_cls

    @staticmethod
    def is_valid_structured_plan(plan_text: str) -> bool:
        section_pattern = re.compile(
            r"(?:^|\n)(?:##?\s*)?\d{1,2}\.\s*([a-z][\w_]*)\s*\n",
            re.IGNORECASE,
        )
        section_names = {
            match.group(1).strip().lower()
            for match in section_pattern.finditer(plan_text or "")
        }
        required = {
            "objective_text",
            "plain_language_goal",
            "mastery_definition",
            "concept_decomposition",
            "dependency_order",
        }
        return required.issubset(section_names)

    @staticmethod
    def is_valid_legacy_plan(plan: Dict[str, Any]) -> bool:
        concepts = plan.get("concepts", []) if isinstance(plan, dict) else []
        recommended_order = (
            plan.get("recommended_order", []) if isinstance(plan, dict) else []
        )
        return bool(isinstance(concepts, list) and concepts and recommended_order)

    async def generate(
        self, objective_text: str, teaching_content: str = "",
    ) -> TeachingPlanArtifact:
        from ..prompts import CONCEPT_DECOMPOSITION_PROMPT

        user_content = f"Objective: {objective_text}"
        if teaching_content:
            user_content += f"\n\nTeaching content:\n{teaching_content[:3000]}"

        messages = [
            {"role": "system", "content": CONCEPT_DECOMPOSITION_PROMPT},
            {"role": "user", "content": user_content},
        ]
        logger.info(
            "Generating teaching plan with deployment=%s effort=%s requested_tokens=%d",
            getattr(self.reasoning_client, "deployment", "unknown"),
            self.reasoning_effort,
            self.max_completion_tokens,
        )
        response = await asyncio.to_thread(
            self.reasoning_client.chat,
            messages,
            0.3,
            self.max_completion_tokens,
            self.reasoning_effort,
        )

        try:
            plan = json.loads(response)
            if self.is_valid_legacy_plan(plan):
                logger.info(
                    "Teaching plan generated (legacy JSON): %d concepts",
                    len(plan.get("concepts", [])),
                )
                return TeachingPlanArtifact(
                    objective_text=objective_text,
                    plan=plan,
                    display_plan=self.display_formatter(plan),
                )
            raise self.plan_error_cls(
                "Planner returned legacy JSON without concepts or teaching order."
            )
        except (json.JSONDecodeError, TypeError):
            pass

        if response and len(response) > 100 and self.is_valid_structured_plan(response):
            logger.info(
                "Teaching plan generated (structured text): %d chars",
                len(response),
            )
            return TeachingPlanArtifact(
                objective_text=objective_text,
                plan=response,
                display_plan=self.display_formatter(response),
            )

        response_preview = (response or "").strip().replace("\n", " ")
        if len(response_preview) > 180:
            response_preview = response_preview[:180] + "..."
        detail = "empty response"
        if response_preview:
            detail = f"invalid response preview={response_preview!r}"
        raise self.plan_error_cls(
            "Teaching plan generation failed on gpt-5.4: "
            f"{detail}. Guided tutoring will not continue without a valid plan."
        )


class ConceptExtractionWorker:
    def __init__(self, *, tutor_client) -> None:
        self.tutor_client = tutor_client

    async def extract(self, teaching_plan: Any) -> Optional[List[Dict[str, str]]]:
        if not teaching_plan or not isinstance(teaching_plan, str):
            return None

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a precise extraction tool. Given a teaching plan, "
                    "extract the ordered list of teachable concepts from the "
                    "dependency_order or concept_decomposition section.\n\n"
                    "Rules:\n"
                    "- Return ONLY the teachable concepts, in teaching order.\n"
                    "- Each concept should have a short snake_case 'id' and a "
                    "human-readable 'label'.\n"
                    "- Do NOT include dependency annotations, section headings, "
                    "or explanatory text.\n"
                    "- Merge closely related sub-concepts into one entry.\n"
                    "- Do NOT include application/assessment tasks.\n"
                    "- Target 6-10 concepts.\n"
                    '- Output JSON: {"concepts": [{"id": "...", "label": "..."}]}'
                ),
            },
            {"role": "user", "content": teaching_plan},
        ]

        try:
            raw = await asyncio.to_thread(
                self.tutor_client.chat,
                messages,
                0.0,
                800,
                response_format={"type": "json_object"},
            )
            parsed = json.loads(raw)
            concepts = parsed.get("concepts", [])
            if concepts and isinstance(concepts, list):
                if len(concepts) > 10:
                    logger.info(
                        "Concept extraction (LLM): %d concepts, capping to 10",
                        len(concepts),
                    )
                    concepts = concepts[:10]
                logger.info(
                    "Concept extraction (LLM): %d concepts from teaching plan",
                    len(concepts),
                )
                return concepts
        except (json.JSONDecodeError, TypeError, KeyError) as exc:
            logger.warning("Concept extraction LLM call failed to parse: %s", exc)
        except Exception as exc:
            logger.warning("Concept extraction LLM call failed: %s", exc)

        return None
