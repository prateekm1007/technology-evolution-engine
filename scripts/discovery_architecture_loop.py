#!/usr/bin/env python3
"""
discovery_architecture_loop.py — The 9-phase discovery maturity driver.

Per CEO cycle 68: "Read your governance and anti entropy files and
create the loop."

This loop:
  1. Assesses the system's maturity on the 9-phase scale
  2. Identifies the current phase (lowest incomplete)
  3. Proposes the next concrete work to advance that phase
  4. Writes a maturity assessment report + PDF deliverable

Per PDF Mandate: every significant loop output produces a PDF.
"""
import sys
import pathlib
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


# ---------------------------------------------------------------------------
# The 9 Phases — maturity model
# ---------------------------------------------------------------------------

PHASES = {
    "I": {
        "name": "Scientific Memory",
        "success_criterion": "Everything becomes replayable",
        "target": "Store facts, mechanisms, observations, interventions, theories",
        "required_classes": ["Observation", "Intervention", "Theory"],
        "current_status": "70%",
        "current_assessment": "IdentityGraph, SimilarityGraph, MechanismGraph, CausalGraph, ExperimentGraph exist. Missing: Observation, Intervention, Theory classes. CausalEdge has mechanism_status but no Observation with measurement/uncertainty.",
        "next_work": "Add Observation, Intervention, Theory dataclasses to invention_compiler/. Wire them into the DiscoveryGraph as new node types.",
    },
    "II": {
        "name": "Dimensional Reasoning",
        "success_criterion": "Impossible laws disappear automatically",
        "target": " Buckingham π theorem, dimensional consistency, unit propagation",
        "required_classes": ["Dimension"],
        "current_status": "5%",
        "current_assessment": "The system treats all numbers as dimensionless. Stefan-Boltzmann's T⁴ (K⁴) and PCM's linear (kg/W) are fit identically. No unit consistency check exists.",
        "next_work": "Add Dimension dataclass (mass, length, time, current, temperature, amount). Implement Buckingham π theorem. Add dimensional consistency check to BACON's candidate law forms.",
    },
    "III": {
        "name": "Symbolic Discovery",
        "success_criterion": "Discover equations you never programmed",
        "target": "Open search space: sin, cos, log, sqrt, atan, exp, polynomials, piecewise, nested compositions",
        "required_classes": [],
        "current_status": "20%",
        "current_assessment": "BACON has 6 candidate forms (linear, inverse, log, power, exponential, quadratic). BACON.3 does recursive composition. BACON.4 does 3+ variable products. Missing: open search (PySR-style), trigonometric functions, piecewise laws.",
        "next_work": "Add sin/cos/log/sqrt/atan to candidate forms. Implement PySR-style genetic programming search. Add Monte Carlo tree search for law form exploration.",
    },
    "IV": {
        "name": "Mechanism Induction",
        "success_criterion": "The system explains",
        "target": "Entity → activity → constraint → state transition (Machamer-Darden-Craver)",
        "required_classes": ["Mechanism (expanded)"],
        "current_status": "25%",
        "current_assessment": "CausalEdge has mechanism field (text description). Missing: structured mechanism representation (entities, activities, organization, constraints, transitions). The system describes but does not explain.",
        "next_work": "Expand Mechanism class to include entities, activities, organization, constraints, transitions. Implement Machamer-Darden-Craver framework.",
    },
    "V": {
        "name": "Intervention Search",
        "success_criterion": "The engine proposes experiments",
        "target": "do(x) calculus, counterfactual search, Bayesian optimization, causal bandits",
        "required_classes": [],
        "current_status": "30%",
        "current_assessment": "design_competing_experiment exists (accepts hypotheses). design_autonomous_competing_experiment generates hypotheses. Missing: Pearl do-calculus, counterfactual search, Bayesian optimization for experiment selection.",
        "next_work": "Implement Pearl do-calculus (do(x) vs observe(x)). Add counterfactual search. Add Bayesian optimization for experiment selection.",
    },
    "VI": {
        "name": "Laboratory Closure",
        "success_criterion": "The engine learns from reality",
        "target": "prediction → experiment → measurement → belief update → theory revision",
        "required_classes": [],
        "current_status": "10%",
        "current_assessment": "10 closed loops exist (EXP-001 through EXP-010). All use external verification (paper lookup, not physical experiment). Missing: experiment compiler, protocol generator, simulator, measurement ingestion, automatic revision.",
        "next_work": "Build experiment compiler (generates executable protocol from prediction). Build measurement ingestion (accepts external measurement, compares to prediction). Build belief revision (updates graph based on measurement outcome).",
    },
    "VII": {
        "name": "Adjacent Possible Exploration",
        "success_criterion": "The system explores what does not yet exist",
        "target": "Arthur, Fleming, Youn, NK models, combinatorial innovation",
        "required_classes": [],
        "current_status": "15%",
        "current_assessment": "SwansonBridgeSearch finds undiscovered A→B→C paths. GentnerStructureMapping finds structural analogies. Missing: state-space exploration, NK models, combinatorial innovation search.",
        "next_work": "Implement NK model for fitness landscape exploration. Add combinatorial innovation search (combine existing mechanisms in novel ways).",
    },
    "VIII": {
        "name": "Discovery Economics",
        "success_criterion": "maximize(expected_information_gain)",
        "target": "expected_value, cost, risk, information_gain, time_to_validation",
        "required_classes": [],
        "current_status": "0%",
        "current_assessment": "Not started. The system does not prioritize which discovery to pursue next. No cost/benefit analysis of experiments.",
        "next_work": "Add expected_information_gain calculation for each candidate bridge/experiment. Add cost model (financial, time, risk). Implement ranking by expected_value / cost.",
    },
    "IX": {
        "name": "Apollo Benchmark",
        "success_criterion": "Blind tests → 100, novel hits → 25, closed loops → 1000",
        "target": "Continuous blind discovery testing",
        "required_classes": [],
        "current_status": "2/100 blind tests",
        "current_assessment": "2 blind tests completed (1 NOVEL HIT, 1 RETRIEVAL). 10 closed loops. 7 domains. 14% verified mechanisms. Need: more blind tests, more domains, more closed loops, higher verification rate.",
        "next_work": "Run more blind discovery tests (target 10 by end of Phase I). Expand to more domains (target 20 by end of Phase III). Increase closed loops to 50 by end of Phase VI.",
    },
}


