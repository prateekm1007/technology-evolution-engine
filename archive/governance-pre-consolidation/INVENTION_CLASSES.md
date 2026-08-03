# INVENTION_CLASSES

**Status:** Phase 14S taxonomy.
**Location:** repo root.
**Phase:** 14S.

> I no longer think you are studying a single phenomenon called
> "invention." I think you are studying a family of related
> phenomena.
> — CEO directive, Phase 14S

---

## Purpose

This document classifies the invention events observed across
Li-ion, photovoltaics, semiconductors, and telecommunications into
candidate classes. The classification is descriptive, not
prescriptive — it organizes what the boundary registry
(BOUNDARY_REGISTRY.md) already documents, without proposing new
formulas or fixes.

The frozen formula `score = max(dTRL/dt) × adjacency` addresses
only two of these classes (Emergence and Recombination). The other
three are not addressed — they are not "theory failures" so much
as out-of-scope cases that the formula was never designed to handle.

---

## The five candidate classes

| Class | Mechanism | What accumulates | What triggers the event | Theory's coverage |
|---|---|---|---|---|
| Emergence | Capability formation | TRL of a new capability (1 → 9) | Capability crosses a maturity threshold (typically TRL ≥ 7) | COVERED (velocity term) |
| Scaling | Efficiency improvement | Cumulative production volume, defect density, yield | Optimization within an already-mature capability | NOT COVERED |
| Coordination | Synchronization | Standards consensus (3GPP release phase) | Standards body reaches consensus | NOT COVERED |
| Recombination | Combination | Adjacency between existing capabilities | A reachable combination becomes realized | COVERED (adjacency term) |
| Discovery | Scientific advance | Understanding of physical/biological mechanism | A scientific result enables a new capability | NOT COVERED |

---

## Class definitions

### 1. Emergence

**Definition:** A new capability forms and rises from low TRL
to TRL 9. The event is the capability's arrival at a maturity
threshold that makes it usable in combinations.

**Signature:**
- A capability with TRL < 5 at T-k reaches TRL ≥ 7 by T.
- The combination includes this rising capability.
- The event would not have been possible without the capability
  reaching the threshold.

**Examples from the registries:**
- 1997 copper interconnect (COPPER_INTERCONNECT rises TRL 6 → 8 → 9)
- 2007 45nm high-k (HIGH_K_GATE_STACK rises TRL 6 → 8 → 9)
- 2011 Intel 22nm FinFET (NON_PLANAR_TRANSISTOR rises TRL 7 → 8 → 9)
- 1997 Li-ion EV (STATE_OF_CHARGE_MONITORING rises TRL 4 → 9)
- 2008 Tesla Roadster (THERMAL_MANAGEMENT rises TRL 6 → 9)
- 2019 Porsche Taycan (FAST_CHARGING rises TRL 8 → 9)

**What the formula does for this class:** The velocity term
`max(dTRL/dt)` detects the rising capability. The formula assigns
high scores to combinations containing rising capabilities. This
is the formula's HOME TERRITORY.

**Failure modes within this class (from BOUNDARY_REGISTRY.md):**
- Pattern 3 (threshold granularity, 5 semiconductor cases): the
  capability IS rising, but the 5-year TRL snapshot granularity
  produces velocity exactly at the 0.20 threshold. This is a
  measurement problem, not a class problem.
- Pattern 2 (telecom generation transitions, 7 cases): these ARE
  emergence events (new generations are emerging), but the
  trajectory model represents them as plateaued because the
  capability "re-rises." This is a state-variable problem
  (see STATE_VARIABLES.md), not a class problem.

### 2. Scaling

**Definition:** An efficiency improvement within an already-mature
capability. The capability is at TRL 9 and remains at TRL 9. The
event is an optimization (more transistors per chip, more bits
per Hz, more capacity per kWh) rather than a capability formation.

**Signature:**
- All capabilities in the combination are at TRL 9 at T-1.
- The event is characterized by a quantitative metric improving
  (transistor count, data rate, energy density) rather than a
  new capability appearing.
- No capability crosses a maturity threshold.

**Examples from the registries:**
- 1971 Intel 4004 (10um, 2300 transistors — scaling within mature
  optical lithography + planar transistor + wafer fabrication)
- 1985 Intel 386 (1.5um, 275K transistors — same scaling)
- 1993 Intel Pentium (0.8um, 3.1M transistors — same scaling)
- 1995 0.35um DRAM (scaling of lithography + wafer fabrication)
- 2001 130nm strained silicon (material optimization within
  mature planar transistor capability)
- 2010 Samsung Galaxy S (mass-market scaling of smartphone
  hardware)
- 2014 LTE Advanced (carrier aggregation, MIMO — optimization
  within mature 4G)
- 2017 Gigabit LTE (modem complexity optimization)
- 2020 AMD 3D V-Cache (post-maturity packaging refinement)
- 2022 Samsung 3nm GAA (architecture refinement within
  mature NON_PLANAR_TRANSISTOR)

**What the formula does for this class:** The velocity term
produces 0 (no rising capability). The formula assigns low
scores to scaling combinations. The formula CANNOT detect
scaling events — they are out of scope.

**What would detect scaling events:** A different formula
using a scaling metric (transistor count, data rate, energy
density) as the state variable. This is NOT the frozen formula's
job.

### 3. Coordination

**Definition:** An event triggered by synchronization among
multiple actors — typically a standards body reaching consensus.
The capabilities involved are already mature; the bottleneck is
coordination, not capability.

**Signature:**
- All capabilities in the combination are at TRL 9 at T-1.
- The event coincides with a standards-body release (3GPP
  freeze, IEEE standard, IEC specification).
- The event would not have occurred without the consensus,
  even though the capabilities existed.

