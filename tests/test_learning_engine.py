"""Tests for DR-80: learning engine (belief revision + operator ranking)."""
import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.operator_ranking import (
    OperatorRanking, OperatorStats, RankingResult,
)
from scripts.belief_revision import (
    BeliefRevision, BeliefState, Observation,
)


# ---------------------------------------------------------------------------
# DR-80.1: operator_ranking
# ---------------------------------------------------------------------------
def test_ranking_starts_with_all_operators():
    """A fresh ranking has stats for all 14 operators."""
    r = OperatorRanking()
    assert len(r.stats) == 14
    assert all(s.n_applied == 0 for s in r.stats.values())


def test_ranking_records_pass_outcome():
    """record_outcome(passed=True) increments n_passed."""
    r = OperatorRanking()
    s = r.record_outcome("combine", passed=True)
    assert s.n_applied == 1
    assert s.n_passed == 1
    assert s.success_rate == 1.0
    assert s.last_outcome == "pass"


def test_ranking_records_fail_outcome():
    """record_outcome(passed=False) increments n_failed."""
    r = OperatorRanking()
    s = r.record_outcome("combine", passed=False)
    assert s.n_applied == 1
    assert s.n_failed == 1
    assert s.success_rate == 0.0
    assert s.last_outcome == "fail"


def test_ranking_success_rate_mixed():
    """Mixed outcomes produce the correct success rate."""
    r = OperatorRanking()
    r.record_outcome("combine", passed=True)
    r.record_outcome("combine", passed=True)
    r.record_outcome("combine", passed=False)
    s = r.get_stats("combine")
    assert s.n_applied == 3
    assert s.n_passed == 2
    assert abs(s.success_rate - 2/3) < 1e-6


def test_ranking_get_ranking_sorts_by_success():
    """get_ranking returns operators sorted by success_rate descending."""
    r = OperatorRanking()
    # combine: 3/3
    for _ in range(3):
        r.record_outcome("combine", passed=True)
    # invert: 1/3
    r.record_outcome("invert", passed=True)
    for _ in range(2):
        r.record_outcome("invert", passed=False)
    # substitute: 0/3
    for _ in range(3):
        r.record_outcome("substitute", passed=False)

    result = r.get_ranking()
    assert isinstance(result, RankingResult)
    # Combine should be rank 1
    assert result.stats[0].operator == "combine"
    assert result.stats[0].rank == 1
    # Best and worst
    assert result.best_operator == "combine"
    # Substitute must be in the worst group
    worst_stats = [s for s in result.stats if s.success_rate == 0.0]
    assert any(s.operator == "substitute" for s in worst_stats)


def test_ranking_demotes_low_success_operators():
    """Operators below demotion_threshold are flagged as demoted."""
    r = OperatorRanking(demotion_threshold=0.3)
    for _ in range(3):
        r.record_outcome("substitute", passed=False)
    assert r.demote("substitute") is True
    assert r.demote("combine") is False  # no observations yet


def test_ranking_promotes_high_success_operators():
    """Operators above promotion_threshold are flagged as promoted."""
    r = OperatorRanking(promotion_threshold=0.7)
    for _ in range(3):
        r.record_outcome("combine", passed=True)
    assert r.promote("combine") is True


def test_ranking_top_k():
    """top_k returns the top-k operator names by success rate."""
    r = OperatorRanking()
    for _ in range(3):
        r.record_outcome("combine", passed=True)
    for _ in range(2):
        r.record_outcome("invert", passed=True)
    top2 = r.top_k(k=2)
    assert "combine" in top2
    assert "invert" in top2


def test_ranking_record_outcomes_batch():
    """record_outcomes accepts a batch."""
    r = OperatorRanking()
    r.record_outcomes([("combine", True), ("invert", False),
                       ("combine", True)])
    assert r.get_stats("combine").n_applied == 2
    assert r.get_stats("invert").n_applied == 1


def test_ranking_result_serializable():
    import json
    r = OperatorRanking()
    r.record_outcome("combine", passed=True)
    result = r.get_ranking()
    json.dumps(result.to_dict())


