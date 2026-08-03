# CROSS_DOMAIN_STRESS_TEST — Phase 13F

**Status:** THRESHOLD NOT PRE-REGISTERED. TREAT AS PROPOSAL.
**Location:** repo root.
**Phase:** 13F.

> Photovoltaics are encouraging.
> Now deliberately choose difficult domains.
> — CEO directive, Phase 13F

---

## Threshold pre-registration disclosure (added post-Phase-13, F-041, EP-6)

The decision rule in this document
("SURVIVES 2 of 4 → LOCAL with FUNDAMENTAL ASPIRATIONS") was
written in the same commit (`4879274`) as `PHASE_13_SYNTHESIS.md`,
which uses the threshold to classify the model's current status.

Per EP-6, a threshold written in the same commit as the document
evaluating against it is not pre-registration — it is a number
chosen with the answer already visible. The 2-of-4 threshold is
therefore reclassified from BINDING CRITERION to PROPOSAL.

**What would convert this to binding:** the threshold is
re-committed as a standalone artifact (its own commit, dated
before any Phase 14 stress test runs). The re-commit must
either keep 2-of-4 (with explicit justification for why 2 is
the right number) or adjust it (per the auditor's note: a
more honest threshold would be 3 of 4 for LOCAL and 4 of 4
for FUNDAMENTAL; 2 of 4 should be "M4 not yet transferred to
structurally different domains").

The 4 domain selections (aviation, semiconductors, telecom,
pharma) and the structural-violation rationale for each are
retained — those do not depend on the threshold. The candidate
events, capability lists, and falsification criteria for each
domain are retained as planning material.

The original content below is retained unchanged per
CONSTITUTION.md Law 7. Read the 2-of-4 threshold as a
proposal, not as a binding criterion.

---

## Purpose

The photovoltaic generalization (Phase 11F) confirmed M4
(transferability) for the Li-ion methodology. PV is a "sister
domain" — same physics-driven, cost-curve-dominated,
manufacturing-intensive structure as Li-ion. A model that
transfers from Li-ion to PV has demonstrated *horizontal*
transfer; it has not yet demonstrated *vertical* transfer
across structurally different innovation systems.

Phase 13F specifies the protocol for cross-domain stress testing
in four deliberately chosen difficult domains: aviation,
semiconductors, telecommunications, and pharmaceuticals. Each
domain is structurally different from Li-ion in a specific way
that stresses a different assumption of the model. If the model
survives all four, it has a claim to being *fundamental*; if it
fails in any, the failure mode identifies the boundary of its
applicability — which is itself an M5-grade result.

This document is a PLAN, not a result. The four stress tests will
be executed in subsequent phases (Phase 14A–14D, CEO-permitted).
The plan specifies the protocol, the data requirements, the
expected failure modes, and the falsification criteria.

---

## Domain selection rationale

### Why these four domains?

Each domain violates a different assumption of the Li-ion + PV
methodology:

| Domain | Structural difference from Li-ion | Assumption stressed |
|---|---|---|
| Aviation | Regulatory capture, multi-decade certification cycles, single-incident catastrophic failure | Velocity threshold (0.20 TRL/year too aggressive — aviation moves 0.05–0.10) |
| Semiconductors | Pure-play research-to-fab, multi-billion-dollar capital cycles, lithography-driven generational jumps | Adjacency metric (graph distance doesn't capture node-generation jumps) |
| Telecommunications | Standards-driven (3GPP), infrastructure-network effects, regulatory spectrum allocation | Bottleneck type (standards consensus is not physical or economic — it's coordination) |
| Pharmaceuticals | FDA clinical trial phases, patent cliff, biological mechanism uncertainty | Trajectory shape (TRL is not monotonically rising — clinical trial failures cause step drops) |

### What makes them "difficult"?

The PV test was encouraging because PV and Li-ion share:
1. Physical-physics bottlenecks (energy density vs cost).
2. Manufacturing-curve cost decline (Wright's Law).
3. Continuous TRL progression.
4. No catastrophic single-event failure mode.
5. Multi-year commercialization lag.

The four stress-test domains each break one of these:
1. Aviation: catastrophic single-event failure (Lion Air 737 MAX).
2. Semiconductors: discontinuous node jumps (28nm → 14nm → 7nm).
3. Telecommunications: standards-body coordination (3GPP).
4. Pharmaceuticals: clinical trial failure (phase III failure
   drops TRL from 7 to 1).

If the model survives all four, it has demonstrated that
velocity × adjacency is not specific to physical-physics-driven
manufacturing domains. If it fails in a specific way, the
failure mode identifies the boundary condition.

---

## Stress Test 1: Aviation

### Domain scope

Commercial aviation, 1970–2025. Capability set:
- AIRFRAME_DESIGN (aluminum → composite)
- PROPULSION (turbofan → geared turbofan → hybrid-electric)
- AVIONICS (analog → fly-by-wire → digital)
- MATERIALS (aluminum → carbon-fiber composite → titanium)
- MANUFACTURING (riveted → composite layup → 3D-printed)
- CERTIFICATION (FAR Part 25 → continued airworthiness)

### Why this is hard

1. **Multi-decade cycles.** A new airframe program takes 7–10
   years from concept to certification. The Li-ion 5-year
   horizon is too short; aviation requires 10-year horizons.
2. **Catastrophic failure as causal event.** The 737 MAX crashes
   (2018, 2019) were causative — they reset MCAS development,
   changed the certification regime, and slowed the entire
   narrowbody pipeline. The model has no concept of negative
   trajectory steps.
3. **Regulatory capture.** The FAA and EASA set de facto capability
   ceilings. A capability at TRL 9 in Europe may be at TRL 6 in
   the US due to certification lag. The model's TRL is currently
   geographically uniform.
4. **Single dominant customer.** Boeing and Airbus effectively
   define the market. Invention is *buyer-pulled* as much as
   *capability-pushed*.

### Expected failure modes

- The model will likely MISS events driven by regulatory change
  (e.g., ETOPS-240 certification enabling A330/A340 long-range
  operations) because regulatory capability is not in the
  ontology.
- The model will likely produce false positives for composites
  in the 1990s — composites had high trajectory velocity
  (B-2 bomber, 777 empennage) but did not produce a composite
  fuselage event until the 787 (2009), 15 years later. The lag
  structure is longer than Li-ion.
- The model will likely FAIL on the 737 MAX case — MCAS was a
  software addition with no capability trajectory. The event
  (crashes) was caused by software-system interaction, not by
  capability motion.

### Falsification criteria

The model FAILS Stress Test 1 if:
- Aviation precision is below 1.5% (half the Li-ion + PV mean).
- More than 2 of 5 expected events are missed (recall < 60%).
- Any TP requires a non-modeled factor (regulatory or software)
  that is not disclosed in `missingPreconditions`.

The model SURVIVES Stress Test 1 if:
- Aviation precision is above 1.5%.
- At least 3 of 5 expected events are caught.
- The lead time (Phase 13B protocol) is ≥ 5 years for STRONG
  classification events.

### Data requirements

- 20 aviation events (1970–2025), spanning airframe, propulsion,
  avionics, materials, and certification milestones.
- 8–10 capability trajectories, including the discontinuous
  composite-materials trajectory and the regulatory-capability
  trajectory (if modelable).
- Adjacency measurements for at least 10 key combinations
  (e.g., {AIRFRAME_DESIGN=composite, PROPULSION=turbofan} for
  the 787; {AVIONICS=digital, CERTIFICATION=Part 25} for the
  A320).

### Candidate events

| Year | Event | Combination |
|---|---|---|
| 1969 | Concorde enters service | [AIRFRAME=supersonic, PROPULSION=afterburning-turbojet] |
| 1970 | Boeing 747 enters service | [AIRFRAME=widebody, PROPULSION=high-bypass-turbofan, MANUFACTURING=riveted] |
| 1982 | Boeing 767 enters service (glass cockpit) | [AIRFRAME=widebody, AVIONICS=glass-cockpit] |
| 1988 | Airbus A320 enters service (fly-by-wire) | [AIRFRAME=narrowbody, AVIONICS=fly-by-wire] |
| 1995 | Boeing 777 enters service (composite empennage) | [AIRFRAME=widebody, MATERIALS=composite-empennage, PROPULSION=geared-turbofan-predecessor] |
| 2007 | Airbus A380 enters service | [AIRFRAME=very-large, AVIONICS=fly-by-wire-improved] |
| 2009 | Boeing 787 enters service (composite fuselage) | [AIRFRAME=widebody, MATERIALS=composite-fuselage] |
| 2016 | Airbus A350 enters service | [AIRFRAME=widebody, MATERIALS=composite-fuselage, PROPULSION=geared-turbofan] |
| 2017 | Bombardier C Series (Airbus A220) | [AIRFRAME=narrowbody, MATERIALS=composite, PROPULSION=geared-turbofan] |
| 2018, 2019 | 737 MAX crashes | [AVIONICS=MCAS, CERTIFICATION=Part-25-loophole] — NEGATIVE EVENT |

### Expected outcome

The model will likely SURVIVE on composite-fuselage events
(2009, 2016, 2017 — clear trajectory from B-2 1989 → 777 1995 →
787 2009) and FAIL on MCAS (2018–2019 — software-induced,
no trajectory). The mixed outcome is itself an M5-grade finding:
the model applies to *capability-driven* innovation and does NOT
apply to *system-integration* failures.

---

## Stress Test 2: Semiconductors

### Domain scope

Logic semiconductors, 1970–2025. Capability set:
- LITHOGRAPHY (g-line → i-line → DUV → ArF → EUV)
- TRANSISTOR_DESIGN (planar → FinFET → GAA)
- INTERCONNECT (aluminum → copper → low-k dielectric)
- MATERIALS (silicon → strained-silicon → SiGe → high-k)
- DESIGN_TOOLS (manual → schematic → HDL → EDA → AI-assisted)
- FAB_PROCESS (200mm → 300mm → 450mm-stalled)

### Why this is hard

1. **Discontinuous node jumps.** Lithography generations jump
   from 28nm to 14nm to 7nm — these are NOT smooth TRL
   progressions. The TRL framework may not apply at all; the
   relevant trajectory may be "node count" or "transistor
   density" — neither is in the current ontology.
2. **Multi-billion-dollar capital cycles.** A new fab costs
   $10B+; the build decision is made 3–5 years before production.
   The lead-time structure is dominated by capital allocation,
   not by capability trajectory.
3. **Global concentration.** TSMC, Samsung, Intel — three
   players. Invention is concentrated in their R&D roadmaps,
   not in a broad ecosystem.
4. **Patent thickets.** The patent landscape is so dense that
   adjacency may be measured by *patent distance*, not by
   *capability graph distance*.

### Expected failure modes

- The model will likely FAIL on EUV (entered production 2018–2019).
  EUV was a 20+ year trajectory (ASML started ~1999, Cymer
  acquisition 2012, first production 2018). The trajectory is
  real but the lead time is so long that the model's 5-year
  horizon cannot capture it.
- The model will likely produce false positives on FinFET
  derivatives — multiple FinFET variants exist (low-power,
  high-performance, FD-SOI competitor), and the model may flag
  all of them when only one or two realize.
- The model will likely MISS the Intel 10nm node struggle
  (delayed 2017 → 2019 → 2020). The capability trajectory was
  present but the *manufacturing yield* bottleneck (not modeled)
  delayed the event by 3 years.

### Falsification criteria

The model FAILS Stress Test 2 if:
- Semiconductor precision is below 1.5%.
- The model produces more than 3 false positives for any single
  TP (indicating inability to discriminate among high-adjacency
  variants).
- Any TP requires a non-modeled factor (yield, capital allocation,
  roadmap coordination) not disclosed.

The model SURVIVES Stress Test 2 if:
- Semiconductor precision is above 1.5%.
- The model correctly identifies EUV as a long-lead-time STRONG
  foresight case (per LEAD_TIME_PROTOCOL.md).
- The FinFET trajectory produces ≤ 2 false positives.

### Data requirements

- 20 semiconductor events (1970–2025), spanning lithography,
  transistor design, materials, and fab processes.
- 8–10 capability trajectories, including the discontinuous
  lithography-node trajectory.
- Adjacency measurements using a *patent-distance* metric in
  addition to the *capability-graph-distance* metric. If the
  two metrics diverge, this is evidence that the adjacency
  metric needs domain-specific calibration.

### Candidate events

| Year | Event | Combination |
|---|---|---|
| 1971 | Intel 4004 (first commercial microprocessor) | [LITHOGRAPHY=10um, TRANSISTOR=planar, FAB_PROCESS=50mm] |
| 1989 | Intel 80486 (first integrated FPU) | [LITHOGRAPHY=1um, TRANSISTOR=planar, DESIGN_TOOLS=HDL] |
| 1995 | 350nm node, 200mm wafers | [LITHOGRAPHY=DUV, FAB_PROCESS=200mm] |
| 1999 | Intel Pentium III (copper interconnect) | [INTERCONNECT=copper, LITHOGRAPHY=250nm] |
| 2001 | 130nm node, strained silicon | [MATERIALS=strained-silicon, LITHOGRAPHY=193nm-ArF] |
| 2007 | Intel 45nm (high-k metal gate) | [MATERIALS=high-k, TRANSISTOR=planar-final] |
| 2011 | Intel 22nm (FinFET) | [TRANSISTOR=FinFET] |
| 2012 | TSMC 28nm (HKMG planar) | [MATERIALS=high-k, LITHOGRAPHY=193nm-immersion] |
| 2018 | TSMC 7nm (EUV pre-production) | [LITHOGRAPHY=EUV, TRANSISTOR=FinFET-improved] |
| 2020 | TSMC 5nm (EUV in production) | [LITHOGRAPHY=EUV, TRANSISTOR=FinFET-final] |
| 2022 | Samsung 3nm (GAA) | [TRANSISTOR=GAA, LITHOGRAPHY=EUV-multiple-patterning] |
| 2017–2020 | Intel 10nm struggle | [TRANSISTOR=FinFET, FAB_PROCESS=yield-bottleneck — NOT MODELED] |

### Expected outcome

The model will likely SURVIVE on FinFET and GAA events
(clear capability trajectories) and STRUGGLE on the Intel 10nm
case (manufacturing yield bottleneck not in ontology). The
mixed outcome will likely identify *manufacturing yield* as
the missing fifth factor (after velocity, adjacency, bottleneck
removal, cost decline — see NECESSITY_SUFFICIENCY.md).

---

## Stress Test 3: Telecommunications

### Domain scope

Mobile telecommunications, 1980–2025. Capability set:
- WIRELESS_PROTOCOL (1G analog → 2G GSM → 3G UMTS → 4G LTE → 5G NR)
- SPECTRUM_ALLOCATION (sub-1GHz → 2.5GHz → mmWave)
- NETWORK_ARCHITECTURE (circuit-switched → packet-switched → SDN)
- DEVICE_INTEGRATION (phone → smartphone → IoT)
- STANDARDS_CONSENSUS (CCIR → 3GPP release cycles)
- INFRASTRUCTURE_DEPLOYMENT (cell towers → small cells → MIMO arrays)

### Why this is hard

1. **Standards-body coordination.** 3GPP releases set the
   trajectory; individual firms cannot invent ahead of the
   standard. The capability trajectory is *collective*, not
   *firm-level*.
2. **Network effects.** A protocol is useless without a device
   ecosystem and an infrastructure deployment. The capability
   must reach TRL 9 *simultaneously* in three places: protocol,
   device, infrastructure.
3. **Spectrum auctions.** Regulatory allocation of spectrum is
   the binding constraint. The model has no concept of
   regulatory-coordination bottlenecks.
4. **Multi-decade infrastructure cycles.** Cellular towers last
   20+ years; protocol generations are 10 years. The cycles are
   mismatched, creating lock-in effects.

### Expected failure modes

- The model will likely FAIL on 5G mmWave. The capability
  trajectory (3GPP Release 15, 2017) was clear, but the
  deployment has been slow (2020–2024) due to spectrum auctions
  and infrastructure cost. The model will over-predict 5G
  mmWave events.
- The model will likely produce false positives on IoT
  combinations — many combinations of {WIRELESS_PROTOCOL,
  DEVICE_INTEGRATION=IoT} score high on velocity and adjacency,
  but only a few realize commercially.
- The model will likely MISS the 3G → 4G transition event
  (LTE commercialization 2009–2010) because the trajectory
  was standards-driven, not capability-driven.

### Falsification criteria

The model FAILS Stress Test 3 if:
- Telecom precision is below 1.5%.
- The model cannot distinguish IoT combinations that realized
  (e.g., NB-IoT 2017) from those that did not (e.g., early
  WiMAX 2008 — failed standard).
- The 5G mmWave case produces more than 3 false positives.

The model SURVIVES Stress Test 3 if:
- Telecom precision is above 1.5%.
- The model correctly identifies LTE (2009) and NB-IoT (2017) as
  STRONG foresight cases.
- The 5G case identifies at least 1 TP with explicit disclosure
  of the spectrum-allocation missing-precondition.

### Data requirements

- 20 telecom events (1980–2025), spanning protocol releases,
  device launches, and infrastructure milestones.
- 6–8 capability trajectories, including the discontinuous
  protocol-generation trajectory (each generation is a step).
- Adjacency measurements using a *standards-distance* metric
  (how many 3GPP releases apart) in addition to capability
  graph distance.

### Candidate events

| Year | Event | Combination |
|---|---|---|
| 1983 | AMPS (1G) commercial | [WIRELESS_PROTOCOL=AMPS, SPECTRUM=sub-1GHz] |
| 1991 | GSM (2G) commercial | [WIRELESS_PROTOCOL=GSM, STANDARDS_CONSENSUS=ETSI] |
| 2001 | WCDMA (3G) commercial | [WIRELESS_PROTOCOL=WCDMA, SPECTRUM=2GHz] |
| 2009 | LTE (4G) commercial | [WIRELESS_PROTOCOL=LTE, NETWORK_ARCHITECTURE=packet-switched] |
| 2010 | iPhone 4 (first mainstream smartphone with LTE-ready hardware) | [DEVICE_INTEGRATION=smartphone, WIRELESS_PROTOCOL=LTE-precursor] |
| 2017 | NB-IoT standardized | [WIRELESS_PROTOCOL=NB-IoT, DEVICE_INTEGRATION=IoT] |
| 2019 | 5G NR sub-6GHz commercial | [WIRELESS_PROTOCOL=5G-NR, SPECTRUM=sub-6GHz] |
| 2022 | 5G mmWave limited deployment | [WIRELESS_PROTOCOL=5G-NR, SPECTRUM=mmWave, INFRASTRUCTURE_DEPLOYMENT=small-cell] |
| 2008 | WiMAX fails | [WIRELESS_PROTOCOL=WiMAX — FAILED STANDARD — NEGATIVE EVENT] |

### Expected outcome

The model will likely SURVIVE on LTE and NB-IoT (clear
capability trajectories + standards consensus) and STRUGGLE on
5G mmWave (infrastructure bottleneck not in ontology). The
WiMAX case is the most interesting — a *failed* standard with
high trajectory velocity but no event. This will likely expose
the standards-consensus missing factor.

---

## Stress Test 4: Pharmaceuticals

### Domain scope

Pharmaceutical drug development, 1980–2025. Capability set:
- DRUG_DISCOVERY (random screening → structure-based → HTS → AI-assisted)
- BIOASSAY (in-vivo → in-vitro → cell-based → organoid)
- CLINICAL_TRIAL_DESIGN (open-label → RCT → adaptive → basket)
- MANUFACTURING_PROCESS (chemical synthesis → biologic → cell-gene-therapy)
- REGULATORY_PATHWAY (FDA standard → accelerated → breakthrough → fast-track)
- DELIVERY_MECHANISM (oral → injectable → implantable → mRNA-LNP)

### Why this is hard

1. **Non-monotonic TRL.** Clinical trial failures cause TRL to
   *drop*, not just plateau. A drug at TRL 7 (Phase III ready)
   that fails Phase III drops to TRL 2 (back to preclinical).
   The model's velocity framework assumes monotonic rise.
2. **Biological mechanism uncertainty.** A drug can succeed in
   Phase II and fail in Phase III for reasons that are not
   capability-driven — they are *biological* (off-target effects,
   patient heterogeneity). The model has no concept of
   biological uncertainty.
3. **Patent cliff dynamics.** A drug's commercial trajectory is
   shaped by patent expiry (loss of exclusivity), not by
   capability trajectory. A "me-too" drug at TRL 9 in 2024 may
   have no commercial event because the patent landscape is
   exhausted.
4. **Long timelines.** 12–15 years from discovery to approval.
   The 5-year horizon is one-third of the development cycle.

### Expected failure modes

- The model will likely FAIL on mRNA vaccines (BioNTech/Pfizer
  COVID 2020). The mRNA trajectory was 30 years (Karikó 1990s →
  BioNTech 2008 → COVID 2020). The 5-year horizon cannot capture
  it. The COVID emergency authorization is also a regulatory
  anomaly, not a normal capability event.
- The model will likely produce many false positives in oncology
  — basket trials and adaptive designs have created many
  capability combinations that look promising but do not realize.
- The model will likely MISS the GLP-1 agonist event
  (semaglutide/Ozempic 2017–2023). The trajectory was driven by
  biological serendipity (incidental weight loss in trials) — not
  capability motion.

### Falsification criteria

The model FAILS Stress Test 4 if:
- Pharma precision is below 1.0% (lower threshold than other
  domains due to inherent difficulty).
- The model cannot handle TRL drops (clinical trial failures).
- The model misses the COVID mRNA vaccine event without
  disclosing the emergency-authorization missing-precondition.

The model SURVIVES Stress Test 4 if:
- Pharma precision is above 1.0%.
- The model correctly identifies at least 1 non-COVID TP (e.g.,
  Keytruda 2014 — PD-1 inhibitor).
- The mRNA case is correctly flagged as a step-change (per
  TIME_REVERSAL_PROTOCOL.md EV-1992 pattern).

### Data requirements

- 20 pharma events (1980–2025), spanning discovery, clinical
  development, and approval milestones.
- 8–10 capability trajectories, including the non-monotonic
  clinical-trial trajectory.
- Adjacency measurements using a *target-distance* metric
  (biological pathway distance) in addition to capability graph
  distance.

### Candidate events

| Year | Event | Combination |
|---|---|---|
| 1987 | First statin (lovastatin) approved | [DRUG_DISCOVERY=fungal-extract, BIOASSAY=in-vivo, DELIVERY=oral] |
| 1997 | Gleevec (imatinib) approved — paradigm-shifting targeted therapy | [DRUG_DISCOVERY=structure-based, BIOASSAY=cell-based] |
| 2006 | Gardasil (HPV vaccine) approved | [MANUFACTURING=biologic, BIOASSAY=cell-based, DELIVERY=injectable] |
| 2011 | Yervoy (ipilimumab, anti-CTLA4) approved — immuno-oncology begins | [DRUG_DISCOVERY=monoclonal-antibody, BIOASSAY=cell-based] |
| 2014 | Keytruda (pembrolizumab, anti-PD1) approved | [DRUG_DISCOVERY=monoclonal-antibody, REGULATORY_PATHWAY=breakthrough] |
| 2017 | Kymriah (tisagenlecleucel, CAR-T) approved — first cell therapy | [MANUFACTURING=cell-therapy, BIOASSAY=cell-based, REGULATORY_PATHWAY=breakthrough] |
| 2020 | Comirnaty (mRNA COVID vaccine) approved | [DRUG_DISCOVERY=mRNA, DELIVERY=LNP, REGULATORY_PATHWAY=emergency-use-authorization] |
| 2021 | Semaglutide (Ozempic) for weight loss approved | [DRUG_DISCOVERY=peptide-engineering, DELIVERY=injectable, BIOASSAY=serendipity — NOT MODELED] |
| 2023 | Leqembi (lecanemab, anti-amyloid) approved — Alzheimer's | [DRUG_DISCOVERY=monoclonal-antibody, BIOASSAY=biomarker-based] |
| 1999, 2006 | Vioxx withdrawn (2004), Avandia restricted (2010) | [REGULATORY_PATHWAY=post-marketing-surveillance — NEGATIVE EVENTS] |

### Expected outcome

The model will likely SURVIVE on targeted-therapy events
(Gleevec, Keytruda) — clear capability trajectories with
predictable timing. The model will likely FAIL on mRNA COVID
(emergency authorization anomaly) and on GLP-1 (biological
serendipity). The mixed outcome will likely expose
*biological uncertainty* as the missing fifth factor.

---

## Cross-stress-test synthesis

### The deep question

> Is the simplified theory fundamental or merely local?

The model has been validated in two domains (Li-ion, PV) that
share a structural signature: physical-physics bottlenecks,
continuous TRL progression, manufacturing-curve cost decline,
multi-year integration lag. The four stress tests deliberately
violate this signature:

| Stress test | Structural violation | If model survives | If model fails |
|---|---|---|---|
| Aviation | Catastrophic failure, certification cycles | Trajectory framework is robust to non-physical events | Model is local to non-catastrophic systems |
| Semiconductors | Discontinuous node jumps | Adjacency framework is robust to step changes | Model is local to continuous TRL systems |
| Telecommunications | Standards-body coordination | Bottleneck framework is robust to coordination problems | Model is local to firm-level capability systems |
| Pharmaceuticals | Non-monotonic TRL | Velocity framework is robust to failure-recovery | Model is local to monotonic progression systems |

### Decision rule

| Outcome | Verdict |
|---|---|
| Survives all 4 | Model is FUNDAMENTAL — applies across structurally diverse innovation systems. M5 candidate. |
| Survives 3 of 4 | Model is PARTIALLY FUNDAMENTAL — applies to a class of systems defined by the failure mode. M5 not yet. |
| Survives 2 of 4 | Model is LOCAL — applies to physical-manufacturing systems only. M4 confirmed, M5 not yet. |
| Survives ≤ 1 of 4 | Model is CURVE-FIT — Li-ion and PV results are coincidence. M3 and M4 falsified. |

### The honest expectation

Based on the structural analysis above, the most likely outcome is
**Survives 2 of 4** — the model survives Aviation and
Semiconductors (capability-driven, even if discontinuous) and
fails Telecommunications (standards-coordination bottleneck) and
Pharmaceuticals (non-monotonic TRL). This would place the model
at LOCAL — confirmed for physical-manufacturing systems, not
yet fundamental across all innovation systems.

This is not a failure — it is the *correct* honest result for a
Phase 13 model. The CEO's directive was to determine whether the
simplified theory is fundamental or merely local. A LOCAL verdict
with clearly identified boundary conditions is more honest than
a premature FUNDAMENTAL claim. The boundary conditions themselves
are an M5-grade result: they tell future researchers *when* the
trajectory × adjacency framework applies and *when* it does not.

---

## Execution plan

### Phase 14A: Aviation stress test

- Build aviation capability ontology (8 capabilities).
- Build aviation event registry (20 events).
- Build aviation trajectory registry (1990–2025).
- Run frozen Formula B (`velocity × adjacency`) on aviation backtest.
- Apply Phase 13 protocols: Mechanism Registry, Lead Time,
  Persistence, Necessity/Sufficiency, Time Reversal.
- Decision: SURVIVES or FAILS based on the criteria above.

### Phase 14B: Semiconductors stress test

- Build semiconductor capability ontology.
- Build semiconductor event registry.
- Build semiconductor trajectory registry (with discontinuous nodes).
- Run frozen Formula B with patent-distance adjacency metric.
- Apply Phase 13 protocols.
- Decision: SURVIVES or FAILS.

### Phase 14C: Telecommunications stress test

- Build telecom capability ontology (with standards-body coordination).
- Build telecom event registry.
- Build telecom trajectory registry (with step-wise protocol generations).
- Run frozen Formula B with standards-distance adjacency metric.
- Apply Phase 13 protocols.
- Decision: SURVIVES or FAILS.

### Phase 14D: Pharmaceuticals stress test

- Build pharma capability ontology (with non-monotonic TRL).
- Build pharma event registry.
- Build pharma trajectory registry (with TRL drops for clinical failures).
- Run frozen Formula B.
- Apply Phase 13 protocols.
- Decision: SURVIVES or FAILS.

### Phase 14E: Cross-stress-test synthesis

- Aggregate SURVIVES/FAILS counts.
- Apply decision rule above.
- Write FUNDAMENTAL_VS_LOCAL.md with the verdict.
- If LOCAL: identify the boundary conditions precisely.
- If FUNDAMENTAL: proceed to M5 claim.

### What this plan does NOT authorize

- Modifying Formula B. The frozen formula
  `score = max(dTRL/dt) × adjacency` is used unchanged in all
  four stress tests. If the model fails, the formula is wrong;
  if it succeeds, the formula is supported. Modifying the formula
  mid-stress-test is curve-fitting.
- Modifying the ontology mid-stress-test. Each domain's ontology
  is built before the backtest; once frozen for that domain, it
  cannot be modified. Ontology gaps are disclosed as
  `missingPreconditions`, not patched.
- Re-defining the SURVIVES/FAILS criteria after seeing results.
  The criteria are set in this document; they are not adjusted
  to match outcomes.

---

## Enforcement

- This plan is append-only (Constitution Law 7).
- Each stress test execution MUST produce a Phase 14X report
  following the structure of Phase 13 deliverables.
- The decision rule (2-of-4 threshold) is binding. Adjusting the
  threshold after seeing results is forbidden.
- The Phase 14X reports MUST disclose all `missingPreconditions`
  honestly. Hiding ontology gaps to inflate SURVIVES counts is
  the most likely failure mode of the stress tests — and it is
  the failure mode the CEO's directive most directly warns
  against ("the danger that you start believing the story you've
  constructed").
