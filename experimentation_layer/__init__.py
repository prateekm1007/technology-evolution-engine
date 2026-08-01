"""
Experimentation Layer — the loop that closes the invention compiler.

STATUS: SCAFFOLD. Declared but NOT implemented. Per CTO review #3
(commit `b22cbc6`), this package exists as a documented target
toward which the entire repository should converge. It does not
yet do anything.

# Why this layer exists

The CTO observed that the architecture was converging toward four
interacting layers:

    Observation layer       (knowledge acquisition: graph, evidence, failures)
            ↓
    Knowledge layer         (encoded laws, equations, pathways)
            ↓
    Reasoning layer         (causal analysis, counterfactuals, simulation)
            ↓
    Blueprint layer         (composed 11-layer output)

But the loop is not complete until the system can ask:

    What should we build?
    How should we build it?
    What experiment should we run?
    What did we learn?
    How should the blueprint change?

That requires a fifth layer:

    Experimentation layer  (the loop: predict -> build -> observe -> learn)

# What "implemented" means

This layer is NOT implemented when:
  - It exists only as a docstring.
  - It declares functions but the functions raise NotImplementedError.
  - It has no tests for an actual predict -> build -> observe -> learn
    cycle on a real invention.

This layer IS implemented when:
  - At least one real invention has been pushed through the full loop.
  - The build outcome (pass/fail) is recorded in the verification
    ledger (data/ledger/predictions.jsonl) per Law 8.
  - The blueprint for that invention was revised based on what was
    learned.

Until those conditions are met, the system is an invention catalog,
not an invention laboratory. The Creation benchmark level (5th level
of the CTO-mandated benchmark hierarchy) cannot be marked
"expectations_satisfied" until this layer is implemented.

# The loop, in detail

    predict    — use the InventionCompiler to produce a blueprint for
                 a candidate invention. The blueprint is a PREDICTION
                 that the invention can be built.

    build      — actually construct a prototype (or commission an
                 external team to do so). This step is OUTSIDE the
                 system; the system only records the request and
                 awaits the outcome.

    observe    — record the build outcome: did the prototype work?
                 What failed? What surprised us? The observation is
                 appended to the ledger as a verification entry with
                 outcome="pass" or outcome="fail".

    learn      — compare the prediction to the observation. If they
                 disagree, identify which layer of the blueprint was
                 wrong (was the prerequisite chain incomplete? was
                 the governing equation wrong? was the cost model
                 wrong?). Update the relevant module.

    revise     — re-compile the same problem with the updated module.
                 The new blueprint is the next prediction. The loop
                 repeats.

# Relationship to Law 8

Law 8 (CONSTITUTION.md): "No 'verified' label without a successful
prediction, a failed prediction, and replayable evidence."

The verification cycle (scripts/run_verification_cycle.py) currently
uses HISTORICAL failures as ground truth. That's a valid
predict->observe->reconcile loop, but the observations are
pre-existing (we didn't run the experiment, we read about it).

The Experimentation layer is the same loop with LIVE experiments:
the system proposes, someone builds, the system observes and learns.
That's a strictly higher bar than the historical verification cycle,
and it's the bar at which the system can honestly claim to be an
invention laboratory.

# First concrete deliverable

The first concrete deliverable of this layer is: a single closed
loop on one real invention. The invention should be small enough to
build in weeks, not years (e.g., a specific sensor design, a
specific material sample). The loop should:
  - Produce a blueprint.
  - Be built by a human (or external team).
  - Record the outcome (pass/fail) in the ledger.
  - Trigger a module update if the prediction was wrong.
  - Re-compile the same problem and produce a revised blueprint.

Until that loop exists, this package is a scaffold and a docstring.
"""
