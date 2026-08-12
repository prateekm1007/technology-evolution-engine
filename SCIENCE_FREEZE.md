# SCIENCE FREEZE

**Status:** ACTIVE — enforced by CI
**Date:** 2026-08-13
**Authority:** CTO Directive (Phase 0/1/2 ONLY) + Scientific Audit Q14–Q20 (verdict B — Simplify radically)

---

## 1. What Is Frozen

No new discovery architecture may be built, merged, or deployed until a prospective sealed experiment (PSCD-1 / AINT-1) produces a positive result showing A2 > A1 by a pre-registered margin δ.

## 2. Prohibited Work (Until Phase 3 Pass)

The following are **prohibited** until a prospective sealed experiment produces a positive result:

- New `discovery_engine_v5+`
- Temporal reasoning module
- Negative-knowledge graph
- New combination modes
- Patent discovery integration
- GLiREL replacement or new relation extractor
- New invention compiler
- New scoring dimensions or scorer logic
- Funding/value simulators
- Product/UI work
- New "world-class" scorecards
- Another retrospective famous-discovery benchmark
- Adjudication engine V9+ (V1–V8.1 reached diminishing returns)

## 3. CI Enforcement

CI must **FAIL** if a PR modifies any of the following paths, unless the PR is explicitly tagged `phase-3-experiment`:

```
discovery_fabric/discovery_modes/*
invention_compiler/*
discovery_fabric/evaluation/discovery_value/*
discovery_fabric/evaluation/funding/*
patent_discovery/*
discovery_fabric/dsb_v1/scorer.py
discovery_fabric/dsb_v1/cases/*
discovery_fabric/dsb_v1/receipts/*
discovery_fabric/dsb_v1/scores/*
```

## 4. What Is Permitted

- Phase 0: Quarantine of historical artifacts (move to `cemetery/`, flag `INVALID_AS_EVIDENCE`)
- Phase 1: Truth substrate (corpus verification, retrieval snapshot, prediction schema, sealed outcomes)
- Phase 2: A0/A1 baseline runners (LLM-only and LLM+retrieval, no Fabric)
- PSCD-1 pre-registration and dry-run with fabricated outcomes
- Bug fixes to existing frozen artifacts (with explicit review)
- Governance/honesty corrections (e.g., fixing false gate states)

## 5. Evidence Classes (Never Collapsed)

```
MACHINE_RESULT
AI_CTO_ADJUDICATION
HUMAN_EXPERT_ADJUDICATION
EXTERNAL_EXPERIMENTAL_CONFIRMATION
```

These are separate evidence tiers. AI_CTO_ADJUDICATION is NOT HUMAN_EXPERT_ADJUDICATION. Machine results are NOT human validation. Never collapse them.

## 6. Gate States (Corrected)

```
E5_HUMAN_ADJUDICATION = NOT_PERFORMED
DSB_SCIENTIFICALLY_CLOSED = FALSE
NORTH_STAR = UNPROVEN
```

A regression test enforces: `overall_pass` cannot be `true` while any required gate is pending.

## 7. AINT-1 Kill Switch

```
if A2 - A1 <= 0:
    FABRIC_STATUS = RETIRED
```

If A2 does not beat A1 prospectively on the primary endpoint, the Fabric is retired. No "maybe another module would help." No "the scorer was imperfect." No "let's add temporal reasoning."

## 8. Architecture as Hypothesis, Not Default

```
A1 = default (LLM + retrieval)
A2 = optional hypothesis (Fabric)
```

Not:
```
Fabric = product
LLM = control
```

The audit supports this reversal. The current data gives no reason to believe the extra representation is useful.

## 9. Primary Endpoint

The primary endpoint is **NOT**: plausibility, mechanism quality, LLM judge score, similarity, historical recovery, semantic overlap, "interestingness," or expert enthusiasm.

It **IS**:

> **retrieval-negative + non-entailed + later-confirmed**

with a pre-registered quantitative tolerance.

## 10. No Invention System Yet

The order is:
```
DISCOVERY → prospective confirmation → independent novelty → external validation → invention
```

Not:
```
discovery hypothesis → invention module → product → hope
```

---

## Gates (Evidence-Based, Not Time-Based)

```
TRUTH SUBSTRATE PASS
        ↓
A0/A1 RUNNABLE
        ↓
PSCD SEALED
        ↓
DRY RUN PASS
        ↓
A2 AUTHORIZED
        ↓
PROSPECTIVE RESULT
        ↓
ARCHITECTURE LIVES OR DIES
```

Time is not the gate. Evidence is.

---

**This freeze is constitutional. It supersedes any prior plan that adds Fabric modules before a prospective win.**