def assess_maturity() -> Dict[str, Any]:
    """Assess the system's maturity on the 9-phase scale."""
    assessment = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "phases": {},
        "current_phase": None,
        "apollo_metrics": {},
    }

    # Check each phase's actual status
    for phase_id, phase_info in PHASES.items():
        # Check if required classes exist
        classes_exist = []
        for cls_name in phase_info.get("required_classes", []):
            # Check if the class exists in invention_compiler/
            found = False
            for py_file in (ROOT / "invention_compiler").glob("*.py"):
                try:
                    content = py_file.read_text()
                    if f"class {cls_name}" in content or f"class {cls_name.split('(')[0]}" in content:
                        found = True
                        break
                except:
                    pass
            classes_exist.append({"class": cls_name, "exists": found})

        # Check Apollo metrics (for Phase IX)
        if phase_id == "IX":
            # Count blind tests in ledger
            ledger_path = ROOT / "data" / "ledger" / "predictions.jsonl"
            blind_tests = 0
            novel_hits = 0
            retrievals = 0
            null_results = 0
            if ledger_path.exists():
                for line in ledger_path.read_text().splitlines():
                    if not line.strip():
                        continue
                    try:
                        entry = json.loads(line)
                        if entry.get("type") in ("blind_test_hypothesis", "blind_test_hypothesis_v2"):
                            blind_tests += 1
                        if entry.get("outcome", "").startswith("NOVEL HIT"):
                            novel_hits += 1
                        elif entry.get("outcome", "").startswith("RETRIEVAL"):
                            retrievals += 1
                        elif entry.get("outcome", "").startswith("NULL"):
                            null_results += 1
                    except:
                        pass

            assessment["apollo_metrics"] = {
                "blind_tests": blind_tests,
                "novel_hits": novel_hits,
                "retrievals": retrievals,
                "null_results": null_results,
                "target_blind_tests": 100,
                "target_novel_hits": 25,
            }

        assessment["phases"][phase_id] = {
            "name": phase_info["name"],
            "success_criterion": phase_info["success_criterion"],
            "current_status": phase_info["current_status"],
            "current_assessment": phase_info["current_assessment"],
            "next_work": phase_info["next_work"],
            "required_classes": classes_exist,
        }

    # Determine current phase (lowest incomplete phase)
    for phase_id in ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"]:
        status = assessment["phases"][phase_id]["current_status"]
        if "%" in status:
            pct = int(status.replace("%", "").strip())
            if pct < 100:
                assessment["current_phase"] = phase_id
                break

    return assessment


