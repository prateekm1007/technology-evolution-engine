"""
layer_status package — the honest layer-status table.

Per CTO review #6 (commit `874ec10`), the system's 7 layers must be
honestly assessed against 4 status values:

  - not_started  — no infrastructure exists for this layer.
  - scaffolded   — infrastructure exists (classes, packages,
                   docstrings) but no real-world cycle has run
                   through it.
  - partial      — infrastructure exists AND at least one cycle has
                   run on historical/synthetic data, but no real-
                   world outcome has confirmed a prediction.
  - closed       — infrastructure exists AND at least one real-world
                   cycle has confirmed a prediction.

The current honest assessment (per CTO review #6):

  | Layer           | Status      |
  | --------------- | ----------- |
  | Observation     | Partial     |
  | Knowledge       | Partial     |
  | Reasoning       | Partial     |
  | Blueprint       | Partial     |
  | Simulation      | Partial     |
  | Experimentation | Scaffolded  |
  | Creation        | Not started |

This file is the canonical source of that table. Other modules
(loop status, audit reports) should import from here so the
honest assessment is consistent across the system.

# When to update this table

The status of a layer changes when:

  - not_started → scaffolded: infrastructure for the layer is added
    (a package is created, a class is defined, a docstring is
    written).
  - scaffolded → partial: at least one cycle runs through the layer
    on historical/synthetic data. E.g., the verification cycle
    running on 9 historical failures moves the Reconstruction loop
    from scaffolded to partial (and the Observation layer along
    with it).
  - partial → closed: at least one cycle runs through the layer on
    REAL-WORLD data and the prediction is confirmed by an external
    observation. This is the only transition that requires
    external reality; the others can be done by the system itself.

# What "closed" means per layer

  Observation     closed: the system observes real-world phenomena
                  directly (not just historical records).
  Knowledge       closed: the system's encoded laws/equations are
                  confirmed by real-world measurements.
  Reasoning       closed: the system's counterfactuals are confirmed
                  by real-world resurrections/experiments.
  Blueprint       closed: a system-proposed blueprint is built and
                  works as predicted.
  Simulation      closed: a system-run simulation's prediction is
                  confirmed by a real-world measurement.
  Experimentation closed: a system-proposed experiment is run by
                  an external collaborator and the outcome is recorded.
  Creation        closed: a system-proposed prototype is built,
                  succeeds, and the success enters the ledger.

Today, NONE of the layers are closed. Loop 1 (reconstruction) is
the closest: its cycles have run on historical data (which IS
real-world observed fact), so the Observation layer is partial and
the Reconstruction loop is closed. But the Observation layer is
not "closed" because the system has not yet observed a real-world
phenomenon IN REAL TIME — only historical records.
"""


# The 4 valid layer status values.
VALID_LAYER_STATUSES = ("not_started", "scaffolded", "partial", "closed")


# The honest current status of each layer, per CTO review #6.
# This is the canonical source — other modules should import from here.
LAYER_STATUS = {
    "observation": "partial",
    "knowledge": "partial",
    "reasoning": "partial",
    "blueprint": "partial",
    "simulation": "partial",
    "experimentation": "scaffolded",
    "creation": "not_started",
}


