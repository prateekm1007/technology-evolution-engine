# Phase 0 — Establish Repository Truth

**Status:** COMPLETE
**Commit:** d060aa9 (DXP-005 pause) + this commit
**Date:** 2026-08-08
**Amendment Reference:** Amendment 3 (CI verification), Amendment 13 (PHASE_STATUS.json)

---

## What Phase 0 establishes

Per the amended 18-phase execution order, Phase 0 must establish repository truth:
- The current commit SHA
- The branch
- The engine source state (clean / dirty)
- The CI status (per Amendment 3, with three explicit terminal states)
- The local test status (kept separate from CI status per Amendment 3)
- The frozen objects in force

These are recorded in `PHASE_STATUS_phase0.json`.

## Strict CI vs local test distinction (Amendment 3)

Per Amendment 3, the GitHub CI status uses three explicit terminal states:

```
VERIFIED_PASS
VERIFIED_FAIL
NOT_INDEPENDENTLY_VERIFIED
```

For this repository, the GitHub CI status is:

```
NOT_INDEPENDENTLY_VERIFIED
```

This is **not** a defect. The environment in which this Phase 0 was executed
does not provide independent GitHub Actions access:

- The GitHub REST API is rate-limited (HTTP 429 without auth token)
- The `GITHUB_TOKEN` and `GH_TOKEN` environment variables are not set
- The `gh` CLI is not available

Per Amendment 3, the absence of independent verification is the correct
terminal state. It is not inferable from any of the following:

- local pytest passing
- local build succeeding
- git push succeeding
- the existence of a `.github/workflows/ci.yml` file
- the absence of visible errors

The local tests-vs-GitHub-CI distinction is enforced:

```
LOCAL TESTS:
    178 substrate+adversarial tests passed (smoke check)
    2663 tests collected total (not all run in Phase 0)

GITHUB CI:
    NOT_INDEPENDENTLY_VERIFIED
```

These two are never collapsed into "CI PASSED".

## Engine source state

The engine source is **content-clean**:

- `git diff engine/` shows 0 lines of content changes
- `git status --porcelain engine/` returns empty
- The `engine/checkpoint.py` `_check_engine_source_clean()` check passes

The working tree has 1651 "modified" files, but **all 1651 are mode-only
changes** (file permission drift from 100644 to 100755). This is a
pre-existing repository state, not introduced by Phase 0 work.

## Frozen objects in force

| Object | Value |
|---|---|
| Substrate freeze commit | `f8e3f2a` |
| Gate 2 protocol SHA | `32691a7` |
| Gate 2 manifest SHA | `79788334adf8bb058d7e5a4ec6f41283d69fb891fcdab995e21e28c05f5b3829` |
| Measurement integrity baseline tag | `stage-1-measurement-integrity-baseline` |
| Cognitive baseline tag | `777cb6d` |
| Historical F1 baseline | 0.5714 (NOT a capability claim) |
| Bridge synonyms state | `EMPTY_MAP_{}_FROZEN` |

These frozen objects remain in force. No frozen object was modified in
Phase 0.

## Amendment 14 enforcement (DXP-005 pause)

DXP-005 was paused in this Phase 0 work:

- Partial state preserved (frozen-in-place, not modified)
- Pause notice written: `discovery_experiment/FINAL_VERDICT/DXP-005_PAUSE_NOTICE.md`
- Pause commit: `d060aa9`
- Resume condition: ONLY if Phase 17 produces `DISCRIMINATIVE`
- No "rescue" allowed (Amendment 15)

The partial DXP-005 state is NOT labeled "promising" (Amendment 15
forbids that label). It is labeled INCOMPLETE.

## Phase 0 → Phase 1 transition

Phase 1 is "Fix BusinessPipeline silent failures". This is an
`ENGINEERING_FIX` category commit per Amendment 12.

The next phase may not silently alter Phase 0's frozen assumptions
(Amendment 13). Specifically:

- The CI status remains `NOT_INDEPENDENTLY_VERIFIED` until independent
  GitHub Actions evidence is retrieved
- The local-test count remains 178 (smoke check) until a full local
  run is performed
- The frozen objects in force remain unchanged

## No scientific results visible

Phase 0 has produced no scientific results. No discovery claims. No
discrimination measurements. No matcher outputs. The scientific
visibility boundary (Amendment 14) has not been crossed.
