#!/usr/bin/env python3
"""
Deterministic replay artifact generator (CTO V16 #7).

Proves: same snapshot + same schema + same extractor + same validator + same
knowledge cutoff = same Claims, same evidence spans, same source hashes,
same Claim IDs, same statuses, same relation IDs.

Run twice in independent processes. Output must be byte-for-byte identical
after canonicalization.
"""
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from source_fabric.mddg.claims.claim import (
    extract_causal_claims_v4, Claim,
)

# Fixed test corpus for replay determinism
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
    """Generate a deterministic replay artifact from the fixed corpus."""
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
        )
        all_claims.extend(claims)

    # Canonicalize: sort by claim_id for determinism
    # Exclude non-deterministic fields (creation_timestamp) from the summary
    claim_summaries = []
    for c in sorted(all_claims, key=lambda x: x.claim_id):
        claim_summaries.append({
            "claim_id": c.claim_id,
            "claim_type": c.claim_type,
            "status": c.status,
            "cause": c.cause,
            "failure_mode": c.failure_mode,
            "causal_relation": c.causal_relation,
            "mechanism": c.mechanism,
            "mechanism_status": c.mechanism_status,
            "intervention": c.intervention,
            "measured_effect": c.measured_effect,
            "boundary_conditions": c.boundary_conditions,
            "failure_mode_source": c.failure_mode_source,
            "effect_direction": c.effect_direction,
            "effect_value": c.effect_value,
            "schema_version": c.claim_schema_version,
            "validator_version": c.validator_version,
            "extraction_version": c.extraction_version,
            "evidence_count": len(c.source_evidence),
            "evidence_hashes": sorted([e.source_hash for e in c.source_evidence]),
            "evidence_spans": sorted([(e.char_start, e.char_end) for e in c.source_evidence
                               if e.has_span() or e.supports_slot == "mechanism"]),
            # Deterministic content hash (excludes creation_timestamp)
            "content_hash": hashlib.sha256(
                json.dumps({
                    "claim_id": c.claim_id,
                    "claim_type": c.claim_type,
                    "status": c.status,
                    "cause": c.cause,
                    "failure_mode": c.failure_mode,
                    "causal_relation": c.causal_relation,
                    "mechanism": c.mechanism,
                    "intervention": c.intervention,
                    "measured_effect": c.measured_effect,
                    "boundary_conditions": c.boundary_conditions,
                }, sort_keys=True).encode()
            ).hexdigest()[:16],
        })

    artifact = {
        "artifact_name": "REPLAY_ARTIFACT_V10",
        "generated_at": "2026-08-13T06:00:00Z",  # FIXED timestamp for determinism
        "corpus_size": len(REPLAY_CORPUS),
        "claims_generated": len(all_claims),
        "claim_summaries": claim_summaries,
        # Deterministic hashes
        "corpus_hash": hashlib.sha256(
            json.dumps(REPLAY_CORPUS, sort_keys=True).encode()
        ).hexdigest(),
        "claim_ids_hash": hashlib.sha256(
            "|".join(sorted(c.claim_id for c in all_claims)).encode()
        ).hexdigest(),
        "claim_hashes_hash": hashlib.sha256(
            "|".join(sorted(cs["content_hash"] for cs in claim_summaries)).encode()
        ).hexdigest(),
        "status_hash": hashlib.sha256(
            "|".join(sorted(f"{c.claim_id}:{c.status}" for c in all_claims)).encode()
        ).hexdigest(),
    }

    # Root hash over the entire artifact (excluding the root hash itself)
    artifact_content = json.dumps(
        {k: v for k, v in artifact.items()},
        sort_keys=True, default=str
    )
    artifact["root_hash"] = hashlib.sha256(artifact_content.encode()).hexdigest()

    return artifact


def main():
    artifact = generate_replay_artifact()
    output_path = REPO / "source_fabric" / "mddg" / "claims" / "REPLAY_ARTIFACT_V10.json"
    output_path.write_text(json.dumps(artifact, indent=2, sort_keys=True, default=str))
    print(f"Replay artifact written to {output_path}")
    print(f"Root hash: {artifact['root_hash'][:16]}...")
    print(f"Claims generated: {artifact['claims_generated']}")
    print(f"Claim IDs hash: {artifact['claim_ids_hash'][:16]}...")
    print(f"Status hash: {artifact['status_hash'][:16]}...")

    # Verify determinism: generate again and compare
    artifact2 = generate_replay_artifact()
    if artifact["root_hash"] == artifact2["root_hash"]:
        print("DETERMINISM CHECK: PASS (identical root hash on re-generation)")
    else:
        print("DETERMINISM CHECK: FAIL (root hash differs)")
        sys.exit(1)


if __name__ == "__main__":
    main()
