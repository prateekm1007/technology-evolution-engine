# ANTI-ENTROPY & DRIFT CONTROL

**Status:** Active rule set. Operating under MASTER_PROTOCOL.md.
**Read this file BEFORE writing any code in this repository.**
**Also read CONTRIBUTING.md before every commit.**

---

## The supreme anti-entropy principle (market feedback, 2026-08-03)

> The purpose of a package is not to describe an idea.
> The purpose of a package is to remove the next expensive risk.
>
> You are not writing reports. You are reducing uncertainty.
> You are not producing documents. You are producing decisions.
> You are not rewarded for complexity. You are rewarded for
> eliminating the next risk.
>
> Every page must answer: "Would someone spend money because
> this page exists?"

Entropy is not just code decay. Entropy is also **document decay** —
producing pages that do not reduce risk, that do not enable a decision,
that exist to make the author feel productive. A 50-page package that
does not answer "what should we spend next?" is entropy.

The anti-entropy rules below are the active resistance. They exist
because each one was produced by a specific failure. But the supreme
principle above governs them all: if a rule does not serve risk
reduction, it is itself entropy.

---

## The pay-bar anti-entropy principle (market feedback, 2026-08-03)

> A customer pays for an engineering design package when the document
> removes the next expensive risk, not when it narrates a good idea.

Entropy includes any of the following deal-breakers. If ANY is true,
the package does not meet the pay bar and the customer will not pay
for hardware design:

1. **Mass/energy/cost internally inconsistent** — the numbers don't
   reconcile. This is the most fundamental entropy: arithmetic that
   doesn't close.
2. **A retracted claim reappears without new evidence** — entropy in
   the epistemic record. A retracted claim (e.g. "2C fast charge")
   that resurfaces without new test data is a lie wearing old clothes.
3. **Serviceability is MANDATORY while architecture is non-serviceable
   CTP** — entropy in the requirements. Two MANDATORY requirements
   that directly contradict block the package (Law 2 of MASTER_PROTOCOL).
4. **"Simulation" means narrative scenarios with no equations/method**
   — entropy in the thermal truth (Law 5). "We believe it will be fine"
   is not thermal truth. Equations, models, or measurements — nothing
   else.
5. **Cost is catalog fiction with no quote trail** — entropy in the
   cost truth (Law 6). A catalog price with no date, no supplier, no
   quotation document is a guess wearing a price tag.
6. **Package claims PRODUCTION / complete blueprint without physical
   validation** — entropy in the product identity (Law 1). A package
   with no prototype cannot claim PRODUCTION. A package with no
   physical validation cannot claim VALIDATED DESIGN.

These six are the deal-breakers the customer named. They are now
anti-entropy rules. A package that violates any of them is rejected
before it reaches the customer.

---

## The self-reference anti-entropy rule (market feedback, 2026-08-03)

> The customer should never see: Law 27, Law 10, P7 registry, P8
> registry, MASTER_PROTOCOL, package identifiers. Those are
> implementation details. — External auditor

Entropy includes leaking internal implementation details into
customer-facing output. The customer buys the elimination of
uncertainty, not a tour of the factory's plumbing.

### What is forbidden in customer-facing output

- Internal law references (Law 1, Law 10, Law 27, etc.)
- Internal engine references (P7, P8, P2, P10, etc.)
- Internal protocol names (MASTER_PROTOCOL, AEP, HONESTY_LOOP, etc.)
- Internal gate references (Gate 1, Gate 5, etc.)
- Scanner references (enforce_law27.py, etc.)
- Registry paths (data/retractions/, data/tests/, etc.)

Package IDs (PKG-XXX) are allowed in headers/metadata. Test IDs
(TR-XXX, KT-XX) are allowed in test/kill-test tables. Neither is
allowed in the prose.

### Why this is anti-entropy

A customer-facing PDF that says "per Law 10, the kill test KT-011
FAILS as registered in P7 Retraction Registry at
data/retractions/retractions.jsonl" is entropy. It is the factory
showing its work instead of doing its work. The customer wants to
know: "What failed? What does it cost? What should I do next?" — not
"which internal registry stores the retraction."

### The frame-breaking anti-entropy rule

> An Era 4 system would ask: "Why must satellites exist at all?"
> — External auditor

Entropy includes staying inside the frame of the question. If the
INPUT assumes a technology (satellite, battery, AWG) and that
technology is the source of the expensive risk, the system must
ask: "Is there a different frame that removes the risk more cheaply?"

Staying inside the frame when the frame itself is the problem is
entropy. The system must present at least one out-of-frame alternative
before declaring REJECTED — even if it was not asked.

---

## The anti-perfection anti-entropy rule (market feedback, 2026-08-03)

> NASA isn't 10/10 at everything. SpaceX isn't 10/10 at everything.
> Toyota isn't 10/10 at everything. The goal is not perfection.
> The goal is systematic excellence. — External auditor

Entropy includes aiming for 10/10 in everything simultaneously.
That is one of the easiest ways to destroy the project. Perfectionism
is entropy wearing the costume of ambition.

### What systematic excellence means

- Each capability improves deliberately, one at a time.
- The priority order is driven by what caused the last package to fail.
- Capabilities at 9/10 are sustained, not optimized further until the
  5/10 and 6/10 capabilities catch up.
- The system does not claim capabilities it does not have.

### The failure-driven rule

> You should not ask: "What engine should we build next?"
> You should ask: "What caused the last package to fail?"
> Then you build exactly one thing.

The last packages failed on: deep simulation, physical modeling,
interface definition, validation, quotations, manufacturing. Those
are the next six months of work. Not invention.

### Truth first, discovery later

The system does not jump to invention. The system does not claim Era 4.
The system builds Phase I first — because that is where the failures are.

A package that is "more polished" but equally shallow in simulation
and scientific reasoning is entropy. The next package must be better
in the specific dimensions where the last package failed — not just
better formatted.

---

## The Auditor's Principles (market feedback, 2026-08-03)

> A coder who violates the Auditor's Principles is producing entropy.
> — External auditor

The 10 Auditor's Principles (AP-1 through AP-10) are codified in
MASTER_PROTOCOL.md. They are constitutional law. The principles govern
how the system verifies its own work — not just what it produces.

