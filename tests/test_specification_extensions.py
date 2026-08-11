"""Tests for DR-70: specification compiler extensions."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.goal_parser import GoalParser, Goal, GoalParseResult
from scripts.acceptance_criteria import (
    AcceptanceCriteriaCompiler, AcceptanceCriteria,
    AcceptanceCriterion, AcceptanceResult, AcceptanceCheck,
)


# ---------------------------------------------------------------------------
# DR-70.1: goal_parser.py
# ---------------------------------------------------------------------------
def test_goal_parser_relative_increase():
    """'increase efficiency by 20%' with baseline → target = baseline * 1.2."""
    gp = GoalParser()
    g = gp.parse("increase efficiency by 20%", baseline=0.35)
    assert g.metric == "efficiency"
    assert g.direction == "increase"
    assert g.magnitude_kind == "relative"
    assert abs(g.magnitude - 0.20) < 1e-9
    assert abs(g.target - 0.42) < 1e-9


def test_goal_parser_relative_decrease():
    """'reduce cost by 10%' → target = baseline * 0.9."""
    gp = GoalParser()
    g = gp.parse("reduce cost by 10%", baseline=200.0)
    assert g.direction == "decrease"
    assert g.magnitude_kind == "relative"
    assert abs(g.target - 180.0) < 1e-9


def test_goal_parser_absolute_target():
    """'improve ZT to 1.5' → target = 1.5."""
    gp = GoalParser()
    g = gp.parse("improve ZT to 1.5")
    assert g.metric == "ZT"
    assert abs(g.target - 1.5) < 1e-9


def test_goal_parser_halve():
    """'halve thermal conductivity' → target = baseline / 2."""
    gp = GoalParser()
    g = gp.parse("halve thermal conductivity", baseline=1.5)
    assert g.direction == "decrease"
    assert abs(g.target - 0.75) < 1e-9


def test_goal_parser_double():
    """'double the Seebeck coefficient' → target = baseline * 2."""
    gp = GoalParser()
    g = gp.parse("double the Seebeck coefficient", baseline=200e-6)
    assert g.direction == "increase"
    assert abs(g.target - 400e-6) < 1e-12


def test_goal_parser_currency_magnitude():
    """'reduce cost by $50/kg' → absolute magnitude with USD/kg units."""
    gp = GoalParser()
    g = gp.parse("reduce cost by $50/kg", baseline=200.0)
    assert g.magnitude_kind == "absolute"
    assert abs(g.magnitude - 50.0) < 1e-9
    assert "USD" in g.units or "usd" in g.units
    # target = baseline - magnitude
    assert abs(g.target - 150.0) < 1e-9


def test_goal_parser_metric_synonyms():
    """Synonyms map to canonical metric names."""
    gp = GoalParser()
    g1 = gp.parse("improve figure of merit by 10%")
    g2 = gp.parse("increase ZT by 10%")
    assert g1.metric == "ZT"
    assert g2.metric == "ZT"


def test_goal_parser_parse_many_returns_result():
    """parse_many returns a GoalParseResult with goals and unparsed lists."""
    gp = GoalParser()
    result = gp.parse_many([
        "increase efficiency by 20%",
        "reduce cost by 10%",
    ])
    assert isinstance(result, GoalParseResult)
    assert result.n_goals == 2
    assert result.unparsed == []


def test_goal_parser_low_confidence_for_unparseable():
    """Unparseable goals get low confidence."""
    gp = GoalParser()
    g = gp.parse("a very strange goal with no clear direction or magnitude")
    # Metric falls back to the raw text
    assert g.confidence < 0.5


def test_goal_parser_goal_serializable():
    import json
    gp = GoalParser()
    g = gp.parse("increase efficiency by 20%", baseline=0.35)
    json.dumps(g.to_dict())


# ---------------------------------------------------------------------------
# DR-70.2: acceptance_criteria.py
# ---------------------------------------------------------------------------
def test_acceptance_compile_basic():
    """Compile a list of criteria into checkable callables."""
    compiler = AcceptanceCriteriaCompiler()
    criteria = compiler.compile([
        {"metric": "ZT", "operator": ">", "threshold": 1.0},
    ])
    assert len(criteria) == 1
    assert criteria.criteria[0].metric == "ZT"


def test_acceptance_evaluate_pass():
    """A candidate that satisfies all criteria passes."""
    compiler = AcceptanceCriteriaCompiler()
    criteria = compiler.compile([
        {"metric": "ZT", "operator": ">", "threshold": 1.0},
        {"metric": "seebeck_coefficient", "operator": ">", "threshold": 200},
    ])
    result = criteria.evaluate({"ZT": 1.2, "seebeck_coefficient": 250})
    assert result.passed is True
    assert result.n_passed == 2
    assert result.n_failed == 0


def test_acceptance_evaluate_fail():
    """A candidate that fails one criterion fails overall."""
    compiler = AcceptanceCriteriaCompiler()
    criteria = compiler.compile([
        {"metric": "ZT", "operator": ">", "threshold": 1.0},
    ])
    result = criteria.evaluate({"ZT": 0.8})
    assert result.passed is False
    assert result.n_failed == 1
    assert result.checks[0].value == 0.8


def test_acceptance_missing_metric_fails():
    """A missing metric is flagged missing=True and fails overall."""
    compiler = AcceptanceCriteriaCompiler()
    criteria = compiler.compile([
        {"metric": "ZT", "operator": ">", "threshold": 1.0},
    ])
    result = criteria.evaluate({})
    assert result.passed is False
    assert result.n_missing == 1
    assert result.checks[0].missing is True


def test_acceptance_all_operators():
    """All comparison operators evaluate correctly."""
    compiler = AcceptanceCriteriaCompiler()
    criteria = compiler.compile([
        {"metric": "a", "operator": ">", "threshold": 1.0},
        {"metric": "b", "operator": ">=", "threshold": 2.0},
        {"metric": "c", "operator": "<", "threshold": 3.0},
        {"metric": "d", "operator": "<=", "threshold": 4.0},
        {"metric": "e", "operator": "==", "threshold": 5.0},
        {"metric": "f", "operator": "!=", "threshold": 6.0},
    ])
    result = criteria.evaluate({
        "a": 2.0, "b": 2.0, "c": 2.0, "d": 4.0, "e": 5.0, "f": 7.0,
    })
    assert result.passed is True


def test_acceptance_unknown_operator_raises():
    """An unknown operator raises a ValueError."""
    import pytest
    compiler = AcceptanceCriteriaCompiler()
    with pytest.raises(ValueError):
        compiler.compile([{"metric": "x", "operator": "~", "threshold": 1.0}])


def test_acceptance_compile_from_text():
    """Compile a text criterion like 'ZT > 1.0' into a callable."""
    compiler = AcceptanceCriteriaCompiler()
    ac = compiler.compile_from_text("ZT > 1.0")
    assert ac.criteria[0].metric == "ZT"
    assert ac.criteria[0].operator == ">"
    assert ac.criteria[0].threshold == 1.0
    r = ac.evaluate({"ZT": 1.5})
    assert r.passed is True


def test_acceptance_compile_from_specification():
    """Compile from a scripts.specification.Specification."""
    from scripts.specification import SpecificationEngine
    spec = SpecificationEngine().compile(
        "improve thermoelectric efficiency of bismuth telluride")
    compiler = AcceptanceCriteriaCompiler()
    ac = compiler.compile_from_specification(spec)
    assert len(ac) >= 1
    # The spec for thermoelectric should have ZT > 1.0
    metrics = [c.metric for c in ac]
    assert "ZT" in metrics


def test_acceptance_result_serializable():
    import json
    compiler = AcceptanceCriteriaCompiler()
    criteria = compiler.compile([
        {"metric": "ZT", "operator": ">", "threshold": 1.0},
    ])
    result = criteria.evaluate({"ZT": 1.2})
    json.dumps(result.to_dict())


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
