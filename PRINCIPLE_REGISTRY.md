# PRINCIPLE_REGISTRY — Phase 9B

**Status:** scientific instrument (attempt to break the principles).
**Location:** repo root.
**Phase:** 9B.

> Every principle must be treated as temporary.
> — CEO directive, Phase 9B

## Schema

```typescript
interface PrincipleRecord {
    principleId: string;
    scope: string;
    exceptions: string[];
    supportingEvidence: string[];
    counterEvidence: string[];
    confidence: string;  // EXPLICIT | IMPLIED | STRUCTURAL | SPECULATIVE
}
```

---

## P-001: Charge conservation

**Scope:** All electrochemical cells.
**Exceptions:** None recorded.
**Supporting evidence:** Maxwell's equations; basic electrochemistry.
**Counter-evidence:** None. This is a fundamental law of physics.
**Confidence:** STRUCTURAL

**Status:** SURVIVED. Charge conservation is universal within known physics.

---

## P-002: Lattice insertion chemistry (Li-ion specifically)

**Scope:** Li-ion batteries only.
**Exceptions:** Flow batteries, lead-acid, Li-S, Li-air (conversion reactions).
**Supporting evidence:** Li-ion electrode materials (graphite, LFP, NCM) all use intercalation.
**Counter-evidence:** At T=1990, lead-acid (no intercalation) was dominant. The principle's scope is correct but the EDGE-026 that invokes it is over-generalized — it applies REQUIRES INTERCALATION to ELECTROCHEMICAL_ENERGY_STORAGE (too broad) rather than to LI_ION_STORAGE (correctly scoped).
**Confidence:** STRUCTURAL

**Status:** SURVIVED (as a principle). But the EDGE using it (EDGE-026) is misapplied — the edge is too broad for the principle's scope.

---

## P-003: Transport kinetics

**Scope:** Cells where C-rate matters.
**Exceptions:** Supercapacitors (electrostatic, not ion transport).
**Supporting evidence:** Butler-Volmer equation; documented C-rate limits.
**Counter-evidence:** None within scope.
**Confidence:** STRUCTURAL

**Status:** SURVIVED.

---

## P-004: Joule heating (I²R losses)

**Scope:** All real cells with internal resistance > 0.
**Exceptions:** Low C-rate (heating negligible); superconducting cells (theoretical).
**Supporting evidence:** Ohm's law; Joule's first law; well-documented thermal behavior.
**Counter-evidence:** None within scope.
**Confidence:** STRUCTURAL

**Status:** SURVIVED.

---

## P-005: Manufacturing process dependency

**Scope:** Commercially manufactured cells.
**Exceptions:** Lab-scale coin cells (pressed, not coated).
**Supporting evidence:** Battery manufacturing process literature.
**Counter-evidence:** None within scope.
**Confidence:** STRUCTURAL

**Status:** SURVIVED. But note: the scope is "commercially manufactured." The 5 patents in the corpus include lab-scale and pilot-scale work. The principle may not apply to all of them.

---

## P-006: Feedback control

**Scope:** Active safety management systems.
**Exceptions:** Passive safety devices (fuses, PTC, CID).
**Supporting evidence:** Control theory; BMS literature.
**Counter-evidence:** Passive safety devices protect without monitoring. The REQUIRES edge (EDGE-030: SAFETY_PROTECTION REQUIRES STATE_OF_CHARGE_MONITORING) is too strong — passive safety doesn't require monitoring.
**Confidence:** STRUCTURAL

**Status:** INCONCLUSIVE. The principle is correct for ACTIVE safety. The edge is too broad — it applies to ALL safety protection, including passive.

---

## P-007: Thermodynamic energy density ceiling

**Scope:** All electrochemical chemistries.
**Exceptions:** None.
**Supporting evidence:** Gibbs free energy; electrochemical thermodynamics.
**Counter-evidence:** None.
**Confidence:** STRUCTURAL

**Status:** SURVIVED. This is thermodynamics.

---

## P-008: Exothermic decomposition threshold

**Scope:** Li-ion cells (~130-180°C).
**Exceptions:** Other chemistries have different thresholds.
**Supporting evidence:** Battery safety literature; ARC test data.
**Counter-evidence:** The threshold varies by chemistry and formulation. LFP is more thermally stable than NCM. The ~150°C figure is an approximation.
**Confidence:** STRUCTURAL

**Status:** SURVIVED with caveat. The threshold is approximate and chemistry-dependent. The principle is sound; the specific value needs calibration.

---

## P-009: Market price elasticity

**Scope:** Commercial electrochemical storage.
**Exceptions:** Research/lab-scale (no market).
**Supporting evidence:** BNEF price surveys; Wright's Law.
**Counter-evidence:** The threshold changes over time ($600/kWh in 2010 → $100/kWh in 2026). Without TemporalState, the constraint is applied with the wrong threshold for historical backtests.
**Confidence:** STRUCTURAL

**Status:** INCONCLUSIVE. The principle is correct but the threshold is temporal. The model cannot apply this constraint at T=1995 (threshold was ~$3000/kWh) without temporal data.

---

## P-010: Transport safety regulation (UN Model Regulations)

**Scope:** Commercial lithium battery shipping.
**Exceptions:** Small prototypes; non-lithium chemistries.
**Supporting evidence:** UN Model Regulations; UN38.3 test manual.
**Counter-evidence:** None within scope.
**Confidence:** EXPLICIT

**Status:** SURVIVED.

---

## P-011: Product safety standard (IEC 62133)

**Scope:** Consumer secondary cells.
**Exceptions:** Industrial/motive (IEC 62660 for EVs).
**Supporting evidence:** IEC 62133:2012.
**Counter-evidence:** The standard covers consumer products, not EVs or grid. If the model predicts EV battery innovations, IEC 62133 is the wrong standard.
**Confidence:** EXPLICIT

**Status:** SURVIVED with caveat. The standard is correct for consumer products but may not apply to all predictions in the vertical.

---

## Summary

| Principle | Status | Finding |
|---|---|---|
| P-001 charge conservation | SURVIVED | Universal |
| P-002 lattice insertion | SURVIVED | Principle correct; EDGE-026 misapplied (too broad) |
| P-003 transport kinetics | SURVIVED | Correct within scope |
| P-004 Joule heating | SURVIVED | Correct within scope |
| P-005 manufacturing dependency | SURVIVED | Scope is "commercial"; some patents are lab-scale |
| P-006 feedback control | INCONCLUSIVE | Correct for active safety; EDGE-030 too broad (includes passive) |
| P-007 thermodynamic ceiling | SURVIVED | Universal |
| P-008 exothermic decomposition | SURVIVED with caveat | Threshold is approximate, chemistry-dependent |
| P-009 market elasticity | INCONCLUSIVE | Correct principle; threshold is temporal (needs TemporalState) |
| P-010 UN38.3 | SURVIVED | Externally validated |
| P-011 IEC 62133 | SURVIVED with caveat | Consumer only; not EV/grid |

**8 SURVIVED, 2 INCONCLUSIVE, 0 FAILED.**

The principles are sound. The EDGES that invoke them are sometimes
too broad (EDGE-026, EDGE-030) or need temporal scoping (P-009).
The principles themselves survive scrutiny. The model's weakness is
in how edges apply principles, not in the principles themselves.
