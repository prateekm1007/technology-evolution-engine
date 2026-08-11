# TRAJECTORY_PROTOCOL — Phase 10A

**Status:** constitutional document (replace states with trajectories).
**Location:** repo root.
**Phase:** 10A.

> Do not optimize the formula. Destroy the formula.
> — CEO directive, Phase 10

> Static systems do not invent. Dynamic systems do.
> — CEO directive, Phase 10A

## The rejection

The previous formula used:
```text
readiness = min(TRL(t)) / 9
```

This measures the STATE of each capability at time T. It fails because
inventions emerge when capabilities are APPROACHING maturity, not when
they are already mature. The weakest-link principle (min) penalizes
the emerging capabilities that are about to break through — exactly
the capabilities that signal invention.

## The replacement

Replace:
```text
TRL(t)          — static state at time T
```

With:
```text
dTRL/dt         — rate of change of TRL at time T
```

A capability at TRL 5 that is rising (TRL 4→5 in 2 years) is more
invention-relevant than a capability at TRL 9 that has been stable
for 10 years.

## Required questions

1. **Is capability maturity accelerating?**
   - dTRL/dt > 0 means the capability is improving.
   - d²TRL/dt² > 0 means the improvement is accelerating.
   - Accelerating maturity signals approaching breakthrough.

2. **Is manufacturing cost decreasing?**
   - d(cost)/dt < 0 means cost is falling.
   - Wright's Law: cost decreases ~20% per doubling of production.
   - Accelerating cost decrease signals approaching economic viability.

3. **Are constraints weakening?**
   - Regulatory relaxation, physical limit circumvention, material
     substitution.
   - A weakening constraint opens previously-blocked combinations.

4. **Are regulations changing?**
   - New regulations create new feasibility gates.
   - Removed regulations remove gates.
   - Changed regulations shift thresholds.

5. **Is infrastructure expanding?**
   - Charging stations, grid capacity, recycling facilities.
   - Infrastructure expansion opens deployment pathways.

## Trajectory-based readiness (candidate formula)

```text
trajectory_readiness(capability, T) =
    α * dTRL/dt          (capability maturity velocity)
  + β * (-d(cost)/dt)    (cost decrease velocity)
  + γ * constraint_relief (constraint weakening rate)
```

Where α, β, γ are experimental weights (NOT constitutional).

For a combination:
```text
trajectory_readiness(combo, T) = max(trajectory_readiness(c, T) for c in combo)
```

Note: MAX, not MIN. The combination's invention potential is determined
by its FASTEST-RISING capability, not its weakest. The weakest-link
principle was wrong for invention prediction — it predicts stability,
not breakthrough.

## What this changes

The model stops asking "is this ready?" and starts asking
"is this approaching readiness?" The trajectory matters more than
the state. A capability at TRL 3 with dTRL/dt = +2/year is more
invention-relevant than one at TRL 9 with dTRL/dt = 0.
