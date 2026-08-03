# MASTER_PROTOCOL

> If a document does not directly increase truth, reduce risk, increase
> reproducibility, or improve execution, it shall not exist.
> — CEO directive, Master Protocol consolidation

This is the single document that governs how the system produces
engineering packages. Everything else — the code, the tests, the
data — implements what this document defines. The coder reads this
document and nothing else before producing a package.

The protocol decides. The coder executes.

---

## The single command

```
INPUT:  A problem statement (e.g., "Build an EV battery pack")
OUTPUT: MASTER_PACKAGE.md — a single document with 11 sections
```

The coder does not decide what to produce. The protocol defines the
11 sections. The coder fills each section honestly.

---

## The 11 sections

Every package MUST contain all 11 sections, in order. A section that
cannot be filled is marked BLOCKED with a stated reason — it is never
skipped.

### 0. PURPOSE

What are we building and why?

One paragraph. State the primary objective. State the success metric.
State the package maturity level (see §Maturity below).

### 1. REQUIREMENTS

List every requirement. Classify each:

- MANDATORY — failure makes the design fail in its primary purpose
- DESIRABLE — improves the design, may be traded with justification
- ASPIRATIONAL — a goal, not a commitment
- EXPERIMENTAL — being tested for future inclusion

Two MANDATORY requirements that directly conflict block the package
(see §Consistency). A conflict between MANDATORY and DESIRABLE is
resolved by the MANDATORY winning, recorded as a tradeoff (§6).

### 2. EVIDENCE

What has humanity already learned about building this?

Study reality before creating reality. Minimum: existing products,
failed products, patents, academic literature, standards, supplier
data. Every source carries a rank (A-I) determining its weight.

Every claim in the package MUST cite at least one evidence ID from
this section. A claim without evidence is a hallucination.

### 3. DECOMPOSITION

Break the design into subsystems, components, interfaces, dependencies.

Every component has: name, function, mass, cost, supplier, alternatives.
Every interface has: type (electrical, thermal, mechanical, communications,
manufacturing, service), and a status (PASS / PASS_WITH_CONDITIONS /
MARGINAL / BLOCKED / REJECTED).

Mass stack-up: every component's mass must be listed. The total MUST
equal the sum of the parts plus an explicitly justified margin. A bare
mass total is forbidden — the stack-up is the only permitted form.

### 4. ALTERNATIVES

For every major design decision, at least 3 alternatives (primary + A + B).

Each alternative has: description, tradeoff, evidence. A single-path
recommendation is a single point of failure and is forbidden.

### 5. CONSISTENCY

Are the numbers physically possible? Are the requirements compatible?

Checks:
- Arithmetic: mass stack-up sums to total. Cost BOM sums to total.
- Units: energy density = energy / mass. Verify the arithmetic.
- Dimensions: torque = force × distance. Verify the units.
- Requirements: two MANDATORY requirements cannot directly conflict.
  If they do, the package is REJECTED until one is demoted or the
  design changes.

If any check fails, the affected claim is retracted (§10).

### 6. TRADEOFFS

For every decision: what did you gain? What did it cost? What did you sacrifice?

A decision without a stated sacrifice is not a decision — it is a preference.

### 7. ADVERSARIAL REVIEW

Why will this fail? Who disagrees? What is missing?

Four reviewers attack the design:
1. Chief Engineer — physics, tolerances, manufacturing
2. Manufacturing Expert — yield, assembly, supply chain
3. Economist — unit economics, margins, break-even
4. Customer — usability, maintenance, value proposition

Each reviewer attempts to destroy the proposal. If any finds a fatal
flaw, the package is REJECTED. Minor issues are recorded as conditions.

### 8. IMPLEMENTATION

BOM, manufacturing plan, assembly sequence, procurement.

Every BOM line has: supplier, part number, unit price, quantity, lead
time, quotation date, quotation expiry, landed cost. A line without a
quotation date is ESTIMATED and must be labeled as such. PRODUCTION
packages require all lines QUOTED.

### 9. VALIDATION

What has been tested? What hasn't? What failed?

Every test is one of three types (these cannot be conflated):
- ANALYTICAL_ESTIMATE (L2): derivation from first principles
- NUMERICAL_SIMULATION (L3): governing equations solved numerically
- PHYSICAL_VALIDATION (L4-L9): physical test on a real unit

Every test has pre-stated pass criteria (committed before the test
runs, not alongside the results). FAIL is a valid result — it is not
hidden. A FAIL triggers a retraction (§10).

Validation levels:
- L0: hypothesis (no evidence beyond the claim)
- L1: literature support (published sources exist)
- L2: analytical estimate (derived from first principles)
- L3: numerical model (governing equations solved)
- L4: bench validation (physical test, sub-scale)
- L5: subsystem validation (physical test, full subsystem)
- L6: prototype (full prototype tested in lab)
- L7: pilot deployment (tested in real environment)
- L8: production candidate (pre-production units built and tested)
- L9: production deployment (at scale, measured against reality)

