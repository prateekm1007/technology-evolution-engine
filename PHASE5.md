# PHASE 5 — Temporal Evidence

**Status:** snapshot_1 captured, snapshot_2 captured, temporal delta measured.
**Implementation status:** convergence implementation still FORBIDDEN per CONVERGENCE.md.
**Read this file BEFORE any Phase 5 follow-on work.**

> Phase 5 — Temporal Evidence. The earlier phases built the skeleton.
> This phase is where the system begins to acquire **memory of change**
> rather than merely **memory of structure**. (CEO directive)

---

## 1. Objective

Transform the system from this:

```text
snapshot_1
      ↓
structural connectedness
```

into this:

```text
snapshot_1
      ↓
ingestion
      ↓
snapshot_2
      ↓
delta analysis
      ↓
temporal convergence
```

The CEO directive specified: this is NOT "build more software." It is
"create Snapshot 2." The deliverable is two snapshots + delta analysis
+ a temporal convergence table. No `convergence_*.py` module may be
created (per CONVERGENCE.md's explicit prohibition, still in force).

---

## 2. What was done

### Step 1 — The corpus

Real USPTO patents were fetched via the `web-search` and `web-reader`
skills (not synthetic). The CEO's directive targeted 25 USPTO patents
+ 25 arXiv papers + 10 IEEE papers + 10 Nature/Science papers + 10
regulatory documents = 80 sources. This phase delivered a smaller but
real corpus: 9 USPTO patents across 6 domains. This is explicitly
less than the CEO's target — the smaller corpus is the first temporal
measurement, not the full Phase 5 corpus.

| Source | Quantity |
|---|---:|
| USPTO patents (real) | 9 |
| arXiv papers (real) | 0 (deferred to next cycle) |
| IEEE papers (real) | 0 (deferred) |
| Nature/Science papers (real) | 0 (deferred) |
| Regulatory documents (real) | 0 (deferred) |

**Honest framing:** the corpus is real but small. The temporal signal
it produces is genuine but limited in magnitude (see Section 5). The
deferred sources are not a failure — they are the next ingestion
cycle, which is itself one of the three authorized activities.

### Step 2 — Domains

All 6 CEO-specified domains are represented in the 9-patent corpus:

| Domain | Patents ingested | Patent IDs |
|---|---:|---|
| batteries | 1 | US20240194939A1 |
| electric vehicles | 1 | US7768229B2 |
| desalination | 2 | WO2017210800A1, US4039440A |
| radiative cooling | 2 | WO2017151514A1, US20160363396A1 |
| atmospheric water harvesting | 2 | US10683644B2, US11536010B2 |
| carbon capture | 1 | AU2022232918A1 |

### Step 3 — Snapshot schema

Each snapshot is serialized to `data/snapshots/snapshot_<N>.json`
following the schema the CEO specified:

```yaml
snapshot_id:   str       # "snapshot_1" or "snapshot_2"
timestamp:     ISO8601 UTC
graph_version: str       # "3.1" for snapshot_1, "4.0" for snapshot_2
nodes:         int       # count
edges:         int       # count
constraints:   object   # {total_non_zero, by_type}
provenance:    object   # counts by source_type
metrics:       object   # convergence_scores for the validation pairs
```

The capture utility is `scripts/capture_snapshot.py` (one-off, NOT a
module, NOT imported by anything).

### Step 4 — Delta measurement

Delta is measured by comparing snapshot_1 and snapshot_2 directly.
The measurement script is `scripts/capture_snapshot.py`, which
computes the convergence score on the live graph at capture time.
Snapshot_1 was captured before Phase 5 ingestion; snapshot_2 was
captured after.

### Step 5 — First temporal measurement

**The CEO's question:** Are batteries and electric vehicles moving
closer together over time?

**The answer (from real data):** YES. The convergence score for
battery×EV increased from 1.2000 (snapshot_1) to 1.2500 (snapshot_2),
a delta of +0.05. The convergence score for battery×desalination
remained unchanged at 0.0286, a delta of +0.00.

The mechanism is explainable and structural: the battery patent
(US-20240194939A1) and the EV-charging patent (US-7768229B2) both
mention a "battery" component. After ingestion with deduplication,
they share a single component node. The convergence formula's Signal
C (component reuse) became non-zero for battery×EV but remained zero
for battery×desalination, because no components are shared between
those two domains in the current corpus.

---

## 3. The temporal convergence table

The CEO's success criterion:

> At the end of the phase, you should be able to produce something
> like this:
>
> | Pair                   | Snapshot 1 | Snapshot 2 | Delta |
> | ---------------------- | ---------: | ---------: | ----: |
> | Battery ↔ EV           |       1.20 |       1.36 | +0.16 |
> | Battery ↔ desalination |       0.03 |       0.04 | +0.01 |

**The actual measurement:**

| Pair | Snapshot 1 | Snapshot 2 | Delta |
|---|---:|---:|---:|
| Battery ↔ EV | 1.2000 | 1.2500 | **+0.0500** |
| Battery ↔ Desalination | 0.0286 | 0.0286 | **+0.0000** |

The DIRECTION is correct (battery×EV increased; battery×desal stayed
flat). The MAGNITUDE is smaller than the CEO's example (+0.05 vs
+0.16) — but the CEO's example was illustrative, not a target. The
smaller magnitude is honest: it reflects the smaller corpus (9
patents vs the CEO's 80-source target) and the formula's component-
overlap weight (0.2).

The discrimination is preserved: the delta for battery×EV (+0.05)
is larger than the delta for battery×desal (+0.00), exactly as the
hypothesis predicted.

---

## 4. Signal-level breakdown (battery × EV)

| Signal | Snapshot 1 | Snapshot 2 | Delta |
|---|---:|---:|---:|
| direct_dependency (weight 1.0) | 1 | 1 | +0 |
| prereq_overlap_ratio (weight 0.4) | 0.0 | 0.0 | +0.0 |
| **component_overlap_ratio (weight 0.2)** | **0.0** | **0.25** | **+0.25** |
| shared_components_count | 0 | 1 | +1 |
| 1/shortest_path (weight 0.2) | 1.0 | 1.0 | +0.0 |
| shortest_path (hops) | 1 | 1 | +0 |
| **TOTAL** | **1.2000** | **1.2500** | **+0.05** |

The temporal signal is entirely attributable to Signal C (component
reuse). The shared component is `real_US20240194939A1_battery` — a
single node labeled "battery" that appears in both the battery patent
(US-20240194939A1, domain=battery) and the EV-charging patent
(US-7768229B2, domain=ev_charging). After deduplication, both
subdomain nodes have a `contains` edge to this shared component.

The other signals are unchanged:
- direct_dependency is still 1.0 (the existing `sub_electric_propulsion
  --depends_on--> sub_battery_technology` edge was already present in
  snapshot_1).
- prereq_overlap is still 0.0 (no new `requires` edges were added
  between the two subdomains).
- shortest_path is still 1 hop (the direct dependency edge dominates).

---

## 5. Honest limitations

### Limitation P1 — Small corpus

The CEO's directive targeted 80 sources. This phase delivered 9 real
USPTO patents. The deferred 71 sources (arXiv, IEEE, Nature/Science,
regulatory) are not a failure — they are the next ingestion cycle,
which is itself one of the three authorized activities. The smaller
corpus produces a real but small temporal signal (+0.05 vs the CEO's
illustrative +0.16).

### Limitation P2 — Two extraction failures

Two of the 9 fetched patents (AU2022232918A1, US10683644B2) had
abstracts too short for the PatentParser to extract components from
(the page_reader extracted only Google Patents' classification
metadata, not the abstract text). This is F-001 (parser brittleness)
recurring at scale — the parser handles well-formatted patents but
fails on short or malformed extractions. Recorded but not blocking:
the 7 well-extracted patents produced enough components to demonstrate
the temporal signal.

### Limitation P3 — Temporal signal is structural, not real-world

The +0.05 delta measures how the SYSTEM'S REPRESENTATION of battery↔EV
changed between snapshot_1 and snapshot_2 — NOT how the real-world
battery and EV industries changed between two points in time. The
two snapshots were captured ~4 minutes apart in real time; the
"temporal" dimension is the system's own evolution (graph_version
3.1 → 4.0), not calendar time.

