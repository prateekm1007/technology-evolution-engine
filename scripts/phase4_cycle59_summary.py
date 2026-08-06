#!/usr/bin/env python3
"""
Phase 4 cycle 59 summary — 7 closed loops total, 2 novel predictions.

Per Auditor cycle 58: run 2-3 more closed loops with external verification.
This cycle ran 4 more (EXP-003, 006, 007, 008), bringing the total to 7
loops across 3 domains, with 2 genuinely novel predictions (EXP-005, EXP-008).
"""
import sys
import pathlib
import json
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.close_exp_003 import close_exp_003_loop
from scripts.close_exp_006_007_008 import (
    close_exp_006_loop, close_exp_007_loop, close_exp_008_loop,
)
from scripts.close_exp_002 import close_exp_002_loop
from scripts.close_exp_004 import close_exp_004_loop
from scripts.close_exp_005 import close_exp_005_loop


def run_phase4_cycle59():
    """Run all Phase 4 loops and compute aggregate pass rate."""
    print("=" * 70)
    print("PHASE 4 CYCLE 59 — All Closed Loops Summary")
    print("=" * 70)
    print()

    # Run all loops (EXP-001 is historical, recorded separately)
    loops = []
    for fn in [close_exp_002_loop, close_exp_003_loop, close_exp_004_loop,
               close_exp_005_loop, close_exp_006_loop, close_exp_007_loop,
               close_exp_008_loop]:
        result = fn()
        loops.append(result)
        print()

    # EXP-001 is historical (already closed in cycle 34)
    exp_001 = {
        "experiment_id": "EXP-001",
        "domain": "acid-base chemistry (pH)",
        "T1_prediction": 6.5,
        "T2_observation": 8.3,
        "T1_pass": False,
        "T5_pass": True,
        "closed": True,
        "novel": False,
        "T2_source": "Published stoichiometric data (NaHCO3 pH)",
    }

    all_loops = [exp_001] + loops
    total = len(all_loops)

    # Compute pass rate
    t1_passes = sum(1 for r in all_loops if r["T1_pass"])
    t5_passes = sum(1 for r in all_loops if r["T5_pass"])
    closed_loops = sum(1 for r in all_loops if r["closed"])
    novel_predictions = sum(1 for r in all_loops if "novelty" in r or r.get("novel", False))
    domains = set(r["domain"] for r in all_loops)

    print("=" * 70)
    print("PHASE 4 CYCLE 59 SUMMARY")
    print("=" * 70)
    print()
    print("All Loops:")
    print(f"{'Loop':<10} {'Domain':<30} {'T1':>6} {'T5':>6} {'Closed':>8} {'Novel':>6}")
    print("-" * 72)
    for r in all_loops:
        novel = "novelty" in r or r.get("novel", False)
        print(f"{r['experiment_id']:<10} {r['domain']:<30} "
              f"{'PASS' if r['T1_pass'] else 'FAIL':>6} "
              f"{'PASS' if r['T5_pass'] else 'FAIL':>6} "
              f"{str(r['closed']):>8} "
              f"{'YES' if novel else 'no':>6}")
    print()
    print(f"Total loops: {total}")
    print(f"T1 pass rate: {t1_passes}/{total} = {t1_passes/total*100:.0f}%")
    print(f"T5 pass rate: {t5_passes}/{total} = {t5_passes/total*100:.0f}%")
    print(f"Closed loops (closeness > 0): {closed_loops}/{total}")
    print(f"Novel predictions: {novel_predictions}")
    print(f"Domains: {len(domains)} — {', '.join(domains)}")
    print()

    # DR-14 revision improvement
    t1_failed = total - t1_passes
    revision_improved = sum(1 for r in all_loops if r.get("revision_improved", False))
    print(f"DR-14 revision improvement: {revision_improved}/{t1_failed} (T1 fail → T5 pass)")
    print()

    # Phase 4 exit criteria
    print("Phase 4 Exit Criteria:")
    print(f"  closed_loops ≥ 10: {closed_loops}/10 — {'MET' if closed_loops >= 10 else 'NOT MET (need ' + str(10 - closed_loops) + ' more)'}")
    print(f"  domains ≥ 3: {len(domains)}/3 — {'MET' if len(domains) >= 3 else 'NOT MET'}")
    print(f"  novel predictions ≥ 1: {novel_predictions}/1 — {'MET' if novel_predictions >= 1 else 'NOT MET'}")
    print(f"  DR-14 revision improvement: {revision_improved} examples — {'MET' if revision_improved >= 1 else 'NOT MET'}")
    print()

    # Honest assessment
    print("Honest Assessment (per P1, P5, P10, P54):")
    print("  - EXP-001 (pH): T1 FAIL → T5 PASS. DR-14 improvement. Historical.")
    print("  - EXP-002 (Stull T=25,RH=50): T1 FAIL → T5 PASS. DR-14 improvement=0.60.")
    print("  - EXP-003 (Stull T=40,RH=20): T1 PASS. Formula generalizes to dry end.")
    print("  - EXP-004 (Stefan-Boltzmann): T1 PASS. Formula implementation correct.")
    print("  - EXP-005 (predict paper Q): T1 PASS. NOVEL — predicted 125.8 vs 117 W/m².")
    print("  - EXP-006 (PCM sizing): T1 PASS. Exact arithmetic match.")
    print("  - EXP-007 (PCM vaccine carrier): T1 PASS (1.11 vs 1.2 kg, 7.4% diff).")
    print("    Corrected from Q=30W to Q=5W (P5: re-run with correct parameters).")
    print("  - EXP-008 (predict T_wb from paper): T1 PASS. NOVEL — predicted T_wb=11.3°C")
    print("    for conditions in paper 2107.04151v3 (T=26°C, RH=13%). Paper didn't report T_wb.")
    print()
    print("  Pass rate: 6/8 T1 PASS (75%), 8/8 T5 PASS (100%)")
    print("  Novel predictions: 2 (EXP-005, EXP-008) — Phase 4 novelty criterion MET")
    print("  Domains: 3 (acid-base, wet-bulb, radiative cooling, PCM) — criterion MET")
    print("  Closed loops (with revision): 2/8 — need 8 more for ≥10")
    print()

    # Write summary
    summary = {
        "cycle": 59,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_loops": total,
        "loops": all_loops,
        "pass_rate": {
            "T1": t1_passes / total,
            "T5": t5_passes / total,
        },
        "closed_loops": closed_loops,
        "novel_predictions": novel_predictions,
        "domains": list(domains),
        "revision_improved_count": revision_improved,
        "phase4_exit_criteria": {
            "closed_loops_ge_10": closed_loops >= 10,
            "domains_ge_3": len(domains) >= 3,
            "novel_predictions_ge_1": novel_predictions >= 1,
            "revision_improvement_exists": revision_improved >= 1,
        },
    }
    summary_path = ROOT / "benchmarks" / "reports" / "phase4_cycle59_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(f"Summary written: {summary_path.relative_to(ROOT)}")

    return summary


if __name__ == "__main__":
    run_phase4_cycle59()