### 10. RETRACTIONS

What claims were retracted? Why? What replaces them?

A retracted claim is not deleted — it is marked RETRACTED with a
reason, a date, and a replacement (or explicit WITHDRAWN status).
The Retraction Registry is append-only. No claim may be silently
edited.

Reason categories: NUMERICAL_CONTRADICTION, SEMANTIC_CONTRADICTION,
EVIDENCE_INVALIDATED, MEASUREMENT_SUPERSEDED, ASSUMPTION_FALSIFIED,
KILL_TEST_FAILED, DESIGN_CHANGE, EXTERNAL_AUDIT.

A package with unresolved retractions (RETRACTED with no replacement)
is BLOCKED.

### 11. FINAL VERDICT

APPROVED | APPROVED_WITH_CONDITIONS | REJECTED | BLOCKED

The verdict is determined by the preceding sections, not by the coder's
judgment. If any MANDATORY requirement is unmet: REJECTED. If any
consistency check fails: REJECTED. If any kill test FAILS unmitigated:
REJECTED. If any test is NOT_RUN: APPROVED_WITH_CONDITIONS (at best).
If all tests PASS and all retractions are resolved: APPROVED.

---

## Typed status (replaces numerical confidence)

No claim in any package may carry a numerical confidence, probability,
certainty, or reliability value. The system has no calibration data,
no decades of observations, no millions of validation samples. A
number like "58% confidence" is false precision.

Every claim carries a typed status block:

```
validation_level: L0-L9
evidence_strength: ABSENT | WEAK | MODERATE | STRONG | VERY_STRONG
experimental_validation: ABSENT | BENCH | SUBSYSTEM | PROTOTYPE | PILOT | PRODUCTION
status: PASS | PASS_WITH_CONDITIONS | MARGINAL | BLOCKED | REJECTED | PLAUSIBLE
```

The single exception: Monte Carlo simulations may report numerical
probabilities internal to the simulation, labeled SIMULATION_INTERNAL.
These may not be promoted to claim confidence.

---

## Maturity levels

A package declares its maturity:

- CONCEPT: idea + classification + state vector
- DECISION: + alternatives + constraints + economics
- EVALUATION: + simulations + benchmarks + adversarial review
- PROTOTYPE: + manufacturing plan + CAD + validation plan
- PRODUCTION: + production specs + supplier traceability + field data

No package is "complete." No package is a "blueprint." The maturity
level is declared on the package, not implied.

---

## Forbidden language

The following are forbidden in any package:

1. Numerical confidence (e.g., "confidence: 58%"). Use typed status.
2. PASS/FAIL percentages (e.g., "85.7% PASS"). Use STATUS enum.
3. "Complete blueprint" or "complete engineering blueprint." Use the
   maturity level.
4. Simulation mislabeling (e.g., calling analytical estimates
   "simulations"). Use the correct test type.
5. Uncalibrated probability, certainty, or reliability percentages.

The scanner (scripts/enforce_law27.py) mechanically enforces this.

---

## The principle

> If a document does not directly increase truth, reduce risk,
> increase reproducibility, or improve execution, it shall not exist.

Apply this to every document in the repository. If it doesn't pass,
archive it. The code that implements the rules stays. The tests that
verify the code stay. The data that records the history stays. The
documents that describe documents — those go.

---

## What lives in this repository

| What | Why it exists | Principle test |
|---|---|---|
| MASTER_PROTOCOL.md (this file) | The factory | Increases reproducibility |
| FAILURES.md | Institutional memory of failures | Increases truth |
| CONSTITUTION.md | Research-process laws (8 laws) | Increases truth (Law 7, Law 8) |
| ANTI_ENTROPY.md | Operational anti-entropy rules | Reduces risk |
| web/backend/ (code) | The engines (Oracle, Retraction, Test) | Improves execution |
| product/ (code) | The analyzer pipeline | Improves execution |
| scripts/ (code) | Scanners, registration, audit | Improves execution |
| tests/ (code) | Verifies the code works | Increases reproducibility |
| data/ (JSON) | The graph, ledger, registries | Increases truth |
| examples/ | Produced packages | Increases reproducibility |
| archive/ | Consolidated/retired documents | History (Law 7) |

Everything not in this table should be archived. The coder does not
read archived documents. The coder reads MASTER_PROTOCOL.md and
FAILURES.md. That is enough.

---

## The coder's contract

1. Read MASTER_PROTOCOL.md (this document).
2. Read FAILURES.md (do not re-introduce past failures).
3. Receive the INPUT.
4. Produce MASTER_PACKAGE.md with all 11 sections.
5. Register retractions in the Retraction Registry (P7, in code).
6. Register tests in the Test Registry (P8, in code).
7. Run the scanner on the package. If it fails, fix and re-run.
8. Commit, push, paste git log --oneline -1.

The protocol decides what gets produced. The coder executes.
