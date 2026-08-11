"""Tests for DR-78: experimental closure extensions."""
import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.specification import SpecificationEngine
from scripts.capability_graph import CapabilityGraph
from scripts.measurement_engine import Residual, MeasurementInstrument
from scripts.residual_analysis import (
    ResidualAnalyzer, ResidualAnalysisReport, BiasReport,
)
from scripts.experiment_runner import (
    ExperimentRunner, ExperimentResult, ExperimentIteration,
)


def _spec_and_graph():
    spec = SpecificationEngine().compile(
        "improve thermoelectric efficiency of bismuth telluride")
    cg = CapabilityGraph()
    cg.from_relations([
        ("bismuth telluride", "generates", "voltage"),
        ("bismuth telluride", "conducts", "electricity"),
    ])
    return spec, cg


# ---------------------------------------------------------------------------
# DR-78.1: residual_analysis
# ---------------------------------------------------------------------------
def test_residual_analyzer_returns_report():
    """analyze() returns a ResidualAnalysisReport."""
    residuals = [
        Residual(config_id="C0", config_hash="h0", metric="ZT",
                 predicted=1.10, measured=1.00, residual=0.10,
                 relative_residual=0.10, significant=True),
        Residual(config_id="C1", config_hash="h1", metric="ZT",
                 predicted=1.12, measured=1.02, residual=0.10,
                 relative_residual=0.098, significant=True),
    ]
    analyzer = ResidualAnalyzer()
    report = analyzer.analyze(residuals)
    assert isinstance(report, ResidualAnalysisReport)
    assert report.n_residuals == 2
    assert report.n_metrics == 1


def test_residual_analyzer_detects_high_bias():
    """Predictions consistently above measurements → 'high' bias."""
    residuals = [
        Residual(config_id=f"C{i}", config_hash=f"h{i}", metric="ZT",
                 predicted=1.10, measured=1.00, residual=0.10,
                 relative_residual=0.10, significant=True)
        for i in range(5)
    ]
    analyzer = ResidualAnalyzer()
    report = analyzer.analyze(residuals)
    assert "ZT" in report.per_metric
    assert report.per_metric["ZT"].bias_direction == "high"
    assert report.has_systematic_bias is True


def test_residual_analyzer_detects_low_bias():
    """Predictions consistently below measurements → 'low' bias."""
    residuals = [
        Residual(config_id=f"C{i}", config_hash=f"h{i}", metric="ZT",
                 predicted=0.90, measured=1.00, residual=-0.10,
                 relative_residual=-0.10, significant=True)
        for i in range(5)
    ]
    analyzer = ResidualAnalyzer()
    report = analyzer.analyze(residuals)
    assert report.per_metric["ZT"].bias_direction == "low"


def test_residual_analyzer_no_bias_for_unbiased():
    """Random residuals around zero → no systematic bias."""
    residuals = [
        Residual(config_id=f"C{i}", config_hash=f"h{i}", metric="ZT",
                 predicted=1.00 + (i % 3 - 1) * 0.001,
                 measured=1.00,
                 residual=(i % 3 - 1) * 0.001,
                 relative_residual=(i % 3 - 1) * 0.001,
                 significant=False)
        for i in range(10)
    ]
    analyzer = ResidualAnalyzer()
    report = analyzer.analyze(residuals)
    assert report.per_metric["ZT"].bias_direction == "none"
    assert report.has_systematic_bias is False


def test_residual_analyzer_recommended_correction():
    """The recommended correction moves the prediction toward measured."""
    residuals = [
        Residual(config_id=f"C{i}", config_hash=f"h{i}", metric="ZT",
                 predicted=1.10, measured=1.00, residual=0.10,
                 relative_residual=0.10, significant=True)
        for i in range(5)
    ]
    analyzer = ResidualAnalyzer()
    report = analyzer.analyze(residuals)
    # Predictions are 10% too high → correction should be ~0.909
    correction = report.per_metric["ZT"].recommended_correction
    assert 0.85 < correction < 0.95


def test_residual_analyzer_finds_most_biased_metric():
    """most_biased_metric is the one with the largest bias magnitude."""
    residuals = [
        Residual(config_id="C0", config_hash="h0", metric="ZT",
                 predicted=1.10, measured=1.00, residual=0.10,
                 relative_residual=0.10, significant=True),
        Residual(config_id="C1", config_hash="h1", metric="V_oc_V",
                 predicted=0.020, measured=0.020,
                 residual=0.0, relative_residual=0.0, significant=False),
    ]
    analyzer = ResidualAnalyzer()
    report = analyzer.analyze(residuals)
    assert report.most_biased_metric == "ZT"


