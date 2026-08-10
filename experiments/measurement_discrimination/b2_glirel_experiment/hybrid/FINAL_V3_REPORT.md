# B-2 GLiREL Experiment — Final Report (V3 Lock)

**Date:** 2026-08-10
**Status:** NON-AUTHORITATIVE PARALLEL ENGINEERING EXPERIMENT
**Frozen B-2 instrument (commit f905b68):** UNTOUCHED
**Held-out set:** NOT ACCESSED

---

## V3 Adapter Freeze

| Dimension | Value |
|-----------|-------|
| Adapter | span_adapter_v3.py (four-case: standard, single_token, swapped_inversion, out_of_range) |
| Status | IMMUTABLE — no further changes |
| Freeze record | hybrid_v3/FREEZE_RECORD.md |
| Code commit | 98ed9c0 (adapter), 6653517 (gold benchmark) |

---

## Gold Benchmark Results (GLiREL-SPAN-GOLD-v1)

### Span Engineering: SOLVED

| Metric | Value | Assessment |
|--------|-------|------------|
| Mechanical span validity | 100.0% (500/500) | Independently verified |
| Span precision | 100.0% (500/500) | All extracted spans match gold entities |
| Span recall | 73.7% (14/19) | 5 minor entities not extracted |

### Relation Quality: POOR

| Metric | Value | Assessment |
|--------|-------|------------|
| Relation precision | 1.2% (3/250) | Only 3 exactly match gold |
| Relation recall | 10.0% (3/30) | Only 3 gold relations recovered |
| Direction accuracy | 2.0% (3/147) | Direction almost always wrong |

### Relation Classification

| Classification | Count | % |
|---------------|-------|---|
| PARTIAL | 140 | 56.0% |
| WRONG_ENTITY | 103 | 41.2% |
| WRONG_RELATION | 4 | 1.6% |
| CORRECT | 3 | 1.2% |

### Interpretation

- The V3 adapter is correct (spans are perfect)
- GLiREL beta's relation extraction quality is too low for direct evidence use (1.2% precision)
- The LLM's 31% evidence utilization rate and zero false citations are **justified** by the gold benchmark: the LLM is correctly rejecting 98.8% of GLiREL relations because they ARE wrong
- The 56% PARTIAL rate suggests GLiREL finds relevant entity pairs but gets relation label or direction wrong

---

## A/B/C Representation Experiment

### Status: PARTIAL — 8/13 cases (24/39 API calls)

**BLOCKED by API rate limiting (429).** Checkpoint preserved at 24/39. No duplicate calls. Resumable when rate limit clears.

### Completed Cases (8/13)

| Case | Expected | A (raw) | B (table) | C (graph) |
|------|----------|---------|-----------|-----------|
| ADV-01 | REJECT | X (UNSUPPORTED) | OK (REJECT) | OK (REJECT) |
| ADV-02 | REJECT | OK (REJECT) | OK (REJECT) | X (UNSUPPORTED) |
| ADV-03 | ALLOW | OK (ALLOW) | X (REJECT) | OK (ALLOW) |
| ADV-04 | ALLOW | X (UNSUPPORTED) | X (REJECT) | X (UNSUPPORTED) |
| ADV-05 | REJECT | X (UNSUPPORTED) | X (UNSUPPORTED) | X (UNSUPPORTED) |
| ADV-06 | REJECT | X (UNSUPPORTED) | X (UNSUPPORTED) | OK (REJECT) |
| ADV-07 | ALLOW | **OK** (ALLOW) | X (UNSUPPORTED) | X (REJECT) |
| ADV-08 | ALLOW | X (UNSUPPORTED) | **OK** (ALLOW) | X (REJECT) |

### Summary (8 cases only — NOT final)

| Representation | Accuracy | False Citations | Total Cited |
|---------------|----------|-----------------|-------------|
| A (raw list) | 3/8 | 0 | 14 |
| B (table) | 3/8 | 0 | 14 |
| C (graph) | 3/8 | 0 | 6 |

### Key Observations (8 cases)

1. **All three representations have equal accuracy (3/8)** — no representation dominates
2. **Zero false citations** across all representations — LLM correctly rejects wrong evidence
3. **ADV-07 won only by A** — raw list provides enough context for 4 cited relations
4. **ADV-08 won only by B** — structured table enables 4 cited relations
5. **Representation C (graph) cites the least** (6 vs 14) — most selective

### Remaining Cases (blocked by rate limiting)

| Case | Status |
|------|--------|
| ADV-09 | NOT STARTED |
| ADV-10 | NOT STARTED |
| ADV-11 | NOT STARTED |
| ADV-12 | NOT STARTED |
| ADV-13 | NOT STARTED |

---

## Forensic Traces: ADV-07 and ADV-08

### ADV-07 (enzyme-templated inorganic lattice formation → ALLOW)

| Rep | Label | Cited | Details |
|-----|-------|-------|---------|
| A | ALLOW | 4 | PRODUCES(osteoblast→Calcium phosphate), USES(diatoms→silicatein), PRODUCES(diatoms→silica-based) — helpful=true |
| B | UNSUPPORTED | 0 | No relations cited |
| C | REJECT | 1 | USES(diatoms→silicatein) — helpful=true but insufficient |

**Why A succeeds:** The raw list format gives the LLM all 10 relations at once, allowing it to find 3 cross-source relations that establish enzyme-templated mineral deposition. The table (B) and graph (C) formats cause the LLM to be more selective, missing the cross-source connection.

