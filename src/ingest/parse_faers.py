"""Parse FAERS ASCII files into Parquet format for efficient downstream processing."""
from pathlib import Path

import polars as pl

from src.config import RAW_DIR, PROCESSED_DIR, FAERS_QUARTERS

FAERS_TABLES = ["DEMO", "DRUG", "REAC", "OUTC", "RPSR", "THER", "INDI"]


def find_ascii_file(quarter_dir: Path, table: str) -> Path | None:
    """Locate a specific FAERS table file inside a quarter directory."""
    matches = list(quarter_dir.rglob(f"{table}*.txt"))
    return matches[0] if matches else None


def parse_table(path: Path, table: str, quarter: str) -> pl.DataFrame:
    """Parse a single FAERS ASCII file into a Polars DataFrame."""
    df = pl.read_csv(
        path,
        separator="$",
        infer_schema_length=10_000,
        ignore_errors=True,
        truncate_ragged_lines=True,
    )
    # Normalize column names to lowercase for consistency
    df = df.rename({c: c.lower() for c in df.columns})
    # Tag each row with its source quarter for auditability
    df = df.with_columns(pl.lit(quarter).alias("faers_quarter"))
    return df


def parse_quarter(quarter: str) -> dict[str, Path]:
    """Parse all tables of a quarter and write them as Parquet files."""
    quarter_dir = RAW_DIR / quarter
    output_dir = PROCESSED_DIR / quarter
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {}
    for table in FAERS_TABLES:
        ascii_path = find_ascii_file(quarter_dir, table)
        if ascii_path is None:
            print(f"  [warn] {quarter} {table}: file not found")
            continue

        df = parse_table(ascii_path, table, quarter)
        parquet_path = output_dir / f"{table.lower()}.parquet"
        df.write_parquet(parquet_path, compression="snappy")
        results[table] = parquet_path
        print(f"  [ok] {table}: {len(df):,} rows -> {parquet_path.name}")

    return results


def parse_all():
    """Parse every configured FAERS quarter."""
    for quarter in FAERS_QUARTERS:
        print(f"\n=== Parsing {quarter} ===")
        parse_quarter(quarter)


if __name__ == "__main__":
    parse_all()
    print("\nAll quarters parsed successfully.")