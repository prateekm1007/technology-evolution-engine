#!/usr/bin/env python3
"""
acceptance_criteria.py — DR-70: Generate machine-checkable acceptance criteria.

Given a Specification (or any structured criteria), produce Python callables
that take a candidate (dict of metrics) and return PASS/FAIL with a reason.

Each criterion is compiled into an AcceptanceCriterion dataclass with:
  - metric: the metric name
  - operator: the comparison operator
  - threshold: the bound
  - check_fn: a callable (candidate: dict) -> AcceptanceResult

Example:
  "ZT > 1.0" → check_fn({"ZT": 1.2}) → AcceptanceResult(passed=True, ...)
  "ZT > 1.0" → check_fn({"ZT": 0.8}) → AcceptanceResult(passed=False, ...)

Usage:
    from scripts.acceptance_criteria import AcceptanceCriteriaCompiler
    compiler = AcceptanceCriteriaCompiler()
    criteria = compiler.compile([
        {"metric": "ZT", "operator": ">", "threshold": 1.0},
        {"metric": "cost_per_kg", "operator": "<=", "threshold": 200.0,
         "units": "USD/kg"},
    ])
    result = criteria.evaluate({"ZT": 1.2, "cost_per_kg": 150.0})
    # result.passed == True
"""
import sys
import operator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Callable, Tuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


# Operator lookup table.
OPERATORS: Dict[str, Callable[[float, float], bool]] = {
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "==": operator.eq,
    "!=": operator.ne,
}


@dataclass
class AcceptanceCriterion:
    """A single machine-checkable acceptance criterion."""
    criterion_id: str
    metric: str
    operator: str
    threshold: float
    units: str = ""
    description: str = ""
    check_fn: Callable[[Dict[str, Any]], "AcceptanceCheck"] = field(
        default=None, repr=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "criterion_id": self.criterion_id,
            "metric": self.metric,
            "operator": self.operator,
            "threshold": self.threshold,
            "units": self.units,
            "description": self.description,
        }


@dataclass
class AcceptanceCheck:
    """The result of evaluating one criterion against a candidate."""
    criterion_id: str
    metric: str
    passed: bool
    value: Optional[float] = None
    threshold: Optional[float] = None
    operator: str = ""
    reason: str = ""
    missing: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "criterion_id": self.criterion_id,
            "metric": self.metric,
            "passed": self.passed,
            "value": self.value,
            "threshold": self.threshold,
            "operator": self.operator,
            "reason": self.reason,
            "missing": self.missing,
        }


@dataclass
class AcceptanceResult:
    """The result of evaluating ALL criteria against a candidate."""
    passed: bool
    n_total: int = 0
    n_passed: int = 0
    n_failed: int = 0
    n_missing: int = 0
    checks: List[AcceptanceCheck] = field(default_factory=list)
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "n_total": self.n_total,
            "n_passed": self.n_passed,
            "n_failed": self.n_failed,
            "n_missing": self.n_missing,
            "checks": [c.to_dict() for c in self.checks],
            "timestamp": self.timestamp,
        }


class AcceptanceCriteriaCompiler:
    """DR-70: compile structured criteria into checkable callables."""

    def compile(self, criteria_specs: List[Dict[str, Any]]) -> "AcceptanceCriteria":
        """Compile a list of criterion dicts into an AcceptanceCriteria object.

        Each dict must have: metric, operator, threshold.
        Optional: units, description, criterion_id (auto-assigned if absent).
        """
        compiled: List[AcceptanceCriterion] = []
        for i, spec in enumerate(criteria_specs):
            metric = spec["metric"]
            op = spec["operator"]
            threshold = spec["threshold"]
            if op not in OPERATORS:
                raise ValueError(f"unknown operator: {op}")
            units = spec.get("units", "")
            description = spec.get("description", "")
            cid = spec.get("criterion_id", f"AC-{i:04d}")

            # Build a closure bound to this criterion's parameters
            def make_fn(metric=metric, op=op, threshold=threshold, cid=cid):
                fn = OPERATORS[op]
                def check(candidate: Dict[str, Any]) -> AcceptanceCheck:
                    if metric not in candidate:
                        return AcceptanceCheck(
                            criterion_id=cid, metric=metric, passed=False,
                            threshold=threshold, operator=op,
                            reason=f"metric '{metric}' missing from candidate",
                            missing=True)
                    value = candidate[metric]
                    if value is None or not isinstance(value, (int, float)):
                        return AcceptanceCheck(
                            criterion_id=cid, metric=metric, passed=False,
                            value=value, threshold=threshold, operator=op,
                            reason=f"metric '{metric}' is not numeric: {value!r}",
                            missing=True)
                    ok = bool(fn(value, threshold))
                    return AcceptanceCheck(
                        criterion_id=cid, metric=metric, passed=ok,
                        value=value, threshold=threshold, operator=op,
                        reason=(f"{value} {op} {threshold} = "
                                f"{'PASS' if ok else 'FAIL'}"),
                        missing=False)
                return check

            compiled.append(AcceptanceCriterion(
                criterion_id=cid,
                metric=metric, operator=op, threshold=threshold,
                units=units, description=description,
                check_fn=make_fn(),
            ))
        return AcceptanceCriteria(compiled)

    def compile_from_specification(self, spec) -> "AcceptanceCriteria":
        """Compile criteria from a scripts.specification.Specification object."""
        return self.compile(spec.acceptance_criteria)

    def compile_from_text(self, text: str) -> "AcceptanceCriteria":
        """Compile a single text criterion like 'ZT > 1.0' into a callable.

        Supported syntax: "<metric> <op> <value> [<units>]"
        """
        import re
        m = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*"
                     r"(>=|<=|==|!=|>|<)\s*"
                     r"(-?\d+\.?\d*)\s*"
                     r"([A-Za-z/%·_]*)\s*",
                     text)
        if not m:
            raise ValueError(f"cannot parse criterion text: {text!r}")
        metric = m.group(1)
        op = m.group(2)
        threshold = float(m.group(3))
        units = m.group(4) or ""
        return self.compile([{
            "metric": metric, "operator": op, "threshold": threshold,
            "units": units, "description": text,
        }])


