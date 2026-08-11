# LEAD_TIME_PROTOCOL — Phase 13B

**Status:** constitutional document (lead-time analysis).
**Location:** repo root.
**Phase:** 13B.

> The model must not merely predict correctly.
> It must predict *early enough to matter*.
> — CEO directive, Phase 13B

---

## Purpose

A model that predicts an event one year before it happens, when the
event's prerequisites have been visible for fifteen years, has
*zero* actionable lead time. It is a calendar, not a forecast.

A model that predicts an event ten years before it happens, but
only at confidence 5%, has *theoretical* lead time and *practical*
zero — the signal is indistinguishable from noise.

The Lead-Time Protocol forces the project to measure prediction
lead time AND prediction confidence simultaneously. The product
`lead_time × confidence` is the model's *actionable foresight*.
Without both, precision is meaningless.

This protocol operationalizes the CEO's directive that success be
measured by explanatory depth, not precision. A 3.57% precision
model that predicts five years early at high confidence is more
valuable than a 50% precision model that predicts one year early
at low confidence — because the former creates decision space,
the latter merely confirms what is already happening.

---

## Schema

```typescript
interface LeadTimeRecord {
    mechanismId: string;       // MECH-XXX from MECHANISM_REGISTRY
    predictionYear: number;    // T at which the model ranked the combination in Top-10
    eventYear: number;         // year the event actually occurred
    leadTime: number;          // eventYear - predictionYear (years)
    confidence: number;        // normalized rank-based confidence at prediction time (0.0–1.0)
    actionableForesight: number; // leadTime × confidence (years)
}
```

### Field semantics

| Field | Type | Required | Meaning |
|---|---|---|---|
| `mechanismId` | string | yes | Foreign key into MECHANISM_REGISTRY.md. Every lead-time record must correspond to a mechanism. |
| `predictionYear` | int | yes | The exact `T` value at which the combination entered the Top-10. From backtest raw output. |
| `eventYear` | int | yes | The year the event was realized. From EVENT_REGISTRY.md. |
| `leadTime` | int | yes | `eventYear - predictionYear`. Positive = predictive. Zero = contemporaneous. Negative = retrospective (model predicted after the event). |
| `confidence` | float | yes | `1 - (rank / total_ranked)`. A Top-10 prediction ranked #1 out of 246 candidates has confidence `1 - (1/246) = 0.996`. Ranked #10 has confidence `1 - (10/246) = 0.959`. Below Top-10 is excluded by definition. |
| `actionableForesight` | float | yes | `leadTime × confidence`. Measured in years. The model's actual decision-relevant foresight. If `confidence` is 0.5 and `leadTime` is 5 years, `actionableForesight` is 2.5 years. |

### Classification of records

| Lead time | Confidence | Classification | Meaning |
|---|---|---|---|
| ≥ 3 years | ≥ 0.95 | STRONG foresight | Decision-relevant; investor/engineer can act on it. |
| 1–2 years | ≥ 0.95 | WEAK foresight | Useful for prioritization; not for commitment. |
| 0 years | ≥ 0.95 | CONTEMPORANEOUS | Model confirms what is happening; no foresight value. |
| < 0 (negative) | any | RETROSPECTIVE | Model predicted after the event. Failure mode. |
| any | < 0.95 | INSUFFICIENT CONFIDENCE | Even with positive lead time, signal is too weak. |

### What this protocol forbids

- Reporting precision without lead time. From Phase 13 onward,
  every backtest result table MUST include lead-time columns.
- Reporting lead time without confidence. A 10-year lead time at
  rank #9 of 10 has near-zero actionable foresight.
- Aggregating lead times across events. Mean lead time is
  meaningless when the underlying lag structure varies by
  bottleneck type (see MECHANISM_REGISTRY Observation 3).

---

## Lead-time records (Li-ion domain)

For each TP in the expanded 14-point backtest, the prediction year
is the earliest `T` at which the combination entered the Top-10.
Where a combination appears in multiple T windows (e.g. FAST_CHARGING
combos), the EARLIEST T is recorded — that is when the model first
"noticed" it.

### LT-001: Li-ion BMS in early EVs (1997)

| Field | Value |
|---|---|
| mechanismId | MECH-001 |
| predictionYear | 1995 |
| eventYear | 1997 |
| leadTime | 2 years |
| confidence | 1 - (2/246) = 0.992 |
| actionableForesight | 2 × 0.992 = 1.984 years |
| classification | WEAK foresight |

