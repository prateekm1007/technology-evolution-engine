# INVENTION_CONSTITUTION.md

## The Invention Standard

A module may only be called an **engine** if it can:

1. **generate** candidates (not retrieve or rank existing ones),
2. **predict** with a trusted forward model (not score perturbation),
3. **close the loop** with real measurement (not synthetic self-validation).

If any of these three is missing, the module is a **tool**, not an engine.

## The Invention Loop

```text
specification → generated artifact → forward prediction → novelty check → prototype → real measurement → revision
```

If any step is synthetic, the system is still a discovery engine with better formatting.

If all steps are real for one domain, the repo has crossed the threshold into invention.

## Stage Definitions

| Stage | What it does | Status |
|---|---|---|
| Discovery | Find relationships not explicitly stated | ✅ Done |
| Invention | Generate candidates that did not exist, predict, measure | 🚧 Building |
| Engineering | Fabricate, test, iterate on real prototypes | Future |
| Science | Discover new laws from invention-driven experiments | Future |

## What Not to Touch

- `CONSTITUTION.md`
- `MASTER_PROTOCOL.md`
- `EPISTEMIC_ENGINE.md`
- `ANTI_ENTROPY.md`
- `FAILURES.md`
- Current discovery/re-audit stack
- Current benchmark and scorecard generation

## Enforcement

The naming rule is enforced by `tests/test_invention_naming.py`:
- No module may use the name "engine" in its class name unless it implements
  `generate()`, `predict()`, and `measure()` (or close the equivalent loop).
- Modules that only detect, extract, or score are **tools**, not engines.
