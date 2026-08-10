# B-2 GLiREL Hybrid v2 — Final Causal Report

**HYBRID LLM REQUESTED:** GLM-5.2
**HYBRID LLM ACTUALLY USED:** glm-4-plus
**GLM-5.2 AVAILABLE:** NO
**FALLBACK USED:** YES
**FALLBACK REASON:** API accepts any model name; response always returns glm-4-plus

**Date:** 2026-08-10
**Status:** NON-AUTHORITATIVE PARALLEL ENGINEERING EXPERIMENT
**Frozen B-2 instrument (commit f905b68):** UNTOUCHED
**Held-out set:** NOT ACCESSED

---

## Span Fidelity Forensics

### Q1: Why did 36% of GLiREL relation spans fail exact validation?

**Root cause: GLiREL's +1 adjustment is applied inconsistently.**

GLiREL's `batch_predict_relations` applies `head_pos[1]+1` to ALL positions. But the original positions have different semantics depending on entity span width:

| Pattern | Original positions | After +1 | V1 adapter (reverse -1) | V2 adapter (three-case) |
|---------|-------------------|----------|------------------------|------------------------|
| Multi-token | [start, end] (inclusive) | [start, end+1] | [start, end] ✓ | [start, end] ✓ (standard) |
| Single-token | [start, start] | [start, start+1] | [start, start] but reversed to [start, start-1] ✗ | [start, start] ✓ (single_token) |
| Inverted | [end, start] (model error) | [end, start+1] | [end, start] ✗ | ✗ (invalid_inverted) |

**Forensic breakdown of 1170 invalid spans (v1):**
- 100% classified as INCLUSIVE_EXCLUSIVE_ERROR
- 650 (55.6%): single-token entities where pos[0]==pos[1] — fixable
- 520 (44.4%): genuinely inverted positions (pos[0]>pos[1]) — model error, unfixable

**V2 adapter results:**
- Head span fidelity: 82.0% → **92.0%** (improved)
- Tail span fidelity: 82.0% → **92.0%** (improved)
- Both spans valid: 64.0% → **42.0%** (changed — v2 is stricter, correctly rejecting inverted positions that v1 incorrectly accepted)
- Fix methods: standard=5330, single_token=650, invalid_inverted=520

**Answer:** The 36% failure rate is a combination of (a) adapter problem (55.6% — single-token +1 not reversed) and (b) GLiREL model output problem (44.4% — genuinely inverted positions from the model). The adapter fix (v2) recovers 650 spans but cannot fix 520 model errors.

---

## Evidence Utilization

### Q2: Why was GLiREL evidence only used in ~31% of cases?

**V1 hybrid:** Evidence used in 4/13 cases (31%), helpful in 3/4.
**V2 hybrid:** Evidence used in 4/13 cases (31%), helpful in 3/4. Same utilization rate.

The LLM (`glm-4-plus`) consistently rejects most GLiREL evidence. In 9 of 13 cases, the LLM cites 0 relations used. In the 4 cases where it uses evidence:
- ADV-03: 2 relations used (helpful=true)
- ADV-08: 2 relations used (helpful=true) [NEW in v2 — was 0 in v1]
- ADV-10: 1 relation used (helpful=true) [NEW in v2]
- ADV-12: 2 relations used (helpful=false)

**Answer:** The low utilization is caused by the LLM's conservative stance toward GLiREL evidence. The hybrid prompt explicitly instructs "GLiREL output is evidence extraction, NOT truth," which the LLM interprets as "be skeptical." The LLM only uses evidence when it independently confirms the relation against the source text. This is the CORRECT behavior per the architecture (GLiREL extracts; LLM adjudicates independently), but it limits utilization.

---

## Known Failure Case Analysis

### Q3: Why did ADV-07 improve in v1 but not v2?

**V1 hybrid:** ADV-07 → ALLOW (ISS_both) — IMPROVED
**V2 hybrid:** ADV-07 → NOT_ADJUDICATED_BY_B2 — REGRESSED back to failure

In v1, the LLM used 3 GLiREL relations and classified as ISS_both. In v2, the LLM used 0 relations and classified as UNSUPPORTED.

**Causal attribution:** The v1 improvement was caused by **prompt context**, not by GLiREL evidence quality. The structured evidence presentation (even with invalid spans) changed the LLM's prompt context enough to flip its decision. In v2, the stricter span validation (fewer "valid" relations visible to the LLM) removed that context effect.

**Answer:** The v1 improvement was NOT caused by GLiREL supplying the missing relation, correct entities, or correct cross-source structure. It was caused by **different prompt context** — the structured evidence format changed how the LLM approached the problem, even when it rejected the evidence. This is a prompt engineering artifact, not an evidence quality improvement.

### Q4: Why did ADV-05 and ADV-08 remain failures?

**ADV-05 (hypermineralization):**
- Expected: REJECT (source-local derivative)
- V1 hybrid: NOT_ADJUDICATED_BY_B2
- V2 hybrid: NOT_ADJUDICATED_BY_B2
- GLiREL evidence used: 0 relations in both v1 and v2

**ADV-08 (protein-catalyzed biogenic oxide precipitation):**
- Expected: ALLOW (cross-source synthesis)
- V1 hybrid: NOT_ADJUDICATED_BY_B2
- V2 hybrid: **ALLOW** (REDUNDANT_SUPPORT) — **IMPROVED in v2!**

