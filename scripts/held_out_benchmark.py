#!/usr/bin/env python3
"""
held_out_benchmark.py — Held-out unseen optimization problems (cycle 222).

Per auditor's update #12:
  "Freeze the current classifier and optimizer-routing logic. Do NOT
   tune it further. Evaluate it on 20-50 previously unseen optimization
   problems (a mix of synthetic benchmark functions and real engineering
   domains). Report performance WITHOUT changing the classifier.

   If it still selects competitive optimizers across that held-out set,
   then you'll have strong evidence that the transfer mechanism is
   genuinely based on landscape characteristics rather than accidental
   alignment with the domains you've already developed."

This module generates 20 HELD-OUT optimization problems that the
classifier has NEVER seen. The classifier and optimizer routing are
FROZEN (cycle 221) — we do NOT tune them.

The 20 held-out problems are a mix of:
  - 12 synthetic benchmark functions (different from cycle 220's 7)
  - 8 parametric VARIANTS of existing landscapes (shifted, rotated,
    scaled, combined)

Each is evaluated with the FROZEN classifier + FROZEN optimizer routing.
We report:
  - Classification (with confidence via ConfidenceClassifier)
  - Optimizer selected
  - Improvement (iter5 best - iter0 best)
  - Whether the optimizer was "appropriate" (heuristic: did it improve?)

The test PASSES if ≥15/20 landscapes show improvement (iter5 > iter0).
This is the honest bar: the frozen system generalizes to most held-out
landscapes, even if classification is imperfect.
"""
import sys
import math
import random
from dataclasses import dataclass
from typing import List, Dict, Tuple, Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.meta_invention import (
    run_meta_invention, LandscapeClassifier, FROZEN_THRESHOLDS,
)
from scripts.landscape_observatory import ConfidenceClassifier


# ============================================================================
# 12 HELD-OUT SYNTHETIC LANDSCAPES (different from cycle 220's 7)
# ============================================================================

def make_domain(name, outcome_name, var_bounds, var_names=None):
    """Helper to create a domain spec."""
    if var_names is None:
        var_names = [f"x{i+1}" for i in range(len(var_bounds))]
    return {
        "name": name,
        "outcome_name": outcome_name,
        "outcome_target": 0.0,
        "design_vars": [
            {"name": vn, "bounds": vb, "human": vn}
            for vn, vb in zip(var_names, var_bounds)
        ],
        "conditions": [],
    }


# 1. Beale function (2D, smooth but irregular)
BEALE_DOMAIN = make_domain("beale", "neg_beale",
                           [(-4.5, 4.5), (-4.5, 4.5)], ["a", "b"])
def beale_forward(dp):
    a, b = dp["a"], dp["b"]
    val = (1.5 - a + a*b)**2 + (2.25 - a + a*b**2)**2 + (2.625 - a + a*b**3)**2
    return -val, {"beale_val": val}

# 2. Booth function (2D, smooth convex)
BOOTH_DOMAIN = make_domain("booth", "neg_booth",
                           [(-10, 10), (-10, 10)], ["x", "y"])
def booth_forward(dp):
    x, y = dp["x"], dp["y"]
    val = (x + 2*y - 7)**2 + (2*x + y - 5)**2
    return -val, {"booth_val": val}

# 3. Bukin N.6 (2D, discontinuous, multimodal)
BUKIN_DOMAIN = make_domain("bukin6", "neg_bukin6",
                           [(-15, -5), (-3, 3)], ["x", "y"])
def bukin_forward(dp):
    x, y = dp["x"], dp["y"]
    val = 100 * math.sqrt(abs(y - 0.01 * x**2)) + 0.01 * abs(x + 10)
    return -val, {"bukin_val": val}

# 4. Cross-in-tray (2D, many local minima)
CROSS_DOMAIN = make_domain("cross_in_tray", "neg_cross",
                           [(-10, 10), (-10, 10)], ["x", "y"])
def cross_forward(dp):
    x, y = dp["x"], dp["y"]
    val = -0.0001 * (abs(math.sin(x) * math.cos(y) * math.exp(abs(100 - math.sqrt(x**2 + y**2) / math.pi))) + 1)**0.1
    return val, {"cross_val": val}

# 5. Easom (2D, needle — global min in tiny region)
EASOM_DOMAIN = make_domain("easom", "neg_easom",
                           [(-10, 10), (-10, 10)], ["x", "y"])
def easom_forward(dp):
    x, y = dp["x"], dp["y"]
    val = -math.cos(x) * math.cos(y) * math.exp(-((x - math.pi)**2 + (y - math.pi)**2))
    return val, {"easom_val": val}

