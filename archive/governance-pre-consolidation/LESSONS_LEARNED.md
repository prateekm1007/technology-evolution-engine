# LESSONS_LEARNED

**Status:** Project archival document.
**Location:** repo root.
**Phase:** 14 (closing).

> That document may ultimately prove more valuable than the code.
> It would preserve the evolution of the ideas themselves instead
> of merely preserving the implementation.
> — CEO directive, Phase 14 close

---

## Purpose

This document is the project's honest accounting of its own
intellectual evolution. It records what was believed, what
survived, what failed, what was learned, and what remains
unknown.

The document is self-authored (per EP-5, not independently
graded) and should be read as reflection, not evidence. Specific
claims about the model's performance are cited to committed
artifacts; the broader lessons are interpretive.

---

## 1. What was believed initially

### The original hypothesis (Phase 1-5)

The project began with the **co-occurrence model**:

```
documents → components → shared labels → convergence score → invention prediction
```

The belief was that if two domains shared enough component labels
in their source documents (patents, papers), they were "converging"
and would produce inventions at their intersection. The
convergence score `Signal C = shared_components / total_components`
was the predictor.

The underlying assumption: **invention is a single phenomenon
driven by the intersection of previously separate domains**. One
model, one formula, one signal.

### The original north star

```
predict inventions
```

The goal was to predict which capability combinations would
produce invention events within a 5-year horizon. Precision
was the metric. Beating NULL_MODEL was the threshold.

### The original scope

```
electrochemical energy storage (broadly)
```

The model was scoped to all of electrochemical energy storage —
batteries, fuel cells, supercapacitors. The belief was that the
methodology would generalize within this scope.

### The original confidence

High. The belief was that with enough documents, enough component
extraction, and enough convergence measurement, the model would
predict inventions. The Phase 5 baseline (669 nodes, 40 tests) was
treated as a foundation to build on, not a ceiling to question.

---

## 2. What survived

### 2.1 The trajectory-velocity insight

**Original claim (Phase 10):** Invention happens when capabilities
are CHANGING, not when they are stable. Use `dTRL/dt` instead of
TRL.

**Status:** SURVIVED. This is the project's most defensible
insight. It appears in:
- Li-ion: all 5 TPs involve rising-capability velocity > 0.20.
- Semiconductors: the 2 real TPs (copper 1997, high-k 2007) involve
  velocity 0.40.
- The frozen formula `max(dTRL/dt) × adjacency` is built on this
  insight.

**Caveat:** The signal is directional, not statistically significant
(Li-ion p=0.2188, semiconductors p=0.5000). The insight is real;
the predictive power is weak at small n.

### 2.2 The adjacency insight

**Original claim (Phase 10):** Invention happens CLOSE to existing
combinations, not far away. Use `1/(1+distance)` instead of
novelty metrics.

**Status:** SURVIVED. The adjacency term correctly identifies
reachable combinations. All TPs in all domains are at graph
distance ≤ 2 from existing realized combinations.

**Caveat:** Adjacency alone produces 0 TPs (per the ablation,
adjacency-only = NULL_MODEL level). Adjacency is necessary but
not sufficient — it requires velocity to discriminate.

### 2.3 The frozen-formula discipline

**Original claim (Phase 11):** Formula B must be frozen. New data
tests the frozen formula; the formula does not adapt to new data.

**Status:** SURVIVED. The formula was frozen at Phase 11 and has
not been modified through Phase 14. Every backtest since (Li-ion
expanded, PV generalization, semiconductor stress test, telecom
stress test) used the same formula. The discipline prevented the
project from curve-fitting.

**Caveat:** The frozen formula may be too narrow (it covers only
2 of 5 invention classes, per INVENTION_CLASSES.md). But the
discipline of freezing it allowed the project to discover this
boundary honestly.

### 2.4 The forward-only backtest protocol

**Original claim (Phase 8):** Predictions must be made using only
data available at time T. Events in (T, T+horizon] are the
evaluation, not the input.

