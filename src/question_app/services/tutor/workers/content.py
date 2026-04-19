from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any, Callable, Dict, List, Optional

from ..artifacts import (
    RetrievalRunArtifact,
    TeachingContentArtifact,
    TeachingPlanArtifact,
)

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


class RetrievalWorker:
    AVAILABLE_TOOLS_TEXT = """
Available WCAG MCP tools:
1. list_principles() — Lists all 4 WCAG 2.2 principles with descriptions.
2. list_guidelines(principle?) — Lists guidelines, optionally filtered by principle (1-4).
3. list_success_criteria(level?, guideline?, principle?) — Lists SC with optional filters.
4. get_success_criteria_detail(ref_id) — Gets normative SC text only (~500-2000 chars).
5. get_criterion(ref_id) — Gets full SC details including Understanding docs (~5K-18K chars).
6. get_guideline(ref_id) — Gets full guideline details including all its SC.
7. search_wcag(query, level?) — Searches SC titles/descriptions by keyword.
8. get_criteria_by_level(level, include_lower?) — Gets all SC for a conformance level.
9. count_criteria(group_by) — Returns counts grouped by level, principle, or guideline.
10. get_full_criterion_context(ref_id) — Gets comprehensive SC context + techniques + glossary.
11. get_techniques_for_criterion(ref_id) — Gets all techniques for a specific SC.
12. get_technique(id) — Gets details for a specific technique by ID.
13. search_techniques(query) — Searches techniques by keyword.
14. get_glossary_term(term) — Gets official WCAG definition of a glossary term.
15. search_glossary(query) — Searches glossary terms by keyword.
16. list_glossary_terms() — Lists glossary terms available in WCAG.
17. whats_new_in_wcag22() — Lists all SC added in WCAG 2.2.
"""

    def __init__(self, *, reasoning_client, wcag_mcp) -> None:
        self.reasoning_client = reasoning_client
        self.wcag_mcp = wcag_mcp

    def assess_coverage(
        self, objective_text: str, teaching_plan: Any, results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        hits = [result for result in results if result.get("status") == "HIT"]
        hit_content = "\n".join(result.get("result", "") for result in hits).lower()
        context = f"{objective_text}\n{str(teaching_plan)[:3000]}".lower()

        require_rollup = any(
            marker in context
            for marker in (
                "conformance",
                "level aa",
                "level aaa",
                "level a",
                "criteria by level",
            )
        )
        require_techniques = any(
            marker in context
            for marker in (
                "technique",
                "techniques",
                "sufficient",
                "advisory",
                "informative",
                "normative",
                "requirement",
                "requirements",
            )
        )

        rollup_phrases = [
            "all level a and level aa",
            "all a and aa",
            "all a and all aa",
            "meet all level a",
            "all level a success criteria",
        ]
        technique_phrases = [
            "sufficient technique",
            "advisory technique",
            "informative",
            "techniques are not required",
            "sufficient and advisory",
        ]

        missing_checks = []
        if require_rollup and not any(phrase in hit_content for phrase in rollup_phrases):
            missing_checks.append("conformance_rollup_rule")
        if require_techniques and not any(phrase in hit_content for phrase in technique_phrases):
            missing_checks.append("techniques_vs_requirements")

        return {
            "hit_count": len(hits),
            "hit_chars": sum(result.get("chars", 0) for result in hits),
            "missing_checks": missing_checks,
            "required_checks": {
                "conformance_rollup_rule": require_rollup,
                "techniques_vs_requirements": require_techniques,
            },
            "budget_chars": 20000,
        }

    @staticmethod
    def build_feedback_message(
        coverage: Dict[str, Any], remaining_calls: int, budget_chars: int,
    ) -> str:
        lines = [
            f"Research status: hits={coverage['hit_count']}, chars={coverage['hit_chars']}.",
        ]
        if coverage.get("missing_checks"):
            lines.append(
                "Still missing explicit evidence for: "
                + ", ".join(coverage["missing_checks"])
                + "."
            )
        else:
            lines.append(
                "No deterministic evidence checks are currently failing, but you may "
                "continue retrieving if the teaching plan still needs more support."
            )
        lines.append(
            f"Remaining budget: {remaining_calls} tool calls, about "
            f"{max(budget_chars - coverage['hit_chars'], 0)} chars."
        )
        lines.append(
            "Do not repeat prior tool calls. Prefer smaller, more targeted tools "
            "before deep criterion fetches. Stop only when you judge the teaching plan "
            "has enough supporting evidence."
        )
        return "\n".join(lines)

    @staticmethod
    def annotate_results(
        planned_calls: List[Dict[str, Any]], results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        annotated = []
        for planned_call, result in zip(planned_calls, results):
            enriched = dict(result)
            for field in ("tool_call_id", "round", "sequence", "source", "rationale"):
                value = planned_call.get(field)
                if value not in (None, ""):
                    enriched[field] = value
            annotated.append(enriched)
        return annotated

    def extract_agentic_planned_calls(
        self,
        tool_calls: List[Dict[str, Any]],
        round_number: int,
        seen_calls: set,
        max_new_calls: int,
    ) -> List[Dict[str, Any]]:
        try:
            from ...wcag_mcp_client import normalize_tool_args
        except ModuleNotFoundError:
            normalize_tool_args = lambda _fn_name, fn_args: dict(fn_args)

        planned_calls = []
        for tool_call in tool_calls:
            if len(planned_calls) >= max_new_calls:
                break

            function = tool_call.get("function", {})
            fn_name = function.get("name", "")
            if not fn_name:
                continue

            args_text = function.get("arguments", "") or "{}"
            try:
                fn_args = json.loads(args_text)
            except (json.JSONDecodeError, TypeError):
                logger.warning(
                    "Guided retrieval: invalid tool arguments for %s: %s",
                    fn_name,
                    args_text,
                )
                continue

            rationale = ""
            if isinstance(fn_args, dict) and "rationale" in fn_args:
                raw_rationale = fn_args.pop("rationale")
                if isinstance(raw_rationale, str):
                    rationale = raw_rationale.strip()

            normalized_args = normalize_tool_args(fn_name, fn_args)
            dedupe_key = (fn_name, json.dumps(normalized_args, sort_keys=True))
            if dedupe_key in seen_calls:
                logger.info(
                    "Guided retrieval: skipping duplicate call %s(%s)",
                    fn_name,
                    normalized_args,
                )
                continue
            seen_calls.add(dedupe_key)

            planned_calls.append(
                {
                    "tool_call_id": tool_call.get("id", ""),
                    "tool": fn_name,
                    "args": fn_args,
                    "rationale": rationale,
                    "category": "agentic",
                    "round": round_number,
                    "sequence": len(planned_calls) + 1,
                    "source": "guided_retrieval",
                }
            )

        return planned_calls

    @staticmethod
    def build_tool_description_lookup(tool_definitions: List[Dict[str, Any]]) -> Dict[str, str]:
        lookup: Dict[str, str] = {}
        for tool in tool_definitions or []:
            fn = tool.get("function") or {}
            name = fn.get("name")
            description = fn.get("description") or ""
            if name:
                lookup[name] = " ".join(str(description).split())
        return lookup

    @staticmethod
    def summarise_tool_result(result: Dict[str, Any]) -> str:
        status = result.get("status") or "?"
        chars = result.get("chars")
        if status == "BLOCKED":
            return "blocked"
        if status == "ERROR":
            raw = result.get("result") or ""
            return f"error: {raw[:80]}"
        if isinstance(chars, int):
            label = f"{chars} chars"
            if status == "MISS":
                return f"miss ({label})"
            return label
        return str(status).lower()

    async def run_agentic_retrieval(
        self,
        *,
        objective_text: str,
        teaching_plan: Any,
        ws_send,
        prompt_builder: Callable[..., str],
    ) -> RetrievalRunArtifact:
        try:
            from ...wcag_mcp_client import GUIDED_WCAG_TOOL_DEFINITIONS
        except ModuleNotFoundError:
            GUIDED_WCAG_TOOL_DEFINITIONS = getattr(self.wcag_mcp, "tool_definitions", [])

        if not self.wcag_mcp:
            logger.warning("Guided retrieval skipped: WCAG MCP client unavailable")
            return RetrievalRunArtifact(
                objective_text=objective_text,
                teaching_plan=teaching_plan,
            )

        tool_description_lookup = self.build_tool_description_lookup(
            GUIDED_WCAG_TOOL_DEFINITIONS
        )
        base_prompt = prompt_builder(
            objective_text=objective_text,
            teaching_plan=teaching_plan,
        )
        coverage = self.assess_coverage(objective_text, teaching_plan, [])
        budget_chars = coverage["budget_chars"]
        max_rounds = 4
        max_tool_calls = 10

        messages = [
            {"role": "system", "content": base_prompt},
            {
                "role": "user",
                "content": (
                    "Research the WCAG evidence needed for this guided lesson. "
                    "Use tools until you judge the teaching plan has enough supporting "
                    "evidence, then stop. "
                    f"Current retrieval budget: about {budget_chars} characters."
                ),
            },
        ]

        all_results: List[Dict[str, Any]] = []
        seen_calls = set()
        total_tool_calls = 0

        for round_number in range(1, max_rounds + 1):
            remaining_calls = max_tool_calls - total_tool_calls
            if remaining_calls <= 0:
                logger.info("Guided retrieval: tool-call budget exhausted")
                break

            await ws_send(
                {
                    "type": "stage",
                    "stage": "searching",
                    "detail": f"Researching WCAG sources (round {round_number}/{max_rounds})...",
                }
            )
            response_msg = await self.reasoning_client.chat_with_tools(
                messages=messages,
                tools=GUIDED_WCAG_TOOL_DEFINITIONS,
                temperature=0.0,
                max_tokens=500,
                tool_choice="required" if round_number == 1 else "auto",
                reasoning_effort="medium",
            )
            tool_calls = response_msg.get("tool_calls") or []
            messages.append(response_msg)

            if not tool_calls:
                logger.info(
                    "Guided retrieval: model stopped after round %s with no tool calls",
                    round_number,
                )
                break

            planned_calls = self.extract_agentic_planned_calls(
                tool_calls=tool_calls,
                round_number=round_number,
                seen_calls=seen_calls,
                max_new_calls=remaining_calls,
            )
            if not planned_calls:
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "You repeated prior tool calls or produced invalid tool "
                            "arguments. Choose a different retrieval strategy or stop "
                            "if you judge the existing evidence is already enough."
                        ),
                    }
                )
                continue

            for planned_call in planned_calls:
                tool_name = planned_call.get("tool", "")
                await ws_send(
                    {
                        "type": "tool_activity",
                        "phase": "retrieval",
                        "round": planned_call.get("round", round_number),
                        "sequence": planned_call.get("sequence"),
                        "name": tool_name,
                        "params": planned_call.get("args") or {},
                        "description": tool_description_lookup.get(tool_name, ""),
                        "rationale": planned_call.get("rationale", ""),
                        "status": "calling",
                    }
                )

            round_results = await self.wcag_mcp.execute_planned_tool_calls(planned_calls)
            round_results = self.annotate_results(planned_calls, round_results)
            all_results.extend(round_results)
            total_tool_calls += len(planned_calls)

            for planned_call, result in zip(planned_calls, round_results):
                tool_name = planned_call.get("tool", "")
                await ws_send(
                    {
                        "type": "tool_activity",
                        "phase": "retrieval",
                        "round": planned_call.get("round", round_number),
                        "sequence": planned_call.get("sequence"),
                        "name": tool_name,
                        "params": planned_call.get("args") or {},
                        "description": tool_description_lookup.get(tool_name, ""),
                        "rationale": planned_call.get("rationale", ""),
                        "status": "completed",
                        "result_status": result.get("status", ""),
                        "result_summary": self.summarise_tool_result(result),
                    }
                )

            for result in round_results:
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": result.get("tool_call_id", ""),
                        "content": result.get("result") or "No results found.",
                    }
                )

            coverage = self.assess_coverage(
                objective_text, teaching_plan, all_results
            )
            logger.info(
                "Guided retrieval round %s: %s hits, %s chars, missing=%s",
                round_number,
                coverage["hit_count"],
                coverage["hit_chars"],
                coverage["missing_checks"],
            )
            if coverage["hit_chars"] >= budget_chars:
                logger.info("Guided retrieval: content budget reached")
                break

            messages.append(
                {
                    "role": "user",
                    "content": self.build_feedback_message(
                        coverage=coverage,
                        remaining_calls=max_tool_calls - total_tool_calls,
                        budget_chars=budget_chars,
                    ),
                }
            )

        return RetrievalRunArtifact(
            objective_text=objective_text,
            teaching_plan=teaching_plan,
            results=all_results,
            coverage=self.assess_coverage(objective_text, teaching_plan, all_results),
        )