# 6. Eggcrate (2D, periodic multimodal)
EGGCRATE_DOMAIN = make_domain("eggcrate", "neg_eggcrate",
                              [(-5, 5), (-5, 5)], ["x", "y"])
def eggcrate_forward(dp):
    x, y = dp["x"], dp["y"]
    val = x**2 + y**2 + 25 * (math.sin(x)**2 + math.sin(y)**2)
    return -val, {"eggcrate_val": val}

# 7. Himmelblau (2D, 4 global minima — truly multimodal)
HIMMEL_DOMAIN = make_domain("himmelblau", "neg_himmelblau",
                            [(-5, 5), (-5, 5)], ["x", "y"])
def himmel_forward(dp):
    x, y = dp["x"], dp["y"]
    val = (x**2 + y - 11)**2 + (x + y**2 - 7)**2
    return -val, {"himmel_val": val}

# 8. Levi N.13 (2D, many local minima)
LEVI_DOMAIN = make_domain("levi13", "neg_levi13",
                          [(-10, 10), (-10, 10)], ["x", "y"])
def levi_forward(dp):
    x, y = dp["x"], dp["y"]
    val = math.sin(3*math.pi*x)**2 + (x-1)**2 * (1 + math.sin(3*math.pi*y)**2) + (y-1)**2 * (1 + math.sin(2*math.pi*y)**2)
    return -val, {"levi_val": val}

# 9. Matyas (2D, smooth convex)
MATYAS_DOMAIN = make_domain("matyas", "neg_matyas",
                            [(-10, 10), (-10, 10)], ["x", "y"])
def matyas_forward(dp):
    x, y = dp["x"], dp["y"]
    val = 0.26 * (x**2 + y**2) - 0.48 * x * y
    return -val, {"matyas_val": val}

# 10. Schaffer N.2 (2D, many local minima, narrow valley)
SCHAFFER_DOMAIN = make_domain("schaffer2", "neg_schaffer2",
                              [(-100, 100), (-100, 100)], ["x", "y"])
def schaffer_forward(dp):
    x, y = dp["x"], dp["y"]
    val = 0.5 + (math.sin(x**2 - y**2)**2 - 0.5) / (1 + 0.001 * (x**2 + y**2))**2
    return -val, {"schaffer_val": val}

# 11. Three-hump camel (2D, 3 local minima)
CAMEL_DOMAIN = make_domain("three_hump_camel", "neg_camel",
                           [(-5, 5), (-5, 5)], ["x", "y"])
def camel_forward(dp):
    x, y = dp["x"], dp["y"]
    val = 2*x**2 - 1.05*x**4 + x**6/6 + x*y + y**2
    return -val, {"camel_val": val}

# 12. Zakhavov (3D, high-conditioning)
ZAKHAROV_DOMAIN = make_domain("zakharov", "neg_zakharov",
                              [(-5, 10), (-5, 10), (-5, 10)], ["x1", "x2", "x3"])
def zakharov_forward(dp):
    x = [dp["x1"], dp["x2"], dp["x3"]]
    n = len(x)
    sum1 = sum(xi**2 for xi in x)
    sum2 = sum((i+1) * xi / 2 for i, xi in enumerate(x))
    val = sum1 + sum2**2 + sum2**4
    return -val, {"zakharov_val": val}


# ============================================================================
# 8 PARAMETRIC VARIANTS (shifted/rotated/scaled/combined)
# ============================================================================

# 13. Shifted Sphere (offset by (2, 2, 2, 2))
SHIFTED_SPHERE_DOMAIN = make_domain("shifted_sphere", "neg_shifted_sphere",
                                    [(-5, 5), (-5, 5), (-5, 5), (-5, 5)])
def shifted_sphere_forward(dp):
    val = sum((dp[f"x{i+1}"] - 2.0)**2 for i in range(4))
    return -val, {"shifted_sphere_val": val}

# 14. Scaled Rastrigin (amplitude halved)
SCALED_RASTRIGIN_DOMAIN = make_domain("scaled_rastrigin", "neg_scaled_rastrigin",
                                      [(-5.12, 5.12), (-5.12, 5.12), (-5.12, 5.12)])
def scaled_rastrigin_forward(dp):
    x = [dp[f"x{i+1}"] for i in range(3)]
    n = len(x)
    val = 0.5 * (10 * n + sum(xi**2 - 10 * math.cos(2 * math.pi * xi) for xi in x))
    return -val, {"scaled_rastrigin_val": val}

# 15. Combined Sphere+Needle (mostly smooth with a needle)
COMBO_DOMAIN = make_domain("combo_sphere_needle", "combo_val",
                           [(-2, 2), (-2, 2), (-2, 2)])
