# AEP_PROTOCOL

**Status:** Autonomous Excellence Protocol.
**Location:** TEE repo root.
**Phase:** AEP-1.

> The goal is not to create a genius.
> The goal is to create an excellence machine.
> The coder should not be allowed to choose excellence.
> The system itself should force excellence as the default outcome.
> — CEO directive, AEP-1

---

## Purpose

The AEP replaces ad-hoc development with a mandatory pipeline.
No work proceeds from idea to implementation without passing
through all 10 gates. Each gate has pass/fail criteria. Failure
at any gate means the work is rejected — not patched, not
"fixed later." The work goes back to the stage where the gate
failed.

This is the 6th governance layer:
1. Research process (CONSTITUTION.md)
2. Documentation (EVIDENCE_STANDARDS.md)
3. Architecture (REACHABILITY_CONSTITUTION.md)
4. Product (BLUEPRINT_CONSTITUTION.md + ENGINEERING_PRINCIPLES.md)
5. Coder directions (CODER_DIRECTIONS.md)
6. **Development pipeline (AEP_PROTOCOL.md — this document)**

---

## The 10-Gate Pipeline

```
REQUEST → Gate 1 → Gate 2 → Gate 3 → Gate 4 → Gate 4.5 → Gate 5 →
Gate 6 → Gate 7 → Gate 8 → Gate 9 → Gate 10 → Gate 10.5 → Gate 11 → SHIPPED
```

No gate may be skipped. No gate may be passed conditionally.
Each gate produces an artifact that becomes part of the work record.

The pipeline now includes three sub-gates that sit between the
canonical gates:
- **Gate 4.5 (Consistency)** — physics/dimensional consistency (existing).
- **Gate 10.5 (Kill-Test)** — every assumption has a kill test, none failed unmitigated (existing).
- **Gate 11 (Loop Closure)** — Honesty Loop closure; no forbidden language, all 10 priority engines PASS (NEW, see HONESTY_LOOP.md).

---

### Gate 1 — Comprehension Gate

**Question:** Do we understand what we're solving?

**Required answers:**
- What problem are we solving?
- Why does it matter?
- Who is affected?
- What constraints exist?
- How will success be measured?

**Pass criteria:** All 5 questions answered with specific, checkable
statements (not vague aspirations). Success metric must be quantitative.

**Failure:** Work is rejected. Return to request clarification.

**Artifact:** COMPREHENSION_RECORD (5 answers, stored in work record).

---

### Gate 2 — Research Gate

**Question:** Has the system studied reality before designing?

**Minimum requirements:**
- 10 papers (academic literature, ranked D+)
- 10 products (existing products, ranked E+)
- 10 failures (recalls, bankruptcies, postmortems, ranked F+)
- 10 patents (active or expired, ranked C+)
- 10 expert sources (standards, regulations, specifications, ranked B+)

**Pass criteria:** All 50 sources collected and ranked per the evidence
hierarchy. Each source has: id, source, rank, confidence, retrievedAt.

**Failure:** Work is rejected. Return to research.

**Artifact:** RESEARCH_RECORD (50+ evidence entries).

---

### Gate 3 — First-Principles Gate

**Question:** Has every assumption been decomposed to first principles?

**Required:** Every design assumption must be traced through a
constraint chain to a physical or economic first principle.

**Example:**
```
battery density → mass → motor efficiency → range
```

**Pass criteria:** Every assumption has a constraint chain. Every
chain terminates in a physical law, economic principle, or regulatory
requirement — not in another assumption.

**Failure:** Work is rejected. Return to constraint decomposition.

**Artifact:** CONSTRAINT_CHAIN_RECORD (assumption → chain → first principle).

---

### Gate 4 — Alternatives Gate

**Question:** Has the system considered alternatives?

**Required:** For every major design decision, at least 3 alternatives
(primary + A + B). Each alternative has: description, tradeoff,
evidence.

