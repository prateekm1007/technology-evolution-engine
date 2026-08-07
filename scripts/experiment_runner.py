#!/usr/bin/env python3
"""
experiment_runner.py — DR-78: Orchestrates the full experimental loop.

Loop:
  1. PREDICT: forward_model.predict(config) → Prediction
  2. BUILD: prototype_compiler.compile(config) → Prototype
  3. MEASURE: measurement_instrument.measure(config) → Measurement
  4. RESIDUAL: residual = predicted - measured for each metric
  5. REPAIR: based on residual analysis, update correction priors
             so the next candidate is shifted

This is the DR-78 wrapper around the existing measurement_engine
(Stage VII) plus the new residual_analysis module (DR-78). The runner
adds:
  - Explicit per-step provenance
  - A residual-analysis pass at the end of each iteration
  - A repair step that updates priors using the recommended corrections
  - A complete trace log

Usage:
    from scripts.experiment_runner import ExperimentRunner
    runner = ExperimentRunner(seed=42)
    result = runner.run(spec, capability_graph,
                        n_iterations=3, n_candidates=4)
    # result.iterations[i].residual_analysis = ResidualAnalysisReport
"""
import sys
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.artifact_generator import ArtifactGenerator, Configuration
from scripts.forward_model import ForwardModel, Prediction
from scripts.prototype_compiler import PrototypeCompiler, Prototype
from scripts.measurement_engine import (
    MeasurementEngine, MeasurementInstrument, Measurement, Residual,
    IterationResult,
)
from scripts.residual_analysis import (
    ResidualAnalyzer, ResidualAnalysisReport,
)


@dataclass
class ExperimentIteration:
    """The result of one iteration of the experimental loop."""
    iteration: int
    generated_configs: List[Configuration] = field(default_factory=list)
    predictions: List[Prediction] = field(default_factory=list)
    prototypes: List[Prototype] = field(default_factory=list)
    measurements: List[Measurement] = field(default_factory=list)
    residuals: List[Residual] = field(default_factory=list)
    residual_analysis: Optional[ResidualAnalysisReport] = None
    correction_priors_before: Dict[str, float] = field(default_factory=dict)
    correction_priors_after: Dict[str, float] = field(default_factory=dict)
    n_manufacturing_pass: int = 0
    n_measured: int = 0
    trace: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: str = ""


@dataclass
class ExperimentResult:
    """The output of ExperimentRunner.run()."""
    iterations: List[ExperimentIteration] = field(default_factory=list)
    final_priors: Dict[str, float] = field(default_factory=dict)
    closed: bool = False         # True if the loop produced a measurable repair
    residual_history: List[float] = field(default_factory=list)
    n_total_generated: int = 0
    n_total_measured: int = 0
    seed: int = 0
    n_iterations: int = 0
    n_candidates: int = 0
    timestamp: str = ""
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "n_iterations": len(self.iterations),
            "n_total_generated": self.n_total_generated,
            "n_total_measured": self.n_total_measured,
            "final_priors": self.final_priors,
            "closed": self.closed,
            "residual_history": self.residual_history,
            "seed": self.seed,
            "timestamp": self.timestamp,
            "provenance": self.provenance,
        }


