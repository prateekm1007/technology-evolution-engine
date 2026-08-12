# PSCD-1 Pre-Registration

**Status:** PRE-REGISTERED — frozen before any A2 implementation
**Date:** 2026-08-13
**Authority:** CTO Directive (Phase 0/1/2 ONLY) + Scientific Audit Q14–Q20

---

## 1. Experiment Name

Prospective Sealed Cross-Domain Prediction Contest (PSCD-1)

## 2. Arms

| Arm | Definition |
|---|---|
| A0 | Frontier LLM alone. Frozen model identifier. Frozen prompt. No retrieval. Fixed token/tool budget. |
| A1 | Same model, same budget, same prompt, plus one immutable retrieval snapshot. |
| A2 | TEE minimal (only components that survive deletion list). **NOT YET AUTHORIZED** — only after A0/A1 runnable + dry-run pass. |
| A3 | Random/hypothesis-noise control (foil). |

**Budget parity:** All arms receive identical token budget, tool budget, wall-clock budget, and retrieval access (A0 gets empty retrieval; A1/A2/A3 get the same snapshot).

**The ONLY difference between A0 and A1 is retrieval.** The ONLY difference between A1 and A2 is the Fabric scaffolding. No mechanism extraction, no constraints, no combination engine, no special scoring prompt in A0/A1.

## 3. Sample Size

N ≥ 50 sealed task pairs (paper-pairs from frozen corpus, domains disjoint).

Domains: at least 2 disjoint scientific domains.

## 4. Domain Allocation

Domains allocated by independent custodian (not the implementer). Allocation frozen before any arm runs.

## 5. Cutoff Date

T0: pre-registered publication cutoff. No source published after T0 may be in the retrieval snapshot or used as evidence.

## 6. Retrieval Snapshot

One immutable index pinned by content hash (`retrieval_snapshot_sha256`). Same snapshot for A1, A2, A3. A0 receives empty retrieval (no documents).

## 7. Model Freeze

- Model identifier: [TO BE FROZEN — frontier LLM, version-pinned]
- Model version/date: [TO BE FROZEN]
- Prompt template hash: [TO BE FROZEN — same prompt for A0/A1/A2]

## 8. Predictions Per Case

K = 1 prediction per case per arm. (Each arm emits exactly 1 prediction per sealed task.)

## 9. Primary Endpoint

> **retrieval-negative + non-entailed + later-confirmed**

with a pre-registered quantitative tolerance.

Definition:
- **retrieval-negative**: no retrieved source in the frozen corpus directly entails the proposed relationship (machine-checkable)
- **non-entailed**: the proposed relationship is not logically entailed by the supplied evidence (deterministic check)
- **later-confirmed**: the prediction's quantitative forecast matches a later-observed outcome within the pre-registered tolerance

**NOT the endpoint:** plausibility, mechanism quality, LLM judge score, similarity, historical recovery, semantic overlap, "interestingness," expert enthusiasm.

## 10. Tolerance Rule

Quantitative predictions must specify a point estimate + tolerance (e.g., "value X ± 20%" or "YES/NO exact match").

Calibration error = |predicted - observed| / |observed|. Must be ≤ 0.50 for "confirmed."

Binary predictions require exact YES/NO match.

## 11. Foil Definition

Fabricated/counterfactual relationships mixed into the sealed set. Foils are designed to sound plausible but are NOT real relationships.

For every arm, calculate:
- `true_confirmation_rate`: fraction of true (non-foil) predictions that are later-confirmed
- `foil_confirmation_rate`: fraction of foil predictions that are "confirmed" (should be 0 if the system works)
- `net_discovery_rate = true_confirmation_rate - foil_confirmation_rate`

**A beautiful true-positive rate with a large foil rate is a failed discovery system.**

## 12. Statistical Test

Two-proportion z-test (A2 vs A1 on primary endpoint), one-sided.
Bootstrap 95% CI for the difference.
Bonferroni correction for 3 comparisons (A2 vs A1, A2 vs A0, A1 vs A0).

## 13. Effect Size

δ = +10 percentage points (absolute). A2 must exceed A1 by ≥ 10pp on the primary endpoint.

ε = 5% (maximum foil confirmation rate for any arm).

## 14. Stopping Rule