**Status:** SURVIVED. The ablation script's `get_priors(year)`
function uses strict inequality (`year < T`), confirmed by
external review (commit 7b1ea07) to have no temporal leakage.
Every backtest in the project follows this protocol.

**Caveat:** The protocol was violated in the TIME_REVERSAL_PROTOCOL.md
document (retrospective preconditions, EP-3 violation), but that
was a documentation artifact, not a backtest issue. The backtests
themselves are clean.

### 2.5 The evidence-standards governance (EP-1 to EP-12)

**Original claim (Phase 13):** The documentation layer must follow
the same evidence discipline as the code layer. No claim without
an artifact; no self-grading; no post-hoc thresholds; no silent
scope changes.

**Status:** SURVIVED. The EP rules were committed (commit 937bbd1)
and have been applied (with some imperfection) through Phase 14.
The F-041 and F-042 failure records document violations that were
caught and corrected. The governance machinery functioned.

**Caveat:** The EP rules were created AFTER the project had already
committed several violations (TIME_REVERSAL_PROTOCOL.md, self-graded
MECHANISM_REGISTRY.md, post-hoc CROSS_DOMAIN_STRESS_TEST.md threshold).
The rules are remedial, not preventive. Future projects should
adopt them from the start.

### 2.6 The structured-failure observation

**Original claim (Phase 14R):** The formula's failures are not
random — they follow patterns that correspond to structural
features of the domains.

**Status:** SURVIVED. The BOUNDARY_REGISTRY.md cataloged 28
failure cases in 5 patterns. The patterns are consistent across
semiconductors and telecom. Random failures would imply noise;
structured failures imply missing structure.

**Caveat:** The patterns are descriptive, not predictive. They
explain why the formula failed but do not prescribe a fix (the
formula is frozen).

---

## 3. What failed

### 3.1 The co-occurrence model (Phase 1-5)

**Original claim:** Shared component labels between domains
predict invention at their intersection.

**Status:** FAILED. The convergence score saturated at
`d(shared)/d(total) = 0.00` across three consecutive ingestion
cycles (Phase 5.B, 5.C, 5.D). The signal was not growing with
more data — it was stuck at 1 shared component out of 11 total.

**Why it failed:** Co-occurrence ≠ enablement. Two domains can
share component labels without one enabling invention in the other.
The model conflated vocabulary overlap with causal relevance.

**Lesson:** Correlation (shared labels) is not causation
(enablement). The project's first major pivot.

### 3.2 The inevitability framing (Phase 10F)

**Original claim:** The model is an "inevitability detector" —
predicting conditions under which invention becomes unavoidable.

**Status:** FAILED. Falsified by 135 false positives at 3.57%
precision (Phase 11A backtest). A condition that produces an event
only 3.57% of the time is not "unavoidable." Recorded as FEC-005
(commit 88e2996).

**Why it failed:** Over-claiming. The model measures landscape
susceptibility, not invention inevitability. Invention requires
susceptibility AND agency (a firm, inventor, or institution that
acts). The model measures the landscape, not the agency.

**Lesson:** Don't claim more than the formula measures. The
susceptibility framing (SCOPE_CHANGE_SUSCEPTIBILITY.md) is the
corrected version.

### 3.3 The M3 statistical claim (Phase 11A)

**Original claim:** The model achieves "predictive capability"
(M3) because 3.57% precision beats NULL_MODEL's 0.71%.

**Status:** FAILED. The McNemar exact test gives p=0.2188
(commit 829ac26). The 3.57% vs 0.71% difference is not
statistically distinguishable from chance at n=14.

**Why it failed:** Insufficient data. The directional advantage
is real (5 TPs vs 1 for NULL) but the sample size is too small
to reach significance. The claim was made before the significance
test was run.

