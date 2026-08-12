"""
DISCOVERY_FABRIC_V1_BASELINE — freeze current state.

Hashes:
- evidence.jsonl (7,032 objects)
- knowledge_graph.json
- discovery_candidates.json
- source quotas/queries/timestamps

This is a baseline, not a scientific result.
"""
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

REPO = Path(__file__).resolve().parents[2]
EVIDENCE_FILE = REPO / "discovery_fabric/evidence/evidence.jsonl"
GRAPH_FILE = REPO / "discovery_fabric/knowledge_graph/knowledge_graph.json"
CANDIDATES_FILE = REPO / "discovery_fabric/discovery_candidates/discovery_candidates.json"
BASELINE_DIR = REPO / "discovery_fabric/baseline"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_json(obj):
    canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Freezing DISCOVERY_FABRIC_V1_BASELINE")

    baseline = {
        "baseline_id": "DISCOVERY_FABRIC_V1_BASELINE",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "description": "Baseline of Discovery Evidence Fabric V1 — not a scientific result, a checkpoint.",
    }

    # 1. Hash evidence file
    evidence_hash = sha256_file(EVIDENCE_FILE)
    evidence_count = 0
    sources = Counter()
    domains = Counter()
    with open(EVIDENCE_FILE) as f:
        for line in f:
            if line.strip():
                e = json.loads(line)
                evidence_count += 1
                sources[e.get("source", "?")] += 1
                domains[e.get("domain", "?")] += 1

    baseline["evidence"] = {
        "file": str(EVIDENCE_FILE.relative_to(REPO)),
        "sha256": evidence_hash,
        "count": evidence_count,
        "by_source": dict(sources),
        "by_domain": dict(domains),
    }
    print(f"  evidence: {evidence_count} objects, hash: {evidence_hash[:16]}...")

    # 2. Hash graph
    graph_hash = sha256_file(GRAPH_FILE)
    with open(GRAPH_FILE) as f:
        graph = json.load(f)
    baseline["knowledge_graph"] = {
        "file": str(GRAPH_FILE.relative_to(REPO)),
        "sha256": graph_hash,
        "stats": graph.get("stats", {}),
    }
    print(f"  graph: {graph['stats']['total_edges']} edges, hash: {graph_hash[:16]}...")

    # 3. Hash candidates
    candidates_hash = sha256_file(CANDIDATES_FILE)
    with open(CANDIDATES_FILE) as f:
        cand_data = json.load(f)
    baseline["candidates"] = {
        "file": str(CANDIDATES_FILE.relative_to(REPO)),
        "sha256": candidates_hash,
        "count": cand_data.get("total_candidates", 0),
        "by_type": dict(Counter(c["discovery_type"] for c in cand_data.get("candidates", []))),
        "by_epistemic_state": dict(Counter(c.get("epistemic_state", "?") for c in cand_data.get("candidates", []))),
    }
    print(f"  candidates: {cand_data['total_candidates']}, hash: {candidates_hash[:16]}...")

    # 4. Source quotas/queries/timestamps
    source_quotas = {}
    with open(EVIDENCE_FILE) as f:
        for line in f:
            if line.strip():
                e = json.loads(line)
                src = e.get("source", "?")
                if src not in source_quotas:
                    source_quotas[src] = {
                        "count": 0,
                        "retrieval_method": e.get("retrieval_method", "unknown"),
                        "earliest_timestamp": e.get("retrieval_timestamp", ""),
                        "latest_timestamp": e.get("retrieval_timestamp", ""),
                    }
                source_quotas[src]["count"] += 1
                ts = e.get("retrieval_timestamp", "")
                if ts:
                    if source_quotas[src]["earliest_timestamp"] > ts:
                        source_quotas[src]["earliest_timestamp"] = ts
                    if source_quotas[src]["latest_timestamp"] < ts:
                        source_quotas[src]["latest_timestamp"] = ts

    baseline["source_quotas"] = source_quotas
    print(f"  sources: {len(source_quotas)}")

    # 5. Baseline manifest hash
    baseline["baseline_manifest_hash"] = sha256_json(
        {k: v for k, v in baseline.items() if k != "baseline_manifest_hash"}
    )
    print(f"  baseline manifest hash: {baseline['baseline_manifest_hash'][:16]}...")

    # Save
    output = BASELINE_DIR / "DISCOVERY_FABRIC_V1_BASELINE.json"
    with open(output, "w") as f:
        json.dump(baseline, f, indent=2, ensure_ascii=False)

    print(f"\n  Saved: {output}")
    print(f"\n  BASELINE FROZEN. This is a checkpoint, not a scientific result.")
    return baseline


if __name__ == "__main__":
    main()
