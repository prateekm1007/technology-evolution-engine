# Epistemic Layer

**Status:** the "why" layer. Separates observations, principles, and assumptions.
**Location:** `evidence/epistemic/`
**Phase:** 7C.2+ (per CEO correction 4 + final separation directive).

> The graph is not the asset.
> Trust in the graph is the asset.
> — CEO final directive

This layer exists so that when someone asks "Why does this edge
exist?", the answer breaks into three parts:

1. **What did we observe?** (observations/)
2. **Which principle was invoked?** (principles/)
3. **Which assumptions were introduced?** (assumptions/)
4. **Which reviewer approved it?** (in the EdgeJustification)

## Structure

```
evidence/
    epistemic/
        observations/   — Type A: what did we observe? (document facts)
        principles/     — Type B: what do we believe is true? (physical laws)
        assumptions/     — Type C: what are we taking for granted? (modeling choices)
```

## The three statement types (NEVER mixed)

### Type A — Observations

```typescript
interface Observation {
    source: string;        // document ID
    statement: string;     // what was observed
    evidence: string[];    // citations
}
```

Example: "Patent US20240194939A1 contains CPC code H01M 10/0562."

These are facts about documents. They are externally verifiable.
They do NOT interpret — they record.

### Type B — Principles

```typescript
interface Principle {
    name: string;            // e.g., "charge conservation"
    description: string;     // what the principle states
    references: string[];   // where it is established
}
```

Example: "Charge conservation requires ion transport between electrodes."

These are named physical/economic laws. They are grounded in
established science. They do NOT observe — they explain.

### Type C — Assumptions

```typescript
interface Assumption {
    statement: string;    // the assumption
    rationale: string;    // why it seems reasonable
    reviewer: string;     // who made it
}
```

Example: "Capability maturity can be approximated from CPC evidence."

These are modeling choices that the system depends on but cannot
prove. They are the most vulnerable to being wrong. Recording
them explicitly is what makes the graph auditable rather than
assertive.

## Why this separation matters

If, six months from now, someone asks:

> "Why does EDGE-025 exist (ELECTROCHEMICAL_ENERGY_STORAGE REQUIRES ION_TRANSPORT)?"

The answer is:

1. **Observation:** No observation needed — this is a structural edge,
   not an evidence edge. (If it were an evidence edge, we'd cite the
   patent + CPC code.)
2. **Principle:** "charge conservation" — electrochemical storage
   requires ions to move between electrodes to balance electron flow.
3. **Assumption:** A-003 ("structural invariants are stable across time")
   — we're assuming this physical necessity held in 1990 and still
   holds in 2026.
4. **Reviewer:** coder_agent_001 / 2026-08-02, confidence STRUCTURAL.

That four-part answer is what turns a graph into an auditable body
of knowledge.

## The four-layer architecture (complete)

| Layer | Question | Artifact | Location |
|---|---|---|---|
| Constitutional | What are we allowed to do? | Rules | repo root (10 files) |
| Experimental | How should we measure it? | Formulas | evidence/experiments/ |
| Observation | What did we observe? | Evidence | evidence/observations/ |
| **Epistemic** | **Why does this edge exist?** | **Justifications** | **evidence/epistemic/** |

The epistemic layer is further divided into:

| Sub-layer | Question | Schema |
|---|---|---|
| observations/ | What did we observe? | Observation |
| principles/ | What do we believe is true? | Principle |
| assumptions/ | What are we taking for granted? | Assumption |