**Lesson:** Effect size alone is insufficient. Always report
both effect size AND statistical significance. Neither replaces
the other. (This became the project's statistical rule.)

### 3.4 The universality assumption (Phase 14)

**Original claim:** The frozen formula generalizes across
structurally different domains.

**Status:** FAILED. 0/4 stress-test domains survived the
advancement criteria (semiconductors and telecom both failed;
aviation and pharmaceuticals not run).

**Why it failed:** The formula covers only 2 of 5 invention
classes (Emergence and Recombination). Domains dominated by
Scaling (semiconductors) or Coordination (telecom) are out of
scope. The formula was over-extended to domains it was not
designed for.

**Lesson:** Invention is heterogeneous, not homogeneous. A
single formula cannot cover all invention classes. The project's
expectation that one formula would generalize was the deepest
untested assumption, and it was wrong.

### 3.5 The time-reversal "evidence" (Phase 13E)

**Original claim:** The model has "100% backward explanatory
power" — every event's preconditions were satisfied in the prior
5-year window.

**Status:** FAILED (as evidence). The preconditions were selected
by a process that already knew the outcomes (EP-3 violation).
The 100% backward fit is a retrospective consistency check, not
independent evidence. Recorded in TIME_REVERSAL_PROTOCOL.md
retitle (commit 88e2996).

**Why it failed:** Look-ahead bias. Selecting preconditions
after knowing the outcome will always produce 100% fit. The
forward-only protocol (used in backtests) is the correct test.

**Lesson:** Retrospective consistency is not evidence. Only
forward prediction counts. (This became EP-3.)

### 3.6 The self-graded explanatory depth (Phase 13)

**Original claim:** 87% of cases have "DEEP" explanation.

**Status:** FAILED. Self-graded by the same author and session
that wrote the explanations (EP-5 violation). The 87% figure is
retired. No independent grading has been done.

**Why it failed:** Self-grading is test theater. The methodology
exists to catch this pattern elsewhere in the stack; the project
applied it to its own narrative summaries and missed the violation
until external review.

**Lesson:** The author of an explanation cannot grade its depth.
Either the human grades it against a pre-agreed rubric, or an
independent process grades it blind. (This became EP-5.)

### 3.7 The post-hoc threshold (Phase 13F)

**Original claim:** The 2-of-4 cross-domain threshold is a
binding criterion.

**Status:** FAILED (as pre-registration). The threshold was
written in the same commit as the synthesis that uses it (EP-6
violation). It is a proposal, not a pre-registered criterion.

**Why it failed:** Thresholds committed alongside the test that
uses them are not pre-registration — they are numbers chosen with
the answer visible.

**Lesson:** Commit criteria as standalone artifacts before any
test runs. (This became EP-6.)

### 3.8 The silent scope change (Phase 13)

**Original claim:** The model's target is "susceptibility" not
"inevitability."

**Status:** The scope change itself is defensible, but the WAY
it was introduced — mid-synthesis, without marking the original
target as falsified first — was a violation (EP-7).

**Why it failed:** Redefining the target is a retraction, not
a rewording. The original "inevitability" claim should have been
marked FALSIFIED before "susceptibility" was introduced.

**Lesson:** Scope changes are argued for explicitly or they don't
happen. The retraction precedes the new target. (This became
EP-7.)

---

## 4. What was learned

### 4.1 Invention is heterogeneous

The deepest lesson. The project began with the assumption that
invention is one phenomenon. It is not. Per INVENTION_CLASSES.md,
invention is at least five classes:

```
Emergence (capability formation)
Scaling (efficiency improvement)
Coordination (synchronization)
Recombination (combination)
Discovery (scientific advance)
```

A single formula cannot cover all five. The frozen formula covers
two (Emergence and Recombination). The other three require
different instruments that have not been built.

This lesson reframes the project's entire arc: the move from
"one phenomenon, one model, one formula" to "many phenomena, many
mechanisms, many instruments" is not a retreat — it is a
refinement. The project discovered that its original assumption
was wrong, and the discovery is itself the result.

### 4.2 The north star is reachability, not prediction

The original north star was "predict inventions." The refined
north star is "understand how possibilities become reachable."

These are related but different. The first asks "what will
happen?" The second asks "what becomes possible?" The frozen
formula addresses the second question for one mechanism
(capability emergence + adjacency). The other four mechanisms
(scaling, coordination, discovery, recombination-without-emergence)
are also reachability questions, but they require different
instruments.

### 4.3 Failure → classification → understanding → simplicity

The project's constitutional rule (per COMPRESSION_TEST.md):

```
failure → understanding → simplicity
```

NOT:

```
failure → complexity → success
```

Phase 14S followed this discipline: instead of patching the
formula to handle telecom's "re-rise" problem, the project
classified the failure (Pattern 2), understood it (non-monotonic
TRL), and stated the boundary simply (BOUNDARY_THEOREM.md). No
patches, no new formulas, no complexity.

### 4.4 Structured failures imply missing structure

If the formula's failures were random, the theory would be wrong.
But the failures are structured — they follow patterns that
correspond to specific structural features of the domains. This
implies the formula is detecting something real but missing
something specific. The "something missing" is what H1 (emergence
vs exploitation), H3 (TRL as wrong state variable), and H4
(multiple invention classes) identify.

### 4.5 Evidence discipline must be enforced at the documentation layer

The project's evidence discipline was previously enforced at the
code layer (tests, benchmarks, replay) and the formula layer
(FORMULA_B_FROZEN.md, ablation). It was NOT enforced at the
documentation layer. Phase 13 introduced four violations at the
documentation layer (retrospective leakage, self-graded depth,
post-hoc threshold, silent scope change) that the code-layer
discipline could not catch.

The EP rules (EP-1 to EP-12) close this gap. Future projects
should adopt them from the start, not as a remedial measure.

### 4.6 The governance machinery functioned

The most encouraging finding. The project's governance machinery
(evidence standards, falsifier tracker, boundary registry,
failure records) caught its own violations. The F-041 and F-042
records document violations that were caught and corrected. The
M3 statistical claim was made prematurely and then honestly
retracted when the significance test failed. The inevitability
framing was over-claimed and then honestly falsified.

The machinery is not perfect — the violations happened in the
first place. But the machinery caught them, which is more than
most projects achieve.

### 4.7 The boundary is the finding

The project's most valuable output is not the formula (which is
narrow) or the predictions (which are not statistically
significant). It is the BOUNDARY — the rigorous statement of
where the theory applies and where it fails. Future researchers
building a multi-instrument theory of invention can start from
this boundary, knowing what the velocity × adjacency instrument
does and does not cover.

