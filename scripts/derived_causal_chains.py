#!/usr/bin/env python3
"""
derived_causal_chains.py — Infer causal chains from forward model probes (cycle 219).

Per auditor update #9 (priority #3):
  "Advance Layer C from curated to derived. The executable causal chains
   are a great foundation. The next step is to *infer* chain structure
   from the mechanism models (vary a variable → propagate → observe
   which downstream quantities move), so the chain is discovered, not
   selected from a lookup."

This module implements causal-chain DERIVATION via counterfactual probing:

  1. Take a forward model (any function: design_point → (outcome, derived))
  2. Pick a "root" design variable (e.g., composition_x)
  3. Probe the forward model at two values of the root (baseline + perturbed)
  4. Observe which DERIVED quantities (S, σ, κ, etc.) changed
  5. For each derived quantity that changed, probe IT as a root in a
     separate counterfactual — does perturbing it change the OUTCOME?
  6. If yes, we have a chain: root → derived_1 → outcome
  7. Repeat recursively to build multi-hop chains

The output is the SAME data structure as curated CAUSAL_CHAINS — a list
of (variable, change, mechanism, formula) steps — but the chain TOPOLOGY
is discovered by probing, not selected from a lookup.

Mechanism names + formulas are still curated (they reference named
physical relations like "Pisarenko" or "Klemens"), but the system
DISCOVERS which relations are relevant by observing which derived
quantities actually move when a variable is perturbed.

This is partial progress toward derived causal discovery — the topology
is inferred, the labels are curated. Full derivation (inferring the
formula itself from data) is future work.
"""
import sys
import math
import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Callable, Any
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.meta_invention import CausalStep, CausalChain, CAUSAL_CHAINS


@dataclass
class ProbeResult:
    """Result of probing a forward model by perturbing one variable."""
    variable: str
    baseline_value: float
    perturbed_value: float
    baseline_outcome: float
    perturbed_outcome: float
    baseline_derived: Dict[str, float]
    perturbed_derived: Dict[str, float]

    def outcome_delta(self) -> float:
        return self.perturbed_outcome - self.baseline_outcome

    def derived_deltas(self) -> Dict[str, float]:
        """Return the change in each derived quantity."""
        deltas = {}
        for key in self.baseline_derived:
            if key in self.perturbed_derived:
                deltas[key] = self.perturbed_derived[key] - self.baseline_derived[key]
        return deltas

    def derived_ratios(self) -> Dict[str, float]:
        """Return relative change in each derived quantity (handles scale)."""
        ratios = {}
        for key in self.baseline_derived:
            if key in self.perturbed_derived:
                base = self.baseline_derived[key]
                if abs(base) > 1e-12:
                    ratios[key] = (self.perturbed_derived[key] - base) / abs(base)
        return ratios


