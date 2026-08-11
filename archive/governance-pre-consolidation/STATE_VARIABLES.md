# STATE_VARIABLES

**Status:** Phase 14S taxonomy.
**Location:** repo root.
**Phase:** 14S.

> TRL itself may be the wrong state variable.
> — CEO directive, Phase 14S

---

## Purpose

This document catalogues candidate state variables for invention
prediction. The frozen formula uses ONE state variable (TRL per
capability). The boundary registry (BOUNDARY_REGISTRY.md) shows
this is insufficient — different invention classes (per
INVENTION_CLASSES.md) require different state variables.

This document is descriptive. It lists candidates without
proposing which to use or how to combine them. The frozen
formula is unchanged (Rule 1).

---

## The current state variable: TRL

**Definition:** Technology Readiness Level — a 1-9 scale measuring
how mature a capability is, from concept (TRL 1) to commercial
deployment (TRL 9).

**Used by the frozen formula:** Yes. `max(dTRL/dt)` is the velocity
term.

**What TRL captures:**
- The maturity of a capability (1 = concept, 9 = commercial)
- The rate of maturation (dTRL/dt)

**What TRL does NOT capture (per BOUNDARY_REGISTRY.md):**
- Which generation a capability is serving (1G vs 5G — Pattern 2)
- Whether a capability is "active frontier" or "legacy" (both at TRL 9)
- The coordination state of standards bodies (3GPP release phase)
- The cost state (cost per kWh, cost per transistor)
- The institutional state (spectrum auction timing, FDA pathway)
- The infrastructure state (cell tower density, fab capacity)
- The regulatory state (UN38.3, FAR Part 25, IEC 62133)

**Failure modes traceable to TRL (from BOUNDARY_REGISTRY.md):**
- Pattern 2 (7 cases): TRL cannot represent "re-rise" — the same
  capability rising for a new generation.
- Pattern 4 (2 cases): TRL 9 does not distinguish "just matured"
  from "mature for 10 years."
- Pattern 3 (5 cases): TRL granularity (5-year snapshots) produces
  velocity exactly at the threshold.

**Verdict:** TRL is necessary but not sufficient. It captures
capability maturity but not the other states that affect invention.

---

## Candidate state variables

### 1. Capability state (refined TRL)

**What it captures:** Capability maturity, with refinements:
- Per-generation TRL (WIRELESS_PROTOCOL_1G, _2G, _3G, _4G, _5G as
  separate capabilities, each with its own TRL trajectory)
- Sub-capability TRL (NON_PLANAR_TRANSISTOR_FINFET vs _GAA as
  sub-capabilities)
- "Active vs legacy" flag (TRL 9 + active = frontier; TRL 9 +
  legacy = superseded)

**Addresses which boundary patterns:**
- Pattern 2 (generation transitions): YES — per-generation TRL
  would represent 2G, 3G, 4G, 5G as separate rising trajectories.
- Pattern 4 (post-maturity): PARTIAL — "active vs legacy" flag
  would distinguish just-matured from mature-for-10-years, but
  does not capture the optimization metric.
- Pattern 3 (threshold granularity): NO — granularity is a
  measurement issue, not a state-variable issue.

**Cost:** Increases ontology complexity. Telecom would go from 8
capabilities to ~25 (5 generations × 5 rising capabilities).
Semiconductors would go from 8 to ~15 (sub-capabilities for
NON_PLANAR_TRANSISTOR, EUV_LITHOGRAPHY).

**Risk:** Per EP-6 / COMPRESSION_TEST, complexity must be
justified by explanatory power. Per-generation TRL would explain
Pattern 2 but at the cost of 3x more capabilities. The trade-off
is not obviously favorable.

### 2. Cost state

**What it captures:** The cost of the capability or its output,
in domain-specific units:
- Li-ion: $/kWh
- Semiconductors: $/transistor or $/mm² of silicon
- Telecom: $/subscriber or $/base station
- Aviation: $/seat-mile
- Pharmaceuticals: $/patient-year