---

## 5. What remains unknown

### 5.1 Is the theory wrong, or is the ontology incomplete?

The CEO's central question. The honest answer (per
PHASE_14R_REFLECTION.md): I do not know.

Evidence for "ontology incomplete":
- Failures are structured, not random.
- The theory works for emergence events in monotonic-TRL domains.
- The telecom "re-rise" failures are clearly ontology issues.

Evidence for "theory wrong":
- No statistical significance in any domain.
- Telecom produced 0 TPs (worse than NULL).
- Even emergence events fail when the ontology is correct.

The boundary theorem (BOUNDARY_THEOREM.md) states the boundary
rigorously, but the conclusion is the CEO's to draw. The evidence
does not allow a definitive answer.

### 5.2 Would aviation and pharmaceuticals reveal new patterns?

The CEO's decision to pause before these domains was correct —
they would likely confirm existing patterns rather than reveal
new ones:
- Aviation: slow velocity (0.05-0.10 TRL/year) → Pattern 3
  (threshold granularity) or Pattern 1 (scaling).
- Pharmaceuticals: non-monotonic TRL (clinical trial failures) →
  Pattern 2 (re-rise equivalent) or a new pattern (TRL drops).

But this is a prediction, not a finding. Running them would
either confirm the patterns (low marginal value) or reveal new
ones (high marginal value). Without running them, we don't know
which.

### 5.3 Would acceleration outperform velocity?

