#!/usr/bin/env python3
"""
residual_analysis.py — DR-78: Analyze prediction-vs-measurement residuals.

Given a list of residuals (predicted - measured) for one or more metrics,
identify systematic biases:

  - Mean bias (is the prediction consistently higher or lower than measured?)
  - Per-metric bias (which metrics are most biased?)
  - Trend vs parameter value (does the bias grow with a parameter?)
  - Outliers (configs with extreme residuals)
  - Recommended correction (multiplicative factor to apply to predictions
    of this metric in future iterations)

Usage:
    from scripts.residual_analysis import ResidualAnalyzer
    analyzer = ResidualAnalyzer()
    report = analyzer.analyze(residuals)
    # report.per_metric_bias['ZT'] = BiasReport(...)
"""
import sys
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@dataclass
class BiasReport:
    """Per-metric bias analysis."""
    metric: str
    n_samples: int = 0
    mean_residual: float = 0.0     # mean(predicted - measured)
    mean_relative_residual: float = 0.0  # mean(residual / |measured|)
    mean_ratio: float = 1.0        # mean(measured / predicted)
    std_residual: float = 0.0
    bias_direction: str = "none"   # 'high', 'low', 'none'
    bias_magnitude: float = 0.0    # |mean_relative_residual|
    recommended_correction: float = 1.0  # multiplicative factor for next pred
    outlier_config_ids: List[str] = field(default_factory=list)


@dataclass
class ResidualAnalysisReport:
    """The output of ResidualAnalyzer.analyze()."""
    n_residuals: int = 0
    n_metrics: int = 0
    overall_bias: float = 0.0
    overall_relative_bias: float = 0.0
    per_metric: Dict[str, BiasReport] = field(default_factory=dict)
    most_biased_metric: Optional[str] = None
    has_systematic_bias: bool = False
    recommendations: List[str] = field(default_factory=list)
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "n_residuals": self.n_residuals,
            "n_metrics": self.n_metrics,
            "overall_bias": self.overall_bias,
            "overall_relative_bias": self.overall_relative_bias,
            "per_metric": {k: v.__dict__ for k, v in self.per_metric.items()},
            "most_biased_metric": self.most_biased_metric,
            "has_systematic_bias": self.has_systematic_bias,
            "recommendations": self.recommendations,
            "timestamp": self.timestamp,
        }


