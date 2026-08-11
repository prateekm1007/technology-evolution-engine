# Drift Detection (Discipline 3)

Detects unintended changes in benchmark outputs, graph structure, assumptions, and scoring calibration.

## Usage

    python scripts/detect_drift.py --baseline
    python scripts/detect_drift.py --compare
    python scripts/detect_drift.py --report

## Monitored Signals

| Signal | Threshold | Severity |
|--------|-----------|----------|
| Graph node count | +/-5 | medium/high |
| Graph edge count | +/-10 | medium/high |
| Graph content hash | any | medium |
| Assumption changes | any | high |
| PCS drift | +/-0.1 | medium |
| RPS drift | +/-0.1 | medium |
| Missing outputs | any | high |

## Law 7 Compliance

The baseline is immutable once created. Never overwrite.
