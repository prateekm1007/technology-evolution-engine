# TENSION_PROTOCOL — Phase 10C

**Status:** constitutional document (introduce tension between forces).
**Location:** repo root.
**Phase:** 10C.

> The highest-scoring region may not be the optimum.
> The optimum may be the region under the greatest tension.
> — CEO directive, Phase 10C

## The rejection

The previous formula multiplied all signals together:
```text
score = readiness × novelty × feasibility
```

This assumes all signals COOPERATE — higher is better for each.
Reality does not work that way. Signals TENSION against each other.

## The replacement

Introduce TENSION: the model should identify combinations where
opposing forces create pressure for change.

| Variable | Direction | What it means |
|---|---|---|
| Maturity | increasing | Capability is becoming viable |
| Novelty | moderate | Not too familiar, not too distant |
| Cost | decreasing | Economic viability approaching |
| Regulation | weakening | Regulatory barriers falling |
| Infrastructure | expanding | Deployment pathways opening |

### Tension examples

**High tension (invention pressure):**
- A capability's TRL is RISING (approaching breakthrough)
- Cost is FALLING rapidly
- BUT a regulation is NOT yet removed (blocking)
- → Pressure builds. When the regulation is removed, the invention
  becomes INEVITABLE.

**Low tension (stable, no invention):**
- All capabilities are mature (TRL 9, stable)
- Cost has been low for years (no change)
- No regulatory changes
- → No pressure. The combination exists or doesn't, but nothing is
  CHANGING to make it newly possible.

**Wrong tension (high novelty, low maturity):**
- A combination is very unusual (far from existing)
- But the capabilities are at TRL 2 (basic research)
- → This is imagination, not adjacency. Not invention pressure.

## Tension-based scoring (candidate formula)

```text
tension_score(combo, T) =
    trajectory_velocity(combo, T)     — how fast capabilities are improving
  × constraint_pressure(combo, T)      — how much pressure constraints exert
  × adjacency(combo, T)                — how close to existing
```

Note: this is NOT a simple multiplication. Tension is highest when
velocity is HIGH (things changing fast) and constraint pressure is
HIGH (barriers still present). When the barrier falls, the tension
releases and the invention happens.

The model should look for HIGH-TENSION combinations — places where
capability growth is pushing against a constraint that is about to
give way.
