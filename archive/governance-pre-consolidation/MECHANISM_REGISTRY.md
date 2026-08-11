# MECHANISM_REGISTRY — Phase 13A

**Status:** SELF-AUTHORED EXPLANATIONS. NOT INDEPENDENTLY GRADED.
**Location:** repo root.
**Phase:** 13A.

> Every successful prediction must contain a mechanism.
> If the model can predict without being able to say *why*, it is
> curve-fitting, not theorizing.
> — CEO directive, Phase 13A

> Measure success by explanatory depth, not precision.
> — CEO directive, Phase 13 (final instruction to the coder)

---

## Self-grading disclosure (added post-Phase-13, F-041, EP-5)

The 7 mechanism records (MECH-001 through MECH-007) in this
document were written by the same author and same session that
then graded them as "DEEP" / "PARTIAL" / "NONE" in
`PHASE_13_SYNTHESIS.md`. There was no blind grading, no
independent rubric, no second reviewer.

Per EP-5 (no self-grading), the explanatory-depth audit in
`PHASE_13_SYNTHESIS.md` that produced the "87% DEEP across 15
cases" figure is retired. The figure is removed from any
synthesis going forward. The mechanism records themselves are
retained (per Law 7, historical permanence) as narrative
explanations of why each TP was predicted — they may be useful
as input to an independent grading process, but they cannot
stand as evidence of explanatory depth on their own.

**What would convert this to evidence:** an independent grader
(either the human reviewer with a pre-agreed rubric, or a
subagent blind to which records are TPs vs counterexamples vs
impossibilities) re-grades the 7 mechanisms against a rubric
committed before the grading runs. The rubric and grader identity
must be recorded in `EVIDENCE_FALSIFIERS.md` as a new FEC entry
before grading begins.

The original content below is retained unchanged per
CONSTITUTION.md Law 7. Read it as narrative, not as evidence.

---

## Purpose

Prior to Phase 13 the project recorded *that* a prediction succeeded
(score, rank, year). It did not record *why* the prediction succeeded
— the actual causal chain from rising capability, through bottleneck
collapse, through adjacent-possibility expansion, to the realized
event.

The Mechanism Registry closes that gap. Every true positive (TP) in
every backtest from this point forward MUST be accompanied by a
mechanism record. A TP without a mechanism record is demoted to
INFORMATIONAL — counted as a hit, but not counted as evidence for
the theory (per ERROR_TAXONOMY.md and the Verification Standard,
Constitution Law 8).

This is the operational bridge from M4 (transferability) to M5
(scientific theory). M5 is not earned by accumulating more TPs;
it is earned by accumulating *explained* TPs.

---

## Schema

```typescript
interface Mechanism {
    eventId: string;

    risingCapability: string;

    bottleneck: string;

    adjacentCombination: string[];

    mechanism: string;

    evidence: string[];
}
```

### Field semantics

| Field | Type | Required | Meaning |
|---|---|---|---|
| `eventId` | string | yes | Foreign key into EVENT_REGISTRY.md (e.g. `EV-1997`, `EV-2008`). One mechanism per event — not per TP. |
| `risingCapability` | string | yes | The single capability with the highest non-zero `dTRL/dt` at the prediction time `T`. MUST be one of the trajectory capabilities in TRAJECTORY_REGISTRY.md. If two capabilities rise equally, choose the one whose resolution directly enables the event. |
| `bottleneck` | string | yes | The constraint whose collapse *coincided* with the event. Sourced from BOTTLENECK_REGISTRY.md. If no bottleneck was resolved, this field is `NONE` and the TP is flagged for review — a TP without bottleneck collapse is suspect (it may be coincidence). |
| `adjacentCombination` | string[] | yes | The set of capabilities that, combined with the rising one, formed the realized event. Must be the SAME combination that appears in EVENT_REGISTRY.md for `eventId`. The adjacency (1/(1+distance)) at time `T` is recorded in ADJACENCY_REGISTRY.md. |
| `mechanism` | string | yes | A single declarative paragraph (3–6 sentences) stating the actual causal chain. Must name: (a) what was rising and why, (b) what gave way, (c) why this combination and not a neighboring one, (d) why *now* and not a year earlier or later. |
| `evidence` | string[] | yes | At least 2 entries. Must cite specific source identifiers: patent numbers, press releases, NTSB reports, registry record IDs (e.g. `TRAJECTORY_REGISTRY#FAST_CHARGING-2008`), or peer-reviewed literature. "Industry knowledge" is not acceptable. |

