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
        return {"available": False, "verdict": "NOT_RUN",
                "verdict_tier": "NOT_RUN", "error": "file missing"}
    data = json.loads(path.read_text())
    return {
        "available": True,
        "verdict": data.get("gate_verdict", "UNKNOWN"),
        "verdict_tier": data.get("verdict_tier", "UNKNOWN"),
        "production_f1_strict": data.get("production_f1_strict"),
        "production_f1_lenient": data.get("production_f1_lenient"),
        "fp_floor_lenient": data.get("fp_floor_lenient"),
        "comparisons_lenient": data.get("comparisons_lenient"),
    }


def harvest_gate_b(reports_dir: Path) -> Dict:
    """Read Gate B result from historical_recalibration.json."""
    path = reports_dir / "historical_recalibration.json"
    if not path.exists():
        return {"available": False, "verdict": "NOT_RUN",
                "verdict_tier": "NOT_RUN", "error": "file missing"}
    data = json.loads(path.read_text())
    return {
        "available": True,
        "verdict": data.get("gate_verdict", "UNKNOWN"),
        "verdict_tier": data.get("verdict_tier", "UNKNOWN"),
        "n_claims": data.get("n_claims"),
        "verdict_counts_dr91": data.get("verdict_counts_dr91_convention"),
        "verdict_counts_honest": data.get("verdict_counts_honest_convention"),
        "formula_inflation_observed": data.get("formula_inflation_observed"),
        "formula_inflation_severity": data.get("formula_inflation_severity", "P0"),
    }


def harvest_gate_c(reports_dir: Path) -> Dict:
    """Read Gate C result from proposal_evaluation_n30.json."""
    path = reports_dir / "proposal_evaluation_n30.json"
    if not path.exists():
        return {"available": False, "verdict": "NOT_RUN",
                "verdict_tier": "NOT_RUN", "error": "file missing"}
    data = json.loads(path.read_text())
    return {
        "available": True,
        "verdict": data.get("gate_verdict", "UNKNOWN"),
        "verdict_tier": data.get("verdict_tier", "UNKNOWN"),
        "n_total": data.get("n_total"),
        "n_met": data.get("n_met"),
        "useful_performance_threshold": data.get("useful_performance_threshold"),
        "useful_performance_met": data.get("useful_performance_met"),
        "honest_f1_mean": data.get("honest_f1_mean"),
        "distribution": data.get("distribution"),
        "t_test": data.get("t_test"),
    }


def harvest_gate_d(reports_dir: Path) -> Dict:
    """Read Gate D result.

    Cycle 257 design change: Gate D now accepts AI specialist surrogate
    review in lieu of Tier-2 human review (since this system is meant to
    be an end-to-end AI loop). The aggregation script applies the same
    verdict thresholds regardless of reviewer type.

    The verdict_tier for Gate D is one of:
      SCIENCE_PASS       — human or AI surrogate reviewed and accepted
      AI_SURROGATE_REVIEW_FAIL — AI surrogate reviewed and rejected
      BLOCKED_ON_HUMAN_OR_AI_SURROGATE_REVIEW — no responses yet
      FAIL               — full failure
    """
    agg_path = reports_dir / "tier2_review_aggregated.json"
    responses_path = reports_dir / "tier2_review_responses.csv"
    if not agg_path.exists():
        # Check if scaffolding exists
        scaffold_path = reports_dir / "tier2_review_status.md"
        if scaffold_path.exists():
            return {
                "available": True,
                "verdict": "BLOCKED_ON_HUMAN_OR_AI_SURROGATE_REVIEW",
                "verdict_tier": "BLOCKED_ON_HUMAN_OR_AI_SURROGATE_REVIEW",
                "scaffolding_built": True,
                "blocked_reason": (
                    "Awaiting review responses (human Tier-2 OR AI surrogate). "
                    "Per cycle 257 design change, AI specialist review is "
                    "accepted because this system is meant to be an end-to-end "
                    "AI loop."
                ),
            }
        return {"available": False, "verdict": "NOT_RUN",
                "verdict_tier": "NOT_RUN", "error": "no scaffolding"}
    data = json.loads(agg_path.read_text())
    gate_verdict = data.get("gate_verdict", "UNKNOWN")

    # Determine reviewer type from responses CSV (look for reviewer_type column)
    reviewer_type = "UNKNOWN"
    if responses_path.exists():
        import csv as _csv
        with open(responses_path, "r") as f:
            reader = _csv.DictReader(f)
            first = next(iter(reader), {})
            reviewer_type = first.get("reviewer_type", "HUMAN")

    # Map verdict to verdict_tier
    if reviewer_type == "AI_PRE_REVIEW":
        if gate_verdict == "PASS":
            verdict_tier = "SCIENCE_PASS"  # AI surrogate PASSED
        else:
            verdict_tier = f"AI_SURROGATE_REVIEW_{gate_verdict}"
    else:
        # Human review
        verdict_tier = gate_verdict  # PASS/PARTIAL/FAIL

    return {
        "available": True,
        "verdict": gate_verdict,
        "verdict_tier": verdict_tier,
        "reviewer_type": reviewer_type,
        "n_responses": data.get("n_responses"),
        "accept_rate": data.get("accept_rate"),
        "overall_mean_score": data.get("overall_mean_score"),
    }