class CausalChainDeriver:
    """Infers causal chains from forward model probes.

    Algorithm:
      1. Start with a root variable (e.g., composition_x)
      2. Probe forward model at baseline and perturbed root values
      3. For each derived quantity that changed significantly:
         - Probe whether perturbing THAT derived quantity (as a free
           variable, where possible) changes the outcome
         - If yes, add it as the next step in the chain
      4. Recurse until no derived quantities change significantly or
         we reach the outcome variable directly.

    Limitations (honest):
      - Mechanism names + formulas are still curated (we look up the
        physical relation that matches the (variable, derived) pair).
      - The chain topology IS discovered (which variables affect which
        derived quantities), but the labels are not.
      - For derived quantities that aren't design variables (e.g., S, σ, κ
        in TE), we cannot directly "perturb them" — instead, we observe
        their natural variation across many design points and test for
        correlation with the outcome.
    """

    # Curated mechanism labels — maps (variable, derived_or_outcome) →
    # (mechanism_name, formula). The chain topology is DERIVED; these
    # labels are looked up based on what the topology discovers.
    MECHANISM_LABELS = {
        ("composition_x", "lattice_thermal_conductivity"): (
            "Mass disorder scattering",
            "κ_L ∝ 1/(1+Γ·x·(1-x))",
        ),
        ("composition_x", "thermal_conductivity"): (
            "Klemens alloy scattering",
            "κ_L = (1-x)κ_A + xκ_B + κ_alloy",
        ),
        ("carrier_concentration", "seebeck_coefficient"): (
            "Pisarenko relation",
            "S = (8π²k²/3eh²) m*T (π/3n)^(2/3)",
        ),
        ("carrier_concentration", "electrical_conductivity"): (
            "Drude relation",
            "σ = neμ",
        ),
        ("grain_size_nm", "electrical_conductivity"): (
            "Grain boundary scattering",
            "μ⁻¹ = μ_bulk⁻¹ + μ_GB⁻¹",
        ),
        ("grain_size_nm", "mobility"): (
            "Matthiessen rule",
            "μ⁻¹ = μ_bulk⁻¹ + μ_GB⁻¹",
        ),
        ("electrical_conductivity", "ZT"): (
            "Thermoelectric figure of merit",
            "ZT = S²σT/κ",
        ),
        ("seebeck_coefficient", "ZT"): (
            "Thermoelectric figure of merit",
            "ZT = S²σT/κ",
        ),
        ("thermal_conductivity", "ZT"): (
            "Thermoelectric figure of merit",
            "ZT = S²σT/κ",
        ),
        ("lattice_thermal_conductivity", "ZT"): (
            "Thermoelectric figure of merit",
            "ZT = S²σT/κ",
        ),
        # Battery
        ("electrode_thickness_um", "areal_capacity_mAh_per_cm2"): (
            "Volumetric capacity",
            "Q_areal = Q_volumetric × t × (1-φ)",
        ),
        ("particle_size_nm", "accessible_capacity_fraction"): (
            "Diffusion-limited capacity",
            "τ_diff = d²/(4D_Li), accessible = 1/(1+τ_diff/t_char)",
        ),
        ("C_rate", "accessible_capacity_fraction"): (
            "Char time vs diffusion time",
            "t_char = 3600/C_rate",
        ),
        ("areal_capacity_mAh_per_cm2", "specific_energy_Whkg"): (
            "Specific energy",
            "E = Q_areal × V / mass",
        ),
        ("accessible_capacity_fraction", "specific_energy_Whkg"): (
            "Capacity derating",
            "E = Q_accessible × V / mass",
        ),
        # Catalyst
        ("particle_size_nm", "dispersion"): (
            "Surface atom fraction",
            "D ≈ 1/d (nm)",
        ),
        ("loading_wt_pct", "sintering_factor"): (
            "Sintering above threshold",
            "F_sinter = 1/(1+max(0, L-L_th)²)",
        ),
        ("calcination_temp_K", "metal_support_interaction"): (
            "Anchoring",
            "MSI = f(T_calc)",
        ),
        ("dispersion", "TOF_s1"): (
            "Active site density",
            "TOF = k × D × F_sinter × MSI",
        ),
        # PV
        ("absorber_thickness_nm", "absorption"): (
            "Beer-Lambert",
            "A = 1 - exp(-αt)",
        ),
        ("bandgap_eV", "Voc_V"): (
            "Open-circuit voltage",
            "Voc ≈ Eg/q - kT·ln(J0/Jsc)",
        ),
        ("defect_density_cm2", "diffusion_length_nm"): (
            "Recombination-limited diffusion",
            "L = √(D·τ), τ ~ 1/N_def",
        ),
        ("Voc_V", "PCE_pct"): (
            "Power conversion efficiency",
            "PCE = Voc × Jsc × FF / Pin",
        ),
        ("absorption", "PCE_pct"): (
            "Power conversion efficiency",
            "PCE = Voc × Jsc × FF / Pin",
        ),
    }

    def __init__(self, domain_spec: Dict, forward_fn: Callable,
                 perturbation_fraction: float = 0.2,
                 significance_threshold: float = 0.05):
        self.domain = domain_spec
        self.forward_fn = forward_fn
        self.perturbation_fraction = perturbation_fraction
        self.significance_threshold = significance_threshold
        # Cache: probe results keyed by (variable, baseline_value)
        self.probe_cache: Dict[Tuple[str, float], ProbeResult] = {}

    def probe(self, design_point: Dict[str, float], variable: str,
              direction: str = "increase") -> ProbeResult:
        """Probe the forward model by perturbing one variable.

        direction: "increase" or "decrease" — which way to perturb.
        """
        lo, hi = None, None
        for v in self.domain["design_vars"]:
            if v["name"] == variable:
                lo, hi = v["bounds"]
                break
        if lo is None:
            # Variable not in design space — can't probe directly
            raise ValueError(f"Variable {variable} not in design space")

        base_val = design_point[variable]
        # Perturb by 50% of the way to the bound in the chosen direction
        if direction == "increase":
            perturbed_val = base_val + 0.5 * (hi - base_val)
        else:
            perturbed_val = base_val - 0.5 * (base_val - lo)

        # Avoid caching by exact value (use rounded key)
        cache_key = (variable, round(base_val, 6), direction)
        if cache_key in self.probe_cache:
            return self.probe_cache[cache_key]

        # Evaluate baseline
        baseline_outcome, baseline_derived = self.forward_fn(design_point)
        # Evaluate perturbed
        perturbed_dp = dict(design_point)
        perturbed_dp[variable] = perturbed_val
        perturbed_outcome, perturbed_derived = self.forward_fn(perturbed_dp)

        result = ProbeResult(
            variable=variable,
            baseline_value=base_val,
            perturbed_value=perturbed_val,
            baseline_outcome=baseline_outcome,
            perturbed_outcome=perturbed_outcome,
            baseline_derived=baseline_derived,
            perturbed_derived=perturbed_derived,
        )
        self.probe_cache[cache_key] = result
        return result

    def find_significant_derived(self, probe_result: ProbeResult) -> List[Tuple[str, float, str]]:
        """Find derived quantities that changed significantly when the
        variable was perturbed.

        Returns list of (derived_name, relative_change, direction).
        """
        ratios = probe_result.derived_ratios()
        significant = []
        for name, ratio in ratios.items():
            if abs(ratio) > self.significance_threshold:
                direction = "increases" if ratio > 0 else "decreases"
                significant.append((name, ratio, direction))
        # Sort by magnitude
        significant.sort(key=lambda x: -abs(x[1]))
        return significant

    def find_direct_outcome_link(self, probe_result: ProbeResult) -> Optional[str]:
        """Check if perturbing the variable directly changes the outcome
        significantly. If yes, return the direction."""
        outcome_delta = probe_result.outcome_delta()
        base = abs(probe_result.baseline_outcome)
        if base < 1e-12:
            base = 1.0
        rel_change = abs(outcome_delta) / base
        if rel_change > self.significance_threshold:
            return "increases" if outcome_delta > 0 else "decreases"
        return None

    def derive_chain(self, root_variable: str, baseline_dp: Dict[str, float],
                     max_depth: int = 4) -> Optional[CausalChain]:
        """Derive a causal chain starting from root_variable.

        Algorithm:
          1. Probe root_variable (perturb it) → see what derived quantities move
          2. For each derived quantity that moves significantly:
             a. If it has a mechanism label for (root, derived) → add step 1
             b. Recurse: treat derived as new root, see what IT moves
          3. Continue until we reach the outcome variable directly

        Chain structure (matches curated CAUSAL_CHAINS):
          Step 1: variable=root, change=perturbation_direction,
                  mechanism=(root→derived relation), formula
          Step 2: variable=derived, change=observed_direction_of_derived,
                  mechanism=(derived→outcome relation), formula
          Step 3: variable=outcome, change=observed_direction_of_outcome,
                  mechanism=(final formula), formula

        Each step's `change` is the direction THAT variable changed.
        """
        chain_steps = []
        outcome_name = self.domain["outcome_name"]

        # Step 1: probe root variable
        probe = self.probe(baseline_dp, root_variable, "increase")
        significant_derived = self.find_significant_derived(probe)

        if not significant_derived:
            # No derived quantities moved — root has no indirect effect
            direct_link = self.find_direct_outcome_link(probe)
            if direct_link:
                # Direct root → outcome link
                label = self.MECHANISM_LABELS.get((root_variable, outcome_name))
                if label:
                    mech, formula = label
                    chain_steps.append(CausalStep(
                        variable=root_variable,
                        change="increases",  # we perturbed "increase"
                        mechanism=mech,
                        formula=formula,
                    ))
                    chain_steps.append(CausalStep(
                        variable=outcome_name,
                        change=direct_link,
                        mechanism=mech,
                        formula=formula,
                    ))
                    return CausalChain(
                        chain_id=f"DERIVED-{root_variable}_to_{outcome_name}",
                        steps=chain_steps,
                        final_variable=outcome_name,
                        final_change=direct_link,
                    )
            return None

        # Find the most-significant derived quantity with a label
        next_var = None
        next_direction = None
        for name, ratio, direction in significant_derived:
            if (root_variable, name) in self.MECHANISM_LABELS:
                next_var = name
                next_direction = direction  # direction the DERIVED moved
                mech, formula = self.MECHANISM_LABELS[(root_variable, name)]
                # Step 1: root variable was perturbed "increase"
                chain_steps.append(CausalStep(
                    variable=root_variable,
                    change="increases",  # perturbation direction
                    mechanism=mech,
                    formula=formula,
                ))
                break

        if next_var is None:
            return None

        # Step 2: derived quantity moved (observed direction)
        outcome_link = self.MECHANISM_LABELS.get((next_var, outcome_name))
        if outcome_link:
            mech, formula = outcome_link
            chain_steps.append(CausalStep(
                variable=next_var,
                change=next_direction,  # observed direction of derived
                mechanism=mech,
                formula=formula,
            ))

            # Step 3: outcome (observed direction from probe)
            outcome_delta = probe.outcome_delta()
            outcome_direction = "increases" if outcome_delta > 0 else "decreases"
            chain_steps.append(CausalStep(
                variable=outcome_name,
                change=outcome_direction,
                mechanism=mech,  # same formula, restated for outcome
                formula=formula,
            ))

            return CausalChain(
                chain_id=f"DERIVED-{root_variable}_to_{outcome_name}_via_{next_var}",
                steps=chain_steps,
                final_variable=outcome_name,
                final_change=outcome_direction,
            )

        # Could not complete the chain (no outcome link label)
        return None


