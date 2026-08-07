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
| M-101 | Gen 1 Document Parsing F1 | scripts/nine_tenths_loop_v2.py | SPECIFIED below |
| M-102 | Gen 2 Entity Extraction F1 | scripts/nine_tenths_loop_v2.py | SPECIFIED below |
| M-103 | Gen 3 Relation Extraction F1 | scripts/nine_tenths_loop_v2.py | SPECIFIED below |
| M-104 | Gen 4 Mechanism Extraction F1 | scripts/nine_tenths_loop_v2.py | SPECIFIED below |
| M-105 | Gen 5 Discovery Layer F1 + Novelty | scripts/nine_tenths_loop_v2.py | SPECIFIED below |

### Search metrics

| Metric ID | Metric name | Module | Status |
|---|---|---|---|
| M-201 | L5a held-out beats (count) | scripts/l5b_synthesis_heldout.py | SPECIFIED below |
| M-202 | L5b held-out beats (count) | scripts/l5b_synthesis_heldout.py | SPECIFIED below |
| M-203 | L5b+synthesis held-out beats (count) | scripts/l5b_synthesis_heldout.py | SPECIFIED below |
| M-204 | Multi-seed mean held-out beats | scripts/l5b_synthesis_multiseed.py | SPECIFIED below |
| M-205 | Composite selection rate | scripts/l5b_synthesis_multiseed.py | SPECIFIED below |

### Evaluation metrics

| Metric ID | Metric name | Module | Status |
|---|---|---|---|
| M-301 | AI surrogate accept rate | dr100_tier2_human_review.py | SPECIFIED below |
| M-302 | AI surrogate overall mean score | dr100_tier2_human_review.py | SPECIFIED below |
| M-303 | AI surrogate D1-D7 dimension means | dr100_tier2_human_review.py | SPECIFIED below |
| M-304 | Evaluator agreement (inter-rater) | dr95_epistemic_calibration.py | SPECIFIED below |
| M-305 | Evaluator bias (self-validation) | dr94_calibration_study.py | SPECIFIED below |
| M-306 | ECE (expected calibration error) | dr95_epistemic_calibration.py | SPECIFIED below |

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

## M-101: Gen 1 Document Parsing F1 (invention metric)

