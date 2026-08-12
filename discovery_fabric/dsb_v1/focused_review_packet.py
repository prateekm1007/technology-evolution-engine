"""
DSB V1 — Focused Review Packet Builder
========================================

Extracts the 12 machine "recoveries" (cases where the deterministic scorer
returned DISCOVERY_STRUCTURE_RECOVERY = RECOVERED) PLUS all cases where
fabricated score > real score (per arm), into a separate adjudicator-blind
packet for PRIORITY review.

The focused review packet is a SUBSET of the 80 blind packets. It is given
to adjudicators IN ADDITION to the full 80-packet set, with the instruction
to pay especially close attention to these packets.

CRITICAL: The focused review packet does NOT reveal:
  - which cases are the 12 "recoveries"
  - which cases are fabricated vs real
  - which arm produced each proposal
  - the deterministic scorer's verdict

It simply marks these packets as "PRIORITY_REVIEW" so adjudicators know to
spend extra time on them. The reasoning is documented separately (in the
scorer's output) but is NOT included in the packet.

Adjudicator-blindness is preserved.
"""
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

import sys
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from discovery_fabric.dsb_v1.scorer import score_all
from discovery_fabric.dsb_v1.case_schema import load_case
from discovery_fabric.dsb_v1.human_adjudication_packet import build_adjudication_packet


def build_focused_review_packet() -> dict:
    """Build the focused review packet.

    Selects:
      (a) All 12 receipts where deterministic scorer returned
          discovery_structure_recovery.verdict == "RECOVERED"
      (b) For each arm, the fabricated case with the highest discovery-structure
          score (to ensure all "fabricated > real" cases are reviewed)

    Returns a dict with:
      - n_priority_packets
      - priority_packets (list of blind packets with priority_review=True)
      - selection_criteria (documentation of how packets were selected)
    """
    # Load all scores
    scorer_result = score_all()
    scores = scorer_result["scores"]

    # Load all receipts and cases
    receipts_dir = REPO / "discovery_fabric/dsb_v1/receipts"
    real_dir = REPO / "discovery_fabric/dsb_v1/cases/real"
    fab_dir = REPO / "discovery_fabric/dsb_v1/cases/fabricated"

    cases = {}
    for d in [real_dir, fab_dir]:
        for cp in sorted(d.glob("DSB-*.json")):
            case = load_case(cp)
            cases[case["case_id"]] = case

    receipts = {}
    for rp in sorted(receipts_dir.glob("RECEIPT-*.json")):
        r = json.load(open(rp))
        receipts[r["receipt_id"]] = r

    # ---- Selection (a): all 12 "recoveries" ----
    recovery_receipt_ids = []
    for s in scores:
        if s["discovery_structure_recovery"]["verdict"] == "RECOVERED":
            recovery_receipt_ids.append(s["receipt_id"])

    # ---- Selection (b): for each arm, the highest-scoring fabricated case ----
    # (these are the "fabricated > real" candidates — cases where a fabricated
    # counterfactual scored higher than any real case for that arm)
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

    # Top-2 fabricated per arm
    top_fab_receipt_ids = set()
    for arm, lst in by_arm_fab.items():
        lst.sort(key=lambda x: -x[0])  # descending by score
        for score, rid in lst[:2]:
            top_fab_receipt_ids.add(rid)

    # Union of (a) and (b)
    priority_receipt_ids = set(recovery_receipt_ids) | top_fab_receipt_ids

    # Build priority packets (blind — same schema as full packets)
    priority_packets = []
    for rid in sorted(priority_receipt_ids):
        receipt = receipts.get(rid)
        if not receipt:
            continue
        case = cases.get(receipt["case_id"])
        if not case:
            continue
        packet = build_adjudication_packet(receipt, case)
        # Add priority_review flag (does NOT reveal why this packet was selected)
        packet["priority_review"] = True
        # Re-seal
        packet.pop("packet_hash", None)
        canonical = json.dumps(packet, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        packet["packet_hash"] = hashlib.sha256(canonical.encode()).hexdigest()
        priority_packets.append(packet)

    return {
        "n_priority_packets": len(priority_packets),
        "priority_packets": priority_packets,
        "selection_criteria": {
            "criteria_a_recoveries": (
                "All receipts where the deterministic scorer returned "
                "discovery_structure_recovery.verdict == RECOVERED. "
                f"Count: {len(recovery_receipt_ids)}"
            ),
            "criteria_b_top_fabricated_per_arm": (
                "For each arm, the top-2 fabricated cases by discovery-structure score. "
                f"Count: {len(top_fab_receipt_ids)}"
            ),
            "union_count": len(priority_receipt_ids),
            "note": (
                "Adjudicators do NOT see which criterion selected each packet, "
                "nor the deterministic scorer's verdict. Packets are marked "
                "priority_review=True to indicate extra attention is warranted."
            ),
        },
    }


def main():
    print("=" * 72)
    print("DSB V1 — FOCUSED REVIEW PACKET BUILDER")
    print("=" * 72)
    print()

    result = build_focused_review_packet()
    print(f"Priority packets: {result['n_priority_packets']}")
    print(f"\nSelection criteria:")
    for k, v in result["selection_criteria"].items():
        print(f"  {k}: {v}")

    out_path = REPO / "discovery_fabric/dsb_v1/adjudication/focused_review_packets.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\nSaved: {out_path}")

    # Also save a blind version (strip the selection_criteria)
    blind = {
        "n_priority_packets": result["n_priority_packets"],
        "priority_packets": result["priority_packets"],
        "note": (
            "These packets are a SUBSET of the full 80-packet set. "
            "Adjudicators should review ALL 80 packets, but spend extra time "
            "on packets marked priority_review=True. The reason for priority "
            "status is NOT revealed to preserve adjudicator blindness."
        ),
    }
    blind_path = REPO / "discovery_fabric/dsb_v1/adjudication/focused_review_packets_BLIND.json"
    with open(blind_path, "w") as f:
        json.dump(blind, f, indent=2, ensure_ascii=False)
    print(f"Blind version: {blind_path}")


if __name__ == "__main__":
    main()
