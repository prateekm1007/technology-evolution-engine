# TELECOM_TRAJECTORY_REGISTRY

**Status:** Phase 14A, Domain 2 trajectory registry.
**Location:** repo root.
**Phase:** 14A.
**Committed before backtest:** yes (per Rule 3).

---

## Schema

```typescript
interface TelecomTrajectory {
    capability: string;
    year: number;
    trl: number;
    velocity: number;      // dTRL/dt over 5-year window
    notes: string;
}
```

---

## T-points

10 T-points at 5-year intervals:

```
1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2025
```

Wait — that's 11. Let me use 10: 1980, 1985, 1990, 1995, 2000, 2005,
2010, 2015, 2020, 2025. The 5-year horizon (HORIZON = 5) means
predictions at T are evaluated against events in (T, T+5].

---

## TRL trajectories

### 1. WIRELESS_PROTOCOL (rising in discrete steps)

This capability rises in DISCRETE STEPS — each generation is a
step from TRL 3 (concept) to TRL 9 (commercial). After each
generation reaches TRL 9, the capability plateaus until the
next generation begins.

| Year | TRL | Velocity (dTRL/dt) | Notes |
|---|---|---|---|
| 1975 | 3 | — | 1G concept (Bell Labs cellular concept since 1947, but actively developing in 1970s) |
| 1980 | 5 | 0.40 | 1G pre-commercial trials |
| 1985 | 9 | 0.80 | 1G commercial (AMPS 1983); TRL jumps to 9 |
| 1990 | 9 | 0.00 | 1G plateau; 2G at concept/standardization (GSM group formed 1982, standard frozen 1990) |
| 1995 | 9 | 0.00 | 2G commercial (GSM 1991); capability already at TRL 9 |
| 2000 | 9 | 0.00 | 2G plateau; 3G at standardization (3GPP formed 1998, Release 99 frozen 2000) |
| 2005 | 9 | 0.00 | 3G commercial (WCDMA 2001); capability at TRL 9 |
| 2010 | 9 | 0.00 | 3G plateau; 4G commercial (LTE 2009); capability at TRL 9 |
| 2015 | 9 | 0.00 | 4G plateau; 5G at concept (5G PPP formed 2012) |
| 2020 | 9 | 0.00 | 5G commercial (2019); capability at TRL 9 |
| 2025 | 9 | 0.00 | 5G plateau; 6G at research (TRL 3-4) |

**Key observation:** WIRELESS_PROTOCOL has velocity > 0.20 only
during 1975-1985 (1G rise). After 1985, the capability is at TRL 9
and plateaus. The 2G, 3G, 4G, 5G transitions are NOT captured as
velocity in this model — they're "re-rising" of the same capability
to a new generation.

This is a structural limitation. The trajectory model assumes a
capability rises ONCE from TRL 1 to TRL 9. Telecom capabilities
rise MULTIPLE TIMES (once per generation). The frozen formula
cannot distinguish "1G at TRL 9" from "5G at TRL 9" — both are
just TRL 9.

This is pre-stated as a known limitation.

### 2. SPECTRUM_UTILIZATION (rising in steps)

| Year | TRL | Velocity | Notes |
|---|---|---|---|
| 1975 | 9 | 0.00 | Sub-1GHz mature since 1940s |
| 1980 | 9 | 0.00 | Stable |
| 1985 | 9 | 0.00 | Stable |
| 1990 | 9 | 0.00 | Stable (2G uses sub-1GHz) |
| 1995 | 9 | 0.00 | Stable |
| 2000 | 9 | 0.00 | 3G uses 2GHz band; still sub-3GHz, capability mature |
| 2005 | 9 | 0.00 | Stable |
| 2010 | 9 | 0.00 | 4G uses 2.5-2.6GHz; capability still mature |
| 2015 | 5 | -0.80 | mmWave research active; capability "re-rising" for 5G mmWave (drops to track new sub-capability) |
| 2020 | 9 | 0.80 | 5G mmWave commercial (2020); capability at TRL 9 for mmWave |
| 2025 | 9 | 0.00 | Stable; sub-THz research (6G) at TRL 3-4 |

**Key observation:** SPECTRUM_UTILIZATION has a NEGATIVE velocity
in 2010-2015 because the capability "drops" to track the new
mmWave sub-capability. This is non-monotonic TRL — same structural
violation as pharmaceuticals (clinical trial failure drops TRL).
The frozen formula's velocity term will produce negative values,
which (after capping) become 0 — meaning the model cannot detect
the mmWave rise.

This is pre-stated as a known limitation.

### 3. PACKET_SWITCHING (rising, then stable)

| Year | TRL | Velocity | Notes |
|---|---|---|---|
| 1975 | 9 | 0.00 | Circuit-switching mature since 1900s (telephony) |
| 1980 | 9 | 0.00 | Stable |
| 1985 | 5 | -0.80 | Packet-switching for mobile (GPRS concept); capability "re-rising" |
| 1990 | 7 | 0.40 | GPRS lab validation |
| 1995 | 9 | 0.40 | GPRS commercial (2000); TRL 9 |
| 2000 | 9 | 0.00 | Stable (2.5G GPRS) |
| 2005 | 9 | 0.00 | 3G packet core mature |
| 2010 | 9 | 0.00 | 4G all-IP mature |
| 2015 | 9 | 0.00 | Stable |
| 2020 | 9 | 0.00 | Stable (5G uses same IP core) |
| 2025 | 9 | 0.00 | Stable |