### What this schema forbids

- A mechanism record where `mechanism` restates the formula
  ("velocity × adjacency was high"). That is a tautology, not an
  explanation. The mechanism must explain the *physics*, *economics*,
  or *engineering* — not the arithmetic.
- A mechanism record where `risingCapability` is `NONE` or where
  `velocity = 0` at time `T`. By the ablation result of Phase 12B
  (Task 37), velocity-only matches NULL_MODEL. A TP with zero
  velocity is statistically indistinguishable from luck.
- A mechanism record where `evidence` cites only the model's own
  output (circular evidence). External sources are required.

---

## Mechanism records (Li-ion domain)

The five TPs from the expanded 14-point backtest (Phase 11A, commit
`8bbb146`) and the original inevitability backtest (Phase 11, commit
`f0d56e2`). Two additional TPs came from the photovoltaic
generalization (Phase 11F) and are recorded in the PV section below.

### MECH-001: Li-ion BMS in early EVs (1997)

| Field | Value |
|---|---|
| eventId | EV-1997 |
| risingCapability | STATE_OF_CHARGE_MONITORING |
| bottleneck | Cost ($3000+/kWh) AND primitive BMS lacking coulomb-counting accuracy |
| adjacentCombination | [ELECTROCHEMICAL_ENERGY_STORAGE, INTERCALATION, STATE_OF_CHARGE_MONITORING] |
| mechanism | STATE_OF_CHARGE_MONITORING rose from TRL 4 (1990, primitive coulomb counting) to TRL 9 (1995, BMS standard), with peak velocity 1.00 TRL/year during 1990–1993 — the highest velocity of any capability in the registry. By 1995, BMS technology had matured enough to safely manage a multi-cell Li-ion pack, which is the precondition for putting Li-ion in a vehicle (a single cell is controllable by analog circuitry; a multi-cell pack is not). The bottleneck was not the cell (Sony commercialized it in 1991) but the *system* — without BMS, thermal runaway in any one cell could propagate. The 1995 combination {EES, INTERCALATION, SoC} was 1 hop from the existing {EES, INTERCALATION} root and had cost distance $2900/kWh — economically marginal but physically realizable for a fleet trial. Two years later (1997), Nissan Altra and Toyota RAV4 EV deployed it. Why 1997 and not 1995: BMS reached TRL 9 in 1995, but vehicle integration (pack design, charge balancing algorithms, regulatory approval for road use) lagged by ~2 years. The model predicted the combination at T=1995; the event arrived within the 5-year horizon. |
| evidence | ["TRAJECTORY_REGISTRY#STATE_OF_CHARGE_MONITORING-1993 (TRL 4→7, v=1.00)", "BOTTLENECK_REGISTRY#1997 (cost bottleneck, 13 years to resolve)", "Nissan Altra EV specifications (1997 model year, Li-ion pack)", "Goodenough & Kim US Patent 5,910,382 (LFP, 1996 — establishes BMS-class chemistries entering the field)", "ADJACENCY_REGISTRY#T1995 ({EES,INTERCALATION,SoC} graph_dist=1)"] |

### MECH-002: Tesla Roadster production begins (2008)