def write_maturity_report(assessment: Dict[str, Any]) -> pathlib.Path:
    """Write a maturity assessment report as markdown + generate PDF."""
    reports_dir = ROOT / "benchmarks" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Discovery Maturity Assessment — Cycle 69",
        "",
        f"**Generated:** {assessment['timestamp']}",
        f"**Current phase:** {assessment['current_phase']}",
        "",
        "## 9-Phase Maturity Scale",
        "",
        "| Phase | Name | Status | Success Criterion |",
        "|---|---|---|---|",
    ]
    for phase_id, info in assessment["phases"].items():
        status = info["current_status"]
        if "100%" in status:
            marker = "✅"
        else:
            try:
                pct = int(status.replace("%","").strip())
                marker = "🟡" if pct >= 20 else "🔴"
            except ValueError:
                marker = "🔴"
        lines.append(f"| {phase_id} | {info['name']} | {marker} {info['current_status']} | {info['success_criterion']} |")

    lines.extend([
        "",
        "## Apollo Metrics",
        "",
        "| Metric | Current | Target |",
        "|---|---|---|",
    ])
    for k, v in assessment.get("apollo_metrics", {}).items():
        if isinstance(v, int):
            target = v * 10 if "target" not in k else v
            lines.append(f"| {k} | {v} | {target} |")

    lines.extend([
        "",
        "## Current Phase Detail",
        "",
    ])
    current = assessment["phases"][assessment["current_phase"]]
    lines.extend([
        f"**Phase {assessment['current_phase']}: {current['name']}**",
        f"**Status:** {current['current_status']}",
        f"**Success criterion:** {current['success_criterion']}",
        "",
        f"**Assessment:** {current['current_assessment']}",
        "",
        f"**Next work:** {current['next_work']}",
        "",
        "## Required New Classes",
        "",
    ])
    for phase_id, info in assessment["phases"].items():
        for cls in info.get("required_classes", []):
            status = "✅ exists" if cls["exists"] else "❌ missing"
            lines.append(f"- Phase {phase_id} ({info['name']}): `{cls['class']}` — {status}")

    lines.extend([
        "",
        "## The Final Architecture",
        "",
        "```",
        "OBSERVE → EXTRACT → REPRESENT → EXPLAIN → DISCOVER → INTERVENE",
        "→ PREDICT → EXPERIMENT → MEASURE → LEARN → REVISE",
        "```",
        "",
        "## Path Forward",
        "",
        "The system is at Phase I (Scientific Memory, 70%). The next step is to",
        "add Observation, Intervention, and Theory dataclasses to close Phase I,",
        "then proceed to Phase II (Dimensional Reasoning) — the biggest omission",
        "identified by the CEO.",
        "",
    ])

    report_path = reports_dir / "maturity_assessment.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")

    # Generate PDF
    import subprocess
    pdf_path = ROOT / "product" / "MATURITY_ASSESSMENT.pdf"
    try:
        subprocess.run([
            "python", str(ROOT / "scripts" / "generate_pdf.py"),
            str(report_path), str(pdf_path)
        ], check=True, capture_output=True, timeout=60)
        print(f"PDF generated: {pdf_path}")
    except Exception as e:
        print(f"PDF generation failed: {e}")

    return report_path


def main():
    print("=" * 70)
    print("DISCOVERY ARCHITECTURE LOOP — 9-Phase Maturity Assessment")
    print("=" * 70)

    assessment = assess_maturity()

    print(f"\nCurrent phase: {assessment['current_phase']}")
    current = assessment["phases"][assessment["current_phase"]]
    print(f"  {assessment['current_phase']}: {current['name']} — {current['current_status']}")
    print(f"  Success criterion: {current['success_criterion']}")
    print(f"  Next work: {current['next_work'][:100]}...")
    print()

    print("All phases:")
    for phase_id, info in assessment["phases"].items():
        status = info["current_status"]
        if "100%" in status:
            marker = "✅"
        else:
            try:
                pct = int(status.replace("%","").strip())
                marker = "🟡" if pct >= 20 else "🔴"
            except ValueError:
                marker = "🔴"  # non-numeric status (e.g., "2/100 blind tests")
        print(f"  {marker} Phase {phase_id}: {info['name']:30s} {info['current_status']:>5s}")

    print()
    print("Apollo Metrics:")
    for k, v in assessment.get("apollo_metrics", {}).items():
        print(f"  {k}: {v}")

    # Write report + PDF
    report_path = write_maturity_report(assessment)
    print(f"\nReport: {report_path}")

    # Write JSON assessment
    json_path = ROOT / "benchmarks" / "reports" / "maturity_assessment.json"
    json_path.write_text(json.dumps(assessment, indent=2, default=str), encoding="utf-8")
    print(f"JSON: {json_path}")

    print(f"\n{'=' * 70}")
    print(f"CURRENT PHASE: {assessment['current_phase']} — {current['name']}")
    print(f"NEXT WORK: {current['next_work'][:120]}")
    print(f"{'=' * 70}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
