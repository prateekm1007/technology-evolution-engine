# INVENTION_CONSTITUTION.md

## The Invention Standard

A module may only be called an **engine** if it can:

1. **generate** candidates (not retrieve or rank existing ones),
2. **predict** with a trusted forward model (not score perturbation),
3. **close the loop** with real measurement (not synthetic self-validation).

If any of these three is missing, the module is a **tool**, not an engine.

## The Invention Loop

```text
specification → generated artifact → forward prediction → failure engine → novelty check → prototype → real measurement → revision
```

If any step is synthetic, the system is still a discovery engine with better formatting.

If all steps are real for one domain, the repo has crossed the threshold into invention.

## Stage Definitions

| Stage | What it does | Status |
|---|---|---|
| Discovery | Find relationships not explicitly stated | ✅ Done (F1=0.9189 (HISTORICAL — was circular, current F1=0.5714 after cycle 270)) |
| Capability | What can this knowledge do? | ✅ Exists (`scripts/capability_graph.py`) — extend, don't rebuild |
| Specification | What do we want? | ✅ Built (`scripts/specification.py`) |
| Invention | Generate candidates that did not exist, predict, measure | 🚧 Building (vertical slice closes) |
| Engineering | Fabricate, test, iterate on real prototypes | Future |
| Science | Discover new laws from invention-driven experiments | Future |

## Stage 0.5 — Capability Graph: Extend, Don't Rebuild

The repo already has a working capability graph (`scripts/capability_graph.py`).
Stage 0.5 is **evolution of an existing proof-of-concept**, not a new build.
The existing graph derives capabilities from discovery relations. The evolution
adds: reasoning (`capability_reasoner.py`), composition (`capability_composer.py`),
similarity (`capability_similarity.py`), and constraints (`capability_constraints.py`).

**Rule:** Do NOT create a parallel capability graph. Extend the existing one.

## The Failure Engine — First-Class Constitutional Gate

The Failure Engine (`scripts/failure_engine.py`) is NOT a supporting utility.
It is a **first-class constitutional gate** with VETO authority over every
stage (Constitutional Rule 8).

**Mandatory adversarial tests for every new invention stage:**
1. Inject synthetic measurements → loop must refuse closure
2. Inject circular gold → pipeline must reject
3. Inject KB equations as simulation → forward model must fail validation
4. Inject self-validation (prediction = measurement) → must be detected

These tests are MANDATORY. No new stage may merge without passing them.

**The discovery baseline is NOT fixed truth.** The Failure Engine must audit
it continuously. The current honest discovery F1=0.9189 was defensible at the time (HISTORICAL — current F1=0.5714 after circular synonym removal in cycle 270) but
must not be treated as permanent — it can change if the gold set or
extraction pipeline changes.

## Frozen Discovery Stack (Stage 0)

The following modules are FROZEN — only bug fixes permitted:

| Module | Path |
|---|---|
| Entity extraction | `scripts/extract_entities.py`, `scripts/nlp_pipeline.py` |
| Relation extraction | `scripts/extract_relations.py` (via `nlp_pipeline.py`) |
| Mechanism extraction | `scripts/mechanism_extractor.py`, `scripts/mechanism_state_machine.py` |
| Constraint discovery | `scripts/constraint_discovery_v2.py` (NOT `constraint_discovery.py`) |
| BACON engine | `invention_compiler/bacon_engine.py` |
| Graph isomorphism | `scripts/graph_isomorphism_analogy.py` |
| Grounded hypothesis | `scripts/grounded_hypothesis_v2.py` (NOT `grounded_hypothesis.py`) |
| Re-audit loop | `scripts/reaudit_loop.py` |

## Single Execution Path

All execution goes through `scripts/tee_orchestrator.py` — the SINGLE
authoritative entrypoint. No competing loop scripts.

```
python3 -m scripts.tee_orchestrator <command>
```

Commands: `discovery`, `invention`, `benchmark`, `scorecard`,
`failure-audit`, `reaudit`, `full-loop`.

The `full-loop` command runs the Failure Engine FIRST as a gate.
If it VETOES, execution stops.

## What Not to Touch

- `CONSTITUTION.md`
- `MASTER_PROTOCOL.md`
- `EPISTEMIC_ENGINE.md`
- `ANTI_ENTROPY.md`
- `FAILURES.md`
- Current discovery/re-audit stack (frozen — bug fixes only)
- Current benchmark and scorecard generation

## Enforcement

The naming rule is enforced by `tests/test_invention_naming.py`:
- No module may use the name "engine" in its class name unless it implements
  `generate()`, `predict()`, and `measure()` (or close the equivalent loop).
- Modules that only detect, extract, or score are **tools**, not engines.

The circularity gate is enforced by `benchmarks/discovery_capability_benchmark.py`:
- If any bridge word appears in input snippets, the benchmark EXITS NON-ZERO.
- F-099 can never silently return.

The Failure Engine gate is enforced by `scripts/tee_orchestrator.py`:
- `failure-audit` runs before any other command in `full-loop`.
- VETO stops execution.

