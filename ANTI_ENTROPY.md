# ANTI-ENTROPY & DRIFT CONTROL

**Status:** Active rule set.
**Read this file BEFORE writing any code in this repository.**

This repository has a documented history of entropy:
- F-005 (ledger corruption predating version control)
- F-006 (silent degradation instead of loud failure)
- F-011 (a "verified" stamp with no evidence)
- F-013/F-015 (the same fix landed in 1 of 3 readers)

Entropy is not a one-time event. It is the default state of a codebase
that doesn't actively resist it. The rules below are the active
resistance.

---

## Anti-Entropy & Drift Control

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
