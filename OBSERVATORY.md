# OBSERVATORY — Phase 8F

**Status:** constitutional document (the observation process as an object of study).
**Location:** repo root.
**Phase:** 8F.

> You have repeatedly discovered something unexpected:
> the observation process changes the architecture.
> Therefore, the observation process itself must become an object of study.
> — CEO directive, Phase 8F

This document defines the observatory: a systematic record of how
the act of observing the system has changed the system's architecture.

---

## 1. The phenomenon

Throughout this project, the act of measuring, auditing, and
documenting the system has repeatedly changed the architecture:

| Observation event | Architectural consequence |
|---|---|
| Phase 5.D: measured d(shared)/d(total) = 0.00 | Discovered the saturation was structural, not data-driven → triggered the architectural pivot |
| Phase 5.E: classified 140 labels | Discovered 37.5% signal loss → quantified the normalization gap |
| Phase 5.F: compared 3 approaches | Discovered H0 was needed → added the null hypothesis |
| Phase 7 audit: audited 147 edges | Discovered ENABLES and SUBSTITUTES_FOR were too strong → suspended both |
| Phase 7C.1: justified every edge | Discovered evidence ≠ structural → separated edge types |
| Phase 7C.2: separated edge types | Discovered confidence was false precision → switched to ordinal labels |
| Phase 7C.3: added principles + assumptions | Discovered epistemology is part of the architecture |

Each observation didn't just measure the system — it CHANGED the
system. The observation process is not neutral. It is an active
force in the architecture's evolution.

---

## 2. The schema

```typescript
interface ObservationEvent {
    observation: string;          // what was observed
    consequence: string;           // what happened as a result
    architecturalImpact: string;  // how the architecture changed
    confidence: string;            // EXPLICIT | IMPLIED | STRUCTURAL | SPECULATIVE
}
```

---

## 3. The observation events (recorded)

### OE-001: Saturation signature

**Observation:** The convergence score's derivative d(shared_components)/d(total_components) was 0.00 for two consecutive cycles (Phase 5.B, 5.C).

**Consequence:** The system had saturated — not because of insufficient data, but because the primitive (co-occurrence) was wrong.

**Architectural impact:** Triggered the architectural pivot from CO_OCCURRENCE_MODEL to CAPABILITY_MODEL. Changed the objective from "optimize convergence" to "replace the primitive."

**Confidence:** EXPLICIT

### OE-002: 37.5% signal loss

**Observation:** Classification of 140 component labels revealed 37.5% of bridgeable signal was lost to normalization gaps.

**Consequence:** The normalization gap was large enough to justify investigating candidate solutions — but not large enough to justify implementing any specific one without testing.

**Architectural impact:** Led to H0 (null hypothesis), the comparative analysis (Phase 5.F), and the eventual conclusion that the bottleneck was structural, not fixable by normalization.

**Confidence:** EXPLICIT

### OE-003: Edges were too strong

**Observation:** Auditing 147 edges in the v1.0 capability graph revealed that ENABLES and SUBSTITUTES_FOR edges were causal claims without sufficient evidence.

**Consequence:** Both edge types were suspended. The graph was rebuilt with only 4 authorized edge types.

**Architectural impact:** Reduced the edge type count from 6 to 4. Added the CAUSALITY_POLICY.md. Changed the question from "can we build the graph?" to "can we trust the graph?"

**Confidence:** EXPLICIT

### OE-004: Evidence ≠ structural

**Observation:** Evidence edges (from CPC codes) and structural edges (from domain knowledge) were mixed in the same array, conflating observations with model assertions.

**Consequence:** Separated evidence_edges and structural_edges into distinct arrays with distinct schemas.

**Architectural impact:** Added the principle field to structural edges. Created the epistemic layer. Led to the realization that "epistemology is part of the architecture."

**Confidence:** EXPLICIT

### OE-005: Confidence was false precision

**Observation:** Numeric confidence (0.5) appeared quantitative but was actually ordinal.

**Consequence:** Replaced numeric confidence with ordinal labels (EXPLICIT/IMPLIED/STRUCTURAL/SPECULATIVE).

**Architectural impact:** Simplified the confidence model. Made the epistemic status of each edge honest rather than artificially precise.

**Confidence:** EXPLICIT

### OE-006: Epistemology is the architecture

**Observation:** Recording assumptions and principles revealed that the model's trustworthiness depends on the epistemic layer, not the graph layer.

**Consequence:** The graph is not the asset; trust in the graph is the asset.

**Architectural impact:** Architecture frozen. The four-layer separation (Constitutional / Experimental / Observation / Epistemic) became the structural foundation. The direction of dependency was corrected: observation → principle → assumption → evidence → edge → graph → prediction.

**Confidence:** EXPLICIT

---

## 4. Why this matters

If the observation process changes the architecture, then the
observation process must be part of the architecture. The
observatory records this meta-level: how the system learned about
itself, and how that learning changed what it is.

This is the recursive discipline the CEO identified early in the
project: "the loop is now auditing the mechanism that created the
loop." The observatory is the institutional memory of that recursion.

---

## 5. What this document does NOT do

- It does NOT authorize new observation events (those emerge from
  the work itself).
- It defines the SCHEMA for recording them and the EXISTING events.
- Future observation events will be appended here as they occur.
