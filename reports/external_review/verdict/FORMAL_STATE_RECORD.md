# Formal State Record

## Current state
```
REVIEW_RECEIVED
Development Freeze
```

## State progression

```
STAGE −1
Measurement Integrity
        ↓
NOT TRUSTWORTHY
        ↓
External Independent Review
        ↓
PREMATURE
        ↓
CURRENT STATE
REVIEW_RECEIVED
        ↓
Development Freeze
```

## Immutable facts (frozen)

1. `777cb6d` remains the epistemic baseline.
2. `0.5714` remains a historical measurement, **not a capability claim**.
3. The existing `discover_shared_entities()` pathway is not evidence of generative discovery.
4. The gold snippets do not adequately isolate novel inference from semantic recognition.
5. Stage −1's scorer defects remain unfixed and documented.
6. The external review does **not** establish that the underlying engine is incapable of discovery; it establishes that the current experiment cannot establish that it can.

## What the external review established

The problem is not merely that the scorer has bugs. The problem is that the scientific construct itself has not yet been demonstrated. The benchmark tests entity intersection, not generation of a novel bridge. Even a perfectly repaired scorer would not establish independent invention against the current gold set.

## What does NOT change

- `stage-1-measurement-integrity-baseline` tag — immutable
- `GOLD_DISCOVERIES` — untouched
- `_bridge_matches()` — untouched
- `BRIDGE_SYNONYMS` — untouched (empty)
- `fp` — untouched (0 by construction)
- Production F1 (0.5714) — frozen as historical baseline
- Development freeze — remains in force

## Next step (not yet started)

Design a **Scientific Gate 2 Protocol** specifying:
- Blind proposal experiment
- Controls (retrieval, LLM, random, human)
- Leakage rules (lexical, semantic, conceptual, mechanistic)
- Novelty adjudication (three-gate: novel to inputs, novel to literature, expert-validated)
- Expert procedure (blinded, independent)
- Statistical analysis (validated discovery yield, not F1)
- Stopping criteria

The protocol must be independently approved before implementation begins.

## Prohibition

No single F1-style headline metric at the next stage. A system producing 1 genuinely novel, experimentally useful hypothesis may be scientifically more impressive than a system producing 90 semantically correct rediscoveries. The next stage measures **validated discovery yield**, not merely textual matching.