**Key observation:** PACKET_SWITCHING "re-rose" in 1985-1995 for
mobile packet data, then plateaued. Same non-monotonic pattern.

### 4. SMART_DEVICE_INTEGRATION (rising in steps)

| Year | TRL | Velocity | Notes |
|---|---|---|---|
| 1975 | 9 | 0.00 | Basic phone mature |
| 1980 | 9 | 0.00 | Stable |
| 1985 | 9 | 0.00 | Stable |
| 1990 | 9 | 0.00 | Feature phone mature |
| 1995 | 9 | 0.00 | Stable |
| 2000 | 9 | 0.00 | Stable (early smartphones exist but niche) |
| 2005 | 5 | -0.80 | Smartphone capability "re-rising" (iPhone development) |
| 2010 | 9 | 0.80 | Smartphone commercial (iPhone 2007); TRL 9 |
| 2015 | 5 | -0.80 | IoT capability "re-rising" (NB-IoT development) |
| 2020 | 9 | 0.80 | IoT commercial (NB-IoT 2016, LTE-M); TRL 9 |
| 2025 | 9 | 0.00 | Stable; AR/VR at TRL 5-7 (emerging) |

**Key observation:** SMART_DEVICE_INTEGRATION has TWO "re-rise"
cycles: smartphone (2005-2010) and IoT (2015-2020). The velocity
is negative during the "drop" phase (2000-2005, 2010-2015) because
the capability tracks the new sub-capability.

### 5. NETWORK_VIRTUALIZATION (rising, still maturing)

| Year | TRL | Velocity | Notes |
|---|---|---|---|
| 1975 | 1 | — | Concept (not active) |
| 1980 | 1 | 0.00 | Not active |
| 1985 | 1 | 0.00 | Not active |
| 1990 | 1 | 0.00 | Not active |
| 1995 | 1 | 0.00 | Not active |
| 2000 | 3 | 0.40 | SDN research (OpenFlow concept) |
| 2005 | 4 | 0.20 | Lab validation (university SDN) |
| 2010 | 5 | 0.20 | Component validation (NFV PoC) |
| 2015 | 6 | 0.20 | Subsystem prototype (early cloud RAN) |
| 2020 | 8 | 0.40 | System qualification (5G SA cloud-native core) |
| 2025 | 9 | 0.20 | Actual system proven (5G SA mature) |

**Key observation:** NETWORK_VIRTUALIZATION is the only telecom
capability with a smooth rise (TRL 1 → 9 over 2000-2025). It's
the closest analog to Li-ion's rising capabilities.

### 6-8. Stable capabilities

| Capability | TRL (1975-2025) | Velocity |
|---|---|---|
| RADIO_TRANSMISSION | 9 throughout | 0.00 |
| ANTENNA_HARDWARE | 9 throughout | 0.00 |
| INFRASTRUCTURE_DEPLOYMENT | 9 throughout | 0.00 |

---

## Summary: rising vs stable capabilities

| Capability | Type | Rise pattern | Peak velocity | Notes |
|---|---|---|---|---|
| WIRELESS_PROTOCOL | rising | Discrete steps (1G → 5G) | 0.80 (1G rise only) | Re-rises per generation; model captures only 1G rise |
| SPECTRUM_UTILIZATION | rising | Non-monotonic (mmWave) | 0.80 (mmWave rise) | Drops to track new sub-capability |
| PACKET_SWITCHING | rising | Non-monotonic (mobile packet) | 0.40 | Re-rose for mobile, then plateaued |
| SMART_DEVICE_INTEGRATION | rising | Non-monotonic (smartphone, IoT) | 0.80 | Two re-rise cycles |
| NETWORK_VIRTUALIZATION | rising | Smooth | 0.40 | Only smooth-rise capability |
| RADIO_TRANSMISSION | stable | — | 0.00 | Always TRL 9 |
| ANTENNA_HARDWARE | stable | — | 0.00 | Always TRL 9 |
| INFRASTRUCTURE_DEPLOYMENT | stable | — | 0.00 | Always TRL 9 |

---

## What this trajectory registry exposes

1. **4 of 5 rising capabilities have non-monotonic TRL.** They
   "re-rise" for each new generation/sub-capability. The frozen
   formula's velocity term (dTRL/dt) will produce NEGATIVE values
   during the "drop" phases, which (after capping at 0) become 0 —
   meaning the model cannot detect the new generation's rise.

2. **Only NETWORK_VIRTUALIZATION has a smooth rise.** It's the
   only telecom capability that rises once, monotonically, from
   TRL 1 to TRL 9. If the theory works for telecom, it will work
   through NETWORK_VIRTUALIZATION's trajectory.

3. **WIRELESS_PROTOCOL — the main capability — has velocity > 0.20
   only during 1975-1985 (1G rise).** After 1985, the model cannot
   detect 2G, 3G, 4G, or 5G rises because WIRELESS_PROTOCOL is
   already at TRL 9. This is the structural limitation: the
   trajectory model cannot represent "re-rising" capabilities.

4. **The 7 Group A events (scaling) occur during plateau periods**
   when no capability is rising. The model will not predict them
   — same as semiconductors' Group A events.

5. **The 8 Group B events occur during "re-rise" phases** when
   the model shows negative or zero velocity (because the
   capability "dropped" to track the new sub-capability). The
   model will likely MISS most Group B events for the same reason.

This is pre-stated honestly. The backtest will confirm or refute
these predictions.
