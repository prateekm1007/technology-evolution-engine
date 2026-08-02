# CLASSIFICATION_COVERAGE — Phase 7B

**Status:** coverage definition (to be populated during ingestion).
**Phase:** 7B.

This document will track how much of the 50-patent corpus is
covered by CPC/IPC codes, and how many capabilities each patent
provides evidence for.

---

## 1. Coverage metrics (to be filled during ingestion)

| Metric | Target | Actual (pending) |
|---|---:|---:|
| Patents with CPC codes | 50/50 (100%) | — |
| Patents with IPC codes | 50/50 (100%) | — |
| Patents with both CPC and IPC | ≥40/50 (≥80%) | — |
| CPC codes per patent (avg) | ≥2 | — |
| Capabilities evidenced per patent (avg) | ≥2 | — |
| Patents evidencing ≥3 capabilities | ≥25/50 (50%) | — |

### Why these targets

- **100% CPC/IPC coverage:** every patent in the corpus should
  have classification codes. If a patent has no CPC/IPC, it was
  selected incorrectly or the data is incomplete.
- **≥2 codes per patent:** most battery patents span multiple CPC
  subclasses (e.g., electrode + electrolyte + assembly). Two codes
  is the minimum for meaningful capability mapping.
- **≥2 capabilities per patent:** a patent that evidences only one
  capability is a narrow refinement. A patent that evidences 2+
  capabilities is a combinatorial event — exactly what the
  CAPABILITY_MODEL is designed to capture.
- **≥50% patents with ≥3 capabilities:** the system's value is in
  finding combinatorial patterns. If most patents only evidence
  one capability, the combinatorial signal is too sparse.

---

## 2. Coverage gap analysis (to be filled during ingestion)

| Gap type | Count (pending) | Mitigation |
|---|---:|---|
| Patents with no CPC code | — | Fall back to IPC; if neither, exclude from corpus |
| Patents whose CPC code doesn't map to any capability | — | Record as unmapped; investigate |
| Capabilities with 0 evidence (not mentioned by any patent) | — | Investigate; may need capability redefinition |
| CPC codes not in H01M (out-of-scope) | — | Exclude; confirms scope restriction |

---

## 3. What this document does NOT do

- It does NOT contain the actual coverage data (ingestion not yet
  executed).
- It does NOT evaluate the quality of CPC mapping (that's Phase 7D
  validation).
- It establishes the METRICS that will be measured during ingestion,
  so the ingestion process knows what to track.
