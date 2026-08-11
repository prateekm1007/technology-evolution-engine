# STOP BUILDING LIST

Cycle 258. Constitutional enforcement. Per ROADMAP_V2.md.

The coder is forbidden from building any of the following until
Programs A-D are complete (Gate 1 + Gate 2 + Gate 3 + Gate 4 = PASS).

## Forbidden work

| # | Forbidden until | Rationale |
|---|---|---|
| 1 | Better Proposal Composer (beyond Gen0 experiments) | Proposal Composer Gen0 is FROZEN per Program C. Stage P1 (mechanism-driven composer) requires Programs A-D first. |
| 2 | New discovery algorithms | Discovery work is FROZEN per Program B until benchmark recovery completes. |
| 3 | New invention algorithms | Invention depends on Programs A-D per Program E. Invention is no longer priority one. |
| 4 | L6 search | L1-L5 research chapter is complete per Program F. Closed research direction. |
| 5 | Product features | Not until Gate 4 (Invention) PASS. |
| 6 | UI improvements | Not until Gate 4 (Invention) PASS. |
| 7 | Commercialization work | Not until Gate 4 (Invention) PASS. |
| 8 | Benchmark tuning | Tuning benchmarks to make scores look better is the No-Gaming Rule violation (CONSTITUTION.md). Forbidden permanently, not just until gates pass. |
| 9 | Score improvements | Improving scores without improving the underlying capability is the Prime Directive violation (CONSTITUTION.md). Forbidden permanently. |

## Enforcement

This list is enforced by:

1. **Pre-commit check** (CONTRIBUTING.md): every commit must declare which
   Program and Stage the work belongs to. Work outside Programs A-G is
   rejected.
2. **CI test** (`tests/test_stop_building_enforcement.py`): scans changed
   files for forbidden patterns. Fails CI if any forbidden work is detected.
3. **PR review**: reviewers must reject PRs that violate the STOP BUILDING
   list, regardless of code quality.

## Exceptions

The ONLY exception is repair work that is explicitly required by a
Program A-D stage. For example:
- Repairing the ProposalComposer to satisfy Stage P1 is ALLOWED.
- Adding new proposals to Gen0 is FORBIDDEN.
- Repairing the discovery benchmark to satisfy Stage D1-D2 is ALLOWED.
- Adding new discovery algorithms is FORBIDDEN.

When in doubt, the answer is NO. File a STOP_BUILDING_REVIEW issue
and wait for explicit approval.

## Mapping to existing work

The 4 gates built in cycles 256-257 (DR-97..DR-101) are NOT discarded.
They map to the new Gate 1-4 structure as follows:

| Old gate | New gate | Status |
|---|---|---|
| DR-97 (external baselines) | Gate 2 Stage D3 | INSTRUMENTATION_SCAFFOLD_PASS (oracle-assisted; needs true external baselines) |
| DR-98 (historical recalibration) | Gate 2 Stage D4 | SENSITIVITY_ANALYSIS_PASS (not full recalibration; needs original gold data reconstruction) |
| DR-99 (N≥30 proposal evaluation) | Gate 1 Stage M3 (precursor) | WEAK_STATISTICAL_PASS (per-proposal F1=0.15 below 0.30 useful-performance threshold) |
| DR-100 (Tier-2 / AI surrogate review) | Gate 2 Stage D5 / Gate 3 Stage P3 | AI_SURROGATE_REVIEW_FAIL (0/6 accepted, mean 2.24/5) |
| DR-101 (final verdict eligibility) | Gate 1+2+3+4 (meta) | BLOCKED (0/4 SCIENCE_PASS) |

The new Gate 1-4 structure (GO / NO-GO Gates in ROADMAP_V2.md) is
canonical. The old DR-97..DR-101 modules remain as evidence and as
the foundation for the new gates.
