# EVIDENCE PHASE ROADMAP

The core architecture is frozen and functional. The product surfaces are defined.
The system now enters the **Evidence Phase** to prove utility and build the moat.

## Phase 1: Reality Testing
- Execute 20-50 real-world tests against the `BusinessPipeline` and `ConsumerPipeline`.
- **Business inputs:** Uploaded patents, tech-transfer disclosures, expired patents, R&D reports.
- **Consumer inputs:** "Reduce household water consumption", "Grow food indoors", "Build inexpensive environmental sensors".
- **Metrics:** Usefulness, novelty, feasibility, implementation cost, expert evaluation (blind scoring).

## Phase 2: Patent Adjacency Scoring (The Moat)
Implementation of the Adjacency Score (AS) metric in `product/scoring/adjacency.py`.
AS = structural_similarity + prerequisite_overlap + material_overlap + manufacturing_overlap + cemetery_overlap + ecosystem_overlap.
This score determines which permutations are surfaced to the user.

## Phase 3: Invention Lineage Mapping
Implementation of the lineage mapper in `product/lineage/mapper.py`.
Generates the UX flow: Ancestors → Parallel Lineages → Historical Failures → Missing Prerequisites → Resurrection → Adjacent Opportunities → Blueprints.

## Phase 4: The Technology Map
Constructing the computational model of technological evolution.
Mapping: materials → components → processes → systems → industries → constraints → future possibilities.
This transitions the platform from a patent analyzer to a predictive engine of civilization-scale tech evolution.
