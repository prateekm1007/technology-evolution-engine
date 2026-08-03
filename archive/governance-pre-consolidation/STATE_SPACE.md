# STATE_SPACE

**Status:** Phase 15 Deliverable 4.
**Location:** repo root.
**Phase:** 15.

> State before trajectory.
> — REACHABILITY_CONSTITUTION.md, Rule 2

---

## Purpose

This document defines the candidate state space for the
reachability engine. The state space is the canonical vocabulary
of state variables that mechanisms (per MECHANISM_REGISTRY_V2.md)
operate on. Every formula, every mechanism, every class must
declare which state variables it uses.

The frozen formula `score = max(dTRL/dt) × adjacency` uses only
ONE state variable (capability_state, expressed as TRL). The
boundary registry (BOUNDARY_REGISTRY.md) showed this is
insufficient — different process classes require different state
variables. This document catalogues the candidates.

This document is descriptive, not prescriptive. It does not
propose which state variables to use or how to combine them. It
defines the vocabulary. Per Rule 3 of REACHABILITY_CONSTITUTION.md,
mechanisms before formulas — the state variables follow the
mechanisms, not the other way around.

---

## Schema

```typescript
interface StateDimension {
    id: string;
    name: string;
    description: string;
    unit: string;
    measurementProtocol: string;
    transferableAcrossDomains: boolean;
    domainExamples: string[];
}
```

---

## The eight candidate dimensions

### SD-001: capability_state

| Field | Value |
|---|---|
| id | SD-001 |
| name | capability_state |
| description | The maturity of a capability, measured as TRL (1-9) or a refined per-generation / per-sub-capability variant. Includes "active vs legacy" flag for capabilities at TRL 9. |
| unit | TRL (1-9 integer) OR refined: (TRL, generation, sub-capability, active/legacy) tuple |
| measurementProtocol | Per TRAJECTORY_REGISTRY.md (Li-ion, semiconductor, telecom). Each capability's TRL is recorded at 5-year intervals. Refinement (per-generation TRL) is unimplemented but specified in STATE_VARIABLES.md. |
| transferableAcrossDomains | YES — TRL is a universal concept (every capability has a maturity level) |
| domainExamples | ["Li-ion: FAST_CHARGING TRL 1→9 over 1990-2015", "Semiconductors: HIGH_K_GATE_STACK TRL 1→9 over 1980-2010", "Telecom: WIRELESS_PROTOCOL TRL 3→9 over 1975-1985 (1G only)"] |

**Used by mechanisms:** MECH-E001, MECH-E002, MECH-R001, MECH-R002
**Used by frozen formula:** YES (as dTRL/dt — the velocity trajectory)

### SD-002: scientific_state

| Field | Value |
|---|---|
| id | SD-002 |
| name | scientific_state |
| description | The state of scientific understanding underlying a capability. Includes publication count, citation velocity, experimental replication status, and paradigm acceptance level. |
| unit | Composite: (publication_count, citation_velocity, replication_status, paradigm_acceptance) tuple. Ranges: publication_count [0, ∞), citation_velocity [0, ∞), replication_status {none, single, partial, broad}, paradigm_acceptance {fringe, contested, mainstream, consensus} |
| measurementProtocol | NOT IMPLEMENTED. Would require: (a) literature search per capability, (b) citation analysis, (c) replication tracking. Substantial data collection effort. |
| transferableAcrossDomains | YES — scientific understanding applies to all domains |
| domainExamples | ["1947 transistor effect: paradigm_acceptance=consensus by 1960", "1989 Hisamoto FINFET: paradigm_acceptance=fringe in 1989, mainstream by 2005", "1980 Goodenough LCO: paradigm_acceptance=contested in 1980, consensus by 1991"] |

**Used by mechanisms:** MECH-D001 (Discovery)
**Used by frozen formula:** NO

### SD-003: manufacturing_state

