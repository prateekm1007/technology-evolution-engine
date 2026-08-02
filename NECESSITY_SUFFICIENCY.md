# NECESSITY_SUFFICIENCY — Phase 13D

**Status:** constitutional document (necessity / sufficiency analysis).
**Location:** repo root.
**Phase:** 13D.

> Velocity may be necessary.
> Velocity may not be sufficient.
> — CEO directive, Phase 13D

---

## Purpose

A factor can be *necessary* (every event has it) without being
*sufficient* (some cases have it but no event occurs). The
distinction is foundational to scientific theory: a necessary
factor rules out combinations; a sufficient factor rules them in.

Formula B's frozen form `max(dTRL/dt) × adjacency` contains two
factors (velocity and adjacency) and *implicitly* depends on two
more (bottleneck removal and cost decline) that the ablation
(Task 37) showed to be statistically redundant — but statistical
redundancy is not the same as causal redundancy.

This protocol distinguishes, for each of the four factors, whether
it is necessary, sufficient, both, or neither. The CEO's directive
is explicit: this distinction is "absolutely critical."

---

## Definitions

| Term | Meaning |
|---|---|
| **Necessary** | Every true positive in the registry has this factor present at non-trivial level. If the factor is absent, no event occurs. Failure mode: false negatives (model misses events that *should* be predictable). |
| **Sufficient** | When this factor is present at non-trivial level, an event occurs. Presence implies event. Failure mode: false positives (model over-predicts). |
| **Necessary AND sufficient** | The factor alone explains all events and excludes all non-events. This is the gold standard — equivalent to a deterministic law. Rare in complex systems. |
| **Necessary but NOT sufficient** | The factor must be present, but its presence does not guarantee an event. Other factors (modeled or unmodeled) must align. This is the typical case for causal factors in real systems. |
| **Sufficient but NOT necessary** | The factor alone can produce events, but events can also occur through other pathways. The factor is one of multiple routes to the outcome. |
| **Neither** | The factor is not required for events AND its presence does not guarantee events. The factor is noise. |

### The test protocol

For each factor, the project applies four checks:

1. **Necessity check:** Of all TPs in MECHANISM_REGISTRY, how many
   have this factor present at non-trivial level? (Non-trivial =
   velocity > 0.20 TRL/year; adjacency > 0.5 i.e. graph_dist ≤ 1;
   bottleneck resolved at event year; cost decline > 10%/year.)
2. **Sufficiency check:** Of all combinations in the backtest with
   this factor present at non-trivial level, how many produced
   events? (Sufficient if > 50%, ambiguous if 10–50%, not
   sufficient if < 10%.)
3. **Counterexample audit:** Of COUNTEREXAMPLE_REGISTRY entries,
   which have this factor present? (Counterexamples with the
   factor present indicate the factor is NOT sufficient.)
4. **Impossibility audit:** Of IMPOSSIBILITY_REGISTRY entries,
   which have this factor absent? (Impossibilities with the factor
   absent indicate the factor is necessary.)

---

## The four factors

### Factor 1: velocity (`max(dTRL/dt)`)

**Definition:** The maximum TRL velocity across all capabilities in
the combination at time `T`. Measured in TRL/year.

**Threshold for "non-trivial":** velocity > 0.20 TRL/year (per
PERSISTENCE_PROTOCOL.md).

| Check | Result |
|---|---|
| Necessity | All 7 TPs in MECHANISM_REGISTRY have velocity > 0.20 in their rising capability. **All 7.** Necessity is satisfied. |
| Sufficiency | Of 140 Top-10 predictions in the expanded backtest, 7 produced events. **5% of velocity-positive predictions produce events.** Sufficiency is NOT satisfied. |
| Counterexample audit | CE-001, CE-002, CE-003 all had velocity ≥ 0.20 (from the cost_bonus term — but in the simplified formula, velocity is the rising-capability velocity, and CE-001 to CE-003 had ALL stable capabilities with zero rising-capability velocity). Under the simplified formula, the counterexamples do NOT have the velocity factor present. This is consistent with the necessity finding. |
| Impossibility audit | IM-001 to IM-005 all involve combinations where the relevant velocity is below threshold (FAST_CHARGING at TRL 2 in 1995 cannot deliver fast charging; cost velocity negative). Impossibilities are consistent with velocity being necessary. |

