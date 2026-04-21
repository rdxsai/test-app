from __future__ import annotations

import asyncio
import json
from typing import Any, Optional

from ..artifacts import TeachingGraphArtifact
from ..prompts import TEACHING_GRAPH_PLANNER_PROMPT


class TeachingGraphPlannerWorker:
    def __init__(
        self,
        *,
        reasoning_client,
        max_completion_tokens: int,
        reasoning_effort: str,
        graph_error_cls: type[Exception],
    ) -> None:
        self.reasoning_client = reasoning_client
        self.max_completion_tokens = max_completion_tokens
        self.reasoning_effort = reasoning_effort
        self.graph_error_cls = graph_error_cls

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        stripped = (text or "").strip()
        if not stripped.startswith("```"):
            return stripped
        lines = stripped.splitlines()
        if len(lines) >= 2 and lines[-1].strip() == "```":
            return "\n".join(lines[1:-1]).strip()
        return "\n".join(lines[1:]).strip()

    async def generate(
        self,
        objective_text: str,
        *,
        learner_level: Optional[str] = None,
        prerequisite_assumptions: Optional[str] = None,
    ) -> TeachingGraphArtifact:
        user_lines = [f"OBJECTIVE:\n{objective_text.strip()}"]
        if learner_level:
            user_lines.append(f"LEARNER LEVEL:\n{learner_level.strip()}")
        if prerequisite_assumptions:
            user_lines.append(
                f"PREREQUISITE ASSUMPTIONS:\n{prerequisite_assumptions.strip()}"
            )

        response = await asyncio.to_thread(
            self.reasoning_client.chat,
            [
                {"role": "system", "content": TEACHING_GRAPH_PLANNER_PROMPT},
                {"role": "user", "content": "\n\n".join(user_lines)},
            ],
            0.1,
            self.max_completion_tokens,
            self.reasoning_effort,
            {"type": "json_object"},
        )

        try:
            payload = json.loads(self._strip_code_fences(response))
            return TeachingGraphArtifact.from_dict(payload)
        except Exception as exc:
            preview = self._strip_code_fences(response).replace("\n", " ").strip()
            if len(preview) > 200:
                preview = preview[:200] + "..."
            detail = preview or "empty response"
            raise self.graph_error_cls(
                "Teaching graph generation failed: "
                f"{detail}. Guided graph build cannot continue without a valid graph."
            ) from exc
