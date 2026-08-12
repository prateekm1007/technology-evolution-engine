# PROSPECTIVE EXPERIMENT PROTOCOL

**Date:** 2026-08-12
**Task ID:** v1.13-postmortem-and-prospective-infra
**Status:** INFRASTRUCTURE COMPLETE. EXPERIMENT NOT YET RUN.
**Directive:** "Do not run the prospective experiment yet. First make the entire pipeline auditable and independently reproducible."

---

## 1. Purpose

This document specifies the protocol for the prospective experiment that will
test the North Star question:

> "Can TEE produce independently novel, retrieval-negative, adversarially
> surviving, falsifiable hypotheses at a materially higher rate than controls?"

The retrospective V1.13 experiments (frozen at `7209b294` and `38b9b62e`)
could not establish this because of parametric-memory leakage, experimenter
bias in case selection, and the absence of a true control. The postmortem
(`v1_13_postmortem/V1.13_RETROSPECTIVE_BENCHMARK_POSTMORTEM.md`) documents
why retrospective evaluation is exhausted.

The prospective experiment is the next legitimate test.

---

## 2. The Pipeline (7 Stages)

```
PRE_REGISTER → FREEZE_MODEL → FREEZE_EVIDENCE → GENERATE_PREDICTION
            → WAIT → EXTERNAL_OBSERVATION → DETERMINISTIC_SCORE
```

### Stage 1: PRE_REGISTER
**Module:** `pre_registration.py`
**Output:** Sealed pre-registration manifest (in `manifests/`)

The manifest fixes EVERYTHING that is decided before any prediction is generated:
- Problem set (selected independently of outcomes — see §4)
- Model snapshot identifier (version pin or weights hash)
- Retrieval corpus (frozen, hash-sealed)
- Prompt templates for all 4 arms (B_llm_only, C_mechanism, F_full, D_random)
- Analysis plan (α, MDE, sample size, INDETERMINATE handling, decision rule)
- Observation window (start, end)
- Outcome source specification (independent of engine)
- Trusted timestamp (UTC, from system clock; verified against file mtime)

The manifest is hash-sealed immediately after creation. Any modification
is detectable by re-computing the hash.

### Stage 2: FREEZE_MODEL
**Module:** `pre_registration.py` (verification in `generator.py`)
**Output:** Model snapshot verification record

Before any prediction is generated, the model snapshot is verified to match
the manifest:
- If local model: hash the weights file, compare to manifest's `weights_hash`
- If hosted model: query the endpoint's version info, compare to manifest's `model_version`

If the model has been updated since registration, the experiment is ABORTED.

### Stage 3: FREEZE_EVIDENCE
**Module:** `pre_registration.py` (verification in `generator.py`)
**Output:** Retrieval corpus verification record

The retrieval corpus is verified to match the manifest:
- Hash the corpus manifest file, compare to manifest's `corpus_hash`
- Verify the document count matches
- Verify the date filter excludes all documents dated after the manifest timestamp

If the corpus has been modified since registration, the experiment is ABORTED.

### Stage 4: GENERATE_PREDICTION
**Module:** `generator.py`
**Output:** 4 × N sealed prediction receipts (in `receipts/`)

For each of N problems, generate 4 predictions (one per arm) in the SAME run:
- All 4 arms use the SAME model snapshot, SAME corpus, SAME generation_timestamp
- The generator is given ONLY the problem description + retrieved evidence
- The generator is NOT given any outcome information
- Each prediction is a point estimate + tight multiplicative tolerance
  (tolerance_lower ≥ 0.25, tolerance_upper ≤ 4.0)
- Broad ranges (e.g., "[1, 1000]") are forbidden
- Each receipt is hash-sealed immediately after generation

If a generation fails, it is recorded as INDETERMINATE (no retries with
different prompts; same-prompt retries are allowed).

### Stage 5: WAIT
**Module:** `observation_window.py` (verification in `audit_verifier.py`)
**Output:** (no output — this is a quiescent period)

Between `generation_timestamp` and `observation_window.window_start`, NO
engine activity is permitted. The audit verifier checks that no log entries
exist in this interval.

