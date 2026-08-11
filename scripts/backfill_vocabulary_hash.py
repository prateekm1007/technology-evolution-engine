#!/usr/bin/env python3
"""
backfill_vocabulary_hash.py — Fix the 23 broken vocabulary_hash entries (F-072).

Per cycle 138: 23 of 35 reaudit entries have vocabulary_hash = hash of empty
string because the original code only checked 6 field names that didn't match
the actual claim entry structure. This script recomputes the vocabulary_hash
for all reaudit entries using the fixed compute_vocabulary_hash logic.

Per Law 7: this does NOT alter outcomes, verdicts, or overturned flags. It
only fixes the metadata field that was broken. A backfill event is appended
to the ledger to record the correction.
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[1]
PREDICTIONS = REPO / "data" / "ledger" / "predictions.jsonl"
sys.path.insert(0, str(REPO))

from scripts.reaudit_loop import compute_vocabulary_hash


def backfill():
    if not PREDICTIONS.exists():
        print("ERROR: predictions.jsonl not found")
        return

    # Read all entries
    with PREDICTIONS.open() as f:
        lines = f.readlines()

    fixed_count = 0
    total_reaudit = 0
    empty_hash_before = 0
    new_lines = []

    for line in lines:
        try:
            entry = json.loads(line.strip())
        except json.JSONDecodeError:
            new_lines.append(line)
            continue

        if entry.get("type") != "reaudit":
            new_lines.append(line)
            continue

        total_reaudit += 1
        old_hash = entry.get("vocabulary_hash", "")

        # Check if the hash is broken (empty-string hash)
        import hashlib
        empty_hash = hashlib.sha256(b'').hexdigest()[:16]
        if old_hash == empty_hash:
            empty_hash_before += 1

        # Recompute the hash using the fixed logic
        # We need to find the original claim entry to get the literature terms
        claim_id = entry.get("claim_id", "")
        vocab_terms = []

        # First: check if the reaudit entry itself has literature fields
        for key in ("lit_A", "lit_B", "literature_A", "literature_B",
                    "lit_a_query", "lit_b_query"):
            if key in entry and entry[key]:
                vocab_terms.append(str(entry[key]))

        # Fallback: find the original claim entry in the ledger
        if not vocab_terms:
            for line2 in lines:
                try:
                    e2 = json.loads(line2.strip())
                    if (e2.get("type") in ("blind_test_result", "claim") and
                        (e2.get("experiment_id") == claim_id or
                         e2.get("test_id") == claim_id)):
                        # Extract literature terms from the claim
                        for key in ("lit_A", "lit_B", "literature_A", "literature_B",
                                    "lit_a_query", "lit_b_query", "lit_A_query", "lit_B_query"):
                            if key in e2 and e2[key]:
                                vocab_terms.append(str(e2[key]))
                        # Fallback: bridges_description
                        if not vocab_terms and "bridges_description" in e2:
                            vocab_terms.append(str(e2["bridges_description"]))
                        # Fallback: cross_details
                        if not vocab_terms and "cross_details" in e2:
                            for item in e2["cross_details"]:
                                if isinstance(item, dict):
                                    for v in item.values():
                                        if v:
                                            vocab_terms.append(str(v))
                        # Fallback: all string values
                        if not vocab_terms:
                            for k, v in e2.items():
                                if k in ("type", "timestamp", "writer", "outcome", "expected"):
                                    continue
                                if v and isinstance(v, str) and len(v) >= 3:
                                    vocab_terms.append(v)
                        break
                except json.JSONDecodeError:
                    continue

        # Final fallback: use claim_id
        if not vocab_terms:
            vocab_terms = [claim_id or "unknown_claim"]

        new_hash = compute_vocabulary_hash(vocab_terms)

        if new_hash != old_hash:
            entry["vocabulary_hash"] = new_hash
            entry["vocabulary_hash_backfilled"] = True
            entry["vocabulary_hash_backfill_cycle"] = 138
            fixed_count += 1

        new_lines.append(json.dumps(entry) + "\n")

    # Write back
    with PREDICTIONS.open("w") as f:
        f.writelines(new_lines)

    # Append backfill event
    backfill_event = {
        "type": "vocabulary_hash_backfill",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cycle": 138,
        "writer": "scripts.backfill_vocabulary_hash",
        "total_reaudit_entries": total_reaudit,
        "empty_hash_before": empty_hash_before,
        "fixed_count": fixed_count,
        "reason": "F-072 fix: vocabulary_hash was hash-of-empty-string for 23/35 entries because original code only checked 6 field names that didn't match claim entry structure. Recomputed all hashes with fixed fallback logic.",
    }
    with PREDICTIONS.open("a") as f:
        f.write(json.dumps(backfill_event) + "\n")

    print(f"Total reaudit entries: {total_reaudit}")
    print(f"Empty hash before: {empty_hash_before}")
    print(f"Fixed: {fixed_count}")
    print(f"Backfill event appended to ledger.")


if __name__ == "__main__":
    backfill()
