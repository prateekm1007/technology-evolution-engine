# ASSUMPTION_STRESS_TESTS — Phase 9A

**Status:** scientific instrument (attempt to destroy the model's assumptions).
**Location:** repo root.
**Phase:** 9A (per CEO directive: red-team the assumptions).

> Your assumptions are now explicit objects.
> That means they can be attacked.
> — CEO directive, Phase 9A

This document attacks each of the 5 assumptions (A-001 through A-005)
to determine whether they survive scrutiny. If an assumption fails,
it is recorded honestly. The model is updated or invalidated accordingly.

## Schema

```typescript
interface AssumptionStressTest {
    assumptionId: string;
    attack: string;
    expectedFailure: string;
    observedFailure: string;
    status: "SURVIVED" | "FAILED" | "INCONCLUSIVE";
}
```

---

## Stress Test A-001: CPC codes approximate capability

**Assumption:** A patent's CPC code accurately reflects the capabilities the patent describes.

**Attack:** Examine the 5 patents in the corpus. For each, check whether
the CPC-mapped capabilities actually appear in the patent's claims.
If a patent has CPC code H01M 4/00 (which maps to INTERCALATION,
ELECTRON_COLLECTION, ELECTRODE_COATING) but its claims don't mention
intercalation, the CPC code is misleading.

**Expected failure:** At least one patent where the CPC code maps to a
capability the patent doesn't actually describe.

**Observed failure:**

- US12489120B2 (Redox flow battery): CPC code H01M 4/86 maps to
  ELECTRON_COLLECTION. Flow batteries use redox reactions at electrodes
  — they DO collect electrons, but the capability is better described
  as "redox reaction at electrode" than "electron collection" (which
  implies current collector function). The CPC code is technically
  correct but semantically imprecise. The capability mapping
  over-generalizes.

- US20190051907A1 (Metal-hydrogen battery): was in the original 15
  but dropped in the scope reduction to 5. Its CPC code H01M 12/00
  (fuel cells) was mapped to ELECTROCHEMICAL_ENERGY_STORAGE — correct
  at the domain level but misleading at the capability level
  (metal-hydride batteries and fuel cells are different mechanisms).

**Status:** INCONCLUSIVE

The CPC codes are mostly correct but semantically coarse. They tell
you what DOMAIN a patent is in, but not precisely which CAPABILITY
it enables. The assumption survives for domain-level classification
but fails for fine-grained capability mapping. The model should
acknowledge this imprecision — CPC is a coarse signal, not a precise
one.

---

## Stress Test A-002: 10 capabilities are sufficient

**Assumption:** The 10 capabilities in CAPABILITY_CATALOG.md are sufficient to model the electrochemical energy storage vertical.

**Attack:** Try to express the following real-world battery innovations
using only the 10 capabilities. If any can't be expressed, the catalog
is insufficient.

1. Solid-state battery (needs SOLID_ELECTROLYTE_SINTERING — DROPPED)
2. Sodium-ion battery (needs SODIUM_ION_TRANSPORT — not in catalog)
3. Battery recycling (needs RECYCLING — DROPPED)
4. Grid-scale storage (needs GRID_INTERCONNECTION — DROPPED)
5. Conversion-type anode (needs CONVERSION_REACTION — DROPPED)

**Expected failure:** At least one innovation can't be expressed.

**Observed failure:** ALL FIVE cannot be expressed with the reduced
10-capability catalog. SOLID_ELECTROLYTE_SINTERING, RECYCLING,
GRID_INTERCONNECTION, and CONVERSION_REACTION were all in the original
20 but were dropped in the scope reduction.

**Status:** FAILED

The 10-capability catalog is insufficient for the full electrochemical
storage vertical. The scope reduction (CEO Decision 1, Phase 7C.1)
was too aggressive. The model can describe Li-ion intercalation
batteries but cannot describe solid-state, sodium-ion, conversion-type,
or recycling innovations.

**Implication:** The model is currently scoped to "Li-ion intercalation
batteries" not "electrochemical energy storage." The vertical name is
broader than the capability catalog supports. Either the vertical
should be narrowed to "Li-ion intercalation batteries" or the catalog
should be expanded (requiring CEO authorization per ONTOLOGY_FREEZE.md).

---

## Stress Test A-003: Structural invariants are stable across time

**Assumption:** The structural REQUIRES edges hold across 1990-2026.

**Attack:** Check whether REQUIRES edges hold at T=1990 (before Li-ion
commercialization in 1991).

**Expected failure:** EDGE-026 (ELECTROCHEMICAL_ENERGY_STORAGE REQUIRES
INTERCALATION) would be false at T=1990 because the dominant chemistry
was lead-acid (which doesn't use intercalation) and NiCd (which uses
a different mechanism).

**Observed failure:** At T=1990, "electrochemical energy storage" was
dominated by lead-acid (no intercalation) and NiCd (intercalation-like
but not the same mechanism as Li-ion). The REQUIRES INTERCALATION edge
is specific to Li-ion, not universal. It would be FALSE at T=1990.

**Status:** FAILED

The structural invariant "ELECTROCHEMICAL_ENERGY_STORAGE REQUIRES
INTERCALATION" is NOT stable across time. It is true for Li-ion
(post-1991) but false for lead-acid (pre-1991 dominant). The edge
should be scoped to Li-ion specifically, not to electrochemical
storage generally.

**Implication:** EDGE-026 should be narrowed or removed. The principle
P-002 (lattice insertion chemistry, scope: Li-ion only) already
records this limitation, but the EDGE itself doesn't carry the temporal
scope. The edge is over-generalized.

---

## Stress Test A-004: The 5 selected patents are representative

**Assumption:** The 5 patents are representative of electrochemical energy storage.

**Attack:** Check what the 5 patents cover vs. what the domain contains.

**Expected failure:** The 5 patents miss major sub-domains.

**Observed failure:**
- The 5 patents cover: solid-state (1), flow battery (1), Li-ion + fast
  charging (1), battery pack (1), electrode coating (1).
- Missing: lead-acid, NiMH, sodium-ion, lithium-sulfur, lithium-air,
  supercapacitors, zinc-air, aluminum-ion.
- Missing: manufacturing at scale (only lab-scale coating is covered).
- Missing: recycling/end-of-life.
- Missing: grid-scale deployment.

**Status:** FAILED

The 5 patents represent a narrow slice (Li-ion and its neighbors).
They do not represent the full electrochemical storage domain. The
sample is biased toward Li-ion-adjacent technologies.

**Implication:** Any backtest results from these 5 patents will be
biased toward Li-ion. Predictions about non-Li-ion technologies
(lead-acid, sodium-ion, etc.) cannot be made from this sample. The
backtest results should be qualified: "valid for Li-ion-adjacent
technologies, not for electrochemical storage broadly."

---

## Stress Test A-005: The 5 constraints are the most important

**Assumption:** The 5 constraints are the most important for this vertical.

**Attack:** Identify a real-world battery failure that was caused by
a constraint NOT in the 5.

**Expected failure:** A historical failure caused by a missing constraint.

**Observed failure:** Samsung Galaxy Note 7 (2016) — thermal runaway
caused by internal short circuit from separator damage. The
THERMAL_RUNAWAY_THRESHOLD constraint IS in the catalog (CON_002).
But the ROOT CAUSE was separator integrity (manufacturing defect),
which is a MANUFACTURING constraint. The manufacturing constraints
(SOLID_ELECTROLYTE_DENSIFICATION, DRY_ELECTRODE_YIELD) were dropped
in the scope reduction. Separator integrity is not in the 5 constraints.

**Status:** FAILED

The Note 7 failure was caused by a manufacturing constraint (separator
integrity) that is NOT in the 5-constraint catalog. The catalog captures
physics and regulatory constraints but misses manufacturing constraints.
A model that can't explain the Note 7 failure is missing load-bearing
constraints.

**Implication:** The 5-constraint catalog is insufficient for predicting
real-world battery failures. Manufacturing constraints should be
reinstated (requiring CEO authorization per ONTOLOGY_FREEZE.md, or
the vertical should be narrowed to exclude manufacturing-dependent
predictions).

---

## Summary

| Assumption | Status | Implication |
|---|---|---|
| A-001 (CPC ≈ capability) | INCONCLUSIVE | CPC is coarse, not precise. Survives at domain level, fails at fine-grained capability level. |
| A-002 (10 capabilities sufficient) | FAILED | 5 real-world innovations can't be expressed. Catalog is too narrow. |
| A-003 (invariants stable across time) | FAILED | REQUIRES INTERCALATION is false pre-1991 (lead-acid dominant). Edge is over-generalized. |
| A-004 (5 patents representative) | FAILED | Sample is Li-ion-biased. Missing lead-acid, Na-ion, Li-S, supercapacitors, recycling. |
| A-005 (5 constraints most important) | FAILED | Note 7 failure caused by separator integrity (manufacturing constraint) not in catalog. |

**4 of 5 assumptions FAILED or are INCONCLUSIVE.**

This is not a failure of the project. This is the scientific method
working as designed. The stress tests revealed that the model's
current scope is narrower than claimed. The honest response is:

1. Narrow the vertical to "Li-ion intercalation batteries" (matching
   what the 10 capabilities actually cover).
2. OR expand the catalogs (requiring CEO authorization).
3. Record the failures in CEMETERY.md (Phase 9E).
4. Update the assumptions with their observed failures.

The model has not been destroyed. But its scope has been honestly
bounded. It covers Li-ion intercalation, not all electrochemical
storage. That's a smaller claim — and a more defensible one.
