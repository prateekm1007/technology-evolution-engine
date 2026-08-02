# NOVELTY — Phase 6 Score B Definition

**Status:** constitutional document (Score B definition).
**Location:** repo root (peer of CAPABILITY_ONTOLOGY.md, CONVERGENCE.md, READINESS.md).
**Phase:** 6 (architectural investigation; implementation NOT yet authorized).
**Question:** Has this combination already been explored?

> Score B — Novelty: Has this combination already been explored?
> Inputs: combinatorial distance, exploration score, historical rarity,
> exploitation score.
> — CEO directive, Phase 6, Section 9

This document defines the Novelty score for the capability-centric
architecture. It follows the 5-section structure established by
CONVERGENCE.md. The formula is a prior informed by the prior art
(Fleming, Youn et al.); it is NOT a fitted constant.

**This document does NOT authorize implementation.** It defines what
Novelty means.

---

## 1. Definition

**Novelty** measures whether a combination of capabilities has been
attempted before. It asks "is this combination familiar or unfamiliar?"
— which is the combinatorial question Youn et al. (2015) and Fleming
(2001) formalized.

**The defining property:** Novelty is a **combinatorial** measurement,
not a pairwise one. It asks about combinations (sets of capabilities),
not pairs. This distinguishes it from Readiness (per-capability) and
Feasibility (threshold gates on combinations).

**The key insight from Fleming (prior art):**

> Recombining familiar components does NOT reliably reduce inventive
> uncertainty. Refining already-used combinations reliably does.

**Translation:** high Novelty (unfamiliar combination) does NOT
predict success. It predicts uncertainty. A high-Novelty combination
is one whose outcome is uncertain — it might be a breakthrough, or
it might fail. A low-Novelty combination (familiar) is one whose
outcome is more predictable (incremental refinement).

**This inverts the Phase 5 convergence assumption.** Phase 5 assumed
high overlap = good (convergence). Novelty says high overlap = low
novelty = incremental (not breakthrough). If the system is meant to
find breakthroughs, it should score for productive unfamiliarity,
not for convergence.

**Relationship to the other scores:**
- Readiness (Score A): can it exist? (per-capability)
- Novelty (Score B): has this combination been tried? (combinatorial)
- Feasibility (Score C): would reality allow it? (threshold gates)

A combination can be high-Novelty (never tried) AND high-Readiness
(each capability is mature) — this is the "breakthrough candidate"
case. A combination can be low-Novelty (frequently tried) AND
high-Readiness — this is the "incremental refinement" case.

---

## 2. Signals

Four candidate signals, grounded in the prior art.

### Signal N1 — Combinatorial distance

**What it measures:** how far the combination is from existing
combinations. If the capabilities in the combination frequently
co-occur in existing patents/papers, distance is low. If they have
never co-occurred, distance is high.

**Unit:** continuous [0, 1]. 0 = combination is identical to an
existing one; 1 = combination has never been attempted.

**Why necessary:** this is the direct operationalization of Fleming's
"unfamiliar components" and Youn et al.'s "exploration" (new
combinations vs refinements).

**Computation:** for a combination C = {c1, c2, ..., cn}, find all
existing combinations that include any subset of C. If no existing
combination includes all of C, N1 = 1.0 (fully novel). If existing
combinations include all of C, N1 = 0.0 (fully familiar). Otherwise,
N1 = 1 - (max overlap with any existing combination / |C|).

**Live data:** not yet ingested. Requires the capability-centric
graph with typed edges (REQUIRES, ENABLES, etc.) and historical
combination data.

### Signal N2 — Exploration score (Youn et al.)

**What it measures:** whether the combination represents "exploration"
(new combinations of technologies) or "exploitation" (refinements of
existing combinations), per Youn et al.'s invariant rate finding.

**Unit:** binary (exploration=1, exploitation=0) or continuous
(degree of exploration).

**Why necessary:** Youn et al. found the exploitation/exploration
rate is invariant across 220 years of patent data. This suggests
the rate is a structural property of the inventive process. The
Novelty score should capture whether a given combination is on the
exploration side or the exploitation side.

**Computation:** a combination is "exploration" if at least one
capability pair in it has never co-occurred in any prior combination.
"Exploitation" if all pairs have co-occurred.

### Signal N3 — Historical rarity

**What it measures:** how frequently this specific combination (or
near-identical combinations) has appeared in the historical record.

**Unit:** continuous [0, 1]. 0 = combination is very common; 1 =
combination has never appeared.

**Why necessary:** distinguishes "rare but attempted" from "never
attempted." A combination that has been attempted once is different
from one attempted 100 times.

**Computation:** 1 - (count of historical occurrences / max count
across all combinations). Normalized to [0, 1].

### Signal N4 — Exploitation score (inverse of N1-N3)

**What it measures:** the degree to which the combination refines
existing combinations rather than creating new ones.

**Unit:** continuous [0, 1]. 0 = fully novel; 1 = fully refinement.

**Why necessary:** Fleming's finding is that refinement reduces
uncertainty. A high-exploitation combination is low-risk (predictable
outcome) but also low-breakthrough. This is the inverse of Novelty
but is recorded separately to preserve the distinction.

**Computation:** N4 = 1 - max(N1, N2, N3). Or: N4 = 1 - Novelty.
This is a cross-check, not an independent signal — it ensures the
Novelty score and the Exploitation score are consistent.

---

## 3. Formula (experimental — NOT constitutional)