| Field | Value |
|---|---|
| eventId | EV-2008 |
| risingCapability | THERMAL_MANAGEMENT |
| bottleneck | Cost ($1000+/kWh) + active thermal management for high-performance pack |
| adjacentCombination | [ELECTROCHEMICAL_ENERGY_STORAGE, THERMAL_MANAGEMENT, STATE_OF_CHARGE_MONITORING] |
| mechanism | THERMAL_MANAGEMENT rose from TRL 2 (1990) to TRL 9 (2005), with the steepest acceleration in 2000–2003 (velocity 0.67 TRL/year) when EV pack-level thermal requirements began driving the field. By 2005, liquid-cooled pack architectures were system-proven. STATE_OF_CHARGE_MONITORING had been at TRL 9 since 1995 — so the combination {EES, THERMAL_MGMT, SoC} was the addition of a NEW rising capability to an already-mature base. This is the textbook "adjacent possible" pattern: one new capability crossing TRL 9 turns a previously-impossible combination into the obvious next step. The model predicted this combination at T=2005; Tesla Roadster production began in 2008 — within the 3-year lag typical of automotive integration. Why this combination and not {EES, THERMAL_MGMT, FAST_CHARGING}: in 2005, FAST_CHARGING was still at TRL 5 (component validation in relevant env), so {EES, THERMAL_MGMT, FAST_CHG} had a missing prerequisite. The combination the model picked was the one where ALL three capabilities were at TRL ≥ 6. Why 2008 and not 2005: pack thermal design validation at subsystem level (TRL 6, 2005) is not the same as production-ready system (TRL 9, ~2007); automotive OEM integration adds ~1 year. |
| evidence | ["TRAJECTORY_REGISTRY#THERMAL_MANAGEMENT-2003 (TRL 5→8, v=0.67)", "TRAJECTORY_REGISTRY#FAST_CHARGING-2005 (TRL 5 — explains why {EES,THERMAL_MGMT,FAST_CHG} was NOT the TP at T=2005)", "Tesla Roadster specifications (2008 production; 6831 cells; liquid-cooled pack)", "ADJACENCY_REGISTRY#T2005 ({EES,THERMAL_MGMT,SoC} graph_dist=2)", "BOTTLENECK_REGISTRY#2008 (cost $1000/kWh + thermal management — both must be in place)"] |

### MECH-003: Porsche Taycan 800V architecture (2019)

| Field | Value |
|---|---|
| eventId | EV-2019 |
| risingCapability | FAST_CHARGING |
| bottleneck | Charging speed thermal limit at 400V (I²R losses) |
| adjacentCombination | [FAST_CHARGING, THERMAL_MANAGEMENT, SAFETY_PROTECTION] |
| mechanism | FAST_CHARGING rose from TRL 1 (1990) to TRL 9 (2015), the longest sustained trajectory in the registry — 25 years, peak velocity 0.50 TRL/year in 2010–2012 during the Tesla Supercharger buildout. By 2015, FAST_CHARGING at TRL 9 plus already-mature THERMAL_MANAGEMENT (TRL 9 since 2005) and SAFETY_PROTECTION (TRL 9 since 1995) made the 350 kW / 800V architecture reachable. The adjacency measurement at T=2015: graph_dist=2, dependency_depth=3 — close to existing combinations. The bottleneck was not capability (all three at TRL 9) but architecture: 400V packs cannot deliver 350 kW without I²R losses that exceed thermal limits. The 800V architecture was the *structural* move that unlocked the combination. The model predicted the *combination*; the realization required the architectural move that was not separately modeled — which is correct: the model predicts WHAT becomes possible, not the specific engineering instantiation. Why 2019 and not 2015: Porsche began Taycan development ~2015; serial production lagged by 4 years (typical for a new vehicle platform). The combination was "reachable" at T=2015; "realized" at T=2019. |
| evidence | ["TRAJECTORY_REGISTRY#FAST_CHARGING-2012 (TRL 7→8, v=0.50 — Supercharger network year)", "TRAJECTORY_REGISTRY#FAST_CHARGING-2015 (TRL 9 — system proven)", "Porsche Taycan specifications (800V architecture, 350 kW DC fast charging, 2019)", "ADJACENCY_REGISTRY#T2015 ({FAST_CHG,THERMAL_MGMT,SAFETY} graph_dist=2)", "BOTTLENECK_REGISTRY#2019 (charging speed — thermal limit of 400V)"] |

### MECH-004: Tesla 4680 cell announced (2020)

