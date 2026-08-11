# Comparison Baseline

Independent evaluators must compare the engine against at least the following baselines:

## 1. Human baseline

Give the same input snippets to qualified researchers (domain-matched where possible).

Measure:
- How many of the 20 gold bridges do humans find?
- How many additional connections do humans find that the engine misses?
- How many connections does the engine find that humans miss?
- Are human-found connections more or less novel than engine-found connections?

Do not assume AI superiority. If humans find the same or more connections, the engine is not adding value.

## 2. Generic LLM baseline

Give the same input snippets to a generic LLM (GPT-4, Claude, Gemini, etc.) with a simple zero-shot prompt:

```
Given these two text snippets from different scientific domains, what connecting concept or mechanism do they share?

Snippet A: [text]
Snippet B: [text]

List all connecting concepts you can identify.
```

Measure:
- How many of the 20 gold bridges does the LLM find?
- Does the LLM find connections the engine misses?
- Does the engine find connections the LLM misses?
- Are the LLM's explanations more or less mechanistically sound?

## 3. Retrieval-only baseline

Use BM25 or TF-IDF retrieval to find shared terms between the two snippets.

Measure:
- How many gold bridges are retrievable by simple term overlap?
- This is essentially what the current engine does (token-overlap matching), but without the NLP pipeline overhead.

## 4. Random baseline

Randomly select terms from a scientific vocabulary.

Measure:
- What hit rate does random selection produce?
- The Stage −1 shuffled-gold experiment found 0.1374 mean hit rate. An independent evaluator should replicate this.

## Purpose

The purpose of these baselines is to answer:

> Is the engine doing something beyond retrieval, generic language-model association, and chance?

If the engine does not outperform the LLM baseline, it is not adding value beyond what a generic LLM can do.

If the engine does not outperform the retrieval baseline, it is not adding value beyond simple term matching.

If the engine does not outperform the random baseline, it is producing noise.

## The exact models can be selected by evaluators

The evaluators should choose the specific LLM, retrieval method, and human experts. The authors do not prescribe these — that would compromise independence.
