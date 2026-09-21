"""Cached database queries for the Streamlit explorer.

Streamlit's @st.cache_data avoids re-running expensive queries on every
rerun. Cache is invalidated when arguments change.
"""
import polars as pl
import streamlit as st
from sqlalchemy import create_engine, text

from src.config import DATABASE_URL
from src.analytics.signals import scan_signals_for_drug


@st.cache_resource
def get_engine():
    """Reuse a single SQLAlchemy engine across reruns."""
    return create_engine(DATABASE_URL)


@st.cache_data(ttl=3600)
def cohort_overview() -> dict:
    """High-level counts of the GLP-1 cohort in the database."""
    engine = get_engine()
    with engine.connect() as conn:
        stats = {}
        stats["total_reports"] = conn.execute(
            text("SELECT COUNT(*) FROM reports")
        ).scalar()
        stats["total_drug_mentions"] = conn.execute(
            text("SELECT COUNT(*) FROM drugs WHERE is_glp1 = TRUE")
        ).scalar()
        stats["total_reactions"] = conn.execute(
            text("SELECT COUNT(*) FROM reactions")
        ).scalar()
        stats["unique_events"] = conn.execute(
            text("SELECT COUNT(DISTINCT pt) FROM reactions")
        ).scalar()
        stats["serious_reports"] = conn.execute(text("""
            SELECT COUNT(DISTINCT primaryid) FROM outcomes
            WHERE outc_cod IN ('DE','LT','HO','DS','CA')
        """)).scalar()
    return stats


@st.cache_data(ttl=3600)
def reports_by_quarter() -> pl.DataFrame:
    """Number of GLP-1 cohort reports per quarter."""
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT faers_quarter, COUNT(*)::INT AS n_reports
            FROM reports
            GROUP BY faers_quarter
            ORDER BY faers_quarter
        """)).mappings().all()
    return pl.DataFrame([dict(r) for r in rows])


@st.cache_data(ttl=3600)
def drug_distribution() -> pl.DataFrame:
    """Report counts per GLP-1 active ingredient (via brand-name matching)."""
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT drugname, COUNT(*)::INT AS n_reports
            FROM drugs
            WHERE is_glp1 = TRUE
            GROUP BY drugname
            ORDER BY n_reports DESC
            LIMIT 20
        """)).mappings().all()
    return pl.DataFrame([dict(r) for r in rows])


@st.cache_data(ttl=3600)
def demographics() -> pl.DataFrame:
    """Age and sex distribution of the GLP-1 cohort."""
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT
                CASE
                    WHEN age < 18 THEN '<18'
                    WHEN age < 40 THEN '18-39'
                    WHEN age < 60 THEN '40-59'
                    WHEN age < 75 THEN '60-74'
                    WHEN age >= 75 THEN '75+'
                    ELSE 'Unknown'
                END AS age_group,
                COALESCE(sex, 'Unknown') AS sex,
                COUNT(*)::INT AS n_reports
            FROM reports
            GROUP BY age_group, sex
            ORDER BY age_group, sex
        """)).mappings().all()
    return pl.DataFrame([dict(r) for r in rows])


@st.cache_data(ttl=3600)
def signals_for_drug(drug_key: str, min_cases: int = 10) -> pl.DataFrame:
    """Compute and cache the full signal scan for a drug."""
    return scan_signals_for_drug(drug_key, min_cases=min_cases)


@st.cache_data(ttl=3600)
def available_glp1_drugs() -> list[str]:
    """Return the list of GLP-1 active ingredients loaded in the reference table."""
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT active_ingredient FROM glp1_drugs ORDER BY active_ingredient"
        )).all()
    return [r[0] for r in rows]