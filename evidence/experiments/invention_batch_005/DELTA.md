# DELTA report — batch_004 (pre-Gap 4 fix) vs batch_005 (post-Gap 4 fix)

Date: 2026-08-01
Gap fixed: Gap 4 (missing counterevidence)
Architecture modification: orchestrator.py ONLY (per Maestro Loop PHASE 6)
Hypothesis: see evidence/experiments/invention_batch_005/cycle_4_hypothesis.py

## Headline metrics

| Metric | batch_004 (pre-fix) | batch_005 (post-fix) |
|---|---|---|
| Hypotheses with non-empty counterevidence | 0/20 | 20/20 |
| Avg counterevidence items per hypothesis | 0 | ~5 |
| Counterevidence sources | none | Layer 3 + Layer 5 + Layer 10 |

## What changed (Gap 4 fix)

The orchestrator's `_chain_summary` method was modified to pull
counterevidence from four layers:

1. **Layer 3 failure_modes** — e.g., "failure_mode: cost_overrun",
   "failure_mode: regulatory_rejection"
2. **Layer 5 stress_testing** — worst-case composites below 0.40
   (e.g., "stress_scenario: composite=0.3678 (below 0.40)")
3. **Layer 10 technical_risks** — failure modes + stress composites
   not already in Layer 3
4. **Layer 10 commercial_risks** — e.g., "commercial_risk:
   market_size_too_small_to_justify_capex"

Before the fix, the counterevidence field was always empty. The system
was an optimism engine — it only listed what supported the claim,
never what would weaken it. After the fix, every hypothesis answers
BOTH questions:

- Why might this work? (evidence)
- Why might this fail? (counterevidence)

## The hypothesis (PHASE 5 prediction)

> "At least 15/20 hypotheses will have non-empty counterevidence."

Result: **20/20** — the hypothesis is CONFIRMED (and exceeded).

## PHASE 10 — DECISION

**YES — reality supported the hypothesis.**

The modification is preserved.

## What did NOT change

- Unique composite scores: unchanged (Gap 4 doesn't affect scoring).
- Blueprint buildable fields: unchanged (Gap 3 fix preserved).
- Causal classifications: unchanged (Gap 2+7 fix preserved).
- 0 compiler exceptions in both batches.
- Gaps 1, 2, 3, 5, 6, 7 are UNCHANGED.

## What was modified

- invention_compiler/orchestrator.py: added counterevidence construction
  in `_chain_summary` — pulls from Layer 3, 5, 10. Passed to Hypothesis
  constructor and fallback dict.
- tests/test_gap4_fix.py: 11 new tests.
- evidence/experiments/invention_batch_005/: 20 YAML outputs + DELTA.md.

## What was NOT modified (per Maestro Loop PHASE 6)

- simulation_module.py (Gap 1)
- dependency_module.py (Gap 2+7)
- blueprint_module.py (Gap 3)
- prototype_module.py (Gap 5)
- chemistry_knowledge_module.py (Gap 6)
- All other modules

## Loop history

| Cycle | Gap | File modified | Decision |
|---|---|---|---|
| 1 | Differentiation (Gap 1) | simulation_module.py | YES |
| 2 | Causal graph (Gap 2+7) | dependency_module.py | YES |
| 3 | Blueprint structure (Gap 3) | blueprint_module.py | YES |
| 4 | Counterevidence (Gap 4) | orchestrator.py | YES |

## Next gap (per priority table)

| Gap | Priority | Status |
|---|---|---|
| Gap 6 (chemical differentiation) | Medium | Next |
| Gap 5 (templated plans) | Medium | After Gap 6 |
