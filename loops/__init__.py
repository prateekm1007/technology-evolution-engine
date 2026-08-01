"""
loops/ package — the 5 mandated loops (CTO review #4).

Per CTO review #4 (commit `f590661`), the repository is in phase
transition. The objective is no longer to add modules — the
objective is to close loops.

A loop is "closed" when at least one cycle has completed AND the
reconciliation has been recorded in the verification ledger
(data/ledger/predictions.jsonl). A loop that has only the "propose"
stage is OPEN, not closed.

The 5 loops:

  Loop 1 — reconstruction:
      humanity discovers X → system reconstructs X → compare results
      Status: CLOSED (via existing verification cycle)

  Loop 2 — resurrection:
      humanity abandons X → system identifies missing prerequisites →
      system predicts renewed feasibility → compare results
      Status: CLOSED (via resurrection_module's counterfactuals)

  Loop 3 — forecasting:
      system predicts X → time passes → compare prediction against reality
      Status: OPEN — requires time. Predictions can be recorded as
      Hypotheses today; reconciliation requires waiting.

  Loop 4 — experimentation:
      system proposes blueprint → experiment is executed →
      measurements are recorded → system updates model
      Status: OPEN — requires external collaborator to run an
      experiment.

  Loop 5 — creation:
      system proposes blueprint → prototype is built →
      prototype succeeds → knowledge enters the ledger
      Status: OPEN — this is the DESTINATION, not a process. The
      system does not honestly claim to be an invention compiler
      until at least one Creation loop is closed.

Each loop module exposes:
  - status() -> dict with at minimum:
      {
        "closed": bool,
        "reason": str (especially if closed=False),
        "cycles_completed": int,
      }
  - run_one_cycle() -> dict (attempts one loop closure; may be a
      no-op for OPEN loops with a clear reason)

The loops/ package does NOT replace the verification_engine or
the existing audit harness — it wraps them with the language of
"closing loops" so progress is measurable as "loops closed",
not "modules added".
"""

# Re-export the loop classes for convenience.
from .reconstruction_loop import ReconstructionLoop
from .resurrection_loop import ResurrectionLoop
from .forecasting_loop import ForecastingLoop
from .experimentation_loop import ExperimentationLoop
from .creation_loop import CreationLoop

__all__ = [
    "ReconstructionLoop",
    "ResurrectionLoop",
    "ForecastingLoop",
    "ExperimentationLoop",
    "CreationLoop",
]
