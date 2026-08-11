# TRAJECTORY_REGISTRY — Phase 11C

**Status:** evidence layer (capability trajectories).
**Location:** repo root.
**Phase:** 11C.

> Formula B succeeded because it stopped asking 'What exists?'
> and started asking 'What is changing?'
> — CEO observation, Phase 11

## Schema

```typescript
interface CapabilityTrajectory {
    capability: string;
    year: number;
    trl: number;
    velocity: number;      // dTRL/dt
    acceleration: number;  // d²TRL/dt²
}
```

## TRL Trajectories (1990-2023)

### ELECTROCHEMICAL_ENERGY_STORAGE

| Year | TRL | Velocity | Acceleration | Notes |
|---|---|---|---|---|
| 1990 | 6 | — | — | Lab-scale Li-ion (pre-commercial) |
| 1991 | 9 | 0.60 | — | Sony commercializes. Jump from TRL 6 to 9. |
| 1995 | 9 | 0.00 | -0.15 | Stable. Decelerating from the 1991 jump. |
| 2000 | 9 | 0.00 | 0.00 | Stable. |
| 2005 | 9 | 0.00 | 0.00 | Stable. |
| 2010 | 9 | 0.00 | 0.00 | Stable. |
| 2015 | 9 | 0.00 | 0.00 | Stable. |
| 2020 | 9 | 0.00 | 0.00 | Stable. |
| 2023 | 9 | 0.00 | 0.00 | Stable. |

### ION_TRANSPORT

| Year | TRL | Velocity | Acceleration | Notes |
|---|---|---|---|---|
| 1990 | 9 | — | — | Liquid electrolytes mature since 1970s |
| 1991-2023 | 9 | 0.00 | 0.00 | Stable throughout. |

### INTERCALATION

| Year | TRL | Velocity | Acceleration | Notes |
|---|---|---|---|---|
| 1990 | 8 | — | — | Near-mature (LCO cathode developed 1980) |
| 1991 | 9 | 0.20 | — | Commercialization pushes to TRL 9 |
| 1995 | 9 | 0.00 | -0.05 | Stable |
| 2000-2023 | 9 | 0.00 | 0.00 | Stable. |

### ELECTRON_COLLECTION

| Year | TRL | Velocity | Acceleration | Notes |
|---|---|---|---|---|
| 1990-2023 | 9 | 0.00 | 0.00 | Al/Cu current collectors. Mature since 1970s. |

### FAST_CHARGING (KEY TRAJECTORY)

| Year | TRL | Velocity | Acceleration | Notes |
|---|---|---|---|---|
| 1990 | 1 | — | — | Not a concept |
| 1993 | 2 | 0.33 | — | Basic principles (high-rate understood) |
| 1995 | 2 | 0.00 | -0.11 | No progress |
| 1997 | 3 | 0.50 | 0.25 | Experimental proof (some protocols) |
| 2000 | 4 | 0.33 | -0.08 | Component lab validation |
| 2003 | 5 | 0.33 | 0.00 | Component validation in relevant env (power tools) |
| 2005 | 5 | 0.00 | -0.11 | Plateau |
| 2008 | 6 | 0.33 | 0.22 | Subsystem prototype (early EVs) |
| 2010 | 7 | 0.20 | -0.07 | System prototype (CHAdeMO, early Supercharger) |
| 2012 | 8 | 0.50 | 0.15 | System qualification (Tesla Supercharger network) |
| 2015 | 9 | 0.33 | -0.08 | Actual system proven (350kW chargers) |
| 2018 | 9 | 0.00 | -0.11 | Stable |
| 2020 | 9 | 0.00 | 0.00 | Stable |
| 2023 | 9 | 0.00 | 0.00 | Stable (4C charging now mainstream) |

**Key observation:** FAST_CHARGING has the HIGHEST velocity of any
capability. Its rise from TRL 1 to TRL 9 spans 1990-2015, with
multiple acceleration phases (1993-1997, 2008-2012). All true
positives in the backtest involve FAST_CHARGING.

### THERMAL_MANAGEMENT

| Year | TRL | Velocity | Acceleration | Notes |
|---|---|---|---|---|
| 1990 | 2 | — | — | Basic principles |
| 1993 | 4 | 0.67 | — | Rapid rise (pack-level thermal issues recognized) |
| 1995 | 5 | 0.33 | -0.11 | Component validation |
| 2000 | 6 | 0.20 | -0.04 | Subsystem prototype |
| 2003 | 8 | 0.67 | 0.16 | Rapid rise (EV pack requirements drive it) |
| 2005 | 9 | 0.33 | -0.11 | System proven (EV packs standard) |
| 2008-2023 | 9 | 0.00 | 0.00 | Stable |

### STATE_OF_CHARGE_MONITORING

| Year | TRL | Velocity | Acceleration | Notes |
|---|---|---|---|---|
| 1990 | 4 | — | — | Component lab (primitive coulomb counting) |
| 1993 | 7 | 1.00 | — | RAPID rise (BMS technology advances) |
| 1995 | 9 | 0.67 | -0.11 | System proven (BMS standard) |
| 2000-2023 | 9 | 0.00 | 0.00 | Stable |

### SAFETY_PROTECTION

| Year | TRL | Velocity | Acceleration | Notes |
|---|---|---|---|---|
| 1990 | 6 | — | — | System prototype (fuses, PTC exist) |
| 1993 | 8 | 0.67 | — | Rapid rise (CID, vents developing) |
| 1995 | 9 | 0.33 | -0.11 | System proven |
| 2000-2023 | 9 | 0.00 | 0.00 | Stable |

### ELECTRODE_COATING

| Year | TRL | Velocity | Acceleration | Notes |
|---|---|---|---|---|
| 1990-2023 | 9 | 0.00 | 0.00 | Mature since 1970s (slot-die coating). |

### CELL_ASSEMBLY

| Year | TRL | Velocity | Acceleration | Notes |
|---|---|---|---|---|
| 1990-2023 | 9 | 0.00 | 0.00 | Mature since 1970s (winding, stacking). |

## Key observations

1. **Three capabilities have significant trajectories:** FAST_CHARGING,
   THERMAL_MANAGEMENT, and STATE_OF_CHARGE_MONITORING. These are the
   capabilities that rose from low TRL to TRL 9 during the 1990-2023
   period.

2. **All three true positives in Formula B's backtest involve at
   least one trajectory capability.** This confirms the trajectory
   hypothesis: inventions emerge where capabilities are CHANGING.

3. **Acceleration matters as much as velocity.** FAST_CHARGING's
   acceleration phases (1993-1997, 2008-2012) correspond to periods
   of rapid innovation. The model should eventually track acceleration,
   not just velocity.

4. **The "stable" capabilities (ION_TRANSPORT, ELECTRON_COLLECTION,
   ELECTRODE_COATING, CELL_ASSEMBLY) have zero velocity throughout.**
   They contribute to feasibility but not to invention prediction.
   A combination of all-stable capabilities scores zero on velocity
   — which is correct, because no invention is IMMINENT when nothing
   is changing.
