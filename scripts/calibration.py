#!/usr/bin/env python3
"""
calibration.py — Platt scaling and isotonic regression for confidence calibration.

Closes F-067 blocker #4: "Platt scaling does not exist in the codebase."
Closes F-068 (CALIB-SCORE-DESIGN): calibration scoring was for infrastructure,
not outcome. This module provides the actual calibration code that produces
a measured ECE (Expected Calibration Error).

Per DR-49: the calibration score in nine_tenths_loop.py reads the ECE from
this module's output (benchmarks/reports/calibration_score.json) and awards
outcome points based on ECE thresholds.

Usage:
    python3 -m scripts.calibration          # run calibration, print ECE
    python3 -m scripts.calibration --platt  # apply Platt scaling
    python3 -m scripts.calibration --isotonic  # apply isotonic regression
"""
import json
import sys
import math
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass, asdict

REPO = Path(__file__).resolve().parents[1]
PREDICTIONS = REPO / "data" / "ledger" / "predictions.jsonl"
REPORT = REPO / "benchmarks" / "reports" / "calibration_score.json"


@dataclass
class CalibrationResult:
    """Result of a calibration evaluation."""
    method: str  # "raw", "platt", "isotonic"
    n_samples: int
    ece: float  # Expected Calibration Error
    brier: float  # Brier score
    bins: List[Dict]  # per-bin accuracy/confidence/count


def load_predictions() -> List[Dict]:
    """Load reaudit predictions from the ledger."""
    entries = []
    if not PREDICTIONS.exists():
        return entries
    with PREDICTIONS.open() as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if entry.get("type") == "reaudit":
                    entries.append(entry)
            except json.JSONDecodeError:
                continue
    return entries


def extract_confidence_outcome(entries: List[Dict]) -> List[Tuple[float, int]]:
    """Extract (confidence, outcome) pairs from reaudit entries.

    confidence: the predicted confidence (0-1)
    outcome: 1 if the prediction was correct (upheld), 0 if overturned

    Reaudit entries have 'overturned' (bool): false = upheld (correct),
    true = overturned (incorrect).
    """
    pairs = []
    for entry in entries:
        conf = entry.get("confidence")
        overturned = entry.get("overturned")
        if conf is None or overturned is None:
            continue
        # overturned=false means the original verdict was upheld (correct)
        # overturned=true means the original verdict was overturned (incorrect)
        outcome = 0 if overturned else 1
        pairs.append((float(conf), outcome))
    return pairs


def compute_ece(pairs: List[Tuple[float, int]], n_bins: int = 10) -> Tuple[float, List[Dict]]:
    """Compute Expected Calibration Error.

    ECE = sum over bins of (|bin|/N) * |accuracy(bin) - confidence(bin)|

    Returns (ece, bins) where bins is a list of per-bin stats.
    """
    if not pairs:
        return 0.0, []

    bin_edges = [i / n_bins for i in range(n_bins + 1)]
    bins = []
    ece = 0.0
    n = len(pairs)

    for i in range(n_bins):
        lo, hi = bin_edges[i], bin_edges[i + 1]
        in_bin = [(c, o) for c, o in pairs if lo <= c < hi or (i == n_bins - 1 and c == hi)]
        if not in_bin:
            bins.append({"bin_lo": lo, "bin_hi": hi, "count": 0,
                         "accuracy": 0.0, "confidence": 0.0, "gap": 0.0})
            continue
        count = len(in_bin)
        acc = sum(o for _, o in in_bin) / count
        conf = sum(c for c, _ in in_bin) / count
        gap = abs(acc - conf)
        ece += (count / n) * gap
        bins.append({"bin_lo": lo, "bin_hi": hi, "count": count,
                     "accuracy": round(acc, 4), "confidence": round(conf, 4),
                     "gap": round(gap, 4)})

    return round(ece, 4), bins


def compute_brier(pairs: List[Tuple[float, int]]) -> float:
    """Compute Brier score: mean of (confidence - outcome)^2."""
    if not pairs:
        return 0.0
    return round(sum((c - o) ** 2 for c, o in pairs) / len(pairs), 4)


