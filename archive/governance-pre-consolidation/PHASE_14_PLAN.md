# PHASE_14_PLAN

**Status:** Phase 14 execution plan.
**Location:** repo root.
**Phase:** 14 (plan).

> Determine whether the theory is local or universal.
> — CEO directive, Phase 14

---

## Honest starting state

Before executing Phase 14, the project state must be stated
flatly. Per EP-1 (no claim without artifact) and EP-11 (no
promotional language):

### What is established

1. **The ablation result (FEC-001).** Formula B (frozen, full)
   and velocity+adjacency (simplified) produce byte-identical
   per-T precision arrays on the Li-ion 14-point backtest.
   Verified at the precision level. NOT verified at the
   per-candidate level (rankings differ at 8/14 T-points; see
   PHASE_13_OPEN_ITEMS_RESOLUTION.md Item 2).

2. **The forward-only backtest protocol.** The ablation script
   uses time-safe priors (`get_priors(year)` returns events
   with `year < T` strictly). No leakage in the backtest itself.

3. **The pre-1990 TRL data gap.** T=1991 and T=1993 backtest
   results are contaminated by missing pre-1990 TRL data, which
   produces spurious velocity values for mature capabilities.
   This is a data bug, not a logic bug. T ≥ 1995 are clean.

### What is NOT established

1. **M3 (predictive capability).** NOT STATISTICALLY SUPPORTED.
   McNemar exact test on Formula B vs NULL: p=0.2188. Paired
   t-test: t(13)=1.472, p=0.141. Both fail to reject H0 at
   p<0.10. The 3.57% vs 0.71% precision difference is not
   distinguishable from chance at n=14.

2. **The necessity claim (FEC-002).** Reclassified from FINDING
   to HYPOTHESIS in commit 88e2996 (EP-4 violation: no
   pre-stated falsifier). The falsifier is now stated, but the
   forward test has not run. Existing 7 TPs are consistent with
   the hypothesis but are a retrospective check, not evidence.

3. **The inevitability claim (FEC-005).** FALSIFIED by 135
   false positives at 3.57% precision. Retired. Scope changed
   to susceptibility estimation (commit 74b6c2b).

4. **The counterexample registry scores.** CE-002 and CE-003
   claimed scores (0.8333) are not reproducible by the current
   script (actual scores: 0.005 and 0.003). The CE registry
   needs correction or retraction.

5. **The mechanism registry's explanatory depth.** Self-graded
   (EP-5 violation). The 87% DEEP rate is retired. Independent
   grading has not been done.

### What Phase 14 adds

Phase 14 adds NEW DOMAINS. Each domain provides:
- 10-15 T-points of backtest data (increasing n from 14 to
  50-70 total across domains).
- Different structural assumptions (per INVARIANT_REGISTRY.md).
- Different events and capabilities.

The increased n directly addresses the significance test
failure. At n=50-70, McNemar's test has substantially more
power. If the directional advantage (Formula B > NULL) holds
across domains, the combined test may reach significance even
if no single domain does.

This is the honest justification for proceeding with Phase 14
despite M3 not being established: the problem is insufficient
data, not a wrong theory. Phase 14 provides more data.

---

## Checkpoint 3 verification

Per EVIDENCE_LOOP.md, Phase 14 cannot start until Checkpoint 3
passes on all 6 checks:

| # | Check | Status | How satisfied |
|---|---|---|---|
| 3.1 | Phase 13 open items resolved or deferred | ✅ Resolved (commits 829ac26, 7b1ea07). Resolution found M3 not significant; this is recorded, not hidden. | Phase 13 open items resolution document. |
| 3.2 | Falsifiers pre-stated | ✅ DESTRUCTION_TEST_PROTOCOL.md (commit 3ace7af). | Five destruction tests with pre-stated falsifiers. |
| 3.3 | Graders specified | ⚠️ Partial. External adversaries (Phase 14F) specified by CEO. Mechanism registry grading TBD — will be done by external adversaries post-hoc, not by the coder. | This document, below. |
| 3.4 | Thresholds pre-committed | ✅ PHASE_14_ADVANCEMENT_CRITERIA.md (commit 140653e). | Standalone commit before any stress test. |
| 3.5 | Retraction precedes new target | ✅ SCOPE_CHANGE_SUSCEPTIBILITY.md (commit 74b6c2b). FEC-005 (commit 88e2996) is the retraction. | Formal scope change document. |
| 3.6 | Forward-only preconditions | ✅ PREDICTION_LEDGER.md (commit 3ace7af). | Schema enforces timestamp + immutable rationale. |

Check 3.3 is partially satisfied. The mechanism registry grading
will be done by the external adversaries (Phase 14F: Historian,
Economist, Physicist, Statistician) as part of their adversarial
review. The coder does not grade the mechanism records. This is
the best available independent grading process given the project's
constraints.

**Checkpoint 3 verdict: PASS (with 3.3 partially satisfied by
deferring grading to Phase 14F external adversaries).**

---

## Domain execution plan

Per CEO directive Phase 14A, the order is:
1. Semiconductors
2. Telecommunications
3. Aviation
4. Pharmaceuticals

### Per-domain execution steps

For each domain:

1. **Build the capability ontology.** 6-10 capabilities specific
   to the domain. Committed before the backtest runs.

2. **Build the event registry.** 15-20 historical events spanning
   30+ years. Each event: year, combination, event description,
   evidence citations. Committed before the backtest runs.

3. **Build the trajectory registry.** TRL trajectories for every
   capability, at 5-year intervals, from the domain's earliest
   relevant year to 2025. Committed before the backtest runs.

