# MECHANISM_REGISTRY_V2

**Status:** Phase 15 Deliverable 2.
**Location:** repo root.
**Phase:** 15.

> Mechanisms before formulas.
> — CEO directive, Phase 15, REACHABILITY_CONSTITUTION rule

---

## Purpose

This document defines the schema for mechanisms — the causal
processes by which reachability changes within a process class.
Whereas PROCESS_CLASSIFIER.md defines WHAT a process is, this
document defines HOW the process produces reachability.

A mechanism is a specific causal chain: inputs → constraints →
outputs. The frozen formula `velocity × adjacency` is ONE
mechanism (the Emergence + Recombination mechanism). Other
classes require other mechanisms.

This document is the schema and seed registry. It is descriptive
— mechanisms are cataloged from existing evidence, not invented.
The frozen formula is NOT modified.

---

## Schema

```typescript
interface Mechanism {
    mechanismId: string;

    class: string;

    inputs: string[];

    constraints: string[];

    outputs: string[];

    evidence: string[];
}
```

### Field semantics

| Field | Type | Required | Meaning |
|---|---|---|---|
| `mechanismId` | string | yes | MECH-XXX identifier. Sequential within class. |
| `class` | string | yes | One of the five classes from PROCESS_CLASSIFIER.md. |
| `inputs` | string[] | yes | The state variables (per STATE_SPACE.md) that must be present for the mechanism to fire. Each input must reference a specific state variable and a specific value range. |
| `constraints` | string[] | yes | The conditions that block the mechanism from firing. A constraint is "what prevents this mechanism from producing output." If any constraint is active, the mechanism does not fire — even if inputs are present. |
| `outputs` | string[] | yes | What the mechanism produces when inputs are present AND constraints are absent. Must be observable — a state change in some state variable, or a new event in an event registry. |
| `evidence` | string[] | yes | Cited events from the project's registries that exemplify this mechanism. At least 1 citation required. |

### What this schema forbids

- A mechanism without `constraints`. Every mechanism has constraints — "no constraints" means the mechanism always fires, which is implausible and unfalsifiable.
- A mechanism whose `outputs` are not observable. If the output cannot be checked against an event registry or a state trajectory, the mechanism is untestable.
- A mechanism whose `inputs` reference a state variable not in STATE_SPACE.md. The state space is the canonical vocabulary; ad-hoc state variables are forbidden.
- A mechanism without `evidence`. Mechanisms must be grounded in actual events. Speculative mechanisms (with no cited example) belong in OPEN_QUESTIONS.md, not here.

---

## Seed mechanism registry

The mechanisms below are cataloged from the project's existing
evidence (Li-ion, PV, semiconductors, telecom). They are not
exhaustive — more mechanisms exist and will be added as evidence
accumulates.

### Class: DISCOVERY

#### MECH-D001: Scientific publication enables new capability concept

| Field | Value |
|---|---|
| mechanismId | MECH-D001 |
| class | DISCOVERY |
| inputs | ["scientific_state: a peer-reviewed paper or experimental result is published that introduces a new concept (TRL 1) for a capability that did not previously exist"] |
| constraints | ["the concept must be reproducible (not a single unrepeated experiment)", "the concept must be physically plausible (does not violate known physical laws)", "the concept must have at least one potential application domain"] |
| outputs | ["a new capability node enters the ontology at TRL 1", "downstream Emergence mechanisms may now fire (the capability can begin its rise to TRL 9)"] |
| evidence | ["1947 Bardeen/Brattain/Shockley transistor effect → enabled PLANAR_TRANSISTOR (TRL 1 in 1947, TRL 9 by 1960s)", "1989 Hisamoto FINFET paper → enabled NON_PLANAR_TRANSISTOR (TRL 1 in 1989, TRL 9 by 2011)", "1980 Goodenough LCO cathode → enabled Li-ion intercalation (TRL 1 in 1980, TRL 9 by 1991)", "1989 Malone mRNA-LNP concept → enabled mRNA vaccines (TRL 1 in 1989, TRL 9 by 2020)"] |

**Note:** Discovery events are upstream of the project's current
event registries (which begin at commercialization). The evidence
cited here is from public scientific history, not from the
project's registries. The Discovery class is the least-tested
class in the project.

---

### Class: EMERGENCE

#### MECH-E001: Rising capability crosses maturity threshold

