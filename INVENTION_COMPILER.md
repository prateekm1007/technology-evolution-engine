# INVENTION COMPILER — Master Specification

**Status:** Active directive.
**Supersedes:** the "idea generator" framing. The system is not an idea generator.
**Read this file BEFORE writing any code in this repository.**

> The objective of the system is not to generate ideas.
> The objective is to generate **blueprints**.
>
> An idea is worthless if an engineer cannot build it.
> A blueprint is valuable because it transforms possibility into execution.

---

## CTO review (commit `a3d167d`)

The CTO reviewed the first vertical slice (commit `a3d167d`) and
approved the architecture but did NOT approve the scientific claims.
This distinction matters and is now encoded as a rule.

### Approved (architecture layer)

```text
✓ Layer architecture
✓ Orchestration pipeline
✓ Evidence chain architecture
✓ Audit integration
✓ Blueprint generation framework
✓ Dependency graph framework
✓ Constraint propagation framework
✓ Simulation framework
✓ Verification framework
✓ Test framework
```

### Not yet approved (scientific reasoning layer)

```text
✗ Physics engine
✗ Chemistry engine
✗ Biology engine
✗ Economics engine
✗ Information theory engine
✗ Thermodynamics engine
✗ Control theory engine
```

The current implementations of these are MODULES, not ENGINES. They do
keyword matching against the civilization graph. They do not encode
conservation laws, reaction pathways, molecular structure models,
differential equations, or any actual science. Until they do, they
must not be called "engines." See the Naming Rule below.

### Naming rule (CTO-mandated, mandatory)

From this point forward, the system may NOT use the word `engine`
unless ALL THREE of the following conditions are satisfied:

```text
1. Explicit model.        — a formal scientific/mathematical model
                             is encoded in code, not a keyword map.
2. Empirical validation.  — the model has been tested against real
                             data and the test results are recorded
                             in the verification ledger.
3. Reproducible results.  — re-running the model with the same inputs
                             produces the same outputs, byte-exact.
```

Until then, the preferred terminology is:

```text
module
adapter
framework
layer
compiler stage
```

The single exception as of this writing is `verification_engine`,
which meets all three conditions: it has an explicit predict→observe→
reconcile model, it has been empirically validated against 9
historical failures (6 pass + 3 fail in the ledger), and it is
deterministic (seeded RNG, replayable). Everything else in
`invention_compiler/` is a MODULE.

### The "non-obvious discovery" rule

The portable MRI example is useful as a smoke test, but it is also
dangerous: everyone already knows portable MRI is plausible, so the
system may simply be reconstructing existing human knowledge. The
real test of the compiler is whether it can surface something
non-obvious — a combination or prerequisite chain a human expert
would not immediately identify. The 5-benchmark suite (below) is
designed to probe this.

### Final rule

Do not optimize for producing ideas.
Optimize for producing blueprints that scientists and engineers would respect.
That is a much higher bar.
And it is much closer to the north star.

---

## 5-benchmark suite (CTO-mandated)

The compiler must produce a defensible chain of reasoning for each of
these five test cases. "Defensible" means: the chain exists, every
layer emits non-NULL output, and the verdict matches the expected
result within one bucket.

| # | Case | Expected verdict | Why this case is interesting |
|---|---|---|---|
| 1 | Portable MRI | `feasible` | Control case. Known plausible; tests the compiler doesn't say "impossible" on a real invention. |
| 2 | Solid-state ammonia synthesis (Haber-Bosch without high T/P) | `uncertain` | Active research area. The honest answer is "we don't know yet." Tests the compiler can say "uncertain" honestly. |
| 3 | Room-temperature superconductors | `unknown` | May be physically impossible. Tests the compiler can say "unknown" without claiming feasibility. |
| 4 | Carbon-negative cement | `potentially feasible` | Already exists in early commercial form (e.g., CarbonCure, Solidia). Tests the compiler can distinguish "potentially feasible" from "feasible." |
| 5 | Artificial photosynthesis | `partially feasible` | Components work; full system doesn't yet. Tests the compiler can express partial feasibility. |

