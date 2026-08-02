# CONVERGENCE — Phase 4 Definition

**Status:** definition stage only. Implementation forbidden.
**Phase:** 4 (per INVENTION_COMPILER.md roadmap).
**Read this file BEFORE writing any convergence-related code.**

> Phase 4 — Define convergence mathematically. Only after the
> definition exists should implementation begin.

This document is the deliverable for Phase 4. It is a **definition**,
not a module. No `convergence_*.py` file exists or should exist until
this definition has been validated against real-world evidence per the
plan in Section 5.

---

## 1. Definition

**Convergence** between two domains A and B is the structural
potential for them to share or exchange capabilities, measured as a
function of (a) whether one directly depends on the other, (b) how
many prerequisites they share, and (c) how topologically close they
are in the civilization graph.

The defining property: **convergence is a structural measurement, not
a temporal one.** It says "these two fields are connected" — it does
NOT say "they are getting closer over time." The latter requires
temporal data, which the graph does not yet have (see Section 4,
Failure Mode 3, and Signal E in Section 2).

This is a deliberate narrowing. A definition that conflates "connected
now" with "getting closer over time" would be vocabulary-without-
substance — the exact anti-pattern this project's audit history has
flagged repeatedly (F-018, F-021, F-024, F-026). The honest claim is:
**structural convergence is a necessary precondition for temporal
convergence, but is not by itself evidence of temporal convergence.**

The success criterion from the CEO directive is:

> Why are batteries and electric vehicles converging while batteries
> and desalination are not?

Operationally, this means: the formula in Section 3 must produce a
higher number for `(sub_battery_technology, sub_electric_propulsion)`
than for `(sub_battery_technology, sub_desalination)` when run
against the live graph. The numbers, computed by
`scripts/measure_convergence.py` against `data/civilization_graph.json`
at commit `b573b33`:

```
Convergence(battery, EV)           = 1.2000
Convergence(battery, desalination) = 0.0286
Delta: 1.1714
```

The formula discriminates. The definition is operationally meaningful.

---

## 2. Signals

Five candidate signals were considered (per the CEO directive).
Each is grounded in the live graph state at commit `b573b33`:

### Signal A' — direct dependency (refined from CEO's Signal A)

**What it measures:** does a direct `depends_on` or `requires` edge
exist between A and B in either direction?

**Unit:** binary (0 or 1).

**Why it is necessary:** it is the strongest possible structural
signal. If A directly depends on B, then a capability improvement in
B can propagate to A. This is the literal mechanism of "convergence"
in the engineering sense — one field's progress unlocks the other's.

**Live data:** EV has a direct `depends_on` edge to battery
(`sub_electric_propulsion --depends_on--> sub_battery_technology`).
No direct edge exists between battery and desalination.

