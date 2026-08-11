# External Review Verdict

The evaluator must ultimately answer exactly six questions.

## Q1: Does the system produce proposals that are not explicitly present in its inputs?

YES / NO

Evidence required.

## Q2: Are those proposals genuinely novel?

YES / NO / MIXED

Evidence required. For each proposal classified as novel, provide prior-art search results confirming no prior publication exists.

## Q3: Does the engine outperform reasonable recognition/retrieval baselines?

YES / NO / UNKNOWN

Evidence required. Compare against at least: BM25 retrieval, generic LLM zero-shot, random selection.

## Q4: Does it outperform human researchers on any well-defined discovery task?

YES / NO / UNKNOWN

Evidence required. Give the same inputs to qualified researchers and compare.

## Q5: Can the result be independently reproduced?

YES / NO

Evidence required. The evaluator must run the engine from a clean checkout and reproduce the frozen baseline results.

## Q6: Is there sufficient evidence to call the system an AI discovery engine?

YES / NO / PREMATURE

Evidence required. This is the final judgment. "PREMATURE" means the evidence is insufficient to answer either way.

---

## No internal verdict

No internal document declares that the engine passed external review. No favorable conclusion has been pre-written. The only valid internal state after this package is:

```
AWAITING_INDEPENDENT_REVIEW
```

The evaluator's verdict replaces this state. The authors do not pre-write the evaluator's conclusion.