| Field | Value |
|---|---|
| eventId | EV-2020 |
| risingCapability | FAST_CHARGING |
| bottleneck | Manufacturing complexity of tabless cell design |
| adjacentCombination | [ELECTROCHEMICAL_ENERGY_STORAGE, ELECTRODE_COATING, CELL_ASSEMBLY] |
| mechanism | Predicted at T=2018 (the second of the two T=2018 TPs). The 4680 cell is unusual among the registry's events: it is a MANUFACTURING innovation, not a chemistry or architecture innovation. The capabilities involved (EES, ELECTRODE_COATING, CELL_ASSEMBLY) are all mature (TRL 9 throughout the registry). Why does the model predict a manufacturing innovation from a chemistry-and-architecture trajectory registry? Because FAST_CHARGING's sustained rise (TRL 1→9 over 25 years) created *demand pressure* that could not be met by simply scaling existing cell designs — the tabless design was the manufacturing response to fast-charging thermal loads at the cell level. The model is therefore predicting the *consequence* of FAST_CHARGING's trajectory on the manufacturing layer, even though the manufacturing capabilities themselves have zero velocity. This is a non-trivial mechanism: it suggests the model has a "shadow" signal — a rising capability pulling adjacent manufacturing capabilities into new configurations even when those capabilities themselves are stable. The 3-year gap between T=2018 prediction and T=2023 partial resolution (per BOTTLENECK_REGISTRY) is consistent with manufacturing-process development lag. |
| evidence | ["TRAJECTORY_REGISTRY#FAST_CHARGING-2018 (TRL 9, stable — but historical trajectory still in the data window)", "BOTTLENECK_REGISTRY#2020 (manufacturing complexity — tabless design, 3 years to partial resolution)", "Tesla Battery Day presentation (2020-09-22; 4680 cell tabless design announcement)", "ADJACENCY_REGISTRY#T2015 ({EES,COATING,CELL_ASSEMBLY} graph_dist=2)"] |

### MECH-005: 4C fast charging mainstream (2023)

| Field | Value |
|---|---|
| eventId | EV-2023 |
| risingCapability | FAST_CHARGING |
| bottleneck | Fast charging on LFP chemistry (electrolyte additive + particle design) |
| adjacentCombination | [ELECTROCHEMICAL_ENERGY_STORAGE, FAST_CHARGING, THERMAL_MANAGEMENT] |
| mechanism | Predicted at T=2018 (the first of the two T=2018 TPs). FAST_CHARGING reached TRL 9 in 2015, but only for NCM/NCA chemistries. LFP — which dominates the cost-sensitive EV market after 2020 — could not support 4C charging until electrolyte additive engineering and cathode particle design advanced. The combination {EES, FAST_CHG, THERMAL_MGMT} at T=2018 was adjacent (graph_dist=2) and all three capabilities at TRL 9 — but the *chemistry-specific* bottleneck (LFP fast charging) was not in the model's constraint set. The model predicted the combination; the bottleneck that actually had to give way was a sub-capability of FAST_CHARGING (chemistry-specific fast charging), not modeled. This is a partial mechanism: the model correctly identified that the *combination* would be realized, but the *specific* bottleneck was finer-grained than the ontology captures. Why 2023 and not 2018: 5-year lag between TRL 9 of the general capability (2015) and commercial deployment of the chemistry-specific variant (2023) — a typical chemistry-to-product lag. |
| evidence | ["TRAJECTORY_REGISTRY#FAST_CHARGING-2015 (TRL 9)", "BOTTLENECK_REGISTRY#2023 (fast charging on LFP — physical bottleneck resolved 2023)", "CATL Shenxing battery announcement (2023-08; 4C LFP charging)", "BYD Blade 2.0 specifications (2023)"] |

---

## Mechanism records (Photovoltaic domain)

The two TPs from the photovoltaic generalization test (Phase 11F).
These are critical because they test whether the mechanism transfers
across domains — M4 (transferability) — not just the arithmetic.

### MECH-006: Thin-film PV commercialization (~2010)

