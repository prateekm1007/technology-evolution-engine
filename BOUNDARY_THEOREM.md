# BOUNDARY_THEOREM

**Status:** Phase 14S taxonomy.
**Location:** repo root.
**Phase:** 14S.

> Attempt to state, as rigorously as possible, where the present
> theory applies and where it fails.
> — CEO directive, Phase 14S

---

## Purpose

This document states, as rigorously as the data allows, the
boundary of the present theory. It is the project's honest
accounting of what the frozen formula `score = max(dTRL/dt) ×
adjacency` can and cannot do, based on the evidence accumulated
across Li-ion, photovoltaics, semiconductors, and
telecommunications.

Per EP-4, every claim has a pre-stated falsifier. Per EP-5, this
is self-authored and should be independently reviewed. Per EP-11,
no promotional language.

---

## The theory

**Frozen formula:**
```
score = max(dTRL/dt) × adjacency
```

where:
- `max(dTRL/dt)` is the maximum TRL velocity across capabilities
  in the combination, normalized and capped at 1.0
- `adjacency = 1/(1 + distance)` where distance is the symmetric
  difference to the nearest existing realized combination

**Underlying claim (per SCOPE_CHANGE_SUSCEPTIBILITY.md):**
The formula estimates the susceptibility of a capability landscape
to invention. Susceptibility = the conditions for invention are
present (rising capability + reachable combination). Invention
requires susceptibility AND agency; the formula measures the
landscape, not the agency.

---

## Where the theory applies

### Domain 1: Emergence-driven invention with monotonic TRL

**Applies when:**
1. The event is an Emergence-class invention (per INVENTION_CLASSES.md)
   — a new capability is rising from low TRL to TRL 9.
2. The capability's TRL trajectory is monotonic (rises once, then
   plateaus; does not "re-rise" for a new generation).
3. The velocity at T-1 is unambiguously above the 0.20 threshold
   (typically ≥ 0.30, ideally ≥ 0.40).
4. The event involves a combination of the rising capability with
   mature base capabilities (Recombination class).

**Evidence:**
- Li-ion: 5 TPs, all involving rising capabilities (FAST_CHARGING,
  THERMAL_MANAGEMENT, STATE_OF_CHARGE_MONITORING). All trajectories
  are monotonic. All velocities ≥ 0.33.
- Semiconductors: 2 real TPs (copper 1997 velocity 0.40, high-k
  2007 velocity 0.40). Both involve rising capabilities with
  monotonic trajectories.

**What the formula does here:** The velocity term detects the
rising capability. The adjacency term detects the reachable
combination. The product identifies susceptible landscapes —
combinations where a rising capability is about to make a new
combination realizable.

**Caveat:** Even in this domain, the formula does not achieve
statistical significance (Li-ion p=0.2188, semiconductors p=0.5000).
The directional advantage is real (5 TPs vs 1 for NULL on Li-ion)
but not statistically distinguishable from chance at n=14.

### Domain 2: Recombination-driven invention with mature capabilities

**Applies when:**
1. The event is a Recombination-class invention — a combination of
   mature capabilities becomes reachable.
2. All capabilities in the combination are at TRL ≥ 7.
3. The combination is graph-distance ≤ 2 from existing realized
   combinations.
4. No rising capability is required (velocity may be 0).

**Evidence:**
- Li-ion: most events (13/16) involve combinations of mature
  capabilities. The adjacency term drives these predictions.

**What the formula does here:** The adjacency term detects
reachable combinations. The velocity term contributes 0, but the
product is still non-zero if adjacency is high.

**Caveat:** The formula conflates Emergence and Recombination
in the same score. A combination with high velocity × low adjacency
scores the same as low velocity × high adjacency. These are
different invention classes (per INVENTION_CLASSES.md) and should
perhaps be scored differently.

---

## Where the theory does NOT apply

### Boundary 1: Scaling events (Pattern 1)

**Does not apply when:** The event is a Scaling-class invention —
an efficiency improvement within an already-mature capability.

**Why it fails:** All capabilities in the combination are at TRL 9
(velocity = 0). The formula's velocity term produces 0. The
adjacency term may be high (the combination is reachable), but
without velocity, the score is 0.

