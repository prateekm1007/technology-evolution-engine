"""
DSB V1 — Human Adjudication Packet Builder
============================================

Builds a BLIND packet for human adjudicators. The packet contains, for each
(case, arm) pair:
  - case_id (internal, for bookkeeping — NOT shown to adjudicator)
  - arm (NOT shown to adjudicator — to prevent bias)
  - exposed_facts (what the generator saw)
  - proposed_relationship (what the generator produced)
  - proposed_mechanism
  - proposed_constraint_released

The adjudicator answers 3 questions per packet:
  Q1. MECHANISM_MATCH: Does the proposed mechanism plausibly explain a real
       scientific mechanism that could underlie a discovery from these facts?
       (YES / NO / PARTIAL)
  Q2. DISCOVERY_STRUCTURE_MATCH: Does the proposed_relationship express a
       relationship NOT explicit in the exposed_facts that combines them in
       a novel way?
       (YES / NO / PARTIAL)
  Q3. SPECIFICITY: Is the proposed_relationship specific enough to be
       falsifiable?
       (YES / NO)

The packet does NOT include:
  - case_type (real vs fabricated) — adjudicator is blind to this
  - breakthrough_relationship
  - answer_mechanism
  - withheld_facts
  - forbidden_terms
  - historical_source
  - arm

The human adjudication step is NOT automated. The packet is produced as a
JSON file that can be sent to human adjudicators. Results must be collected
separately and scored.

STATUS: Packet built. Human adjudication PENDING (not yet performed).
"""
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

import sys
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from discovery_fabric.dsb_v1.case_schema import load_case


ADJUDICATION_DIR = REPO / "discovery_fabric/dsb_v1/adjudication"
ADJUDICATION_DIR.mkdir(parents=True, exist_ok=True)


def build_adjudication_packet(receipt: dict, case: dict) -> dict:
    """Build a blind adjudication packet for one (case, arm) pair.

    The packet is BLIND: it does not reveal case_type, arm, breakthrough,
    withheld facts, or any answer information.
    """
    # Generate a random-looking packet ID that does NOT encode case_id or arm
    # (to prevent the adjudicator from inferring them)
    import hashlib as _h
    seed = f"{receipt['receipt_id']}|{receipt['receipt_hash']}"
    packet_id = "ADJ-" + _h.sha256(seed.encode()).hexdigest()[:12]

    packet = {
        "schema_version": "1.0.0",
        "packet_id": packet_id,
        # Internal bookkeeping (NOT shown to adjudicator)
        "_internal": {
            "receipt_id": receipt["receipt_id"],
            "case_id": case["case_id"],
            "case_type": case["case_type"],
            "arm": receipt["arm"],
            "receipt_hash": receipt["receipt_hash"],
            "answer_hash": case["answer_hash"],
        },
        # What the adjudicator sees:
        "exposed_facts": sorted(case["exposed_facts"]),  # same as generator saw
        "proposed_relationship": receipt.get("proposed_relationship", ""),
        "proposed_mechanism": receipt.get("mechanism", ""),
        "proposed_constraint_released": receipt.get("constraint_released", ""),
        # What the adjudicator must answer:
        "questions": {
            "Q1_MECHANISM_MATCH": {
                "question": "Does the proposed mechanism plausibly explain a real scientific mechanism that could underlie a discovery from these facts?",
                "options": ["YES", "NO", "PARTIAL"],
            },
            "Q2_DISCOVERY_STRUCTURE_MATCH": {
                "question": "Does the proposed_relationship express a relationship NOT explicit in the exposed_facts that combines them in a novel way?",
                "options": ["YES", "NO", "PARTIAL"],
            },
            "Q3_SPECIFICITY": {
                "question": "Is the proposed_relationship specific enough to be falsifiable?",
                "options": ["YES", "NO"],
            },
        },
        "built_at": datetime.now(timezone.utc).isoformat(),
    }

    # Seal
    canonical = json.dumps(packet, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    packet["packet_hash"] = hashlib.sha256(canonical.encode()).hexdigest()
    return packet


def build_all_packets() -> dict:
    """Build adjudication packets for all 80 receipts."""
    REPO = Path(__file__).resolve().parents[2]
    receipts_dir = REPO / "discovery_fabric/dsb_v1/receipts"
    real_dir = REPO / "discovery_fabric/dsb_v1/cases/real"
    fab_dir = REPO / "discovery_fabric/dsb_v1/cases/fabricated"

    # Load cases
    cases = {}
    for d in [real_dir, fab_dir]:
        for cp in sorted(d.glob("DSB-*.json")):
            case = load_case(cp)
            cases[case["case_id"]] = case

    # Build packets
    packets = []
    for rp in sorted(receipts_dir.glob("RECEIPT-*.json")):
        receipt = json.load(open(rp))
        case_id = receipt.get("case_id")
        case = cases.get(case_id)
        if not case:
            continue
        packet = build_adjudication_packet(receipt, case)
        packets.append(packet)

    return {"n_packets": len(packets), "packets": packets}


def main():
    print("=" * 72)
    print("DSB V1 — HUMAN ADJUDICATION PACKET BUILDER")
    print("=" * 72)
    print()

    result = build_all_packets()
    packets = result["packets"]
    print(f"Built {len(packets)} adjudication packets\n")

    # Save packets
    out_path = ADJUDICATION_DIR / "adjudication_packets.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # Also save a "blind" version (with _internal stripped) for sending to adjudicators
    blind_packets = []
    for p in packets:
        blind = {k: v for k, v in p.items() if k != "_internal"}
        blind_packets.append(blind)
    blind_path = ADJUDICATION_DIR / "adjudication_packets_BLIND.json"
    with open(blind_path, "w") as f:
        json.dump(blind_packets, f, indent=2, ensure_ascii=False)

    print(f"Full packets (with internal bookkeeping): {out_path}")
    print(f"Blind packets (for adjudicators): {blind_path}")
    print()
    print("STATUS: Human adjudication NOT yet performed.")
    print("The blind packets are ready to be sent to human adjudicators.")
    print("Adjudicators should answer Q1, Q2, Q3 for each packet.")
    print("Results must be collected in a separate file: adjudication_results.json")
    print()
    print("NOTE: Human adjudication is OUT OF SCOPE for this automated run.")
    print("The exit gate documents that this step is PENDING.")

    # Show one sample blind packet
    print(f"\nSample blind packet:")
    print(json.dumps(blind_packets[0], indent=2)[:1500])


if __name__ == "__main__":
    main()