class RetrievalBundleBuilder:
    def __init__(self, *, wcag_mcp, retrieval_worker: RetrievalWorker) -> None:
        self.wcag_mcp = wcag_mcp
        self.retrieval_worker = retrieval_worker

    @staticmethod
    def truncate_text(text: str, max_chars: int) -> str:
        text = (text or "").strip()
        if len(text) <= max_chars:
            return text
        return text[: max_chars - 3].rstrip() + "..."

    @staticmethod
    def normalize_excerpt(text: str) -> str:
        cleaned = (text or "").replace("\t", " ")
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        cleaned = re.sub(r"[ ]{2,}", " ", cleaned)
        return cleaned.strip()

    @staticmethod
    def first_markdown_heading(text: str) -> str:
        for line in (text or "").splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                return stripped.lstrip("#").strip()
        return ""

    @staticmethod
    def parse_markdown_sections(text: str) -> Dict[str, str]:
        sections: Dict[str, List[str]] = {}
        current: Optional[str] = None
        for line in (text or "").splitlines():
            if line.startswith("## "):
                current = line[3:].strip()
                sections[current] = []
                continue
            if current is not None:
                sections[current].append(line)
        return {
            name: "\n".join(lines).strip()
            for name, lines in sections.items()
            if "\n".join(lines).strip()
        }

    def add_bundle_item(
        self,
        bucket: List[Dict[str, Any]],
        *,
        title: str,
        content: str,
        result: Dict[str, Any],
    ) -> None:
        normalized_title = (title or "").strip()
        normalized_content = self.normalize_excerpt(content)
        if not normalized_content:
            return
        dedupe_key = (
            normalized_title.lower(),
            re.sub(r"\s+", " ", normalized_content).strip().lower(),
        )
        for existing in bucket:
            existing_key = (
                str(existing.get("title", "")).strip().lower(),
                re.sub(r"\s+", " ", str(existing.get("content", ""))).strip().lower(),
            )
            if existing_key == dedupe_key:
                return
        bucket.append(
            {
                "title": normalized_title,
                "content": normalized_content,
                "source_tool": result.get("tool", ""),
                "source_args": result.get("args", {}),
                "round": result.get("round"),
                "sequence": result.get("sequence"),
            }
        )

    def extract_glossary_definition_item(self, result: Dict[str, Any]) -> Optional[Dict[str, str]]:
        text = result.get("result", "") or ""
        title = self.first_markdown_heading(text)
        body = text
        if "\n\n" in text:
            body = text.split("\n\n", 1)[1]
        body = body.split("\n\n[View in", 1)[0].strip()
        body = self.normalize_excerpt(body)
        if not body:
            return None
        return {
            "title": title or result.get("args", {}).get("term", "Glossary term"),
            "content": body,
        }

    def extract_success_criteria_detail_item(self, result: Dict[str, Any]) -> Optional[Dict[str, str]]:
        text = result.get("result", "") or ""
        title = self.first_markdown_heading(text) or result.get("args", {}).get("ref_id", "Success Criterion")
        sections = self.parse_markdown_sections(text)
        meta_lines = []
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("**Level:**") or stripped.startswith("**Principle:**") or stripped.startswith("**Guideline:**"):
                meta_lines.append(stripped)
        body_parts = []
        if meta_lines:
            body_parts.append(" | ".join(meta_lines))
        if sections.get("Success Criterion"):
            body_parts.append(sections["Success Criterion"])
        elif sections.get("Description"):
            body_parts.append(sections["Description"])
        content = self.normalize_excerpt("\n\n".join(body_parts))
        if not content:
            return None
        return {"title": title, "content": self.truncate_text(content, 1200)}

    def extract_criterion_items(
        self, result: Dict[str, Any]
    ) -> Dict[str, Optional[Dict[str, str]]]:
        text = result.get("result", "") or ""
        title = self.first_markdown_heading(text) or result.get("args", {}).get("ref_id", "Success Criterion")
        sections = self.parse_markdown_sections(text)

        core_parts = []
        if sections.get("In Brief"):
            core_parts.append(sections["In Brief"])
        if sections.get("Description"):
            core_parts.append(sections["Description"])
        core_content = self.normalize_excerpt("\n\n".join(core_parts))

        intent_text = sections.get("Intent", "")
        intent_blocks = [
            self.normalize_excerpt(block)
            for block in re.split(r"\n\s*\n", intent_text)
            if self.normalize_excerpt(block)
        ]
        decision_blocks = [
            block for block in intent_blocks
            if any(
                marker in block.lower()
                for marker in (
                    "scope",
                    "criteria",
                    "change of context",
                    "without receiving focus",
                    "not considered",
                    "do not need",
                    "not within the scope",
                    "does not meet",
                )
            )
        ] or intent_blocks[:2]
        decision_content = self.normalize_excerpt("\n\n".join(decision_blocks[:3]))

        examples_text = sections.get("Examples", "")
        example_blocks = [
            self.normalize_excerpt(block)
            for block in re.split(r"\n###\s+Example\s+\d+\s*\n", examples_text)
            if self.normalize_excerpt(block)
        ]
        positive_blocks = []
        contrast_blocks = []
        risk_blocks = []
        for block in example_blocks:
            lowered = block.lower()
            if any(
                marker in lowered
                for marker in (
                    'too "chatty"',
                    "too chatty",
                    "unnecessarily interrupt",
                    "best practices but are not requirements",
                    "not to force authors",
                )
            ):
                risk_blocks.append(block)
                continue
            if any(
                marker in lowered
                for marker in (
                    "not status messages",
                    "do not meet the definition",
                    "not required",
                    "does not meet the definition",
                    "does not need",
                    "excepted from this success criterion",
                )
            ):
                contrast_blocks.append(block)
                continue
            positive_blocks.append(block)

        return {
            "core": {
                "title": title,
                "content": self.truncate_text(core_content, 1600),
            } if core_content else None,
            "decision": {
                "title": f"Decision Boundaries for {title}",
                "content": self.truncate_text(decision_content, 1800),
            } if decision_content else None,
            "examples": {
                "title": f"Examples from {title}",
                "content": self.truncate_text("\n\n".join(positive_blocks[:2]), 1800),
            } if positive_blocks else None,
            "contrast": {
                "title": f"Contrast Cases from {title}",
                "content": self.truncate_text("\n\n".join(contrast_blocks[:2]), 1500),
            } if contrast_blocks else None,
            "risks": {
                "title": f"Risks and Misuse Notes for {title}",
                "content": self.truncate_text("\n\n".join(risk_blocks[:2]), 1200),
            } if risk_blocks else None,
        }

    def extract_technique_items(
        self, result: Dict[str, Any]
    ) -> Dict[str, Optional[Dict[str, str]]]:
        text = result.get("result", "") or ""
        title = self.first_markdown_heading(text) or "Technique guidance"
        sections = self.parse_markdown_sections(text)

        technique_parts = []
        if sections.get("Sufficient Techniques"):
            technique_parts.append("Sufficient techniques:\n" + sections["Sufficient Techniques"])
        if sections.get("Advisory Techniques"):
            technique_parts.append("Advisory techniques:\n" + sections["Advisory Techniques"])
        technique_content = self.normalize_excerpt("\n\n".join(technique_parts))

        risk_parts = []
        if sections.get("Failure Techniques"):
            risk_parts.append("Failure techniques:\n" + sections["Failure Techniques"])
        if 'role="alert" or aria-live="assertive"' in text:
            risk_parts.append('Use of role="alert" or aria-live="assertive" on non-urgent content is a misuse risk.')
        risk_content = self.normalize_excerpt("\n\n".join(risk_parts))

        return {
            "techniques": {
                "title": title,
                "content": self.truncate_text(technique_content, 2200),
            } if technique_content else None,
            "risks": {
                "title": f"Failure and Misuse Notes for {title}",
                "content": self.truncate_text(risk_content, 1400),
            } if risk_content else None,
        }

    @staticmethod
    def summarize_raw_hit(result: Dict[str, Any]) -> Dict[str, Any]:
        preview = (result.get("result") or "").strip()
        preview = preview[:240] + ("..." if len(preview) > 240 else "")
        return {
            "tool": result.get("tool", ""),
            "args": result.get("args", {}),
            "round": result.get("round"),
            "sequence": result.get("sequence"),
            "chars": result.get("chars", 0),
            "preview": preview,
        }

    async def build_bundle(
        self,
        results: list,
        objective_text: str = "",
        teaching_plan: Any = None,
    ) -> Dict[str, Any]:
        coverage = self.retrieval_worker.assess_coverage(
            objective_text, teaching_plan, results
        )

        fallback_calls = []
        if "conformance_rollup_rule" in coverage["missing_checks"]:
            logger.info("Evidence check: roll-up rule MISSING, running fallbacks")
            fallback_calls.extend([
                {"tool": "get_glossary_term", "args": {"term": "conformance"}, "category": "fallback"},
                {"tool": "get_criterion", "args": {"ref_id": "1.1.1"}, "category": "fallback"},
            ])
        if "techniques_vs_requirements" in coverage["missing_checks"]:
            logger.info("Evidence check: techniques distinction MISSING, running fallbacks")
            fallback_calls.extend([
                {"tool": "get_technique", "args": {"id": "H37"}, "category": "fallback"},
                {"tool": "get_glossary_term", "args": {"term": "accessibility supported"}, "category": "fallback"},
            ])

        working_results = list(results)
        if fallback_calls and self.wcag_mcp:
            fallback_results = await self.wcag_mcp.execute_planned_tool_calls(fallback_calls)
            working_results.extend(
                self.retrieval_worker.annotate_results(fallback_calls, fallback_results)
            )
            coverage = self.retrieval_worker.assess_coverage(
                objective_text, teaching_plan, working_results
            )

        hits = []
        seen = set()
        for result in working_results:
            if result.get("status") != "HIT":
                continue
            key = (result.get("tool"), json.dumps(result.get("args", {}), sort_keys=True))
            if key in seen:
                continue
            seen.add(key)
            hits.append(result)

        bundle = {
            "version": 1,
            "objective_text": objective_text,
            "coverage": coverage,
            "sections": {
                "core_rules": [],
                "definitions": [],
                "decision_rules": [],
                "examples": [],
                "contrast_cases": [],
                "technique_patterns": [],
                "risks": [],
                "structural_context": [],
            },
            "raw_hits": [self.summarize_raw_hit(result) for result in hits],
        }

        glossary_terms = {
            str(result.get("args", {}).get("term", "")).strip().lower()
            for result in hits
            if result.get("tool") == "get_glossary_term"
        }

        for result in hits:
            tool = result.get("tool", "")
            args = result.get("args", {})

            if tool == "search_glossary":
                query = str(args.get("query", "")).strip().lower()
                if query in glossary_terms:
                    continue
                continue

            if tool == "get_glossary_term":
                item = self.extract_glossary_definition_item(result)
                if item:
                    self.add_bundle_item(
                        bundle["sections"]["definitions"],
                        title=item["title"],
                        content=item["content"],
                        result=result,
                    )
                continue

            if tool in {"list_principles", "list_guidelines", "list_success_criteria", "get_guideline", "get_criteria_by_level", "count_criteria"}:
                self.add_bundle_item(
                    bundle["sections"]["structural_context"],
                    title=self.first_markdown_heading(result.get("result", "")) or tool.replace("_", " ").title(),
                    content=self.truncate_text(result.get("result", ""), 1600),
                    result=result,
                )
                continue

            if tool == "get_success_criteria_detail":
                item = self.extract_success_criteria_detail_item(result)
                if item:
                    self.add_bundle_item(
                        bundle["sections"]["core_rules"],
                        title=item["title"],
                        content=item["content"],
                        result=result,
                    )
                continue

            if tool == "get_criterion":
                items = self.extract_criterion_items(result)
                if items.get("core"):
                    self.add_bundle_item(bundle["sections"]["core_rules"], result=result, **items["core"])
                if items.get("decision"):
                    self.add_bundle_item(bundle["sections"]["decision_rules"], result=result, **items["decision"])
                if items.get("examples"):
                    self.add_bundle_item(bundle["sections"]["examples"], result=result, **items["examples"])
                if items.get("contrast"):
                    self.add_bundle_item(bundle["sections"]["contrast_cases"], result=result, **items["contrast"])
                if items.get("risks"):
                    self.add_bundle_item(bundle["sections"]["risks"], result=result, **items["risks"])
                continue

            if tool == "get_full_criterion_context":
                item = self.extract_success_criteria_detail_item(result)
                if item:
                    self.add_bundle_item(
                        bundle["sections"]["core_rules"],
                        title=item["title"],
                        content=item["content"],
                        result=result,
                    )
                continue

            if tool == "get_techniques_for_criterion":
                items = self.extract_technique_items(result)
                if items.get("techniques"):
                    self.add_bundle_item(bundle["sections"]["technique_patterns"], result=result, **items["techniques"])
                if items.get("risks"):
                    self.add_bundle_item(bundle["sections"]["risks"], result=result, **items["risks"])
                continue

            if tool in {"get_technique", "search_techniques"}:
                self.add_bundle_item(
                    bundle["sections"]["technique_patterns"],
                    title=self.first_markdown_heading(result.get("result", "")) or str(args.get("id", args.get("query", "Technique"))),
                    content=self.truncate_text(result.get("result", ""), 1200),
                    result=result,
                )
                continue

            if tool == "search_wcag":
                self.add_bundle_item(
                    bundle["sections"]["core_rules"],
                    title=f"Search Results for {args.get('query', '')}".strip(),
                    content=self.truncate_text(result.get("result", ""), 1200),
                    result=result,
                )

        return bundle


