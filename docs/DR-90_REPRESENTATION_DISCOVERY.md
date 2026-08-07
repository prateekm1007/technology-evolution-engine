# DR-90 — Representation Discovery

## The Research Hypothesis

> **H-REP-001:** The limiting factor in automated invention is not search quality but representational expressiveness. Systems that can discover new representational primitives will unlock invention strategies that cannot be reached by composing, parameterizing, or deriving operators within a fixed DSL.

## Scientific Basis (from the L5b saturation evidence, cycles 228-239)

Four independent experiments all converged on the same ceiling:

| Hypothesis | Cycle | Result |
|-----------|------:|--------|
| Better search (evolutionary) | 230 | NO — flat fitness |
| Deeper composition (triples) | 236 | NO — 7.1× complexity, +0 performance |
| Parameterization (alpha) | 238 | NO — 9/10 = 9/10 |
| Landscape-derived operators | 239 | NO — 9/10 = 9/10 |

**Conclusion:** The DSL's current primitive vocabulary is sufficient.
New primitives must come from OUTSIDE the existing composition space.

This is not a setback — it is the definitive answer to "what is the
bottleneck?" The bottleneck is REPRESENTATION. Progress requires
fundamentally new representational primitives that this DSL cannot express.

## Mission

Do NOT build another optimizer.
Do NOT build another operator.
Do NOT build another search strategy.

Instead answer one question:

> **How does a system invent a representational primitive that did not
> previously exist?**

## Stage 0 — Freeze Everything (PERMANENT)

The following modules are FROZEN. No modifications. Only additive work.

- Discovery Engine (F1=0.9189)
- Extraction (entities, relations, mechanisms)
- Forward Models
- L1-L5b (landscape measurement, taxonomy, optimizer selection,
  meta-learning, program discovery, DSL extension, synthesis)
- Failure Engine
- Benchmarks (discovery, blind suite, entropy saturation)
- Scorecards
- FAILURES.md (F-001 through F-129, append-only)

## Stage 1 — Study Human Invention

Humans almost never invent by composing operators.
They invent by changing representation.

Historical examples:
- Calculus (changed from discrete to continuous)
- Vector spaces (changed from scalar to directional)
- Fourier transform (changed from time to frequency domain)
- Tensor notation (changed from index to multi-dimensional)
- Dynamic programming (changed from search to memoization)
- Gradient descent (changed from discrete to directional)
- Backpropagation (changed from manual to automatic differentiation)
- Attention (changed from fixed to dynamic routing)
- MCTS (changed from exhaustive to probabilistic search)
- Bayesian Optimization (changed from direct to surrogate)
- Diffusion (changed from direct generation to iterative denoising)
- Transformers (changed from sequential to parallel attention)

None of those are "operator combinations."
They are new representations.

### Deliverable

```
representation_library.json
```

Each entry:
- primitive name
- why it mattered
- what representation changed
- what previous representation failed
- what new search became possible

Target: 100 historical invention primitives.

## Stage 2 — Representation Grammar

Instead of:
```
Operator → Composition → Program
```

Discover:
```
Representation → Operator Language → Programs
```

The engine should manipulate REPRESENTATIONS, not operators.

Example representations to explore:
- latent_space (search in compressed representation)
- constraint_manifold (search on constraint surface)
- symmetry_group (search modulo symmetries)
- causal_factorization (search via causal decomposition)
- dual_space (search in the dual)
- energy_landscape (search via annealing)

### Deliverable

```
representation_dsl.py
```

## Stage 3 — Representation Mutation

The engine mutates REPRESENTATIONS, not programs.

Example mutations:
- search points → search trajectories
- search trajectories → search distributions
- search distributions → search manifolds
- search manifolds → search proofs
- search proofs → search simulations

The search space ITSELF changes.

### Deliverable

```
representation_mutator.py
```

## Stage 4 — Representation Evaluation

A representation is good only if it unlocks searches that were
previously impossible.

Metrics (NOT accuracy):
- Novel reachable states
- Compression
- Prediction quality
- Search efficiency
- Transfer
- Complexity

### Deliverable

```
representation_benchmark.py
```

## Stage 5 — Primitive Discovery

The engine searches for new REPRESENTATIONAL PRIMITIVES.

Not operators. Primitives.

Example:
- Current: distance → Discovered: causal distance
- Current: neighbor → Discovered: counterfactual neighbor
- Current: objective → Discovered: multi-agent objective

These are genuine conceptual inventions.

### Deliverable

```
primitive_discovery.py
```

## Stage 6 — External Validation

Nothing counts unless an external benchmark shows the new representation
beats the previous representation.

Requirements:
- Same compute
- Same data
- Same benchmark
- Representation changes
- Performance improves
- Otherwise: REJECT

## Success Criteria

A representation is accepted only if it:
- enables a search previously impossible
- compresses reasoning
- transfers to unrelated domains
- survives the blind suite
- survives the Failure Engine
- produces measurable improvement

Otherwise: FAIL.

## Explicit "Do Not Build"

The coder is FORBIDDEN from building:
- another optimizer
- another search heuristic
- another mutation operator
- another crossover
- another Bayesian variant
- another evolutionary variant
- another parameterized primitive
- another operator composition DSL

Those hypotheses have already been explored and, within the current
representation, have reached saturation (F-126 through F-129).

## Relationship to the Current System

The current system (cycles 1-239) is the FOUNDATION:
- Discovery pipeline provides the knowledge base
- Invention engine provides the generate→predict→measure loop
- L1-L4 provides landscape-aware optimizer selection
- L5a provides program discovery over a fixed DSL
- L5b provides the saturation evidence that motivates DR-90
- The blind suite and entropy benchmark provide the evaluation framework

DR-90 does NOT replace the current system. It EXTENDS it by asking:
"What if the DSL itself could evolve?"

The current system's value is NOT diminished by the saturation —
it is INCREASED, because the saturation evidence is the scientific
finding that makes DR-90 necessary and credible.

## Timeline

This is a multi-year research program, not a sprint.
Each stage is a research milestone, not an implementation cycle.

- Stage 1 (Study): 3-6 months
- Stage 2 (Grammar): 6-12 months
- Stage 3 (Mutation): 12-18 months
- Stage 4 (Evaluation): 6-12 months
- Stage 5 (Discovery): 12-24 months
- Stage 6 (Validation): ongoing

Total: 3-5 years for meaningful progress.

## The Bottom Line

The current system has answered:
> "Can we build a landscape-aware meta-search architecture
>  with honest benchmarks?"

Answer: YES (9/10 blind, multi-seed robust, 4 hypotheses falsified).

DR-90 asks:
> "Can a system invent new representational primitives
>  that unlock strategies the current DSL cannot express?"

Answer: UNKNOWN. That is the research frontier.
