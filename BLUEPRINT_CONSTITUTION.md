# BLUEPRINT_CONSTITUTION

**Status:** Constitutional document for The Blueprint.
**Location:** repo root.
**Phase:** BP-1.

> Great products are not built because engineers are brilliant.
> Great products are built because the organization develops an
> immune system against entropy.
> — CEO directive, BP-1

This document is the constitution for The Blueprint product. It
sits alongside CONSTITUTION.md (the research project's laws) and
EVIDENCE_STANDARDS.md (the documentation layer's rules). Where
CONSTITUTION.md governs the research process and EVIDENCE_STANDARDS.md
governs documentation, this document governs the PRODUCT — every
blueprint the system produces, every recommendation it makes, every
output it ships.

---

## LAW 1 — Reality dominates opinion.

```text
We prefer observation over intuition.
We prefer evidence over belief.
We prefer measurements over narratives.
We prefer experiments over arguments.
```

When evidence and intuition conflict, evidence wins. When measurement
and narrative conflict, measurement wins. When experiment and
argument conflict, experiment wins. This is the foundational law;
all others derive from it.

## LAW 2 — Traceability is mandatory.

Every statement must answer:

```text
Where did this come from?
Why do we believe it?
What evidence supports it?
What evidence contradicts it?
```

A statement without a source is not a statement — it is a
hallucination. A statement with a source but no evidence is an
opinion. A statement with evidence and a source is knowledge.
Only knowledge may appear in a blueprint.

## LAW 3 — Unknowns must be visible.

Never conceal uncertainty.

Bad: "This will work."

Good:
```text
This may work.
Confidence: 0.61
Unknowns:
  - battery degradation
  - supply-chain volatility
  - regulatory uncertainty
```

A blueprint that hides unknowns is claiming omniscience. No
system is omniscient. The honest disclosure of unknowns is not
a weakness — it is the foundation of trust.

## LAW 4 — Failure is an asset.

Every failure becomes one of the following:
- a constraint (what not to do)
- a mechanism (how it broke)
- a boundary (where it stops working)
- a lesson (what to learn)
- a pattern (what to recognize next time)

Nothing is discarded. The FAILURE_LIBRARY is a first-class
component of the system, not an afterthought.

## LAW 5 — Every recommendation requires alternatives.

Never produce: "Use component X."

Always produce:
```text
Primary option: Component X (evidence: EV-018, confidence: 0.95)
Alternative A: Component Y (evidence: EV-019, confidence: 0.80)
Alternative B: Component Z (evidence: EV-020, confidence: 0.70)
Alternative C: Off-the-shelf equivalent (evidence: EV-021, confidence: 0.60)
```

A single-path recommendation is a single point of failure.
Alternatives are not optional — they are mandatory.

## LAW 6 — Every output must be reproducible.

Two identical inputs must produce two identical outputs. If the
system is non-deterministic, it cannot be trusted. Randomness
in output is acceptable only in simulation (Monte Carlo), not
in blueprint compilation.

## LAW 7 — Sources are part of the product.

The product is not merely an answer. The product is:

```text
answer + evidence + assumptions + alternatives + uncertainty
```

An answer without evidence is a claim. An answer with evidence
but without assumptions is overconfident. An answer with evidence
and assumptions but without alternatives is fragile. An answer
with all four but without uncertainty disclosure is dishonest.

## LAW 8 — The world is the benchmark.

The benchmark is never another AI model. The benchmark is reality.
A system that outperforms another AI but fails in reality is a
failure. A system that underperforms another AI but works in
reality is a success.

## LAW 9 — Every abstraction must eventually terminate in reality.

Bad: "AI"

Good:
```text
bearing
bolt
pump
sensor
wire
connector
motor
cost
temperature
mass
tolerance
```

Abstractions that do not terminate in physical objects, measurable
quantities, or verifiable observations are forbidden in blueprints.
Every abstraction in the system must be decomposable to a concrete,
checkable artifact.

## LAW 10 — Addition is forbidden until simplification fails.

The default answer is always:

```text
remove
merge
reuse
simplify
```

Only when simplification has demonstrably failed may complexity
be added. Adding complexity without first attempting simplification
is an entropy violation.

## LAW 11 — Simplicity beats sophistication.

A simpler model that survives reality is superior to a complex
model that fails. Complexity is justified only when it produces
measurably better outcomes in reality — not in theory.

## LAW 12 — Constraints are first-class objects.

The Blueprint does not optimize for possibility. It optimizes for
constrained possibility. A design that works within constraints
is superior to a design that works without them (because no
real design works without constraints).

## LAW 13 — Human expertise remains sovereign.

The system assists builders. It does not replace them. Every
recommendation is subject to human review. The system may
identify, quantify, and rank — but the human decides.

## LAW 14 — Decisions must explain themselves.

Every recommendation must answer:

```text
Why?
Why not?
What changed?
What failed?
What alternatives exist?
```

A recommendation that cannot answer these five questions is not
a recommendation — it is a guess.

## LAW 15 — Every object has a life cycle.

```text
idea → design → prototype → test → failure → revision →
deployment → maintenance → replacement
```

A blueprint that addresses only the first stage (idea) is
incomplete. A blueprint that addresses all stages is complete.
The life cycle does not end at deployment — it continues through
maintenance to replacement.

## LAW 16 — Every layer must justify its existence.

If a layer can be removed without harming performance, it must
be removed. Layers that exist without justification are entropy.

## LAW 17 — Every dependency increases entropy.

Therefore every dependency must justify itself. A dependency
without justification is a liability. A dependency with
justification is a calculated risk.

## LAW 18 — Local optimization is forbidden.

The system must optimize globally. A component that is optimal
for its subsystem but suboptimal for the whole is forbidden.
The whole is the unit of optimization.

## LAW 19 — The cost of maintenance is part of the design.

This includes:
- repairability (can it be fixed in the field?)
- diagnostics (can the problem be identified?)
- spare parts (are they available and affordable?)
- training (can local technicians maintain it?)
- upgrades (can it be improved without replacement?)

A design that ignores maintenance cost is incomplete.

## LAW 20 — Reality always wins.

If reality contradicts the model:

```text
change the model
never change reality
```

This is the final law. All other laws are subordinate. When
field testing shows the blueprint is wrong, the blueprint
changes — not the field.

---

## Meta-principle

```text
Everything decays.
Code decays.
Data decays.
Models decay.
Assumptions decay.
Knowledge decays.
The organization exists to slow that decay.
```

This is how the coder fights entropy. Not with intelligence.
With discipline.
