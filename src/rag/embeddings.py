"""Wrapper around Voyage AI embeddings API with batching and error handling."""
from typing import Literal

import voyageai

from src.config import VOYAGE_API_KEY

# Model configuration
MODEL_NAME = "voyage-3"
EMBEDDING_DIM = 1024
MAX_BATCH_SIZE = 128  # Voyage limits batches to 128 texts

_client = voyageai.Client(api_key=VOYAGE_API_KEY)


def embed_texts(
        texts: list[str],
        input_type: Literal["document", "query"] = "document",
) -> list[list[float]]:
    """Embed a list of texts using Voyage AI.

    Args:
        texts: Strings to embed. Automatically chunked into batches.
        input_type: 'document' for corpus items (MedDRA PTs), 'query' for
            user searches. Voyage optimizes each direction differently.

    Returns:
        List of embeddings, one per input text, in the same order.
    """
    if not texts:
        return []

    all_embeddings: list[list[float]] = []
    for i in range(0, len(texts), MAX_BATCH_SIZE):
        batch = texts[i : i + MAX_BATCH_SIZE]
        result = _client.embed(
            texts=batch,
            model=MODEL_NAME,
            input_type=input_type,
        )
        all_embeddings.extend(result.embeddings)
    return all_embeddings


def embed_query(text: str) -> list[float]:
    """Convenience wrapper for embedding a single search query."""
    return embed_texts([text], input_type="query")[0]