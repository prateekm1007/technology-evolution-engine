# B-2 Adversarial v2 — Diagnostic Results

**Date:** 2026-08-09
**Detector under test:** `b1_b2_verification._check_leakage` at commit `20ac268`
**Adversarial fixture:** `test_fixture.json` (13 cases, including 4 controls)
**Production substrate:** UNCHANGED — no modifications made.

## Purpose

Per the external auditor's round-72 verdict, the current B-2 detector was NOT
to be modified. The task was to construct an adversarial test set whose expected
dispositions are **derivable from semantic rationales** (not from hard-coded labels
in the test fixture), and to run the current detector against it as a diagnostic.

The diagnostic does NOT unfreeze Protocol B. It produces evidence only.

## Summary

| Metric | Value |
|--------|-------|
| Total cases | 13 |
| Matches (detector == expected) | 7 |
| Mismatches | 6 |
| Controls passing | 4/4 |
| Adversarial-only matches (ADV-01..08, ADV-13) | 3/9 |

## Per-case results

| ID | Category | Candidate | Expected | Detector | Match? |
|----|----------|-----------|----------|----------|--------|
| ADV-01 | (1) no-overlap paraphrase | `skeletal calcification process` | REJECT | ALLOW | **MISMATCH** |
| ADV-02 | (1) no-overlap paraphrase | `calcified matrix in osseous structures` | REJECT | ALLOW | **MISMATCH** |
| ADV-03 | (2) cross-source synthesis | `enzyme-templated mineral deposition` | ALLOW | REJECT | **MISMATCH** |
| ADV-04 | (2) cross-source synthesis | `silicatein-guided calcification` | ALLOW | REJECT | **MISMATCH** |
| ADV-05 | (3) source-local disguised | `hypermineralization` | REJECT | REJECT | MATCH |
| ADV-06 | (3) source-local disguised | `xenomineralization` | REJECT | REJECT | MATCH |
| ADV-07 | (4) minimal-overlap synthesis | `enzyme-templated inorganic lattice formation` | ALLOW | ALLOW | MATCH |
| ADV-08 | (4) minimal-overlap synthesis | `protein-catalyzed biogenic oxide precipitation` | ALLOW | REJECT | **MISMATCH** |
| ADV-09 | (control) clean bridge | `quantum entanglement` | ALLOW | ALLOW | MATCH |
| ADV-10 | (control) exact leakage | `calcium phosphate` | REJECT | REJECT | MATCH |
| ADV-11 | (control) round-72 true-allow | `biomineralization` | ALLOW | ALLOW | MATCH |
| ADV-12 | (control) round-72 true-reject | `mineralizing` | REJECT | REJECT | MATCH |
| ADV-13 | (3) defeats suffix heuristic | `pseudomineralization` | REJECT | ALLOW | **MISMATCH** |

## Auditor's round-72 questions, answered

### Q1: Can the detector reject a no-overlap source-local paraphrase?
**ADV-01 `skeletal calcification process`: expected REJECT, detector ALLOW → NO.**

The detector's "no lexical overlap → novel → allow" branch fires for any
candidate whose tokens don't share 8-char substrings with either source. ADV-01
is a synonym-substituted paraphrase of Source A (every content word is a
synonym: skeletal↔bone, calcification↔calcium phosphate deposition,
process↔mineralization). The detector cannot detect synonymy.

### Q2: Can the detector allow a cross-source synthesis with one-source overlap?
**ADV-03 `enzyme-templated mineral deposition`: expected ALLOW, detector REJECT → NO.**

The candidate overlaps with Source A only (via `mineral`), and its unshared
tokens (`enzyme`, `templated`, `deposition`) do not appear in Source B literally
or via 8-char substring. The detector's "overlap with one source → check unshared
in other source" branch fires, finds no overlap, and rejects.

The detector cannot recognize that `enzyme` is a hypernym of Source B's
`silicatein` (silicatein IS an enzyme).

### Q3: Can the detector reject a source-local derivative disguised as cross-domain?
**ADV-05 `hypermineralization`: expected REJECT, detector REJECT → YES (by accident).**

The detector's single-token suffix check catches the 5-char excess `"ation"`,
which matches the `"tion"` suffix with `len(suffix)+1 = 5` slack. The detector
rejects `hypermineralization` and `xenomineralization` correctly — but for purely
lexical parameter-tuning reasons, not because it recognizes that `hyper-` and
`xeno-` are degree/foreign modifiers.

### Q4: Can the detector DISTINGUISH no-overlap ALLOW from no-overlap REJECT?
**ADV-07 (true ALLOW): detector ALLOW. ADV-01 (true REJECT): detector ALLOW.**
**→ Detector gives the SAME answer for both: cannot distinguish.**

This is the central exhibit. The detector's "no overlap → allow" rule is
structurally unable to distinguish a synonym-substituted source-local paraphrase
(true REJECT) from a cross-source generalization with no lexical anchor (true
ALLOW). Both produce zero lexical overlap; both fall through to the same ALLOW
branch.

### Q5: Does the round-72 suffix-heuristic generalize beyond the test fixture?
**ADV-11 `biomineralization` (true ALLOW, excess `"ion"` 3 chars): detector ALLOW → RIGHT.**
**ADV-13 `pseudomineralization` (true REJECT, excess `"zation"` 6 chars): detector ALLOW → WRONG.**

The same `non-suffix excess ≥ 3 chars → ALLOW` branch fires for both cases. The
branch gives the correct answer on ADV-11 (because `biomineralization` happens to
be a true cross-source umbrella) and the wrong answer on ADV-13 (because
`pseudomineralization` is a source-local derivative whose excess doesn't fit a
suffix in the list).

