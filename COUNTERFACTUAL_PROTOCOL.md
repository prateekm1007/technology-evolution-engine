# COUNTERFACTUAL_PROTOCOL — Phase 8C

**Status:** constitutional document (counterfactual reasoning).
**Location:** repo root.
**Phase:** 8C.

> The system must answer three questions.
> — CEO directive, Phase 8C

This document defines the counterfactual protocol — the methodology
for explaining why predictions succeeded or failed by examining what
WOULD have happened under different conditions.

---

## The three questions

### Question 1: Why did this happen?

When a prediction succeeds, explain the causal chain:

```text
What capabilities existed at T?
What constraints were removed by T?
What structural edges connected them?
Which principles made the combination reachable?
Which assumptions were load-bearing?
```

If the prediction succeeded but the causal chain can't be traced,
the success is INFORMATIONAL (per ERROR_TAXONOMY.md) — the model
got lucky, not smart.

### Question 2: Why didn't something else happen?

When a prediction succeeds, also check what DIDN'T happen:

```text
What other combinations were reachable at T?
Why didn't THEY appear by T+n?
What constraint blocked them?
Was the constraint correctly modeled?
```

This is the precision check. If the model flagged 10 combinations
and only 1 happened, the other 9 are false positives. The
counterfactual asks: WHY didn't they happen? If the model can't
explain, it's not distinguishing — it's flagging everything and
hoping some are right.

### Question 3: What would have needed to change?

When a prediction FAILS, explain what WOULD have made it succeed:

```text
Which capability was missing?
Which constraint was too strong?
Which principle was out of scope?
Which assumption was wrong?
```

This is the learning question. A failure without a counterfactual
explanation is just a data point. A failure WITH a counterfactual
explanation is a discovery — it tells the model what to fix.

---

## The counterfactual schema

```typescript
interface CounterfactualAnalysis {
    predictionId: string;          // the prediction being analyzed
    question: string;              // "why_did" | "why_didnt" | "what_would_change"
    analysis: string;              // the counterfactual reasoning
    assumptionsExamined: string[]; // which assumptions were tested
    principlesExamined: string[];  // which principles were tested
    conclusion: string;            // what the counterfactual reveals
    reviewer: string;
}
```

---

## Why this matters

Counterfactual reasoning is what separates a scientific model from
a pattern matcher. A pattern matcher says "X happened." A scientific
model says "X happened BECAUSE of Y, and if Y hadn't been present,
X wouldn't have happened, and if Z had been present instead, W
would have happened."

Without counterfactuals, the model can only describe. With
counterfactuals, it can explain — and explanation is the foundation
of trust.

Per the CEO's directive: the objective is "a machine that explains
why it deserves to be trusted." Counterfactual reasoning IS that
explanation.