**Interpretation:** Two years of decision-relevant notice that
Li-ion BMS EVs were coming. Sufficient for an incumbent OEM to
begin a vehicle program (typical OEM program timeline is 3–5 years
from decision to launch). Sufficient for a battery supplier to
allocate R&D capacity to EV-pack-grade BMS. NOT sufficient for a
new entrant to build a vehicle program from cold start.

### LT-002: Tesla Roadster production begins (2008)

| Field | Value |
|---|---|
| mechanismId | MECH-002 |
| predictionYear | 2005 |
| eventYear | 2008 |
| leadTime | 3 years |
| confidence | 1 - (10/375) = 0.973 |
| actionableForesight | 3 × 0.973 = 2.920 years |
| classification | WEAK foresight (almost STRONG) |

**Interpretation:** Three years of notice. Just below the STRONG
threshold. Tesla Motors was founded in 2003 — two years BEFORE the
model's prediction year. This is the most interesting case in the
registry: the model predicted in 2005 what Tesla had already bet
on in 2003. The model is *confirming* the trajectory, not
*discovering* it. This is honest — and important. A model that
claims to have predicted the Tesla Roadster would be lying; a model
that confirms a bet already made is doing exactly what a
trajectory-velocity model should do.

### LT-003: Porsche Taycan 800V architecture (2019)

| Field | Value |
|---|---|
| mechanismId | MECH-003 |
| predictionYear | 2015 |
| eventYear | 2019 |
| leadTime | 4 years |
| confidence | 1 - (10/375) = 0.973 |
| actionableForesight | 4 × 0.973 = 3.892 years |
| classification | STRONG foresight |

**Interpretation:** Four years of decision-relevant notice.
Porsche began Taycan development in 2014–2015 — exactly when the
model flagged the combination. This is the cleanest case in the
registry: the model's prediction year aligns with the actual
industry decision year. An investor using the model's 2015 output
could have allocated capital to 800V component suppliers
(SiC power electronics, high-voltage contactors, advanced
thermal-management systems) and captured the 2019 production ramp.

### LT-004: Tesla 4680 cell announced (2020)

| Field | Value |
|---|---|
| mechanismId | MECH-004 |
| predictionYear | 2018 |
| eventYear | 2020 |
| leadTime | 2 years |
| confidence | 1 - (rank/total) — approximate 0.95 (estimated from per-T distribution; raw rank not preserved in committed JSON) |
| actionableForesight | ~1.9 years |
| classification | WEAK foresight |

**Interpretation:** Two years of notice. Tesla announced the 4680
at Battery Day (September 2020). The model flagged the combination
at T=2018 — two years prior. *However*, this mechanism is
unusual (per MECH-004): the rising capability (FAST_CHARGING) is
pulling through a manufacturing innovation in *adjacent*
capabilities. The lead time is real but the mechanism is a
"shadow signal" — the model is detecting a second-order effect,
not a first-order one. Confidence in this TP should be discounted
in any decision-making use of the model.

### LT-005: 4C fast charging mainstream (2023)

| Field | Value |
|---|---|
| mechanismId | MECH-005 |
| predictionYear | 2018 |
| eventYear | 2023 |
| leadTime | 5 years |
| confidence | 1 - (rank/total) — approximate 0.95 |
| actionableForesight | ~4.75 years |
| classification | STRONG foresight |

**Interpretation:** Five years of decision-relevant notice.
CATL Shenxing (4C LFP) was announced August 2023; the model flagged
the combination at T=2018. This is the longest lead time in the
registry. *However*, the mechanism is partial (per MECH-005):
the model correctly predicted the combination would be realized,
but the bottleneck was a sub-capability (chemistry-specific fast
charging) not captured in the ontology. The lead time is real; the
explanation is incomplete. This is exactly the kind of case that
Phase 13 (mechanism depth) is designed to expose.

---

## Lead-time records (Photovoltaic domain)

### LT-006: Thin-film PV commercialization (~2010)

| Field | Value |
|---|---|
| mechanismId | MECH-006 |
| predictionYear | 2005 |
| eventYear | 2010 (First Solar >1 GW production) |
| leadTime | 5 years |
| confidence | 1 - (rank/total) — approximate 0.95 |
| actionableForesight | ~4.75 years |
| classification | STRONG foresight |

**Interpretation:** Five years of notice. First Solar was founded
in 1999 and reached commercial scale ~2008–2010. The model flagged
the combination in 2005 — six years after founding, five years
before scale. Like LT-002 (Tesla Roadster), the model is
confirming a trajectory already in motion. But unlike LT-002, the
lead time here is *long enough to act on*: an investor in 2005
could have identified First Solar as the leader and accumulated
position before its 2006 IPO.

