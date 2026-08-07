#!/usr/bin/env python3
"""
failure_engine.py — DR-75: The orchestrator that runs ALL failure detectors.

Has veto authority over every stage (per Constitutional Rule 8: "No
'verified' label without a successful prediction, a failed prediction,
and replayable evidence").

The engine runs:
  1. SelfValidationDetector (DR-75.2)
  2. CircularGoldChecker (DR-75.3)
  3. ForwardModelChecker (DR-75.4)

Returns PASS / FAIL / VETO:
  - PASS: all detectors pass
  - FAIL: at least one detector warns but none vetoes
  - VETO: at least one detector fails (severity='fail')

A VETO blocks the candidate from being labeled "verified."

Usage:
    from scripts.failure_engine import FailureEngine
    engine = FailureEngine()
    result = engine.run(prediction, measurement, input_text, gold_text,
                        forward_model, sample_configs)
    # result.status == "PASS" | "FAIL" | "VETO"
"""
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.self_validation_detector import (
    SelfValidationDetector, SelfValidationReport,
)
from scripts.circular_gold_checker import (
    CircularGoldChecker, ContaminationReport,
)
from scripts.forward_model_checker import (
    ForwardModelChecker, ForwardModelCheckReport,
)


@dataclass
class FailureEngineResult:
    """The output of FailureEngine.run()."""
    status: str = "PASS"   # 'PASS', 'FAIL', 'VETO'
    self_validation: Optional[SelfValidationReport] = None
    gold_contamination: Optional[ContaminationReport] = None
    forward_model_check: Optional[ForwardModelCheckReport] = None
    n_detectors_run: int = 0
    n_passed: int = 0
    n_warned: int = 0
    n_failed: int = 0
    reasons: List[str] = field(default_factory=list)
    timestamp: str = ""
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "self_validation": (self.self_validation.to_dict()
                                if self.self_validation else None),
            "gold_contamination": (self.gold_contamination.to_dict()
                                   if self.gold_contamination else None),
            "forward_model_check": (self.forward_model_check.to_dict()
                                    if self.forward_model_check else None),
            "n_detectors_run": self.n_detectors_run,
            "n_passed": self.n_passed,
            "n_warned": self.n_warned,
            "n_failed": self.n_failed,
            "reasons": self.reasons,
            "timestamp": self.timestamp,
            "provenance": self.provenance,
        }


