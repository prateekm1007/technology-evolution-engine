# ENGINEERING_PRINCIPLES

**Status:** Constitutional document for The Blueprint engineering.
**Location:** repo root.
**Phase:** BP-1.

> This is how the coder fights entropy. Not with intelligence.
> With discipline.
> — CEO directive, BP-1

This document defines the engineering principles that govern
how The Blueprint is built. It is the operational complement
to BLUEPRINT_CONSTITUTION.md (which defines what the product
must do). This document defines how the team must work.

---

## Principle 1 — Observe before designing.

Before designing anything, study what already exists:

```text
What products already do this?
Why did they succeed or fail?
What components do they use?
What patents protect them?
What do users complain about?
What recalls involved them?
```

Per CONSTITUTION.md Rule 8: learn from reality before creating
reality. A design that ignores existing products is a
hallucination, not a design.

## Principle 2 — Every component has alternatives.

No component is irreplaceable. For every component in the BOM:

```text
Primary: the best option (cost, availability, performance)
Alternative A: second-best (different supplier or technology)
Alternative B: third option (fallback for supply disruption)
Alternative C: off-the-shelf equivalent (last resort)
```

If a component has no alternatives, it is a single point of
failure and must be flagged as a critical dependency.

## Principle 3 — Constraints propagate.

Constraints are not independent. A battery density constraint
propagates to vehicle weight, which propagates to motor size,
which propagates to cost. The system must model these
propagations as a graph, not a list.

```text
battery density → vehicle weight → motor size → cost
```

A constraint that is modeled in isolation will produce
optimizations that fail globally.

## Principle 4 — Numerical certainty is never assigned to claims without repeated experimental validation.

> A weather forecast can legitimately say "58% probability of
> rain" because it has decades of data, repeated observations,
> calibration curves, and millions of validation samples.
> The Blueprint has none of those things. Therefore "confidence
> = 58%" is forbidden.
> — Consolidated review, post-BP-2 (Law 27)

Per Law 27 (BLUEPRINT_CONSTITUTION.md), no claim in a Blueprint
may carry a numerical confidence, probability, certainty, or
reliability value unless the claim has been validated by
repeated physical experiment with a calibration curve.

### What is forbidden

```text
confidence: 0.58
confidence: 58%
probability = 0.83
certainty = 70%
reliability = 92%
```

### What is required instead

Every claim must declare its epistemic status as a typed object:

```text
validation_level: L2          // L0 hypothesis → L9 production deployment
status: PLAUSIBLE              // PASS / PASS_WITH_CONDITIONS / MARGINAL / BLOCKED / REJECTED
evidence_strength: MODERATE    // ABSENT / WEAK / MODERATE / STRONG / VERY_STRONG
experimental_validation: ABSENT  // ABSENT / BENCH / SUBSYSTEM / PROTOTYPE / PILOT / PRODUCTION
```

### The single exception

Monte Carlo simulations may report numerical probabilities
internal to the simulation (e.g., "thermal runaway probability
under Monte Carlo: 0.12"). Such numbers must be labeled
`SIMULATION_INTERNAL` and may not be promoted to a claim
confidence — they describe the model, not the world.

### Relationship to the original Principle 4

The original Principle 4 stated: "Confidence is never 1.0.
The maximum confidence is 0.95 (per EP-16)." This permitted
a continuous scale of false precision — 0.95, 0.85, 0.61,
0.50 — none of which had calibration behind them.

The amended Principle 4 forbids the numerical form entirely
for claims without experimental validation. The typed status
block is the only permitted vocabulary. This is stronger than
"never 1.0" — it is "never a number, without validation."

## Principle 5 — Failures are cataloged, not hidden.

Every failure mode is recorded in the FAILURE_LIBRARY with:
- The failure scenario
- The probability of occurrence
- The severity of impact
- The mitigation strategy

Failures are not embarrassing — they are data. A system that
has never failed has never been tested.

## Principle 6 — Every output is reproducible.

Given the same input, the system must produce the same output.
Non-determinism is acceptable only in:
- Monte Carlo simulation (where randomness is the point)
- Evidence retrieval timestamps (which change over time)

The blueprint compilation itself is deterministic.

## Principle 7 — The product includes its own audit trail.

Every blueprint ships with:
- The evidence that supports it
- The assumptions it relies on
- The unknowns it has not resolved
- The alternatives it considered and rejected
- The confidence in each recommendation

A blueprint without its audit trail is an opinion. A blueprint
with its audit trail is a decision-ready artifact.

## Principle 8 — Simplicity is the default.

When choosing between a simple solution and a complex one:
- Start with the simple solution
- Test it against reality
- Add complexity only when the simple solution demonstrably fails
- Document why complexity was added

This is the compression test (COMPRESSION_TEST.md) applied to
product design, not just to formulas.

## Principle 9 — Maintenance is designed, not added.

A product's maintenance cost is determined at design time, not
at deployment time. The design must specify:
- Which components are field-replaceable
- What tools are required for repair
- What diagnostic procedures exist
- What spare parts are stocked
- What training field technicians need

A design that requires factory return for repair is a design
that will fail in the field.

## Principle 10 — The world changes; the blueprint must track it.

Evidence decays. Prices change. Suppliers go bankrupt.
Regulations shift. The blueprint must include:
- Evidence timestamps (when was this verified?)
- Decay indicators (which evidence is stale?)
- Update triggers (what events should trigger re-verification?)

A blueprint that is correct today but wrong in 6 months is
a snapshot, not a living document.