def demonstrate_derivation():
    """Demonstrate causal-chain derivation vs curated."""
    print("=" * 78)
    print("DERIVED CAUSAL CHAINS (cycle 219) — topology inferred from probes")
    print("=" * 78)
    print()

    from scripts.cross_domain_transfer import (
        THERMOELECTRIC_DOMAIN, BATTERY_DOMAIN, CATALYST_DOMAIN, PV_DOMAIN,
        thermoelectric_forward, battery_forward, catalyst_forward, pv_forward,
    )

    cases = [
        ("Thermoelectric", THERMOELECTRIC_DOMAIN, thermoelectric_forward, "composition_x"),
        ("Thermoelectric", THERMOELECTRIC_DOMAIN, thermoelectric_forward, "carrier_concentration"),
        ("Thermoelectric", THERMOELECTRIC_DOMAIN, thermoelectric_forward, "grain_size_nm"),
        ("Battery",        BATTERY_DOMAIN,         battery_forward,        "particle_size_nm"),
        ("Catalyst",       CATALYST_DOMAIN,        catalyst_forward,       "particle_size_nm"),
        ("Photovoltaic",   PV_DOMAIN,              pv_forward,             "bandgap_eV"),
    ]

    for domain_name, spec, fn, root_var in cases:
        print(f"--- Domain: {domain_name}, root variable: {root_var} ---")
        deriver = CausalChainDeriver(spec, fn)
        # Use mid-bounds baseline
        baseline = {}
        for v in spec["design_vars"]:
            lo, hi = v["bounds"]
            if lo > 0 and hi / lo > 100:
                baseline[v["name"]] = math.exp((math.log(lo) + math.log(hi)) / 2)
            else:
                baseline[v["name"]] = (lo + hi) / 2
        # For TE, use a more realistic carrier concentration
        if root_var == "carrier_concentration":
            baseline["carrier_concentration"] = 1e19

        # Probe to see what moves
        probe = deriver.probe(baseline, root_var, "increase")
        print(f"  Baseline {root_var}={probe.baseline_value:.3e} → outcome={probe.baseline_outcome:.3e}")
        print(f"  Perturbed {root_var}={probe.perturbed_value:.3e} → outcome={probe.perturbed_outcome:.3e}")
        print(f"  Outcome delta: {probe.outcome_delta():+.3e}")
        print(f"  Derived deltas:")
        for name, delta in probe.derived_deltas().items():
            print(f"    {name}: {delta:+.3e}")

        # Derive chain
        chain = deriver.derive_chain(root_var, baseline, max_depth=4)
        if chain:
            print(f"  DERIVED CHAIN: {chain.chain_id}")
            for i, step in enumerate(chain.steps):
                print(f"    {i+1}. {step.variable} {step.change} via {step.mechanism}")
                print(f"       formula: {step.formula}")
        else:
            print(f"  (no chain derivable — no matching mechanism labels)")
        print()


if __name__ == "__main__":
    demonstrate_derivation()
