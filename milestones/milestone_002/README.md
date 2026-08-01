# Milestone 002 — Improved electrolyte composition for a Zn-Cu galvanic cell

**Status:** open (not yet executed)
**Class:** B (invention)
**Loop closes:** Loop 4 (experimentation), contributes to Loop 5 (creation)
**Estimated cost:** $50
**Estimated time:** 2 days

This is the first **Class B (invention) milestone**. Per CTO review #6:

> Class B milestones verify that the system can generate useful
> blueprints (improved electrolyte, catalyst, material, manufacturing
> process). The fifth criterion: "Does the experiment teach the
> system how to invent?"

This milestone satisfies all 5 criteria: inexpensive, measurable,
reproducible, executable within days, AND teaches the system how to
invent.

## The baseline

A standard Zn-Cu galvanic cell with 5% NaCl-water electrolyte. The
expected open-circuit voltage is ~0.85V (high-school chemistry demo).

## The improvement claim (a Hypothesis)

The system proposes replacing the NaCl electrolyte with 5% citric-acid
electrolyte, claiming the open-circuit voltage will increase by at
least 0.10V (i.e., to at least 0.95V).

The Hypothesis carries:
- `claim`: "Replacing the 5% NaCl electrolyte with a 5% citric-acid
  electrolyte will increase the Zn-Cu galvanic cell open-circuit
  voltage by at least 0.10V compared to the NaCl baseline."
- `confidence`: 0.45
- `evidence`: 9 named items (chemistry knowledge module's
  electrochemistry + Nernst equation + K_eq; citric acid pKa1=3.13;
  Zn oxidation potential -0.76V; Cu reduction potential +0.34V;
  theoretical max voltage 1.10V; overpotential analysis)
- `counterevidence`: 4 items (weak-acid limitation, H+ diffusion rate,
  Zn-acid side reaction, internal resistance)
- `assumptions`: 4 items (clean electrodes, 25C, high-impedance
  multimeter, comparable concentrations)
- `status`: pending

## The measurement plan

A human constructs both cells per the procedure in `spec.json`:
1. Baseline: Zn + Cu in 5% NaCl, measure voltage 3 times.
2. Proposed: Zn + Cu in 5% citric acid, measure voltage 3 times.
3. Compute mean baseline and mean proposed; the improvement is
   `proposed_mean - baseline_mean`.

Pass criterion: `proposed_mean - baseline_mean >= 0.05V` (half the
predicted 0.10V, to tolerate measurement noise).

## What closes when this milestone completes

- Loop 4 (experimentation): CLOSED — the first real Class B
  experimentation cycle. The system proposed an improvement, a human
  tested it, measurements were recorded, and the improvement claim
  was reconciled (pass or fail) into the ledger.
- Loop 5 (creation): CONTRIBUTED TO — if the improvement is
  confirmed, the system has generated a (small but real) invention:
  an improved electrolyte composition that a person could use.
  This is the substrate of the invention compiler's value proposition.

## Why this is Class B, not Class A

Class A milestones (like milestone_001, the pH prediction) verify the
machinery works mechanically — they measure a property. Class B
milestones verify the system can generate useful blueprints — they
test whether the system's PROPOSAL is correct.

The distinction matters: a system that can measure pH but cannot
propose an improved electrolyte is a measurement tool, not an
invention compiler. The Class B milestone is what tests the
invention capability.

## Next action

When a human is ready to execute the experiment:

1. Run the procedure in `spec.json` → `measurement_plan` → `procedure`.
2. Record the 6 voltage readings in `result.json` (template below).
3. Run `scripts/close_milestone_002.py` (to be implemented when a
   result is recorded). That script will:
   - Load the baseline + improvement_claim from `spec.json`.
   - Load the measurements from `result.json`.
   - Compute the improvement (proposed_mean - baseline_mean).
   - Reconcile the Hypothesis (pass or fail).
   - Append a verification entry to `data/ledger/predictions.jsonl`
     with type="verification", outcome="pass"|"fail", and the
     prediction + measurement attached.
   - Mark this milestone's status as "closed" in `spec.json`.
   - If pass: also update the Loop 5 (creation) status, because the
     system has generated a useful blueprint.

## result.json template (to be filled in by the human experimenter)

```json
{
  "milestone_id": "milestone_002",
  "executed_at": "ISO8601 UTC when the experiment was run",
  "experimenter": "name of the person who ran it",
  "baseline_trials": [
    {"trial": 1, "measured_voltage_V": <float>},
    {"trial": 2, "measured_voltage_V": <float>},
    {"trial": 3, "measured_voltage_V": <float>}
  ],
  "proposed_trials": [
    {"trial": 1, "measured_voltage_V": <float>},
    {"trial": 2, "measured_voltage_V": <float>},
    {"trial": 3, "measured_voltage_V": <float>}
  ],
  "notes": "any observations (electrode condition, reaction vigor, etc.)"
}
```

## Why this milestone matters

Per the CTO: "A pH measurement may validate the experimental loop,
but it may not validate the invention loop."

This milestone validates the invention loop. The improvement is
small (+0.10V on a galvanic cell) and the science is well-known —
but the test is whether the SYSTEM's proposal is correct. If the
system's proposal is confirmed, the system has generated a useful
material-composition blueprint. If the proposal is falsified, the
system learns that citric acid does not improve galvanic cell
voltage — which is also valuable information.

Either way, the system learns. That is the substrate of a learning
system, and the point at which the repository stops describing the
world and starts learning from it.
