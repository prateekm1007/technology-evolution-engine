# PROCESS_CLASSIFIER

**Status:** Phase 15 Deliverable 1.
**Location:** repo root.
**Phase:** 15.

> Classification precedes prediction.
> There may be a universal classifier, even if there is no
> universal invention formula.
> — CEO directive, Phase 15, Principles 1 and 3

---

## Purpose

This document defines the schema and content of the process
classifier. The classifier's job is to determine WHICH KIND OF
PROCESS a candidate event belongs to BEFORE any formula is
applied. Per Principle 3, classification precedes prediction:
no formula runs until the class is identified.

The five classes (Discovery, Emergence, Scaling, Coordination,
Recombination) are inherited from INVENTION_CLASSES.md (Phase 14S)
and re-articulated here as the foundation of the reachability
engine architecture. The frozen formula
`score = max(dTRL/dt) × adjacency` from Phase 11 is NOT modified,
NOT retracted, NOT extended. It is one of several instruments —
specifically, it is the Emergence + Recombination instrument. The
other four classes require other instruments that have not been
built.

---

## Schema

```typescript
interface ProcessClass {
    id: string;

    name:
        | "DISCOVERY"
        | "EMERGENCE"
        | "SCALING"
        | "COORDINATION"
        | "RECOMBINATION";

    description: string;

    dominantStateVariables: string[];

    characteristicPatterns: string[];

    examples: string[];

    exclusions: string[];
}
```

### Field semantics

| Field | Type | Required | Meaning |
|---|---|---|---|
| `id` | string | yes | PC-XXX identifier. |
| `name` | enum | yes | One of the five canonical class names. |
| `description` | string | yes | One-paragraph description of what this class IS (not what it predicts). |
| `dominantStateVariables` | string[] | yes | The state variables (per STATE_SPACE.md) that primarily drive this class. Other variables may matter; these are dominant. |
| `characteristicPatterns` | string[] | yes | Observable features that identify this class. Used by the (unbuilt) classifier to assign class. Must be checkable from data, not interpretive. |
| `examples` | string[] | yes | Concrete events from the project's registries that exemplify this class. |
| `exclusions` | string[] | yes | What this class is NOT. Specifically, the boundary cases that might be confused with this class but belong elsewhere. |

### What this schema forbids

- A class without `exclusions`. The exclusions are the boundary; without them, the class is unbounded and the classifier cannot distinguish.
- A `description` that mentions prediction. The classifier describes WHAT IS, not WHAT WILL BE. Prediction is downstream.
- A `dominantStateVariables` list with more than 3 entries. If more than 3 state variables dominate, the class is probably two classes combined and should be split.

---

## The five process classes

### PC-001: DISCOVERY

| Field | Value |
|---|---|
| id | PC-001 |
| name | DISCOVERY |
| description | A scientific advance that enables a new capability or class of capabilities. The event is the publication or experimental confirmation of a result that changes what is physically possible. The event is NOT the commercialization — it is the discovery itself. |
| dominantStateVariables | ["scientific_state"] |
| characteristicPatterns | ["publication of a peer-reviewed paper or patent that introduces a new concept", "experimental confirmation of a previously-theoretical effect", "a TRL-1-to-TRL-2 transition (concept to basic principles) for a capability that did not previously exist", "the event is upstream of any commercial deployment by 5-20+ years"] |
| examples | ["1947 Bardeen/Brattain/Shockley transistor effect (Bell Labs) — enabled PLANAR_TRANSISTOR", "1989 Hisamoto FINFET paper — enabled NON_PLANAR_TRANSISTOR", "1980 Goodenough LCO cathode — enabled Li-ion intercalation chemistry", "1989 mRNA lipid nanoparticle concept (Malone) — enabled mRNA vaccines (commercialized 30 years later)"] |
| exclusions | ["A capability reaching TRL 9 (that is Emergence or Scaling, not Discovery)", "A new combination of existing capabilities (that is Recombination)", "A standards-body consensus (that is Coordination)", "Discovery events are upstream of the current event registries — the project's registries begin at commercialization, not at discovery"] |

### PC-002: EMERGENCE