**Inputs:**
- benchmarks/outputs/benchmark_*_output.json (parsed document structure)
- benchmarks/consumer/expected/*.json (gold expected structure)
- Section segmentation ground truth

**Outputs:**
- F1 score in [0.0, 1.0] for section segmentation
- Score in [0, 10] via formula `round(10 × F1)`

**Assumptions:**
- F1 computed by `benchmarks/discovery_benchmark.py` and persisted to
  `benchmarks/reports/gen1_pr_score.json`
- Score formula: `round(10 × F1)` (per F-081 single-rubric rule)
- 9/10 requires F1 ≥ 0.85; 10/10 requires F1 ≥ 0.95

**Known failure modes:**
- Document parsing is the foundation layer; if F1 is low, all
  downstream Gen 2-6 metrics inherit the noise
- The benchmark uses synthetic PDFs; performance on real PDFs may differ
- No uncertainty quantification until Stage M3 bootstrap is extended
  to invention metrics (pending)

**Uncertainty:**
- Bootstrap quantified (cycle 261): 1.0000 ± 0.0000 (95% CI: 1.0000,
  1.0000; N=5, B=500). DEGENERATE — all 5 files have perfect F1.
- The degenerate CI means the metric cannot discriminate on this sample.
- A larger benchmark with harder documents would produce non-degenerate
  variance.

**Evidence tier:**
- D (academic literature: standard F1 on document parsing benchmarks)

**Calibration status:**
- UNCALIBRATED. Stage M2 (provenance) will track calibration version.

**Owner:**
- scripts/nine_tenths_loop_v2.py::assess_all (reads from
  benchmarks/reports/gen1_pr_score.json)

**Acceptance:**
- Reported as `gen1_document_parsing: score/10 (F1=X.XXXX)` in scorecard
- Must include ± std and 95% CI once Stage M3 bootstrap is extended
- Cannot be used alone for capability claims (invention metrics are
  downstream of discovery metrics which are NOT TRUSTWORTHY)

---

## M-102: Gen 2 Entity Extraction F1 (invention metric)

**Inputs:**
- benchmarks/outputs/benchmark_*_output.json (extracted entities)
- benchmarks/consumer/expected/*.json (gold entities)
- Entity-level ground truth (PER, ORG, MATERIAL, MECHANISM, etc.)

**Outputs:**
- F1 score in [0.0, 1.0] for entity extraction
- Score in [0, 10] via formula `round(10 × F1)`

**Assumptions:**
- F1 computed by `benchmarks/extractor_benchmarks.py` and persisted to
  `benchmarks/reports/gen2_pr_score.json`
- Same `round(10 × F1)` formula as M-101
- spaCy en_core_web_sm model is the extractor (Gen 2 NLP pipeline)

**Known failure modes:**
- This is a RECOGNITION metric, not a DISCOVERY metric (see F-075)
- High entity F1 does NOT imply discovery capability — a system that
  extracts entities perfectly but discovers nothing scores 9/10 here
- The DR-91 audit (cycle 243) showed entity-level F1 was measuring
  recognition, not bridge proposal; this metric inherits that caveat

**Uncertainty:**
- Bootstrap quantified (cycle 261): 0.9431 ± 0.0208 (95% CI: 0.8983,
  0.9764; N=65, B=500). Synthetic reconstruction from aggregate TP/FP/FN.
- The CI is narrow because N=65 (large sample). The synthetic
  reconstruction assumes the per-item FP/FN split matches the aggregate
  ratio — this is an approximation, documented in Known failure modes.

**Evidence tier:**
- D (academic: standard NER F1)

**Calibration status:**
- UNCALIBRATED

**Owner:**
- scripts/nine_tenths_loop_v2.py::assess_all (reads gen2_pr_score.json)

**Acceptance:**
- Reported as `gen2_entity_extraction: score/10 (F1=X.XXXX)`
- MUST be reported alongside M-005 (Discovery F1) to distinguish
  recognition from discovery
- Cannot be used alone for capability claims

---

## M-103: Gen 3 Relation Extraction F1 (invention metric)

**Inputs:**
- benchmarks/outputs/benchmark_*_output.json (extracted relations)
- benchmarks/consumer/expected/*.json (gold relations)
- Relation-level ground truth (subject-predicate-object triples)

**Outputs:**
- F1 score in [0.0, 1.0] for relation extraction
- Score in [0, 10] via formula `round(10 × F1)`

**Assumptions:**
- F1 computed by `benchmarks/relation_extraction_benchmark.py` and
  persisted to `benchmarks/reports/gen3_pr_score.json`
- Same `round(10 × F1)` formula
- Test threshold: F1 ≥ 0.85 for 9/10 (enforced by
  tests/test_scorecard_integrity.py::test_gen3_f1_above_085)

**Known failure modes:**
- Historical: F1=0.6441 (cycle 145), then 0.7692, then 0.9091 (cycle
  188 after de-circularization). Each step documented in FAILURES.md.
- The cycle-188 jump from 0.7143 to 0.9091 was due to removing circular
  gold (F-099 class), not improving the extractor. Score improvements
  without capability improvements violate the Prime Directive.
- Still measures retrieval, not discovery (F-075)

**Uncertainty:**
- Bootstrap quantified (cycle 261): 0.8800 ± 0.0304 (95% CI: 0.8145,
  0.9322; N=85, B=500). Per-sentence F1 resampled.
- The CI is narrow because N=85 (large sample). This is the most
  reliable invention metric bootstrap (real per-item data, not
  synthetic reconstruction).

**Evidence tier:**
- D (academic: standard relation extraction F1)

**Calibration status:**
- UNCALIBRATED

**Owner:**
- scripts/nine_tenths_loop_v2.py::assess_all (reads gen3_pr_score.json)

**Acceptance:**
- Reported as `gen3_relation_extraction: score/10 (F1=X.XXXX)`
- MUST include circular-gold audit (F-099) status alongside
- Cannot be used alone for capability claims

---

## M-104: Gen 4 Mechanism Extraction F1 (invention metric)

**Inputs:**
- benchmarks/outputs/benchmark_*_output.json (extracted mechanism chains)
- benchmarks/consumer/expected/*.json (gold mechanism chains)
- Mechanism-chain ground truth (multi-hop causal chains)

**Outputs:**
- F1 score in [0.0, 1.0] for mechanism extraction
- Score in [0, 10] via formula `round(10 × F1)`

**Assumptions:**
- F1 computed by `benchmarks/mechanism_chain_benchmark.py` and
  persisted to `benchmarks/reports/gen4_pr_score.json`
- Same `round(10 × F1)` formula
- Test threshold: F1 ≥ 0.90 for 9/10 (enforced by
  tests/test_scorecard_integrity.py::test_gen4_f1_above_090, F-092)

**Known failure modes:**
- Historical: F1=0.7143 (cycle 188 pre-de-circularization) → 0.9091
  (post-de-circularization). The jump was a gold-fix, not a capability
  fix (F-099).
- Mechanism chains are deeper than relations but still measure
  retrieval unless the chains are novel
- The 0.90 threshold (F-092) was set post-fix; pre-fix it would have
  failed

**Uncertainty:**
- Bootstrap quantified (cycle 261): 0.9091 ± 0.0677 (95% CI: 0.7368,
  1.0000; N=12, B=500). Synthetic reconstruction from aggregate TP/FP/FN.
- The CI is wide (0.7368 to 1.0000) because N=12 is small and the F1
  is high (near ceiling). The CI touching 1.0 means the metric could
  plausibly be perfect on a different sample.

**Evidence tier:**
- D (academic: mechanism chain extraction)

**Calibration status:**
- UNCALIBRATED

**Owner:**
- scripts/nine_tenths_loop_v2.py::assess_all (reads gen4_pr_score.json)

**Acceptance:**
- Reported as `gen4_mechanism_extraction: score/10 (F1=X.XXXX)`
- Test test_gen4_f1_above_090 enforces F1 ≥ 0.90
- Cannot be used alone for capability claims

---

## M-105: Gen 5 Discovery Layer F1 + Novelty Rate (invention metric)

**Inputs:**
- benchmarks/outputs/benchmark_*_output.json (discovered bridges)
- benchmarks/consumer/expected/*.json (gold bridges)
- Bridge-level ground truth (cross-domain Swanson bridges)
- Novelty rate: fraction of discovered bridges NOT in training set

**Outputs:**
- F1 score in [0.0, 1.0] for discovery
- Novelty rate in [0.0, 1.0]
- Score in [0, 10] via formula `round(10 × F1)`

**Assumptions:**
- F1 computed by `benchmarks/discovery_benchmark.py` and persisted to
  `benchmarks/reports/gen5_pr_score.json`
- Same `round(10 × F1)` formula
- Novelty rate is reported alongside but does NOT affect the score
  (per F-081 single-rubric rule)

**Known failure modes:**
- THIS IS THE METRIC DR-91 INVALIDATED. The F1=0.9189 reported since
  cycle 201 was measuring entity recognition, not bridge proposal
  (F-143, F-145). The honest F1 is 0.8571 (DR-91 convention) or
  0.8333 (honest convention) — see M-005 and M-013.
- The novelty rate is a separate measurement and is NOT a substitute
  for discovery F1
- FP floor = 1.0 (M-008) means any candidate matches; this metric
  inherits that catastrophic finding

**Uncertainty:**
- Bootstrap quantified (cycle 261): 0.9375 ± 0.0464 (95% CI: 0.8276,
  1.0000; N=17, B=500). Per-hit resampled (15 TPs + 2 FNs).
- The CI touches 1.0 because the F1 is high and N=17 is moderate.
- NOTE: this bootstrap uses the gen5_pr_score.json data (connection-
  finding F1=0.9375), which is DIFFERENT from M-005/M-013 (discovery
  F1=0.8571). The gen5 metric measures connection-finding (retrieval +
  novel), while M-005 measures bridge proposal specifically. They are
  not interchangeable. The DR-91 invalidation applies to M-005, not
  directly to M-105 — but M-105 inherits the caveat because it uses the
  same discovery benchmark infrastructure.

**Evidence tier:**
- B (forensic audit, DR-91) — but with P0 caveat that the metric
  itself is contested (F-145 formula inflation rule)

**Calibration status:**
- UNCALIBRATED. The DR-91 audit (cycle 243) is the de-facto calibration;
  it found the metric overclaims.

**Owner:**
- scripts/nine_tenths_loop_v2.py::assess_all (reads gen5_pr_score.json)

**Acceptance:**
- Reported as `gen5_discovery_layer: score/10 (F1=X.XXXX, novelty=Y.YYYY)`
- MUST be reported alongside M-008 (FP floor) and M-005/M-013
  (bootstrap-CI discovery F1)
- FORBIDDEN to report as a naked F1; must include the DR-91 caveat
- This is the most contested metric in the entire specification

---

## M-201: L5a Held-out Beats (search metric)

**Inputs:**
- 10 held-out blind problems (BLIND-011 through BLIND-020)
- L5a DSL (13 operators) — the baseline operator vocabulary
- For each problem: best outcome with L5a DSL vs random baseline

**Outputs:**
- Count in [0, 10] of problems where L5a beats random baseline
- Per-problem boolean: beats_random (True/False)

**Assumptions:**
- "Beats" = best_outcome > rand_best + 1e-9 (strictly greater)
- Random baseline = best of N random programs on the same problem
- Held-out = problems NOT used to synthesize/train the DSL
- Established baseline: 2/10 (cycle 229, documented in
  scripts/l5b_synthesis_heldout.py)

**Known failure modes:**
- The 2/10 baseline is itself a point estimate; bootstrap CI not yet
  computed for search metrics
- "Beats random" is a weak bar — random is the floor, not a meaningful
  competitor
- The 10 held-out problems may not be representative of the full
  problem space
- Ties (best_outcome == rand_best) count as NOT beats, which is
  conservative but may undercount

**Uncertainty:**
- Bootstrap quantified (cycle 261): 0.9000 ± 0.0891 (95% CI: 0.7000,
  1.0000; N=10, B=100). Per-problem beats resampled.
- The CI is wide (0.7000 to 1.0000) because N=10 is small and the
  point estimate is high (9/10).
- NOTE: the documented baseline was 2/10 (cycle 229), but the current
  code produces 9/10. This discrepancy is a Stage M4 (repeatability)
  finding — the code has drifted since cycle 229. The bootstrap reports
  what the code produces NOW, not the historical number.

**Evidence tier:**
- B (forensic: held-out evaluation, no training leakage)

**Calibration status:**
- UNCALIBRATED

**Owner:**
- scripts/l5b_synthesis_heldout.py::evaluate_on_held_out_with_composites
  (with empty composite list = L5a baseline)

**Acceptance:**
- Reported as `L5a held-out: N/10 beats baseline`
- MUST include the 2/10 baseline for comparison
- Cannot be used alone for capability claims (L5a is the weakest DSL)

---

## M-202: L5b Held-out Beats (search metric)

**Inputs:**
- Same 10 held-out blind problems (BLIND-011 through BLIND-020)
- L5b DSL (18 operators = L5a 13 + 5 new primitives)
- For each problem: best outcome with L5b DSL vs random baseline

**Outputs:**
- Count in [0, 10] of problems where L5b beats random baseline
- Per-problem boolean: beats_random (True/False)

**Assumptions:**
- Same "beats" definition as M-201
- L5b = L5a + 5 new operators added in cycle 230-231
- Established baseline: 5/10 (cycle 231, documented in
  scripts/l5b_synthesis_heldout.py)

**Known failure modes:**
- Same as M-201 (point estimate, weak bar, representativeness)
- The jump from 2/10 (L5a) to 5/10 (L5b) is real but small; the
  marginal value of the 5 new operators is +3/10
- L5b is still below the 9/10 threshold that would indicate strong
  search capability

**Uncertainty:**
- Bootstrap quantified (cycle 261): 0.9000 ± 0.0891 (95% CI: 0.7000,
  1.0000; N=10, B=100). Same data as M-201 — see M-201 for details.
- The documented 5/10 baseline (cycle 231) is NOT reproduced by current
  code (which gives 9/10). This is because the evaluator uses
  EXTENDED_OPS (18 ops) internally, making M-201 and M-202 identical.
  A true L5a baseline would use BASE_OPS only (13 ops). This is a
  Stage M4 repeatability finding.

**Evidence tier:**
- B (forensic: held-out evaluation)

**Calibration status:**
- UNCALIBRATED

**Owner:**
- scripts/l5b_synthesis_heldout.py::evaluate_on_held_out_with_composites

**Acceptance:**
- Reported as `L5b held-out: N/10 beats baseline`
- MUST include the 5/10 baseline and the 2/10 L5a baseline for comparison
- The +3/10 marginal improvement is the honest claim; not the absolute 5/10

---

## M-203: L5b+Synthesis Held-out Beats (search metric)

**Inputs:**
- Same 10 held-out blind problems
- L5b+Synthesis DSL (35 operators = L5b 18 + 17 synthesized composites)
- Synthesized composites from training set (BLIND-001..010)
- For each problem: best outcome with composite DSL vs random baseline

**Outputs:**
- Count in [0, 10] of problems where L5b+Synthesis beats random baseline
- Per-problem boolean: beats_random (True/False)

**Assumptions:**
- Composites are PAIRS of existing operators (not invented from scratch)
- Composites synthesized on training (BLIND-001..010), evaluated on
  held-out (BLIND-011..020) — no leakage
- Established result: 9/10 (cycle 234, single seed)

**Known failure modes:**
- The 9/10 is a single-seed result; multi-seed mean is 8.6/10 (M-204)
- The composites generalize (5/10 → 9/10), but the +4/10 jump is
  within seed variance (std 0.80 across 5 seeds)
- 1/10 problems still fail (BLIND-015, BLIND-018) — the composites
  don't help every problem type
- The 9/10 figure is HONEST but should not be reported without the
  multi-seed context (M-204)

**Uncertainty:**
- Bootstrap quantified (cycle 261): 0.9000 ± 0.0891 (95% CI: 0.7000,
  1.0000; N=10, B=100). Per-problem beats resampled.
- The documented 9/10 (cycle 234) is NOT reproduced by current code
  (which gives 9/10 on this run, but with composites from
  min_pair_frequency=1 instead of the historical default). The
  bootstrap CI is the same as M-201/M-202 because the per-problem
  beats happen to be identical on this seed.
- Multi-seed: quantified via M-204 (mean 8.6, std 0.80)

**Evidence tier:**
- B (forensic: held-out + multi-seed)

**Calibration status:**
- UNCALIBRATED

**Owner:**
- scripts/l5b_synthesis_heldout.py::evaluate_on_held_out_with_composites

**Acceptance:**
- Reported as `L5b+Synthesis held-out: N/10 beats baseline (single seed)`
- MUST include M-204 (multi-seed mean) alongside
- The honest claim is "8.6/10 mean across 5 seeds", not "9/10"

---

## M-204: Multi-seed Mean Held-out Beats (search metric)

**Inputs:**
- 5 seeds: 42, 7, 99, 123, 256
- For each seed: synthesize composites on training, evaluate on held-out
- Same 10 held-out blind problems per seed

**Outputs:**
- Mean beats count in [0, 10] across 5 seeds
- Standard deviation across 5 seeds
- Per-seed beats count
- Per-seed composite count and selection rate

**Assumptions:**
- Seeds are arbitrary (chosen for reproducibility, not cherry-picked)
- Per-seed: synthesize → evaluate → record. No cross-seed contamination.
- Established result: mean 8.6/10, std 0.80, range [8, 10] (cycle 235)

**Known failure modes:**
- 5 seeds is a small sample; the std 0.80 has its own uncertainty
- Seed 99 achieved 10/10 — this is the best case, not the typical case
- The mean 8.6 is below the 9/10 single-seed figure (M-203); the
  difference is seed variance, not a contradiction
- All seeds produce composites (3-5 per seed), 100% selection rate —
  but the composites themselves differ across seeds

**Uncertainty:**
- Bootstrap quantified (cycle 261): 8.6000 ± 0.3529 (95% CI: 8.0000,
  9.4000; N=5, B=500). Per-seed beats resampled.
- The CI is narrow (8.0 to 9.4) but N=5 is very small. The bootstrap
  is on seed-level beats, not per-problem beats — this measures
  seed-to-seed variance, not problem-to-problem variance.
- The std 0.3529 is the bootstrap std; the original multi-seed std
  was 0.80 (on the 5 raw values). The bootstrap std is smaller because
  it benefits from resampling.

**Evidence tier:**
- B (forensic: multi-seed held-out)

**Calibration status:**
- UNCALIBRATED (but multi-seed is a form of repeatability check, M4)

**Owner:**
- scripts/l5b_synthesis_multiseed.py::run_multiseed_synthesis_heldout

**Acceptance:**
- Reported as `Multi-seed mean: 8.6/10 (std 0.80, range [8, 10], N=5 seeds)`
- This is the CANONICAL search capability claim (not M-203 single-seed)
- The honest claim: "Engine synthesizes composites that generalize to
  held-out, robustly across 5 seeds (mean 8.6/10, std 0.80)."

---

## M-205: Composite Selection Rate (search metric)

**Inputs:**
- Per-seed: synthesized composites (3-5 per seed)
- Per-seed: held-out evaluation with composite DSL
- For each composite: selection_count (how many programs selected it)

**Outputs:**
- Selection rate in [0.0, 1.0] = (composites with selection_count > 0)
  / (total composites)
- Total selection count across all composites
- Per-composite selection count

**Assumptions:**
- "Selected" = a program in the search referenced the composite
- Selection is by the search itself (not forced)
- Established result: 100% selection rate across all 5 seeds (cycle 235)

**Known failure modes:**
- 100% selection rate is suspiciously high — it may indicate the
  composites are trivially useful OR the search is biased toward
  selecting composites (because they're new)
- The selection rate does NOT measure whether the composites IMPROVE
  outcomes, only whether they're USED
- A composite that is selected but produces worse outcomes would still
  count as "selected"

**Uncertainty:**
- Bootstrap quantified (cycle 261): 1.0000 ± 0.0000 (95% CI: 1.0000,
  1.0000; N=43, B=500). DEGENERATE — all 43 composites have
  selection_count > 0.
- The degenerate CI confirms the suspiciously-high finding documented
  in Known failure modes: 100% selection rate is not a capability
  claim, it's a usage claim. The metric cannot discriminate.

**Evidence tier:**
- B (forensic: held-out selection tracking)

**Calibration status:**
- UNCALIBRATED

**Owner:**
- scripts/l5b_synthesis_multiseed.py::run_multiseed_synthesis_heldout

**Acceptance:**
- Reported as `Composite selection rate: 100% (N composites, M total selections)`
- MUST be reported alongside M-204 (does selection translate to beats?)
- The 100% figure alone is NOT a capability claim — it's a usage claim

---

## M-304: Evaluator Inter-rater Agreement (evaluation metric)

**Inputs:**
- Multi-evaluator results from dr95_epistemic_calibration.py
- Per-proposal: 3 judges (judge_1_standard, judge_2_adversarial,
  judge_3_neutral), each producing a recommendation (ACCEPT/REVISE/REJECT)
- Per-criterion: D1-D7 scores from each judge

**Outputs:**
- Agreement rate in [0.0, 1.0] = fraction of proposals where all 3
  judges agree on recommendation
- Per-criterion agreement (D1-D7)
- Disagreement graph (structured edges: judge_a, judge_b, criterion,
  value_a, value_b, reason_a, reason_b)

**Assumptions:**
- "Agree" = all 3 judges produce the same recommendation
- Partial agreement (2/3) is NOT agreement
- Established result: 1/6 agreement rate (17%) on 6 proposals (DR-96,
  cycle 252) — judges disagree 83% of the time

**Known failure modes:**
- 17% agreement is catastrophic — evaluators are unreliable instruments
- The 3 judges use different prompts (standard, adversarial, neutral),
  which is a feature (diversity) but also a bug (no ground truth)
- Agreement is on RECOMMENDATION only; per-criterion agreement may
  differ (some criteria are more subjective than others)
- This is the DR-96 finding: "evaluators are unreliable instruments"
  (F-143, F-145)

**Uncertainty:**
- Bootstrap quantified (cycle 261): 0.1667 ± 0.1485 (95% CI: 0.0000,
  0.5000; N=6, B=500). Per-proposal agreement resampled.
- The CI is very wide (0.0000 to 0.5000) because N=6 is small and the
  point estimate is low (1/6 agreed). The CI includes 0, meaning the
  true agreement rate could plausibly be 0%.
- This wide CI is itself a finding: with N=6, we cannot distinguish
  'evaluators rarely agree' from 'evaluators never agree'.

**Evidence tier:**
- I (LLM inference — judges are LLM-based)

**Calibration status:**
- UNCALIBRATED. The DR-96 audit IS the calibration attempt; it found
  the evaluators are not calibratable with current prompt design.

**Owner:**
- audit/measurement_integrity/dr95_epistemic_calibration.py
  ::multi_evaluator_calibration
- audit/measurement_integrity/dr96_evaluation_science.py
  ::build_disagreement_graph

**Acceptance:**
- Reported as `Inter-rater agreement: X/Y (Z%)` with per-criterion breakdown
- MUST be reported alongside M-305 (self-validation bias) and M-306 (ECE)
- Agreement < 50% blocks any evaluator-based claim (per DR-96)

---

## M-305: Evaluator Self-validation Bias (evaluation metric)

**Inputs:**
- Internal evaluator scores (Tier 0 self-evaluation, from
  dr94_calibration_study.py)
- External evaluator scores (Tier 1 LLM, from dr94)
- Paired proposals (same proposal scored by both)

**Outputs:**
- Bias = mean(internal_score - external_score), positive = overestimates
- Mean Calibration Error (MCE) = mean(|internal - external|)
- Overestimate rate = fraction where internal > external + 1.0
- Agreement rate = fraction where |internal - external| ≤ 1.0
- Correlation between internal and external scores

**Assumptions:**
- Internal evaluator is the ProposalComposer's own confidence
- External evaluator is an independent LLM (different prompt, different
  model instance)
- Scores on the same 1-5 scale
- Established result: bias = +2.50 (DR-94, cycle 250) — internal
  overestimates by 2.50 points on a 5-point scale

**Known failure modes:**
- +2.50 bias on a 5-point scale means internal scores are
  systematically ~50% too high
- Overestimate rate: 100% (every proposal overestimated)
- This is the DR-94 finding: internal evaluation is not trustworthy
  (F-143, F-145)
- The bias may be due to (a) the internal evaluator being too generous,
  (b) the external evaluator being too harsh, or (c) both — without a
  ground truth, we cannot distinguish

**Uncertainty:**
- Bootstrap quantified (cycle 261): 2.5000 ± 0.0556 (95% CI: 2.3750,
  2.6250; N=6, B=500). Per-proposal residual resampled.
- The CI is narrow (2.3750 to 2.6250) because all 6 residuals are
  tightly clustered around 2.5 (range 2.25 to 2.75). The bias is
  consistent across proposals — this is NOT noise, it's systematic.
- The narrow CI means the bias is precisely estimated: +2.50 ± 0.06.
  This is a high-confidence finding: the internal evaluator overestimates
  by exactly 2.50 points.

**Evidence tier:**
- I (LLM inference on both sides)

**Calibration status:**
- UNCALIBRATED. The DR-94 study IS the calibration attempt; it found
  the internal evaluator is biased beyond calibration (100%
  overestimate rate).

**Owner:**
- audit/measurement_integrity/dr94_calibration_study.py
  ::compute_calibration

**Acceptance:**
- Reported as `Self-validation bias: +X.XX (MCE=Y.YY, overestimate=Z%)`
- MUST be reported alongside M-304 (agreement) and M-306 (ECE)
- Bias > +1.0 blocks any internal-evaluator-based claim (per DR-94)
- This metric is the reason Gate D (AI surrogate review) FAILED in
  cycle 257 — the AI surrogate reviewer rejected all 6 proposals,
  confirming the internal evaluator's bias

---

## M-306: Expected Calibration Error (ECE) (evaluation metric)

**Inputs:**
- Per-proposal: confidence score (from ProposalComposer, in [0, 1])
- Per-proposal: accepted/rejected boolean (from external evaluator)
- Binned into confidence groups (default 10 bins)

**Outputs:**
- ECE = Σ (|bin_confidence - bin_accuracy| × bin_size / N) in [0, 1]
- Brier score = mean((confidence - accepted)²) in [0, 1]
- Maximum Calibration Error (MCE) = max |bin_confidence - bin_accuracy|
- Reliability diagram data (per-bin confidence vs accuracy)

**Assumptions:**
- Confidence is the ProposalComposer's self-reported confidence
- Accepted/rejected is the external evaluator's verdict
- Perfect calibration: ECE = 0 (confidence matches accuracy in every bin)
- Established result: ECE = 0.433 (DR-96, cycle 252) — poor calibration

**Known failure modes:**
- ECE = 0.433 means confidence is very poorly calibrated (0 = perfect,
  1 = worst)
- This is the Goodhart's law vulnerability (DR-96): if you optimize
  confidence, you don't necessarily improve accuracy
- The Brier score (also computed) provides a complementary view but
  tells the same story
- 6 proposals is too few for reliable binning; the ECE estimate itself
  is uncertain

**Uncertainty:**
- Bootstrap quantified (cycle 261): 0.9000 ± 0.0111 (95% CI: 0.8750,
  0.9250; N=6, B=500). Per-proposal (confidence, accepted) pairs resampled.
- NOTE: the bootstrap ECE (0.9000) differs from the reported ECE (0.433)
  because the bootstrap uses 5 bins and a confidence proxy (internal_quality
  normalized to [0,1]) rather than the original confidence values. The
  bootstrap ECE is higher because the proxy confidence is all in the
  0.8-0.95 range, making every bin's |conf - acc| large.
- The CI is narrow (0.8750 to 0.9250) but the metric itself is
  approximated. The narrow CI reflects 'the approximation is stable',
  not 'the ECE is precisely 0.90'.
- The original 0.433 ECE (from dr95) used the actual confidence values
  and 10 bins. The two numbers are not directly comparable.

**Evidence tier:**
- I (LLM inference)

**Calibration status:**
- UNCALIBRATED. The DR-96 study IS the calibration attempt; it found
  ECE = 0.433, which is "poorly calibrated" (threshold: ECE > 0.2).

**Owner:**
- audit/measurement_integrity/dr95_epistemic_calibration.py
  ::compute_confidence_calibration

**Acceptance:**
- Reported as `ECE: 0.XXX (Brier: 0.YYY, MCE: 0.ZZZ)`
- MUST be reported alongside M-304 (agreement) and M-305 (bias)
- ECE > 0.2 blocks any confidence-based claim (per DR-96)
- This metric completes the evaluator-unreliability triad:
  M-304 (judges disagree) + M-305 (internal biased) + M-306
  (confidence miscalibrated) = evaluators are not trustworthy
  instruments (yet)

---

## Stage M1 acceptance criteria

Stage M1 is complete when:

1. Every metric in the inventory above has a complete specification
   (all 9 fields filled in).
2. No metric exists in the codebase that is not in the inventory.
3. The specification is reviewed and accepted by the measurement owner.

**Current status: 30 of 30 metrics specified (100%).**
- M-001 through M-016: discovery metrics (16/16)
- M-101 through M-105: invention metrics (5/5)
- M-201 through M-205: search metrics (5/5)
- M-301 through M-303: evaluation metrics (3/3, M-303 split into D1-D7)
- M-304 through M-306: evaluation metrics (3/3)

**Stage M1: PASS (specification complete).**

**Caveat (Stage M3 gap):** the 14 new metrics (M-101..M-105,
M-201..M-205, M-304..M-306) have "NOT YET QUANTIFIED" in their
Uncertainty fields. Stage M3 bootstrap (cycle 259) covered the original
19 metrics but NOT these 14. Extending bootstrap to cover all 30 metrics
is a Stage M3 follow-up task — it does not block Stage M1 acceptance
(specification is complete), but it does block Gate 1 overall (the
"Confidence intervals on all metrics" criterion requires all 30 to
have CIs, not just 19).
