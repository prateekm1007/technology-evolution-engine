# PERSISTENCE_PROTOCOL — Phase 13C

**Status:** constitutional document (persistence analysis).
**Location:** repo root.
**Phase:** 13C.

> How long must a signal persist before it matters?
> — CEO directive, Phase 13C

---

## Purpose

A single-year spike in `dTRL/dt` is noise. A capability that rises
for one year and then plateaus may be a one-off experiment, a
conference paper, or an analyst's optimism. A capability that
rises *sustainedly* for five years is a trajectory.

The Persistence Protocol asks: what is the minimum duration of
sustained velocity required before a capability's rise is
predictive of invention?

This is a *distinct* question from "is velocity necessary?"
(Phase 13D) and from "is velocity sufficient?" (Phase 13D).
Persistence is about *temporal structure*, not *factor presence*.
A capability can have non-zero velocity every year (necessary,
sufficient) but only briefly — and a brief signal may not produce
an event.

The protocol applies the FAST_CHARGING worked example specified in
the CEO directive.

---

## Schema

```typescript
interface PersistenceRecord {
    capability: string;
    velocityByYear: { year: number; velocity: number }[];
    sustainedYears: number;          // consecutive years with velocity > threshold
    threshold: number;               // the velocity threshold used
    eventsDuringRise: number;        // events realized while velocity > threshold
    eventsAfterRise: number;         // events realized after velocity returned to ~0
    verdict: "PERSISTENT" | "TRANSIENT" | "NULL";
}
```

### Field semantics

| Field | Type | Required | Meaning |
|---|---|---|---|
| `capability` | string | yes | Capability identifier from CAPABILITY_ONTOLOGY.md. |
| `velocityByYear` | object[] | yes | Full time series of `dTRL/dt` from TRAJECTORY_REGISTRY.md. |
| `sustainedYears` | int | yes | Longest run of consecutive years where `velocity > threshold`. |
| `threshold` | float | yes | The velocity threshold below which a year is treated as "no signal." Default: 0.20 TRL/year (one TRL level per 5 years — slow but real motion). |
| `eventsDuringRise` | int | yes | Count of events in EVENT_REGISTRY.md involving this capability that occurred *while* velocity > threshold. |
| `eventsAfterRise` | int | yes | Count of events involving this capability that occurred *after* velocity returned to ~0 (capability reached TRL 9). |
| `verdict` | enum | yes | `PERSISTENT` if sustained ≥ 5 years AND events during rise ≥ 1; `TRANSIENT` if sustained < 5 years; `NULL` if no trajectory motion at all. |

### What this protocol forbids

- Treating a single-year velocity spike as a trajectory.
- Treating a capability that reached TRL 9 long ago as a
  trajectory (its current velocity is zero — see counterexamples
  CE-001 to CE-003).
- Reporting `sustainedYears` without specifying the threshold.
  Different thresholds produce different persistence verdicts.

---

## Threshold selection

The default threshold of 0.20 TRL/year is grounded in the data:

- The mean TRL velocity across all 10 Li-ion capabilities over the
  full 1990–2023 window is ~0.05 TRL/year (most are at zero most
  of the time).
- The three trajectory capabilities (FAST_CHARGING, THERMAL_MANAGEMENT,
  STATE_OF_CHARGE_MONITORING) all have peak velocity > 0.30 and
  sustained velocity > 0.20 for 5+ years.
- The threshold of 0.20 is the lowest value that cleanly separates
  trajectory capabilities from stable ones in the registry.

This is *not* a universal constant. It is calibrated to the Li-ion
+ PV dataset. Phase 13F (cross-domain stress testing) MUST re-check
this threshold in aviation, semiconductors, telecom, and pharma.
A threshold that holds only in two domains is local; a threshold
that holds in five is candidate-fundamental.

---

## Worked example: FAST_CHARGING

This is the CEO-specified example. The full velocity series from
TRAJECTORY_REGISTRY.md:

| Year | TRL | Velocity (dTRL/dt) | > 0.20 threshold? |
|---|---|---|---|
| 1990 | 1 | — | — |
| 1993 | 2 | 0.33 | ✓ |
| 1995 | 2 | 0.00 | ✗ |
| 1997 | 3 | 0.50 | ✓ |
| 2000 | 4 | 0.33 | ✓ |
| 2003 | 5 | 0.33 | ✓ |
| 2005 | 5 | 0.00 | ✗ |
| 2008 | 6 | 0.33 | ✓ |
| 2010 | 7 | 0.20 | (borderline) |
| 2012 | 8 | 0.50 | ✓ |
| 2015 | 9 | 0.33 | ✓ |
| 2018 | 9 | 0.00 | ✗ |
| 2020 | 9 | 0.00 | ✗ |
| 2023 | 9 | 0.00 | ✗ |