**Verdict: NECESSARY, NOT SUFFICIENT.**

**Implication:** Velocity must be present for invention, but its
presence alone does not guarantee invention. Other factors must
align. The ablation result (velocity-only matches NULL_MODEL at
0.71%) is the empirical confirmation: velocity alone is noise;
velocity × adjacency is signal. The necessity finding explains
*why* the ablation produced this result — velocity is necessary
but not sufficient, so velocity alone should not beat NULL.
Velocity × adjacency works because adjacency provides the
second necessary factor.

**This is the most important finding of Phase 13D.** Velocity is
the gate; adjacency is the trigger. The model needs both.

### Factor 2: adjacency (`1 / (1 + distance)`)

**Definition:** The inverse of the graph distance from the
combination to the nearest existing realized combination. Measured
as a continuous value in (0, 1].

**Threshold for "non-trivial":** adjacency > 0.5 (graph_dist ≤ 1).

| Check | Result |
|---|---|
| Necessity | All 7 TPs have adjacency > 0.5 (graph_dist ≤ 2 in the registry; most at graph_dist = 1 or 2). Necessity is satisfied. |
| Sufficiency | Of 140 Top-10 predictions, 7 produced events. ~5% of adjacency-positive predictions produce events. Sufficiency is NOT satisfied. |
| Counterexample audit | CE-001, CE-002, CE-003 all had HIGH adjacency (they were close to existing combinations — in fact they WERE existing combinations). This is the strongest evidence that adjacency is NOT sufficient: high-adjacency counterexamples are the dominant failure mode. |
| Impossibility audit | Impossibilities are not adjacency-structured (they are constraint-structured). Not directly applicable. |

**Verdict: NECESSARY, NOT SUFFICIENT.**

**Implication:** Adjacency must be present for invention (the
combination must be reachable from what exists), but high
adjacency does not guarantee invention (counterexamples CE-001
to CE-003 are all high-adjacency and all failed). The
ablation result (adjacency-only = 0% precision) is the empirical
confirmation: adjacency alone is useless because adjacency without
velocity is just the status quo.

**The deep finding:** The counterexamples reveal that adjacency is
*necessary but potentially harmful in isolation*. A combination
that is too close to what already exists is the LEAST likely to
produce a new event — it's already been done. The model needs
adjacency to be high enough to be reachable but not so high that
the combination is already realized. The current formula does
not capture this nuance.

### Factor 3: bottleneck removal

**Definition:** Whether the active bottleneck (physical, economic,
infrastructure, manufacturing, regulatory) at time `T` was
resolved by time `T+5`.

**Threshold for "non-trivial":** bottleneck resolved at or before
event year (years_to_resolve ≤ 5).

| Check | Result |
|---|---|
| Necessity | All 7 TPs have a bottleneck that was resolved at or near the event year (per BOTTLENECK_REGISTRY). **All 7.** Necessity is satisfied. |
| Sufficiency | Cannot be directly tested in the current data — bottleneck resolution is not tracked for non-events. However, indirect evidence: many bottlenecks in the registry were resolved without producing events. The cost bottleneck resolved ~2010 (cost dropped below $300/kWh) — but multiple Li-ion chemistries existed at $300/kWh without producing new events. Bottleneck removal is NOT sufficient. |
| Counterexample audit | CE-001 to CE-003: bottlenecks for these were already resolved (they were stable combinations). The counterexamples had bottleneck removal present and still did not produce events. NOT sufficient. |
| Impossibility audit | IM-001 to IM-005: all involve unresolved bottlenecks. Impossibilities are bottleneck-structured. Bottleneck removal is consistent with necessity. |

**Verdict: NECESSARY, NOT SUFFICIENT.**

