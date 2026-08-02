# SEMICONDUCTOR_EVENT_REGISTRY

**Status:** Phase 14A, Domain 1 event registry.
**Location:** repo root.
**Phase:** 14A.
**Committed before backtest:** yes (per Rule 3).

---

## Schema

```typescript
interface SemiconductorEvent {
    year: number;
    combination: string[];
    event: string;
    evidence: string[];
    significance: string;
    risingCapabilityPresent: boolean;
}
```

The `risingCapabilityPresent` field is pre-computed from the
trajectory registry: does at least one capability in the
combination have non-zero velocity at year-1? This field is
used by destruction test D4 (invention without velocity).

---

## Events (1971-2022)

### Group A: Scaling events (no rising capability in combination)

These events occur within an already-mature technology base.
The capabilities involved (OPTICAL_LITHOGRAPHY, PLANAR_TRANSISTOR,
WAFER_FABRICATION, METAL_INTERCONNECT) are all at TRL 9
throughout. These events are SCALING, not CAPABILITY-DRIVEN
invention.

| Year | Combination | Event | Evidence | Rising cap? |
|---|---|---|---|---|
| 1971 | [OPTICAL_LITHOGRAPHY, PLANAR_TRANSISTOR, METAL_INTERCONNECT] | Intel 4004 (first commercial microprocessor) | Intel 4004 datasheet; Federico Faggin, "The Making of the First Microprocessor" (IEEE Micro, 1996); 10um process, 2300 transistors | No |
| 1985 | [OPTICAL_LITHOGRAPHY, PLANAR_TRANSISTOR, WAFER_FABRICATION] | Intel 386 (32-bit microprocessor, 1.5um) | Intel 386 datasheet; 1.5um CMOS process, 275K transistors | No |
| 1993 | [OPTICAL_LITHOGRAPHY, PLANAR_TRANSISTOR] | Intel Pentium (0.8um, superscalar) | Intel Pentium datasheet; 0.8um BiCMOS, 3.1M transistors | No |
| 1995 | [OPTICAL_LITHOGRAPHY, WAFER_FABRICATION] | 0.35um node, 64M DRAM | Hitachi/Toshiba 64M DRAM data; 0.35um process, 200mm wafers | No |
| 2001 | [OPTICAL_LITHOGRAPHY, PLANAR_TRANSISTOR] | 130nm node, strained silicon | IBM/Joint Development Program strained Si announcement; 130nm process | No |

**5 events with no rising capability present.** These are the
destruction test D4 candidates. If D4 requires zero invention
without velocity, these 5 events falsify the strict necessity
claim.

### Group B: Capability-driven events (rising capability present)

These events involve at least one rising capability. They are
the events the theory SHOULD predict.