| Field | Value |
|---|---|
| id | PC-002 |
| name | EMERGENCE |
| description | A capability forms and rises from low TRL to TRL 9. The event is the capability's arrival at a maturity threshold that makes it usable in combinations. This is the class the frozen formula `velocity × adjacency` was designed for. |
| dominantStateVariables | ["capability_state", "scientific_state"] |
| characteristicPatterns | ["a capability with TRL < 5 at T-k reaches TRL ≥ 7 by T", "the event would not have been possible without the capability reaching the threshold", "the velocity (dTRL/dt) is non-zero and rising", "the event is the first commercial deployment of the new capability (or the first major product using it)"] |
| examples | ["1997 copper interconnect (COPPER_INTERCONNECT TRL 6→8→9)", "2007 45nm high-k (HIGH_K_GATE_STACK TRL 6→8→9)", "1997 Li-ion with BMS in EVs (STATE_OF_CHARGE_MONITORING TRL 4→9)", "2008 Tesla Roadster (THERMAL_MANAGEMENT TRL 6→9)", "2019 Porsche Taycan 800V (FAST_CHARGING TRL 8→9)", "1983 AMPS 1G (WIRELESS_PROTOCOL TRL 3→9 for 1G)"] |
| exclusions | ["A capability rising for a NEW GENERATION after already reaching TRL 9 (that is a Coordination event, not Emergence — see PC-004)", "An efficiency improvement within a mature capability (that is Scaling)", "A scientific result that enables a new capability (that is Discovery — upstream of Emergence)", "A combination of mature capabilities becoming reachable (that is Recombination)"] |

### PC-003: SCALING

| Field | Value |
|---|---|
| id | PC-003 |
| name | SCALING |
| description | An efficiency improvement within an already-mature capability. The capability is at TRL 9 and remains at TRL 9. The event is an optimization (more transistors per chip, more bits per Hz, more capacity per kWh) rather than a capability formation. |
| dominantStateVariables | ["manufacturing_state", "economic_state"] |
| characteristicPatterns | ["all capabilities in the combination are at TRL 9 at T-1", "the event is characterized by a quantitative metric improving (transistor count, data rate, energy density, cost per unit)", "no capability crosses a maturity threshold", "the velocity (dTRL/dt) is zero for all capabilities in the combination"] |
| examples | ["1971 Intel 4004 (10um, 2300 transistors)", "1985 Intel 386 (1.5um, 275K transistors)", "1993 Intel Pentium (0.8um, 3.1M transistors)", "1995 0.35um DRAM (64M cells)", "2001 130nm strained silicon", "2010 Samsung Galaxy S (mass-market smartphone)", "2014 LTE Advanced (carrier aggregation, 4x4 MIMO)", "2017 Gigabit LTE (1 Gbps peak rate)", "2020 AMD 3D V-Cache (post-maturity packaging refinement)", "2022 Samsung 3nm GAA (architecture refinement within mature NON_PLANAR_TRANSISTOR)"] |
| exclusions | ["A new capability forming (that is Emergence)", "A new generation of an existing capability (that is Coordination — the standard changed)", "A scientific result enabling a new metric (that is Discovery)", "Scaling is the LARGEST class in the semiconductor and telecom event registries, which is why the frozen formula (which detects Emergence, not Scaling) failed on those domains"] |

### PC-004: COORDINATION

| Field | Value |
|---|---|
| id | PC-004 |
| name | COORDINATION |
| description | An event triggered by synchronization among multiple actors — typically a standards body reaching consensus, a regulatory body granting approval, or an industry consortium agreeing on a specification. The capabilities are already mature; the bottleneck is coordination, not capability. |
| dominantStateVariables | ["coordination_state", "institutional_state", "regulatory_state"] |
| characteristicPatterns | ["all capabilities in the combination are at TRL 9 at T-1 (already mature)", "the event coincides with a standards-body release, regulatory approval, or industry consortium agreement", "the event would not have occurred without the consensus, even though the capabilities existed", "the velocity (dTRL/dt) is zero — capabilities are plateaued", "the bottleneck is the coordination process, not the capability trajectory"] |
| examples | ["1991 GSM 2G commercial launch (GSM MoU 1987, standard frozen 1990)", "2001 WCDMA 3G (3GPP formed 1998, Release 99 frozen 2000)", "2009 LTE 4G (3GPP Release 8 frozen 2008)", "2016 NB-IoT (3GPP Release 13)", "2019 5G NR sub-6GHz (3GPP Release 15 frozen 2018)", "2003 LFP cathode commercialization (Goodenough patent licensing)", "2010 mass-market EVs (Nissan Leaf, Chevy Volt — government subsidies as coordination enabler)"] |
| exclusions | ["A genuinely new capability emerging (that is Emergence — Coordination requires mature capabilities)", "An efficiency improvement within mature capabilities WITHOUT a coordination event (that is Scaling)", "A scientific result that enables coordination (that is Discovery — upstream)", "A combination of mature capabilities becoming reachable WITHOUT coordination (that is Recombination)"] |

### PC-005: RECOMBINATION

