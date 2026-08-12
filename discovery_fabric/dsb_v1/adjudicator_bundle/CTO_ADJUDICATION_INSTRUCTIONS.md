# CTO ADJUDICATION INSTRUCTIONS — DSB V1

**Bundle:** DSB_V1_ADJUDICATOR_BUNDLE
**Date:** 2026-08-12T20:07:15.611132+00:00
**Evidence tier:** AI_CTO_ADJUDICATION (NOT HUMAN_VALIDATED)

---

## 1. Bundle Contents

This bundle contains ONLY:
- `cto_packets_BLIND.json` — 80 blinded adjudication packets
- `CTO_ADJUDICATION_INSTRUCTIONS.md` — this file
- `cto_adjudication_template.json` — empty ledger template
- `BUNDLE_MANIFEST.json` — public integrity metadata (file hashes)

This bundle does NOT contain:
- Case files (real or fabricated)
- Real/fabricated labels
- Breakthrough relationships
- Withheld facts
- Answer mechanisms
- Machine receipts or scores
- Full packets
- Evaluator secrets
- Git metadata or repository history
- Research repository code

## 2. Adjudicator Environment Requirements

The adjudicator machine/container MUST:
- Have ZERO access to the research repository
- Have ZERO access to Git objects, case files, or evaluator namespace
- Have ZERO access to machine scores or vault keys
- Run in a separate OS identity/container from the evaluator

The adjudicator machine MUST NOT:
- Be able to read the research repository
- Be able to read Git objects (.git/)
- Be able to read case files (cases/real/, cases/fabricated/)
- Be able to read evaluator_boundary/
- Be able to read receipts/ or scores/
- Have network access to the evaluator machine

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

### Q6. PLAUSIBILITY
Is this proposal scientifically plausible — could it work in reality, regardless of whether it has been historically demonstrated?
- PLAUSIBLE / IMPLAUSIBLE / UNCERTAIN

## 4. Submission

1. Copy `cto_adjudication_template.json` to `cto_adjudication.json`.
2. Fill in all 80 adjudication slots.
3. Fill in `submitted_at` and `time_spent_minutes`.
4. Seal the ledger: compute SHA-256 of the ledger (excluding ledger_hash) and add it as `ledger_hash`.
5. Save.

## 5. Evidence Tier

AI_CTO_ADJUDICATION — NOT HUMAN_VALIDATED. Per MC-1 (No self-validation),
CTO adjudication cannot validate the system. No architecture change permitted
based on this adjudication alone.

---

**End of Adjudication Instructions.**