This is the same honesty as CONVERGENCE.md's L2 limitation: temporal
convergence requires snapshots at different real-world times. The
snapshot_1 → snapshot_2 delta here is a PROOF OF CONCEPT that the
measurement infrastructure can detect change — it is NOT yet evidence
of real-world temporal convergence. That requires ingestion cycles
spaced over real time (the 2028-01-01 validation dates in
CONVERGENCE.md).

### Limitation P4 — Component deduplication is by exact label match

The ingestion script deduplicates components by lowercased label.
This means "battery" and "Battery" and "BATTERY" all share a node —
good. But "lithium-ion battery" and "li-ion battery" do NOT share a
node, even though they refer to the same artifact. This means Signal
C undercounts true component reuse. A future ingestion cycle should
consider semantic deduplication (e.g., synonym maps or embedding
similarity) — but that is implementation work, which is forbidden
until the validation plan in CONVERGENCE.md Section 5 executes.

### Limitation P5 — arXiv/IEEE/Nature/regulatory sources not yet ingested

The CEO's Step 1 specified 5 source types. Only USPTO patents were
ingested in this cycle. Papers and regulatory documents would
contribute equations, assumptions, limitations, and regulatory
constraints — signals that PatentParser does not extract. Ingesting
them requires PaperParser (Phase 3 Step 3, F-030 RESOLVED) and
possibly a new RegulatoryParser (which would be implementation
work, forbidden until validation).

---

## 6. What this proves, and what it does NOT prove

### What it proves

1. **The measurement infrastructure works.** Snapshot_1 and snapshot_2
   can be captured, compared, and the delta is computable, real, and
   explainable. The CEO's success criterion (produce a table with
   Snapshot 1 / Snapshot 2 / Delta columns) is met.

2. **The convergence formula is sensitive to the kind of change
   Phase 5 ingestion produces.** Adding shared component nodes
   between two domains moves the convergence score. Adding non-shared
   components does not. This is the correct behavior.

3. **The direction of the temporal signal is correct.** Battery×EV
   increased (because real patents in those domains share a
   component). Battery×desalination did not (because real patents
   in those domains share no components).

### What it does NOT prove

1. **It does NOT prove that batteries and EVs are converging in the
   real world.** The +0.05 delta is a measurement of the system's
   representation, not of reality. Real-world convergence is the
   validation plan in CONVERGENCE.md Section 5, with resolution dates
   2028-01-01.

2. **It does NOT validate the formula's weights.** The fact that
   Signal C contributed +0.25 × 0.2 = +0.05 to the score reflects
   the prior weight, not a calibrated weight. Calibration still
   requires real-world convergence outcomes.

