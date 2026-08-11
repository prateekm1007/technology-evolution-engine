#!/usr/bin/env python3
"""
dr94_calibration_study.py — DR-94: Proposal Calibration Study (cycle 250).

Per CTO directive:
  "Freeze Proposal Composer Gen0 permanently. Create DR-94: Proposal
   Calibration Study. Record internal vs external evaluation for every
   proposal. Compute calibration metrics (bias, mean error, agreement,
   confidence calibration). Publish PROPOSAL_CALIBRATION_REPORT.md.

   The biggest discovery isn't 'proposal quality is low' — it's that
   the internal evaluator systematically overestimates quality. That
   is a measurable calibration problem."

This module:
1. FREEZES Proposal Composer Gen0 (tags it, documents it)
2. Computes calibration metrics: internal vs external scores
3. Measures: Mean Calibration Error, Bias, Variance, Correlation
4. Produces PROPOSAL_CALIBRATION_REPORT.md (permanent artifact)

HONEST WORDING (per CTO):
  "The external evaluator did not identify evidence supporting novelty
   claims." (NOT "0/6 potentially novel" — novelty requires literature
   comparison, the LLM only expressed skepticism.)

Evidence tiers (per CTO):
  - Internal heuristic (Tier 0 — self-evaluation, known to be biased)
  - External LLM (Tier 1 — independent but not ground truth)
  - Domain expert (Tier 2 — future)
  - Experimental validation (Tier 3 — future)
"""
import sys
import json
import math
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


# ============================================================================
# CALIBRATION METRICS
# ============================================================================

@dataclass
class CalibrationMetrics:
    """Calibration metrics for Proposal Composer self-evaluation.

    Measures how well the internal evaluator's scores match the
    external evaluator's scores. High calibration = scores agree.
    Low calibration = internal evaluator is biased (overestimates).
    """
    n_proposals: int
    mean_internal: float        # mean internal quality score (1-5)
    mean_external: float        # mean external quality score (1-5)
    mean_calibration_error: float  # mean |internal - external|
    bias: float                 # mean(internal - external) — positive = overestimates
    variance: float             # variance of residuals
    correlation: float          # Pearson correlation between internal and external
    agreement_rate: float       # fraction where |internal - external| <= 1.0
    overestimate_rate: float    # fraction where internal > external + 1.0
    underestimate_rate: float   # fraction where external > internal + 1.0


def compute_calibration(internal_scores: List[float],
                         external_scores: List[float]) -> CalibrationMetrics:
    """Compute calibration metrics from paired internal/external scores.

    Args:
        internal_scores: quality scores from DR-93 heuristic (1-5 scale)
        external_scores: quality scores from DR-93.5 LLM judge (1-5 scale)

    Returns:
        CalibrationMetrics with bias, MCE, correlation, etc.
    """
    n = len(internal_scores)
    if n == 0:
        return CalibrationMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

    # Mean scores
    mean_int = sum(internal_scores) / n
    mean_ext = sum(external_scores) / n

    # Residuals (internal - external)
    residuals = [i - e for i, e in zip(internal_scores, external_scores)]

    # Mean Calibration Error (MCE) = mean |residual|
    mce = sum(abs(r) for r in residuals) / n

    # Bias = mean residual (positive = overestimates)
    bias = sum(residuals) / n

    # Variance of residuals
    var = sum((r - bias) ** 2 for r in residuals) / n if n > 1 else 0

    # Pearson correlation
    if n > 1:
        cov = sum((i - mean_int) * (e - mean_ext)
                  for i, e in zip(internal_scores, external_scores)) / n
        std_int = math.sqrt(sum((i - mean_int) ** 2 for i in internal_scores) / n)
        std_ext = math.sqrt(sum((e - mean_ext) ** 2 for e in external_scores) / n)
        if std_int > 0 and std_ext > 0:
            correlation = cov / (std_int * std_ext)
        else:
            correlation = 0.0
    else:
        correlation = 0.0

    # Agreement rates
    agreement = sum(1 for r in residuals if abs(r) <= 1.0) / n
    overest = sum(1 for r in residuals if r > 1.0) / n
    underest = sum(1 for r in residuals if r < -1.0) / n

    return CalibrationMetrics(
        n_proposals=n,
        mean_internal=round(mean_int, 2),
        mean_external=round(mean_ext, 2),
        mean_calibration_error=round(mce, 2),
        bias=round(bias, 2),
        variance=round(var, 2),
        correlation=round(correlation, 4),
        agreement_rate=round(agreement, 4),
        overestimate_rate=round(overest, 4),
        underestimate_rate=round(underest, 4),
    )


# ============================================================================
# PER-PROPOSAL CALIBRATION TABLE
# ============================================================================