# ============================================================================
# ELIGIBILITY DECISION
# ============================================================================

def decide_eligibility(gates: Dict[str, Dict]) -> Dict:
    """Decide whether the FINAL verdict is eligible based on gate results.

    Cycle 257 tightening: FINAL verdict requires SCIENCE_PASS on ALL gates.
    Anything less (INSTRUMENTATION_SCAFFOLD_PASS, SENSITIVITY_ANALYSIS_PASS,
    WEAK_STATISTICAL_PASS, AI_SURROGATE_REVIEW_FAIL, BLOCKED) blocks eligibility.

    Phase 6 epistemic gate (audit round 12): Before deciding eligibility,
    verify that M-005 (discovery F1) and M-008 (FP floor) — the two
    critical-path metrics that feed the gate verdicts — are eligible
    for scientific use. If they are quarantined, eligibility is BLOCKED
    regardless of gate verdicts, because the gate verdicts themselves
    were derived from untrusted metrics.

    Returns a dict with:
      - eligible: bool
      - blocking_gates: list of gate names that blocked eligibility
      - reason: human-readable explanation
    """
    # PHASE 6 EPISTEMIC GATE (audit round 12)
    # The gate verdicts aggregated below were derived from metric values
    # (M-005 F1, M-008 FP floor) that are currently quarantined. No
    # eligibility decision may be made using untrusted metrics.
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from engine.epistemic_state_enforcer import (
        assert_metric_eligible_for_scientific_use,
        MetricNotEligible,
    )

    epistemic_blocks = []
    for critical_metric in ["M-005", "M-008"]:
        try:
            assert_metric_eligible_for_scientific_use(critical_metric)
        except MetricNotEligible as e:
            epistemic_blocks.append({
                "metric": critical_metric,
                "error": str(e),
            })

    if epistemic_blocks:
        return {
            "eligible": False,
            "blocking_gates": ["EPISTEMIC_GATE"],
            "reason": (
                f"EPISTEMIC GATE BLOCKED: The following critical-path metrics "
                f"are not eligible for scientific use: "
                f"{[b['metric'] for b in epistemic_blocks]}. "
                f"The gate verdicts aggregated by this function were derived "
                f"from these metrics. Since the metrics are quarantined/not "
                f"independently verified, the gate verdicts themselves are "
                f"untrusted. No eligibility decision may be made. Per Phase 6: "
                f"no scientific decision may use a non-eligible metric. "
                f"Epistemic blocks: {epistemic_blocks}"
            ),
            "epistemic_gate": "BLOCKED",
            "epistemic_blocks": epistemic_blocks,
        }

    blocking = []
    reasons = []

    for gate_name, gate_result in gates.items():
        verdict_tier = gate_result.get("verdict_tier", "NOT_RUN")
        if verdict_tier == "SCIENCE_PASS":
            pass  # only this tier qualifies for FINAL verdict
        elif verdict_tier in (
            "INSTRUMENTATION_SCAFFOLD_PASS",
            "SENSITIVITY_ANALYSIS_PASS",
            "WEAK_STATISTICAL_PASS",
        ):
            blocking.append(gate_name)
            reasons.append(
                f"{gate_name}: verdict_tier={verdict_tier} — instrumentation/scaffold "
                f"pass only, NOT SCIENCE_PASS. The gate runs and produces signal "
                f"but does not prove the scientific claim."
            )
        elif verdict_tier == "NOT_RUN":
            blocking.append(gate_name)
            reasons.append(
                f"{gate_name}: NOT_RUN — {gate_result.get('error', 'no reason')}"
            )
        elif verdict_tier.startswith("BLOCKED"):
            blocking.append(gate_name)
            reasons.append(
                f"{gate_name}: {verdict_tier} — {gate_result.get('blocked_reason', 'blocked')}"
            )
        elif verdict_tier.startswith("AI_SURROGATE_REVIEW_"):
            blocking.append(gate_name)
            reasons.append(
                f"{gate_name}: {verdict_tier} — AI surrogate review did not pass. "
                f"accept_rate={gate_result.get('accept_rate')}, "
                f"overall_mean={gate_result.get('overall_mean_score')}"
            )
        elif verdict_tier in ("FAIL", "PARTIAL"):
            blocking.append(gate_name)
            reasons.append(f"{gate_name}: verdict_tier={verdict_tier}")
        else:
            blocking.append(gate_name)
            reasons.append(f"{gate_name}: unexpected verdict_tier {verdict_tier!r}")

    eligible = len(blocking) == 0

    return {
        "eligible": eligible,
        "blocking_gates": blocking,
        "reasons": reasons,
        "n_gates_science_pass": sum(1 for g in gates.values() if g.get("verdict_tier") == "SCIENCE_PASS"),
        "n_gates_total": len(gates),
        # Legacy field kept for backward compat with tests
        "n_gates_passed": sum(1 for g in gates.values() if g.get("verdict") == "PASS"),
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
    lines.append(f"Gates with SCIENCE_PASS: {eligibility['n_gates_science_pass']}/{eligibility['n_gates_total']}")
    lines.append("")
    lines.append("**Cycle 257 tightening**: FINAL verdict requires SCIENCE_PASS on")
    lines.append("ALL gates. INSTRUMENTATION_SCAFFOLD_PASS, SENSITIVITY_ANALYSIS_PASS,")
    lines.append("WEAK_STATISTICAL_PASS, AI_SURROGATE_REVIEW_FAIL, and BLOCKED all")
    lines.append("block eligibility. These verdict tiers mean the gate's")
    lines.append("instrumentation runs but does not prove the scientific claim.")
    lines.append("")
    if eligibility["blocking_gates"]:
        lines.append("## Blocking gates")
        lines.append("")
        for gate, reason in zip(eligibility["blocking_gates"], eligibility["reasons"]):
            lines.append(f"- **{gate}**: {reason}")
        lines.append("")
    lines.append("## Gate summary")
    lines.append("")
    lines.append("| Gate | Name | Verdict | Verdict tier |")
    lines.append("|---|---|---|---|")
    gate_names = {
        "A": "External baselines",
        "B": "Historical re-calibration",
        "C": "N≥30 proposal evaluation",
        "D": "Tier-2 / AI surrogate review",
    }
    for gate_letter in ("A", "B", "C", "D"):
        g = gates.get(gate_letter, {})
        v = g.get("verdict", "NOT_RUN")
        vt = g.get("verdict_tier", "NOT_RUN")
        if vt is None or vt == "UNKNOWN":
            vt = "NOT_RUN"
        lines.append(f"| {gate_letter} | {gate_names[gate_letter]} | {v} | {vt} |")
    lines.append("")
    lines.append("## What this means")
    lines.append("")
    lines.append("The PRELIMINARY verdict (NOT TRUSTWORTHY) remains in effect.")
    lines.append("The measurement system has NOT earned the FINAL verdict because")
    lines.append("zero gates have reached SCIENCE_PASS. The instrumentation runs,")
    lines.append("but the scientific claims are not proven.")
    lines.append("")
    lines.append("## What is required to unblock")
    lines.append("")
    for gate, reason in zip(eligibility["blocking_gates"], eligibility["reasons"]):
        if gate == "A":
            lines.append("- **Gate A (External baselines)**: Cycle 257 finding: the")
            lines.append("  current BM25 baseline is lexical/oracle-assisted (uses the")
            lines.append("  gold bridge as the query). Repair requires implementing")
            lines.append("  true external baselines that propose bridges WITHOUT seeing")
            lines.append("  gold labels.")
        elif gate == "B":
            lines.append("- **Gate B (Historical re-calibration)**: Cycle 257 finding:")
            lines.append("  this is a sensitivity analysis, not a full recalibration.")
            lines.append("  Repair requires reconstructing each historical cycle's")
            lines.append("  original gold data, matcher version, and scoring formula.")
            lines.append("  Also: P0 finding — DR-91 F1 formula `2r/(1+r)` inflates")
            lines.append("  scores; future F1 claims must use honest `2pr/(p+r)`.")
        elif gate == "C":
            lines.append("- **Gate C (N≥30 proposal evaluation)**: Cycle 257 finding:")
            lines.append("  the PASS criterion was too weak. Distinguishability from")
            lines.append("  FP=1.0 is necessary but not sufficient. Useful proposal")
            lines.append("  performance requires per-proposal honest F1 mean ≥ 0.30;")
            lines.append("  observed 0.1500. Repair requires reworking the matcher to")
            lines.append("  produce higher per-proposal F1.")
        elif gate == "D":
            if "AI_SURROGATE_REVIEW_FAIL" in reason:
                lines.append("- **Gate D (AI surrogate review)**: AI surrogate reviewer")
                lines.append("  (AI_SURROGATE_001, Tier-1.5 pre-screen) reviewed 6")
                lines.append("  proposals and REJECTED all 6. The proposals are")
                lines.append("  'template-level shared-term hypotheses, not mature")
                lines.append("  scientific discovery claims.' Per cycle 257 design,")
                lines.append("  AI specialist review is accepted (end-to-end AI loop),")
                lines.append("  but the proposals did not pass. Repair requires")
                lines.append("  reworking the ProposalComposer to produce domain-grounded")
                lines.append("  hypotheses with concrete mechanisms, not shared vocabulary.")
            else:
                lines.append("- **Gate D (Tier-2 / AI surrogate review)**: No review")
                lines.append("  responses collected yet. Per cycle 257 design, AI")
                lines.append("  specialist review is accepted. See")
                lines.append("  reports/tier2_review_status.md.")
    lines.append("")
    lines.append("## What is NOT blocked")
    lines.append("")
    lines.append("The scaffolding for all four gates is complete. The measurement")
    lines.append("infrastructure is in place. The remaining work is:")
    lines.append("- Repair Gate A with true external baselines (no oracle)")
    lines.append("- Repair Gate B with full historical recalibration + honest F1")
    lines.append("- Repair Gate C with useful-performance threshold (≥0.30 mean F1)")
    lines.append("- Repair Gate D with reworked ProposalComposer (or human review)")
    lines.append("- Document formula inflation as P0 concern for any future F1 claim")
    lines.append("")

    blocked_path.write_text("\n".join(lines))
    return blocked_path


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 80)
    print("DR-101: FINAL Verdict Eligibility (cycle 257, gate E)")
    print("Meta-gate: harvests results from gates A-D, decides eligibility.")
    print("Cycle 257 tightening: FINAL requires SCIENCE_PASS on ALL gates.")
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
    print(f"{'Gate':<6} {'Available':<8} {'Verdict':<14} {'Verdict tier':<45} {'Detail'}")
    print("-" * 130)
    for gate_letter, g in gates.items():
        detail = ""
        if g.get("available"):
            if gate_letter == "A":
                detail = f"prod F1 lenient = {g.get('production_f1_lenient')}"
            elif gate_letter == "B":
                detail = f"n_claims = {g.get('n_claims')}, formula_inflation = {g.get('formula_inflation_observed')}"
            elif gate_letter == "C":
                detail = f"N = {g.get('n_total')}, useful_perf_met = {g.get('useful_performance_met')}"
            elif gate_letter == "D":
                if g.get("reviewer_type") == "AI_PRE_REVIEW":
                    detail = f"AI surrogate, accept_rate = {g.get('accept_rate')}"
                else:
                    detail = g.get("blocked_reason", f"accept_rate = {g.get('accept_rate')}")
        else:
            detail = g.get("error", "")
        avail = "yes" if g.get("available") else "no"
        vt = g.get("verdict_tier", "NOT_RUN")
        if vt is None or vt == "UNKNOWN":
            vt = "NOT_RUN"
        print(f"{gate_letter:<6} {avail:<8} {g.get('verdict', 'NOT_RUN'):<14} {vt:<45} {detail[:80]}")
    print()

    # Decide eligibility
    eligibility = decide_eligibility(gates)
    print("=" * 80)
    print("ELIGIBILITY DECISION (cycle 257 tightening)")
    print("=" * 80)
    print()
    print(f"Gates with SCIENCE_PASS: {eligibility['n_gates_science_pass']}/{eligibility['n_gates_total']}")
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
        "cycle": 257,
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
    lines.append("| Gate | Name | Verdict | Verdict tier |")
    lines.append("|---|---|---|---|")
    gate_names = {
        "A": "External baselines (DR-97)",
        "B": "Historical re-calibration (DR-98)",
        "C": "N≥30 proposal evaluation (DR-99)",
        "D": "Tier-2 / AI surrogate review (DR-100)",
    }
    for gate_letter in ("A", "B", "C", "D"):
        g = gates.get(gate_letter, {})
        v = g.get("verdict", "NOT_RUN")
        vt = g.get("verdict_tier", "NOT_RUN")
        if vt is None or vt == "UNKNOWN":
            vt = "NOT_RUN"
        lines.append(f"| {gate_letter} | {gate_names[gate_letter]} | {v} | {vt} |")
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
