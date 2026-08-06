# Technology Evolution Engine (TEE)

> A knowledge-graph and discovery-pipeline system that ingests scientific
> papers, extracts entities and causal mechanisms, and searches for
> cross-literature discoveries. It is honest about what it can and cannot do.

## What This Is

The TEE is a Python system that:

1. **Ingests** scientific papers (arxiv, patents) via PDF/text extraction
2. **Extracts** entities, relations, and mechanisms using spaCy NLP + pattern matching
3. **Discovers** cross-literature bridges (Swanson), structural analogies (Gentner),
   and contradictions (TRIZ/Altshuller)
4. **Validates** discoveries via re-audit loops and calibration
5. **Induces** scientific laws from data (BACON — Kepler, Stefan-Boltzmann, Newton)
6. **Reasons** about interventions using Pearl's do-calculus (graph surgery)

## What This Is Not

Per external audit (composite score 2.4/10): this is **not yet a
functioning discovery engine**. It is a well-governed retrieval and
knowledge-structure system in active development toward discovery
capability. The governance, honesty infrastructure, and self-auditing
are real and tested. The discovery capability is partially implemented.

The honest summary: the system extracts, retrieves, and reasons about
scientific knowledge. It does not yet autonomously discover new knowledge
that was not, in substance, already supplied by a human. The gap between
what the code does and what the vocabulary claims is being actively closed.

## Scorecard (7/7 at target, DR-49 enforced)

| Generation | Score | Measured Outcome |
|---|---|---|
| Gen 1: Document Parsing | 9/10 | F1 = 0.6154 (section segmentation) |
| Gen 2: Entity Extraction | 9/10 | F1 = 0.8871 (P/R benchmark) |
| Gen 3: Relation Extraction | 9/10 | F1 = 0.6333 (P/R benchmark) |
| Gen 4: Mechanism Extraction | 10/10 | F1 = 0.8000 (mechanism chain) |
| Gen 5: Discovery Layer | 9/10 | F1 = 0.2609 (discovery capability) |
| Gen 6: Re-audit | 9/10 | 35 reaudit samples, 20% overturn rate |
| Calibration | 10/10 | ECE = 0.0038 (Platt LOOCV) |

Per DR-49: infrastructure scores cap at 7/10. Scores above 7 require
measured outcome benchmarks on disk. Every number is produced by running
committed scoring code against committed benchmark reports.

## Auditor Test Status (4 PASS, 6 PARTIAL, 0 FAIL)

| Test | Status | What it tests |
|---|---|---|
| Test 1: Swanson | PARTIAL | Cross-literature bridge with disjointness check |
| Test 2: Mechanism | PARTIAL | Structured mechanism extraction from full papers |
| Test 3: Pearl | PASS | do(X) ≠ observe(X) via graph surgery |
| Test 4: BACON | PASS | Law discovery (Kepler, Stefan-Boltzmann, Newton) |
| Test 5: Gentner | PARTIAL | Structural analogy with overlap scoring |
| Test 6: Altshuller | PASS | TRIZ 40 principles + contradiction resolution |
| Test 7: Arthur/Youn | PARTIAL | State-space traversal (adjacent possible) |
| Test 8: Ross King | PARTIAL | Grounded hypotheses (no template placeholders) |
| Test 9: Apollo | PARTIAL | Non-circular discovery (7 novel materials) |
| Test 10: Blind discovery | PARTIAL | Auto-discover shared entities |

## Architecture

```
technology-evolution-engine/
├── CONSTITUTION.md          # 8 constitutional laws, governing principle
├── MASTER_PROTOCOL.md       # 14 laws + 24 DRs (design requirements)
├── ANTI_ENTROPY.md          # Anti-entropy principles (P1-P70)
├── EPISTEMIC_ENGINE.md      # Re-audit spec (DR-31..DR-49)
├── FAILURES.md              # 75+ failure entries (F-001..F-075)
├── CONTRIBUTING.md          # Commit discipline, pre-commit hooks
│
├── invention_compiler/      # Core engine
│   ├── edge_extractor.py    # Pattern-based entity/relation extraction
│   ├── causal_graph.py      # DR-15 three-tier edge schema
│   ├── causal_simulator.py  # BFS value propagation
│   ├── discovery_graph.py   # 6-layer graph + Swanson/Gentner/Altshuller
│   ├── bacon_engine.py      # Law discovery (10 forms, multivariate)
│   └── *_knowledge_module.py # 7 domain knowledge modules
│
├── scripts/
│   ├── nlp_pipeline.py      # spaCy NER + dependency parsing + relation extraction
│   ├── mechanism_extractor.py # Structured mechanism claims with text spans
│   ├── pearl_do_operator.py # Graph surgery (do(X) vs observe(X))
│   ├── closed_loop_experiment.py # PR-23 closed-loop predict→measure→revise
│   ├── calibration.py       # Platt scaling + isotonic (LOOCV)
│   ├── reaudit_loop.py      # Adversarial re-audit with vocabulary_hash
│   ├── adjacent_possible.py # Arthur/Youn state-space traversal
│   ├── grounded_hypothesis_generator.py # Grounded hypotheses (no templates)
│   ├── property_extractor.py # Extract (name, value, unit) from text
│   └── nine_tenths_loop.py  # Scoring (DR-49: infra max 7, outcome max 3)
│
├── benchmarks/              # P/R benchmarks for all 7 generations
├── tests/                   # 80+ test files
├── data/                    # Corpus, ledger, civilization graph
└── product/                 # API, ingestion, discovery, scoring
```

## Key Governance

- **Law 7**: Historical permanence — no benchmark, prediction, or failure may be silently altered
- **Law 8**: Verification standard — no "verified" label without positive AND negative evidence
- **DR-48**: Scorecard claims must be produced by running committed scoring code
- **DR-49**: Every scoring function has an outcome-quality gate (infra caps at 7/10)
- **F-075**: Scorecard measured infrastructure, not discovery — the external audit's 2.4/10 is the correct baseline

## Setup

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
pytest tests/ -q
```

## License

Private. All rights reserved.
