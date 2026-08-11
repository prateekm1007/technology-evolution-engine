#!/usr/bin/env python3
"""Robustness check: run meta-invention with multiple seeds."""
import sys
import math
import random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.cross_domain_transfer import (
    THERMOELECTRIC_DOMAIN, BATTERY_DOMAIN, CATALYST_DOMAIN, PV_DOMAIN,
    thermoelectric_forward, battery_forward, catalyst_forward, pv_forward,
)
from scripts.meta_invention import run_meta_invention

domains = [
    ("Thermoelectric", THERMOELECTRIC_DOMAIN, thermoelectric_forward),
    ("Battery",        BATTERY_DOMAIN,         battery_forward),
    ("Catalyst",       CATALYST_DOMAIN,        catalyst_forward),
    ("Photovoltaic",   PV_DOMAIN,              pv_forward),
]

print("Multi-seed robustness check (5 seeds × 4 domains)")
print("=" * 90)
print(f"{'Domain':<15} {'Seed 42':<10} {'Seed 7':<10} {'Seed 99':<10} {'Seed 123':<10} {'Seed 256':<10} {'Mean Δ':<10} {'Won':<5}")
print("-" * 90)

for name, spec, fn in domains:
    deltas = []
    for seed in [42, 7, 99, 123, 256]:
        iters, _, _ = run_meta_invention(spec, fn, n_iterations=5, n_per_iter=50, seed=seed)
        delta = iters[-1]["best_outcome"] - iters[0]["best_outcome"]
        deltas.append(delta)
    mean_d = sum(deltas) / len(deltas)
    n_won = sum(1 for d in deltas if d > 0)
    print(f"{name:<15} " + " ".join(f"{d:>+8.3f} " for d in deltas) + f" {mean_d:>+8.3f}  {n_won}/5")
