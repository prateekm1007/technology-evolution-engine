#!/usr/bin/env python3
"""Run MDDG FOUNDATION pilot with minimal scale to fit within time limits."""
import sys
sys.path.insert(0, '/home/z/my-project/audit/technology-evolution-engine')
from source_fabric.mddg.foundation_pilot import run_mddg_foundation_pilot
from pathlib import Path
import json

report = run_mddg_foundation_pilot(
    Path('source_fabric/mddg_foundation_output'),
    devices_per_category=8,
    papers_per_device=1,
    patents_per_device=1,
    trials_per_device=1
)
s = report['summary']
fg = report['foundation_gate']
print('=== FOUNDATION GATE ===')
for k, v in fg.items():
    print(f'  {"PASS" if v else "FAIL"} {k}')
print()
print('=== METRICS ===')
for k in ['devices_ingested', 'papers_linked', 'patents_linked', 'trials_linked',
          'adverse_events_linked', 'recalls_linked', 'failure_modes_extracted',
          'real_lifecycle_chains', 'structural_edges', 'substantive_edges']:
    print(f'  {k}: {s[k]}')
print(f'  stage_dist: {s["lifecycle_stage_distribution"]}')
