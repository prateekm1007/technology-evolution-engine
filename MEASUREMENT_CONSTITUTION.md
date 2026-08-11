# MEASUREMENT CONSTITUTION

Cycle: 266. Stage M8. Program A.
Per ROADMAP_V2.md: 'Rules every future metric must satisfy.'

This document is the constitutional layer of the measurement
engine. It codifies everything learned from Stages M1-M7 and
the DR-91..DR-101 audit into 8 enforceable rules. Every future
metric MUST satisfy all 8 rules before it may be used in any
capability claim.

---

## MC-1: No self-validation

**Statement:** A metric may not be validated by the same system that produced it. Every metric must have an independent rescoring path.

**Source:** DR-94 (M-305 bias = +2.50, 100% overestimate), ROADMAP_V2 M8

**Enforcement:** Every metric specification (M1) must document an independent evaluator. The measurement audit modules (dr91_dr96) reproduce matchers from scratch (zero production imports).

---

## MC-2: Independent rescoring

**Statement:** Every metric must have an independent implementation that reproduces the score without sharing matching code with production.

**Source:** DR-91 (independent matcher, zero production imports), ROADMAP_V2 M8

**Enforcement:** The DR-91 audit module (dr91_measurement_audit.py) reproduces all matchers (m_exact, m_token, m_fuzzy, m_synonym) from scratch. The bootstrap module (bootstrap_statistics.py) uses the same independent matchers.

---

## MC-3: Confidence calibration

**Statement:** Every metric that produces a confidence score must report ECE or Brier score. Confidence without calibration is forbidden.

**Source:** DR-96 (M-306 ECE = 0.433, poorly calibrated), ROADMAP_V2 M8

**Enforcement:** M-306 (ECE) is specified in M1 and bootstrapped in M3. ECE > 0.2 blocks any confidence-based claim (per DR-96). The ScoredValue (M2) carries calibration_version.

---

## MC-4: Evidence tiers

**Statement:** Every metric must declare an evidence tier (A-I per CONSTITUTION evidence hierarchy). Metrics at tier I (LLM inference) carry weight 0.20 and must be flagged as 'unverified — inference only.'

**Source:** CONSTITUTION evidence hierarchy, M1 specification, ROADMAP_V2 M8

**Enforcement:** Every metric in MeasurementEngineSpecification.md (M1) has an 'Evidence tier' field. The ScoredValue (M2) carries evidence_tier. The bootstrap (M3) reports tier.

---

## MC-5: Adversarial testing

**Statement:** Every metric must be tested against adversarial inputs: FP floor (random candidates) must be < 5%, sensitivity to input perturbation must be documented (M6), and a failure envelope must exist (M7).

**Source:** M6 (sensitivity), M7 (failure envelope), DR-91 (FP floor), ROADMAP_V2 M8

**Enforcement:** M-008 (FP floor) is specified, bootstrapped, and has a failure envelope. M6 tests 26 perturbations across 4 metrics. M7 generates 38 failure envelope documents. FP floor > 5% blocks discovery claims.

---

## MC-6: Historical permanence

**Statement:** No metric may be silently altered. Historical scores must be reproducible. Code drift must be documented. Repeatability (M4) must be demonstrated.

**Source:** CONSTITUTION Law 7, M4 (repeatability), M-201 code drift, ROADMAP_V2 M8

**Enforcement:** M4 runs 5 metrics × 10 seeds, all CV < 0.15. Code drift (M-201 documented 2/10 vs current 8.3/10) is documented in the failure envelope. FAILURES.md is append-only (Law 7). Historical recalibration (DR-98) re-scores past claims.

---

## MC-7: No naked numbers

**Statement:** No score may be reported as a bare scalar. Every score must be a ScoredValue with ± uncertainty, 95% CI, evidence tier, calibration version, evaluator version, benchmark version, timestamp.

**Source:** M2 (provenance), ANTI_ENTROPY line 559 ('no bare scalar'), ROADMAP_V2 M8

**Enforcement:** ScoredValue dataclass (M2) has 17 fields. @with_provenance decorator wraps score functions. ProvenanceRegistry loads bootstrap CIs. is_naked_number() detects bare floats.

---

## MC-8: Bootstrap uncertainty

**Statement:** Every metric must report a bootstrap 95% CI with N and B. Point estimates without CIs are forbidden.

**Source:** M3 (bootstrap), ROADMAP_V2 Stage M3

**Enforcement:** bootstrap_statistics.py bootstraps all 38 metrics (B=500/200/100, seed=42). reports/bootstrap_statistics.json contains CIs for all metrics. MeasurementEngineSpecification.md (M1) Uncertainty fields are populated from M3.

---

## Compliance

Compliance is checked by `programs/A_metrology/measurement_constitution_m8.py`
and enforced by `tests/test_measurement_constitution_m8.py`. The
compliance report is at `reports/measurement_constitution_m8.json`.

A metric that violates any rule is BLOCKED from use in capability
claims until the violation is resolved.

---

## Relationship to CONSTITUTION.md

This document extends CONSTITUTION.md with measurement-specific
rules. The relationship is:

- **CONSTITUTION.md Principle 1**: 'No capability work until the
  measurement layer proves it can measure that capability.'
  This document defines what 'proves it can measure' means: the
  8 rules below.
- **CONSTITUTION.md Law 7**: 'Historical permanence.' MC-6
  operationalizes this for metrics.
- **CONSTITUTION.md Law 8**: 'Verification standard.' MC-1 and
  MC-2 operationalize this for measurement.
- **ANTI_ENTROPY line 559**: 'No layer's output may emit a bare
  scalar.' MC-7 operationalizes this.

---

## Relationship to ROADMAP_V2.md

ROADMAP_V2.md Stage M8 lists 6 example rules. This document
codifies 8 (the 6 examples plus MC-7 no-naked-numbers from M2
and MC-8 bootstrap-uncertainty from M3, both of which are
direct consequences of the M2/M3 work).
