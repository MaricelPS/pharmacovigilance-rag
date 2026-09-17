"""Build aggregate background tables from the full FAERS universe.

These tables contain no personal data — only counts of (drug, event) pairs
across all reports in FAERS. They are the denominators used to compute
disproportionality metrics (PRR, ROR, IC).

Aggregates built:
    - drug_totals:       reports mentioning each active ingredient
    - event_totals:      reports mentioning each MedDRA PT
    - drug_event_counts: reports mentioning both a given drug and a given event
    - quarter_totals:    total unique reports per quarter
"""
from io import StringIO

import polars as pl
from sqlalchemy import create_engine, text

from src.config import PROCESSED_DIR, DATABASE_URL, FAERS_QUARTERS
from src.etl.normalize import normalize_drug_name


engine = create_engine(DATABASE_URL)


def deduplicate_demo(demo: pl.DataFrame) -> pl.DataFrame:
    """Keep latest caseversion per caseid to avoid double counting."""
    return (
        demo.sort(["caseid", "caseversion"], descending=[False, True])
        .unique(subset=["caseid"], keep="first")
    )


def build_drug_key(drug: pl.DataFrame) -> pl.DataFrame:
    """Add a normalized `drug_key` column derived from prod_ai, falling back
    to drugname when prod_ai is missing."""
    return drug.with_columns(
        pl.when(pl.col("prod_ai").is_not_null() & (pl.col("prod_ai") != ""))
        .then(pl.col("prod_ai"))
        .otherwise(pl.col("drugname"))
        .map_elements(normalize_drug_name, return_dtype=pl.Utf8)
        .alias("drug_key")
    ).filter(pl.col("drug_key").is_not_null())


def build_quarter_aggregates(quarter: str) -> dict[str, pl.DataFrame]:
    """Compute all aggregate tables for a single quarter."""
    qdir = PROCESSED_DIR / quarter
    demo = deduplicate_demo(pl.read_parquet(qdir / "demo.parquet"))
    drug = pl.read_parquet(qdir / "drug.parquet")
    reac = pl.read_parquet(qdir / "reac.parquet")

    valid_pids = demo.select("primaryid")

    # Restrict drug and reac rows to deduplicated reports
    drug = drug.join(valid_pids, on="primaryid", how="inner")
    reac = reac.join(valid_pids, on="primaryid", how="inner")

    # Normalize drug names into a drug_key
    drug = build_drug_key(drug)

    # Keep only relevant roles for signal detection: primary + secondary suspect
    # Concomitants inflate background counts unfairly. Standard practice is PS+SS.
    drug_susp = drug.filter(pl.col("role_cod").is_in(["PS", "SS"]))

    # Unique (report, drug) and (report, event) pairs — a report may list
    # the same drug or PT multiple times with different formulations/rows.
    drug_pairs = drug_susp.select(["primaryid", "drug_key"]).unique()
    event_pairs = reac.select(["primaryid", "pt"]).unique().rename({"pt": "event_pt"})

    # 1. Quarter totals (unique reports)
    quarter_totals = pl.DataFrame({
        "faers_quarter": [quarter],
        "n_reports": [len(valid_pids)],
    })

    # 2. Drug totals
    drug_totals = (
        drug_pairs.group_by("drug_key")
        .agg(pl.len().alias("n_reports"))
        .with_columns(pl.lit(quarter).alias("faers_quarter"))
    )

    # 3. Event totals
    event_totals = (
        event_pairs.group_by("event_pt")
        .agg(pl.len().alias("n_reports"))
        .with_columns(pl.lit(quarter).alias("faers_quarter"))
    )

    # 4. Drug-event co-occurrence
    drug_event = (
        drug_pairs.join(event_pairs, on="primaryid", how="inner")
        .group_by(["drug_key", "event_pt"])
        .agg(pl.len().alias("n_reports"))
        .with_columns(pl.lit(quarter).alias("faers_quarter"))
    )

    return {
        "quarter_totals": quarter_totals,
        "drug_totals": drug_totals,
        "event_totals": event_totals,
        "drug_event_counts": drug_event,
    }


def copy_dataframe(df: pl.DataFrame, table: str, columns: list[str]):
    """Bulk-load a DataFrame into Postgres using COPY."""
    pandas_df = df.select(columns).to_pandas()
    buf = StringIO()
    pandas_df.to_csv(buf, index=False, header=False, na_rep="", sep="\t")
    buf.seek(0)

    raw_conn = engine.raw_connection()
    try:
        with raw_conn.cursor() as cur:
            cols = ", ".join(columns)
            copy_sql = (
                f"COPY {table} ({cols}) FROM STDIN "
                f"WITH (FORMAT csv, DELIMITER E'\\t', NULL '')"
            )
            cur.copy_expert(copy_sql, buf)
        raw_conn.commit()
    finally:
        raw_conn.close()


def truncate_aggregates():
    """Clear existing aggregates before rebuilding."""
    with engine.begin() as conn:
        conn.execute(text(
            "TRUNCATE drug_event_counts, drug_totals, event_totals, quarter_totals;"
        ))


def load_quarter_aggregates(quarter: str):
    """Compute and load aggregates for a single quarter."""
    print(f"\n=== Aggregating {quarter} ===")
    aggs = build_quarter_aggregates(quarter)

    copy_dataframe(aggs["quarter_totals"], "quarter_totals",
                   ["faers_quarter", "n_reports"])
    print(f"  quarter_totals: 1 row (n_reports={aggs['quarter_totals']['n_reports'][0]:,})")

    copy_dataframe(aggs["drug_totals"], "drug_totals",
                   ["drug_key", "faers_quarter", "n_reports"])
    print(f"  drug_totals: {len(aggs['drug_totals']):,} unique drugs")

    copy_dataframe(aggs["event_totals"], "event_totals",
                   ["event_pt", "faers_quarter", "n_reports"])
    print(f"  event_totals: {len(aggs['event_totals']):,} unique events")

    copy_dataframe(aggs["drug_event_counts"], "drug_event_counts",
                   ["drug_key", "event_pt", "n_reports", "faers_quarter"])
    print(f"  drug_event_counts: {len(aggs['drug_event_counts']):,} pairs")


def build_all():
    """Build background aggregates for all configured quarters."""
    truncate_aggregates()
    for quarter in FAERS_QUARTERS:
        load_quarter_aggregates(quarter)
    print("\nBackground aggregates complete.")


if __name__ == "__main__":
    build_all()