#!/usr/bin/env python3
"""Run the graph-grounded teaching pipeline for a single objective.

Usage:
    poetry run python scripts/run_pipeline.py [OBJECTIVE_ID]

If OBJECTIVE_ID is omitted, defaults to I.A.2.
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

from question_app.api.pg_vector_store import VectorStoreService
from question_app.core.config import config
from question_app.services.tutor.azure_client import (
    AzureAPIMClient,
    build_graph_responses_client,
)
from question_app.services.tutor.hybrid_system import GuidedTutorSystem
from question_app.services.tutor.workers.graph import GraphGroundingProjector
from question_app.services.wcag_mcp_client import WCAGMCPClient


PROJECT_RESULTS_DIR = PROJECT_ROOT / "results"
PROJECT_RESULTS_DIR.mkdir(exist_ok=True)


def pretty_json(obj) -> str:
    return json.dumps(obj, indent=2, default=repr, ensure_ascii=False)


async def main() -> None:
    objective_id = sys.argv[1] if len(sys.argv) > 1 else "I.A.2"
    azure_config = {
        "api_key": config.AZURE_OPENAI_SUBSCRIPTION_KEY,
        "endpoint": config.AZURE_OPENAI_ENDPOINT,
        "deployment_name": config.AZURE_OPENAI_DEPLOYMENT_ID,
        "tutor_deployment_name": config.AZURE_OPENAI_TUTOR_DEPLOYMENT_ID,
        "reasoning_deployment_name": config.AZURE_OPENAI_REASONING_DEPLOYMENT_ID,
        "api_version": config.AZURE_OPENAI_API_VERSION,
        "content_filter_policy": config.AZURE_OPENAI_CONTENT_FILTER_POLICY,
    }

    vector_service = VectorStoreService()
    azure_client = AzureAPIMClient(
        endpoint=azure_config["endpoint"],
        deployment=(
            azure_config.get("reasoning_deployment_name")
            or azure_config["deployment_name"]
        ),
        api_key=azure_config["api_key"],
        api_version=azure_config.get("api_version", "2024-02-15-preview"),
        content_filter_policy=azure_config.get("content_filter_policy"),
    )
    wcag_mcp = (
        WCAGMCPClient(command=config.WCAG_MCP_COMMAND, azure_client=azure_client)
        if config.WCAG_MCP_ENABLED
        else None
    )
    graph_responses_client = build_graph_responses_client(
        azure_config={
            **azure_config,
            "endpoint": config.OPENAI_RESPONSES_ENDPOINT,
            "api_version": config.OPENAI_RESPONSES_API_VERSION,
        },
        responses_deployment=config.OPENAI_RESPONSES_MODEL,
        enabled=config.OPENAI_RESPONSES_ENABLED,
    )

    system = GuidedTutorSystem(
        azure_config=azure_config,
        vector_store_service=vector_service,
        wcag_mcp_client=wcag_mcp,
        student_mcp_client=None,
        graph_responses_client=graph_responses_client,
    )

    objective = system._fetch_objective_by_id(objective_id)
    if not objective:
        print(f"Objective '{objective_id}' not found in DB.")
        sys.exit(1)
    objective_text = objective["text"]
    print(f"Objective: {objective_id} - {objective_text}")

    started = time.perf_counter()
    artifact = await system._build_teaching_graph_content(objective_text)
    elapsed = round(time.perf_counter() - started, 2)
    tutor_content = (
        GraphGroundingProjector.render_tutor_content(artifact.tutor_facing_content)
        if artifact.tutor_facing_content
        else ""
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = PROJECT_RESULTS_DIR / f"graph_pipeline_{timestamp}.json"
    md_path = PROJECT_RESULTS_DIR / f"graph_pipeline_{timestamp}.md"
    json_path.write_text(pretty_json(artifact.to_dict()) + "\n", encoding="utf-8")

    lines = [
        "# Graph Pipeline Trace",
        "",
        f"**Objective ID**: `{objective_id}`",
        f"**Objective**: {objective_text}",
        f"**Run at**: {datetime.now().isoformat()}",
        f"**Total time**: {elapsed}s",
        "",
        "## Validation",
        "",
        f"- Status: `{artifact.validation.overall_status}`",
        f"- Evidence cards: `{len(artifact.evidence_cards.evidence_cards) if artifact.evidence_cards else 0}`",
        f"- Claims: `{len(artifact.claim_ledger.claims) if artifact.claim_ledger else 0}`",
        "",
        "## Tutor-Facing Content",
        "",
        tutor_content,
        "",
        "## Full Artifact",
        "",
        "```json",
        pretty_json(artifact.to_dict()),
        "```",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {md_path}")
    print(f"Wrote {json_path}")

    if wcag_mcp:
        await wcag_mcp.close()


if __name__ == "__main__":
    asyncio.run(main())
