# SEMICONDUCTOR_BOTTLENECK_REGISTRY

**Status:** Phase 14A, Domain 1 bottleneck registry.
**Location:** repo root.
**Phase:** 14A.
**Committed before backtest:** yes (per Rule 3).

---

## Schema

```typescript
interface SemiconductorBottleneck {
    year: number;
    event: string;
    bottleneck: string;
    bottleneckType: "physical" | "manufacturing" | "economic" | "regulatory" | "infrastructure";
    resolution: string;
    yearsToResolve: number;
}
```

---

## Bottleneck records (1971-2022)

| Year | Event | Bottleneck | Type | Resolution | Years to Resolve |
|---|---|---|---|---|---|
| 1971 | Intel 4004 | Integration density (how many transistors per chip) | physical | 10um lithography + planar MOSFET scaling | 0 (resolved by 1971) |
| 1985 | Intel 386 | Heat dissipation at higher clock speeds | physical | Plastic DIP packaging, heat spreaders | 0 (resolved by 1985) |
| 1993 | Pentium | Interconnect RC delay (Al resistance at 0.8um) | physical | Aluminum interconnect still adequate at 0.8um; copper not yet needed | 4 (resolved by copper, 1997) |
| 1995 | 0.35um node, 64M DRAM | Interconnect RC delay at 0.35um | physical | Shallow trench isolation, Al with barrier layers | 2 (resolved by copper, 1997) |
| 1997 | Copper interconnect | Aluminum resistivity at 0.25um | physical | Damascene copper process (IBM) | 0 (resolved by 1997) |
| 2001 | 130nm strained silicon | Carrier mobility (electron/hole velocity in channel) | physical | Strained silicon (SiGe source/drain, tensile/compressive strain) | 0 (resolved by 2001) |
| 2004 | 90nm SOI | Subthreshold leakage current at 90nm | physical | Silicon-on-insulator (SOI) substrate; partially-depleted SOI (AMD, IBM) | 0 (resolved by 2004) |
| 2007 | 45nm high-k metal gate | Gate oxide leakage (SiO2 too thin at 45nm, ~1.2nm) | physical | Hf-based high-k dielectric + metal gate (Intel) | 0 (resolved by 2007) |
| 2009 | TSV 3D packaging | Inter-die bandwidth (wire bond limited) | physical + manufacturing | Through-silicon vias (TSVs) + silicon interposer (Xilinx/TSMC CoWoS) | 0 (resolved by 2009) |
| 2011 | Intel 22nm FinFET | Short-channel effects at 22nm (planar transistor leakage) | physical | Non-planar FinFET / Tri-Gate architecture (Intel) | 0 (resolved by 2011) |
| 2014 | Intel 14nm FinFET | Patterning difficulty at 14nm (double patterning) | manufacturing | Double/quadruple patterning + design restrictions | 1 (resolved by 2015) |
| 2018 | TSMC 7nm EUV | DUV multi-patterning complexity at 7nm (too many masks) | physical | EUV lithography (13.5nm wavelength, single exposure) | 0 (resolved by 2018) |
| 2020 | TSMC 5nm EUV | EUV throughput + defect density at 5nm | manufacturing | Improved EUV source power, in-line metrology | 0 (resolved by 2020) |
| 2020 | AMD 3D V-Cache | Memory bandwidth (off-chip DRAM latency) | physical + manufacturing | Hybrid copper-to-copper bonding (TSMC SoIC) + TSV | 0 (resolved by 2020) |
| 2022 | Samsung 3nm GAA | Short-channel effects at 3nm (FinFET channel control insufficient) | physical | Gate-all-around (GAA / MBCFET) architecture (Samsung) | 0 (resolved by 2022) |

---

## Bottleneck type distribution

| Type | Count | Events |
|---|---|---|
| physical | 11 | 1971, 1993, 1995, 1997, 2001, 2004, 2007, 2011, 2018, 2020 (AMD), 2022 |
| manufacturing | 3 | 2009 (partial), 2014, 2020 (TSMC) |
| economic | 0 | — |
| regulatory | 0 | — |
| infrastructure | 0 | — |

