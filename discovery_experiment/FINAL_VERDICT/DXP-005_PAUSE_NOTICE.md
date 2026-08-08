# DXP-005 — PAUSE NOTICE (Amendment 14)

**Status:** PAUSED — INCOMPLETE
**Pause Date:** 2026-08-08
**Reason:** Amendment directive received mid-execution
**Resume Condition:** Only after Phase 17 of the new 18-phase plan produces `DISCRIMINATIVE` verdict

---

## What was DXP-005?

DXP-005 was a preregistered generator-ablation experiment testing the H-GEN-1
intervention (mechanism-preservation through abstraction).

- 3 conditions × 10 cases = 30 runs planned
- A = baseline (no mechanism graph)
- B = H-GEN-1 (real mechanism graph)
- C = mechanism-null (irrelevant mechanism graph with same structure)
- Provider: OpenRouter Nemotron 3 Ultra (ZAI rate-limited)
- Ground truth frozen at SHA `db2df3ec...`

## Why was it paused?

Two reasons:

1. **Operational:** The bash tool repeatedly killed background processes
   after ~2 minutes, preventing the long-running adversarial gate from
   completing within the tool's time budget. Each adversarial call to
   Nemotron takes 20-60 seconds, and a single case × condition requires
   3 calls plus generation, totaling 4-8 minutes per condition.

2. **Programmatic:** The Amendment directive establishes that no discovery
   experiment (DXP-*) may claim discovery until the matching/discrimination
   study (Phases 8-17) has produced a `DISCRIMINATIVE` verdict. Since
   DXP-005's results could not be safely interpreted without first
   establishing that the matcher is real, continuing execution would
   risk producing "discovery-adjacent" results that the program is no
   longer authorized to interpret.

## What was completed before pause?

| Case | Type | Status |
|---|---|---|
| N1 (gecko→underwater) | negative | TRANSFER_REJECTED (correct) |
| N2 (bird→submarine) | negative | A: 4 hyps, 0 surv / B: 3 hyps, 0 surv / C: 3 hyps, adversarial incomplete |
| N3 (cactus→battery) | negative | B: 3 hyps generated, no adversarial |
| N4 (chameleon→LED) | negative | B: 3 hyps / C: 3 hyps / A: 0 hyps (LLM empty) |
| N5 (firefly→solar) | negative | NOT_STARTED |
| P1-P5 (positives) | positive | NOT_STARTED |

**Completion:** ~10 of 30 conditions have hypotheses generated. ~6 of 30
have adversarial results. 0 cases are fully complete.

## How is the partial state preserved?

Per Amendment 14, the partial DXP-005 state is FROZEN IN PLACE:

- All `04_hypotheses.json` files: preserved
- All `05_adversarial.json` files: preserved
- All `result.json` files: preserved
- All upstream `HASHES.json` files: preserved
- The provider used (Nemotron 3 Ultra via OpenRouter) is recorded in
  each manifest

The partial state is NOT to be deleted, modified, or "completed" with a
different provider. If DXP-005 is resumed, it must be resumed with the
SAME provider (Nemotron 3 Ultra) under the SAME protocol, OR declared
a NEW EXPERIMENT (DXP-005b) with a new preregistration.

## Why not "finish what we started"?

The Amendment directive explicitly forbids the failure mode where the
machine is allowed to "hide from the answer" by accumulating partial
discovery-adjacent results without first proving its discrimination is
real. The discrimination study (Phases 8-17) is the prerequisite.

A "finished" DXP-005 without a discrimination verdict would be:
- scientifically uninterpretable
- a violation of Amendment 16 (Discovery Gate depends on Discrimination)
- exactly the kind of "impressive but non-independent positive result"
  that the Final Non-Negotiable Principle declares less valuable than
  a reproducible negative

## Resume protocol

If and only if Phase 17 produces `DISCRIMINATIVE`:

1. The DXP-005 specification (already frozen at SHA `db2df3ec...`)
   remains valid.
2. The runner scripts (`run_dxp005.py`, `run_dxp005_step.py`,
   `run_dxp005_all.sh`) remain valid.
3. The partial state can be resumed with the SAME provider.
4. If the provider is changed (e.g., back to ZAI), the experiment
   becomes DXP-005b with a new preregistration.

If Phase 17 produces `NOT_DISCRIMINATIVE`:

- DXP-005 is permanently abandoned (Amendment 15).
- The partial state is preserved as a historical record.
- No discovery claims may be made on the basis of DXP-005 results.

---

## No "rescue" allowed

Per Amendment 15:

> Do not:
> * add semantic synonyms;
> * change thresholds;
> * remove hard cases;
> * alter the null;
> * change the metric;
> * reinterpret the criterion;
> * rerun until favorable;
> * call the result "promising."

The partial DXP-005 state is NOT "promising." It is INCOMPLETE. The
incomplete state is itself a result: it tells us the experimental
infrastructure was not yet ready to complete a generator ablation
under operational constraints.

The honest path forward is Phase 0 → Phase 17. The discrimination
verdict will determine whether DXP-005 may resume.
