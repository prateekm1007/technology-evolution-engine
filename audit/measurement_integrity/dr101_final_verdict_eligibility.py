#!/usr/bin/env python3
"""
dr101_final_verdict_eligibility.py — DR-101: FINAL Verdict Eligibility
(cycle 256, gate E of "Road to FINAL verdict").

Per PRELIMINARY_MEASUREMENT_VERDICT.md and F-143:
  The FINAL verdict requires all gates to pass:
    - Gate A: External baselines (DR-97)
    - Gate B: Historical re-calibration (DR-98)
    - Gate C: N≥30 proposal evaluation (DR-99)
    - Gate D: Tier-2 human domain expert review (DR-100)

This module reads the gate results from reports/*.json and decides:
  - If ALL gates PASS → FINAL verdict is eligible, write FINAL_MEASUREMENT_VERDICT.md
  - If any gate is PARTIAL or FAIL → FINAL verdict BLOCKED, write
    FINAL_VERDICT_BLOCKED.md documenting which gates failed
  - If any gate is BLOCKED (Gate D, by design) → FINAL verdict BLOCKED
    on human review

This gate is the META-gate: it does not run measurements itself, it
harvests the results of the other four gates.

Output:
  - reports/final_verdict_eligibility.md
  - reports/final_verdict_eligibility.json
  - FINAL_MEASUREMENT_VERDICT.md      (only if eligible)
  - FINAL_VERDICT_BLOCKED.md          (if not eligible)
"""
import sys
import json
from pathlib import Path
from typing import Dict, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


# ============================================================================
# GATE RESULT HARVESTERS
# ============================================================================

def harvest_gate_a(reports_dir: Path) -> Dict:
    """Read Gate A result from external_baselines.json."""
    path = reports_dir / "external_baselines.json"
    if not path.exists():
        return {"available": False, "verdict": "NOT_RUN", "error": "file missing"}
    data = json.loads(path.read_text())
    return {
        "available": True,
        "verdict": data.get("gate_verdict", "UNKNOWN"),
        "production_f1_strict": data.get("production_f1_strict"),
        "production_f1_lenient": data.get("production_f1_lenient"),
        "fp_floor_lenient": data.get("fp_floor_lenient"),
        "comparisons_lenient": data.get("comparisons_lenient"),
    }


def harvest_gate_b(reports_dir: Path) -> Dict:
    """Read Gate B result from historical_recalibration.json."""
    path = reports_dir / "historical_recalibration.json"
    if not path.exists():
        return {"available": False, "verdict": "NOT_RUN", "error": "file missing"}
    data = json.loads(path.read_text())
    return {
        "available": True,
        "verdict": data.get("gate_verdict", "UNKNOWN"),
        "n_claims": data.get("n_claims"),
        "verdict_counts_dr91": data.get("verdict_counts_dr91_convention"),
        "verdict_counts_honest": data.get("verdict_counts_honest_convention"),
        "formula_inflation_observed": data.get("formula_inflation_observed"),
    }


def harvest_gate_c(reports_dir: Path) -> Dict:
    """Read Gate C result from proposal_evaluation_n30.json."""
    path = reports_dir / "proposal_evaluation_n30.json"
    if not path.exists():
        return {"available": False, "verdict": "NOT_RUN", "error": "file missing"}
    data = json.loads(path.read_text())
    return {
        "available": True,
        "verdict": data.get("gate_verdict", "UNKNOWN"),
        "n_total": data.get("n_total"),
        "n_met": data.get("n_met"),
        "distribution": data.get("distribution"),
        "t_test": data.get("t_test"),
    }


