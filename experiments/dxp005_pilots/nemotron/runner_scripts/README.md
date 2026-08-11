# Nemotron Pilot Runner Scripts (ARCHIVAL)

**Status:** ARCHIVAL — DO NOT EXECUTE
**Quarantine Date:** 2026-08-08
**Parent:** `experiments/dxp005_pilots/nemotron/QUARANTINE_MANIFEST.json`

## What these scripts are

These are the operational runner scripts used to execute the DXP-005
Nemotron pilot. They were moved here from `scripts/` per external audit
finding B (2026-08-08):

> "Do not leave scripts/run_dxp005_step.py, scripts/run_dxp005_all.sh
> as runnable production-looking scripts pointing at
> discovery_experiment/ENGINE_OUTPUT/DXP-005. Move them under the pilot
> namespace or turn them into inert archival artifacts."

## Why they are here

The DXP-005 protocol was frozen on ZAI (glm-4-plus). These scripts were
created to execute DXP-005 with Nemotron 3 Ultra via OpenRouter after
ZAI became unavailable (HTTP 429). That provider substitution violated
Amendment 14 (Scientific Visibility Boundary). The resulting data is
quarantined as an unpreregistered exploratory pilot.

These scripts are preserved as archival artifacts because:
1. They document exactly how the quarantined pilot was executed
2. They may inform a future separately-preregistered Nemotron experiment
3. Deleting them would destroy the operational record

## Machine-enforced prohibition

Each script contains a machine-enforced protocol lock at the top of
its `main()`:

```python
from engine.protocol_lock import assert_experiment_authorized
assert_experiment_authorized("DXP-005")
```

This lock reads `PROGRAM_STATE.json` and raises `ExperimentNotAuthorized`
if DXP-005 is not in AUTHORIZED status. Since DXP-005 is currently
PAUSED, these scripts CANNOT execute. The lock is fail-closed.

Even if moved back to `scripts/`, the lock would still prevent execution.

## Files

| File | Purpose |
|---|---|
| `run_dxp005_step.py` | Run a single step (upstream/hypotheses/adversarial) for one case × condition |
| `run_dxp005_one.py` | Run all 3 conditions for a single case |
| `run_dxp005_all.sh` | Bash loop over all 10 cases × 3 conditions |

## How to re-enable (NOT RECOMMENDED)

These scripts should NOT be re-enabled for DXP-005. If a future
experiment (e.g., DXP-005b-NEMOTRON) is separately preregistered, new
runner scripts should be created for that experiment with its own
protocol lock referencing its own experiment ID.

To re-enable DXP-005 itself (the ZAI-preregistered version), ALL of
the following must be true:
1. Phase 17 of the 18-phase plan produces DISCRIMINATIVE
2. ZAI provider is available
3. The frozen protocol is still valid
4. `PROGRAM_STATE.json` is updated to `dxp005.status = AUTHORIZED`

Until then, these scripts are inert.
