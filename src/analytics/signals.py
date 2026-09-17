"""Signal detection queries against the aggregate tables in Postgres."""
from dataclasses import asdict

import polars as pl
from sqlalchemy import create_engine, text

from src.config import DATABASE_URL
from src.analytics.disproportionality import compute_metrics, SignalMetrics


engine = create_engine(DATABASE_URL)


def get_contingency(
        drug_key: str,
        event_pt: str,
        quarters: list[str] | None = None,
) -> tuple[int, int, int, int]:
    """Build the 2x2 contingency table (a, b, c, d) for a drug-event pair.

    Args:
        drug_key: Normalized active ingredient.
        event_pt: MedDRA Preferred Term.
        quarters: Optional list of FAERS quarters to restrict the analysis.
            None means all loaded quarters.

    Returns:
        Tuple (a, b, c, d) where:
            a = reports with drug AND event
            b = reports with drug, without event
            c = reports without drug, with event
            d = reports without drug, without event
    """
    quarter_filter = ""
    params = {"drug_key": drug_key, "event_pt": event_pt}

    if quarters:
        quarter_filter = "WHERE faers_quarter = ANY(:quarters)"
        params["quarters"] = quarters

    sql = text(f"""
    WITH
    n_total AS (
        SELECT COALESCE(SUM(n_reports), 0)::BIGINT AS n
        FROM quarter_totals
        {quarter_filter}
    ),
    n_drug AS (
        SELECT COALESCE(SUM(n_reports), 0)::BIGINT AS n
        FROM drug_totals
        WHERE drug_key = :drug_key
        {"AND faers_quarter = ANY(:quarters)" if quarters else ""}
    ),
    n_event AS (
        SELECT COALESCE(SUM(n_reports), 0)::BIGINT AS n
        FROM event_totals
        WHERE event_pt = :event_pt
        {"AND faers_quarter = ANY(:quarters)" if quarters else ""}
    ),
    n_both AS (
        SELECT COALESCE(SUM(n_reports), 0)::BIGINT AS n
        FROM drug_event_counts
        WHERE drug_key = :drug_key AND event_pt = :event_pt
        {"AND faers_quarter = ANY(:quarters)" if quarters else ""}
    )
    SELECT
        (SELECT n FROM n_both)                             AS a,
        (SELECT n FROM n_drug)  - (SELECT n FROM n_both)   AS b,
        (SELECT n FROM n_event) - (SELECT n FROM n_both)   AS c,
        (SELECT n FROM n_total) - (SELECT n FROM n_drug)
                                - (SELECT n FROM n_event)
                                + (SELECT n FROM n_both)   AS d;
    """)

    with engine.connect() as conn:
        row = conn.execute(sql, params).mappings().one()
    return int(row["a"]), int(row["b"]), int(row["c"]), int(row["d"])


def compute_signal(
        drug_key: str,
        event_pt: str,
        quarters: list[str] | None = None,
) -> SignalMetrics:
    """Compute disproportionality metrics for a single drug-event pair."""
    a, b, c, d = get_contingency(drug_key, event_pt, quarters)
    return compute_metrics(a, b, c, d)


def scan_signals_for_drug(
        drug_key: str,
        quarters: list[str] | None = None,
        min_cases: int = 3,
) -> pl.DataFrame:
    """Scan all events reported with a drug and compute metrics for each.

    Filters to events with at least `min_cases` co-occurrences to avoid
    noise from tiny cell counts.

    Returns a Polars DataFrame sorted by IC descending.
    """
    quarter_filter = ""
    params = {"drug_key": drug_key, "min_cases": min_cases}
    if quarters:
        quarter_filter = "AND faers_quarter = ANY(:quarters)"
        params["quarters"] = quarters

    sql = text(f"""
        SELECT event_pt, SUM(n_reports)::BIGINT AS n_both
        FROM drug_event_counts
        WHERE drug_key = :drug_key {quarter_filter}
        GROUP BY event_pt
        HAVING SUM(n_reports) >= :min_cases
        ORDER BY n_both DESC
    """)

    with engine.connect() as conn:
        rows = conn.execute(sql, params).mappings().all()

    print(f"Scanning {len(rows)} events for '{drug_key}'...")
    results = []
    for row in rows:
        metrics = compute_signal(drug_key, row["event_pt"], quarters)
        results.append({
            "event_pt": row["event_pt"],
            **asdict(metrics),
        })

    return (
        pl.DataFrame(results)
        .sort("ic", descending=True)
    )


if __name__ == "__main__":
    # Demo: top signals for semaglutide
    print("\n=== Top signals for semaglutide (2024) ===\n")
    df = scan_signals_for_drug("semaglutide", min_cases=10)
    top = df.filter(pl.col("is_signal_ema")).head(20)
    print(top.select([
        "event_pt", "a", "prr", "prr_chi2",
        "ror", "ror_ci_low", "ror_ci_high",
        "ic", "ic_ci_low", "is_signal_ema", "is_signal_bcpnn",
    ]))