| Field | Value |
|---|---|
| mechanismId | MECH-E001 |
| class | EMERGENCE |
| inputs | ["capability_state: a capability with TRL < 5 at T-k", "scientific_state: the underlying science is sound (TRL ≥ 3)", "manufacturing_state: the capability can be produced at the required quality (TRL ≥ 5)"] |
| constraints | ["no physical constraint blocks the capability (e.g., thermal runaway threshold not exceeded)", "no economic constraint blocks the capability (e.g., cost per unit is not 10x above market)", "no regulatory constraint blocks the capability (e.g., no certification required, or certification is achievable)"] |
| outputs | ["the capability crosses TRL ≥ 7 (system prototype demonstrated)", "combinations containing the capability become reachable (adjacency term activates)", "an Emergence-class invention event may occur within 1-5 years"] |
| evidence | ["1997 copper interconnect (COPPER_INTERCONNECT TRL 6→8→9 from 1985-1997)", "2007 45nm high-k (HIGH_K_GATE_STACK TRL 6→8→9 from 1995-2007)", "2008 Tesla Roadster (THERMAL_MANAGEMENT TRL 6→9 from 2000-2008)", "1997 Li-ion BMS EV (STATE_OF_CHARGE_MONITORING TRL 4→9 from 1990-1995)"] |

**This is the mechanism the frozen formula `max(dTRL/dt) ×
adjacency` was designed to detect.** The velocity term measures
the input (rising capability_state). The adjacency term measures
the output (combinations becoming reachable). The formula is an
instrument for THIS mechanism — not for the others.

#### MECH-E002: Accelerating capability approaches inflection

| Field | Value |
|---|---|
| mechanismId | MECH-E002 |
| class | EMERGENCE |
| inputs | ["capability_state: a capability with non-zero acceleration (d²TRL/dt² > 0)", "scientific_state: the underlying science is maturing (TRL ≥ 4)"] |
| constraints | ["the acceleration is sustained for ≥ 2 time periods (not a single-period spike)", "no constraint blocks continued acceleration"] |
| outputs | ["the capability is approaching a maturity-threshold crossing (MECH-E001 will fire soon)", "an Emergence-class invention event is IMMINENT (1-2 year horizon, vs 5-year for MECH-E001)"] |
| evidence | ["FAST_CHARGING TRL trajectory 1990-2012 (sustained acceleration across multiple periods)", "THERMAL_MANAGEMENT TRL trajectory 1990-2005 (acceleration 2000-2003)"] |

**Note:** MECH-E002 is UNTESTED. The frozen formula uses velocity
(dTRL/dt), not acceleration (d²TRL/dt²). This mechanism is H2
from PHASE_14R_REFLECTION.md — the hypothesis that acceleration
may be more fundamental than velocity. Testing it requires a new
formula (unfreezing the current one), which is outside Phase 15's
scope.

---

### Class: SCALING

#### MECH-S001: Manufacturing yield improvement enables cost decline

| Field | Value |
|---|---|
| mechanismId | MECH-S001 |
| class | SCALING |
| inputs | ["manufacturing_state: cumulative production volume is rising", "manufacturing_state: defect density is declining", "economic_state: cost per unit is declining (Wright's Law: ~20% per doubling)"] |
| constraints | ["the capability is at TRL 9 (mature)", "no physical limit has been reached (e.g., no wavelength-of-light floor)", "market demand exists for the scaled output"] |
| outputs | ["more units produced at lower cost per unit", "the capability is deployed more widely", "a Scaling-class invention event may occur (new product at scale, mass-market deployment)"] |
| evidence | ["1971-2001 Intel microprocessor scaling (10um → 0.13um, 2300 → 3.1M transistors)", "1991-2010 Li-ion cost decline ($3000/kWh → $300/kWh, enabled mass-market EVs)", "2009-2020 smartphone mass-market scaling (Galaxy S → 5G era, billion-unit installed base)"] |

**Note:** MECH-S001 uses manufacturing_state and economic_state —
NOT capability_state. The frozen formula (which uses TRL) cannot
detect this mechanism. A different instrument is required.

#### MECH-S002: Process refinement within mature capability

| Field | Value |
|---|---|
| mechanismId | MECH-S002 |
| class | SCALING |
| inputs | ["manufacturing_state: a mature manufacturing process (TRL 9)", "scientific_state: incremental process improvements identified"] |
| constraints | ["no new capability is formed (the improvement is within the existing capability)", "the improvement does not require a new standard or certification"] |
| outputs | ["a refined version of the mature capability is deployed", "a Scaling-class invention event (post-maturity exploitation) may occur"] |
| evidence | ["2020 AMD 3D V-Cache (refinement of mature ADVANCED_PACKAGING)", "2022 Samsung 3nm GAA (refinement within mature NON_PLANAR_TRANSISTOR — though GAA is arguably a new sub-capability)", "2017 Gigabit LTE (modem complexity optimization within mature 4G)"] |

