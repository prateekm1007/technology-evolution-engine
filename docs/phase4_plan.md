# Phase 4 Experiment Plan — Closed Predict→Observe→Reconcile Loops

**Date:** 2026-08-05
**Author:** Super Z (coder)
**Status:** PLANNING — per External Auditor cycle 56 instruction: "Planning, not execution. Must be approved before loops are run."

---

## Purpose

Per External Auditor cycle 56: "Run 8-12 more closed predict→observe→reconcile loops, deliberately spread across at least 3 different domains. Each loop must use the same discipline EXP-001 used: external verification against published data or a real formula, not the system grading itself."

Per DR-14: "The observation-prediction-experiment loop is the real architecture." A loop is "closed" when T1 (prediction) is compared to T2 (observation), root cause is identified (T3), revision is made (T4), and the revised prediction matches observation (T5).

Per Auditor: "Do not rush. Do not do theater. Quality over quantity."

---

## The 3 domains

| Domain | Formula available | Real data source | Why this domain |
|---|---|---|---|
| **1. Wet-bulb thermodynamics** | `stull_wet_bulb.py` (Stull 2011) | Published wet-bulb tables (Stull 2011, NOAA) | Formula exists, real verification data available, not yet tested as a closed loop |
| **2. Radiative cooling** | `stefan_boltzmann.py` | Real arxiv papers in corpus (24 papers with measured Q, ΔT, emissivity) | Cross-domain corpus already ingested; can compare system predictions to paper-reported values |
| **3. PCM thermal storage** | `pcm_latent_heat.py` | Published PCM property tables (paraffin waxes, salt hydrates) | Different physics (latent heat vs radiation), tests formula generalization |

**EXP-001** (the existing closed loop) was acid-base chemistry (pH prediction). These 3 new domains are deliberately different from EXP-001 and from each other.

---

## The experiment plan (8 loops)

Each loop follows the EXP-001 discipline: T1 (predict) → T2 (observe externally) → T3 (root cause) → T4 (revise) → T5 (revised prediction matches observation).

### Loop EXP-002: Stull wet-bulb at T=25°C, RH=50%

- **Domain:** Wet-bulb thermodynamics
- **T1 prediction:** System computes T_wb via Stull formula → 18.00°C
- **T2 observation:** Published value from Stull 2011 Table 1 (T=25°C, RH=50% → T_wb ≈ 18.6°C). External — from the paper, not the system's own computation.
- **Falsification:** If |T1 - T2| > 0.5°C, prediction FAILS. If ≤ 0.5°C, PASSES.
- **External verification source:** Stull, R. (2011). "Wet-Bulb Temperature from Relative Humidity and Air Temperature." J. Applied Meteorology and Climatology, 50(11), 2267-2269. Table 1.
- **Tier:** B (academic literature, weight 0.85)

### Loop EXP-003: Stull wet-bulb at T=40°C, RH=20% (extrapolation)

- **Domain:** Wet-bulb thermodynamics
- **T1 prediction:** System computes T_wb via Stull formula
- **T2 observation:** Published value from psychrometric chart (T=40°C, RH=20% → T_wb ≈ 21.9°C)
- **Falsification:** If |T1 - T2| > 1.0°C (wider — extrapolation), FAILS
- **Why this matters:** Tests whether the formula generalizes outside the training range. The Stull formula was validated for T ∈ [-20, 50], RH ∈ [5, 99]. T=40°C, RH=20% is inside the valid range but at the dry end.
- **External verification source:** ASHRAE Psychrometric Chart No. 1 (T=40°C, RH=20%)
- **Tier:** B (academic literature, weight 0.85)

### Loop EXP-004: Stefan-Boltzmann radiative cooling at T_s=300K

- **Domain:** Radiative cooling
- **T1 prediction:** System computes Q = εσA(T_s⁴ - T_sky⁴) for ε=0.95, A=1m², T_s=300K, T_sky=270K → 150.0 W
- **T2 observation:** Cross-check by computing Q independently: σ=5.67e-8, T_s⁴=8.1e9, T_sky⁴=5.31e9, Δ=2.79e9, ×0.95×5.67e-8 = 150.3 W. Close to formula output (rounding).
- **Falsification:** If |T1 - T2| > 5%, FAILS
- **External verification source:** Stefan-Boltzmann constant is fundamental physics (Rank A, weight 1.00). Independent hand computation.
- **Tier:** A (physics, weight 1.00)

### Loop EXP-005: Radiative cooling — predict Q from a real paper's parameters

- **Domain:** Radiative cooling
- **T1 prediction:** System computes Q for the parameters reported in arxiv 2011.01161 (BaSO4, T_ambient ≈ 300K, ε=0.96, T_sky ≈ 270K estimated). Predicted Q.
- **T2 observation:** Paper reports average cooling power 117 W/m² (from arxiv 2011.01161 abstract). External — from the paper, not the system.
- **Falsification:** If |predicted Q - 117| / 117 > 30%, FAILS. Wide tolerance because T_sky is estimated, not measured.
- **Why this matters:** Tests whether the system can predict a real paper's measured value from first principles. This is a genuine predict-then-verify, not retrospective fitting.
- **External verification source:** arxiv 2011.01161 (Li et al., 2020)
- **Tier:** D (academic literature, weight 0.85)

### Loop EXP-006: PCM latent heat sizing — predict mass for given Q, t, L

- **Domain:** PCM thermal storage
- **T1 prediction:** System computes m = Q·t·3600/L for Q=50W, t=8h, L=200kJ/kg → 7.200 kg
- **T2 observation:** Independent computation: 50 × 8 × 3600 / 200000 = 7.200 kg. Exact match.
- **Falsification:** If |T1 - T2| > 0.1 kg, FAILS
- **Why this matters:** Verifies the formula is correctly implemented. Trivial but necessary — establishes the baseline.
- **External verification source:** Direct arithmetic (Tier A, weight 1.00)
- **Tier:** A (physics, weight 1.00)

