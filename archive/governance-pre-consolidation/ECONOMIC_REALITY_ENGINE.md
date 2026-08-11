# ECONOMIC_REALITY_ENGINE

**Status:** Honesty Loop Priority 9 engine (specification).
**Location:** repo root.
**Phase:** Honesty Loop v1.0 / P9.
**Governance:** Per BLUEPRINT_CONSTITUTION.md Law 27 (no numerical certainty without experimental validation), Law 28 (forbidden language), Law 29 (typed status enums). See HONESTY_LOOP.md.
**Triggered by:** Consolidated review finding — "Every component
should have supplier, supplier location, part number, lead time,
MOQ, revision number, quotation date, import duty, shipping
cost." (The procurement half. The economic reality half is
quote-backed pricing.)

> An estimated price is an opinion. A quoted price is a fact.
> A blueprint that ships cost claims based on estimates is
> shipping opinions as facts. The Economic Reality Engine
> forbids this.
> — Consolidated review, post-BP-2

---

## Purpose

The Economic Reality Engine forbids estimated prices in
PRODUCTION packages. Every cost claim must trace through
the Procurement Engine (P4) to a dated quotation from a
named supplier. Estimates are permitted in CONCEPT and
DECISION packages only, and must be labeled `ESTIMATE` —
never presented as a price.

This is Priority 9 because the EV battery blueprint shipped
"$11,845 unit cost, $157.9/kWh" — a number with no quotation
backup, no supplier names, and no dates. The number was
unfalsifiable. The Economic Reality Engine makes it falsifiable
or forbids it.

---

## Schema

```typescript
interface EconomicRealityRecord {
    id: string                                // ER-XXX
    assemblyId: string                       // the assembly (PACK-001, ROBOT-001, etc.)
    costBreakdown: CostLine[]
    totalCostUSD: number                      // computed: sum(costBreakdown.landedCostUSD)
    costPerKWh?: number                       // for energy-storage assemblies: totalCostUSD / kWh
    costBasis: "QUOTED" | "ESTIMATED" | "MIXED"
    quotationDate?: string                   // the EARLIEST quotation date among all lines (most stale)
    quotationExpiryDate?: string              // the EARLIEST expiry (first to expire)
    exchangeRateReference?: string            // if non-USD quotes were converted
    sensitivityAnalysis?: SensitivityRecord
    evidenceLineageIds: string[]              // EV-XXX (P1)
    status: "PASS" | "PASS_WITH_CONDITIONS" | "MARGINAL" | "BLOCKED" | "REJECTED"
    retractionId?: string                     // if this retracts a prior narrative cost claim (P7)
}

interface CostLine {
    bomLineId: string                         // BL-XXX
    procurementId: string                     // PR-XXX from Procurement Engine (P4)
    description: string
    unitLandedCostUSD: number                // from PR.landed.unitPriceUSD
    quantity: number
    subtotalUSD: number                       // unitLandedCostUSD × quantity
    costBasis: "QUOTED" | "ESTIMATED"
    quotationDate: string
    quotationExpiryDate?: string
    evidenceId: string
}

interface SensitivityRecord {
    scenarios: {
        name: string                         // "supplier price +10%", "USD/CNY +5%", "lead time +30 days"
        costDeltaUSD: number
        costDeltaPercent: number
        evidenceId: string                    // supports the sensitivity assumption
    }[]
    notes: string
}
```

---

## Cost basis rules

1. **PRODUCTION packages require `costBasis: QUOTED`.** Every
   cost line must trace to a ProcurementRecord (P4) with a
   non-stale quotation. Mixed-basis (some quoted, some
   estimated) is permitted only with `STATUS:
   PASS_WITH_CONDITIONS` and the conditions must list which
   lines are estimated.