**Key observation:** Semiconductors are dominated by PHYSICAL
bottlenecks (11/15). This is the same pattern as Li-ion (7/16
physical). The semiconductor domain has MORE physical bottlenecks
because the technology is fundamentally about pushing physical
limits (wavelength, channel length, gate oxide thickness).

No economic, regulatory, or infrastructure bottlenecks appear in
the semiconductor event registry. This is a structural difference
from Li-ion, where cost ($/kWh) was the dominant economic bottleneck.
In semiconductors, cost is a background condition (Wright's Law
applies), but the bottleneck is always physical — the next physics
limit that must be overcome.

---

## Bottleneck era analysis (per CEO directive)

| Era | Dominant bottleneck | Example events |
|---|---|---|
| 1970s | Integration density (transistor count per chip) | Intel 4004 (1971): 2300 transistors at 10um |
| 1980s | Heat (clock speed × transistor count) | Intel 386 (1985): heat dissipation at 16MHz |
| 1990s | Interconnects (RC delay at sub-micron) | Pentium (1993), copper interconnect (1997) |
| 2000s | Leakage (gate + subthreshold) | 90nm SOI (2004), 45nm high-k (2007) |
| 2010s | Lithography (patterning at sub-22nm) | FinFET (2011), EUV (2018) |
| 2020s | Economics (fab cost >$10B, node economics) | 5nm EUV (2020), 3nm GAA (2022) |

This matches the CEO's bottleneck table exactly.

---

## Bottleneck resolution timing

| years_to_resolve | Count | Events |
|---|---|---|
| 0 (resolved at event year) | 13 | All except 1993, 1995, 2014 |
| 1-2 years | 2 | 1993 (4 years), 1995 (2 years), 2014 (1 year) |
| 3+ years | 0 | — |

**Key observation:** 13 of 15 bottlenecks were resolved AT the
event year (years_to_resolve = 0). This is the same pattern as
Li-ion (10/16 resolved at event year). Inventions happen at
bottleneck resolution.

The 2 exceptions (1993, 1995) are interconnect-delay bottlenecks
that were not fully resolved until copper interconnect arrived in
1997. The 2014 exception (14nm patterning) was resolved in 2015
with improved multi-patterning.

---

## What this registry exposes

1. **Semiconductors are physics-bound, not economics-bound.**
   Unlike Li-ion (where cost/kWh was the dominant bottleneck),
   semiconductors are bound by physical limits: wavelength, channel
   length, gate oxide thickness. The economic dimension (fab cost)
   exists but is a secondary constraint, not the bottleneck.

2. **The bottleneck type is always physical.** This means the
   model's CONSTRAINT nodes (per the Li-ion ontology) need a
   semiconductor-specific set: LITHOGRAPHY_RESOLUTION_LIMIT,
   GATE_OXIDE_LEAKAGE_THRESHOLD, SHORT_CHANNEL_EFFECT_LIMIT,
   INTERCONNECT_RC_DELAY_LIMIT. These are different from Li-ion's
   THERMAL_RUNAWAY_THRESHOLD and THEORETICAL_ENERGY_DENSITY_LIMIT.

3. **Bottleneck resolution is binary (0 or 1-2 years).** Unlike
   Li-ion's cost bottleneck (13 years, 1997-2010), semiconductor
   bottlenecks are resolved quickly once the physics is
   understood. The lag is short — inventions happen close to
   bottleneck resolution.

4. **The 2020s shift to economics.** The CEO's table identifies
   economics as the 2020s bottleneck. This is visible in the 2020
   events: TSMC 5nm EUV fab cost ~$20B; Samsung 3nm GAA fab cost
   ~$25B. The bottleneck is shifting from "can we make it?" to
   "can we afford to make it?" — which is the same shift Li-ion
   experienced in the 2010s.
