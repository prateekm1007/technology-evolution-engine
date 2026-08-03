# HISTORICAL_VALIDATION_PROTOCOL — Phase 7D

**Status:** validation protocol (constitutional).
**Phase:** 7D.

> Establish predictive discipline.
> — CEO authorization, Phase 7D

This document defines the frozen-time backtest methodology for
the CAPABILITY_MODEL. It is the ultimate falsification test.

---

## 1. The methodology

```text
year = T

knowledge = data available at T (ONLY data with publicationDate <= T)

prediction = ranked possibilities (using Readiness, Novelty, Feasibility scores
             computed with ONLY data available at T)

evaluation = outcomes at T+n (what actually happened, measured at T+n)
```

### What this means

- At year T, the system's knowledge is the graph restricted to
  nodes/edges with `validFrom <= T`.
- The system computes Readiness, Novelty, and Feasibility for
  candidate capability combinations using ONLY that historical state.
- The system ranks the candidates.
- At T+n (n = 5 to 10 years), we check: did the predicted combinations
  actually materialize?

---

## 2. Backtest points

```text
T = 1995, 2000, 2005, 2010, 2015, 2020
```

At each T, snapshot the graph as-of T. Generate predictions. Evaluate
at T+5 to T+10.

---

## 3. Required metrics

Per CEO authorization:

```text
precision       = true_positives / (true_positives + false_positives)
recall          = true_positives / (true_positives + false_negatives)
false_positives = flagged but didn't happen
false_negatives = happened but weren't flagged
specificity     = true_negatives / (true_negatives + false_positives)
calibration     = predicted probability vs observed frequency
```

### Why precision matters most

Per the external review:

> Given the transistor's inputs existed, you can construct hundreds
> of other component-combinations from 1946 that look equally
> convergent by any metric and that never became anything. If you
> don't measure how many of those your system also flags, a positive
> result tells you almost nothing.

The system must measure false positives — not just true positives.
A system that flags 1000 combinations and gets 10 right has 1%
precision. A system that flags 20 and gets 10 right has 50%
precision. The second is more useful, even though recall is lower.

---

## 4. Forbidden methodology

Per CEO authorization:

```text
inventor hindsight      — looking up what the inventor said they intended
post hoc reasoning       — explaining why something happened after the fact
manual cherry-picking    — selecting only the cases where the system was right
transistor stories       — narrative validation without metrics
retrospective explanations — "of course it would predict X, because..."
```

### Why these are forbidden

- **Inventor hindsight:** the inventor's stated intent is not
  available to the system at time T. Using it in the backtest is
  information leakage.
- **Post hoc reasoning:** the system must predict BEFORE the outcome,
  not explain AFTER. "Of course it would predict X" is not a
  prediction — it's a rationalization.
- **Manual cherry-picking:** selecting only the cases where the
  system was right inflates precision. The system must report ALL
  flagged combinations, not just the successful ones.
- **Transistor stories:** a single anecdote ("the system predicted
  the transistor!") is not validation. The system must report
  precision/recall across the full ranked list, not just the
  highlight reel.
- **Retrospective explanations:** "the system would have predicted
  X because the inputs were available" is not a prediction. The
  system must generate the prediction FROM the inputs, not from
  knowledge of the outcome.

---

## 5. Success criteria (CAPABILITY_MODEL vs CO_OCCURRENCE_MODEL)

The CEO's authorization defines the comparison:

| Criterion | Requirement |
|---|---|
| Precision | CAPABILITY_MODEL > CO_OCCURRENCE_MODEL |
| False positives | CAPABILITY_MODEL < CO_OCCURRENCE_MODEL |
| Interpretability | CAPABILITY_MODEL > CO_OCCURRENCE_MODEL |
| Reproducibility | CAPABILITY_MODEL ≥ CO_OCCURRENCE_MODEL |
| Explanatory power | CAPABILITY_MODEL > CO_OCCURRENCE_MODEL |

### How to measure each

- **Precision:** run both models on the same backtest points.
  Compare precision at each point.
- **False positives:** same — compare FP counts.
- **Interpretability:** can the system explain WHY it flagged a
  combination? The CAPABILITY_MODEL traces evidence (EVIDENCE_PROTOCOL).
  The CO_OCCURRENCE_MODEL traces shared labels. Evidence > labels
  for interpretability.
- **Reproducibility:** both models must be deterministic (same input →
  same output). The CAPABILITY_MODEL is deterministic (manual
  extraction + typed edges). The CO_OCCURRENCE_MODEL is deterministic
  (keyword matching + formula). Reproducibility should be equal.
- **Explanatory power:** the CAPABILITY_MODEL distinguishes Readiness,
  Novelty, and Feasibility independently. The CO_OCCURRENCE_MODEL
  blends them into one number. Three independent scores > one
  blended score for explanatory power.

---

## 6. Failure criteria

Per CEO authorization:

```text
ontology explosion       — node/edge types exceed ONTOLOGY_FREEZE caps
inability to explain      — system flags a combination but cannot trace why
deterioration of precision — CAPABILITY_MODEL precision < CO_OCCURRENCE_MODEL
excessive false positives — FP rate higher than CO_OCCURRENCE_MODEL
inability to replay       — same input produces different output
inability to trace evidence — nodes/edges lack evidence citations
```

If ANY of these occur, the experiment is unsuccessful. The
CAPABILITY_MODEL has not defeated the CO_OCCURRENCE_MODEL. H0
(capability-centric architecture is not worth the cost) is
reinstated.

---

## 7. What this document does NOT do

- It does NOT execute the backtest (the corpus is not yet ingested).
- It does NOT define the specific combinations to predict (those
  emerge from the graph at time T).
- It does NOT authorize code (the scoring code must be built first,
  following the protocols in Phase 7C).
- It defines the METHODOLOGY and the METRICS, so that when the
  backtest is run, the results are comparable and falsifiable.

---

## 8. The ultimate test

> Do not attempt to build the machine that changes the world.
> Build the smallest machine capable of proving that the larger
> machine is possible.
> — CEO authorization, Phase 7

The frozen-time backtest IS that proof. If the CAPABILITY_MODEL,
on 50 patents + 50 papers + 10 products in one vertical, produces
higher precision and lower false positives than the
CO_OCCURRENCE_MODEL on the same data, then the architecture is
worth scaling. If it doesn't, it isn't.

This is Law 8 (verification standard) applied at the architectural
level: no "validated" label without a successful prediction, a
failed prediction, and replayable evidence.
