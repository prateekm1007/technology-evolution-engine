#!/usr/bin/env python3
"""V2 comparison runner — thin wrapper that calls run_v2_comparison from build_v2.py."""
import sys, os
from pathlib import Path
REPO = Path(__file__).resolve().parents[3]
os.chdir(REPO)
sys.path.insert(0, str(REPO))

from discovery_fabric.dsb_v1.adjudication_engine_v2.build_v2 import run_v2_comparison, EVALUATOR_BOUNDARY, ADJUDICATOR_WS, REPORTS_DIR
import json
from datetime import datetime, timezone

result = run_v2_comparison()
print("=" * 72)
print("ADJUDICATION_ENGINE_V2 — COMPARISON")
print("=" * 72)
print()

if result["status"] != "COMPUTED":
    print(f"Status: FROZEN — {result.get('reason', 'prerequisites not met')}")
    sys.exit(0)

print(f"Status: COMPUTED")
print(f"Rows compared: {result['n_rows']}")
print()
print("Confusion matrices (CTO Q2 vs Machine Discovery):")
for key in ["real_strict", "real_lenient", "fabricated_strict", "fabricated_lenient", "all_strict", "all_lenient"]:
    m = result["confusion_matrices"][key]
    print(f"  {key:20s}: TP={m['tp']} FP={m['fp']} TN={m['tn']} FN={m['fn']} | "
          f"P={m['precision']} R={m['recall']} F1={m['f1']} FPr={m['false_positive_rate']}")
print()
print("Plausibility vs actual case_type:")
for ct, pc in result["plausibility_correlation"].items():
    print(f"  {ct:12s}: n={pc['n']} plausible={pc['plausible']} implausible={pc['implausible']} uncertain={pc['uncertain']} plausible_rate={pc['plausible_rate']}")
print()
print(f"Agreement (strict): {result['agreement_strict']*100:.1f}%")
print(f"Agreement (lenient): {result['agreement_lenient']*100:.1f}%")
print(f"Disagreements: {result['n_disagreements']}")

# Save results
out_path = REPORTS_DIR / "comparison_results.json"
with open(out_path, "w") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
print(f"\nResults: {out_path}")