### Verdict buckets (for mapping composite feasibility → verdict)

```text
composite >= 0.75     → feasible
0.55 <= composite < 0.75 → potentially_feasible
0.40 <= composite < 0.55 → partially_feasible
0.25 <= composite < 0.40 → uncertain
composite < 0.25       → unknown
```

These buckets are priors, not calibrations. They should be recalibrated
as the verification cycle accumulates outcomes for real inventions.

The benchmark runner is at `scripts/run_compiler_benchmarks.py` and
produces `evidence/reports/compiler_benchmark_report.json`. A case is
"PASS" if the verdict matches expected OR is within one bucket. A case
is "FAIL" if the verdict is more than one bucket away from expected.

---

## New principle

```text
Idea → Hypothesis → Theory → Architecture → Blueprint → Prototype → Product
```

The system is responsible for everything up to the blueprint stage.
The user (or downstream engineers) take it from blueprint → prototype → product.

---

## The final output shape

The final output is NOT:

```json
{
  "idea": "Portable MRI",
  "technical_feasibility": 0.82
}
```

The final output IS a chain of reasoning:

```text
Problem definition
        ↓
Scientific principles
        ↓
Mathematical formulation
        ↓
Physical constraints
        ↓
Chemical constraints
        ↓
Engineering constraints
        ↓
Dependency graph
        ↓
Alternative architectures
        ↓
Simulation
        ↓
Materials specification
        ↓
Manufacturing pathway
        ↓
Regulatory pathway
        ↓
Economic model
        ↓
Experimental protocol
        ↓
Prototype specification
        ↓
Invention blueprint
```

That is a fundamentally different problem than "find an idea."

---

## Required output structure — 11 layers