class FailureEngine:
    """DR-75: orchestrator with veto authority."""

    def __init__(self,
                 self_validation_detector: Optional[SelfValidationDetector] = None,
                 gold_checker: Optional[CircularGoldChecker] = None,
                 forward_model_checker: Optional[ForwardModelChecker] = None,
                 physical_plausibility_checker: Optional[Any] = None):
        self.detectors = {
            "self_validation": self_validation_detector or SelfValidationDetector(),
            "gold_contamination": gold_checker or CircularGoldChecker(),
            "forward_model_check": forward_model_checker or ForwardModelChecker(),
        }
        # F-100: physical plausibility checker with VETO authority
        if physical_plausibility_checker is not None:
            self.detectors["physical_plausibility"] = physical_plausibility_checker
        else:
            try:
                from scripts.physical_plausibility import PhysicalPlausibilityChecker
                self.detectors["physical_plausibility"] = PhysicalPlausibilityChecker()
            except ImportError:
                pass

    # ----- public API ---------------------------------------------------
    def run(self,
            prediction: Optional[Any] = None,
            measurement: Optional[Any] = None,
            input_text: Optional[str] = None,
            gold_text: Optional[str] = None,
            forward_model: Optional[Any] = None,
            sample_configs: Optional[List[Any]] = None,
            metric: str = "ZT") -> FailureEngineResult:
        """Run all failure detectors.

        Each detector is OPTIONAL — if its inputs are missing, it's
        skipped (with a note in the result). A detector that runs and
        returns severity='fail' triggers a VETO.
        """
        reports: Dict[str, Any] = {}
        reasons: List[str] = []
        n_passed = 0
        n_warned = 0
        n_failed = 0
        n_run = 0

        # 1. Self-validation detector
        if prediction is not None and measurement is not None:
            sv = self.detectors["self_validation"].check(prediction, measurement)
            reports["self_validation"] = sv
            n_run += 1
            if sv.severity == "pass":
                n_passed += 1
            elif sv.severity == "warn":
                n_warned += 1
                reasons.append(f"self_validation WARN: {sv.reasons}")
            else:  # fail
                n_failed += 1
                reasons.append(f"self_validation VETO: {sv.reasons}")
        else:
            reasons.append("self_validation: skipped (prediction or "
                           "measurement missing)")

        # 2. Gold contamination checker
        if input_text is not None and gold_text is not None:
            gc = self.detectors["gold_contamination"].check(input_text, gold_text)
            reports["gold_contamination"] = gc
            n_run += 1
            if gc.is_contaminated:
                n_failed += 1
                reasons.append(f"gold_contamination VETO: {gc.n_hits} "
                               f"bridge phrases found: "
                               f"{gc.bridge_phrases_found[:3]}")
            else:
                n_passed += 1
        else:
            reasons.append("gold_contamination: skipped (input_text or "
                           "gold_text missing)")

        # 3. Forward model checker
        if forward_model is not None and sample_configs:
            fmc = self.detectors["forward_model_check"].check(
                forward_model, sample_configs, metric=metric)
            reports["forward_model_check"] = fmc
            n_run += 1
            if fmc.severity == "pass":
                n_passed += 1
            elif fmc.severity == "warn":
                n_warned += 1
                reasons.append(f"forward_model_check WARN: {fmc.reasons}")
            else:
                n_failed += 1
                reasons.append(f"forward_model_check VETO: {fmc.reasons}")
        else:
            reasons.append("forward_model_check: skipped (forward_model "
                           "or sample_configs missing)")

        # 4. F-100: Physical plausibility checker
        plaus_checker = self.detectors.get("physical_plausibility")
        if plaus_checker is not None and prediction is not None:
            # Extract predicted properties from the prediction object
            pred_props = {}
            if hasattr(prediction, 'predicted_properties'):
                pred_props = prediction.predicted_properties
            elif isinstance(prediction, dict):
                pred_props = prediction

            if pred_props:
                plaus_result = plaus_checker.check_prediction(pred_props)
                reports["physical_plausibility"] = plaus_result
                n_run += 1
                if plaus_result.vetoed:
                    n_failed += 1
                    violation_strs = [f"{v.parameter}={v.value} [{v.min_allowed},{v.max_allowed}]"
                                      for v in plaus_result.violations if v.severity == "veto"]
                    reasons.append(f"physical_plausibility VETO: {violation_strs}")
                elif plaus_result.n_warnings > 0:
                    n_warned += 1
                    reasons.append(f"physical_plausibility WARN: {plaus_result.n_warnings} warnings")
                else:
                    n_passed += 1

        # Determine overall status
        if n_failed > 0:
            status = "VETO"
        elif n_warned > 0:
            status = "FAIL"
        else:
            status = "PASS"

        return FailureEngineResult(
            status=status,
            self_validation=reports.get("self_validation"),
            gold_contamination=reports.get("gold_contamination"),
            forward_model_check=reports.get("forward_model_check"),
            n_detectors_run=n_run,
            n_passed=n_passed,
            n_warned=n_warned,
            n_failed=n_failed,
            reasons=reasons,
            timestamp=datetime.now(timezone.utc).isoformat(),
            provenance={
                "engine": "FailureEngine",
                "veto_authority": "Constitutional Rule 8",
                "detectors": list(self.detectors.keys()),
            },
        )

    def veto(self, result: FailureEngineResult) -> bool:
        """Convenience: did this result trigger a veto?"""
        return result.status == "VETO"


def main():
    print("=" * 60)
    print("FAILURE ENGINE (DR-75)")
    print("=" * 60)
    print()

    from scripts.forward_model import ForwardModel, Prediction
    from scripts.measurement_engine import Measurement
    from scripts.artifact_generator import (
        Configuration, Component, MATERIAL_PARAMS,
    )

    fm = ForwardModel()
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
    pred = fm.predict(configs[1])

    # Independent measurement
    meas = Measurement(
        config_id=configs[1].config_id,
        config_hash=configs[1].config_hash,
        domain="thermoelectric",
        measured_properties={
            "ZT": pred.predicted_properties["ZT"] * 0.85,
            "V_oc_V": pred.predicted_properties["V_oc_V"] * 0.92,
        },
        corrections_applied={"contact_resistance_ohm": 5e-3},
        provenance={"method": "high-fidelity with contact resistance",
                    "corrections": ["contact_resistance_ohm: 5 mΩ"]},
    )

    engine = FailureEngine(forward_model_checker=ForwardModelChecker(
        kb_values={"ZT": 0.93}))
    result = engine.run(
        prediction=pred, measurement=meas,
        input_text="improve thermoelectric efficiency of bismuth telluride",
        gold_text="The reference contains Seebeck, conductivity, and "
                  "thermal data for various lead alloys.",
        forward_model=fm, sample_configs=configs, metric="ZT")
    print(f"Status: {result.status}")
    print(f"Detectors run: {result.n_detectors_run}")
    print(f"Passed: {result.n_passed}, Warned: {result.n_warned}, "
          f"Failed: {result.n_failed}")
    print(f"Reasons:")
    for r in result.reasons:
        print(f"  - {r}")


if __name__ == "__main__":
    main()
