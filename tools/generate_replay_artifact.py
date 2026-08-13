#!/usr/bin/env python3
"""
Deterministic replay artifact generator V2 (CTO V17 #2, #8, #9).

Per CTO: "Replay must contain full input hashes + full canonical Claim/evidence/
relation output hash, not summary-only fixtures. Verify in two independent processes."
"""
import sys
import json
import hashlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from source_fabric.mddg.claims.claim import extract_causal_claims_v4, Claim
from source_fabric.mddg.claims.clock import ReplayClock
from source_fabric.mddg.claims.contract_loader import load_contract, get_contract_hash
from source_fabric.mddg.failure_taxonomy import FAILURE_MODES

REPLAY_CORPUS = [
    {
        "text": "Ceramic coating reduces implant wear by 30 percent in hip replacements.",
        "source_id": "replay:p1", "source_type": "paper",
        "source_field": "abstract", "source_hash": "replay_hash_1",
        "publication_date": "2023-06-15", "evidence_tier": "D",
    },
    {
        "text": "Surface passivation treatment prevents corrosion degradation in titanium implants.",
        "source_id": "replay:p2", "source_type": "paper",
        "source_field": "abstract", "source_hash": "replay_hash_2",
        "publication_date": "2022-03-10", "evidence_tier": "D",
    },
    {
        "text": "Antimicrobial coating reduces infection rate by 60 percent at body temperature in vivo.",
        "source_id": "replay:p3", "source_type": "paper",
        "source_field": "abstract", "source_hash": "replay_hash_3",
        "publication_date": "2023-11-12", "evidence_tier": "D",
    },
    {
        "text": "Coating X was associated with a 31% change in wear.",
        "source_id": "replay:p4", "source_type": "paper",
        "source_field": "abstract", "source_hash": "replay_hash_4",
        "publication_date": "2024-01-20", "evidence_tier": "D",
    },
    {
        "text": "Previous studies reported that coating X reduced wear.",
        "source_id": "replay:p5", "source_type": "paper",
        "source_field": "abstract", "source_hash": "replay_hash_5",
        "publication_date": "2023-09-05", "evidence_tier": "D",
    },
]


def generate_replay_artifact() -> dict:
    """Generate a fully deterministic replay artifact using ReplayClock."""
    clock = ReplayClock("2026-08-13T06:00:00Z")

    all_claims = []
    for item in REPLAY_CORPUS:
        claims = extract_causal_claims_v4(
            item["text"],
            source_id=item["source_id"],
            source_type=item["source_type"],
            source_field=item["source_field"],
            source_hash=item["source_hash"],
            publication_date=item["publication_date"],
            evidence_tier=item["evidence_tier"],
            clock=clock,
        )
        all_claims.extend(claims)

    # Full canonical output: every Claim with ALL fields (excluding nothing)
    claim_outputs = []
    for c in sorted(all_claims, key=lambda x: x.claim_id):
        d = c.canonical_dict()
        # Remove non-deterministic fields for hash computation
        # (creation_timestamp is now deterministic via ReplayClock, so keep it)
        claim_outputs.append(d)

    # Compute hashes
    corpus_hash = hashlib.sha256(
        json.dumps(REPLAY_CORPUS, sort_keys=True).encode()
    ).hexdigest()

    contract = load_contract()
    contract_hash = get_contract_hash()

    taxonomy_hash = hashlib.sha256(
        json.dumps(sorted(FAILURE_MODES), default=str).encode()
    ).hexdigest()

    # Full canonical output hash
    full_output = json.dumps(claim_outputs, sort_keys=True, default=str)
    full_output_hash = hashlib.sha256(full_output.encode()).hexdigest()

    # Individual hashes
    claim_ids = sorted(c.claim_id for c in all_claims)
    claim_ids_hash = hashlib.sha256("|".join(claim_ids).encode()).hexdigest()

    statuses = sorted(f"{c.claim_id}:{c.status}" for c in all_claims)
    status_hash = hashlib.sha256("|".join(statuses).encode()).hexdigest()

    # Evidence hashes
    all_evidence = []
    for c in sorted(all_claims, key=lambda x: x.claim_id):
        for ev in c.source_evidence:
            all_evidence.append({
                "source_id": ev.source_id,
                "supports_slot": ev.supports_slot,
                "char_start": ev.char_start,
                "char_end": ev.char_end,
                "quoted_span": ev.quoted_span,
                "source_hash": ev.source_hash,
            })
    evidence_hash = hashlib.sha256(
        json.dumps(all_evidence, sort_keys=True, default=str).encode()
    ).hexdigest()

    artifact = {
        "artifact_name": "REPLAY_ARTIFACT_V10",
        "artifact_version": 2,
        "generated_with_clock": "ReplayClock",
        "corpus_size": len(REPLAY_CORPUS),
        "claims_generated": len(all_claims),

        # Full input hashes
        "input_snapshot_hash": corpus_hash,
        "source_record_ids": sorted(item["source_id"] for item in REPLAY_CORPUS),
        "source_record_hashes": sorted(item["source_hash"] for item in REPLAY_CORPUS),
        "source_registry_hash": corpus_hash,  # same as corpus for replay
        "ontology_hash": taxonomy_hash,
        "failure_taxonomy_hash": taxonomy_hash,
        "claim_contract_hash": contract_hash,
        "extractor_version": 10,
        "validator_version": 10,
        "knowledge_cutoff": "2026-08-13",

        # Full output
        "claim_outputs": claim_outputs,
        "full_output_hash": full_output_hash,
        "claim_ids_hash": claim_ids_hash,
        "status_hash": status_hash,
        "evidence_hash": evidence_hash,

        # Root hash over everything
    }

    # Compute root hash over the entire artifact (excluding root_hash itself)
    artifact_for_hash = {k: v for k, v in artifact.items()}
    artifact_content = json.dumps(artifact_for_hash, sort_keys=True, default=str)
    artifact["root_hash"] = hashlib.sha256(artifact_content.encode()).hexdigest()

    return artifact


def main():
    artifact = generate_replay_artifact()
    output_path = REPO / "source_fabric" / "mddg" / "claims" / "REPLAY_ARTIFACT_V10.json"
    output_path.write_text(json.dumps(artifact, indent=2, sort_keys=True, default=str))

    print(f"Replay artifact written to {output_path}")
    print(f"Root hash: {artifact['root_hash'][:16]}...")
    print(f"Claims generated: {artifact['claims_generated']}")
    print(f"Full output hash: {artifact['full_output_hash'][:16]}...")
    print(f"Claim IDs hash: {artifact['claim_ids_hash'][:16]}...")
    print(f"Status hash: {artifact['status_hash'][:16]}...")
    print(f"Evidence hash: {artifact['evidence_hash'][:16]}...")
    print(f"Contract hash: {artifact['claim_contract_hash'][:16]}...")

    # Determinism check: generate again and compare
    artifact2 = generate_replay_artifact()
    if artifact["root_hash"] == artifact2["root_hash"]:
        print("\nDETERMINISM CHECK: PASS (identical root hash on re-generation)")
        print("  (verified in same process — independent process check requires separate run)")
    else:
        print("\nDETERMINISM CHECK: FAIL (root hash differs)")
        sys.exit(1)


if __name__ == "__main__":
    main()
