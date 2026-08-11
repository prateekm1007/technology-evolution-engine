#!/usr/bin/env python3
"""
operator_ranking.py — DR-80: Rank operators by measured success rate.

Operators that produced failing candidates get demoted. Operators that
produced successful candidates get promoted.

Each operator accumulates:
  - n_applied: how many times it was applied
  - n_passed: how many of the resulting candidates passed acceptance
  - n_failed: how many failed
  - success_rate = n_passed / n_applied

The ranking is updated based on outcomes recorded in the DesignMemory
(DR-79).

Usage:
    from scripts.operator_ranking import OperatorRanking
    ranking = OperatorRanking()
    ranking.record_outcome("combine", passed=True)
    ranking.record_outcome("combine", passed=False)
    rank = ranking.get_ranking()  # sorted list of (operator, success_rate)
"""
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.operator_library import OPERATOR_LIBRARY


@dataclass
class OperatorStats:
    """Per-operator success statistics."""
    operator: str
    n_applied: int = 0
    n_passed: int = 0
    n_failed: int = 0
    success_rate: float = 0.0  # n_passed / n_applied
    rank: int = 0              # 1 = best
    last_outcome: Optional[str] = None  # 'pass' or 'fail'
    last_updated: str = ""


@dataclass
class RankingResult:
    """The output of OperatorRanking.get_ranking()."""
    stats: List[OperatorStats] = field(default_factory=list)
    n_operators: int = 0
    best_operator: Optional[str] = None
    worst_operator: Optional[str] = None
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stats": [s.__dict__ for s in self.stats],
            "n_operators": self.n_operators,
            "best_operator": self.best_operator,
            "worst_operator": self.worst_operator,
            "timestamp": self.timestamp,
        }


class OperatorRanking:
    """DR-80: rank operators by measured success rate."""

    def __init__(self,
                 operators: Optional[List[str]] = None,
                 demotion_threshold: float = 0.3,
                 promotion_threshold: float = 0.7):
        """Args:
            operators: list of operator names (defaults to all 14)
            demotion_threshold: success rate below this is "low"
            promotion_threshold: success rate above this is "high"
        """
        self.operators: List[str] = list(operators) if operators else list(OPERATOR_LIBRARY.names)
        self.demotion_threshold = demotion_threshold
        self.promotion_threshold = promotion_threshold
        self.stats: Dict[str, OperatorStats] = {
            op: OperatorStats(operator=op) for op in self.operators
        }

    # ----- public API ---------------------------------------------------
    def record_outcome(self, operator: str, passed: bool) -> OperatorStats:
        """Record one outcome for an operator application.

        Args:
            operator: the operator name
            passed: did the resulting candidate pass acceptance?

        Returns:
            the updated OperatorStats
        """
        if operator not in self.stats:
            self.stats[operator] = OperatorStats(operator=operator)
        s = self.stats[operator]
        s.n_applied += 1
        if passed:
            s.n_passed += 1
            s.last_outcome = "pass"
        else:
            s.n_failed += 1
            s.last_outcome = "fail"
        s.success_rate = s.n_passed / s.n_applied if s.n_applied > 0 else 0.0
        s.last_updated = datetime.now(timezone.utc).isoformat()
        return s

    def record_outcomes(self, outcomes: List[Tuple[str, bool]]) -> None:
        """Record a batch of (operator, passed) outcomes."""
        for op, passed in outcomes:
            self.record_outcome(op, passed)

    def get_ranking(self) -> RankingResult:
        """Return the current ranking sorted by success_rate descending.

        Ties broken by operator name (for reproducibility).
        """
        sorted_stats = sorted(
            self.stats.values(),
            key=lambda s: (-s.success_rate, s.operator))
        for i, s in enumerate(sorted_stats, 1):
            s.rank = i
        best = sorted_stats[0].operator if sorted_stats else None
        worst = sorted_stats[-1].operator if sorted_stats else None
        return RankingResult(
            stats=sorted_stats,
            n_operators=len(sorted_stats),
            best_operator=best,
            worst_operator=worst,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def get_stats(self, operator: str) -> Optional[OperatorStats]:
        """Get stats for a specific operator."""
        return self.stats.get(operator)

    def promote(self, operator: str) -> bool:
        """Is this operator currently promoted (above promotion_threshold)?"""
        s = self.stats.get(operator)
        if s is None or s.n_applied == 0:
            return False
        return s.success_rate >= self.promotion_threshold

    def demote(self, operator: str) -> bool:
        """Is this operator currently demoted (below demotion_threshold)?"""
        s = self.stats.get(operator)
        if s is None or s.n_applied == 0:
            return False
        return s.success_rate <= self.demotion_threshold

    def top_k(self, k: int = 5) -> List[str]:
        """Return the top-k operator names by success rate."""
        ranking = self.get_ranking()
        return [s.operator for s in ranking.stats[:k]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stats": {op: s.__dict__ for op, s in self.stats.items()},
            "demotion_threshold": self.demotion_threshold,
            "promotion_threshold": self.promotion_threshold,
        }


def main():
    print("=" * 60)
    print("OPERATOR RANKING (DR-80)")
    print("=" * 60)
    print()

    ranking = OperatorRanking()

    # Simulate outcomes
    # 'combine' is great (3/3 pass)
    for _ in range(3):
        ranking.record_outcome("combine", passed=True)
    # 'invert' is mediocre (1 pass, 2 fail)
    ranking.record_outcome("invert", passed=True)
    for _ in range(2):
        ranking.record_outcome("invert", passed=False)
    # 'substitute' is bad (0 pass, 3 fail)
    for _ in range(3):
        ranking.record_outcome("substitute", passed=False)

    result = ranking.get_ranking()
    print(f"Top 5 operators:")
    for s in result.stats[:5]:
        print(f"  rank {s.rank}: {s.operator:15s} "
              f"success={s.success_rate:.2f} "
              f"({s.n_passed}/{s.n_applied})")
    print()
    print(f"Best:  {result.best_operator}")
    print(f"Worst: {result.worst_operator}")
    print()
    print(f"Promoted: {[op for op in ranking.operators if ranking.promote(op)]}")
    print(f"Demoted:  {[op for op in ranking.operators if ranking.demote(op)]}")


if __name__ == "__main__":
    main()