def harvest_gate_d(reports_dir: Path) -> Dict:
    """Read Gate D result.

    Gate D is special: it produces a scaffolding (not a result).
    The actual verdict only exists if responses have been collected
    and the aggregation script has been run, producing
    tier2_review_aggregated.json.
    """
    agg_path = reports_dir / "tier2_review_aggregated.json"
    if not agg_path.exists():
        # Check if scaffolding exists
        scaffold_path = reports_dir / "tier2_review_status.md"
        if scaffold_path.exists():
            return {
                "available": True,
                "verdict": "BLOCKED_ON_HUMAN",
                "scaffolding_built": True,
                "blocked_reason": "Awaiting human domain expert review responses",
            }
        return {"available": False, "verdict": "NOT_RUN", "error": "no scaffolding"}
    data = json.loads(agg_path.read_text())
    return {
        "available": True,
        "verdict": data.get("gate_verdict", "UNKNOWN"),
        "n_responses": data.get("n_responses"),
        "accept_rate": data.get("accept_rate"),
        "overall_mean_score": data.get("overall_mean_score"),
    }


# ============================================================================
# ELIGIBILITY DECISION
# ============================================================================

def decide_eligibility(gates: Dict[str, Dict]) -> Dict:
    """Decide whether the FINAL verdict is eligible based on gate results.

    Returns a dict with:
      - eligible: bool
      - blocking_gates: list of gate names that blocked eligibility
      - reason: human-readable explanation
    """
    blocking = []
    reasons = []

    for gate_name, gate_result in gates.items():
        verdict = gate_result.get("verdict", "NOT_RUN")
        if verdict in ("NOT_RUN", "BLOCKED_ON_HUMAN", "FAIL", "UNKNOWN"):
            blocking.append(gate_name)
            reasons.append(f"{gate_name}: {verdict} — {gate_result.get('blocked_reason', gate_result.get('error', 'no reason'))}")
        elif verdict == "PARTIAL":
            blocking.append(gate_name)
            reasons.append(f"{gate_name}: PARTIAL — not full pass")
        elif verdict == "PASS":
            pass  # good
        else:
            blocking.append(gate_name)
            reasons.append(f"{gate_name}: unexpected verdict {verdict!r}")

    eligible = len(blocking) == 0

    return {
        "eligible": eligible,
        "blocking_gates": blocking,
        "reasons": reasons,
        "n_gates_passed": sum(1 for g in gates.values() if g.get("verdict") == "PASS"),
        "n_gates_total": len(gates),
    }


# ============================================================================
# FINAL VERDICT WRITERS
# ============================================================================