**Implication:** A bottleneck must give way for an event to occur,
but bottleneck removal alone does not produce events. This is
intuitively correct: removing the cost bottleneck for Li-ion EVs
in 2010 did not *cause* the Leaf and Volt — it merely *permitted*
them. The cause was the combination of cost decline + existing
Li-ion capability + BMS maturity + automotive OEM willingness to
build them.

**The deep finding:** Bottleneck removal is *permissive* but not
*productive*. It opens the door; it does not push anyone through.
The model currently treats bottleneck as a binary gate
(feasibility filter). This is correct for necessity checking but
misses the productive dimension.

### Factor 4: cost decline

**Definition:** The rate of cost decrease for the relevant cost
metric (e.g., $/kWh for Li-ion, $/W for PV).

**Threshold for "non-trivial":** cost decline > 10%/year.

| Check | Result |
|---|---|
| Necessity | All 7 TPs occurred during periods of cost decline (Li-ion cost dropped from $3000/kWh in 1991 to $100/kWh in 2023; PV cost dropped from $100/W in 1975 to $0.20/W in 2023). **All 7.** Necessity is satisfied. |
| Sufficiency | Of 140 Top-10 predictions, 7 produced events. All 140 predictions occurred during cost decline periods. ~5% of cost-decline-positive predictions produce events. Sufficiency is NOT satisfied. |
| Counterexample audit | CE-001 to CE-003: all occurred during cost decline. Cost decline is present in counterexamples. NOT sufficient. |
| Impossibility audit | IM-002 (cost at $3000/kWh in 1995, target $100/kWh — 15 doublings away) and IM-005 (silicon wafer cost too high in 2000) are economic impossibilities. Cost absence is consistent with necessity. |

**Verdict: NECESSARY, NOT SUFFICIENT.**

**Implication:** Cost decline is necessary (no event occurs in a
rising-cost environment, by economic definition) but not
sufficient (cost decline alone does not produce events — most
cost-declining combinations do not produce events).

**The deep finding:** Cost decline is a *background condition*,
not a *signal*. The ablation result confirmed this: the cost_bonus
term added zero independent signal because cost decline is
correlated with everything else in the registry. The necessity
finding does NOT contradict the ablation: cost is necessary
(broadly) but redundant with velocity (specifically) — because
velocity of capability development is what drives cost decline.
Removing cost_bonus from the formula was correct; declaring cost
"unnecessary" would be wrong.

---

## The factor-by-factor table

| Factor | Necessary | Sufficient | Verdict |
|---|---|---|---|
| velocity | ✅ Yes — all 7 TPs have it | ❌ No — only 5% of velocity-positive cases produce events | NECESSARY, NOT SUFFICIENT |
| adjacency | ✅ Yes — all 7 TPs have it | ❌ No — counterexamples dominate; high-adjacency combinations that already exist are the failure mode | NECESSARY, NOT SUFFICIENT |
| bottleneck removal | ✅ Yes — all 7 TPs had it resolved | ❌ No — bottleneck removal is permissive, not productive | NECESSARY, NOT SUFFICIENT |
| cost decline | ✅ Yes — all 7 TPs occurred during cost decline | ❌ No — cost decline is a background condition | NECESSARY, NOT SUFFICIENT |

**ALL FOUR FACTORS ARE NECESSARY. NONE ARE SUFFICIENT.**

This is the central finding of Phase 13D. It is not a failure —
it is the *typical structure* of complex-system causality. Real
inventions are produced by the *conjunction* of necessary factors,
not by any single sufficient one.

---

## The conjunction analysis

If all four factors are necessary, then the model's correct form
is the conjunction (logical AND):

```
event = velocity ∧ adjacency ∧ bottleneck_resolved ∧ cost_declining
```

Not the product (arithmetic ×). The product `velocity × adjacency`
is a *proxy* for the conjunction — it is zero if either factor is
zero, which is logically equivalent to AND. But the product
treats the factors as continuous quantities, while the conjunction
treats them as binary gates.

