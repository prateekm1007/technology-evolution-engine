# GO / NO-GO GATES

Cycle 258. Canonical gate structure per ROADMAP_V2.md.

These gates supersede the DR-97..DR-101 gate architecture from
cycles 256-257 (which remain as evidence and foundation). The new
structure has 4 gates, one per Program A-D. Gate 4 (Invention) is
the final gate; it cannot pass until Gates 1-3 pass.

---

## Gate 1 — Measurement (Program A: Computational Metrology)

**Pass only if ALL of the following are satisfied:**

| Criterion | Stage | Status |
|---|---|---|
| Bootstrap statistics implemented | M3 | **PASS** (cycle 261: all 30 metrics bootstrapped, B=500/200/100) |
| Confidence intervals on all metrics | M3 | **PASS** (cycle 261: all 30 metrics have 95% CIs in reports/bootstrap_statistics.json) |
| Evaluator reliability quantified | M4 / E1 | **PARTIAL** (cycle 267: 3 evaluator metrics tested × 10 seeds; M-305 bias STABLE, M-306 ECE STABLE, M-304 agreement UNSTABLE CV=0.64 — N=6 too small) |
| Calibration documented | M2 / E1 | NOT STARTED |
| Repeatability demonstrated | M4 | **PASS** (cycle 263: 5 metrics × 10 seeds, all CV < 0.15; 2 deterministic, 3 nondeterministic) |
| Measurement specification complete | M1 | **PASS** (cycle 260: 30/30 metrics specified, all 9 fields each) |
| Measurement provenance (no naked numbers) | M2 | **PASS** (cycle 262: ScoredValue + ProvenanceRegistry + @with_provenance infrastructure complete; 38 metrics loaded) |
| Reproducibility across hardware/LLMs/prompts | M5 | NOT STARTED |
| Sensitivity analysis | M6 | **PARTIAL** (cycle 264: 26 perturbations tested, 18 ROBUST, 4 SENSITIVE, 4 FRAGILE; truncate_75pct and M-010 input perturbation are repair priorities) |
| Failure envelope documented | M7 | **PASS** (cycle 265: 38 failure envelope documents generated, all with failure modes + boundary conditions + repair recommendations) |
| Measurement constitution | M8 | **PASS** (cycle 266: 8 constitutional rules, 304 compliance checks, all compliant) |

**Current verdict: IN PROGRESS.** Stage M1 PASS. M3 PASS. M2 PASS.
M4 PASS. M6 PARTIAL. M7 PASS. M8 PASS. Evaluator reliability (M4/E1)
PARTIAL — 3 evaluator metrics tested, M-304 UNSTABLE (N=6 too small).
2 of 11 criteria remain NOT STARTED (M5 reproducibility, calibration
documented). This is the project's #1 priority.

---

## Gate 2 — Discovery (Program B: Discovery Recovery)

**Pass only if ALL of the following are satisfied:**

| Criterion | Stage | Status |
|---|---|---|
| Proposal benchmark replaces entity benchmark | D1 | NOT STARTED |
| External baselines included (true external, not oracle-assisted) | D3 | INSTRUMENTATION_SCAFFOLD_PASS (DR-97, oracle-assisted; needs repair) |
| Historical recalibration complete | D4 | SENSITIVITY_ANALYSIS_PASS (DR-98, sensitivity only; needs full recalibration) |
| FP floor acceptable | D2 | FAIL (FP floor = 1.0, per DR-91) |
| Human review completed | D5 | AI_SURROGATE_REVIEW_FAIL (DR-100; 0/6 accepted) |
| Mechanism-first benchmark | D2 | NOT STARTED |

**Current verdict: BLOCKED.** 5 of 6 criteria not started or failed.
Discovery work is frozen per Program B until this gate passes.

---

## Gate 3 — Proposal (Program C: Proposal Science)

**Pass only if ALL of the following are satisfied:**

| Criterion | Stage | Status |
|---|---|---|
| Mechanism-driven proposals outperform Gen0 | P1 | NOT STARTED (Gen0 frozen) |
| Independent evaluation improves | P3 | NOT STARTED |
| Calibration bias decreases relative to Gen0 | P3 | NOT STARTED |
| ScientificClaim canonical object | P2 | NOT STARTED |

**Current verdict: NOT STARTED.** Gen0 is frozen. Stage P1 (mechanism-driven
composer) cannot begin until Gate 1 (Measurement) is at least PARTIAL,
because we cannot measure "outperform Gen0" without a trustworthy
measurement layer.

---

## Gate 4 — Invention (Program E: Invention Engine)

**Pass only if ALL of the following are satisfied:**

| Criterion | Stage | Status |
|---|---|---|
| Proposal engine trusted (Gate 3 PASS) | — | BLOCKED (Gate 3 not started) |
| Measurement engine trusted (Gate 1 PASS) | — | BLOCKED (Gate 1 not started) |
| Discovery benchmark trusted (Gate 2 PASS) | — | BLOCKED (Gate 2 not started) |

**Current verdict: BLOCKED.** Invention work is frozen per Program E
until Gates 1-3 pass. This is the most explicit "STOP BUILDING" in
the entire roadmap.

---

## Meta-gate: FINAL verdict

The FINAL verdict (replacing PRELIMINARY_MEASUREMENT_VERDICT.md as
canonical) requires:
- Gate 1 PASS
- Gate 2 PASS
- Gate 3 PASS
- Gate 4 PASS

Current state: **0/4 gates PASS.** Gate 1 is IN PROGRESS (Stage M3
complete, Stage M1 63%). PRELIMINARY (NOT TRUSTWORTHY) remains canonical.

---

## Sequencing rules

1. **Gate 1 must be attempted first.** No other gate can be honestly
   evaluated until the measurement layer is trustworthy.
2. **Gate 2 depends on Gate 1.** Discovery claims require measurement
   to be meaningful.
3. **Gate 3 depends on Gate 1 and Gate 2.** Proposal quality claims
   require both measurement and discovery benchmark trust.
4. **Gate 4 depends on Gate 1, 2, 3.** Invention claims require all
   three.

This sequencing is constitutional. Violations are STOP_BUILDING list
violations.

---

## Worked example: what counts as "Gate 1 progress"

Adding bootstrap statistics to F1 (Stage M3) counts as Gate 1 progress.
Adding a new proposal composer (Stage P1) does NOT count as Gate 1
progress — it's Gate 3 progress, and Gate 3 is blocked until Gate 1
passes.

Adding an external BM25 baseline (Stage D3) does NOT count as Gate 1
progress — it's Gate 2 progress, and Gate 2 is blocked until Gate 1
passes. (DR-97 already did this prematurely; it's labeled
INSTRUMENTATION_SCAFFOLD_PASS for this reason.)
