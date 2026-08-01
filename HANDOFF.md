# TEE MASTER HANDOFF (v1.4)

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

## CTO REVIEW #2 (commit `02d7658`)

The CTO described the post-rename state as "a genuine increase in
maturity rather than an increase in complexity" and approved:
1. Terminology correction (engine -> module).
2. Honest benchmarks (3/5 PASS, 2/5 FAIL — the failures being the
   valuable result).
3. Explicit honesty contracts in the benchmark report.

The CTO also issued a NEW DIRECTIVE: depth over breadth. The next
objective is NOT to build additional modules. The next objective is
to increase the explanatory power of EXISTING modules:

- physics_module: keyword matching -> laws, equations, constraints,
  units, conservation principles
- chemistry_module: keywords -> reaction pathways, kinetics,
  equilibrium, energy states
- mathematics_module: templates -> optimization, probability, graph
  theory, differential equations, control theory
- dependency_module: connections -> causal relationships
- resurrection_module: historical similarity -> historical
  counterfactual analysis

The 4-category benchmark taxonomy was also mandated:
Reconstruction / Resurrection / Forecasting / Synthesis.

## IMPLEMENTATION WORK THIS SESSION
- Upgrade physics_module to encode conservation laws, units,
  dimensional analysis, thermodynamics laws, EM laws, fluid mechanics.
- Upgrade chemistry_module to encode reaction pathways, kinetics
  (Arrhenius), equilibrium constants, Gibbs energy states.
- Upgrade mathematics_module to encode optimization, probability,
  graph theory, ODE/PDE types, control theory.
- Upgrade dependency_module to encode causal edges
  (necessary/sufficient/strength) and counterfactual analysis.
- Upgrade resurrection_module to encode historical counterfactual
  analysis.
- Add 4-category benchmark taxonomy (Reconstruction/Resurrection/
  Forecasting/Synthesis) to benchmarks/compiler/.
- Re-run benchmark suite — verify the 2 FAIL cases (ammonia synthesis,
  RT superconductors) move closer to their expected verdicts.

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
