#!/usr/bin/env python3
"""Run the frozen Instance A gold benchmark from the CLI."""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
os.chdir(PROJECT_ROOT)

from dotenv import load_dotenv

load_dotenv()

from question_app.api.pg_vector_store import VectorStoreService
from question_app.core.config import config
from question_app.services.eval.instance_a_benchmark import run_instance_a_benchmark
from question_app.services.eval.repository import EvalRepository
from question_app.services.general_chat_service import GeneralChatService
from question_app.services.tutor.azure_client import AzureAPIMClient
from question_app.services.wcag_mcp_client import WCAGMCPClient


def _build_chat_service() -> tuple[GeneralChatService, EvalRepository]:
    azure_config = {
        "api_key": config.AZURE_OPENAI_SUBSCRIPTION_KEY,
        "endpoint": config.AZURE_OPENAI_ENDPOINT,
        "deployment_name": config.AZURE_OPENAI_DEPLOYMENT_ID,
        "instance_a_deployment_name": config.AZURE_OPENAI_INSTANCE_A_DEPLOYMENT_ID,
        "tutor_deployment_name": config.AZURE_OPENAI_TUTOR_DEPLOYMENT_ID,
        "reasoning_deployment_name": config.AZURE_OPENAI_REASONING_DEPLOYMENT_ID,
        "api_version": config.AZURE_OPENAI_API_VERSION,
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
    )
    wcag_mcp = WCAGMCPClient(
        command=config.WCAG_MCP_COMMAND,
        azure_client=azure_client,
    ) if config.WCAG_MCP_ENABLED else None

    service = GeneralChatService(
        azure_config=azure_config,
        vector_store_service=vector_service,
        wcag_mcp_client=wcag_mcp,
        db_manager=vector_service.db,
    )
    return service, EvalRepository(db=vector_service.db)


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default=str(PROJECT_ROOT / "eval" / "instance_a_gold_v1.json"))
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--batch-id", default=None)
    parser.add_argument("--no-judge", action="store_true")
    args = parser.parse_args()

    service, eval_repo = _build_chat_service()
    try:
        result = await run_instance_a_benchmark(
            chat_service=service,
            eval_repo=eval_repo,
            dataset_path=args.dataset,
            limit=args.limit,
            use_judge=not args.no_judge,
            batch_id=args.batch_id,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        return 0
    finally:
        await service.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