def test_ranking_unknown_operator_added():
    """Recording an unknown operator adds it to the stats."""
    r = OperatorRanking(operators=["combine", "invert"])
    assert "substitute" not in r.stats
    r.record_outcome("substitute", passed=True)
    assert "substitute" in r.stats


# ---------------------------------------------------------------------------
# DR-80.2: belief_revision
# ---------------------------------------------------------------------------
def test_belief_starts_uniform():
    """Initial beliefs are uniform across operators."""
    br = BeliefRevision()
    state = br.revise()
    # All operators have equal belief (0.5 with default Beta(1,1))
    beliefs = list(state.beliefs.values())
    assert all(abs(b - beliefs[0]) < 1e-9 for b in beliefs)


def test_belief_observation_updates_belief():
    """Observing 'pass' increases the operator's belief."""
    br = BeliefRevision()
    before = br.get_belief("combine")
    br.observe("combine", passed=True)
    after = br.get_belief("combine")
    assert after > before


def test_belief_observation_fail_decreases_belief():
    """Observing 'fail' decreases the operator's belief."""
    br = BeliefRevision()
    before = br.get_belief("combine")
    br.observe("combine", passed=False)
    after = br.get_belief("combine")
    assert after < before


def test_belief_top_operator_after_observations():
    """After observations, the operator with most passes is top."""
    br = BeliefRevision()
    for _ in range(5):
        br.observe("combine", passed=True)
    for _ in range(3):
        br.observe("substitute", passed=False)
    state = br.revise()
    assert state.top_operator == "combine"
    assert state.beliefs["combine"] > state.beliefs["substitute"]


def test_belief_entropy_decreases_with_observations():
    """As we observe outcomes, the entropy decreases (distribution sharpens)."""
    br = BeliefRevision()
    initial = br.revise()
    for _ in range(10):
        br.observe("combine", passed=True)
    final = br.revise()
    assert final.entropy < initial.entropy


def test_belief_recommended_operators():
    """recommended_operators returns top-k by belief."""
    br = BeliefRevision()
    for _ in range(5):
        br.observe("combine", passed=True)
    for _ in range(2):
        br.observe("invert", passed=True)
    top2 = br.recommended_operators(top_k=2)
    assert top2[0] == "combine"
    assert "invert" in top2


def test_belief_observe_many_batch():
    """observe_many accepts a batch."""
    br = BeliefRevision()
    br.observe_many([("combine", True), ("invert", False),
                     ("combine", True)])
    state = br.revise()
    assert state.n_observations == 3
    assert state.beliefs["combine"] > state.beliefs["invert"]


def test_belief_reset_returns_to_prior():
    """reset() returns beliefs to the prior."""
    br = BeliefRevision()
    br.observe("combine", passed=True)
    assert br.get_belief("combine") != 0.5
    br.reset()
    assert abs(br.get_belief("combine") - 0.5) < 1e-9


def test_belief_state_serializable():
    import json
    br = BeliefRevision()
    br.observe("combine", passed=True)
    state = br.revise()
    json.dumps(state.to_dict())


def test_belief_weighted_observation():
    """Weighted observations count more."""
    br = BeliefRevision()
    # Two passes for 'invert' with weight 1
    br.observe("invert", passed=True)
    br.observe("invert", passed=True)
    # One fail for 'combine' with weight 10
    br.observe("combine", passed=False, weight=10.0)
    # combine's belief should now be lower than invert's
    assert br.get_belief("combine") < br.get_belief("invert")


def test_belief_and_ranking_consistent():
    """BeliefRevision and OperatorRanking agree on the top operator."""
    outcomes = [("combine", True), ("combine", True),
                ("substitute", False), ("substitute", False)]
    br = BeliefRevision()
    br.observe_many(outcomes)
    r = OperatorRanking()
    r.record_outcomes(outcomes)
    br_top = br.recommended_operators(top_k=1)[0]
    r_top = r.top_k(k=1)[0]
    assert br_top == r_top == "combine"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