class AcceptanceCriteria:
    """A bundle of compiled acceptance criteria."""

    def __init__(self, criteria: List[AcceptanceCriterion]):
        self.criteria: List[AcceptanceCriterion] = list(criteria)

    def evaluate(self, candidate: Dict[str, Any]) -> AcceptanceResult:
        """Evaluate all criteria against a candidate dict.

        Returns:
            AcceptanceResult with per-criterion checks and overall pass.
        """
        checks = [c.check_fn(candidate) for c in self.criteria]
        n_total = len(checks)
        n_passed = sum(1 for c in checks if c.passed)
        n_failed = sum(1 for c in checks if not c.passed and not c.missing)
        n_missing = sum(1 for c in checks if c.missing)
        return AcceptanceResult(
            passed=(n_failed == 0 and n_missing == 0 and n_total > 0),
            n_total=n_total, n_passed=n_passed,
            n_failed=n_failed, n_missing=n_missing,
            checks=checks,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def __len__(self) -> int:
        return len(self.criteria)

    def __iter__(self):
        return iter(self.criteria)


def main():
    print("=" * 60)
    print("ACCEPTANCE CRITERIA (DR-70)")
    print("=" * 60)
    print()

    compiler = AcceptanceCriteriaCompiler()
    criteria = compiler.compile([
        {"metric": "ZT", "operator": ">", "threshold": 1.0,
         "description": "Figure of merit"},
        {"metric": "seebeck_coefficient", "operator": ">", "threshold": 200,
         "units": "µV/K"},
        {"metric": "cost_per_kg", "operator": "<=", "threshold": 200.0,
         "units": "USD/kg"},
    ])

    print(f"Compiled {len(criteria)} criteria.")
    for c in criteria:
        print(f"  {c.criterion_id}: {c.metric} {c.operator} {c.threshold} "
              f"{c.units}")
    print()

    print("Candidate A (should PASS):")
    result = criteria.evaluate({
        "ZT": 1.2, "seebeck_coefficient": 250, "cost_per_kg": 150.0,
    })
    print(f"  passed={result.passed} ({result.n_passed}/{result.n_total})")
    for ch in result.checks:
        print(f"    {ch.criterion_id}: {ch.metric}={ch.value} "
              f"{ch.operator} {ch.threshold} → {ch.passed}")
    print()

    print("Candidate B (should FAIL on ZT):")
    result = criteria.evaluate({
        "ZT": 0.8, "seebeck_coefficient": 250, "cost_per_kg": 150.0,
    })
    print(f"  passed={result.passed} ({result.n_passed}/{result.n_total})")
    print()

    print("Candidate C (missing metric → missing=True, fail):")
    result = criteria.evaluate({
        "seebeck_coefficient": 250, "cost_per_kg": 150.0,
    })
    print(f"  passed={result.passed}, n_missing={result.n_missing}")
    print()

    print("Compile from text 'ZT > 1.5':")
    ac = compiler.compile_from_text("ZT > 1.5")
    print(f"  {ac.criteria[0].metric} {ac.criteria[0].operator} "
          f"{ac.criteria[0].threshold}")
    r = ac.evaluate({"ZT": 2.0})
    print(f"  ZT=2.0 → passed={r.passed}")


if __name__ == "__main__":
    main()
