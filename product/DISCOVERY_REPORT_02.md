# Discovery Report 02: Eddy Current Heating Bridge Between Magnetic Hyperthermia and Induction Heating

**Package ID:** DISC-002
**Date:** 2026-08-05
**Status:** RETRIEVAL, NOT DISCOVERY
**Maturity Level:** DISCOVERY

---

## 0. Purpose

This package reports the second blind discovery test by the Technology Evolution Engine. The test connected magnetic nanoparticle hyperthermia (cancer treatment) with induction heating for metal joining (manufacturing) through the shared mechanism of eddy current heating. The bridge was real but turned out to be partially published — a valid negative result.

---

## 1. The Bridge

```
alternating_magnetic_field (Literature A) → magnetic_field (shared) → electromagnetic_induction (Literature B)
```

**Literature A:** Magnetic nanoparticle hyperthermia — cancer treatment using magnetic nanoparticles heated by alternating magnetic fields via Néel relaxation and hysteresis.

**Literature B:** Induction heating for metal joining — manufacturing process using electromagnetic induction to heat metal workpieces via eddy currents for brazing and soldering.

**The bridge:** Both literatures use alternating magnetic fields to generate heat. The shared intermediate is electromagnetic induction → eddy currents → Joule heating. The system predicted that eddy current heating (the mechanism in induction brazing) could be applied to nanoparticle hyperthermia using conductive nonmagnetic nanoparticles.

---

## 2. Evidence

### Prediction (T1, locked before verification)

> The eddy current heating mechanism used in induction brazing can be applied to magnetic nanoparticle hyperthermia by designing nanoparticles that heat primarily via eddy currents rather than Néel relaxation or hysteresis. Specifically, conductive nanoparticles heated by eddy currents from an alternating magnetic field could achieve higher specific absorption rates than traditional iron oxide nanoparticles.

**Locked at:** 2026-08-05T02:53:00Z

### Verification (T2, 3 sources, Tier D)

| # | Source | Key finding | Tier |
|---|---|---|---|
| 1 | Chen 2025, ScienceDirect | "These conductive nonmagnetic materials with magnetic field responsiveness may provide new inspirations for advancing MHT" | D |
| 2 | Stigliano 2016, PMC | "Mitigation of eddy current heating during magnetic nanoparticle hyperthermia" — treats eddy currents as a side effect | D |
| 3 | 2005, AACR | "High-amplitude AMF causes nonspecific heating in tissues through induced eddy currents" | D |

**T1 vs T2: PARTIAL PASS.** The concept exists in the literature (Chen 2025) but is framed differently — as an emerging approach, not a mainstream therapy. Eddy currents are primarily treated as a side effect to mitigate (Stigliano 2016).

---

## 3. Outcome

**OUTCOME 2: RETRIEVAL, NOT DISCOVERY.** The bridge is real and cross-literature (induction heating → eddy current → nanoparticle hyperthermia), but the specific application has been noted by at least one source (Chen 2025). The system did not discover something unknown; it retrieved a connection that exists but is not widely cited by either community.

This is a valid, useful, negative result. The system found a real connection between two literatures that don't cite each other, but the connection is not genuinely novel — it exists in the broader literature.

---

## 4. Method

### Step 1: Literature selection
- Literature A: Magnetic nanoparticle hyperthermia (cancer treatment via magnetic heating)
- Literature B: Induction heating for metal joining (manufacturing via electromagnetic heating)
- Candidate bridge: eddy current heating / electromagnetic induction

### Step 2: Ingestion and extraction
- 20 papers fetched (10 per literature) via z-ai web_search
- LLM-guided open-domain extraction (the regex extractor cannot handle these domains)
- Literature A: 16 entities, 20 edges
- Literature B: 16 entities, 20 edges
- Shared intermediates: 5 entities (Joule heating, eddy current heating, electromagnetic heating, magnetic field, alternating current)
- Combined graph: 37 nodes, 40 edges

### Step 3: Discovery algorithms
- **Swanson bridges:** 15 total, 2 cross-literature
  - Top bridge: alternating_magnetic_field (A) → magnetic_field (shared) → electromagnetic_induction (B)
  - Score: 0.6
  - A→C absent from both source literatures — genuine Swanson bridge
- **Gentner analogies:** 2,755 total, 10 cross-literature
  - Structural parallels between magnetic_nanoparticles → magnetic_hyperthermia and induction_coil → electromagnetic_induction
- **Altshuller contradictions:** 0
- **BACON:** No applicable formula in this domain

### Step 4: Independent verification
- Searched for "conductive nanoparticles eddy current heating cancer therapy"
- Found Chen 2025 mentioning conductive nonmagnetic materials for MHT
- Found Stigliano 2016 discussing eddy current heating as a side effect to mitigate
- T1 is partially confirmed but not genuinely novel

### Step 5: Report
- OUTCOME 2: RETRIEVAL, NOT DISCOVERY
- The bridge exists in the literature but is not widely cited by either community
- The system found a real connection but did not discover something unknown

---

## 5. Significance

This is a valid negative result. The system found a real cross-literature bridge (eddy current heating connecting magnetic hyperthermia to induction heating), but the bridge is not genuinely novel — at least one source (Chen 2025) notes the concept. The system's contribution is identifying the bridge from the two source literatures alone, without being told about Chen 2025.

The difference between OUTCOME 1 (NOVEL HIT) and OUTCOME 2 (RETRIEVAL) is subtle: in both cases, the system found a connection between two literatures. In OUTCOME 1, the connection was unknown. In OUTCOME 2, the connection was partially known but not widely cited. The system's discovery process works either way — it found the bridge from the two source literatures alone.

---

## 6. Limitations

1. The prediction is binary (eddy current heating for cancer therapy: yes/no). A quantitative prediction would be stronger.
2. The extraction was LLM-guided, not automated. The extraction quality depends on the LLM's reading comprehension.
3. The bridge is real but not novel — Chen 2025 mentions conductive nonmagnetic materials for MHT. The system did not discover something unknown.
4. The Altshuller contradiction search found 0 contradictions — the two literatures don't have conflicting requirements in the extracted graph.

---

## 7. Comparison with Discovery 01

| Metric | Discovery 01 (mycelium/CaCO3) | Discovery 02 (eddy current/hyperthermia) |
|---|---|---|
| Outcome | NOVEL HIT | RETRIEVAL |
| Bridge novel? | Yes (5 sources confirm, neither source literature mentions it) | Partially (1 source mentions it as emerging) |
| Cross-literature? | Yes (mycelium composites ↔ self-healing concrete) | Yes (magnetic hyperthermia ↔ induction heating) |
| Prediction confirmed? | Yes (5 sources) | Partially (1 source, framed differently) |
| Extraction method | LLM-guided | LLM-guided |

Discovery 01 was a NOVEL HIT. Discovery 02 is a RETRIEVAL. Both are valid results from the blind discovery test process.

---

## 8. Final Verdict

**RETRIEVAL, NOT DISCOVERY.** The system found a real cross-literature bridge (eddy current heating connecting magnetic hyperthermia to induction heating), but the bridge is partially published (Chen 2025). The system's contribution is identifying the bridge from the two source literatures alone — a valid Swanson-type retrieval, but not a novel discovery.

The PDF mandate is fulfilled. The cycle is complete.