**Note on refinement:** the CEO's original Signal A was "shared
prerequisites" (the overlap of A's prereqs and B's prereqs). On the
live graph, this signal is 0.0 for BOTH test pairs — it does not
discriminate. The refinement (Signal A') — does a direct prereq edge
exist between A and B themselves — is what actually discriminates.
The original Signal A is preserved as a secondary component of the
formula (Section 3) but contributes 0 to both test pairs in current
data.

### Signal A — shared prerequisite overlap (original CEO definition)

**What it measures:** |prereqs(A) ∩ prereqs(B)| / |prereqs(A) ∪ prereqs(B)|,
where prereqs are the targets of `depends_on` / `requires` edges
(excluding A and B themselves to avoid double-counting Signal A').

**Unit:** ratio in [0, 1].

**Why it is necessary:** two fields that share prerequisites (e.g.,
both depend on the same material, the same principle) are structurally
co-located — they share a common ancestor in the dependency graph,
which makes knowledge transfer possible.

**Live data:** 0.0 for both test pairs (battery and EV share no
prerequisites other than each other; battery and desalination share
none). The signal carries no discriminative information on the current
graph, but is retained in the formula because future ingestion may
populate shared prerequisites (e.g., if a future patent ingests a
component used by both desalination and battery technology, the signal
becomes non-zero and contributes).

### Signal B — constraint overlap

**What it measures:** |constraints(A) ∩ constraints(B)| /
|constraints(A) ∪ constraints(B)|, where constraints are the Law 2
constraint types with non-zero values.

**Unit:** ratio in [0, 1].

**Why it is necessary (in principle):** two fields bound by the same
constraints (energy, cost, manufacturing, etc.) face the same
engineering pressures, which creates pressure to share solutions.

**Live data:** 1.0 for both test pairs. The signal does NOT
discriminate. Reason: F-024 (Phase 2 priors fill all 10 constraint
slots uniformly across all nodes). Every node has all 10 constraint
types at non-zero values, so the overlap ratio is always 1.0.

**EXCLUDED from the convergence score (Section 3).** Carrying no
information, the signal is excluded until F-024 is fully resolved
(either by ingesting enough real constraints to produce variation, or
by re-deriving constraints with zero values for absent constraints).

### Signal C — component reuse

**What it measures:** |components(A) ∩ components(B)| /
|components(A) ∪ components(B)|, where components are the
component-typed nodes reachable from A or B via `contains` edges.

**Unit:** ratio in [0, 1].

**Why it is necessary:** if two fields share actual components
(membranes, catalysts, sensors, batteries), they can directly exchange
physical artifacts — the strongest form of convergence after direct
dependency.

**Live data:** 0.0 for both test pairs. The signal does NOT
discriminate. Battery and EV do not share component subtrees in the
current graph (their connection is via Signal A', not via shared
components). Battery and desalination share no components either.

**Retained in the formula** (Section 3) despite contributing 0 on the
current graph, because future ingestion that adds components under
battery and/or EV subdomains would make this signal non-zero.

### Signal D — graph topology (shortest path)

**What it measures:** the shortest path length between A and B in the
undirected graph (treating all edge types as traversable).

**Unit:** integer ≥ 0 (or None if unreachable).

**Why it is necessary:** even without direct dependency or shared
prerequisites, two fields may be close in the graph (e.g., both are
subdomains of the same domain). Short path = high potential for
indirect knowledge transfer.

**Live data:** 1 hop (battery↔EV) vs 7 hops (battery↔desalination).
The signal discriminates.

### Signal E — temporal convergence

**What it measures:** the rate of change of structural convergence
over time — is the pair getting closer?

**Unit:** convergence_score delta per unit time.

**Why it is necessary (in principle):** this is the only signal that
actually distinguishes "converging" from "similar." Two fields can
be highly structurally connected (Signals A-D high) without converging
— they may have been connected forever. True convergence requires
the connection to be NEW or GROWING.

**Live data:** NOT COMPUTABLE. Every node in the graph shares one
`created_at` timestamp (Phase 2 batch ingestion at
`2026-08-01T09:54:16Z`). There is no second snapshot to compare
against. Computing temporal convergence requires at least two graph
snapshots at different times — see Section 4, Failure Mode 3.

**EXCLUDED from the convergence score.** Cannot be computed on the
current graph. This is the single most important prerequisite for
Phase 4's evolution from a structural definition to a temporal one.

---

## 3. Formula

Given two nodes A and B in the civilization graph:

```
Convergence(A, B) =
    1.0 * direct_dependency(A, B)
  + 0.4 * shared_prereq_overlap_ratio(A, B)
  + 0.2 * component_overlap_ratio(A, B)
  + 0.2 * (1 / shortest_path(A, B))      if finite, else 0
  + 0.0 * constraint_overlap_ratio(A, B)  # EXCLUDED — F-024
  + 0.0 * temporal_convergence(A, B)      # EXCLUDED — no snapshots
```

Where:

- `direct_dependency(A, B)` ∈ {0, 1}: 1 if any `depends_on` or
  `requires` edge exists between A and B in either direction.
- `shared_prereq_overlap_ratio(A, B)` ∈ [0, 1]: the Jaccard
  similarity of A's prereqs and B's prereqs (excluding A and B
  themselves).
- `component_overlap_ratio(A, B)` ∈ [0, 1]: the Jaccard similarity
  of the component subtrees of A and B.
- `1 / shortest_path(A, B)` ∈ (0, 1]: inverse of undirected shortest
  path length. 1.0 if A == B. 0 if unreachable.
- `constraint_overlap_ratio(A, B)`: EXCLUDED. Weight 0. F-024 makes
  this signal uniform across all pairs.
- `temporal_convergence(A, B)`: EXCLUDED. Weight 0. Not computable
  on a single-snapshot graph.

**Score range:** [0, 1.6]. The maximum (1.0 + 0.4 + 0.2 + 0.2 = 1.6)
is achieved when A and B directly depend on each other, share all
prerequisites, share all components, and are at path length 1.

**Weights — justification:** the weights encode a strict priority
ordering:

1. Direct dependency (weight 1.0) is the strongest possible signal —
   one field literally requires the other.
2. Shared prerequisites (weight 0.4) is weaker — common ancestors
   enable knowledge transfer but don't guarantee it.
3. Component reuse (weight 0.2) is weaker still — shared physical
   artifacts could mean convergence OR could mean one field cannibalized
   the other's parts.
4. Path length (weight 0.2, inverse) is the weakest — being nearby in
   the graph enables but does not require interaction.

The weights are PRIORS, not fitted constants. They are not calibrated
against real-world convergence outcomes (no such data exists yet —
see Section 5). They are honest about being priors: any future
calibration must be recorded in the ledger per Law 8.

**Live numbers (computed by scripts/measure_convergence.py at
commit b573b33):**

```
Convergence(battery, EV):
    direct_dependency      = 1.0       (1.0 * 1.0 = 1.0000)
    shared_prereq_overlap  = 0.0       (0.4 * 0.0 = 0.0000)
    component_overlap      = 0.0       (0.2 * 0.0 = 0.0000)
    1/shortest_path        = 1.0       (0.2 * 1.0 = 0.2000)
    constraint_overlap     = 1.0       EXCLUDED
    temporal               = N/A       EXCLUDED
    TOTAL                              = 1.2000

Convergence(battery, desalination):
    direct_dependency      = 0.0       (1.0 * 0.0 = 0.0000)
    shared_prereq_overlap  = 0.0       (0.4 * 0.0 = 0.0000)
    component_overlap      = 0.0       (0.2 * 0.0 = 0.0000)
    1/shortest_path        = 1/7       (0.2 * 0.143 = 0.0286)
    constraint_overlap     = 1.0       EXCLUDED
    temporal               = N/A       EXCLUDED
    TOTAL                              = 0.0286

DELTA = 1.1714  (formula discriminates — success criterion met)
```

---

## 4. Failure modes

Per Law 6 (CONSTITUTION.md: "The engine may not explain the future
without exposing the assumptions that produced it"), the failure modes
of this measurement are:

### Failure Mode 1 — "Similar" misread as "converging"

**Description:** the formula measures STRUCTURAL connectedness, not
TEMPORAL convergence. Two fields can be highly structurally connected
without converging — they may have been connected forever.

**Impact:** an analyst reading "Convergence(battery, EV) = 1.2" might
infer "battery and EV are getting closer over time." The formula does
not say that. It says "battery and EV are structurally connected now."

**Mitigation:** the spec is honest about this (Section 1, Section 2
Signal E). Any consumer of the score MUST be told that the score is
structural, not temporal. The word "convergence" is retained only
because the CEO's directive uses it; consumers should read it as
"structural convergence potential" until Signal E becomes computable.

### Failure Mode 2 — Uniform constraint data (F-024)

**Description:** Signal B (constraint overlap) is currently 1.0 for
every pair in the graph because Phase 2 priors fill all 10 constraint
slots uniformly.

**Impact:** the signal carries no discriminative information. If it
were included in the score with a non-zero weight, every pair would
receive the same bonus from it, contributing nothing but noise.

**Mitigation:** EXCLUDED from the score (weight 0.0). The exclusion
is explicit in the formula. When F-024 is fully resolved (real
constraint variation across nodes), the weight should be re-evaluated
— but only after re-deriving the formula against the new data, not
before.

### Failure Mode 3 — No temporal data exists

**Description:** Signal E (temporal convergence) cannot be computed
because the graph has only one snapshot. Every node shares one
`created_at` timestamp.

**Impact:** the formula cannot distinguish "fields that are
converging" from "fields that are similar." This is the single most
important limitation of the current definition.

**Mitigation:** Signal E is EXCLUDED from the score (weight 0.0). The
validation plan (Section 5) explicitly requires at least one more
graph snapshot before this signal can contribute. The honest framing:
**the current definition measures structural connectedness, not
convergence in the temporal sense. Calling it "convergence" is a
forward-promissory naming — the temporal dimension will be added when
the data exists.**

### Failure Mode 4 — Trivial prerequisite overlap

**Description:** two fields might share a prerequisite like
"electricity" or "manufacturing" that is so generic it carries no
information about convergence.

**Impact:** the shared_prereq_overlap_ratio would be non-zero for
pairs that aren't actually converging — just trivially similar.

**Mitigation:** none yet. The current graph has 0 shared prereqs for
both test pairs, so this failure mode is not active. When future
ingestion produces non-zero shared prereqs, the formula should be
re-examined — possibly by weighting prereqs by their inverse frequency
(a rare shared prereq is more informative than a common one).

### Failure Mode 5 — Direct dependency ≠ convergence direction

**Description:** a `depends_on` edge A → B means A requires B, but
the convergence is asymmetric — B's progress unlocks A, not the
reverse. The formula treats direct_dependency as symmetric (1.0
regardless of direction).

**Impact:** for the battery↔EV case, this is correct (EV depends on
battery, so battery progress unlocks EV — they ARE converging). But
for other pairs, an asymmetric dependency might not indicate
convergence.

**Mitigation:** the formula's symmetry is a deliberate simplification.
Future iterations may want to distinguish "A depends on B" from "B
depends on A" from "both depend on each other." For now, the
simplification is honest about being a prior.

### Failure Mode 6 — Formula weights are priors, not fitted constants

**Description:** the weights (1.0, 0.4, 0.2, 0.2) are not calibrated
against real-world convergence outcomes. They are priors chosen by
inspection.

**Impact:** the absolute convergence score is not meaningful — only
the RELATIVE score between two pairs is. A score of 1.2 doesn't mean
"highly converging"; it means "more structurally connected than a
pair scoring 0.03."

**Mitigation:** the spec is explicit that weights are priors (Section
3). Calibration requires real-world convergence outcomes (Section 5),
which do not yet exist. The first calibration will be recorded in the
ledger per Law 8.

---

## 5. Validation plan

Per principle #4 ("A capability isn't shipped until it writes to the
system of record") and Law 6 ("expose assumptions"), the definition
is falsifiable. The validation plan:

### Validation pair 1: (sub_battery_technology, sub_electric_propulsion)

**Predicted score:** 1.2000 (computed against live graph).

**Real-world claim:** batteries and electric vehicles ARE converging
in the real world — EV adoption is driving battery R&D, and battery
improvements unlock new EV categories.

**Falsification:** if, by 2028-01-01, the EV industry has NOT
increased its dependence on battery R&D (measured by: number of
joint industry-academia battery/EV research collaborations, or
share of EV-industry R&D budget allocated to battery chemistry),
the structural convergence score of 1.2 was misleading — it
indicated connection, but the connection was not becoming more
consequential over time.

**Resolution date:** 2028-01-01.

### Validation pair 2: (sub_battery_technology, sub_desalination)

**Predicted score:** 0.0286 (computed against live graph).

**Real-world claim:** batteries and desalination are NOT converging
in the real world — desalination is bound by membrane and thermal
constraints, not by energy storage. Even though battery improvements
could marginally help desalination (e.g., solar-powered RO plants),
the structural connection is weak.

**Falsification:** if, by 2028-01-01, a major desalination technology
shift occurs that is PRIMARILY enabled by battery improvements (e.g.,
>20% of new desalination capacity uses battery-based energy storage
as a core component, not just an auxiliary), the structural
convergence score of 0.03 was misleading — it missed a real
convergence that the graph did not represent.

**Resolution date:** 2028-01-01.

### Pre-validation prerequisite: a second graph snapshot

Both validation pairs require a SECOND graph snapshot to test
whether the convergence score CHANGES over time. Without a second
snapshot, the validation can only test the STRUCTURAL claim (are
the pairs connected differently?), not the TEMPORAL claim (are they
getting closer?).

**Action item (blocking):** before the validation plan can be
executed, the system must produce at least one more Phase 3 ingestion
cycle. The new ingestion will:
1. Add new nodes/edges (real patents/papers, not synthetic).
2. Be snapshotted at a different `created_at` timestamp.
3. Enable a second measurement of the convergence score, which can
   be compared against the first.

Without this, the validation plan can only confirm structural
discrimination (which is already done — Section 3), not temporal
convergence (which is the actual scientific claim).

### What this definition does NOT yet validate

- **It does not validate the weights.** The weights (1.0, 0.4, 0.2,
  0.2) are priors. Real validation of the weights requires a
  calibration set of (pair, real-world-outcome) tuples, which does
  not exist yet.
- **It does not validate the formula's predictive power.** The
  formula describes current structural state, not future convergence.
  Predictive validation requires the temporal dimension (Signal E).
- **It does not validate against more than two pairs.** The CEO's
  success criterion named two; the spec validates against those two.
  Future validation should expand to at least 5-10 pairs spanning
  "obviously converging," "obviously not converging," and "unclear"
  cases.

---

## Explicit prohibition

Per the CEO directive, no Python module with "convergence" in its
name may be created during Phase 4. Specifically:

- `convergence_module.py` — FORBIDDEN
- `convergence_engine.py` — FORBIDDEN
- `convergence_layer.py` — FORBIDDEN
- `convergence_agent.py` — FORBIDDEN

The single `scripts/measure_convergence.py` is a ONE-OFF MEASUREMENT
SCRIPT, not a module. It is NOT imported by any other file. Its output
(the convergence numbers in Section 3) is pasted into this document
and the commit message. The script is committed for reproducibility
(Law 7: historical permanence) but is not a module.

If a future phase needs convergence as a runtime capability, that
phase must:
1. Demonstrate that the validation plan in Section 5 has produced at
   least one (pair, real-world-outcome) tuple.
2. Re-derive the formula against the validated data.
3. Only then create a module — and the module must be named honestly
   per the "use the word 'engine' honestly" rule (it's a module until
   validated, not an engine).

---

## Success criterion — answered

> Why are batteries and electric vehicles converging while batteries
> and desalination are not?

**Answer:** because `sub_electric_propulsion --depends_on-->
sub_battery_technology` is a direct edge in the graph (Signal A' = 1.0),
while no direct or near-direct structural connection exists between
battery and desalination (shortest path = 7 hops, contributing only
0.0286 to the score). The convergence scores are 1.2000 vs 0.0286,
a delta of 1.1714.

**Honest caveat:** this answer describes STRUCTURAL connectedness, not
TEMPORAL convergence. The system cannot yet answer "are they getting
closer over time" — that requires a second graph snapshot (Section 5,
pre-validation prerequisite).

---

## Implementation status

- **Definition:** COMPLETE (this document).
- **Measurement script:** COMPLETE (`scripts/measure_convergence.py`,
  one-off, not imported by anything).
- **Discrimination against success-criterion pairs:** VERIFIED
  (1.2000 vs 0.0286, delta 1.1714).
- **Validation against real-world outcomes:** NOT STARTED. Requires
  (a) a second graph snapshot and (b) time to pass (resolution dates
  2028-01-01 for both pairs).
- **Convergence module:** FORBIDDEN. Not created.
- **Phase 4 status:** definition complete. Implementation forbidden
  until validation plan executes.