**Addresses which boundary patterns:**
- Pattern 1 (scaling events): PARTIAL — scaling events are often
  cost-driven (more transistors per chip = lower cost per
  transistor). A cost-state term might detect scaling.
- Pattern 4 (post-maturity): YES — post-maturity exploitation
  is often cost-driven (3D V-Cache, GAA refinement). Cost state
  would capture this.
- Pattern 2 (generation transitions): NO — generation transitions
  are not primarily cost-driven.

**Cost:** Requires cost trajectory data for every capability. The
Li-ion domain has this (COST_TIMELINE in run_ablation.py). The
semiconductor and telecom domains do not — it would require
substantial data collection.

**Risk:** The ablation (Task 37) showed cost_bonus added ZERO
independent signal on Li-ion. Cost is correlated with velocity
(capability progress drives cost down). Adding cost state may
repeat the cost_bonus mistake.

### 3. Institutional state

**What it captures:** The state of relevant institutions:
- Standards body release phase (3GPP: concept → study item →
  work item → freeze → commercial)
- Regulatory pathway (FDA: preclinical → IND → Phase I/II/III →
  NDA → approval; FAA: concept → certification basis →
  compliance → type certificate)
- Industry consortium maturity (EUV LLC, GSM Association, etc.)

**Addresses which boundary patterns:**
- Pattern 2 (generation transitions): YES — standards-body
  release phase would directly detect 2G/3G/4G/5G transitions.
  This is the coordination-state variable H3 identifies.
- Pattern 1 (scaling): NO — scaling is not institutional.
- Pattern 4 (post-maturity): NO — post-maturity exploitation is
  not institutional.

**Cost:** Requires standards-body release timeline data. For
telecom, this is available (3GPP release dates are public).
For pharmaceuticals, FDA pathway data is available. For
semiconductors, IEEE/IEC standards are available but less
centrally tracked.

**Risk:** Institutional state is domain-specific. A telecom
standards phase does not translate to aviation certification.
This means the formula cannot use a single institutional-state
term across domains — it would need domain-specific
institutional state, breaking transferability.

### 4. Manufacturing state

**What it captures:** The state of manufacturing capability:
- Yield (defect density per wafer, cells per pack passing QA)
- Throughput (wafers per hour, cells per minute)
- Process node (lithography generation in production)

**Addresses which boundary patterns:**
- Pattern 1 (scaling): YES — scaling events are often
  manufacturing-driven (yield improvement, throughput increase).
- Pattern 4 (post-maturity): YES — post-maturity exploitation is
  often manufacturing-process refinement.
- Pattern 2 (generation transitions): NO — generation transitions
  are not primarily manufacturing-driven.

**Cost:** Requires manufacturing trajectory data. Semiconductor
yield data is partially public (IEDM papers, company reports).
Li-ion manufacturing data is less public.

**Risk:** Manufacturing state may be too correlated with TRL
(manufacturing maturity often tracks capability maturity). If
correlated, it adds no independent signal — same failure mode
as cost_bonus.

### 5. Infrastructure state

**What it captures:** The state of deployment infrastructure:
- Cell tower density (telecom)
- Charging station density (Li-ion EVs)
- Fab capacity (semiconductors)
- Clinical trial infrastructure (pharmaceuticals)

**Addresses which boundary patterns:**
- Pattern 1 (scaling): PARTIAL — some scaling events are
  infrastructure-driven (mass-market smartphone adoption required
  4G infrastructure density).
- Pattern 2 (generation transitions): PARTIAL — generation
  transitions often require new infrastructure (5G requires
  small-cell density).

**Cost:** Requires infrastructure deployment data. Some is
available (cell tower counts, charging station counts). Much is
proprietary.

**Risk:** Infrastructure state lags capability state —
infrastructure is built AFTER the capability is proven. Using
infrastructure as a state variable may produce lagging signals
rather than predictive ones.

### 6. Coordination state

**What it captures:** Specifically, the state of multi-actor
coordination:
- Number of organizations participating in a standards body
- Consensus progress (e.g., 3GPP release freeze date)
- Patent landscape consolidation (cross-licensing agreements signed)

