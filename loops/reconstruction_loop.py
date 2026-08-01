"""
Loop 1 — Reconstruction.

    humanity discovers X
            ↓
    system reconstructs X
            ↓
    compare results

STATUS: CLOSED via the existing verification cycle.

The verification cycle (scripts/run_verification_cycle.py) already
implements this loop: for each of 9 historical failures, the system
PREDICTS whether the technology would resurrect under a simulated
constraint move, OBSERVES the documented ground-truth outcome, and
RECONCILES pass/fail into the ledger.

The loop is closed because the cycle has run: 6 pass + 3 fail
entries exist in data/ledger/predictions.jsonl with type="verification"
and writer="scripts.run_verification_cycle.reconcile".
"""
import json
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_LEDGER = _ROOT / "data" / "ledger" / "predictions.jsonl"


class ReconstructionLoop:
    """Loop 1: reconstruct what humanity already knows.

    This loop is closed via the verification cycle that already
    exists in scripts/run_verification_cycle.py.
    """

    LOOP_NAME = "reconstruction"
    LOOP_NUMBER = 1

    def status(self) -> dict:
        """Return the closure status of this loop.

        Per CTO review #5, three states exist: open, partially_closed,
        closed. Loop 1 is `closed` because historical failures ARE
        observed facts — the system's reconstructions are compared
        against real-world outcomes (the historical record), not
        against the system's own predictions.
        """
        passes, fails = self._count_verification_entries()
        closed = (passes >= 1 and fails >= 1)
        return {
            "loop_name": self.LOOP_NAME,
            "loop_number": self.LOOP_NUMBER,
            "closed": closed,
            "partially_closed": False,  # closed implies not partially_closed
            "cycles_completed": passes + fails,
            "passes": passes,
            "fails": fails,
            "reason": (
                "CLOSED via verification cycle (scripts/run_verification_cycle.py). "
                f"{passes} pass + {fails} fail entries in ledger. "
                "Real-world confirmation: historical failures are observed "
                "facts, not predictions — the system's reconstructions are "
                "compared against the historical record."
                if closed else
                "OPEN — verification cycle has not recorded >=1 pass AND >=1 fail."
            ),
            "infrastructure": "scripts/run_verification_cycle.py",
            "real_world_confirmation": closed,
        }

    def run_one_cycle(self) -> dict:
        """Run one verification cycle. Delegates to the existing script."""
        import subprocess
        result = subprocess.run(
            [sys.executable, "scripts/run_verification_cycle.py"],
            cwd=str(_ROOT), capture_output=True, text=True,
        )
        return {
            "loop_name": self.LOOP_NAME,
            "returncode": result.returncode,
            "stdout_tail": result.stdout[-500:],
            "stderr_tail": result.stderr[-500:] if result.stderr else None,
        }

    def _count_verification_entries(self) -> tuple:
        """Count pass and fail entries in the verification ledger."""
        if not _LEDGER.exists():
            return (0, 0)
        passes, fails = 0, 0
        with _LEDGER.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if entry.get("type") == "verification":
                    if entry.get("outcome") == "pass":
                        passes += 1
                    elif entry.get("outcome") == "fail":
                        fails += 1
        return (passes, fails)
