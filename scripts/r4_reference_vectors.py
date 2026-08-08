#!/usr/bin/env python3
"""r4_reference_vectors.py — Mechanically compute frozen reference vectors for R4.1.

Deterministic. No timestamp. No RNG. Canonical JSON.
Running twice produces identical bytes and identical SHA-256.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.stats import binom

OUTPUT = Path(__file__).resolve().parents[1] / "experiments" / "measurement_discrimination" / "r4_reference_vectors.json"

N = 20
DELTA_MIN = 0.20
ALPHA = 0.05


def mcnemar_analysis(b, c, N):
    n_d = b + c
    theta_hat = (b - c) / N
    p_one_sided = float(binom.sf(b - 1, n_d, 0.5)) if n_d > 0 else 1.0
    se = float(np.sqrt(max(n_d - (b - c) ** 2 / N, 0)) / N)
    cc = 1 / (2 * N)
    ci_lower = theta_hat - 1.96 * se - cc
    ci_upper = theta_hat + 1.96 * se + cc
    passes = (p_one_sided < ALPHA) and (ci_lower > DELTA_MIN)
    return {
        "b": b, "c": c, "N": N, "n_d": n_d,
        "theta_hat": round(theta_hat, 10),
        "p_one_sided": p_one_sided,
        "ci_lower": round(ci_lower, 10),
        "ci_upper": round(ci_upper, 10),
        "passes": passes,
    }


def main():
    vectors = [
        mcnemar_analysis(9, 1, N),
        mcnemar_analysis(12, 1, N),
        mcnemar_analysis(8, 2, N),
        mcnemar_analysis(14, 0, N),
    ]

    payload = {
        "artifact_type": "R4_REFERENCE_VECTORS",
        "calculation_type": "EXACT_BINOMIAL_WALD_CI (deterministic, no simulation, no RNG, no timestamp)",
        "parameters": {
            "N": N,
            "alpha": ALPHA,
            "delta_min": DELTA_MIN,
            "p_value_method": "binom.sf(b-1, n_d, 0.5) (exact one-sided upper tail)",
            "ci_method": "Wald with continuity correction: theta_hat ± 1.96*SE ± 1/(2N)",
            "passes_rule": "p_one_sided < 0.05 AND ci_lower > 0.20",
        },
        "vectors": vectors,
    }

    content_str = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    content_sha = hashlib.sha256(content_str.encode()).hexdigest()
    payload["calculation_content_sha256"] = content_sha

    artifact_without_sha = {k: v for k, v in payload.items() if k != "artifact_sha256"}
    artifact_str = json.dumps(artifact_without_sha, sort_keys=True, separators=(",", ":"))
    artifact_sha = hashlib.sha256(artifact_str.encode()).hexdigest()
    payload["artifact_sha256"] = artifact_sha

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2))

    # Verify reproducibility
    reloaded = json.loads(OUTPUT.read_text())
    reloaded_without = {k: v for k, v in reloaded.items() if k != "artifact_sha256"}
    reloaded_str = json.dumps(reloaded_without, sort_keys=True, separators=(",", ":"))
    reloaded_sha = hashlib.sha256(reloaded_str.encode()).hexdigest()
    assert reloaded_sha == artifact_sha, "REPRODUCIBILITY FAILED"

    print(f"Reference vectors written to {OUTPUT}")
    print(f"calculation_content_sha256: {content_sha[:16]}...")
    print(f"artifact_sha256: {artifact_sha[:16]}...")
    print(f"Reproducibility: VERIFIED")
    print()
    for v in vectors:
        print(f"  b={v['b']}, c={v['c']}: theta={v['theta_hat']}, p={v['p_one_sided']:.10f}, ci_lower={v['ci_lower']:.10f}, passes={v['passes']}")


if __name__ == "__main__":
    main()