| Year | Combination | Event | Evidence | Rising cap? |
|---|---|---|---|---|
| 1997 | [COPPER_INTERCONNECT, OPTICAL_LITHOGRAPHY] | Copper interconnect in production (IBM PowerPC 750) | IBM press release 1997-09; Motorola/IBM joint announcement; damascene copper process at 0.25um | Yes (COPPER_INTERCONNECT) |
| 2007 | [HIGH_K_GATE_STACK, PLANAR_TRANSISTOR] | 45nm high-k metal gate (Intel Penryn) | Intel press release 2007-01; Intel 45nm process paper (IEDM 2007); Hf-based high-k dielectric | Yes (HIGH_K_GATE_STACK) |
| 2009 | [ADVANCED_PACKAGING, OPTICAL_LITHOGRAPHY] | TSV 3D packaging (Xilinx Virtex-7, TSMC CoWoS) | Xilinx Virtex-7 product brief; TSMC CoWoS technology paper (IEEE ECTC 2011) | Yes (ADVANCED_PACKAGING) |
| 2011 | [NON_PLANAR_TRANSISTOR, OPTICAL_LITHOGRAPHY] | Intel 22nm FinFET (Ivy Bridge) | Intel press release 2011-05; Intel 22nm Tri-Gate paper (VLSI 2012); first volume FinFET production | Yes (NON_PLANAR_TRANSISTOR) |
| 2012 | [HIGH_K_GATE_STACK, NON_PLANAR_TRANSISTOR, OPTICAL_LITHOGRAPHY] | TSMC 28nm HKMG (Qualcomm Snapdragon) | TSMC 28nm HPM process; Qualcomm Snapdragon S4; first volume 28nm production | Yes (HIGH_K_GATE_STACK, NON_PLANAR_TRANSISTOR) |
| 2014 | [NON_PLANAR_TRANSISTOR, OPTICAL_LITHOGRAPHY] | Intel 14nm FinFET (Broadwell) | Intel 14nm process paper (IEDM 2014); Broadwell 2nd-gen FinFET | Yes (NON_PLANAR_TRANSISTOR) |
| 2018 | [EUV_LITHOGRAPHY, NON_PLANAR_TRANSISTOR] | TSMC 7nm EUV (Apple A12 Bionic) | Apple A12 announcement 2018-09; TSMC 7FF+ process with EUV; first volume EUV production | Yes (EUV_LITHOGRAPHY, NON_PLANAR_TRANSISTOR) |
| 2020 | [EUV_LITHOGRAPHY, NON_PLANAR_TRANSISTOR] | TSMC 5nm EUV (Apple A14 Bionic) | Apple A14 announcement 2020-09; TSMC 5nm N5 process; full EUV | Yes (EUV_LITHOGRAPHY, NON_PLANAR_TRANSISTOR) |
| 2020 | [ADVANCED_PACKAGING, NON_PLANAR_TRANSISTOR] | AMD 3D V-Cache (TSV packaging) | AMD press release 2020-10; TSMC SoIC packaging; hybrid copper-to-copper bonding | Yes (ADVANCED_PACKAGING, NON_PLANAR_TRANSISTOR) |
| 2022 | [EUV_LITHOGRAPHY, NON_PLANAR_TRANSISTOR] | Samsung 3nm GAA (gate-all-around) | Samsung Foundry 3nm GAA announcement 2022-06; first volume GAA production; MBCFET architecture | Yes (EUV_LITHOGRAPHY, NON_PLANAR_TRANSISTOR) |

**10 events with rising capability present.** These are the events
the theory should predict. If the theory works, the Top-10
predictions at the relevant T-points should include these
combinations.

---

## Summary

| Category | Count | Description |
|---|---|---|
| Group A (scaling, no rising cap) | 5 | Intel 4004, 386, Pentium, 0.35um DRAM, 130nm strained Si |
| Group B (capability-driven, rising cap) | 10 | Copper, high-k, TSV, FinFET, EUV, GAA |
| Total | 15 | |

## The key structural finding (pre-stated, per EP-4)

The semiconductor domain has a feature Li-ion does not: 33% of
events (5/15) occur WITHOUT a rising capability in the
combination. These are scaling events — incremental improvements
within an already-mature technology base.

If destruction test D4 (invention without velocity) uses a strict
falsifier ("any event without velocity falsifies necessity"), then
these 5 events FALSIFY the necessity claim (FEC-002) for the
semiconductor domain.

This is a legitimate finding. The theory's boundary is: it applies
to capability-driven invention, not to scaling-driven invention.
The semiconductor domain exposes this boundary.

Per the CEO's instruction: "Search for evidence that this sentence
is wrong: rising capabilities that become increasingly adjacent
produce susceptible regions in technological space." The 5 scaling
events are exactly this evidence. If the sentence is to survive
semiconductors, it must be qualified: "rising capabilities produce
susceptible regions in technological space FOR CAPABILITY-DRIVEN
invention, not for SCALING-DRIVEN invention."

Whether that qualification counts as "survival" or "falsification"
depends on the advancement criteria (condition 4: no destruction-test
falsification). This is pre-stated honestly before the backtest runs.
