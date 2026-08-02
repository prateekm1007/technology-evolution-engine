# Failures — Phase 8B

**Status:** evidence layer (failure records).
**Location:** `evidence/failures/`
**Phase:** 8B (per CEO directive: the system must now record failures).

> Every successful prediction is evidence.
> Every failed prediction is also evidence.
> — CEO directive, Phase 8B

## Schema

```typescript
interface FailureRecord {
    id: string;                    // e.g., "FAIL-001"
    prediction: string;            // what the model predicted
    outcome: string;              // what actually happened
    explanation: string;          // why the prediction failed
    violatedAssumption: string[]; // which assumptions (A-xxx) were wrong
    violatedPrinciple: string[]; // which principles (P-xxx) were wrong
    reviewer: string;             // who analyzed the failure
    errorType: string;            // FALSE_POSITIVE | FALSE_NEGATIVE | MISPLACED_CONFIDENCE | UNEXPLAINED
    severity: string;             // CRITICAL | MAJOR | MINOR | INFORMATIONAL
}
```

## Constitutional rule

```
Every successful prediction is evidence.
Every failed prediction is also evidence.
```

A model that only records successes is not a scientific instrument —
it's a marketing brochure. Failures are MORE informative than
successes because they reveal which assumptions and principles are
wrong. A success that can't be explained is false evidence (per
ERROR_TAXONOMY.md: INFORMATIONAL severity).

## Current failures

No failures recorded yet — the frozen-time backtest (Phase 8A/
BACKTEST_PROTOCOL.md) has not been executed. Failures will be
recorded here when the backtest runs.

## What goes here

- Every FALSE POSITIVE (predicted but didn't happen) → what was
  missed? Which constraint should have blocked the prediction?
- Every FALSE NEGATIVE (happened but wasn't predicted) → what was
  missing? Which capability or edge should have been present?
- Every MISPLACED CONFIDENCE (predicted with high confidence,
  outcome was opposite) → which principle was out of scope?
- Every UNEXPLAINED result → provenance chain broken; which
  EdgeJustification is missing?
