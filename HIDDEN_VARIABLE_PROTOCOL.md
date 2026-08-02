# HIDDEN_VARIABLE_PROTOCOL — Phase 12A

**Status:** constitutional document (hidden-variable attack).
**Location:** repo root.
**Phase:** 12A.

> What, exactly, is the model predicting?
> — CEO directive, Phase 12

## The attack

Formula B looks like:
```text
velocity × adjacency × feasibility
```

But the real signal might be:
```text
cost_decline × infrastructure_growth
```
or
```text
manufacturing_scale × regulation
```
or
```text
expert_selection_bias
```
or simply:
```text
time itself
```

## Required questions

### Q1: Is velocity merely a proxy for cost decline?

TRL rises when investment flows. Investment flows when cost is falling.
So dTRL/dt may be a proxy for d(cost)/dt.

**Test:** Replace velocity with cost_velocity only. If precision holds, velocity was a proxy.

### Q2: Is adjacency merely a proxy for time?

As time passes, more combinations exist. Symmetric difference shrinks
because the space fills in. So adjacency may just be measuring how
"late" it is.

**Test:** Replace adjacency with a simple time index (year - 1990). If precision holds, adjacency was a proxy for time.

### Q3: Is feasibility merely a proxy for maturity?

Feasibility gates check TRL >= 7. This is almost equivalent to "is
the capability mature?" — which is the static readiness the model
rejected. Feasibility may be doing nothing the velocity term isn't.

**Test:** Remove feasibility. If precision holds, feasibility was redundant.

### Q4: Is time itself the signal?

All events happen over time. Cost falls over time. TRL rises over time.
Infrastructure grows over time. Maybe the model is just predicting
"things that happen later happen later."

**Test:** Replace the entire formula with `score = year`. If precision is non-zero, time alone is the signal.

## How to run the tests

Each test replaces one component of Formula B with a simpler alternative.
If the simpler alternative achieves similar precision, the replaced
component was a proxy — it adds no independent signal.

If the simpler alternative achieves LOWER precision, the replaced
component contributes independent signal — it is NOT merely a proxy.

## The honest framing

If velocity is a proxy for cost decline, the model is still useful —
but the MECHANISM is economic, not technological. The model would be
saying "inventions happen when costs fall" rather than "inventions happen
when capabilities mature." Those are different theories with different
policy implications.

If time itself is the signal, the model is saying "everything eventually
happens" — which is trivially true and scientifically useless.
