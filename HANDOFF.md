# TEE MASTER HANDOFF (v2.2 — Maestro Loop formalized)

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

## MAESTRO MODIFICATION LOOP (v1.0) — formalized

The modification process is now formalized as the Maestro Modification
Loop: a 10-phase epistemic loop (not a software-development loop).

```text
PHASE 0 FREEZE → PHASE 1 EXECUTION → PHASE 2 OBSERVATION →
PHASE 3 GAP ANALYSIS → PHASE 4 SELECTION → PHASE 5 HYPOTHESIS →
PHASE 6 MODIFICATION → PHASE 7 RE-EXECUTION → PHASE 8 DELTA →
PHASE 9 LEDGER → PHASE 10 DECISION → REPEAT
```

### Canonical question

> What did reality teach us, and how should the system change because of it?

### Canonical objects

```text
Observation → Knowledge → Hypothesis → Blueprint → Experiment → Observation
```

### Loop state

| Gap | Phase | Decision |
|---|---|---|
| Gap 1 (identical scoring) | 10 — DECISION | YES — preserved |
| Gap 2+7 (arbitrary deps + causal graph) | 10 — DECISION | YES — preserved |
| Gap 3 (non-buildable blueprints) | 3 → 4 | Next. Critical. Not yet modified. |

### 10 epistemic anti-entropy rules

1. Freeze architecture. 2. Change one thing. 3. Measure everything.
4. Record every failure. 5. Reward evidence. 6. Punish complexity.
7. Prefer causality over correlation. 8. Prefer experiments over arguments.
9. Prefer reality over expectations. 10. Prefer loops over modules.

## LEARN + MODIFY step (commits `194089d` → `a701d77`)

Gap 1 fix (commit `194089d`) succeeded: 9 → 18 unique composites,
8 → 2 max collisions. Portable MRI moved to partially_feasible —
honest, not a regression (system changed opinion because new evidence
entered the computation).

CTO observation: the fix is still aggregation (w₁x₁ + w₂x₂ + ...),
not causation. Recorded for a future iteration.

**Gap selected next: Gap 2 + Gap 7 (arbitrary dependency selection
+ weak causal graph).** Per the CTO: "Pick Gap 2 and Gap 7 together,
because they are really the same problem. Without causal structure,
you cannot have: prerequisites, counterfactuals, resurrection,
forecasting, blueprints, experimentation. Everything depends upon it."

The fix: replace dependency_module's arbitrary `_pick_target` with
problem-aware relevance matching (domain + constraint keywords +
problem-text keywords). Localized to dependency_module.py only.

## IMPLEMENTATION WORK THIS SESSION
- Fix Gap 2+7 ONLY in dependency_module.py.
- Add test asserting problem-relevant target selection + non-zero
  causal classifications when relevant prerequisites exist.
- Re-run all 20 inventions → invention_batch_003/.
- Produce DELTA.md comparing batch_002 vs batch_003.
- Confirm only dependency_module.py was modified.

## LEARN + MODIFY step (commits `bdfca58` → `194089d`)

## CEO DIRECTIVE — FREEZE ARCHITECTURE (commit `0c6d5d7`)

Effective immediately: NO new layers, modules, packages, frameworks,
or abstractions. Use only what already exists.

The CEO and CTO agreed the repository is approaching the point
where adding more abstractions produces the illusion of progress.
The most valuable thing now is to STOP building infrastructure
and FORCE the system to produce inventions.

### Required: 20-invention experiment

Run the compiler against 20 candidate inventions (solid-state
batteries, carbon-negative concrete, atmospheric water harvesting,
portable MRI, desalination, autonomous greenhouses, modular nuclear
reactors, artificial photosynthesis, protein engineering, biodegradable
polymers, adaptive prosthetics, vertical farming, thermoelectric
materials, carbon capture materials, superconducting materials,
precision fermentation, agricultural robotics, synthetic fuels,
smart textiles, distributed manufacturing).

Required output per invention: see INVENTION_COMPILER.md
"Required output format".

Outputs go to `evidence/experiments/invention_batch_001/`:
- one YAML file per invention
- FAILURES.md recording every compiler failure, ambiguity, gap
- SUMMARY.md counting inventions produced, blueprints generated,
  failures identified

### The sequence is Build → Observe → Learn → Modify

NOT Build → Modify → Modify → Modify. The architecture is modified
only AFTER reviewing observed failures from the experiment.

### What this overrides

This freeze overrides the "Close loops, don't add modules" rule
from review #4: even loop-closing infrastructure is frozen until
the experiment is reviewed. The ONLY exception is the
close_milestone_001.py / close_milestone_002.py scripts that
record experimental outcomes from external collaborators.

## IMPLEMENTATION WORK THIS SESSION
- Run the 20-invention experiment. DO NOT modify the architecture.
- Record every output in `evidence/experiments/invention_batch_001/`.
- Record every failure in `evidence/experiments/invention_batch_001/FAILURES.md`.
- Produce SUMMARY.md counting inventions produced, blueprints
  generated, failures identified.
