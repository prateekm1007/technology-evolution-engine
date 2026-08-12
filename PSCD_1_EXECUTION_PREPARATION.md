# PSCD-1 EXECUTION PREPARATION — FINAL STATUS

**Date:** 2026-08-13
**Commit:** dfd4cc32 (code/protocol frozen)
**Status:** CODE AND PROTOCOL FROZEN. Awaiting external custodian.

---

## 1. What Is Frozen

All code, protocol, and instrumentation are frozen at commit `dfd4cc32`. No further V8/V9 instrumentation cycles. The baseline is ready enough for the scientific experiment.

### Frozen artifacts:
- `SCIENCE_FREEZE.md` — constitutional freeze on new architecture
- `pscd/PSCD_1_PREREGISTRATION.md` — full protocol including cache/routing/fallback policy (§20) and custodian workflow (§21)
- `pscd/prediction_schema.py` — canonical Prediction with machine-checkable attestation
- `pscd/a0_a1_runners.py` — A0/A1 runners with budget parity
- `pscd/retrieval_snapshot_v1.json` — 106-source frozen snapshot
- `pscd/PSCD_CUTOFF_FREEZE.json` — conservative cutoff (previous complete UTC day)
- `pscd_v7_final_measurement.py` — V7 measurement harness (final version)
- `SCIENTIFIC_EXECUTION_GATE.json` — gate state with 13/13 parity invariants

### Cache/Routing/Fallback Policy (frozen in preregistration §20):
```
CACHE_POLICY = NOT_PERMITTED
ROUTING_POLICY = FIXED_MODEL
PROVIDER_FALLBACK = NOT_PERMITTED
```

Enforced by parity harness: observed_response_model, observed_response_status, observed_retry_count must match across A0 and A1.

## 2. What Is NOT Modified

- Discovery architecture: NOT modified (quarantined)
- Scorer: NOT modified (frozen)
- DSB V1 cases/prompts/receipts: NOT modified (frozen)
- Corpus selection: NOT modified (106 included, 6 excluded, pre-registered)
- Temporal reasoning: NOT implemented
- Negative knowledge: NOT implemented
- Patents: NOT integrated
- New discovery modes: NOT added
- A2: NOT implemented, NOT authorized

## 3. Gate Status

```
CORPUS/SNAPSHOT INTEGRITY       GREEN
TEMPORAL CONTROL                GREEN
A0/A1 MEASUREMENT HARNESS       GREEN
PER-SOURCE EVIDENCE MAPPING     GREEN
ENTAILMENT HANDLING             GREEN
REAL OUTCOME SEAL               RED    ← ONLY BLOCKER
SCIENTIFIC EXECUTION            BLOCKED
A2                              NOT AUTHORIZED
```

## 4. The Only Remaining Blocker

**REAL_SEAL_READY = FALSE**

A real prospective outcome must be sealed externally, before predictions are evaluated. This is a scientific requirement, not an engineering one.

### Custodian Workflow (documented in preregistration §21):
1. Custodian selects N≥50 paper-pairs from frozen corpus
2. Custodian identifies later-observed outcomes
3. Custodian encrypts outcomes with AES-256-GCM
4. Custodian stores ciphertext + manifest in durable storage
5. Custodian holds key — builder has no access
6. Builder runs A0/A1, hash-commits predictions
7. Custodian verifies predictions sealed
8. Custodian releases key for evaluation
9. Evaluator decrypts, scores deterministically

## 5. What Happens Next (Not Code)

The next evidence should come from the experiment, not another version number.

```
SCIENTIFIC_EXECUTION_PERMITTED = FALSE  (until REAL_SEAL_READY = TRUE)
A2_AUTHORIZATION_REQUESTED = FALSE      (not requested)
```

When the external custodian provides a real sealed outcome:
1. `REAL_SEAL_READY` → `TRUE`
2. `SCIENTIFIC_EXECUTION_PERMITTED` → `TRUE`
3. Run A0/A1 on the sealed task set
4. Hash-commit predictions
5. Custodian releases key
6. Score deterministically
7. Analyze: does any arm beat foils?
8. If yes: A2 authorization may be requested
9. If A2 ≤ A1: FABRIC_STATUS = RETIRED

---

**This is the point where more coding becomes a liability. The next evidence should come from the experiment, not another version number.**

**STOP.**