class TeachingContentRenderer:
    def __init__(self, *, bundle_builder: RetrievalBundleBuilder) -> None:
        self.bundle_builder = bundle_builder

    def render(self, bundle: Dict[str, Any], for_display: bool = False) -> str:
        if not bundle:
            return ""

        sections = bundle.get("sections", {})
        section_specs = [
            ("CORE FACTS", sections.get("core_rules", []), 2, 1400),
            ("DEFINITIONS", sections.get("definitions", []), 3, 600),
            ("DECISION BOUNDARIES", sections.get("decision_rules", []), 2, 1400),
            ("EXAMPLES", sections.get("examples", []), 2, 1400),
            ("CONTRAST CASES", sections.get("contrast_cases", []), 2, 1200),
            ("TECHNIQUE PATTERNS", sections.get("technique_patterns", []), 3, 1200),
            ("RISKS / MISUSE", sections.get("risks", []), 2, 900),
            ("STRUCTURE NOTES", sections.get("structural_context", []), 2, 1200),
        ]

        rendered_sections = []
        for heading, items, max_items, max_chars in section_specs:
            if not items:
                continue
            limit = None if for_display else max_items
            lines = [f"## {heading}"]
            for item in items if limit is None else items[:limit]:
                title = str(item.get("title", "")).strip()
                raw_content = str(item.get("content", "")).strip()
                content = (
                    raw_content
                    if for_display
                    else self.bundle_builder.truncate_text(raw_content, max_chars)
                )
                if title:
                    lines.append(f"### {title}")
                lines.append(content)
                lines.append("")
            rendered_sections.append("\n".join(lines).strip())

        return "\n\n".join(section for section in rendered_sections if section)


