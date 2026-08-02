# INEVITABILITY_PROTOCOL — Phase 10F

**Status:** constitutional document (predict conditions of inevitability).
**Location:** repo root.
**Phase:** 10F.

> Do not attempt to predict inventions.
> Attempt to predict the conditions under which inventions become inevitable.
> — CEO directive, Phase 10F

> What could not have been prevented from happening?
> — CEO directive, Phase 10F

## The deepest change

Stop asking:
```text
What might happen?
```

Ask:
```text
What could not have been prevented from happening?
```

This question forces the model to think in terms of pressure, tension,
capability accumulation, and constraint collapse. It is much closer
to the way technological history actually unfolds.

## What "inevitable" means

A combination is INEVITABLE at time T when:
1. Its capabilities are accumulating (TRL rising, cost falling)
2. Its constraints are weakening (regulatory, physical, economic)
3. Its adjacency is closing (existing combinations are approaching it)
4. Its bottleneck is approaching resolution
5. No alternative path satisfies the same need

When all five conditions hold, the invention is not "possible" — it
is "inevitable." It will happen unless prevented by an external shock.

## The inevitability score (candidate)

```text
inevitability(combo, T) =
    capability_accumulation(combo, T)    — are capabilities rising?
  × constraint_collapse(combo, T)       — are constraints falling?
  × adjacency_closing(combo, T)        — is the gap to existing closing?
  × bottleneck_resolution(combo, T)    — is the blocker about to give?
  × (1 - alternative_available)        — is there no substitute?
```

If all five factors are high, the combination is INEVITABLE. If any
factor is zero, the combination is merely possible, not inevitable.

## Why this is closer to the north star

The north star is:
```text
available capabilities + removed constraints + institutions + economics + time = reachable possibilities
```

"Inevitable" is the limiting case of "reachable":
- Capabilities have accumulated sufficiently
- Constraints have been removed
- Time has passed
- The combination is in the adjacent possible
- No alternative path exists

The model should identify combinations that are approaching this
limiting case — where invention is no longer a question of "if" but
"when."

## Historical examples

### Li-ion EVs (inevitable by ~2008)

By 2008:
- Li-ion capability: TRL 9 (mature, cost falling)
- Thermal management: TRL 9 (required for EV packs)
- Fast charging: TRL 5 (rising, approaching)
- Cost: falling rapidly ($1000→$300/kWh)
- Regulatory: UN38.3 in force (compliant)
- Infrastructure: beginning to expand (Tesla Roadster proving ground)
- Alternative: NiMH EVs had failed (GM EV1)

Li-ion EVs were INEVITABLE by 2008. The Tesla Roadster was the first
proof; the Leaf and Volt (2010) were the mass-market confirmation.
The model should have identified this inevitability.

### Solid-state batteries (not yet inevitable as of 2026)

As of 2026:
- Solid electrolyte capability: TRL 5-6 (lab to pilot, not mature)
- Manufacturing: TRL 3-4 (sintering yield issues)
- Cost: very high (not approaching threshold)
- Regulatory: not yet applicable (no standard for solid-state)
- Alternative: liquid Li-ion is sufficient (no pressure to switch)

Solid-state batteries are POSSIBLE but not INEVITABLE. The model
should identify this distinction.

## What this changes

The model stops being a "possibility predictor" and becomes an
"inevitability detector." It doesn't predict WHAT will be invented —
it predicts the CONDITIONS under which invention becomes unavoidable.

This is closer to Hayek (information diffusion), Arthur (recursive
combination), Kauffman (adjacent possible), Fleming (recombinant
uncertainty), and Hidalgo (capability space) than the original
convergence model ever was.
