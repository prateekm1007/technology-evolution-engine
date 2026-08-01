# INVENTION COMPILER — Master Specification

**Status:** ARCHITECTURE FROZEN. Operating under the Maestro Modification Loop (v1.0).
**Read this file BEFORE writing any code in this repository.**
**Also read CONTRIBUTING.md before every commit — it's the pre-commit checklist.**

> The objective of the system is not to generate ideas.
> The objective is to generate **blueprints**.
>
> An idea is worthless if an engineer cannot build it.
> A blueprint is valuable because it transforms possibility into execution.

---

## MAESTRO MODIFICATION LOOP (v1.0)

This is **not** a software-development loop.
It is an **epistemic loop**.

The question is no longer:

> What should we build?

The question is:

> What did reality teach us, and how should the system change because of it?

### The 10 phases

```text
PHASE 0 — FREEZE
    No architecture changes. No new modules. No new abstractions.
    No new layers. Only observation.

PHASE 1 — EXECUTION
    Run N inventions through the compiler.

PHASE 2 — OBSERVATION
    Record: outputs, failures, scores, assumptions, counterevidence,
    collisions, blueprint quality. DO NOT FIX ANYTHING.

PHASE 3 — GAP ANALYSIS
    Rank every failure by: severity, frequency, impact, locality,
    measurability.

PHASE 4 — SELECTION
    Select ONE gap. Never select two unrelated gaps. Never modify
    the entire system. (Two gaps may be selected together ONLY if
    they describe the same failure — e.g., Gap 2 + Gap 7.)

PHASE 5 — HYPOTHESIS
    Write a Hypothesis (claim/confidence/evidence/counterevidence/
    assumptions/dependencies) predicting what the modification will
    achieve.

PHASE 6 — MODIFICATION
    Modify ONE component. Everything else remains frozen.

PHASE 7 — RE-EXECUTION
    Run exactly the same inventions. No substitutions. No removals.
    No additions.

PHASE 8 — DELTA ANALYSIS
    Measure: before, after, difference.

PHASE 9 — LEDGER UPDATE
    Record: modification, evidence, observations, failures,
    consequences.

PHASE 10 — DECISION
    Did reality support the hypothesis?
    YES → preserve the modification.
    NO → revert the modification.
    PARTIALLY → investigate further.

REPEAT
```

### Canonical objects

```text
Observation
      ↓
Knowledge
      ↓
Hypothesis
      ↓
Blueprint
      ↓
Experiment
      ↓
Observation
```

### Current loop state

| Gap | Phase | Status |
|---|---|---|
| Gap 1 (identical scoring) | 10 — DECISION | YES — preserved. 9→18 unique scores, 8→2 max collisions. |
| Gap 2+7 (arbitrary deps + weak causal graph) | 10 — DECISION | YES — preserved. 0→most non-zero causal classifications. |
| Gap 3 (non-buildable blueprints) | 3 — GAP ANALYSIS → 4 | Identified as Critical/next. Not yet selected for modification. |

### Loop history

