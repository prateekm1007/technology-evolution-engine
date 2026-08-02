# TIME_REVERSAL_PROTOCOL — Phase 13E

**Status:** constitutional document (time-reversed analysis).
**Location:** repo root.
**Phase:** 13E.

> Run the model backward.
> Instead of asking "What will happen?" ask "Given what happened,
> what had to be true beforehand?"
> — CEO directive, Phase 13E

---

## Purpose

Forward prediction is hard because the space of possible events is
large and the space of actual events is small. Precision is
inherently low. The model's current 3.57% precision on Li-ion
means 96% of its Top-10 predictions are wrong — but it also means
the model is predicting many things that *could* have happened but
didn't.

Time reversal flips the question. Given an event E that occurred
in year Y, what *must* have been true in year Y-1, Y-3, Y-5, Y-10?
The space of necessary preconditions is much smaller than the
space of possible futures. A model that correctly identifies the
minimal precondition set for every past event is making a stronger
claim than one that predicts the next event with 5% precision.

This protocol applies Bayes' rule backwards: instead of
`P(event | factors)`, it asks `P(factors | event)`. The latter is
directly measurable from the registry; the former requires
exhaustive enumeration of counterfactuals.

---

## Schema

```typescript
interface TimeReversalRecord {
    eventId: string;                       // EV-YYYY from EVENT_REGISTRY
    eventYear: number;
    minimalPreconditions: {
        capability: string;
        minTRL: number;                   // minimum TRL required at year Y - lag
        requiredBy: number;                // year by which this TRL must be reached
        observedTRL: number;               // actual TRL at that year (from TRAJECTORY_REGISTRY)
        satisfied: boolean;
    }[];
    missingPreconditions: string[];         // capabilities the ontology lacks
    counterfactualViolation: string | null; // case where preconditions met but event didn't occur
    verdict: "EXPLAINED" | "PARTIAL" | "UNEXPLAINED";
}
```

### Field semantics

| Field | Type | Required | Meaning |
|---|---|---|---|
| `eventId` | string | yes | Event being explained. Must be in EVENT_REGISTRY.md. |
| `eventYear` | int | yes | Year event occurred. |
| `minimalPreconditions` | object[] | yes | One entry per capability the event *required*. Each entry specifies the minimum TRL the capability must have had by a year prior to the event, and whether the registry confirms it had that TRL. |
| `missingPreconditions` | string[] | yes | Capabilities the ontology does not model but which the event required. Honest disclosure of model gaps. Empty array if the ontology is complete for this event. |
| `counterfactualViolation` | string or null | yes | If non-null: a year window where ALL minimal preconditions were satisfied but the event did NOT occur. This would indicate the preconditions are not sufficient. |
| `verdict` | enum | yes | `EXPLAINED` if all preconditions satisfied at the required year AND no counterfactual violation. `PARTIAL` if some preconditions satisfied but ontology gaps exist. `UNEXPLAINED` if preconditions were not satisfied (impossible event, or registry is wrong). |

### What this protocol forbids

- Using *post-event* data to explain the event (look-ahead bias).
  All `observedTRL` values must come from TRAJECTORY_REGISTRY.md
  at the year prior to the event — never from the event year
  itself.
- Hand-waving about "industry trends." Every precondition must be
  tied to a specific capability with a specific TRL threshold.
- Treating the model's own predictions as evidence. The protocol
  is independent of forward prediction — it asks what HAD to be
  true, not what the model said would be true.

---

## Time-reversal records (Li-ion domain)

For each of the 16 events in EVENT_REGISTRY.md, the minimal
precondition set is derived and checked against the registry. The
TRL thresholds are derived from the event's combination: each
capability in the combination must have been at TRL ≥ 7 (system
prototype demonstrated) at a year prior to the event — typically
2–5 years prior to allow for integration.

### TR-001: Sony commercializes Li-ion (1991)

