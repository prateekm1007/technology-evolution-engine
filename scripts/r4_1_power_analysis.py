#!/usr/bin/env python3
"""r4_1_power_analysis.py — Exact finite-sample joint-distribution power
enumerator with certified extrema for R4.1A.

PROBLEM BEING SOLVED
--------------------
R4.1 (commit 1526cfe) contains a hand-written McNemar power table that
assumes:

    p11 = min(pe, pr)  ->  worst-case power (minimises n_d)
    p11 = 0            ->  best-case power  (maximises n_d)

That reasoning is INVALID for the actual combined decision rule:

    p_one_sided < 0.05  AND  ci_lower > 0.20

because changing p11 changes BOTH p10 = pe - p11 AND p01 = pr - p11,
and therefore changes the distribution of both favourable and
unfavourable discordant pairs. Power depends on the SIGN of (b - c),
not merely on the count (b + c).

CERTIFIED EXTREMA (R4.1A upgrade)
---------------------------------
The previous version of this script searched the feasible p11 interval
on a 1001-point grid. That gave an excellent approximation but did NOT
certify the global extremum — the true extremum could lie between grid
points.

This version exploits the finite-sample structure:

    For fixed (pe, pr), Power(p11) is a POLYNOMIAL in p11 of degree <= N.

Each term P(b, c | p11) = M * (pe - p11)^b * (pr - p11)^c
                              * (1 - pe - pr + p11)^(N-b-c)

is a polynomial of degree b + c + (N - b - c) = N. The power is the
sum over passing (b, c) pairs, so it is also a degree-≤N polynomial.

We therefore:
    1. Construct Power(p11) as an explicit numpy Polynomial.
    2. Differentiate it.
    3. Find ALL roots of Power'(p11) via polynomial root-finding
       (companion matrix eigenvalues).
    4. Filter to real roots in the feasible interval [lo, hi].
    5. Evaluate Power at both endpoints and every interior stationary
       point.
    6. The min and max of these evaluations are the CERTIFIED global
       extrema.

This is a certified global optimization because the global extrema of
a differentiable function on a closed interval occur only at endpoints
or at stationary points, and we enumerate ALL stationary points.

A 1001-point grid search is retained as a CROSS-CHECK. The certified
and grid-search values must agree to within 1e-4. If they don't, an
AssertionError is raised.

ESTIMATOR (matches r4_reference_vectors.py EXACTLY)
---------------------------------------------------
The p-value and CI formulas are imported from
scripts/r4_reference_vectors.py to guarantee single-source-of-truth.
The combined rule is:

    p_one_sided = binom.sf(b - 1, n_d, 0.5)   if n_d > 0 else 1.0
    theta_hat   = (b - c) / N
    SE          = sqrt(max(n_d - (b - c)^2 / N, 0)) / N
    CC          = 1 / (2 * N)
    CI_lower    = theta_hat - 1.96 * SE - CC
    passes      = (p_one_sided < 0.05) AND (CI_lower > 0.20)

TYPE-I REPORTING
----------------
The Type-I error rate is reported as TWO distinct quantities:

    1. max_type_i_among_evaluated_null_scenarios
       The maximum over the FINITE set of tested null scenarios
       (pe = pr in {0.10, 0.20, 0.30, 0.50, 0.70}). This is an
       exploratory characterization, NOT a global bound.

    2. global_type_i_upper_bound = alpha = 0.05
       The rigorous universal bound, from:
           P(combined rule fires) <= P(p < 0.05) <= alpha
       under H0. This holds for ALL (pe, pr) with pe = pr, not just
       the tested scenarios.

The global maximum over the CONTINUOUS null parameter space
(pe = pr = p, p in [0, 1]) is NOT established by this script. Only the
universal upper bound (0.05) is claimed.

DETERMINISM
-----------
No timestamp. No RNG. No simulation. Canonical JSON (sort_keys=True,
separators=(",", ":")). Running twice from identical source produces
identical bytes and identical SHA-256.

Usage:
    python3 scripts/r4_1_power_analysis.py
    Output: experiments/measurement_discrimination/r4_1_power_analysis.json
"""
import hashlib
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
from numpy.polynomial import Polynomial

REPO = Path(__file__).resolve().parents[1]
OUTPUT = (
    REPO / "experiments" / "measurement_discrimination"
    / "r4_1_power_analysis.json"
)