- **Cycle 1 (Gap 1):** commit `bdfca58` (observe) → `194089d` (modify simulation_module.py + re-execute batch_002 + delta). Decision: YES.
- **Cycle 2 (Gap 2+7):** commit `194089d` (learn) → `a701d77` (modify dependency_module.py + re-execute batch_003 + delta). Decision: YES.
- **Cycle 3 (Gap 3):** commit `a701d77` (learn) → `d3cb446` (modify blueprint_module.py + re-execute batch_004 + delta). Decision: YES.
- **Cycle 4 (Gap 4):** commit `d3cb446` (learn) → `d76bea4` (modify orchestrator.py + re-execute batch_005 + delta). Decision: YES.
- **Cycle 5 (Gap 5):** commit `d76bea4` (learn) → `8ce8637` (modify prototype_module.py + re-execute batch_006 + delta). Decision: YES.
- **F-016 fix:** commit `8ce8637` → `e54ce03` (repair corrupted historian/*.json + mode4_constraint_leverage.json). Not a Maestro cycle — a critical data-integrity fix.

### External auditor's verified findings (commit `e54ce03`)

An external auditor independently verified three key claims:

1. **0/577 graph nodes have constraints** — Law 2's constraint surface is unimplemented on the actual seed graph. The invention_compiler computes constraints for its test problem but never writes them back.
2. **Convergence detection doesn't exist** — every "converge" mention is a docstring honestly saying "does not yet do that."
3. **invention_compiler is a parallel vertical slice** — it reads the graph but never writes back. Knowledge accumulates in System B without propagating to System A.

### The separation problem

```text
System A (original architecture)
    ├── civilization_graph.json (577 nodes, 0 constraints)
    ├── historian/*.json (was corrupted, now repaired)
    ├── ledger/predictions.jsonl (was corrupted, now clean)
    └── engine/*.py (stubs: Historian 17 lines, Resurrection 18 lines)

System B (invention compiler)
    ├── invention_compiler/ (15 modules, 4000+ lines)
    ├── benchmarks/compiler/ (6 cases)
    ├── loops/ (5 loops, 2 closed)
    └── hypothesis/ (the Hypothesis class)
```

Knowledge accumulates in System B without propagating back to System A. This is the most important architectural finding in the audit history.

### CTO's 5-phase roadmap (canonical forward plan)

Per the CTO and external auditor, the next phases are:

**Phase 1 — Close the loop.** ✅ DONE — first forward-looking prediction
(`phase1_aprm_selective_emitters_001`) written to ledger with resolution
date 2027-06-01. (9 retrospective cycles existed before this; the Phase
1 entry is the first forward-looking one, not the first overall.)

**Phase 2 — Unify representations.** ✅ DONE — constraints propagated
into the 577-node graph (0/577 → 577/577). Auditor verified. Caveat:
constraint values are priors with no zero entries (F-024), so Oracle
binding_share is still uniform. Real variation requires Phase 3.

**Phase 3 — Ingest external evidence.** ← CURRENT

Per the CTO directive:
- Do NOT build another framework. No new modules unless reality forces it.
- Objective: connect the existing system to external evidence.
- Allowed source modifications: `product/ingestion/*`,
  `civilization_graph.json`, `historian/*`, `ledger/*`, `tests/*`.
- Everything else frozen.

**Auditor's Phase 3 execution roadmap (verified, canonical):**

Step 0 — Fix F-001 before ingesting anything real. The parser only
handles claims-formatted trigger phrases; real patent text won't always
match. Test against 2-3 real patent abstracts from Google Patents before
picking the full 10-20 list. This is the load-bearing prerequisite.

Step 1 — Close the two contract gaps the current tests don't cover:
  (a) Add a "historian reconstruct source" test (currently zero coverage).
  (b) Convert graph-write tests from shape-checks into actual writes
      against a scratch copy of civilization_graph.json with assertion
      on resulting node/edge count and provenance fields.

Step 2 — Ingest 3 real patents first, not 10-20. Prove the pipeline
end-to-end (real patent text → parser → graph write → provenance in
node → historian can point back to source) on a small number before
scaling. Failures must be cheap to diagnose.

Step 3 — Build paper_parser.py against one real paper. One arXiv
abstract, prove equations/assumptions/limitations extraction works
(even shallowly) before committing to 10-20.

Step 4 — Scale to 10-20 patents / 10-20 papers once Steps 2-3 are
proven. Let constraint counts move 0→20→50→100/577 as a byproduct
of real ingestion, not a separate migration script. F-024 is explicit
that priors don't count as this metric moving.

Step 5 — Close F-022 (cemetery fields missing) while touching the
graph-write path, since it's the same code region.

**Phase 3 success criteria (concrete):**

Success is NOT "new module added." Success is:
- Real patent ingested (at least 3, target 10-20)
- Real paper ingested (at least 1, target 10-20)
- Real constraints extracted (target: ≥20/577 with real, not prior,
  constraint values traceable to a source)
- Real provenance preserved (every extracted item carries source,
  source_type, title, authors, publication_date, doi/patent_number,
  confidence, extracted_by, timestamp)
- Real graph updated (nodes/edges added, not just shape-checked)
- Historian can reconstruct the source (test coverage)

**Phase 3 reporting format:**
```
WHAT WAS MODIFIED
WHAT WAS OBSERVED
WHAT CHANGED
WHAT FAILED
WHAT REMAINS UNKNOWN
```

**Phase 4 — Define convergence mathematically.** Only after the
definition exists should implementation begin.

**Phase 5 — Audience specialization.** Only after Phases 1-4 give the
underlying system something true to say to any audience.

### The shift

Early in the project, success meant building modules.
Now success means closing loops.

That is a much harder objective, but it is also much closer to the mission.

---

## CEO DIRECTIVE — FREEZE ARCHITECTURE (commit `0c6d5d7`)

Effective immediately:

- No new layers.
- No new modules.
- No new packages.
- No new frameworks.
- No new abstractions.

Use only what already exists.

### LEARN step (post-experiment gap analysis, commit `bdfca58`)

After running the 20-invention experiment (commit `bdfca58`), 7
gaps were observed. The CEO/CTO classified them:

| Gap | Severity | Frequency | Impact |
|---|---|---|---|
| Identical scoring (Gap 1) | Critical | High (11/20) | High |
| Arbitrary dependencies (Gap 2) | Critical | High | High |
| Non-buildable blueprints (Gap 3) | Critical | High | High |
| Missing counterevidence (Gap 4) | High | High (20/20) | High |
| Template plans (Gap 5) | Medium | High | Medium |
| Chemical differentiation (Gap 6) | Medium | Medium | Medium |
| Weak causal graph (Gap 7) | Critical | High | High |

### MODIFY step — pick ONE gap (commit `bdfca58` → next)

Per the CEO: "Do not solve all seven problems simultaneously.
Pick one. Fix it. Run all twenty inventions again. Observe what
changes. Only then move to the next one."

**Gap selected: Gap 1 (identical scoring).**

Why Gap 1 first:
- Critical severity (highest priority).
- Highest frequency among critical gaps (11/20 candidates affected).
- Localized to ONE module (`simulation_module.py`) — does not
  require touching the dependency_module, blueprint_module, or
  any other module. This honors the "pick one" rule strictly.
- Most measurable impact across all 20 candidates — the delta
  report will show which composites changed and by how much.
- Does not require deep architectural changes; the existing
  complexity-penalty mechanism in simulation_module can be
  extended with additional problem-specific signals.

**The fix (Gap 1 only):**

The simulation_module currently uses keyword-based complexity
penalties. 11/20 candidates produce composite=0.5777 because they
all have 5 applicable_laws and none of the special keywords
(superconduct/ambient/ammonia/photosynth/etc.). The fix: use
MULTIPLE problem-specific signals, not just keyword presence:

- applicable_law_count (existing)
- governing_equations_count (NEW — more equations = harder)
- failure_modes_count (NEW — more failure modes = harder)
- missing_capabilities_count (NEW — more missing = harder)
- prerequisite_chain_depth (NEW — deeper chain = harder)
- domain complexity multiplier (NEW — e.g., superconductivity
  domain gets extra penalty)

Combining these signals produces different composites for
different problems, even when the keyword signatures are similar.

**What the fix does NOT touch:**

- dependency_module (Gap 2, Gap 7) — unchanged
- blueprint_module (Gap 3) — unchanged
- orchestrator (Gap 4) — unchanged
- prototype_module (Gap 5) — unchanged
- chemistry_knowledge_module (Gap 6) — unchanged

Only `simulation_module.py` is modified. This is the strict
"pick one" rule.

### LEARN step (Gap 1 delta analysis, commit `194089d`)

The Gap 1 fix succeeded:

| Metric | Before (batch_001) | After (batch_002) |
|---|---|---|
| Unique scores | 9 | 18 |
| Maximum collisions | 8 | 2 |
| Minimum score | 0.3678 | 0.2592 |
| Maximum score | 0.6827 | 0.5777 |

The portable MRI benchmark case moved from `potentially_feasible` to
`partially_feasible`. Per the CEO/CTO: this is a SUCCESS, not a
regression. The system changed its opinion because new evidence
entered the computation (multi-signal complexity). Tuning the
penalty to make the case pass would be the "rewarding agreement
with priors" anti-pattern.

### CTO observation on Gap 1 (commit `194089d`)

The CTO noted that the fix is still aggregation (w₁x₁ + w₂x₂ + ...),
not causation. Eventually the relationships should look like:

```text
physics constraints → dependency graph → failure modes →
    manufacturing constraints → economic constraints → feasibility
```

That is causality, not aggregation. This is recorded for a future
iteration. The Gap 1 fix did not move to causality — it added more
signals to the aggregation, which is a strictly-better aggregation
but not yet causation.

### MODIFY step — pick ONE (combined) gap (commit `194089d` → next)

Per the CEO: "Pick one. Fix it. Run all twenty inventions again.
Observe what changes. Only then move to the next one."

Per the CTO recommendation (commit `194089d`): "Pick Gap 2 and Gap 7
together, because they are really the same problem."

**Gap selected: Gap 2 + Gap 7 (arbitrary dependency selection + weak causal graph).**

Why Gap 2 + Gap 7 next:
- Critical priority (highest).
- Same problem, not two problems: the dependency_module picks an
  arbitrary target_node_id when the invention is not in the graph,
  which produces all-zero causal classifications. Fixing the target
  selection fixes both gaps simultaneously.
- "Without causal structure, you cannot have: prerequisites, counter-
  facts, resurrection, forecasting, blueprints, experimentation.
  Everything depends upon it." (CTO)
- Localized to ONE module (`dependency_module.py`) — the "pick one"
  rule is honored (Gap 2 + Gap 7 are one problem in one module).

**The fix (Gap 2 + Gap 7 only):**

The dependency_module's `_pick_target` method currently picks the
first system node in the matching domain, or the first system node
period. This is arbitrary for novel inventions. The fix replaces
arbitrary selection with **problem-aware relevance matching**:

1. Score every node in the graph by relevance to the problem:
   - domain match (highest weight)
   - constraint keyword overlap (medium weight)
   - problem-text keyword overlap (low weight)
2. Pick the highest-scoring node as the target.
3. If the highest score is below a threshold, declare the invention
   "novel relative to the graph" — this is informative, not a failure.
4. The causal classification (necessary/sufficient/contributing) then
   operates on the relevance-matched target, producing non-zero
   classifications when relevant prerequisites exist.

What the fix does NOT do:
- It does NOT add nodes to the graph (that would be modifying the
  observation layer, which is frozen).
- It does NOT change the causal classification heuristic itself
  (Gap 7's "weak causal graph" is fixed by giving the heuristic a
  real target to work with, not by changing the heuristic).
- It does NOT touch any other module.

**What the fix does NOT touch:**

- simulation_module.py (Gap 1 — just fixed, leave alone)
- blueprint_module.py (Gap 3)
- orchestrator (Gap 4)
- prototype_module.py (Gap 5)
- chemistry_knowledge_module.py (Gap 6)
- physics/mathematics/economics/constraint/resurrection/etc.

Only `dependency_module.py` is modified. Gap 2 + Gap 7 are one
problem in one module.

### Updated priority table (per CTO review, commit `194089d`)

| Gap | Priority |
|---|---|
| Gap 2 + Gap 7 (this iteration) | Critical |
| Gap 3 (next) | Critical |
| Gap 4 | High |
| Gap 6 | Medium |
| Gap 5 | Medium |

Gap 1 is closed (delta reviewed). The remaining gaps are addressed
one at a time, each with its own modify → observe → learn cycle.

### Build → Observe → Learn → Modify (NOT Build → Modify → Modify → Modify)

The sequence is now:

```text
Build (commits up to bdfca58)
   ↓
Observe (20-invention experiment, commit bdfca58)
   ↓
Learn (gap analysis, commit 194089d governor files)
   ↓
Modify (Gap 1 fix in simulation_module.py, commit 194089d)
   ↓
Observe (batch_002 re-run + DELTA.md, commit 194089d)
   ↓
Learn (Gap 1 delta analysis — THIS section)
   ↓
Modify (Gap 2+7 fix in dependency_module.py — NEXT commit)
   ↓
Observe (batch_003 re-run + DELTA.md)
   ↓
Learn (Gap 2+7 delta analysis)
   ↓
Modify (Gap 3 OR another, ONLY after delta review)
```

NOT:

```text
Build
   ↓
Modify
   ↓
Modify
   ↓
Modify
   ↓
Modify
```

The architecture may only be modified AFTER reviewing observed
failures from running the compiler against real problems. Modifying
the architecture in the absence of observed failures is entropy.

### Required experiment: 20 candidate inventions

Run the compiler against 20 candidate inventions:

1. solid-state batteries
2. carbon-negative concrete
3. atmospheric water harvesting
4. portable MRI systems
5. desalination systems
6. autonomous greenhouses
7. modular nuclear reactors
8. artificial photosynthesis
9. protein engineering systems
10. biodegradable polymers
11. adaptive prosthetics
12. vertical farming systems
13. thermoelectric materials
14. carbon capture materials
15. superconducting materials
16. precision fermentation
17. agricultural robotics
18. synthetic fuels
19. smart textiles
20. distributed manufacturing

### Required output format (per invention)

```yaml
problem:
domain:
hypothesis:

physical_laws:
chemical_principles:
mathematical_formulation:

constraints:
dependencies:
assumptions:

architecture:
simulation:

prototype_plan:
experimental_plan:

failure_modes:
counterevidence:

confidence:

final_blueprint:
```

### Most important rule

Do not modify the system while running these experiments.
Record every failure.
Only after reviewing the failures should the architecture change.

---

## North star (refined per CTO review #2)

```text
Search engines organize information.
Recommendation engines organize preferences.
Prediction engines organize probabilities.
Invention engines organize possibilities.
```

That is the precise description of what we are trying to build.

---

## CTO review #6 (commit `874ec10`) — scaffolding ≠ closure

The CTO reviewed the partially_closed / extended-Hypothesis /
agent-scaffold / milestone_001 commit (`874ec10`) and pushed back
on one specific phrasing:

> "The system is ready for that cycle."

The CTO's correction:

> "I would rewrite it as follows: 'The infrastructure required for
> that cycle now exists.' Those are not the same thing."

### Scaffolding vs closure rule (CTO-mandated)

From this commit forward, two distinct concepts must not be
conflated:

- **Scaffolding** — the infrastructure (classes, packages, docstrings,
  spec files, ledger interfaces) exists. The system CAN run a cycle
  in principle. No cycle has actually run.
- **Closure** — at least one cycle has actually run, the prediction
  was tested by an external observation, and the outcome was
  recorded in the ledger. The system HAS LEARNED something.

A scaffolded loop is `open` or `partially_closed`. A closed loop
requires a real-world outcome. Scaffolding is necessary but not
sufficient for closure.

The honest language rule: when reporting status, use "the
infrastructure required for X now exists", NOT "the system is
ready for X". Readiness is a stronger claim than infrastructure-
existence.

### Layer status (CTO-mandated, honest)

| Layer | Status |
|---|---|
| Observation | Partial |
| Knowledge | Partial |
| Reasoning | Partial |
| Blueprint | Partial |
| Simulation | Partial |
| Experimentation | Scaffolded |
| Creation | Not started |

The status values are:

- **Not started** — no infrastructure exists for this layer.
- **Scaffolded** — infrastructure exists (classes, packages,
  docstrings) but no real-world cycle has run through it.
- **Partial** — infrastructure exists AND at least one cycle has
  run on historical/synthetic data, but no real-world outcome has
  confirmed a prediction.
- **Closed** — infrastructure exists AND at least one real-world
  cycle has confirmed a prediction.

The current state: Layers 1-5 are Partial (compiler runs, but
no real-world confirmation); Layer 6 (Experimentation) is
Scaffolded (infrastructure exists, no cycle run); Layer 7
(Creation) is Not started.

### Canonical Hypothesis schema (CTO-mandated, finalized)

Per CTO review #5, the Hypothesis object was extended. Per CTO
review #6, the canonical schema now includes `id` as the first
field:

```yaml
id:               # stable identifier (NEW, review #6)
claim:
confidence:
evidence:
counterevidence:
assumptions:
dependencies:    # references other Hypotheses by id
status:
created_at:
updated_at:
```

The `id` field is required so dependencies can reference other
Hypotheses unambiguously. IDs are auto-generated stable hashes
of (claim + evidence + created_at) so they are deterministic per
Law 7 (reproducibility).

### Two classes of milestones (CTO-mandated)

The CTO's criticism of milestone_001 (pH prediction):

> "A pH measurement may validate the experimental loop, but it
> may not validate the invention loop."

The CTO therefore defined two classes of milestones:

| Class | Verifies | Examples |
|---|---|---|
| A — infrastructure milestones | The machinery works | pH prediction, thermal conductivity, viscosity, electrical resistance |
| B — invention milestones | The system can generate useful blueprints | improved electrolyte compositions, improved catalyst combinations, new material combinations, modified manufacturing processes |

The most important criterion for any milestone:

```text
Does the experiment teach the system how to invent?
```

Class A milestones do NOT teach the system how to invent — they
verify that the experimentation loop works mechanically. Class B
milestones DO teach the system how to invent — they test whether
the system's blueprints would actually improve a real invention.

The honest milestone framework rule: every milestone must declare
its class (A or B). Class A milestones can close Loop 4
(experimentation). Class B milestones can close BOTH Loop 4 AND
contribute to Loop 5 (creation).

milestone_001 (pH prediction) is now declared as Class A. A
Class B candidate (milestone_002) is added at
`milestones/milestone_002/` — an improved electrolyte
composition prediction. Class B milestones have a higher bar:
they must propose something the system claims is an IMPROVEMENT
over an existing baseline, not just a measurement.

### Belief as the emerging fifth entity (CTO observation)

The CTO observed that the system now has four entities:

```text
Agent → Hypothesis → Experiment → Observation
```

And a fifth is emerging:

```text
Belief
```

Because the system will eventually need to answer:

- Which hypotheses do we currently believe?
- How strongly do we believe them?
- What evidence would change our minds?

That is a very different problem from storing documents. A Belief
is the system's current committed position on a hypothesis,
given all observed evidence to date. It is updated by Bayes (or a
similar rule) as observations accumulate. A Hypothesis without a
Belief is just a stored assertion; a Hypothesis WITH a Belief is a
live claim the system is committed to.

The Belief layer is scaffolded at `belief/` (declared, not
implemented). Its first concrete deliverable: a function that,
given a Hypothesis and all related observations, returns a Belief
(confidence updated by evidence).

---

## CTO review #5 (commit `0029759`) — the unit of measurement has changed

The CTO reviewed the phase-transition commit (`0029759`) and
described it as "the strongest transition so far because you've
changed the unit of measurement."

Previously, success meant:

```text
more code
more modules
more features
```

Now success means:

```text
more evidence
more closed loops
more validated hypotheses
```

### Loop 2 is partially_closed, not closed (CTO correction)

The CTO pushed back on Loop 2 (resurrection) being marked
`closed=True`. The argument that it's closed — system identifies
historical failures, generates counterfactuals, writes to ledger —
is sound *as infrastructure*. But the system has NOT demonstrated
that one of those resurrected ideas actually became feasible in the
real world.

Per the CTO directive, Loop 2 is reclassified:

```text
status = partially_closed
```

This introduces a third status value beyond `closed`/`open`:
`partially_closed`. A loop is `partially_closed` when the
infrastructure exists and has been exercised, but no real-world
outcome has confirmed the system's prediction.

(Per CTO review #6 above, this is sharpened: `partially_closed`
= scaffolded + cycles run on historical data; `closed` = real-
world confirmation. Scaffolding ≠ closure.)

| Loop | Status (review #4) | Status (review #5) | Status (review #6) |
|---|---|---|---|
| 1. Reconstruction | closed | closed | closed |
| 2. Resurrection | closed | partially_closed | partially_closed |
| 3. Forecasting | open | open | open |
| 4. Experimentation | open | open | open (scaffolded, no cycle run) |
| 5. Creation | open | open | open (not started) |

### Extended Hypothesis schema (CTO-mandated, finalized in review #6)

The CTO observed that the Hypothesis object is the correct
abstraction and will "almost certainly survive every future
architectural revision." The schema is extended (review #5) and
finalized (review #6) with `id`:

```yaml
id:               # stable identifier (review #6)
claim:           # falsifiable statement
confidence:      # scalar in [0,1]
evidence:        # named inputs supporting the claim
counterevidence: # named inputs that would weaken the claim (review #5)
assumptions:     # what the claim assumes to be true (review #5)
dependencies:    # other Hypothesis IDs this one depends on (review #5)
status:          # pending | pass | fail
created_at:      # ISO8601 UTC
updated_at:      # ISO8601 UTC, updated on reconcile() (review #5)
```

### Hypotheses evolve — there's an agent underneath (CTO observation, refined in review #6)

The CTO observed that the current model is:

```text
hypothesis → loop → ledger
```

But eventually it becomes:

```text
agent → hypothesis → experiment → observation → hypothesis
```

(Per review #6, this is further extended to:)

```text
agent → hypothesis → experiment → observation → belief → hypothesis
```

Hypotheses are not static. They evolve. The agent layer is
scaffolded at `agent/` (declared, not implemented). The Belief
layer is scaffolded at `belief/` (declared, not implemented).

### The next milestone must be small (CTO-mandated, refined in review #6)

> Do not attempt to invent a room-temperature superconductor.
> Instead, choose a problem that satisfies four conditions:
>   - inexpensive
>   - measurable
>   - reproducible
>   - executable within days rather than months

(Per review #6, a fifth criterion is added:)

>   - Does the experiment teach the system how to invent?

Class A milestones satisfy the first four but not the fifth.
Class B milestones satisfy all five. The first Class B milestone
is worth more than any number of Class A milestones.

---

## CTO review #4 (commit `f590661`) — phase transition

The CTO reviewed the expectations_satisfied reframe (commit `f590661`)
and approved the language change as "fundamentally chang[ing] the
philosophy of the system." The repository is now entering a new phase.

### Phase transition directive

The objective is no longer to add modules.
The objective is to **close loops**.

Every loop below has three stages: propose, observe, reconcile. A
loop is "closed" when at least one cycle has completed and the
reconciliation has been recorded in the verification ledger.

(Per CTO review #5 above, "closed" is sharpened: a loop is
`partially_closed` when infrastructure exists but no real-world
outcome confirms the prediction; `closed` requires a real-world
outcome.)

### The 7-step sequence (CTO-mandated, replaces the 5-layer architecture)

```text
Observation
        ↓
Knowledge
        ↓
Reasoning
        ↓
Blueprint
        ↓
Simulation
        ↓
Experimentation
        ↓
Creation
```

Creation is NOT a process. Creation is an OUTCOME. The first 6
steps are processes; the 7th is the result of those processes
succeeding in the real world. Conflating them is the same class
of error as conflating "expectations_satisfied" with "correctness".

### The 5 loops (CTO-mandated)

```text
Loop 1 — reconstruction
    humanity discovers X
            ↓
    system reconstructs X
            ↓
    compare results

Loop 2 — resurrection
    humanity abandons X
            ↓
    system identifies missing prerequisites
            ↓
    system predicts renewed feasibility
            ↓
    compare results

Loop 3 — forecasting
    system predicts X
            ↓
    time passes
            ↓
    compare prediction against reality

Loop 4 — experimentation
    system proposes blueprint
            ↓
    experiment is executed
            ↓
    measurements are recorded
            ↓
    system updates model

Loop 5 — creation
    system proposes blueprint
            ↓
    prototype is built
            ↓
    prototype succeeds
            ↓
    knowledge enters the ledger
```

Each loop is implemented as a module in `loops/`. The first three
loops (1, 2, 3) can be partially closed using existing infrastructure
(verification cycle, resurrection counterfactuals, benchmark suite).
Loops 4 and 5 require external collaboration (someone must run an
experiment or build a prototype) and are honestly declared as OPEN
until that happens.

### The claim/confidence/evidence rule (extended in CTO review #5)

From this point forward, every assertion the system emits must
carry the extended Hypothesis schema:

```yaml
claim: "Portable MRI is feasible."
confidence: 0.62
evidence:
  - Ampere_law
  - Maxwell_equations
  - battery_energy_density
counterevidence:        # NEW (review #5)
  - superconducting_materials_shortage
assumptions:            # NEW (review #5)
  - "regulatory pathway is FDA 510(k)"
  - "permanent magnet field strength sufficient"
dependencies:           # NEW (review #5) — other Hypotheses this one depends on
  - hypothesis_battery_density_001
status: pending
created_at: 2026-08-01T...
updated_at: 2026-08-01T...
```

- `claim` is a falsifiable statement.
- `confidence` is a scalar in [0, 1] representing the system's
  belief in the claim, prior to observation.
- `evidence` is a list of named inputs that produced the claim.
  Empty evidence means the claim is unsupported; confidence should
  be 0 in that case.
- `counterevidence` is a list of named inputs that would weaken
  the claim. Empty counterevidence is allowed (the claim has no
  known counter-signals).
- `assumptions` is a list of preconditions the claim makes.
- `dependencies` is a list of Hypothesis IDs this Hypothesis
  depends on. If a dependency is reconciled to `fail`, this
  Hypothesis should be re-examined.
- `status` is `pending` (default), `pass`, or `fail`.
- `created_at` and `updated_at` are ISO8601 UTC timestamps.

No layer's output may emit a bare scalar ("feasibility: 0.82") —
that scalar must be the `confidence` of an explicit `claim`, with
explicit `evidence`.

### The fundamental object is changing (CTO observation, refined in review #5)

Originally the system's fundamental object was:

```text
document
```

Then it became:

```text
graph
```

Then:

```text
blueprint
```

The CTO suspects it will eventually become:

```text
hypothesis
```

(Implemented in commit `0029759`.) Per review #5, the hypothesis
itself is not the terminal object — it is one stage in an
agent-driven evolution loop:

```text
agent → hypothesis → experiment → observation → hypothesis
```

Hypotheses are not static. They evolve. The agent layer
(scaffolded at `agent/`) is the next substrate.

---

## CTO review #3 (commit `b22cbc6`)

The CTO reviewed the depth-over-breadth commit (`b22cbc6`) and
approved the progress but pushed back on one critical point:

> "You are very close to accidentally rewarding the system for
> agreeing with your expectations rather than for predicting
> reality. That's a dangerous distinction."

### Epistemic caveat (CTO-mandated)

The benchmark suite currently asks: "did the compiler produce the
verdict we expected?" That is NOT the same as asking "did the
compiler produce a verdict that matches reality?"

If we repeatedly tune the scoring system until it produces the
answers we expected all along, we risk building a machine that
**reproduces our beliefs** rather than **discovers new truths**.

This is especially dangerous because the north star is not
classification — it is invention. A classifier that agrees with
human experts is useless if the goal is to surface combinations
human experts would not have considered.

### New rule: expectations ≠ correctness

From this commit forward, the benchmark report MUST use the language
"expectations_satisfied" rather than "PASS". Those are different
things:

- "PASS" implies correctness.
- "expectations_satisfied" is honest about what was actually tested:
  did the system's output match what the benchmarker expected?

The benchmark report must carry an `epistemic_caveat` block that
makes this distinction explicit. Real correctness requires the
Experimentation layer (see below) to close the loop: predict, build,
observe, learn.

### The 5-level benchmark hierarchy (CTO-mandated, upgraded to 7-step sequence in review #4)

The 4-category taxonomy from CTO review #2 is upgraded to 5 levels:

| Level | Question |
|---|---|
| Reconstruction | Can we rediscover what humanity already knows? |
| Resurrection | Can we rediscover abandoned possibilities? |
| Forecasting | Can we identify what is becoming feasible? |
| Synthesis | Can we discover combinations nobody has considered? |
| Creation | Can we generate a blueprint that somebody can actually build? |

Creation is the destination. The first four levels are classification
problems — the system labels an invention as feasible/uncertain/unknown.
Creation is a generation problem — the system emits a blueprint that
an engineer could start building from. The system does not honestly
claim to be an invention compiler until at least one Creation case
has been verified by an actual build.

NOTE (per CTO review #4): the 5 levels above are benchmark LEVELS.
The 7-step sequence (Observation→Knowledge→Reasoning→Blueprint→
Simulation→Experimentation→Creation) is the PROCESS sequence.
Creation appears in both — it is the destination of the sequence
AND the highest benchmark level.

### The knowledge spectrum (CTO-mandated rename)

There is a large difference between:

```text
encoding laws;
reasoning over laws;
simulating laws;
discovering laws.
```

The current domain modules (physics, chemistry, biology, mathematics,
economics) are at the **encoding** stage. They are NOT reasoning,
simulating, or discovering. The name "physics_module" did not make
this explicit. Per the CTO directive, the 5 domain modules are
renamed to `*_knowledge_module.py` to make the encoding stage
explicit.

The full spectrum:

| Stage | What it does | Name pattern | Status |
|---|---|---|---|
| Encode | Store laws/equations as structured data | `*_knowledge_module.py` | Current |
| Reason | Apply laws to derive conclusions | `*_reasoning_module.py` | Future |
| Simulate | Numerically solve the laws | `*_simulation_module.py` | Future |
| Discover | Find laws not previously known | `*_discovery_module.py` | Aspirational |

A module may NOT be renamed up the spectrum (e.g., `physics_knowledge_module` → `physics_reasoning_module`) until the verification cycle has recorded at least one pass AND one fail for the new capability against real data.

The cross-cutting modules (constraint, dependency, resurrection,
analogy, simulation, architecture, blueprint, prototype) are NOT
renamed — they are not knowledge-encoding modules, they are
reasoning/synthesis modules. The spectrum applies only to the 5
domain modules.

### The 5-layer architecture (now upgraded to 7-step sequence in CTO review #4)

The CTO observed in review #3 that the architecture was converging
toward four interacting layers:

```text
Observation layer       (knowledge acquisition: graph, evidence, failures)
        ↓
Knowledge layer         (encoded laws, equations, pathways)
        ↓
Reasoning layer         (causal analysis, counterfactuals, simulation)
        ↓
Blueprint layer         (composed 11-layer output)
```

Plus a fifth:

```text
Experimentation layer  (the loop: predict -> build -> observe -> learn)
```

Per CTO review #4 above, this is now expanded to a 7-step sequence
(Observation → Knowledge → Reasoning → Blueprint → Simulation →
Experimentation → Creation). The experimentation_layer/ scaffold
from review #3 is preserved; the loops/ package (review #4)
implements the closing of the loops that pass through it.

---

## CTO review #2 (commit `02d7658`)

The CTO reviewed the post-rename state and described it as
"a genuine increase in maturity rather than an increase in
complexity." Three things were specifically approved:

1. **Terminology correction.** Renaming `*_engine` to `*_module`
   reduced semantic inflation. Calling something a "physics engine"
   creates an obligation to satisfy a high standard. Calling something
   a "physics module" simply describes what it is.

2. **Honest benchmarks.** 3/5 PASS, 2/5 FAIL. "The most valuable
   result here is not the three passes. It is the two failures."

3. **Explicit honesty contracts.** The sentence "A PASS means the
   compiler ran end-to-end and produced a defensible chain of
   reasoning, not that the compiler has determined whether the
   invention is feasible in the real world" was called out. The CTO
   said: "That sentence should probably be printed everywhere in the
   repository." It is now in the benchmark report's `honesty_note`
   field and in this file.

### Architectural observation (CTO)

The system now has three distinct layers:

```text
Layer A — Knowledge acquisition
Layer B — Reasoning and synthesis
Layer C — Blueprint generation
```

That separation is important because it allows each layer to evolve
independently.

### New directive: depth over breadth (CTO-mandated)

The next objective is NOT to build additional modules.
The next objective is to increase the explanatory power of EXISTING
modules.

Concrete upgrades required:

| Module | From | To |
|---|---|---|
| physics_module | keyword matching | laws, equations, constraints, units, conservation principles |
| chemistry_module | keywords | reaction pathways, kinetics, equilibrium, energy states |
| mathematics_module | templates | optimization, probability, graph theory, differential equations, control theory |
| dependency_module | connections | causal relationships |
| resurrection_module | historical similarity | historical counterfactual analysis |

These upgrades are NOT renames. They are encodings of actual
scientific principles. Until a module encodes a real principle
(not a keyword filter), it is still a keyword-matching module
and must not be renamed to "engine."

### 4-category benchmark taxonomy (CTO-mandated, upgraded to 5 in review #3, then 7-step sequence in review #4)

The benchmark suite was originally divided into four categories.
Per CTO review #3 above, this is upgraded to 5 levels
(Reconstruction, Resurrection, Forecasting, Synthesis, Creation).
Per CTO review #4 above, the 5 levels are benchmark levels; the
7-step sequence (Observation → Knowledge → Reasoning → Blueprint →
Simulation → Experimentation → Creation) is the process sequence.

---

## CTO review #1 (commit `a3d167d`)

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
