# ECONOMIC_ENGINE

**Status:** Phase 16A Deliverable 6.
**Location:** repo root.
**Phase:** 16A.

---

## Purpose

The Economic Engine produces the economics model for an idea: how
much capital is needed, what the unit cost is, what the operating
cost is, what revenue is expected, and how long until break-even.

---

## Schema

```typescript
interface EconomicsModel {
    capitalRequirement: number
    unitCost: number
    operatingCost: number
    expectedRevenue: number
    breakEvenPeriod: number
}
```

### Field semantics

| Field | Type | Required | Meaning |
|---|---|---|---|
| `capitalRequirement` | number (USD) | yes | Total capital needed to develop and deploy. Includes R&D, manufacturing setup, initial inventory. |
| `unitCost` | number (USD) | yes | Cost to produce one unit at scale. Includes materials, labor, manufacturing overhead. |
| `operatingCost` | number (USD/year) | yes | Annual operating cost per unit. Includes maintenance, energy, support. |
| `expectedRevenue` | number (USD/year) | yes | Expected annual revenue per unit. Based on market size and willingness-to-pay. |
| `breakEvenPeriod` | number (years) | yes | Years until cumulative revenue exceeds cumulative cost. `breakEven = capitalRequirement / (expectedRevenue - operatingCost)`. |

---

## Example

### Autonomous farming robot

```json
{
  "capitalRequirement": 15000000,
  "unitCost": 45000,
  "operatingCost": 5000,
  "expectedRevenue": 12000,
  "breakEvenPeriod": 2.1
}
```

Interpretation:
- $15M capital to develop and set up manufacturing.
- $45K per robot at scale.
- $5K/year operating cost (maintenance, energy, software updates).
- $12K/year revenue (leasing model: $1K/month per robot).
- Break-even: $15M / ($12K - $5K) = $15M / $7K = 2143 units. At 1000 units/year, break-even in 2.1 years.

---

## Economic analysis protocol

1. **Estimate capitalRequirement.** Sum: R&D cost + manufacturing setup + initial inventory + regulatory compliance.
2. **Estimate unitCost.** Sum: materials + labor + manufacturing overhead. Apply Wright's Law if scaling is expected.
3. **Estimate operatingCost.** Sum: maintenance + energy + support + software updates.
4. **Estimate expectedRevenue.** Market size × market share × unit price. Consider leasing vs purchase models.
5. **Compute breakEvenPeriod.** `capitalRequirement / (expectedRevenue - operatingCost)` per unit, divided by units per year.
6. **Flag negative unit economics.** If `expectedRevenue < operatingCost`, the idea is not economically viable without subsidies or model changes.

---

## Relationship to constraint engine

The Economic Engine feeds the Constraint Engine:

- If `capitalRequirement > available capital` → ECONOMICS constraint (severity based on gap).
- If `breakEvenPeriod > market window` → TIME constraint.
- If `unitCost > willingness-to-pay` → ECONOMICS constraint (severity 1.0 — absolute blocker).

---

## Relationship to frozen formula

The frozen formula does not use economic_state directly. The Phase
12 ablation showed cost_bonus was redundant (correlated with
velocity). However, the Economic Engine is NOT the frozen formula's
cost_bonus — it is a full economic model used by the Blueprint
Engine, not by the reachability instruments.

The distinction: the frozen formula estimates LANDSCAPE
susceptibility. The Economic Engine estimates IDEA economics. They
operate at different levels.

---

## What this engine does NOT do

- It does not forecast market size. Market size is an input (from Layer 0).
- It does not model competition. Competitive dynamics are future work.
- It does not handle multi-product portfolios. One idea = one EconomicsModel.
- It does not modify the frozen formula.

---

## Pre-stated falsifier (EP-4)

**Claim:** The 5-field EconomicsModel captures all economic information needed to evaluate an idea's viability.

**Falsifier:** An idea whose economics cannot be evaluated from these 5 fields — e.g., an idea that requires modeling subscription tiers, advertising revenue, or multi-sided market dynamics.

**Status:** PENDING. No economics models have been built (no implementation).
