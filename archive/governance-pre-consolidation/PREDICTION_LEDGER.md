# PREDICTION_LEDGER

**Status:** Phase 14B protocol.
**Location:** repo root.
**Phase:** 14B.

> Every prediction must be committed before evaluation.
> — CEO directive, Phase 14B

---

## Purpose

The prediction ledger records every prediction the model makes,
with a timestamp, a confidence, a rationale, and a status. The
status field is the binding commitment: once a prediction is
committed with status `PENDING`, the prediction cannot be
edited, the rationale cannot be amended, and the confidence
cannot be adjusted. Only the status field changes (from
`PENDING` to `CORRECT` or `INCORRECT`) when the evaluation
window closes.

This enforces EP-3 (forward-only preconditions) at the
prediction level. A prediction committed at time T cannot be
influenced by events that occur after T, because the prediction
is already in the ledger.

---

## Schema

```typescript
interface Prediction {
    timestamp: string;

    domain: string;

    prediction: string;

    confidence: number;

    rationale: string[];

    status:
        | "PENDING"
        | "CORRECT"
        | "INCORRECT";
}
```

### Field semantics

| Field | Type | Required | Meaning |
|---|---|---|---|
| `timestamp` | string (ISO 8601) | yes | When the prediction was committed. Includes commit hash. |
| `domain` | string | yes | Which domain (li_ion, photovoltaics, semiconductors, telecommunications, aviation, pharmaceuticals). |
| `prediction` | string | yes | The specific claim. Must be falsifiable: must specify what event will occur (or not occur), in what time window, with what combination. |
| `confidence` | float (0.0–1.0) | yes | The model's confidence in the prediction. For Top-10 predictions, `1 - (rank / total_ranked)`. For susceptibility predictions, the normalized score. |
| `rationale` | string[] | yes | The reasons for the prediction. Must cite: (a) which capabilities are rising, (b) what adjacency is closing, (c) what bottleneck is weakening. Cannot be amended after commitment. |
| `status` | enum | yes | `PENDING` (within evaluation window), `CORRECT` (event occurred), `INCORRECT` (event did not occur within window). |

### What this schema forbids

- Editing a prediction after commitment. The timestamp field is
  immutable. If a prediction needs amendment, a new prediction
  is committed with a new timestamp, and the old one remains
  `PENDING` until its window closes (then marked `INCORRECT`).
- Committing a prediction without a rationale. "High score" is
  not a rationale. The rationale must explain WHY the score is
  high in landscape terms (what is changing, what is reachable).
- Committing a prediction with status other than `PENDING`.
  All new predictions are `PENDING` until evaluated.

---

## Prediction types

### Type 1: Top-10 event prediction (inevitability metric)

The model predicts that a specific capability combination will
produce an invention event within the 5-year horizon. This is
the metric used in all prior backtests.

- `prediction`: "Combination {X, Y, Z} will produce an invention
  event between T+1 and T+5."
- `confidence`: `1 - (rank / total_ranked)` at time T.
- `status` flips to `CORRECT` if an event in EVENT_REGISTRY
  matches the combination within the window; `INCORRECT`
  otherwise.

### Type 2: Susceptibility prediction (new metric)

The model predicts that a specific capability landscape is
susceptible to invention — meaning the conditions for invention
are present. This does NOT predict that an event will occur;
it predicts that the landscape is in a state where invention
is possible.

- `prediction`: "At time T, the landscape containing
  capabilities {X, Y, Z} is susceptible to invention, defined
  as: velocity > 0.20 AND adjacency > 0.5 for at least one
  capability in the combination."
- `confidence`: the normalized `max(dTRL/dt) × adjacency` score.
- `status` flips to `CORRECT` if the susceptibility conditions
  are met at T (regardless of whether an event occurs); 
  `INCORRECT` if the conditions are not met. Note: this is a
  landscape-state prediction, not an event prediction. It is
  evaluated against the trajectory registry, not the event
  registry.

### Type 3: Impossibility prediction (inverse metric)

The model predicts that a specific capability combination CANNOT
produce an invention event, because a blocking constraint is
active.

- `prediction`: "Combination {X, Y, Z} cannot produce an invention
  event at time T, because constraint C is active."
- `confidence`: 1.0 if the constraint is physical (thermal
  runaway, energy density ceiling); 0.7 if economic; 0.5 if
  regulatory.
- `status` flips to `CORRECT` if no event occurs within the
  window AND the constraint is documented as active; `INCORRECT`
  if an event occurs despite the constraint (indicating the
  constraint was not actually blocking).

---

## Evaluation protocol

For each `PENDING` prediction:

1. **At commitment (time T):** the prediction is added to the
   ledger with status `PENDING`. The commit hash is recorded.
2. **At T+5 (or the domain-specific horizon):** the evaluation
   runs. For Type 1, check EVENT_REGISTRY for a matching event.
   For Type 2, check TRAJECTORY_REGISTRY for the susceptibility
   conditions. For Type 3, check both.
3. **After evaluation:** the status field is updated to
   `CORRECT` or `INCORRECT`. The rationale and confidence
   fields are NOT modified. A new entry is added to the
   `evaluation` array (see below) recording when the evaluation
   ran and what it found.

### Evaluation record (appended, not a schema field)

```typescript
interface Evaluation {
    evaluated_at: string;     // ISO timestamp + commit hash
    evaluated_by: string;     // "coder" or "external_reviewer"
    evidence: string;          // citation to EVENT_REGISTRY or TRAJECTORY_REGISTRY
    status_change: "PENDING → CORRECT" | "PENDING → INCORRECT";
}
```

---

## Initial predictions (to be populated per domain)

The ledger starts empty. Predictions are added as each domain's
stress test runs. For each domain:

1. Build the domain ontology + event registry + trajectory
   registry.
2. Run the frozen formula at each T-point.
3. Commit the Top-10 predictions as Type 1 entries (PENDING).
4. Commit the susceptibility predictions as Type 2 entries
   (PENDING).
5. After the 5-year horizon passes (for historical backtests,
   this is immediate — the events are already in the registry),
   evaluate and update status.

### Historical vs forward predictions

For historical backtests (semiconductors, telecom, aviation,
pharma), the events are already known. The "blind prediction"
requirement (14B) means: the predictions are committed BEFORE
checking against the event registry. The forward-only protocol
(EP-3) is satisfied because the formula runs on trajectory
data up to time T, and the event check is against events in
(T, T+5] — events the formula did not see.

For forward predictions (if any are made for current or future
years), the predictions are committed now and evaluated when
the 5-year window closes. These are the only predictions that
can satisfy M5's "confirmed by reality" criterion.

---

## Enforcement

- A prediction without a timestamp (including commit hash) is
  invalid. Per EP-1, no artifact = no claim.
- A prediction whose rationale cites post-T information is
  invalid (EP-3 violation). The rationale must reference only
  data available at time T.
- A prediction whose status is updated without an evaluation
  record is invalid (EP-1 + EP-12).
- This ledger is append-only (Law 7). Predictions are never
  deleted; statuses are never changed except via the evaluation
  protocol.
