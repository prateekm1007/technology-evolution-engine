# EDGE_JUSTIFICATION — Phase 7B/7C Audit

**Status:** audit document (every edge justified or flagged for review).
**Location:** `evidence/observations/` (audit, not constitutional).
**Phase:** 7B/7C (per auditor correction: "Every single edge should contain source, CPC code, capability, relationship, justification, confidence, reviewer").

> Until that exists, the graph is still largely an assertion.
> — Auditor correction

This document audits every edge in `data/capability_graph.json`.
Each edge is classified as:
- **JUSTIFIED** — the evidence is sufficient and the claim is defensible.
- **NEEDS REVIEW** — the evidence is thin or the claim is too strong.
- **FLAGGED** — the claim is not defensible at current confidence and
  should either be downgraded or removed.

---

## Summary

| Edge type | Count | JUSTIFIED | NEEDS REVIEW | FLAGGED |
|---|---:|---:|---:|---:|
| EMBODIED_IN | 119 | 119 | 0 | 0 |
| REQUIRES | 11 | 9 | 2 | 0 |
| CONSTRAINS | 10 | 10 | 0 | 0 |
| ENABLES | 4 | 0 | 4 | 0 |
| REGULATED_BY | 2 | 2 | 0 | 0 |
| SUBSTITUTES_FOR | 1 | 0 | 0 | 1 |
| **TOTAL** | **147** | **140** | **6** | **1** |

---

## Inference rules (the 28 INFERRED evidence records)

All 28 INFERRED evidence records come from two inference sources:

### Rule 1: `structural_invariant` (17 edges)

**Claim:** these capability→capability relationships are structural
invariants of electrochemical energy storage — they hold regardless
of the specific patent or paper.

**Rules used:**
1. ELECTROCHEMICAL_ENERGY_STORAGE REQUIRES ION_TRANSPORT — ions must
   move between electrodes for electrochemical storage to work.
