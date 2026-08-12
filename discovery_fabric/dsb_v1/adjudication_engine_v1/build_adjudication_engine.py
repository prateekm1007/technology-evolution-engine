"""
ADJUDICATION_ENGINE_V1 — Build Step
=====================================

This module builds the CTO adjudication infrastructure:
  1. Extends the freeze to explicitly cover DSB V1 scorer + V1.12 V3 scorer
  2. Builds 80 blinded CTO adjudication packets (all answer fields hidden)
  3. Seals the machine score vault (CTO must NOT read; revealed only after CTO submits)
  4. Builds the empty CTO adjudication template
  5. Writes CTO adjudication instructions

CRITICAL ENFORCEMENT:
  - The machine score vault is sealed NOW, before the CTO adjudicates.
  - The CTO must adjudicate WITHOUT seeing machine scores.
  - The comparison engine (run_comparison.py) verifies:
      (a) CTO ledger has 80 entries
      (b) CTO ledger timestamps are AFTER vault seal timestamp
      (c) Vault hash matches (vault not tampered with)
  - The AI_CTO_ADJUDICATION evidence tier is SEPARATE from HUMAN_VALIDATED.
    The CTO is NOT an independent expert (they directed the system).
    Per MC-1 (No self-validation), CTO adjudication CANNOT validate the
    system — it can only check whether the machine scorer agrees with
    informed CTO judgment.

NO new discovery architecture. NO scorer changes. NO benchmark changes.
"""
import json
import hashlib
import sys
import os
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[3]
os.chdir(REPO)
sys.path.insert(0, str(REPO))

DSB_DIR = REPO / "discovery_fabric" / "dsb_v1"
ENGINE_DIR = DSB_DIR / "adjudication_engine_v1"
LEDGER_DIR = ENGINE_DIR / "ledger"
VAULT_DIR = ENGINE_DIR / "vault"
ANALYSIS_DIR = ENGINE_DIR / "analysis"
DISAGREEMENT_DIR = ENGINE_DIR / "disagreements"

