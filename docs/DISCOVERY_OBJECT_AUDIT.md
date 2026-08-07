# Discovery Object Audit — Phase VI.5

## DR-91 Phase VI.5: What exactly IS a "discovery"?

Per CTO review (post-Phase VI+VII):

> "Your benchmark currently scores Discovery → Entity.
> But the invention engine never invents entities.
> It invents mechanisms, constraints, predictions, experiments.
> Discovery should probably be scored the same way.
>
> If you redefine the benchmark object first, then the remaining
> phases will be evaluating the capability you actually care about,
> rather than a proxy that has now been shown to fail catastrophically."

## The Problem (formally stated)

The current benchmark scores:

```
Entity(bridge_concept) ∈ ExtractedEntities
```

This checks whether a NOUN appears in the extracted entity pool.
With 143 entities, any noun matches something. FP = 1.0.

The benchmark SHOULD score:

```
BridgeProposal {
    mechanism: "X causes Y via Z"
    shared_variables: [v1, v2, ...]
    prediction: "if Z holds, then W"
    falsification: "if not-Z, then not-W"
    evidence: [source_a, source_b]
}
```

This checks whether the engine PROPOSED a cross-domain connection
with a mechanism, not whether a noun was extracted.

## Four Competing Hypotheses (from CTO)

The Phase VI experiment showed FP=1.0 regardless of matching component.
This is consistent with four hypotheses:

| Hypothesis | Description | Consistent with data? |
|-----------|-------------|----------------------|
| H1: Entity extractor too permissive | 143 entities = noise | YES |
| H2: Bridge definition too weak | "charge transfer" matches "charge transport" | YES |
| H3: Gold bridges underspecified | Single nouns like "conductivity" occur everywhere | YES |
| H4: Discovery object is wrong | Scoring entities (nouns) instead of proposals (claims) | YES |

H4 is the most fundamental. If the benchmark scores nouns instead of
claims, FP=1.0 is inevitable — not because of extraction noise, but
because nouns are too coarse to discriminate discoveries from
non-discoveries.

## The Redefined Discovery Object

### Current (broken) object

```python
class Discovery:
    bridge: str  # a noun phrase, e.g., "thermal_emission"
```

Matching: does this noun appear in extracted entities?

Problem: nouns are ubiquitous. "Thermal" appears in 50+ entities.
FP = 1.0 is guaranteed.

### Proposed (correct) object

```python
class BridgeProposal:
    # The MECHANISM: what connects the two domains
    mechanism: str  # "Reducing grain size below 50nm increases ZT
                    #  when κ > 1.0, because phonon scattering
                    #  reduces lattice thermal conductivity"

    # The SHARED VARIABLES: what the two domains have in common
    shared_variables: List[str]  # ["grain_size", "thermal_conductivity"]

    # The PREDICTION: what should happen if the mechanism is correct
    prediction: str  # "If grain_size < 50nm AND κ > 1.0, then ZT increases"

    # The FALSIFICATION: what would prove the mechanism wrong
    falsification: str  # "If grain_size < 50nm AND κ > 1.0
                        #  AND ZT does NOT increase, mechanism is false"

    # The EVIDENCE: which sources support each component
    evidence: List[str]  # ["source_a: grain size affects κ",
                         #  "source_b: ZT depends on κ"]
```

Matching: does the engine PROPOSE a mechanism that connects domain A
to domain B via shared variables, with a testable prediction?

This is FAR harder to fake:
- A random noun cannot produce a mechanism
- A plausible-sounding phrase cannot generate a falsifiable prediction
- The proposal must connect TWO domains, not just mention a concept

## Why This Matters

The invention engine already generates mechanisms, constraints, and
predictions (invention_compiler/causal_graph.py, forward_model.py).
The discovery benchmark should score the SAME type of object.

Currently there's a mismatch:
- Invention engine: generates BridgeProposals (mechanism + prediction)
- Discovery benchmark: scores Entities (nouns)

This mismatch is WHY the benchmark fails. The benchmark is measuring
a proxy (entity extraction) that is too coarse to capture the actual
capability (cross-domain bridge proposal).

## Impact on Prior Conclusions

If the discovery object is redefined from Entity to BridgeProposal:

1. **Discovery F1=0.9189** becomes meaningless — it measured entity
   recognition, not bridge proposal. The honest score under the new
   object is UNKNOWN (must be re-measured).

2. **H1-H4 saturation (cycles 230-239)**: NOT affected. These were
   based on the blind suite (optimizer performance), not discovery F1.

3. **DR-90 representation discovery**: must wait until the benchmark
   measures the right object. If the benchmark measures entities,
   representation improvements won't show up (entities are too coarse).

4. **Maturity assessments**: Discovery rating (9.0/10) must be
   marked "UNVERIFIED — benchmark measured entity recognition, not
   bridge proposal. True discovery capability unknown."

## Next Steps (revised DR-91 roadmap)

```
Phase I-VII   ✓  (completed — benchmark proven NOT TRUSTWORTHY)
Phase VI.5    ←  THIS DOCUMENT (discovery object audit)
Phase VIII    External reference benchmark (with NEW object)
Phase IX      Historical recalibration (with NEW object)
Phase X       Scientific reassessment
FINAL VERDICT
```

The key insight: before building external baselines (Phase VIII),
we must first define what they're benchmarking. If we benchmark
entities, any system that extracts nouns will score well. If we
benchmark BridgeProposals, only systems that propose mechanisms
with testable predictions will score well.

## Formal Definition

A **Discovery** is a BridgeProposal that:

1. Identifies a MECHANISM connecting domain A to domain B
2. Specifies SHARED VARIABLES that appear in both domains
3. Makes a PREDICTION that is testable
4. Provides a FALSIFICATION criterion
5. Cites EVIDENCE from both source domains

An **Entity** is NOT a Discovery. It is a recognition that a noun
exists in text. Entities are necessary but not sufficient for
discovery — they're the building blocks, not the result.

## The Honest Claim (revised)

Previous claim: "Discovery F1 = 0.9189"
Honest revision: "Entity recognition F1 = 0.97 (token overlap).
Bridge proposal F1 = UNKNOWN (not measured). The benchmark measured
entity recognition, not discovery. The true discovery capability
of the engine is UNVERIFIED."