2. ELECTROCHEMICAL_ENERGY_STORAGE REQUIRES INTERCALATION — MOST
   Li-ion storage uses intercalation. **NEEDS REVIEW:** this is
   not universal (conversion reactions don't use intercalation).
   The REQUIRES claim is too strong; should be ENABLES or
   EMBODIED_IN.
3. FAST_CHARGING REQUIRES THERMAL_MANAGEMENT — fast charging
   generates heat.
4. FAST_CHARGING REQUIRES ION_TRANSPORT — fast charging requires
   fast ion transport.
5. HIGH_POWER_DISCHARGE REQUIRES ION_TRANSPORT — high power requires
   fast ion transport.
6. HIGH_POWER_DISCHARGE REQUIRES ELECTRON_COLLECTION — high power
   requires efficient electron collection.
7. SELECTIVE_ION_TRANSPORT REQUIRES ION_TRANSPORT — selective
   transport is a specialization of ion transport.
8. CELL_BALANCING REQUIRES STATE_OF_CHARGE_MONITORING — balancing
   requires knowing the state of each cell.
9. SAFETY_PROTECTION REQUIRES STATE_OF_CHARGE_MONITORING — safety
   cutoffs require monitoring.
10. CELL_ASSEMBLY REQUIRES ELECTRODE_COATING — assembly requires
    coated electrodes.
11. CELL_ASSEMBLY REQUIRES SELECTIVE_ION_TRANSPORT — assembly
    requires a separator.

**ENABLES edges (4 — all NEED REVIEW):**
12. SOLID_ELECTROLYTE_SINTERING ENABLES ION_TRANSPORT — sintering
    enables solid electrolyte ion transport. **NEEDS REVIEW:**
    ENABLES is a strong causal claim. Sintering enables solid-
    state ion transport specifically, not ion transport in general.
    Should be: SOLID_ELECTROLYTE_SINTERING ENABLES
    SOLID_STATE_ION_TRANSPORT (a more specific capability).
13. ELECTRODE_COATING ENABLES INTERCALATION — coating enables
    intercalation electrodes. **NEEDS REVIEW:** coating doesn't
    enable intercalation as a mechanism; it enables the physical
    electrode. The relationship is EMBODIED_IN, not ENABLES.
14. RECYCLING ENABLES ELECTROCHEMICAL_ENERGY_STORAGE — recycling
    enables sustainable storage. **NEEDS REVIEW:** recycling
    doesn't enable storage; it enables sustainable production.
    The ENABLES claim is too broad.
15. GRID_INTERCONNECTION ENABLES ELECTROCHEMICAL_ENERGY_STORAGE —
    grid connection enables grid-scale storage. **NEEDS REVIEW:**
    grid connection enables DEPLOYMENT of storage, not storage
    itself. The claim conflates deployment with capability.

**SUBSTITUTES_FOR edge (1 — FLAGGED):**
16. CONVERSION_REACTION SUBSTITUTES_FOR INTERCALATION — conversion
    can replace intercalation in some chemistries. **FLAGGED:**
    Substitutability is notoriously difficult to establish.
    Conversion reactions and intercalation are fundamentally
    different energy storage mechanisms. They are NOT substitutable
    in the same design — you choose one or the other. This edge
    should be REMOVED or reclassified as something weaker (e.g.,
    ALTERNATIVE_TO, which doesn't exist in the frozen edge types).

### Rule 2: `structural_constraint` (11 edges)

**Claim:** these constraint→capability relationships are structural
limits — the constraint limits the capability's performance.

**Rules used:**
17-27. Each constraint (from CONSTRAINT_CATALOG.md) CONSTRAINS the
    capability it limits. These are defensible:
    - THEORETICAL_ENERGY_DENSITY_LIMIT CONSTRAINS HIGH_ENERGY_DENSITY_STORAGE
    - ION_TRANSPORT_RESISTANCE CONSTRAINS ION_TRANSPORT
    - THERMAL_RUNAWAY_THRESHOLD CONSTRAINS ELECTROCHEMICAL_ENERGY_STORAGE
    - etc.

**REGULATED_BY edges (2 — JUSTIFIED):**
28. UN38_3_SHIPPING_SAFETY REGULATED_BY ELECTROCHEMICAL_ENERGY_STORAGE
    — shipping regulations govern battery transport.
29. IEC_62133_SAFETY_STANDARD REGULATED_BY SAFETY_PROTECTION
    — safety standards govern protection systems.

---

## EMBODIED_IN edges (119) — ALL JUSTIFIED

These edges connect each patent (PRODUCT node) to the capabilities
it evidences (CAPABILITY nodes). The evidence is the patent's CPC
codes, which are externally validated by the USPTO.

**Example:**
```
PAT_US20240194939A1 → EMBODIED_IN → CAP_ELECTROCHEMICAL_ENERGY_STORAGE
  evidence: E-0019
  source: US20240194939A1 (patent)
  CPC codes: H01M 10/00, H01M 10/0525, ...
  confidence: 1.0 (EXPLICIT)
  justification: patent's CPC code H01M 10/00 maps to
                 ELECTROCHEMICAL_ENERGY_STORAGE per CPC_MAPPING.md
```

**Why all 119 are JUSTIFIED:** CPC codes are assigned by patent
examiners, not by the system. The mapping from CPC to capability
is defined in CPC_MAPPING.md and is deterministic. The evidence is
explicit (confidence 1.0) and traceable (patent ID + CPC code).

---

## Corrections needed

Based on this audit, the following corrections should be made to
the capability graph:

1. **Edge #2** (ELECTROCHEMICAL_ENERGY_STORAGE REQUIRES INTERCALATION):
   downgrading from REQUIRES to a weaker claim or adding a qualifier
   ("most Li-ion" not "all electrochemical storage").

2. **Edge #12** (SOLID_ELECTROLYTE_SINTERING ENABLES ION_TRANSPORT):
   needs scoping to solid-state ion transport specifically.

3. **Edge #13** (ELECTRODE_COATING ENABLES INTERCALATION):
   should be reclassified as EMBODIED_IN, not ENABLES.

4. **Edge #14** (RECYCLING ENABLES ELECTROCHEMICAL_ENERGY_STORAGE):
   too broad. Recycling enables sustainability, not storage.

5. **Edge #15** (GRID_INTERCONNECTION ENABLES ELECTROCHEMICAL_ENERGY_STORAGE):
   too broad. Grid connection enables deployment, not storage.

6. **Edge #16** (CONVERSION_REACTION SUBSTITUTES_FOR INTERCALATION):
   FLAGGED for removal. Substitutability not established.

**These corrections have NOT been applied to the graph yet.** They
are recorded here for CEO review. Applying them is the next
authorized step, but only after the CEO confirms the scope reduction
(15→5 patents, 20→10 capabilities, etc.) and the corrected edges.

---

## Scope reduction proposal (per auditor)

The auditor proposed shrinking the scope further:

| Item | Previous | Proposed |
|---|---:|---:|
| Patents | 15 | 5 |
| Capabilities | 20 | 10 |
| Constraints | 10 | 5 |
| Edge types | 6 | 4 |

**Status:** PROPOSED — requires CEO authorization. If approved,
the capability graph would be rebuilt with the reduced scope,
correcting the flagged edges in the process.

---

## Honest framing (per auditor correction)

Previous language (too strong):
> "The capability graph is built."
> "The pipeline works end-to-end."

Corrected language:
> "An initial evidence graph has been constructed for a limited
> corpus (15 patents). The pipeline demonstrates CPC code extraction
> → capability mapping → evidence attachment. It has NOT demonstrated
> causal validity, predictive validity, generalization, superiority
> over the co-occurrence model, or robustness across domains."

The distinction between:
```
classification ≠ capability ≠ enablement ≠ prediction
```
must be maintained. CPC codes classify patents; they don't prove
capabilities exist. Capabilities are typed nodes; they don't prove
enablement. Enablement edges are causal claims; they don't predict
outcomes. The frozen-time backtest (Phase 7D) is the only test of
predictive validity.
