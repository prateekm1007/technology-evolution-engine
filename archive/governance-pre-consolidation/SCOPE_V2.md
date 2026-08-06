# SCOPE_V2 — Phase 9 Post-Stress-Test Scope

**Status:** constitutional document (honest scope after stress tests).
**Location:** repo root.
**Phase:** 9 post-stress-test (per CEO Instruction 1).

> Before: electrochemical energy storage
> After: lithium-ion intercalation systems
> That is not a retreat. That is increased precision.
> — CEO directive, Phase 9

This document redefines the model's scope based on the Phase 9
stress test results. 4 of 5 assumptions failed, revealing that the
model's actual coverage is narrower than originally claimed.

---

## 1. What the model covers

**Li-ion intercalation battery systems** — specifically:

- Lithium-ion cells using intercalation chemistry (graphite anode,
  LFP/NCM/NCA cathode, liquid or solid electrolyte)
- Battery management systems (monitoring, balancing, safety)
- Thermal management for Li-ion cells
- Electrode manufacturing (coating, assembly) for Li-ion
- Charging systems (including fast charging) for Li-ion
- Regulations governing Li-ion transport and safety (UN38.3, IEC 62133)

### Capabilities covered (10)

ELECTROCHEMICAL_ENERGY_STORAGE, ION_TRANSPORT, INTERCALATION,
ELECTRON_COLLECTION, FAST_CHARGING, THERMAL_MANAGEMENT,
STATE_OF_CHARGE_MONITORING, SAFETY_PROTECTION, ELECTRODE_COATING,
CELL_ASSEMBLY

### Constraints covered (5)

THEORETICAL_ENERGY_DENSITY_LIMIT, THERMAL_RUNAWAY_THRESHOLD,
COST_PER_KWH_THRESHOLD, UN38_3_SHIPPING_SAFETY,
IEC_62133_SAFETY_STANDARD

---

## 2. What the model does NOT cover

- **Flow batteries** (redox, vanadium) — different mechanism (no
  intercalation; uses dissolved redox species)
- **Lead-acid batteries** — different mechanism (no intercalation)
- **Sodium-ion batteries** — different ion (Na⁺ not Li⁺); different
  electrode materials
- **Lithium-sulfur** — conversion reaction, not intercalation
- **Lithium-air** — conversion reaction, not intercalation
- **Supercapacitors** — electrostatic storage, not electrochemical
- **Fuel cells** — energy conversion, not storage
- **Battery recycling** — RECYCLING capability was dropped in scope
  reduction (FAIL-005)
- **Grid-scale deployment** — GRID_INTERCONNECTION capability was
  dropped (FAIL-005)
- **Manufacturing defects and quality control** — manufacturing
  constraints were dropped (FAIL-008); the Note 7 failure cannot
  be explained by this model

---

## 3. Known exceptions

| Exception | What it means | Which assumption/principle |
|---|---|---|
| Pre-1991: lead-acid dominant | REQUIRES INTERCALATION (EDGE-026) is false before Li-ion commercialization | A-003 (failed), P-002 (scope: Li-ion only) |
| Passive safety devices (fuses, PTC, CID) | SAFETY_PROTECTION REQUIRES STATE_OF_CHARGE_MONITORING (EDGE-030) is too broad — passive safety doesn't require monitoring | P-006 (scope: active safety only) |
| Lab-scale coin cells | CELL_ASSEMBLY REQUIRES ELECTRODE_COATING (EDGE-029) may not hold — lab cells use pressed powder, not coated electrodes | P-005 (scope: commercial only) |
| Cost threshold changes over time | COST_PER_KWH_THRESHOLD cannot be applied at T=1995 ($3000/kWh) without TemporalState | P-009 (needs temporal data) |

---

## 4. Known blind spots

- **Manufacturing constraints:** separator integrity, dry electrode
  yield, solid electrolyte densification — all dropped. The model
  cannot predict manufacturing-related failures (FAIL-008).
- **Supply chain:** material scarcity (lithium, cobalt, nickel) was
  a constraint in the original 10 but was dropped in scope reduction.
  The model cannot predict supply-chain-driven changes.
- **Non-Li-ion chemistries:** any prediction about sodium-ion, Li-S,
  Li-air, or flow batteries is outside the model's scope.
- **Scale:** the model is built from 5 patents. It cannot predict
  at industry scale.
- **Temporal dynamics:** the model has TemporalState fields but no
  historical data populated. The backtest cannot run without temporal
  data.

---

## 5. Confidence level

**M1 — Structured observations (approaching M2).**

Per the model maturity framework (MODEL_MATURITY.md):

- M0 (Hypothesis): passed — the CAPABILITY_MODEL is more than a
  hypothesis; it has structure.
- M1 (Structured observations): current state — the model has
  nodes, edges, evidence, justifications, and principles. It is
  structured. But predictions have not been tested against outcomes.
- M2 (Reproducible evidence): approaching — the model is
  deterministic and reproducible, but the frozen-time backtest has
  not been run.
- M3-M5: not yet achieved.

**Overall confidence in the model's current scope:** MODERATE.

The model honestly describes Li-ion intercalation systems with
evidence-backed edges and scoped principles. It does NOT honestly
describe all electrochemical energy storage. The scope reduction
from "electrochemical energy storage" to "Li-ion intercalation
systems" is the single most important output of the Phase 9
stress tests.
