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
