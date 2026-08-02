# NORMALIZATION_GAP — Phase 5.D Measurement

**Status:** measurement document. No parser changes. No semantic matching.
**Phase:** 5.D (per CEO directive, post-Phase 5.C audit).
**Read this file BEFORE any future parser or ingestion work.**

> Do not solve these problems yet. Measure them.
> — CEO directive, Phase 5.D

This document measures the normalization gap between component labels
in the civilization graph. It does NOT propose solutions. Per the
CEO's most important instruction:

> Do not interpret this as permission to build semantic matching.
> The evidence currently supports only this statement:
>   Exact-label matching is the limiting factor.
> It does not support the statement:
>   Semantic matching is the correct solution.
> Those are very different conclusions.

---

## 1. The bottleneck has shifted

The Phase 5.A–5.C audits identified the bottleneck as:

```text
insufficient data
```

The Phase 5.D measurement identifies the bottleneck as:

```text
insufficient normalization
```

The graph now has 140 distinct component labels across 669 nodes.
10 of those labels are shared by 2+ sources (exact matches). 4 are
**potential matches** — pairs of labels that refer to the same concept
but are treated as different labels because the parser uses exact
matching. The remaining 126 are unmatched (no bridge exists, no
potential bridge identified).

This means the system has stopped producing new shared components
(not because no new components are being ingested, but because the
new components don't match existing labels).

---

## 2. The failed-bridge table

For every failed bridge, this section records: Source A, Source B,
and why the bridge failed. **No solutions are proposed.**

| # | Source A | Source B | Why bridge failed | In graph both? |
|---|---|---|---|---|
| 1 | `metal-organic framework` | `MOF` / `MOFs` | abbreviation | No — `mof` excluded from keyword list (false-positive risk: substring-matches `monolithic`, `demof`, etc.); appears in arxiv_2311.00341, arxiv_2407.00470, arxiv_2501.04825 source text but was never extracted |
| 2 | `sorbent` | `adsorbent` | terminology drift | Yes — both extracted as separate component nodes from arxiv:2311.00341 (DAC paper). Near-synonyms in AWH/DAC literature; both refer to materials that capture gases |
| 3 | `electrode` | `anode` / `cathode` | hypernym / subtype | Yes — `electrode` extracted from US patent US20240194939A1 (battery); `anode` + `cathode` extracted from arxiv:2307.03620 (battery paper). Anode and cathode are subtypes of electrode |
| 4 | `battery` | `an all-solid-state battery laminate including at least one...` | compound vs simple | Yes — `battery` extracted as a simple keyword from US patent US20240194939A1; the long compound label was extracted from the same patent's claims-format parser (different extraction pathway). Both contain "battery" but don't share a node |

### Failed bridges NOT yet observed (but expected in future ingestion)

These are normalization gaps that the auditor identified as expected
patterns but that haven't manifested in the current corpus because the
extraction hasn't produced both sides yet:

| # | Source A | Source B | Why bridge would fail | Status |
|---|---|---|---|---|
| 5 | `battery` (in graph) | `batteries` (NOT in graph) | pluralization | The keyword `battery` uses substring matching: `'battery' in text.lower()`. This does NOT match `batteries` (the trailing 'y' vs 'ies'). The arxiv:2307.03620 paper uses "batteries" throughout — the `battery` keyword undercounts. The word "batteries" is in the source text but was not extracted. |
| 6 | `electrode` (in graph) | `electrodes` (NOT in graph) | pluralization | Same substring-matching issue. arxiv:2307.03620 mentions "anode, cathode, solid electrolyte" (singular) but other papers might use plurals. |
| 7 | `membrane` (in graph) | `membranes` (NOT in graph) | pluralization | Same substring-matching issue. The desalination literature uses both singular and plural forms. |
| 8 | `metamaterial` (in graph) | `metamaterials` (NOT in graph) | pluralization | Same substring-matching issue. 3 radiative cooling arxiv papers mention "metamaterials" (plural); the keyword `metamaterial` happens to match `metamaterials` because `'metamaterial' in 'metamaterials'.lower()` → True (substring). This is an ACCIDENTAL match — the keyword works for plurals in this case because the plural adds an 's' after the full singular. Not all keywords have this property. |

---

## 3. The `bridgeable_shared_components` metric

A purely analytical measurement (NOT an implementation). Measures
how much signal is being lost to normalization gaps.

### Definition

```
bridgeable_shared_components = {
    exact_matches:    labels shared by 2+ sources (already merged)
    potential_matches: labels that COULD share under some normalization rule
    unmatched_labels: labels with no bridge, no potential
}
```

### Current values (graph v4.2, 669 nodes)

| Metric | Count |
|---|---:|
| Total distinct component labels | 140 |
| **Exact matches** (labels shared by 2+ sources) | **10** |
| **Potential matches** (normalization gaps identified) | **4** |
| **Unmatched labels** (no bridge, no potential) | **126** |

### The 10 exact matches (labels already shared)

| Label | Sources sharing it |
|---|---|
| `substrate` | 6 sources (US-10123456, US-10456789, US-10678901, US-10890123, US-10901234, US-11012345) |
| `electrode` | 5 sources (10.1038/nchem.2023.007, 10.1038/nenergy.2023.003, US-10678901, US-10789012, US20240194939A1) |
| `sensor` | 5 sources (US-10123456, US-10345678, US-10678901, US-10890123, US-10901234) |
| `coating` | 5 sources (10.1021/acs.nanolett.2023.004, US-10123456, US-10456789, US-10901234, WO2017151514A1) |
| `pump` | 5 sources (US-10234567, US-10456789, US-10567890, US-10789012, US-10890123) |
| `membrane` | 4 sources (10.1021/acs.nanolett.2023.004, US-10456789, US-10789012, US4039440A) |
| `chamber` | 3 sources (US-10234567, US-10789012, WO2017210800A1) |
| `battery` | 3 sources (10.1038/nenergy.2023.003, US-10345678, US20240194939A1) |
| `exchanger` | 2 sources (US-10123456, US-10567890) |
| `panel` | 2 sources (US-10890123, US20160363396A1) |

### Signal loss measurement

The 10 exact matches represent the current signal ceiling — these
are the labels that ARE shared across sources. The 4 potential
matches represent signal that COULD be recovered IF normalization
rules were applied (pluralization, abbreviation, synonymy, hypernym).

**Signal recovery potential:**
- If all 4 potential matches were resolved: +4 shared labels (40%
  increase over current 10).
- If pluralization gaps (5-8) were also resolved: depends on future
  ingestion, but the arxiv:2307.03620 paper alone would gain
  "batteries" as a shared label with the existing "battery" node.

**This is a measurement, not a recommendation.** The CEO's directive
explicitly forbids interpreting this as permission to build semantic
matching. The numbers show that normalization gaps exist; they do
NOT show that semantic matching is the right solution.

---

## 4. Saturation analysis

The CEO's directive: "Measure d(shared_components) / d(total_components).
That derivative is probably more informative than the raw score itself."

### Saturation table (battery × EV pair, across all 4 snapshots)

| Snapshot | Graph v | Nodes | Edges | Shared components | Total components | Score | d(shared) | d(total) | **d(shared)/d(total)** |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| snapshot_1 | 3.1 | 632 | 530 | 0 | 0 | 1.2000 | — | — | — |
| snapshot_2 | 4.0 | 651 | 550 | 1 | 4 | 1.2500 | +1 | +4 | **+0.2500** |
| snapshot_3 | 4.1 | 661 | 557 | 1 | 7 | 1.2286 | +0 | +3 | **+0.0000** |
| snapshot_4 | 4.2 | 669 | 562 | 1 | 11 | 1.2182 | +0 | +4 | **+0.0000** |

### What the derivative shows

- **Phase 5.A (snapshot_1 → snapshot_2):** d(shared)/d(total) = 1/4 = **0.25**.
  The system added 4 components, 1 of which was shared. This is the
  only cycle that grew the shared-components numerator. The score
  increased by +0.05.

- **Phase 5.B (snapshot_2 → snapshot_3):** d(shared)/d(total) = 0/3 = **0.00**.
  The system added 3 components, NONE of which were shared. The
  denominator grew without the numerator. The score DECREASED by
  0.0214.

- **Phase 5.C (snapshot_3 → snapshot_4):** d(shared)/d(total) = 0/4 = **0.00**.
  Same pattern as Phase 5.B. The score DECREASED by 0.0104.

### The saturation point

The derivative has been **0.00 for two consecutive cycles**. This is
the saturation point the CEO predicted: the system has stopped
producing new shared components. Each new ingestion cycle only
grows the denominator, which dilutes the ratio and decreases the
score.

**The score is not broken.** The formula is behaving exactly as
designed — it measures the RATIO of shared to total components.
When the ratio shrinks, the score shrinks. That is structurally
correct.

**The hypothesis was wrong.** The assumption behind Phases 5.B and
5.C was that more ingestion → more shared components. The
derivative shows this assumption is false under the current
parser + formula combination. Adding sources that don't extract
matching labels grows the denominator without growing the numerator.

---

## 5. What this proves, and what it does NOT prove

### What it proves

1. **Exact-label matching is the limiting factor.** The 4 potential
   matches (Section 2) and the pluralization gaps (Section 2,
   rows 5-8) are concrete examples of labels that COULD share a
   node but currently don't because the parser uses exact matching.

2. **The system has saturated.** The derivative d(shared)/d(total)
   has been 0.00 for two consecutive cycles. Further ingestion
   cycles that don't address normalization will continue to
   produce 0.00 derivatives and decrease the score.

3. **The 10 exact matches are the current signal ceiling.** These
   are the labels that ARE shared across sources. The convergence
   formula's Signal C can only grow via these 10 labels OR via
   resolving the 4 potential matches.

### What it does NOT prove

1. **It does NOT prove that semantic matching is the correct
   solution.** The CEO's directive is explicit on this point. The
   evidence supports "exact-label matching is the limiting factor."
   It does NOT support "semantic matching is the right fix."
   Those are different conclusions.

2. **It does NOT prove that the 4 potential matches SHOULD be
   merged.** Some of them are debatable:
   - `sorbent` vs `adsorbent`: are these truly the same concept,
     or are they different (adsorbent = surface capture; sorbent
     = bulk capture)? A domain expert might argue they should
     stay separate.
   - `electrode` vs `anode`/`cathode`: anode and cathode are
     SUBTYPES of electrode. Merging them would lose information
     (you'd no longer know which electrode is the anode).

3. **It does NOT authorize any parser or formula change.** The
   parser is frozen (Task 1). The formula is frozen (CONVERGENCE.md).
   This document is a measurement, not a recommendation.

---

## 6. Implementation status

| Item | Status |
|---|---|
| Parser (PatentParser + PaperParser) | FROZEN per CEO Task 1. No keyword additions, no heuristics, no stemming, no embeddings, no synonym engines. |
| NORMALIZATION_GAP.md (this file) | COMPLETE — Task 2 |
| bridgeable_shared_components metric | COMPLETE — Task 3 (10 exact / 4 potential / 126 unmatched) |
| Saturation analysis | COMPLETE — Task 4 (derivative is 0.00 for last 2 cycles) |
| Convergence module | FORBIDDEN per CONVERGENCE.md. Not created. |
| Semantic matching | FORBIDDEN per CEO's most important instruction. Not created. |
| Phase 5.D status | Measurement COMPLETE. No implementation work done. No implementation work authorized. |

---

## 7. The single most important number

```
d(shared_components) / d(total_components) = 0.00
```

for two consecutive cycles. The system has saturated. The score
will not increase via more ingestion alone until the normalization
gap is addressed — but the CEO has NOT authorized addressing it.
This document measures the gap. It does not close it.
