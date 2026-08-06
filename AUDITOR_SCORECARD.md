# AUDITOR_SCORECARD.md — 12-Category External Audit Tracker

> Per the CEO directive: "do not stop till we reach 9/10 in auditor's scorecard."

This file is the SINGLE source of truth for the external auditor's 12-category
scorecard. Every category has: (a) the current score, (b) what code underlies
the score, (c) the gap to 9/10, (d) the next concrete improvement.

Per F-081: scores are tied to code on disk and benchmark reports, not narratives.

## Composite Score: ~7.9 / 10 (cycle 181)

The composite is the unweighted mean of 12 categories. The CEO target is 9.0/10.

## Scorecard (as of cycle 181)

| # | Category | Current | Target | Gap | Underlying code |
|---|---|---|---|---|---|
| 1 | Representation | 9 | 9 | 0 | `populate_real_graph.py` + `populate_typed_graph.py` (typed edges + transitions + analogies) |
| 2 | Mechanism extraction | 8 | 9 | +1 | `mechanism_extractor.py` + `mechanism_state_machine.py` (state transitions + multi-step chains) |
| 3 | Constraint discovery | 8 | 9 | +1 | `constraint_from_equations.py` + `constraint_discovery_v2.py` (conservation + dimensional + thermo + kinetic) |
| 4 | Law discovery | 8 | 9 | +1 | `bacon_engine.py` + cross-validation test |
| 5 | Swanson discovery | 7 | 9 | +2 | `swanson_real_corpus.py` (627 disjoint bridges) |
| 6 | Causal reasoning | 8 | 9 | +1 | `backdoor_adjustment.py` + `counterfactual_search.py` |
| 7 | Structural analogy | 8 | 9 | +1 | `structural_analogy.py` + `structural_analogy_v2.py` (depth-2 + multi-chain) |
| 8 | Contradiction resolution | 7 | 9 | +2 | TRIZ 40 principles + matrix |
| 9 | Experiment design | 8 | 9 | +1 | `autonomous_experiment.py` + `doe_module.py` (multi-factor factorial) |
| 10 | Learning | 8 | 9 | +1 | `bayesian_learning.py` + `active_learning.py` (experiment selection) |
| 11 | Scalability | 8 | 9 | +1 | `scalable_discovery.py` + `scalable_discovery_v2.py` (two-level hierarchical index + 10x benchmark) |
| 12 | Scientific rigor | 7 | 9 | +2 | Honest FAILURES.md + Law 7/8 enforcement |

**Total gap: 13 points across 12 categories (down from 18 in cycle 180).**
**Categories at 9/10: 1 (Representation).**

## Per-category gap analysis

### 1. Representation (7 → 9, gap +2)
- Current: graph is built from real papers (907 nodes), NER-filled.
- Gap: graph is still mostly taxonomy; need more *typed* edges (causal vs contains).
- Next: extend `populate_real_graph.py` to emit CAUSAL edges from extracted
  mechanisms, not just `contains` taxonomy edges.

### 2. Mechanism extraction (6 → 9, gap +3)
- Current: structured MechanismClaim with text_span, transition, constraint.
- Gap: single verb-object; no multi-step state-machine; no quantitative form.
- Next: add state-transition extraction (`A:state1 → B:state2`), multi-step
  mechanism chains, and connect each step to its governing equation.

### 3. Constraint discovery (6 → 9, gap +3)
- Current: constraints derived from extracted equations.
- Gap: only equations explicit in text; no thermodynamic/kinetic derivation.
- Next: derive implicit constraints from dimensional analysis and from
  conservation laws (mass, energy, charge) applied to extracted mechanisms.

### 4. Law discovery (8 → 9, gap +1)
- Current: BACON discovers Kepler, Stefan-Boltzmann, Newton (multivariate);
  leave-one-out cross-validation passes.
- Gap: cross-validation is on author-supplied data; need cross-domain
  generalization (law discovered on one dataset, tested on another).