Every invention the system produces MUST emit all 11 layers.
A layer that returns `null` is acceptable (we don't always know);
a layer that is silently skipped is a bug.

### Layer 0 — Opportunity definition

```yaml
problem:
domain:
motivation:
market:
constraints:
time_horizon:
```

### Layer 1 — First-principles analysis

```yaml
physics:
chemistry:
biology:
mathematics:
economics:
information_theory:
thermodynamics:
control_theory:
```

### Layer 2 — Dependency graph

```yaml
prerequisites:
adjacent_technologies:
required_materials:
required_infrastructure:
missing_capabilities:
regulatory_constraints:
```

### Layer 3 — Scientific formulation

```yaml
governing_equations:
boundary_conditions:
assumptions:
failure_modes:
optimization_targets:
```

### Layer 4 — Engineering architecture

```yaml
subsystems:
interfaces:
inputs:
outputs:
tolerances:
energy_requirements:
computational_requirements:
```

### Layer 5 — Simulation layer

```yaml
monte_carlo:
sensitivity_analysis:
stress_testing:
parameter_ranges:
```

### Layer 6 — Manufacturing layer

```yaml
materials:
suppliers:
tooling:
assembly:
quality_control:
scaling_constraints:
```

### Layer 7 — Economic layer

```yaml
capex:
opex:
cost_curve:
market_size:
adoption_model:
```

### Layer 8 — Experimental layer

```yaml
hypothesis:
experiments:
measurements:
success_criteria:
failure_criteria:
```

### Layer 9 — Prototype layer

```yaml
prototype_v1:
prototype_v2:
prototype_v3:
timeline:
```

### Layer 10 — Final blueprint

```yaml
blueprint:
patent_landscape:
technical_risks:
commercial_risks:
recommended_actions:
```

---

## Required modules (renamed per CTO review)

```text
physics_module/
chemistry_module/
biology_module/
mathematics_module/
economics_module/

constraint_module/
simulation_module/
dependency_module/
resurrection_module/
analogy_module/

blueprint_module/
prototype_module/
verification_engine/    <- the one module that meets the "engine" bar:
                          explicit model + empirical validation +
                          reproducible results
```

A module that currently does keyword matching may NOT be renamed
back to "engine" until it satisfies the three conditions in the
Naming Rule section above.

### Module → Layer mapping

The mapping is approximate; some modules span multiple layers.

| Module | Feeds layer(s) | Status as of commit `e97c718` |
|---|---|---|
| `physics_engine/` | Layer 1 (physics) | Not yet implemented |
| `chemistry_engine/` | Layer 1 (chemistry) | Not yet implemented |
| `biology_engine/` | Layer 1 (biology) | Not yet implemented |
| `mathematics_engine/` | Layer 1 (mathematics), Layer 3 (governing equations) | Not yet implemented |
| `economics_engine/` | Layer 1 (economics), Layer 7 (economic layer) | Not yet implemented |
| `constraint_engine/` | Layer 2 (constraints), Layer 4 (tolerances) | Partial — `product/scoring/feasibility.py` carries constraint weights |
| `simulation_engine/` | Layer 5 (simulation layer) | Partial — `web/backend/adapters/oracle_deep.py` runs equilibrium simulation |
| `dependency_engine/` | Layer 2 (dependency graph) | Partial — `product/lineage/mapper.py` walks prerequisite chains |
| `resurrection_engine/` | Layer 2 (resurrection candidates) | Partial — `engine/resurrection.py` exists as a stub; `evidence/failures/*.json` provides ground truth |
| `analogy_engine/` | Layer 0 (cross-domain analogies) | Partial — `product/discovery/synthesizer.py` finds cross-domain pairs |
| `blueprint_engine/` | Layer 10 (final blueprint) | Stub — `engine/blueprint.py` exists |
| `prototype_engine/` | Layer 9 (prototype layer) | Not yet implemented |
| `verification_engine/` | All layers (Law 8 enforcement) | Implemented — `scripts/run_verification_cycle.py` + `scripts/enforce_law8.py` |

---

## Required rule

The system may NEVER output:

> "This is a good idea."

The system MUST output:

> "Here is the complete chain of reasoning required to build this."

Concretely: no module may return a scalar "score" without also returning the
evidence chain that produced the score. The `FeasibilityScorer` in
`product/scoring/feasibility.py` is the reference pattern — it returns the
score AND the evidence block AND the falsification criteria. Every new
module should follow the same pattern.

---

## Ultimate question

The final question the system must answer is NOT:

> What is the next idea?

The final question IS:

> What is the next invention that humanity is capable of building, and
> what exact sequence of steps would allow someone to build it?

That is the destination toward which the entire repository should converge.

---

## Relationship to the existing Constitution and Governance

This file does NOT override CONSTITUTION.md. Law 8 still applies:
a blueprint is a *prediction* that an engineer can build the thing.
Until at least one blueprint has been built and the build outcome
recorded as pass or fail in `data/ledger/predictions.jsonl`, every
blueprint the compiler produces is stamped `integrated`, not `verified`.

This file DOES supersede the "Evidence Phase Roadmap" framing in
`EVIDENCE_PHASE.md`. The evidence phase is now a means, not an end —
the end is a working invention compiler.

---

## What this changes about how we work

1. Every PR must move us closer to the invention-compiler destination.
   If a change does not advance one of the 11 layers or 13 modules,
   it is entropy and should be rejected at review.

2. The 11-layer output structure is the contract. New modules must
   declare which layer they feed and emit that layer's schema.

3. A module that returns only a number is a bug. Every output must
   carry its evidence chain, its assumptions, and its falsification
   criteria. This is the Law 8 honesty rule applied at the module
   level.

4. The `verification_engine/` is the loop that closes the whole
   system. It already exists as `scripts/run_verification_cycle.py`
   and `scripts/enforce_law8.py`. It should be promoted to a
   first-class module and wired across every layer's output.
