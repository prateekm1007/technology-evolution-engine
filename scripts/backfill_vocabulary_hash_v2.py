#!/usr/bin/env python3
"""
backfill_vocabulary_hash_v2.py — Fix F-072 completely: backfill BOTH ledger files.

Per cycle 139 (auditor-caught): the cycle-138 backfill only rewrote
predictions.jsonl and missed reaudit_log.jsonl — the second mirror file
that log_reaudit() writes to. reaudit_log.jsonl was still 23/34 (67.6%)
broken. This script backfills BOTH files using a shared function so a
fix to one ledger can't diverge from the other again.

Per Law 7: this is a metadata correction, not an outcome alteration.
Verdicts, overturned flags, and confidences are preserved. Only the
vocabulary_hash field (and backfill markers) are changed. A backfill
event is appended to BOTH files.
"""
import json
import sys
import hashlib
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[1]
PREDICTIONS = REPO / "data" / "ledger" / "predictions.jsonl"
REAUDIT_LOG = REPO / "data" / "ledger" / "reaudit_log.jsonl"
sys.path.insert(0, str(REPO))

from scripts.reaudit_loop import compute_vocabulary_hash

EMPTY_HASH = hashlib.sha256(b'').hexdigest()[:16]

# Both files that log_reaudit() writes to — must stay in sync.
LEDGER_FILES = [PREDICTIONS, REAUDIT_LOG]


def find_claim_entry(claim_id: str, all_lines: list) -> dict:
    """Find the original claim entry for a given claim_id."""
    for line in all_lines:
        try:
            e = json.loads(line.strip())
            if (e.get("type") in ("blind_test_result", "claim") and
                (e.get("experiment_id") == claim_id or e.get("test_id") == claim_id)):
                return e
        except json.JSONDecodeError:
            continue
    return {}


def extract_vocab_terms(entry: dict, claim_id: str, all_lines: list) -> list:
    """Extract vocabulary terms using the same logic as the fixed reaudit_loop.py."""
    vocab_terms = []

    # Primary: check all known literature field names
    for key in ("lit_A", "lit_B", "literature_A", "literature_B",
                "lit_a_query", "lit_b_query", "lit_A_query", "lit_B_query",
                "literature_a", "literature_b"):
        if key in entry and entry[key]:
            vocab_terms.append(str(entry[key]))

    # Fallback 1: bridges/cross_details
    if not vocab_terms:
        for bridge_key in ("bridges_description", "bridge", "cross_details"):
            if bridge_key in entry and entry[bridge_key]:
                val = entry[bridge_key]
                if isinstance(val, str):
                    vocab_terms.append(val)
                elif isinstance(val, list):
                    for item in val:
                        if isinstance(item, dict):
                            for v in item.values():
                                if v:
                                    vocab_terms.append(str(v))
                        elif item:
                            vocab_terms.append(str(item))

    # Fallback 2: all string values from the entry
    if not vocab_terms:
        skip_keys = {"type", "timestamp", "writer", "outcome", "expected",
                     "extraction_log_proves_separation", "cycle"}
        for k, v in entry.items():
            if k in skip_keys:
                continue
            if v and isinstance(v, str) and len(v) >= 3:
                vocab_terms.append(v)
            elif v and isinstance(v, (int, float)):
                vocab_terms.append(str(v))

    # Fallback 3: claim_id
    if not vocab_terms:
        vocab_terms = [claim_id or "unknown_claim"]

    return vocab_terms


