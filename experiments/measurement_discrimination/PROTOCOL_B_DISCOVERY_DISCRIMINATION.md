# Protocol B — Actual Discovery Discrimination

**Status:** DRAFT (not yet designed in detail)
**Date:** 2026-08-09
**Supersedes:** PREREGISTRATION_SUPERSEDED_DRAFT.md (which was invalid for relationship discrimination)
**Claim limit:** DISCOVERY_DISCRIMINATION (if it passes)

---

## Central Question

> **Can the discovery system identify a cross-domain relationship from source information when the gold bridge is NOT supplied as the answer?**

This is the experiment relevant to the North Star. It tests whether the engine can generate/identify a mechanism connecting two domains without being handed the answer.

---

## Key Design Principle

The gold bridge must NOT be supplied as input to the scorer.

The system must:
1. Receive source-domain information (documents, mechanisms, entities)
2. Generate candidate mechanisms/relationships
3. Have its output evaluated by an independent procedure

The frozen `_bridge_matches()` function may be used as part of the scoring pipeline, but ONLY if the candidate is system-generated (not the gold bridge itself).

---

## Relationship to Existing Infrastructure

### SCIENTIFIC_GATE_2_PROTOCOL.md (v1.2 FROZEN)

Gate 2 already defines this type of experiment:
- Gate A: engine generates a proposal that cannot be recovered from inputs
- Gate B: independent literature search for novelty
- Gate C: blinded expert validation

Protocol B should be designed as a **measurement-discrimination prerequisite** to Gate 2, not a replacement for it. If Protocol B shows the system cannot discriminate, Gate 2 is premature.

### DXP-005 (PAUSED)

DXP-005 tested H-GEN-1 (mechanism preservation through abstraction). It is paused because:
1. The ZAI provider is unavailable
2. The discrimination study (Protocol A then B) is a prerequisite
3. Amendment 14 (Scientific Visibility Boundary) prohibits resuming DXP-005 until the discrimination study produces DISCRIMINATIVE

### Frozen Matcher

The frozen `_bridge_matches()` function scores string similarity. In Protocol B, the system's OUTPUT (not the gold bridge) is compared against the gold bridge using the frozen matcher. The key difference from Protocol A:

```text
Protocol A: candidate = gold.bridge (TPR=1.0 by construction)
Protocol B: candidate = system_output (TPR is NOT 1.0 — system might fail)
```

---

## Required Design Elements (To Be Specified)

Before Protocol B can be frozen, the following must be specified:

1. **System input format:** What source information does the system receive?
2. **System output format:** What must the system produce? (relationship + mechanism)
3. **Candidate generation procedure:** How does the system generate proposals?
4. **Scoring procedure:** How is the system's output compared to the gold bridge?
   - Can use `_bridge_matches()` if the candidate is system-generated
   - May also require semantic evaluation (Gate A/B/C from Gate 2 protocol)
5. **True cases:** Same 20 GOLD_DISCOVERIES, but the system receives source documents, NOT the bridge
6. **Null cases:** Must be designed to test whether the system's discrimination is above chance
7. **Primary metric:** Δ = TPR_system − FPR_null (where TPR_system is NOT 1.0 by construction)
8. **Threshold:** Must be preregistered before results
9. **Power justification:** Must demonstrate N is sufficient or classify as exploratory
10. **Decision rule:** Exhaustive partition, every outcome maps to exactly one state

---

## Prerequisites

Protocol B may be designed and preregistered ONLY if:
1. Protocol A produces `LEXICALLY_SEPARABLE` (the matcher can at least distinguish gold from non-gold strings)
2. The system can receive source documents and generate candidate mechanisms (this requires the discovery engine pipeline to be operational)
3. The provider (ZAI) is available for LLM-based stages (if Protocol B uses LLM stages)
4. P46 served-instrument verification is satisfied

---

## What This Protocol Does NOT Authorize

- Executing Protocol B before Protocol A passes
- Modifying the frozen matcher
- Modifying the gold set
- Making any discovery claim before execution completes
- Bypassing the epistemic gate (Phase 6)
- Bypassing the F1 freeze (Phase 7)

---

## Status

```
DRAFT — awaiting Protocol A result and system readiness
```
