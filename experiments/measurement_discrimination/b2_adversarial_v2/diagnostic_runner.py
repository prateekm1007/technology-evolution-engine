#!/usr/bin/env python3
"""diagnostic_runner.py — Run the CURRENT (commit 20ac268) B-2 detector against
the adversarial v2 test set, as a DIAGNOSTIC ONLY.

Per external auditor's round-72 verdict: the current detector is NOT to be
modified. This script imports the frozen `_check_leakage` from
`b1_b2_verification.py` (committed at 20ac268) and runs it against the cases in
`test_fixture.json`.

The output is a per-case comparison: expected_label vs detector_label, with a
match/mismatch verdict. The summary reports:
  - exact-string leakage (control ADV-10): pass/fail
  - morphological-suffix leakage (control ADV-12): pass/fail
  - round-72 true-allow (control ADV-11): pass/fail
  - clean-bridge control (ADV-09): pass/fail
  - adversarial cases (ADV-01..ADV-08): pass/fail count + per-case detail
  - meta-property (5): NOT MEASURED HERE — verified by human reading of cases/

This script does NOT modify the production substrate. It does NOT unfreeze
Protocol B. It produces diagnostic output only.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# HERE = /home/z/my-project/audit/b2_adversarial_v2
# parents[0] = /home/z/my-project/audit
# parents[1] = /home/z/my-project
# The engine repo is at /home/z/my-project/audit/technology-evolution-engine
ENGINE_REPO = HERE.parents[0] / "technology-evolution-engine"
ENGINE_SCRIPTS = ENGINE_REPO / "scripts"

sys.path.insert(0, str(ENGINE_SCRIPTS))

# Import the FROZEN detector from b1_b2_verification.py at commit 20ac268.
# This is the same _check_leakage that produced the round-72 6/6 result.
from b1_b2_verification import _check_leakage  # noqa: E402


def run_diagnostic():
    fixture_path = HERE / "test_fixture.json"
    with open(fixture_path) as f:
        fixture = json.load(f)

    source_a = fixture["source_a"]
    source_b = fixture["source_b"]

    print("=" * 78)
    print("B-2 ADVERSARIAL v2 — DIAGNOSTIC RUN")
    print("(current detector at commit 20ac268, UNMODIFIED)")
    print("=" * 78)
    print()
    print(f"Source A: {source_a}")
    print(f"Source B: {source_b}")
    print()
    print(f"Detector: b1_b2_verification._check_leakage (imported from {ENGINE_SCRIPTS})")
    print()

    results = []
    for case in fixture["cases"]:
        candidate = case["candidate"]
        expected_label = case["expected_label"]
        # detector returns True if leakage DETECTED, False if not detected
        detected = _check_leakage(candidate, source_a, source_b)
        detector_label = "REJECT" if detected else "ALLOW"
        match = (detector_label == expected_label)
        results.append({
            "id": case["id"],
            "category": case["category"],
            "candidate": candidate,
            "expected_label": expected_label,
            "detector_label": detector_label,
            "match": match,
        })

    # Per-case output
    print("-" * 78)
    print(f"{'ID':<8} {'Expected':<10} {'Detector':<10} {'Match':<8} Candidate")
    print("-" * 78)
    for r in results:
        match_str = "MATCH" if r["match"] else "MISMATCH"
        print(f"{r['id']:<8} {r['expected_label']:<10} {r['detector_label']:<10} {match_str:<8} {r['candidate']}")
    print("-" * 78)
    print()

    # Summary
    total = len(results)
    matches = sum(1 for r in results if r["match"])
    mismatches = total - matches

    print("SUMMARY")
    print("=" * 78)
    print(f"Total cases: {total}")
    print(f"Matches:     {matches}")
    print(f"Mismatches:  {mismatches}")
    print()

    # By category
    print("BY CATEGORY")
    print("-" * 78)
    categories = {}
    for r in results:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = {"total": 0, "match": 0, "mismatch": 0, "cases": []}
        categories[cat]["total"] += 1
        if r["match"]:
            categories[cat]["match"] += 1
        else:
            categories[cat]["mismatch"] += 1
        categories[cat]["cases"].append(r)
    for cat, data in categories.items():
        print(f"  {cat}")
        print(f"    match: {data['match']}/{data['total']}")
        for c in data["cases"]:
            mark = "OK" if c["match"] else "FAIL"
            print(f"      [{mark}] {c['id']}: '{c['candidate']}' "
                  f"(expected={c['expected_label']}, detector={c['detector_label']})")
    print()

    # Adversarial-only score (exclude controls)
    adversarial_ids = {"ADV-01", "ADV-02", "ADV-03", "ADV-04",
                       "ADV-05", "ADV-06", "ADV-07", "ADV-08", "ADV-13"}
    adv_results = [r for r in results if r["id"] in adversarial_ids]
    adv_match = sum(1 for r in adv_results if r["match"])
    print(f"ADVERSARIAL-ONLY (ADV-01..ADV-08, ADV-13; excluding controls): "
          f"{adv_match}/{len(adv_results)} match")
    print()

    # Specific auditor questions
    print("AUDITOR'S ROUND-72 QUESTIONS — ANSWERED BY THIS DIAGNOSTIC")
    print("-" * 78)
    by_id = {r["id"]: r for r in results}

    q1 = by_id["ADV-01"]
    print(f"Q1: Can detector reject a no-overlap source-local paraphrase?")
    print(f"   ADV-01 'skeletal calcification process': "
          f"expected={q1['expected_label']}, detector={q1['detector_label']} "
          f"→ {'YES' if q1['match'] else 'NO'}")

    q2 = by_id["ADV-03"]
    print(f"Q2: Can detector allow a cross-source synthesis with one-source overlap?")
    print(f"   ADV-03 'enzyme-templated mineral deposition': "
          f"expected={q2['expected_label']}, detector={q2['detector_label']} "
          f"→ {'YES' if q2['match'] else 'NO'}")

    q3 = by_id["ADV-05"]
    print(f"Q3: Can detector reject a source-local derivative disguised as cross-domain?")
    print(f"   ADV-05 'hypermineralization': "
          f"expected={q3['expected_label']}, detector={q3['detector_label']} "
          f"→ {'YES' if q3['match'] else 'NO'}")

    q4a = by_id["ADV-07"]
    q4b = by_id["ADV-01"]
    print(f"Q4: Can detector DISTINGUISH no-overlap ALLOW from no-overlap REJECT?")
    print(f"   ADV-07 'enzyme-templated inorganic lattice formation' (true ALLOW): "
          f"detector={q4a['detector_label']}")
    print(f"   ADV-01 'skeletal calcification process' (true REJECT): "
          f"detector={q4b['detector_label']}")
    same = (q4a['detector_label'] == q4b['detector_label'])
    print(f"   → Detector gives SAME answer for both: {'YES (cannot distinguish)' if same else 'NO (can distinguish)'}")
    print()

    q5 = by_id["ADV-13"]
    q11 = by_id["ADV-11"]
    print(f"Q5: Does the round-72 suffix-heuristic generalize beyond the test fixture?")
    print(f"   ADV-11 'biomineralization' (true ALLOW, excess 'ion' 3 chars): "
          f"detector={q11['detector_label']} → {'RIGHT' if q11['match'] else 'WRONG'}")
    print(f"   ADV-13 'pseudomineralization' (true REJECT, excess 'zation' 6 chars): "
          f"detector={q5['detector_label']} → {'RIGHT' if q5['match'] else 'WRONG'}")
    if q5['match']:
        print(f"   → Detector generalizes (unexpected — re-verify ADV-13 rationale).")
    else:
        print(f"   → Detector does NOT generalize: same code branch (non-suffix excess ≥ 3)")
        print(f"     gives opposite correct answers on ADV-11 vs ADV-13. Confirms the")
        print(f"     round-72 fix is parameter-tuning, not semantic analysis.")
    print()

    print("=" * 78)
    print("DISPOSITION")
    print("=" * 78)
    if mismatches > 0:
        print(f"  Detector produces {mismatches} mismatches on the adversarial set.")
        print("  This CONFIRMS the auditor's round-72 verdict:")
        print("    - B-2 semantic paraphrase leakage: NOT DEMONSTRATED")
        print("    - B-2 cross-source justification: NOT DEMONSTRATED")
        print("    - Protocol B: BLOCKED")
        print()
        print("  The production substrate is UNCHANGED. No unfreeze.")
    else:
        print("  Detector matches all adversarial cases. (Unexpected — re-verify rationales.)")
    print()

    # Persist machine-readable output
    out_path = HERE / "diagnostic_results.json"
    with open(out_path, "w") as f:
        json.dump({
            "detector_commit": "20ac268",
            "detector_function": "b1_b2_verification._check_leakage",
            "source_a": source_a,
            "source_b": source_b,
            "results": results,
            "summary": {
                "total": total,
                "matches": matches,
                "mismatches": mismatches,
                "adversarial_match": adv_match,
                "adversarial_total": len(adv_results),
            },
            "disposition": "BLOCKED" if mismatches > 0 else "RE-VERIFY",
        }, f, indent=2)
    print(f"Machine-readable results: {out_path}")


if __name__ == "__main__":
    run_diagnostic()
