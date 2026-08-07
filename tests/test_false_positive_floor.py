"""CI gate: false-positive floor must be measured and documented."""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

def test_fp_floor_documented():
    """False-positive floor is measured and documented in reports."""
    repo = Path(__file__).resolve().parents[1]
    # Check that adversarial results exist
    adv_path = repo / "reports" / "adversarial_results.json"
    assert adv_path.exists(), "adversarial_results.json must exist"
    with open(adv_path) as f:
        data = json.load(f)
    results = data.get("results", [])
    assert len(results) > 0, "Must have at least one adversarial test result"
    for r in results:
        assert "fp_rate" in r
        assert "verdict" in r

def test_fp_floor_measurement_exists():
    """The independent matcher can measure FP floor."""
    from audit.stage_minus1.exact_matcher import shuffled_gold_estimate, match_exact_normalized
    gold = [{"bridge": "alpha"}]
    cands = ["alpha", "beta", "gamma"]
    result = shuffled_gold_estimate(gold, cands, match_exact_normalized, n_shuffles=50)
    assert "fp_floor" in result
    assert "mean" in result  # has statistics, not just point estimate