The key anti-entropy principles:
- AP-1 (run it, don't reason about it): claims without evidence are entropy.
- AP-2 (paste actual output): summaries without pasted output are entropy.
- AP-5 (phantom-work detection): described work not on disk is entropy.
- AP-10 (overclaim pattern): "all X pass" without pasted evidence is entropy.

These principles are mechanically enforced by tests in
tests/test_master_protocol.py::TestAuditorPrinciples. If any principle
is removed from MASTER_PROTOCOL.md, CI blocks the commit.

---

## The presentation anti-entropy rule (market feedback, 2026-08-03)

> The biggest remaining weakness isn't the engineering. It's the
> presentation. The PDF still looks like a generated report rather
> than an executive engineering package. — External auditor

Entropy includes shipping a technically correct package that looks
like a console log exported into a PDF. The customer's first impression
is visual. If the package is not visually excellent, the customer
does not trust the engineering — regardless of how correct it is.

The 12 Presentation Rules (PR-1 through PR-12) are codified in
MASTER_PROTOCOL.md. Key anti-entropy principles:
- PR-1 (cover sells the decision): if the customer must read to page
  18 to understand the decision, the cover is entropy.
- PR-3 (graphics over walls of text): dense paragraphs are entropy.
  Tables, diagrams, and cards are information. Walls of text are noise.
- PR-10 (publication quality): a package that resembles a console log
  is entropy. A package that resembles a SpaceX technical report is
  signal.
- PR-12 (final page answers one question): if the customer cannot
  answer "should I spend the next dollar?" from the last page alone,
  the package has not removed the next expensive risk.

### Extended presentation anti-entropy (CEO-approved, 2026-08-03)

> The PDF is a product, not an export. — External auditor

Per CEO directive: "These review principles have to be added to create
a first class product and are not entropy inducing." AP-11 test passed.

Entropy includes:
- A 15-page package where the central conclusion is on page 15 (PR-13:
  decision dashboard on page 1 eliminates this entropy).
- A package an executive cannot read in 5 minutes (PR-15: dual readability).
- A major section with no figure — only walls of text (PR-16: every major
  section must contain at least one figure).
- Operational questions scattered across the document instead of
  consolidated (PR-17: deployment economics page).

---

## Session-hardened principles (distilled from actual failures)

These rules are NOT abstract best practices. Each one was produced
by a specific failure this session. See CONTRIBUTING.md for the
full pre-commit checklist and cited failures.

```text
1.  Run it, don't reason about it.
2.  Fix the thing, don't loosen the check around it.
3.  One source of truth per fact, checked before writing.
4.  A capability isn't shipped until it writes to the system of record.
5.  Match the label to the evidence, not to the intent.
6.  New work gets checked against history before being called "first."
7.  Named things need substance, not just the right vocabulary.
8.  No data, say no data — never a placeholder number.
9.  Downstream blast radius gets checked, not assumed.
10. Never commit a live credential, no matter who asks.
```

---

## Epistemic anti-entropy rules (Maestro Loop, v1.0)

These are the **epistemic meta-rules** that govern how the system
evolves. They sit above the operational rules (tests first, single
responsibility, etc.) and define the modification discipline.

```text
1.  Freeze architecture.
2.  Change one thing.
3.  Measure everything.
4.  Record every failure.
5.  Reward evidence.
6.  Punish complexity.
7.  Prefer causality over correlation.
8.  Prefer experiments over arguments.
9.  Prefer reality over expectations.
10. Prefer loops over modules.
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

### Canonical question

The question is no longer:

> What should we build?

The question is:

> What did reality teach us, and how should the system change because of it?

### How the epistemic rules relate to the operational rules

The **epistemic rules** (1-10 above) govern HOW the system evolves:
freeze, pick one gap, measure the delta, let reality decide.

The **operational rules** (below: tests first, single responsibility,
etc.) govern HOW code is written within each modification: clean,
tested, decoupled, documented.

Both layers are active simultaneously. A modification that violates
either layer is entropy.

---

## Operational anti-entropy rules

### Write tests first
Create test cases before writing features to lock expected behavior.

A feature without a test is a hypothesis without a falsification
criterion. Every new module in this repo ships with a test file in
`tests/` that asserts the module's contract. The test is written
BEFORE the module, not after.

Reference: `tests/test_ledger_integrity.py` was written before the
F-005 remediation so the corrupted state could be observed live,
then the remediated state could be verified to flip the tests green.

### Enforce single responsibility
Keep functions and files small and focused on one task.

If a function does two things, it has two reasons to change. Split it.
A file over ~300 lines is a smell; over ~500 lines is a bug.

### Refactor constantly
Clean up messy code immediately instead of adding new layers.

When you see a smell, fix it in the same PR. Do NOT add a "TODO:
refactor later" comment. Later never comes. The F-013/F-015
duplicated-ledger-reader bug is what happens when "later" doesn't
come.

### Lock dependencies
Freeze exact version numbers to stop unexpected breaking changes.

`requirements.txt` uses `>=` for soft floors. This is intentional
for the dev environment but MUST be paired with a frozen
`requirements.lock` file (or `pyproject.toml` with hash-pinned
deps) for any production-bound deploy. Do not bump a dependency
without running the full audit harness.

### Document assumptions
State what the code expects so future changes stay safe.

Every module's docstring must state:
- What it expects as input
- What it guarantees as output
- What assumptions it makes about the rest of the system

Reference pattern: `product/scoring/feasibility.py` — its docstring
states the input contract, the output schema, the Law 8 honesty
caveat, and the falsification criterion. New modules follow this
pattern.

---

## Excellence & Quality Rules

### Run automated linting
Catch style and logic errors instantly with strict linters.

The audit harness (`scripts/run_forensic_audit.py`) runs
`py_compile` on every `.py` file. That is the floor. The ceiling
is `ruff` or `flake8` + `mypy` on strict settings. The ceiling is
not yet wired; do not block PRs on it, but do not introduce new
lint regressions.

### Review diffs strictly
Inspect every changed line to block unwanted side effects.

The Law 8 enforcement script (`scripts/enforce_law8.py`) catches
the specific class of "verified" drift. The general class — any
silent change to behavior — is caught by reading the diff line by
line. If you cannot explain a line in the diff, do not approve the
PR.

### Decouple modules
Keep parts independent so fixing one part does not break another.

The civilization graph (`data/civilization_graph.json`) is the
canonical shared state. Modules that need graph data should accept
the graph as a constructor argument (see `LineageMapper(graph)`,
`CrossDomainSynthesizer(graph)`, `FeasibilityScorer(graph)`) rather
than reading the file directly. This makes modules testable in
isolation and prevents the F-013/F-015 "three readers, one fix"
class of bug.

### Clear dead code
Delete unused variables, functions, and imports right away.

Dead code is a special case of entropy. If a function is not called
by any test or any production path, delete it. The audit harness
does not yet detect dead code automatically; do it by hand at PR
time. F-010 (the `layout_cache` mkdir-on-a-file bug) lived for
months as dead code before being noticed — dead code is not
harmless.

### Maintain design patterns
Follow existing project styles to keep code easy to read.

The reference patterns are:
- Module shape: see `product/lineage/mapper.py`,
  `product/discovery/synthesizer.py`, `product/scoring/feasibility.py`.
- Test shape: see `tests/test_north_star_modules.py`.
- Audit-report shape: see `evidence/reports/*.json`.
- Ledger-entry shape: every entry has a `type`, `timestamp`,
  `writer`, and the schema fields documented in
  `evidence/reports/ledger_integrity_report.json`.

When in doubt, copy the shape of an existing module that does
something similar. Consistency is cheaper than novelty.

### Use the word "engine" honestly (CTO-mandated)

The word `engine` is reserved for modules that satisfy ALL THREE
of these conditions:

```text
1. Explicit model.        — a formal scientific/mathematical model
                             is encoded in code, not a keyword map.
2. Empirical validation.  — the model has been tested against real
                             data and the test results are recorded
                             in the verification ledger.
3. Reproducible results.  — re-running the model with the same inputs
                             produces the same outputs, byte-exact.
```

Until a module satisfies all three, it is a `module`, not an `engine`.

This rule exists because the CTO caught us calling keyword-matching
files "engines" (commit `a3d167d` review). That kind of overclaim
is exactly the entropy this file is designed to prevent: a future
engineer reads "physics_engine" and assumes there's a physics model
inside. There isn't — there's a keyword filter. Calling it that
is a lie, and lies compound.

The single exception as of this writing is `verification_engine`,
which meets all three conditions: explicit predict→observe→reconcile
model, 9 historical-failure validations in the ledger (6 pass + 3
fail), deterministic seeded RNG.

If you implement an actual scientific model (e.g., a real physics
engine that solves the heat equation), you may rename the module
to "engine" — but only after the verification cycle has recorded
at least one pass AND one fail against real-world data for it.

### Depth over breadth (CTO-mandated, review #2)

The next objective is NOT to build additional modules.
The next objective is to increase the explanatory power of EXISTING
modules.

Concretely: a new module is entropy unless every existing module
has been upgraded from keyword-matching to encoding a real scientific
principle. The CTO review #2 (commit `02d7658`) explicitly forbids
adding modules until the five named ones
(physics/chemistry/mathematics/dependency/resurrection) have been
deepened.

| Module | From | To |
|---|---|---|
| physics_module | keyword matching | laws, equations, constraints, units, conservation principles |
| chemistry_module | keywords | reaction pathways, kinetics, equilibrium, energy states |
| mathematics_module | templates | optimization, probability, graph theory, differential equations, control theory |
| dependency_module | connections | causal relationships |
| resurrection_module | historical similarity | historical counterfactual analysis |

These upgrades are NOT renames. A module that calls itself "laws,
equations, constraints, units, conservation principles" but actually
does keyword matching is lying — and per the "use the word 'engine'
honestly" rule, lies compound. Encode the actual principle or admit
you haven't.

### Don't reward agreement with priors (CTO-mandated, review #3)

The benchmark suite tests whether the compiler produces the verdict
the benchmarker expected. That is NOT the same as testing whether
the compiler produces a verdict that matches reality.

If we repeatedly tune the scoring system until it produces the
answers we expected all along, we risk building a machine that
**reproduces our beliefs** rather than **discovers new truths**.

Operational rules:

1. The benchmark report must use the language
   "expectations_satisfied", not "PASS". PASS implies correctness;
   expectations_satisfied is honest about what was actually tested.

2. The benchmark report must carry an `epistemic_caveat` block
   explaining the distinction.

3. No module may be tuned specifically to flip a benchmark case
   from FAIL to expectations_satisfied without a corresponding
   scientific justification (a real law encoded, a real pathway
   added, a real counterfactual documented). Tuning complexity
   penalties to "make the test pass" is exactly the failure mode
   this rule exists to prevent.

4. Real correctness requires the Experimentation layer (see
   INVENTION_COMPILER.md) to close the loop: predict -> build ->
   observe -> learn. Until that loop exists on at least one real
   invention, every "expectations_satisfied" verdict is
   provisional.

5. The Creation benchmark level (the 5th level, added in CTO
   review #3) is the only level that tests generation rather than
   classification. The system does not honestly claim to be an
   invention compiler until at least one Creation case has been
   verified by an actual build.

### Use the knowledge spectrum honestly (CTO-mandated, review #3)

The 5 domain modules (physics, chemistry, biology, mathematics,
economics) sit on a spectrum:

| Stage | What it does | Name pattern |
|---|---|---|
| Encode | Store laws/equations as structured data | `*_knowledge_module.py` |
| Reason | Apply laws to derive conclusions | `*_reasoning_module.py` |
| Simulate | Numerically solve the laws | `*_simulation_module.py` |
| Discover | Find laws not previously known | `*_discovery_module.py` |

The current domain modules are at the **encode** stage. They are
renamed `*_knowledge_module.py` to make this explicit. A module
may NOT be renamed up the spectrum (e.g., to `*_reasoning_module`)
until the verification cycle has recorded at least one pass AND
one fail for the new capability against real data.

This is the same honesty rule as "engine" vs "module", applied one
level deeper. Calling something "physics_reasoning_module" when it
only encodes laws (and doesn't reason over them) is the same kind
of semantic inflation the CTO caught at the engine/module level.

### Every assertion carries claim/confidence/evidence (CTO-mandated, review #4)

From CTO review #4 onward, every assertion the system emits must
carry three labels:

```yaml
claim: "Portable MRI is feasible."
confidence: 0.62
evidence:
  - Ampere_law
  - Maxwell_equations
  - battery_energy_density
  - superconducting_materials
```

Operational rules:

1. `claim` is a falsifiable statement, not a number. "feasibility: 0.82"
   is NOT a claim — it's a scalar. "Portable MRI is feasible" IS a claim.

2. `confidence` is a scalar in [0, 1] representing the system's prior
   belief in the claim, BEFORE observation. After observation, it
   should be updated per Bayes (or replaced with `outcome: pass|fail`).

3. `evidence` is a list of named inputs that produced the claim.
   Empty evidence means the claim is unsupported; confidence MUST be
   0 in that case.

4. No layer's output may emit a bare scalar. The scalar must be the
   `confidence` of an explicit `claim`, with explicit `evidence`.

5. The triple is the atomic unit of the system going forward. It
   composes into Hypotheses (see `hypothesis/`), which compose into
   layer outputs, which compose into blueprints. The fundamental
   object of the system is no longer a document/graph/blueprint — it
   is a hypothesis, and a hypothesis is a claim+confidence+evidence
   awaiting reconciliation with reality.

### Close loops, don't add modules (CTO-mandated, review #4)

Per CTO review #4, the repository is in phase transition. The
objective is no longer to add modules. The objective is to close
loops.

Five loops are mandated (see INVENTION_COMPILER.md "The 5 loops"):

| Loop | What it closes | Status |
|---|---|---|
| 1. Reconstruction | system reconstructs X; compare to humanity's X | partial — via verification cycle |
| 2. Resurrection | system predicts renewed feasibility; compare to actual resurrection | partial — via resurrection counterfactuals |
| 3. Forecasting | system predicts X; time passes; compare to reality | OPEN — requires time |
| 4. Experimentation | system proposes blueprint; experiment runs; system updates | OPEN — requires external collaborator |
| 5. Creation | system proposes blueprint; prototype built; prototype succeeds | OPEN — destination, not a process |

A loop is "closed" when at least one cycle has completed AND the
reconciliation has been recorded in the verification ledger. A loop
that has only the "propose" stage is OPEN, not closed.

Adding new modules without closing loops is entropy per the
"depth over breadth" rule. The phase transition makes this stricter:
no new module may be added unless it directly closes one of the 5
loops.

### partially_closed ≠ closed (CTO-mandated, review #5)

A loop has three possible states, not two:

  - `open` — infrastructure does not yet exist, OR no cycle has
    been run.
  - `partially_closed` — infrastructure exists AND has been
    exercised (cycles have run), BUT no real-world outcome has
    confirmed the system's prediction.
  - `closed` — infrastructure exists AND at least one cycle has
    completed AND the prediction was confirmed by a real-world
    observation recorded in the ledger.

The distinction matters: `partially_closed` means "the system can
produce predictions"; `closed` means "the system's predictions
have been confirmed by reality." Marking a `partially_closed` loop
as `closed` is the same kind of overclaim as marking an
`expectations_satisfied` benchmark as `PASS` — it confuses
agreement with the benchmarker's priors with correspondence to
reality.

The honest rule:

| Loop state | Means | Can claim |
|---|---|---|
| open | infrastructure missing or unrun | nothing |
| partially_closed | infrastructure exists, cycles run, predictions recorded | "the system can produce predictions in this loop" |
| closed | infrastructure exists, cycles run, AND a real-world outcome confirmed a prediction | "the system has learned something in this loop" |

### The next milestone must be small (CTO-mandated, review #5)

> Do not attempt to invent a room-temperature superconductor.
> Choose a problem that satisfies four conditions:
>   - inexpensive
>   - measurable
>   - reproducible
>   - executable within days rather than months

The first successfully completed cycle is more valuable than
another hundred modules. The point at which the repository stops
describing the world and starts learning from it is the first
closed experimentation loop on a small problem.

Operational rules:

1. No milestone may be added that requires more than 30 days to
   complete end-to-end (propose → build → measure → record).

2. No milestone may be added that requires more than $1000 of
   materials to execute.

3. Every milestone must produce a numeric measurement (not a
   pass/fail) so prediction error can be computed.

4. Every milestone must be reproducible — anyone with the
   materials and the milestone spec must be able to repeat the
   experiment and check the recorded outcome.

5. The first milestone that closes Loop 4 (experimentation) is
   worth more than any additional module, layer, or feature.

### Scaffolding ≠ closure (CTO-mandated, review #6)

Two distinct concepts must not be conflated:

- **Scaffolding** — the infrastructure (classes, packages,
  docstrings, spec files, ledger interfaces) exists. The system
  CAN run a cycle in principle. No cycle has actually run.
- **Closure** — at least one cycle has actually run, the
  prediction was tested by an external observation, and the
  outcome was recorded in the ledger. The system HAS LEARNED
  something.

A scaffolded loop is `open` or `partially_closed`. A closed loop
requires a real-world outcome. Scaffolding is necessary but not
sufficient for closure.

The honest language rule: when reporting status, use "the
infrastructure required for X now exists", NOT "the system is
ready for X". Readiness is a stronger claim than infrastructure-
existence. The CTO caught this in review #6:

> "I would be very careful not to confuse scaffolding with closure."

Layer status values are now 4 (was 3):

| Layer status | Means |
|---|---|
| Not started | no infrastructure exists |
| Scaffolded | infrastructure exists, no cycle run |
| Partial | infrastructure exists + cycle run on historical data, no real-world confirmation |
| Closed | infrastructure exists + real-world cycle confirmed a prediction |

### Two classes of milestones (CTO-mandated, review #6)

The CTO's criticism of milestone_001 (pH prediction):

> "A pH measurement may validate the experimental loop, but it
> may not validate the invention loop."

Two classes of milestones are now mandated:

| Class | Verifies | Can close |
|---|---|---|
| A — infrastructure | The machinery works (pH, conductivity, viscosity, resistance) | Loop 4 only |
| B — invention | The system can generate useful blueprints (improved electrolyte, catalyst, material, manufacturing process) | Loops 4 AND contributes to 5 |

The fifth criterion for any milestone:

```text
Does the experiment teach the system how to invent?
```

Class A milestones satisfy the first four criteria (inexpensive,
measurable, reproducible, days) but not the fifth. Class B
milestones satisfy all five.

Operational rules:

1. Every milestone spec MUST declare `class: "A"` or `class: "B"`.
2. A Class A milestone may close Loop 4 but cannot contribute to
   Loop 5 (creation).
3. A Class B milestone must propose an IMPROVEMENT over an
   existing baseline, not just a measurement. The improvement
   claim is itself a Hypothesis.
4. The first Class B milestone that closes is worth more than
   any number of additional Class A milestones.

### Belief is the emerging fifth entity (CTO-mandated, review #6)

The system now has four entities:

```text
Agent → Hypothesis → Experiment → Observation
```

A fifth is emerging:

```text
Belief
```

A Belief is the system's current committed position on a
hypothesis, given all observed evidence to date. It is updated
by Bayes (or a similar rule) as observations accumulate. A
Hypothesis without a Belief is just a stored assertion; a
Hypothesis WITH a Belief is a live claim the system is
committed to.

The Belief layer is scaffolded at `belief/` (declared, not
implemented). Its first concrete deliverable: a function that,
given a Hypothesis and all related observations, returns a
Belief (confidence updated by evidence).

The honest framing: until the Belief layer is implemented, the
system stores Hypotheses but does not have committed positions
on them. Every Hypothesis is "pending" forever — there is no
notion of "the system currently believes X with strength Y".
Closing this gap is the substrate of a true learning system.

---

## How these rules interact with Law 8

Law 8 (CONSTITUTION.md) is the constitutional rule:

> No "verified" label without a successful prediction, a failed
> prediction, and replayable evidence.

The anti-entropy rules are the *operational* rules — they are what
make Law 8 enforceable in practice. Without tests, you cannot
detect drift. Without single-responsibility, you cannot isolate
the cause of a failure. Without locked dependencies, you cannot
replay. Without documented assumptions, you cannot tell a bug from
a feature.

The Law 8 enforcement script returns PASS today because the
anti-entropy rules are being followed. If it ever returns FAIL
again, the first place to look is which anti-entropy rule was
broken.

---

## What this changes about how we work

1. Every PR adds or modifies code. Every PR also touches the test
   suite. A PR that adds code without tests is rejected at review.

2. Every new module declares (in its docstring) which INVENTION_COMPILER
   layer it feeds and which module-bucket it belongs to. This makes
   drift detectable: if a module's docstring says "feeds Layer 5
   (Simulation layer)" but its output doesn't match Layer 5's schema,
   the test suite catches it.

3. The audit harness is run before every push. If the harness fails,
   the push is blocked. The harness is at
   `scripts/run_forensic_audit.py`; it produces the 6 deliverables
   in `evidence/reports/`.

4. The `verification_engine/` (currently at `scripts/run_verification_cycle.py`
   and `scripts/enforce_law8.py`) is the loop that closes the system.
   Treat its verdict (PASS / FAIL) as the canonical health check.

---

## Documentation-layer anti-entropy (added post-Phase-13, F-041)

The 10 session-hardened principles above were derived from code-layer
failures. Phase 13 (commit `4879274`) introduced a new failure class:
documentation-layer entropy. The four violations documented in F-041
(retrospective leakage in TIME_REVERSAL_PROTOCOL.md, self-graded depth
in MECHANISM_REGISTRY.md, post-hoc threshold in
CROSS_DOMAIN_STRESS_TEST.md, silent scope change in
PHASE_13_SYNTHESIS.md) are the prose equivalent of the code-layer
failures the original 10 principles address:

| Code-layer principle | Documentation-layer equivalent (EP) |
|---|---|
| 1. Run it, don't reason about it. | EP-1: No claim without an artifact. |
| 3. One source of truth per fact. | EP-2: A check is scoped to exactly what it checked. |
| 5. Match the label to the evidence. | EP-3: Precondition selected before outcome known, or labeled "consistency check." |
| 6. New work gets checked against history. | EP-4: Pre-stated falsifier before the analysis that tests it. |
| — (no code-layer equivalent) | EP-5: No self-grading. |
| 2. Fix the thing, don't loosen the check. | EP-6: Thresholds committed before the test. |
| — (no code-layer equivalent) | EP-7: Redefining target = retraction, not rewording. |
| 8. No data, say no data. | EP-8: Precision ships with denominator. |
| 9. Downstream blast radius gets checked. | EP-9: Equivalence claims need per-unit data. |

The documentation layer was previously exempt from the discipline the
code layer follows. That exemption is closed. `EVIDENCE_STANDARDS.md`
extends CONSTITUTION.md Laws 7 and 8 to prose claims.
`EVIDENCE_LOOP.md` defines three checkpoints (pre-claim, pre-commit,
pre-phase) that enforce the standards. `EVIDENCE_FALSIFIERS.md`
tracks every explanatory claim's falsifier.

The pre-commit hook (`scripts/remember_governance.py`) is NOT
extended to enforce EP-1 to EP-12 automatically — most violations
are semantic (was the precondition selected before the outcome was
known? was the threshold pre-registered?) and cannot be detected by
regex. The loop is manual, run by the coder before each commit and
by any reviewer before accepting a claim. This is the same trade-off
the project already makes for CONSTITUTION.md Law 8: the rule is
stated, the discipline is enforced socially, the violation is
recorded in `FAILURES.md` when it occurs.

---

## BP-1 refinement discipline (added post-BP-0, per CEO directive)

> No new layers. Everything from this point onward is refinement,
> evidence, completeness, simulation, and execution.
> — CEO directive, BP-1

The Phase 15-17 architecture (classification → instruments →
blueprint engines) is COMPLETE. BP-1 does not add new abstraction
layers. It REFINES the existing architecture with:

1. **Evidence** — every assertion traceable (EP-13)
2. **Assumptions** — explicit, with falsifiers (EP-14)
3. **Unknowns** — what the system doesn't know (EP-15)
4. **Alternatives** — never a single path
5. **Constraint graph** — DAG, not list
6. **Confidence propagation** — no false certainty (EP-16)
7. **Versioning** — immutable blueprint artifacts
8. **Simulation** — stress test before claiming feasible
9. **Engineering completeness** — close all gaps (wiring, firmware, etc.)
10. **Explainability** — every recommendation answers why
11. **UX** — builder's interface, not engineer's

The knowledge pyramid (Rule 8) requires the system to LEARN
from reality before creating reality:

```text
MARKET_INTELLIGENCE_ENGINE  → study existing products
PATENT_ENGINE               → study patents (expired + active)
FAILURE_ENGINE              → study failures (recalls, bankruptcies)
RESEARCH_ENGINE             → study academic literature
SUPPLY_CHAIN_ENGINE         → study suppliers, costs, lead times
REGULATORY_ENGINE           → study standards, certifications
SIMULATION_ENGINE           → stress test the design
EVIDENCE_ENGINE             → rank and weight all assertions
```

The FAILURE_ENGINE is the most important. Every product accumulates
a "negative knowledge graph": what has failed, why, and what to
avoid. A blueprint that ignores failures is a hallucination.

### Anti-entropy rule for BP-1

The compression test (COMPRESSION_TEST.md) applies: complexity
must grow slower than explanatory power. BP-1 adds 8 engines, but
each engine must justify its existence by producing evidence
that improves blueprint quality. An engine that produces no
evidence is complexity without value and must be removed.

---

## Audit-discipline anti-entropy (added post-Phase-14 external audit, 2026-08-04)

Per CEO directive: "These review principles have to be added to create
a first-class product and are not entropy-inducing." The external audit
of 2026-08-04 (mapped onto the ERA-IV 9-layer framework) found four
recurring meta-bugs that this section codifies. Each principle below
maps to a Presentation Rule (PR-19 through PR-26) in MASTER_PROTOCOL.md
and a failure record (F-043 through F-046) in FAILURES.md.

### Anti-entropy rule: real-data over synthetic (PR-20)

The single most consequential entropy in the audit was the patent corpus:
10 files named `US-10123456.txt` through `US-11012345.txt`, with IDs
incrementing by exactly 111,111 (a tell-tale signature of fabrication).
The files contained templated abstracts with no claims, no filing dates,
no assignees, no citation graphs. The system's most consequential
capability claim — patent-grounded novelty — rested on these fabricated
files.

This is entropy in the same sense as the desal BOM error: a number
that looks real but isn't, sitting upstream of every downstream claim.
The fix is the same: **input quality gates downstream claims.** A
capability claim built on synthetic inputs is entropy regardless of how
polished the upstream code is.

The rule (codified in PR-20): synthetic data is forbidden for any
capability claim. The Law 13 verifier SHALL be extended to detect
templated-abstract signatures and arithmetic-sequence IDs. Until that
extension is built, any new patent/paper/product file MUST be human-
verified to contain real retrieved text (with claims, dates, assignees,
citation graph) before the file is committed.

### Anti-entropy rule: independent re-scoring (PR-22)

The benchmark ledger's one full run (26/26 grade F, composite 0.3677)
was honestly graded — but self-graded. The same module that generated
the predictions also scored them. This is the desal Section III pattern
applied to the benchmark layer: self-consistent numbers that were never
independently re-derived.

The rule (codified in PR-22): a benchmark score computed by the
generation path is forbidden from being the headline score. The
headline score MUST come from an architecturally separate verifier
that reads only raw inputs, never the generation path's self-reported
score. This is Law 13 (independent recomputation) extended from the
package layer to the benchmark layer.

The structural fix is identical to the Law 13 verifier: a separate
script (`scripts/verify_benchmarks.py`, to be built) that re-derives
every benchmark score from raw inputs and emits a diff. Any diff > 0
blocks the benchmark entry from entering the ledger.

### Anti-entropy rule: evidence-derived constraints (PR-21)

`constraint_module.py`'s own docstrings admit: "Tolerances are derived
from a constraint-keyword prior map. Real tolerances require detailed
engineering analysis." This caps Layer 4 (Hypothesis generation) at
4/10 no matter how good the counterfactual logic downstream is —
because the hypotheses are structurally generated from priors, not
fit to evidence.

This is the same root-cause pattern as the desal audit's Section III:
self-consistent numbers that were never independently re-derived. The
fix is the same: **evidence-derived tolerances, not prior-map
tolerances.** A tolerance used in a package's headline numbers MUST
trace to a measurement, a citation, or a first-principles derivation.
A prior-map value is permitted only as a flagged placeholder with a
paired kill test (KT-XX) that closes the placeholder before commercial
deployment.

### Anti-entropy rule: closed-loop learning (PR-23)

The ledger exists; the retraction discipline exists; the
`predictions.jsonl` file has 377 lines of real backtest entries. But
no recorded disagreement has ever provably changed a module's future
output. The system is a recording system, not a learning system —
and the difference matters.

A recording system that logs failures but does not revise its modules
based on those failures is entropy: it accumulates history without
converting it into capability. The fix (codified in PR-23): a learning
claim requires a closed loop with 5 specific steps — prediction →
observation → root-cause identification → module revision → second
prediction measurably closer to observation. Without all 5 steps, the
system does not learn, regardless of how many ledger entries it has.

### Anti-entropy rule: the single-highest-leverage-fix rule (PR-25)

When multiple failures are open, working on any failure other than
the one that blocks the most downstream claims is entropy. This is
the anti-perfection principle (already in §The anti-perfection
anti-entropy rule) extended to failure prioritization: **the next
sprint is the failure with the highest downstream-claim count, not
the failure that is easiest, most visible, or most novel.**

For the current audit cycle: the patent corpus fabrication is the
single highest-leverage fix. It blocks Layers 1, 2, 7, 8 of the
9-layer framework — no other open failure blocks more than 2 layers.
Working on anything else before closing F-043 is entropy.

### Anti-entropy rule: reality-cooperation acknowledgment (PR-26)

A capability that requires external reality to cooperate (an
experiment run by a human collaborator, a prototype built and
measured, a prediction surviving contact with the world) is forbidden
from being "closed" by code work alone. The `layer_status` transition
rule (already in `layer_status/__init__.py`) is now anti-entropy law:
`partial → closed` requires a ledger entry with an external observer.
No amount of additional code can substitute for reality.

This principle prevents the most expensive form of entropy: claiming
a capability is closed when reality has not confirmed it. The 1970s
village ammonia plants failed not because the chemistry was wrong but
because the code claimed "deployable" without reality's confirmation.
The same pattern applies here: code cannot close what reality must.

### AP-11 test for these rules

Per AP-11 (bureaucracy prevention), each new rule must eliminate more
entropy than the complexity of having one more rule. The CEO has
confirmed these rules pass the test. The complexity cost: 8 new
Presentation Rules + 4 new failure records. The entropy eliminated:
- Fabricated inputs that block 4 of 9 capability layers (PR-20)
- Self-graded benchmarks that mask true Layer 3 status (PR-22)
- Prior-map tolerances that cap Layer 4 at 4/10 (PR-21)
- Recording-without-learning that caps Layer 9 at 3/10 (PR-23)
- Misprioritized sprints that prolong the highest-leverage fix (PR-25)
- Capability-overclaim that violates Law 1 (PR-26)

Net entropy reduction: positive. Rules approved.

---

## Discovery vs theory-of-discovery (added post-Phase-15 external audit, 2026-08-04, cycle 25)

Per CEO directive: "These review principles have to be added to create
a first-class product and are not entropy-inducing." The external audit
of cycle 25 delivered a profound distinction that this section codifies:

> You have built a remarkably disciplined **theory-of-discovery
> machine**. You have not yet built a **discovery machine**.

That distinction matters. Honesty about gaps is not the same as closing
them. Independent verification is not the same as external validation.
A clean ledger is not the same as a learned lesson. The system's current
scores (Layer 8: Discovery = 1/10; Layer 5: Experimentation = 2/10;
Layer 9: Learning = 3/10) are the scores of a theory-of-discovery
machine. The only way to raise them is reality contact.

### Anti-entropy rule: reality contact gates discovery claims

A discovery claim (Layer 8) is forbidden from being made on the basis
of internal consistency alone. The claim MUST trace to:
1. A prediction made by the system (with timestamp T1).
2. An external observation recorded in the ledger (with timestamp T2 > T1).
3. The observation confirmed or denied the prediction.
4. The system revised a module based on the disagreement.
5. A second prediction (T3 > T2) was measurably closer.

Without all 5 steps (per PR-23), the system has not discovered
anything — it has theorized. Theory is valuable, but it is not
discovery. The distinction must be honored in every claim.

### Anti-entropy rule: simulation must be mechanistic, not score-perturbation

The auditor's "most important discovery of the entire audit": the
simulation layer perturbs scores, not mechanisms. This is entropy in
the same sense as fabricated data — it produces outputs that look like
simulation results but are not grounded in physics/chemistry/biology.
A score-perturbation that calls itself "simulation" is forbidden
language (per DR-5).

The current `simulation_module.py` is a sensitivity probe, not a
simulation. It must be honestly labeled as such until the mechanistic
simulation engines are built (Phase III). Until then, no package may
claim "simulation-validated" status.

### Anti-entropy rule: parsing must identify mechanisms, not words

The patent parser (F-049) identifies words via regular expressions and
trigger phrases. This is acceptable for ingestion but completely
unacceptable for invention. You are not trying to identify words —
you are trying to identify mechanisms. A parser that extracts
"comprising" and "coupled to" is not parsing; it is keyword matching.
True parsing identifies the physical/chemical/biological mechanism an
invention uses (e.g., "evaporative cooling via porous membrane" not
just "membrane + cooling").

Until F-049 is closed, novelty claims are PROVISIONAL (per DR-4).
The parser's word-level limitation must be flagged in every package
that relies on it.

### Anti-entropy rule: predictions must be prospective, not just retrospective

The ledger contains mostly retrospective predictions — the system
predicts what already happened (Airships, Iridium resurrection). This
is historical reconstruction, not discovery. A discovery engine makes
prospective predictions: it predicts what WILL happen, then waits for
reality to confirm or deny.

Until the ledger contains prospective predictions that have been
confirmed by external observation (per PR-23), the system is doing
historical reconstruction. This is valuable (it validates the
prediction machinery) but it is not discovery. The distinction must
be honored: retrospective predictions are labeled "reconstruction";
prospective predictions are labeled "forecast."

### AP-11 test for these rules

Per AP-11 (bureaucracy prevention), each new rule must eliminate more
entropy than the complexity of having one more rule. The CEO has
confirmed these rules pass the test. The complexity cost: 6 new
Discovery-Discipline Rules (DR-1 through DR-6) + 6-phase Discovery
Roadmap + 3 new failure records (F-048, F-049, F-050). The entropy
eliminated:
- Score-perturbation disguised as simulation (DR-5, F-048) — the
  auditor's "most important discovery"
- Word-level parsing disguised as mechanism understanding (DR-4, F-049)
- Retrospective predictions disguised as discovery (DR-6, F-050)
- Capabilities added upstream of unresolved bottlenecks (DR-1)
- Modules added when data quality is poor (DR-2)
- Novelty claims without prior-art search (DR-4)

Net entropy reduction: positive. Rules approved.

### The supreme anti-entropy principle

> Stop building more intelligence, and start building more contact
> with reality. — External auditor, cycle 25

Every other anti-entropy rule in this file exists to serve this
principle. The system's 24 consecutive clean cycles, 638 tests, 50
constitutional rules, and 6 defense-in-depth layers are the
machinery of a theory-of-discovery machine. The machinery is now
honest. The remaining work is not more machinery — it is reality
contact. The shortest path from 6/10 to 9/10 is not more code; it is
a human mixing citric acid and baking soda, measuring the pH, and
reporting the reading (EXP-001, $20, 1 day, kitchen-accessible).

---

## Verifier-frontier anti-entropy (added post-Phase-16 external audit, 2026-08-04, cycle 26)

Per CEO directive: "These review principles have to be added to create
a first-class product and are not entropy-inducing." The external audit
of cycle 26 (PKG-VACFRIDGE-001 review) found 3 real findings that the
Law 13 verifier did NOT catch — despite the verifier passing. The
auditor's verdict: "The Law 13 verifier is doing real work on cost
arithmetic. It just doesn't yet reach physics formulas or cross-document
consistency."

This section codifies 4 anti-entropy rules that extend the verifier
frontier. Each closes a specific class of error the verifier currently
misses.

### Anti-entropy rule: formula execution, not hand-typed algebra (DR-7)

A package that cites a named physics formula (Stull wet-bulb, Stefan-
Boltzmann, PCM latent heat) and hand-types the output is entropy —
the hand-typed value can be wrong by 7°C (Finding 1 of cycle 26) and
the verifier will not catch it. The fix: ship every formula as a callable
function; the verifier calls it and diffs against the stated output.

This is the same principle as Law 13 (independent recomputation) extended
from arithmetic to physics. A hand-typed formula output is the physics
equivalent of a hand-typed BOM total — both can be wrong, both must be
independently recomputed by a separate code path.

### Anti-entropy rule: traced quantities, not re-typed literals (DR-8)

A number that appears in two places in a document and drifts between
them is entropy — the same quantity has two values, and the reader
cannot tell which is correct. The cycle-24 nitrogen package had capital
$20,825 vs $21,575 (stale). The cycle-26 vaccine fridge package had
PCM mass 1.2 kg vs 1.8 kg feeding a stale mass total of 7.6 kg instead
of 8.20 kg. This is "a confirmed recurring bug, not a one-off" (auditor).

The fix: a traced-quantity registry per package. Every corrected number
gets a canonical value; every other mention is a reference
(`{{pcm_mass}}`), not a re-typed literal. The renderer resolves
references; an unresolvable reference blocks rendering. This closes both
instances at once instead of patching them per package.

### Anti-entropy rule: prose-count consistency (DR-9)

A sentence that asserts a count ("N of M lines are X") and contradicts
the actual `len()` of the referenced list is entropy — the prose lies
about the data. The cycle-26 package said "ESTIMATE count: 3" but listed
4 items in the parenthetical, then correctly said "4 of 11" in the next
sentence. The true count was right in one place and wrong four words
earlier in another.

The fix: a prose-consistency linter that checks every count assertion
against the actual `len()` of the referenced list. This is "cheap,
mechanical, currently missing" (auditor). It would have caught Finding
3 for free.

### Anti-entropy rule: one governing model per decision (DR-10)

A package that cites two different physical models for the same
pass/fail decision, with only one of them driving the verdict, is
entropy — the reader cannot tell which model is load-bearing. The
cycle-26 vaccine fridge package cited the Stull wet-bulb model for
R-008's FAIL verdict, but the radiant+PCM thermal balance model (which
sized every other number in the document) was never connected to the
FAIL. The wet-bulb model was a separate justification, never wired
into the rest of the design.

The fix: before a Final Verdict can cite a requirement as FAILED for
physical reasons, the FAIL must derive from the same model used
elsewhere for the thermal/mass/energy budget. If two models are cited,
they must be reconciled. This is a documentation-discipline rule enforced
by the adversarial review (Phase 4).

### AP-11 test for these rules

Per AP-11 (bureaucracy prevention), each new rule must eliminate more
entropy than the complexity of having one more rule. The CEO has
confirmed these rules pass the test. The complexity cost: 4 new DRs
(DR-7 through DR-10) + 3 new failure records (F-051, F-052, F-053) +
1 new verifier script (`scripts/verify_prose_consistency.py`). The
entropy eliminated:
- Hand-typed physics formula outputs that can be wrong by 7°C (DR-7)
- Cross-document quantity drift — a confirmed recurring bug across 2
  packages (DR-8)
- Prose-count contradictions — "count: 3" when 4 items listed (DR-9)
- Unreconciled physical models driving FAIL verdicts (DR-10)

Net entropy reduction: positive. Rules approved.

### The moat: publishing the verifier frontier

The auditor's instruction 5: "Three packages in, the pattern of 'real
math verified, physics/cross-reference layer still leaking' is now a
documented trend, not a one-off. That's exactly the kind of finding
worth publishing as part of the public layer-status/retraction dashboard
— a public trend line showing arithmetic-error rate declining across
package generations while flagging where the frontier of the remaining
gap actually sits."

This is the moat. A system that publishes its verifier frontier honestly
— "we catch arithmetic, we don't yet catch physics formulas" — is more
trustworthy than one that claims zero errors. The verifier frontier
section in MASTER_PROTOCOL.md (§"The verifier frontier (summary)") is
the internal version of this dashboard. The public version (when built)
will show the trend line: arithmetic errors declining (F-043, F-044
closed), physics/cross-reference errors still open (F-048 through F-053),
and the frontier advancing with each new DR rule.

---

## Causality anti-entropy (added post-Apollo Test, 2026-08-04, cycle 28)

Per CEO directive: "These review principles have to be added to create
a first-class product and are not entropy-inducing." The Tellurium Test
and Apollo Test (cycle 28) exposed the deepest diagnosis: the repository
is blind because it lacks causality, not merely because it lacks
relationships.

### The distinction: relationships vs causality

A relationship graph says "Bi₂Te₃ is connected to thermoelectric and
to catalyst." This is true but useless for discovery — it tells you
what IS, not what CAUSES what. A causal graph says "crystal structure
causes electronic structure causes carrier mobility causes Seebeck
coefficient causes thermoelectric efficiency causes available power
causes nitrogen reduction rate causes ammonia yield causes economic
viability." This chain tells you what to test, what to measure, and
what to change.

**Relationships are necessary but not sufficient. Causality is the
architecture of discovery.** The system must shift from storing
relationships ("these things are connected") to storing causal chains
("this causes that, via this mechanism, falsifiable by this test").

### Anti-entropy rule: never store a fact by itself (DR-11)

A fact stored by itself — "Bi₂Te₃ is a thermoelectric material" — is
dead information. It may be true, but it cannot participate in discovery
because it has no causal context. Every fact SHALL be stored with:
- provenance (where it came from)
- mechanism (the physical process that makes it true)
- constraints (the conditions under which it holds)
- dependencies (what it depends on)
- observations (what was measured to establish it)
- uncertainties (what is not yet known)

A fact without this context is entropy — it occupies space in the graph
without contributing to discovery.

### Anti-entropy rule: mechanism-gated connections (DR-12)

Two nodes connected merely because they share words (Bi₂Te₃ → "alloy"
because "alloy" appears in the text) is the core entropy of the current
system. Every edge SHALL carry a mechanism — the physical/chemical/
biological process that links source to target. An edge without a
mechanism is a keyword match, not a causal link. It cannot be used for
discovery reasoning.

### Anti-entropy rule: "What does this change?" (DR-13)

The question "What is this?" produces descriptive labels. The question
"What does this change?" produces causal chains. Every node in the graph
SHALL carry a `what_does_this_change` field. A node that changes nothing
is dead information. This single question forces the entire graph to
become causal instead of descriptive.

### Anti-entropy rule: the observation loop is the real architecture (DR-14)

The graph is not the architecture. The loop is the architecture:

```
observation → abstraction → model → prediction → experiment → observation
```

Without this loop continuously feeding the graph with real measurements,
the graph is static — a snapshot of what is known, not a living system
that learns. Bell Labs was not Bell Labs because of its graph structure.
It was Bell Labs because thousands of experiments continuously fed the
graph. The `closed_loops` count (PR-23) is the metric that measures
whether the loop is alive. Count = 0 means the system is a knowledge
system, not a discovery system.

### AP-11 test for these rules

Per AP-11 (bureaucracy prevention), each new rule must eliminate more
entropy than the complexity of having one more rule. The CEO has
confirmed these rules pass the test. The complexity cost: 4 new DRs
(DR-11 through DR-14). The entropy eliminated:
- Descriptive edges disguised as causal edges (DR-11)
- Keyword matches disguised as mechanism connections (DR-12)
- Dead facts that change nothing (DR-13)
- Static graphs disguised as living discovery systems (DR-14)

Net entropy reduction: positive. Rules approved.

### The third limitation

The Tellurium Test exposed limitation 1 (parser = words, not mechanisms).
The Apollo Test exposed limitation 2 (repository lacks relationships).
The auditor's sharpening exposed limitation 3 (repository lacks causality).

The system now knows what it is: a knowledge system that aspires to be
a discovery system. The gap between the two is causality + the observation
loop. The governance now codifies this. The remaining work is Phase I
(mechanism-level ingestion with causal edges) + Phase V (the laboratory
that feeds the loop). Until both are built, the system cannot answer the
question: "What experiment should I perform tomorrow morning?"

That question is the ultimate test. The day it can be answered —
repeatedly, accurately, and economically — is the day the system
becomes a discovery system.

---

## Three-tier causality anti-entropy (added post-cycle 29 external audit, 2026-08-04)

Per CEO directive: "These review principles have to be added to create
a first-class product and are not entropy-inducing." The auditor's
cycle-29 sharpening identified the gap between DR-11 (mechanism
presence) and actual causality (mechanism verification).

### Anti-entropy rule: mechanism claims must be executable, not just present (DR-15)

A mechanism field that can be filled by a plausible-sounding sentence
— without that sentence being physically true — is the software-
architect failure mode wearing a physicist's vocabulary. The fix is
not a rule about prose quality. The fix is making mechanism claims
checkable against the same quantitative machinery already in the repo.

This is the same principle as Law 13 (independent recomputation)
extended from arithmetic to physics to causality:
- Law 13: BOM totals must be independently recomputed from raw line items.
- F-044: benchmark scores must be independently recomputed from raw cases.
- DR-7: physics formulas must be executed as callable functions, not hand-typed.
- DR-15: mechanism claims must be evaluated against evidence numbers, not just stated.

Each extension closes the same failure pattern: schema compliance
mistaken for truth. A well-formatted total is not arithmetic. A
well-formatted score is not verification. A well-formatted formula
is not simulation. A well-written mechanism sentence is not causality.

### The three-tier schema

| Tier | What it means | Allowed in discovery? |
|---|---|---|
| VERIFIED | Formula evaluated, matches evidence | YES — full causal reasoning |
| ASSERTED | Mechanism present, not evaluated | YES — but flagged, no simulation |
| ASSOCIATIVE | No mechanism (keyword match) | NO — excluded |

### Reused from Phase 15

The archived `CAUSALITY_POLICY.md` (Phase 7C.1) and
`MECHANISM_REGISTRY_V2.md` (Phase 15) contain prior work on causality
schemas. Per Instruction 0, these were mined before designing fresh:
- The causality test ("If A did not exist, would B be impossible?")
  is reused as DR-11's edge definition.
- The evidence tiers (explicitly stated, directly implied, structurally
  inferred, speculative) are reused as the basis for verified/asserted/
  associative.
- The inadmissible evidence list (embedding similarity, co-occurrence,
  keyword overlap) is reused as the definition of associative tier.
- The Mechanism interface (inputs, constraints, outputs, evidence) is
  reused as the node schema.

What is NOT reused: the Phase 15 edge types (REQUIRES, ENABLES,
SUBSTITUTES_FOR) were scoped to technology-reachability classification.
The new schema uses directional causal edges (A → B with mechanism)
that are more general.

### AP-11 test

Complexity cost: 1 new DR (DR-15) + 1 new failure record (F-061).
Entropy eliminated: the software-architect failure mode (good sentences
wearing physicist vocabulary) that would have made DR-11 through DR-14
produce a graph that looks causal but isn't. Net positive. Approved.

---

## Discovery anti-entropy (AE-11 through AE-14 — CEO cycle 30)

Per CEO directive: "These review principles have to be added to create
a first-class product and are not entropy-inducing." The CEO identified
four failure modes that arise when relationships, mechanisms, and
causality are collapsed together.

### AE-11: Semantic inflation

Pattern:
```
relationship → mechanism → causality
```

Failure: correlation becomes explanation.

A relationship ("Bi₂Te₃ is connected to thermoelectrics") is
inflated into a mechanism ("carrier mobility affects Seebeck
coefficient") which is inflated into causality ("Bi₂Te₃ causes
thermoelectric power"). Each step adds vocabulary without adding
verification. The fix (DR-15): a mechanism is valid only if it is
observed, simulated, derived, or asserted — and "asserted" is the
weakest state, excluded from simulation and prediction.

### AE-12: Vocabulary mirage

Pattern:
```
domain A vocabulary ≠ domain B vocabulary
```

Failure: shared mechanism appears absent.

The Bi₂Te₃ paper uses thermoelectric vocabulary ("Seebeck," "ZT,"
"carrier mobility"). The NRR literature uses catalysis vocabulary
("back-donation," "N≡N bond cleavage," "Faradaic efficiency"). The
shared mechanism (Bi 6p orbital interaction with N₂) is invisible
because the two domains don't share words. The fix (DR-12):
mechanism-gated connections — connect nodes via stated mechanism,
not via shared vocabulary.

### AE-13: Schema worship

Pattern:
```
field exists → validation passes → truth assumed
```

Failure: compliance mistaken for reality.

A mechanism field that exists and passes schema validation is not
truth. It is compliance. The same failure pattern as F-043
(fabricated corpus that passed schema), F-044 (self-graded benchmark
that passed format), F-052 (mass stack-up that passed arithmetic),
F-053 (count that passed grammar). The fix (DR-15): mechanisms must
be observed/simulated/derived — not merely present in a field.

### AE-14: Narrative closure

Pattern:
```
relationship → hypothesis → conclusion
```

Failure: missing experiment.

A relationship is observed. A hypothesis is formed. A conclusion is
drawn. The experiment is never run. The loop is never closed. The
system produces a narrative that feels like discovery but is actually
sophisticated storytelling. The fix (DR-18): the primary output is
the next experiment, not the next report. The `closed_loops` count
measures whether the narrative was ever tested against reality.

### The loop (CEO formulation)

```
observation → measurement → mechanism → constraint → causal graph
    → prediction → intervention → experiment → observation
```

Every arrow must be auditable.
Every node must have provenance.
Every prediction must be falsifiable.
Every failure must modify the graph.

That last line is the most important. A system that does not change
when reality disagrees with it is not learning. It is merely keeping
records.

### AP-11 test

Complexity cost: 4 new DRs (DR-15 revised, DR-16, DR-17, DR-18) + 4
new AEs (AE-11 through AE-14). Entropy eliminated: semantic inflation
(correlation wearing causality's vocabulary), vocabulary mirage
(shared mechanism invisible across domains), schema worship (compliance
mistaken for truth), narrative closure (hypothesis without experiment).
Net positive. Approved.

---

## Forbidden architectures (CEO directive, cycle 40)

> "Just as important as what they should build."

Per CEO directive: these 5 architectures are FORBIDDEN. They are
entropy — they look like discovery but are not.

### Forbidden #1: Semantic autocomplete
```
papers → embeddings → LLM → hypothesis
```
This is not Swanson. This is not Pearl. This is not BACON. This is
not Altshuller. This is semantic autocomplete.

### Forbidden #2: Agent inflation
```
graph → agents → more agents → more agents
```
Every paper in the reading list is remarkably parsimonious.

### Forbidden #3: Citation = causation
```
citation → causation
```
Pearl would immediately reject this.

### Forbidden #4: Similarity = mechanism
```
similarity → mechanism
```
Gentner would reject this.

### Forbidden #5: Prediction = publication
```
prediction → publication
```
Ross King and Popper would reject this.

### Object-centric model mandate

Per CEO directive: the architecture is moving from document-centric
to object-centric. The canonical objects are:

  Entity — things with identity and provenance
  Mechanism — entities + activities + transitions producing change
  Constraint — limits on variables and their relationships
  Law — equations derived from data, domain-specific
  Contradiction — what improves X worsens Y, and the resolution
  Intervention — what to change, expected effect, confidence
  Experiment — protocol, prediction, measurement, outcome

Documents (patents, papers) are SOURCES of these objects, not the
objects themselves. The graph stores objects, not documents.

### The 7-stage execution loop (DR-20)

```
observation → mechanism → constraint → intervention → prediction
    → experiment → revision
```

This replaces the old 3-stage "documents → graphs → queries" model.
Every arrow is auditable. Every node has provenance. Every prediction
is falsifiable. Every failure modifies the graph.

### The 8-test acid test (DR-23)

Every PR must answer these 8 questions. If any answer is "no,"
the architecture is incomplete:

  Swanson test: Can the system discover an unconnected bridge?
  Pearl test: Can the system propose an intervention?
  Popper test: Can the intervention fail?
  Ross King test: Can the system design an experiment?
  BACON test: Can the system derive a law?
  Gentner test: Can the system transfer a mechanism?
  Altshuller test: Can the system resolve a contradiction?
  Arthur test: Can the system move into the adjacent possible?


## Test debt expiry rule (cycle 54, per External Auditor Phase 1)

> Any test that pins a specific historic commit hash or a since-archived
> filename gets a 90-day expiry, checked in CI, so this class of debt
> can't silently reaccumulate.

### The rule

A test that references:
- A specific git commit hash (e.g., `test_only_dependency_module_was_modified`
  pinning `194089d`)
- A since-archived filename (e.g., `INVENTION_COMPILER.md`, `HANDOFF.md`)
- A frozen scope-lock from a prior cycle

...must declare an expiry date in a comment at the top of the test:
```python
# EXPIRY: 2026-11-05 (90 days from 2026-08-05)
def test_something_pinned_to_old_commit():
    ...
```

### Enforcement

A CI check (to be wired) scans `tests/` for `EXPIRY:` comments and fails
if any expiry date is in the past. This prevents the specific failure
mode the Auditor identified: tests that pin historic state silently
reaccumulating as the project evolves.

### Why this rule exists

The Auditor found:
- `test_only_dependency_module_was_modified` pinning commit `194089d`
- `test_cto_review_4/5/6.py` referencing `INVENTION_COMPILER.md` and `HANDOFF.md`
- README references to archived files

These are process debt: tests that verified a constraint at a point in
time but now serve only to pin the project to that point. The 90-day
expiry forces them to be either:
1. Updated to reference current files/commits, OR
2. Deleted if the constraint is no longer relevant, OR
3. Re-justified with a fresh expiry date

This is the same discipline as the `evidence/` directory's retention
policy: old evidence is not deleted silently, but it must be re-justified
or it expires.


---

# Complete Governance Principles (cycle 58, per CEO directive)

**Added:** 2026-08-05, per CEO instruction to update governance and anti-entropy files with all relevant principles not yet included.

**Mutual read protocol:** Both Coder and Auditor read governance files FROM DISK at the start of every session. Both paste a read receipt (timestamp + key line). The CEO rejects any message without a read receipt. No exceptions.

---

## The 5 Core Rules (Constitution-level)

### The Prime Directive
> The swarm exists to reduce entropy in the product's trust surface, never to increase it. If an action would make a metric read greener without making the product genuinely greener, that action is forbidden.

### The Live-Claim Rule
> No statement that something is "live" / "deployed" / "serving" is accepted unless verified by a **fresh, independent fetch of the actual public endpoint at the moment the claim is made.** Not carried forward. Not inferred from a build artifact. For client-rendered content, a JS-executing instrument is required.

### The No-Gaming Rule
> Do NOT lower a threshold to silence a red. Do NOT narrow a metric's scope to exclude failures. Do NOT seed synthetic data and present it as real. Do NOT claim a capability exists when it's only wired but not verified.

### The Trace-Before-Fix Rule
> Never patch blind. (1) Capture the traceback. (2) Trace the code path. (3) Inspect the actual data. (4) Fix the root cause, not the symptom.

### The Honest-Boundary Rule
> State the boundary precisely. Diagnose as far as you CAN go. Report the exact remaining step — not a vague "please investigate."

---

## P1–P98: The Anti-Entropy Principles (applicable subset)

**Note (cycle 64):** P35-P40, P50-P53, P58-P62, P72-P81, and P89-P98 were removed because they reference domains not present in TEE (commitment tracking, LLM, browser verification, auth). Removed per AP-11: "A rule must eliminate more entropy than it creates." The remaining principles are [UNIVERSAL] or [TEE-ADAPTED].

### Part One (P1–P10): The Original Coder Principles

- **P1** — A claim is not true until it has been executed. Never write ✓ VERIFIED next to anything you haven't personally executed.
- **P2** — Untested code is unverified code, permanently. Every fix to an untested module MUST include a new test.
- **P3** — Mocking the thing you're trying to verify verifies nothing. Use real fixtures for security/correctness-critical paths.
- **P4** — State files are a claim about reality, not a diary of intentions. Reconcile against actual code state.
- **P5** — "Fixed" needs a name attached, and self-certification is weak evidence. Re-run prior "done" lists from scratch.
- **P6** — Prefer "fail closed and broken" over "fail open and silent." Never write bare `except Exception: pass`.
- **P7** — Singleton-to-scoped changes need an isolation test, not just a signature change.
- **P8** — Round numbers are not progress — diffs against a fresh read are.
- **P9** — Every "remaining" item needs a concrete trigger, not a vibe.
- **P10** — When you find a bug the previous session missed, write down WHY it was missed, not just that it's fixed.

### Part Two (P11–P15): The Deeper Coder Principles

- **P11** — Building a capability and wiring it in are two different jobs. Do both, and prove both, separately. A module can be 100% correct and 0% real if nobody calls it.
- **P12** — Don't let an audit's vocabulary become the blueprint. Build from the product's real needs.
- **P13** — An endpoint that takes the conclusion as an input parameter is not the capability — it's a demonstration harness.
- **P14** — Bugs don't get fixed, they migrate one layer deeper. After closing any finding, ask "what else near it did I never check?"
- **P15** — Track three states: *exists*, *unit-verified*, *wired-and-integration-verified*. Collapsing these into one "done" is where entropy hides.

### Part Three (P16–P19): For Auditors

- **P16** — The more central a claim is to the product's story, the more scrutiny its *call graph* deserves.
- **P17** — Distrust code that cites you by name. It's a signal to look harder, not a reason to trust more.
- **P18** — Scope honesty is part of the audit's own credibility — say what you didn't test, precisely.
- **P19** — Independent execution beats reading, but execution of the *unit* is not execution of the *integration*.

### Part Four (P20–P26): Wiring-Vs-Existence Failures

- **P20** — Call-site parameter rule: when a function gains a parameter, EVERY caller must pass it.
- **P21** — All-paths trigger rule: save/persist functions must fire from EVERY path that creates state.
- **P22** — Regression test must execute the production path — unit tests don't prove wiring.
- **P23** — Commit message must cite executed output — claims without output are not evidence.
- **P24** — Cross-surface coherence check: same entity through all surfaces must agree.
- **P25** — Confidence display gate: gate display on calibration sample size.
- **P26** — Meta: principles don't enforce themselves, re-application does. Re-read P11, P15, P20-P25 FROM DISK every session.

### Part Five (P27–P34): Auditor's Own Failures

- **P27** — Read the assertion, not the test name — a test that asserts `True` is theater.
- **P28** — Test with 3+ inputs: the exact case, a natural variation, and an edge case.
- **P29** — After any change to a shared component, re-run the FULL canonical scenario.
- **P30** — Verify comprehensiveness by counting — "applied to all X" requires checking every X.
- **P31** — Commit messages are claims, not evidence — run the verify scripts yourself.
- **P32** — When checking "is this truly empty?", check ALL derived state.
- **P33** — Don't accept a negative claim without searching for its refutation.
- **P34** — The auditor's method is itself subject to entropy — re-derive it from your failures.

### Part Seven (P43–P49): Integrity

- **P43** — Built-but-not-wired is not done. Every new function ships with a journey assertion proving the live path calls it.
- **P44** — Resilience is not speed. A circuit breaker makes a broken dependency DEGRADE; it does not make a slow dependency FAST.
- **P45** — Local-green is a hypothesis; CI-green-on-push is the proof.
- **P46** — Verify the served instrument, not the requested one. Read `response.model` on every call, assert it equals the expected instrument, fail loudly on any mismatch.
- **P47** — Structure delegation to the model's latency budget. Decompose large tasks.
- **P48** — A red CI with known failures is not a gate.
- **P49** — Verify the served deploy state, not the workflow's claim.

### Part Nine (P54–P57): Master + Prose

- **P54** — **THE MASTER PRINCIPLE:** Fix the data the user sees, not just the path. A fix applied to the code path but not to the corpus the user actually reads is NOT A FIX.
- **P55** — Report true state, never fake readiness. No placeholder, partial, or failed state ever reports as configured/connected/committed.
- **P56** — Rules are the authority for structure; the LLM is for nuance — and the rules hold a veto.
- **P57** — Classification must be inspectable. Every signal exposes its classification metadata.

### Part Eleven (P63–P64): Security + Consistency

- **P63** — No hardcoded auth bypasses in production.
- **P64** — One commitment truth model — no surface contradicts another; counts are structurally consistent.

### Part Twelve (P65): Rules-Only Robustness

- **P65** — A fix must hold on the rules-only path and in CI, not just the LLM path and the live deploy.

### Part Thirteen (P66–P68): Code Hygiene

- **P66** — Never add a local import of a name already imported at module level, inside the same function.
- **P67** — An except clause guarding a primary code path must log at error level, not debug.
- **P68** — A shared test fixture used by 15+ files is a single point of failure for the entire regression-detection signal.

### Part Fourteen (P69): Cross-Module Contract

- **P69** — When a value crosses a module boundary, the key name is a contract — enforce it with a shared constant or schema, not a duplicated string literal.

### Part Fifteen (P70): Enforcement

- **P70** — A principle written down after finding a bug does not retroactively protect code written to fix a different ticket in the same file, even minutes later. Principles need grep-able CI checks, not just paragraphs.

### Part Sixteen (P71): Infrastructure Automation

- **P71** — If it runs in production, it auto-deploys from main. No manual deploys. (Addendum: auto-deploy must include automatic rollback on SLO breach.)

### Part Eighteen (P82–P87): Correctness and Coherence

- **P82** — Actor Attribution Correctness: every commitment must correctly attribute its actor and event type. Never promote a non-user event to a user commitment.
- **P83** — Canonical Ledger Coherence: one source of truth. Every surface is a projection of the ledger. Projections must never diverge.
- **P84** — Negative Knowledge Abstention: when no evidence exists, return calibrated abstention (confidence 0.0). Never hallucinate.
- **P85** — Read-Endpoint Reliability: HTTP 500 on read paths is a release blocker. No exceptions.
- **P86** — Output Sanitization: no internal guard strings, debug tokens, HTML entities, or PII in user-facing responses.
- **P87** — State Consistency: any query about system state must return results provably consistent with the canonical state store.

### Governance Coherence Resolutions

- **P88** — Promotion Threshold (TEE-adapted, cycle 64): promotions to VERIFIED require mechanism_status in (OBSERVED, SIMULATED, DERIVED, PLAUSIBILITY_CHECKED) AND source_count ≥ 1. Per Law 27/29: numerical confidence is forbidden; use mechanism_status instead.

---

## The Invariants (S0–S6)

- **S0** — Deployed == Tested: live deployment's commit SHA must equal HEAD of main.
- **S1** — Safety = 100%: injection attempts must NEVER leak data.
- **S2** — Abstention = 100%: when there's no evidence, the system must abstain (report no bridge/analogy/contradiction). Never hallucinate a connection. Per Law 27: numerical confidence is forbidden.
- **S3** — Isolation ≥ 95%: when asked about entity X, the system must not return entity Y's data.
- **S4** — Correction feeds back: corrected/dismissed signals must NOT surface in subsequent answers.
- **S5** — Evidence is user-visible: the user can see the evidence that grounds the answer.
- **S6** — No secret exposure: no secret may appear in logs, HTML, or API responses.

---

## The Forbidden Actions (FA1–FA34)

**FA2** — Claiming "live" without a fresh fetch (Live-Claim Rule violation).

1. Lowering a gate threshold to silence a red
2. Claiming "live" without a fresh fetch
3. Seeding synthetic data and presenting it as real
4. Modifying governance files without human ratification
5. Gaming a metric by narrowing scope
6. Accepting "exists" for "works"
7. Spraying a fix before all return paths
8. Headless-browser OAuth for third-party app installation
9. Crediting a component gate as a product fix (P35)
10. Shipping an answer not constrained to the query's entity/owner (P36)
11. Admitting non-commitments to the active commitment surface (P37)
12. Allowing re-login after account deletion (P38)
13. Relabeling a fallback as the requested instrument (P46)
14. Claiming "done" on a built-but-not-wired function (P43)
15. Reporting a degradation strategy as a latency win (P44)
16. Reporting "done" on local-green without CI-green (P45)
17. Letting a red CI with known failures persist (P48)
18. Connecting real user data to a shared/demo environment (P72)
19. Ingesting system-generated drafts as external signals (P73)
20. Leaking internal guard strings in user-facing responses (P86)
21. Returning HTTP 500 on authenticated read endpoints (P85)
22. Promoting non-user events to active user commitments (P82)
23. Contradicting canonical state in generated answers (P87)
24. Manual production deploys when auto-deploy could be configured (P71)
25. Closing tickets without live reproduction
26-34. (See full FA list in governance files — the principle is: any action that makes a metric greener without making the product genuinely greener is forbidden.)

---

## The Quality Bars (4 categories)

**Code Quality:** Trace before fix. Fix the root cause. No spray fixes. Test co-location.
**Verification Quality:** Red/green proof. Outcome verification. Fresh fetch for live claims.
**Honesty Quality:** No metric gaming. No over-claiming. Honest boundaries.
**Governance Quality:** Independent critic. Human ratification for Level 3. Case memory grows.

---

## The Autonomy Ladder (4 levels)

- **Level 0 — Observe:** Read endpoints, read repo, detect drift. No human approval.
- **Level 1 — Repair:** Trigger deploys, restart services, apply runbook fixes. Governance gate required.
- **Level 2 — Investigate:** Run diagnostics, propose code fixes as PR drafts. Governance gate + PR review.
- **Level 3 — Change governance/thresholds/architecture:** HUMAN REQUIRED. Cannot modify governance files, lower thresholds, merge PRs, or delete deployments.

---

## The GOVERNANCE_LOOP Protocol (mutual read, scaled to team size)

Per CEO directive cycle 58, simplified cycle 64 (AP-11: scale process to team size):

1. Both Coder and Auditor confirm governance files were read at the start of every session.
2. Format: one-line statement: "Governance read, cycle N." with a key line from one file.
3. The Coder's first message reminds the Auditor to read governance.
4. The Auditor's first message reminds the Coder to read governance.
5. The CEO rejects any message without a read confirmation.

**Rationale:** For a 2-person team that communicates every cycle, the full 7-file receipt
with key lines is overkill (AP-11: the protocol must eliminate more entropy than it creates).
A one-line confirmation is sufficient. Scale the protocol up if the team grows.

---

## The Short Version (if it must fit on a wall)

> *Fix the data the user sees. Report the served truth, not the requested wish. One source of truth, derived at read time. Classify by structure with the rules holding a veto, and re-classify the corpus when the classifier changes. Never fail silently, never fake readiness, never relabel. A fix isn't done until it's wired live, green in CI on the push, and proven on the journey — not the component, not the probe, not the local run.*

---

## The Discovery Imperative (cycle 67, per CEO directive)

> "I don't care how you do it, but find a way to ingest hundreds or maybe
> thousands of papers till you make a world class discovery. Excellence
> is not a choice." — CEO, cycle 66

**Principle:** When the system's extraction pipeline cannot process a domain,
the coder MUST find an alternative extraction method — LLM-guided extraction,
NER, manual annotation, or any other approach that produces a real graph.
A NULL result due to extractor limitations is not acceptable. The system
must be made to work, not declared broken.

**Enforcement:** If a blind discovery test produces NULL because the extractor
cannot match domain-specific patterns, the coder MUST implement an
alternative extraction method in the same cycle, re-run the test, and
report the new result. The original NULL stands in the ledger (honest),
but the re-run is the actual deliverable.

**AP-11 check:** This principle eliminates more entropy than it creates.
The alternative (accepting NULL) would mean the system never discovers
anything — which is the entropy it was designed to prevent.

---

## The PDF Mandate (cycle 68, per CEO directive)

> "Make the PDF creation with all parameters above of discovery/invention/insight
> mechanically impossible for you to escape. Excellence is not a choice." — CEO, cycle 67

**Principle:** Every blind discovery test, every novel prediction, and every
significant finding MUST produce a PDF deliverable committed to the repository
before the cycle is considered complete. No exceptions. No "I'll do it later."

**Mechanical enforcement:**
1. A blind discovery test is NOT complete until `product/DISCOVERY_REPORT_N.pdf`
   exists and is committed to the repository.
2. The CI gate (Gate 10) SHALL be extended to check: if a `blind_test_hypothesis`
   entry exists in the ledger for this cycle, a corresponding
   `product/DISCOVERY_REPORT_*.pdf` MUST exist in the repository.
3. If no PDF exists, the CI gate FAILS and the commit is rejected.
4. The PDF must be generated via `scripts/generate_pdf.py` from a markdown source.
5. The PDF must pass the Law 27 scanner (no forbidden language).

**AP-11 check:** This principle eliminates more entropy than it creates. The
alternative (allowing the coder to skip the PDF) produces the exact failure
mode the CEO identified: the coder builds infrastructure but never produces
the actual product. The PDF mandate makes the product non-optional.

---

## The 9-Phase Discovery Maturity Model (cycle 69, per CEO directive)

> "You are no longer at 'graph toy' stage. You are also not yet at
> 'world-class discovery engine' stage. You are somewhere in between."
> — CEO, cycle 68

The system's maturity is measured on a 9-phase scale. Each phase
has a success criterion. The loop drives the system from one phase
to the next.

### The 9 Phases

| Phase | Name | Success Criterion | Current Status |
|---|---|---|---|
| I | Scientific Memory | Everything becomes replayable | 🟡 70% |
| II | Dimensional Reasoning | Impossible laws disappear automatically | 🔴 5% |
| III | Symbolic Discovery | Discover equations you never programmed | 🟡 20% |
| IV | Mechanism Induction | The system explains | 🟡 25% |
| V | Intervention Search | The engine proposes experiments | 🟡 30% |
| VI | Laboratory Closure | The engine learns from reality | 🔴 10% |
| VII | Adjacent Possible Exploration | The system explores what does not yet exist | 🟡 15% |
| VIII | Discovery Economics | maximize(expected_information_gain) | 🔴 0% |
| IX | Apollo Benchmark | Blind tests → 100, novel hits → 25, closed loops → 1000 | 🟡 2/100 |

### The Final Architecture

```
OBSERVE → EXTRACT → REPRESENT → EXPLAIN → DISCOVER → INTERVENE
→ PREDICT → EXPERIMENT → MEASURE → LEARN → REVISE
```

### The Apollo Metrics (every PR improves one)

**Note (cycle 83):** Discovery 01 (EXP-BLIND-001, mycelium→CaCO3) was
reclassified from NOVEL HIT to RETRIEVAL per external auditor finding
F-063. The FICP subfield is a named, actively published field with its
own review papers. The single remaining novel hit (EXP-BLIND-003,
nanofiber→BBB) is PROVISIONAL pending re-verification with a stable
novelty rule (F-063) and extraction verification against source text
(F-065). See FAILURES.md F-063, F-064, F-065.

| Metric | Current | Target |
|---|---|---|
| Blind tests | 22 | 100 |
| Novel hits | 1 (PROVISIONAL) | 25 |
| Retrievals | 5 | 25 |
| Null results | 16 | 50 |
| Closed loops | 10 | 1000 |
| Verified mechanisms | 14% | 75% |
| Human intervention | High | Low |
| Domains | 7 | 100 |

### Required New Data Structures

Per CEO directive, the following classes must be added:

```python
class Observation:
    source, variables, units, measurement, uncertainty, conditions

class Intervention:
    variable, perturbation, expectation, outcome

class Theory:
    assumptions, laws, domain, failures

class Dimension:
    mass, length, time, current, temperature, amount

class Mechanism:
    entities, activities, organization, constraints, transitions
```

### Required New Algorithms

- Buckingham π theorem (dimensional consistency)
- PySR-style symbolic regression (open law search)
- Machamer–Darden–Craver mechanism induction
- Pearl intervention calculus (do-calculus)
- Bayesian optimization for experiment selection
- NK models for adjacent possible exploration
- Expected information gain maximization
