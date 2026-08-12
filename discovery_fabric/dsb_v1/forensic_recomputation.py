#!/usr/bin/env python3
"""
DSB V1 FORENSIC RECOMPUTATION
==============================

Pure recomputation from frozen receipts only. No new modules. No interpretation.

Reads:
  - Frozen cases (real + fabricated)
  - Frozen receipts (80)
  - Frozen scorer (scorer.py — used as-is, NOT tuned)
  - Frozen freeze manifest

Computes:
  1. All 80 scorer outcomes directly from frozen receipts
  2. The exact 13-recovery list (independently regenerated)
  3. Verification: 10 fabricated + 3 real = 13
  4. The 14 focused-review packet IDs (regenerated, verified selection used no human outcomes)
  5. Freeze manifest hash verification (all artifacts unchanged after freeze)

Outputs:
  - DSB_V1_FORENSIC_RECOMPUTATION.md (single file, zero interpretation)

This script is a READ-ONLY forensic audit. It does not modify any artifact.
"""
import json
import hashlib
import sys
import os
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[2]
os.chdir(REPO)
sys.path.insert(0, str(REPO))

DSB_DIR = REPO / "discovery_fabric" / "dsb_v1"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_str(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


# =============================================================================
# Step 1: Verify freeze manifest — all artifacts unchanged after freeze
# =============================================================================

def verify_freeze_manifest() -> dict:
    """Verify every artifact in the freeze manifest is unchanged."""
    manifest_path = DSB_DIR / "FREEZE_MANIFEST.json"
    if not manifest_path.exists():
        return {"error": "FREEZE_MANIFEST.json not found", "all_unchanged": False}

    with open(manifest_path) as f:
        manifest = json.load(f)

    frozen = manifest.get("frozen_artifacts", {})
    n_total = len(frozen)
    n_unchanged = 0
    n_modified = 0
    n_missing = 0
    modifications = []

    for rel_path, expected_hash in frozen.items():
        full_path = DSB_DIR / rel_path
        if not full_path.exists():
            n_missing += 1
            modifications.append({"path": rel_path, "status": "MISSING"})
            continue
        actual_hash = sha256_file(full_path)
        if actual_hash == expected_hash:
            n_unchanged += 1
        else:
            n_modified += 1
            modifications.append({
                "path": rel_path,
                "status": "MODIFIED",
                "expected": expected_hash[:16],
                "actual": actual_hash[:16],
            })

    return {
        "manifest_hash": manifest.get("manifest_hash"),
        "frozen_at": manifest.get("frozen_at"),
        "n_total": n_total,
        "n_frozen_declared": manifest.get("n_frozen"),
        "n_unchanged": n_unchanged,
        "n_modified": n_modified,
        "n_missing": n_missing,
        "modifications": modifications,
        "all_unchanged": (n_modified == 0 and n_missing == 0),
        "n_frozen_matches_declared": (n_total == manifest.get("n_frozen")),
    }


# =============================================================================
# Step 2: Inventory frozen inputs
# =============================================================================

def inventory_inputs() -> dict:
    """Inventory all frozen inputs (cases, receipts)."""
    real_dir = DSB_DIR / "cases" / "real"
    fab_dir = DSB_DIR / "cases" / "fabricated"
    receipts_dir = DSB_DIR / "receipts"

    real_cases = sorted(real_dir.glob("DSB-R-*.json"))
    fab_cases = sorted(fab_dir.glob("DSB-F-*.json"))
    receipts = sorted(receipts_dir.glob("RECEIPT-*.json"))

    # Hash every input
    real_hashes = {p.name: sha256_file(p) for p in real_cases}
    fab_hashes = {p.name: sha256_file(p) for p in fab_cases}
    receipt_hashes = {p.name: sha256_file(p) for p in receipts}

    return {
        "real_cases": {
            "n": len(real_cases),
            "files": [p.name for p in real_cases],
            "hashes": real_hashes,
        },
        "fabricated_cases": {
            "n": len(fab_cases),
            "files": [p.name for p in fab_cases],
            "hashes": fab_hashes,
        },
        "receipts": {
            "n": len(receipts),
            "files": [p.name for p in receipts],
            "hashes": receipt_hashes,
        },
    }


# =============================================================================
# Step 3: Recompute all 80 scorer outcomes from frozen receipts
# =============================================================================

def recompute_all_scores() -> dict:
    """Recompute all 80 scorer outcomes directly from frozen receipts + frozen cases."""
    from discovery_fabric.dsb_v1.scorer import score_receipt
    from discovery_fabric.dsb_v1.case_schema import load_case

    real_dir = DSB_DIR / "cases" / "real"
    fab_dir = DSB_DIR / "cases" / "fabricated"
    receipts_dir = DSB_DIR / "receipts"

    # Load all cases
    cases = {}
    for d in [real_dir, fab_dir]:
        for cp in sorted(d.glob("DSB-*.json")):
            case = load_case(cp)
            cases[case["case_id"]] = case

    # Score every receipt
    scores = []
    for rp in sorted(receipts_dir.glob("RECEIPT-*.json")):
        with open(rp) as f:
            receipt = json.load(f)
        case_id = receipt.get("case_id")
        case = cases.get(case_id)
        if not case:
            continue
        score = score_receipt(receipt, case)
        scores.append(score)

    return {"n_scores": len(scores), "scores": scores}


# =============================================================================
# Step 4: Independently regenerate the 13-recovery list
# =============================================================================

def regenerate_recovery_list(scores: list) -> dict:
    """Independently regenerate the list of RECOVERED receipts."""
    recovered = []
    for s in scores:
        if s["discovery_structure_recovery"]["verdict"] == "RECOVERED":
            recovered.append({
                "receipt_id": s["receipt_id"],
                "case_id": s["case_id"],
                "case_type": s["case_type"],
                "arm": s["arm"],
                "score": s["discovery_structure_recovery"]["score"],
            })

    # Sort by score descending for readability
    recovered.sort(key=lambda x: -x["score"])

    # Count by case_type
    by_type = {}
    for r in recovered:
        ct = r["case_type"]
        by_type[ct] = by_type.get(ct, 0) + 1

    return {
        "n_recovered": len(recovered),
        "by_case_type": by_type,
        "recovered_list": recovered,
    }


# =============================================================================
# Step 5: Verify 10 fabricated + 3 real = 13
# =============================================================================

def verify_recovery_counts(recovery_data: dict) -> dict:
    """Verify the recovery counts: 10 fabricated + 3 real = 13."""
    by_type = recovery_data["by_case_type"]
    n_fabricated = by_type.get("fabricated", 0)
    n_real = by_type.get("real", 0)
    n_total = recovery_data["n_recovered"]

    return {
        "n_fabricated": n_fabricated,
        "n_real": n_real,
        "n_total": n_total,
        "fabricated_plus_real_equals_total": (n_fabricated + n_real) == n_total,
        "expected_fabricated": 10,
        "expected_real": 3,
        "expected_total": 13,
        "fabricated_matches_expected": n_fabricated == 10,
        "real_matches_expected": n_real == 3,
        "total_matches_expected": n_total == 13,
    }


# =============================================================================
# Step 6: Regenerate the 14 focused-review packet IDs
# =============================================================================

def regenerate_focused_review_packets(scores: list) -> dict:
    """Regenerate the 14 focused-review packet IDs.

    Selection criteria (NO human outcomes used):
      (a) All receipts where scorer returned discovery_structure_recovery.verdict == RECOVERED
      (b) For each arm, the top-2 fabricated cases by discovery-structure score

    Union of (a) and (b) should be 14 packet IDs.
    """
    from discovery_fabric.dsb_v1.case_schema import load_case

    real_dir = DSB_DIR / "cases" / "real"
    fab_dir = DSB_DIR / "cases" / "fabricated"

    # Load cases
    cases = {}
    for d in [real_dir, fab_dir]:
        for cp in sorted(d.glob("DSB-*.json")):
            case = load_case(cp)
            cases[case["case_id"]] = case

    # Criterion (a): all RECOVERED receipts
    criterion_a = set()
    for s in scores:
        if s["discovery_structure_recovery"]["verdict"] == "RECOVERED":
            criterion_a.add(s["receipt_id"])

    # Criterion (b): top-2 fabricated per arm by discovery score
    by_arm_fab = {}
    for s in scores:
        case = cases.get(s["case_id"], {})
        if case.get("case_type") != "fabricated":
            continue
        arm = s["arm"]
        disc_score = s["discovery_structure_recovery"]["score"]
        if arm not in by_arm_fab:
            by_arm_fab[arm] = []
        by_arm_fab[arm].append((disc_score, s["receipt_id"]))

    criterion_b = set()
    for arm, lst in by_arm_fab.items():
        lst.sort(key=lambda x: -x[0])
        for score, rid in lst[:2]:
            criterion_b.add(rid)

    union = criterion_a | criterion_b

    # Map receipt_ids to packet_ids (replicate the packet_id construction)
    # packet_id = "ADJ-" + sha256(f"{receipt_id}|{receipt_hash}")[:12]
    packet_id_map = {}
    receipts_dir = DSB_DIR / "receipts"
    for rp in sorted(receipts_dir.glob("RECEIPT-*.json")):
        with open(rp) as f:
            receipt = json.load(f)
        rid = receipt["receipt_id"]
        seed = f"{rid}|{receipt['receipt_hash']}"
        packet_id = "ADJ-" + sha256_str(seed)[:12]
        packet_id_map[rid] = packet_id

    union_packet_ids = sorted([packet_id_map[rid] for rid in union if rid in packet_id_map])

    return {
        "criterion_a_count": len(criterion_a),
        "criterion_a_receipt_ids": sorted(criterion_a),
        "criterion_b_count": len(criterion_b),
        "criterion_b_receipt_ids": sorted(criterion_b),
        "union_count": len(union),
        "union_receipt_ids": sorted(union),
        "union_packet_ids": union_packet_ids,
        "selection_used_human_outcomes": False,
    }


# =============================================================================
# Step 7: Verify focused-review packet IDs match the frozen file
# =============================================================================

def verify_focused_review_match(regenerated: dict) -> dict:
    """Verify the regenerated packet IDs match the frozen focused_review_packets_BLIND.json."""
    frozen_path = DSB_DIR / "adjudication" / "focused_review_packets_BLIND.json"
    if not frozen_path.exists():
        return {"error": "focused_review_packets_BLIND.json not found", "match": False}

    with open(frozen_path) as f:
        frozen_data = json.load(f)

    frozen_packet_ids = sorted([p["packet_id"] for p in frozen_data["priority_packets"]])
    regenerated_packet_ids = regenerated["union_packet_ids"]

    return {
        "frozen_packet_ids_count": len(frozen_packet_ids),
        "regenerated_packet_ids_count": len(regenerated_packet_ids),
        "frozen_packet_ids": frozen_packet_ids,
        "regenerated_packet_ids": regenerated_packet_ids,
        "match": frozen_packet_ids == regenerated_packet_ids,
    }


# =============================================================================
# Step 8: Cross-check receipt hashes (receipt_hash field vs file hash)
# =============================================================================

def verify_receipt_integrity() -> dict:
    """Verify each receipt's stored receipt_hash matches its recomputed hash."""
    from discovery_fabric.dsb_v1.generator import verify_receipt

    receipts_dir = DSB_DIR / "receipts"
    n_total = 0
    n_valid = 0
    n_invalid = 0
    invalid_list = []

    for rp in sorted(receipts_dir.glob("RECEIPT-*.json")):
        with open(rp) as f:
            receipt = json.load(f)
        n_total += 1
        if verify_receipt(receipt):
            n_valid += 1
        else:
            n_invalid += 1
            invalid_list.append(rp.name)

    return {
        "n_total": n_total,
        "n_valid": n_valid,
        "n_invalid": n_invalid,
        "invalid_files": invalid_list,
        "all_valid": n_invalid == 0,
    }


# =============================================================================
# Step 9: Per-arm summary (recomputed)
# =============================================================================

def per_arm_summary(scores: list) -> dict:
    """Recompute per-arm summary: n, recoveries, mean scores."""
    from collections import defaultdict
    by_arm = defaultdict(lambda: {"n": 0, "recovered": 0, "mech_reconstructed": 0,
                                   "disc_score_sum": 0.0, "mech_score_sum": 0.0,
                                   "real_recovered": 0, "fab_recovered": 0,
                                   "real_n": 0, "fab_n": 0})
    for s in scores:
        arm = s["arm"]
        ctype = s["case_type"]
        by_arm[arm]["n"] += 1
        if ctype == "real":
            by_arm[arm]["real_n"] += 1
        else:
            by_arm[arm]["fab_n"] += 1
        if s["discovery_structure_recovery"]["verdict"] == "RECOVERED":
            by_arm[arm]["recovered"] += 1
            if ctype == "real":
                by_arm[arm]["real_recovered"] += 1
            else:
                by_arm[arm]["fab_recovered"] += 1
        if s["mechanism_reconstruction"]["verdict"] == "RECONSTRUCTED":
            by_arm[arm]["mech_reconstructed"] += 1
        by_arm[arm]["disc_score_sum"] += s["discovery_structure_recovery"]["score"]
        by_arm[arm]["mech_score_sum"] += s["mechanism_reconstruction"]["score"]

    summary = {}
    for arm, d in sorted(by_arm.items()):
        summary[arm] = {
            "n": d["n"],
            "real_n": d["real_n"],
            "fab_n": d["fab_n"],
            "recovered": d["recovered"],
            "real_recovered": d["real_recovered"],
            "fab_recovered": d["fab_recovered"],
            "mech_reconstructed": d["mech_reconstructed"],
            "disc_score_mean": round(d["disc_score_sum"] / max(d["n"], 1), 4),
            "mech_score_mean": round(d["mech_score_sum"] / max(d["n"], 1), 4),
        }
    return summary


# =============================================================================
# Main: produce the forensic recomputation report
# =============================================================================

def main():
    print("=" * 72)
    print("DSB V1 — FORENSIC RECOMPUTATION (from frozen receipts only)")
    print("=" * 72)
    print()

    # Step 1: Verify freeze manifest
    print("[Step 1] Verifying freeze manifest...")
    freeze_check = verify_freeze_manifest()
    print(f"  Total frozen: {freeze_check['n_total']}")
    print(f"  Unchanged: {freeze_check['n_unchanged']}")
    print(f"  Modified: {freeze_check['n_modified']}")
    print(f"  Missing: {freeze_check['n_missing']}")
    print(f"  All unchanged: {freeze_check['all_unchanged']}")

    # Step 2: Inventory inputs
    print("\n[Step 2] Inventorying frozen inputs...")
    inputs = inventory_inputs()
    print(f"  Real cases: {inputs['real_cases']['n']}")
    print(f"  Fabricated cases: {inputs['fabricated_cases']['n']}")
    print(f"  Receipts: {inputs['receipts']['n']}")

    # Step 3: Verify receipt integrity
    print("\n[Step 3] Verifying receipt integrity (stored hash vs recomputed hash)...")
    receipt_integrity = verify_receipt_integrity()
    print(f"  Valid: {receipt_integrity['n_valid']}/{receipt_integrity['n_total']}")
    print(f"  All valid: {receipt_integrity['all_valid']}")

    # Step 4: Recompute all 80 scores
    print("\n[Step 4] Recomputing all 80 scorer outcomes from frozen receipts...")
    scores_result = recompute_all_scores()
    print(f"  Scores recomputed: {scores_result['n_scores']}")

    # Step 5: Regenerate 13-recovery list
    print("\n[Step 5] Independently regenerating 13-recovery list...")
    recovery_data = regenerate_recovery_list(scores_result["scores"])
    print(f"  Recoveries: {recovery_data['n_recovered']}")
    print(f"  By case_type: {recovery_data['by_case_type']}")

    # Step 6: Verify counts
    print("\n[Step 6] Verifying 10 fabricated + 3 real = 13...")
    count_check = verify_recovery_counts(recovery_data)
    print(f"  Fabricated: {count_check['n_fabricated']} (expected 10) — match: {count_check['fabricated_matches_expected']}")
    print(f"  Real: {count_check['n_real']} (expected 3) — match: {count_check['real_matches_expected']}")
    print(f"  Total: {count_check['n_total']} (expected 13) — match: {count_check['total_matches_expected']}")

    # Step 7: Regenerate focused-review packet IDs
    print("\n[Step 7] Regenerating 14 focused-review packet IDs (no human outcomes)...")
    focused = regenerate_focused_review_packets(scores_result["scores"])
    print(f"  Criterion A (recoveries): {focused['criterion_a_count']}")
    print(f"  Criterion B (top-2 fab per arm): {focused['criterion_b_count']}")
    print(f"  Union: {focused['union_count']}")
    print(f"  Selection used human outcomes: {focused['selection_used_human_outcomes']}")

    # Step 8: Verify focused-review match
    print("\n[Step 8] Verifying regenerated packet IDs match frozen file...")
    focused_match = verify_focused_review_match(focused)
    print(f"  Frozen count: {focused_match['frozen_packet_ids_count']}")
    print(f"  Regenerated count: {focused_match['regenerated_packet_ids_count']}")
    print(f"  Match: {focused_match['match']}")

    # Step 9: Per-arm summary
    print("\n[Step 9] Per-arm summary (recomputed)...")
    arm_summary = per_arm_summary(scores_result["scores"])
    for arm, s in arm_summary.items():
        print(f"  {arm}: n={s['n']}, recovered={s['recovered']} (real={s['real_recovered']}, fab={s['fab_recovered']}), "
              f"disc_mean={s['disc_score_mean']}, mech_mean={s['mech_score_mean']}")

    # ===== Produce the report =====
    print("\n[Producing report] DSB_V1_FORENSIC_RECOMPUTATION.md")

    report = []
    report.append("# DSB V1 — FORENSIC RECOMPUTATION")
    report.append("")
    report.append(f"**Date:** {datetime.now(timezone.utc).isoformat()}")
    report.append("**Source:** Frozen receipts only. No new modules. No interpretation.")
    report.append("**Purpose:** Recompute all DSB V1 outcomes from frozen artifacts; verify counts, hashes, and selections.")
    report.append("")
    report.append("---")
    report.append("")

    # Section 1: Inputs
    report.append("## 1. Inputs (Frozen Artifacts)")
    report.append("")
    report.append(f"- Real cases: **{inputs['real_cases']['n']}** files")
    for f in inputs['real_cases']['files']:
        report.append(f"  - `{f}` — SHA-256: `{inputs['real_cases']['hashes'][f][:32]}...`")
    report.append(f"- Fabricated cases: **{inputs['fabricated_cases']['n']}** files")
    for f in inputs['fabricated_cases']['files']:
        report.append(f"  - `{f}` — SHA-256: `{inputs['fabricated_cases']['hashes'][f][:32]}...`")
    report.append(f"- Receipts: **{inputs['receipts']['n']}** files")
    report.append(f"  - (all 80 receipt hashes verified in §3 below)")
    report.append("")

    # Section 2: Freeze manifest verification
    report.append("## 2. Freeze Manifest Verification")
    report.append("")
    report.append(f"- Manifest hash: `{freeze_check['manifest_hash'][:32]}...`")
    report.append(f"- Frozen at: `{freeze_check['frozen_at']}`")
    report.append(f"- Total frozen artifacts: **{freeze_check['n_total']}**")
    report.append(f"- Unchanged: **{freeze_check['n_unchanged']}**")
    report.append(f"- Modified: **{freeze_check['n_modified']}**")
    report.append(f"- Missing: **{freeze_check['n_missing']}**")
    report.append(f"- All artifacts unchanged after freeze: **{freeze_check['all_unchanged']}**")
    if freeze_check['modifications']:
        report.append("")
        report.append("### Modifications detected:")
        report.append("")
        for m in freeze_check['modifications']:
            report.append(f"- `{m['path']}` — status: {m['status']}")
            if m['status'] == 'MODIFIED':
                report.append(f"  - expected: `{m['expected']}...`")
                report.append(f"  - actual: `{m['actual']}...`")
    report.append("")

    # Section 3: Receipt integrity
    report.append("## 3. Receipt Integrity (stored hash vs recomputed hash)")
    report.append("")
    report.append(f"- Total receipts: **{receipt_integrity['n_total']}**")
    report.append(f"- Valid (hash matches): **{receipt_integrity['n_valid']}**")
    report.append(f"- Invalid (hash mismatch): **{receipt_integrity['n_invalid']}**")
    report.append(f"- All valid: **{receipt_integrity['all_valid']}**")
    if receipt_integrity['invalid_files']:
        report.append("")
        report.append("### Invalid files:")
        for f in receipt_integrity['invalid_files']:
            report.append(f"- `{f}`")
    report.append("")

    # Section 4: Recomputed scores
    report.append("## 4. Recomputed Scorer Outcomes (80 receipts)")
    report.append("")
    report.append(f"- Total scores recomputed: **{scores_result['n_scores']}**")
    report.append("")
    report.append("### Per-arm summary (recomputed)")
    report.append("")
    report.append("| Arm | N | Real N | Fab N | Recovered | Real Recovered | Fab Recovered | Mech Reconstructed | Disc Score Mean | Mech Score Mean |")
    report.append("|---|---|---|---|---|---|---|---|---|---|")
    for arm, s in arm_summary.items():
        report.append(f"| {arm} | {s['n']} | {s['real_n']} | {s['fab_n']} | {s['recovered']} | {s['real_recovered']} | {s['fab_recovered']} | {s['mech_reconstructed']} | {s['disc_score_mean']} | {s['mech_score_mean']} |")
    report.append("")

    # Section 5: 13-recovery list
    report.append("## 5. Independently Regenerated 13-Recovery List")
    report.append("")
    report.append(f"- Total recoveries: **{recovery_data['n_recovered']}**")
    report.append(f"- By case type: **{recovery_data['by_case_type']}**")
    report.append("")
    report.append("### Recovery list (sorted by score descending)")
    report.append("")
    report.append("| Receipt ID | Case ID | Case Type | Arm | Score |")
    report.append("|---|---|---|---|---|")
    for r in recovery_data['recovered_list']:
        report.append(f"| {r['receipt_id']} | {r['case_id']} | {r['case_type']} | {r['arm']} | {r['score']} |")
    report.append("")

    # Section 6: Count verification
    report.append("## 6. Count Verification: 10 Fabricated + 3 Real = 13")
    report.append("")
    report.append(f"- Fabricated recoveries: **{count_check['n_fabricated']}** (expected 10) — match: **{count_check['fabricated_matches_expected']}**")
    report.append(f"- Real recoveries: **{count_check['n_real']}** (expected 3) — match: **{count_check['real_matches_expected']}**")
    report.append(f"- Total recoveries: **{count_check['n_total']}** (expected 13) — match: **{count_check['total_matches_expected']}**")
    report.append(f"- Fabricated + Real = Total: **{count_check['fabricated_plus_real_equals_total']}**")
    report.append("")

    # Section 7: Focused-review packet IDs
    report.append("## 7. Regenerated 14 Focused-Review Packet IDs")
    report.append("")
    report.append("### Selection criteria (NO human outcomes used)")
    report.append("")
    report.append(f"- Criterion A (all RECOVERED receipts): **{focused['criterion_a_count']}** receipts")
    for rid in focused['criterion_a_receipt_ids']:
        report.append(f"  - `{rid}`")
    report.append(f"- Criterion B (top-2 fabricated per arm by discovery score): **{focused['criterion_b_count']}** receipts")
    for rid in focused['criterion_b_receipt_ids']:
        report.append(f"  - `{rid}`")
    report.append(f"- Union: **{focused['union_count']}** receipts")
    report.append(f"- Selection used human outcomes: **{focused['selection_used_human_outcomes']}**")
    report.append("")
    report.append("### Union packet IDs (14 expected)")
    report.append("")
    for pid in focused['union_packet_ids']:
        report.append(f"- `{pid}`")
    report.append("")

    # Section 8: Focused-review match verification
    report.append("## 8. Focused-Review Packet ID Match Verification")
    report.append("")
    report.append(f"- Frozen packet IDs count: **{focused_match['frozen_packet_ids_count']}**")
    report.append(f"- Regenerated packet IDs count: **{focused_match['regenerated_packet_ids_count']}**")
    report.append(f"- Match (frozen == regenerated): **{focused_match['match']}**")
    report.append("")
    report.append("### Frozen packet IDs (from focused_review_packets_BLIND.json)")
    report.append("")
    for pid in focused_match['frozen_packet_ids']:
        report.append(f"- `{pid}`")
    report.append("")
    report.append("### Regenerated packet IDs")
    report.append("")
    for pid in focused_match['regenerated_packet_ids']:
        report.append(f"- `{pid}`")
    report.append("")

    # Section 9: Summary of all checks
    report.append("## 9. Summary of All Forensic Checks")
    report.append("")
    report.append("| Check | Result |")
    report.append("|---|---|")
    report.append(f"| Freeze manifest — all artifacts unchanged | **{'PASS' if freeze_check['all_unchanged'] else 'FAIL'}** |")
    report.append(f"| Receipt integrity — all 80 hashes valid | **{'PASS' if receipt_integrity['all_valid'] else 'FAIL'}** |")
    report.append(f"| Recomputed scores — 80/80 | **{'PASS' if scores_result['n_scores'] == 80 else 'FAIL'}** |")
    report.append(f"| Recovery count — 13 total | **{'PASS' if count_check['total_matches_expected'] else 'FAIL'}** |")
    report.append(f"| Recovery split — 10 fabricated + 3 real | **{'PASS' if count_check['fabricated_matches_expected'] and count_check['real_matches_expected'] else 'FAIL'}** |")
    report.append(f"| Focused-review — 14 packet IDs | **{'PASS' if focused['union_count'] == 14 else 'FAIL'}** |")
    report.append(f"| Focused-review — regenerated matches frozen | **{'PASS' if focused_match['match'] else 'FAIL'}** |")
    report.append(f"| Focused-review — no human outcomes used in selection | **{'PASS' if not focused['selection_used_human_outcomes'] else 'FAIL'}** |")
    report.append("")
    report.append("---")
    report.append("")
    report.append("**End of forensic recomputation. No interpretation. STOP.**")

    # Write report
    out_path = DSB_DIR / "DSB_V1_FORENSIC_RECOMPUTATION.md"
    with open(out_path, "w") as f:
        f.write("\n".join(report))
    print(f"\nReport written: {out_path}")
    print(f"Report SHA-256: {sha256_file(out_path)[:32]}...")


if __name__ == "__main__":
    main()
