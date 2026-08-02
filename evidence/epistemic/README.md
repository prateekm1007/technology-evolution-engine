# Epistemic Layer

**Status:** structural layer for justifications, assumptions, and causal claims.
**Location:** `evidence/epistemic/`
**Phase:** 7C.2 (per CEO correction 4).

This layer separates epistemic artifacts from observations and
experiments. It contains:

## Structure

```
evidence/
    observations/      — measurement logs, analyses (Phase 5+)
    experiments/       — formulas, thresholds, coefficients (Phase 6+)
    epistemic/          — justifications, assumptions, causal claims (Phase 7C.2+)
        causality/      — causal claims and their evidence
        justifications/ — edge justifications (the "why" for every edge)
        assumptions/     — structural assumptions that aren't evidence-backed
```

## What goes where

| Artifact | Layer | Why |
|---|---|---|
| CPC code → capability mapping | Evidence (observations/) | It's an observation from a patent |
| Formula weights | Experimental (experiments/) | It's a candidate to be tested |
| "Edge #25 is REQUIRES because charge conservation" | Epistemic (epistemic/justifications/) | It's a justification |
| "Ions must move for the reaction to occur" | Epistemic (epistemic/assumptions/) | It's a structural assumption |
| "ENABLES requires historical counterfactual" | Epistemic (epistemic/causality/) | It's a causal claim definition |

## The four-layer separation

| Layer | Purpose | What it contains |
|---|---|---|
| Constitutional (repo root) | Governance | Rules, invariants, guardrails |
| Experimental (evidence/experiments/) | Formulas | Candidate scoring functions, thresholds |
| Observation (evidence/observations/) | Measurements | Logs, analyses, edge justification tables |
| **Epistemic (evidence/epistemic/)** | **Justifications** | **Why each edge exists, what assumptions it makes, what causal claims it asserts** |

The epistemic layer is the "why" layer. When someone asks "why does
this edge exist?", the answer lives here.