def backfill_file(ledger_path: Path, all_lines: list, claim_cache: dict) -> dict:
    """Backfill vocabulary_hash in a single ledger file. Returns stats.

    Uses claim_cache (precomputed from predictions.jsonl) so both ledger
    files get identical hashes for the same claim_id. This prevents the
    divergence that happened in cycle 138/139 where each file computed
    hashes from its own (different) source data.
    """
    if not ledger_path.exists():
        return {"file": str(ledger_path), "error": "file not found"}

    fixed_count = 0
    total_reaudit = 0
    empty_hash_before = 0
    new_lines = []

    for line in ledger_path.open():
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

        if old_hash == EMPTY_HASH:
            empty_hash_before += 1

        # Use the claim_cache (canonical source from predictions.jsonl)
        # so both files get identical hashes for the same claim_id.
        claim_id = entry.get("claim_id", "")
        source_entry = claim_cache.get(claim_id)

        if source_entry:
            # Found a canonical claim entry — use it for both files
            vocab_terms = extract_vocab_terms(source_entry, claim_id, all_lines)
        else:
            # No claim entry found — use ONLY the claim_id as the vocabulary
            # term. This is deterministic and identical for both files.
            # (The previous fallback used the reaudit entry itself, which
            # differs between the two files because evidence_summary content
            # differs, causing hash divergence.)
            vocab_terms = [claim_id or "unknown_claim"]

        new_hash = compute_vocabulary_hash(vocab_terms)

        if new_hash != old_hash:
            entry["vocabulary_hash"] = new_hash
            entry["vocabulary_hash_backfilled"] = True
            entry["vocabulary_hash_backfill_cycle"] = 139
            fixed_count += 1

        new_lines.append(json.dumps(entry, default=str) + "\n")

    # Write back
    with ledger_path.open("w") as f:
        f.writelines(new_lines)

    return {
        "file": str(ledger_path),
        "total_reaudit": total_reaudit,
        "empty_hash_before": empty_hash_before,
        "fixed_count": fixed_count,
    }


def main():
    # Read all lines from predictions.jsonl once (for claim lookup)
    all_lines = PREDICTIONS.read_text().splitlines() if PREDICTIONS.exists() else []

    # Build a canonical claim cache from predictions.jsonl so both ledger
    # files get identical hashes for the same claim_id. This prevents the
    # divergence that happened in cycle 138/139.
    claim_cache = {}
    for line in all_lines:
        try:
            e = json.loads(line.strip())
            if e.get("type") in ("blind_test_result", "claim"):
                eid = e.get("experiment_id") or e.get("test_id", "")
                if eid:
                    claim_cache[eid] = e
        except json.JSONDecodeError:
            continue

    print("=" * 60)
    print("F-072 complete backfill — BOTH ledger files (canonical source)")
    print("=" * 60)
    print(f"Claim cache: {len(claim_cache)} entries from predictions.jsonl")

    results = []
    for ledger_path in LEDGER_FILES:
        print(f"\nBackfilling {ledger_path.name}...")
        result = backfill_file(ledger_path, all_lines, claim_cache)
        results.append(result)
        if "error" in result:
            print(f"  ERROR: {result['error']}")
        else:
            print(f"  Total reaudit: {result['total_reaudit']}")
            print(f"  Empty hash before: {result['empty_hash_before']}")
            print(f"  Fixed: {result['fixed_count']}")

    # Append backfill event to BOTH files
    backfill_event = {
        "type": "vocabulary_hash_backfill",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cycle": 139,
        "writer": "scripts.backfill_vocabulary_hash_v2",
        "reason": "F-072 complete fix: cycle 138 backfill only reached predictions.jsonl, missed reaudit_log.jsonl (23/34 still broken). This backfill covers BOTH mirror files using a shared function.",
        "files_backfilled": [r.get("file", "") for r in results],
        "results": results,
    }

    for ledger_path in LEDGER_FILES:
        if ledger_path.exists():
            with ledger_path.open("a") as f:
                f.write(json.dumps(backfill_event, default=str) + "\n")

    print(f"\nBackfill event appended to both files.")

    # Verify
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)
    for ledger_path in LEDGER_FILES:
        if not ledger_path.exists():
            continue
        total = empty = 0
        with ledger_path.open() as f:
            for line in f:
                try:
                    e = json.loads(line.strip())
                    if e.get("type") == "reaudit":
                        total += 1
                        if e.get("vocabulary_hash") == EMPTY_HASH:
                            empty += 1
                except json.JSONDecodeError:
                    continue
        pct = (empty / total * 100) if total else 0
        status = "OK" if empty == 0 else "BROKEN"
        print(f"  {ledger_path.name}: {empty}/{total} ({pct:.1f}%) broken — {status}")


if __name__ == "__main__":
    main()