def write_final_verdict(reports_dir: Path, gates: Dict, eligibility: Dict) -> Path:
    """Write FINAL_MEASUREMENT_VERDICT.md (only called if eligible)."""
    repo = reports_dir.parent
    verdict_path = repo / "FINAL_MEASUREMENT_VERDICT.md"

    gate_a = gates["A"]
    gate_b = gates["B"]
    gate_c = gates["C"]
    gate_d = gates["D"]

    lines = []
    lines.append("# FINAL MEASUREMENT VERDICT")
    lines.append("")
    lines.append("## Verdict: TRUSTWORTHY (with documented limitations)")
    lines.append("")
    lines.append("All four measurement gates have PASSED. The measurement system is")
    lines.append("now considered trustworthy, with the following documented limitations:")
    lines.append("")
    lines.append("## Gate results")
    lines.append("")
    lines.append("| Gate | Name | Verdict | Key metric |")
    lines.append("|---|---|---|---|")
    lines.append(f"| A | External baselines | {gate_a['verdict']} | "
                  f"production F1 (lenient) = {gate_a.get('production_f1_lenient')} |")
    lines.append(f"| B | Historical re-calibration | {gate_b['verdict']} | "
                  f"{gate_b.get('n_claims')} claims re-scored |")
    lines.append(f"| C | N≥30 proposal evaluation | {gate_c['verdict']} | "
                  f"N={gate_c.get('n_total')} |")
    lines.append(f"| D | Tier-2 human review | {gate_d['verdict']} | "
                  f"accept rate = {gate_d.get('accept_rate')} |")
    lines.append("")
    lines.append("## Documented limitations")
    lines.append("")
    if gate_b.get("formula_inflation_observed"):
        lines.append("- **DR-91 F1 formula inflation**: The historical F1 formula")
        lines.append("  `2*recall/(1+recall)` inflates scores by ignoring false positives.")
        lines.append("  The honest F1 `2*p*r/(p+r)` is lower. Both are reported in")
        lines.append("  reports/historical_recalibration.json for transparency.")
    lines.append("- **FP floor = 1.0**: Under lenient (synonym+token) matching, any")
    lines.append("  random candidate matches the gold pool. This is a property of the")
    lines.append("  matcher design, not a bug. It is documented in DR-91 and reaffirmed")
    lines.append("  in DR-97 Gate A.")
    lines.append("- **Strict F1 = 0**: Under strict (exact) matching, the production")
    lines.append("  matcher never finds the exact bridge. This is because the bridges")
    lines.append("  are concept-level, not lexical. The system relies on synonym/token")
    lines.append("  matching, which is honest about what it does but should not be")
    lines.append("  confused with exact discovery.")
    lines.append("")
    lines.append("## Production F1 (honest, with FP counted)")
    lines.append("")
    lines.append("Under the HONEST F1 formula (2*p*r/(p+r)):")
    lines.append(f"- Aggregate (PRELIMINARY): {gate_a.get('production_f1_lenient', 0.8571)}")
    if gate_c.get("distribution"):
        honest_mean = gate_c["distribution"]["lenient_honest"]["mean"]
        lines.append(f"- Per-proposal (N={gate_c.get('n_total')}): {honest_mean}")
    lines.append("")
    lines.append("Both numbers are reported. The aggregate F1 is the system-level score.")
    lines.append("The per-proposal F1 is the per-instance score. They measure different")
    lines.append("things and should not be conflated.")
    lines.append("")
    lines.append("## Conclusion")
    lines.append("")
    lines.append("The measurement system has earned the FINAL verdict. The system")
    lines.append("is not a perfect discovery engine — it has documented limitations —")
    lines.append("but it is now MEASURED HONESTLY. Future claims about the system")
    lines.append("must cite these gate results and respect the documented limitations.")
    lines.append("")

    verdict_path.write_text("\n".join(lines))
    return verdict_path


