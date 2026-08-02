# SEMICONDUCTOR_TRAJECTORY_REGISTRY

**Status:** Phase 14A, Domain 1 trajectory registry.
**Location:** repo root.
**Phase:** 14A.
**Committed before backtest:** yes (per Rule 3).

---

## Schema

```typescript
interface SemiconductorTrajectory {
    capability: string;
    year: number;
    trl: number;
    velocity: number;      // dTRL/dt over 5-year window
    notes: string;
}
```

---

## T-points

The backtest uses 12 T-points at 5-year intervals:

```
1970, 1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2025
```

The 5-year horizon (HORIZON = 5) means predictions at T are
evaluated against events in (T, T+5].

---

## TRL trajectories

### 1. COPPER_INTERCONNECT (rising, then stable)

| Year | TRL | Velocity (dTRL/dt) | Notes |
|---|---|---|---|
| 1965 | 1 | — | Concept (IBM research on Cu interconnect) |
| 1970 | 2 | 0.20 | Basic principles (Cu resistivity advantage known) |
| 1975 | 3 | 0.20 | Experimental proof (Cu deposition research) |
| 1980 | 4 | 0.20 | Lab validation (damascene process concept) |
| 1985 | 5 | 0.20 | Component validation in lab |
| 1990 | 6 | 0.20 | Subsystem prototype (IBM pilot line) |
| 1995 | 8 | 0.40 | System qualification (IBM pre-production) |
| 2000 | 9 | 0.20 | Actual system proven (IBM PowerPC 750, 1997) |
| 2005 | 9 | 0.00 | Stable (Cu is standard for all leading-edge nodes) |
| 2010 | 9 | 0.00 | Stable |
| 2015 | 9 | 0.00 | Stable |
| 2020 | 9 | 0.00 | Stable |
| 2025 | 9 | 0.00 | Stable |

**Key observation:** COPPER_INTERCONNECT rises from TRL 1 (1965)
to TRL 9 (2000), with peak velocity 0.40 (1990-1995). The 1997
copper interconnect event occurs when the capability is at TRL 8
(1995) — the model should predict this event at T=1995.

### 2. HIGH_K_GATE_STACK (rising, then stable)

| Year | TRL | Velocity | Notes |
|---|---|---|---|
| 1965 | 1 | — | Concept (high-k dielectric research) |
| 1970 | 1 | 0.00 | Not active |
| 1975 | 1 | 0.00 | Not active |
| 1980 | 2 | 0.20 | Basic principles (HfO2, ZrO2 studied) |
| 1985 | 3 | 0.20 | Experimental proof (university research) |
| 1990 | 4 | 0.20 | Lab validation (Intel, IBM research) |
| 1995 | 5 | 0.20 | Component validation |
| 2000 | 6 | 0.20 | Subsystem prototype (process integration) |
| 2005 | 8 | 0.40 | System qualification (Intel pre-production) |
| 2010 | 9 | 0.20 | Actual system proven (Intel 45nm, 2007) |
| 2015 | 9 | 0.00 | Stable (high-k standard at all nodes ≤45nm) |
| 2020 | 9 | 0.00 | Stable |
| 2025 | 9 | 0.00 | Stable |

**Key observation:** HIGH_K_GATE_STACK rises from TRL 1 (1980)
to TRL 9 (2010), with peak velocity 0.40 (2000-2005). The 2007
high-k event occurs when the capability is at TRL 8 (2005) —
the model should predict this event at T=2005.

### 3. NON_PLANAR_TRANSISTOR (rising, then stable)

| Year | TRL | Velocity | Notes |
|---|---|---|---|
| 1965 | 1 | — | Concept |
| 1970 | 1 | 0.00 | Not active |
| 1975 | 1 | 0.00 | Not active |
| 1980 | 2 | 0.20 | Basic principles (3D transistor concepts) |
| 1985 | 3 | 0.20 | Experimental proof (early FinFET research) |
| 1990 | 4 | 0.20 | Lab validation (Hisamoto FINFET paper, 1989) |
| 1995 | 5 | 0.20 | Component validation |
| 2000 | 6 | 0.20 | Subsystem prototype (UC Berkeley, IBM research) |
| 2005 | 7 | 0.20 | System prototype in relevant env (Intel 22nm dev) |
| 2010 | 8 | 0.20 | System qualification (Intel 22nm pre-production) |
| 2015 | 9 | 0.20 | Actual system proven (Intel 22nm FinFET, 2011; 14nm, 2014) |
| 2020 | 9 | 0.00 | Stable (FinFET at 5nm, 7nm, 10nm) |
| 2025 | 9 | 0.00 | Stable (GAA at 3nm is subsumed under same capability) |

**Key observation:** NON_PLANAR_TRANSISTOR rises from TRL 1 (1980)
to TRL 9 (2015), with consistent velocity 0.20. The 2011 FinFET
event occurs when the capability is at TRL 8 (2010) — the model
should predict this event at T=2010.

### 4. EUV_LITHOGRAPHY (rising, then stable)

| Year | TRL | Velocity | Notes |
|---|---|---|---|
| 1965 | 1 | — | Concept (soft X-ray lithography) |
| 1970 | 1 | 0.00 | Not active |
| 1975 | 1 | 0.00 | Not active |
| 1980 | 2 | 0.20 | Basic principles (X-ray proximity lithography) |
| 1985 | 3 | 0.20 | Experimental proof (EUV LLC formed 1997, but pre-cursor research earlier) |
| 1990 | 4 | 0.20 | Lab validation (EUV LLC research begins) |
| 1995 | 5 | 0.20 | Component validation (plasma source development) |
| 2000 | 6 | 0.20 | Subsystem prototype (ASML alpha demo tool, 2006 — delayed) |
| 2005 | 6 | 0.00 | Plateau (source power problems, delayed 2005-2010) |
| 2010 | 7 | 0.20 | System prototype (ASML NXE:3100 beta, 2010) |
| 2015 | 8 | 0.20 | System qualification (ASML NXE:3300B pre-production, 2015) |
| 2020 | 9 | 0.20 | Actual system proven (TSMC 7nm EUV, 2018; 5nm, 2020) |
| 2025 | 9 | 0.00 | Stable |