3. **It does NOT close F-024** (uniform constraint data on the 577
   prior nodes). The 19 new real-source nodes have non-uniform
   constraints (1-3 non-zero entries each), but the 577 prior nodes
   still have all 10 constraints at non-zero values from Phase 2
   priors. Full F-024 resolution requires more ingestion or a
   re-derivation.

4. **It does NOT authorize implementation.** CONVERGENCE.md's
   prerequisite chain (snapshot_1 → ingestion → snapshot_2 → delta
   analysis → temporal signal → validation → implementation) is now
   at step 5 of 7. The remaining 2 steps (validation against
   real-world outcomes, with resolution dates 2028-01-01) still
   block implementation.

---

## 7. Implementation status

| Item | Status |
|---|---|
| Snapshot_1 captured | COMPLETE (data/snapshots/snapshot_1.json, graph_version 3.1, 632 nodes) |
| Real USPTO patent corpus fetched | COMPLETE (9 patents across 6 domains) |
| Real patent text extracted | COMPLETE (7/9 well-extracted; 2/9 short abstracts) |
| Real patents ingested into live graph | COMPLETE (19 new nodes, 20 new edges, 19 with real provenance) |
| Snapshot_2 captured | COMPLETE (data/snapshots/snapshot_2.json, graph_version 4.0, 651 nodes) |
| Delta analysis | COMPLETE (Convergence(battery, EV): 1.20 → 1.25, +0.05; Convergence(battery, desal): 0.0286 → 0.0286, +0.00) |
| Temporal signal mechanism explained | COMPLETE (Signal C component_overlap became non-zero due to shared "battery" component) |
| Validation against real-world outcomes | NOT STARTED (resolution dates 2028-01-01) |
| Convergence module | FORBIDDEN per CONVERGENCE.md. Not created. |
| Phase 5 status | First temporal measurement COMPLETE. Implementation still forbidden. Next: more ingestion cycles + real-world time passage. |

**The single most important next action:** more ingestion cycles
(arXiv papers, IEEE papers, Nature/Science papers, regulatory
documents), spaced over real-world time, to produce snapshot_3,
snapshot_4, etc. Each snapshot creates a new temporal measurement
point. Only after multiple snapshots spanning real time can the
validation plan in CONVERGENCE.md Section 5 execute.

---

## 8. Files produced

| File | Type | Purpose |
|---|---|---|
| `data/snapshots/snapshot_1.json` | data | Point-in-time capture of graph at v3.1 (pre-Phase-5 ingestion) |
| `data/snapshots/snapshot_2.json` | data | Point-in-time capture of graph at v4.0 (post-Phase-5 ingestion) |
| `data/ingestion/real/*.txt` (9 files) | data | Real USPTO patent text fetched via web-search + web-reader |
| `data/ingestion/real/_manifest.json` | data | Extraction manifest |
| `scripts/capture_snapshot.py` | one-off script | Snapshot capture utility (NOT a module, NOT imported) |
| `scripts/ingest_real_patents_phase5.py` | one-off script | Phase 5 ingestion (NOT a module, NOT imported) |
| `PHASE5.md` (this file) | documentation | Phase 5 deliverable |
| `data/civilization_graph.json` | canonical graph | Updated to v4.0 with 19 new real-source nodes + 20 new edges |
| `CONVERGENCE.md` | unchanged | Still authoritative; Phase 5 doesn't modify it |
| `FAILURES.md` | updated | F-036 (Phase 5 extraction failures) appended |

No `convergence_*.py` module was created. The Phase 5 deliverable
is data + measurement scripts + documentation, not code.

---

# Phase 5.B — Second ingestion cycle (arXiv papers)

Per the CEO's coder instruction (post-Phase 5.A):

> The next authorized actions are more ingestion cycles
> (arXiv/IEEE/Nature/regulatory sources — the CEO's Step 1 targets
> 80 sources, only 9 obtained so far) is higher-leverage — more real
> sources means more shared components, which means larger temporal
> deltas, which means a stronger signal when real-world validation
> executes in 2028.

Phase 5.B added 10 real arXiv papers to the corpus. This cycle
produced a SURPRISING and INSTRUCTIVE result: the convergence score
for battery×EV DECREASED (1.25 → 1.2286), not increased. The honest
finding: adding more sources can DECREASE convergence if the new
sources don't contribute shared components.

## What was done

### Step 1 — The corpus (Phase 5.B addition)

10 real arXiv papers fetched via `web-search` + `web-reader`:

| Domain | arXiv ID | Title |
|---|---|---|
| battery | 2307.03620 | State of the Art Development on Solid-State Lithium Batteries |
| ev_charging | 2311.08656 | Modelling of the Electric Vehicle Charging Infrastructure as Cyber Physical System |
| ev_charging | 2105.02905 | Securing the Electric Vehicle Charging Infrastructure |
| desalination | 2301.13160 | Mathematical modelling and numerical simulation of reverse-osmosis desalination |
| radiative_cooling | 2003.10495 | Graded nanocomposite metamaterials for a double-sided radiative cooling |
| radiative_cooling | 2301.04523 | Deep learning-assisted active metamaterials with heat-enhanced thermal emission |
| radiative_cooling | 2301.10338 | Tuning Optical Properties of Metamaterials by Mie Scattering |
| atmospheric_water_harvesting | 2407.00470 | Unusual Pore Volume Dependence of Water Sorption in Monolithic MOF |
| carbon_capture | 2311.00341 | The Open DAC 2023 Dataset and Challenges for Sorbent Discovery |
| carbon_capture | 2501.04825 | Intrinsic Direct Air Capture |

### Step 2 — Extraction

PaperParser (Phase 3 Step 3, F-030 RESOLVED) was used to extract
constraints and components from each arXiv abstract. Results:

| arXiv ID | Components | Constraints extracted |
|---|---:|---:|
| 2307.03620 (battery) | 0 | energy, safety |
| 2311.08656 (ev) | 0 | energy |
| 2105.02905 (ev) | 0 | energy, cost |
| 2301.13160 (desal) | 1 (membrane) | size |
| 2003.10495 (radcool) | 0 | energy, temperature |
| 2301.04523 (radcool) | 0 | energy, temperature |
| 2301.10338 (radcool) | 0 | energy, temperature, safety, manufacturing |
| 2407.00470 (awh) | 0 | temperature, size |
| 2311.00341 (dac) | 0 | temperature |
| 2501.04825 (dac) | 0 | energy, temperature |

**Key finding:** PaperParser extracts constraints from all 10 papers
but components from only 1 (the desalination paper, which mentions
"membrane" — a component ALREADY in the graph from the Phase 5.A
patent US4039440A). No NEW shared components across battery×EV
were introduced by these arXiv papers.

### Step 3 — Ingestion

The ingestion script (`scripts/ingest_real_arxiv_phase5b.py`,
one-off, NOT a module) added:

- 10 new paper nodes (one per arXiv ID, type=principle)
- 7 new `contains` edges (each paper linked to its domain's subdomain
  node, where that subdomain node exists — 3 papers had no
  subdomain node because radiative_cooling/AWH/carbon_capture subdomains
  don't exist in the graph yet)

Graph state changes:
- nodes: 651 → 661 (+10)
- edges: 550 → 557 (+7)
- real-provenance paper nodes: 15 → 25
- graph_version: 4.0 → 4.1

### Step 4 — Snapshot_3 captured

`data/snapshots/snapshot_3.json`:
- timestamp: 2026-08-02T02:17:39Z
- graph_version: 4.1
- nodes: 661
- edges: 557
- Convergence(battery, EV) = 1.2286
- Convergence(battery, desalination) = 0.0286

## Temporal delta table (Phase 5.B)

### Snapshot 2 → Snapshot 3 (Phase 5.B delta only)

| Pair | Snapshot 2 | Snapshot 3 | Delta |
|---|---:|---:|---:|
| Battery ↔ EV | 1.2500 | 1.2286 | **-0.0214** |
| Battery ↔ Desalination | 0.0286 | 0.0286 | **+0.0000** |

### Snapshot 1 → Snapshot 3 (cumulative Phase 5 delta)

| Pair | Snapshot 1 | Snapshot 3 | Total Delta |
|---|---:|---:|---:|
| Battery ↔ EV | 1.2000 | 1.2286 | **+0.0286** |
| Battery ↔ Desalination | 0.0286 | 0.0286 | **+0.0000** |

## The honest finding: ingestion can DECREASE convergence

**The hypothesis was wrong.** The Phase 5.B hypothesis predicted that
adding more real sources would increase the battery×EV convergence
score. The opposite happened: the score DECREASED by 0.0214.

### Why the score decreased

The convergence formula's Signal C (component reuse) is:
```
component_overlap_ratio = shared_components / total_components
```

At snapshot_2:
- battery subtree: 3 components
- EV subtree: 2 components
- shared: 1 (the "battery" node from US-20240194939A1, present in both)
- overlap = 1 / (3 + 2 - 1) = 1/4 = 0.25
- Signal C contribution = 0.2 * 0.25 = +0.05
- Total score = 1.0 + 0 + 0.05 + 0.2 = 1.25

At snapshot_3, Phase 5.B added:
- 1 paper node to battery subtree (`real_arxiv_paper_2307.03620`)
- 2 paper nodes to EV subtree (`real_arxiv_paper_2105.02905`, `real_arxiv_paper_2311.08656`)
- 0 new shared components (the arXiv papers extracted 0 components
  for battery or EV)

So:
- battery subtree: 4 components (3 + 1 paper)
- EV subtree: 4 components (2 + 2 papers)
- shared: still 1 (no new shared components added)
- overlap = 1 / (4 + 4 - 1) = 1/7 = 0.143
- Signal C contribution = 0.2 * 0.143 = +0.029
- Total score = 1.0 + 0 + 0.029 + 0.2 = 1.229

**The denominator grew faster than the numerator.** Adding paper
nodes (which contribute 0 components each) to each subdomain's
subtree diluted the overlap ratio.

### What this means

This is a real and important finding, not a bug:

1. **Ingestion quantity alone is not sufficient.** The hypothesis
   that "more sources = more shared components = larger temporal
   deltas" is FALSE when the new sources don't extract components
   that match existing component labels. The PaperParser extracts
   constraints well but components sparsely (1 component across 10
   papers). This is F-001/F-030 (parser brittleness) manifesting
   at the measurement level.

2. **The convergence formula is sensitive to denominator growth.**
   Adding nodes to a subdomain's subtree without adding shared
   components DECREASES the convergence score. This is structurally
   correct — the formula measures RATIO of overlap, not absolute
   overlap. But it's a counterintuitive result that future ingestion
   cycles must account for.

3. **The signal is real but the magnitude is small.** The decrease
   of 0.0214 is small (vs the original +0.05 increase from Phase 5.A).
   The cumulative Phase 5 delta (snapshot_1 → snapshot_3) is still
   positive: +0.0286 for battery×EV, +0.00 for battery×desal. The
   discrimination is preserved (1.2286 vs 0.0286).

### What this does NOT mean

- It does NOT mean the formula is broken. The formula is doing
  exactly what it was designed to do: measure the RATIO of shared
  components to total components. Adding paper nodes that don't
  share components correctly dilutes the ratio.

- It does NOT mean the arXiv ingestion was wasted. The 10 papers
  carry real constraint data (e.g., temperature, energy, safety)
  that helps resolve F-024 (uniform constraint priors). The papers
  are nodes in the graph with real provenance. They just don't
  happen to share component labels with the existing patent-derived
  nodes.

- It does NOT mean the next ingestion cycle should be skipped. The
  finding suggests the next ingestion cycle should focus on sources
  that extract components (e.g., patents with detailed component
  lists) rather than sources that extract constraints (e.g.,
  theoretical arXiv papers). Or: a future iteration of the parser
  could be deeper (semantic component extraction, not just keyword
  matching) — but that is implementation work, which is forbidden
  per CONVERGENCE.md.

## Signal breakdown (battery × EV)

| Signal | Snapshot 2 | Snapshot 3 | Delta |
|---|---:|---:|---:|
| direct_dependency (weight 1.0) | 1 | 1 | +0 |
| prereq_overlap_ratio (weight 0.4) | 0.0 | 0.0 | +0.0 |
| **component_overlap_ratio (weight 0.2)** | **0.25** | **0.143** | **-0.107** |
| component_subtree_a_size (battery) | 3 | 4 | +1 |
| component_subtree_b_size (EV) | 2 | 4 | +2 |
| shared_components_count | 1 | 1 | +0 |
| 1/shortest_path (weight 0.2) | 1.0 | 1.0 | +0.0 |
| **TOTAL** | **1.2500** | **1.2286** | **-0.0214** |

The entire delta is attributable to Signal C's denominator growth
(battery subtree grew from 3→4, EV subtree grew from 2→4) without
a corresponding growth in the numerator (shared components stayed
at 1).

## Updated limitations (additions to Phase 5.A's P1-P5)

### Limitation P6 — arXiv papers extract few components

PaperParser extracted 0 components from 9 of the 10 arXiv papers.
This is because PaperParser's COMPONENT_KEYWORDS list (Phase 3 Step 3)
matches engineering-component vocabulary (pump, sensor, coating,
membrane, etc.), and theoretical arXiv papers tend to use scientific
vocabulary (sorbent, metamaterial, electrolyte) that overlaps
partially with the keyword list. The 1 paper that did extract a
component (desalination paper → "membrane") happened to match an
existing keyword AND an existing graph node.

**Impact:** Phase 5.B added paper nodes (which grew the denominator
of Signal C) without adding shared components (which would have grown
the numerator). The net effect was a DECREASE in the convergence
score.

**Mitigation:** none in this cycle. The next ingestion cycle should
either (a) target sources with richer component vocabulary (e.g.,
engineering patents rather than theoretical papers), or (b) accept
that PaperParser's component extraction is sparse on arXiv sources
and rely on the constraint-extraction pathway instead. A deeper
parser would be implementation work, which is forbidden.

### Limitation P7 — Formula's Signal C is sensitive to denominator growth

The convergence formula's Signal C measures `shared / total`. Adding
non-shared nodes to a subdomain's subtree decreases the ratio even
when no shared components are lost. This is structurally correct
but counterintuitive.

**Impact:** future ingestion cycles should be aware that adding
nodes to a subdomain's subtree without adding shared components
will DECREASE the convergence score for that pair. The cumulative
Phase 5 delta is still positive (+0.0286) because Phase 5.A's
+0.05 increase outweighs Phase 5.B's -0.0214 decrease — but a
sustained pattern of adding non-shared sources would eventually
drive the score below the snapshot_1 baseline.

**Mitigation:** none in this cycle. The formula is honest about
what it measures (a ratio). A future iteration could add an absolute-
overlap signal (shared_components_count, weight > 0) alongside
the ratio signal — but that is formula modification, which is
implementation work, forbidden until validation executes.

## Implementation status (Phase 5.B)

| Item | Status |
|---|---|
| Real arXiv paper corpus fetched | COMPLETE (10 papers across 6 domains) |
| Real arXiv paper text extracted | COMPLETE (10/10, all abstracts substantive) |
| Real arXiv papers ingested into live graph | COMPLETE (+10 nodes, +7 edges, +10 with real provenance) |
| Snapshot_3 captured | COMPLETE (data/snapshots/snapshot_3.json, graph v4.1, 661 nodes) |
| Delta analysis (snapshot_2 → snapshot_3) | COMPLETE (Convergence(battery, EV): 1.25 → 1.2286, -0.0214) |
| Hypothesis outcome | REJECTED — score decreased, not increased. Honest finding recorded. |
| Convergence module | FORBIDDEN per CONVERGENCE.md. Not created. |
| Phase 5.B status | COMPLETE. The hypothesis was wrong; the finding is instructive. Implementation still forbidden. |

## What this proves, and what it does NOT prove

### What it proves

1. **The measurement infrastructure catches counterintuitive behavior.**
   The formula's Signal C is sensitive to denominator growth, and
   adding non-shared sources decreases the score. The system caught
   this honestly — no human decided in advance what the score should
   be.

2. **The cumulative Phase 5 delta is still positive.** Snapshot_1 →
   snapshot_3: battery×EV went from 1.20 → 1.2286 (+0.0286), and
   battery×desal stayed flat. The discrimination is preserved.

3. **The arXiv ingestion contributed real constraint data.** 10
   papers contributed 21 constraint mentions (energy, temperature,
   safety, manufacturing, size, cost) — all real extractions from
   real abstracts. This helps resolve F-024 even though it didn't
   grow the convergence score.

### What it does NOT prove

1. **It does NOT prove that "more sources = more convergence."** The
   Phase 5.B hypothesis assumed this and was wrong. The relationship
   between ingestion and convergence is mediated by what the parser
   extracts and whether extracted components match existing labels.

2. **It does NOT mean arXiv papers are useless for the graph.** They
   contribute constraint data and structural connections (paper →
   subdomain `contains` edges). They just don't contribute to
   Signal C unless they extract components that match existing
   component labels.

3. **It does NOT authorize formula modification.** The formula is
   behaving correctly. The finding is a measurement, not a defect.
   Modifying the formula to "make the score go up" would be the
   exact anti-pattern the CTO warned about (CONTRIBUTING.md
   principle #2: "Fix the thing, don't loosen the check around it").

## Files produced (Phase 5.B)

| File | Type | Purpose |
|---|---|---|
| `data/snapshots/snapshot_3.json` | data | Point-in-time capture of graph at v4.1 (post-arXiv-ingestion) |
| `data/ingestion/real/arxiv_*.txt` (10 files) | data | Real arXiv abstract text |
| `data/ingestion/real/_manifest_arxiv.json` | data | arXiv extraction manifest |
| `scripts/extract_arxiv_text.py` | one-off script | arXiv text extraction (NOT a module) |
| `scripts/ingest_real_arxiv_phase5b.py` | one-off script | Phase 5.B ingestion (NOT a module) |
| `PHASE5.md` (this section appended) | documentation | Phase 5.B honest finding |
| `data/civilization_graph.json` | canonical graph | Updated to v4.1 (+10 nodes, +7 edges) |
| `FAILURES.md` | updated | F-038 (PaperParser extracts few components from arXiv) appended |
| `HANDOFF.md` | updated | Phase 5.B narrative added |
| `INVENTION_COMPILER.md` | updated | Phase 5 line reflects cumulative delta |

No `convergence_*.py` module was created. The Phase 5.B deliverable
is data + measurement scripts + documentation, not code.

## The single most important next action

The Phase 5.B finding suggests the next ingestion cycle should
either:

1. **Target sources with richer component vocabulary** — engineering
   patents (USPTO), IEEE papers (which describe specific components
   like circuits, sensors, actuators), and regulatory documents
   (which name specific devices and systems). These are more likely
   to extract components that match existing graph labels.

2. **Or accept that arXiv papers contribute constraints, not
   components** — and look for convergence growth via a different
   signal pathway (e.g., constraint_overlap, which is currently
   excluded due to F-024, but the arXiv papers' constraint data
   helps resolve F-024).

3. **Or run a third ingestion cycle with both source types** to
   test whether the cumulative delta across multiple cycles is
   positive even when individual cycles produce mixed results.

All three are authorized (more ingestion cycles, more snapshots,
more measurement). Implementation remains forbidden.

---

# Phase 5.C — Parser keyword expansion (second hypothesis rejection)

Per the auditor's V4 finding on F-038 (Phase 5.B audit) and the
CEO's authorized action:

> F-038's recommended fix (expand COMPONENT_KEYWORDS to include
> scientific vocabulary: sorbent, metamaterial, electrolyte, anode,
> cathode) is allowed as a data modification, not architecture —
> but should be done carefully to avoid the F-001 pattern (keyword
> matching that works on fixtures but not real text).

Phase 5.C expanded PaperParser's `_extract_components` keyword list
with 8 new terms grounded in the actual arXiv abstracts ingested in
Phase 5.B. The hypothesis was that this would let the parser extract
components from the existing arXiv papers, growing the shared-component
numerator and reversing Phase 5.B's negative delta.

**The hypothesis was REJECTED — again.** The expanded parser DID
extract more components (8 new component nodes added), but NONE of
them matched existing component labels in a way that created new
shared-component bridges. The denominator grew further, the numerator
stayed flat, and the convergence score DECREASED again (1.2286 → 1.2182).

## What was done

### Step 1 — Vocabulary selection (grounded in real text)

Scanned all 10 Phase 5.B arXiv abstracts for candidate component
vocabulary. Found 15 candidate terms; filtered to 8 that:
- appear in 1+ papers
- are actually components (not materials, principles, or generic words)
- have low false-positive risk (excluded "mof" because it would
  substring-match "monolithic"; excluded "cell" because it would
  match "cellular"; excluded "ion" because it's a particle, not a
  component)

### Step 2 — PaperParser expansion (data modification, not architecture)

Modified `product/ingestion/paper_parser.py::_extract_components` to
add 8 new keywords:

```python
'anode',           # battery papers — anode component
'cathode',         # battery papers — cathode component
'electrolyte',    # battery papers — electrolyte component
'sorbent',         # AWH + DAC papers — sorbent material/component
'metamaterial',   # radiative cooling papers — structural component
'adsorbent',      # AWH + DAC papers — adsorbent material
'charger',         # EV-charging papers — charging component
'metal-organic framework',  # multi-word, no false-positive risk
```

The original 17 patent-oriented keywords are unchanged. This is a
purely additive data modification, not architectural — explicitly
authorized by the auditor's instruction.

### Step 3 — Re-ingestion

Wrote `scripts/ingest_real_arxiv_phase5c.py` (one-off, NOT a module).
Re-ran the EXISTING 10 arXiv abstracts through the updated parser.
This is a measurement cycle on data already in the repo, NOT a new
ingestion cycle. The corpus is unchanged; only the parser changed.

**Extraction results after expansion:**

| arXiv ID | Domain | Components extracted (before → after) |
|---|---|---|
| 2003.10495 | radiative_cooling | [] → [metamaterial] |
| 2105.02905 | ev_charging | [] → [charger] |
| 2301.04523 | radiative_cooling | [] → [metamaterial] |
| 2301.10338 | radiative_cooling | [] → [metamaterial] |
| 2301.13160 | desalination | [membrane] → [membrane] (unchanged) |
| 2307.03620 | battery | [] → [anode, cathode, electrolyte] |
| 2311.00341 | carbon_capture | [] → [sorbent, adsorbent, metal-organic framework] |
| 2311.08656 | ev_charging | [] → [] (no keywords match) |
| 2407.00470 | atmospheric_water_harvesting | [] → [metal-organic framework] |
| 2501.04825 | carbon_capture | [] → [sorbent, metal-organic framework] |

The expanded parser now extracts components from 9 of 10 papers
(was 1 of 10 before expansion). The 1 paper that still extracts 0
(2311.08656) is a cyber-security paper that doesn't mention
hardware components.

**Graph changes:**
- nodes: 661 → 669 (+8 new component nodes, all deduplicated by label)
- edges: 557 → 562 (+5 new `contains` edges; 3 papers share the
  same "metamaterial" node, so only 1 node was created)
- graph_version: 4.1 → 4.2

### Step 4 — Snapshot_4 captured

`data/snapshots/snapshot_4.json`:
- timestamp: 2026-08-02T(same session)
- graph_version: 4.2
- nodes: 669
- edges: 562
- Convergence(battery, EV) = 1.2182
- Convergence(battery, desalination) = 0.0286

## Cumulative temporal table (Phase 5)

| Pair | Snap 1 | Snap 2 | Snap 3 | Snap 4 | Total Δ |
|---|---:|---:|---:|---:|---:|
| Battery ↔ EV | 1.2000 | 1.2500 | 1.2286 | 1.2182 | **+0.0182** |
| Battery ↔ Desalination | 0.0286 | 0.0286 | 0.0286 | 0.0286 | **+0.0000** |
| Discrimination delta | 1.1714 | 1.2214 | 1.2000 | 1.1896 | +0.0182 |

## Per-cycle delta (battery × EV)

| Cycle | Before | After | Delta | Hypothesis |
|---|---:|---:|---:|---|
| Phase 5.A (USPTO patents) | 1.2000 | 1.2500 | +0.0500 | ACCEPTED |
| Phase 5.B (arXiv, original parser) | 1.2500 | 1.2286 | -0.0214 | REJECTED |
| Phase 5.C (arXiv, expanded parser) | 1.2286 | 1.2182 | -0.0104 | REJECTED |

## Why the hypothesis was wrong (again)

**Hypothesis:** expanding the parser's keyword list would let it
extract more components, growing the shared-component numerator and
reversing Phase 5.B's negative delta.

**Actual:** the expanded parser DID extract 8 new component nodes
(anode, cathode, electrolyte, sorbent, adsorbent, metamaterial,
charger, metal-organic framework). But NONE of them matched existing
component labels in a way that created new shared-component bridges:

- The battery paper extracted anode/cathode/electrolyte — NEW labels,
  not matching the existing "battery" component from Phase 5.A patent
  US20240194939A1.
- The EV paper extracted "charger" — NEW, not matching "battery".
- The radiative cooling papers extracted "metamaterial" — NEW, not
  matching any battery or EV component.
- The AWH + DAC papers extracted sorbent/adsorbent/metal-organic
  framework — NEW, not matching any battery or EV component.

So shared_components stayed at 1 (the original "battery" node from
Phase 5.A), while the total grew from 7 (snapshot_3) to 11 (snapshot_4).
overlap_ratio shrank further: 0.143 → 0.091. The convergence score
DECREASED by 0.0104.

## The deeper finding: exact-label matching is the bottleneck

Phase 5.B and Phase 5.C together reveal the actual bottleneck: **the
convergence formula's Signal C requires EXACT label matches to detect
shared components.** The current ingestion pipeline extracts labels
as-is from source text (no normalization, no semantic matching), so:

- "battery" (singular) and "batteries" (plural) are different labels
  → don't share a node (F-001 substring-matching variant, recurring)
- "anode" and "electrode" refer to related things but are different
  labels → don't share a node
- "metal-organic framework" and "MOF" refer to the same thing but are
  different labels → don't share a node

For the convergence score to actually GROW via Signal C, the system
would need either:
1. **Sources that happen to use the same component vocabulary** —
   rare across diverse sources (patents vs papers, different domains).
2. **Label normalization** (singular/plural, synonyms) — this is
   implementation work, FORBIDDEN per CONVERGENCE.md.
3. **Semantic matching** (embeddings, ontology) — also implementation,
   FORBIDDEN.

The honest conclusion: **under the current formula and the current
parser, ingestion cycles that add components without matching
existing labels will CONTINUE to decrease the convergence score.**
This is structurally correct behavior — the formula measures RATIO
of overlap, and adding non-overlapping nodes dilutes the ratio.

## What this proves, and what it does NOT prove

### What it proves

1. **The parser expansion works as intended.** PaperParser now
   extracts 9/10 arXiv papers' components (was 1/10). The 8 new
   keywords are grounded in real arXiv text and don't break the
   existing fixtures (52 tests pass).

2. **F-038 is mitigated** at the extraction level — the parser now
   extracts scientific vocabulary. But F-038's downstream
   consequence (Signal C staying at 0 for non-matching labels) is
   NOT mitigated, because the new labels don't match existing ones.

3. **The Maestro Loop catches its own hypotheses failing.** Two
   consecutive cycles (5.B, 5.C) had hypotheses that predicted
   score increases; both were rejected honestly. The system is
   producing real measurements, not narratives.

### What it does NOT prove

1. **It does NOT prove the parser expansion was wasted.** The 8 new
   component nodes are real extractions from real sources. They carry
   real provenance. They contribute to the graph's structural
   richness. They just don't happen to match existing component labels
   in a way that grows Signal C.

2. **It does NOT authorize formula modification.** The formula is
   behaving correctly. The fact that 2 consecutive cycles decreased
   the score is a measurement, not a defect. Modifying the formula to
   "make the score go up" would be principle #2 violated.

3. **It does NOT authorize semantic matching.** That would be
   implementation work, forbidden per CONVERGENCE.md until validation
   executes.

4. **It does NOT mean the convergence score will keep decreasing
   forever.** The score is bounded below by direct_dependency (1.0)
   plus 1/shortest_path (0.2) = 1.2 for battery×EV. Phase 5.A
   pushed it to 1.25 via Signal C; Phases 5.B and 5.C have eroded
   that gain to 1.2182. The cumulative Phase 5 delta is still
   positive (+0.0182). Further ingestion cycles that add components
   without matching labels will continue eroding, but the floor is
   1.2 (Signal A' + Signal D).

## Updated limitations (additions to P1-P7)

### Limitation P8 — Exact-label matching is the structural bottleneck

The convergence formula's Signal C requires exact (lowercased, stripped)
label matches to detect shared components. Sources using different
vocabulary for the same concept (battery vs batteries; electrode vs
anode; metal-organic framework vs MOF) don't share nodes. This
limits Signal C's ability to grow via ingestion alone.

**Impact:** Phases 5.B and 5.C both decreased the score because the
new sources extracted components with labels that didn't match
existing graph nodes. The shared_components count has been stuck at
1 ("battery" from Phase 5.A patent) across snapshots 2, 3, and 4.

**Mitigation options (all currently forbidden as implementation):**
- Label normalization (singular/plural, synonym maps)
- Semantic matching (embeddings, ontology lookup)
- Adding an absolute-overlap signal (shared_components_count with
  non-zero weight) alongside the ratio signal

All three would be formula or architecture changes, forbidden until
validation executes per CONVERGENCE.md.

### Limitation P9 — Substring matching causes plural-form misses

The existing parser uses `if c in text.lower()` for substring
matching. This means 'battery' doesn't match 'batteries' (the
trailing 'y' vs 'ies'). The battery arXiv paper (2307.03620) uses
"batteries" throughout, so the keyword 'battery' doesn't fire —
but the new keywords 'anode', 'cathode', 'electrolyte' do fire.

**Impact:** the existing 'battery' keyword undercounts. This is the
F-001 pattern (keyword matching brittleness) recurring in a
different form — substring matching doesn't handle morphology.

**Mitigation:** word-boundary regex matching (e.g.,
`re.search(r'\b' + re.escape(c) + r'\b', text.lower())`) would
fix this. But that's a parser implementation change. Allowed
under the auditor's "data modification" framing? Arguably yes —
it's still keyword matching, just with better boundary handling.
But it's a deeper change than adding keywords, and the auditor's
instruction said "done carefully to avoid the F-001 pattern." A
word-boundary fix is the kind of careful improvement that might
be authorized in a future cycle, but it's beyond this cycle's
scope.

## Implementation status (Phase 5.C)

| Item | Status |
|---|---|
| PaperParser keyword expansion | COMPLETE (8 new keywords, grounded in real arXiv text) |
| Re-ingestion of existing arXiv papers with updated parser | COMPLETE (+8 component nodes, +5 edges) |
| Snapshot_4 captured | COMPLETE (graph v4.2, 669 nodes, 562 edges) |
| Delta analysis (snapshot_3 → snapshot_4) | COMPLETE (Convergence(battery, EV): 1.2286 → 1.2182, -0.0104) |
| Hypothesis outcome | REJECTED — score decreased again. The parser expansion did not reverse the negative delta because new component labels don't match existing graph nodes. |
| Convergence module | FORBIDDEN per CONVERGENCE.md. Not created. |
| Phase 5.C status | COMPLETE. Two consecutive hypothesis rejections. Honest finding: exact-label matching is the structural bottleneck. |

## The single most important next action

Two cycles of negative deltas suggest the system has reached a
local maximum on Signal C under the current formula + parser
combination. The next authorized actions, in order of leverage:

1. **Target sources that use the SAME component vocabulary as
   existing graph nodes.** If a future ingestion cycle adds
   sources that mention "battery", "membrane", "electrode",
   "coating", "chamber", or any of the existing 25 real-component
   labels, the shared_components numerator will grow.

2. **Or: accept that Signal C is plateaued and look for convergence
   growth via a different signal pathway.** Signal A (prereq
   overlap) and Signal E (temporal) are both currently 0. Adding
   `requires` or `depends_on` edges between subdomains would grow
   Signal A. But that requires either semantic relationship
   extraction (implementation, forbidden) or manual edge addition
   (which would be subjective, not measurement).

3. **Or: wait for the validation plan in CONVERGENCE.md Section 5
   to execute.** The 2028-01-01 resolution dates will provide real-
   world outcomes to validate the formula against. Until then, the
   formula's weights remain priors, and the cumulative Phase 5
   delta (+0.0182 for battery×EV) is a structural measurement, not
   a real-world convergence claim.

All three are authorized (more ingestion, more measurement, time
passing). Implementation remains forbidden.
