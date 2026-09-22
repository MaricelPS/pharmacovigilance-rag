"""Run the evaluation dataset through the pharmacovigilance agent.

Outputs:
    - evaluation/results/traces.json: full trace of each question
    - evaluation/results/metrics.json: aggregated metrics
    - evaluation/results/report.md: human-readable report
"""
import json
import sys
import time
import re
from pathlib import Path

import yaml

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.rag.agent import ask_with_trace


DATASET_PATH = Path(__file__).parent / "eval_dataset.yaml"
RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


# Map user-friendly tool names to actual agent tools
TOOL_ALIASES = {
    "semantic_event_search": {"semantic_event_search", "semantic_search"},
    "detect_signals": {"detect_signals", "get_open_signals"},
    "query_cohort_events": {"query_cohort_events", "check_subgroup"},
    "compare_drugs": {"compare_drugs"},
    # Edge cases and "check_signal" are ambiguous — evaluated separately
    "check_signal": {"semantic_event_search", "detect_signals",
                     "query_cohort_events", "compare_drugs"},
    "handle_invalid_drug": set(),  # No tool call expected, or graceful rejection
    "handle_absurd_event": set(),
}


def load_dataset() -> list[dict]:
    """Load the evaluation dataset from YAML."""
    with open(DATASET_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["items"]


# Bilingual synonym map for MedDRA PT matching.
# Maps English canonical form -> list of acceptable substrings (case-insensitive).
PT_SYNONYMS = {
    "injection site": [
        "injection site",
        "sitio de inyección",
        "sitio inyección",
        "reacción en el sitio",
    ],
    "incorrect dose administered": [
        "incorrect dose administered",
        "dosis incorrecta",
        "dosis incorrecta administrada",
    ],
    "impaired gastric emptying": [
        "impaired gastric emptying",
        "vaciamiento gástrico",
        "vaciado gástrico",
    ],
    "optic ischaemic neuropathy": [
        "optic ischaemic neuropathy",
        "optic ischemic neuropathy",
        "neuropatía óptica isquémica",
        "naion",
    ],
    "ischaemic optic neuropathy": [
        "ischaemic optic neuropathy",
        "ischemic optic neuropathy",
        "neuropatía óptica isquémica",
        "naion",
    ],
    "optic nerve infarction": [
        "optic nerve infarction",
        "infarto del nervio óptico",
    ],
    "hepatic function abnormal": [
        "hepatic function abnormal",
        "función hepática anormal",
        "funcion hepatica",
    ],
    "pancreatitis": ["pancreatitis"],
    "pancreatitis acute": [
        "pancreatitis acute",
        "pancreatitis aguda",
    ],
    "gastroparesis": [
        "gastroparesis",
        "gastroparesia",
        "vaciamiento gástrico",
        "impaired gastric emptying",
    ],
    "gastric emptying impaired": [
        "gastric emptying impaired",
        "impaired gastric emptying",
        "vaciamiento gástrico",
    ],
    "gastric hypomotility": [
        "gastric hypomotility",
        "hipomotilidad gástrica",
        "hipomotilidad",
    ],
    "suicidal ideation": [
        "suicidal ideation",
        "ideación suicida",
        "ideacion suicida",
    ],
    "suicide attempt": [
        "suicide attempt",
        "intento de suicidio",
    ],
    "aspiration pneumonia": [
        "aspiration pneumonia",
        "neumonía por aspiración",
        "neumonia por aspiracion",
    ],
    "gastric aspiration": [
        "gastric aspiration",
        "aspiración gástrica",
        "aspiración pulmonar",
        "aspiration",
    ],
    "nausea": ["nausea", "náusea", "náuseas"],
    "vomiting": ["vomiting", "vómito", "vomito"],
    "diarrhoea": ["diarrhoea", "diarrhea", "diarrea"],
    "dyspepsia": ["dyspepsia", "dispepsia"],
    "rhabdomyolysis": ["rhabdomyolysis", "rabdomiólisis", "rabdomiolisis"],
    "blood creatine phosphokinase increased": [
        "creatine phosphokinase",
        "creatina quinasa",
        "cpk",
    ],
    "death": [
        "death", "muerte", "muertes", "fallecimiento", "óbito",
        "mortalidad", "mortal", "fatal", "letalidad", "letal",
        "outcome fatal", "resultado fatal", "desenlace fatal",
    ],
    "geriatric subpopulation": [
        "≥65",
        ">= 65",
        ">65",
        "mayores de 65",
        "adultos mayores",
        "geriátric",
        "ancian",
    ],
    "pregnancy": ["pregnancy", "embaraz"],
}


def match_pt(pt: str, answer: str) -> bool:
    """Check if a MedDRA PT (or its known synonyms) appears in the answer."""
    key = pt.lower()
    synonyms = PT_SYNONYMS.get(key, [key])
    return any(syn in answer for syn in synonyms)


def evaluate_item(item: dict, trace: dict) -> dict:
    """Evaluate a single agent trace against the expected criteria."""
    answer = trace["final_answer"].lower()
    called_tools = {tc["name"] for tc in trace["tool_calls"]}
    is_edge_case = item["category"] == "edge_case"

    # 1. Tool correctness
    expected_alias = item.get("expected_tool", "")
    expected_tools = TOOL_ALIASES.get(expected_alias, set())
    if is_edge_case:
        # Edge cases: acceptable to call any tool (returns empty) or no tool.
        # What matters is the answer NOT hallucinating data.
        tool_ok = True
    elif not expected_tools:
        tool_ok = True
    else:
        tool_ok = bool(called_tools & expected_tools)

    # 2. Must-mention PTs — bilingual matching
    must_pts = item.get("must_mention_pts") or []
    mentioned_pts = [pt for pt in must_pts if match_pt(pt, answer)]
    pt_coverage = len(mentioned_pts) / len(must_pts) if must_pts else 1.0

    # 3. Forbidden claims — token-based matching with negative-context filter
    forbidden = item.get("forbidden_claims") or []
    violations = []
    negative_contexts = [
        "no causa", "sin causa", "no causalidad", "sin causalidad",
        "no establece", "no implica", "no demuestra", "no confirma",
        "causalidad no", "does not cause", "not cause",
    ]
    for claim in forbidden:
        c = claim.lower()
        pattern = re.compile(rf"\b{re.escape(c)}\b")
        matches = list(pattern.finditer(answer))
        if not matches:
            continue
        real_violation = False
        for m in matches:
            start = max(0, m.start() - 30)
            end = min(len(answer), m.end() + 30)
            ctx = answer[start:end]
            if not any(neg in ctx for neg in negative_contexts):
                real_violation = True
                break
        if real_violation:
            violations.append(claim)
    no_forbidden = len(violations) == 0

    # 4. Safeguards check
    has_n_citation = bool(re.search(r"n\s*=\s*\d+", answer))
    limitation_terms = [
        "asociación", "association", "no causalidad", "not causation",
        "subnotificación", "underreporting", "sesgo", "bias", "limitación",
        "limitation", "no permite", "no se puede establecer",
    ]
    has_limitation = any(term in answer for term in limitation_terms)

    # Edge cases: don't penalize missing n= or limitations if the agent
    # correctly declined to answer with fabricated data.
    if is_edge_case:
        has_n_citation = True   # Not applicable
        has_limitation = True   # Not applicable

    return {
        "id": item["id"],
        "category": item["category"],
        "tool_ok": tool_ok,
        "called_tools": list(called_tools),
        "expected_tool": expected_alias,
        "pt_coverage": pt_coverage,
        "mentioned_pts": mentioned_pts,
        "missing_pts": [pt for pt in must_pts if pt not in mentioned_pts],
        "no_forbidden": no_forbidden,
        "forbidden_violations": violations,
        "has_n_citation": has_n_citation,
        "has_limitation": has_limitation,
        "n_turns": trace["n_turns"],
        "error": trace.get("error"),
    }

def summarize(evaluations: list[dict]) -> dict:
    """Aggregate per-item evaluations into overall metrics."""
    n = len(evaluations)
    return {
        "total_questions": n,
        "tool_accuracy": sum(e["tool_ok"] for e in evaluations) / n,
        "avg_pt_coverage": sum(e["pt_coverage"] for e in evaluations) / n,
        "no_forbidden_rate": sum(e["no_forbidden"] for e in evaluations) / n,
        "n_citation_rate": sum(e["has_n_citation"] for e in evaluations) / n,
        "limitation_rate": sum(e["has_limitation"] for e in evaluations) / n,
        "avg_turns": sum(e["n_turns"] for e in evaluations) / n,
        "errors": [e["id"] for e in evaluations if e.get("error")],
    }


def build_report(items: list[dict], traces: list[dict],
                 evaluations: list[dict], metrics: dict) -> str:
    """Render a Markdown evaluation report."""
    lines = ["# Agent Evaluation Report\n"]
    lines.append(f"**Total questions**: {metrics['total_questions']}\n")
    lines.append("## Overall metrics\n")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Tool routing accuracy   | {metrics['tool_accuracy']:.1%} |")
    lines.append(f"| PT coverage (avg)       | {metrics['avg_pt_coverage']:.1%} |")
    lines.append(f"| No forbidden claims     | {metrics['no_forbidden_rate']:.1%} |")
    lines.append(f"| Cites n= evidence       | {metrics['n_citation_rate']:.1%} |")
    lines.append(f"| Mentions limitations    | {metrics['limitation_rate']:.1%} |")
    lines.append(f"| Avg agent turns         | {metrics['avg_turns']:.1f} |")

    if metrics["errors"]:
        lines.append(f"\n**Errors**: {metrics['errors']}")

    lines.append("\n## Per-question breakdown\n")

    for item, trace, ev in zip(items, traces, evaluations):
        lines.append(f"### {item['id']} — {item['category']}")
        lines.append(f"**Question**: {item['question']}\n")
        lines.append(f"- Tool routing: "
                     f"{'PASS' if ev['tool_ok'] else 'FAIL'} "
                     f"(expected `{ev['expected_tool']}`, "
                     f"called {ev['called_tools']})")
        lines.append(f"- PT coverage: {ev['pt_coverage']:.0%} "
                     f"(missing: {ev['missing_pts'] or 'none'})")
        lines.append(f"- Forbidden claims: "
                     f"{'clean' if ev['no_forbidden'] else 'VIOLATION: ' + str(ev['forbidden_violations'])}")
        lines.append(f"- n= citations: {'yes' if ev['has_n_citation'] else 'no'}")
        lines.append(f"- Limitations mentioned: "
                     f"{'yes' if ev['has_limitation'] else 'no'}")
        lines.append(f"- Turns: {ev['n_turns']}")
        lines.append("")
        lines.append(f"<details><summary>Answer preview</summary>\n")
        preview = trace["final_answer"][:1000]
        if len(trace["final_answer"]) > 1000:
            preview += "..."
        lines.append(f"```\n{preview}\n```\n</details>\n")

    return "\n".join(lines)


def main():
    items = load_dataset()
    print(f"Loaded {len(items)} evaluation items.\n")

    traces = []
    for item in items:
        print(f"Running {item['id']} ({item['category']})...")
        t0 = time.time()
        trace = ask_with_trace(item["question"])
        elapsed = time.time() - t0
        print(f"  turns={trace['n_turns']} time={elapsed:.1f}s "
              f"tools={[tc['name'] for tc in trace['tool_calls']]}")
        traces.append(trace)

    print("\nEvaluating traces...")
    evaluations = [evaluate_item(item, tr) for item, tr in zip(items, traces)]
    metrics = summarize(evaluations)

    # Persist
    (RESULTS_DIR / "traces.json").write_text(
        json.dumps(traces, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (RESULTS_DIR / "evaluations.json").write_text(
        json.dumps(evaluations, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (RESULTS_DIR / "metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (RESULTS_DIR / "report.md").write_text(
        build_report(items, traces, evaluations, metrics),
        encoding="utf-8",
    )

    print("\n=== Overall Metrics ===")
    for k, v in metrics.items():
        if isinstance(v, float):
            print(f"  {k}: {v:.1%}" if "rate" in k or "accuracy" in k or "coverage" in k
                  else f"  {k}: {v:.2f}")
        else:
            print(f"  {k}: {v}")

    print(f"\nReport saved to: {RESULTS_DIR / 'report.md'}")

def rerun_evaluation_only():
    """Re-score existing traces without re-calling the agent. Zero API cost."""
    items = load_dataset()
    traces = json.loads(
        (RESULTS_DIR / "traces.json").read_text(encoding="utf-8")
    )
    evaluations = [evaluate_item(item, tr) for item, tr in zip(items, traces)]
    metrics = summarize(evaluations)

    (RESULTS_DIR / "evaluations.json").write_text(
        json.dumps(evaluations, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (RESULTS_DIR / "metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (RESULTS_DIR / "report.md").write_text(
        build_report(items, traces, evaluations, metrics),
        encoding="utf-8",
    )

    print("=== Re-evaluated Metrics ===")
    for k, v in metrics.items():
        if isinstance(v, float):
            print(f"  {k}: {v:.1%}" if "rate" in k or "accuracy" in k or "coverage" in k
                  else f"  {k}: {v:.2f}")
        else:
            print(f"  {k}: {v}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--rescore":
        rerun_evaluation_only()
    else:
        main()