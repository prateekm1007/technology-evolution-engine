"""
Diverse-domain mechanism extractor — ensures cross-domain coverage.
Extracts mechanisms from ALL 8 domains, not just the first ones in the file.
"""
import json
import sys
import hashlib
import time
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from discovery_fabric.connectors.openrouter_llm import chat_json
from discovery_fabric.mechanisms.extractor_v3_openrouter import (
    extract_mechanism, MECHANISM_FIELDS, UNKNOWN, SYSTEM_PROMPT
)

EVIDENCE_FILE = REPO / "discovery_fabric/evidence/evidence.jsonl"
CHECKPOINT = REPO / "discovery_fabric/mechanisms/extraction_checkpoint_v4.json"
OUTPUT = REPO / "discovery_fabric/mechanisms/structured_mechanisms_v4.json"


def load_evidence_by_domain():
    """Load evidence grouped by domain."""
    by_domain = defaultdict(list)
    with open(EVIDENCE_FILE) as f:
        for line in f:
            if line.strip():
                e = json.loads(line)
                abstract = e.get("abstract", "")
                if abstract and abstract != "UNAVAILABLE" and len(abstract) > 50:
                    by_domain[e.get("domain", "?")].append(e)
    return by_domain


def load_checkpoint():
    if CHECKPOINT.exists():
        with open(CHECKPOINT) as f:
            return json.load(f)
    return {"processed_ids": [], "mechanisms": [], "status_counts": {}}


def save_checkpoint(cp):
    with open(CHECKPOINT, "w") as f:
        json.dump(cp, f, indent=2)


def main(per_domain=5):
    print(f"[{datetime.now(timezone.utc).isoformat()}] Diverse-domain extraction")
    print(f"  target: {per_domain} per domain × 8 domains = {per_domain * 8}")

    by_domain = load_evidence_by_domain()
    print(f"  domains: {list(by_domain.keys())}")

    cp = load_checkpoint()
    processed = set(cp["processed_ids"])
    mechanisms = cp["mechanisms"]
    status_counts = cp.get("status_counts", {})

    for domain, evidence in by_domain.items():
        domain_count = sum(1 for m in mechanisms if m.get("domain") == domain and m.get("extraction_status") == "SUCCESS")
        needed = per_domain - domain_count
        if needed <= 0:
            print(f"  {domain}: already has {domain_count}")
            continue

        print(f"  {domain}: need {needed} more")
        for e in evidence:
            if needed <= 0:
                break
            if e["id"] in processed:
                continue

            title = e.get("title", "")[:150]
            abstract = e.get("abstract", "")
            eid = e["id"]

            mechanism, status = extract_mechanism(title, abstract, eid)

            if mechanism:
                mechanism["evidence_id"] = eid
                mechanism["source"] = e.get("source", "")
                mechanism["domain"] = domain
                mechanism["source_uri"] = e.get("source_uri", "")
                mechanism["extraction_timestamp"] = datetime.now(timezone.utc).isoformat()
                mechanism["extraction_status"] = status
                mechanism["mechanism_hash"] = hashlib.sha256(
                    json.dumps(mechanism, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
                ).hexdigest()
                mechanisms.append(mechanism)
            else:
                mechanisms.append({
                    "evidence_id": eid, "source": e.get("source", ""), "domain": domain,
                    "extraction_status": status, "mechanism_hash": UNKNOWN,
                })

            status_counts[status] = status_counts.get(status, 0) + 1
            processed.add(eid)
            needed -= 1

            # Save after every item
            cp["processed_ids"] = list(processed)
            cp["mechanisms"] = mechanisms
            cp["status_counts"] = status_counts
            save_checkpoint(cp)

    # Final save
    with open(OUTPUT, "w") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_attempted": len(mechanisms),
            "status_counts": status_counts,
            "mechanisms": mechanisms,
        }, f, indent=2, ensure_ascii=False)

    # Summary by domain
    from collections import Counter
    success_by_domain = Counter(m.get("domain", "?") for m in mechanisms if m.get("extraction_status") == "SUCCESS")
    print(f"\n[{datetime.now(timezone.utc).isoformat()}] COMPLETE")
    print(f"  Total: {len(mechanisms)} | Status: {status_counts}")
    print(f"  Success by domain: {dict(success_by_domain)}")
    print(f"  Saved: {OUTPUT}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-domain", type=int, default=5)
    args = parser.parse_args()
    main(args.per_domain)
