#!/usr/bin/env python3
"""
forward_model_checker.py — DR-75: Verify the forward model is NOT just
reusing a stored KB equation.

The forward model (Stage IV) is supposed to evaluate physics formulas on
the candidate's parameters. If it instead looks up the answer in a
knowledge base (or returns a stored constant), the entire pipeline is
fake — every candidate "predicts" the same value, regardless of its
parameters.

The checker verifies:
  1. Two configs with DIFFERENT parameters produce DIFFERENT predictions.
  2. The prediction is NOT equal to any stored KB value for the same
     metric (adversarial: inject a KB equation as the simulation →
     must fail).
  3. The prediction varies continuously with parameter changes.

Adversarial test: inject a "FakeForwardModel" that always returns a
stored constant — the checker MUST flag it.

Usage:
    from scripts.forward_model_checker import ForwardModelChecker
    checker = ForwardModelChecker()
    report = checker.check(forward_model, sample_configs)
    # report.is_kb_reuse == True/False
"""
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.artifact_generator import (
    Configuration, Component, MATERIAL_PARAMS,
)


@dataclass
class ForwardModelCheckReport:
    """The output of ForwardModelChecker.check()."""
    is_kb_reuse: bool = False           # True = BAD (model is fake)
    is_constant: bool = False           # True = returns same value always
    severity: str = "pass"               # 'pass', 'warn', 'fail'
    reasons: List[str] = field(default_factory=list)
    distinct_predictions: int = 0
    n_configs_tested: int = 0
    kb_match: bool = False               # True = matches a stored KB value
    kb_matches: List[str] = field(default_factory=list)
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_kb_reuse": self.is_kb_reuse,
            "is_constant": self.is_constant,
            "severity": self.severity,
            "reasons": self.reasons,
            "distinct_predictions": self.distinct_predictions,
            "n_configs_tested": self.n_configs_tested,
            "kb_match": self.kb_match,
            "kb_matches": self.kb_matches,
            "timestamp": self.timestamp,
        }


class ForwardModelChecker:
    """DR-75: verify the forward model is not reusing a KB equation."""

    def __init__(self, kb_values: Optional[Dict[str, float]] = None):
        """Args:
            kb_values: known KB-stored values for metrics (to detect reuse).
                e.g., {"ZT": 0.93} — if the model returns 0.93 for ZT
                regardless of parameters, it's reusing the KB.
        """
        self.kb_values: Dict[str, float] = kb_values or {}

    # ----- public API ---------------------------------------------------
    def check(self, forward_model: Any,
              configs: List[Configuration],
              metric: str = "ZT") -> ForwardModelCheckReport:
        """Check whether the forward model is genuinely physics-based.

        Args:
            forward_model: an object with a .predict(config) method
            configs: a list of Configurations with DIFFERENT parameters
            metric: the metric to compare

        Returns:
            ForwardModelCheckReport with is_kb_reuse flag
        """
        reasons: List[str] = []
        kb_matches: List[str] = []

        if not configs:
            return ForwardModelCheckReport(
                severity="warn",
                reasons=["no configs supplied — cannot check"],
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        # Run predictions
        try:
            predictions = [forward_model.predict(c) for c in configs]
        except Exception as e:
            return ForwardModelCheckReport(
                is_kb_reuse=False,
                severity="fail",
                reasons=[f"forward_model.predict() raised: {e!r}"],
                n_configs_tested=len(configs),
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        # Extract the metric from each prediction
        values: List[float] = []
        for p in predictions:
            props = getattr(p, "predicted_properties", {}) or {}
            if metric in props:
                v = props[metric]
                if isinstance(v, (int, float)):
                    values.append(float(v))
        if len(values) < 2:
            return ForwardModelCheckReport(
                severity="warn",
                reasons=[f"could not extract metric '{metric}' from "
                         f"predictions (got {len(values)} values)"],
                n_configs_tested=len(configs),
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        # 1. Distinctness check: different params → different values
        distinct = len(set(round(v, 8) for v in values))
        if distinct == 1:
            reasons.append(
                f"All {len(values)} predictions returned the same value "
                f"({values[0]:.6g}) for metric '{metric}' despite "
                f"different input parameters — model is constant or "
                f"returning a stored KB value.")
            is_constant = True
        else:
            is_constant = False

        # 2. KB-match check
        if metric in self.kb_values:
            kb_val = self.kb_values[metric]
            for v in values:
                if abs(v - kb_val) < 1e-9:
                    kb_matches.append(
                        f"prediction {v} == KB stored value {kb_val}")
        if kb_matches:
            reasons.append(f"Predictions match stored KB values: "
                           f"{kb_matches[:3]}")

        # 3. Variance check (continuous variation)
        if len(values) >= 3:
            mean = sum(values) / len(values)
            variance = sum((v - mean) ** 2 for v in values) / len(values)
            if variance < 1e-12:
                reasons.append(
                    f"Variance of predictions across {len(values)} configs "
                    f"is ~0 — model does not respond to parameter changes.")

        is_kb = bool(reasons)
        if is_constant or kb_matches:
            severity = "fail"
        elif reasons:
            severity = "warn"
        else:
            severity = "pass"

        return ForwardModelCheckReport(
            is_kb_reuse=is_kb,
            is_constant=is_constant,
            severity=severity,
            reasons=reasons,
            distinct_predictions=distinct,
            n_configs_tested=len(configs),
            kb_match=bool(kb_matches),
            kb_matches=kb_matches,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


def main():
    print("=" * 60)
    print("FORWARD MODEL CHECKER (DR-75)")
    print("=" * 60)
    print()

    from scripts.forward_model import ForwardModel

    # Build configs with different Seebeck coefficients
    configs = []
    for i, S in enumerate([100e-6, 200e-6, 300e-6, 400e-6]):
        c = Configuration(
            config_id=f"C{i}", spec_objective="x",
            domain="thermoelectric",
            components=[Component(material="bismuth_telluride", role="active",
                                  parameters={**MATERIAL_PARAMS["bismuth_telluride"],
                                              "seebeck_coefficient": S})],
            structure="monolithic",
            parameters={"thickness_m": 1e-3, "area_m2": 1e-4,
                        "T_hot_K": 400.0, "T_cold_K": 300.0},
            design_operator_chain=["init"],
        )
        c.config_hash = c.compute_hash()
        configs.append(c)

    # Real forward model
    real_fm = ForwardModel()
    checker = ForwardModelChecker(kb_values={"ZT": 0.93})
    r1 = checker.check(real_fm, configs, metric="ZT")
    print(f"Real forward model: kb_reuse={r1.is_kb_reuse} severity={r1.severity}")
    print(f"  distinct_predictions={r1.distinct_predictions}")
    print()

    # Fake forward model that always returns a stored KB value
    class FakeKBForwardModel:
        def predict(self, config):
            from scripts.forward_model import Prediction
            return Prediction(
                config_id=config.config_id,
                config_hash=config.config_hash,
                domain=config.domain,
                predicted_properties={"ZT": 0.93},  # always the same!
            )

    r2 = checker.check(FakeKBForwardModel(), configs, metric="ZT")
    print(f"Fake KB forward model: kb_reuse={r2.is_kb_reuse} severity={r2.severity}")
    print(f"  reasons: {r2.reasons}")


if __name__ == "__main__":
    main()