The observation window is pre-registered (e.g., "12 months after registration"
to "24 months after registration"). The window duration depends on the
problem domain — materials science may need 24 months; biology may need
36 months.

### Stage 6: EXTERNAL_OBSERVATION
**Module:** `observation_window.py`
**Output:** N sealed observation records (in `observations/`)

During the observation window, an INDEPENDENT curator (NOT the experimenter)
collects outcomes from the pre-registered source:
- The source is specified in the manifest (e.g., "peer-reviewed publication
  in journal X", "public database Y", "regulatory filing Z")
- The curator signs a statement of independence
- The curator extracts the outcome value + measurement date from the source
- The curator seals the observation and appends it to the log
- Observations collected before `window_start` or after `window_end` are rejected
- Observations from sources other than the pre-registered source are rejected

### Stage 7: DETERMINISTIC_SCORE
**Module:** `deterministic_scorer.py` + `pre_registered_analysis.py`
**Output:** Sealed score records + sealed analysis result (in `scores/`)

After ALL observations are collected:
1. The deterministic scorer scores each receipt against its observation
   - Information-content test (deterministic entailment, no LLM judge)
   - Quantitative accuracy (point estimate + tolerance, calibration error)
   - Final classification: RECONSTRUCTION / GENUINE_NOVEL_PREDICTION /
     CORRECT / INCORRECT / INDETERMINATE
   - DPS=1 if GENUINE_NOVEL_PREDICTION AND CORRECT
2. The pre-registered analysis is applied:
   - Two-proportion z-test (treatment vs. random control) for each treatment arm
   - Bonferroni correction (α / num_comparisons)
   - Decision rule (pre-registered, immutable):
     POSITIVE_RESULT requires ALL of:
       - ≥ 3 GENUINE_NOVEL_PREDICTION cases across the treatment arm
       - Treatment DPS=1 rate ≥ random DPS=1 rate + 15pp
       - z-test p-value < α / num_comparisons
       - ≥ 1 CORRECT case with calibration_error ≤ 0.50
     Otherwise: NEGATIVE_RESULT

---

## 3. Auditability Guarantees

The entire pipeline is auditable by an independent third party. The
`audit_verifier.py` module checks 27 critical invariants (I1-I27):

### Manifest invariants
- **I1.** Manifest is hash-sealed and unmodified.
- **I2.** Manifest timestamp is real (UTC, not backdated, within 60s of file mtime).
- **I3.** Problem set contains no outcome information (no "answer" keys).
- **I4.** All 4 arms registered in the same manifest with the same timestamp.
- **I5.** Analysis plan is sealed in the manifest (not a separate file).

### Generator invariants
- **I6.** Generator was not invoked before manifest was sealed.
- **I7.** Model snapshot matches manifest.
- **I8.** Retrieval corpus matches manifest.
- **I9.** Retrieval corpus date filter excludes post-registration documents.
- **I10.** All 4 arms generated in the same run (same generation_timestamp).
- **I11.** Generator was not given outcome information.
- **I12.** Each receipt is hash-sealed and unmodified.
- **I13.** No retries with different prompts (only same-prompt retries allowed).

### Observation invariants
- **I14.** No observation collected before window_start.
- **I15.** Observations come from the source specified in the manifest.
- **I16.** Observations collected by an independent curator.
- **I17.** Each observation is hash-sealed and unmodified.
- **I18.** Observation measurement_date is within the observation window.
- **I19.** Observation source URL is accessible (best-effort check).

### Scorer invariants
- **I20.** Scorer not invoked until all observations collected.
- **I21.** Scorer uses the analysis plan from the manifest.
- **I22.** Scorer is deterministic (reproducible).
- **I23.** Score output is hash-sealed and unmodified.

### Analysis invariants
- **I24.** Analysis plan applied is the one in the manifest.
- **I25.** Analysis applied only after all scores computed.
- **I26.** Analysis is deterministic (reproducible).
- **I27.** Analysis output is hash-sealed and unmodified.

The audit verifier produces a sealed audit report (hash-sealed, append-only
log entry). An independent auditor can re-run the verifier and obtain the
same audit hash.

---

## 4. Critical Requirements (Per Directive)

### R1. Model snapshot must be fixed before registration.
**Status:** Enforced by I7 + the manifest's `model_snapshot` field.
The model snapshot identifier (version pin or weights hash) is sealed in
the manifest at registration time. The generator verifies the snapshot
matches before generating any prediction.

### R2. Retrieval corpus must be frozen before prediction.
**Status:** Enforced by I8 + I9 + the manifest's `retrieval_corpus` field.
The corpus hash is sealed in the manifest at registration time. The
generator verifies the corpus matches and that the date filter excludes
post-registration documents.

### R3. Prediction timestamp must be real, not backdated.
**Status:** Enforced by I2 (manifest timestamp) and the receipt's
`generation_timestamp` field (which is `datetime.now(timezone.utc).isoformat()`
at generation time, not a parameter). The audit verifier checks that the
generation timestamp is after the manifest timestamp.

### R4. Prediction must be specific and falsifiable.
**Status:** Enforced by `validate_prediction()` in `generator.py`:
- BINARY predictions must be exact YES/NO
- Numeric predictions must have a point estimate + multiplicative tolerance
- Tolerance bounds: lower ≥ 0.25, upper ≤ 4.0 (no broad ranges)
- Each prediction must have a `falsification_condition` of ≥ 20 characters
  with a testable outcome (numeric bound, comparison, or negation)

### R5. No historical answer is supplied to the generator.
**Status:** Enforced by I3 + I11. The problem set is checked for forbidden
keys ("outcome", "answer", "result", etc.). The generator receives only
the problem description + retrieved evidence (which is itself filtered
to pre-registration documents only).

### R6. Future evidence is inaccessible until the observation window closes.
**Status:** Enforced by I9 + I14 + the corpus date filter. The retrieval
corpus is date-filtered to exclude documents dated after the manifest
timestamp. The audit verifier checks that no observation is collected
before `window_start`.

### R7. External outcomes must come from sources outside the engine.
**Status:** Enforced by I15 + I16 + the manifest's `outcome_source_spec`.
The outcome source is pre-registered (e.g., "peer-reviewed publication
in journal X"). The curator signs a statement of independence. The audit
verifier checks that each observation's `source_name` matches the
pre-registered source and that the `curator_statement` asserts independence.

### R8. Register controls at the same time: LLM-only, mechanism-only, full system, random.
**Status:** Enforced by I4 + I10. All 4 arms are registered in the same
manifest (I4) and generated in the same run with the same `generation_timestamp`
(I10). They cannot be registered or generated separately.

### R9. Do not generate the benchmark from known discoveries.
**Status:** Enforced by case-selection protocol (§5). The problem set
MUST be selected by a process that is independent of the discovery outcome:
- Random sampling from a problem space (e.g., "all materials-science problems
  proposed in 2024")
- Selection by an independent party who does not know which problems will
  be solved
- Selection from a pre-existing registry (e.g., a DARPA problem set) that
  was created before the engine existed

The manifest's `problem_set` field is audited (I3) to ensure no outcome
information is present. The case-selection protocol itself is documented
in the manifest's `outcome_source_spec.independence_verification` field.

### R10. Pre-register the analysis before observing outcomes.
**Status:** Enforced by I5 + I24. The analysis plan is sealed in the
manifest at registration time (I5). The analysis module verifies that
the applied plan matches the manifest's plan (I24). The decision rule
(POSITIVE vs. NEGATIVE) is in the analysis plan and cannot be modified
after outcomes are observed.

---

## 5. Case-Selection Protocol

The most difficult requirement is R9: "Do not generate the benchmark from
known discoveries."

V1.13 failed this requirement because all 10 cases were famous historical
discoveries. The prospective experiment must use a different case-selection
protocol. Acceptable protocols include:

### Protocol A: Pre-existing registry
Use a problem registry that was created before the engine existed. Examples:
- DARPA problem sets (e.g., DARPA ARC molecular synthesis challenges)
- XPRIZE competition problem statements
- NIH NCATS challenge problems
- Published "open problems" lists in specific domains

The registry must have been created before the pre-registration timestamp.
The problem set is sampled from the registry (optionally stratified by
domain).

### Protocol B: Forward-looking problem generation
Generate problems from a process that does not look at outcomes. Examples:
- "All materials combinations proposed in materials-science papers published
  in 2024-Q1 that have not yet been experimentally tested"
- "All protein targets in clinical-trial registrations as of 2024-Q1 that
  have no approved drug"

The problem set is generated by a script that reads only pre-registration
literature and does not check whether the problem has been solved.

### Protocol C: Independent party selection
An independent party (not the experimenter, not the engine) selects problems.
The independent party must certify that they did not know which problems
would be solved when they made the selection.

The selected protocol is documented in the manifest's
`outcome_source_spec.independence_verification` field.

---

## 6. Infrastructure Status

| Module | File | Status |
|---|---|---|
| Pre-registration | `pre_registration.py` | ✅ Built, infrastructure-verified |
| Generator | `generator.py` | ✅ Built, infrastructure-verified |
| Observation window | `observation_window.py` | ✅ Built, infrastructure-verified |
| Deterministic scorer | `deterministic_scorer.py` | ✅ Built, infrastructure-verified |
| Pre-registered analysis | `pre_registered_analysis.py` | ✅ Built, infrastructure-verified |
| Audit verifier | `audit_verifier.py` | ✅ Built, infrastructure-verified (27 invariants) |

All modules are in DRAFT mode. They produce sample / stub outputs for
infrastructure verification only. They do NOT execute the real experiment.

---

## 7. DO NOT RUN Directive

**The prospective experiment is NOT to be run until ALL of the following
are true:**

1. A real pre-registration manifest is built (no `TO_BE_*` placeholders).
2. The model snapshot is genuinely frozen (local model with pinned weights,
   or hosted model with version-pinned endpoint).
3. The retrieval corpus is genuinely frozen (hash-sealed, date-filtered,
   independently verifiable).
4. The problem set is selected via an acceptable case-selection protocol
   (§5), documented in the manifest.
5. An independent curator is engaged (not the experimenter).
6. An independent auditor has reviewed the manifest and the audit verifier
   returns PASS on all applicable invariants.
7. The observation window is set (typically 12-24 months, depending on
   problem domain).
8. The experimenter has committed to publishing the result regardless of
   whether it is POSITIVE or NEGATIVE.

Running the experiment before these conditions are met would reproduce
the same flaws that invalidated V1.13.

---

## 8. What a Positive Result Would Mean

If the prospective experiment produces a POSITIVE_RESULT (all 4 gates pass):
- The engine produced at least 3 GENUINE_NOVEL_PREDICTION cases (not
  reconstructable from evidence) that were later independently observed
  to be correct.
- The treatment arm's DPS=1 rate materially exceeds the random control's
  rate by ≥ 15 percentage points.
- The result is statistically significant at α = 0.05 (Bonferroni-corrected).
- At least 1 prediction was quantitatively accurate (calibration_error ≤ 0.50).

This would be the FIRST legitimate evidence that the engine can discover
things a strong LLM, retrieval system, and null generator cannot.

## 9. What a Negative Result Would Mean

If the prospective experiment produces a NEGATIVE_RESULT:
- The engine cannot produce discoveries at a rate above the random control,
  even under prospective, pre-registered, independently-audited conditions.
- The North Star thesis is refuted for the current architecture.
- Further work would require a fundamentally different approach (not just
  more data or better prompts).

Either result is publishable. The pre-registration ensures the analysis
cannot be p-hacked or cherry-picked after the fact.

---

## 10. Relationship to V1.13

V1.13 is permanently closed. The retrospective experiments are frozen at:
- `7209b294` — V1.13 Forensic Correction (Gate 1)
- `38b9b62e` — V1.13 Gate 2: Leakage / IC Validation

The prospective experiment does NOT extend V1.13. It is a new experiment
with a new design, new infrastructure, and new auditability guarantees.
The V1.13 postmortem (`v1_13_postmortem/V1.13_RETROSPECTIVE_BENCHMARK_POSTMORTEM.md`)
documents why the retrospective approach is exhausted and why the
prospective approach is the next legitimate test.

---

**End of Prospective Experiment Protocol. Infrastructure is complete.
The experiment is NOT to be run until §7 conditions are met.**
