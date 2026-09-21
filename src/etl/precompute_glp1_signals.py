"""Precompute disproportionality metrics for every GLP-1 drug × event pair.

Runs once (locally, against the full drug_event_counts table) and stores
results in glp1_signals. In production we drop drug_event_counts and
serve queries from this small table instead.
"""
from dataclasses import asdict

from sqlalchemy import create_engine, text
from tqdm import tqdm

from src.config import DATABASE_URL
from src.analytics.signals import compute_signal


engine = create_engine(DATABASE_URL)


GLP1_ACTIVE_INGREDIENTS = [
    "semaglutide", "liraglutide", "tirzepatide",
    "dulaglutide", "exenatide", "lixisenatide",
]

MIN_CASES = 3  # Skip pairs with fewer than 3 co-occurrences


def get_events_for_drug(drug_key: str, min_cases: int) -> list[str]:
    """Return all events reported at least `min_cases` times with the drug."""
    sql = text("""
        SELECT event_pt, SUM(n_reports)::BIGINT AS n
        FROM drug_event_counts
        WHERE drug_key = :drug_key
        GROUP BY event_pt
        HAVING SUM(n_reports) >= :min_cases
    """)
    with engine.connect() as conn:
        rows = conn.execute(
            sql, {"drug_key": drug_key, "min_cases": min_cases}
        ).mappings().all()
    return [r["event_pt"] for r in rows]


def truncate_signals():
    """Clear existing precomputed signals."""
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE glp1_signals;"))


def insert_signals(rows: list[dict]):
    """Bulk insert precomputed signals."""
    if not rows:
        return
    sql = text("""
        INSERT INTO glp1_signals
        (drug_key, event_pt, a, b, c, d,
         prr, prr_chi2, ror, ror_ci_low, ror_ci_high,
         ic, ic_ci_low, is_signal_ema, is_signal_bcpnn)
        VALUES
        (:drug_key, :event_pt, :a, :b, :c, :d,
         :prr, :prr_chi2, :ror, :ror_ci_low, :ror_ci_high,
         :ic, :ic_ci_low, :is_signal_ema, :is_signal_bcpnn)
        ON CONFLICT (drug_key, event_pt) DO NOTHING
    """)
    with engine.begin() as conn:
        conn.execute(sql, rows)


def precompute_all():
    """Compute metrics for every GLP-1 × event pair and store them."""
    truncate_signals()
    total_inserted = 0

    for drug in GLP1_ACTIVE_INGREDIENTS:
        events = get_events_for_drug(drug, MIN_CASES)
        print(f"\n=== {drug}: {len(events)} events ===")

        batch = []
        for event in tqdm(events, desc=drug):
            m = compute_signal(drug, event)
            batch.append({
                "drug_key": drug,
                "event_pt": event,
                **{k: v for k, v in asdict(m).items()
                   if k in ("a", "b", "c", "d",
                            "prr", "prr_chi2",
                            "ror", "ror_ci_low", "ror_ci_high",
                            "ic", "ic_ci_low",
                            "is_signal_ema", "is_signal_bcpnn")},
            })
            if len(batch) >= 500:
                insert_signals(batch)
                total_inserted += len(batch)
                batch = []
        if batch:
            insert_signals(batch)
            total_inserted += len(batch)

    print(f"\nDone. Inserted {total_inserted:,} precomputed signal rows.")


if __name__ == "__main__":
    precompute_all()