| Field | Value |
|---|---|
| id | SD-003 |
| name | manufacturing_state |
| description | The state of manufacturing capability: yield (defect density), throughput (units per time), process node, and process maturity. |
| unit | Composite: (yield_fraction, defect_density, throughput, process_node, process_maturity) tuple. yield_fraction [0, 1], defect_density [0, ∞) defects/cm², throughput [0, ∞) units/hour, process_node [length, e.g., 7nm], process_maturity {lab, pilot, production, mature, legacy} |
| measurementProtocol | PARTIALLY IMPLEMENTED. Li-ion has cost data (COST_TIMELINE in run_ablation.py). Semiconductors have process-node data (in TRAJECTORY_REGISTRY). Yield data is partially public (IEDM papers). Throughput data is largely proprietary. |
| transferableAcrossDomains | YES — manufacturing applies to all physical products |
| domainExamples | ["Li-ion: cost $3000/kWh (1995) → $100/kWh (2023), Wright's Law ~20% per doubling", "Semiconductors: defect density ~1/cm² at 10um (1971) → ~0.01/cm² at 5nm (2020)", "Telecom: cell tower deployment density (mature since 1990s)"] |

**Used by mechanisms:** MECH-S001, MECH-S002
**Used by frozen formula:** NO (the cost_bonus term was removed in Phase 12 ablation as redundant)

### SD-004: institutional_state

| Field | Value |
|---|---|
| id | SD-004 |
| name | institutional_state |
| description | The state of relevant institutions: standards body release phase, industry consortium maturity, dominant-firm commitment, supply chain consolidation. |
| unit | Composite: (standards_body_phase, consortium_maturity, dominant_firm_commitment, supply_chain_consolidation) tuple. standards_body_phase {none, concept, study_item, work_item, frozen, deprecated}, consortium_maturity {none, forming, active, mature, dissolved}, dominant_firm_commitment {none, exploratory, committed, leading, exiting}, supply_chain_consolidation {fragmented, consolidating, consolidated, monopoly} |
| measurementProtocol | NOT IMPLEMENTED. Would require: (a) standards-body release timeline tracking (partially public for 3GPP), (b) industry consortium membership tracking, (c) firm commitment inference from press releases / capex announcements, (d) supply chain analysis. |
| transferableAcrossDomains | PARTIAL — institutional structures differ across domains (3GPP for telecom, IEC for semiconductors, FDA for pharma, FAA for aviation). The CONCEPT transfers; the specific institutions do not. |
| domainExamples | ["Telecom: 3GPP Release 15 frozen June 2018 → 5G NR commercial 2019", "Pharma: FDA breakthrough designation → accelerated approval (Keytruda 2014)", "Aviation: Boeing 737 MAX certification basis (2012) → type certificate (2017) → grounding (2019)"] |

**Used by mechanisms:** MECH-C001 (standards-body consensus)
**Used by frozen formula:** NO

### SD-005: economic_state

| Field | Value |
|---|---|
| id | SD-005 |
| name | economic_state |
| description | The economic conditions affecting reachability: cost per unit, market size, willingness-to-pay, capital availability, subsidy structure. |
| unit | Composite: (cost_per_unit, market_size, willingness_to_pay, capital_availability, subsidy_fraction) tuple. cost_per_unit [domain-specific, e.g., $/kWh, $/transistor, $/patient-year], market_size [units/year], willingness_to_pay [$], capital_availability [$], subsidy_fraction [0, 1] |
| measurementProtocol | PARTIALLY IMPLEMENTED. Li-ion has cost_per_unit (COST_TIMELINE). Market size is partially available (industry reports). Willingness-to-pay and capital availability are harder to measure. |
| transferableAcrossDomains | YES — economics applies to all commercial inventions |
| domainExamples | ["Li-ion: cost $3000/kWh (1995) blocked mass-market EVs; cost $300/kWh (2010) enabled Leaf/Volt; cost $100/kWh (2023) enabled 4C fast charging", "Telecom: cell tower capex ~$200K per site; mass deployment requires $10B+ per operator", "Pharma: drug development cost $2.6B per approved drug (Tufts CSDD estimate)"] |

**Used by mechanisms:** MECH-S001 (yield improvement → cost decline)
**Used by frozen formula:** NO (cost_bonus removed in Phase 12 ablation)

### SD-006: regulatory_state

