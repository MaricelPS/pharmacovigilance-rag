"""Semantic search over MedDRA PTs using pgvector cosine similarity."""
import polars as pl
from sqlalchemy import create_engine, text

from src.config import DATABASE_URL
from src.rag.embeddings import embed_query


engine = create_engine(DATABASE_URL)


def search_pts(query: str, top_k: int = 15, min_similarity: float = 0.35) -> pl.DataFrame:
    """Return the MedDRA PTs most semantically similar to a free-text query.

    Args:
        query: Natural-language description of the event of interest.
        top_k: Maximum number of PTs to return.
        min_similarity: Minimum cosine similarity to include a PT in results.

    Returns:
        Polars DataFrame with columns: pt, similarity.
    """
    query_emb = embed_query(query)

    sql = text("""
        SELECT
            pt,
            1 - (embedding <=> CAST(:emb AS vector)) AS similarity
        FROM pt_embeddings
        ORDER BY embedding <=> CAST(:emb AS vector)
        LIMIT :top_k
    """)

    with engine.connect() as conn:
        rows = conn.execute(sql, {"emb": str(query_emb), "top_k": top_k}).mappings().all()

    df = pl.DataFrame([dict(r) for r in rows])
    return df.filter(pl.col("similarity") >= min_similarity)


if __name__ == "__main__":
    # Demo queries covering different clinical concepts
    demos = [
        "liver problems",
        "pancreas inflammation",
        "vision loss",
        "severe allergic reaction",
        "mental health disturbance",
        "thyroid issues",
    ]
    for q in demos:
        print(f"\n=== Query: '{q}' ===")
        results = search_pts(q, top_k=10)
        print(results)