"""Concrete implementations of the tools exposed to the LLM agent."""
from dataclasses import asdict

import polars as pl
from sqlalchemy import create_engine, text

from src.config import DATABASE_URL
from src.analytics.signals import scan_signals_for_drug, compute_signal
from src.rag.semantic_search import search_pts


engine = create_engine(DATABASE_URL)


def tool_semantic_event_search(query: str, top_k: int = 10) -> list[dict]:
    """Return top PTs matching the natural-language query."""
    df = search_pts(query, top_k=top_k, min_similarity=0.35)
    return df.to_dicts()


def tool_detect_signals(
        drug_key: str, min_cases: int = 10, top_n: int = 20
) -> list[dict]:
    """Scan and return top signals for a drug ranked by IC."""
    df = scan_signals_for_drug(drug_key, min_cases=min_cases)
    top = (
        df.filter(pl.col("is_signal_ema") | pl.col("is_signal_bcpnn"))
        .head(top_n)
        .select([
            "event_pt", "a", "prr", "prr_chi2",
            "ror", "ror_ci_low", "ror_ci_high",
            "ic", "ic_ci_low", "is_signal_ema", "is_signal_bcpnn",
        ])
    )
    return top.to_dicts()


def tool_query_cohort_events(
        drug_key: str | None = None,
        event_pts: list[str] | None = None,
        age_min: float | None = None,
        age_max: float | None = None,
        sex: str | None = None,
        serious_only: bool = False,
        top_n: int = 20,
) -> dict:
    """Aggregate cohort-level counts filtered by demographics and outcome."""
    filters = ["d.is_glp1 = TRUE"]
    params: dict = {"top_n": top_n}

    if drug_key:
        filters.append(
            "(LOWER(d.drugname) LIKE :drug_pattern OR "
            "LOWER(d.prod_ai) LIKE :drug_pattern)"
        )
        params["drug_pattern"] = f"%{drug_key.lower()}%"
    if event_pts:
        filters.append("r.pt = ANY(:event_pts)")
        params["event_pts"] = event_pts
    if age_min is not None:
        filters.append("rep.age >= :age_min")
        params["age_min"] = age_min
    if age_max is not None:
        filters.append("rep.age <= :age_max")
        params["age_max"] = age_max
    if sex:
        filters.append("rep.sex = :sex")
        params["sex"] = sex
    if serious_only:
        filters.append(
            "EXISTS (SELECT 1 FROM outcomes o WHERE o.primaryid = rep.primaryid "
            "AND o.outc_cod IN ('DE','LT','HO','DS','CA'))"
        )

    where_clause = " AND ".join(filters)

    sql = text(f"""
        SELECT r.pt AS event_pt,
               COUNT(DISTINCT rep.primaryid) AS n_reports
        FROM reports rep
        JOIN drugs d ON d.primaryid = rep.primaryid
        JOIN reactions r ON r.primaryid = rep.primaryid
        WHERE {where_clause}
        GROUP BY r.pt
        ORDER BY n_reports DESC
        LIMIT :top_n
    """)

    with engine.connect() as conn:
        rows = conn.execute(sql, params).mappings().all()

    return {
        "filters_applied": {
            "drug_key": drug_key, "event_pts": event_pts,
            "age_min": age_min, "age_max": age_max,
            "sex": sex, "serious_only": serious_only,
        },
        "n_events_returned": len(rows),
        "events": [dict(r) for r in rows],
    }


def tool_compare_drugs(drug_keys: list[str], event_pts: list[str]) -> list[dict]:
    """Compute disproportionality metrics for each (drug, event) combination."""
    results = []
    for drug in drug_keys:
        for event in event_pts:
            m = compute_signal(drug, event)
            results.append({
                "drug_key": drug,
                "event_pt": event,
                **{k: v for k, v in asdict(m).items()
                   if k in ("a", "prr", "prr_chi2", "ror",
                            "ror_ci_low", "ror_ci_high",
                            "ic", "ic_ci_low",
                            "is_signal_ema", "is_signal_bcpnn")},
            })
    return results


TOOL_DISPATCH = {
    "semantic_event_search": tool_semantic_event_search,
    "detect_signals": tool_detect_signals,
    "query_cohort_events": tool_query_cohort_events,
    "compare_drugs": tool_compare_drugs,
}