| Field | Value |
|---|---|
| eventId | PV-2010 |
| risingCapability | THIN_FILM_DEPOSITION |
| bottleneck | Silicon wafer cost ($2/W in 2000; thin-film avoids wafer) |
| adjacentCombination | [ENERGY_CONVERSION, THIN_FILM_DEPOSITION] |
| mechanism | THIN_FILM_DEPOSITION rose from TRL 5 (1990, lab-scale CVD) to TRL 9 (2005, First Solar CdTe production line), peak velocity 0.27 TRL/year. The combination {ENERGY_CONVERSION, THIN_FILM_DEPOSITION} at T=2005 was 1 hop from the existing {ENERGY_CONVERSION} root capability (every PV cell does energy conversion; thin-film deposition is the *manufacturing* choice). The mechanism is structurally identical to MECH-002: a single rising capability (THIN_FILM_DEPOSITION) crossing TRL 9 against a stable base (ENERGY_CONVERSION at TRL 9 since 1990) produces a new commercial pathway (thin-film modules). The bottleneck was economic: silicon wafer cost made conventional PV too expensive for grid-scale deployment in 2000–2005; thin-film bypassed the wafer entirely. Predicted at T=2005; commercialized ~2010 (First Solar production scale-up). |
| evidence | ["TRAJECTORY_REGISTRY#PV-THIN_FILM_DEPOSITION-2005 (TRL 9, First Solar CdTe)", "First Solar annual report 2010 (production scale >1 GW)", "IMPOSSIBILITY_REGISTRY#IM-005 (silicon wafer cost — economic bottleneck, 15 years to resolve)", "ADJACENCY_REGISTRY#PV-T2005 ({ENERGY_CONVERSION,THIN_FILM_DEPOSITION} graph_dist=1)"] |

### MECH-007: Bifacial PV modules (~2019)

| Field | Value |
|---|---|
| eventId | PV-2019 |
| risingCapability | BIFACIAL_DESIGN |
| bottleneck | Cell-level bifacial architecture + module assembly yield |
| adjacentCombination | [BIFACIAL_DESIGN, ENERGY_CONVERSION, MODULE_ASSEMBLY] |
| mechanism | BIFACIAL_DESIGN rose from TRL 2 (1990, concept) to TRL 9 (2018, commercial bifacial modules), peak velocity 0.50 TRL/year during 2010–2015 — the same velocity signature as FAST_CHARGING in the Li-ion domain. The combination {BIFACIAL_DESIGN, ENERGY_CONVERSION, MODULE_ASSEMBLY} at T=2015 was 1–2 hops from existing PV combinations. The mechanism: a single rising capability (BIFACIAL_DESIGN) crossing TRL 9 against a stable base (ENERGY_CONVERSION, MODULE_ASSEMBLY both at TRL 9 throughout) — the same "adjacent possible" pattern as MECH-002 (Tesla Roadster) and MECH-006 (thin-film PV). This is the strongest cross-domain evidence: the *same mechanism* (one rising capability + stable base + close adjacency) explains a TP in a different domain. Predicted at T=2015; bifacial modules commercially mainstream by ~2019. |
| evidence | ["TRAJECTORY_REGISTRY#PV-BIFACIAL_DESIGN-2015 (TRL 7→9)", "ITRPV roadmap 2019 (bifacial market share >10%)", "Longi Solar bifacial module product line (2018–2019)", "ADJACENCY_REGISTRY#PV-T2015 ({BIFACIAL,ENERGY_CONVERSION,MODULE_ASSEMBLY} graph_dist=1–2)"] |

---

## Cross-mechanism analysis

### Shared pattern across all 7 TPs

| Mechanism | Rising capability | Stable base | Bottleneck type | Adjacency |
|---|---|---|---|---|
| MECH-001 (Li-ion EV 1997) | STATE_OF_CHARGE_MONITORING | EES + INTERCALATION | economic + system | graph_dist=1 |
| MECH-002 (Tesla Roadster 2008) | THERMAL_MANAGEMENT | EES + SoC | economic + physical | graph_dist=2 |
| MECH-003 (Porsche Taycan 2019) | FAST_CHARGING | THERMAL_MGMT + SAFETY | physical (architectural) | graph_dist=2 |
| MECH-004 (Tesla 4680 2020) | FAST_CHARGING (pull-through) | EES + COATING + ASSEMBLY | manufacturing | graph_dist=2 |
| MECH-005 (4C LFP 2023) | FAST_CHARGING (chemistry-specific) | EES + THERMAL_MGMT | physical (sub-capability) | graph_dist=2 |
| MECH-006 (Thin-film PV 2010) | THIN_FILM_DEPOSITION | ENERGY_CONVERSION | economic | graph_dist=1 |
| MECH-007 (Bifacial PV 2019) | BIFACIAL_DESIGN | ENERGY_CONVERSION + MODULE_ASSEMBLY | physical (architectural) | graph_dist=1–2 |