class ResidualAnalyzer:
    """DR-78: analyze prediction-vs-measurement residuals."""

    def __init__(self, outlier_threshold: float = 3.0,
                 bias_threshold: float = 0.05):
        """Args:
            outlier_threshold: |relative_residual| above this is an outlier
            bias_threshold: |mean_relative_residual| above this is systematic
        """
        self.outlier_threshold = outlier_threshold
        self.bias_threshold = bias_threshold

    # ----- public API ---------------------------------------------------
    def analyze(self, residuals: List[Any]) -> ResidualAnalysisReport:
        """Analyze a list of residuals.

        Each residual is expected to have:
          - metric: str
          - predicted: float
          - measured: float
          - residual: float (predicted - measured)
          - relative_residual: float (residual / |measured|)
          - config_id: str (optional)

        The scripts.measurement_engine.Residual dataclass satisfies this.
        """
        # Group by metric
        by_metric: Dict[str, List[Any]] = {}
        for r in residuals:
            by_metric.setdefault(r.metric, []).append(r)

        per_metric: Dict[str, BiasReport] = {}
        all_relative = []
        recommendations: List[str] = []
        for metric, group in by_metric.items():
            br = self._analyze_one_metric(metric, group)
            per_metric[metric] = br
            all_relative.extend(r.relative_residual for r in group)
            if br.bias_magnitude > self.bias_threshold:
                recommendations.append(
                    f"Metric '{metric}' shows {br.bias_direction} bias "
                    f"of {br.bias_magnitude*100:.2f}%. Apply correction "
                    f"factor {br.recommended_correction:.4f} to future "
                    f"predictions.")

        overall_relative = (sum(all_relative) / len(all_relative)
                            if all_relative else 0.0)
        overall_bias = (sum(r.residual for r in residuals) / len(residuals)
                        if residuals else 0.0)

        # Find most-biased metric
        most_biased = None
        if per_metric:
            most_biased = max(per_metric.values(),
                              key=lambda b: b.bias_magnitude).metric

        has_systematic = any(
            b.bias_magnitude > self.bias_threshold for b in per_metric.values())

        return ResidualAnalysisReport(
            n_residuals=len(residuals),
            n_metrics=len(per_metric),
            overall_bias=overall_bias,
            overall_relative_bias=overall_relative,
            per_metric=per_metric,
            most_biased_metric=most_biased,
            has_systematic_bias=has_systematic,
            recommendations=recommendations,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    # ----- internals ----------------------------------------------------
    def _analyze_one_metric(self, metric: str,
                            group: List[Any]) -> BiasReport:
        n = len(group)
        mean_resid = sum(r.residual for r in group) / n
        mean_rel = sum(r.relative_residual for r in group) / n
        # mean ratio = mean(measured / predicted)
        ratios = [r.measured / r.predicted for r in group
                  if r.predicted != 0]
        mean_ratio = sum(ratios) / len(ratios) if ratios else 1.0
        # Std of residuals
        if n >= 2:
            var = sum((r.residual - mean_resid) ** 2 for r in group) / n
            std = math.sqrt(var)
        else:
            std = 0.0
        # Direction
        if mean_rel > self.bias_threshold:
            direction = "high"  # prediction > measurement
        elif mean_rel < -self.bias_threshold:
            direction = "low"
        else:
            direction = "none"
        # Outliers
        outliers = [r.config_id for r in group
                    if abs(r.relative_residual) > self.outlier_threshold]
        # Recommended correction: multiplicative factor for the next pred
        # If predictions are systematically HIGH (mean_rel > 0), the
        # correction factor should be < 1 (multiply future predictions
        # by mean_ratio = measured/predicted).
        if mean_ratio > 0:
            correction = max(0.5, min(1.5, mean_ratio))
        else:
            correction = 1.0

        return BiasReport(
            metric=metric,
            n_samples=n,
            mean_residual=mean_resid,
            mean_relative_residual=mean_rel,
            mean_ratio=mean_ratio,
            std_residual=std,
            bias_direction=direction,
            bias_magnitude=abs(mean_rel),
            recommended_correction=correction,
            outlier_config_ids=outliers,
        )


def main():
    print("=" * 60)
    print("RESIDUAL ANALYSIS (DR-78)")
    print("=" * 60)
    print()

    from scripts.measurement_engine import Residual

    # Synthetic residuals: prediction consistently 10% high on ZT
    residuals = [
        Residual(config_id=f"C{i}", config_hash=f"h{i}", metric="ZT",
                 predicted=1.10 + i * 0.01,
                 measured=1.00 + i * 0.01,
                 residual=0.10,
                 relative_residual=0.10 / 1.00,
                 significant=True)
        for i in range(5)
    ]
    # Add V_oc residuals that are unbiased
    residuals.extend([
        Residual(config_id=f"C{i}", config_hash=f"h{i}", metric="V_oc_V",
                 predicted=0.020 + i * 0.001,
                 measured=0.020 + i * 0.001,
                 residual=0.0,
                 relative_residual=0.0,
                 significant=False)
        for i in range(5)
    ])

    analyzer = ResidualAnalyzer()
    report = analyzer.analyze(residuals)
    print(f"n_residuals: {report.n_residuals}")
    print(f"n_metrics: {report.n_metrics}")
    print(f"overall_bias: {report.overall_bias:.4f}")
    print(f"has_systematic_bias: {report.has_systematic_bias}")
    print(f"most_biased_metric: {report.most_biased_metric}")
    for metric, br in report.per_metric.items():
        print(f"  {metric}: bias={br.bias_direction} "
              f"mag={br.bias_magnitude:.4f} correction={br.recommended_correction:.4f}")
    print()
    print("Recommendations:")
    for r in report.recommendations:
        print(f"  - {r}")


if __name__ == "__main__":
    main()