| Field | Value |
|---|---|
| id | SD-006 |
| name | regulatory_state |
| description | The state of regulatory approval: certification pathway, testing requirements, approval status, post-market surveillance. |
| unit | Composite: (pathway, testing_phase, approval_status, post_market_status) tuple. pathway {none, standard, accelerated, breakthrough, emergency, restricted}, testing_phase {preclinical, phase_1, phase_2, phase_3, submission, review, approved, withdrawn}, approval_status {none, pending, conditional, full, revoked}, post_market_status {none, monitored, restricted, withdrawn} |
| measurementProtocol | PARTIALLY IMPLEMENTED. Regulatory data is public (FDA, FAA, FCC, EMA filings). Quantifying as state is feasible but unimplemented. |
| transferableAcrossDomains | NO — regulatory structures differ across domains (FDA for pharma, FAA for aviation, FCC for telecom, IEC for semiconductors). The CONCEPT transfers; the specific pathways do not. |
| domainExamples | ["Pharma: Keytruda 2014 (FDA breakthrough designation → approval)", "Aviation: Boeing 737 MAX type certificate (2017) → grounding (2019) → recertification (2020)", "Telecom: FCC 5G spectrum auction (2019) enabled 5G mmWave deployment", "Li-ion: UN38.3 (2003) enabled transport certification; IEC 62133 (2012) enabled consumer certification"] |

**Used by mechanisms:** MECH-C002 (regulatory approval pathway)
**Used by frozen formula:** NO

### SD-007: coordination_state

| Field | Value |
|---|---|
| id | SD-007 |
| name | coordination_state |
| description | The state of multi-actor coordination: number of participating organizations, consensus progress, patent landscape consolidation, cross-licensing agreements. |
| unit | Composite: (participating_organizations, consensus_progress, patent_consolidation, cross_licensing_status) tuple. participating_organizations [integer], consensus_progress [0, 1], patent_consolidation {fragmented, consolidating, consolidated, single_dominant}, cross_licensing_status {none, partial, broad, universal} |
| measurementProtocol | NOT IMPLEMENTED. Would require: (a) standards-body membership tracking (partially public), (b) consensus progress inference from meeting minutes (labor-intensive), (c) patent landscape analysis (public but complex), (d) cross-licensing agreement tracking (partially public). |
| transferableAcrossDomains | PARTIAL — coordination structures differ across domains but the concept of "consensus progress" is universal. |
| domainExamples | ["Telecom: 3GPP has 700+ member organizations; consensus on Release 15 (5G) took ~3 years", "Semiconductors: EUV LLC (1997-2000) consolidated EUV research across Intel, Motorola, AMD, IBM; ASML acquired Cymer 2013", "Pharma: patent cliff dynamics — when key patents expire, generic manufacturers coordinate entry"] |

**Used by mechanisms:** MECH-C001 (standards-body consensus convergence)
**Used by frozen formula:** NO

### SD-008: infrastructure_state

| Field | Value |
|---|---|
| id | SD-008 |
| name | infrastructure_state |
| description | The state of deployment infrastructure: cell tower density, charging station density, fab capacity, clinical trial infrastructure, supply chain readiness. |
| unit | Composite: (deployment_density, capacity_utilization, geographic_coverage, age_distribution) tuple. deployment_density [domain-specific, e.g., towers/km², stations/country], capacity_utilization [0, 1], geographic_coverage [fraction of population covered], age_distribution [histogram of infrastructure age] |
| measurementProtocol | PARTIALLY IMPLEMENTED. Some infrastructure data is public (cell tower counts, charging station counts). Fab capacity is partially public (company reports). Clinical trial infrastructure is partially public (ClinicalTrials.gov). |
| transferableAcrossDomains | YES — infrastructure applies to all deployment-dependent inventions |
| domainExamples | ["Telecom: cell tower density — 5G mmWave requires small-cell density ~10x 4G", "Li-ion EV: charging station density — Tesla Supercharger network (2012) enabled long-distance EV travel", "Semiconductors: fab capacity — TSMC 5nm fab cost ~$20B; 3nm fab ~$25B", "Pharma: clinical trial infrastructure — Phase III trials require 1000+ patients across multiple sites"] |