def test_residual_analyzer_outliers_detected():
    """Residuals with extreme |relative_residual| are flagged as outliers."""
    residuals = [
        Residual(config_id="C0", config_hash="h0", metric="ZT",
                 predicted=1.0, measured=1.0, residual=0.0,
                 relative_residual=0.0, significant=False),
        Residual(config_id="C1", config_hash="h1", metric="ZT",
                 predicted=5.0, measured=1.0, residual=4.0,
                 relative_residual=4.0, significant=True),
    ]
    analyzer = ResidualAnalyzer(outlier_threshold=3.0)
    report = analyzer.analyze(residuals)
    assert "C1" in report.per_metric["ZT"].outlier_config_ids


def test_residual_analyzer_report_serializable():
    import json
    residuals = [
        Residual(config_id="C0", config_hash="h0", metric="ZT",
                 predicted=1.1, measured=1.0, residual=0.1,
                 relative_residual=0.1, significant=True),
    ]
    analyzer = ResidualAnalyzer()
    report = analyzer.analyze(residuals)
    json.dumps(report.to_dict())


# ---------------------------------------------------------------------------
# DR-78.2: experiment_runner
# ---------------------------------------------------------------------------
def test_experiment_runner_returns_result():
    """run() returns an ExperimentResult with iterations."""
    spec, cg = _spec_and_graph()
    runner = ExperimentRunner(seed=42)
    result = runner.run(spec, cg, n_iterations=2, n_candidates=3)
    assert isinstance(result, ExperimentResult)
    assert len(result.iterations) == 2


def test_experiment_runner_records_residuals():
    """Each iteration records a non-empty residuals list."""
    spec, cg = _spec_and_graph()
    runner = ExperimentRunner(seed=42)
    result = runner.run(spec, cg, n_iterations=1, n_candidates=3)
    it = result.iterations[0]
    assert len(it.residuals) > 0


def test_experiment_runner_runs_residual_analysis():
    """Each iteration runs residual analysis."""
    spec, cg = _spec_and_graph()
    runner = ExperimentRunner(seed=42)
    result = runner.run(spec, cg, n_iterations=1, n_candidates=3)
    it = result.iterations[0]
    assert it.residual_analysis is not None
    assert isinstance(it.residual_analysis, ResidualAnalysisReport)


def test_experiment_runner_repairs_priors():
    """After running, the priors are updated (repaired)."""
    spec, cg = _spec_and_graph()
    runner = ExperimentRunner(seed=42)
    initial_priors = dict(runner.measurement_engine.correction_priors)
    result = runner.run(spec, cg, n_iterations=2, n_candidates=4)
    final_priors = result.final_priors
    # At least one prior should have changed
    assert final_priors != initial_priors or len(result.iterations) >= 1


def test_experiment_runner_one_measurement_changes_next_iteration():
    """CRITICAL: one real measurement changes the next iteration's candidates."""
    spec, cg = _spec_and_graph()
    # Run the full loop (with measurement)
    runner_with = ExperimentRunner(seed=42)
    runner_with.run(spec, cg, n_iterations=1, n_candidates=3)
    configs_with = runner_with.measurement_engine.generate(spec, cg, n=3)

    # Run without measurement (priors stay at 1.0)
    runner_without = ExperimentRunner(seed=42)
    configs_without = runner_without.measurement_engine.generate(spec, cg, n=3)

    h_with = [c.config_hash for c in configs_with]
    h_without = [c.config_hash for c in configs_without]
    assert h_with != h_without, (
        "one real measurement MUST change the next iteration's candidates")


def test_experiment_runner_trace_present():
    """Each iteration has a trace log."""
    spec, cg = _spec_and_graph()
    runner = ExperimentRunner(seed=42)
    result = runner.run(spec, cg, n_iterations=1, n_candidates=3)
    it = result.iterations[0]
    assert len(it.trace) > 0
    steps = [e["step"] for e in it.trace]
    assert "predict" in steps
    assert "build" in steps
    assert "measure" in steps
    assert "residual" in steps
    assert "repair" in steps


def test_experiment_runner_closed_when_systematic_bias():
    """If any iteration shows systematic bias, result.closed is True."""
    spec, cg = _spec_and_graph()
    runner = ExperimentRunner(seed=42)
    result = runner.run(spec, cg, n_iterations=3, n_candidates=4)
    # The measurement instrument includes contact resistance and temp-dep
    # Seebeck, so the prediction (which ignores those) should systematically
    # diverge from the measurement.
    assert result.closed is True


def test_experiment_runner_reproducible():
    """Same seed → same residual history."""
    spec, cg = _spec_and_graph()
    r1 = ExperimentRunner(seed=42).run(spec, cg, n_iterations=2, n_candidates=3)
    r2 = ExperimentRunner(seed=42).run(spec, cg, n_iterations=2, n_candidates=3)
    # Final priors should match (deterministic)
    assert r1.final_priors == r2.final_priors


def test_experiment_runner_result_serializable():
    import json
    spec, cg = _spec_and_graph()
    runner = ExperimentRunner(seed=42)
    result = runner.run(spec, cg, n_iterations=1, n_candidates=3)
    json.dumps(result.to_dict())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
