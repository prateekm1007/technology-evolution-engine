# DELTA report — batch_005 (pre-Gap 5 fix) vs batch_006 (post-Gap 5 fix)

Date: 2026-08-01
Gap fixed: Gap 5 (templated plans)
Architecture modification: prototype_module.py ONLY (per Maestro Loop PHASE 6)
Hypothesis: see evidence/experiments/invention_batch_006/cycle_5_hypothesis.py

## Headline metrics

| Metric | batch_005 (pre-fix) | batch_006 (post-fix) |
|---|---|---|
| Unique v1 goal strings | 1/20 (all identical) | 16/20 |
| Unique v2 goal strings | 1/20 (all identical) | 14/20 |
| Unique duration triples | 2/20 | 8/20 |
| V1 goals reference domain | 0/20 | 20/20 |
| V1 success thresholds reference problem | 0/20 | 20/20 |

## What changed (Gap 5 fix)

The prototype_module's `analyze()` method was modified to produce
invention-specific v1/v2/v3 goals, scopes, success thresholds, and
durations.

Before: all 20 candidates had the same v1 goal ("prove the core
mechanism works at lab scale"), same v2 goal ("prove the subsystems
integrate"), same v3 goal ("prove the manufacturing pathway").

After: each candidate's goals reference its specific domain, problem
text, constraints, and key physics term. For example:
- Solid-state batteries: "prove the core material property
  (material_property) holds at lab scale for build solid state batteries"
- Portable MRI: "prove the imaging mechanism (magnetic_field) produces
  diagnostic-quality signal for build portable mri"
- Artificial photosynthesis: "prove the energy conversion mechanism
  (photon_conversion) works at lab scale for build artificial photosynthesis"

Durations now incorporate domain-specific time multipliers:
- medical_imaging/medical_devices: 1.5x (regulatory + clinical)
- biology: 1.4x (sterile handling, growth cycles)
- energy: 1.3x (safety, scale-up)
- electronics/manufacturing: 0.8-0.9x (faster iteration)

## The hypothesis (PHASE 5 prediction)

> "At least 15/20 candidates will have unique v1 goal strings."

Result: **16/20** — the hypothesis is CONFIRMED.

## PHASE 10 — DECISION

**YES — reality supported the hypothesis.**

The modification is preserved.

## What did NOT change

- Unique composite scores: unchanged (Gap 5 doesn't affect scoring).
- Blueprint buildable fields: unchanged (Gap 3 fix preserved).
- Counterevidence: unchanged (Gap 4 fix preserved).
- Causal classifications: unchanged (Gap 2+7 fix preserved).

## What was modified

- invention_compiler/prototype_module.py: replaced templated goals/
  scopes/thresholds with invention-specific versions parameterized by
  domain, problem text, constraints, and key physics. Added domain-
  specific time multipliers and goal templates.
- tests/test_gap5_fix.py: 12 new tests.

## What was NOT modified (per Maestro Loop PHASE 6)

- simulation_module.py, dependency_module.py, blueprint_module.py,
  orchestrator.py, chemistry_knowledge_module.py, all other modules.

## Loop history

| Cycle | Gap | File | Decision |
|---|---|---|---|
| 1 | Differentiation | simulation_module.py | YES |
| 2 | Causal graph | dependency_module.py | YES |
| 3 | Blueprint structure | blueprint_module.py | YES |
| 4 | Counterevidence | orchestrator.py | YES |
| 5 | Templated plans | prototype_module.py | YES |

## Next gap

| Gap | Priority | Status |
|---|---|---|
| Gap 6 (chemical differentiation) | Medium | Next |