| Field | Value |
|---|---|
| id | PC-005 |
| name | RECOMBINATION |
| description | An event triggered by a combination of existing capabilities becoming reachable. The capabilities are mature (TRL ≥ 7); the event is the realization of an adjacent-possible combination. No new capability is needed; the existing ones combine in a new way. |
| dominantStateVariables | ["capability_state", "infrastructure_state"] |
| characteristicPatterns | ["all capabilities in the combination are at TRL ≥ 7 at T-1 (already mature)", "the combination is graph-distance ≤ 2 from existing realized combinations (high adjacency)", "the event is the first realization of this specific combination", "the velocity (dTRL/dt) may be zero — what matters is that the combination is newly reachable, not that any capability is rising", "often triggered by an ENABLING capability reaching TRL 9 that makes a previously-impossible combination possible"] |
| examples | ["1997 Li-ion with BMS in EVs (EES + INTERCALATION + SoC — combination of mature capabilities)", "2012 Tesla Supercharger (FAST_CHARGING + THERMAL_MANAGEMENT — combination)", "2019 Porsche Taycan 800V (FAST_CHARGING + THERMAL_MGMT + SAFETY_PROTECTION)", "2009 TSV 3D packaging (ADVANCED_PACKAGING + OPTICAL_LITHOGRAPHY)", "2020 AMD 3D V-Cache (ADVANCED_PACKAGING + NON_PLANAR_TRANSISTOR)", "2010 thin-film PV commercialization (ENERGY_CONVERSION + THIN_FILM_DEPOSITION — both mature, combination newly reachable)", "2019 bifacial PV modules (BIFACIAL_DESIGN + ENERGY_CONVERSION + MODULE_ASSEMBLY)"] |
| exclusions | ["A new capability forming and being combined (that is Emergence — the rising capability is the trigger)", "A combination triggered by a standards body (that is Coordination)", "A combination that requires no new coordination AND involves a rising capability (that is Emergence with Recombination — Emergence dominates)", "Recombination is the LARGEST class in the Li-ion event registry, which is why the frozen formula (which includes adjacency) works on Li-ion"] |

---

## Cross-class analysis

### Class distribution across domains (re-stated from INVENTION_CLASSES.md)

| Domain | Discovery | Emergence | Scaling | Coordination | Recombination | Total |
|---|---|---|---|---|---|---|
| Li-ion | 0 | 3 | 0 | 0 | 13 | 16 |
| Photovoltaics | 0 | 2 | 0 | 0 | 0 | 2 |
| Semiconductors | 0 | 5 | 5 | 0 | 5 | 15 |
| Telecom | 0 | 1 | 4 | 5 | 0 | 10 |

**Key observations:**

1. **Discovery is absent from all event registries.** The registries begin at commercialization; Discovery is upstream by 5-20+ years. The project has never tested Discovery because it has no Discovery events in its data.

2. **Each domain is dominated by 1-2 classes.** Li-ion is dominated by Recombination. Semiconductors are evenly split. Telecom is dominated by Coordination. This explains why the frozen formula (Emergence + Recombination) works on Li-ion and fails on telecom.

3. **The frozen formula addresses 2 of 5 classes** (Emergence and Recombination). The other 3 classes (Discovery, Scaling, Coordination) require other instruments that have not been built.

### Class overlap

Some events fit multiple classes. The classifier must resolve which class dominates:

| Overlap case | Dominant class | Reason |
|---|---|---|
| Emergence + Recombination (rising capability + new combination) | Emergence | The rising capability is the trigger; the combination is the form |
| Scaling + Coordination (efficiency improvement + standards release) | Coordination | The standards release is the trigger; the efficiency is the form |
| Recombination + Coordination (new combination + standards release) | Coordination | The standards release enables the combination |
| Discovery + Emergence (scientific result + capability formation) | Discovery | The discovery is upstream; the emergence is downstream |

The dominance rule: **the class whose absence would have prevented the event dominates.** If the scientific discovery hadn't happened, no capability would have emerged → Discovery dominates. If the standard hadn't been agreed, no commercial deployment → Coordination dominates.

---

## What the classifier does NOT do

- It does not predict. It classifies. Prediction is downstream.
- It does not run any formula. The frozen formula runs only after the classifier assigns a class.
- It does not modify the frozen formula. The formula is unchanged (Rule 1, Phase 14 close).
- It does not claim the five classes are exhaustive. A sixth class may exist (e.g., "regulatory change" as distinct from Coordination). The falsifier is pending.

---

## Pre-stated falsifier (EP-4)

**Claim:** The five classes (Discovery, Emergence, Scaling, Coordination, Recombination) cover all invention events in the project's registries.

**Falsifier:** An event that does not fit any of the five classes — i.e., an event where:
- No scientific advance was the trigger (not Discovery)
- No capability crossed a maturity threshold (not Emergence)
- No efficiency improvement within mature capabilities (not Scaling)
- No standards-body or regulatory consensus (not Coordination)
- No new combination of existing capabilities (not Recombination)

If such an event is found, a sixth class is needed.

**Status:** PENDING. No event in the current registries (Li-ion, PV, semiconductors, telecom) fails to fit one of the five classes. But the registries are not exhaustive — future domains (aviation, pharmaceuticals, others) may reveal events that do not fit.
