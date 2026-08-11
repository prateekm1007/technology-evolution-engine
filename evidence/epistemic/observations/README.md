# Observations — Type A Epistemic Statements

**Status:** epistemic layer (observations: what did we observe?).
**Location:** `evidence/epistemic/observations/`

An observation is a statement of fact about a document. It is NOT
an interpretation, a principle, or an assumption. It is what a
human or machine directly observed in a source document.

## Schema

```typescript
interface Observation {
    source: string;        // document ID (patent number, DOI, etc.)
    statement: string;     // what was observed (verbatim or direct)
    evidence: string[];    // citations (CPC code, page, claim number)
}
```

## What goes here

- "Patent US20240194939A1 contains CPC code H01M 10/0562."
- "Patent US12489120B2 contains CPC code H01M 4/86."
- "Regulation UN38.3 specifies test T.1 through T.8 for lithium battery transport."

## What does NOT go here

- Principles ("charge conservation requires ion transport") → principles/
- Assumptions ("CPC codes approximate capability maturity") → assumptions/
- Interpretations ("this patent is about solid-state batteries") → that's
  an interpretation of the CPC code, not an observation. The observation
  is: "the patent contains CPC code H01M 10/0562."

## Current observations

The observations for the 5-patent trusted graph are recorded in
`data/capability_graph.json` as EMBODIED_IN evidence edges. Each
evidence edge's `evidence[]` field contains the observation (e.g.,
`"CPC:H01M 10/0562"`). The full EdgeJustification records the
observation, the reviewer, and the confidence.
