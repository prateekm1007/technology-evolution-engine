# CTO ADJUDICATION INSTRUCTIONS — DSB V1

**Engine:** ADJUDICATION_ENGINE_V1
**Date:** 2026-08-12T18:40:21.755237+00:00
**Vault sealed at:** 2026-08-12T18:40:21.752996+00:00
**Vault hash:** `438a2123b5b6408f0f156d2bbea6876e...`

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