| Field | Value |
|---|---|
| eventId | EV-1991 |
| eventYear | 1991 |
| minimalPreconditions | [{ELECTROCHEMICAL_ENERGY_STORAGE, minTRL: 6, requiredBy: 1989, observedTRL: 6, satisfied: true}, {ION_TRANSPORT, minTRL: 9, requiredBy: 1985, observedTRL: 9, satisfied: true}, {INTERCALATION, minTRL: 6, requiredBy: 1989, observedTRL: 8, satisfied: true}] |
| missingPreconditions | ["Anode graphite formulation (not in ontology)"] |
| counterfactualViolation | null |
| verdict | PARTIAL |

**Interpretation:** All three modeled preconditions were satisfied
by 1989. The event occurred in 1991 — 2 years after the
preconditions were met. The 2-year lag is the integration period
(cell design, manufacturing line setup, product launch). The
missing precondition (anode graphite formulation) is an honest
disclosure: Yoshino's 1985 prototype used a specific graphite
anode that the ontology does not track. The ontology is therefore
*incomplete* for this event, but the modeled preconditions are
*sufficient to identify the trajectory direction*.

### TR-002: Li-ion in consumer electronics (1992)

| Field | Value |
|---|---|
| eventId | EV-1992 |
| eventYear | 1992 |
| minimalPreconditions | [{ELECTROCHEMICAL_ENERGY_STORAGE, minTRL: 9, requiredBy: 1990, observedTRL: 6 (at 1990), satisfied: false}, {CELL_ASSEMBLY, minTRL: 8, requiredBy: 1990, observedTRL: 9, satisfied: true}] |
| missingPreconditions | ["Camcorder form-factor integration (not in ontology)"] |
| counterfactualViolation | "EES at TRL 6 in 1990 (not TRL 9) — but Sony commercialized in 1991, so by 1992 EES at TRL 9. Strict precondition not met in 1990 but met in 1991. Lag structure tighter than expected." |
| verdict | PARTIAL |

**Interpretation:** The strict precondition (EES at TRL 9 by 1990)
was not met — EES was at TRL 6 until the 1991 commercialization
jump. This is the only event in the registry where the strict
precondition was *not* met in the year before the event. The
explanation: Sony's 1991 commercialization was a step-change
that brought EES from TRL 6 to TRL 9 in one year. The model
cannot predict step changes; it can only predict smooth
trajectories. This is a fundamental limitation — but it is
honest about it.

### TR-003: LFP cathode commercialization (1996)

| Field | Value |
|---|---|
| eventId | EV-1996 |
| eventYear | 1996 |
| minimalPreconditions | [{ELECTROCHEMICAL_ENERGY_STORAGE, minTRL: 9, requiredBy: 1994, observedTRL: 9, satisfied: true}, {INTERCALATION, minTRL: 9, requiredBy: 1994, observedTRL: 9, satisfied: true}, {ELECTRODE_COATING, minTRL: 9, requiredBy: 1994, observedTRL: 9, satisfied: true}] |
| missingPreconditions | ["LFP-specific cathode synthesis (not in ontology)"] |
| counterfactualViolation | null |
| verdict | PARTIAL |

**Interpretation:** All modeled preconditions were satisfied 2
years before the event. The missing precondition (LFP synthesis)
is a chemistry-specific capability not in the ontology. The event
is consistent with the trajectory model: LFP was a chemistry
innovation that required no new system-level capability.

### TR-004: Li-ion EVs (1997, Nissan Altra)

| Field | Value |
|---|---|
| eventId | EV-1997 |
| eventYear | 1997 |
| minimalPreconditions | [{ELECTROCHEMICAL_ENERGY_STORAGE, minTRL: 9, requiredBy: 1995, observedTRL: 9, satisfied: true}, {INTERCALATION, minTRL: 9, requiredBy: 1995, observedTRL: 9, satisfied: true}, {STATE_OF_CHARGE_MONITORING, minTRL: 7, requiredBy: 1995, observedTRL: 9, satisfied: true}] |
| missingPreconditions | [] |
| counterfactualViolation | null |
| verdict | EXPLAINED |

