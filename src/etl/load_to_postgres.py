"""ETL pipeline: load FAERS Parquet into Postgres.

Strategy:
1. Deduplicate reports by keeping the latest caseversion per caseid.
2. Identify GLP-1 cohort: reports where at least one drug matches a GLP-1.
3. Load full detail (reports, drugs, reactions, outcomes, indications) for
   the GLP-1 cohort only.
4. Build background aggregate tables from the ENTIRE FAERS universe
   for disproportionality analysis.
"""
from pathlib import Path
from io import StringIO

import polars as pl
from sqlalchemy import create_engine, text

from src.config import PROCESSED_DIR, DATABASE_URL, FAERS_QUARTERS
from src.etl.normalize import (
    build_glp1_matcher,
    add_glp1_flag,
    parse_age_to_years,
)


engine = create_engine(DATABASE_URL)


def load_glp1_matcher() -> dict[str, str]:
    """Load the GLP-1 dictionary from the database and build a name matcher."""
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT active_ingredient, brand_names FROM glp1_drugs"
        )).mappings().all()
    return build_glp1_matcher([dict(r) for r in rows])


def read_quarter(quarter: str) -> dict[str, pl.DataFrame]:
    """Read all Parquet files for a quarter into a dict of DataFrames."""
    qdir = PROCESSED_DIR / quarter
    return {
        table: pl.read_parquet(qdir / f"{table.lower()}.parquet")
        for table in ["demo", "drug", "reac", "outc", "indi"]
    }


def deduplicate_demo(demo: pl.DataFrame) -> pl.DataFrame:
    """Keep latest caseversion per caseid."""
    return (
        demo.sort(["caseid", "caseversion"], descending=[False, True])
        .unique(subset=["caseid"], keep="first")
    )


def identify_glp1_cohort(
        drug: pl.DataFrame,
        matcher: dict[str, str],
) -> tuple[pl.DataFrame, set[int]]:
    """Return the drug DF with a glp1_active_ingredient column and the set of
    primaryids that mention any GLP-1 drug."""
    drug = add_glp1_flag(drug, matcher)
    glp1_pids = set(
        drug.filter(pl.col("glp1_active_ingredient").is_not_null())
        .get_column("primaryid")
        .unique()
        .to_list()
    )
    return drug, glp1_pids


def build_reports_frame(demo: pl.DataFrame, quarter: str) -> pl.DataFrame:
    """Transform DEMO into the shape expected by the `reports` table."""
    return (
        demo.select([
            "primaryid",
            "caseid",
            "caseversion",
            pl.col("event_dt").cast(pl.Utf8),
            pl.col("fda_dt").cast(pl.Utf8),
            pl.col("age").cast(pl.Float64, strict=False),
            pl.col("age_cod").alias("age_unit"),
            "sex",
            pl.col("reporter_country"),
            pl.col("occr_country").alias("occur_country"),
            pl.col("rept_cod").alias("reporter_type"),
        ])
        .with_columns([
            pl.lit(quarter).alias("faers_quarter"),
            # Normalize age to years
            pl.struct(["age", "age_unit"]).map_elements(
                lambda r: parse_age_to_years(r["age"], r["age_unit"]),
                return_dtype=pl.Float64,
            ).alias("age_years"),
        ])
        .drop("age")
        .rename({"age_years": "age"})
        .with_columns([
            # Parse YYYYMMDD dates leniently
            pl.col("event_dt").str.strptime(pl.Date, "%Y%m%d", strict=False),
            pl.col("fda_dt").str.strptime(pl.Date, "%Y%m%d", strict=False),
        ])
    )


def copy_dataframe(df: pl.DataFrame, table: str, columns: list[str]):
    """Bulk-load a DataFrame into Postgres using COPY.

    Uses CSV format with tab delimiter and empty string as NULL marker,
    which avoids issues with `\\N` being misinterpreted in numeric columns.
    """
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


def load_quarter(quarter: str, matcher: dict[str, str]):
    """Full ETL for a single quarter."""
    print(f"\n=== Loading {quarter} ===")
    tables = read_quarter(quarter)

    # 1. Deduplicate DEMO by caseid
    demo = deduplicate_demo(tables["demo"])
    print(f"  DEMO: {len(tables['demo']):,} -> {len(demo):,} after dedupe")

    valid_pids = set(demo["primaryid"].to_list())

    # 2. Identify GLP-1 cohort
    drug_with_flag, glp1_pids = identify_glp1_cohort(tables["drug"], matcher)
    glp1_pids &= valid_pids  # Intersect with deduplicated reports
    print(f"  GLP-1 cohort: {len(glp1_pids):,} reports")

    # 3. Filter all tables to the cohort
    demo_cohort = demo.filter(pl.col("primaryid").is_in(list(glp1_pids)))
    drug_cohort = drug_with_flag.filter(pl.col("primaryid").is_in(list(glp1_pids)))
    reac_cohort = tables["reac"].filter(pl.col("primaryid").is_in(list(glp1_pids)))
    outc_cohort = tables["outc"].filter(pl.col("primaryid").is_in(list(glp1_pids)))
    indi_cohort = tables["indi"].filter(pl.col("primaryid").is_in(list(glp1_pids)))

    # 4. Load `reports`
    reports_df = build_reports_frame(demo_cohort, quarter)
    copy_dataframe(reports_df, "reports", [
        "primaryid", "caseid", "caseversion", "event_dt", "fda_dt",
        "age", "age_unit", "sex", "reporter_country", "occur_country",
        "reporter_type", "faers_quarter",
    ])
    print(f"  reports: {len(reports_df):,} rows loaded")

    # 5. Load `drugs`
    drugs_df = drug_cohort.select([
        "primaryid",
        pl.col("drug_seq").cast(pl.Int32, strict=False),
        "role_cod",
        "drugname",
        "prod_ai",
        "route",
        pl.col("dose_amt").cast(pl.Float64, strict=False),
        pl.col("dose_unit"),
        pl.col("glp1_active_ingredient").is_not_null().alias("is_glp1"),
    ])
    copy_dataframe(drugs_df, "drugs", [
        "primaryid", "drug_seq", "role_cod", "drugname", "prod_ai",
        "route", "dose_amt", "dose_unit", "is_glp1",
    ])
    print(f"  drugs: {len(drugs_df):,} rows loaded")

    # 6. Load `reactions`
    copy_dataframe(reac_cohort, "reactions", [
        "primaryid", "pt", "drug_rec_act",
    ])
    print(f"  reactions: {len(reac_cohort):,} rows loaded")

    # 7. Load `outcomes`
    copy_dataframe(outc_cohort, "outcomes", ["primaryid", "outc_cod"])
    print(f"  outcomes: {len(outc_cohort):,} rows loaded")

    # 8. Load `indications`
    indi_df = indi_cohort.select([
        "primaryid",
        pl.col("indi_drug_seq").cast(pl.Int32, strict=False),
        "indi_pt",
    ])
    copy_dataframe(indi_df, "indications", [
        "primaryid", "indi_drug_seq", "indi_pt",
    ])
    print(f"  indications: {len(indi_df):,} rows loaded")


def load_all():
    """Run the full ETL for all configured quarters."""
    matcher = load_glp1_matcher()
    print(f"GLP-1 matcher loaded with {len(matcher)} name variants")
    for quarter in FAERS_QUARTERS:
        load_quarter(quarter, matcher)
    print("\nCohort ETL complete.")


if __name__ == "__main__":
    load_all()