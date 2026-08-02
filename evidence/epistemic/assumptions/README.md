# Assumptions — Type C Epistemic Statements (updated Phase 9 post-stress)

**Status:** epistemic layer (assumptions: what are we taking for granted?).
**Location:** `evidence/epistemic/assumptions/`
**Phase:** 9 post-stress (per CEO Instruction 2: assumption lifecycle applied).

> Every assumption must be falsifiable.
> — CEO Rule 1

An assumption is a statement the system depends on but cannot
prove from evidence alone. Each has a lifecycle:
PROPOSED → ACTIVE → QUESTIONED → FALSIFIED → REPLACED or RETIRED.

## Schema

```typescript
interface Assumption {
    id: string;
    statement: string;
    rationale: string;
    falsificationCriterion: string;
    status: "PROPOSED" | "ACTIVE" | "QUESTIONED" | "FALSIFIED" | "REPLACED" | "RETIRED";
    reviewer: string;
}
```

---

## A-001: CPC codes approximate capability

**Statement:** A patent's CPC code accurately reflects the capabilities the patent describes.

**Rationale:** CPC codes are assigned by USPTO patent examiners. Decades-refined, globally consistent.

**Falsification criterion:** A patent whose CPC code maps to a capability but whose claims don't describe it.

**Status:** QUESTIONED (stress test found CPC is coarse — correct at domain level, imprecise at fine-grained capability level).

**Reviewer:** coder_agent_001 / 2026-08-02

---

## A-002: 10 capabilities are sufficient (FALSIFIED → REPLACED by A-002a)

**Original statement:** 10 capabilities are sufficient for electrochemical energy storage.

**Falsification criterion:** The backtest produces predictions impossible without a dropped capability.

**Status:** FALSIFIED (5 innovations can't be expressed with 10 capabilities: solid-state, Na-ion, recycling, grid-scale, conversion-type).

**Replaced by:** A-002a (below).

---

## A-002a: 10 capabilities are sufficient for Li-ion intercalation systems

**Statement:** The 10 capabilities in CAPABILITY_CATALOG.md are sufficient to model Li-ion intercalation battery systems specifically (not all electrochemical storage).

**Rationale:** The 10 capabilities cover the Li-ion value chain: storage → ion transport → intercalation → electron collection → fast charging → thermal management → monitoring → safety → electrode coating → cell assembly. This is narrower than the original claim but matches what the stress test proved the model can actually cover.

**Falsification criterion:** A Li-ion intercalation innovation that cannot be expressed using these 10 capabilities (e.g., a new Li-ion feature that doesn't map to any of the 10).

**Status:** ACTIVE (replacement for falsified A-002).

**Reviewer:** coder_agent_001 / 2026-08-02

---

## A-003: Structural invariants stable across time (FALSIFIED → REPLACED by A-003a)

**Original statement:** Structural REQUIRES edges hold across 1990-2026.

**Falsification criterion:** A historical period where the invariant doesn't hold.

**Status:** FALSIFIED (REQUIRES INTERCALATION is false pre-1991 when lead-acid was dominant).

**Replaced by:** A-003a (below).

---

## A-003a: Li-ion-specific invariants are stable across the Li-ion era (1991-2026)

**Statement:** Structural REQUIRES edges specific to Li-ion chemistry are stable across the period in which Li-ion is commercially relevant (1991-2026). Pre-Li-ion chemistries (lead-acid, NiCd) are out of scope.

**Rationale:** Li-ion was commercialized by Sony in 1991. The structural edges (REQUIRES ION_TRANSPORT, REQUIRES INTERCALATION) are physical necessities of Li-ion specifically, not of all electrochemical storage. Before 1991, these edges would have been false because the dominant chemistry (lead-acid) doesn't use intercalation.

**Falsification criterion:** A year between 1991 and 2026 in which a Li-ion REQUIRES edge doesn't hold (e.g., a Li-ion variant that doesn't require intercalation).

**Status:** ACTIVE (replacement for falsified A-003).

**Reviewer:** coder_agent_001 / 2026-08-02

---

## A-004: 5 patents representative (FALSIFIED → REPLACED by A-004a)

**Original statement:** 5 patents are representative of electrochemical energy storage.

**Falsification criterion:** The backtest reveals the sample is biased.

**Status:** FALSIFIED (sample is Li-ion-biased; missing lead-acid, Na-ion, Li-S, etc.).

**Replaced by:** A-004a (below).

---

## A-004a: 5 patents are representative of Li-ion intercalation systems

**Statement:** The 5 patents selected are representative of Li-ion intercalation systems. They are NOT representative of the broader electrochemical storage domain.

**Rationale:** The 5 patents span solid-state Li-ion, flow battery (Li-ion adjacent), Li-ion + fast charging, battery pack assembly, and electrode coating. They cover the Li-ion value chain. They do NOT cover non-Li-ion chemistries.

**Falsification criterion:** The backtest reveals that predictions about Li-ion intercalation systematically miss a class of innovations that a different Li-ion sample would have caught.

**Status:** ACTIVE (replacement for falsified A-004).

**Reviewer:** coder_agent_001 / 2026-08-02

---

## A-005: 5 constraints most important (FALSIFIED → REPLACED by A-005a)

**Original statement:** 5 constraints are the most important for this vertical.

**Falsification criterion:** A dropped constraint was load-bearing for a failed prediction.

**Status:** FALSIFIED (Note 7 caused by separator integrity — a manufacturing constraint not in the 5).

**Replaced by:** A-005a (below).

---

## A-005a: 5 constraints capture physics and regulatory limits for Li-ion (manufacturing NOT covered)

**Statement:** The 5 constraints capture the most important physics and regulatory limits for Li-ion intercalation systems. Manufacturing constraints are NOT covered. The model cannot predict manufacturing-related failures.

**Rationale:** The 5 constraints cover physical limits (energy density ceiling, thermal runaway threshold), economic limits (cost per kWh), and regulatory limits (UN38.3, IEC 62133). Manufacturing constraints (separator integrity, dry electrode yield, solid electrolyte densification) were dropped in scope reduction and are NOT covered.

**Falsification criterion:** A backtest prediction fails because a manufacturing constraint that should have been modeled was absent, AND the failure cannot be explained by any of the 5 existing constraints.

**Status:** ACTIVE (replacement for falsified A-005). This is an honest narrowing — the model explicitly does NOT predict manufacturing-related failures.

**Reviewer:** coder_agent_001 / 2026-08-02

---

## Summary

| Assumption | Original status | Current status | Replacement |
|---|---|---|---|
| A-001 (CPC ≈ capability) | ACTIVE | QUESTIONED | (narrowed, not replaced) |
| A-002 (10 caps sufficient) | ACTIVE | FALSIFIED | → A-002a (Li-ion only) |
| A-003 (invariants stable) | ACTIVE | FALSIFIED | → A-003a (Li-ion era only) |
| A-004 (5 patents representative) | ACTIVE | FALSIFIED | → A-004a (Li-ion representative) |
| A-005 (5 constraints most important) | ACTIVE | FALSIFIED | → A-005a (manufacturing NOT covered) |

IC-006 (impossibility criterion: assumptions falsified without update) is now RESOLVED. All 4 falsified assumptions have been replaced with narrower, honest versions. The model has been updated.