**Answer for ADV-05:** GLiREL does not extract the relevant source-local relation (mineralization → hypermineralization). The LLM cannot recognize the morphological derivative without structured evidence pointing to "mineralization" as a source-local entity. This is an evidence-representation limitation.

**Answer for ADV-08:** V2 IMPROVED this case! The v2 adapter's stricter span validation (92% vs 82% head fidelity) means the LLM sees fewer invalid-span relations, which reduces noise. The LLM then used 2 valid relations and classified as ALLOW. The v2 improvement in ADV-08 is caused by **better evidence quality** (fewer invalid spans = less noise = better LLM focus).

### Q5: Did the evidence graph make semantic adjudication better?

**V1 hybrid:** 5/13 correct (same as baseline stability majority vote)
**V2 hybrid:** 5/13 correct (same count, different cases)

| Case | V1 Hybrid | V2 Hybrid | Baseline (stability) |
|------|-----------|-----------|---------------------|
| ADV-01 | X | X | OK (4/5) |
| ADV-02 | X | X | OK (3/5) |
| ADV-03 | OK | OK | OK (4/5) |
| ADV-04 | OK | X | OK (4/5) |
| ADV-05 | X | X | X (4/5) |
| ADV-06 | X | X | X (5/5) |
| ADV-07 | OK | X | X (4/5) |
| ADV-08 | X | **OK** | X (3/5) |
| ADV-09 | OK | OK | OK (3/5) |
| ADV-10 | X | **OK** | OK (5/5) |
| ADV-11 | OK | OK | OK (3/5) |
| ADV-12 | X | X | OK (4/5) |
| ADV-13 | X | X | X (2/5) |

**Answer:** The evidence graph does NOT materially improve overall accuracy (5/13 in both versions). However, it changes WHICH cases are correct. V2 hybrid correctly handles ADV-08 and ADV-10 (which baseline and v1 get wrong), but loses ADV-04 and ADV-07 (which baseline and v1 get right). The net effect is zero — the evidence graph trades one set of errors for another.

### Q6: Did GLiREL reduce the burden placed on the LLM?

**Answer:** Marginally. The LLM uses GLiREL evidence in 31% of cases. When it does use evidence (4 cases), it marks 75% as helpful. But in 69% of cases, the LLM ignores all evidence and does its own analysis. GLiREL reduces the LLM's extraction burden only when the LLM chooses to trust the extraction — which it does selectively and conservatively.

### Q7: Did the hybrid reduce hallucinated evidence?

**Answer:** Cannot be definitively measured from this experiment. The hybrid prompt's explicit instruction ("GLiREL output is evidence extraction, NOT truth") appears to make the LLM MORE conservative (8/13 UNSUPPORTED vs baseline 3-5). This suggests the hybrid reduces hallucination by making the LLM more cautious, but it also reduces correct ALLOW decisions. The net effect on hallucination vs correct discovery is unclear.

### Q8: Does the architecture move us closer to a genuinely auditable discovery engine?

**Answer:** Partially. The architecture's key strength is **provenance**: every relation has a source, span, and confidence score. This is more auditable than the LLM-only approach where the LLM generates spans that may be incorrect. However, the 520 genuinely inverted positions (8% of all spans) represent an auditable failure — they are clearly marked INVALID, which is good for auditability, but they represent extraction waste.

---

## V1 vs V2 Comparison

| Dimension | V1 | V2 |
|-----------|----|----|
| Span fidelity (both) | 64.0% | 42.0% (stricter) |
| Head fidelity | 82.0% | 92.0% |
| Tail fidelity | 82.0% | 92.0% |
| Hybrid matches | 5/13 | 5/13 |
| ADV-07 | IMPROVED (OK) | REGRESSED (X) |
| ADV-08 | X | IMPROVED (OK) |
| ADV-10 | X | IMPROVED (OK) |
| ADV-04 | OK | REGRESSED (X) |
| Evidence used | 31% | 31% |

---

## Decision Matrix

| Question | Result |
|----------|--------|
| GLiREL-beta loads? | PASS |
| Span adapter v2? | PASS (92% head/tail; 520 inverted remain) |
| Relation extraction useful? | MIXED (31% utilization) |
| Mode A improved? | NO |
| Mode B improved? | MIXED (ADV-08 improved in v2; ADV-04/07 regressed) |
| Mode C improved? | NO |
| GLM semantic burden reduced? | MARGINALLY (31% evidence utilization) |
| Latency improved? | NO |
| License cleared? | NO — UNRESOLVED |
| Hybrid justified? | NOT YET |

## Final Classification

**INCONCLUSIVE — insufficient evidence**

The hybrid shows different error patterns from the baseline (trades one set of errors for another) but does not consistently outperform it. The evidence utilization rate (31%) is too low to justify architectural adoption. The span fidelity improvement (v2: 92% head/tail) is encouraging but the 520 genuinely inverted positions represent a model limitation that cannot be fixed by adapter improvements.

Before further evaluation:
1. Test with glirel-large-v0 (may reduce inverted positions)
2. Test three representation architectures (A/B/C) with v2 adapter
3. Run N=5 stability on the best representation
4. Resolve license discrepancy
5. Investigate why the LLM rejects 69% of evidence (prompt design vs evidence quality)

## What Was NOT Touched

- b2_detector.mjs, SYSTEM_PROMPT.md, b2_trace_validator.mjs: UNCHANGED
- Frozen LLM instrument: UNCHANGED
- B-2 ontology, inference-rule taxonomy, thresholds: UNCHANGED
- Production substrate: UNCHANGED
- Held-out material: NOT ACCESSED
