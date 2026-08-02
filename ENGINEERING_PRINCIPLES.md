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

## Principle 4 — Confidence is never 1.0.

No assertion is certain. The maximum confidence is 0.95 (per
EP-16). Every assertion carries:
- Evidence (ranked A through I)
- Assumptions (with falsifiers)
- Penalties (for uncertainty, risk, and gaps)

A confidence of 0.95 means "strongly supported by evidence but
not proven." A confidence of 0.50 means "supported but uncertain."
A confidence of 0.20 means "LLM inference only — unverified."

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
