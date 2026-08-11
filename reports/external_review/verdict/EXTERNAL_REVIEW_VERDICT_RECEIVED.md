# External Review Verdict — Received

## Date
2026-08-08

## Verdict
PREMATURE — DO NOT CALL IT AN AI DISCOVERY/INVENTION ENGINE YET

## Reviewer
Independent external reviewer (not the repository authors)

## Key finding (deeper than Stage −1)

The current evaluated "discovery" mechanism is fundamentally an
entity-overlap / recognition pipeline. The gold snippets frequently
already contain the underlying bridge concept in paraphrased form.

Even a perfectly repaired scorer applied to the current
discover_shared_entities() benchmark would not by itself establish
independent invention.

The problem is not merely a scoring bug — it is a construct-validity
problem. The benchmark tests entity intersection, not generation of
a novel bridge.

## Answers to the six questions

Q1: Does the system produce proposals not explicitly present in inputs?
    NO — not demonstrated. discover_shared_entities() constructs
    proposals from extracted entities already present in inputs.

Q2: Are those proposals genuinely novel?
    NO — not demonstrated. Gold relationships are known published
    relationships. Evaluated outputs are mostly recognition of concepts
    already expressed in supplied snippets.

Q3: Does the engine outperform recognition/retrieval baselines?
    UNKNOWN — no evidence supplied demonstrates superiority over
    entity-overlap/retrieval baseline.

Q4: Does it outperform human researchers?
    UNKNOWN — no valid controlled human comparison performed.

Q5: Can the result be independently reproduced?
    PARTIALLY — source-level claims inspectable; runtime reproduction
    unverified by reviewer (environment limitation).

Q6: Is there sufficient evidence to call this an AI discovery engine?
    PREMATURE — evidence does not isolate discovery from entity
    extraction, semantic recognition, lexical overlap, retrieval, or
    benchmark construction.

## What the reviewer found beyond Stage −1

1. The discovery operator (discover_shared_entities) cannot generate
   a concept absent from the inputs. It does entity intersection.

2. The gold snippets contain semantic leakage — bridge concepts are
   present in paraphrased form (e.g., "thermal regulation" ≈
   "stable thermal conditions" ≈ "thermal management").

3. The circularity gate only detects lexical leakage, not semantic
   or conceptual leakage.

4. Three operations are conflated: entity extraction, entity
   intersection, and relation discovery. Only the first two are
   implemented.

## What the reviewer recommends next

NOT: "Repair the scorer and get F1 above 0.9."

INSTEAD: "Construct a genuinely blind proposal task in which the
correct cross-domain relationship is absent from the input
representations, require the engine to generate the relationship
rather than retrieve/intersect it, and have independent experts
determine whether the resulting proposal is genuinely novel and
scientifically meaningful."

## Three-gate protocol proposed by reviewer

Gate A — Novel proposal: Did the system propose something not
         explicitly represented in the inputs?

Gate B — Novel knowledge: Was that proposal genuinely absent from
         prior literature?

Gate C — Valid knowledge: Does the proposed relationship survive
         expert/scientific scrutiny?

Only A=PASS, B=PASS, C=PASS should count as genuine discovery.

## Disposition

| Area | Verdict |
|---|---|
| Stage −1 measurement audit | PASS |
| Evidence preservation | PASS |
| Production benchmark left frozen | PASS |
| External-review independence protocol | PASS |
| Current scorer validity | FAIL |
| Proposal-locus integrity | FAIL |
| False-positive measurement | FAIL |
| Matcher validity for scientific discovery | FAIL |
| Semantic leakage control | FAIL |
| Actual novel-proposal generation demonstrated | NO |
| Novelty demonstrated | NO |
| Human superiority demonstrated | UNKNOWN |
| Generic/retrieval baseline superiority | UNKNOWN |
| World-class discovery capability demonstrated | NO |
| Evidence that project could eventually become one | Plausible, but unproven |

## State

AWAITING_INDEPENDENT_REVIEW → REVIEW_RECEIVED

The development freeze remains in force. No production code, benchmark,
gold set, or scorer may be modified until the next scientific protocol
is designed and approved.

The 0.5714 score remains frozen as historical baseline. It is not
deleted, not corrected, not advertised. It is evidence of a
measurement methodology that has been found invalid for
independent-discovery claims by both internal Stage −1 audit and
external independent review.
