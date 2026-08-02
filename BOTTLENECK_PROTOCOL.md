# BOTTLENECK_PROTOCOL — Phase 10D

**Status:** constitutional document (identify the single blocking factor).
**Location:** repo root.
**Phase:** 10D.

> What single thing prevents this combination from existing?
> This is probably more important than asking: what enables it?
> — CEO directive, Phase 10D

## The rejection

The previous model asked "what ENABLES this combination?" It looked
for capabilities that were present, constraints that were satisfied,
and edges that connected them. This is an enablement model.

But inventions often happen not because something new is ENABLED,
but because something old is REMOVED. The bottleneck is the single
constraint that, if removed, would make the combination possible.

## The replacement

For each candidate combination, ask:

```text
What is the ONE thing that, if changed, would make this combination
possible?
```

### Bottleneck identification

A bottleneck is the constraint with:
1. The highest impact on the combination's feasibility (removing it
   changes feasibility from FALSE to TRUE).
2. The shortest expected time to resolution (the constraint is
   weakening or about to be removed).

### Bottleneck types

| Bottleneck type | Example | Resolution signal |
|---|---|---|
| Physical | Energy density below theoretical limit | New chemistry discovered |
| Manufacturing | Dry electrode yield < 90% | Process improvement |
| Economic | Cost per kWh > $100 | Scale production |
| Regulatory | UN38.3 not yet passed | Test passed |
| Infrastructure | No charging stations | Infrastructure investment |

### Bottleneck-based scoring (candidate formula)

```text
bottleneck_score(combo, T) =
    1 / time_to_resolution(bottleneck(combo, T))
```

A combination whose bottleneck is about to be resolved (short time
to resolution) scores higher than one whose bottleneck is decades away.

This formula doesn't ask "is this ready?" — it asks "how soon will
the ONE thing blocking this be removed?"

## Why this is more important than enablement

Enablement asks: "What do we need?" (Additive — what must be present.)
Bottleneck asks: "What's in the way?" (Subtractive — what must be removed.)

In technological history, most inventions happen when a BOTTLENECK
is removed, not when a new capability is added. The transistor
happened when semiconductor physics became understood (bottleneck
removed), not when someone added a new component. Li-ion EVs happened
when cost dropped below $300/kWh (economic bottleneck removed), not
when someone invented a new capability.

The bottleneck is usually ONE thing. Finding it is more valuable
than listing everything that enables the combination.
