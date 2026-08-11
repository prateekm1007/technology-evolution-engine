# Milestone 001 — pH prediction of citric-acid + sodium-bicarbonate mixture

**Status:** open (not yet executed)
**Loop closes:** Loop 4 (experimentation)
**Estimated cost:** $20
**Estimated time:** 1 day

This is the first milestone. Per CTO review #5, it satisfies the four
small-milestone criteria:

- **inexpensive** — $20 of materials (citric acid, baking soda, pH strips)
- **measurable** — produces a numeric pH value (range 0-14)
- **reproducible** — anyone with the materials can repeat it
- **executable within days** — 1 day end-to-end

## The prediction

The system predicts that 1g citric acid + 2g sodium bicarbonate in
100mL distilled water at 25C will produce a mixture with pH in the
range 6.0-7.0 (center: 6.5). The prediction is encoded as a
Hypothesis in `spec.json` with confidence=0.55, supported by 6 named
pieces of evidence (including the chemistry knowledge module's
acid-base neutralization pathway, the K_eq equilibrium model, the
Arrhenius kinetics model, citric-acid pKa, sodium-bicarbonate pKb,
and a stoichiometric calculation showing NaHCO3 in 4.5x molar excess).

The prediction also carries 3 named counterevidence items
(multi-step deprotonation, CO2 evolution, temperature-dependence of
pKa) and 4 assumptions (distilled water, open container, pH strip
accuracy, room temperature).

## The measurement plan

A human constructs the mixture per the procedure in `spec.json`,
dips a pH strip, and records the reading. The procedure includes
3 trials for reproducibility. The pass criterion is
`abs(measured_pH - 6.5) <= 1.0 AND all 3 trials agree within +/-0.5`.

## What closes when this milestone completes

- Loop 4 (experimentation): CLOSED — the first real experimentation
  cycle. The system proposed a hypothesis, a human ran the experiment,
  measurements were recorded, prediction error was computed, and the
  hypothesis was reconciled (pass or fail) into the ledger.
- Loop 5 (creation): unchanged. This is a measurement, not a prototype
  build. Creation remains OPEN.

## Next action

When a human is ready to execute the experiment:

1. Run the procedure in `spec.json` → `measurement_plan` → `procedure`.
2. Record the pH reading (and the 3 trials) in `result.json` (template below).
3. Run `scripts/close_milestone_001.py` (to be implemented when a result
   is recorded). That script will:
   - Load the prediction from `spec.json`.
   - Load the measurement from `result.json`.
   - Compute prediction error.
   - Reconcile the Hypothesis (pass or fail).
   - Append a verification entry to `data/ledger/predictions.jsonl`
     with type="verification", outcome="pass"|"fail", and the
     prediction + measurement attached.
   - Mark this milestone's status as "closed" in `spec.json`.

## result.json template (to be filled in by the human experimenter)

```json
{
  "milestone_id": "milestone_001",
  "executed_at": "ISO8601 UTC when the experiment was run",
  "experimenter": "name of the person who ran it",
  "trials": [
    {"trial": 1, "measured_pH": <float>},
    {"trial": 2, "measured_pH": <float>},
    {"trial": 3, "measured_pH": <float>}
  ],
  "notes": "any observations (e.g., reaction vigor, CO2 evolution time, temperature drift)"
}
```

## Why this milestone matters

Per the CTO: "The first successfully completed cycle will be much
more valuable than another hundred modules. That is the point at
which the repository stops merely describing the world and starts
learning from it."

When this milestone closes, the system will have, for the first
time, predicted something about the real world, had that prediction
tested by an actual experiment, and recorded the outcome. That is
the substrate of a learning system. Everything before this milestone
is description; everything after is learning.