---

### Class: COORDINATION

#### MECH-C001: Standards-body consensus convergence

| Field | Value |
|---|---|
| mechanismId | MECH-C001 |
| class | COORDINATION |
| inputs | ["coordination_state: a standards body is in the work-item phase (3GPP, IEEE, IEC)", "institutional_state: participating organizations have agreed on key technical parameters", "capability_state: the underlying capabilities are mature (TRL ≥ 7)"] |
| constraints | ["no participating organization exercises a veto", "no competing standard has gained decisive market share (e.g., WiMAX vs LTE)", "spectrum or regulatory allocation is available (if required)"] |
| outputs | ["a standard is frozen and published", "commercial deployment becomes authorized", "a Coordination-class invention event may occur (first commercial deployment under the new standard)"] |
| evidence | ["1991 GSM 2G (GSM MoU 1987, standard frozen 1990, commercial 1991)", "2001 WCDMA 3G (3GPP formed 1998, Release 99 frozen 2000)", "2009 LTE 4G (3GPP Release 8 frozen 2008, commercial 2009)", "2019 5G NR sub-6GHz (3GPP Release 15 frozen 2018)"] |

**Note:** MECH-C001 uses coordination_state and institutional_state
— NOT capability_state. The frozen formula cannot detect this
mechanism. The telecom domain is dominated by MECH-C001, which is
why the formula failed there.

#### MECH-C002: Regulatory approval pathway

| Field | Value |
|---|---|
| mechanismId | MECH-C002 |
| class | COORDINATION |
| inputs | ["regulatory_state: a product has completed required safety/efficacy testing", "regulatory_state: the regulatory body is reviewing the application", "capability_state: the underlying capability is mature (TRL ≥ 7)"] |
| constraints | ["no safety/efficacy failure in testing", "no regulatory policy change that blocks approval (e.g., new restriction)", "the application is complete and compliant"] |
| outputs | ["regulatory approval is granted", "commercial deployment becomes legal", "a Coordination-class invention event may occur (first commercial deployment after approval)"] |
| evidence | ["2017 Kymriah CAR-T (FDA breakthrough designation → approval)", "2014 Keytruda PD-1 (FDA breakthrough → approval)", "2009 first 4G LTE deployments (regulatory spectrum allocation enabled deployment)", "2003 UN38.3 in force (enabled Li-ion transport certification)"] |

---

### Class: RECOMBINATION

#### MECH-R001: Adjacent combination becomes reachable

| Field | Value |
|---|---|
| mechanismId | MECH-R001 |
| class | RECOMBINATION |
| inputs | ["capability_state: all capabilities in the combination are at TRL ≥ 7", "capability_state: the combination is graph-distance ≤ 2 from existing realized combinations (high adjacency)", "infrastructure_state: any required infrastructure exists (e.g., charging stations, cell towers)"] |
| constraints | ["no capability in the combination is blocked by a constraint (e.g., thermal runaway)", "no regulatory barrier to the combination (e.g., certification required)", "the combination has not been realized before (novelty)"] |
| outputs | ["a new combination of existing capabilities is realized", "a Recombination-class invention event occurs"] |
| evidence | ["1997 Li-ion with BMS in EVs (EES + INTERCALATION + SoC — combination of mature capabilities, made reachable by SoC reaching TRL 9)", "2012 Tesla Supercharger (FAST_CHARGING + THERMAL_MANAGEMENT — combination)", "2019 Porsche Taycan 800V (FAST_CHARGING + THERMAL_MGMT + SAFETY_PROTECTION)", "2009 TSV 3D packaging (ADVANCED_PACKAGING + OPTICAL_LITHOGRAPHY)"] |

**This is the mechanism the frozen formula's adjacency term
`1/(1+distance)` was designed to detect.** The formula combines
MECH-E001 (velocity) and MECH-R001 (adjacency) into a single
score, which is why it works for Emergence + Recombination events
but not for pure Recombination events (where velocity is zero).

#### MECH-R002: Enabling capability makes combination reachable

