#!/usr/bin/env python3
"""
forward_model.py — Stage IV: Predict candidate behavior from physics.

For each candidate Configuration, predict its physical behavior using
known physical laws (Stefan-Boltzmann, Ohm's law, Seebeck effect,
thermoelectric figure of merit ZT, supercapacitor energy/power). The
model:

  1. Computes a nominal prediction from the configuration's parameters.
  2. Estimates an uncertainty bound on each prediction (linearized
     propagation of input uncertainties through the formula, plus a
     structural model error term).
  3. Records the equations used, the assumptions made, and the
     evidence rank (rank A — physics).
  4. Produces DIFFERENT predictions when candidate parameters change.

This is NOT a score or a perturbation. It is the actual physics
formula evaluated on the configuration's parameters, with uncertainty
propagation.

Usage:
    from scripts.forward_model import ForwardModel
    from scripts.artifact_generator import ArtifactGenerator
    pred = ForwardModel().predict(configuration)
"""
import sys
import math
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Physical constants (CODATA / SI).
STEFAN_BOLTZMANN = 5.670374419e-8   # W/(m^2·K^4)
BOLTZMANN_K = 1.380649e-23          # J/K
ELECTRON_CHARGE = 1.602176634e-19   # C

# Default relative uncertainties (1σ) on input parameters.
# These are conservative engineering defaults; the Constitution (Law 6)
# requires the engine to expose its assumptions.
DEFAULT_REL_UNCERTAINTY = {
    "seebeck_coefficient": 0.10,         # ±10% (alloy composition, temperature)
    "electrical_conductivity": 0.20,     # ±20% (carrier density, mobility)
    "thermal_conductivity": 0.15,        # ±15% (phonon scattering)
    "thickness_m": 0.05,                 # ±5% (manufacturing tolerance)
    "area_m2": 0.05,
    "T_hot_K": 0.02,
    "T_cold_K": 0.02,
    "emissivity": 0.05,
    "porosity": 0.20,
}

# Structural model error (1σ relative) — accounts for the gap between
# the textbook formula and real behavior (contact resistance, edge
# losses, etc.). Conservative default.
STRUCTURAL_MODEL_ERROR = 0.10


@dataclass
class Prediction:
    """The output of ForwardModel.predict()."""
    config_id: str
    config_hash: str
    domain: str
    predicted_properties: Dict[str, float] = field(default_factory=dict)
    uncertainty: Dict[str, Tuple[float, float]] = field(default_factory=dict)  # (low, high) 1σ
    equations_used: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    evidence_rank: str = "A"   # physics
    timestamp: str = ""
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "config_id": self.config_id,
            "config_hash": self.config_hash,
            "domain": self.domain,
            "predicted_properties": self.predicted_properties,
            "uncertainty": {k: list(v) for k, v in self.uncertainty.items()},
            "equations_used": self.equations_used,
            "assumptions": self.assumptions,
            "evidence_rank": self.evidence_rank,
            "timestamp": self.timestamp,
            "provenance": self.provenance,
        }