2. **CONCEPT and DECISION packages permit `costBasis: ESTIMATED`.**
   But every estimated line must be labeled `ESTIMATE` and
   carry a `basis` field stating how the estimate was derived
   (e.g., "BloombergNEF 2024 cell price index, $89/kWh ×
   280 Ah × 3.2 V = $79.5, +15% margin").

3. **Cost totals are computed, not entered.** `totalCostUSD`
   must equal `sum(costBreakdown.subtotalUSD)`. The engine
   recomputes this and rejects mismatches.

4. **Cost-per-kWh is computed only for energy-storage assemblies.**
   For a 75 kWh pack at $11,845 total, cost-per-kWh =
   11845 / 75 = $157.9/kWh. The engine forbids entering this
   number directly; it must be derived.

5. **Quotation dates are tracked.** The record's
   `quotationDate` is the EARLIEST (most stale) date among
   all lines. If the earliest is older than 90 days, the
   record is `STATUS: MARGINAL` or `STATUS: BLOCKED` per
   the staleness table in PROCUREMENT_ENGINE.md.

6. **Sensitivity analysis is required for PRODUCTION packages.**
   At minimum: supplier price ±10%, FX ±5%, lead time +30
   days. Each scenario produces a cost delta. The total
   cost is reported as a point estimate PLUS a sensitivity
   range — never as a point estimate alone.

---

## Staleness and decay (mirrors P4)

| Quote age | Status | Notes |
|---|---|---|
| < 30 days | PASS | Fresh quote |
| 30-90 days | PASS_WITH_CONDITIONS | Re-quote before commitment |
| 90-180 days | MARGINAL | Re-quote before PO; stale quotes in PRODUCTION packages are forbidden |
| > 180 days | BLOCKED | Quote expired; cannot be used in PRODUCTION |

---

## Example economic reality record

```
ER-001: 75 kWh LFP battery pack

  costBreakdown:
    - BL-001 cells          PR-001  $94.65 × 96   = $9,086.40   QUOTED 2024-07-15
    - BL-002 busbars        PR-004  $1.20  × 96   =   $115.20   QUOTED 2024-07-20
    - BL-003 coolant         PR-007  $3.20  × 6    =    $19.20   QUOTED 2024-08-01
    - BL-004 housing        PR-010  $480   × 1    =   $480.00   QUOTED 2024-07-30
    - BL-005 insulation      PR-013  $42    × 1    =    $42.00   QUOTED 2024-08-05
    - BL-006 harnesses       PR-016  $85    × 1    =    $85.00   QUOTED 2024-08-05
    - BL-007 fasteners       PR-019  $18    × 1    =    $18.00   QUOTED 2024-08-05
    - BL-008 mounts          PR-022  $72    × 1    =    $72.00   QUOTED 2024-08-05
    - BL-009 BMS             PR-025  $312   × 1    =   $312.00   QUOTED 2024-07-22
    - BL-010 pack assembly   PR-028  $1,615 × 1    = $1,615.00   ESTIMATE (labor + overhead, +20% margin)

  totalCostUSD: 11,844.80 (computed: sum of all subtotals)

  costPerKWh: 11844.80 / 75 = $157.93/kWh (computed)

  costBasis: MIXED  (9 QUOTED + 1 ESTIMATE)
  quotationDate: 2024-07-15  (oldest: PR-001)
  quotationExpiryDate: 2024-10-15

  sensitivityAnalysis:
    scenarios:
      - name: "Cell price +10%"
        costDeltaUSD: +908.64
        costDeltaPercent: +7.7%
        evidenceId: EV-501
      - name: "USD/CNY +5%"
        costDeltaUSD: +445.00
        costDeltaPercent: +3.8%
        evidenceId: EV-502
      - name: "Lead time +30 days"
        costDeltaUSD: +0 (no expedite fee assumed; production line slack)
        costDeltaPercent: 0%
        evidenceId: EV-503
    notes: "Largest sensitivity is cell price (77% of cost). Battery
            price index volatility 2024 Q3: ±15% YoY (BloombergNEF).
            PRODUCTION commitment should hedge cell price."

  status: PASS_WITH_CONDITIONS
    (conditions: 1 line ESTIMATED; re-quote all lines before PO;
     quotation expires 2024-10-15)
```

Without this engine, "$11,845, $157.9/kWh" is an opinion
with units. With it, the same number is a typed, dated,
supplier-backed, sensitivity-analyzed fact — or it is
forbidden.

---

## What this engine does NOT do

- It does not place orders. That is procurement.
- It does not negotiate prices. That is supplier engineering.
- It does not set prices. That is the market.
- It does not compute margins. Margin is downstream (business
  model); the engine produces the cost basis that margin is
  computed against.

---

## Pre-stated falsifier (EP-4)

**Claim:** Every cost claim in a PRODUCTION package can be
resolved to dated, supplier-backed quotations through the
Procurement Engine.

**Falsifier:** A PRODUCTION package that ships a cost total
where one or more lines have no PR-XXX reference, or where
the quotation has expired. Such claims are forbidden;
the package cannot ship.

**Status:** PENDING. Engine specified; implementation awaits
AEP Gate 1 for the engine itself.
