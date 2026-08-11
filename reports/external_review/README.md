# External Review README

## Repository
technology-evolution-engine

## Frozen baseline
stage-1-measurement-integrity-baseline

## Commit
777cb6d

## Purpose
Independent evaluation of genuine cross-domain discovery.

## Development status
FROZEN

## Feature development
PROHIBITED

## Benchmark repair
PROHIBITED

## Expected evaluator behavior
Adversarial

---

## Your mission

You are not being asked to confirm the authors' conclusions. You are being asked to determine whether the evidence survives independent scrutiny.

The repository authors have measured three defects in their own benchmark:

1. **Proposal-locus leakage**: 25% of current true positives come from ambient entity presence, not from the system proposing the bridge.
2. **FP=0 by construction**: The scorer never counts false positives, so precision=1.0 is a tautology.
3. **Loose matcher**: All 20 current matches are token-overlap, not exact. Zero strict-normalized matches exist.

The authors have frozen the benchmark in this state as evidence. They have NOT repaired it.

Your job is to determine: **Can this engine demonstrate genuine novel cross-domain discovery when recognition, retrieval, lexical overlap, benchmark leakage, and self-grading are removed?**

## What you have access to

- Full repository source code
- All benchmark code and gold sets
- The Stage −1 measurement evidence (`reports/stage_minus_1/`)
- All historical failures and audit results (`FAILURES.md`)
- The measurement infrastructure (`programs/A_metrology/`)

## What you should NOT trust

- Any F1 score reported by the production scorer (it has measured defects)
- The engine's own novelty assertions
- Generated prose explanations of discoveries
- Any claim of "verified" or "production ready"

## Where to start

1. Read `reports/external_review/FROZEN_BASELINE.md` for the measurement matrix
2. Read `reports/external_review/KNOWN_MEASUREMENT_DEFECTS.md` for what's broken
3. Read `reports/external_review/EXTERNAL_EVALUATOR_BRIEF.md` for your mission
4. Read `reports/external_review/RECOMMENDED_TEST_BATTERY.md` for test suggestions
5. Run the engine yourself: `python3 -m benchmarks.discovery_capability_benchmark`
6. Inspect the gold set: `benchmarks/discovery_capability_benchmark.py` (GOLD_DISCOVERIES)
7. Try to break it
