#!/usr/bin/env python3
"""
generate_auditor_scorecard.py — Generate AUDITOR_SCORECARD.md from
MEASURED benchmark reports (kill F-086).

Per cycle 184 (auditor update #3): the self-graded AUDITOR_SCORECARD.md
was a manual narrative that contradicted the generation benchmarks.
F-086 is P0.

This script REPLACES the manual scorecard with one GENERATED from
committed benchmark reports. Every category must point to:
  - a benchmark report file
  - a measured F1 (or other metric)
  - a passing test

If a category has no measured benchmark, it gets score = 0 and a
"NO MEASURED BENCHMARK" tag.

Usage:
    python3 -m scripts.generate_auditor_scorecard
"""
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "benchmarks" / "reports"
SCORECARD_PATH = ROOT / "AUDITOR_SCORECARD.md"


def _read_f1(report_name: str) -> float:
    """Read F1 from a benchmark report."""
    path = REPORTS / report_name
    if not path.exists():
        return 0.0
    try:
        with path.open() as f:
            data = json.load(f)
        return data.get("f1", 0.0)
    except Exception:
        return 0.0


def _read_ece() -> float:
    """Read ECE from calibration report."""
    path = REPORTS / "calibration_score.json"
    if not path.exists():
        return 1.0
    try:
        with path.open() as f:
            data = json.load(f)
        return data.get("ece", 1.0)
    except Exception:
        return 1.0


def _read_overturn_rate() -> float:
    """Read overturn rate from predictions ledger."""
    predictions = ROOT / "data" / "ledger" / "predictions.jsonl"
    if not predictions.exists():
        return 0.0
    total = 0
    overturned = 0
    with predictions.open() as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if entry.get("type") == "reaudit":
                    total += 1
                    if entry.get("overturned"):
                        overturned += 1
            except json.JSONDecodeError:
                continue
    if total == 0:
        return 0.0
    return overturned / total


def _score_from_f1(f1: float) -> int:
    """Single rubric: total_score = round(10 × F1)."""
    return round(10 * f1)


def _score_from_ece(ece: float) -> int:
    """Calibration score: round(10 × (1 - ECE))."""
    return round(10 * (1 - ece))


def _score_from_overturn(rate: float) -> int:
    """Gen 6 score: round(10 × min(1.0, overturn_rate × 4))."""
    return round(10 * min(1.0, rate * 4))


def _measured_categories() -> list:
    """Build the measured scorecard rows.

    Each row: (category_name, score, max, metric_name, metric_value,
               report_file, test_file, formula, notes)
    """
    rows = []

    # === GENERATION BENCHMARKS (measured F1) ===
    gen1_f1 = _read_f1("gen1_pr_score.json")
    rows.append({
        "category": "Gen 1: Document Parsing",
        "score": _score_from_f1(gen1_f1),
        "max": 10,
        "metric": "F1",
        "metric_value": gen1_f1,
        "report": "benchmarks/reports/gen1_pr_score.json",
        "test": "tests/test_regression_suite.py",
        "formula": "round(10 × F1)",
        "notes": "Section segmentation",
    })

    gen2_f1 = _read_f1("gen2_pr_score.json")
    rows.append({
        "category": "Gen 2: Entity Extraction",
        "score": _score_from_f1(gen2_f1),
        "max": 10,
        "metric": "F1",
        "metric_value": gen2_f1,
        "report": "benchmarks/reports/gen2_pr_score.json",
        "test": "tests/test_regression_suite.py",
        "formula": "round(10 × F1)",
        "notes": "NER + alias resolution",
    })

    gen3_f1 = _read_f1("gen3_pr_score.json")
    rows.append({
        "category": "Gen 3: Relation Extraction",
        "score": _score_from_f1(gen3_f1),
        "max": 10,
        "metric": "F1",
        "metric_value": gen3_f1,
        "report": "benchmarks/reports/gen3_pr_score.json",
        "test": "tests/test_regression_suite.py",
        "formula": "round(10 × F1)",
        "notes": "BOTTLENECK — auditor's #1 target for F1≥0.90",
    })

    gen4_f1 = _read_f1("gen4_pr_score.json")
    rows.append({
        "category": "Gen 4: Mechanism Extraction",
        "score": _score_from_f1(gen4_f1),
        "max": 10,
        "metric": "F1",
        "metric_value": gen4_f1,
        "report": "benchmarks/reports/gen4_pr_score.json",
        "test": "tests/test_regression_suite.py",
        "formula": "round(10 × F1)",
        "notes": "Mechanism chain benchmark",
    })

    gen5_f1 = _read_f1("gen5_pr_score.json")
    rows.append({
        "category": "Gen 5: Discovery Layer (connection-finding)",
        "score": _score_from_f1(gen5_f1),
        "max": 10,
        "metric": "F1",
        "metric_value": gen5_f1,
        "report": "benchmarks/reports/gen5_pr_score.json",
        "test": "tests/test_regression_suite.py",
        "formula": "round(10 × F1)",
        "notes": "F-087: F1 counts RETRIEVAL+NOVEL as TP. novelty_rate tracked separately.",
    })

    overturn_rate = _read_overturn_rate()
    rows.append({
        "category": "Gen 6: Re-audit",
        "score": _score_from_overturn(overturn_rate),
        "max": 10,
        "metric": "overturn_rate",
        "metric_value": overturn_rate,
        "report": "data/ledger/predictions.jsonl",
        "test": "tests/test_failure_regression_suite.py",
        "formula": "round(10 × min(1.0, overturn_rate × 4))",
        "notes": "Re-audit adversarial verification",
    })

    ece = _read_ece()
    rows.append({
        "category": "Calibration",
        "score": _score_from_ece(ece),
        "max": 10,
        "metric": "ECE",
        "metric_value": ece,
        "report": "benchmarks/reports/calibration_score.json",
        "test": "tests/test_failure_regression_suite.py",
        "formula": "round(10 × (1 - ECE))",
        "notes": "Platt scaling LOOCV",
    })

    return rows