| Field | Value |
|---|---|
| mechanismId | MECH-R002 |
| class | RECOMBINATION |
| inputs | ["capability_state: a previously-rising capability reaches TRL 9 (becomes stable base)", "capability_state: other capabilities in the combination are already at TRL ≥ 7"] |
| constraints | ["the newly-mature capability is not blocked by any constraint", "the combination is reachable (graph-distance ≤ 2)"] |
| outputs | ["a combination that was previously impossible (because one capability was below TRL 7) becomes reachable", "a Recombination-class invention event may occur (the combination is realized within 1-3 years)"] |
| evidence | ["1997 Li-ion BMS EV (STATE_OF_CHARGE_MONITORING reached TRL 9 → combination with EES + INTERCALATION became reachable)", "2008 Tesla Roadster (THERMAL_MANAGEMENT reached TRL 9 → combination with EES + SoC became reachable)", "2019 bifacial PV (BIFACIAL_DESIGN reached TRL 9 → combination with ENERGY_CONVERSION + MODULE_ASSEMBLY became reachable)"] |

**Note:** MECH-R002 is a hybrid — it is triggered by an Emergence
event (capability reaches TRL 9) but produces a Recombination
output (new combination becomes reachable). This is why the frozen
formula works: the velocity term detects the Emergence trigger, and
the adjacency term detects the Recombination output. The formula
is an instrument for MECH-R002 specifically.

---

## Cross-mechanism analysis

### Mechanisms the frozen formula detects

| Mechanism | Detected? | How |
|---|---|---|
| MECH-E001 (rising capability crosses threshold) | YES | velocity term `max(dTRL/dt)` |
| MECH-R001 (adjacent combination becomes reachable) | YES | adjacency term `1/(1+distance)` |
| MECH-R002 (enabling capability makes combination reachable) | YES | velocity term detects the trigger; adjacency term detects the output |

### Mechanisms the frozen formula does NOT detect

| Mechanism | Why not detected |
|---|---|
| MECH-D001 (scientific publication) | No scientific_state variable in formula |
| MECH-E002 (acceleration) | Formula uses velocity, not acceleration (H2 untested) |
| MECH-S001 (yield/cost scaling) | No manufacturing_state or economic_state in formula |
| MECH-S002 (process refinement) | No manufacturing_state in formula |
| MECH-C001 (standards consensus) | No coordination_state in formula |
| MECH-C002 (regulatory approval) | No regulatory_state in formula |

The frozen formula detects 3 of 8 mechanisms. The other 5 require
other instruments that have not been built.

### Mechanism overlap and dominance

Some events are produced by multiple mechanisms. The dominance
rule (from PROCESS_CLASSIFIER.md): the class whose absence would
have prevented the event dominates.

| Event | Mechanisms present | Dominant mechanism |
|---|---|---|
| 1997 copper interconnect | MECH-E001 + MECH-R001 | MECH-E001 (copper was rising — without the rise, no event) |
| 2009 LTE 4G | MECH-C001 + MECH-R001 (LTE combined WIRELESS_PROTOCOL + PACKET_SWITCHING, both mature) | MECH-C001 (without 3GPP Release 8, no deployment) |
| 2019 Porsche Taycan | MECH-R002 (FAST_CHARGING enabling) + MECH-R001 (combination reachable) | MECH-R002 (FAST_CHARGING reaching TRL 9 was the trigger) |
| 2020 AMD 3D V-Cache | MECH-S002 (process refinement) | MECH-S002 (post-maturity scaling) |

---

## What this registry does NOT do

- It does not propose formulas for each mechanism. Building formula instruments is post-Phase-15 work.
- It does not claim the 8 mechanisms are exhaustive. More mechanisms exist and will be added as evidence accumulates.
- It does not grade the mechanisms by importance. All mechanisms are cataloged equally.
- It does not address H2 (acceleration) directly — MECH-E002 is cataloged but untested.

---

## Pre-stated falsifier (EP-4)

**Claim:** The 8 mechanisms (MECH-D001, MECH-E001, MECH-E002, MECH-S001, MECH-S002, MECH-C001, MECH-C002, MECH-R001, MECH-R002 — note 9 if MECH-E002 counts) cover all reachability-changing processes in the project's event registries.

**Falsifier:** An event whose reachability change cannot be traced to any of these mechanisms — i.e., an event where:
- No scientific publication triggered it (not MECH-D001)
- No capability crossed a maturity threshold (not MECH-E001)
- No acceleration approached an inflection (not MECH-E002)
- No yield/cost improvement enabled it (not MECH-S001)
- No process refinement within mature capability (not MECH-S002)
- No standards-body consensus converged (not MECH-C001)
- No regulatory approval was granted (not MECH-C002)
- No adjacent combination became reachable (not MECH-R001)
- No enabling capability made a combination reachable (not MECH-R002)

If such an event is found, a new mechanism is needed.

**Status:** PENDING. The current event registries (Li-ion, PV, semiconductors, telecom) all fit at least one mechanism. But the registries are not exhaustive.