**Addresses which boundary patterns:**
- Pattern 2 (generation transitions): YES — coordination state
  directly detects standards-body convergence.
- Pattern 1 (scaling): NO.
- Pattern 4 (post-maturity): NO.

**Cost:** Coordination data is partially available (3GPP
membership, patent filings). Consensus progress is harder to
quantify.

**Risk:** Coordination state is domain-specific (3GPP for telecom,
FDA for pharma, ICAO for aviation). Same transferability risk as
institutional state.

### 7. Regulatory state

**What it captures:** The state of regulatory approval:
- For pharma: IND → Phase I → II → III → NDA → approval
- For aviation: concept → certification basis → compliance →
  type certificate
- For telecom: spectrum auction timing, deployment authorization
- For Li-ion: UN38.3, IEC 62133 compliance status

**Addresses which boundary patterns:**
- Pattern 2 (generation transitions): PARTIAL — some generation
  transitions are gated by regulatory approval (5G SA requires
  regulatory authorization for cloud-native core).
- Pattern 1 (scaling): NO.

**Cost:** Regulatory data is public (FDA, FAA, FCC filings).
Quantifying regulatory state is feasible.

**Risk:** Regulatory state is domain-specific. Same transferability
risk.

---

## Cross-state-variable analysis

| State variable | Addresses Pattern 1 | Pattern 2 | Pattern 3 | Pattern 4 | Pattern 5 | Transferable across domains? |
|---|---|---|---|---|---|---|
| TRL (current) | NO | NO | NO | NO | NO | YES |
| Capability state (refined) | NO | YES | NO | PARTIAL | NO | YES |
| Cost state | PARTIAL | NO | NO | YES | NO | YES (units differ) |
| Institutional state | NO | YES | NO | NO | NO | NO (domain-specific) |
| Manufacturing state | YES | NO | NO | YES | NO | PARTIAL |
| Infrastructure state | PARTIAL | PARTIAL | NO | NO | NO | PARTIAL |
| Coordination state | NO | YES | NO | NO | NO | NO (domain-specific) |
| Regulatory state | NO | PARTIAL | NO | NO | NO | NO (domain-specific) |

**Key observation:** No single state variable addresses all five
patterns. The frozen formula uses TRL, which addresses NONE of the
robust-falsification patterns (1, 2, 4). This is why the formula
fails on those patterns.

**Transferability varies:** TRL, capability state, cost state, and
manufacturing state are transferable across domains (different
units, same concept). Institutional, coordination, and regulatory
state are domain-specific. A formula using only transferable
state variables would address Patterns 1, 2 (partially), and 4 —
but not the domain-specific patterns.

---

## What this catalog does NOT do

- It does not propose a new formula. Each state variable is a
  candidate, not a recommendation.
- It does not claim the seven state variables are exhaustive.
  Others may exist (e.g., "talent state" — availability of skilled
  engineers; "supply chain state" — raw material availability).
- It does not address whether multiple state variables should be
  combined (e.g., TRL × cost × coordination). That is a
  formula-design question, post-Phase-14.
- It does not address H2 (velocity vs acceleration). Acceleration
  is a derivative of TRL, not a separate state variable.

---

## Pre-stated falsifier (EP-4)

**Claim:** The seven state variables (TRL, capability state, cost
state, institutional state, manufacturing state, infrastructure
state, coordination state, regulatory state) cover the state
space needed to predict all five invention classes.

**Falsifier:** An event that cannot be predicted by any combination
of these seven state variables. Such an event would have:
- No capability trajectory (not TRL or capability state)
- No cost trajectory (not cost state)
- No institutional/coordination/regulatory precursor (not those states)
- No manufacturing/infrastructure precursor (not those states)

If such an event is found, an eighth state variable is needed.
(Candidate: "geopolitical state" — events triggered by wars,
sanctions, or trade agreements that none of the seven states
capture.)

This falsifier is PENDING.
