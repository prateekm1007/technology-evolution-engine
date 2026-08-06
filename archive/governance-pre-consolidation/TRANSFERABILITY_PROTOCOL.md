# TRANSFERABILITY_PROTOCOL — Phase 8E

**Status:** constitutional document (transferability testing).
**Location:** repo root.
**Phase:** 8E.

> A principle that only works once is not a principle.
> — CEO directive, Phase 8E

This document defines the transferability test: whether the
CAPABILITY_MODEL's principles and methods survive when applied to
a different domain.

---

## 1. Why transferability matters

A model that works only on electrochemical energy storage is an
electrochemistry tool, not an invention engine. The CEO's north
star is:

```text
available capabilities + removed constraints + institutions + economics + time = reachable possibilities
```

This equation is domain-agnostic. If it only works in one domain,
the model hasn't captured the general principle — it's overfit to
one vertical.

---

## 2. The transferability ladder

```text
electrochemical storage (current vertical)
        ↓
photovoltaics (first transfer test)
        ↓
semiconductors (second transfer test)
```

### Why this ladder

- **Electrochemical storage → photovoltaics:** both involve
  materials science, manufacturing processes, and cost curves. But
  photovoltaics has different capabilities (light absorption, charge
  separation, grid interconnection) and different constraints
  (Shockley-Queisser limit, panel efficiency, silicon supply).
  Transfer here tests whether the MODEL (capability + constraint +
  evidence) transfers, even if the specific capabilities and
  constraints change.

- **Photovoltaics → semiconductors:** a further generalization.
  Semiconductors involve fab processes, lithography, and different
  economics. Transfer here tests whether the principles (Joule
  heating, manufacturing dependency) and the method (CPC mapping,
  evidence-backed edges, falsifiable assumptions) survive a
  fundamentally different domain.

---

## 3. What transfers and what doesn't

### What should transfer (if the model is general)

- The **method**: CPC mapping, evidence-backed edges, EdgeJustification
  schema, the four-layer architecture.
- The **structural edge types**: REQUIRES, CONSTRAINS, EMBODIED_IN,
  REGULATED_BY.
- The **principles** that are physics-general (P-001 charge
  conservation, P-004 Joule heating, P-007 thermodynamic limits).
- The **validation framework**: VALIDATION_CONSTITUTION,
  BACKTEST_PROTOCOL, ERROR_TAXONOMY, COUNTERFACTUAL_PROTOCOL,
  ADVERSARIAL_REVIEW_PROTOCOL.

### What should NOT transfer (domain-specific)

- The specific **capabilities** (ELECTROCHEMICAL_ENERGY_STORAGE →
  LIGHT_ABSORPTION for photovoltaics).
- The specific **constraints** (THERMAL_RUNAWAY_THRESHOLD →
  SHOCKLEY_QUEISSER_LIMIT for photovoltaics).
- The specific **principles** that are domain-specific (P-002 lattice
  insertion, P-008 exothermic decomposition).
- The specific **CPC codes** (H01M → H01L for semiconductors).

### What this tests

If the METHOD transfers but the SPECIFICS don't, the model has
captured a general principle. If neither transfers, the model is
overfit to electrochemical storage and the architectural pivot
hasn't paid off.

---

## 4. The transferability test procedure

```text
Step 1: Select the second vertical (photovoltaics).
Step 2: Ingest 5 patents with CPC codes (H01L for PV).
Step 3: Map CPC codes to capabilities (new capability catalog).
Step 4: Create evidence-backed edges (same EdgeJustification schema).
Step 5: Identify which principles transfer (in scope) and which don't.
Step 6: Run the frozen-time backtest on the second vertical.
Step 7: Compare precision/recall to the first vertical.
Step 8: Adversarial review: did the method work without modification?
```

### Success criterion

The METHOD (evidence-backed edges, EdgeJustification, falsifiable
assumptions, scoped principles) works in the second vertical
WITHOUT modification. The SPECIFICS (capabilities, constraints,
CPC codes) are different but follow the same schema.

### Failure criterion

The method requires modification to work in the second vertical.
The principles don't transfer. The evidence structure doesn't
capture the domain. The model is overfit.

---

## 5. What this document does NOT do

- It does NOT authorize a second vertical yet (ONTOLOGY_FREEZE.md
  caps at 1 vertical). Adding a second vertical requires explicit
  CEO authorization.
- It defines the TEST: what would be checked IF a second vertical
  were authorized.
- It records the CEO's instruction: "A principle that only works
  once is not a principle."