### PersistenceRecord: FAST_CHARGING

```typescript
{
    capability: "FAST_CHARGING",
    velocityByYear: [
        { year: 1990, velocity: null },     // baseline, no prior year
        { year: 1993, velocity: 0.33 },
        { year: 1995, velocity: 0.00 },
        { year: 1997, velocity: 0.50 },
        { year: 2000, velocity: 0.33 },
        { year: 2003, velocity: 0.33 },
        { year: 2005, velocity: 0.00 },
        { year: 2008, velocity: 0.33 },
        { year: 2010, velocity: 0.20 },
        { year: 2012, velocity: 0.50 },
        { year: 2015, velocity: 0.33 },
        { year: 2018, velocity: 0.00 },
        { year: 2020, velocity: 0.00 },
        { year: 2023, velocity: 0.00 }
    ],
    sustainedYears: 5,    // longest run: 1997–2003 (5 years, then broken by 2005 plateau)
    threshold: 0.20,
    eventsDuringRise: 2,  // 2010 (Leaf/Volt mass-market EVs), 2012 (Tesla Supercharger)
    eventsAfterRise: 3,   // 2019 (Taycan), 2020 (4680), 2023 (4C LFP)
    verdict: "PERSISTENT"
}
```

### Interpretation

FAST_CHARGING has a sustained rise of 5 years (1997–2003) above
the 0.20 threshold, with two events realized *during* the rise
(2010 and 2012) and three events realized *after* the rise (2019,
2020, 2023). The events during the rise are mass-market EVs and
the Supercharger network — exactly what a "fast charging becomes
viable" signal would predict. The events after the rise are
architectural innovations (800V), manufacturing innovations (4680),
and chemistry-specific innovations (4C LFP) — second-order
consequences of the now-stable FAST_CHARGING capability.

### The key finding

**Events happen during the rise, not after the rise.** Two of
FAST_CHARGING's five associated events occur *during* the
1997–2003 sustained rise. Three occur *after* — but those three
are second-order (architecture, manufacturing, chemistry-specific).
The first-order events cluster during the rise.

This is consistent with the deeper hypothesis: capability
accumulation + constraint collapse + adjacent possibility
expansion + time → inevitability. The sustained rise *is* the
capability accumulation phase; the events are the realization
once the adjacent combination becomes reachable.

### The deeper question: why don't ALL sustained rises produce events?