class TeachingContentPipelineOrchestrator:
    def __init__(
        self,
        *,
        plan_worker: TeachingPlanWorker,
        concept_worker: ConceptExtractionWorker,
        retrieval_worker: RetrievalWorker,
        bundle_builder: RetrievalBundleBuilder,
        renderer: TeachingContentRenderer,
    ) -> None:
        self.plan_worker = plan_worker
        self.concept_worker = concept_worker
        self.retrieval_worker = retrieval_worker
        self.bundle_builder = bundle_builder
        self.renderer = renderer

    async def run(
        self,
        *,
        objective_text: str,
        ws_send,
        prompt_builder: Callable[..., str],
    ) -> TeachingContentArtifact:
        await ws_send({"type": "stage", "stage": "composing", "detail": "Creating teaching plan..."})
        await ws_send({"type": "teaching_plan_generating"})
        plan_artifact = await self.plan_worker.generate(objective_text)
        await ws_send(
            {
                "type": "teaching_plan",
                "plan": plan_artifact.plan,
                "display_plan": plan_artifact.display_plan,
            }
        )
        logger.info("Pipeline step 1: teaching plan (%d chars)", len(str(plan_artifact.plan)))

        await ws_send({"type": "stage", "stage": "searching", "detail": "Researching WCAG content..."})
        await ws_send({"type": "teaching_content_generating"})
        retrieval_coro = self.retrieval_worker.run_agentic_retrieval(
            objective_text=objective_text,
            teaching_plan=plan_artifact.plan,
            ws_send=ws_send,
            prompt_builder=prompt_builder,
        )
        extract_coro = self.concept_worker.extract(plan_artifact.plan)
        retrieval_artifact, extracted_concepts = await asyncio.gather(
            retrieval_coro, extract_coro,
        )
        hits = [r for r in retrieval_artifact.results if r.get("status") == "HIT"]
        logger.info(
            "Pipeline step 2: %d/%d hits, %d chars",
            len(hits),
            len(retrieval_artifact.results),
            sum(r.get("chars", 0) for r in hits),
        )

        await ws_send({"type": "stage", "stage": "searching", "detail": "Validating evidence..."})
        retrieval_bundle = await self.bundle_builder.build_bundle(
            retrieval_artifact.results,
            objective_text=objective_text,
            teaching_plan=plan_artifact.plan,
        )
        teaching_content = self.renderer.render(retrieval_bundle)
        display_teaching_content = self.renderer.render(
            retrieval_bundle, for_display=True
        )
        logger.info(
            "Pipeline step 3: teaching pack (%s chars tutor / %s chars display, %s raw hits)",
            len(teaching_content),
            len(display_teaching_content),
            len(retrieval_bundle.get("raw_hits", [])),
        )
        await ws_send(
            {
                "type": "teaching_content",
                "content": teaching_content,
                "display_content": display_teaching_content,
            }
        )
        await ws_send(
            {
                "type": "stage",
                "stage": "searching",
                "detail": f"Teaching pack: {len(teaching_content)} chars from {len(hits)} sources",
            }
        )

        return TeachingContentArtifact(
            objective_text=objective_text,
            teaching_plan=plan_artifact.plan,
            teaching_content=teaching_content,
            display_content=display_teaching_content,
            retrieval_bundle=retrieval_bundle,
            extracted_concepts=extracted_concepts,
        )

