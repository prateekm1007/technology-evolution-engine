# REACHABILITY_CONSTITUTION

**Status:** Phase 15 Deliverable 3.
**Location:** repo root.
**Phase:** 15.

> The north star remains unchanged:
> available capabilities + constraints + institutions + economics
> + time → reachable possibilities.
> What changes is the architecture.
> — CEO directive, Phase 15

This document is the constitution for the reachability engine
architecture. It supersedes none of the prior constitutional
documents (CONSTITUTION.md, EVIDENCE_STANDARDS.md) — it extends
them to the new architecture. The frozen formula
`score = max(dTRL/dt) × adjacency` is preserved (Rule 1, Phase 14
close). This constitution governs how the next instruments are
built, not how the frozen formula is used.

---

## The six rules

### Rule 1: Classification before prediction

> Never ask "What will happen?" Ask "What kind of process is this?"

Before any formula runs, the process class (Discovery, Emergence,
Scaling, Coordination, Recombination — per PROCESS_CLASSIFIER.md)
must be identified. The class determines which mechanism (per
MECHANISM_REGISTRY_V2.md) is at work, which determines which
instrument (formula) is appropriate.

**Enforcement:** No backtest, no prediction, no synthesis may
proceed without first recording the process class. If the class
cannot be determined, the event is recorded as UNCLASSIFIED and
no formula runs. The classifier is a hard gate, not a soft hint.

**Why:** The Phase 14 failure was caused by applying the Emergence +
Recombination instrument (the frozen formula) to Scaling and
Coordination domains (semiconductors, telecom). Classification
before prediction would have prevented this.

### Rule 2: State before trajectory

> The state of the system determines what is reachable; the
> trajectory of the state determines when it becomes reachable.

State variables (per STATE_SPACE.md) are the foundation.
Trajectories (dTRL/dt, d²TRL/dt², dCost/dt) are derivatives of
state. A formula that uses trajectories without grounding them in
state variables is measuring motion without measuring position —
it cannot tell where the system IS, only where it is GOING.

**Enforcement:** Every formula must declare which state variables
it uses. A formula that uses a trajectory (e.g., dTRL/dt) must
declare the underlying state variable (e.g., capability_state).
Trajectories without state grounding are forbidden.

**Why:** The frozen formula uses dTRL/dt (a trajectory) but does
not explicitly track capability_state (the state). This is why it
cannot detect when a capability has "re-risen" — it sees the
trajectory as zero (plateaued) when the state has actually dropped
to track a new sub-capability.

### Rule 3: Mechanisms before formulas

> A formula is an instrument for a mechanism. Build the mechanism
> first; the formula follows.

Mechanisms (per MECHANISM_REGISTRY_V2.md) are the causal chains
that produce reachability. Formulas are the mathematical
instruments that detect when a mechanism is firing. Building a
formula without specifying its mechanism is curve-fitting.

**Enforcement:** Every formula must cite the mechanism it is an
instrument for. The frozen formula cites MECH-E001 and MECH-R001
(velocity detects rising capability; adjacency detects reachable
combination). A formula that cannot cite a mechanism is rejected.

**Why:** The Phase 13 "necessity but not sufficiency" framing
was a symptom of building a formula without specifying its
mechanism. The formula detected a signal without understanding
what produced the signal.

### Rule 4: Boundaries are assets

> The boundary of a theory is not a failure — it is the theory's
> most valuable output.

A theory that claims to apply everywhere is unfalsifiable. A
theory that states its boundary rigorously is testable. The
boundary tells future researchers what the theory does NOT
cover, which is as important as what it does cover.

**Enforcement:** Every theory, every formula, every mechanism
must come with a BOUNDARY statement: the conditions under which
it does NOT apply. The frozen formula's boundary is stated in
BOUNDARY_THEOREM.md. Future instruments must have equivalent
boundary statements.

**Why:** The Phase 14 stress tests failed because the frozen
formula had no stated boundary. It was applied to domains it was
not designed for, producing 0/4 survival. If the boundary had
been stated from Phase 11, the stress tests would have been
designed differently — or not run at all.

### Rule 5: Failures are observations

> A failed prediction is not a setback — it is an observation that
> the current theory does not cover this case.

Failures are classified (per BOUNDARY_REGISTRY.md), not ignored
or explained away. A failure that fits a known pattern confirms
the boundary. A failure that does NOT fit a known pattern reveals
a new pattern — which may require a new class, a new mechanism,
or a new state variable.

