# INVARIANT_REGISTRY

**Status:** Phase 14C protocol.
**Location:** repo root.
**Phase:** 14C.

> Each domain must answer four questions.
> — CEO directive, Phase 14C

---

## Purpose

Every domain has a different structure. The Li-ion domain is
physical-physics-driven with manufacturing-curve cost decline.
The semiconductor domain is lithography-node-driven with
discontinuous jumps. The telecom domain is standards-body-driven
with coordination bottlenecks. The pharmaceutical domain is
clinical-trial-driven with non-monotonic TRL.

The invariant registry forces each domain to articulate its
own answer to four structural questions. These answers are
committed BEFORE the backtest runs, so the domain's structure
is not retro-fitted to the results.

The four questions are:

1. **What accumulates?** — What capability or resource grows
   over time in this domain? (In Li-ion: TRL of rising
   capabilities. In semiconductors: transistor density. In
   pharma: clinical trial phase progression.)

2. **What accelerates?** — What changes the rate of accumulation?
   (In Li-ion: cost decline enables deployment scale. In
   semiconductors: lithography generation jumps. In pharma:
   FDA breakthrough designation.)

3. **What constrains?** — What is the binding bottleneck? (In
   Li-ion: thermal runaway, cost. In semiconductors: lithography
   resolution, yield. In pharma: clinical trial failure, biological
   uncertainty.)

4. **What becomes adjacent?** — What new combinations become
   reachable as capabilities accumulate? (In Li-ion: BMS + thermal
   management enables EV packs. In semiconductors: EUV + FinFET
   enables 7nm. In pharma: mAb + biomarker enables targeted therapy.)

---

## Schema

```typescript
interface DomainInvariant {
    domain: string;

    whatAccumulates: string;
    whatAccelerates: string;
    whatConstrains: string;
    whatBecomesAdjacent: string;

    // How the frozen formula maps to this domain
    velocityMapping: string;      // what dTRL/dt means here
    adjacencyMapping: string;     // what graph distance means here

    // Domain-specific structural violations
    structuralViolations: string[]; // how this domain breaks Li-ion assumptions
}
```

### Field semantics

| Field | Type | Required | Meaning |
|---|---|---|---|
| `domain` | string | yes | Domain identifier. |
| `whatAccumulates` | string | yes | The accumulating quantity. Must be specific (not "knowledge" — must be "TRL of FAST_CHARGING capability"). |
| `whatAccelerates` | string | yes | The accelerator. Must be specific (not "market demand" — must be "Wright's Law cost decline at 20% per doubling"). |
| `whatConstrains` | string | yes | The binding bottleneck. Must identify the ONE constraint that blocks invention (per BOTTLENECK_PROTOCOL.md). |
| `whatBecomesAdjacent` | string | yes | The adjacent-possibility expansion. Must name specific combinations that become reachable. |
| `velocityMapping` | string | yes | How `dTRL/dt` is operationalized in this domain. If TRL is not the right metric (e.g., semiconductors may use node generation), state what metric is used and why TRL is or isn't appropriate. |
| `adjacencyMapping` | string | yes | How graph distance is operationalized. If capability-graph distance is not the right metric (e.g., telecom may use standards-release distance), state what is used. |
| `structuralViolations` | string[] | yes | How this domain violates Li-ion's assumptions. Must list at least one violation (otherwise the domain is not a stress test). |

### What this schema forbids

- Vague answers. "Knowledge accumulates" is forbidden; "TRL of
  FAST_CHARGING accumulates from 1 to 9 over 1990-2015" is
  acceptable.
- No structural violations. If a domain has no violations of
  Li-ion's assumptions, it is not a stress test — it is a
  replication. Replications are useful but do not test the
  theory's boundaries.
- Retro-fitting the mappings after the backtest. The velocity
  and adjacency mappings are committed BEFORE the backtest runs.
  If they need to change, a new invariant record is committed
  (with a `_review` suffix) and the backtest is re-run.

---

## Domain invariant records

### Domain 1: Semiconductors