# Detailed status with a `reason` per layer. The reason explains
# WHY the layer is at its current status, not just WHAT the status is.
LAYER_STATUS_DETAILS = {
    "observation": {
        "status": "partial",
        "reason": (
            "Infrastructure exists (data/civilization_graph.json, "
            "evidence/failures/*.json, evidence/corruption/*). "
            "Cycles have run on HISTORICAL data (9 historical "
            "failures reconciled in the ledger). NO real-time "
            "observation has occurred — the system reads records, "
            "it does not perceive phenomena."
        ),
        "infrastructure_present": [
            "data/civilization_graph.json (577 nodes)",
            "evidence/failures/*.json (9 failure records)",
            "evidence/corruption/* (F-005 postmortem + reproduction)",
            "scripts/run_verification_cycle.py (reads historical failures)",
        ],
        "real_world_confirmation": False,
    },
    "knowledge": {
        "status": "partial",
        "reason": (
            "Infrastructure exists (5 domain knowledge modules: "
            "physics, chemistry, biology, mathematics, economics). "
            "Modules encode laws/pathways/equations as structured "
            "data. NO real-world measurement has confirmed the "
            "encoded knowledge is correct — the laws are sourced "
            "from literature, not from the system's own observation."
        ),
        "infrastructure_present": [
            "invention_compiler/physics_knowledge_module.py (15 laws encoded)",
            "invention_compiler/chemistry_knowledge_module.py (7 pathways, 3 kinetics, 2 equilibrium, 3 energy states)",
            "invention_compiler/biology_knowledge_module.py",
            "invention_compiler/mathematics_knowledge_module.py (5 optimization, 6 probability, 5 graph, 6 ODE/PDE, 6 control)",
            "invention_compiler/economics_knowledge_module.py",
        ],
        "real_world_confirmation": False,
    },
    "reasoning": {
        "status": "partial",
        "reason": (
            "Infrastructure exists (constraint_module, dependency_module, "
            "resurrection_module with counterfactuals). Cycles have run "
            "on HISTORICAL data (9 historical failures analyzed, 9 "
            "counterfactuals emitted). NO real-world counterfactual "
            "has been confirmed by an actual resurrection the system "
            "PREDICTED before it happened."
        ),
        "infrastructure_present": [
            "invention_compiler/constraint_module.py (causal classification + counterfactual)",
            "invention_compiler/dependency_module.py (prerequisite chain + counterfactual)",
            "invention_compiler/resurrection_module.py (per-failure counterfactuals)",
        ],
        "real_world_confirmation": False,
    },
    "blueprint": {
        "status": "partial",
        "reason": (
            "Infrastructure exists (blueprint_module composes 11-layer "
            "output). Cycles have run on 6 benchmark cases. NO real-"
            "world prototype has been built from a system-proposed "
            "blueprint. The benchmark suite measures expectations_"
            "satisfied, NOT real-world build success."
        ),
        "infrastructure_present": [
            "invention_compiler/orchestrator.py (11-layer compile)",
            "invention_compiler/blueprint_module.py (Layer 10 composer)",
            "benchmarks/compiler/ (6 benchmark cases)",
        ],
        "real_world_confirmation": False,
    },
    "simulation": {
        "status": "partial",
        "reason": (
            "Infrastructure exists (simulation_module with Monte Carlo). "
            "Cycles have run on benchmark cases (200 samples each). "
            "NO real-world measurement has confirmed a simulation's "
            "prediction. The Monte Carlo is a sensitivity probe on "
            "the feasibility score, not a physics simulation."
        ),
        "infrastructure_present": [
            "invention_compiler/simulation_module.py (Monte Carlo, sensitivity, stress)",
        ],
        "real_world_confirmation": False,
    },
    "experimentation": {
        "status": "scaffolded",
        "reason": (
            "Infrastructure exists (experimentation_layer/ package, "
            "milestones/milestone_001/ spec, milestones/milestone_002/ "
            "spec, ledger interface). NO cycle has actually run — no "
            "experiment has been proposed by the system AND executed "
            "by an external collaborator AND recorded in the ledger. "
            "Per CTO review #6: scaffolding ≠ closure. The "
            "infrastructure required for the experimentation cycle "
            "now exists; the system is NOT ready for the cycle until "
            "an external collaborator executes an experiment."
        ),
        "infrastructure_present": [
            "experimentation_layer/ (scaffolded)",
            "milestones/milestone_001/spec.json (Class A: pH prediction)",
            "milestones/milestone_002/spec.json (Class B: improved electrolyte)",
            "hypothesis/hypothesis.py (Hypothesis class for predictions)",
            "data/ledger/predictions.jsonl (verification ledger)",
        ],
        "real_world_confirmation": False,
    },
    "creation": {
        "status": "not_started",
        "reason": (
            "Per CTO review #4/#6: Creation is the DESTINATION, not a "
            "process. No infrastructure specifically for Creation "
            "exists — Creation is what happens when Loop 5 closes "
            "(system-proposed blueprint → prototype built → prototype "
            "succeeds → knowledge enters the ledger). Until at least "
            "one Creation loop is closed, the system is an invention "
            "catalog, not an invention compiler."
        ),
        "infrastructure_present": [],  # nothing specific to Creation
        "real_world_confirmation": False,
    },
}


def get_layer_status(layer_name: str) -> str:
    """Get the status string for a layer by name."""
    return LAYER_STATUS.get(layer_name, "not_started")


def get_layer_details(layer_name: str) -> dict:
    """Get the full details dict for a layer by name."""
    return LAYER_STATUS_DETAILS.get(layer_name, {
        "status": "not_started",
        "reason": f"layer {layer_name!r} not recognized",
        "infrastructure_present": [],
        "real_world_confirmation": False,
    })


def all_layers_status() -> dict:
    """Return the full layer status table with details."""
    return {
        layer: LAYER_STATUS_DETAILS[layer]
        for layer in LAYER_STATUS
    }


def count_closed_layers() -> int:
    """How many layers are closed today?"""
    return sum(1 for s in LAYER_STATUS.values() if s == "closed")


def count_scaffolded_layers() -> int:
    """How many layers are scaffolded today?"""
    return sum(1 for s in LAYER_STATUS.values() if s == "scaffolded")


def count_partial_layers() -> int:
    """How many layers are partial today?"""
    return sum(1 for s in LAYER_STATUS.values() if s == "partial")


def count_not_started_layers() -> int:
    """How many layers are not started today?"""
    return sum(1 for s in LAYER_STATUS.values() if s == "not_started")