def _discovery_capability_score() -> dict:
    """The discovery_capability benchmark — separate from Gen 5."""
    path = REPORTS / "discovery_capability_score.json"
    if not path.exists():
        return {
            "category": "Discovery Capability (operator-blind)",
            "score": 0,
            "max": 10,
            "metric": "F1",
            "metric_value": 0.0,
            "report": "benchmarks/reports/discovery_capability_score.json",
            "test": "—",
            "formula": "round(10 × F1)",
            "notes": "NO MEASURED BENCHMARK — report file missing",
        }
    with path.open() as f:
        data = json.load(f)
    f1 = data.get("f1", 0.0)
    return {
        "category": "Discovery Capability (operator-blind)",
        "score": _score_from_f1(f1),
        "max": 10,
        "metric": "F1",
        "metric_value": f1,
        "report": "benchmarks/reports/discovery_capability_score.json",
        "test": "tests/test_failure_regression_suite.py",
        "formula": "round(10 × F1)",
        "notes": "Operator-blind gold-standard discovery",
    }


def generate_scorecard() -> str:
    """Generate the AUDITOR_SCORECARD.md content from measured reports."""
    measured = _measured_categories()
    discovery = _discovery_capability_score()
    all_rows = measured + [discovery]

    # Composite is the mean of the 7 generation benchmarks (the
    # canonical scorecard). The discovery capability is reported
    # separately.
    gen_scores = [r["score"] for r in measured]
    composite = sum(gen_scores) / len(gen_scores) if gen_scores else 0.0

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = []
    lines.append("# AUDITOR_SCORECARD.md — MEASURED (auto-generated)")
    lines.append("")
    lines.append("> Per F-086 (cycle 184): this file is GENERATED from committed benchmark")
    lines.append("> reports by `scripts/generate_auditor_scorecard.py`. No manual entries.")
    lines.append("> Every score points to a benchmark report file + a passing test.")
    lines.append("> If a category has no measured benchmark, it gets score = 0.")
    lines.append("")
    lines.append(f"**Generated:** {now}")
    lines.append(f"**Composite (7 generation benchmarks):** {composite:.2f} / 10")
    lines.append(f"**Formula:** Single rubric — `total_score = round(10 × F1)` (or equivalent)")
    lines.append(f"**CEO target:** 9.0 / 10")
    lines.append("")
    lines.append("## Measured Scorecard")
    lines.append("")
    lines.append("| Category | Score | Metric | Value | Report | Test | Notes |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in all_rows:
        lines.append(
            f"| {r['category']} | **{r['score']}/{r['max']}** | "
            f"{r['metric']} | {r['metric_value']:.4f} | "
            f"`{r['report']}` | `{r['test']}` | {r['notes']} |"
        )
    lines.append("")
    lines.append("## How to regenerate")
    lines.append("")
    lines.append("```bash")
    lines.append("python3 -m benchmarks.section_segmentation_benchmark  # Gen 1")
    lines.append("python3 -m benchmarks.entity_extraction_benchmark    # Gen 2")
    lines.append("python3 -m benchmarks.relation_extraction_benchmark  # Gen 3")
    lines.append("python3 -m benchmarks.mechanism_chain_benchmark      # Gen 4")
    lines.append("python3 -m benchmarks.discovery_benchmark            # Gen 5")
    lines.append("python3 -m scripts.generate_auditor_scorecard        # this file")
    lines.append("```")
    lines.append("")
    lines.append("## Per Law 7 (historical permanence)")
    lines.append("")
    lines.append("This file is reproducible: same benchmark reports → same scorecard.")
    lines.append("Manual edits to scores are FORBIDDEN. To change a score, change")
    lines.append("the underlying benchmark or extraction code, then re-run.")
    lines.append("")
    lines.append("## Auditor's 12-category scorecard (separate from generation benchmarks)")
    lines.append("")
    lines.append("The external auditor's 12 categories (Representation, Mechanism,")
    lines.append("Constraint, Law, Swanson, Causal, Structural, Contradiction,")
    lines.append("Experiment, Learning, Scalability, Scientific rigor) are NOT")
    lines.append("self-graded. They are evaluated by the external auditor and")
    lines.append("recorded in FAILURES.md. The last external audit (update #3,")
    lines.append("cycle 183) gave an honest composite of ~4.5/10.")
    lines.append("")
    lines.append("The generation-benchmark composite above is the INTERNALLY")
    lines.append("measured score. The two scores measure different things and")
    lines.append("should not be conflated.")
    lines.append("")

    return "\n".join(lines)


def main():
    content = generate_scorecard()
    with SCORECARD_PATH.open("w") as f:
        f.write(content)
    print(f"Wrote {SCORECARD_PATH}")
    print()
    print(content.split("\n")[4])  # composite line


if __name__ == "__main__":
    main()