- If A2 − A1 ≤ 0 on primary endpoint: **FABRIC_STATUS = RETIRED**. Stop.
- If no arm beats foils (all arms' net_discovery_rate ≤ 0): discovery thesis in doubt. Revisit.
- If A2 > A1 by δ with CI excluding 0 and foil rate ≤ ε: A2 authorized for Phase 5.

## 15. AINT-1 Kill Switch

```
if A2 - A1 <= 0:
    FABRIC_STATUS = RETIRED
```

No "maybe another module would help." No "the scorer was imperfect." No "let's add temporal reasoning." No "let's try a stronger extractor."

**If A2 does not beat A1 prospectively, we simplify.**

## 16. Anti-Game Rules

- No scorer trained on these cases
- No human in the generation loop
- Model/date freeze enforced
- Retrieval snapshot hash enforced
- Coder cannot touch sealed keys (separate identity)
- All predictions hash-committed before key release

## 17. Human Expert Role

Humans are used ONLY for:
- Calibration set (N ≥ 20, dual-annotated, disjoint from test)
- Novelty/entailment adjudication
- Eventual external confirmation

Generation remains machine-only and blind.

## 18. Evidence Classes (Never Collapsed)

```
MACHINE_RESULT
AI_CTO_ADJUDICATION
HUMAN_EXPERT_ADJUDICATION
EXTERNAL_EXPERIMENTAL_CONFIRMATION
```

## 19. Gate Sequence (Evidence-Based)

```
TRUTH SUBSTRATE PASS
        ↓
A0/A1 RUNNABLE
        ↓
PSCD SEALED
        ↓
DRY RUN PASS
        ↓
A2 AUTHORIZED
        ↓
PROSPECTIVE RESULT
        ↓
ARCHITECTURE LIVES OR DIES
```

Time is not the gate. Evidence is.

## 20. Cache / Routing / Fallback Policy (V7 Addition)

The following protocol parameters are frozen as part of this pre-registration:

```
CACHE_POLICY = NOT_PERMITTED
  OpenRouter response caching must be disabled for all PSCD arms.
  If caching cannot be disabled, cache-hit responses must be recorded in the
  execution receipt and excluded from the primary analysis.
  Rationale: a cached response does not represent independent experimental compute.

ROUTING_POLICY = FIXED_MODEL
  All arms must request the same model identifier (meta-llama/llama-3.3-70b-instruct).
  If OpenRouter routes to a different provider/backend, the observed_response_model
  in the execution receipt must match across A0 and A1. If it does not match,
  the parity harness fails and the run is invalidated.

PROVIDER_FALLBACK = NOT_PERMITTED
  If OpenRouter falls back to a different model/provider, the run is invalidated.
  The execution receipt must record observed_response_model for every call.
  Any mismatch between requested model and observed response model invalidates
  the affected arm's predictions for that task.
```

These policies are enforced by the parity harness (V7+), which compares:
- `observed_response_model` (A0 vs A1 must match)
- `observed_response_status` (both must be 200)
- `observed_retry_count` (must match)

### Execution Receipt Requirements

Every PSCD prediction must include an HTTPExecutionReceipt with:
- `observed_response_model` — the model actually used
- `observed_response_status` — HTTP status
- `observed_retry_count` — retries actually used
- `observed_response_schema_hash` — derived from actual response JSON
- `observed_request_body_hash` — hash of actual serialized request
- `observed_rendered_prompt_hash` — hash of actual prompt sent

If OpenRouter exposes cache-hit metadata in the response, it must be recorded.

## 21. Custodian Workflow for Real Outcome Seal

The real PSCD-1 outcome seal must be generated by an external custodian:

1. **Custodian** (not the builder) selects N≥50 paper-pairs from the frozen corpus
2. **Custodian** identifies later-observed outcomes (T0+Δ papers, patents, registered results)
3. **Custodian** encrypts outcomes with AES-256-GCM
4. **Custodian** stores ciphertext + manifest in durable storage
5. **Custodian** holds the key — builder has no access
6. **Builder** runs A0/A1, hash-commits predictions
7. **Custodian** verifies predictions are sealed
8. **Custodian** releases key for evaluation
9. **Evaluator** decrypts outcomes, scores predictions deterministically

The seal is REAL only when:
- Ciphertext physically exists in durable storage
- Key is held by custodian (not builder)
- Predictions were sealed BEFORE key release
- Timestamp ordering is verifiable

---

**This pre-registration is frozen. No modifications after A0/A1 are runnable. If new evidence requires changes, create PSCD-2 (do not modify PSCD-1).**
