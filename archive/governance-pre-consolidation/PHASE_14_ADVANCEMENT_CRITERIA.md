# PHASE_14_ADVANCEMENT_CRITERIA

**Status:** Pre-registered threshold (EP-6).
**Location:** repo root.
**Phase:** 14.

> This document commits the advancement criteria for Phase 14
> as a standalone artifact BEFORE any domain stress test runs.
> Per EP-6, a threshold written in the same commit as the test
> that uses it is not pre-registration. This document commits
> the threshold first; the stress tests commit later, separately.

---

## The criteria

Per CEO directive Phase 14, the advancement criteria for the
four-domain stress test (semiconductors, telecommunications,
aviation, pharmaceuticals) are:

| Domains survived | Verdict |
|---|---|
| 0/4 | Reject theory |
| 1/4 | Local phenomenon |
| 2/4 | Promising framework |
| 3/4 | Strong theory |
| 4/4 | Candidate M5 |

### What "survive" means

A domain "survives" if ALL of the following hold:

1. **Forward-only backtest produces TPs.** The frozen formula
   `score = max(dTRL/dt) × adjacency` is run on the domain's
   capability ontology with the domain's event registry. At
   least 1 TP must appear in the Top-10 across the domain's
   T-points. Zero TPs = domain does not survive.

2. **Precision exceeds NULL_MODEL.** The domain's Formula B
   precision must exceed the NULL_MODEL precision (random
   selection) for the same domain. If Formula B = NULL on
   precision, the domain does not survive.

3. **Significance test passes (McNemar p < 0.10).** Per the
   EP-10 resolution finding (M3 not statistically supported at
   p=0.2188 on Li-ion n=14), the bar for "survive" must include
   statistical significance. A domain survives only if McNemar's
   exact test on Formula B vs NULL_MODEL produces p < 0.10
   (one-sided) or p < 0.20 (two-sided, more conservative).
   This is a LOWER bar than p < 0.05, justified by the small
   sample sizes per domain (expected n ≈ 10–15 T-points per
   domain).

4. **No destruction-test falsification (Phase 14E).** If any
   of the 5 destruction questions (can X exist without Y?)
   produces a falsifying observation in this domain, the domain
   does not survive. See DESTRUCTION_TEST_PROTOCOL.md for the
   pre-stated falsifiers.

### What "survive" does NOT require

- A specific precision threshold (e.g., > 3%). Precision varies
  by domain based on event density; a domain with sparse events
  may have low precision but still beat NULL.
- Per-candidate equivalence to Li-ion. The formula is frozen;
  its per-candidate behavior in a new domain is what we're
  testing, not matching.
- Mechanism records graded DEEP by an independent grader.
  Phase 14 produces mechanism records but does not block domain
  survival on grading — grading is a separate process per
  EP-5 and will be done post-hoc by the external adversaries
  (Phase 14F).

### Why the bar is set here

The CEO's advancement table is the binding criterion. The four
sub-conditions above operationalize "survive" concretely. Setting
the bar lower (e.g., "any TP" without significance) would
repeat the M3 mistake — claiming predictive capability without
statistical support. Setting it higher (e.g., p < 0.05 per
domain) would make survival nearly impossible given expected
sample sizes, which would test the threshold rather than the
theory.

The p < 0.10 (one-sided) bar is a compromise. It is stricter
than the Li-ion backtest's p=0.2188 (which would not survive).
It is looser than conventional p < 0.05. The justification:
n ≈ 10–15 per domain is small; the exact McNemar test is
conservative at small n; and the four-domain aggregation
provides additional power (if 3+ domains individually show
directional advantage, the combined evidence is stronger
than any single domain).

### Interaction with M3 status

M3 (predictive capability) is currently NOT STATISTICALLY
SUPPORTED on Li-ion (p=0.2188, commit 829ac26). This means
Li-ion itself would not "survive" under the criteria above
(condition 3 fails).

This is the honest starting state. Phase 14 does not pretend
Li-ion is clean. If the four stress-test domains also fail
condition 3, the theory is rejected (0/4 or low 1/4). If 2+
domains pass condition 3, the theory has cross-domain support
that Li-ion alone does not provide — which is the most
defensible outcome the data could produce.

---

## Pre-registration statement

I, the coder, commit this threshold on 2026-08-02, before any
semiconductor, telecommunications, aviation, or pharmaceutical
backtest has been run. The criteria above are binding. If the
stress tests produce results that fall between categories
(e.g., 2 domains survive conditions 1-3 but fail condition 4),
the verdict is the lower category (in this example, "promising
framework" becomes "local phenomenon" because condition 4
failed).

The criteria may not be adjusted after seeing results. If they
need adjustment, the adjustment is committed as a separate
artifact (this file, versioned with a `_review` suffix per
Law 7), and the stress tests are re-run from scratch.

---

## What this document does NOT do

- It does not authorize Phase 14 to start. Phase 14 starts only
  after Checkpoint 3 (EVIDENCE_LOOP.md) passes on all 6 checks.
  This document satisfies check 3.4 only.
- It does not define the domains. The domains are specified in
  the CEO directive (semiconductors, telecommunications,
  aviation, pharmaceuticals, in that order).
- It does not define the destruction tests. Those are in
  DESTRUCTION_TEST_PROTOCOL.md (Phase 14E).