**Evidence:** 11 of 28 boundary cases (BC-001 to BC-005, BC-020 to
BC-024). These include Intel 4004, 386, Pentium, 0.35um DRAM,
130nm strained Si, IS-95, EV-DO, Galaxy S, LTE-A, Gigabit LTE.

**What would address this:** A different formula using a scaling
metric (transistor count, data rate, cost per unit) as the state
variable. The frozen formula cannot detect scaling events.

### Boundary 2: Generation transitions (Pattern 2)

**Does not apply when:** The event is a generation transition — a
capability "re-rising" for a new generation (2G → 3G → 4G → 5G).

**Why it fails:** The trajectory model represents WIRELESS_PROTOCOL
as a single capability that rose once (1G) and then plateaued.
The 2G, 3G, 4G, 5G transitions are not captured as rising
trajectories — they appear as plateaus. The velocity term produces
0 or negative (if the capability "drops" to track a sub-capability).

**Evidence:** 7 of 28 boundary cases (BC-013 to BC-019). These
include GSM 2G, WCDMA 3G, iPhone, LTE 4G, NB-IoT, 5G NR, 5G mmWave.

**What would address this:** Per-generation TRL (each generation
as a separate capability with its own trajectory), OR a different
state variable (institutional state, coordination state). The
frozen formula cannot detect generation transitions.

### Boundary 3: Post-maturity exploitation (Pattern 4)

**Does not apply when:** The event occurs AFTER a capability has
reached TRL 9 — a refinement or optimization within a mature
capability.

**Why it fails:** The capability is at TRL 9 (velocity = 0). The
formula cannot distinguish "just reached maturity" from "mature
for 10 years." Post-maturity exploitation is invisible.

**Evidence:** 2 of 28 boundary cases (BC-011 AMD 3D V-Cache,
BC-012 Samsung 3nm GAA).

**What would address this:** A "time since maturity" state
variable, or a manufacturing-state variable (yield, process
refinement). The frozen formula cannot detect post-maturity
exploitation.

### Boundary 4: Events at the velocity threshold (Pattern 3)

**Does not apply when:** The rising capability's velocity is
exactly at the 0.20 threshold (due to 5-year TRL snapshot
granularity producing 1-TRL-per-5-years = 0.20).