class ExperimentRunner:
    """DR-78: orchestrates the predict → build → measure → residual → repair loop."""

    def __init__(self, seed: int = 42,
                 forward_model: Optional[ForwardModel] = None,
                 compiler: Optional[PrototypeCompiler] = None,
                 instrument: Optional[MeasurementInstrument] = None,
                 measurement_engine: Optional[MeasurementEngine] = None,
                 residual_analyzer: Optional[ResidualAnalyzer] = None):
        self.seed = seed
        self.forward_model = forward_model or ForwardModel()
        self.compiler = compiler or PrototypeCompiler(forward_model=self.forward_model)
        self.instrument = instrument or MeasurementInstrument()
        self.measurement_engine = measurement_engine or MeasurementEngine(
            seed=seed, forward_model=self.forward_model,
            compiler=self.compiler, instrument=self.instrument)
        self.residual_analyzer = residual_analyzer or ResidualAnalyzer()
        self._trace: List[Dict[str, Any]] = []

    # ----- public API ---------------------------------------------------
    def run(self, spec, capability_graph,
            n_iterations: int = 3, n_candidates: int = 4) -> ExperimentResult:
        """Run the full predict→build→measure→residual→repair loop."""
        iterations: List[ExperimentIteration] = []
        residual_history: List[float] = []
        closed = False

        for i in range(n_iterations):
            iter_result = self._run_one_iteration(
                spec, capability_graph, n_candidates, i)
            iterations.append(iter_result)
            if iter_result.residual_analysis:
                # Track the mean |relative_residual| across all metrics
                mean_abs_rel = sum(
                    abs(b.mean_relative_residual)
                    for b in iter_result.residual_analysis.per_metric.values()
                ) / max(1, len(iter_result.residual_analysis.per_metric))
                residual_history.append(mean_abs_rel)
                if iter_result.residual_analysis.has_systematic_bias:
                    closed = True

        return ExperimentResult(
            iterations=iterations,
            final_priors=dict(self.measurement_engine.correction_priors),
            closed=closed,
            residual_history=residual_history,
            n_total_generated=sum(len(it.generated_configs) for it in iterations),
            n_total_measured=sum(it.n_measured for it in iterations),
            seed=self.seed,
            n_iterations=n_iterations,
            n_candidates=n_candidates,
            timestamp=datetime.now(timezone.utc).isoformat(),
            provenance={
                "engine": "ExperimentRunner",
                "stage": "DR-78",
                "loop": "predict → build → measure → residual → repair",
            },
        )

    # ----- internals ----------------------------------------------------
    def _run_one_iteration(self, spec, capability_graph, n: int,
                           iteration: int) -> ExperimentIteration:
        trace: List[Dict[str, Any]] = []
        priors_before = dict(self.measurement_engine.correction_priors)
        trace.append({"step": "priors_before", "priors": dict(priors_before)})

        # 1. PREDICT (generate + predict)
        configs = self.measurement_engine.generate(spec, capability_graph, n=n)
        predictions = [self.forward_model.predict(c) for c in configs]
        trace.append({"step": "predict",
                      "n_configs": len(configs),
                      "n_predictions": len(predictions)})

        # 2. BUILD (compile prototypes; skip if manufacturing fails)
        prototypes: List[Prototype] = []
        buildable: List[tuple] = []
        for c, p in zip(configs, predictions):
            proto = self.compiler.compile(c, prediction=p)
            if proto.manufacturing_pass:
                prototypes.append(proto)
                buildable.append((c, p))
        trace.append({"step": "build",
                      "n_manufacturing_pass": len(prototypes),
                      "n_total": len(configs)})

        # 3. MEASURE
        measurements = [self.instrument.measure(c) for c, _ in buildable]
        trace.append({"step": "measure", "n_measured": len(measurements)})

        # 4. RESIDUAL
        residuals = self._compute_residuals(
            [p for _, p in buildable], measurements)
        trace.append({"step": "residual", "n_residuals": len(residuals)})

        # 5. RESIDUAL ANALYSIS (DR-78)
        analysis = self.residual_analyzer.analyze(residuals) if residuals else None
        if analysis:
            trace.append({"step": "residual_analysis",
                          "has_systematic_bias": analysis.has_systematic_bias,
                          "most_biased_metric": analysis.most_biased_metric,
                          "n_recommendations": len(analysis.recommendations)})

        # 6. REPAIR: update priors based on analysis
        if analysis:
            self._apply_recommended_corrections(analysis)
        trace.append({"step": "repair",
                      "priors_after": dict(self.measurement_engine.correction_priors)})

        return ExperimentIteration(
            iteration=iteration,
            generated_configs=configs,
            predictions=predictions,
            prototypes=prototypes,
            measurements=measurements,
            residuals=residuals,
            residual_analysis=analysis,
            correction_priors_before=priors_before,
            correction_priors_after=dict(self.measurement_engine.correction_priors),
            n_manufacturing_pass=len(prototypes),
            n_measured=len(measurements),
            trace=trace,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def _compute_residuals(self, predictions: List[Prediction],
                           measurements: List[Measurement]) -> List[Residual]:
        """Compute residuals for each (prediction, measurement) pair."""
        residuals: List[Residual] = []
        for pred, meas in zip(predictions, measurements):
            for metric, pred_val in pred.predicted_properties.items():
                if metric in meas.measured_properties:
                    meas_val = meas.measured_properties[metric]
                    if isinstance(pred_val, (int, float)) and isinstance(meas_val, (int, float)):
                        res = pred_val - meas_val
                        rel = res / abs(meas_val) if abs(meas_val) > 1e-12 else 0.0
                        residuals.append(Residual(
                            config_id=pred.config_id,
                            config_hash=pred.config_hash,
                            metric=metric,
                            predicted=pred_val,
                            measured=meas_val,
                            residual=res,
                            relative_residual=rel,
                            significant=abs(rel) > 0.05,
                        ))
        return residuals

    def _apply_recommended_corrections(self, analysis: ResidualAnalysisReport) -> None:
        """Apply the residual analyzer's recommended corrections to priors.

        The analyzer recommends a multiplicative correction per metric.
        We map metric → parameter (e.g., ZT → seebeck_coefficient) and
        update the prior.
        """
        # Map metric → parameter
        metric_to_param = {
            "V_oc_V": "seebeck_coefficient",
            "ZT": "seebeck_coefficient",
            "Q_cond_W": "thermal_conductivity",
            "Q_rad_W": "emissivity",
        }
        for metric, br in analysis.per_metric.items():
            param = metric_to_param.get(metric)
            if param is None:
                continue
            old = self.measurement_engine.correction_priors.get(param, 1.0)
            # Smooth update: 50% old, 50% new (damped)
            new = 0.5 * old + 0.5 * (old * br.recommended_correction)
            new = max(0.5, min(1.5, new))
            self.measurement_engine.correction_priors[param] = round(new, 6)


def main():
    print("=" * 60)
    print("EXPERIMENT RUNNER (DR-78)")
    print("=" * 60)
    print()

    from scripts.specification import SpecificationEngine
    from scripts.capability_graph import CapabilityGraph

    spec = SpecificationEngine().compile(
        "improve thermoelectric efficiency of bismuth telluride")
    cg = CapabilityGraph()
    cg.from_relations([
        ("bismuth telluride", "generates", "voltage"),
        ("bismuth telluride", "conducts", "electricity"),
    ])

    runner = ExperimentRunner(seed=42)
    result = runner.run(spec, cg, n_iterations=3, n_candidates=4)

    print(f"Iterations: {len(result.iterations)}")
    print(f"Total generated: {result.n_total_generated}")
    print(f"Total measured: {result.n_total_measured}")
    print(f"Closed: {result.closed}")
    print(f"Residual history: {[round(r, 4) for r in result.residual_history]}")
    print(f"Final priors: {result.final_priors}")
    print()

    for it in result.iterations:
        print(f"--- Iteration {it.iteration} ---")
        print(f"  Generated: {len(it.generated_configs)}")
        print(f"  Manufacturing pass: {it.n_manufacturing_pass}")
        print(f"  Measured: {it.n_measured}")
        print(f"  Priors before: {it.correction_priors_before}")
        print(f"  Priors after: {it.correction_priors_after}")
        if it.residual_analysis:
            print(f"  Systematic bias: "
                  f"{it.residual_analysis.has_systematic_bias}")
            print(f"  Most biased: "
                  f"{it.residual_analysis.most_biased_metric}")
            for metric, br in it.residual_analysis.per_metric.items():
                print(f"    {metric}: bias={br.bias_direction} "
                      f"mag={br.bias_magnitude:.4f} "
                      f"correction={br.recommended_correction:.4f}")
        print()


if __name__ == "__main__":
    main()