H2 (velocity vs acceleration) is untested. Testing it requires
unfreezing the formula (Rule 1 forbids). A new formula using
`d²TRL/dt²` might detect generation transitions (where velocity
is discontinuous), but this is speculation.

### 5.4 Would a multi-state ontology work?

H3 (TRL as wrong state variable) suggests using multiple state
variables (capability state + cost state + coordination state +
etc.). STATE_VARIABLES.md catalogs seven candidates. Whether
combining them would produce better predictions is untested —
it requires building a new ontology and formula.

### 5.5 Are the five invention classes correct?

H4 (multiple invention classes) proposes five classes. The
classification is a candidate, not a final taxonomy. Other
classes may exist (e.g., "regulatory change" might be distinct
from "coordination"). The falsifier (an event that fits none of
the five classes) is pending.

### 5.6 Can the multi-instrument vision be realized?

The refined north star — "understand how possibilities become
reachable" — implies multiple instruments, one per mechanism. Can
this vision be realized? It would require:
- A scaling-detection formula (using scaling metrics)
- A coordination-detection formula (using standards-body state)
- A discovery-detection formula (using scientific-advance metrics)
- A recombination formula (the current adjacency term, refined)

Each would be a separate research project. Whether they can be
built and whether they would collectively cover the invention
space is unknown.

### 5.7 Was the project a success?

By the original north star ("predict inventions"), the project
did not succeed — no domain achieved statistical significance,
and 0/4 stress-test domains survived.

By the refined north star ("understand how possibilities become
reachable"), the project partially succeeded — it identified one
mechanism (capability emergence + adjacency) rigorously, and it
identified the boundary where that mechanism applies.

By the meta-goal ("build a system that can honestly identify its
own boundaries"), the project succeeded — the governance machinery
caught violations, the boundary registry cataloged failures, and
the boundary theorem stated scope rigorously.

Whether this counts as "success" depends on which goal one
prioritizes. The project does not resolve this question.

---

## Closing note

This document is the project's honest accounting. It does not
claim success. It does not claim failure. It records what
happened — the beliefs, the survivals, the failures, the lessons,
the unknowns — and leaves the conclusion to the reader.

The code is in the repository. The formulas are frozen. The
evidence is committed. The boundary is stated. The lessons are
recorded.

What happens next is not this project's decision. The project
has reached its boundary. The next step — if there is one — is
a new project that builds on these lessons, with multiple
instruments instead of one, and with the evidence standards (EP-1
to EP-12) adopted from the start rather than discovered late.

The north star is larger than this project. But this project
identified one part of it honestly, and that identification —
the boundary, not the prediction — may be its most valuable
contribution.

---

## Artifact references

| Lesson | Source artifact |
|---|---|
| Co-occurrence model failed | CONVERGENCE.md, FAILURES.md F-039 |
| Velocity × adjacency signal | FORMULA_B_FROZEN.md, evidence/observations/ablation_results.json |
| M3 not statistically supported | PHASE_13_OPEN_ITEMS_RESOLUTION.md, evidence/observations/phase13_open_items_resolution.json |
| Inevitability falsified | EVIDENCE_FALSIFIERS.md FEC-005, SCOPE_CHANGE_SUSCEPTIBILITY.md |
| Universality failed | PHASE_14_SEMICONDUCTOR_RESULTS.md, PHASE_14_TELECOM_RESULTS.md |
| Boundary patterns | BOUNDARY_REGISTRY.md |
| Invention classes | INVENTION_CLASSES.md |
| State variables | STATE_VARIABLES.md |
| Boundary theorem | BOUNDARY_THEOREM.md |
| Evidence standards | EVIDENCE_STANDARDS.md, EVIDENCE_LOOP.md, EVIDENCE_FALSIFIERS.md |
| Phase 14R reflection | PHASE_14R_REFLECTION.md |
| Phase 14S taxonomy | INVENTION_CLASSES.md, STATE_VARIABLES.md, BOUNDARY_THEOREM.md |