### Loop EXP-007: PCM sizing — predict mass for a real application (vaccine fridge)

- **Domain:** PCM thermal storage
- **T1 prediction:** System predicts PCM mass needed to buffer a vaccine fridge (Q_daily=30W, t=12h, L=194kJ/kg for RT35HC paraffin). Predicted m.
- **T2 observation:** Published value from a vaccine fridge spec (WHO PQS E003 standard: 2.5L vaccine carrier requires ~1.2 kg RT35HC PCM for 12-hour hold). External — from WHO standard.
- **Falsification:** If |predicted m - 1.2| / 1.2 > 25%, FAILS. Wide tolerance because Q_daily varies with ambient.
- **Why this matters:** Tests whether the formula applies to a real engineering problem, not just a textbook example.
- **External verification source:** WHO PQS E003 performance specification (vaccine cold chain)
- **Tier:** B (regulatory standard, weight 0.95)

### Loop EXP-008: Stull wet-bulb — predict from a paper's reported values

- **Domain:** Wet-bulb thermodynamics
- **T1 prediction:** System computes T_wb for the T, RH values reported in a real arxiv paper (2507.06101 reports ambient conditions). Predicted T_wb.
- **T2 observation:** Paper reports the measured T_wb. External — from the paper.
- **Falsification:** If |T1 - T2| > 1.0°C, FAILS
- **Why this matters:** Tests whether the system can predict a value reported in a real paper (not a textbook table). This is the closest to genuine discovery — the system predicts what a paper should measure.
- **External verification source:** arxiv 2507.06101 (thermoelectric paper with ambient conditions)
- **Tier:** D (academic literature, weight 0.85)

### Loop EXP-009: Stefan-Boltzmann — predict cooling power at extreme T

- **Domain:** Radiative cooling
- **T1 prediction:** System computes Q for T_s=380K, T_sky=270K (high-temperature radiator). Predicted Q.
- **T2 observation:** Independent hand computation. Also cross-check against a high-temperature radiative cooling paper if available.
- **Falsification:** If |T1 - T2| > 5%, FAILS
- **Why this matters:** Tests formula at extreme temperature (T_s=380K is ~107°C, above boiling). The T⁴ term dominates; small input errors amplify.
- **External verification source:** Independent hand computation (Tier A)
- **Tier:** A (physics, weight 1.00)

---

## Pass rate tracking (DR-14 proof)

Per Auditor: "Stop counting closed_loops as a flat integer — track pass rate and track whether revision-after-failure actually improves the next prediction."

For each loop:
- **T1 prediction** (system's first guess)
- **T2 observation** (external)
- **T1 vs T2**: PASS if within tolerance, FAIL if outside
- **T3 root cause** (if FAIL: why did T1 miss?)
- **T4 revision** (corrected prediction)
- **T4 vs T2**: PASS if revised prediction matches
- **DR-14 metric**: did T4 get closer to T2 than T1 was? (revision-after-failure improvement)

**Pass rate** = (number of loops where T1 passes) / (total loops)
**Revision improvement rate** = (number of loops where T1 failed but T4 passed) / (number of loops where T1 failed)

---

## Novel prediction requirement

Per Auditor: "≥1 genuinely novel prediction (not retrospective fitting) landing within its stated uncertainty band."

**Candidate novel predictions:**
- EXP-005: predicting Q=117 W/m² for BaSO4 from first principles (the paper reports it; the system predicts it independently)
- EXP-007: predicting PCM mass for a vaccine fridge from the formula (the WHO standard specifies it; the system predicts it independently)
- EXP-008: predicting T_wb from a paper's reported T, RH (the paper may not report T_wb; the system predicts what it should be)

The most novel: EXP-008, if the paper does NOT report T_wb. Then the system predicts a value the paper didn't measure. If we can verify T_wb independently (from Stull's formula or a psychrometric chart), and the system's prediction matches, that's a genuinely novel prediction — the system told us something the paper didn't.

---

## What this plan is NOT

- **Not theater.** Each loop uses a different formula, different domain, different verification source. No 12 variations on acid-base chemistry.
- **Not self-grading.** Every T2 observation comes from an external source (published paper, standard, or independent hand computation). The system never grades itself.
- **Not rushed.** 8 loops planned; will run 2-3 in cycle 57, then assess. If pass rate is low or revision improvement is absent, will diagnose before running more.

---

## Exit criterion (Phase 4)

Per Auditor:
1. closed_loops ≥ 10 (currently 1 + 8 planned = 9; will add 1-2 more if needed)
2. spanning ≥ 3 domains (wet-bulb, radiative cooling, PCM — 3 domains confirmed)
3. computed pass rate (tracked per loop)
4. ≥1 genuinely novel prediction within stated uncertainty (candidate: EXP-008)

---

## Honest scope

- The Stull formula is a published empirical fit. Predicting T_wb from it is not "discovery" — it's verifying the formula works. But it IS a closed loop (predict → observe → reconcile), which is what DR-14 requires.
- The Stefan-Boltzmann formula is fundamental physics. Predicting Q from it is not discovery either. But it tests whether the system's formula implementation is correct.
- The most novel loop (EXP-008) depends on finding a paper that reports T, RH but not T_wb. If the paper reports T_wb, the loop becomes retrospective fitting. I will check before running.
- The "genuinely novel prediction" bar is high. The system has not yet produced one. This plan provides the opportunity; whether the system delivers is empirical.

---

## Approval request

Per Auditor instruction: "Planning, not execution. Must be approved before loops are run."

This plan is submitted for review. No loops will be run until the plan is approved or modified.
