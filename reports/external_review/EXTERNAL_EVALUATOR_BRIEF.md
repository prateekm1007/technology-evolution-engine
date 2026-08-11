# External Evaluator Brief

## Your mission

Determine whether the engine can generate genuinely novel cross-domain discoveries that cannot be explained by retrieval, entity extraction, terminology overlap, synonym leakage, benchmark construction, or recognition of relationships already present in the supplied material.

## What you should know

The repository authors have measured three defects in their own benchmark and frozen it as evidence rather than repairing it. The defects are documented in `KNOWN_MEASUREMENT_DEFECTS.md`. The frozen measurement matrix is in `FROZEN_BASELINE.md`.

The authors have NOT asked you to validate their benchmark. They have asked you to **try to invalidate it and the discovery claim**.

## You may

- Inspect every source file
- Inspect every benchmark
- Inspect every gold set
- Create private evaluation scripts
- Construct new blind tests
- Change wording
- Construct adversarial negatives
- Search external literature
- Compare against human researchers
- Compare against ordinary LLM prompting
- Test different models
- Test different temperature settings
- Run repeated trials
- Challenge novelty
- Challenge provenance
- Challenge causality

## You must not

- Silently modify the frozen baseline
- Present a modified benchmark as the original benchmark
- Report unsupported scores
- Treat generated prose as evidence
- Accept the engine's own novelty assertion as proof

## Key questions you must answer

1. Does the system produce proposals that are not explicitly present in its inputs?
2. Are those proposals genuinely novel?
3. Does the engine outperform reasonable recognition/retrieval baselines?
4. Does it outperform human researchers on any well-defined discovery task?
5. Can the result be independently reproduced?
6. Is there sufficient evidence to call the system an AI discovery engine?

See `EVALUATION_RESULT_SCHEMA.md` for the required result format.

## What "discovery" means here

A **discovery** is a proposed cross-domain connection that:
- Is NOT explicitly stated in either input
- Is NOT retrievable by simple lexical overlap
- Is supported by a plausible mechanism
- Is NOT already well-known in the literature
- Would be considered non-obvious by a domain expert

If the engine produces a bridge concept that appears verbatim in the input text, that is **recognition**, not discovery.

If the engine produces a bridge concept that matches an input entity via token overlap, that is **lexical matching**, not discovery.

If the engine produces a bridge concept that is already published in a review paper, that is **retrieval**, not discovery.

## Where to start

1. Read `FROZEN_BASELINE.md` — the measurement matrix
2. Read `KNOWN_MEASUREMENT_DEFECTS.md` — what's broken
3. Read `RECOMMENDED_TEST_BATTERY.md` — test suggestions
4. Run the benchmark: `python3 -m benchmarks.discovery_capability_benchmark`
5. Read the gold set: `benchmarks/discovery_capability_benchmark.py` (search for `GOLD_DISCOVERIES`)
6. Inspect the matcher: search for `_bridge_matches` in the same file
7. Construct your own test
8. Try to break it
