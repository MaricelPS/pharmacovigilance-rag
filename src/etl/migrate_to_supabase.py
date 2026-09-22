"""Migrate cohort tables from the local Docker Postgres to Supabase.

Copies only the tables required by the production Streamlit app:
    reports, drugs, reactions, outcomes, indications,
    glp1_signals, pt_embeddings, glp1_drugs

Uses server-side COPY TO STDOUT / COPY FROM STDIN for bulk transfer.
"""
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from src.config import DATABASE_URL


# Load Supabase connection string from separate file
load_dotenv(".env.supabase")
SUPABASE_URL = os.getenv("SUPABASE_DATABASE_URL")

if not SUPABASE_URL:
    raise SystemExit("SUPABASE_DATABASE_URL not found in .env.supabase")


# Ordered so foreign keys are respected on insert
MIGRATION_ORDER = [
    "glp1_drugs",       # Independent, small
    "reports",          # Parent of drugs/reactions/outcomes/indications
    "drugs",
    "reactions",
    "outcomes",
    "indications",
    "glp1_signals",     # Independent
    "pt_embeddings",    # Independent, largest by row width
]

# Columns to copy per table (matches schema in init_supabase.sql)
TABLE_COLUMNS = {
    "glp1_drugs":    ["active_ingredient", "brand_names", "indication_class"],
    "reports":       ["primaryid", "caseid", "caseversion", "event_dt",
                      "fda_dt", "age", "age_unit", "sex", "reporter_country",
                      "occur_country", "reporter_type", "serious",
                      "faers_quarter"],
    "drugs":         ["id", "primaryid", "drug_seq", "role_cod", "drugname",
                      "prod_ai", "route", "dose_amt", "dose_unit", "is_glp1"],
    "reactions":     ["id", "primaryid", "pt", "drug_rec_act"],
    "outcomes":      ["id", "primaryid", "outc_cod"],
    "indications":   ["id", "primaryid", "indi_drug_seq", "indi_pt"],
    "glp1_signals":  ["drug_key", "event_pt", "a", "b", "c", "d",
                      "prr", "prr_chi2", "ror", "ror_ci_low", "ror_ci_high",
                      "ic", "ic_ci_low", "is_signal_ema", "is_signal_bcpnn"],
    "pt_embeddings": ["pt", "embedding"],
}


local_engine = create_engine(DATABASE_URL)
supabase_engine = create_engine(SUPABASE_URL)


def truncate_target(table: str):
    """Empty the destination table (idempotent re-runs)."""
    with supabase_engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {table} CASCADE"))


def source_row_count(table: str) -> int:
    """Row count in the local source table."""
    with local_engine.connect() as conn:
        return conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()


def target_row_count(table: str) -> int:
    """Row count in the Supabase target table."""
    with supabase_engine.connect() as conn:
        return conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()


def migrate_table(table: str, columns: list[str]):
    """Copy one table from local Postgres to Supabase.

    Uses BINARY format for pt_embeddings (vector type transfers cleanly)
    and CSV for everything else (broader compatibility).
    """
    cols = ", ".join(columns)
    fmt = "BINARY" if table == "pt_embeddings" else "CSV"

    n_source = source_row_count(table)
    print(f"\n[{table}] {n_source:,} rows to migrate (format={fmt})")

    if n_source == 0:
        print(f"[{table}] source empty, skipping")
        return

    print(f"[{table}] truncating target...")
    truncate_target(table)

    # Stream: local COPY TO STDOUT -> in-memory buffer -> Supabase COPY FROM STDIN
    from io import BytesIO
    buf = BytesIO()

    print(f"[{table}] exporting from local Postgres...")
    t0 = time.time()
    local_raw = local_engine.raw_connection()
    try:
        with local_raw.cursor() as cur:
            cur.copy_expert(
                f"COPY {table} ({cols}) TO STDOUT WITH (FORMAT {fmt})",
                buf,
            )
    finally:
        local_raw.close()

    size_mb = buf.tell() / (1024 * 1024)
    print(f"[{table}] exported {size_mb:.1f} MB in {time.time() - t0:.1f}s")

    buf.seek(0)

    print(f"[{table}] uploading to Supabase...")
    t0 = time.time()
    supabase_raw = supabase_engine.raw_connection()
    try:
        with supabase_raw.cursor() as cur:
            cur.copy_expert(
                f"COPY {table} ({cols}) FROM STDIN WITH (FORMAT {fmt})",
                buf,
            )
        supabase_raw.commit()
    finally:
        supabase_raw.close()

    print(f"[{table}] uploaded in {time.time() - t0:.1f}s")

    # Verify
    n_target = target_row_count(table)
    if n_target != n_source:
        print(f"[{table}] WARNING: source={n_source:,} target={n_target:,}")
    else:
        print(f"[{table}] OK: {n_target:,} rows")


def reset_sequences():
    """Reset BIGSERIAL sequences to max(id) so future inserts don't collide."""
    print("\n[sequences] resetting BIGSERIAL sequences on target...")
    tables_with_serial = ["drugs", "reactions", "outcomes", "indications"]
    with supabase_engine.begin() as conn:
        for t in tables_with_serial:
            conn.execute(text(f"""
                SELECT setval(
                    pg_get_serial_sequence('{t}', 'id'),
                    COALESCE((SELECT MAX(id) FROM {t}), 1),
                    true
                )
            """))
            print(f"  [{t}] sequence updated")


def main():
    print("=" * 60)
    print(" FAERS -> Supabase migration")
    print("=" * 60)
    total_t0 = time.time()

    for table in MIGRATION_ORDER:
        migrate_table(table, TABLE_COLUMNS[table])

    reset_sequences()

    total_min = (time.time() - total_t0) / 60
    print(f"\nMigration complete in {total_min:.1f} minutes.")


if __name__ == "__main__":
    main()