def write_blocked_verdict(reports_dir: Path, gates: Dict,
                           eligibility: Dict) -> Path:
    """Write FINAL_VERDICT_BLOCKED.md (when not eligible)."""
    repo = reports_dir.parent
    blocked_path = repo / "FINAL_VERDICT_BLOCKED.md"

    lines = []
    lines.append("# FINAL VERDICT BLOCKED")
    lines.append("")
    lines.append("## Status: NOT TRUSTWORTHY (FINAL verdict not yet earned)")
    lines.append("")
    lines.append(f"Gate results: {eligibility['n_gates_passed']}/{eligibility['n_gates_total']} PASS")
    lines.append("")
    if eligibility["blocking_gates"]:
        lines.append("## Blocking gates")
        lines.append("")
        for gate, reason in zip(eligibility["blocking_gates"], eligibility["reasons"]):
            lines.append(f"- **{gate}**: {reason}")
        lines.append("")
    lines.append("## Gate summary")
    lines.append("")
    lines.append("| Gate | Name | Verdict |")
    lines.append("|---|---|---|")
    gate_names = {
        "A": "External baselines",
        "B": "Historical re-calibration",
        "C": "N≥30 proposal evaluation",
        "D": "Tier-2 human review",
    }
    for gate_letter in ("A", "B", "C", "D"):
        g = gates.get(gate_letter, {})
        lines.append(f"| {gate_letter} | {gate_names[gate_letter]} | {g.get('verdict', 'NOT_RUN')} |")
    lines.append("")
    lines.append("## What this means")
    lines.append("")
    lines.append("The PRELIMINARY verdict (NOT TRUSTWORTHY) remains in effect.")
    lines.append("The measurement system has NOT earned the FINAL verdict because")
    lines.append("one or more gates have not passed.")
    lines.append("")
    lines.append("## What is required to unblock")
    lines.append("")
    for gate, reason in zip(eligibility["blocking_gates"], eligibility["reasons"]):
        if gate == "A":
            lines.append("- **Gate A (External baselines)**: re-run DR-97. If production")
            lines.append("  F1 doesn't beat baselines, the matcher needs to be reworked.")
        elif gate == "B":
            lines.append("- **Gate B (Historical re-calibration)**: re-run DR-98. If")
            lines.append("  historical claims don't reproduce, the scorecard must be revised.")
        elif gate == "C":
            lines.append("- **Gate C (N≥30 proposal evaluation)**: re-run DR-99. If")
            lines.append("  honest F1 is statistically indistinguishable from FP floor,")
            lines.append("  the matcher produces no signal.")
        elif gate == "D":
            lines.append("- **Gate D (Tier-2 human review)**: This gate is BLOCKED on")
            lines.append("  human domain expert review. Recruit ≥3 experts, distribute")
            lines.append("  reports/tier2_review_form.md, collect responses, run the")
            lines.append("  aggregation script. See reports/tier2_review_status.md.")
    lines.append("")
    lines.append("## What is NOT blocked")
    lines.append("")
    lines.append("The scaffolding for all four gates is complete. The measurement")
    lines.append("infrastructure is in place. The remaining work is:")
    lines.append("- Rework (for any FAIL verdicts)")
    lines.append("- Human review (for Gate D)")
    lines.append("")

    blocked_path.write_text("\n".join(lines))
    return blocked_path


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 80)
    print("DR-101: FINAL Verdict Eligibility (cycle 256, gate E)")
    print("Meta-gate: harvests results from gates A-D, decides eligibility.")
    print("=" * 80)
    print()

    repo = Path(__file__).resolve().parents[2]
    reports_dir = repo / "reports"

    # Harvest all gate results
    gates = {
        "A": harvest_gate_a(reports_dir),
        "B": harvest_gate_b(reports_dir),
        "C": harvest_gate_c(reports_dir),
        "D": harvest_gate_d(reports_dir),
    }

    print("Gate results:")
    print()
    print(f"{'Gate':<6} {'Available':<12} {'Verdict':<22} {'Detail'}")
    print("-" * 80)
    for gate_letter, g in gates.items():
        detail = ""
        if g.get("available"):
            if gate_letter == "A":
                detail = f"prod F1 lenient = {g.get('production_f1_lenient')}"
            elif gate_letter == "B":
                detail = f"n_claims = {g.get('n_claims')}"
            elif gate_letter == "C":
                detail = f"N = {g.get('n_total')}, n_met = {g.get('n_met')}"
            elif gate_letter == "D":
                detail = g.get("blocked_reason", f"accept_rate = {g.get('accept_rate')}")
        else:
            detail = g.get("error", "")
        avail = "yes" if g.get("available") else "no"
        print(f"{gate_letter:<6} {avail:<12} {g.get('verdict', 'NOT_RUN'):<22} {detail}")
    print()

    # Decide eligibility
    eligibility = decide_eligibility(gates)
    print("=" * 80)
    print("ELIGIBILITY DECISION")
    print("=" * 80)
    print()
    print(f"Gates passed: {eligibility['n_gates_passed']}/{eligibility['n_gates_total']}")
    print(f"Eligible for FINAL verdict: {eligibility['eligible']}")
    if eligibility["blocking_gates"]:
        print(f"Blocking gates: {', '.join(eligibility['blocking_gates'])}")
        print()
        print("Reasons:")
        for r in eligibility["reasons"]:
            print(f"  - {r}")
    print()

    # Write FINAL verdict or BLOCKED notice
    if eligibility["eligible"]:
        print("Writing FINAL_MEASUREMENT_VERDICT.md...")
        verdict_path = write_final_verdict(reports_dir, gates, eligibility)
        # Remove any stale BLOCKED file
        blocked_path = repo / "FINAL_VERDICT_BLOCKED.md"
        if blocked_path.exists():
            blocked_path.unlink()
        print(f"  → {verdict_path}")
    else:
        print("Writing FINAL_VERDICT_BLOCKED.md...")
        blocked_path = write_blocked_verdict(reports_dir, gates, eligibility)
        # Ensure no stale FINAL_MEASUREMENT_VERDICT.md exists
        verdict_path = repo / "FINAL_MEASUREMENT_VERDICT.md"
        if verdict_path.exists():
            verdict_path.unlink()
        print(f"  → {blocked_path}")
    print()

    # Write eligibility report
    json_out = {
        "cycle": 256,
        "gate": "E",
        "gate_name": "final_verdict_eligibility",
        "gates": gates,
        "eligibility": eligibility,
        "final_verdict_written": eligibility["eligible"],
        "blocked_verdict_written": not eligibility["eligible"],
    }
    with open(reports_dir / "final_verdict_eligibility.json", "w") as f:
        json.dump(json_out, f, indent=2)

    lines = []
    lines.append("# DR-101: FINAL Verdict Eligibility (Gate E of Road to FINAL)")
    lines.append("")
    lines.append("Cycle: 256")
    lines.append("")
    lines.append("## Meta-gate decision")
    lines.append("")
    lines.append(f"Gates passed: {eligibility['n_gates_passed']}/{eligibility['n_gates_total']}")
    lines.append(f"Eligible for FINAL verdict: **{eligibility['eligible']}**")
    lines.append("")
    if eligibility["blocking_gates"]:
        lines.append("## Blocking gates")
        lines.append("")
        for gate, reason in zip(eligibility["blocking_gates"], eligibility["reasons"]):
            lines.append(f"- **{gate}**: {reason}")
        lines.append("")
    lines.append("## Gate results")
    lines.append("")
    lines.append("| Gate | Name | Verdict |")
    lines.append("|---|---|---|")
    gate_names = {
        "A": "External baselines (DR-97)",
        "B": "Historical re-calibration (DR-98)",
        "C": "N≥30 proposal evaluation (DR-99)",
        "D": "Tier-2 human review (DR-100)",
    }
    for gate_letter in ("A", "B", "C", "D"):
        g = gates.get(gate_letter, {})
        lines.append(f"| {gate_letter} | {gate_names[gate_letter]} | {g.get('verdict', 'NOT_RUN')} |")
    lines.append("")
    if eligibility["eligible"]:
        lines.append("## Outcome")
        lines.append("")
        lines.append("**FINAL_MEASUREMENT_VERDICT.md has been written.**")
        lines.append("")
        lines.append("The measurement system has earned the FINAL TRUSTWORTHY verdict,")
        lines.append("with documented limitations listed in the verdict file.")
    else:
        lines.append("## Outcome")
        lines.append("")
        lines.append("**FINAL_VERDICT_BLOCKED.md has been written.**")
        lines.append("")
        lines.append("The PRELIMINARY verdict (NOT TRUSTWORTHY) remains in effect.")
        lines.append("See FINAL_VERDICT_BLOCKED.md for the list of blocking gates and")
        lines.append("what is required to unblock them.")
    lines.append("")
    with open(reports_dir / "final_verdict_eligibility.md", "w") as f:
        f.write("\n".join(lines))

    print(f"Saved reports/final_verdict_eligibility.json")
    print(f"Saved reports/final_verdict_eligibility.md")
    print()

    # Final summary
    print("=" * 80)
    if eligibility["eligible"]:
        print("FINAL VERDICT: TRUSTWORTHY (with documented limitations)")
        rc = 0
    else:
        print("FINAL VERDICT: BLOCKED — PRELIMINARY (NOT TRUSTWORTHY) remains in effect")
        rc = 2
    print("=" * 80)
    return rc


if __name__ == "__main__":
    sys.exit(main())