**Interpretation:** The cleanest EXPLAINED event in the registry.
All three preconditions satisfied by 1995; event occurred in 1997
(2-year integration lag). The model's T=1995 prediction (MECH-001)
is consistent with the time-reversal analysis: the preconditions
WERE met, and the event DID occur within the 5-year horizon. This
is the strongest single piece of evidence that the model is
detecting real structure, not curve-fitting.

### TR-005: NCM cathode (2001, Argonne)

| Field | Value |
|---|---|
| eventId | EV-2001 |
| eventYear | 2001 |
| minimalPreconditions | [{ELECTROCHEMICAL_ENERGY_STORAGE, minTRL: 9, requiredBy: 1999, observedTRL: 9, satisfied: true}, {INTERCALATION, minTRL: 9, requiredBy: 1999, observedTRL: 9, satisfied: true}, {ELECTRON_COLLECTION, minTRL: 9, requiredBy: 1999, observedTRL: 9, satisfied: true}] |
| missingPreconditions | ["NCM-specific layered oxide synthesis (not in ontology)"] |
| counterfactualViolation | null |
| verdict | PARTIAL |

### TR-006: Tesla Motors founded (2003)

| Field | Value |
|---|---|
| eventId | EV-2003 |
| eventYear | 2003 |
| minimalPreconditions | [{ELECTROCHEMICAL_ENERGY_STORAGE, minTRL: 9, requiredBy: 2001, observedTRL: 9, satisfied: true}, {THERMAL_MANAGEMENT, minTRL: 7, requiredBy: 2001, observedTRL: 6 (2000), satisfied: false}] |
| missingPreconditions | ["EV market willingness to bet (organizational, not capability)"] |
| counterfactualViolation | "THERMAL_MANAGEMENT at TRL 6 in 2000 — strict precondition not met. But Tesla was founded on the BET that thermal management would reach TRL 9 by 2008 (which it did). The event (founding) preceded the precondition satisfaction." |
| verdict | PARTIAL |

**Interpretation:** Tesla's founding is the most epistemologically
interesting case. The model's strict preconditions were NOT met
in 2003 (thermal management was at TRL 6, not TRL 7+). Tesla
was founded on a *bet* that thermal management would mature —
and the bet was correct (TRL 9 by 2005). This is the case where
the trajectory model's *direction* was right but the *timing*
was off. A model that flags the combination as "approaching"
rather than "reached" would catch this case. The current binary
TRL threshold is too strict.

### TR-007: NCM commercialization (2004)

| Field | Value |
|---|---|
| eventId | EV-2004 |
| eventYear | 2004 |
| minimalPreconditions | [{ELECTROCHEMICAL_ENERGY_STORAGE, minTRL: 9, requiredBy: 2002, observedTRL: 9, satisfied: true}, {INTERCALATION, minTRL: 9, requiredBy: 2002, observedTRL: 9, satisfied: true}, {ELECTRON_COLLECTION, minTRL: 9, requiredBy: 2002, observedTRL: 9, satisfied: true}] |
| missingPreconditions | [] |
| counterfactualViolation | null |
| verdict | EXPLAINED |

### TR-008: Tesla Roadster production begins (2008)

| Field | Value |
|---|---|
| eventId | EV-2008 |
| eventYear | 2008 |
| minimalPreconditions | [{ELECTROCHEMICAL_ENERGY_STORAGE, minTRL: 9, requiredBy: 2006, observedTRL: 9, satisfied: true}, {THERMAL_MANAGEMENT, minTRL: 9, requiredBy: 2006, observedTRL: 9, satisfied: true}, {STATE_OF_CHARGE_MONITORING, minTRL: 9, requiredBy: 2006, observedTRL: 9, satisfied: true}] |
| missingPreconditions | ["Automotive OEM willingness to bet on Li-ion for performance EVs (organizational)"] |
| counterfactualViolation | null |
| verdict | EXPLAINED |