**Used by mechanisms:** MECH-R001 (adjacent combination becomes reachable — infrastructure is a constraint)
**Used by frozen formula:** NO

---

## Cross-dimension analysis

### Which dimensions the frozen formula uses

Only SD-001 (capability_state, as dTRL/dt). The formula uses ONE
of EIGHT state dimensions. This is why the formula's boundary is
narrow — it cannot detect mechanisms that depend on the other
seven dimensions.

### Which dimensions each mechanism requires

| Mechanism | Required dimensions |
|---|---|
| MECH-D001 (scientific publication) | SD-002 (scientific_state) |
| MECH-E001 (rising capability) | SD-001 (capability_state), SD-002 (scientific_state), SD-003 (manufacturing_state) |
| MECH-E002 (acceleration) | SD-001 (capability_state), SD-002 (scientific_state) |
| MECH-S001 (yield/cost scaling) | SD-003 (manufacturing_state), SD-005 (economic_state) |
| MECH-S002 (process refinement) | SD-003 (manufacturing_state), SD-002 (scientific_state) |
| MECH-C001 (standards consensus) | SD-007 (coordination_state), SD-004 (institutional_state), SD-001 (capability_state) |
| MECH-C002 (regulatory approval) | SD-006 (regulatory_state), SD-001 (capability_state) |
| MECH-R001 (adjacent combination) | SD-001 (capability_state), SD-008 (infrastructure_state) |
| MECH-R002 (enabling capability) | SD-001 (capability_state) |

**Observation:** SD-001 (capability_state) appears in 7 of 9
mechanisms. It is the most-used state variable — which is why
the frozen formula (which uses only SD-001) detects some signal.
But it is not sufficient for 6 of 9 mechanisms, which require
additional dimensions.

### Transferability across domains

| Dimension | Transferable? | Why |
|---|---|---|
| SD-001 (capability_state) | YES | TRL is universal |
| SD-002 (scientific_state) | YES | Scientific understanding applies everywhere |
| SD-003 (manufacturing_state) | YES | Manufacturing applies to all physical products |
| SD-004 (institutional_state) | PARTIAL | Concept transfers; specific institutions differ |
| SD-005 (economic_state) | YES | Economics applies everywhere |
| SD-006 (regulatory_state) | NO | Regulatory pathways are domain-specific |
| SD-007 (coordination_state) | PARTIAL | Concept transfers; specific bodies differ |
| SD-008 (infrastructure_state) | YES | Infrastructure applies to all deployment |

5 of 8 dimensions are transferable across domains. 3 are
domain-specific (institutional, regulatory, coordination).
A formula using only transferable dimensions would address 6 of 9
mechanisms — missing MECH-C001 (standards consensus) and
MECH-C002 (regulatory approval).

---

## What this document does NOT do

- It does not propose formulas. Each dimension is a candidate, not a recommendation.
- It does not claim the eight dimensions are exhaustive. Others may exist (e.g., "talent_state" — availability of skilled engineers; "geopolitical_state" — wars, sanctions, trade agreements).
- It does not address how to combine dimensions. Multi-dimensional state combination is a formula-design question, post-Phase-15.
- It does not implement measurement protocols. Most dimensions are NOT IMPLEMENTED — building the measurement infrastructure is a substantial data-collection effort.

---

## Pre-stated falsifier (EP-4)

**Claim:** The eight dimensions (capability_state, scientific_state, manufacturing_state, institutional_state, economic_state, regulatory_state, coordination_state, infrastructure_state) cover the state space needed to detect all mechanisms in MECHANISM_REGISTRY_V2.md.

**Falsifier:** A mechanism that requires a state variable not in this list. Specifically: a reachability-changing process whose inputs cannot be expressed as values of any of the eight dimensions.

**Status:** PENDING. No such mechanism has been identified. But the mechanism registry is incomplete (8 mechanisms cataloged; more may exist). When a new mechanism is identified, its inputs will be checked against this list. If a new state variable is needed, a ninth dimension is added.