**Enforcement:** Every failed prediction must be recorded in
BOUNDARY_REGISTRY.md with a typed entry. The failure must be
classified into a pattern (1-5 from Phase 14R) or recorded as
NEW_PATTERN. Failures without classification are forbidden.

**Why:** The Phase 13 counterexamples (CE-001 to CE-003) were
initially treated as embarrassments to be explained away. The
Phase 14R reflection re-classified them as observations that
revealed the emergence-vs-exploitation boundary. The shift from
"failure as setback" to "failure as observation" was the project's
methodological turning point.

### Rule 6: Simplicity dominates complexity

> Failure → classification → understanding → simplicity.
> NOT failure → patch → complexity → success.

When a theory fails, the response is NOT to add complexity
(another term, another constant, another threshold). The response
is to classify the failure, understand its cause, and simplify.
Complexity is the last resort, not the first.

**Enforcement (per COMPRESSION_TEST.md):** The compression ratio
(explanatory power / number of components) must be monitored. If
complexity grows faster than explanatory power, the theory is
violating this rule. The Phase 12 ablation (Task 37) is the
canonical example: the formula simplified from 3+ factors to 2
(velocity × adjacency) without loss of precision.

**Why:** The original co-occurrence model (Phase 1-5) failed by
adding complexity (more shared-label matching, more normalization)
without understanding. The Phase 10 pivot (velocity × adjacency)
succeeded by simplifying. The Phase 14S boundary theorem
continued this discipline: 3 documents, no patches, no complexity.
Phase 15 must continue it.

---

## What this constitution does NOT do

- It does not modify the frozen formula. The formula is preserved
  per Phase 14 close. This constitution governs the NEXT
  instruments.
- It does not override CONSTITUTION.md (Laws 1-8) or
  EVIDENCE_STANDARDS.md (EP-1 to EP-12). It is additive — it
  extends the constitution to the reachability-engine architecture.
- It does not claim the six rules are exhaustive. A seventh rule
  may emerge (e.g., "Agency is not modeled" — the rule that the
  engine measures landscape, not actors). Rules are added when
  the evidence demands them.
- It does not authorize building new formulas. Phase 15 builds
  the classification layer only. Formula-building is post-Phase-15.

---

## Relationship to existing governance

| Existing document | Phase 15 status |
|---|---|
| CONSTITUTION.md (Laws 1-8) | UNCHANGED. Still binding. |
| EVIDENCE_STANDARDS.md (EP-1 to EP-12) | UNCHANGED. Still binding. |
| FORMULA_B_FROZEN.md | UNCHANGED. Frozen formula preserved. |
| EVIDENCE_LOOP.md | UNCHANGED. Checkpoints still apply. |
| EVIDENCE_FALSIFIERS.md | UNCHANGED. Existing FEC entries stand. New mechanisms may add FEC entries. |
| FAILURES.md | UNCHANGED. Existing failures stand. New failures (from new instruments) append. |
| BOUNDARY_REGISTRY.md | UNCHANGED. Existing boundary cases stand. New boundary cases append. |
| REACHABILITY_CONSTITUTION.md (this document) | NEW. Governs the reachability-engine architecture. |

The reachability constitution is the third layer of governance:
1. Code layer (CONSTITUTION.md Laws 1-8)
2. Documentation layer (EVIDENCE_STANDARDS.md EP-1 to EP-12)
3. Architecture layer (REACHABILITY_CONSTITUTION.md Rules 1-6)

Each layer addresses a different failure mode. The code layer
catches implementation errors. The documentation layer catches
narrative over-claims. The architecture layer catches
over-extension — applying an instrument outside its boundary.

---

## Pre-stated falsifier (EP-4)

**Claim:** The six rules (Classification before prediction, State
before trajectory, Mechanisms before formulas, Boundaries are
assets, Failures are observations, Simplicity dominates
complexity) are sufficient to govern the reachability-engine
architecture.

**Falsifier:** A reachability-engine failure that violates none
of the six rules — i.e., an instrument that classified correctly,
grounded in state, cited its mechanism, stated its boundary,
recorded its failures, and stayed simple, but STILL produced
wrong predictions. Such a case would mean the six rules are
necessary but not sufficient, and a seventh rule is needed.

**Status:** PENDING. No such case has occurred (no reachability-engine
instruments have been built yet).