- The architecture is NOT modified in this session.

## CTO REVIEW #6 (commit `874ec10`) — SCAFFOLDING ≠ CLOSURE

The CTO reviewed the partially_closed / extended-Hypothesis /
agent-scaffold / milestone_001 commit (`874ec10`) and pushed back
on one specific phrasing:

> "The system is ready for that cycle."

The CTO's correction:

> "I would rewrite it as follows: 'The infrastructure required
> for that cycle now exists.' Those are not the same thing."

### Key directives

1. **Scaffolding ≠ closure.** Two distinct concepts must not be
   conflated. Scaffolding = infrastructure exists. Closure = a
   cycle has actually run AND a real-world outcome confirmed a
   prediction. Layer status values are now 4: Not started,
   Scaffolded, Partial, Closed.

2. **Honest layer status table.** The 7 layers are now honestly
   assessed:
   - Observation: Partial
   - Knowledge: Partial
   - Reasoning: Partial
   - Blueprint: Partial
   - Simulation: Partial
   - Experimentation: Scaffolded
   - Creation: Not started

3. **Canonical Hypothesis schema finalized with `id`.** The
   Hypothesis object now carries a stable `id` field (auto-
   generated hash of claim+evidence+created_at) as the first
   field, so dependencies can reference other Hypotheses
   unambiguously.

4. **Two classes of milestones.** Class A (infrastructure:
   pH, conductivity, viscosity, resistance) verify machinery.
   Class B (invention: improved electrolyte, catalyst, material,
   manufacturing process) verify the system can generate useful
   blueprints. The fifth criterion: "Does the experiment teach
   the system how to invent?" Class A satisfies the first four
   criteria but not the fifth. milestone_001 is reclassified
   as Class A. milestone_002 (Class B) is added.

5. **Belief as the emerging fifth entity.** Agent → Hypothesis
   → Experiment → Observation → Belief. The system will need to
   answer: Which hypotheses do we currently believe? How strongly?
   What evidence would change our minds? The Belief layer is
   scaffolded at `belief/`.

## IMPLEMENTATION WORK THIS SESSION
- Add `id` field to Hypothesis (auto-generated stable hash).
- Create `layer_status/` module reporting the honest
  Partial/Scaffolded/Not-started table per layer.
- Reframe milestone_001 as Class A (infrastructure).
- Add milestone_002 as Class B (invention) candidate: improved
  electrolyte composition prediction.
- Scaffold `belief/` package (declared, not implemented).
- Tests-first for all of the above.

## CTO REVIEW #5 (commit `0029759`) — UNIT OF MEASUREMENT CHANGED

The CTO reviewed the phase-transition commit (`0029759`) and
described it as "the strongest transition so far because you've
changed the unit of measurement."

Previously, success meant: more code, more modules, more features.
Now success means: more evidence, more closed loops, more validated
hypotheses.

### Key corrections

1. **Loop 2 (resurrection) is `partially_closed`, not `closed`.**
   The system can produce counterfactuals but has not demonstrated
   a real-world resurrection. Three loop states now exist:
   `open`, `partially_closed`, `closed`.

2. **Extended Hypothesis schema.** The Hypothesis object gains:
   `counterevidence`, `assumptions`, `dependencies`, `created_at`,
   `updated_at`. Existing fields preserved.

3. **Agent layer scaffolded.** Hypotheses evolve:
   `agent → hypothesis → experiment → observation → hypothesis`.
   The `agent/` package is declared, not implemented.

4. **Next milestone must be small.** Per CTO: inexpensive,
   measurable, reproducible, executable within days. The first
   closed experimentation loop on a small problem is worth more
   than a hundred additional modules.

### Loop status (review #5)

| Loop | Status | Cycles | Real-world confirmation |
|---|---|---|---|
| 1. Reconstruction | closed | 9 | Yes — historical failures are observed facts |
| 2. Resurrection | **partially_closed** | 9 | No — counterfactuals are predictions, not observations |
| 3. Forecasting | open | 0 | No — requires time |
| 4. Experimentation | open | 0 | No — requires external collaborator |
| 5. Creation | open | 0 | No — destination, not a process |

## IMPLEMENTATION WORK THIS SESSION
- Extend Hypothesis class with counterevidence, assumptions,
  dependencies, created_at, updated_at. Preserve backwards compat.
- Reclassify Loop 2 (resurrection) as partially_closed.
- Add `partially_closed` to allowed loop states across all loop
  modules.
- Scaffold `agent/` package (declared, not implemented).
- Scaffold `milestones/milestone_001/` with the first small
  milestone candidate (pH prediction of a simple mixture).
- Tests-first for all of the above.

## CTO REVIEW #4 (commit `f590661`) — PHASE TRANSITION

The CTO reviewed the expectations_satisfied reframe (commit `f590661`)
and approved the language change as "fundamentally chang[ing] the
philosophy of the system." The repository is now entering a new
phase.

