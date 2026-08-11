#!/usr/bin/env bash
# run_dxp005_all.sh — Advance all DXP-005 cases (NEMOTRON PILOT — ARCHIVAL)
#
# **STATUS: ARCHIVAL — DO NOT EXECUTE**
# This is a quarantined pilot runner. It is preserved as an archival artifact.
# It contains a machine-enforced protocol lock that prevents execution while
# DXP-005 is PAUSED.
#
# The output directory has been redirected to the quarantine namespace.
# See: experiments/dxp005_pilots/nemotron/QUARANTINE_MANIFEST.json
# See: experiments/dxp005_pilots/nemotron/runner_scripts/README.md
set -uo pipefail
cd /home/z/my-project/audit/technology-evolution-engine

# ===== MACHINE-ENFORCED PROTOCOL LOCK (audit finding A) =====
# DXP-005 is PAUSED. The runner cannot proceed unless PROGRAM_STATE.json
# explicitly says status=AUTHORIZED. This is not a documentary prohibition
# — it is a hard failure that prevents execution.
python3 -m engine.protocol_lock DXP-005
LOCK_RC=$?
if [ $LOCK_RC -ne 0 ]; then
  echo "ERROR: DXP-005 protocol lock denied execution. See message above." >&2
  echo "To resume DXP-005, all resume_conditions in PROGRAM_STATE.json must" >&2
  echo "be met AND status must be updated to AUTHORIZED by an authorized operator." >&2
  exit 1
fi

# ===== OUTPUT DIRECTORY LOCK (audit finding B, round 3) =====
# Verify that the quarantine output directory is writable. This prevents
# the quarantined pilot from writing to the primary DXP-005 output path.
python3 -c "
import sys
sys.path.insert(0, '.')
from engine.protocol_lock import assert_output_dir_writable
from pathlib import Path
quarantine_dir = Path('experiments/dxp005_pilots/nemotron/ENGINE_OUTPUT')
assert_output_dir_writable('DXP-005', quarantine_dir)
print('Output directory lock: PASS (quarantine namespace)')
"
LOCK_RC=$?
if [ $LOCK_RC -ne 0 ]; then
  echo "ERROR: Output directory lock denied execution. See message above." >&2
  exit 1
fi

# If we reach here, DXP-005 is AUTHORIZED. The quarantine scripts below
# would execute the Nemotron pilot. But since the canonical DXP-005
# protocol uses ZAI (not Nemotron), executing these scripts would be
# a protocol violation even if DXP-005 is AUTHORIZED.
#
# The canonical runner is scripts/run_dxp005.py (uses ZAI).
# These quarantined scripts are for archival reference only.

echo "ERROR: This is an archival quarantined pilot runner." >&2
echo "       Even if DXP-005 is AUTHORIZED, the canonical runner is" >&2
echo "       scripts/run_dxp005.py (ZAI provider)." >&2
echo "       Nemotron pilot runners are for archival reference only." >&2
echo "       To execute DXP-005, use: python3 scripts/run_dxp005.py" >&2
exit 1