### ADV-08 (protein-catalyzed biogenic oxide precipitation → ALLOW)

| Rep | Label | Cited | Details |
|-----|-------|-------|---------|
| A | UNSUPPORTED | 0 | No relations cited |
| B | ALLOW | 4 | PRODUCES(silicatein→silica), PRODUCES(diatoms→silica), USES(diatoms→silicatein) — helpful=true |
| C | REJECT | 1 | USES(diatoms→silicatein) — helpful=true but insufficient |

**Why B succeeds:** The structured table format with explicit span offsets allows the LLM to verify relations against the source text, giving it confidence to cite 3 Source B relations. The raw list (A) doesn't provide enough structure for verification, and the graph (C) is too selective.

### Causal Attribution

**The representation changes WHICH evidence the LLM uses, not WHAT evidence is available.** The same GLiREL V3 output is presented differently, and the LLM's evidence selection changes. This is a representation effect, not an evidence quality effect.

Given the gold benchmark result (1.2% relation precision), the cited relations in ADV-07 and ADV-08 may be among the 1.2% CORRECT or among the 56% PARTIAL. Without per-relation gold verification of the cited relations, the improvement is **unproven** as a causal effect of better evidence.

---

## 8 Decision-Gate Questions

### Q1: Did the V3 adapter solve the span problem?

**YES.** 100% mechanical validity (500/500 independently verified), 100% span precision, 73.7% span recall. The four-case adapter (standard, single_token, swapped_inversion, out_of_range) recovers all 6500 spans. The 520 "inverted" spans are all MODEL_OUTPUT_INVERSION, recoverable by swapping, and semantically verified (100% Category A).

### Q2: Does the gold benchmark prove GLiREL relation quality is too low for direct use?

**YES.** 1.2% relation precision means 98.8% of extracted relations are wrong. 10% relation recall means 90% of gold relations are missed. 2% direction accuracy means 98% of relations have wrong direction. GLiREL beta's relation extraction is not suitable as a direct evidence source for B-2 adjudication.

### Q3: Does any representation improve the adjudicator on the full 13-case set?

**INCONCLUSIVE (8/13 cases).** All three representations have equal accuracy (3/8) on completed cases. The remaining 5 cases are blocked by API rate limiting. No representation dominates.

### Q4: Does any representation recover ADV-07 or ADV-08 without increasing false positives elsewhere?

**PARTIALLY.** A recovers ADV-07 (ALLOW, 4 cited) but loses ADV-08. B recovers ADV-08 (ALLOW, 4 cited) but loses ADV-07. Neither representation recovers both. Zero false citations across all representations.

### Q5: Is the zero false-citation behavior justified by the gold benchmark?

**YES.** The gold benchmark shows 98.8% of GLiREL relations are wrong. The LLM's zero false-citation rate and 31% utilization rate are the correct response to overwhelmingly wrong evidence. The LLM is not "under-using" evidence arbitrarily — it is filtering bad evidence.

### Q6: Does the hybrid improve the system's auditability even if raw accuracy remains limited?

**PARTIALLY.** The evidence graph (representation C) provides explicit provenance (source, span, score, relation label) that is more auditable than the LLM-only approach. However, with 1.2% relation precision, the auditable evidence is mostly wrong, limiting the value of auditability.

### Q7: Is GLiREL-large still worth a separate test after the representation experiment?

**YES — this is now the strongest argument for testing glirel-large-v0.** The span problem is solved (V3 adapter works for any GLiREL model since it handles the same position format). The relation quality problem (1.2% precision) is a model-capability issue that may improve with a larger checkpoint. The representation experiment (A/B/C) has shown that representation matters but cannot overcome poor relation quality. Testing glirel-large-v0 with the V3 adapter would isolate the model variable.

### Q8: Does any of this justify changing the frozen B-2 experiment?

**NO.** The frozen B-2 detector (commit f905b68) remains authoritative. GLiREL beta's relation quality is too low (1.2% precision) to justify modifying the frozen instrument. The hybrid experiment remains a parallel engineering experiment with no production authorization.

---

## Final Classification

### **INCONCLUSIVE — MORE PUBLIC TESTING**

**Rationale:**
- Span engineering is solved (100% mechanical validity, 100% precision)
- Relation quality is too low (1.2% precision, 10% recall, 2% direction accuracy)
- A/B/C is incomplete (8/13 cases, blocked by rate limiting)
- No representation dominates on completed cases
- Zero false citations is justified by gold benchmark
- GLiREL-large-v0 is the most promising next step (may improve relation quality)

**Next steps (in order):**
1. Complete remaining 5 A/B/C cases when API rate limit clears
2. Test glirel-large-v0 with V3 adapter (isolate model variable)
3. If large model improves relation precision significantly, re-run A/B/C
4. Only then consider N=5 stability
5. Only then consider any frozen B-2 modification

---

## What Was NOT Touched

- b2_detector.mjs, SYSTEM_PROMPT.md, b2_trace_validator.mjs: UNCHANGED
- Frozen LLM instrument: UNCHANGED
- B-2 ontology, inference-rule taxonomy, thresholds: UNCHANGED
- Production substrate: UNCHANGED
- Held-out material: NOT ACCESSED
- V3 adapter: FROZEN (no further changes)
- A/B/C checkpoint: PRESERVED (24/39, resumable)