**Per CEO v3.5 correction:** constitutional documents encode
invariants, not fitted equations. The dimensions (N1-N4) are
invariant — they are the signals Novelty must measure. The
mathematics (weights, normalization, combination rule) are
experimental — they are candidate scoring functions that must be
tested against real data before being elevated.

The candidate formula, weights, and cross-check rules are recorded
in:

```
evidence/experiments/novelty_formula_v1.md
```

That file is in the **experimental layer**, not the constitutional
layer. It will be revised as the formula is tested against the one
vertical's real data. The constitutional layer (this document) does
not commit to a specific formula.

**What IS invariant (constitutional):**
- Novelty is a combinatorial measurement (not per-capability, not
  pairwise in the convergence sense).
- The 4 signals (N1-N4) are the required dimensions.
- Novelty measures uncertainty, NOT value (per Fleming). A high-
  Novelty combination is uncertain, not necessarily good.
- N4 (exploitation) is the inverse cross-check: N4 should equal
  1 - Novelty. This invariant holds regardless of the specific
  formula.

**What is NOT invariant (experimental):**
- The weights of each signal.
- The normalization scheme.
- Whether N4 enters the formula or remains a cross-check.
- The thresholds for "novel" vs. "familiar."

**Important: Novelty does NOT predict success.** A high-Novelty
combination is uncertain — it might be a breakthrough or a failure.
Novelty is a signal of uncertainty, not of value. The system should
use Novelty to identify combinations worth investigating, not to
rank combinations by predicted success. This is an invariant —
it holds regardless of the specific formula.

---

## 4. Failure modes

### Failure Mode N1 — Novelty ≠ value

**Description:** the system treats high Novelty as "good" and low
Novelty as "bad." But Fleming's work says high Novelty = high
uncertainty, not high value.

**Impact:** the system recommends high-Novelty combinations that
are unlikely to succeed, while ignoring low-Novelty combinations
that would reliably produce incremental value.

**Mitigation:** Novelty is presented as "uncertainty" not "value."
The system's output should distinguish "high-Novelty (uncertain,
potentially breakthrough)" from "low-Novelty (predictable,
incremental)." Neither is inherently better — they serve different
purposes.

### Failure Mode N2 — Co-occurrence contamination

**Description:** N1 (combinatorial distance) is computed from
co-occurrence in patents/papers. But co-occurrence in text ≠
co-occurrence in a combination. Two capabilities mentioned in the
same paper might be alternatives, not components of a combination.

**Impact:** Novelty is underestimated (the system thinks a
combination is familiar when it's actually novel).

**Mitigation:** N1 must be computed from typed edges (REQUIRES,
ENABLES, EMBODIED_IN), not from co-occurrence. Two capabilities
that merely co-occur in text are not in a combination; two
capabilities connected by REQUIRES or ENABLES are. This is why
the type system (CAPABILITY_ONTOLOGY.md Section 6) matters.

### Failure Mode N3 — Historical data sparsity

**Description:** N3 (historical rarity) depends on the historical
record. If the historical record is sparse (few patents/papers in
the vertical), every combination looks rare.

**Impact:** Novelty is overestimated (everything looks novel because
there's little history to compare against).

**Mitigation:** the one-vertical scope (50 patents + 50 papers) is
small. Novelty scores in this scope are priors, not calibrated
measurements. The frozen-time backtest will reveal whether the
scores are meaningful at this scale.

### Failure Mode N4 — Time-blind novelty

**Description:** a combination that was novel in 1995 might be
commonplace in 2026. Without temporal state, the system scores
it as novel forever.

**Impact:** the system recommends combinations that are no longer
novel.

**Mitigation:** TemporalState. N3 (historical rarity) must be
computed as-of a date T. "Novel as of 1995" is different from
"novel as of 2026."

---

## 5. Validation plan

### Validation pair 1: lithium-ion + supercapacitor (familiar vs novel)

**Prediction:** the combination {lithium-ion, supercapacitor} should
have low Novelty (they frequently co-occur in hybrid energy storage
systems). The combination {lithium-ion, flow-battery} should have
higher Novelty (less common hybrid).

**Falsification:** if the Novelty scores don't distinguish these, the
combinatorial distance signal (N1) is not capturing the right
distinction.

**Resolution:** requires the capability-centric graph with typed
edges for the electrochemical energy storage vertical.

### Validation pair 2: historical novelty vs eventual success

**Prediction:** per Fleming, high-Novelty combinations should have
higher variance in outcomes (some breakthroughs, some failures).
Low-Novelty combinations should have lower variance (mostly
incremental successes).

**Falsification:** if high-Novelty combinations reliably succeed
(low variance), Fleming's finding doesn't hold at this scale, and
Novelty is not a useful uncertainty signal.

**Resolution:** requires frozen-time backtest. Snapshot at year T,
compute Novelty scores, check outcome variance at T+n. This is the
CEO's Section 12 validation applied to Novelty.

### Pre-validation prerequisite

The one vertical must be ingested with typed edges (REQUIRES, ENABLES,
etc.) and historical combination data before this validation can run.
That ingestion is Phase 7 work, which is NOT yet authorized.

---

## Implementation status

| Item | Status |
|---|---|
| Definition | COMPLETE (this document) |
| Signals (4) | COMPLETE (N1-N4; N4 is a cross-check) |
| Formula | COMPLETE (prior; not fitted) |
| Failure modes (4) | COMPLETE |
| Validation plan | COMPLETE (requires Phase 7 ingestion to execute) |
| Phase 7 implementation | NOT AUTHORIZED |

No code written. No data ingested. This is a definition document,
grounded in Fleming and Youn et al., awaiting Phase 7 authorization
to be tested against real data from the one vertical.