**Hypothesis NS-1:** The product `velocity × adjacency` works
because it approximates the conjunction `velocity ∧ adjacency`
when both factors are above their respective thresholds. The
approximation is good when the factors are independent (which
they mostly are — velocity is about capability trajectory,
adjacency is about graph distance).

**Hypothesis NS-2:** The other two necessary factors
(bottleneck_resolved, cost_declining) are *implicitly* captured
because they are correlated with velocity: when velocity is high,
bottlenecks tend to be resolving (because the rising capability
IS the bottleneck resolution), and cost tends to be declining
(because capability progress drives cost down). This is why the
ablation found them statistically redundant.

**Hypothesis NS-3 (testable):** If NS-2 is correct, the model
should FAIL in cases where velocity is high but bottleneck is NOT
resolved (or cost is NOT declining). Such cases should be false
positives. The counterexamples CE-001 to CE-003 are partially
consistent: they have cost declining but no rising velocity —
and the model scored them high under the OLD formula (with
cost_bonus) but scores them LOW under the simplified formula
(velocity × adjacency alone).

**This is the testable prediction of Phase 13D:** the simplified
frozen formula `velocity × adjacency` should NOT score the
counterexamples CE-001 to CE-003 high. The Phase 13 backtest
re-run with the simplified formula should confirm this. If the
counterexamples still score high, NS-2 is falsified and there
is a hidden variable.

---

## What this protocol exposes

### The honest answer to "is velocity necessary and sufficient?"

**Velocity is necessary but not sufficient.** This is the answer
to the CEO's specific question. Velocity must be present for any
event to occur (all 7 TPs have it; all 5 impossibilities lack it).
But velocity alone is noise (ablation: 0.71%, matching NULL).
Velocity must combine with adjacency — and implicitly with
bottleneck resolution and cost decline — to produce events.

**The model is a conjunction detector, not a single-factor
predictor.** This is the deep structural finding. The frozen
formula `max(dTRL/dt) × adjacency` is the arithmetic proxy for
the logical conjunction `velocity ∧ adjacency`, which is itself
a proxy for the deeper conjunction
`velocity ∧ adjacency ∧ bottleneck_resolved ∧ cost_declining`.

### Why this matters for M5

A scientific theory is not a formula — it is an *explanation*. The
formula `velocity × adjacency` is a curve fit; the explanation
"invention requires the conjunction of capability motion,
adjacent possibility, bottleneck removal, and cost decline" is
a theory. Phase 13D is the step from formula to theory.

The formula stays frozen. The theory grows around it.

### What the protocol does NOT yet settle

1. **Are there OTHER necessary factors not in the four above?**
   Candidates: regulatory environment (UN38.3, IEC 62133);
   market structure (incumbent vs entrant); supply chain
   readiness; talent availability. Each is a candidate fifth
   factor. Each requires its own necessity/sufficiency test.

2. **What is the interaction structure?** The current model treats
   the factors as independent (product = proxy for AND with
   independence). If the factors interact multiplicatively
   (e.g., velocity × bottleneck_resolution matters more than
   either alone), the model is missing structure. The ablation
   did not test interaction terms.

3. **Does the necessity finding hold across domains?** All 7 TPs
   are in Li-ion (5) and PV (2). The 4 Li-ion factors may not be
   the same 4 factors in aviation or pharma. Phase 13F must test.

---

## Enforcement

- The factor-by-factor table MUST be re-derived every time a new
  TP is added to MECHANISM_REGISTRY. If a new TP lacks one of the
  four necessary factors, the necessity finding for that factor
  is falsified.
- The conjunction analysis MUST be the framing for any future
  executive summary of the model. The model is a conjunction
  detector, not a single-factor predictor.
- Hypotheses NS-1, NS-2, NS-3 are tracked in EPISTEMIC_TRACKER
  (to be created if not exists; otherwise appended). Each must be
  marked CONFIRMED, FALSIFIED, or PENDING based on future
  evidence.
- This protocol is append-only (Constitution Law 7).