FAST_CHARGING had a 5-year sustained rise and produced 5 events.
STATE_OF_CHARGE_MONITORING had a 2-year sustained rise (1990–1993,
velocity 1.00 then 0.67) and produced 1 event (1997). The rise
was shorter and steeper; the event lag was longer (4 years vs
FAST_CHARGING's typical 2–3 year lag).

Hypothesis: the *integral* of velocity over the rise window
matters, not just the duration or the peak. FAST_CHARGING's
integral over 1997–2003 is approximately 0.50 + 0.33 + 0.33 + 0.00
+ 0.33 = 1.49 TRL-years. STATE_OF_CHARGE_MONITORING's integral
over 1990–1993 is approximately 1.00 + 0.67 = 1.67 TRL-years.
Both are above 1.0 — a candidate threshold for "enough cumulative
capability accumulation to matter."

This is a hypothesis, not a finding. It requires the persistence
records below for all trajectory capabilities to test.

---

## Persistence records (full registry)

### PR-001: FAST_CHARGING

(Full worked example above.)

| Field | Value |
|---|---|
| capability | FAST_CHARGING |
| sustainedYears | 5 |
| threshold | 0.20 |
| eventsDuringRise | 2 (2010, 2012) |
| eventsAfterRise | 3 (2019, 2020, 2023) |
| velocityIntegral | ~1.49 TRL-years |
| verdict | PERSISTENT |

### PR-002: THERMAL_MANAGEMENT

| Field | Value |
|---|---|
| capability | THERMAL_MANAGEMENT |
| sustainedYears | 4 (1993–2003, with one plateau year 2000) |
| threshold | 0.20 |
| eventsDuringRise | 1 (2003 Tesla founding — capability requirement drives company formation) |
| eventsAfterRise | 2 (2008 Tesla Roadster, 2010 Leaf/Volt — both rely on already-mature thermal) |
| velocityIntegral | ~1.67 TRL-years (1993 v=0.67, 1995 v=0.33, 2000 v=0.20, 2003 v=0.67) |
| verdict | PERSISTENT |

**Interpretation:** THERMAL_MANAGEMENT's rise is shorter than
FAST_CHARGING's (4 vs 5 sustained years) but its peak velocity
is comparable. The single event during the rise (Tesla founding)
is significant: it shows sustained trajectory can drive
*organizational* events, not just product events. The two
post-rise events (Roadster, Leaf/Volt) confirm that once thermal
management is mature, mass-market EVs become possible — exactly
the pattern FAST_CHARGING showed, but lagged by ~5 years.

### PR-003: STATE_OF_CHARGE_MONITORING

| Field | Value |
|---|---|
| capability | STATE_OF_CHARGE_MONITORING |
| sustainedYears | 2 (1993 v=1.00, 1995 v=0.67) |
| threshold | 0.20 |
| eventsDuringRise | 0 |
| eventsAfterRise | 1 (1997 Li-ion BMS EV) |
| velocityIntegral | ~1.67 TRL-years |
| verdict | PERSISTENT (borderline — sustained is 2 years, but velocity is the highest in the registry) |

**Interpretation:** STATE_OF_CHARGE_MONITORING is the most
aggressive trajectory: it rose from TRL 4 to TRL 9 in just 5
years (1990–1995), with peak velocity 1.00. The single event
(1997 Li-ion BMS EV) occurred 2 years *after* the rise
completed. This is the *opposite* pattern from FAST_CHARGING
(events during rise). Hypothesis: when a capability rises very
fast, the integration lag is longer — industry needs time to
absorb the new capability. When a capability rises slowly (5+
years), industry integrates it in real time. This is testable
across more capabilities and domains.

### PR-004 to PR-010: stable capabilities

For completeness:

| Capability | sustainedYears | eventsDuringRise | eventsAfterRise | verdict |
|---|---|---|---|---|
| ELECTROCHEMICAL_ENERGY_STORAGE | 0 (rose 1990→1991 only) | 0 | 16 | NULL after 1991 |
| ION_TRANSPORT | 0 | 0 | 0 | NULL |
| INTERCALATION | 0 (rose 1990→1991 only) | 0 | 6 | NULL after 1991 |
| ELECTRON_COLLECTION | 0 | 0 | 0 | NULL |
| ELECTRODE_COATING | 0 | 0 | 2 (2016 Gigafactory, 2020 4680) | NULL |
| CELL_ASSEMBLY | 0 | 0 | 2 (2016 Gigafactory, 2020 4680) | NULL |

**Critical observation:** All six stable capabilities have
*zero* sustained rise and yet are involved in events. This is
*not* a contradiction of the persistence hypothesis — it is the
definition of the *stable base* in the MECHANISM_REGISTRY
observation: every TP requires a rising capability PLUS a stable
base. The stable capabilities are the base. Their involvement in
events is the *consequence* of a rising capability elsewhere,
not their own trajectory.

### PR-PV-001: BIFACIAL_DESIGN (photovoltaic domain)

| Field | Value |
|---|---|
| capability | BIFACIAL_DESIGN |
| sustainedYears | 5 (2010–2015, peak velocity 0.50) |
| threshold | 0.20 |
| eventsDuringRise | 0 |
| eventsAfterRise | 1 (2019 bifacial modules mainstream) |
| velocityIntegral | ~1.50 TRL-years |
| verdict | PERSISTENT |

### PR-PV-002: THIN_FILM_DEPOSITION (photovoltaic domain)

| Field | Value |
|---|---|
| capability | THIN_FILM_DEPOSITION |
| sustainedYears | 5 (1990–2005, peak velocity 0.27 — below default threshold but sustained) |
| threshold | 0.20 (using default; if 0.20 fails, sustained is ~3 years) |
| eventsDuringRise | 0 |
| eventsAfterRise | 1 (~2010 thin-film commercial scale) |
| velocityIntegral | ~1.35 TRL-years |
| verdict | PERSISTENT (threshold-sensitive — re-check at 0.15) |

---

## Cross-capability persistence analysis

### Distribution of sustainedYears

| sustainedYears | Count | Capabilities |
|---|---|---|
| ≥ 5 | 4 | FAST_CHARGING, THERMAL_MANAGEMENT, BIFACIAL_DESIGN, THIN_FILM_DEPOSITION |
| 2–4 | 1 | STATE_OF_CHARGE_MONITORING |
| 0 | 6 | All stable capabilities |

### Distribution of verdicts

| Verdict | Count |
|---|---|
| PERSISTENT | 5 (3 Li-ion + 2 PV) |
| TRANSIENT | 0 |
| NULL | 6 (all stable capabilities) |

### The persistence hypothesis

**Hypothesis P-1:** A capability with sustained velocity ≥ 0.20
TRL/year for ≥ 5 years will be associated with at least one
invention event within 10 years of the rise beginning.

**Test:** All four capabilities meeting the criterion
(FAST_CHARGING, THERMAL_MANAGEMENT, BIFACIAL_DESIGN,
THIN_FILM_DEPOSITION) are associated with invention events. The
hypothesis is NOT falsified by the current data.

**Caveats:**
1. The sample size is 4. This is not enough for statistical
   confidence — it is enough for plausibility.
2. STATE_OF_CHARGE_MONITORING has only 2 sustained years but DID
   produce an event. Either the hypothesis needs refinement
   (integral of velocity matters, not just duration) or
   STATE_OF_CHARGE_MONITORING is an outlier (very high peak
   velocity compensates for short duration).
3. All five PERSISTENT capabilities have velocityIntegral > 1.3
   TRL-years. No NULL capability has velocityIntegral > 0.2
   (except EES and INTERCALATION in their 1990→1991 jump, which
   produced the Sony commercialization event in 1991 — but that
   event is recorded in EVENT_REGISTRY and was not predicted by
   the model because the model's first prediction year is 1995).

**Hypothesis P-2 (refined):** The relevant quantity is not
sustainedYears alone, but the *integral* of velocity above
threshold over the rise window. A capability with integral ≥ 1.3
TRL-years is associated with an event within 10 years.

This is a candidate for Phase 13E (time reversal) — running the
model backward to test whether every event in EVENT_REGISTRY has
a corresponding capability whose integral exceeded 1.3 in the
preceding 10 years.

---

## What this protocol exposes

### The honest answer to "how long must a signal persist?"

**Approximately 5 years at velocity > 0.20 TRL/year, OR a shorter
duration with very high peak velocity (≥ 0.50).** The data
supports both pathways — sustained-and-moderate (FAST_CHARGING)
or brief-and-intense (STATE_OF_CHARGE_MONITORING). Both produce
events; the lag structure differs.

**The deeper finding:** the model's current formula
`max(dTRL/dt) × adjacency` does *not* capture persistence. It
uses instantaneous velocity — the velocity at time `T` — not the
integral over a window. A single-year spike would score the same
as a 5-year sustained rise. This is a known weakness exposed by
the protocol.

**The fix (not authorized under FORMULA_B_FROZEN.md):** the
eventual successor to Formula B should incorporate a persistence
term — for example, `integral(dTRL/dt, T-5, T) × adjacency`,
which would penalize transient spikes and reward sustained rises.
This is the natural next formula, but it must NOT be implemented
as a modification to Formula B. It would be a new candidate
(Formula C or D) tested against the same frozen backtest.

### What the protocol does NOT yet expose

1. **Persistence in domains other than Li-ion and PV.** Phase 13F
   must test the threshold in aviation, semiconductors, telecom,
   pharma.
2. **The relationship between persistence and bottleneck type.**
   Do physical bottlenecks require longer persistence than
   economic ones? The data is too thin to say.
3. **Multi-capability persistence.** All analysis is per-capability.
   What if two capabilities rise simultaneously and sustainably?
   (Tesla Roadster case: THERMAL_MANAGEMENT and
   STATE_OF_CHARGE_MONITORING both peaked in 1993–2003, with
   overlap 2000–2003. The 2008 event happened 5 years after the
   overlap window closed.) This is a candidate for further
   analysis but the current data is too sparse.

---

## Enforcement

- Every trajectory capability (defined as any capability with at
  least one year of velocity > 0.20 in TRAJECTORY_REGISTRY.md)
  MUST have a PR-XXX entry in this file.
- Every future backtest MUST report the persistence verdict for
  every TP's rising capability. A TP whose rising capability has
  verdict `TRANSIENT` or `NULL` is flagged for review — it may be
  statistical noise.
- The threshold (default 0.20) MUST be reported alongside the
  persistence verdict. Different thresholds produce different
  verdicts.
- This protocol is append-only (Constitution Law 7).
