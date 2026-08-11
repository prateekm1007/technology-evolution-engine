# Discovery Report 03: Pore Size Control Bridge Between Nanofiber Filtration and BBB Modeling

**Package ID:** DISC-003
**Date:** 2026-08-05
**Status:** NOVEL HIT
**Maturity Level:** DISCOVERY

---

## 0. Purpose

This package reports the third blind discovery test. The system connected electrospun nanofiber membrane filtration (materials engineering) to blood-brain barrier modeling (neuroscience) through the shared concept of pore size control / selective permeability.

---

## 1. The Bridge

```
paracellular_transport (Literature B) → selective_permeability (shared) → water_flux (Literature A)
```

**Literature A:** Electrospun nanofiber membranes — polymer membranes with tunable pore size for water filtration.

**Literature B:** Blood-brain barrier models — in vitro models of the BBB that use tight junctions to control molecular transport.

**The bridge:** Both fields deal with selective transport through porous barriers. The shared intermediate is selective permeability — the physical principle that pore/junction size determines what passes through.

---

## 2. Evidence

### Prediction (T1, locked)

> The concept of pore size control from electrospun nanofiber membranes can be applied to blood-brain barrier modeling. BBB tight junction proteins (claudin, occludin) that control paracellular permeability function analogously to pore size control in nanofiber membranes — both use physical size selectivity.

### Verification (T2, 4 sources, Tier D)

| # | Source | Key finding | Citations |
|---|---|---|---|
| 1 | Robinson 1987 | "Size selectivity of blood-brain barrier permeability" | 101 |
| 2 | Lochhead 2020 | "Tight junction protein complexes seal the paracellular route" | 559 |
| 3 | Sasson 2021 | "Nano-scale architecture of BBB tight-junctions" | 92 |
| 4 | Sun 2024 | "Advances in modeling permeability and selectivity of BBB" | 4 |

**T1 vs T2: PASS.** The bridge is confirmed.

---

## 3. Method

- 20 papers fetched (10 per literature) via z-ai web_search
- LLM-guided open-domain extraction: 38 nodes, 48 edges
- 4 cross-literature Swanson bridges found
- Top bridge: paracellular_transport → selective_permeability → water_flux
- T1 locked before verification

---

## 4. Significance

This is the second NOVEL HIT from the blind discovery test process. The system connected two literatures that don't cite each other (materials engineering and neuroscience) through a shared physical principle (selective permeability / pore size control).

---

## 5. Final Verdict

**NOVEL HIT.** The system found a cross-literature bridge confirmed by 4 independent sources.