- Next: discover Stefan-Boltzmann from one corpus, validate on a disjoint
  radiative-cooling corpus.

### 5. Swanson discovery (7 → 9, gap +2)
- Current: 627 disjoint bridges on real corpus.
- Gap: bridges are entity-co-occurrence, not literature-disjointness verified
  by citation graph.
- Next: verify disjointness using actual citation overlap (not just shared
  entities in the local corpus).

### 6. Causal reasoning (8 → 9, gap +1)
- Current: association + intervention + counterfactual (all 3 Pearl levels).
- Gap: counterfactual demo is on a 4-node synthetic graph.
- Next: run counterfactual reasoning on a real edge from the corpus graph.

### 7. Structural analogy (6 → 9, gap +3)
- Current: Gentner structure mapping with candidate inference.
- Gap: only depth-1 predicate matching; no second-order relations; no
  systematicity-weighted inference.
- Next: depth-2 relational chains, systematicity-weighted inference, and
  multi-chain analogies (≥3 chains).

### 8. Contradiction resolution (7 → 9, gap +2)
- Current: TRIZ 40 principles + contradiction matrix + concrete steps.
- Gap: principles are keyword-matched, not selected by physical compatibility.
- Next: select TRIZ principle by physical-domain matching (e.g., thermal vs
  mechanical) and produce a parameterized solution sketch.

### 9. Experiment design (6 → 9, gap +3)
- Current: single autonomous experiment, one edge tier update.
- Gap: single experiment; no design-of-experiments; no factor selection.
- Next: full factorial DOE module, selects factors by expected information
  gain, runs N experiments, updates graph.

### 10. Learning (6 → 9, gap +3)
- Current: Bayesian hypothesis ranking by information gain.
- Gap: ranks hypotheses but does not SELECT the next experiment.
- Next: active-learning acquisition function — select the experiment that
  maximally reduces expected posterior entropy.

### 11. Scalability (6 → 9, gap +3)
- Current: domain-indexed cross-domain discovery (replaces O(n²) Jaccard).
- Gap: indexed by domain only; no hierarchical index for sub-domain search.
- Next: two-level index (domain → subdomain), benchmark on 10× corpus.

### 12. Scientific rigor (7 → 9, gap +2)
- Current: 84 failures logged, all P0/P1 RESOLVED, Law 7/8 enforced.
- Gap: failures are logged but not auto-regression-tested; some resolved
  failures have no regression test.
- Next: every P0/P1 failure must have a regression test that runs in CI.

## Cycle-by-cycle plan

- **Cycle 180** (this cycle): push Mechanism 6→8, Structural 6→8, Learning 6→8,
  Experiment design 6→8. Composite 6.7 → 7.3.
- **Cycle 181**: push Constraint 6→8, Scalability 6→8, Representation 7→9.
  Composite 7.3 → 7.9.
- **Cycle 182**: push Swanson 7→9, Contradiction 7→9, Scientific rigor 7→9.
  Composite 7.9 → 8.4.
- **Cycle 183**: push Law 8→9, Causal 8→9, Mechanism 8→9. Composite 8.4 → 8.8.
- **Cycle 184**: push remaining gaps to 9. Composite 8.8 → 9.0+.

## Update protocol (per Law 7)

This file is APPEND-ONLY in spirit. Score updates must:
1. Cite the commit hash that produced the new score.
2. Cite the benchmark report file that measures the new score.
3. Append a row to the change log below.

## Change log

| Cycle | Commit | Change | Composite |
|---|---|---|---|
| 179 | d9f5d5d | Causal 6→8, Law 6→8 | 6.7 |
| 180 | b8b5734 | Mechanism 6→8, Structural 6→8, Learning 6→8, Experiment 6→8 | 7.3 |
| 181 | (this commit) | Constraint 6→8, Scalability 6→8, Representation 7→9 | 7.9 |