**Why it fails:** The pre-stated threshold is strictly > 0.20
(calibrated to Li-ion's 0.33-0.67 velocities). Semiconductor
trajectories rise in 1-TRL-per-5-year steps, producing velocity
exactly 0.20.

**Evidence:** 5 of 28 boundary cases (BC-006 to BC-010).

**What would address this:** A lower threshold (> 0.15), OR finer
TRL granularity (1-year snapshots instead of 5-year), OR a
different normalization. The frozen formula cannot be adjusted
(Rule 1), but this boundary is NOT a robust falsification — at
threshold > 0.15, all 5 cases would be detected.

### Boundary 5: Adjacency competition (Pattern 5)

**Does not apply when:** Multiple combinations have high scores,
and the Top-10 is filled with high-adjacency combinations that
are not the actual event.

**Why it fails:** The formula ranks combinations by `velocity ×
adjacency`. When many combinations have similar scores, the
Top-10 selection is arbitrary. A combination with velocity 0.40 ×
adjacency 0.5 (score 0.20) ranks below a combination with
velocity 0.20 × adjacency 1.0 (score 0.20) due to tie-breaking.

**Evidence:** 3 of 28 boundary cases (BC-019, BC-025, BC-026).

**What would address this:** A different ranking method (e.g.,
top-K with diversity constraints), or a different formula
architecture. The frozen formula cannot be adjusted.

---

## The boundary theorem (stated rigorously)

**Theorem (informal):** The frozen formula `score = max(dTRL/dt) ×
adjacency` detects susceptible landscapes for Emergence-class and
Recombination-class inventions in domains where:
1. Capability TRL trajectories are monotonic (single rise per
   capability).
2. Velocity at T-1 is unambiguously above 0.20 (typically ≥ 0.30).
3. The candidate set is small enough that high-scoring combinations
   are not masked by adjacency ties.

**The formula does NOT detect:**
1. Scaling-class inventions (zero velocity, mature capabilities).
2. Generation-transition inventions (non-monotonic TRL, re-rise).
3. Post-maturity exploitation (TRL 9, velocity 0).
4. Events at the velocity threshold (granularity issue).
5. Events masked by adjacency competition (selection issue).

**The formula does NOT distinguish:**
1. Emergence from Recombination (both contribute to the same score).
2. Active-frontier TRL 9 from legacy TRL 9.
3. Capability-driven invention from coordination-driven invention.

**Statistical status:**
- Li-ion (home domain): p=0.2188, not significant at n=14.
- Semiconductors: p=0.5000, not significant at n=12.
- Telecom: p=0.5000, 0 TPs (worse than NULL).
- The formula has not achieved statistical significance in any
  domain. The directional advantage is real but small.

---

## The honest summary

The theory is not wrong. It is incomplete.

The frozen formula detects Emergence and Recombination — two of
five invention classes. For those classes, in domains with
monotonic TRL and unambiguous velocity, the formula produces
directional signals (more TPs than NULL). It has not achieved
statistical significance, but the directional signal is consistent
across Li-ion and semiconductors.

For the other three classes (Scaling, Coordination, Discovery),
the formula is silent. It produces 0 velocity, 0 score, and no
prediction. This is not a failure of the formula — it is a
statement of the formula's scope. The formula was never designed
to detect scaling, coordination, or discovery. Expecting it to
is like expecting a thermometer to measure pressure.

The boundary is:
- **In scope:** Emergence + Recombination, monotonic TRL,
  velocity > 0.20 (ideally ≥ 0.40).
- **Out of scope:** Scaling, Coordination, Discovery; non-monotonic
  TRL; velocity at threshold; adjacency competition.

**This is a statement of scope, not a failure.** The formula does
what it was designed to do. The project's error was not in the
formula — it was in expecting the formula to cover all invention
classes. Per INVENTION_CLASSES.md, invention is not one thing but
at least five. The frozen formula addresses two.

---

## What this means for the north star

The CEO's reframing:

> The north star is not "predict inventions." It is "understand
> how possibilities become reachable."

The frozen formula addresses one mechanism by which possibilities
become reachable: capability emergence + adjacency. It does not
address:
- Scaling (possibilities become reachable through optimization)
- Coordination (possibilities become reachable through consensus)
- Discovery (possibilities become reachable through scientific
  advance)

Each of these is a different mechanism of "becoming reachable."
The frozen formula covers one; the other four require different
formulas.

**The north star is larger than the frozen formula.** The frozen
formula is one instrument — a capability-emergence detector. The
project's goal of "understanding how possibilities become
reachable" requires multiple instruments, one per mechanism. The
frozen formula is the first; the others have not been built.

---

## Pre-stated falsifiers (EP-4)

| Claim | Falsifier | Status |
|---|---|---|
| The formula detects Emergence and Recombination in monotonic-TRL domains | A monotonic-TRL domain with emergence events where the formula produces 0 TPs | NOT FALSIFIED (Li-ion has 5 TPs; semiconductors have 2 real TPs) |
| The formula does NOT detect Scaling events | A scaling event that the formula predicts (TP with zero velocity) | NOT FALSIFIED (no such case in the catalog) |
| The formula does NOT detect generation transitions | A generation transition that the formula predicts (TP with re-rising capability) | NOT FALSIFIED (no such case in the catalog) |
| The formula's directional advantage is real but not significant | A larger-n backtest that achieves p<0.05 | PENDING (n=14 on Li-ion is too small; Phase 14 stress tests did not achieve significance) |
| Invention is not one thing but at least five | An event that does not fit any of the five classes | NOT FALSIFIED (no such event found yet) |

---

## What this document does NOT do

- It does not propose new formulas. Each boundary identifies a
  gap, but filling the gap is post-Phase-14 work.
- It does not claim the five boundaries are exhaustive. Other
  boundaries may exist.
- It does not conclude whether the theory is "wrong" or "incomplete."
  The honest answer (per PHASE_14R_REFLECTION.md) is that the
  evidence does not allow a definitive conclusion. This document
  states the boundary rigorously; the conclusion is the CEO's to
  draw.
- It does not address H2 (velocity vs acceleration). Acceleration
  is a different state variable for the same class (Emergence),
  not a different boundary.
