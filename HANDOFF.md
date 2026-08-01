# TEE MASTER HANDOFF (v1.3)

## PRE-CODING READ LIST (MANDATORY)

Before writing or modifying any code in this repository, read these
files in order:

1. `CONSTITUTION.md` — the eight immutable laws. Law 8 is the one
   most often violated.
2. `INVENTION_COMPILER.md` — the master specification. The system
   is an invention compiler, not an idea generator.
3. `ANTI_ENTROPY.md` — operational rules: tests first, single
   responsibility, refactor constantly, lock dependencies,
   document assumptions, decouple modules, clear dead code,
   maintain patterns.
4. `FAILURES.md` — the failure taxonomy. Do not re-introduce.
5. `HANDOFF.md` — this file. Current state of the system.

Skipping this read list will reproduce a bug that has already been
fixed. F-005 is the canonical example.

## RULES
Rule 0: No manual work. Rule 1: Architecture is frozen.

## EIGHT LAWS
1. Transformation, not object. 2. Explicit constraint surface. 3. Nodes and edges.
4. Decomposable. 5. Adversarial survival. 6. Expose assumptions. 7. Historical permanence.
8. Verification standard: no "verified" without a successful prediction, a failed
prediction, and replayable evidence.

## BENCHMARK DISCIPLINES
1. Immutability: never overwrite benchmarks. Use _review/_resolution suffixes.
2. Provenance: every benchmark has source, domain, created_at, reviewer, version, assumptions, limitations.
3. Drift Detection: benchmarks/drift/ monitors graph, assumptions, scores, calibration.

## SEARCH MODES
Mode 1: New combinations. Mode 2: Almost ready. Mode 3: Resurrection. Mode 4: Constraint leverage.

## CANDIDATES
0001 APRM: GATED. 0002 DAM: REVISE. 0003 ACWPS: REVISE.

## INVENTION COMPILER DIRECTIVE
The system is no longer an idea generator. It is an invention compiler.
The final output is a blueprint, not an idea score. See
`INVENTION_COMPILER.md` for the 11-layer output structure and the
13 required modules. Every change must move us closer to one of
those layers or modules.

## CURRENT STATE (as of commit `a3d167d`)
- F-005 remediated. Ledger is clean, 10 entries (1 benchmark_run +
  9 verification). Law 8 verdict: PASS.
- P2 prerequisite chain: implemented in `product/lineage/mapper.py`.
- P3 cross-domain synthesizer: implemented in `product/discovery/synthesizer.py`.
- P4 feasibility scoring: implemented in `product/scoring/feasibility.py`.
- Invention compiler vertical slice: implemented in
  `invention_compiler/` (commit `a3d167d`). 11 layers, 14 modules.
- 47 tests passing.

## CTO REVIEW (commit `a3d167d`)

The CTO approved the ARCHITECTURE but did NOT approve the SCIENTIFIC
CLAIMS. Concretely:

- Approved: layer architecture, orchestration pipeline, evidence
  chain, audit integration, blueprint generation framework, dependency
  graph framework, constraint propagation framework, simulation
  framework, verification framework, test framework.
- NOT approved: physics/chemistry/biology/economics/information_theory/
  thermodynamics/control_theory "engines." The current implementations
  are keyword-matching MODULES, not scientific ENGINES.

New CTO-mandated rules (encoded in INVENTION_COMPILER.md and
ANTI_ENTROPY.md):
1. The word "engine" may only be used for modules with explicit model
   + empirical validation + reproducible results. Otherwise the
   module/adapter/framework/layer/stage terminology applies.
2. The 5-benchmark suite (portable MRI, ammonia synthesis,
   room-temp superconductors, carbon-negative cement, artificial
   photosynthesis) must be run before any further scientific claims.
3. Optimize for blueprints that scientists would respect, not for
   producing ideas.

## IMPLEMENTATION WORK THIS SESSION
- Rename 12 `*_engine.py` files to `*_module.py` (verification_engine
  stays — it meets the bar).
- Add 5-benchmark suite at `benchmarks/compiler/`.
- Add `scripts/run_compiler_benchmarks.py`.
- Add `compiler_benchmark_report.json` as 8th audit deliverable.

## 13 modules required by the invention-compiler directive
After this session's rename:
- 1 fully implemented as engine (verification_engine — meets the bar).
- 12 implemented as modules (renamed from "engine" per CTO rule).
- The next leap: turn the modules into actual scientific engines.

## FINAL INSTRUCTION
Do not redesign. Do not add agents. Optimize for truth, calibration,
prediction, resurrection accuracy, constraint leverage, AND blueprint
completeness. Every layer of the 11-layer output structure must be
emittable before the system can honestly claim to be an invention
compiler.
