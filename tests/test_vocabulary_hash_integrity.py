#!/usr/bin/env python3
"""
test_vocabulary_hash_integrity.py — CI test for F-072 regression prevention.

Per cycle 139 (auditor-caught): the cycle-138 backfill only reached one of
two mirror files. This test ensures vocabulary_hash is non-empty in BOTH
predictions.jsonl AND reaudit_log.jsonl, and that the two files agree.

This test FAILS if:
- Any reaudit entry has an empty-string vocabulary_hash
- The two ledger files have different counts of broken entries
- A reaudit entry exists in one file but not the other (divergence)
"""
import json
import hashlib
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PREDICTIONS = REPO / "data" / "ledger" / "predictions.jsonl"
REAUDIT_LOG = REPO / "data" / "ledger" / "reaudit_log.jsonl"

EMPTY_HASH = hashlib.sha256(b'').hexdigest()[:16]


def count_broken(filepath: Path) -> dict:
    """Count reaudit entries with broken vocabulary_hash."""
    if not filepath.exists():
        return {"total": 0, "broken": 0, "entries": []}
    total = 0
    broken = 0
    entries = {}
    with filepath.open() as f:
        for line in f:
            try:
                e = json.loads(line.strip())
                if e.get("type") == "reaudit":
                    total += 1
                    cid = e.get("claim_id", "")
                    vh = e.get("vocabulary_hash", "")
                    entries[cid] = vh
                    if vh == EMPTY_HASH or not vh:
                        broken += 1
            except json.JSONDecodeError:
                continue
    return {"total": total, "broken": broken, "entries": entries}


def test_predictions_no_broken_hashes():
    """predictions.jsonl must have 0 broken vocabulary_hash entries."""
    result = count_broken(PREDICTIONS)
    assert result["broken"] == 0, (
        f"predictions.jsonl has {result['broken']}/{result['total']} "
        f"broken vocabulary_hash entries (F-072 regression)"
    )


def test_reaudit_log_no_broken_hashes():
    """reaudit_log.jsonl must have 0 broken vocabulary_hash entries."""
    result = count_broken(REAUDIT_LOG)
    assert result["broken"] == 0, (
        f"reaudit_log.jsonl has {result['broken']}/{result['total']} "
        f"broken vocabulary_hash entries (F-072 regression — cycle 138 "
        f"backfill missed this file, cycle 139 fixed it)"
    )


def test_both_files_agree():
    """Both ledger files must have the same broken-entry count (no divergence)."""
    pred = count_broken(PREDICTIONS)
    reaud = count_broken(REAUDIT_LOG)
    # The counts may differ slightly (predictions.jsonl may have more entries
    # from other types), but the broken counts must both be 0
    assert pred["broken"] == 0 and reaud["broken"] == 0, (
        f"Ledger files diverge: predictions.jsonl has {pred['broken']} broken, "
        f"reaudit_log.jsonl has {reaud['broken']} broken. Both must be 0."
    )


def test_reaudit_entries_match_between_files():
    """Reaudit entries in both files should have matching vocabulary_hash values."""
    pred = count_broken(PREDICTIONS)
    reaud = count_broken(REAUDIT_LOG)
    mismatches = []
    for cid, vh in pred["entries"].items():
        if cid in reaud["entries"] and reaud["entries"][cid] != vh:
            mismatches.append(cid)
    assert len(mismatches) == 0, (
        f"{len(mismatches)} reaudit entries have different vocabulary_hash "
        f"values between the two ledger files: {mismatches[:5]}"
    )


def test_no_orphan_entries():
    """Every reaudit claim_id in predictions.jsonl must have a counterpart in
    reaudit_log.jsonl, and vice versa.

    Per cycle 140 (auditor-caught): EXP-AUTO-002 existed in predictions.jsonl
    but had no mirror in reaudit_log.jsonl — a dual-write miss from before the
    two logs were synchronized. The existing test_reaudit_entries_match_between_files
    only checks hash agreement for MATCHING claim_ids, not existence. This test
    closes that gap: it asserts every entry in one file has a counterpart in the
    other.
    """
    pred = count_broken(PREDICTIONS)
    reaud = count_broken(REAUDIT_LOG)
    pred_ids = set(pred["entries"].keys())
    reaud_ids = set(reaud["entries"].keys())
    orphans_in_pred = pred_ids - reaud_ids
    orphans_in_reaud = reaud_ids - pred_ids
    assert len(orphans_in_pred) == 0 and len(orphans_in_reaud) == 0, (
        f"Orphan entries found (dual-write miss):\n"
        f"  In predictions.jsonl but NOT in reaudit_log.jsonl: {sorted(orphans_in_pred)}\n"
        f"  In reaudit_log.jsonl but NOT in predictions.jsonl: {sorted(orphans_in_reaud)}\n"
        f"Every reaudit entry must exist in both ledger files."
    )


if __name__ == "__main__":
    tests = [
        test_predictions_no_broken_hashes,
        test_reaudit_log_no_broken_hashes,
        test_both_files_agree,
        test_reaudit_entries_match_between_files,
        test_no_orphan_entries,
    ]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  PASS: {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {test.__name__}: {e}")
            failed += 1
    print(f"\n{passed}/{passed + failed} tests passed.")
    sys.exit(0 if failed == 0 else 1)
