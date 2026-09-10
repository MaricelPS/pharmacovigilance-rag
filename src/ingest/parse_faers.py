# src/ingest/parse_faers.py
import polars as pl

def parse_file(path: Path, table: str) -> pl.DataFrame:
    return pl.read_csv(
        path, separator="$", infer_schema_length=10000,
        ignore_errors=True
    ).with_columns(pl.lit(table).alias("source_table"))

# Repetir para DEMO, DRUG, REAC, OUTC, INDI