def platt_scale(pairs: List[Tuple[float, int]]) -> List[Tuple[float, int]]:
    """Apply Platt scaling: fit logistic regression on confidence → outcome.

    Platt scaling: P(y=1|f) = 1 / (1 + exp(A*f + B))
    We fit A and B via simple gradient descent (no sklearn dependency).
    """
    if not pairs:
        return pairs

    # Simple logistic regression: minimize log-loss
    # f = confidence, y = outcome
    # P(y=1) = sigmoid(A*f + B)
    # Gradient: dL/dA = sum((P-y)*f), dL/dB = sum(P-y)
    A, B = 1.0, 0.0  # identity initialization
    lr = 0.01
    n_iter = 1000

    for _ in range(n_iter):
        grad_A, grad_B = 0.0, 0.0
        for f, y in pairs:
            p = 1.0 / (1.0 + math.exp(-(A * f + B)))
            err = p - y
            grad_A += err * f
            grad_B += err
        A -= lr * grad_A / len(pairs)
        B -= lr * grad_B / len(pairs)

    # Apply the scaling
    scaled = []
    for f, y in pairs:
        p = 1.0 / (1.0 + math.exp(-(A * f + B)))
        scaled.append((p, y))
    return scaled


def isotonic_regress(pairs: List[Tuple[float, int]]) -> List[Tuple[float, int]]:
    """Apply isotonic regression: monotone non-decreasing fit.

    Simple pool-adjacent-violators algorithm (PAVA).
    """
    if not pairs:
        return pairs

    # Sort by confidence
    sorted_pairs = sorted(pairs, key=lambda x: x[0])

    # PAVA: find the monotone non-decreasing sequence that minimizes squared error
    blocks = [(c, o, 1) for c, o in sorted_pairs]  # (sum_conf, sum_outcome, count)

    i = 0
    while i < len(blocks) - 1:
        mean_i = blocks[i][1] / blocks[i][2]
        mean_next = blocks[i + 1][1] / blocks[i + 1][2]
        if mean_i > mean_next:
            # Merge
            sc = blocks[i][0] + blocks[i + 1][0]
            so = blocks[i][1] + blocks[i + 1][1]
            cnt = blocks[i][2] + blocks[i + 1][2]
            blocks[i] = (sc, so, cnt)
            del blocks[i + 1]
            if i > 0:
                i -= 1
        else:
            i += 1

    # Build lookup: for each original confidence, find the calibrated value
    # Map each block's mean outcome as the calibrated confidence
    block_map = []
    idx = 0
    for sc, so, cnt in blocks:
        mean_outcome = so / cnt
        for _ in range(cnt):
            block_map.append(mean_outcome)

    # Map back to original order
    sorted_indices = sorted(range(len(pairs)), key=lambda i: pairs[i][0])
    calibrated = [None] * len(pairs)
    for si, oi in enumerate(sorted_indices):
        calibrated[oi] = (block_map[si], pairs[oi][1])

    return calibrated


def run_calibration(method: str = "raw") -> CalibrationResult:
    """Run calibration evaluation. method: 'raw', 'platt', or 'isotonic'."""
    entries = load_predictions()
    pairs = extract_confidence_outcome(entries)

    if not pairs:
        return CalibrationResult(method=method, n_samples=0, ece=0.0,
                                  brier=0.0, bins=[])

    if method == "platt":
        pairs = platt_scale(pairs)
    elif method == "isotonic":
        pairs = isotonic_regress(pairs)

    ece, bins = compute_ece(pairs)
    brier = compute_brier(pairs)

    return CalibrationResult(
        method=method,
        n_samples=len(pairs),
        ece=ece,
        brier=brier,
        bins=bins,
    )


def main():
    method = "raw"
    if "--platt" in sys.argv:
        method = "platt"
    elif "--isotonic" in sys.argv:
        method = "isotonic"

    print(f"===== Calibration ({method}) =====")
    result = run_calibration(method)

    print(f"  Samples: {result.n_samples}")
    print(f"  ECE:     {result.ece}")
    print(f"  Brier:   {result.brier}")
    print()

    if result.bins:
        print("  Bins:")
        print(f"    {'Bin':>12}  {'Count':>6}  {'Acc':>6}  {'Conf':>6}  {'Gap':>6}")
        for b in result.bins:
            if b["count"] > 0:
                print(f"    [{b['bin_lo']:.1f},{b['bin_hi']:.1f}]  {b['count']:>6}  "
                      f"{b['accuracy']:>6.3f}  {b['confidence']:>6.3f}  {b['gap']:>6.3f}")

    # Write report
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with REPORT.open("w") as f:
        json.dump(asdict(result), f, indent=2)
    print(f"\n  Report: {REPORT}")

    # DR-49 outcome points (for nine_tenths_loop.py to read)
    if result.ece <= 0.05:
        outcome = 3
    elif result.ece <= 0.10:
        outcome = 2
    elif result.ece <= 0.15:
        outcome = 1
    else:
        outcome = 0
    print(f"  DR-49 outcome points: {outcome}/3 (ECE={result.ece})")


if __name__ == "__main__":
    main()
