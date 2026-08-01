"""
Loop 3 — Forecasting.

    system predicts X
            ↓
    time passes
            ↓
    compare prediction against reality

STATUS: OPEN.

This loop CANNOT be closed in a single session. It requires time
to pass — typically months or years — between the prediction and
the reconciliation. The system can record forecasts today (as
Hypotheses with status="pending" in the ledger), but cannot
reconcile them today.

The honest declaration here is:
  - The infrastructure to record forecasts exists (Hypothesis class,
    ledger).
  - The infrastructure to reconcile forecasts exists (reconcile()
    method on Hypothesis; verification cycle script).
  - But no forecast has been reconciled yet, because no time has
    passed.

The next_action to close this loop: pick a forecast with a short
time horizon (e.g., 6 months), record it as a Hypothesis today,
and schedule a reconciliation run for 6 months from now. The
scheduler is NOT part of this repository yet — that's the
infrastructure gap.
"""
from datetime import datetime, timezone


class ForecastingLoop:
    """Loop 3: predict future feasibility, wait, reconcile."""

    LOOP_NAME = "forecasting"
    LOOP_NUMBER = 3

    def status(self) -> dict:
        return {
            "loop_name": self.LOOP_NAME,
            "loop_number": self.LOOP_NUMBER,
            "closed": False,
            "cycles_completed": 0,
            "reason": (
                "OPEN — forecasting requires time to pass between "
                "prediction and reconciliation. No forecast can be "
                "closed in a single session. The infrastructure to "
                "record forecasts (Hypothesis class, ledger) exists; "
                "the infrastructure to schedule reconciliation runs "
                "does NOT exist yet — that's the gap."
            ),
            "infrastructure_present": [
                "hypothesis/Hypothesis (record forecasts)",
                "scripts/run_verification_cycle.py (reconcile forecasts)",
            ],
            "infrastructure_missing": [
                "scheduler to trigger reconciliation runs at future dates",
                "first forecast recorded with a concrete reconciliation date",
            ],
            "next_action_to_close": (
                "Pick a forecast with a 6-month horizon. Record it as a "
                "Hypothesis today with status='pending'. Schedule a "
                "reconciliation run for 6 months from now. When that run "
                "completes and the outcome is recorded in the ledger, "
                "Loop 3 will be closed."
            ),
        }

    def run_one_cycle(self) -> dict:
        """Record a forecast as a Hypothesis today. Does NOT close the
        loop — only the passage of time + a future reconciliation run
        can do that."""
        from hypothesis.hypothesis import Hypothesis
        forecast = Hypothesis(
            claim=(
                "Solid-state ammonia synthesis will achieve >=10% Faradaic "
                "efficiency at ambient conditions in a peer-reviewed "
                "publication by 2028."
            ),
            confidence=0.35,
            evidence=[
                "electrochemical_ammonia pathway",
                "Arrhenius kinetics",
                "N≡N triple bond binding energy (945 kJ/mol)",
                "active research area (no commercial process yet)",
            ],
            writer="loops.forecasting_loop.run_one_cycle",
        )
        return {
            "loop_name": self.LOOP_NAME,
            "forecast_recorded": forecast.to_dict(),
            "reconciliation_due": "2028-01-01",
            "note": (
                "Forecast recorded as a Hypothesis with status='pending'. "
                "Loop 3 is NOT closed — only the passage of time + a "
                "future reconciliation run can close it."
            ),
        }