**Key observation:** EUV_LITHOGRAPHY rises from TRL 1 (1980) to
TRL 9 (2020), with a plateau at 2005-2010 (source power problems).
The 2018 EUV event occurs when the capability is at TRL 8 (2015) —
the model should predict this event at T=2015.

### 5. ADVANCED_PACKAGING (rising, then stable)

| Year | TRL | Velocity | Notes |
|---|---|---|---|
| 1965 | 1 | — | Concept (flip-chip early concepts) |
| 1970 | 2 | 0.20 | Basic principles (flip-chip on ceramic) |
| 1975 | 3 | 0.20 | Experimental proof (early flip-chip production) |
| 1980 | 4 | 0.20 | Lab validation (multi-chip module concepts) |
| 1985 | 5 | 0.20 | Component validation (TSV concept papers) |
| 1990 | 6 | 0.20 | Subsystem prototype (TSV research at IMEC, IBM) |
| 1995 | 7 | 0.20 | System prototype (early TSV test vehicles) |
| 2000 | 7 | 0.00 | Plateau (packaging not the bottleneck; lithography is) |
| 2005 | 8 | 0.20 | System qualification (TSMC CoWoS development) |
| 2010 | 8 | 0.00 | Plateau (CoWoS in pre-production) |
| 2015 | 9 | 0.20 | Actual system proven (Xilinx Virtex-7, 2012; HBM, 2015) |
| 2020 | 9 | 0.00 | Stable (AMD 3D V-Cache, TSMC SoIC) |
| 2025 | 9 | 0.00 | Stable |

**Key observation:** ADVANCED_PACKAGING rises from TRL 1 (1965)
to TRL 9 (2015), with plateaus at 2000-2005 and 2010-2015. The
2009 TSV event occurs when the capability is at TRL 8 (2005) —
the model should predict this event at T=2005.

### 6. OPTICAL_LITHOGRAPHY (stable throughout)

| Year | TRL | Velocity | Notes |
|---|---|---|---|
| 1965 | 9 | 0.00 | Contact/proximity printing in production |
| 1970-2025 | 9 | 0.00 | Stable throughout (g-line → i-line → DUV → ArF → immersion are all "optical lithography") |

**Note:** EUV is tracked as a SEPARATE capability (EUV_LITHOGRAPHY),
not as part of OPTICAL_LITHOGRAPHY. The distinction matters because
EUV is the rising capability that produces later invention events,
while OPTICAL_LITHOGRAPHY is the stable base.

### 7. PLANAR_TRANSISTOR (stable throughout)

| Year | TRL | Velocity | Notes |
|---|---|---|---|
| 1965 | 9 | 0.00 | Planar MOSFET in production since 1960s |
| 1970-2025 | 9 | 0.00 | Stable throughout (even after FinFET replaced it at leading edge, the capability of building planar transistors remains at TRL 9) |

### 8. WAFER_FABRICATION (stable throughout)

| Year | TRL | Velocity | Notes |
|---|---|---|---|
| 1965 | 9 | 0.00 | 50mm wafer production |
| 1970-2025 | 9 | 0.00 | Stable throughout (100mm → 150mm → 200mm → 300mm are manufacturing scale-up, not new capabilities) |

---

## Summary: rising vs stable capabilities

| Capability | Type | Rise period | Peak velocity | TRL 9 by |
|---|---|---|---|---|
| COPPER_INTERCONNECT | rising | 1965-2000 | 0.40 (1990-1995) | 2000 |
| HIGH_K_GATE_STACK | rising | 1980-2010 | 0.40 (2000-2005) | 2010 |
| NON_PLANAR_TRANSISTOR | rising | 1980-2015 | 0.20 (consistent) | 2015 |
| EUV_LITHOGRAPHY | rising | 1980-2020 | 0.20 (with plateau 2005-2010) | 2020 |
| ADVANCED_PACKAGING | rising | 1965-2015 | 0.20 (with plateaus) | 2015 |
| OPTICAL_LITHOGRAPHY | stable | — | 0.00 | always |
| PLANAR_TRANSISTOR | stable | — | 0.00 | always |
| WAFER_FABRICATION | stable | — | 0.00 | always |

---

## What this trajectory registry exposes

1. **5 rising capabilities, 3 stable.** This is the inverse of
   Li-ion (3 rising, 7 stable). Semiconductors have more rising
   capabilities because the domain is defined by successive
   technology generations.

2. **Rising capabilities peak at different times.** COPPER
   peaks in 1995; HIGH_K in 2005; NON_PLANAR in 2010-2015; EUV
   in 2015-2020; ADVANCED_PACKAGING in 2005-2015. Each
   capability's rise predicts events in its peak window.

3. **Two rising capabilities have plateaus.** EUV plateaued
   at 2005-2010 (source power problems); ADVANCED_PACKAGING
   plateaued at 2000-2005 and 2010-2015. These plateaus test
   whether the persistence protocol (velocity > 0.20 for ≥5
   years) correctly handles interrupted trajectories.

4. **The 5 Group A events (1971, 1985, 1993, 1995, 2001) occur
   when NO rising capability is active at high TRL.**
   COPPER_INTERCONNECT is rising during 1971-1995, but it's
   not in the combination for those events. The combination
   for those events is all-stable capabilities. The theory
   does not predict these events — which is the D4 destruction
   test result.
