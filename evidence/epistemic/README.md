# Epistemic Layer

**Status:** the "why" layer. Separates observations, principles, and assumptions.
**Location:** `evidence/epistemic/`
**Phase:** 7C.3 (frozen per CEO directive: stop implementation, document carefully).

> The graph is not the asset.
> Trust in the graph is the asset.
> — CEO final directive

> Epistemology is part of the architecture.
> — CEO realization, Phase 7C.3

This layer exists so that when someone asks "Why does this edge
exist?", the answer breaks into three parts:

1. **What did we observe?** (observations/) — with falsification criteria
2. **Which principle was invoked?** (principles/) — with scope and exceptions
3. **Which assumptions were introduced?** (assumptions/) — with falsification criteria
4. **Which reviewer approved it?** (in the EdgeJustification)

## The direction of dependency (correct)

```text
observation
      ↓
principle
      ↓
assumption
      ↓
evidence
      ↓
edge
      ↓
graph
      ↓
prediction
```

NOT this (the old, wrong direction):

```text
prediction
      ↓
graph
      ↓
edge
      ↓
justification
```

The dependency flows from observation upward. You observe first,
then invoke principles, then state assumptions, then create edges,
then build the graph, then make predictions. Predictions come LAST,
not first.

## The complete provenance chain

```text
EDGE-025
     │
     ▼
Observation(s)     — what did we observe? (N/A for structural edges)
     │
     ▼
Principle(s)       — which principle? (P-001: charge conservation)
     │
     ▼
Assumption(s)      — which assumptions? (A-003: stable across time)
     │
     ▼
Reviewer           — who approved? (coder_agent_001 / 2026-08-02)
     │
     ▼
Confidence         — how sure? (STRUCTURAL)
```

## The two rules (per CEO 7C.3)

### Rule 1 — Every assumption must be falsifiable

Each assumption (A-001 through A-005) has a `falsificationCriterion`
field stating what would prove it wrong. An assumption without a
falsification criterion is dogma, not a modeling choice.

### Rule 2 — Every principle must have a scope

Each principle (P-001 through P-011) has a `scope` field stating
where it applies, and an `exceptions` field for known cases where
it doesn't hold. A principle without a scope is universal, which
is almost always too strong.

## Structure

```
evidence/
    epistemic/
        observations/   — Type A: what did we observe? (document facts)
        principles/     — Type B: what do we believe is true? (physical laws, with scope)
        assumptions/     — Type C: what are we taking for granted? (with falsification criteria)
```

## The realization

Phase 5 was primarily about discovering that the original primitive
(co-occurrence) was insufficient.

Phase 7 has been about discovering that **epistemology is part of
the architecture**. The graph cannot be trusted unless every edge
traces back to observations, principles, and assumptions — each
explicitly recorded, each falsifiable, each scoped.

That realization is probably more valuable than the graph itself.

## The four-layer architecture (complete)

| Layer | Question | Artifact | Location |
|---|---|---|---|
| Constitutional | What are we allowed to do? | Rules | repo root (10 files) |
| Experimental | How should we measure it? | Formulas | evidence/experiments/ |
| Observation | What did we observe? | Evidence | evidence/observations/ |
| **Epistemic** | **Why do we believe it?** | **Justifications** | **evidence/epistemic/** |

The epistemic layer is further divided into:

| Sub-layer | Question | Schema | Rules |
|---|---|---|---|
| observations/ | What did we observe? | Observation | Must cite source |
| principles/ | What do we believe is true? | Principle | Must have scope + exceptions |
| assumptions/ | What are we taking for granted? | Assumption | Must have falsification criterion |
