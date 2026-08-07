"""CI gate: bootstrap statistics infrastructure exists."""
import sys
import math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

def test_bootstrap_infrastructure_exists():
    """Bootstrap estimation function exists in the audit code."""
    from audit.stage_minus1.exact_matcher import shuffled_gold_estimate
    assert shuffled_gold_estimate is not None

def test_bootstrap_produces_ci():
    """Bootstrap produces confidence intervals, not just point estimates."""
    from audit.stage_minus1.exact_matcher import shuffled_gold_estimate, match_exact_normalized
    gold = [{"bridge": "alpha"}, {"bridge": "beta"}]
    cands = ["alpha", "beta", "gamma", "delta"]
    result = shuffled_gold_estimate(gold, cands, match_exact_normalized, n_shuffles=100)
    assert "mean" in result
    assert "std" in result
    assert "ci95" in result
    assert result["ci95"] >= 0  # CI is non-negative
