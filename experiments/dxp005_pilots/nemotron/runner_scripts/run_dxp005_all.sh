#!/usr/bin/env bash
# run_dxp005_all.sh — Advance all DXP-005 cases through all steps.
#
# Each step is a separate Python invocation that fits within the bash
# tool's time budget. Progress is saved between invocations.
#
# Usage: bash scripts/run_dxp005_all.sh
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

# OPENROUTER_API_KEY must be set in the environment. Do NOT hardcode keys
# in source files (CONTRIBUTING.md item 12, GitHub secret scanning).
if [ -z "${OPENROUTER_API_KEY:-}" ]; then
  echo "ERROR: OPENROUTER_API_KEY environment variable not set" >&2
  exit 1
fi
export OPENROUTER_API_KEY

CASES="N1 N2 N3 N4 N5 P1 P2 P3 P4 P5"
CONDS="A-baseline B-hgen1 C-null"

for CASE in $CASES; do
  # Step 1: upstream
  RESULT_FILE="discovery_experiment/ENGINE_OUTPUT/DXP-005/${CASE}-result.json"
  UPSTREAM_HASH="discovery_experiment/ENGINE_OUTPUT/DXP-005/${CASE}/upstream/HASHES.json"
  if [ ! -f "$UPSTREAM_HASH" ]; then
    echo "[$(date +%H:%M:%S)] === $CASE upstream ==="
    timeout 90 python3 -u scripts/run_dxp005_step.py upstream "$CASE" 2>&1 | tail -10
    echo ""
  fi

  # Check if transfer was rejected
  if [ -f "$UPSTREAM_HASH" ] && grep -q '"transfer_rejected": true' "$UPSTREAM_HASH"; then
    echo "[$(date +%H:%M:%S)] $CASE: TRANSFER_REJECTED — writing result"
    python3 -c "
import json, sys
sys.path.insert(0, '.')
sys.path.insert(0, 'discovery_experiment/CASES')
import hashlib
from pathlib import Path
out = Path('discovery_experiment/ENGINE_OUTPUT/DXP-005')
upstream = json.loads((out / '$CASE/upstream/HASHES.json').read_text())
result = {'case_id': '$CASE', 'status': 'TRANSFER_REJECTED',
          'upstream_hashes': upstream, 'conditions': {}}
(out / '$CASE-result.json').write_text(json.dumps(result, indent=2))
"
    continue
  fi

  for COND in $CONDS; do
    COND_DIR="discovery_experiment/ENGINE_OUTPUT/DXP-005/${CASE}/${COND}"
    RESULT="${COND_DIR}/result.json"

    if [ -f "$RESULT" ]; then
      echo "[$(date +%H:%M:%S)] $CASE-$COND: already complete"
      continue
    fi

    # Step 2: hypotheses (only if not generated)
    if [ ! -f "${COND_DIR}/04_hypotheses.json" ]; then
      echo "[$(date +%H:%M:%S)] === $CASE-$COND hypotheses ==="
      timeout 90 python3 -u scripts/run_dxp005_step.py hypotheses "$CASE" "$COND" 2>&1 | tail -10
      echo ""
    fi

    # Step 3: adversarial (only if not done)
    if [ -f "${COND_DIR}/04_hypotheses.json" ] && [ ! -f "$RESULT" ]; then
      echo "[$(date +%H:%M:%S)] === $CASE-$COND adversarial ==="
      timeout 110 python3 -u scripts/run_dxp005_step.py adversarial "$CASE" "$COND" 2>&1 | tail -15
      echo ""
    fi
  done

  # Write case-level result
  python3 -c "
import json, sys
sys.path.insert(0, '.')
sys.path.insert(0, 'discovery_experiment/CASES')
from pathlib import Path
out = Path('discovery_experiment/ENGINE_OUTPUT/DXP-005')
case_dir = out / '$CASE'
conditions = {}
for cond in ['A-baseline', 'B-hgen1', 'C-null']:
    rf = case_dir / cond / 'result.json'
    if rf.exists():
        conditions[cond] = json.loads(rf.read_text())
upstream = {}
hf = case_dir / 'upstream/HASHES.json'
if hf.exists():
    upstream = json.loads(hf.read_text())
result = {'case_id': '$CASE',
          'upstream_hashes': upstream,
          'conditions': conditions}
if not conditions:
    result['status'] = 'TRANSFER_REJECTED'
(out / '$CASE-result.json').write_text(json.dumps(result, indent=2))
print(f'$CASE: {len(conditions)} conditions')
"
done

echo ""
echo "=== SUMMARY ==="
python3 -c "
import json, sys
sys.path.insert(0, '.')
sys.path.insert(0, 'discovery_experiment/CASES')
from pathlib import Path
out = Path('discovery_experiment/ENGINE_OUTPUT/DXP-005')
for case in ['N1','N2','N3','N4','N5','P1','P2','P3','P4','P5']:
    rf = out / f'{case}-result.json'
    if rf.exists():
        d = json.loads(rf.read_text())
        conds = d.get('conditions', {})
        if conds:
            for c, cr in conds.items():
                print(f'  {case}-{c}: n_hyp={cr.get(\"n_hypotheses\",0)} surv={cr.get(\"n_survived\",0)} kill={cr.get(\"n_killed\",0)}')
        else:
            print(f'  {case}: {d.get(\"status\", \"unknown\")}')
    else:
        print(f'  {case}: NOT RUN')
"
