# PROCUREMENT_ENGINE

**Status:** Honesty Loop Priority 4 engine (specification).
**Location:** repo root.
**Phase:** Honesty Loop v1.0 / P4.
**Triggered by:** Consolidated review finding — "The BOM is still
partially narrative. Every component should have supplier,
location, part number, lead time, MOQ, revision, quotation date,
import duty, shipping cost."

> A BOM line without a supplier is a wish.
> A BOM line with a supplier but no quotation date is a guess.
> A BOM line with a quotation date older than 90 days is a
> stale guess.
> — Consolidated review, post-BP-2

---

## Purpose

The Procurement Engine replaces narrative BOM lines with
fully-specified procurement records. Every line item must
carry supplier, location, part number, lead time, MOQ,
revision, quotation date, import duty, and shipping cost.
A line without these fields is not a BOM line — it is a
wish.

This is Priority 4 because cost claims without procurement
data are unfalsifiable. A "unit cost: $11,845" claim with no
supplier, no quote, and no date cannot be verified or
falsified — it cannot even be re-checked when reality
changes.

---

## Schema

```typescript
interface ProcurementRecord {
    id: string                              // PR-XXX
    bomLineId: string                       // BL-XXX from BOM
    componentId: string                     // CMP-XXX from COMPONENT_ENGINE
    supplier: {
        name: string                        // legal entity name
        location: string                    // city, country
        supplierQualification: "ISO9001" | "IATF16949" | "ISO14001" | "NONE_KNOWN"
        supplierTier: 1 | 2 | 3 | 4         // tier-1 = direct, tier-2 = sub-tier, etc.
    }
    part: {
        partNumber: string                  // supplier's part number
        revision: string                    // revision letter/number
        description: string                 // from supplier datasheet
        datasheetUrl: string                // direct link or path
    }
    quotation: {
        unitPriceUSD: number
        currency: string                    // ISO 4217
        quotationDate: string               // ISO 8601 — when the quote was obtained
        quotationValidUntil: string          // ISO 8601 — when the quote expires
        quotationDocument: string            // path to the quote PDF / email
        minimumOrderQuantity: number         // MOQ
        leadTimeDays: number                // from PO to dock
        incoterm: string                    // "FOB Shanghai", "DDP Mumbai", etc.
    }
    landed: {
        unitPriceUSD: number                // EXW unit price + duty + shipping
        importDutyPercent: number
        shippingCostUSD: number             // per-unit amortized
        shippingCostBasis: string           // "air freight 500kg", "sea 40ft container share"
        exchangeRateDate?: string           // ISO 8601 — if currency conversion applied
    }
    alternatives: string[]                  // PR-XXX IDs of alternative procurement records
    status: "PASS" | "PASS_WITH_CONDITIONS" | "MARGINAL" | "BLOCKED" | "REJECTED"
    evidenceLineageIds: string[]            // EV-XXX (P1)
    retractionId?: string                    // if this record retracts a prior narrative BOM line (P7)
}
```

---

## Required field rules

1. **Every BOM line has a ProcurementRecord.** A BOM line
   without a PR-XXX reference is a narrative line, not a
   procurement record. Narrative lines are forbidden in
   PRODUCTION packages (Law 29d).

2. **Every quotation has a date.** A price without a quotation
   date is untestable — it could be from 2018 or yesterday.
   The date determines the decay trigger (Principle 10):
   quotes older than 90 days are marked `STALE`.

3. **Every quotation has an expiry.** A quotation never lasts
   forever. The `quotationValidUntil` field is required. If
   the supplier did not state an expiry, the engine records
   `quotationValidUntil = quotationDate + 30 days` and marks
   the record `STATUS: PASS_WITH_CONDITIONS` with the
   condition "expiry assumed."

4. **Lead time includes dock-to-warehouse.** "Lead time" is
   from PO to the moment the part is available in the
   assembly facility. Supplier-side lead time only is
   forbidden.

5. **Landed cost is computed, not entered.** `landed.unitPriceUSD`
   must equal `quotation.unitPriceUSD × (1 + importDutyPercent) +
   shippingCostUSD`. The engine recomputes this and rejects
   mismatches.

6. **Every record has at least one alternative.** Per Law 5
    ("every recommendation requires alternatives") and Principle
    2 of ENGINEERING_PRINCIPLES.md. A component with no
    alternative supplier is a single point of failure and
    must be flagged `STATUS: MARGINAL` at best.

7. **Supplier qualification is required.** A supplier without
   ISO9001 or IATF16949 cannot supply safety-critical
   components. The `supplierQualification` field must be
   populated; `NONE_KNOWN` is permitted for non-critical
   components only.

---

## Staleness and decay

Per Principle 10 ("The world changes; the blueprint must
track it"):

| Quote age | Status | Action |
|---|---|---|
| < 30 days | PASS | None |
| 30-90 days | PASS_WITH_CONDITIONS | Note: "Re-quote before PO" |
| 90-180 days | MARGINAL | Re-quote before commitment |
| > 180 days | BLOCKED | Quote is stale; cannot be used in a PRODUCTION package |

Stale quotes in EVALUATION packages are tolerated but flagged.
Stale quotes in PRODUCTION packages are forbidden.

---

## Example procurement record

```
PR-001: LFP cell, EVE LF280K

  supplier:
    name: EVE Energy Co., Ltd.
    location: Huizhou, Guangdong, China
    supplierQualification: IATF16949
    supplierTier: 1

  part:
    partNumber: LF280K
    revision: V3
    description: "280Ah LFP prismatic cell, 3.2V nominal"
    datasheetUrl: "https://evebattery.com/lf280k-v3.pdf"

  quotation:
    unitPriceUSD: 89.00
    currency: USD
    quotationDate: 2024-07-15
    quotationValidUntil: 2024-10-15
    quotationDocument: "evidence/quotes/eve-lf280k-2024-07-15.pdf"
    minimumOrderQuantity: 1000
    leadTimeDays: 75 (incl. dock-to-warehouse, sea freight)
    incoterm: FOB Shenzhen

  landed:
    unitPriceUSD: 89.00 × 1.05 + 1.20 = 94.65
    importDutyPercent: 5%
    shippingCostUSD: 1.20 (sea, 40ft container, 12,000 cells amortized)
    shippingCostBasis: "sea 40ft Shenzhen→Mumbai, 35-day transit, 12k cell share"

  alternatives: [PR-002 (CATL), PR-003 (REPT)]
  status: PASS
  evidenceLineageIds: [EV-301, EV-302]
```

---

## What this engine does NOT do

- It does not negotiate prices. That is a human (or human-led)
  activity.
- It does not place purchase orders. It produces the
  specification that the PO is written against.
- It does not validate supplier quality. That is supplier
  engineering — but the engine REQUIRES the qualification
  be recorded so the gap is visible.

---

## Pre-stated falsifier (EP-4)

**Claim:** Every BOM line in a PRODUCTION package can be
resolved to a ProcurementRecord with all required fields.

**Falsifier:** A BOM line in a PRODUCTION package that has
no supplier, no quotation, or no landed cost — i.e., the
component is unspecified at the moment of commitment. Such
lines must be marked `STATUS: BLOCKED` and the package
cannot ship.

**Status:** PENDING. Engine specified; implementation awaits
AEP Gate 1 for the engine itself.