**Examples from the registries:**
- 1991 GSM 2G (GSM group formed 1982, standard frozen 1990,
  commercial 1991 — coordination event)
- 2001 WCDMA 3G (3GPP formed 1998, Release 99 frozen 2000 —
  coordination event)
- 2009 LTE 4G (3GPP Release 8 frozen 2008 — coordination event)
- 2016 NB-IoT (3GPP Release 13 — coordination event)
- 2019 5G NR sub-6 (3GPP Release 15 frozen 2018 — coordination
  event)

**What the formula does for this class:** The velocity term
produces 0 (capabilities plateaued). The formula CANNOT
detect coordination events — they require a coordination-state
variable, not a capability-state variable.

**What would detect coordination events:** A formula using
standards-body release phase as a state variable. This is NOT
the frozen formula's job.

### 4. Recombination

**Definition:** An event triggered by a combination of existing
capabilities becoming reachable. The capabilities are mature;
the event is the realization of an adjacent-possible combination.

**Signature:**
- All capabilities in the combination are at TRL ≥ 7 at T-1.
- The combination is graph-distance ≤ 2 from existing realized
  combinations.
- The event is the first realization of this specific combination.

**Examples from the registries:**
- 1997 Li-ion with BMS in EVs (EES + INTERCALATION + SoC —
  combination of mature capabilities)
- 2012 Tesla Supercharger (FAST_CHARGING + THERMAL_MANAGEMENT —
  combination)
- 2019 Porsche Taycan 800V (FAST_CHARGING + THERMAL_MANAGEMENT +
  SAFETY_PROTECTION — combination)
- 2009 TSV 3D packaging (ADVANCED_PACKAGING + OPTICAL_LITHOGRAPHY
  — combination)
- 2020 AMD 3D V-Cache (ADVANCED_PACKAGING + NON_PLANAR_TRANSISTOR
  — combination)

**What the formula does for this class:** The adjacency term
`1/(1+distance)` detects reachable combinations. The formula
assigns high scores to combinations that are close to existing
realized ones. This is the formula's HOME TERRITORY (along with
Emergence).

**Failure modes within this class:**
- Pattern 5 (adjacency competition, 3 telecom cases): the
  combination IS reachable, but other high-adjacency combinations
  fill the Top-10. This is a selection problem, not a class
  problem.

### 5. Discovery

**Definition:** A scientific advance that enables a new capability.
The event is not a capability formation or a combination — it is
a scientific result that changes what is possible.

**Signature:**
- A scientific paper, patent, or experimental result is published.
- The result enables a new capability that did not previously
  exist, even conceptually.
- The event is the discovery, not the commercialization.

**Examples from the registries:**
- (None in the current event registries — all events are
  commercialization events, not discovery events.)
- Candidate examples from outside the current registries:
  - 1947 Bardeen, Brattain, Shockley transistor effect (discovery
    that enabled PLANAR_TRANSISTOR)
  - 1989 Hisamoto FINFET paper (discovery that enabled
    NON_PLANAR_TRANSISTOR)
  - 2003 Goodenough LFP discovery (discovery that enabled a new
    Li-ion cathode chemistry)
  - 1989 Aggregation-induced emission (discovery in materials
    science)

**What the formula does for this class:** The formula has no
concept of scientific discovery. TRL begins at 1 (concept), but
the transition from "no capability" to "TRL 1" is not modeled.
Discovery is BEFORE the formula's domain.

**What would detect discovery events:** A formula using scientific
publication rate, citation velocity, or experimental replication
count as state variables. This is NOT the frozen formula's job.

---

## Class distribution across domains

| Domain | Emergence | Scaling | Coordination | Recombination | Discovery | Total |
|---|---|---|---|---|---|---|
| Li-ion | 3 | 0 | 0 | 13 | 0 | 16 |
| Photovoltaics | 2 | 0 | 0 | 0 | 0 | 2 |
| Semiconductors | 5 | 5 | 0 | 5 | 0 | 15 |
| Telecom | 1 | 4 | 5 | 0 | 0 | 10 |
| (some events fit multiple classes) | | | | | | |

**Key observation:** Li-ion is dominated by Recombination (13/16).
Semiconductors are evenly split (5 Emergence, 5 Scaling, 5
Recombination). Telecom is dominated by Coordination (5/10). This
explains why the formula (which covers Emergence + Recombination)
worked on Li-ion and failed on telecom.

---

## What this classification does NOT do

- It does not propose new formulas. Each class may require a
  different formula; that is a post-Phase-14 question.
- It does not claim the five classes are exhaustive. Other classes
  may exist (e.g., "regulatory change" might be distinct from
  "coordination"). The classification is a candidate, not a
  final taxonomy.
- It does not grade the formula's performance per class. That
  grading would require per-class backtests, which would require
  per-class formulas (not authorized).
- It does not address H2 (velocity vs acceleration). Acceleration
  is a different state variable for the same class (Emergence),
  not a different class.

---

## Pre-stated falsifier (EP-4)

**Claim:** Invention falls into one of five classes (Emergence,
Scaling, Coordination, Recombination, Discovery), and the frozen
formula addresses only Emergence and Recombination.

**Falsifier:** An event that does not fit any of the five classes.
Such an event would have:
- No rising capability (not Emergence)
- No mature-capability optimization (not Scaling)
- No standards-body consensus (not Coordination)
- No new combination of existing capabilities (not Recombination)
- No scientific advance (not Discovery)

If such an event is found, the classification is incomplete and a
sixth class is needed. (Candidate: "regulatory change" — events
triggered by government action, like spectrum auctions or drug
approvals, that are not standards-body coordination.)

This falsifier is PENDING — no event has been found yet that does
not fit one of the five classes.