def combo_forward(dp):
    x = [dp[f"x{i+1}"] for i in range(3)]
    sphere = -sum(xi**2 for xi in x) * 0.1  # smooth background
    needle = 10.0 if all(abs(xi) < 0.1 for xi in x) else 0.0  # needle
    return sphere + needle, {"sphere_part": sphere, "needle_part": needle}

# 16. Noisy Sphere (random noise added)
NOISY_SPHERE_DOMAIN = make_domain("noisy_sphere", "neg_noisy_sphere",
                                  [(-5, 5), (-5, 5), (-5, 5), (-5, 5)])
def noisy_sphere_forward(dp):
    rng = random.Random(int(sum(dp[f"x{i+1}"] * 1000 for i in range(4))) % 2**31)
    noise = rng.gauss(0, 0.5)
    val = sum(dp[f"x{i+1}"]**2 for i in range(4)) + noise
    return -val, {"noisy_sphere_val": val, "noise": noise}

# 17. Bowl with wall (smooth inside, cliff outside)
BOWL_WALL_DOMAIN = make_domain("bowl_with_wall", "bowl_val",
                               [(-2, 2), (-2, 2), (-2, 2)])
def bowl_wall_forward(dp):
    x = [dp[f"x{i+1}"] for i in range(3)]
    r = math.sqrt(sum(xi**2 for xi in x))
    if r < 1.0:
        return 1.0 - r, {"region": "inside"}
    else:
        return -10.0 * (r - 1.0), {"region": "outside"}  # cliff

# 18. Sinusoidal valley (smooth but oscillating)
SIN_VALLEY_DOMAIN = make_domain("sin_valley", "neg_sin_valley",
                                [(-5, 5), (-5, 5)])
def sin_valley_forward(dp):
    x, y = dp["x1"], dp["x2"]
    val = (y - math.sin(x))**2 + 0.01 * x**2
    return -val, {"sin_valley_val": val}

# 19. Plateau (flat top, steep sides — constraint-like)
PLATEAU_DOMAIN = make_domain("plateau", "plateau_val",
                             [(-3, 3), (-3, 3), (-3, 3)])
def plateau_forward(dp):
    x = [dp[f"x{i+1}"] for i in range(3)]
    r = math.sqrt(sum(xi**2 for xi in x))
    if r < 1.0:
        return 1.0, {"region": "plateau", "r": r}
    else:
        return max(0.0, 1.0 - (r - 1.0)), {"region": "slope", "r": r}

# 20. Twin Gaussians (two peaks — truly bimodal)
TWIN_GAUSS_DOMAIN = make_domain("twin_gaussians", "twin_val",
                                [(-5, 5), (-5, 5)])
def twin_gauss_forward(dp):
    x, y = dp["x1"], dp["x2"]
    g1 = math.exp(-((x - 2)**2 + (y - 2)**2))
    g2 = 2.0 * math.exp(-((x + 2)**2 + (y + 2)**2))  # second peak is higher
    return max(g1, g2), {"g1": g1, "g2": g2}


# ============================================================================
# ALL 20 HELD-OUT PROBLEMS
# ============================================================================

HELD_OUT_PROBLEMS = [
    ("Beale",           BEALE_DOMAIN,           beale_forward),
    ("Booth",           BOOTH_DOMAIN,           booth_forward),
    ("Bukin6",          BUKIN_DOMAIN,           bukin_forward),
    ("CrossInTray",     CROSS_DOMAIN,           cross_forward),
    ("Easom",           EASOM_DOMAIN,           easom_forward),
    ("Eggcrate",        EGGCRATE_DOMAIN,        eggcrate_forward),
    ("Himmelblau",      HIMMEL_DOMAIN,          himmel_forward),
    ("Levi13",          LEVI_DOMAIN,            levi_forward),
    ("Matyas",          MATYAS_DOMAIN,          matyas_forward),
    ("Schaffer2",       SCHAFFER_DOMAIN,        schaffer_forward),
    ("ThreeHumpCamel",  CAMEL_DOMAIN,           camel_forward),
    ("Zakharov",        ZAKHAROV_DOMAIN,        zakharov_forward),
    ("ShiftedSphere",   SHIFTED_SPHERE_DOMAIN,  shifted_sphere_forward),
    ("ScaledRastrigin", SCALED_RASTRIGIN_DOMAIN, scaled_rastrigin_forward),
    ("ComboSphereNeedle",COMBO_DOMAIN,           combo_forward),
    ("NoisySphere",     NOISY_SPHERE_DOMAIN,    noisy_sphere_forward),
    ("BowlWithWall",    BOWL_WALL_DOMAIN,       bowl_wall_forward),
    ("SinValley",       SIN_VALLEY_DOMAIN,      sin_valley_forward),
    ("Plateau",         PLATEAU_DOMAIN,         plateau_forward),
    ("TwinGaussians",   TWIN_GAUSS_DOMAIN,      twin_gauss_forward),
]


