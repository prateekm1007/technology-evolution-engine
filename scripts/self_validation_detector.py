#!/usr/bin/env python3
"""
self_validation_detector.py — DR-75: Detect self-validation.

A module "validates itself" when the same formula or model is used for
both PREDICTION and MEASUREMENT (or for both the claim and the check).
This is a circularity that produces a fake "verified" stamp.

The detector inspects a (prediction, measurement) pair and the underlying
models, and flags cases where:
  - The prediction's equations_used set overlaps with the measurement's
    method/corrections in a way that suggests the same formula was used.
  - The measurement is computed FROM the prediction (e.g., measurement
    = prediction * factor with no independent physics).

Adversarial test: a measurement that is exactly the prediction (with
no independent corrections) MUST be flagged.

Usage:
    from scripts.self_validation_detector import SelfValidationDetector
    detector = SelfValidationDetector()
    report = detector.check(prediction, measurement)
    # report.is_self_validating == True/False
"""
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Set
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@dataclass
class SelfValidationReport:
    """The output of SelfValidationDetector.check()."""
    is_self_validating: bool = False
    severity: str = "pass"        # 'pass', 'warn', 'fail'
    reasons: List[str] = field(default_factory=list)
    shared_equations: List[str] = field(default_factory=list)
    measurement_independence: float = 1.0  # 1.0 = independent, 0.0 = identical
    config_id: str = ""
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_self_validating": self.is_self_validating,
            "severity": self.severity,
            "reasons": self.reasons,
            "shared_equations": self.shared_equations,
            "measurement_independence": self.measurement_independence,
            "config_id": self.config_id,
            "timestamp": self.timestamp,
        }


# Equations that count as "shared" between prediction and measurement.
# A genuinely independent measurement uses DIFFERENT physics (e.g., a
# correction term rather than the same formula).
PREDICTION_EQUATIONS = {
    "ZT = S^2 * σ * T / κ",
    "V_oc = S * ΔT",
    "R_in = L / (σ * A)",
    "P_max = V_oc^2 / (4 * R_in)",
    "Q_cond = κ * A * ΔT / L",
    "Q_rad = ε * σ_SB * A * (T_surface^4 - T_sky^4)",
    "C = ε_0 * ε_r * A / d",
    "E = 0.5 * C * V^2",
    "P = V^2 / (4 * ESR)",
    "R = L / (σ * A)",
    "V = I * R",
    "P = V * I",
}


