# Principles — Type B Epistemic Statements

**Status:** epistemic layer (principles: what do we believe is true?).
**Location:** `evidence/epistemic/principles/`
**Phase:** 7C.3 (per CEO Rule 2: every principle must have a scope).

> Every principle must have a scope.
> — CEO Rule 2

A principle is a named physical, chemical, or economic law that
justifies a structural edge. It is NOT an observation and NOT an
assumption. It is a domain-model assertion that a reviewer invokes
to explain WHY one capability requires or constrains another.

## Schema

```typescript
interface Principle {
    id: string;                // e.g., "P-001"
    name: string;              // short name
    description: string;       // what the principle states
    scope: string;             // where the principle applies
    exceptions: string[];      // known cases where it doesn't hold
    references: string[];      // where it is established
    confidence: string;        // EXPLICIT | IMPLIED | STRUCTURAL | SPECULATIVE
}
```

---

## P-001: Charge conservation

**Description:** Electrochemical storage requires ions to move between
electrodes to balance the electron flow in the external circuit.
Without ion transport, charge accumulation prevents further reaction.

**Scope:** All electrochemical cells (batteries, fuel cells, electrolyzers).

**Exceptions:** None recorded. This is a fundamental law of physics.

**References:** Maxwell's equations; basic electrochemistry textbooks.
(Pending: specific textbook chapter citations.)

**Confidence:** STRUCTURAL

**Edges using this:** EDGE-025

---

## P-002: Lattice insertion chemistry (Li-ion specifically)

**Description:** Li-ion electrochemical storage requires intercalation —
ions insert into and remove from electrode lattices. This is specific
to intercalation-based chemistries, not universal (conversion reactions
exist).

**Scope:** Li-ion batteries specifically. Does NOT apply to flow
batteries, lead-acid, or conversion-reaction chemistries.

**Exceptions:** Flow batteries (US12489120B2 in this corpus) do not
use intercalation. Lead-acid does not use intercalation. Li-S and
Li-air use conversion reactions, not intercalation.

**References:** Lithium-ion battery textbooks (Pending: specific citations.)

**Confidence:** STRUCTURAL

**Edges using this:** EDGE-026

---

## P-003: Transport kinetics

**Description:** Fast charging requires ions to move rapidly between
electrodes. The C-rate is limited by ion transport kinetics in the
electrolyte and across interfaces.

**Scope:** All electrochemical cells where C-rate matters (i.e., where
fast charging is attempted).

**Exceptions:** Supercapacitors store energy electrostatically, not
via ion transport — this principle doesn't apply to them. (But
supercapacitors are out of scope for this vertical.)

**References:** Electrochemistry transport phenomena (Pending.)

**Confidence:** STRUCTURAL

**Edges using this:** EDGE-027

---

## P-004: Joule heating (I²R losses)

**Description:** High current generates heat via internal resistance
(P = I²R). Without thermal management, cell temperature exceeds
safe limits at high C-rates.

**Scope:** All electrochemical cells with internal resistance > 0
(i.e., all real cells).

**Exceptions:** Superconducting cells (theoretical, not practical).
At very low C-rates, Joule heating is negligible and thermal
management is not required.

**References:** Ohm's law; Joule's first law.

**Confidence:** STRUCTURAL

**Edges using this:** EDGE-028

---

## P-005: Manufacturing process dependency

**Description:** Cell assembly requires coated electrodes. The electrode
coating process produces the functional electrode that is then assembled
into a cell.

**Scope:** All manufactured electrochemical cells (not lab-fabricated
coin cells where electrodes may be pressed, not coated).

**Exceptions:** Lab-scale cells where electrodes are pressed from
powder rather than coated. (Out of scope for this vertical's
commercial focus.)

**References:** Battery manufacturing process literature (Pending.)

**Confidence:** STRUCTURAL

**Edges using this:** EDGE-029

---

## P-006: Feedback control

**Description:** Safety protection systems (e.g., overcharge cutoff)
require knowing the cell's state of charge. Without monitoring, the
safety system cannot determine when to intervene.

**Scope:** All electrochemical cells with active safety management.

**Exceptions:** Passive safety devices (fuses, PTC devices) do not
require state-of-charge monitoring — they trigger on current/temperature
directly.

**References:** Control theory; battery management system literature.

**Confidence:** STRUCTURAL

**Edges using this:** EDGE-030

---

## P-007: Thermodynamic energy density ceiling

**Description:** The theoretical energy density of electrochemical
chemistries (e.g., ~400 Wh/kg for Li-ion) limits the maximum energy
a cell can store. This is a thermodynamic limit, not an engineering
limit.

**Scope:** All electrochemical chemistries. Each chemistry has its own
theoretical ceiling.

**Exceptions:** None. This is thermodynamics.

**References:** Gibbs free energy; electrochemical thermodynamics.

**Confidence:** STRUCTURAL

**Edges using this:** EDGE-031

---

## P-008: Exothermic decomposition threshold

**Description:** If cell temperature exceeds ~150°C, thermal runaway
occurs — an uncontrollable exothermic decomposition reaction.

**Scope:** Lithium-ion cells specifically. Other chemistries have
different thresholds (e.g., lead-acid is more tolerant).

**Exceptions:** The threshold varies by chemistry (~130-180°C).
The ~150°C figure is approximate for typical Li-ion.

**References:** Battery safety literature (Pending.)

**Confidence:** STRUCTURAL

**Edges using this:** EDGE-032

---

## P-009: Market price elasticity

**Description:** The cost per kWh must be below the market threshold
(~$100/kWh for EVs) for the storage to be economically viable.

**Scope:** Commercial electrochemical energy storage (EV, grid,
consumer). Does not apply to research/lab-scale.

**Exceptions:** The threshold changes over time (was $600/kWh in
2010, ~$100/kWh in 2026). Requires TemporalState.

**References:** BNEF battery price surveys; Wright's Law.

**Confidence:** STRUCTURAL

**Edges using this:** EDGE-033

---

## P-010: Transport safety regulation (UN Model Regulations)

**Description:** UN38.3 requires batteries to pass specific safety
tests (T.1-T.8) before commercial transport.

**Scope:** All lithium batteries shipped commercially internationally.

**Exceptions:** Small prototype cells (< 100 Wh) may have reduced
testing requirements under certain conditions.

**References:** UN Model Regulations on the Transport of Dangerous
Goods, Manual of Tests and Criteria, Section 38.3.

**Confidence:** EXPLICIT (regulation is externally validated)

**Edges using this:** EDGE-034, EDGE-036

---

## P-011: Product safety standard (IEC 62133)

**Description:** IEC 62133 specifies safety requirements for secondary
cells containing alkaline or other non-acid electrolytes.

**Scope:** Secondary (rechargeable) cells and batteries for consumer
products.

**Exceptions:** Industrial/motive batteries may be covered by other
standards (e.g., IEC 62660 for EVs).

**References:** IEC 62133:2012 (Edition 2).

**Confidence:** EXPLICIT (standard is externally validated)

**Edges using this:** EDGE-035, EDGE-037

---

## Honest disclosure

References are listed as "Pending" where the principle is grounded
in domain knowledge but not yet cited to specific textbook chapters
or standards sections. This is recorded honestly per principle #8
(no data, say no data). Full citation of references is a prerequisite
for Phase 7D (the frozen-time backtest requires replayable evidence,
and principles without references are not replayable).