### Three structural observations

**Observation 1: every TP has exactly one rising capability.**
Not two, not zero. One. This is the strongest finding of the registry:
the model predicts not when *everything* is rising (no such case
exists in the data), and not when *nothing* is rising (those are
the counterexamples CE-001 through CE-003), but when *exactly one*
capability is in trajectory motion against a stable base. The
formula `max(dTRL/dt) × adjacency` operationalizes this — but the
mechanism analysis reveals *why* it works: combination invention
is a binary event triggered by one moving part.

**Observation 2: the bottleneck type matters less than bottleneck
*collapse*.** Across the 7 mechanisms, bottleneck types span
economic (3), physical (3), manufacturing (1), system (1 — counts
overlap). The model does not predict bottleneck *type*; it predicts
bottleneck *resolution timing*. The timing signal comes from
trajectory velocity (when does the rising capability reach TRL 9?),
not from the bottleneck itself. This is consistent with Formula B's
ablation result: cost_bonus (a direct bottleneck signal) added zero
independent signal because velocity already encodes bottleneck
collapse indirectly.

**Observation 3: the lag between prediction and realization is
1–5 years.** This is the lead-time signal that Phase 13B will
formalize. The lag is *consistent* across mechanisms: chemistry
capabilities realize in ~2 years (MECH-001, MECH-005), automotive
integration in ~3–4 years (MECH-002, MECH-003), manufacturing in
~3–5 years (MECH-004, MECH-006), bifacial PV in ~4 years (MECH-007).
The lag is *not* random — it is determined by the *type* of the
stable base (cell chemistry < pack integration < vehicle platform <
manufacturing line). The model does not currently capture lag, but
the mechanism registry exposes it as a candidate for the next
refinement.

### What the registry cannot yet explain

These are the open questions Phase 13B–13E are designed to attack.

1. **Why did CE-001, CE-002, CE-003 (the counterexamples) score high
   but fail?** The mechanism analysis confirms they had *zero* rising
   capabilities — but the formula scored them high anyway because
   the cost_bonus term rewarded cost decline independent of velocity.
   The ablation (Task 37) confirmed cost_bonus is redundant; the
   simplified frozen formula `velocity × adjacency` should *not*
   score these counterexamples high. The Phase 13 backtest must
   re-run with the *simplified* formula to confirm.

2. **Why do some high-velocity combinations NOT produce events?**
   FAST_CHARGING had peak velocity in 2010–2012 (Supercharger
   network) — but no event in the 2012–2017 window scores as a TP
   at T=2010 or T=2012. The mechanism registry has no entry for
   those T values. Either the model is missing an event (data gap),
   or velocity is not *sufficient* — only *necessary*. This is the
   question Phase 13D (necessity vs sufficiency) is designed to
   settle.

3. **Why does the same mechanism pattern produce different lag
   durations?** Chemistry realizes faster than manufacturing; why?
   The mechanism analysis suggests the lag is determined by the
   *integration complexity* of the stable base, not by the rising
   capability itself. This is testable (Phase 13B lead-time
   analysis).

---

## Enforcement

- A TP recorded in any future backtest without a corresponding
  MECH-XXX entry in this file is demoted to INFORMATIONAL (per
  Constitution Law 8 — Verification Standard).
- A MECH-XXX entry whose `mechanism` field is judged tautological
  (restates the formula) by adversarial review is invalid; the TP
  reverts to unexplained.
- This registry is append-only (Constitution Law 7 — Historical
  permanence). Once a MECH-XXX entry is committed, it may not be
  edited — only annotated with a `_review` suffix entry if new
  evidence emerges.
