"""Calibration runner. python scripts/calibrate.py

F-AUD-003 / F-015 fix: previously this script did
``[json.loads(l) for l in lp.read_text().splitlines() if l.strip()]``
with no error handling — the same crash that F-006 fixed in
``web/backend/main.py::evidence()`` and that F-013 tracked in
``web/backend/adapters/core.py::read_evidence()``. The fix landed
in only one of the three readers; this script was the third.

Per ANTI_ENTROPY.md rule "Decouple modules", the corruption-aware
read logic now lives in ``web/backend/adapters/core._read_ledger_safely``
and is shared by all three readers. This script delegates to it via
``read_ledger()`` so future changes to the read logic land in one
place, not three.
"""
import json, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "web" / "backend"))
from adapters.core import _read_ledger_safely
from adapters.calibration import C


def read_ledger(ledger_path):
    """Read a ledger file with total-corruption detection.

    Thin wrapper around ``adapters.core._read_ledger_safely`` so
    callers (this script, tests, future calibration tooling) share
    a single read path. Returns a dict with ``ledger``,
    ``malformed_lines``, and ``entry_count`` keys.

    Per FAILURES.md F-015, this function must fail loudly with a
    descriptive message (via the ``malformed_lines`` block), not
    with a traceback. It is the function the user runs to actually
    recalibrate, so a traceback on a corrupted ledger is hostile.
    """
    return _read_ledger_safely(pathlib.Path(ledger_path))


def main():
    lp = ROOT / "data" / "ledger" / "predictions.jsonl"
    read = read_ledger(lp)
    ledger = read["ledger"]
    result = C.calibrate_from_ledger(ledger)
    report = {
        "calibration": result,
        "constants": C.status(),
        "ledger_entries": len(ledger),
        "malformed_lines": read["malformed_lines"],
    }
    dest = ROOT / "logs" / "calibration_report.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))

if __name__ == "__main__": main()
