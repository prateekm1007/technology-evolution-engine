# Independence Rules

## Core principle

> The engine, its authors, and its internal benchmark code are not authoritative judges of novelty.

## What this means

The independent evaluator controls:

- **Evaluation criteria** — the evaluator decides what constitutes a discovery, not the engine's authors
- **Negative controls** — the evaluator constructs adversarial tests, not the engine
- **Novelty determination** — the evaluator searches the literature, not the engine
- **Prior-art search** — the evaluator verifies novelty independently
- **Final classification** — the evaluator assigns NOVEL / PREVIOUSLY_KNOWN / etc., not the engine

## What the engine's authors may NOT do

- Claim that the engine has discovered something without independent verification
- Use the engine's own scoring as evidence of discovery
- Use the engine's generated explanations as evidence of novelty
- Set thresholds for what counts as a discovery
- Grade their own engine's performance
- Pre-write a favorable conclusion

## What the engine's authors HAVE done

- Measured and documented three defects in their own benchmark (DEFECT-001, DEFECT-002, DEFECT-003)
- Frozen the benchmark as evidence rather than repairing it
- Produced a complete Stage −1 metrology showing what the current scorer measures and what it does not
- Explicitly prohibited claims of independent discovery (see CLAIMS_NOT_BEING_MADE.md)
- Prepared this external review package to enable independent scrutiny

## The only valid internal state

```
AWAITING_INDEPENDENT_REVIEW
```

No internal document declares that the engine passed external review. No favorable conclusion has been pre-written. The repository is in a state of honest uncertainty about its own capability.