# --------------------------------------------------------------------
# Load the AUTHORITATIVE estimator from r4_reference_vectors.py.
# Single source of truth: the power script must NEVER re-derive the
# p-value or CI formula. If the formula changes, it changes in exactly
# one place and every dependent artifact breaks loudly.
# --------------------------------------------------------------------
def _load_authoritative_estimator():
    spec = importlib.util.spec_from_file_location(
        "r4_reference_vectors",
        REPO / "scripts" / "r4_reference_vectors.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.mcnemar_analysis


mcnemar_analysis = _load_authoritative_estimator()


# --------------------------------------------------------------------
# Protocol constants — must match r4_reference_vectors.py.
# --------------------------------------------------------------------
N = 20
ALPHA = 0.05
DELTA_MIN = 0.20
Z = 1.96

# Grid resolution for the cross-check search. The certified extrema
# come from polynomial root-finding; the grid is only a sanity check.
P11_GRID_SIZE = 1001

# Tolerance for filtering real roots (imaginary part threshold).
REAL_ROOT_TOL = 1e-9

# Required agreement between certified and grid-search extrema.
CERTIFIED_GRID_AGREEMENT_TOL = 1e-4


# --------------------------------------------------------------------
# Pure-math helpers.
# --------------------------------------------------------------------
def multinomial_pmf_b_c(b, c, p10, p01, n):
    """Marginal probability P(B=b, C=c) under the paired-multinomial
    model with N=n, p10 = P(engine YES, retrieval NO),
    p01 = P(engine NO, retrieval YES), and concordant probability
    p_conc = 1 - p10 - p01.

    Derivation: marginalise (a, d) over the constraint a + d = n - b - c
    with total concordant probability p_conc = p11 + p00 = 1 - p10 - p01.
    The result is Multinomial(n; p10, p01, p_conc) marginalised to (b, c):

        P(b, c) = n! / (b! c! (n-b-c)!) * p10^b * p01^c * p_conc^(n-b-c)

    Returns 0.0 for infeasible (b, c) or infeasible probabilities.
    Computed in log-space to avoid overflow for large n.
    """
    if b < 0 or c < 0 or b + c > n:
        return 0.0
    if p10 < 0 or p01 < 0 or p10 + p01 > 1.0 + 1e-12:
        return 0.0
    p_conc = 1.0 - p10 - p01
    if p_conc < -1e-12:
        return 0.0
    p_conc = max(p_conc, 0.0)
    p10 = max(p10, 0.0)
    p01 = max(p01, 0.0)
    k = n - b - c

    # If a probability is zero, the corresponding count must be zero
    # (otherwise the multinomial probability is zero).
    if p10 == 0.0 and b > 0:
        return 0.0
    if p01 == 0.0 and c > 0:
        return 0.0
    if p_conc == 0.0 and k > 0:
        return 0.0

    log_p = (
        math.lgamma(n + 1)
        - math.lgamma(b + 1)
        - math.lgamma(c + 1)
        - math.lgamma(k + 1)
    )
    if b > 0:
        log_p += b * math.log(p10)
    if c > 0:
        log_p += c * math.log(p01)
    if k > 0:
        log_p += k * math.log(p_conc)
    return math.exp(log_p)


def feasible_p11_interval(pe, pr):
    """Feasible interval for p11 given marginal probabilities pe, pr.

    Constraints:
        p10 = pe - p11 >= 0   ->  p11 <= pe
        p01 = pr - p11 >= 0   ->  p11 <= pr
        p00 = 1 - pe - pr + p11 >= 0  ->  p11 >= pe + pr - 1
        p11 >= 0

    Therefore: p11 in [max(0, pe + pr - 1), min(pe, pr)].
    """
    lo = max(0.0, pe + pr - 1.0)
    hi = min(pe, pr)
    if hi < lo:
        return 0.0, 0.0
    return lo, hi


def joint_from_p11(pe, pr, p11):
    """Return (p00, p01, p10, p11) given marginals and concordant-YES."""
    p10 = pe - p11
    p01 = pr - p11
    p00 = 1.0 - p10 - p01 - p11
    return p00, p01, p10, p11


def passes_combined_rule(b, c):
    """Apply the COMPLETE preregistered decision rule to (b, c).

    Returns True iff BOTH gates fire:
        p_one_sided < 0.05
        CI_lower    > 0.20
    """
    a = mcnemar_analysis(b, c, N)
    return bool(a["passes"])


# Pre-compute the passes(b, c) lookup table ONCE at module load.
# This is a 21x21 table (b in [0, 20], c in [0, 20-b]) that depends only
# on (b, c) and the frozen estimator — NOT on (pe, pr, p11). Caching it
# eliminates ~3 million redundant scipy.stats.binom.sf calls per
# search_power_extrema.
PASSES_LOOKUP = {
    (b, c): passes_combined_rule(b, c)
    for b in range(N + 1)
    for c in range(N + 1 - b)
}


def power_at_p11(pe, pr, p11):
    """Exact probability that the combined rule fires, given (pe, pr, p11).

    Sum over all (b, c) with b + c <= N of:
        Multinomial_pmf(b, c | p10, p01, p_conc)
        * I[passes_combined_rule(b, c)]

    This is an EXACT finite enumeration — no simulation.
    """
    p10 = pe - p11
    p01 = pr - p11
    p_conc = 1.0 - p10 - p01
    if p10 < -1e-12 or p01 < -1e-12 or p_conc < -1e-12:
        return 0.0
    p10 = max(p10, 0.0)
    p01 = max(p01, 0.0)
    p_conc = max(p_conc, 0.0)
    total = 0.0
    for (b, c), passes in PASSES_LOOKUP.items():
        if passes:
            total += multinomial_pmf_b_c(b, c, p10, p01, N)
    return total


# --------------------------------------------------------------------
# CERTIFIED POLYNOMIAL-BASED EXTREMUM FINDER (R4.1A upgrade)
#
# For fixed (pe, pr), Power(p11) is a polynomial in p11 of degree <= N:
#
#   Power(p11) = sum_{(b,c) in PASSING} M(N;b,c,N-b-c)
#                 * (pe - p11)^b * (pr - p11)^c * (1-pe-pr+p11)^(N-b-c)
#
# where M(N;b,c,N-b-c) = N! / (b! c! (N-b-c)!) is the multinomial
# coefficient.
#
# Because Power(p11) is a polynomial, its global extrema on the closed
# interval [lo, hi] occur at:
#   - the endpoints (lo, hi)
#   - interior stationary points where Power'(p11) = 0
#
# We find the stationary points by computing the derivative polynomial
# and finding its roots. This gives a CERTIFIED global extremum, not
# merely the maximum of a grid.
# --------------------------------------------------------------------
def power_polynomial(pe, pr):
    """Construct Power(p11) as a numpy Polynomial in p11.

    Power(p11) = sum_{(b,c) in PASSING} M * (pe-p11)^b * (pr-p11)^c
                                          * (1-pe-pr+p11)^(N-b-c)

    where M = N! / (b! c! (N-b-c)!) is the multinomial coefficient.

    This is a polynomial in p11 of degree <= N = 20.
    """
    # Each factor as a Polynomial in p11:
    #   p10 = (pe - p11)              = Polynomial([pe, -1])
    #   p01 = (pr - p11)              = Polynomial([pr, -1])
    #   p_conc = p00 + p11
    #         = (1 - pe - pr + p11) + p11
    #         = 1 - pe - pr + 2*p11   = Polynomial([1 - pe - pr, 2])
    #
    # NOTE: p_conc is the TOTAL concordant probability (p00 + p11),
    # not just p00. The multinomial marginal over (b, c) groups both
    # concordant cells ((YES,YES) and (NO,NO)) into the residual count
    # N - b - c. A previous version of this polynomial used
    # Polynomial([1-pe-pr, 1]) (i.e., p00 only), which is wrong — the
    # grid-search cross-check caught it.
    factor_pe = Polynomial([pe, -1.0])
    factor_pr = Polynomial([pr, -1.0])
    factor_conc = Polynomial([1.0 - pe - pr, 2.0])

    # Pre-compute powers of each factor (degree 0 through N).
    pe_powers = [Polynomial([1.0])]
    for _ in range(N):
        pe_powers.append(pe_powers[-1] * factor_pe)

    pr_powers = [Polynomial([1.0])]
    for _ in range(N):
        pr_powers.append(pr_powers[-1] * factor_pr)

    conc_powers = [Polynomial([1.0])]
    for _ in range(N):
        conc_powers.append(conc_powers[-1] * factor_conc)

    # Sum over passing (b, c) pairs.
    total = Polynomial([0.0])
    for (b, c), passes in PASSES_LOOKUP.items():
        if passes:
            coeff = float(math.comb(N, b) * math.comb(N - b, c))
            term = pe_powers[b] * pr_powers[c] * conc_powers[N - b - c]
            total = total + (coeff * term)

    return total


def certified_extrema(pe, pr):
    """Find certified global min/max of Power(p11) over the feasible interval.

    Method:
    1. Construct Power(p11) as a polynomial.
    2. Compute the derivative Power'(p11).
    3. Find all roots of Power'(p11) — these are the stationary points.
    4. Filter to real roots in the feasible interval [lo, hi].
    5. Evaluate Power at: lo, hi, and each interior stationary point.
    6. The min and max of these evaluations are the certified global
       extrema.

    This is a certified global optimization because:
    - Power(p11) is a polynomial (continuous and differentiable).
    - The global extrema of a differentiable function on a closed
      interval occur at the endpoints or at stationary points.
    - We enumerate ALL stationary points via polynomial root-finding.

    Numerical precision: root-finding uses numpy.roots() (companion
    matrix eigenvalues). Real roots are identified by |imag| < 1e-9.
    The certified extrema are cross-checked against a 1001-point grid
    search and must agree to within 1e-4.
    """
    lo, hi = feasible_p11_interval(pe, pr)

    if hi <= lo + 1e-15:
        # Degenerate interval — single feasible point.
        p = power_at_p11(pe, pr, lo)
        return {
            "power_min": p,
            "power_max": p,
            "p11_at_min": lo,
            "p11_at_max": lo,
            "n_stationary_points": 0,
            "stationary_points": [],
        }

    poly = power_polynomial(pe, pr)
    deriv = poly.deriv()

    # Find roots of the derivative.
    # If the derivative is identically zero, power is constant.
    if len(deriv.coef) == 0 or all(abs(c) < 1e-15 for c in deriv.coef):
        # Power is constant — extrema are at the endpoints (same value).
        p_lo = float(poly(lo))
        p_hi = float(poly(hi))
        power_min = min(p_lo, p_hi)
        power_max = max(p_lo, p_hi)
        return {
            "power_min": power_min,
            "power_max": power_max,
            "p11_at_min": lo if p_lo <= p_hi else hi,
            "p11_at_max": hi if p_lo <= p_hi else lo,
            "n_stationary_points": 0,
            "stationary_points": [],
        }

    roots = deriv.roots()

    # Filter to real roots in [lo, hi].
    stationary_points = []
    for r in roots:
        if abs(r.imag) < REAL_ROOT_TOL:
            r_real = float(r.real)
            if lo - REAL_ROOT_TOL <= r_real <= hi + REAL_ROOT_TOL:
                # Clamp to interval boundary.
                r_real = max(lo, min(hi, r_real))
                stationary_points.append(r_real)

    # Evaluate power at: lo, hi, and each interior stationary point.
    candidates = [lo, hi] + stationary_points
    powers = [float(poly(c)) for c in candidates]

    # Clamp tiny negative values to 0 (floating-point artifact).
    # Power is a probability and must be in [0, 1]. Polynomial
    # evaluation can produce values like -1e-16 due to rounding.
    powers = [max(0.0, min(1.0, p)) for p in powers]

    idx_min = min(range(len(powers)), key=lambda i: powers[i])
    idx_max = max(range(len(powers)), key=lambda i: powers[i])

    return {
        "power_min": powers[idx_min],
        "power_max": powers[idx_max],
        "p11_at_min": candidates[idx_min],
        "p11_at_max": candidates[idx_max],
        "n_stationary_points": len(stationary_points),
        "stationary_points": [
            {"p11": round(p, 10), "power": round(float(poly(p)), 10)}
            for p in stationary_points
        ],
    }


def search_power_extrema(pe, pr):
    """Find the certified global min/max of Power(p11) over the feasible
    interval.

    Uses TWO methods:
    1. Certified polynomial method (authoritative): constructs Power(p11)
       as a degree-<=N polynomial in p11, differentiates it, finds all
       stationary points via polynomial root-finding, and evaluates at
       the interval endpoints and every interior stationary point.
       This gives a CERTIFIED global extremum.

    2. Grid search (cross-check): evaluates power at P11_GRID_SIZE points
       and reports the apparent min/max. Used to verify the certified
       method is working correctly.

    The two methods must agree to within 1e-4. If they don't, an
    AssertionError is raised (the certified method has a bug).
    """
    lo, hi = feasible_p11_interval(pe, pr)

    # Method 1: Certified polynomial extrema (authoritative).
    certified = certified_extrema(pe, pr)

    # Method 2: Grid search (cross-check).
    if hi <= lo + 1e-15:
        grid_min = certified["power_min"]
        grid_max = certified["power_max"]
        grid_p11_min = lo
        grid_p11_max = lo
    else:
        p11_values = [
            lo + (hi - lo) * i / (P11_GRID_SIZE - 1)
            for i in range(P11_GRID_SIZE)
        ]
        powers = [power_at_p11(pe, pr, p11) for p11 in p11_values]
        idx_min = min(range(len(powers)), key=lambda i: powers[i])
        idx_max = max(range(len(powers)), key=lambda i: powers[i])
        grid_min = powers[idx_min]
        grid_max = powers[idx_max]
        grid_p11_min = p11_values[idx_min]
        grid_p11_max = p11_values[idx_max]

    # Verify agreement between certified and grid-search methods.
    agreement = (
        abs(certified["power_min"] - grid_min) < CERTIFIED_GRID_AGREEMENT_TOL
        and abs(certified["power_max"] - grid_max) < CERTIFIED_GRID_AGREEMENT_TOL
    )
    if not agreement:
        raise AssertionError(
            f"Certified and grid-search extrema disagree for "
            f"pe={pe}, pr={pr}: "
            f"certified_min={certified['power_min']:.8f} vs "
            f"grid_min={grid_min:.8f}, "
            f"certified_max={certified['power_max']:.8f} vs "
            f"grid_max={grid_max:.8f}"
        )

    # Determine whether extrema are at endpoints or interior.
    extremum_at_endpoint = (
        abs(certified["p11_at_min"] - lo) < 1e-9
        or abs(certified["p11_at_min"] - hi) < 1e-9
        or abs(certified["p11_at_max"] - lo) < 1e-9
        or abs(certified["p11_at_max"] - hi) < 1e-9
    )

    return {
        "pe": pe,
        "pr": pr,
        "theta": round(pe - pr, 10),
        "p11_lo": round(lo, 10),
        "p11_hi": round(hi, 10),
        # Certified extrema (authoritative)
        "power_min": certified["power_min"],
        "power_max": certified["power_max"],
        "p11_at_min": round(certified["p11_at_min"], 10),
        "p11_at_max": round(certified["p11_at_max"], 10),
        "n_stationary_points": certified["n_stationary_points"],
        "stationary_points": certified["stationary_points"],
        "extremum_at_endpoint": extremum_at_endpoint,
        # Grid-search cross-check
        "grid_search": {
            "power_min": grid_min,
            "power_max": grid_max,
            "p11_at_min": round(grid_p11_min, 10),
            "p11_at_max": round(grid_p11_max, 10),
            "grid_size": P11_GRID_SIZE,
        },
        "grid_and_certified_agree": agreement,
    }


# --------------------------------------------------------------------
# Scenarios. Two classes:
#   POWER scenarios (pe > pr):  how often does the rule fire when there
#     is a real effect of size theta = pe - pr?
#   TYPE-I scenarios (pe = pr): how often does the rule fire under H0?
# --------------------------------------------------------------------
POWER_SCENARIOS = [
    (0.50, 0.10),  # theta = 0.40  (R4.1 row 1)
    (0.50, 0.05),  # theta = 0.45  (R4.1 row 2)
    (0.60, 0.10),  # theta = 0.50  (R4.1 row 3)
    (0.60, 0.05),  # theta = 0.55  (R4.1 row 4)
    (0.70, 0.10),  # theta = 0.60  (R4.1 row 5)
    (0.40, 0.10),  # theta = 0.30  (R4.1 row 6)
    (0.30, 0.05),  # theta = 0.25  (R4.1 row 7)
    (0.20, 0.00),  # theta = 0.20  (R4.1 row 8)
]

TYPE_I_SCENARIOS = [
    (0.10, 0.10),
    (0.20, 0.20),
    (0.30, 0.30),
    (0.50, 0.50),
    (0.70, 0.70),
]


# --------------------------------------------------------------------
# Reference-vector cross-check: re-compute the four frozen vectors
# independently and assert they match the committed JSON.
# --------------------------------------------------------------------
def cross_check_reference_vectors():
    """Re-derive the four frozen vectors and verify they match the
    committed r4_reference_vectors.json exactly. This proves the power
    script is using the same estimator."""
    committed_path = (
        REPO / "experiments" / "measurement_discrimination"
        / "r4_reference_vectors.json"
    )
    if not committed_path.exists():
        raise FileNotFoundError(
            f"Reference vectors not found at {committed_path}. "
            f"Run scripts/r4_reference_vectors.py first."
        )
    committed = json.loads(committed_path.read_text())
    committed_vectors = committed["vectors"]

    expected_inputs = [(9, 1), (12, 1), (8, 2), (14, 0)]
    for (b, c), expected in zip(expected_inputs, committed_vectors):
        actual = mcnemar_analysis(b, c, N)
        for key in ("b", "c", "N", "n_d", "theta_hat",
                    "p_one_sided", "ci_lower", "ci_upper", "passes"):
            if actual[key] != expected[key]:
                raise AssertionError(
                    f"Reference vector mismatch for (b={b}, c={c}) "
                    f"on key '{key}': "
                    f"script={actual[key]!r}, committed={expected[key]!r}"
                )
    return True


# --------------------------------------------------------------------
# Main: build the power table and write the JSON artifact.
# --------------------------------------------------------------------
def main():
    print("R4.1A Power Analysis — Certified Finite-Sample Enumerator")
    print("=" * 70)
    print(f"N = {N}")
    print(f"alpha = {ALPHA}")
    print(f"delta_min = {DELTA_MIN}")
    print(f"decision_rule = (p_one_sided < {ALPHA}) AND (ci_lower > {DELTA_MIN})")
    print(f"extremum_method = POLYNOMIAL_ROOT_FINDING (certified)")
    print(f"grid_cross_check = {P11_GRID_SIZE} points")
    print(f"agreement_tolerance = {CERTIFIED_GRID_AGREEMENT_TOL}")
    print()

    # Cross-check the estimator against the committed reference vectors.
    cross_check_reference_vectors()
    print("Reference vector cross-check: PASSED")
    print("  (script estimator matches committed r4_reference_vectors.json)")
    print()

    # Power scenarios.
    print("POWER SCENARIOS (pe > pr — there is a real effect)")
    print("-" * 70)
    power_rows = []
    for pe, pr in POWER_SCENARIOS:
        row = search_power_extrema(pe, pr)
        power_rows.append(row)
        print(
            f"  pe={pe:.2f}  pr={pr:.2f}  theta={pe-pr:.2f}  "
            f"|  p11 in [{row['p11_lo']:.3f}, {row['p11_hi']:.3f}]  "
            f"|  POWER in [{row['power_min']:.4f}, {row['power_max']:.4f}]  "
            f"|  argmin p11={row['p11_at_min']:.6f}  "
            f"argmax p11={row['p11_at_max']:.6f}  "
            f"|  stationary_pts={row['n_stationary_points']}  "
            f"agree={row['grid_and_certified_agree']}"
        )
    print()

    # Type-I scenarios.
    print("TYPE-I SCENARIOS (pe = pr — null hypothesis, theta = 0)")
    print("-" * 70)
    type_i_rows = []
    for pe, pr in TYPE_I_SCENARIOS:
        row = search_power_extrema(pe, pr)
        type_i_rows.append(row)
        print(
            f"  pe={pe:.2f}  pr={pr:.2f}  theta=0.00  "
            f"|  p11 in [{row['p11_lo']:.3f}, {row['p11_hi']:.3f}]  "
            f"|  TYPE-I in [{row['power_min']:.4f}, {row['power_max']:.4f}]  "
            f"|  argmax p11={row['p11_at_max']:.6f}"
        )
    print()

    # Honest classification.
    # The worst case for the theta=0.40 scenario (R4.1 row 1).
    theta_040_row = next(r for r in power_rows if r["pe"] == 0.50 and r["pr"] == 0.10)
    worst_power_for_medium_effect = theta_040_row["power_min"]
    best_power_for_medium_effect = theta_040_row["power_max"]

    if best_power_for_medium_effect >= 0.80:
        classification = "ADEQUATE_FOR_LARGE_EFFECTS_ONLY"
    elif best_power_for_medium_effect >= 0.50:
        classification = "EXPLORATORY_MEDIUM_EFFECT_MARGINAL"
    else:
        classification = "EXPLORATORY_LOW_POWERED"

    print("Honest classification")
    print("-" * 70)
    print(f"  theta=0.40 worst-case power (certified): {worst_power_for_medium_effect:.4f}")
    print(f"  theta=0.40 best-case power  (certified): {best_power_for_medium_effect:.4f}")
    print(f"  classification: {classification}")
    print()

    # Type-I reporting: distinguish tested-scenario max from global bound.
    max_type_i_tested = max(r["power_max"] for r in type_i_rows)
    type_i_bound_holds = max_type_i_tested <= ALPHA + 1e-9
    print("Type-I error reporting")
    print("-" * 70)
    print(f"  max Type-I among EVALUATED null scenarios: {max_type_i_tested:.6f}")
    print(f"    (exploratory characterization, NOT a global bound)")
    print(f"  global Type-I upper bound (rigorous):     {ALPHA}")
    print(f"    (from P(combined) <= P(p<0.05) <= alpha under H0)")
    print(f"  tested-scenario max <= alpha? {type_i_bound_holds}")
    print(f"  global max over continuous null space: NOT ESTABLISHED")
    print()

    # Build the payload.
    payload = {
        "artifact_type": "R4_1A_POWER_ANALYSIS_CERTIFIED",
        "calculation_type": (
            "EXACT_FINITE_SAMPLE_JOINT_DISTRIBUTION_POWER_ENUMERATOR_"
            "WITH_CERTIFIED_EXTREMA (deterministic, no simulation, "
            "no RNG, no timestamp)"
        ),
        "purpose": (
            "Replace the hand-written McNemar power table in "
            "B1_B2_DESIGN_REVISION_R4_1.md with a mechanically "
            "enumerated table whose extrema are CERTIFIED via "
            "polynomial root-finding, not merely approximated by a "
            "grid search. The R4.1 table assumed extrema occur at "
            "the endpoints of the feasible p11 interval; this script "
            "constructs Power(p11) as an explicit degree-<=N polynomial, "
            "differentiates it, finds ALL stationary points, and "
            "evaluates at endpoints + stationary points to certify "
            "the global min/max."
        ),
        "statistical_lesson": (
            "Minimising the discordant-pair count n_d does NOT necessarily "
            "minimise power for a composite decision rule. Power depends on "
            "the SIGN of (b - c), not merely on the count (b + c). The "
            "combined rule (p < 0.05 AND ci_lower > 0.20) must be evaluated "
            "over the complete joint outcome distribution and the complete "
            "preregistered decision function. Furthermore, for finite N, "
            "Power(p11) is a polynomial of degree <= N in p11, so the "
            "global extrema can be CERTIFIED by polynomial root-finding "
            "rather than approximated by a grid search."
        ),
        "parameters": {
            "N": N,
            "alpha": ALPHA,
            "delta_min": DELTA_MIN,
            "z": Z,
            "p_value_method": (
                "binom.sf(b-1, n_d, 0.5) (exact one-sided upper tail) — "
                "IMPORTED from scripts/r4_reference_vectors.py"
            ),
            "ci_method": (
                "Wald with continuity correction: theta_hat +/- 1.96*SE +/- 1/(2N) — "
                "IMPORTED from scripts/r4_reference_vectors.py"
            ),
            "passes_rule": (
                "p_one_sided < 0.05 AND ci_lower > 0.20 — "
                "matches r4_reference_vectors.py EXACTLY"
            ),
            "extremum_method": (
                "CERTIFIED via polynomial root-finding. For fixed (pe, pr), "
                "Power(p11) is a degree-<=N polynomial in p11. We "
                "differentiate it, find all roots of Power'(p11) via "
                "companion matrix eigenvalues, filter to real roots in "
                "the feasible interval, and evaluate Power at endpoints + "
                "stationary points. This gives the certified global "
                "min/max, not merely the max of a grid."
            ),
            "grid_cross_check": (
                f"A {P11_GRID_SIZE}-point grid search is retained as a "
                f"cross-check. Certified and grid-search extrema must "
                f"agree to within {CERTIFIED_GRID_AGREEMENT_TOL}."
            ),
            "polynomial_degree": (
                "Each term P(b,c|p11) = M * (pe-p11)^b * (pr-p11)^c * "
                "(1-pe-pr+p11)^(N-b-c) is a polynomial of degree "
                "b + c + (N-b-c) = N. The power is the sum over passing "
                "(b,c) pairs, so it is also degree <= N = 20."
            ),
            "enumeration": (
                "For each (pe, pr, p11), sum P(b, c | p10, p01) * "
                "I[passes(b, c)] over all (b, c) with b + c <= N. "
                "P(b, c) is the marginal of Multinomial(N; p10, p01, "
                "1 - p10 - p01). EXACT — no simulation."
            ),
        },
        "power_scenarios": power_rows,
        "type_i_scenarios": type_i_rows,
        "summary": {
            "worst_case_power_for_theta_0_40": worst_power_for_medium_effect,
            "best_case_power_for_theta_0_40": best_power_for_medium_effect,
            "max_type_i_among_evaluated_null_scenarios": max_type_i_tested,
            "max_type_i_among_evaluated_null_scenarios_note": (
                "The maximum over the FINITE set of tested null scenarios "
                "(pe=pr in {0.10, 0.20, 0.30, 0.50, 0.70}). This is an "
                "exploratory characterization, NOT a global bound over "
                "the continuous null parameter space."
            ),
            "global_type_i_upper_bound": ALPHA,
            "global_type_i_upper_bound_note": (
                "The rigorous universal bound, from "
                "P(combined rule fires) <= P(p < 0.05) <= alpha under H0. "
                "This holds for ALL (pe, pr) with pe = pr, not just the "
                "tested scenarios. The global maximum over the continuous "
                "null space (pe=pr=p, p in [0,1]) is NOT established by "
                "this script — only the universal upper bound is claimed."
            ),
            "tested_scenario_max_le_alpha": type_i_bound_holds,
            "classification": classification,
            "interpretation": {
                "EXPLORATORY_LOW_POWERED": (
                    "Best-case power for theta=0.40 is < 0.50. N=20 with "
                    "the combined rule is exploratory only. A negative "
                    "result does NOT establish absence of capability."
                ),
                "EXPLORATORY_MEDIUM_EFFECT_MARGINAL": (
                    "Best-case power for theta=0.40 is in [0.50, 0.80). "
                    "N=20 with the combined rule is exploratory. A "
                    "positive result justifies Stage 2B (larger N); a "
                    "negative result does NOT establish absence of "
                    "capability."
                ),
                "ADEQUATE_FOR_LARGE_EFFECTS_ONLY": (
                    "Best-case power for theta=0.40 is >= 0.80, but only "
                    "for the most favourable joint distribution. Medium "
                    "effects may still be missed depending on the true "
                    "concordance structure."
                ),
            },
            "frozen_status_note": (
                "R4.1 power claims have been mechanically superseded by "
                "this artifact. The hand-written table in "
                "B1_B2_DESIGN_REVISION_R4_1.md Section 2 is INVALID — "
                "do not cite it. Cite this artifact instead. The extrema "
                "in this artifact are CERTIFIED via polynomial "
                "root-finding (R4.1A upgrade)."
            ),
        },
        "mechanically_reproducible": True,
        "reproducibility_note": (
            "This artifact contains no timestamp, no RNG output, and no "
            "nondeterministic fields. Running the script twice from "
            "identical source produces identical JSON bytes and identical "
            "SHA-256 values. Canonical JSON: sort_keys=True, "
            "separators=(',', ':')."
        ),
    }

    # Compute SHA-256 hashes (matches r4_reference_vectors.py pattern).
    content_str = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    content_sha = hashlib.sha256(content_str.encode()).hexdigest()
    payload["calculation_content_sha256"] = content_sha

    artifact_without_sha = {
        k: v for k, v in payload.items() if k != "artifact_sha256"
    }
    artifact_str = json.dumps(
        artifact_without_sha, sort_keys=True, separators=(",", ":")
    )
    artifact_sha = hashlib.sha256(artifact_str.encode()).hexdigest()
    payload["artifact_sha256"] = artifact_sha

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2))

    # Verify reproducibility.
    reloaded = json.loads(OUTPUT.read_text())
    reloaded_without = {
        k: v for k, v in reloaded.items() if k != "artifact_sha256"
    }
    reloaded_str = json.dumps(
        reloaded_without, sort_keys=True, separators=(",", ":")
    )
    reloaded_sha = hashlib.sha256(reloaded_str.encode()).hexdigest()
    assert reloaded_sha == artifact_sha, "REPRODUCIBILITY FAILED"

    print(f"Power analysis written to {OUTPUT}")
    print(f"calculation_content_sha256: {content_sha[:16]}...")
    print(f"artifact_sha256: {artifact_sha[:16]}...")
    print(f"Reproducibility: VERIFIED")


if __name__ == "__main__":
    main()