4. **Run the frozen formula.** `score = max(dTRL/dt) × adjacency`
   at each T-point. No formula changes (Rule 0). No threshold
   changes. No ontology changes.

5. **Run the NULL_MODEL.** Random selection of 10 candidates per
   T-point. Same seed protocol as Li-ion (seed=42).

6. **Run the significance test.** McNemar exact test on Formula B
   vs NULL. Paired t-test on per-T precision. Report p-values.

7. **Run the destruction tests (D1-D5).** Per
   DESTRUCTION_TEST_PROTOCOL.md. Record results in
   DESTRUCTION_TEST_RESULTS.md.

8. **Commit predictions to PREDICTION_LEDGER.md.** Top-10
   predictions as Type 1 (PENDING). Susceptibility predictions
   as Type 2 (PENDING). Evaluate immediately (historical
   backtest) and update status.

9. **Apply the advancement criteria.** Per
   PHASE_14_ADVANCEMENT_CRITERIA.md, does the domain survive?

### What each domain requires (honest scope)

Each domain is a substantial research task. Building a
defensible capability ontology, event registry, and TRL
trajectory registry for semiconductors requires real historical
research — not just coding. The TRL values must be grounded in
actual industry milestones (lithography generations, transistor
architectures, node introductions).

This means Phase 14 cannot be executed in a single session. Each
domain is a multi-session effort: one session to build the
ontology and registries, one to run the backtest and destruction
tests, one to write up the results.

### Domain 1: Semiconductors (starting now)

The semiconductor domain is the first stress test. Per
INVARIANT_REGISTRY.md, the structural violations are:
- TRL is not monotonic (lithography generations are discrete steps)
- Yield bottleneck is economic (defect density), not physical
- Node jumps are discontinuous
- Single dominant customer concentration (TSMC)

The ontology will include:
- LITHOGRAPHY (g-line, i-line, DUV, ArF, EUV)
- TRANSISTOR_DESIGN (planar, FinFET, GAA)
- INTERCONNECT (aluminum, copper, low-k)
- MATERIALS (silicon, strained-silicon, SiGe, high-k)
- DESIGN_TOOLS (manual, schematic, HDL, EDA, AI-assisted)
- FAB_PROCESS (200mm, 300mm, 450mm-stalled)

The event registry will span 1971 (Intel 4004) to 2022
(Samsung 3nm GAA). ~20 events.

The trajectory registry will use lithography-generation TRL:
each generation has a concept year, lab year, pilot year,
production year. TRL rises in steps, not smoothly.

**This domain's backtest will run in the next session.** The
ontology, event registry, and trajectory registry will be
committed as separate artifacts (per EP-6, before the backtest
that uses them).

---

## Phase 14D — Natural experiments

Per CEO directive, the project should actively search for
discontinuities (wars, sanctions, supply-chain shocks,
regulatory changes, infrastructure changes) that expose hidden
causal structure.

Candidate natural experiments per domain:

- **Semiconductors:** 1986 US-Japan semiconductor trade agreement
  (regulatory); 2011 Tōhoku earthquake (supply-chain shock);
  2018 US-China trade war sanctions (ZTE, Huawei) (regulatory).
- **Telecommunications:** 2003 3G spectrum auction failures
  (economic); 2019 Huawei 5G bans (regulatory); COVID-19
  remote-work surge (demand shock).
- **Aviation:** 1973 oil crisis (fuel efficiency push); 2001
  9/11 (security regime change); 2019-2020 737 MAX grounding
  (regulatory + catastrophic failure); COVID-19 travel collapse
  (demand shock).
- **Pharmaceuticals:** 2003 FDA accelerated approval pathway
  change (regulatory); 2020 COVID-19 emergency authorization
  (regulatory); 2004 Vioxx withdrawal (safety event).

Each natural experiment is analyzed as a discontinuity in the
trajectory registry. The question: did the model's susceptibility
estimate change at the discontinuity? If yes, the model is
detecting real causal structure. If no, the model is insensitive
to exogenous shocks.

This analysis runs AFTER each domain's backtest completes,
as a separate phase.

---

## Phase 14F — External adversaries

Per CEO directive, the next reviewers should be:
- Historian (challenge chronology)
- Economist (challenge incentives)
- Physicist (challenge constraints)
- Statistician (challenge inference)

These reviewers are external — they are not the coder. The
coder's role is to prepare the artifacts for their review and
to record their findings honestly.

The external review runs AFTER all four domain stress tests
complete. The reviewers receive:
- The frozen formula
- The four domain backtests
- The destruction test results
- The prediction ledger
- The invariant registry

Each reviewer writes a report challenging the theory from their
discipline's perspective. The reports are appended to the repo
without modification (Law 7). The theory survives Phase 14F only
if it survives all four challenges — or, if it doesn't survive,
the failure modes are recorded and the theory is revised or
rejected accordingly.

---

## What this plan does NOT authorize

- Starting a domain backtest before its ontology + event
  registry + trajectory registry are committed. Per EP-6 and
  EP-3, the data must be frozen before the formula runs.
- Modifying the formula. Rule 0: the theory is frozen.
- Claiming M5 before all four domains + external review
  complete. The advancement criteria in
  PHASE_14_ADVANCEMENT_CRITERIA.md are binding.
- Skipping the destruction tests. D4 and D5 are strict
  necessity tests; if they fail, the theory is falsified
  regardless of how many domains "survive" on conditions 1-3.

---

## Next step

The next step is to build the semiconductor domain's ontology,
event registry, and trajectory registry. These will be committed
as separate artifacts before the semiconductor backtest runs.
This is a multi-session effort; the artifacts will be produced
and committed incrementally.