class SelfValidationDetector:
    """DR-75: detect when a module validates itself."""

    def __init__(self, independence_threshold: float = 0.05):
        """Args:
            independence_threshold: if the measurement differs from the
                prediction by less than this fraction (averaged across
                metrics), it's flagged as self-validating.
        """
        self.independence_threshold = independence_threshold

    # ----- public API ---------------------------------------------------
    def check(self, prediction, measurement) -> SelfValidationReport:
        """Check whether the measurement is independent of the prediction.

        Args:
            prediction: a Prediction (from scripts.forward_model)
            measurement: a Measurement (from scripts.measurement_engine)

        Returns:
            SelfValidationReport with is_self_validating flag
        """
        reasons: List[str] = []
        shared: List[str] = []

        # 1. Equation overlap check
        pred_eqs = set(getattr(prediction, "equations_used", []) or [])
        meas_provenance = getattr(measurement, "provenance", {}) or {}
        meas_method = str(meas_provenance.get("method", "")).lower()
        meas_corrections = meas_provenance.get("corrections", []) or []
        # Normalize an equation for matching: lowercase, strip '*' and
        # extra whitespace so "ZT = S^2 * σ * T / κ" matches
        # "zt = s^2 σ t / κ".
        def _norm(s: str) -> str:
            return " ".join(s.lower().replace("*", " ").split())
        meas_method_norm = _norm(meas_method)
        # If any prediction equation appears (normalized) in the measurement
        # method/corrections, that's a red flag.
        for eq in pred_eqs:
            eq_norm = _norm(eq)
            if eq_norm and eq_norm in meas_method_norm:
                shared.append(eq)
        if shared:
            reasons.append(
                f"Measurement method cites prediction equations: {shared}")

        # 2. Numeric independence check: are the measured values
        # essentially identical to the predicted values (after rounding)?
        pred_props = getattr(prediction, "predicted_properties", {}) or {}
        meas_props = getattr(measurement, "measured_properties", {}) or {}
        common_keys = set(pred_props) & set(meas_props)
        if common_keys:
            rel_diffs = []
            for k in common_keys:
                p = pred_props[k]
                m = meas_props[k]
                if isinstance(p, (int, float)) and isinstance(m, (int, float)):
                    if abs(p) > 1e-15:
                        rel = abs(m - p) / abs(p)
                        rel_diffs.append(rel)
                    elif abs(m) > 1e-15:
                        rel_diffs.append(abs(m - p) / abs(m))
                    else:
                        rel_diffs.append(0.0)  # both zero → identical
            if rel_diffs:
                mean_rel_diff = sum(rel_diffs) / len(rel_diffs)
                independence = mean_rel_diff
                if mean_rel_diff < self.independence_threshold:
                    reasons.append(
                        f"Measurement differs from prediction by only "
                        f"{mean_rel_diff*100:.3f}% on average — likely "
                        f"self-validation (same formula).")
            else:
                independence = 1.0
        else:
            independence = 1.0

        # 3. Corrections presence check: an independent measurement
        # should list explicit corrections (contact resistance, etc.)
        if not meas_corrections and not meas_method:
            reasons.append("Measurement has no corrections and no method "
                           "description — cannot establish independence.")

        # Determine severity
        is_self = bool(reasons)
        if any("self-validation" in r for r in reasons) or shared:
            severity = "fail"
        elif reasons:
            severity = "warn"
        else:
            severity = "pass"

        return SelfValidationReport(
            is_self_validating=is_self,
            severity=severity,
            reasons=reasons,
            shared_equations=shared,
            measurement_independence=round(independence, 6),
            config_id=getattr(prediction, "config_id", ""),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


def main():
    print("=" * 60)
    print("SELF-VALIDATION DETECTOR (DR-75)")
    print("=" * 60)
    print()

    from scripts.forward_model import ForwardModel, Prediction
    from scripts.measurement_engine import Measurement
    from scripts.artifact_generator import (
        Configuration, Component, MATERIAL_PARAMS,
    )
    fm = ForwardModel()
    config = Configuration(
        config_id="DEMO", spec_objective="x", domain="thermoelectric",
        components=[Component(material="bismuth_telluride", role="active",
                              parameters=dict(MATERIAL_PARAMS["bismuth_telluride"]))],
        structure="monolithic",
        parameters={"thickness_m": 1e-3, "area_m2": 1e-4,
                    "T_hot_K": 400.0, "T_cold_K": 300.0},
        design_operator_chain=["init"],
    )
    config.config_hash = config.compute_hash()
    pred = fm.predict(config)

    # Case 1: independent measurement (with corrections)
    meas_independent = Measurement(
        config_id="DEMO", config_hash=config.config_hash,
        domain="thermoelectric",
        measured_properties={
            "ZT": pred.predicted_properties["ZT"] * 0.85,
            "V_oc_V": pred.predicted_properties["V_oc_V"] * 0.92,
        },
        corrections_applied={"contact_resistance_ohm": 5e-3},
        provenance={"method": "high-fidelity with contact resistance",
                    "corrections": ["contact_resistance_ohm: 5 mΩ"]},
    )
    # Case 2: self-validating measurement (identical to prediction)
    meas_self = Measurement(
        config_id="DEMO", config_hash=config.config_hash,
        domain="thermoelectric",
        measured_properties=dict(pred.predicted_properties),
        corrections_applied={},
        provenance={"method": "uses ZT = S^2 σ T / κ formula",
                    "corrections": []},
    )

    detector = SelfValidationDetector()
    r1 = detector.check(pred, meas_independent)
    r2 = detector.check(pred, meas_self)

    print("Independent measurement:")
    print(f"  self_validating={r1.is_self_validating} severity={r1.severity}")
    print(f"  independence={r1.measurement_independence}")
    print()
    print("Self-validating measurement (identical):")
    print(f"  self_validating={r2.is_self_validating} severity={r2.severity}")
    print(f"  independence={r2.measurement_independence}")
    print(f"  reasons: {r2.reasons}")


if __name__ == "__main__":
    main()