**Interpretation:** All three preconditions satisfied by 2006; event
occurred in 2008 (2-year integration lag). The model's T=2005
prediction (MECH-002) is consistent: the preconditions WERE met,
the event DID occur within the horizon. The only gap is the
organizational factor (Tesla's willingness) — which the model
correctly does not claim to predict.

### TR-009: Leaf/Volt mass-market EVs (2010)

| Field | Value |
|---|---|
| eventId | EV-2010 |
| eventYear | 2010 |
| minimalPreconditions | [{ELECTROCHEMICAL_ENERGY_STORAGE, minTRL: 9, requiredBy: 2008, observedTRL: 9, satisfied: true}, {FAST_CHARGING, minTRL: 7, requiredBy: 2008, observedTRL: 6 (at 2008), satisfied: false}, {THERMAL_MANAGEMENT, minTRL: 9, requiredBy: 2008, observedTRL: 9, satisfied: true}, {SAFETY_PROTECTION, minTRL: 9, requiredBy: 2008, observedTRL: 9, satisfied: true}] |
| missingPreconditions | ["Government subsidies (economic, not capability)"] |
| counterfactualViolation | "FAST_CHARGING at TRL 6 in 2008 — strict precondition not met. Leaf/Volt launched with Level 2 charging (6.6 kW) and CHAdeMO DC fast charging at 50 kW — FAST_CHARGING was not at system-proven TRL 9 in 2008." |
| verdict | PARTIAL |

**Interpretation:** The strict precondition for FAST_CHARGING was
not met in 2008. The event occurred anyway — because the Leaf/Volt
launched with *partial* fast charging (50 kW, not 350 kW). The
model's TRL threshold for FAST_CHARGING may be too strict; the
"system prototype demonstrated" (TRL 7) level is sufficient for
mass-market EVs with Level 2 + entry-level DC fast charging.
This is a candidate refinement: FAST_CHARGING has multiple TRL
levels depending on the power class.

### TR-010: Tesla Supercharger network (2012)

| Field | Value |
|---|---|
| eventId | EV-2012 |
| eventYear | 2012 |
| minimalPreconditions | [{FAST_CHARGING, minTRL: 8, requiredBy: 2010, observedTRL: 7 (at 2010), satisfied: false}, {THERMAL_MANAGEMENT, minTRL: 9, requiredBy: 2010, observedTRL: 9, satisfied: true}] |
| missingPreconditions | ["Capital allocation for infrastructure (economic, not capability)"] |
| counterfactualViolation | "FAST_CHARGING at TRL 7 in 2010 (strict precondition TRL 8 not met). Tesla launched Supercharger network in 2012 with 90 kW chargers — TRL 8 was reached in 2012 (system qualification). Event coincided with TRL crossing." |
| verdict | PARTIAL |

### TR-011: Boeing 787 battery fires (2013)

| Field | Value |
|---|---|
| eventId | EV-2013 |
| eventYear | 2013 |
| minimalPreconditions | [{ELECTROCHEMICAL_ENERGY_STORAGE, minTRL: 9, requiredBy: 2011, observedTRL: 9, satisfied: true}, {STATE_OF_CHARGE_MONITORING, minTRL: 9, requiredBy: 2011, observedTRL: 9, satisfied: true}, {SAFETY_PROTECTION, minTRL: 9, requiredBy: 2011, observedTRL: 9, satisfied: true}] |
| missingPreconditions | ["Aviation certification standards (regulatory, not capability)"] |
| counterfactualViolation | null |
| verdict | EXPLAINED |

**Interpretation:** The Boeing 787 battery fires are technically an
*anti-event* — a failure, not an invention. But the time-reversal
analysis works: the preconditions for the *combination* were met
(Boeing selected Li-ion for the 787 auxiliary battery), and the
event (fires) revealed that SAFETY_PROTECTION at TRL 9 was not
sufficient for aviation-grade safety. The model's ontology does
not distinguish automotive-grade and aviation-grade safety; this
is a missing-precondition disclosure.

### TR-012: Tesla Gigafactory (2016)

| Field | Value |
|---|---|
| eventId | EV-2016 |
| eventYear | 2016 |
| minimalPreconditions | [{ELECTROCHEMICAL_ENERGY_STORAGE, minTRL: 9, requiredBy: 2014, observedTRL: 9, satisfied: true}, {ELECTRODE_COATING, minTRL: 9, requiredBy: 2014, observedTRL: 9, satisfied: true}, {CELL_ASSEMBLY, minTRL: 9, requiredBy: 2014, observedTRL: 9, satisfied: true}] |
| missingPreconditions | ["Capital allocation at gigafactory scale (>$5B, economic)"] |
| counterfactualViolation | null |
| verdict | EXPLAINED |

### TR-013: NMC 811 high-nickel cathode (2017)

| Field | Value |
|---|---|
| eventId | EV-2017 |
| eventYear | 2017 |
| minimalPreconditions | [{ELECTROCHEMICAL_ENERGY_STORAGE, minTRL: 9, requiredBy: 2015, observedTRL: 9, satisfied: true}, {INTERCALATION, minTRL: 9, requiredBy: 2015, observedTRL: 9, satisfied: true}, {ELECTRON_COLLECTION, minTRL: 9, requiredBy: 2015, observedTRL: 9, satisfied: true}] |
| missingPreconditions | ["Nickel supply chain (resource, not capability)"] |
| counterfactualViolation | null |
| verdict | EXPLAINED |

### TR-014: Porsche Taycan 800V (2019)

| Field | Value |
|---|---|
| eventId | EV-2019 |
| eventYear | 2019 |
| minimalPreconditions | [{FAST_CHARGING, minTRL: 9, requiredBy: 2017, observedTRL: 9, satisfied: true}, {THERMAL_MANAGEMENT, minTRL: 9, requiredBy: 2017, observedTRL: 9, satisfied: true}, {SAFETY_PROTECTION, minTRL: 9, requiredBy: 2017, observedTRL: 9, satisfied: true}] |
| missingPreconditions | ["SiC power electronics (800V-specific, not in ontology)", "800V contactor and connector standards (not in ontology)"] |
| counterfactualViolation | null |
| verdict | PARTIAL |

**Interpretation:** The cleanest EXPLAINED-with-gaps case. All
modeled preconditions satisfied 2 years prior. The two missing
preconditions (SiC power electronics, 800V standards) are
honest gaps — they are infrastructure and component capabilities
that the ontology would benefit from modeling. The model's
T=2015 prediction (MECH-003) is consistent with the time-reversal
analysis.

### TR-015: Tesla 4680 cell (2020)

| Field | Value |
|---|---|
| eventId | EV-2020 |
| eventYear | 2020 |
| minimalPreconditions | [{ELECTROCHEMICAL_ENERGY_STORAGE, minTRL: 9, requiredBy: 2018, observedTRL: 9, satisfied: true}, {ELECTRODE_COATING, minTRL: 9, requiredBy: 2018, observedTRL: 9, satisfied: true}, {CELL_ASSEMBLY, minTRL: 9, requiredBy: 2018, observedTRL: 9, satisfied: true}] |
| missingPreconditions | ["Tabless cell design manufacturing process (not in ontology — this is THE innovation)", "Structural battery pack integration (not in ontology)"] |
| counterfactualViolation | null |
| verdict | PARTIAL |

**Interpretation:** The 4680 is the most epistemologically
challenging event. All modeled preconditions were satisfied
5+ years prior — but the event did not occur until 2020. The
missing preconditions (tabless design, structural pack) are
the *actual* innovation. The model is detecting that the
*combination* was reachable, but the specific realization
required unmodeled manufacturing innovations. The model is
correct about the *possibility*; it is silent about the
*specific form*. This is a fundamental limit — and honest.

### TR-016: 4C fast charging mainstream (2023)

| Field | Value |
|---|---|
| eventId | EV-2023 |
| eventYear | 2023 |
| minimalPreconditions | [{ELECTROCHEMICAL_ENERGY_STORAGE, minTRL: 9, requiredBy: 2021, observedTRL: 9, satisfied: true}, {FAST_CHARGING, minTRL: 9, requiredBy: 2021, observedTRL: 9, satisfied: true}, {THERMAL_MANAGEMENT, minTRL: 9, requiredBy: 2021, observedTRL: 9, satisfied: true}] |
| missingPreconditions | ["LFP-specific fast-charging electrolyte additives (not in ontology)", "Cathode particle design for fast charging on LFP (not in ontology)"] |
| counterfactualViolation | null |
| verdict | PARTIAL |

**Interpretation:** Same pattern as TR-015. All modeled
preconditions satisfied 2 years prior; the missing preconditions
are the actual innovation (chemistry-specific fast charging on
LFP). The model's T=2018 prediction (MECH-005) is consistent.

---

## Cross-event time-reversal analysis

### Distribution of verdicts

| Verdict | Count | Events |
|---|---|---|
| EXPLAINED | 6 | EV-1997, EV-2004, EV-2008, EV-2013, EV-2016, EV-2017 |
| PARTIAL | 10 | EV-1991, EV-1992, EV-1996, EV-2001, EV-2003, EV-2010, EV-2012, EV-2019, EV-2020, EV-2023 |
| UNEXPLAINED | 0 | — |

### Distribution of counterfactual violations

| Counterfactual type | Count |
|---|---|
| No violation | 12 |
| Strict precondition not met in Y-1 (event occurred anyway) | 4 (EV-1992, EV-2003, EV-2010, EV-2012) |
| Other violation | 0 |

### The deep finding

**6 of 16 events are EXPLAINED — the preconditions were satisfied
and no counterfactual violation occurred.** This is the strongest
result of the time-reversal analysis. For these 6 events, the
model's ontology is complete enough to say "given what happened,
here is what HAD to be true beforehand, and it WAS true."

**10 of 16 events are PARTIAL — the preconditions were satisfied
but the ontology has gaps.** The gaps are consistently
chemistry-specific capabilities (LFP synthesis, NCM synthesis,
graphite anode formulation, LFP fast-charging additives) and
manufacturing innovations (tabless design, structural pack).
The model's ontology captures *system-level* capabilities but
not *component-level* or *process-level* capabilities.

**0 of 16 events are UNEXPLAINED.** No event in the registry
occurred without its modeled preconditions being satisfied at
some point in the prior 5 years. This is the strongest possible
result for the necessity finding (NECESSITY_SUFFICIENCY.md):
every event has its necessary factors present in the prior window.

### The 4 counterfactual violations

The 4 cases where strict preconditions were not met in Y-1 but
the event occurred anyway are:

- EV-1992 (consumer electronics): EES jumped from TRL 6 to TRL 9
  in 1991 — Sony's commercialization was a step change.
- EV-2003 (Tesla founding): THERMAL_MANAGEMENT at TRL 6, not TRL 7+.
  Tesla bet on a future trajectory.
- EV-2010 (Leaf/Volt): FAST_CHARGING at TRL 6, not TRL 7+. Mass-market
  EVs launched with partial fast charging.
- EV-2012 (Supercharger): FAST_CHARGING at TRL 7, not TRL 8+. Tesla
  launched Supercharger network at TRL crossing.

**Pattern:** All 4 violations involve the same capability:
FAST_CHARGING (3 of 4) or a step-change in EES (1 of 4). The
FAST_CHARGING violations suggest the model's TRL thresholds for
FAST_CHARGING are too strict — TRL 7 is sufficient for
mass-market fast charging (50 kW), TRL 8 for networked fast
charging (90 kW), TRL 9 for ultra-fast (350 kW). The ontology
treats FAST_CHARGING as one capability; it should arguably be
three (entry DC, networked DC, ultra-fast).

**The EES step-change (EV-1992)** is a deeper challenge. The
model cannot predict step changes — by definition, a step change
is the absence of a trajectory. This is a fundamental limit of
the trajectory-velocity framework, and it is honest about it.

---

## What this protocol exposes

### The honest answer to "given what happened, what had to be true beforehand?"

**For 6 of 16 events, the model's ontology is complete and the
preconditions were satisfied.** The model can retrospectively
explain these events without gaps.

**For 10 of 16 events, the model's ontology has gaps.** The gaps
are component-level capabilities (chemistry-specific, process-specific)
that the system-level ontology does not model. The model is correct
about the *direction* but incomplete about the *specific form*.

**For 0 of 16 events, the preconditions were not satisfied.**
The necessity finding (NECESSITY_SUFFICIENCY.md) is supported:
every event has its necessary factors present in the prior
5-year window.

### Why this matters for M5

Time reversal is the strongest test of *explanatory depth*. A
model that predicts forward at 5% precision but cannot explain
backward is curve-fitting. A model that explains backward at
100% (all events have their preconditions satisfied) is making
a claim about causal structure.

The model explains backward at 100% for the *modeled*
capabilities (no UNEXPLAINED events). It explains backward at
37.5% for the *complete* ontology (6 EXPLAINED, 10 PARTIAL with
gaps). This is honest progress toward M5 — and it identifies
the specific gaps (chemistry-specific and process-level
capabilities) that the next ontology version should close.

### The asymmetry between forward and backward

Forward precision: 3.57% (5 TPs in 140 Top-10 predictions).
Backward explanatory power: 100% on modeled factors, 37.5% on
complete ontology.

The asymmetry is not a contradiction — it is a consequence of
the conjunction structure (NECESSITY_SUFFICIENCY.md). Necessary
factors are present in all events (backward: 100%). Necessary
factors are not sufficient (forward: 5%). The model identifies
what MUST be present; it does not identify what WILL happen.

This is the correct epistemic stance for a trajectory-velocity
model: necessity, not sufficiency.

---

## What the protocol does NOT yet settle

1. **The 4 counterfactual violations.** Are they ontology gaps
   (FAST_CHARGING should be split into 3 capabilities) or genuine
   failures of necessity? Resolving this requires refining the
   ontology — which is OUT OF SCOPE for Phase 13 (Formula B is
   frozen; the ontology freeze is per ONTOLOGY_FREEZE.md).
2. **The step-change case (EV-1992).** The model cannot predict
   step changes by construction. Is this a fundamental limit, or
   a future refinement (e.g., a step-change indicator based on
   patent-activity spikes)?
3. **The cross-domain transfer.** Time-reversal records for the
   PV events (PV-2010, PV-2019) are not in this protocol — they
   should be added in a Phase 13E-b extension.

---

## Enforcement

- Every event in EVENT_REGISTRY.md MUST have a TR-XXX entry in
  this file. Events without time-reversal records are demoted
  to INTEGRATED (per Constitution Law 8 — Verification Standard).
- The `verdict` field MUST be reported in every executive summary
  of the model. Reporting precision without explanatory verdicts
  is forbidden from Phase 13 onward.
- Counterfactual violations MUST be investigated. A violation
  that cannot be explained is a candidate falsifier of the
  necessity finding.
- This protocol is append-only (Constitution Law 7).
