"""Smoke tests to verify the environment is correctly configured."""
from sqlalchemy import create_engine, text
from src.config import DATABASE_URL, TARGET_DRUGS


def test_database_connection():
    """Verify Postgres is reachable and pgvector is installed."""
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT extname FROM pg_extension WHERE extname = 'vector'"
        )).fetchone()
        assert result is not None, "pgvector extension is not installed"


def test_target_drugs_configured():
    """Verify GLP-1 target drugs are loaded from env."""
    assert len(TARGET_DRUGS) >= 5
    assert "semaglutide" in TARGET_DRUGS