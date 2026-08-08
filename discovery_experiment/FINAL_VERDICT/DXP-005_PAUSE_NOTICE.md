# DXP-005 — PAUSE NOTICE (Amendment 14)

**Status:** PAUSED — NOT EXECUTED UNDER PREREGISTERED PROTOCOL
**Valid Scientific Runs:** 0
**Preregistered Provider:** ZAI (glm-4-plus via z-ai CLI)
**Pause Date:** 2026-08-08
**Reason:** Preregistered provider (ZAI) unavailable (HTTP 429). Protocol freeze prohibits provider substitution.
**Resume Condition:** Only after Phase 17 of the 18-phase plan produces `DISCRIMINATIVE` verdict AND ZAI provider is available, OR a new experiment (DXP-005b) is separately preregistered with a different provider.

---

## CORRECTION (per external audit 2026-08-08)

The original version of this notice incorrectly listed the provider as
"OpenRouter Nemotron 3 Ultra (ZAI rate-limited)". That was the provider
used for the QUARANTINED pilot, NOT the preregistered provider for
DXP-005.

The preregistered DXP-005 protocol (frozen at commit `66b3212`,
specification at `discovery_experiment/CASES/DXP-005_SPECIFICATION.md`)
specified ZAI as the provider. The Nemotron execution was an
unpreregistered provider substitution that violates Amendment 14.

**Correct status:**

```
DXP-005 (preregistered, ZAI):
    STATUS = PAUSED
    VALID_SCIENTIFIC_RUNS = 0
    PRIMARY_PROVIDER = ZAI
    REASON = PROVIDER_UNAVAILABLE (HTTP 429)

DXP-005-NEMOTRON-PILOT (unpreregistered):
    STATUS = QUARANTINED
    VALID_FOR_DXP005_ANALYSIS = false
    REASON = provider_changed_after_protocol_freeze
    LOCATION = experiments/dxp005_pilots/nemotron/
```

The two datasets MUST NOT be merged.

---

## What was DXP-005?

DXP-005 was a preregistered generator-ablation experiment testing the
H-GEN-1 intervention (mechanism-preservation through abstraction).

- 3 conditions × 10 cases = 30 runs planned
- A = baseline (no mechanism graph)
- B = H-GEN-1 (real mechanism graph)
- C = mechanism-null (irrelevant mechanism graph with same structure)
- **Preregistered provider: ZAI (glm-4-plus via z-ai CLI)**
- Ground truth frozen at SHA `db2df3ec...`
- Protocol frozen at commit `66b3212`

## Why was it paused?

The preregistered provider (ZAI) became unavailable (HTTP 429 rate
limit) after the experiment was frozen. Per Amendment 14, a protocol
freeze means the provider cannot be substituted. The correct response
was to pause and wait for ZAI availability.

An earlier version of the coder incorrectly substituted Nemotron 3
Ultra via OpenRouter and resumed execution. That execution is now
quarantined as an unpreregistered exploratory pilot (see
`experiments/dxp005_pilots/nemotron/QUARANTINE_MANIFEST.json`).

## What is the valid DXP-005 state?

```
VALID_SCIENTIFIC_RUNS = 0
```

Zero. No DXP-005 data has been collected under the preregistered
protocol. The Nemotron pilot data exists but is NOT DXP-005 data.

## What was quarantined?

The Nemotron pilot produced partial results for 4 of 10 cases (N1-N4).
These are preserved as exploratory evidence in
`experiments/dxp005_pilots/nemotron/` but are explicitly excluded
from DXP-005 primary analysis.

Key quarantine findings (see QUARANTINE_MANIFEST.json for details):
- N4 is unusable for ablation (N4-A returned 0 hypotheses due to LLM
  empty response, confounding the B-vs-A comparison)
- N1/N2/N3 transfer rejections are observed outputs, not
  CORRECT_NEGATIVE (adjudication requirements not met)
- The N4-B vs N4-C difference is a sanity-check signal, not H-GEN-1
  evidence

## Resume protocol

DXP-005 may resume ONLY if ALL of the following are true:

1. Phase 17 of the 18-phase plan produces `DISCRIMINATIVE` verdict
2. ZAI provider is available (HTTP 429 resolved)
3. The frozen protocol (`66b3212`) is still valid
4. The ground truth (`db2df3ec...`) is still valid
5. No protocol parameters are changed

If ZAI remains unavailable, a new experiment (DXP-005b) must be
separately preregistered with whatever provider is available. DXP-005b
would be a NEW experiment, not a continuation of DXP-005.

If Phase 17 produces `NOT_DISCRIMINATIVE`, DXP-005 is permanently
abandoned (Amendment 15).

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

The quarantined Nemotron pilot is NOT "promising." It is
UNPREREGISTERED_EXPLORATORY data that cannot be used to support or
falsify H-GEN-1.

The honest path forward is Phase 0 → Phase 17 of the 18-phase plan.
The discrimination verdict will determine whether DXP-005 may resume.
