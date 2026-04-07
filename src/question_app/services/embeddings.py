"""
Shared embedding helpers.

This module centralizes Ollama embedding generation so API routers and
services use one implementation.
"""

import asyncio
from typing import List

import httpx

from ..core import config, get_logger

logger = get_logger(__name__)


async def get_ollama_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for a list of texts using Ollama."""
    embeddings: List[List[float]] = []
    logger.info(f"Generating {len(texts)} embeddings via Ollama...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        for index, text in enumerate(texts):
            try:
                normalized = text.strip()
                if not normalized:
                    logger.warning(f"Empty text at index {index}, returning zero vector.")
                    embeddings.append([0.0] * 768)
                    continue

                response = await client.post(
                    f"{config.OLLAMA_HOST}/api/embeddings",
                    json={
                        "model": config.OLLAMA_EMBEDDING_MODEL,
                        "prompt": normalized,
                    },
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()

                payload = response.json()
                embedding = payload.get("embedding")
                if not embedding:
                    logger.error(
                        f"Ollama response missing embedding for index {index}: {payload}"
                    )
                    embeddings.append([0.0] * 768)
                    continue

                embeddings.append(embedding)

                if index < len(texts) - 1:
                    await asyncio.sleep(0.05)
            except Exception as exc:
                logger.error(f"Error generating embedding for text {index}: {exc}")
                embeddings.append([0.0] * 768)

    logger.info(f"Successfully generated {len(embeddings)} embeddings.")
    return embeddings
