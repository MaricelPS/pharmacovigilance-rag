"""Quick inspection of downloaded FAERS files."""
import sys
from pathlib import Path

# Add project root to sys.path so `src` is importable when run as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import polars as pl

from src.config import RAW_DIR, FAERS_QUARTERS

def find_ascii_files(quarter_dir: Path) -> dict[str, Path]:
    """Locate the seven FAERS ASCII files inside a quarter folder."""
    tables = ["DEMO", "DRUG", "REAC", "OUTC", "RPSR", "THER", "INDI"]
    files = {}
    for table in tables:
        matches = list(quarter_dir.rglob(f"{table}*.txt"))
        if matches:
            files[table] = matches[0]
    return files


def preview_quarter(quarter: str):
    """Print row counts and a preview of each table for a quarter."""
    quarter_dir = RAW_DIR / quarter
    files = find_ascii_files(quarter_dir)

    print(f"\n{'='*60}")
    print(f"Quarter: {quarter}")
    print(f"{'='*60}")

    for table, path in files.items():
        try:
            df = pl.read_csv(
                path,
                separator="$",
                infer_schema_length=1000,
                ignore_errors=True,
            )
            print(f"\n[{table}] {path.name} - {len(df):,} rows, {len(df.columns)} cols")
            print(f"Columns: {df.columns[:10]}{'...' if len(df.columns) > 10 else ''}")
        except Exception as e:
            print(f"\n[{table}] ERROR reading {path.name}: {e}")


if __name__ == "__main__":
    for q in FAERS_QUARTERS:
        preview_quarter(q)