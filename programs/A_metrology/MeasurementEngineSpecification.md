# Measurement Engine Specification (Stage M1)

Cycle 258. Program A. Stage M1 deliverable per ROADMAP_V2.md.

This file is the canonical specification for every metric in the
measurement engine. It is INCOMPLETE — it is a scaffold that will
be filled in over subsequent cycles. Each metric must document:

- Inputs
- Outputs
- Assumptions
- Known failure modes
- Uncertainty
- Evidence tier
- Calibration status
- Owner
- Acceptance

Until a metric is documented here, it is NOT a measurement. It is
a naked number (Stage M2 violation).

---

## Metric inventory

The following metrics exist in the repository today. Each must be
specified before Gate 1 (Measurement) can pass.

### Discovery metrics

| Metric ID | Metric name | Module | Status |
|---|---|---|---|
| M-001 | Exact F1 (all entities) | dr91_measurement_audit.py | SPECIFIED below |
| M-002 | Token F1 (all entities) | dr91_measurement_audit.py | SPECIFIED below |
| M-003 | Fuzzy F1 (all entities) | dr91_measurement_audit.py | SPECIFIED below |
| M-004 | Synonym F1 (all entities) | dr91_measurement_audit.py | SPECIFIED below |
| M-005 | Discovery F1 (shared, synonyms) | dr91_measurement_audit.py | SPECIFIED below |
| M-006 | Recognition F1 (all, synonyms) | dr91_measurement_audit.py | SPECIFIED below |
| M-007 | Proposal-locus inflation | dr91_measurement_audit.py | SPECIFIED below |
| M-008 | FP floor (synonym match) | dr91_measurement_audit.py | SPECIFIED below |
| M-009 | UNSAFE synonyms count | dr91_measurement_audit.py | SPECIFIED below |
| M-010 | Per-proposal F1 (honest, lenient) | dr99_proposal_evaluation_n30.py | SPECIFIED below |
| M-011 | Per-proposal F1 (strict, honest) | dr99_proposal_evaluation_n30.py | SPECIFIED below |
| M-012 | Aggregate F1 (DR-91 convention) | dr91_measurement_audit.py | SPECIFIED below |
| M-013 | Aggregate F1 (honest convention) | dr98_historical_recalibration.py | SPECIFIED below |
| M-014 | BM25 baseline recall@1 | dr97_external_baselines.py | SPECIFIED below |
| M-015 | Random baseline F1 (mean of N trials) | dr97_external_baselines.py | SPECIFIED below |
| M-016 | Frequency baseline F1 | dr97_external_baselines.py | SPECIFIED below |

### Invention metrics

| Metric ID | Metric name | Module | Status |
|---|---|---|---|
| M-101 | Generation score | product/scoring.py | TODO (Stage M1 not yet started for invention) |
| M-102 | Prediction score | product/scoring.py | TODO |
| M-103 | Measurement score | product/scoring.py | TODO |
| M-104 | Search score | product/scoring.py | TODO |
| M-105 | Learning score | product/scoring.py | TODO |

### Search metrics

| Metric ID | Metric name | Module | Status |
|---|---|---|---|
| M-201 | L5a held-out beats (count) | scripts/l5b_synthesis.py | TODO |
| M-202 | L5b held-out beats (count) | scripts/l5b_synthesis.py | TODO |
| M-203 | L5b+synthesis held-out beats (count) | scripts/l5b_synthesis.py | TODO |
| M-204 | Multi-seed mean held-out beats | scripts/l5b_synthesis_multiseed.py | TODO |
| M-205 | Composite selection rate | scripts/l5b_synthesis.py | TODO |

### Evaluation metrics

| Metric ID | Metric name | Module | Status |
|---|---|---|---|
| M-301 | AI surrogate accept rate | dr100_tier2_human_review.py | SPECIFIED below |
| M-302 | AI surrogate overall mean score | dr100_tier2_human_review.py | SPECIFIED below |
| M-303 | AI surrogate D1-D7 dimension means | dr100_tier2_human_review.py | SPECIFIED below |
| M-304 | Evaluator agreement (inter-rater) | dr95_epistemic_calibration.py | TODO |
| M-305 | Evaluator bias (self-validation) | dr94_calibration_study.py | TODO |
| M-306 | ECE (expected calibration error) | dr96_evaluation_science.py | TODO |

---

## M-001: Exact F1 (all entities)

**Inputs:**
- Gold discoveries (List[Dict], each with `bridge` field)
- All entities extracted from source_snippet_a + source_snippet_b by NLPPipeline

**Outputs:**
- F1 score in [0.0, 1.0]
- TP, FP, FN counts

