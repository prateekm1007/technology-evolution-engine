# SEMICONDUCTOR_ONTOLOGY

**Status:** Phase 14A, Domain 1 capability ontology.
**Location:** repo root.
**Phase:** 14A.
**Committed before backtest:** yes (per Rule 3).

> You are transferring the methodology, not the ontology.
> — CEO directive, Phase 14, Rule 2

---

## Purpose

This document defines the capability ontology for the semiconductor
domain. It is committed BEFORE the backtest runs (per Rule 3).
It cannot be modified after the backtest commits (per Law 7,
historical permanence).

The ontology transfers the METHODOLOGY (capability + trajectory
+ adjacency + frozen formula), not the Li-ion ontology. The
semiconductor capabilities are domain-specific.

---

## The four invariant questions (per INVARIANT_REGISTRY.md)

### What accumulates?

Transistor density (Moore's Law: ~2x per node generation).
Mapped to TRL per capability: each capability (lithography,
transistor design, interconnect, materials, packaging) has a
TRL that rises as the state of the art advances.

### What accelerates?

Lithography generation transitions (g-line → i-line → DUV →
ArF → EUV). Each transition takes 10-15 years from concept to
production. EUV was conceived ~1989, entered production 2018
(29 years).

### What constrains?

Lithography resolution (physical: wavelength of light).
Secondary: manufacturing yield (economic: defect density per
wafer). Tertiary: short-channel effects (physical: quantum
tunneling at sub-10nm).

### What becomes adjacent?

New transistor architectures become reachable at each lithography
node: FinFET at 22nm (2011), GAA at 3nm (2022). New materials
become reachable: high-k at 45nm (2007). New packaging becomes
reachable: 3D TSV at 28nm (2009).

---

## Capability list (8 capabilities)

### Rising capabilities (5)

These capabilities rise from low TRL to TRL 9 during the 1965-2025
window. They are the semiconductor analog of Li-ion's FAST_CHARGING,
THERMAL_MANAGEMENT, and STATE_OF_CHARGE_MONITORING.

#### 1. COPPER_INTERCONNECT

The capability of using copper (instead of aluminum) for on-chip
interconnect wiring. Copper has lower resistivity than aluminum,
enabling faster signal propagation and lower RC delay at smaller
nodes.

- Concept: 1970s (IBM research)
- Lab: 1980s (IBM, damascene process)
- Pilot: 1995 (IBM pre-production)
- Production: 1997 (IBM PowerPC 750, Motorola)
- Mature: 2000+

#### 2. HIGH_K_GATE_STACK

The capability of using high-permittivity dielectric materials
(instead of SiO2) for transistor gate stacks. Needed because SiO2
gate oxide became too thin at 45nm, causing excessive gate leakage.

- Concept: 1990s (university research on HfO2, ZrO2)
- Lab: mid-1990s (Intel, IBM research)
- Pilot: 2003-2005 (Intel pre-production)
- Production: 2007 (Intel Penryn, 45nm)
- Mature: 2010+

#### 3. NON_PLANAR_TRANSISTOR

The capability of building transistors with non-planar (3D)
architectures: FinFET (tri-gate) and GAA (gate-all-around).
Needed because planar transistors suffered excessive short-channel
effects below 22nm.

- Concept: 1980s (Hisamoto, D. et al., FINFET concept)
- Lab: 1990s (UC Berkeley, IBM research)
- Pilot: 2000s (Intel 22nm development)
- Production: 2011 (Intel Ivy Bridge, 22nm FinFET)
- GAA production: 2022 (Samsung 3nm GAA)
- Mature: 2015+ (FinFET); GAA still maturing

#### 4. EUV_LITHOGRAPHY

The capability of using extreme ultraviolet (13.5nm wavelength)
light for photolithography. Needed because ArF immersion with
multi-patterning reached its practical limit at ~7nm.

- Concept: 1989 (soft X-ray lithography proposed)
- Lab: 1990s (EUV LLC formed 1997, ASML acquired 2000s)
- Pilot: 2006 (ASML alpha demo tool)
- Pre-production: 2015 (ASML NXE:3100 beta)
- Production: 2018 (TSMC 7nm, Apple A12)
- Mature: 2020+ (5nm, 3nm)

#### 5. ADVANCED_PACKAGING

The capability of 3D and 2.5D chip packaging using through-silicon
vias (TSVs) and interposers. Needed because monolithic scaling
hit economic limits and heterogeneous integration became valuable.

- Concept: 1990s (TSV concept, early flip-chip)
- Lab: 2000s (IMEC, IBM research on TSVs)
- Pilot: 2008-2010 (Xilinx Virtex-7, TSMC CoWoS)
- Production: 2012 (Xilinx Virtex-7 28nm SSI)
- Mature: 2020+ (AMD 3D V-Cache, TSMC SoIC)

### Stable base capabilities (3)

These capabilities are at TRL 9 throughout the 1965-2025 window.
They are the semiconductor analog of Li-ion's ELECTRODE_COATING,
CELL_ASSEMBLY, ION_TRANSPORT — mature capabilities that form the
base against which rising capabilities combine.

#### 6. OPTICAL_LITHOGRAPHY

The capability of optical photolithography (g-line, i-line, DUV,
ArF — but NOT EUV, which is a separate rising capability). This
has been at TRL 9 since the first integrated circuits in the
1960s.

#### 7. PLANAR_TRANSISTOR

The capability of building planar MOSFET transistors. At TRL 9
since the 1960s. Note: NON_PLANAR_TRANSISTOR is a separate rising
capability; PLANAR_TRANSISTOR remains at TRL 9 throughout
(even after FinFET replaced it, because the capability of
building planar transistors didn't disappear — it just stopped
being the frontier).

#### 8. WAFER_FABRICATION

The capability of manufacturing silicon wafers and running
semiconductor fabs. At TRL 9 since the 1970s. Wafer size
transitions (100mm → 150mm → 200mm → 300mm) are manufacturing
scale-up, not new capabilities.

---

## Why 8 capabilities (not 10)

The Li-ion ontology had 10 capabilities (3 rising, 7 stable).
The semiconductor ontology has 8 (5 rising, 3 stable). The
difference:

- Li-ion had MORE stable capabilities because battery
  manufacturing is a mature discipline with many sub-capabilities
  (coating, assembly, ion transport, electron collection).
- Semiconductors have MORE rising capabilities because the
  domain is defined by successive technology generations, each
  of which is a distinct capability that rises from concept to
  production.

This is a domain-specific structural difference, not an ontology
inconsistency. The methodology (capability + trajectory +
adjacency + frozen formula) transfers; the specific capabilities
do not.

---

## What this ontology does NOT include

- **DESIGN_AUTOMATION (EDA).** Excluded because EDA tools are
  an enabler of design, not a capability in the trajectory sense.
  EDA maturity affects design productivity but doesn't directly
  produce invention events.
- **POWER_MANAGEMENT.** Excluded because power efficiency is a
  design goal, not a discrete capability. DVFS, clock gating,
  and power gating are techniques, not capabilities.
- **STRAIN ENGINEERING.** Excluded because strained silicon
  (introduced at 90nm, 2004) is a material innovation that's
  subsumed under PLANAR_TRANSISTOR's continued maturity, not a
  separate rising capability.
- **SOI (Silicon-on-Insulator).** Excluded because SOI is a
  substrate choice, not a capability. IBM/AMD used SOI at 90nm
  and 65nm, but it didn't become the industry standard.

These exclusions are deliberate. The ontology tracks capabilities
that RISE (have non-zero velocity) and that combine to produce
invention events. Enablers, techniques, and substrate choices
are tracked in the bottleneck registry, not the capability
ontology.

---

## Enforcement

- This ontology is frozen once committed. It cannot be modified
  after the backtest runs (Law 7).
- If the backtest reveals the ontology is missing a capability,
  the missing capability is noted in the results, but the
  backtest is NOT re-run with the augmented ontology. The
  ontology is the test; augmenting it after seeing results is
  curve-fitting.
- The TRL trajectories for each capability are in
  SEMICONDUCTOR_TRAJECTORY_REGISTRY.md (separate artifact,
  committed before backtest).
