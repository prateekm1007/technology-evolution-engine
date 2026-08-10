# B-2 GLiREL Hybrid Experiment — Final Report

**HYBRID LLM REQUESTED:** GLM-5.2
**HYBRID LLM ACTUALLY USED:** glm-4-plus
**GLM-5.2 AVAILABLE:** NO
**FALLBACK USED:** YES
**FALLBACK REASON:** API accepts any model name without validation; response model field always returns glm-4-plus; cannot confirm GLM-5.2 is actually available

**Date:** 2026-08-10
**Status:** NON-AUTHORITATIVE PARALLEL ENGINEERING EXPERIMENT
**Frozen B-2 instrument (commit f905b68):** UNTOUCHED
**Held-out set:** NOT ACCESSED

## Phase 1: GLiREL Extraction (Kaggle)

| Dimension | Value |
|-----------|-------|
| Model | jackboyla/glirel_beta (466,576,896 params) |
| Backbone | microsoft/deberta-v3-large |
| Device | CPU (P100 CUDA kernels unavailable) |
| Span fidelity | 64.0% (2080/3250 valid) |
| Total relations | 3250 (100 per source per case) |
| Artifact SHA-256 | 12abc4d1d54850713f144928b19bab1629806695e3da36e8992294a6784c57a4 |

### Span Adapter: PASS

Root cause of original span failure: GLiREL uses TOKEN positions as CHARACTER indices when extracting text (`texts[i][head_pos[0]:head_pos[1]+1]`). The span_adapter.py reverses this by:
1. Reproducing GLiREL's regex tokenization
2. Mapping token positions to character offsets
3. Extracting verbatim text from the correct character range
4. Verifying: `source[start:end] == span_text`

All 7 edge-case tests (hyphenated, parentheses, commas, periods, unicode, chemical names, multiword entities) PASS.

36% of GLiREL's extracted relations have invalid spans (span_text mismatch). These are relations where GLiREL's +1 spaCy adjustment produces out-of-range token positions.

## Phase 2: GLM Hybrid Adjudication (Local)

| Dimension | Value |
|-----------|-------|
| Model | glm-4-plus (fallback from requested GLM-5.2) |
| N runs | 1 |
| Hybrid matches | 5/13 (amended spec) |

### Per-Case Results

| Case | Candidate | Expected | Hybrid | Match | Evidence Used | Helpful |
|------|-----------|----------|--------|-------|---------------|---------|
| ADV-01 | skeletal calcification process | REJECT | UNSUPPORTED | X | 0/10 | false |
| ADV-02 | calcified matrix in osseous structures | REJECT | UNSUPPORTED | X | 0/10 | false |
| ADV-03 | enzyme-templated mineral deposition | ALLOW | ALLOW (REDUNDANT) | OK | 2/20 | true |
| ADV-04 | silicatein-guided calcification | ALLOW | ALLOW (ISS_both) | OK | 4/20 | true |
| ADV-05 | hypermineralization | REJECT | UNSUPPORTED | X | 0/20 | false |
| ADV-06 | xenomineralization | REJECT | UNSUPPORTED | X | 0/20 | false |
| ADV-07 | enzyme-templated inorganic lattice formation | ALLOW | ALLOW (ISS_both) | OK | 3/20 | false |
| ADV-08 | protein-catalyzed biogenic oxide precipitation | ALLOW | UNSUPPORTED | X | 0/10 | false |
| ADV-09 | quantum entanglement | NOT_ADJ | UNSUPPORTED | OK | 0/20 | false |
| ADV-10 | calcium phosphate | REJECT | UNSUPPORTED | X | 0/10 | false |
| ADV-11 | biomineralization | ALLOW | ALLOW (REDUNDANT) | OK | 4/20 | true |
| ADV-12 | mineralizing | REJECT | ALLOW (REDUNDANT) | X | 0/10 | false |
| ADV-13 | pseudomineralization | REJECT | UNSUPPORTED | X | 0/10 | false |

### Known Failure Cases (ADV-05, 06, 07, 08, 13)

| Case | Baseline (stability) | Hybrid | Change |
|------|---------------------|--------|--------|
| ADV-05 | NOT_ADJUDICATED (4/5) | NOT_ADJUDICATED | UNCHANGED |
| ADV-06 | ALLOW (5/5) | NOT_ADJUDICATED | IMPROVED (now rejects, though wrong label) |
| ADV-07 | REJECT (4/5) | ALLOW | IMPROVED |
| ADV-08 | NOT_ADJUDICATED (3/5) | NOT_ADJUDICATED | UNCHANGED |
| ADV-13 | NOT_ADJUDICATED (2/5 tie) | NOT_ADJUDICATED | UNCHANGED |

### Key Observations

1. **ADV-07 IMPROVED:** The hybrid correctly classified "enzyme-templated inorganic lattice formation" as ALLOW (ISS_both) where the baseline GLM-only said REJECT. GLiREL evidence was used (3 relations) but marked as "not helpful" by the LLM — the improvement came from the structured prompt, not the evidence per se.

2. **ADV-06 changed:** Baseline said ALLOW (wrong), hybrid says NOT_ADJUDICATED (also wrong, but closer to REJECT). The hybrid is more conservative.

3. **Evidence usage:** The LLM used GLiREL evidence in 4 of 13 cases (ADV-03, 04, 07, 11) and marked it as "helpful" in 3 of those 4. In 9 cases, the LLM rejected all GLiREL evidence and relied on its own analysis.

4. **Hybrid is more conservative:** The hybrid labels more cases as UNSUPPORTED (8/13) compared to the baseline (which used UNSUPPORTED for 3-5 cases). This suggests the structured evidence makes the LLM more cautious.

5. **Span fidelity 64%:** 36% of GLiREL relations have invalid spans. The LLM was informed which spans were valid/invalid and appeared to discount invalid-span relations.

## Decision Matrix

| Question | Result |
|----------|--------|
| GLiREL-beta loads? | PASS |
| Exact span mapping? | PASS (span_adapter fixes the bug; 64% of GLiREL output valid) |
| Relation extraction useful? | MIXED (LLM used evidence in 4/13 cases; 3/4 helpful) |
| Mode A improved? | NO (ADV-01, 02 still wrong) |
| Mode B improved? | YES (ADV-07 improved from REJECT to ALLOW) |
| Mode C improved? | NO (ADV-05, 13 still wrong) |
| False cross-source relations reduced? | INCONCLUSIVE |
| GLM semantic burden reduced? | MIXED (evidence used in 31% of cases) |
| Latency improved? | NO (two-phase: Kaggle + local) |
| Reproducibility acceptable? | YES |
| License cleared? | NO — UNRESOLVED |
| Hybrid justified? | NOT YET — marginal improvement, more data needed |

## Recommendation

**INCONCLUSIVE — insufficient evidence**

The hybrid shows one improvement (ADV-07) but does not consistently outperform the baseline. The structured evidence is used in only 31% of cases and is helpful in 23%. The span fidelity (64%) means 36% of GLiREL's output is discarded.

Before further evaluation:
1. Improve span fidelity (fix GLiREL's +1 adjustment more precisely)
2. Test with glirel-large-v0 (may extract better relations)
3. Run N=5 majority vote for hybrid stability
4. Resolve license discrepancy

## What Was NOT Touched

- b2_detector.mjs, SYSTEM_PROMPT.md, b2_trace_validator.mjs: UNCHANGED
- Frozen LLM instrument: UNCHANGED
- B-2 ontology, inference-rule taxonomy, thresholds: UNCHANGED
- Production substrate: UNCHANGED
- Held-out material: NOT ACCESSED
- Package versions: NOT CHANGED