This is the keystone exhibit: the round-72 fix is parameter-tuning, not semantic
analysis. The boundary between ADV-11 (correct ALLOW) and ADV-13 (incorrect
ALLOW) is **the length of the excess string**, not any semantic property of the
candidate.

## Failure-mode taxonomy

The 6 mismatches cluster into three failure modes:

### Mode A — No-overlap source-local paraphrases wrongly allowed (ADV-01, ADV-02)
Both candidates are synonym-substituted paraphrases of Source A with zero lexical
overlap. The detector's "no overlap → novel → allow" branch fires. The detector
has no mechanism to detect synonymy or paraphrase.

### Mode B — Cross-source syntheses wrongly rejected (ADV-03, ADV-04, ADV-08)
All three candidates have lexical overlap with one source only, and the
candidate's cross-source connection is semantic (hypernymy: `enzyme`↔`silicatein`,
`calcification`↔`calcium phosphate deposition`, `biogenic oxide precipitation`↔
both sources' mineral systems). The detector's "check unshared tokens in other
source" branch is purely lexical and cannot detect hypernymy.

### Mode C — Source-local derivative wrongly allowed (ADV-13)
The candidate is a source-local derivative whose excess (`"zation"`, 6 chars)
does not match any suffix in `COMMON_SUFFIXES` with the `+1` slack. The same code
branch that correctly allows ADV-11 (a true cross-source umbrella) wrongly allows
ADV-13 (a true source-local derivative). The detector's allow/reject decision on
single-token source-local derivatives is determined by the length of the excess
string, not by any semantic property of the candidate.

## Disposition

```text
B-1:
  IMPLEMENTATION EVIDENCE PRESENT
  INDEPENDENT ADJUDICATION REQUIRED
  → ELIGIBLE (unchanged)

B-2 exact leakage:
  DEMONSTRATED (control ADV-10)
  → PASS for exact-string component

B-2 lexical/morphological leakage:
  DEMONSTRATED for tested cases (controls ADV-12, ADV-05, ADV-06)
  → PASS for cases whose excess fits a suffix in COMMON_SUFFIXES

B-2 semantic paraphrase leakage:
  NOT DEMONSTRATED (Mode A: ADV-01, ADV-02)
  → FAIL

B-2 cross-source justification:
  NOT DEMONSTRATED (Mode B: ADV-03, ADV-04, ADV-08; Mode C: ADV-13)
  → FAIL

Protocol B:
  BLOCKED
```

## What this establishes (and what it does NOT)

### Establishes
- The round-72 fix is parameter-tuning, not semantic analysis. The same code
  branch produces opposite correct answers on ADV-11 vs ADV-13, and the
  distinguishing factor is the length of the excess string, not any semantic
  property of the candidate.
- The detector has no mechanism to detect semantic paraphrase (Mode A).
- The detector has no mechanism to detect hypernymy or concept-level reference
  (Mode B).
- The detector's allow/reject decision on single-token source-local derivatives
  is determined by whether the excess string happens to fit a suffix in
  `COMMON_SUFFIXES` with the `+1` slack (Mode C).

### Does NOT establish
- That the detector "establishes cross-source justification" for any candidate.
  The detector's ALLOW on ADV-07 and ADV-11 is by accident (parameter-tuning or
  no-overlap default), not by demonstrated semantic reasoning.
- That the round-72 fix is "wrong" in the sense of producing a wrong answer on
  the original 6/6 fixture. The 6/6 result is reproducible (controls ADV-09,
  ADV-10, ADV-11, ADV-12 all pass). What the round-72 fix does NOT do is
  **generalize** to adversarial cases outside its parameter-tuning sweet spot.

## Meta-property (5) verification

The auditor's meta-property (5) required that each case ship its own semantic
adjudication rationale as a separate document, so the expected disposition is
derivable by a human from the evidence rather than from a hard-coded label in
the test fixture.

Verification:
- Each case has a rationale file at `cases/ADV-NN.md` (13 files).
- Each rationale walks through: (a) lexical overlap audit, (b) semantic content
  of the candidate, (c) semantic mapping to Source A, (d) semantic mapping to
  Source B, (e) cross-source synthesis argument, (f) independent semantic
  verdict.
- The `expected_label` in `test_fixture.json` is the OUTPUT of the rationale's
  semantic reasoning, not an independently asserted label.
- A human adjudicator can read `cases/ADV-NN.md` and verify `expected_label`
  without consulting `test_fixture.json`.

The meta-property is satisfied. The oracle has been moved OUT of the test
fixture and INTO a human-readable rationale document that derives the label from
first principles.

## Files

- `sources.md` — canonical source_a, source_b, definition of cross-source synthesis
- `cases/ADV-01.md` through `cases/ADV-13.md` — per-case semantic rationales
- `test_fixture.json` — bare test cases (candidate + sources + expected label)
- `diagnostic_runner.py` — runs the current detector against the fixture
- `diagnostic_results.json` — machine-readable diagnostic output
- `diagnostic_results.md` — this report

## Production substrate status

**UNCHANGED.** No modifications were made to `b1_b2_verification.py`,
`_check_leakage`, or any other file in the engine repository. The detector was
imported as-is from commit `20ac268` and run against the adversarial fixture as a
read-only diagnostic.

Protocol B remains BLOCKED. The next step is for the auditor to review this
diagnostic and either:
1. Adjudicate the 6 mismatches (confirm the rationale-derived expected labels are
   correct), OR
2. Identify additional adversarial cases that should be added to the set before
   adjudication.

The detector is NOT to be modified until the adversarial set has been
independently adjudicated and the auditor has approved a repair target.