**Forbidden:** Producing only one solution.

**Pass criteria:** Every design decision has ≥ 3 alternatives documented.

**Failure:** Work is rejected. Return to alternative exploration.

**Artifact:** ALTERNATIVES_RECORD (decisions × alternatives).

---

### Gate 4.5 — Consistency Gate

**Question:** Are the numbers physically possible?

**Required checks:**
- The consistency engine must report 0 FATAL violations.
- The dimensional analysis engine must report 0 CONTRADICTION results.

**Pass criteria:** `consistencyViolations.fatal == 0` AND `dimensionalAnalysis.failed == 0`.

**Failure:** Work is rejected. Return to Gate 4 (Decomposition) and fix
the numerical contradictions. A blueprint with physically impossible
quantities cannot proceed to alternatives analysis.

**Artifact:** CONSISTENCY_RECORD (consistencyViolations + dimensionalAnalysis output).

---

### Gate 5 — Contradiction Gate

**Question:** Why is this wrong?

**Required answers:**
- Why is this wrong?
- Why would this fail?
- Who disagrees?
- What assumptions are false?

**Pass criteria:** All 4 questions answered with specific, checkable
contradictions — not vague "it might fail." Each contradiction must
reference evidence or a simulation.

**Failure:** Work is rejected. Return to contradiction search.

**Artifact:** CONTRADICTION_RECORD (4 answers, stored in work record).

---

### Gate 6 — Benchmark Gate

**Question:** How does this compare to the best in the world?

**Required identification:**
- Best product (who is better?)
- Cheapest product (who is cheaper?)
- Fastest product (who is faster?)
- Most reliable product (who fails less?)
- Most profitable product (who captures more value?)

**Pass criteria:** All 5 categories benchmarked against real
competitors (not estimates, not LLM inference).

**Failure:** Work is rejected. Return to benchmarking.

**Artifact:** BENCHMARK_RECORD (5 categories × competitor comparison).

---

### Gate 7 — Adversarial Gate

**Question:** Can 4 internal reviewers destroy the proposal?

**Required reviewers:**
1. Chief Engineer — challenges physics, tolerances, manufacturing
2. Manufacturing Expert — challenges yield, assembly, supply chain
3. Economist — challenges unit economics, margins, break-even
4. Customer — challenges usability, maintenance, value proposition

**Each reviewer attempts to destroy the proposal.** If any reviewer
finds a fatal flaw, the work is rejected.

**Pass criteria:** All 4 reviewers fail to find a fatal flaw.
Minor issues are recorded but do not block.

**Failure:** Work is rejected. Return to the stage where the flaw
was found (research, design, or economics).

**Artifact:** ADVERSARIAL_RECORD (4 reviews, pass/fail per reviewer).

---

### Gate 8 — Implementation Gate

**Question:** Is the design ready to be built?

**Only now** can the coder write code or produce specifications.

**Pass criteria:** All prior gates passed. Implementation plan exists
with: milestones, dependencies, timeline, budget.

