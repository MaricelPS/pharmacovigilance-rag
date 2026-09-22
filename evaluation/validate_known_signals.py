"""Validate that the pharmacovigilance system detects known GLP-1 safety
signals published in peer-reviewed literature or regulatory communications.

For each known drug-event pair, we check whether the system's precomputed
signal table (glp1_signals) flags it as a signal under either EMA criteria
(PRR>=2, chi2>=4, n>=3) or BCPNN criteria (IC lower CI > 0).
"""
import json
import sys
from pathlib import Path

import yaml
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import DATABASE_URL


DATASET_PATH = Path(__file__).parent / "known_signals.yaml"
RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

engine = create_engine(DATABASE_URL)


def load_dataset() -> list[dict]:
    """Load the known signals dataset from YAML."""
    with open(DATASET_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["items"]


def check_signal(drug: str, event_pts: list[str]) -> dict:
    """Query glp1_signals for the given drug-event combinations.

    Returns the best-matching PT (highest IC) among the candidates,
    with its metrics and signal flags.
    """
    sql = text("""
        SELECT event_pt, a, prr, prr_chi2, ror, ror_ci_low, ror_ci_high,
               ic, ic_ci_low, is_signal_ema, is_signal_bcpnn
        FROM glp1_signals
        WHERE drug_key = :drug AND event_pt = ANY(:pts)
        ORDER BY ic DESC NULLS LAST
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql, {"drug": drug, "pts": event_pts}).mappings().all()

    if not rows:
        return {
            "found": False,
            "best_match_pt": None,
            "matches": [],
        }

    best = dict(rows[0])
    return {
        "found": True,
        "best_match_pt": best["event_pt"],
        "matches": [dict(r) for r in rows],
        "a": int(best["a"]),
        "prr": float(best["prr"]) if best["prr"] is not None else None,
        "ror": float(best["ror"]) if best["ror"] is not None else None,
        "ror_ci_low": float(best["ror_ci_low"]) if best["ror_ci_low"] is not None else None,
        "ror_ci_high": float(best["ror_ci_high"]) if best["ror_ci_high"] is not None else None,
        "ic": float(best["ic"]) if best["ic"] is not None else None,
        "ic_ci_low": float(best["ic_ci_low"]) if best["ic_ci_low"] is not None else None,
        "is_signal_ema": bool(best["is_signal_ema"]),
        "is_signal_bcpnn": bool(best["is_signal_bcpnn"]),
    }


def evaluate_all(items: list[dict]) -> list[dict]:
    """Check every known signal against the database."""
    results = []
    for item in items:
        result = check_signal(item["drug"], item["event_pts"])
        results.append({
            "id": item["id"],
            "drug": item["drug"],
            "event_pts": item["event_pts"],
            "year": item["year"],
            "source": item["literature_source"].strip(),
            **result,
        })
    return results


def summarize(results: list[dict]) -> dict:
    """Aggregate detection rates."""
    n = len(results)
    n_found = sum(r["found"] for r in results)
    n_ema = sum(r["found"] and r.get("is_signal_ema", False) for r in results)
    n_bcpnn = sum(r["found"] and r.get("is_signal_bcpnn", False) for r in results)
    n_either = sum(
        r["found"] and (r.get("is_signal_ema", False) or r.get("is_signal_bcpnn", False))
        for r in results
    )

    return {
        "total_known_signals": n,
        "found_in_data": n_found,
        "found_rate": n_found / n,
        "detected_by_ema": n_ema,
        "detected_by_bcpnn": n_bcpnn,
        "detected_by_either": n_either,
        "detection_rate_either": n_either / n,
        "detection_rate_ema": n_ema / n,
        "detection_rate_bcpnn": n_bcpnn / n,
    }


def build_report(items: list[dict], results: list[dict], metrics: dict) -> str:
    """Render a Markdown validation report."""
    lines = ["# Known Signals Validation Report\n"]
    lines.append(
        "Validates that our disproportionality analysis on FAERS 2024 "
        "detects safety signals published in peer-reviewed literature or "
        "reported by regulatory agencies (FDA, EMA).\n"
    )

    lines.append("## Overall detection metrics\n")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Known signals evaluated | {metrics['total_known_signals']} |")
    lines.append(f"| Present in FAERS 2024   | "
                 f"{metrics['found_in_data']} ({metrics['found_rate']:.0%}) |")
    lines.append(f"| Detected (EMA criteria) | "
                 f"{metrics['detected_by_ema']} ({metrics['detection_rate_ema']:.0%}) |")
    lines.append(f"| Detected (BCPNN)        | "
                 f"{metrics['detected_by_bcpnn']} ({metrics['detection_rate_bcpnn']:.0%}) |")
    lines.append(f"| Detected (either)       | "
                 f"{metrics['detected_by_either']} ({metrics['detection_rate_either']:.0%}) |")

    lines.append("\n## Per-signal breakdown\n")
    lines.append(
        "| ID | Drug | Best-match PT | n | ROR (95% CI) | IC | EMA | BCPNN | Year |")
    lines.append(
        "|----|------|---------------|---|--------------|----|-----|-------|------|")
    for r in results:
        if not r["found"]:
            lines.append(
                f"| {r['id']} | {r['drug']} | *not present* | — | — | — | — | — | {r['year']} |"
            )
            continue
        ror_str = (
            f"{r['ror']:.2f} ({r['ror_ci_low']:.2f}-{r['ror_ci_high']:.2f})"
            if r['ror'] is not None else "—"
        )
        ic_str = f"{r['ic']:.2f}" if r['ic'] is not None else "—"
        ema = "yes" if r.get("is_signal_ema") else "no"
        bcpnn = "yes" if r.get("is_signal_bcpnn") else "no"
        lines.append(
            f"| {r['id']} | {r['drug']} | {r['best_match_pt']} | "
            f"{r['a']} | {ror_str} | {ic_str} | {ema} | {bcpnn} | {r['year']} |"
        )

    lines.append("\n## Detailed references\n")
    for item, r in zip(items, results):
        lines.append(f"### {item['id']} — {item['drug']} × {item['event_pts']}")
        lines.append(f"**Source**: {item['literature_source'].strip()}")
        lines.append(f"**Notes**: {item['notes'].strip()}\n")
        if r["found"]:
            lines.append(f"- Best match: **{r['best_match_pt']}**, "
                         f"n={r['a']}, ROR={r['ror']:.2f}, IC={r['ic']:.2f}")
            lines.append(f"- Signal EMA: {r['is_signal_ema']}, "
                         f"BCPNN: {r['is_signal_bcpnn']}")
        else:
            lines.append("- **Not present in FAERS 2024 cohort.**")
        lines.append("")

    return "\n".join(lines)


def main():
    items = load_dataset()
    print(f"Loaded {len(items)} known signals.\n")

    results = evaluate_all(items)
    metrics = summarize(results)

    (RESULTS_DIR / "known_signals_results.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    (RESULTS_DIR / "known_signals_metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (RESULTS_DIR / "known_signals_report.md").write_text(
        build_report(items, results, metrics),
        encoding="utf-8",
    )

    print("=== Detection Metrics ===")
    for k, v in metrics.items():
        if isinstance(v, float):
            print(f"  {k}: {v:.1%}" if "rate" in k else f"  {k}: {v:.2f}")
        else:
            print(f"  {k}: {v}")

    print("\nPer-signal summary:")
    for r in results:
        status = (
            "DETECTED" if r["found"] and (r.get("is_signal_ema") or r.get("is_signal_bcpnn"))
            else "PRESENT-NOT-SIGNAL" if r["found"]
            else "MISSING"
        )
        print(f"  {r['id']} {r['drug']:>12} × {r['event_pts'][0]:<30} → {status}")

    print(f"\nReport saved to: {RESULTS_DIR / 'known_signals_report.md'}")


if __name__ == "__main__":
    main()