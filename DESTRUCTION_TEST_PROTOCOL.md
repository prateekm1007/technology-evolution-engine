# DESTRUCTION_TEST_PROTOCOL

**Status:** Phase 14E protocol.
**Location:** repo root.
**Phase:** 14E.

> The objective is to break the theory.
> — CEO directive, Phase 14E

---

## Purpose

The destruction tests are the falsification battery for the
susceptibility theory. Each test asks whether a component of the
theory (velocity, adjacency, bottleneck removal) can exist without
the outcome (invention), or whether the outcome can exist without
a component. If the answer is "yes" in a way the theory does not
predict, the theory is damaged or falsified.

Per EP-4, every explanatory claim must have a pre-stated
falsification condition. This document pre-states the falsifiers
for each destruction question BEFORE the tests run. The tests
are committed as a protocol; the results commit later,
separately.

---

## The five destruction questions

### D1: Can adjacency exist without invention?

**Theory claim:** Adjacency is necessary for invention. A
combination that is adjacent (graph distance ≤ 2) to existing
combinations is more likely to produce invention than one that
is distant.

**Test:** Search the backtest data across all domains for
combinations with adjacency > 0.5 (graph distance ≤ 1) that
did NOT produce an invention event within the 5-year horizon.
These are "adjacent but no invention" cases.

**Falsifier:** If the rate of invention among adjacent
combinations is NOT significantly higher than the rate among
distant combinations (graph distance > 3), adjacency is not
a necessary factor. Specifically: if
`P(invention | adjacency > 0.5) ≤ P(invention | adjacency < 0.3) + 0.05`,
adjacency is falsified as a necessary factor.

**What survival looks like:** `P(invention | adjacency > 0.5)`
is at least 2x `P(invention | adjacency < 0.3)` across all
domains, OR the McNemar test on adjacency-present vs
adjacency-absent is significant at p < 0.10.

---

### D2: Can velocity exist without invention?

**Theory claim:** Velocity (rising TRL) is necessary for
invention. A capability with dTRL/dt > 0.20 is more likely
to produce invention than one with zero velocity.

**Test:** Search the backtest data for combinations with
velocity > 0.20 that did NOT produce an invention event
within the 5-year horizon. These are "velocity but no
invention" cases — the false positives.

**Falsifier:** If the rate of invention among high-velocity
combinations is NOT significantly higher than among
zero-velocity combinations, velocity is not necessary.
Specifically: if
`P(invention | velocity > 0.20) ≤ P(invention | velocity = 0) + 0.05`,
velocity is falsified as a necessary factor.

**What survival looks like:** `P(invention | velocity > 0.20)`
is at least 2x `P(invention | velocity = 0)` across all
domains. NOTE: the current Li-ion data has 5 TPs all with
velocity > 0.20, and 135 FPs also with velocity > 0.20
(under the OLD formula with cost_bonus). Under the SIMPLIFIED
formula, the FP count among velocity > 0.20 combos needs
re-computation. This test will use the simplified formula.

**Caveat (per SCOPE_CHANGE_SUSCEPTIBILITY.md):** Under the
susceptibility framing, velocity-without-invention is EXPECTED
— susceptibility does not guarantee invention. D2 tests whether
velocity is necessary, not sufficient. If D2 finds many
velocity-without-invention cases, that is consistent with
susceptibility; it is only falsifying if velocity-without-invention
is as common as zero-velocity-without-invention (i.e., velocity
adds no predictive power).

---

### D3: Can bottleneck removal exist without invention?

**Theory claim:** Bottleneck removal is necessary for invention.
When a blocking constraint is resolved, the combination becomes
reachable.

**Test:** Search the backtest data for cases where a documented
bottleneck was resolved (per BOTTLENECK_REGISTRY.md) but no
invention event followed within 5 years. These are
"bottleneck-removed but no invention" cases.

**Falsifier:** If the rate of invention after bottleneck removal
is NOT significantly higher than the rate without bottleneck
removal, bottleneck removal is not necessary. Specifically: if
`P(invention | bottleneck resolved) ≤ P(invention | bottleneck active) + 0.05`,
bottleneck removal is falsified as a necessary factor.

**What survival looks like:** `P(invention | bottleneck resolved)`
is at least 2x `P(invention | bottleneck active)` across all
domains.

**Caveat:** This test requires a bottleneck registry for each
domain. The bottleneck registry must be built BEFORE the test
runs (per EP-3). Bottleneck identification cannot be retrospective
on the events being tested.

---