| Field | Value |
|---|---|
| domain | semiconductors |
| whatAccumulates | Transistor density (Moore's Law: 2x per node generation). Mapped to TRL per lithography generation: 10um (TRL 9 by 1971), 1um (TRL 9 by 1989), 130nm (TRL 9 by 2001), 7nm (TRL 9 by 2018). |
| whatAccelerates | Lithography generation transitions (g-line → i-line → DUV → ArF → EUV). Each transition takes 10-15 years from concept to production. EUV was conceived ~1999, entered production 2018. |
| whatConstrains | Lithography resolution (physical: wavelength of light). Secondary: manufacturing yield (economic: defect density per wafer). |
| whatBecomesAdjacent | New transistor architectures become reachable at each node: FinFET at 22nm (2011), GAA at 3nm (2022). New materials become reachable: high-k at 45nm (2007), SiGe at 90nm. |
| velocityMapping | `dTRL/dt` for the LITHOGRAPHY capability, not for individual transistor types. Lithography TRL rises in steps (concept → lab → pilot → production), not smoothly. The velocity is the rate of step progression. |
| adjacencyMapping | Graph distance from current node to prior node. 1 hop = one generation jump (e.g., 7nm is 1 hop from 10nm, 2 hops from 14nm). Patent distance may be used as a secondary metric. |
| structuralViolations | ["TRL is not monotonic — lithography generations are discrete steps, not continuous progression", "Yield bottleneck is economic (defect density), not physical — Li-ion's cost decline doesn't map directly", "Node jumps are discontinuous — 28nm to 14nm is a 2x jump, not a smooth trajectory", "Single dominant customer concentration (TSMC ~60% of foundry market) — invention is buyer-pulled, not capability-pushed"] |

### Domain 2: Telecommunications

| Field | Value |
|---|---|
| domain | telecommunications |
| whatAccumulates | Protocol generation maturity (1G → 2G → 3G → 4G → 5G → 6G). Each generation takes ~10 years from standardization to widespread deployment. |
| whatAccelerates | 3GPP release cycles (every 1-2 years). Spectrum auctions (regulatory events that unlock deployment). Device ecosystem readiness (smartphone penetration). |
| whatConstrains | Standards-body consensus (coordination bottleneck, not physical). Spectrum availability (regulatory). Infrastructure deployment cost (economic: cell tower density). |
| whatBecomesAdjacent | New use cases become reachable at each generation: mobile data (3G), broadband video (4G), IoT + low-latency (5G). Each generation enables 2-3 new combination classes. |
| velocityMapping | `dTRL/dt` for the WIRELESS_PROTOCOL capability, measured per 3GPP release. TRL rises in steps at each release freeze (Release 99 = 3G TRL 9, Release 8 = 4G TRL 9, Release 15 = 5G TRL 9). |
| adjacencyMapping | Standards-release distance (how many 3GPP releases apart). Secondary: spectrum-band distance (sub-1GHz vs 2.5GHz vs mmWave). |
| structuralViolations | ["Bottleneck is coordination (3GPP consensus), not physical or economic — Li-ion's bottleneck taxonomy doesn't have a coordination type", "TRL is discrete by generation, not continuous — 4G doesn't 'rise' to 5G, it's replaced", "Network effects: a protocol is useless without device + infrastructure — multi-capability simultaneity required", "Spectrum auctions are exogenous regulatory events, not capability trajectories"] |

### Domain 3: Aviation

| Field | Value |
|---|---|
| domain | aviation |
| whatAccumulates | Airframe material maturity (aluminum → composite → carbon-fiber composite). Propulsion efficiency (turbofan bypass ratio). Avionics capability (analog → fly-by-wire → digital). |
| whatAccelerates | Certification cycle (FAR Part 25 amendments, 7-10 year aircraft program cycles). Material science breakthroughs (carbon-fiber layup, titanium 3D printing). Fuel efficiency regulation (ICAO CORSIA). |
| whatConstrains | Certification (regulatory: FAR Part 25, EASA CS-25). Multi-decade program cycles (economic: new airframe program = $10B+ and 7-10 years). Catastrophic failure risk (Boeing 737 MAX crashes reset MCAS development). |
| whatBecomesAdjacent | Composite fuselage becomes reachable when MATERIALS + MANUFACTURING both mature (B-2 1989 → 777 empennage 1995 → 787 fuselage 2009). Fly-by-wire becomes reachable when AVIONICS + SOFTWARE both mature (A320 1988). |
| velocityMapping | `dTRL/dt` for AIRFRAME_DESIGN, PROPULSION, AVIONICS, MATERIALS capabilities. TRL rises over decades, not years. Velocity is typically 0.05-0.10 TRL/year (vs Li-ion's 0.20-0.50). |
| adjacencyMapping | Graph distance in the airframe-propulsion-avionics-materials capability graph. 1 hop = combining two capabilities (e.g., composite + airframe = 787). |
| structuralViolations | ["Velocity threshold 0.20 is too high — aviation moves at 0.05-0.10 TRL/year; the persistence protocol's threshold needs domain calibration", "Catastrophic failure (737 MAX) is a causative event that resets trajectories — Li-ion has no equivalent", "Certification is a multi-year regulatory gate, not a capability — the ontology may need a CERTIFICATION capability node", "Single-program economics (one airframe program = one firm's decade-long bet) — invention is buyer-concentrated"] |

### Domain 4: Pharmaceuticals

| Field | Value |
|---|---|
| domain | pharmaceuticals |
| whatAccumulates | Clinical trial phase progression (preclinical → Phase I → Phase II → Phase III → approval). Drug discovery methodology (random screening → structure-based → HTS → AI-assisted). |
| whatAccelerates | FDA pathways (standard → accelerated → breakthrough → fast-track). Biological mechanism understanding (e.g., PD-1/PD-L1 discovery enabled immuno-oncology). Combinatorial chemistry and HTS throughput. |
| whatConstrains | Clinical trial failure (Phase III failure rate ~30-50%). Biological uncertainty (off-target effects, patient heterogeneity). Patent cliff (loss of exclusivity drives me-too drug economics). |
| whatBecomesAdjacent | Targeted therapy becomes reachable when DRUG_DISCOVERY + BIOASSAY both mature (Gleevec 1997). Immuno-oncology becomes reachable when mAb + cell-biology both mature (Keytruda 2014). Cell therapy becomes reachable when manufacturing + bioassay both mature (Kymriah 2017). |
| velocityMapping | `dTRL/dt` for DRUG_DISCOVERY, BIOASSAY, CLINICAL_TRIAL_DESIGN, MANUFACTURING, DELIVERY capabilities. TRL is NON-MONOTONIC: a Phase III failure drops TRL from 7 to 2. The velocity formula must handle negative velocity. |
| adjacencyMapping | Graph distance in the drug-discovery-bioassay-clinical-manufacturing capability graph. Secondary: biological-pathway distance (how many receptor targets apart). |
| structuralViolations | ["TRL is non-monotonic — clinical trial failures cause TRL to DROP, not plateau. The velocity formula assumes monotonic rise.", "Biological uncertainty is not a capability — it's an irreducible unknown. The ontology has no node type for 'we don't know if this will work.'", "Patent cliff dynamics: a drug's commercial trajectory is shaped by patent expiry, not capability. A me-too drug at TRL 9 may have no commercial event because the patent landscape is exhausted.", "12-15 year development cycle — the 5-year backtest horizon is one-third of the cycle"] |

---

## Cross-domain analysis

The four domains collectively stress every assumption of the
Li-ion + PV methodology:

| Assumption | Li-ion | PV | Semiconductors | Telecom | Aviation | Pharma |
|---|---|---|---|---|---|---|
| TRL monotonic | ✓ | ✓ | partial (steps) | ✗ (discrete gens) | ✓ (slow) | ✗ (drops) |
| Physical bottleneck | ✓ | ✓ | ✓ | ✗ (coordination) | partial (cert) | ✗ (biological) |
| Continuous cost decline | ✓ | ✓ | ✓ | ✗ (step) | partial | ✗ (patent cliff) |
| 5-year horizon sufficient | ✓ | ✓ | partial | partial | ✗ (10yr) | ✗ (15yr) |
| Firm-level agency | ✓ | ✓ | ✓ | ✗ (standards) | ✗ (programs) | ✓ |

If the theory survives in domains that violate these assumptions,
the theory is more fundamental than Li-ion suggested. If it fails
only in the violating domains, the theory is local to
physical-manufacturing systems with continuous TRL progression.

---

## Enforcement

- Each domain's invariant record is committed BEFORE its backtest
  runs. The record cannot be amended after the backtest (Law 7).
  If the backtest reveals the record was wrong, a `_review`
  version is committed and the backtest is re-run.
- The `structuralViolations` field must list at least one
  violation per domain. A domain with no violations is a
  replication, not a stress test.
- The `velocityMapping` and `adjacencyMapping` fields must be
  specific enough that an independent reviewer can reproduce
  the mapping from the domain's trajectory registry.