**Assumptions:**
- Canonicalization: lowercase, underscores, strip non-alphanumeric
- Strict equality: canon(expected) == canon(candidate)
- No synonyms, no fuzzy matching

**Known failure modes:**
- Returns 0.0 for all real-world inputs because bridges are concept-level
  (e.g. "biomineralization") and entities are lexical (e.g. "mineral
  precipitation"). The strict matcher never matches.
- Returns 1.0 for inputs where the gold bridge text appears verbatim in
  the snippet (gold leakage).

**Uncertainty:**
- NOT YET QUANTIFIED. Stage M3 (bootstrap) will add 95% CI.
- Current single-run value is a point estimate with no variance.

**Evidence tier:**
- B (regulatory-equivalent: forensic audit, DR-91)

**Calibration status:**
- UNCALIBRATED. Stage M2 (provenance) will track calibration version.

**Owner:**
- audit/measurement_integrity/dr91_measurement_audit.py

**Acceptance:**
- This metric ALONE is insufficient for any discovery claim (it returns 0).
- It exists as a baseline reference for the strictest possible matching.

---

## M-002: Token F1 (all entities)

**Inputs:** Same as M-001
**Outputs:** F1 in [0.0, 1.0], TP/FP/FN counts
**Assumptions:**
- Canonicalized token overlap: substring match OR ≥1 shared token ≥4 chars
- Stopword-filtered

**Known failure modes:**
- Returns 0.9744 (current value) because any 4+ char token overlap counts
  as a match. This is very lenient.
- High false positive rate (FP floor = 1.0 under this matcher; see M-008).

**Uncertainty:** NOT YET QUANTIFIED. Stage M3.
**Evidence tier:** B
**Calibration status:** UNCALIBRATED
**Owner:** dr91_measurement_audit.py
**Acceptance:**
- Useful as a diagnostic, NOT as a headline score.
- The 0.9744 value is misleading without FP floor context.

---

## M-003: Fuzzy F1 (all entities)

**Inputs:** Same as M-001
**Outputs:** F1 in [0.0, 1.0]
**Assumptions:**
- Character bigram Jaccard similarity ≥ 0.85
- Threshold chosen arbitrarily; not calibrated

**Known failure modes:**
- Returns 0.0000 for current gold (bridges are too short for bigram overlap)
- Threshold is not calibrated to any external standard

**Uncertainty:** NOT YET QUANTIFIED
**Evidence tier:** B
**Calibration status:** UNCALIBRATED
**Owner:** dr91_measurement_audit.py
**Acceptance:**
- Not currently useful. Keep as diagnostic.

---

## M-004: Synonym F1 (all entities)

**Inputs:** Same as M-001 + BRIDGE_SYNONYMS map
**Outputs:** F1 in [0.0, 1.0]
**Assumptions:**
- Token overlap OR canonicalized synonym match
- Synonyms are hand-curated (BRIDGE_SYNONYMS in discovery_capability_benchmark.py)

**Known failure modes:**
- Returns 1.0000 — every gold bridge matches some entity via synonyms
- This IS the FP floor (M-008). The matcher is too lenient to discriminate
  discovery from recognition.
- 1 UNSAFE synonym (inflates gold score; see M-009)

**Uncertainty:** NOT YET QUANTIFIED
**Evidence tier:** B
**Calibration status:** UNCALIBRATED
**Owner:** dr91_measurement_audit.py
**Acceptance:**
- FORBIDDEN as a headline score. Always report alongside M-008 (FP floor).
- The 1.0000 value is an artifact of lenient matching, not a discovery
  measurement.

---

## M-005: Discovery F1 (shared, synonyms)

**Inputs:**
- Gold discoveries
- SHARED entities (entities appearing in BOTH snippet A and B for each gold)

**Outputs:** F1 in [0.0, 1.0]
**Assumptions:**
- Same as M-004 but restricted to shared entities
- Uses DR-91 F1 formula: `f1 = 2*recall/(1+recall)` (assumes precision = recall)

**Known failure modes:**
- Returns 0.8571 (current value) under DR-91 formula
- Under HONEST formula `f1 = 2*p*r/(p+r)`, returns 0.8333 (lower)
- DR-91 formula INFLATES scores by ignoring false positives (P0 finding, F-145)
- The "shared entity" restriction is what differentiates discovery from
  recognition (M-006 uses all entities, M-005 uses shared)

**Uncertainty:** NOT YET QUANTIFIED
**Evidence tier:** B (with P0 caveat about formula)
**Calibration status:** UNCALIBRATED
**Owner:** dr91_measurement_audit.py
**Acceptance:**
- Current canonical "discovery" F1 number, but MUST be reported with
  honest formula (M-013) alongside.
- Cannot be used alone for any capability claim.

---

## M-006: Recognition F1 (all, synonyms)

**Inputs:** Gold discoveries + ALL entities
**Outputs:** F1 in [0.0, 1.0]
**Assumptions:**
- Same as M-004 (all entities, synonyms)
- This IS M-004. The label "Recognition" distinguishes it from "Discovery"
  (M-005) which uses shared entities.

**Known failure modes:**
- Returns 1.0000 — this IS the FP floor
- Often confused with Discovery F1. NEVER combine the two (per DR-91).

**Uncertainty:** NOT YET QUANTIFIED
**Evidence tier:** B
**Calibration status:** UNCALIBRATED
**Owner:** dr91_measurement_audit.py
**Acceptance:**
- FORBIDDEN to report as a discovery score.
- Reports recognition capability only (and even that is uncalibrated).

---

## M-007: Proposal-locus inflation

**Inputs:** M-005 (Discovery F1) and M-006 (Recognition F1)
**Outputs:** Difference in [−1.0, +1.0]
**Assumptions:**
- Inflation = Recognition F1 − Discovery F1
- Positive inflation means recognition (all entities) scores higher than
  discovery (shared entities)

**Known failure modes:**
- Current value: +0.1429 — recognition scores 14.29 percentage points
  higher than discovery
- This is a diagnostic, not a capability score

**Uncertainty:** NOT YET QUANTIFIED
**Evidence tier:** B
**Calibration status:** UNCALIBRATED
**Owner:** dr91_measurement_audit.py
**Acceptance:**
- Report alongside M-005 and M-006.
- Values > 0.10 indicate the matcher is conflating recognition with
  discovery.

---

## M-008: FP floor (synonym match)

**Inputs:**
- Gold discoveries
- 1000 shuffled random candidate sets (same size as gold pool)
- Synonym matcher (M-004)

**Outputs:** F1 in [0.0, 1.0]
**Assumptions:**
- A random candidate set should score near 0 if the matcher discriminates
- FP floor = mean F1 across 1000 shuffles

**Known failure modes:**
- Returns 1.0000 — every random candidate set matches the gold pool
- This is the catastrophic finding from DR-91: the matcher does not
  discriminate at all under lenient matching

**Uncertainty:** NOT YET QUANTIFIED (would require multi-seed shuffle)
**Evidence tier:** A (forensic, adversarial)
**Calibration status:** UNCALIBRATED
**Owner:** dr91_measurement_audit.py
**Acceptance:**
- MUST be < 0.05 for any discovery claim.
- Current value (1.0000) blocks all discovery claims.
- This is the most important metric in the entire measurement engine.

---

## M-009: UNSAFE synonyms count

**Inputs:**
- BRIDGE_SYNONYMS map
- Gold discoveries
- All entities

**Outputs:** Integer count
**Assumptions:**
- A synonym is UNSAFE if removing it decreases the gold score (i.e. the
  synonym is needed for the match) AND the synonym key is a gold bridge

**Known failure modes:**
- Current value: 1 — one synonym inflates the gold score
- This is a benchmark integrity issue, not a capability issue

**Uncertainty:** NOT YET QUANTIFIED
**Evidence tier:** B
**Calibration status:** UNCALIBRATED
**Owner:** dr91_measurement_audit.py
**Acceptance:**
- MUST be 0 for any discovery claim.
- Current value (1) is a benchmark integrity violation.

---

## M-010: Per-proposal F1 (honest, lenient)

**Inputs:**
- 40 proposal evaluations (20 original + 20 perturbed)
- Synonym matcher (M-004)
- HONEST F1 formula: `f1 = 2*p*r/(p+r)`

**Outputs:** Mean F1 across N=40 proposals, in [0.0, 1.0]
**Assumptions:**
- Each proposal gets a binary F1 (0 or 1) based on whether its candidate
  entity matches the gold bridge
- Mean across N=40 is the per-proposal F1

**Known failure modes:**
- Returns 0.1500 — only 15% of proposals match their gold bridge
- Below the useful-performance threshold of 0.30 (cycle 257)

**Uncertainty:** NOT YET QUANTIFIED. Stage M3 will add 95% CI.
**Evidence tier:** B
**Calibration status:** UNCALIBRATED
**Owner:** dr99_proposal_evaluation_n30.py
**Acceptance:**
- MUST be ≥ 0.30 for Gate 1 Stage M3 to pass.
- Current value (0.1500) blocks Gate 1.
- This is the canonical per-proposal performance number (NOT M-005).

---

## M-011: Per-proposal F1 (strict, honest)

**Inputs:** Same as M-010 but with strict matcher (M-001)
**Outputs:** Mean F1 in [0.0, 1.0]
**Assumptions:** Same as M-010, strict matching

**Known failure modes:**
- Returns 0.0000 — strict matching never finds the bridge
- Same root cause as M-001

**Uncertainty:** NOT YET QUANTIFIED
**Evidence tier:** B
**Calibration status:** UNCALIBRATED
**Owner:** dr99_proposal_evaluation_n30.py
**Acceptance:**
- Diagnostic only. Not useful as a headline.

---

## M-012: Aggregate F1 (DR-91 convention)

**Inputs:** Same as M-005
**Outputs:** F1 in [0.0, 1.0]
**Assumptions:**
- DR-91 formula: `f1 = 2*recall/(1+recall)`
- Assumes precision = recall (no false positives)
- INFLATES scores when FP > 0

**Known failure modes:**
- Returns 0.8571 for current gold
- P0 finding (F-145): this formula is non-standard and inflates scores
- Honest F1 (M-013) is significantly lower

**Uncertainty:** NOT YET QUANTIFIED
**Evidence tier:** B (with P0 caveat)
**Calibration status:** UNCALIBRATED
**Owner:** dr91_measurement_audit.py
**Acceptance:**
- FORBIDDEN to report without also reporting M-013 (honest F1).
- P0 rule (F-145): no future F1 claim may use this formula alone.

---

## M-013: Aggregate F1 (honest convention)

**Inputs:** Same as M-005
**Outputs:** F1 in [0.0, 1.0]
**Assumptions:**
- Honest formula: `f1 = 2*p*r/(p+r)`
- Properly counts false positives

**Known failure modes:**
- Returns 0.8333 for current gold (lower than M-012's 0.8571)
- The difference (0.0238) is the formula inflation

**Uncertainty:** NOT YET QUANTIFIED
**Evidence tier:** B
**Calibration status:** UNCALIBRATED
**Owner:** dr98_historical_recalibration.py
**Acceptance:**
- CANONICAL F1 number. Always report this.
- M-012 may be reported alongside for backward compatibility with
  historical claims, but M-013 is canonical.

---

## M-014: BM25 baseline recall@1

**Inputs:**
- Gold discoveries
- BM25 index built per gold (snippet A + snippet B as 2-doc corpus)
- Gold bridge text as query (ORACLE-ASSISTED — see known failure modes)

**Outputs:** Recall@1 in [0.0, 1.0]
**Assumptions:**
- Okapi-BM25 with k1=1.5, b=0.75
- Top-1 retrieved snippet scored against gold bridge
- Under lenient mode: token overlap or synonym match

**Known failure modes:**
- ORACLE-ASSISTED: the BM25 query IS the gold bridge text. A true
  external baseline would propose bridges WITHOUT seeing gold labels.
- Returns 0.6500 (lenient) — production beats this by Δ=+0.21
- Returns 0.0000 (strict) — same as production (both 0)

**Uncertainty:** NOT YET QUANTIFIED
**Evidence tier:** B (with oracle-assisted caveat)
**Calibration status:** UNCALIBRATED
**Owner:** dr97_external_baselines.py
**Acceptance:**
- verdict_tier = INSTRUMENTATION_SCAFFOLD_PASS (NOT SCIENCE_PASS)
- Cannot be used to validate discovery claim until oracle assistance
  is removed.

---

## M-015: Random baseline F1 (mean of N trials)

**Inputs:**
- Gold discoveries
- N=100 random candidate sets
- Strict matcher (M-001) or lenient matcher (M-004)

**Outputs:** Mean F1 in [0.0, 1.0], std, range
**Assumptions:**
- Random 2-grams from combined snippet corpus
- Each trial picks one random candidate per gold

**Known failure modes:**
- Returns 0.0000 (strict) — random 2-grams essentially never match
- Returns 0.0950 (lenient) — small but non-zero false positive rate

**Uncertainty:** Quantified via 100 trials (std reported)
**Evidence tier:** B
**Calibration status:** UNCALIBRATED (but multi-trial)
**Owner:** dr97_external_baselines.py
**Acceptance:**
- Useful as FP floor reference under lenient matching.
- Production (0.8571) beats this by Δ=+0.76 — but the comparison is
  oracle-assisted (see M-014).

---

## M-016: Frequency baseline F1

**Inputs:**
- Gold discoveries
- Most frequent bigram/unigram from combined snippets as candidate

**Outputs:** F1 in [0.0, 1.0]
**Assumptions:**
- Frequency = top bigram count ≥2, else top unigram
- LLM-baseline proxy (simulates naive zero-shot LLM extraction)

**Known failure modes:**
- Returns 0.0000 (strict) — frequency-based candidates rarely match exactly
- Returns 0.3000 (lenient) — 30% match rate via token overlap

**Uncertainty:** NOT YET QUANTIFIED
**Evidence tier:** B
**Calibration status:** UNCALIBRATED
**Owner:** dr97_external_baselines.py
**Acceptance:**
- Useful as LLM-baseline proxy.
- Production beats this by Δ=+0.56 (lenient) — but again, oracle-assisted.

---

## M-301: AI surrogate accept rate

**Inputs:**
- 6 proposals (REVIEW-001 through REVIEW-006)
- 1 AI surrogate reviewer (AI_SURROGATE_001, type AI_PRE_REVIEW)
- 7-dimension rubric (D1-D7) + overall verdict

**Outputs:** Accept rate in [0.0, 1.0]
**Assumptions:**
- ACCEPT verdict = proposal accepted as scientific discovery
- 1 reviewer (no inter-rater agreement)
- AI surrogate review is Tier-1.5 pre-screen, NOT Tier-2 human

**Known failure modes:**
- Returns 0.0000 — 0/6 proposals accepted
- Single reviewer (no inter-rater agreement)
- AI surrogate, not human (per reviewer's own caveat)

**Uncertainty:** NOT YET QUANTIFIED (single reviewer)
**Evidence tier:** I (LLM inference)
**Calibration status:** UNCALIBRATED
**Owner:** dr100_tier2_human_review.py
**Acceptance:**
- MUST be ≥ 0.50 for Gate 2 Stage D5 (human review) to pass.
- Current value (0.0000) blocks Gate 2.
- Tier-1.5 pre-screen; not valid as Tier-2 human review.

---

## M-302: AI surrogate overall mean score

**Inputs:** Same as M-301
**Outputs:** Mean score in [1.0, 5.0]
**Assumptions:**
- Mean of D1-D7 dimension scores
- Higher is better

**Known failure modes:**
- Returns 2.2381 — well below 3.0 (neutral) and 3.5 (PARTIAL threshold)
- Same single-reviewer / AI-surrogate caveats as M-301

**Uncertainty:** NOT YET QUANTIFIED
**Evidence tier:** I
**Calibration status:** UNCALIBRATED
**Owner:** dr100_tier2_human_review.py
**Acceptance:**
- MUST be ≥ 3.5 for Gate 2 Stage D5 PARTIAL.
- Current value (2.2381) blocks Gate 2.

---

## M-303: AI surrogate D1-D7 dimension means

**Inputs:** Same as M-301
**Outputs:** 7 means (D1 through D7), each in [1.0, 5.0]
**Assumptions:**
- D1 = Scientific plausibility
- D2 = Novelty
- D3 = Prediction testability
- D4 = Falsification rigor
- D5 = Alternative explanations
- D6 = Counterexample soundness
- D7 = Overall scientific value

**Known failure modes:**
- D1 (Plausibility): 4.00 — concepts are real
- D2 (Novelty): 1.17 — proposals are not novel (shared vocabulary)
- D3 (Testability): 2.00 — predictions are weak
- D4 (Falsification): 1.83 — falsifiers are not rigorous
- D5 (Alternatives): 3.00 — alternatives are strawman
- D6 (Counterexample): 1.83 — counterexamples are benchmark artifacts
- D7 (Overall value): 1.83 — proposals are not valuable

**Uncertainty:** NOT YET QUANTIFIED
**Evidence tier:** I
**Calibration status:** UNCALIBRATED
**Owner:** dr100_tier2_human_review.py
**Acceptance:**
- Diagnostic. Shows where the ProposalComposer needs repair.
- D2 (Novelty) is the worst dimension (1.17) — the composer produces
  shared-vocabulary bridges, not novel connections.

---

## TODO metrics (Stage M1 not yet started)

The following metrics exist in the codebase but have not yet been
specified. They must be specified before Gate 1 (Measurement) can pass.

- M-101 through M-105 (invention metrics)
- M-201 through M-205 (search metrics)
- M-304 through M-306 (evaluation metrics)

Each will be specified in subsequent cycles, following the same template
as M-001 through M-016 above.

---

## Stage M1 acceptance criteria

Stage M1 is complete when:

1. Every metric in the inventory above has a complete specification
   (all 9 fields filled in).
2. No metric exists in the codebase that is not in the inventory.
3. The specification is reviewed and accepted by the measurement owner.

**Current status: 16 of ~30 metrics specified (53%).**
**Remaining: 14 metrics (invention, search, evaluation) + review.**