### LT-007: Bifacial PV modules (~2019)

| Field | Value |
|---|---|
| mechanismId | MECH-007 |
| predictionYear | 2015 |
| eventYear | 2019 (bifacial market share >10%) |
| leadTime | 4 years |
| confidence | 1 - (rank/total) — approximate 0.95 |
| actionableForesight | ~3.8 years |
| classification | STRONG foresight |

**Interpretation:** Four years of notice. Bifacial module
manufacturing capacity expansion began ~2016–2017 — one to two
years after the model's 2015 prediction. This is the cleanest
cross-domain STRONG foresight case: the model transferred from
Li-ion to PV, predicted a combination, and the industry followed
within the expected lead time.

---

## Aggregate lead-time analysis

### Distribution across mechanisms

| Lead time bucket | Count | Mechanisms |
|---|---|---|
| STRONG (≥3 yr, ≥0.95 conf) | 4 | LT-003, LT-005, LT-006, LT-007 |
| WEAK (1–2 yr, ≥0.95 conf) | 3 | LT-001, LT-002, LT-004 |
| CONTEMPORANEOUS (0 yr) | 0 | — |
| RETROSPECTIVE (<0) | 0 | — |
| INSUFFICIENT CONFIDENCE | 0 | — |

### Mean actionable foresight

```
mean_actionable_foresight = (1.98 + 2.92 + 3.89 + 1.90 + 4.75 + 4.75 + 3.80) / 7
                          = 24.00 / 7
                          ≈ 3.43 years
```

The model delivers ~3.4 years of decision-relevant notice on
average across both domains. This is *below* the 5-year strategic
planning horizon typical of large infrastructure investment but
*above* the 1–2 year tactical horizon of incremental R&D
allocation. The model is therefore useful for the *second*
decision type (R&D prioritization) and not for the *first*
(strategic capacity build).

### Lead time versus mechanism type

Cross-tabulating against MECHANISM_REGISTRY Observation 3:

| Stable base type | Mechanisms | Mean lead time | Notes |
|---|---|---|---|
| Cell chemistry | MECH-001, MECH-005 | 3.5 yr | Chemistry → product lag |
| Pack integration | MECH-002 | 3.0 yr | Automotive OEM lag |
| Vehicle platform | MECH-003 | 4.0 yr | New platform lag |
| Manufacturing line | MECH-004, MECH-006 | 3.5 yr | Process development lag |
| Module assembly | MECH-007 | 4.0 yr | Production ramp lag |

The lead time is *not* uniform. It is determined by the type of
the stable base. The model does not currently predict lag — it
predicts combinations. The lag structure is a candidate for the
next refinement.

---

## What this protocol exposes

### The honest answer to "does the model predict early enough?"

**Yes, with caveats.** The model delivers 3–5 years of
decision-relevant foresight in 4 of 7 cases (STRONG classification),
and 2–3 years in the remaining 3 (WEAK classification). No TP in
the registry is contemporaneous or retrospective.

**However**, the model's lead time is *not* uniformly distributed.
It depends on:
1. The type of the stable base (cell < pack < platform < line).
2. Whether the rising capability is first-order (LT-003, LT-006,
   LT-007 — all STRONG) or second-order (LT-004 — WEAK, and
   suspect).
3. Whether the mechanism has been fully explained (MECH-005 — STRONG
   lead time but partial mechanism).

### The deep question: is 3.4 years enough?

For the model's *current* use case (R&D prioritization within an
existing industry), yes. For strategic capacity build
(gigafactory-scale investment), no — 5 years is the minimum,
and the model only delivers that in 2 of 7 cases.

The model should NOT be marketed as a strategic foresight tool
until mean actionable foresight crosses 5 years. The current
3.4-year mean is R&D-tactical, not strategic.

---

## Enforcement

- Every TP in every future backtest MUST have an LT-XXX entry.
  TPs without lead-time records are demoted to INFORMATIONAL
  (Constitution Law 8).
- The `confidence` field MUST be computed from the raw backtest
  output (rank and total_ranked). Estimates are permitted only when
  raw output was not preserved (as in LT-004 and LT-005); such
  entries are flagged with the `approximate` qualifier and
  prioritized for re-running.
- The `actionableForesight` field MUST be reported alongside
  precision in every executive summary of backtest results.
  Reporting precision without actionable foresight is forbidden
  from Phase 13 onward.
- This protocol is append-only (Constitution Law 7).
