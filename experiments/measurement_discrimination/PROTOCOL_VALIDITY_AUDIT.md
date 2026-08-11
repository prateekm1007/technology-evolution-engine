# Protocol-Validity Audit — Phase 8 Preregistration

**Date:** 2026-08-09
**Auditor:** External audit (round 23)
**Status:** DEFECT FOUND — PREREGISTRATION INVALID FOR RELATIONSHIP DISCRIMINATION

---

## Finding

The Phase 8 preregistration has a fundamental protocol-validity defect.

### The frozen matcher does not observe source relationships

The frozen matcher is:

```python
_bridge_matches(expected_bridge: str, candidate: str) -> bool
```

It receives **only two strings**. It does not receive:
- `literature_a` (source text from domain A)
- `literature_b` (source text from domain B)
- domain labels
- graph structure
- entity pool
- mechanism information

The implementation is exact/substring/token/synonym matching between two strings.

### TPR_true is 1.0 by construction

The preregistration's true candidate is:

```text
candidate = gold.bridge
expected_bridge = gold.bridge
```

Therefore, for every true case:

```text
canonicalize(expected_bridge) == canonicalize(candidate)
```

The substring test immediately returns `True`.

So:

```text
TPR_true = 20/20 = 1.0
```

**by construction.**

The matcher is not discovering that the bridge relates the two domains. The experiment hands it the gold answer as both the expected bridge and the candidate.

### What the experiment actually measures

The null condition asks whether an unrelated bridge string (borrowed from another case) happens to lexically match the original bridge string.

Therefore the experiment measures:

> **How often does the lexical matcher match a gold bridge against itself versus a bridge borrowed from another case?**

This is a **lexical separability benchmark**, not evidence that the matcher can discriminate true cross-domain relationships.

### Classification

```text
PROTOCOL_VALIDITY = INVALID_FOR_RELATIONSHIP_DISCRIMINATION
REASON = SCORER_DOES_NOT_OBSERVE_SOURCE_RELATIONSHIP
TPR_TRUE = 1.0_BY_CONSTRUCTION
```

---

## What must NOT be done

1. **Do NOT modify `_bridge_matches()`** to make it consume source documents. That would alter the frozen matcher and invalidate the F1 freeze (Phase 7).

2. **Do NOT delete the current preregistration.** It is preserved as `PREREGISTRATION_SUPERSEDED_DRAFT.md` and `protocol_SUPERSEDED_DRAFT.json`.

3. **Do NOT execute the current protocol.** No gold opening, no control generation, no statistical run, no result generation.

---

## Required correction

### Two explicitly separated protocols

#### Protocol A — Lexical matcher discrimination

**Question:** Can `_bridge_matches()` distinguish an exact gold bridge from bridges borrowed from other cases?

**Claim limit:** `LEXICAL_MATCHER_DISCRIMINATION` only. Cannot be called `DISCOVERY_DISCRIMINATION`, `CROSS_DOMAIN_RELATIONSHIP_DISCRIMINATION`, or `DISCOVERY_CAPABILITY`.

**Key property:** TPR_true is 1.0 by construction. The experiment measures whether the null (shuffled bridges) produces a low FPR. If FPR is low, the matcher can lexically separate gold bridges from non-gold bridges. This is necessary but NOT sufficient for discovery discrimination.

#### Protocol B — Actual discovery discrimination

**Question:** Can the discovery system identify a relationship between two domains when the bridge is not supplied as the answer?

**Requirements:**
- The system must receive source-domain information (documents, mechanisms, entities)
- The system must generate/evaluate candidate mechanisms
- The gold bridge must NOT be supplied as input to the scorer
- Independent evaluation must determine whether the system's output matches the gold relationship

**Key property:** TPR_true is NOT 1.0 by construction. The system might fail to identify the bridge. This is the experiment relevant to the North Star.

**Relationship to existing infrastructure:**
- The frozen `_bridge_matches()` function may be used as part of Protocol B's scoring pipeline, but ONLY if the candidate is system-generated (not the gold bridge itself).
- The SCIENTIFIC_GATE_2_PROTOCOL.md (v1.2 FROZEN) already defines this type of experiment: Gate A tests whether the engine can generate a proposal that cannot be recovered from inputs.

---

## Additional preregistration defects found

### Defect 1: Null-case exclusion ambiguity

The preregistration says:
> "If a shuffled bridge is found to be a valid connection, the case is flagged and excluded from analysis."

But also:
> "If any null case violates matching properties, label the experiment INCONCLUSIVE — INVALID NULL."

These are different rules applied to the same situation. Post-result exclusion is dangerous.

**Required correction:**
```text
All 20 true cases and all 20 null cases are immutable once generated.
No case may be removed after execution.
If null validity fails, the entire study is INCONCLUSIVE.
```

### Defect 2: Decision rule has a logical hole

Current rules:
- DISCRIMINATIVE: Δ ≥ 0.20 AND CI_lower > 0 AND FPR ≤ 0.30
- NOT_DISCRIMINATIVE: Δ < 0.20 OR CI_lower ≤ 0

The case Δ=0.40, CI_lower>0, FPR=0.50 satisfies neither.

**Required correction — exhaustive partition:**
```text
IF null_validity == FAILED:
    INCONCLUSIVE_INVALID_NULL

ELSE IF Δ >= 0.20 AND CI_lower > 0 AND FPR <= 0.30:
    DISCRIMINATIVE

ELSE:
    NOT_DISCRIMINATIVE
```

### Defect 3: No power justification for N=20

The preregistration treats N=20 as sufficient without demonstrating it can resolve the proposed Δ threshold.

**Required correction:** Either calculate expected resolution or explicitly classify as:
```text
N=20 is exploratory / low-powered.
```

### Defect 4: "Matched null" does too much work

The null is structurally matched on document length, domain distribution, etc. But `_bridge_matches()` sees only strings — those structural properties are invisible to the scorer.

**Required correction:** Distinguish:
```text
STRUCTURAL_MATCHING_OF_CASES (properties of the case design)
INFORMATION_VISIBLE_TO_SCORER (what the matcher actually observes)
```

---

## Status

```text
PROTOCOL_VALIDITY = INVALID_FOR_RELATIONSHIP_DISCRIMINATION
CURRENT_PREREGISTRATION = SUPERSEDED_DRAFT
PHASE_8_EXECUTION = BLOCKED
M-008 = FULL_QUARANTINE (unchanged)
DXP-005 = PAUSED (unchanged)
NORTH_STAR = NOT_ACHIEVED (unchanged)
```

The current preregistration is preserved as a superseded draft. Two new protocols (A: lexical, B: discovery) must be designed, audited, and preregistered before any execution.

This finding does NOT invalidate the governance work from Phases 0-7. The freeze mechanism, epistemic gate, and consumer-boundary enforcement are all still valid. The defect is in the experimental design, not the governance infrastructure.