for d in [LEDGER_DIR, VAULT_DIR, ANALYSIS_DIR, DISAGREEMENT_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# =============================================================================
# Step 1: Freeze extension — explicitly cover DSB V1 scorer + V1.12 V3 scorer
# =============================================================================

def build_freeze_extension() -> dict:
    """Extend the freeze to explicitly cover the scorers used in comparison."""
    from discovery_fabric.dsb_v1.case_schema import load_case
    from discovery_fabric.dsb_v1.scorer import score_all

    # The DSB V1 scorer is already in FREEZE_MANIFEST.json.
    # This extension EXPLICITLY documents that the scorer is frozen for
    # the adjudication comparison, and seals the machine scores into a vault.
    freeze_ext = {
        "schema_version": "1.0.0",
        "manifest_type": "DSB_V1_ADJUDICATION_FREEZE_EXTENSION",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "frozen_artifacts": {
            "scorer.py (DSB V1 scorer)": hashlib.sha256((DSB_DIR / "scorer.py").read_bytes()).hexdigest(),
            "case_schema.py": hashlib.sha256((DSB_DIR / "case_schema.py").read_bytes()).hexdigest(),
            "10 real cases": hashlib.sha256(
                b"".join(p.read_bytes() for p in sorted((DSB_DIR / "cases/real").glob("DSB-R-*.json")))
            ).hexdigest(),
            "10 fabricated cases": hashlib.sha256(
                b"".join(p.read_bytes() for p in sorted((DSB_DIR / "cases/fabricated").glob("DSB-F-*.json")))
            ).hexdigest(),
            "80 receipts": hashlib.sha256(
                b"".join(p.read_bytes() for p in sorted((DSB_DIR / "receipts").glob("RECEIPT-*.json")))
            ).hexdigest(),
        },
        "policy": [
            "The DSB V1 scorer is FROZEN. No tuning during adjudication.",
            "The 80 cases and prompts are FROZEN. No modification.",
            "The 80 receipts are FROZEN. No modification.",
            "Machine scores are sealed in a vault. CTO must NOT read the vault before submitting adjudications.",
            "AI_CTO_ADJUDICATION is a separate evidence tier. NEVER call it HUMAN_VALIDATED.",
            "No architecture change is permitted based on CTO adjudication alone.",
        ],
    }
    canonical = json.dumps(freeze_ext, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    freeze_ext["manifest_hash"] = hashlib.sha256(canonical.encode()).hexdigest()
    return freeze_ext


# =============================================================================
# Step 2: Build 80 blinded CTO adjudication packets
# =============================================================================

def build_cto_packets() -> list:
    """Build 80 blinded packets for CTO adjudication.

    Each packet contains ONLY what the CTO should see:
      - packet_id (opaque, no case_id or arm revealed)
      - exposed_facts (what the generator saw)
      - proposed_relationship (what the generator produced)
      - proposed_mechanism
      - proposed_constraint_released

    The packet does NOT contain:
      - case_id, case_type (real vs fabricated), arm
      - breakthrough_relationship, withheld_facts, answer_mechanism
      - machine scorer verdict
      - any answer information
    """
    from discovery_fabric.dsb_v1.case_schema import load_case

    receipts_dir = DSB_DIR / "receipts"
    real_dir = DSB_DIR / "cases/real"
    fab_dir = DSB_DIR / "cases/fabricated"

    cases = {}
    for d in [real_dir, fab_dir]:
        for cp in sorted(d.glob("DSB-*.json")):
            case = load_case(cp)
            cases[case["case_id"]] = case

    packets = []
    for rp in sorted(receipts_dir.glob("RECEIPT-*.json")):
        with open(rp) as f:
            receipt = json.load(f)
        case = cases.get(receipt["case_id"])
        if not case:
            continue

        # Opaque packet ID (hash of receipt_id + receipt_hash, truncated)
        seed = f"{receipt['receipt_id']}|{receipt['receipt_hash']}"
        packet_id = "CTO-" + hashlib.sha256(seed.encode()).hexdigest()[:12]

        packet = {
            "schema_version": "1.0.0",
            "packet_id": packet_id,
            # What the CTO sees:
            "exposed_facts": sorted(case["exposed_facts"]),
            "proposed_relationship": receipt.get("proposed_relationship", ""),
            "proposed_mechanism": receipt.get("mechanism", ""),
            "proposed_constraint_released": receipt.get("constraint_released", ""),
            # Internal bookkeeping (NOT shown to CTO; used by comparison engine)
            "_internal": {
                "receipt_id": receipt["receipt_id"],
                "case_id": case["case_id"],
                "case_type": case["case_type"],
                "arm": receipt["arm"],
                "receipt_hash": receipt["receipt_hash"],
            },
        }
        # Seal
        canonical = json.dumps(packet, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        packet["packet_hash"] = hashlib.sha256(canonical.encode()).hexdigest()
        packets.append(packet)

    return packets


# =============================================================================
# Step 3: Seal the machine score vault
# =============================================================================

def seal_machine_score_vault() -> dict:
    """Seal all 80 machine scores into a vault file.

    The vault is sealed NOW, before the CTO adjudicates.
    The CTO must NOT read this file.
    The comparison engine verifies the vault hash before running.
    """
    from discovery_fabric.dsb_v1.scorer import score_all

    result = score_all()
    scores = result["scores"]

    vault = {
        "schema_version": "1.0.0",
        "vault_type": "DSB_V1_MACHINE_SCORE_VAULT",
        "sealed_at": datetime.now(timezone.utc).isoformat(),
        "n_scores": len(scores),
        "policy": "CTO must NOT read this file before submitting adjudications. Comparison engine verifies hash before running.",
        "scores": [
            {
                "receipt_id": s["receipt_id"],
                "case_id": s["case_id"],
                "case_type": s["case_type"],
                "arm": s["arm"],
                "mechanism_reconstruction_verdict": s["mechanism_reconstruction"]["verdict"],
                "mechanism_reconstruction_score": s["mechanism_reconstruction"]["score"],
                "discovery_structure_recovery_verdict": s["discovery_structure_recovery"]["verdict"],
                "discovery_structure_recovery_score": s["discovery_structure_recovery"]["score"],
                "score_hash": s["score_hash"],
            }
            for s in scores
        ],
    }
    canonical = json.dumps(vault, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    vault["vault_hash"] = hashlib.sha256(canonical.encode()).hexdigest()
    return vault


# =============================================================================
# Step 4: Build CTO adjudication template + schema
# =============================================================================

CTO_ADJUDICATION_SCHEMA = {
    "schema_version": "1.0.0",
    "evidence_tier": "AI_CTO_ADJUDICATION",
    "tier_note": "This is NOT HUMAN_VALIDATED. The CTO directed the system and is not an independent expert. Per MC-1 (No self-validation), this tier cannot validate the system — it can only check whether the machine scorer agrees with informed CTO judgment.",
    "criteria": {
        "Q1_MECHANISTIC_VALIDITY": {
            "question": "Is the proposed mechanism scientifically valid and plausibly tied to the exposed facts?",
            "options": ["YES", "PARTIAL", "NO"],
        },
        "Q2_DISCOVERY_STRUCTURE_VALIDITY": {
            "question": "Does the proposed_relationship express a relationship NOT explicit in the exposed_facts that combines them in a novel way?",
            "options": ["YES", "PARTIAL", "NO"],
        },
        "Q3_NOVELTY": {
            "question": "Does the proposal introduce genuinely new entities, mechanisms, or relational structure beyond the exposed_facts?",
            "options": ["YES", "PARTIAL", "NO"],
        },
        "Q4_FALSIFIABILITY": {
            "question": "Is the proposed_relationship specific enough to be falsifiable (names specific entities, outcomes, or testable predictions)?",
            "options": ["YES", "NO"],
        },
        "Q5_EXPERIMENTAL_COHERENCE": {
            "question": "Could an experiment be designed to test this proposal, given the exposed_facts?",
            "options": ["YES", "PARTIAL", "NO"],
        },
        "Q6_REAL_VS_FABRICATED": {
            "question": "Based on scientific plausibility alone (not pattern-matching to known discoveries), does this proposal describe a relationship that actually works in reality?",
            "options": ["REAL", "FABRICATED", "UNCERTAIN"],
            "note": "This is the CTO's guess about whether the case is real or fabricated. It tests whether the CTO can distinguish real discoveries from plausible counterfactuals.",
        },
        "Q7_OVERALL_DISCOVERY": {
            "question": "Overall, does this proposal constitute a genuine discovery-structure recovery (not just a restatement)?",
            "options": ["YES", "NO"],
        },
    },
}


def build_cto_template(packets: list) -> dict:
    """Build the empty CTO adjudication template."""
    template = {
        "schema_version": "1.0.0",
        "adjudicator_id": "AI_CTO",
        "evidence_tier": "AI_CTO_ADJUDICATION",
        "independence_statement": (
            "I am the CTO who directed this system. I am NOT an independent expert. "
            "My adjudication is in the AI_CTO_ADJUDICATION tier, NOT HUMAN_VALIDATED. "
            "Per MC-1 (No self-validation), my adjudication cannot validate the system — "
            "it can only check whether the machine scorer agrees with my informed judgment. "
            "I adjudicated each case based solely on the scientific content visible in the packet. "
            "I did NOT read the machine score vault before submitting. "
            "I did NOT look up which cases are real vs fabricated."
        ),
        "submitted_at": "[FILL IN ISO-8601]",
        "time_spent_minutes": 0,
        "adjudications": [
            {
                "packet_id": p["packet_id"],
                "Q1_MECHANISTIC_VALIDITY": "[YES|PARTIAL|NO]",
                "Q2_DISCOVERY_STRUCTURE_VALIDITY": "[YES|PARTIAL|NO]",
                "Q3_NOVELTY": "[YES|PARTIAL|NO]",
                "Q4_FALSIFIABILITY": "[YES|NO]",
                "Q5_EXPERIMENTAL_COHERENCE": "[YES|PARTIAL|NO]",
                "Q6_REAL_VS_FABRICATED": "[REAL|FABRICATED|UNCERTAIN]",
                "Q7_OVERALL_DISCOVERY": "[YES|NO]",
                "comments": "[optional, max 200 chars]",
            }
            for p in packets
        ],
    }
    return template


# =============================================================================
# Step 5: Main build
# =============================================================================

def main():
    print("=" * 72)
    print("ADJUDICATION_ENGINE_V1 — BUILD")
    print("=" * 72)
    print()

    # Step 1: Freeze extension
    print("[1/5] Building freeze extension...")
    freeze_ext = build_freeze_extension()
    with open(ENGINE_DIR / "FREEZE_EXTENSION.json", "w") as f:
        json.dump(freeze_ext, f, indent=2, ensure_ascii=False)
    print(f"  Freeze extension saved. Hash: {freeze_ext['manifest_hash'][:32]}...")

    # Step 2: Build CTO packets
    print("\n[2/5] Building 80 blinded CTO packets...")
    packets = build_cto_packets()
    # Save full packets (with internal bookkeeping) for comparison engine
    with open(ENGINE_DIR / "cto_packets_FULL.json", "w") as f:
        json.dump({"n_packets": len(packets), "packets": packets}, f, indent=2, ensure_ascii=False)
    # Save BLIND packets (no internal) for CTO
    blind_packets = [{k: v for k, v in p.items() if k != "_internal"} for p in packets]
    with open(ENGINE_DIR / "cto_packets_BLIND.json", "w") as f:
        json.dump(blind_packets, f, indent=2, ensure_ascii=False)
    print(f"  {len(packets)} packets built. BLIND version for CTO. FULL version for comparison engine.")

    # Step 3: Seal machine score vault
    print("\n[3/5] Sealing machine score vault...")
    vault = seal_machine_score_vault()
    vault_path = VAULT_DIR / "machine_score_vault.json"
    with open(vault_path, "w") as f:
        json.dump(vault, f, indent=2, ensure_ascii=False)
    print(f"  Vault sealed at {vault['sealed_at']}")
    print(f"  Vault hash: {vault['vault_hash'][:32]}...")
    print(f"  CTO must NOT read: {vault_path}")

    # Step 4: Build CTO template
    print("\n[4/5] Building CTO adjudication template...")
    template = build_cto_template(packets)
    template_path = ENGINE_DIR / "cto_adjudication_template.json"
    with open(template_path, "w") as f:
        json.dump(template, f, indent=2, ensure_ascii=False)
    print(f"  Template saved: {template_path}")
    print(f"  {len(template['adjudications'])} adjudication slots")

    # Step 5: Write instructions
    print("\n[5/5] Writing CTO instructions...")
    write_cto_instructions(vault["sealed_at"], vault["vault_hash"])
    print(f"  Instructions saved: {ENGINE_DIR / 'CTO_ADJUDICATION_INSTRUCTIONS.md'}")

    print("\n" + "=" * 72)
    print("BUILD COMPLETE")
    print("=" * 72)
    print()
    print("NEXT STEPS:")
    print("1. CTO reads CTO_ADJUDICATION_INSTRUCTIONS.md")
    print("2. CTO adjudicates all 80 packets using cto_adjudication_template.json")
    print("3. CTO saves filled template as ledger/cto_adjudication.json")
    print("4. Run: python3 run_comparison.py")
    print("5. Comparison engine verifies temporal ordering, computes metrics,")
    print("   generates disagreement forensic files, produces final report")
    print()
    print("CRITICAL: CTO must NOT read vault/machine_score_vault.json before submitting.")


def write_cto_instructions(vault_sealed_at: str, vault_hash: str):
    """Write the CTO adjudication instructions."""
    instructions = f"""# CTO ADJUDICATION INSTRUCTIONS — DSB V1

**Engine:** ADJUDICATION_ENGINE_V1
**Date:** {datetime.now(timezone.utc).isoformat()}
**Vault sealed at:** {vault_sealed_at}
**Vault hash:** `{vault_hash[:32]}...`

---

## 1. Your Role

You are the CTO adjudicating the DSB V1 benchmark. You directed this system, so you are **NOT an independent expert**. Your adjudication is in the **AI_CTO_ADJUDICATION** evidence tier — separate from HUMAN_VALIDATED. Per MEASUREMENT_CONSTITUTION MC-1 (No self-validation), your adjudication **cannot validate the system**. It can only check whether the machine scorer agrees with your informed judgment.

**Your adjudication decides:**
- Whether the current benchmark/scorer survives (is the machine scorer consistent with your judgment?)
- Whether systematic false positives exist (triggering the scorer-calibration protocol)

**Your adjudication does NOT decide:**
- Whether the system is "human-validated" (it isn't — you're not independent)
- Whether to change the architecture (no architecture change permitted based on your adjudication alone)

---

## 2. What You Will See

For each of the 80 packets in `cto_packets_BLIND.json`, you will see:
- `packet_id` (opaque — no case_id or arm revealed)
- `exposed_facts` (what the generator saw)
- `proposed_relationship` (what the generator produced)
- `proposed_mechanism`
- `proposed_constraint_released`

You will NOT see:
- Whether the case is REAL or FABRICATED
- Which arm produced the proposal
- The machine scorer's verdict
- The breakthrough_relationship or withheld_facts

---

## 3. CRITICAL: Do NOT Read the Vault

The machine scores are sealed in `vault/machine_score_vault.json`. **You must NOT read this file before submitting your adjudications.** The comparison engine verifies that your adjudication timestamps are AFTER the vault seal time. If you read the vault, your adjudication is contaminated.

---

## 4. Seven Criteria Per Packet

For each packet, answer 7 questions:

### Q1. MECHANISTIC_VALIDITY
Is the proposed mechanism scientifically valid and plausibly tied to the exposed facts?
- YES / PARTIAL / NO

### Q2. DISCOVERY_STRUCTURE_VALIDITY
Does the proposed_relationship express a relationship NOT explicit in the exposed_facts that combines them in a novel way?
- YES / PARTIAL / NO

### Q3. NOVELTY
Does the proposal introduce genuinely new entities, mechanisms, or relational structure beyond the exposed_facts?
- YES / PARTIAL / NO

### Q4. FALSIFIABILITY
Is the proposed_relationship specific enough to be falsifiable?
- YES / NO

### Q5. EXPERIMENTAL_COHERENCE
Could an experiment be designed to test this proposal, given the exposed_facts?
- YES / PARTIAL / NO

### Q6. REAL_VS_FABRICATED
Based on scientific plausibility alone (not pattern-matching to known discoveries), does this proposal describe a relationship that actually works in reality?
- REAL / FABRICATED / UNCERTAIN
- This tests whether you can distinguish real discoveries from plausible counterfactuals.

### Q7. OVERALL_DISCOVERY
Overall, does this proposal constitute a genuine discovery-structure recovery (not just a restatement)?
- YES / NO

---

## 5. Submission Format

1. Copy `cto_adjudication_template.json` to `ledger/cto_adjudication.json`.
2. Fill in all 80 adjudication slots.
3. Fill in `submitted_at` (ISO-8601 timestamp).
4. Fill in `time_spent_minutes`.
5. Keep the `independence_statement` as-is (it documents your non-independence).
6. Save.

---

## 6. After Submission

Run:
```bash
python3 discovery_fabric/dsb_v1/adjudication_engine_v1/run_comparison.py
```

The comparison engine will:
1. Verify your ledger has 80 entries
2. Verify your timestamps are AFTER the vault seal time
3. Verify the vault hash (vault not tampered with)
4. Compute: confusion matrix, precision/recall, false-positive rate, agreement, disagreements
5. Generate per-disagreement forensic case files
6. Produce `DSB_V1_CTO_ADJUDICATION_REPORT.md`

---

## 7. What the Report Will Say

The report will state one of:
- **SCORER SURVIVES**: Machine scorer agrees with CTO on enough cases. Benchmark continues.
- **SCORER DOES NOT SURVIVE**: Systematic disagreements. Triggers scorer-calibration protocol (separate 40-case set, NOT these 80).

Either way: **NOT human-validated. No architecture change.**

---

**End of CTO Adjudication Instructions.**
"""
    with open(ENGINE_DIR / "CTO_ADJUDICATION_INSTRUCTIONS.md", "w") as f:
        f.write(instructions)


if __name__ == "__main__":
    main()