class ForwardModel:
    """Stage IV: predict candidate behavior using known physical laws.

    Each domain has its own predictor. The predictor:

      - reads the configuration's component parameters and global params
      - evaluates the textbook physics formula
      - propagates uncertainty by linearization
        σ_y² ≈ Σ (∂y/∂x_i)² σ_x_i²
      - adds a structural model error term in quadrature
      - returns (nominal, (low, high)) per metric

    The model is "trusted" in the Constitution's sense: the prediction
    is the actual physics, not a learned score. Evidence rank A
    (physics and experiments).
    """

    # ----- public API ---------------------------------------------------
    def predict(self, config) -> Prediction:
        """Predict the behavior of a Configuration.

        Args:
            config: a Configuration (see scripts/artifact_generator.py)

        Returns:
            a Prediction with predicted_properties, uncertainty,
            equations_used, assumptions.
        """
        domain = (config.domain or "").lower()
        if domain == "thermoelectric":
            return self._predict_thermoelectric(config)
        elif domain == "thermal":
            return self._predict_thermal(config)
        elif domain == "supercapacitor":
            return self._predict_supercapacitor(config)
        else:
            # Fall back to a generic "electrical" prediction (Ohm's law).
            return self._predict_generic_electrical(config)

    # ----- thermoelectric ----------------------------------------------
    def _predict_thermoelectric(self, config) -> Prediction:
        """Thermoelectric prediction: ZT, V_seebeck, P_max, Q_cond.

        Equations:
          ZT = S^2 * σ * T / κ                      (figure of merit)
          V_oc = S * ΔT                              (Seebeck, open circuit)
          R_in = L / (σ * A)                         (Ohm's law, internal resistance)
          P_max = V_oc^2 / (4 * R_in)                (matched load)
          Q_cond = κ * A * ΔT / L                    (Fourier conduction)
        """
        comp = config.components[0]
        params = comp.parameters
        S = params.get("seebeck_coefficient", 0.0)         # V/K
        sigma = params.get("electrical_conductivity", 0.0) # S/m
        kappa = params.get("thermal_conductivity", 0.0)    # W/(m·K)
        L = config.parameters.get("thickness_m", 1.0e-3)   # m
        A = config.parameters.get("area_m2", 1.0e-4)       # m^2
        T_hot = config.parameters.get("T_hot_K", 400.0)    # K
        T_cold = config.parameters.get("T_cold_K", 300.0)  # K
        T_avg = 0.5 * (T_hot + T_cold)
        dT = T_hot - T_cold

        # Nominal predictions
        ZT = (S ** 2) * sigma * T_avg / kappa if kappa > 0 else 0.0
        V_oc = S * dT
        R_in = L / (sigma * A) if sigma > 0 and A > 0 else float("inf")
        P_max = (V_oc ** 2) / (4.0 * R_in) if R_in < float("inf") else 0.0
        Q_cond = kappa * A * dT / L if L > 0 else 0.0

        # Uncertainties (linearized propagation).
        # Each uncertainty is (1σ relative) — we report (low, high) = (nom - σ_abs, nom + σ_abs).
        def _rel(p): return DEFAULT_REL_UNCERTAINTY.get(p, 0.15)

        # ZT = S^2 σ T / κ → rel σ_ZT = sqrt(4 σ_S^2 + σ_σ^2 + σ_κ^2)
        rel_ZT = math.sqrt(4 * _rel("seebeck_coefficient") ** 2
                           + _rel("electrical_conductivity") ** 2
                           + _rel("thermal_conductivity") ** 2
                           + STRUCTURAL_MODEL_ERROR ** 2)
        # V_oc = S * ΔT → rel σ_V = sqrt(σ_S^2 + σ_dT^2)
        rel_V = math.sqrt(_rel("seebeck_coefficient") ** 2
                          + _rel("T_hot_K") ** 2
                          + _rel("T_cold_K") ** 2
                          + STRUCTURAL_MODEL_ERROR ** 2)
        # R_in = L/(σ A) → rel σ_R = sqrt(σ_L^2 + σ_σ^2 + σ_A^2)
        rel_R = math.sqrt(_rel("thickness_m") ** 2
                          + _rel("electrical_conductivity") ** 2
                          + _rel("area_m2") ** 2
                          + STRUCTURAL_MODEL_ERROR ** 2)
        # P_max = V^2 / (4R) → rel σ_P = sqrt(4 σ_V^2 + σ_R^2)
        rel_P = math.sqrt(4 * rel_V ** 2 + rel_R ** 2)
        # Q_cond = κ A dT / L → rel σ_Q = sqrt(σ_κ^2 + σ_A^2 + σ_dT^2 + σ_L^2)
        rel_Q = math.sqrt(_rel("thermal_conductivity") ** 2
                          + _rel("area_m2") ** 2
                          + _rel("T_hot_K") ** 2
                          + _rel("thickness_m") ** 2
                          + STRUCTURAL_MODEL_ERROR ** 2)

        def band(nom: float, rel: float) -> Tuple[float, float]:
            sigma_abs = abs(nom) * rel
            return (nom - sigma_abs, nom + sigma_abs)

        return Prediction(
            config_id=config.config_id,
            config_hash=config.config_hash,
            domain="thermoelectric",
            predicted_properties={
                "ZT": ZT,
                "V_oc_V": V_oc,
                "R_internal_ohm": R_in,
                "P_max_W": P_max,
                "Q_cond_W": Q_cond,
                "T_avg_K": T_avg,
                "delta_T_K": dT,
            },
            uncertainty={
                "ZT": band(ZT, rel_ZT),
                "V_oc_V": band(V_oc, rel_V),
                "R_internal_ohm": band(R_in, rel_R),
                "P_max_W": band(P_max, rel_P),
                "Q_cond_W": band(Q_cond, rel_Q),
            },
            equations_used=[
                "ZT = S^2 * σ * T / κ",
                "V_oc = S * ΔT",
                "R_in = L / (σ * A)",
                "P_max = V_oc^2 / (4 * R_in)",
                "Q_cond = κ * A * ΔT / L",
            ],
            assumptions=[
                "uniform material properties (no temperature gradient in S, σ, κ)",
                "matched load (R_load = R_in)",
                "no contact resistance",
                "no radiative losses",
                f"structural model error: ±{int(STRUCTURAL_MODEL_ERROR*100)}% (1σ)",
                f"input relative uncertainties (1σ): "
                f"S=±{int(_rel('seebeck_coefficient')*100)}%, "
                f"σ=±{int(_rel('electrical_conductivity')*100)}%, "
                f"κ=±{int(_rel('thermal_conductivity')*100)}%",
            ],
            timestamp=datetime.now(timezone.utc).isoformat(),
            provenance={
                "model": "ForwardModel",
                "stage": "IV",
                "method": "linearized uncertainty propagation",
            },
        )

    # ----- thermal (radiative cooling) ---------------------------------
    def _predict_thermal(self, config) -> Prediction:
        """Thermal prediction: radiative cooling power Q_rad.

        Equation:
          Q_rad = ε * σ_SB * A * (T_surface^4 - T_sky^4)
        """
        comp = config.components[0]
        eps = comp.parameters.get("emissivity", 0.9)
        A = config.parameters.get("area_m2", 1.0e-4)
        T_s = config.parameters.get("T_hot_K", 300.0)
        T_sky = config.parameters.get("T_cold_K", 270.0)

        Q_rad = eps * STEFAN_BOLTZMANN * A * (T_s ** 4 - T_sky ** 4)

        rel_eps = DEFAULT_REL_UNCERTAINTY.get("emissivity", 0.05)
        rel_A = DEFAULT_REL_UNCERTAINTY["area_m2"]
        rel_T = DEFAULT_REL_UNCERTAINTY["T_hot_K"]
        # dQ/dT_s = 4 ε σ A T_s^3  → rel σ_T contribution = 4 * rel_T (linearized)
        rel_Q = math.sqrt(rel_eps ** 2 + rel_A ** 2
                          + (4 * rel_T) ** 2
                          + STRUCTURAL_MODEL_ERROR ** 2)
        sigma_abs = abs(Q_rad) * rel_Q

        return Prediction(
            config_id=config.config_id,
            config_hash=config.config_hash,
            domain="thermal",
            predicted_properties={
                "Q_rad_W": Q_rad,
                "emissivity": eps,
                "T_surface_K": T_s,
                "T_sky_K": T_sky,
            },
            uncertainty={
                "Q_rad_W": (Q_rad - sigma_abs, Q_rad + sigma_abs),
            },
            equations_used=[
                "Q_rad = ε * σ_SB * A * (T_surface^4 - T_sky^4)",
                f"σ_SB = {STEFAN_BOLTZMANN} W/(m^2·K^4)",
            ],
            assumptions=[
                "surface is gray (ε independent of wavelength)",
                "sky is a blackbody at T_sky",
                "no convective losses",
                f"structural model error: ±{int(STRUCTURAL_MODEL_ERROR*100)}% (1σ)",
            ],
            timestamp=datetime.now(timezone.utc).isoformat(),
            provenance={"model": "ForwardModel", "stage": "IV"},
        )

    # ----- supercapacitor ----------------------------------------------
    def _predict_supercapacitor(self, config) -> Prediction:
        """Supercapacitor prediction: C, E, P.

        Equations:
          C = ε_0 * ε_r * A / d              (parallel-plate, EDLC)
          E = 0.5 * C * V^2                  (stored energy)
          P = V^2 / (4 * ESR)                (matched load power)
        """
        comp = config.components[0]
        eps_r = comp.parameters.get("relative_permittivity", 10.0)
        A = config.parameters.get("area_m2", 1.0e-4)
        d = config.parameters.get("thickness_m", 1.0e-6)
        V = config.parameters.get("voltage_V", 1.0)
        ESR = comp.parameters.get("esr_ohm", 0.1)

        eps_0 = 8.8541878128e-12  # F/m
        C = eps_0 * eps_r * A / d if d > 0 else 0.0
        E = 0.5 * C * V ** 2
        P = (V ** 2) / (4.0 * ESR) if ESR > 0 else 0.0

        rel_C = math.sqrt(0.10 ** 2 + 0.05 ** 2 + 0.05 ** 2
                          + STRUCTURAL_MODEL_ERROR ** 2)
        rel_E = math.sqrt(rel_C ** 2 + 0.02 ** 2)
        rel_P = math.sqrt(0.02 ** 2 + 0.20 ** 2 + STRUCTURAL_MODEL_ERROR ** 2)
        return Prediction(
            config_id=config.config_id,
            config_hash=config.config_hash,
            domain="supercapacitor",
            predicted_properties={
                "capacitance_F": C,
                "energy_J": E,
                "power_W": P,
                "voltage_V": V,
            },
            uncertainty={
                "capacitance_F": (C - abs(C) * rel_C, C + abs(C) * rel_C),
                "energy_J": (E - abs(E) * rel_E, E + abs(E) * rel_E),
                "power_W": (P - abs(P) * rel_P, P + abs(P) * rel_P),
            },
            equations_used=[
                "C = ε_0 * ε_r * A / d",
                "E = 0.5 * C * V^2",
                "P = V^2 / (4 * ESR)",
            ],
            assumptions=[
                "parallel-plate EDLC model",
                "no leakage current",
                "uniform dielectric",
                f"structural model error: ±{int(STRUCTURAL_MODEL_ERROR*100)}% (1σ)",
            ],
            timestamp=datetime.now(timezone.utc).isoformat(),
            provenance={"model": "ForwardModel", "stage": "IV"},
        )

    # ----- generic electrical (Ohm's law) ------------------------------
    def _predict_generic_electrical(self, config) -> Prediction:
        """Generic electrical prediction: R, V=IR, P=VI."""
        comp = config.components[0]
        sigma = comp.parameters.get("electrical_conductivity", 1.0e6)
        L = config.parameters.get("thickness_m", 1.0e-3)
        A = config.parameters.get("area_m2", 1.0e-4)
        I = config.parameters.get("current_A", 1.0)

        R = L / (sigma * A) if sigma > 0 and A > 0 else float("inf")
        V = I * R if R < float("inf") else 0.0
        P = V * I

        rel_R = math.sqrt(DEFAULT_REL_UNCERTAINTY["thickness_m"] ** 2
                          + 0.20 ** 2
                          + DEFAULT_REL_UNCERTAINTY["area_m2"] ** 2
                          + STRUCTURAL_MODEL_ERROR ** 2)
        rel_V = rel_R  # V = IR, I is treated as exact
        rel_P = rel_V

        return Prediction(
            config_id=config.config_id,
            config_hash=config.config_hash,
            domain=config.domain or "electrical",
            predicted_properties={
                "resistance_ohm": R,
                "voltage_V": V,
                "power_W": P,
            },
            uncertainty={
                "resistance_ohm": (R - abs(R) * rel_R, R + abs(R) * rel_R),
                "voltage_V": (V - abs(V) * rel_V, V + abs(V) * rel_V),
                "power_W": (P - abs(P) * rel_P, P + abs(P) * rel_P),
            },
            equations_used=[
                "R = L / (σ * A)",
                "V = I * R",
                "P = V * I",
            ],
            assumptions=[
                "ohmic (linear) material",
                "uniform cross-section",
                f"structural model error: ±{int(STRUCTURAL_MODEL_ERROR*100)}% (1σ)",
            ],
            timestamp=datetime.now(timezone.utc).isoformat(),
            provenance={"model": "ForwardModel", "stage": "IV"},
        )


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
def main():
    """Demo: predict three thermoelectric candidates."""
    print("=" * 60)
    print("FORWARD MODEL (Stage IV)")
    print("=" * 60)
    print()

    from scripts.artifact_generator import ArtifactGenerator
    from scripts.specification import SpecificationEngine
    from scripts.capability_graph import CapabilityGraph

    spec = SpecificationEngine().compile(
        "improve thermoelectric efficiency of bismuth telluride")
    cg = CapabilityGraph()
    cg.from_relations([
        ("bismuth telluride", "generates", "voltage"),
        ("bismuth telluride", "conducts", "electricity"),
        ("lead telluride", "generates", "voltage"),
    ])
    configs = ArtifactGenerator(seed=42).generate(spec, cg, n=3)

    fm = ForwardModel()
    for c in configs:
        pred = fm.predict(c)
        print(f"\n  {c.config_id}  hash={c.config_hash}")
        print(f"    operators: {' -> '.join(c.design_operator_chain)}")
        print(f"    predictions:")
        for k, v in pred.predicted_properties.items():
            lo, hi = pred.uncertainty.get(k, (0.0, 0.0))
            print(f"      {k:25s} = {v:12.6g}  (1σ: [{lo:12.6g}, {hi:12.6g}])")
        print(f"    equations: {pred.equations_used}")
        print(f"    assumptions: {len(pred.assumptions)} listed")

    # Different parameters → different predictions
    print()
    print("  Different-parameter test:")
    from scripts.artifact_generator import Component, Configuration, MATERIAL_PARAMS
    c_base = Configuration(
        config_id="A", spec_objective="x", domain="thermoelectric",
        components=[Component(material="bismuth_telluride", role="active",
                              parameters=dict(MATERIAL_PARAMS["bismuth_telluride"]))],
        structure="monolithic",
        parameters={"thickness_m": 1e-3, "area_m2": 1e-4,
                    "T_hot_K": 400.0, "T_cold_K": 300.0},
        design_operator_chain=["init"],
    )
    c_base.config_hash = c_base.compute_hash()
    p1 = fm.predict(c_base)

    # Modify the seebeck coefficient
    c_mod = Configuration(
        config_id="B", spec_objective="x", domain="thermoelectric",
        components=[Component(material="bismuth_telluride", role="active",
                              parameters={**MATERIAL_PARAMS["bismuth_telluride"],
                                          "seebeck_coefficient": 400e-6})],
        structure="monolithic",
        parameters={"thickness_m": 1e-3, "area_m2": 1e-4,
                    "T_hot_K": 400.0, "T_cold_K": 300.0},
        design_operator_chain=["init"],
    )
    c_mod.config_hash = c_mod.compute_hash()
    p2 = fm.predict(c_mod)

    print(f"    base ZT = {p1.predicted_properties['ZT']:.4f}")
    print(f"    mod  ZT = {p2.predicted_properties['ZT']:.4f}")
    print(f"    V_oc base = {p1.predicted_properties['V_oc_V']*1000:.2f} mV")
    print(f"    V_oc mod  = {p2.predicted_properties['V_oc_V']*1000:.2f} mV")
    assert p1.predicted_properties["ZT"] != p2.predicted_properties["ZT"], (
        "different parameters must produce different predictions")
    print("    PASS: different parameters → different predictions")


if __name__ == "__main__":
    main()