**Failure:** Work is rejected. Return to Gate 7 (adversarial review
found something the plan doesn't address).

**Artifact:** IMPLEMENTATION_PLAN (milestones, timeline, budget).

---

### Gate 9 — Validation Gate

**Question:** Did the implementation work?

**Required answers:**
- What failed?
- What succeeded?
- What changed?
- What remains unknown?

**Pass criteria:** All 4 questions answered with specific results.
Failures are recorded, not hidden. Unknowns are declared, not concealed.

**Failure:** Work is rejected. Return to Gate 8 (re-implementation).

**Artifact:** VALIDATION_RECORD (4 answers, test results).

---

### Gate 10 — Postmortem Gate

**Question:** What did we learn?

**Required:** Every failure enters permanent memory. The system's
knowledge base grows with each completed work cycle.

**Pass criteria:** Postmortem document written. Failures cataloged in
FAILURE_LIBRARY. Lessons recorded in CODER_DIRECTIONS.md if
applicable. Assumptions updated if falsified.

**Failure:** Work is not considered complete until the postmortem
is written. No exceptions.

**Artifact:** POSTMORTEM_RECORD (failures, lessons, assumption updates).

---

### Gate 10.5 — Kill-Test Gate

**Question:** Does every assumption have a kill test, and have any kill tests already failed?

**Required checks:**
- Every assumption must have a kill test with a concrete, observable failure condition.
- Kill tests with status FAILED must be mitigated before the gate passes.
- Kill tests with status UNTESTED must be listed in the "Unknowns" section of the final output.

**Pass criteria:** `killTests.failed == 0` OR (all FAILED kill tests are mitigated AND listed in unknowns with confidence penalty).

**Failure:** Work is rejected. Return to Gate 7 (Adversarial) and either mitigate the failed kill test or explicitly accept it with a confidence penalty (minimum -0.05 per failed kill test).

**Artifact:** KILLTEST_RECORD (all kill tests with status, testedAt, mitigation).

---

### Gate 11 — Loop Closure Gate

**Question:** Has the artifact closed the Honesty Loop?

**Context:** Gate 11 is the 7th governance layer (HONESTY_LOOP.md)
applied as the final AEP gate. It sits AFTER Gate 10 (Postmortem)
and AFTER Gate 10.5 (Kill-Test). An artifact cannot ship until
Gate 11 closes the Honesty Loop.

**Required checks:**

1. **Forbidden language scan** — `scripts/enforce_law27.py` must
   exit 0 on the artifact. This means:
   - No `complete blueprint` phrasing (Law 28a)
   - No numerical confidence like `confidence: 58%` or
     `confidence: 0.58` (Law 27, 28c)
   - No `X% PASS` or `score: X%` verdicts (Law 28b)
   - No `simulation: N tests` mislabeling when the tests are
     analytical estimates (Law 28d)
   - No uncalibrated `probability`, `certainty`, or
     `reliability` percentages (Law 27)

2. **Typed claim wrappers** — Every claim in the artifact must
   carry the Law 29e wrapper: `validationLevel`,
   `evidenceStrength`, `experimentalValidation`, `status`,
   `evidenceIds[]`. Bare claims without wrappers are forbidden.

3. **Package maturity declared** — The artifact must declare
   its `package_maturity` (Law 29d): CONCEPT, DECISION,
   EVALUATION, PROTOTYPE, or PRODUCTION.

4. **10 priority engines pass** — Each of the 10 Honesty Loop
   priority engines (P1-P10, see HONESTY_LOOP.md) must produce
   output for the artifact with `STATUS: PASS` or
   `STATUS: PASS_WITH_CONDITIONS`. A `STATUS: BLOCKED` or
   `STATUS: REJECTED` from any engine blocks Gate 11.

5. **No unresolved retractions** — The Retraction Registry
   (P7) must contain no unresolved retractions for this
   artifact. All retractions must have either a replacement
   claim or an explicit `WITHDRAWN` status with rationale.

**Pass criteria:** All 5 checks pass. STATUS: PASS.

**Failure:** Work is rejected. The artifact remains in the
Honesty Loop at Stage 3 (REPLACE) or Stage 3a (RETRACT) until
closure. The artifact cannot ship.

**Artifact:** HONESTY_LOOP_CLOSURE_RECORD (JSON, stored in
`evidence/gates/gate_11_honesty_loop.json`).

---

## Knowledge Object Schema

Every object in the system carries its full knowledge context:

```typescript
interface KnowledgeObject {
    evidence: Evidence[]
    alternatives: Alternative[]
    assumptions: Assumption[]
    failures: Failure[]
    simulations: Simulation[]
    benchmarks: Benchmark[]
    constraints: Constraint[]
    regulations: Regulation[]
    tradeoffs: Tradeoff[]
}
```

An object without its full knowledge context is incomplete.
Per BLUEPRINT_CONSTITUTION.md Law 7: "Sources are part of the product."

---

## Pull Request Scorecard

Every PR must satisfy this scorecard:

| Category | Weight | Meaning |
|---|---|---|
| Correctness | 25% | Does it work? Is it accurate? |
| Simplicity | 15% | Is it as simple as possible? |
| Maintainability | 15% | Can it be maintained? |
| Robustness | 15% | Does it handle edge cases? |
| Performance | 10% | Is it efficient? |
| Explainability | 10% | Can it be explained? |
| Usability | 10% | Can it be used? |

**Minimum passing score:** 70% weighted average.

A PR with 100% correctness but 0% explainability scores:
25% + 0% + 15% + 15% + 10% + 0% + 10% = 75% — passes.

A PR with 100% correctness but 0% simplicity scores:
25% + 0% + 15% + 15% + 10% + 10% + 10% = 85% — passes, but
flagged for simplicity review.

A PR with 50% correctness scores:
12.5% + 15% + 15% + 15% + 10% + 10% + 10% = 87.5% — FAILS.
Correctness below 70% is an automatic fail regardless of other
scores.

---

## Excellence Formula

```text
excellence = knowledge × discipline × repetition × feedback × truthfulness
```

There is no box labelled "genius." That is intentional.

- **knowledge**: evidence base (20+ sources per blueprint)
- **discipline**: gate compliance (11/11 gates passed, including Gate 11 Loop Closure)
- **repetition**: consistent application (every work cycle)
- **feedback**: adversarial review + postmortem
- **truthfulness**: Rule 7 (never pretend uncertainty is certainty) + Law 27 (no numerical certainty without experimental validation)

If any factor is 0, excellence is 0. A system with knowledge but
no discipline produces hallucinations. A system with discipline
but no truthfulness produces confident errors. All 5 factors are
required.

---

## Interaction with existing governance

| Existing | AEP relationship |
|---|---|
| EVIDENCE_LOOP.md (3 checkpoints) | AEP extends: checkpoints become gates |
| EVIDENCE_STANDARDS.md (EP-1 to EP-16) | AEP enforces: every gate requires evidence |
| BLUEPRINT_CONSTITUTION.md (20 Laws + Rule 7) | AEP operationalizes: laws become gate criteria |
| CODER_DIRECTIONS.md (stage progression) | AEP gates apply within each stage |
| WCP_PROTOCOL.md (15 principles) | AEP implements: principles become gate requirements |

The AEP does not replace any existing governance. It adds a
mandatory pipeline layer that enforces all existing governance
through 10 sequential gates.

---

## Status

The AEP is documented and partially automated. The 10 canonical
gates plus 3 sub-gates (Gate 4.5 Consistency, Gate 10.5 Kill-Test,
Gate 11 Loop Closure) form the 13-checkpoint pipeline.

Mechanical enforcement:
- Gate 2 (Research): `scripts/check_aep_gate.py 2` checks source count.
- Gate 4 (Alternatives): `scripts/check_aep_gate.py 4` checks alternatives per decision.
- Gate 7 (Adversarial): `scripts/check_aep_gate.py 7` checks reviewer count.
- Gate 11 (Loop Closure): `scripts/enforce_law27.py` checks forbidden language; `tests/test_honesty_loop.py` verifies the loop's mechanical enforcement.
- All gates: `scripts/check_aep_gate.py --strict` runs the full check in CI.

Gate 11 was added in this commit (Honesty Loop v1.0) per the
consolidated review. The 10 priority engines (P1-P10) are
specified in their own `.md` files; code implementation of
each engine awaits its own AEP Gate 1 (Comprehension) work
item. The loop's enforcement scanner and tests ARE implemented
in this commit.

**Immediate application:** Gate 11 applies to all future work
starting from the next development cycle. Every artifact that
ships must close the Honesty Loop before it leaves the
repository.