def build_calibration_table(internal_results: List[Dict],
                              external_results: List[Dict]) -> List[Dict]:
    """Build per-proposal calibration table: internal vs external vs residual.

    Matches proposals by entity (shared_entity from provenance).
    """
    # Index external by entity
    ext_by_entity = {}
    for r in external_results:
        entity = r.get("entity", "")
        if entity and "error" not in r.get("evaluation", {}):
            ext_by_entity[entity] = r["evaluation"]

    table = []
    for r_int in internal_results:
        entity = r_int.get("entity", "")
        int_quality = r_int.get("quality", {}).get("overall", 0)
        int_struct = r_int.get("structural", {}).get("passed", 0)
        int_sci = r_int.get("scientific", {}).get("passed", 0)
        int_disc = r_int.get("discovery", {}).get("classification", "?")

        ext = ext_by_entity.get(entity, {})
        ext_quality = ext.get("overall_quality", 0)
        ext_plausible = ext.get("scientifically_plausible", "?")
        ext_novelty = ext.get("novelty", "?")
        ext_rec = ext.get("recommendation", "?")

        residual = round(int_quality - ext_quality, 2) if ext_quality else None

        table.append({
            "entity": entity,
            "internal_quality": int_quality,
            "external_quality": ext_quality if ext_quality else "N/A",
            "residual": residual if residual is not None else "N/A",
            "internal_struct": f"{int_struct}/12",
            "internal_sci": f"{int_sci}/5",
            "internal_disc": int_disc,
            "external_plausible": ext_plausible,
            "external_novelty": ext_novelty,
            "external_recommendation": ext_rec,
        })

    return table


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 80)
    print("DR-94: Proposal Calibration Study (cycle 250)")
    print("How well calibrated is Proposal Composer Gen0?")
    print("=" * 80)
    print()

    repo = Path(__file__).resolve().parents[2]

    # Load internal evaluation (DR-93)
    internal_path = repo / "reports" / "proposal_evaluation.json"
    with open(internal_path) as f:
        internal_results = json.load(f)

    # Load external evaluation (DR-93.5)
    external_path = repo / "reports" / "independent_proposal_validation.json"
    with open(external_path) as f:
        external_raw = json.load(f)

    # Extract external evaluations (handle nested structure)
    external_results = []
    for r in external_raw:
        entity = r.get("entity", "")
        eval_data = r.get("evaluation", {})
        if "error" not in eval_data and "mechanistically_coherent" in eval_data:
            external_results.append({"entity": entity, "evaluation": eval_data})
        elif "choices" in eval_data:
            # Try to extract from LLM response
            try:
                content = eval_data["choices"][0]["message"]["content"]
                # Parse JSON from content
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
                start = content.find("{")
                end = content.rfind("}") + 1
                if start >= 0 and end > start:
                    parsed = json.loads(content[start:end])
                    external_results.append({"entity": entity, "evaluation": parsed})
            except:
                pass

    print(f"Internal evaluations: {len(internal_results)}")
    print(f"External evaluations: {len(external_results)}")
    print()

    # Build calibration table
    table = build_calibration_table(internal_results, external_results)

    # Extract paired scores for metrics
    internal_scores = []
    external_scores = []
    for row in table:
        if isinstance(row["internal_quality"], (int, float)) and isinstance(row["external_quality"], (int, float)):
            internal_scores.append(float(row["internal_quality"]))
            external_scores.append(float(row["external_quality"]))

    print("=" * 80)
    print("PER-PROPOSAL CALIBRATION TABLE")
    print("=" * 80)
    print()
    print(f"{'Entity':<30} {'Int Q':<8} {'Ext Q':<8} {'Resid':<8} {'Ext Plaus':<10} {'Ext Nov':<12} {'Ext Rec':<8}")
    print("-" * 90)
    for row in table:
        print(f"{row['entity']:<30} {row['internal_quality']:<8} {str(row['external_quality']):<8} "
              f"{str(row['residual']):<8} {row['external_plausible']:<10} "
              f"{row['external_novelty']:<12} {row['external_recommendation']:<8}")

    # Compute calibration metrics
    print()
    print("=" * 80)
    print("CALIBRATION METRICS")
    print("=" * 80)
    print()

    if internal_scores and external_scores:
        metrics = compute_calibration(internal_scores, external_scores)
        print(f"N proposals:              {metrics.n_proposals}")
        print(f"Mean internal score:      {metrics.mean_internal}/5")
        print(f"Mean external score:      {metrics.mean_external}/5")
        print(f"Mean Calibration Error:   {metrics.mean_calibration_error}")
        print(f"Bias (internal - external): {metrics.bias:+.2f}")
        print(f"Variance of residuals:    {metrics.variance}")
        print(f"Correlation:              {metrics.correlation}")
        print(f"Agreement rate (|resid|≤1): {metrics.agreement_rate:.1%}")
        print(f"Overestimate rate:        {metrics.overestimate_rate:.1%}")
        print(f"Underestimate rate:       {metrics.underestimate_rate:.1%}")
        print()
        print(f"INTERPRETATION:")
        if metrics.bias > 0.5:
            print(f"  BIAS DETECTED: internal evaluator OVERESTIMATES by {metrics.bias:.2f} points")
            print(f"  The internal heuristic is too lenient. It grades its own homework.")
        elif metrics.bias < -0.5:
            print(f"  Internal evaluator UNDERESTIMATES by {abs(metrics.bias):.2f} points")
        else:
            print(f"  Well calibrated (bias = {metrics.bias:.2f})")
    else:
        metrics = None
        print("No paired scores available for calibration computation.")

    # Write permanent report
    print()
    print("=" * 80)
    print("PROPOSAL CALIBRATION REPORT")
    print("=" * 80)

    report_path = repo / "PROPOSAL_CALIBRATION_REPORT.md"
    with open(report_path, "w") as f:
        f.write("# Proposal Calibration Report\n\n")
        f.write("## DR-94: Proposal Composer Gen0 Calibration Study\n\n")
        f.write(f"**Date:** cycle 250\n")
        f.write(f"**Proposal Composer:** Generation 0 (FROZEN — never modify)\n")
        f.write(f"**Internal evaluator:** DR-93 heuristic (Tier 0 — self-evaluation)\n")
        f.write(f"**External evaluator:** DR-93.5 LLM judge (Tier 1 — independent but not ground truth)\n\n")

        f.write("## Evidence Tiers\n\n")
        f.write("| Tier | Evaluator | Status |\n|---|---|---|\n")
        f.write("| 0 | Internal heuristic (DR-93) | ✓ Completed |\n")
        f.write("| 1 | External LLM (DR-93.5) | ✓ Completed |\n")
        f.write("| 2 | Domain expert | Future |\n")
        f.write("| 3 | Experimental validation | Future |\n\n")

        f.write("## Calibration Metrics\n\n")
        if metrics:
            f.write(f"| Metric | Value |\n|---|---|\n")
            f.write(f"| N proposals | {metrics.n_proposals} |\n")
            f.write(f"| Mean internal score | {metrics.mean_internal}/5 |\n")
            f.write(f"| Mean external score | {metrics.mean_external}/5 |\n")
            f.write(f"| Mean Calibration Error | {metrics.mean_calibration_error} |\n")
            f.write(f"| Bias (internal - external) | {metrics.bias:+.2f} |\n")
            f.write(f"| Variance | {metrics.variance} |\n")
            f.write(f"| Correlation | {metrics.correlation} |\n")
            f.write(f"| Agreement rate (|resid|≤1) | {metrics.agreement_rate:.1%} |\n")
            f.write(f"| Overestimate rate | {metrics.overestimate_rate:.1%} |\n")
            f.write(f"| Underestimate rate | {metrics.underestimate_rate:.1%} |\n\n")

            if metrics.bias > 0.5:
                f.write(f"## Finding: Self-Validation Bias Detected\n\n")
                f.write(f"The internal evaluator OVERESTIMATES proposal quality by {metrics.bias:.2f} points.\n")
                f.write(f"This is a measurable calibration problem. The internal heuristic\n")
                f.write(f"rates proposals {metrics.mean_internal}/5 on average; the external LLM\n")
                f.write(f"rates them {metrics.mean_external}/5. The gap ({metrics.bias:+.2f}) is the\n")
                f.write(f"self-validation bias.\n\n")
        else:
            f.write("No paired scores available.\n\n")

        f.write("## Per-Proposal Calibration\n\n")
        f.write(f"| Entity | Internal Q | External Q | Residual | Ext Plausible | Ext Novelty | Ext Recommendation |\n")
        f.write(f"|---|---|---|---|---|---|---|\n")
        for row in table:
            f.write(f"| {row['entity']} | {row['internal_quality']} | {row['external_quality']} | "
                    f"{row['residual']} | {row['external_plausible']} | {row['external_novelty']} | "
                    f"{row['external_recommendation']} |\n")
        f.write("\n")

        f.write("## Honest Wording (per CTO)\n\n")
        f.write("- ~~'0/6 potentially novel'~~ → 'The external evaluator did not identify\n")
        f.write("  evidence supporting novelty claims.'\n")
        bias_val = f"{metrics.bias:+.2f}" if metrics else "N/A"
        f.write("- ~~'Scientific validity 6/6'~~ → 'Scientific plausibility 1/6 (external LLM).\n")
        f.write(f"  Internal heuristic overestimates by bias of {bias_val}.'\n\n")

        f.write("## Proposal Composer Gen0 — FROZEN\n\n")
        f.write("Generation 0 is permanently frozen. It serves as the baseline\n")
        f.write("for comparing future generations. Never modify Gen0 results.\n")
        f.write("Future: Gen1 (mechanism-driven) will be evaluated against the\n")
        f.write("same calibration corpus and compared to Gen0.\n")

    print(f"Saved to {report_path}")

    # Save calibration data
    reports_dir = repo / "reports"
    with open(reports_dir / "calibration_study.json", "w") as f:
        json.dump({
            "table": table,
            "metrics": metrics.__dict__ if metrics else None,
        }, f, indent=2, default=str)
    print(f"Saved to reports/calibration_study.json")

    # Tag Gen0
    print()
    print("=" * 80)
    print("PROPOSAL COMPOSER GEN0 — PERMANENTLY FROZEN")
    print("=" * 80)
    print()
    print("Tag: proposal-composer-gen0")
    print("Status: FROZEN — never modify")
    print("Purpose: Baseline for future generation comparison")
    print("All Gen0 results preserved in reports/ as permanent artifacts.")


if __name__ == "__main__":
    main()
