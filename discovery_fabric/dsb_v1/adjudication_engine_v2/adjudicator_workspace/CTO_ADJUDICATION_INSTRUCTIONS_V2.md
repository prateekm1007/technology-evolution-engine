> ⚠️ **WARNING: OS isolation is NOT enforced in this environment.** Adjudication CANNOT start here. See ADJUDICATION_SECURITY_CORRECTION_REPORT.md.

# CTO ADJUDICATION INSTRUCTIONS V2 — DSB V1

**Engine:** ADJUDICATION_ENGINE_V2 (forensic correction of V1)
**Date:** 2026-08-12T18:54:40.689404+00:00
**Vault sealed at:** 2026-08-12T18:54:40.575564+00:00
**Evidence tier:** AI_CTO_ADJUDICATION (NOT HUMAN_VALIDATED)

---

## 1. What Changed in V2 (vs V1)

V1 had three forensic defects. V2 fixes all three:

### Fix 1: Two-class adjudication
- **Observable judgment (Q1-Q5 + Q6_PLAUSIBILITY):** You evaluate from the BLINDED packet only. You judge plausibility and structure — NOT ground truth.
- **Ground-truth evaluation:** Done by the comparison engine AFTER unblinding, against frozen labels. You do NOT answer these.
- **Q6 change:** V1 asked you to determine REAL vs FABRICATED — impossible when the label is hidden. V2 asks Q6_PLAUSIBILITY: "Is this proposal scientifically plausible?" — observable from the packet alone.

### Fix 2: Cryptographic isolation
- The machine score vault is ENCRYPTED. The decryption key is in `evaluator_boundary/` — OUTSIDE your workspace.
- You cannot read the vault. The key is revealed to the evaluator only AFTER you seal your ledger.

### Fix 3: FULL packets isolated
- `cto_packets_FULL.json` (with case_id, case_type, arm, breakthrough, withheld_facts) is in `evaluator_boundary/`, NOT in your workspace.
- Your workspace contains ONLY: BLIND packets, template, instructions, and the encrypted vault.

---

## 2. Your Workspace

Your workspace (`adjudicator_workspace/`) contains:
- `cto_packets_BLIND.json` — 80 blinded packets
- `cto_adjudication_template.json` — empty template
- `machine_score_vault_ENCRYPTED.bin` — encrypted, unreadable without key

Your workspace does NOT contain:
- Machine scores (encrypted, no key)
- case_type (real vs fabricated)
- arm
- breakthrough_relationship
- withheld_facts
- cto_packets_FULL.json

---

## 3. Six Observable Questions Per Packet

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

### Q6. PLAUSIBILITY (NEW — replaces V1 Q6_REAL_VS_FABRICATED)
Is this proposal scientifically plausible — could it work in reality, regardless of whether it has been historically demonstrated?
- PLAUSIBLE / IMPLAUSIBLE / UNCERTAIN
- This is your judgment of plausibility, NOT a guess about whether the case is real or fabricated. The comparison engine will check whether PLAUSIBILITY correlates with the actual label after unblinding.

---

## 4. Submission + Sealing

1. Copy `cto_adjudication_template.json` to `cto_adjudication.json` (in your workspace).
2. Fill in all 80 adjudication slots.
3. Fill in `submitted_at` and `time_spent_minutes`.
4. **Seal the ledger:** compute SHA-256 of the ledger (excluding ledger_hash) and add it as `ledger_hash`.
5. Save.

The comparison engine verifies your ledger hash BEFORE decrypting the vault. If your ledger is modified after sealing, the hash will not match.

---

## 5. After Submission

Run:
```bash
python3 discovery_fabric/dsb_v1/adjudication_engine_v2/run_v2_comparison.py
```

The comparison engine will:
1. Verify your ledger has 80 entries and is sealed
2. Decrypt the vault using the key from evaluator boundary
3. Compute confusion matrices (strict + lenient, real/fabricated/all)
4. Check plausibility-vs-actual-label correlation
5. Generate per-disagreement forensic case files
6. Produce `DSB_V1_CTO_ADJUDICATION_REPORT_V2.md`

---

## 6. Evidence Tier

Your adjudication is **AI_CTO_ADJUDICATION** — NOT HUMAN_VALIDATED. You are not independent (you directed the system). Per MC-1, your adjudication cannot validate the system. It can only check whether the machine scorer agrees with your informed judgment.

**No architecture change is permitted based on your adjudication alone.**

---

**End of V2 CTO Adjudication Instructions.**