### D4: Can invention exist without velocity?

**Theory claim:** Velocity is necessary for invention. No event
should occur without a rising capability (dTRL/dt > 0.20) in
the combination.

**Test:** Search the EVENT_REGISTRY across all domains for
events whose combination has NO capability with velocity > 0.20
at T-1. These are "invention without velocity" cases.

**Falsifier:** If ANY event in any domain occurs without
velocity > 0.20 in its combination at T-1, the necessity claim
(FEC-002) is falsified. This is a strict test — a single
counterexample falsifies.

**What survival looks like:** Zero events with zero velocity
across all domains. The current Li-ion data has 7 TPs all with
velocity > 0.20 (per MECHANISM_REGISTRY.md), but the
pre-1990 TRL gap contaminates T=1991 and T=1993 (per
PHASE_13_OPEN_ITEMS_RESOLUTION.md). Clean T-points (T ≥ 1995)
must be used.

**Caveat:** This is the strongest destruction test. If it fails
(even one invention occurs without velocity), the necessity
claim is falsified and the theory must be revised. The theory
may survive as "velocity is correlated with invention" but not
as "velocity is necessary."

---

### D5: Can invention exist without adjacency?

**Theory claim:** Adjacency is necessary for invention. No event
should occur in a combination that is graph-distance > 3 from
existing combinations.

**Test:** Search the EVENT_REGISTRY for events whose combination
has graph distance > 3 from all prior realized combinations at
T-1. These are "invention without adjacency" cases.

**Falsifier:** If ANY event occurs at graph distance > 3, the
adjacency necessity claim is falsified. Strict test — single
counterexample falsifies.

**What survival looks like:** All events occur at graph distance
≤ 3 from prior combinations. The current Li-ion data has all
TPs at graph distance 1-2 (per ADJACENCY_REGISTRY.md).

**Caveat:** The graph-distance threshold (3) is calibrated to
Li-ion. Other domains may have different graph structures. If
a domain's natural graph-distance distribution is larger (e.g.,
semiconductor node jumps), the threshold may need domain
calibration — but that calibration must be pre-committed
(per EP-6), not adjusted post-hoc.

---

## Test execution protocol

For each destruction test:

1. **Pre-state the test** (done in this document — the 5 tests
   above are pre-stated before any domain backtest runs).
2. **Run the test** on each domain as its backtest completes.
   The test is a query against the domain's backtest output.
3. **Record the result** as a new entry in
   `DESTRUCTION_TEST_RESULTS.md` (to be created when the first
   domain's tests run). Each entry:
   - Test ID (D1-D5)
   - Domain
   - Result (SURVIVES / FALSIFIED / INCONCLUSIVE)
   - Evidence (specific events or combinations)
   - Impact on the theory
4. **Update FEC entries** if a test falsifies a claim in
   `EVIDENCE_FALSIFIERS.md`.

---

## What this protocol does NOT do

- It does not run the tests. The tests run per-domain as each
  backtest completes. This document only pre-states the protocol.
- It does not define the verdict for the overall theory. The
  verdict is determined by PHASE_14_ADVANCEMENT_CRITERIA.md,
  which includes destruction-test survival as condition 4.
- It does not authorize post-hoc test modification. If a test
  produces an unexpected result, the test is not re-defined to
  accommodate it — the result is recorded, and the theory is
  updated (or rejected) accordingly.

---

## Interaction with the susceptibility scope change

Under the susceptibility framing (SCOPE_CHANGE_SUSCEPTIBILITY.md),
D1 and D2 are partial tests of necessity, not sufficiency. D1 asks
"can adjacency exist without invention?" — under susceptibility,
the answer is yes (susceptibility ≠ inevitability). But D1's
falsifier is not "any adjacent case without invention"; it is
"adjacency does not increase invention rate." This is the correct
test under susceptibility.

D4 and D5 are strict tests of necessity. Under susceptibility,
these are the load-bearing tests. If invention occurs without
velocity or without adjacency, the theory is falsified — not
because susceptibility requires inevitability, but because
susceptibility requires the necessary factors to be present.

D3 (bottleneck removal) is a partial test of necessity. Under
susceptibility, bottleneck removal is necessary (a blocked
landscape is not susceptible). But bottleneck removal without
invention is expected (susceptibility ≠ inevitability).

The destruction tests therefore align with the susceptibility
framing: D1, D2, D3 test whether the factors increase invention
rate (necessary in the sense of "increases probability"); D4, D5
test whether the factors are strictly necessary (no event without
them).
