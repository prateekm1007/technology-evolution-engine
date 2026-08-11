# Recommended Test Battery

Independent evaluators should test at least the following. These are recommendations, not requirements — evaluators should design their own tests as well.

## Test A — Recognition control

Give the engine material where the relationship is explicitly stated.

Example: "X causes Y through mechanism Z" in source A, and "Z is important for W" in source B. The bridge "Z" is explicitly named in both.

Determine whether the engine receives credit for this.

**Purpose:** Separate recognition from discovery. If the engine gets credit for explicitly stated relationships, it is measuring recognition, not discovery.

## Test B — Ambient entity control

Put the correct answer in extracted entities but prevent it from being an actual discovery proposal.

Example: Ensure the gold bridge concept appears as an extracted entity in source A, but is NOT in the shared entity set (not in both A and B).

Determine whether the evaluator counts this as discovery.

**Purpose:** Test proposal-locus integrity. The current production scorer counts this as a discovery (DEFECT-001). An independent evaluator should not.

## Test C — Terminology perturbation

Replace obvious terminology with paraphrases.

Example: Replace "thermal emission" with "heat radiation output". Replace "biomineralization" with "biological mineral precipitation".

**Purpose:** Determine whether discovery survives lexical cues. If the engine only works when the exact terminology is present, it is doing lexical matching, not semantic discovery.

## Test D — Gold shuffle

Randomize gold labels.

Assign gold bridge "biomineralization" to the case that originally had "thermal emission". Assign "thermal emission" to the case that had "tight junctions". Etc.

**Purpose:** Measure chance matching. The Stage −1 experiment found a 13.7% null hit rate with N=1000. An independent evaluator should replicate this.

## Test E — Adversarial negatives

Construct pairs with superficially similar terminology but no meaningful mechanism.

Example: "Heat transfer in electronics" and "Heat transfer in cooking". Both mention "heat transfer" but the connection is trivial and not a scientific discovery.

**Purpose:** Test false discovery. If the engine proposes "heat transfer" as a bridge for this pair, it is doing lexical matching, not discovery.

## Test F — Novel-domain transfer

Give the engine domains it has not been benchmark-tuned against.

The current gold set covers materials science, biology, physics, chemistry. Give it law, economics, sociology, or music theory.

**Purpose:** Test generalization. If the engine only works on the 20 gold domains, it may be overfit.

## Test G — Temporal holdout

Use literature published after the benchmark's documented construction/freeze cutoff.

Determine the benchmark's documented construction/freeze cutoff from repository provenance. Use only literature published after that cutoff. If no sufficient post-cutoff corpus exists, mark the temporal holdout as UNAVAILABLE/PENDING rather than inventing a future test window.

**Purpose:** Prevent benchmark memorization. If the gold answers are somehow encoded in the system, temporal holdout would catch it.

## Test H — Expert blind evaluation

Give outputs to domain experts without telling them:
- Which are AI-generated
- Which are benchmark answers
- Which are generated controls

Ask:
```
Is this relationship genuinely non-obvious?
Is it scientifically meaningful?
Was it already known?
Does the proposed mechanism make sense?
```

**Purpose:** Human expert ground truth. The engine's own scoring is not authoritative (see INDEPENDENCE_RULES.md).

## Test I — Independent literature search

For every claimed discovery, search the literature independently.

Classify:
```
Novel — not previously published
Previously known — published before the benchmark
Partial precedent — related but not identical
Ambiguous — unclear
Unsupported — no evidence found
```

**Purpose:** Verify novelty claims. The engine asserts novelty; an independent search verifies it.

## Test J — Human baseline

Give the same inputs to qualified researchers.

Measure:
```
AI discoveries
Human discoveries
Overlap
Unique AI discoveries
Unique human discoveries
```

Do not assume AI superiority. If humans find the same or more connections, the engine is not adding value.

## Test K — LLM zero-shot baseline

Give the same input snippets to a generic LLM (GPT-4, Claude, etc.) with a simple prompt:

```
Given these two text snippets from different domains, what connecting concept or mechanism do they share?
```

Compare the LLM's answers to the engine's answers.

**Purpose:** Is the engine doing something beyond generic language-model association?