> The objective is no longer to add modules.
> The objective is to **close loops**.

### 5 loops mandated

1. **Reconstruction** — humanity discovers X → system reconstructs X → compare.
   Status: partial — closed via the existing verification cycle (6 pass + 3 fail on historical failures).
2. **Resurrection** — humanity abandons X → system predicts renewed feasibility → compare.
   Status: partial — closed via the resurrection_module's per-failure counterfactuals.
3. **Forecasting** — system predicts X → time passes → compare to reality.
   Status: OPEN — requires time. Predictions can be recorded as hypotheses today.
4. **Experimentation** — system proposes blueprint → experiment runs → measurements recorded → system updates model.
   Status: OPEN — requires external collaborator to run an experiment.
5. **Creation** — system proposes blueprint → prototype built → prototype succeeds → knowledge enters ledger.
   Status: OPEN — this is the destination, not a process. The system does not honestly claim to be an invention compiler until at least one Creation loop is closed.

### 7-step sequence mandated

```text
Observation → Knowledge → Reasoning → Blueprint → Simulation → Experimentation → Creation
```

Creation is NOT a process; Creation is an OUTCOME. Conflating them
is the same error as conflating "expectations_satisfied" with
"correctness".

### claim/confidence/evidence rule

Every assertion must carry three labels:
```yaml
claim: "Portable MRI is feasible."
confidence: 0.62
evidence: [Ampere_law, Maxwell_equations, battery_energy_density, superconducting_materials]
```
No bare scalars. The scalar must be the `confidence` of an explicit
`claim`, with explicit `evidence`. This formalizes the existing
"scalars must carry evidence" rule from CTO review #1.

### Fundamental object is changing

```text
document → graph → blueprint → hypothesis
```

The Hypothesis object (a claim+confidence+evidence triple awaiting
reconciliation with reality) is the new atomic unit of the system.
Scaffolded at `hypothesis/`. Every layer output composes Hypotheses.

## IMPLEMENTATION WORK THIS SESSION
- Create `hypothesis/` package with Hypothesis class (claim/confidence/evidence + status: pending|pass|fail).
- Create `loops/` package with 5 loop contracts (reconstruction, resurrection, forecasting, experimentation, creation).
- Close Loops 1 and 2 using existing verification infrastructure (record loop closures in ledger).
- Honestly declare Loops 3, 4, 5 as OPEN with explicit next-action to close them.
- Add claim/confidence/evidence block to the chain_summary of every compiler output.
- Tests-first for all of the above.

## CTO REVIEW #3 (commit `b22cbc6`)

The CTO reviewed the depth-over-breadth commit (`b22cbc6`) and
approved the progress but pushed back on one critical point:

> "You are very close to accidentally rewarding the system for
> agreeing with your expectations rather than for predicting
> reality."

New CTO-mandated rules (encoded in INVENTION_COMPILER.md and
ANTI_ENTROPY.md):

1. **Expectations ≠ correctness.** The benchmark report must use
   "expectations_satisfied", not "PASS". The report must carry an
   `epistemic_caveat` block making the distinction explicit. Real
   correctness requires the Experimentation layer to close the loop.

2. **5-level benchmark hierarchy.** The 4-category taxonomy is
   upgraded to 5: Reconstruction, Resurrection, Forecasting,
   Synthesis, **Creation**. Creation is "can we generate a blueprint
   somebody can actually build?" — the only level that tests
   generation, not classification. The system does not honestly
   claim to be an invention compiler until at least one Creation
   case has been verified by an actual build.

3. **Knowledge spectrum rename.** The 5 domain modules (physics,
   chemistry, biology, mathematics, economics) are renamed from
   `*_module.py` to `*_knowledge_module.py` to make their position
   on the encode→reason→simulate→discover spectrum explicit. A
   module may not be renamed up the spectrum (e.g., to
   `*_reasoning_module`) until the verification cycle has recorded
   pass+fail for the new capability.

4. **5-layer architecture target.** Observation → Knowledge →
   Reasoning → Blueprint → **Experimentation** (new). The
   Experimentation layer closes the loop: predict → build → observe
   → learn. Until that loop exists, the system is an invention
   catalog, not an invention laboratory. Currently scaffolded as
   `experimentation_layer/` (empty package).

## IMPLEMENTATION WORK THIS SESSION
- Rename 5 domain modules: `physics_module.py` →
  `physics_knowledge_module.py`, etc.
- Add `stage` field to each domain module declaring its position on
  the spectrum (encode/reason/simulate/discover).
- Add Creation as 5th benchmark category in
  `benchmarks/compiler/BENCHMARK_CATEGORIES`.
- Reframe benchmark report: `PASS` → `expectations_satisfied`; add
  `epistemic_caveat` block.
- Scaffold `experimentation_layer/` package (declared, empty) with
  docstring describing the predict→build→observe→learn loop.
- Tests-first for all of the above.

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
