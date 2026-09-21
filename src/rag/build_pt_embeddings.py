"""Compute and store embeddings for every MedDRA Preferred Term in the cohort.

The `pt_embeddings` table holds one row per unique PT, enabling semantic
search over adverse-event terminology.
"""
from sqlalchemy import create_engine, text
from tqdm import tqdm

from src.config import DATABASE_URL
from src.rag.embeddings import embed_texts, EMBEDDING_DIM


engine = create_engine(DATABASE_URL)


def get_missing_pts() -> list[str]:
    """Return all distinct PTs in reactions that don't yet have an embedding."""
    sql = text("""
        SELECT DISTINCT r.pt
        FROM reactions r
        LEFT JOIN pt_embeddings e ON e.pt = r.pt
        WHERE e.pt IS NULL AND r.pt IS NOT NULL
        ORDER BY r.pt
    """)
    with engine.connect() as conn:
        return [row[0] for row in conn.execute(sql)]


def insert_embeddings(pts: list[str], embeddings: list[list[float]]):
    """Bulk-insert embeddings into pt_embeddings."""
    assert len(pts) == len(embeddings)
    with engine.begin() as conn:
        for pt, emb in zip(pts, embeddings):
            conn.execute(
                text("""
                    INSERT INTO pt_embeddings (pt, embedding)
                    VALUES (:pt, CAST(:emb AS vector))
                    ON CONFLICT (pt) DO UPDATE SET embedding = EXCLUDED.embedding
                """),
                {"pt": pt, "emb": str(emb)},
            )


def build_all(chunk_size: int = 128):
    """Compute and store embeddings for every missing PT."""
    pts = get_missing_pts()
    if not pts:
        print("All PTs already embedded.")
        return

    print(f"Embedding {len(pts):,} PTs with dim={EMBEDDING_DIM}...")

    for i in tqdm(range(0, len(pts), chunk_size)):
        chunk = pts[i : i + chunk_size]
        embeddings = embed_texts(chunk, input_type="document")
        insert_embeddings(chunk, embeddings)

    print("Done.")


if __name__ == "__main__":
    build_all()