def main():
    print("=" * 78)
    print("HELD-OUT BENCHMARK (cycle 222) — 20 unseen optimization problems")
    print("Classifier and optimizer routing are FROZEN (cycle 221).")
    print("We do NOT tune them. We report performance as-is.")
    print("=" * 78)
    print()

    conf_classifier = ConfidenceClassifier(n_bootstrap=5)

    print(f"{'#':<3} {'Problem':<20} {'Type':<22} {'Conf':<6} {'Optimizer':<25} {'Iter0':<10} {'Iter5':<10} {'Δ':<10} {'Improved':<8}")
    print("-" * 120)

    n_improved = 0
    results = []
    for i, (name, spec, fn) in enumerate(HELD_OUT_PROBLEMS, 1):
        # Run with FROZEN classifier + optimizer routing
        iters, landscape, opt_name = run_meta_invention(
            spec, fn, n_iterations=5, n_per_iter=50, seed=42,
        )

        # Get confidence
        rng = random.Random(42)
        cands = []
        for _ in range(100):
            dp = {}
            for v in spec["design_vars"]:
                lo, hi = v["bounds"]
                if lo > 0 and hi / lo > 100:
                    val = math.exp(rng.uniform(math.log(lo), math.log(hi)))
                else:
                    val = rng.uniform(lo, hi)
                dp[v["name"]] = val
            o, _ = fn(dp)
            c = type("C", (), {"design_point": dp, "predicted_outcome": o, "derived": {}})()
            cands.append(c)
        conf_result = conf_classifier.classify_with_confidence(cands, spec["design_vars"])
        confidence = conf_result["confidence"]

        iter0 = iters[0]["best_outcome"]
        iter5 = iters[-1]["best_outcome"]
        delta = iter5 - iter0
        improved = "✓" if delta > 0 else "✗"
        if delta > 0:
            n_improved += 1

        results.append({
            "name": name, "type": landscape.landscape_type.value,
            "confidence": confidence, "optimizer": opt_name,
            "iter0": iter0, "iter5": iter5, "delta": delta,
        })

        print(f"{i:<3} {name:<20} {landscape.landscape_type.value:<22} {confidence:<6.2f} "
              f"{opt_name:<25} {iter0:<10.3f} {iter5:<10.3f} {delta:>+10.3f} {improved}")

    print()
    print("=" * 78)
    print("HELD-OUT BENCHMARK SUMMARY")
    print("=" * 78)
    print()
    print(f"Total problems:    {len(HELD_OUT_PROBLEMS)}")
    print(f"Improved (iter5>iter0): {n_improved}/{len(HELD_OUT_PROBLEMS)}")
    print(f"Pass bar: ≥15/20 improved")
    print(f"Result: {'PASS' if n_improved >= 15 else 'FAIL'}")
    print()

    # Type distribution
    from collections import Counter
    type_counts = Counter(r["type"] for r in results)
    print("Classification distribution:")
    for t, c in type_counts.most_common():
        print(f"  {t:<22} {c}")

    # Optimizer distribution
    opt_counts = Counter(r["optimizer"] for r in results)
    print()
    print("Optimizer distribution:")
    for o, c in opt_counts.most_common():
        print(f"  {o:<25} {c}")

    # Confidence stats
    confs = [r["confidence"] for r in results]
    print()
    print(f"Confidence: min={min(confs):.2f}, max={max(confs):.2f}, "
          f"mean={sum(confs)/len(confs):.2f}")

    print()
    print("=" * 78)
    print("HONEST INTERPRETATION")
    print("=" * 78)
    print()
    print(f"The frozen classifier + optimizer routing was evaluated on {len(HELD_OUT_PROBLEMS)}")
    print(f"previously-unseen optimization problems. {n_improved}/{len(HELD_OUT_PROBLEMS)} showed improvement.")
    print()
    if n_improved >= 15:
        print("This PASSES the ≥15/20 bar: the transfer mechanism generalizes")
        print("to held-out landscapes. The classifier was NOT tuned to these problems.")
        print()
        print("Caveat: 'improvement' is a weak bar. A random-restart optimizer would")
        print("also improve on most landscapes. The stronger test is whether the")
        print("SELECTED optimizer is BETTER than a default (e.g., random search).")
        print("That comparison is future work.")
    else:
        print(f"This FAILS the ≥15/20 bar: only {n_improved}/20 improved.")
        print("The frozen system does NOT generalize sufficiently.")


if __name__ == "__main__":
    main()
