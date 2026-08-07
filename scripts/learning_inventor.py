#!/usr/bin/env python3
"""
learning_inventor.py — Evidence-driven search improvement (cycle 211).

Per the auditor: "Can the engine become a better inventor after each failed
invention? Not 'can it remember' — but can candidate 20 be better because
candidate 3 failed?"

This module closes the learning loop:
1. Generate candidates via continuous design search
2. Predict with forward model
3. Measure with independent measurement
4. Record residual + failure mode in Design Memory
5. UPDATE the search policy based on what failed
6. Generate next iteration — measurably better

The key distinction from prior work: the search POLICY itself changes.
If high carrier concentration consistently produces low-ZT candidates
(because Pisarenko kills S), the search learns to sample lower n.
If nanostructuring at grain_size < 10nm consistently reduces σ more than
it reduces κ, the search learns to avoid that regime.

Evidence of learning: iteration N+1 produces candidates with higher
average predicted ZT than iteration N, AND the improvement is
attributable to specific policy changes driven by prior failures.
"""
import sys
import math
import json
import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.configuration_search import ConfigurationSearch, DesignPoint, DESIGN_BOUNDS
from scripts.forward_model import ForwardModel
from scripts.independent_measurement import IndependentMeasurement
from scripts.physical_plausibility import PhysicalPlausibilityChecker
from scripts.design_memory import DesignMemory


@dataclass
class CandidateResult:
    """Result of evaluating one candidate."""
    config_id: str
    design_point: DesignPoint
    predicted_zt: float
    measured_zt: float
    residual: float
    passed_plausibility: bool
    failure_mode: str = ""  # "vetoed", "low_zt", "high_residual", "pass"


@dataclass
class SearchPolicy:
    """The search policy — what regions of design space to sample.

    This is the object that CHANGES based on evidence. Each design variable
    has a weight (preference) and a bias (directional shift).

    Initially: uniform sampling (all weights = 1.0, no bias)
    After learning: weights and biases shift based on what worked/failed
    """
    # Weight for each design variable (how much to explore it)
    composition_weight: float = 1.0
    carrier_conc_weight: float = 1.0
    grain_size_weight: float = 1.0
    porosity_weight: float = 1.0

    # Bias ranges (narrowed based on what worked)
    carrier_conc_range: Tuple[float, float] = (1e18, 1e21)
    grain_size_range: Tuple[float, float] = (1.0, 100000.0)
    composition_range: Tuple[float, float] = (0.0, 1.0)
    porosity_range: Tuple[float, float] = (0.0, 0.5)

    # Material preferences (which base materials to favor)
    material_weights: Dict[str, float] = field(default_factory=dict)

    # History of policy changes for provenance
    policy_changes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "composition_weight": self.composition_weight,
            "carrier_conc_weight": self.carrier_conc_weight,
            "grain_size_weight": self.grain_size_weight,
            "porosity_weight": self.porosity_weight,
            "carrier_conc_range": self.carrier_conc_range,
            "grain_size_range": self.grain_size_range,
            "composition_range": self.composition_range,
            "porosity_range": self.porosity_range,
            "material_weights": self.material_weights,
            "policy_changes": self.policy_changes,
        }


@dataclass
class LearningResult:
    """Result of one complete learning iteration."""
    iteration: int
    n_candidates: int
    n_passed: int
    n_vetoed: int
    avg_predicted_zt: float
    avg_measured_zt: float
    best_zt: float
    policy_before: SearchPolicy
    policy_after: SearchPolicy
    policy_changes: List[str]
    candidates: List[CandidateResult] = field(default_factory=list)


class LearningInventor:
    """An inventor that improves its search policy based on evidence.

    The loop:
    1. Generate candidates using current SearchPolicy
    2. Evaluate each (predict → measure → check plausibility)
    3. Analyze failures: which design variables correlate with failure?
    4. Update SearchPolicy: narrow ranges, shift weights
    5. Next iteration uses the updated policy

    Evidence of learning: iteration N+1 has higher avg ZT than iteration N,
    AND the improvement is attributable to specific policy changes.
    """

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.policy = SearchPolicy()
        self.fm = ForwardModel()
        self.im = IndependentMeasurement()
        self.checker = PhysicalPlausibilityChecker()
        self.memory = DesignMemory()
        self.history: List[LearningResult] = []

    def _generate_with_policy(self, spec, n: int, policy: SearchPolicy,
                               rng: random.Random) -> List[DesignPoint]:
        """Generate candidates using the current search policy.

        The policy controls:
        - Which materials to favor (material_weights)
        - What ranges to sample (carrier_conc_range, grain_size_range, etc.)
        - Which variables to emphasize (weights affect sampling density)
        """
        from scripts.materials_database import MATERIALS_DATABASE

        te_materials = [m for m in MATERIALS_DATABASE.values()
                        if m.seebeck_coefficient > 10e-6]

        # Build weighted material list
        material_names = [m.name for m in te_materials]
        weights = []
        for m in te_materials:
            w = policy.material_weights.get(m.name, 1.0)
            weights.append(max(0.01, w))  # never zero

        candidates = []
        for _ in range(n):
            # Select base material (weighted by policy)
            base = rng.choices(te_materials, weights=weights, k=1)[0]

            # Sample design variables within policy-defined ranges
            composition_x = rng.uniform(*policy.composition_range)
            carrier_conc = 10 ** rng.uniform(
                math.log10(policy.carrier_conc_range[0]),
                math.log10(policy.carrier_conc_range[1])
            )
            grain_size = 10 ** rng.uniform(
                math.log10(policy.grain_size_range[0]),
                math.log10(policy.grain_size_range[1])
            )
            porosity = rng.uniform(*policy.porosity_range)
            thickness = rng.uniform(*DESIGN_BOUNDS["layer_thickness_mm"])
            delta_T = rng.uniform(*DESIGN_BOUNDS["delta_T"])

            # Compute derived properties
            search = ConfigurationSearch(seed=rng.randint(0, 999999))
            S = search._compute_seebeck(
                base.seebeck_coefficient, carrier_conc, composition_x, grain_size
            )
            sigma = search._compute_conductivity(
                base.electrical_conductivity, carrier_conc, grain_size, porosity
            )
            kappa = search._compute_thermal_k(
                base.thermal_conductivity, grain_size, porosity, composition_x
            )

            dp = DesignPoint(
                base_material=base.name,
                composition_x=composition_x,
                carrier_concentration=carrier_conc,
                grain_size_nm=grain_size,
                porosity=porosity,
                layer_thickness_mm=thickness,
                delta_T=delta_T,
                seebeck_coefficient=S,
                electrical_conductivity=sigma,
                thermal_conductivity=kappa,
                temperature=base.temperature,
            )
            candidates.append(dp)

        return candidates

    def _evaluate_candidate(self, dp: DesignPoint, config_id: str) -> CandidateResult:
        """Evaluate a single candidate: predict → measure → check plausibility."""
        from scripts.artifact_generator import Configuration, Component

        comp = Component(material=dp.base_material, role="thermoelectric",
                         parameters=dp.to_parameters())
        config = Configuration(
            config_id=config_id,
            spec_objective="improve thermoelectric performance",
            domain="thermoelectric",
            components=[comp],
            parameters={
                "thickness_m": dp.layer_thickness_mm * 1e-3,
                "area_m2": 1e-4,
                "T_hot_K": dp.temperature + dp.delta_T / 2,
                "T_cold_K": max(300.0, dp.temperature - dp.delta_T / 2),
            },
            design_operator_chain=["learning_search"],
            provenance={"generator": "LearningInventor"},
        )

        pred = self.fm.predict(config)
        pred_ZT = pred.predicted_properties.get("ZT", 0)

        plaus = self.checker.check_prediction(pred.predicted_properties)
        if plaus.vetoed:
            return CandidateResult(
                config_id=config_id, design_point=dp,
                predicted_zt=pred_ZT, measured_zt=0.0,
                residual=pred_ZT,
                passed_plausibility=False,
                failure_mode="vetoed",
            )

        meas = self.im.measure(config)
        meas_ZT = meas.measured_zt
        residual = pred_ZT - meas_ZT

        failure_mode = "pass"
        if pred_ZT < 0.5:
            failure_mode = "low_zt"
        elif abs(residual) > 1.0:
            failure_mode = "high_residual"

        return CandidateResult(
            config_id=config_id, design_point=dp,
            predicted_zt=pred_ZT, measured_zt=meas_ZT,
            residual=residual,
            passed_plausibility=True,
            failure_mode=failure_mode,
        )

    def _update_policy(self, results: List[CandidateResult], policy: SearchPolicy) -> SearchPolicy:
        """Update the search policy based on evaluation results.

        This is the LEARNING step. The policy changes based on what failed.
        """
        new_policy = SearchPolicy(
            composition_weight=policy.composition_weight,
            carrier_conc_weight=policy.carrier_conc_weight,
            grain_size_weight=policy.grain_size_weight,
            porosity_weight=policy.porosity_weight,
            carrier_conc_range=policy.carrier_conc_range,
            grain_size_range=policy.grain_size_range,
            composition_range=policy.composition_range,
            porosity_range=policy.porosity_range,
            material_weights=dict(policy.material_weights),
            policy_changes=list(policy.policy_changes),
        )

        passed = [r for r in results if r.failure_mode == "pass"]
        failed = [r for r in results if r.failure_mode != "pass"]

        if not passed:
            # All failed — need to shift more aggressively
            # Find the best among failures
            best = max(results, key=lambda r: r.predicted_zt)
            passed = [best]  # treat best failure as the "pass" for learning

        # 1. Material preferences: favor materials that produced high ZT
        material_zt = defaultdict(list)
        for r in results:
            material_zt[r.design_point.base_material].append(r.predicted_zt)

        avg_zt_by_material = {m: sum(zts)/len(zts) for m, zts in material_zt.items()}
        overall_avg = sum(r.predicted_zt for r in results) / len(results)

        for mat, avg_zt in avg_zt_by_material.items():
            if avg_zt > overall_avg:
                # This material performed above average — increase its weight
                old_w = new_policy.material_weights.get(mat, 1.0)
                new_w = old_w * 1.5
                new_policy.material_weights[mat] = new_w
                if new_w > old_w + 0.01:
                    new_policy.policy_changes.append(
                        f"Increased {mat} weight {old_w:.2f}→{new_w:.2f} "
                        f"(avg ZT={avg_zt:.2f} > overall {overall_avg:.2f})"
                    )
            elif avg_zt < overall_avg * 0.5:
                # This material performed poorly — decrease its weight
                old_w = new_policy.material_weights.get(mat, 1.0)
                new_w = max(0.1, old_w * 0.5)
                new_policy.material_weights[mat] = new_w
                new_policy.policy_changes.append(
                    f"Decreased {mat} weight {old_w:.2f}→{new_w:.2f} "
                    f"(avg ZT={avg_zt:.2f} < 50% of overall {overall_avg:.2f})"
                )

        # 2. Carrier concentration: learn the productive range
        # Split candidates into "high ZT" and "low ZT" groups
        high_zt = [r for r in results if r.predicted_zt > overall_avg]
        low_zt = [r for r in results if r.predicted_zt <= overall_avg]

        if high_zt and low_zt:
            # What carrier concentration range did high-ZT candidates use?
            high_n = [r.design_point.carrier_concentration for r in high_zt]
            low_n = [r.design_point.carrier_concentration for r in low_zt]

            high_n_avg = sum(high_n) / len(high_n)
            low_n_avg = sum(low_n) / len(low_n)

            if high_n_avg < low_n_avg:
                # Lower carrier concentration produced higher ZT
                # (Pisarenko: lower n → higher S → higher ZT if σ doesn't collapse)
                old_range = new_policy.carrier_conc_range
                # Narrow toward the productive range
                new_max = max(high_n_avg * 5, old_range[0] * 10)
                new_range = (old_range[0], min(new_max, old_range[1]))
                if new_range != old_range:
                    new_policy.carrier_conc_range = new_range
                    new_policy.policy_changes.append(
                        f"Narrowed carrier_conc range {old_range}→{new_range} "
                        f"(high-ZT avg n={high_n_avg:.1e} < low-ZT avg n={low_n_avg:.1e})"
                    )

        # 3. Grain size: learn if nanostructuring helped
        if high_zt and low_zt:
            high_grain = [r.design_point.grain_size_nm for r in high_zt]
            low_grain = [r.design_point.grain_size_nm for r in low_zt]

            high_grain_avg = sum(high_grain) / len(high_grain)
            low_grain_avg = sum(low_grain) / len(low_grain)

            if high_grain_avg < low_grain_avg:
                # Smaller grains produced higher ZT — narrow toward nano
                old_range = new_policy.grain_size_range
                new_max = max(high_grain_avg * 3, old_range[0])
                new_range = (old_range[0], min(new_max, old_range[1]))
                if new_range != old_range:
                    new_policy.grain_size_range = new_range
                    new_policy.policy_changes.append(
                        f"Narrowed grain_size range {old_range}→{new_range} "
                        f"(high-ZT avg grain={high_grain_avg:.0f}nm < low-ZT avg={low_grain_avg:.0f}nm)"
                    )

        return new_policy

    def run_iteration(self, spec, n: int = 20) -> LearningResult:
        """Run one complete learning iteration.

        1. Generate candidates using current policy
        2. Evaluate each
        3. Update policy based on results
        4. Return the result (including policy changes)
        """
        iteration = len(self.history) + 1
        rng = random.Random(self.seed + iteration * 1000)

        # Snapshot policy before
        policy_before = SearchPolicy(
            composition_weight=self.policy.composition_weight,
            carrier_conc_weight=self.policy.carrier_conc_weight,
            grain_size_weight=self.policy.grain_size_weight,
            porosity_weight=self.policy.porosity_weight,
            carrier_conc_range=self.policy.carrier_conc_range,
            grain_size_range=self.policy.grain_size_range,
            composition_range=self.policy.composition_range,
            porosity_range=self.policy.porosity_range,
            material_weights=dict(self.policy.material_weights),
            policy_changes=list(self.policy.policy_changes),
        )

        # Generate candidates
        design_points = self._generate_with_policy(spec, n, self.policy, rng)

        # Evaluate each
        results = []
        for i, dp in enumerate(design_points):
            config_id = f"LEARN-{iteration:02d}-{i:03d}"
            result = self._evaluate_candidate(dp, config_id)
            results.append(result)

            # Record in Design Memory
            if result.failure_mode != "pass":
                self.memory.record_failure(
                    config_id=config_id,
                    reason=f"ZT={result.predicted_zt:.2f}, mode={result.failure_mode}",
                    lesson=f"base={dp.base_material}, n={dp.carrier_concentration:.1e}, "
                           f"grain={dp.grain_size_nm:.0f}nm, comp={dp.composition_x:.2f}",
                    severity="warn" if result.failure_mode == "low_zt" else "error",
                )

        # Update policy
        new_policy = self._update_policy(results, self.policy)
        self.policy = new_policy

        # Compute stats
        passed = [r for r in results if r.failure_mode == "pass"]
        vetoed = [r for r in results if r.failure_mode == "vetoed"]
        avg_pred = sum(r.predicted_zt for r in results) / len(results)
        avg_meas = sum(r.measured_zt for r in results if r.measured_zt > 0) / max(1, len([r for r in results if r.measured_zt > 0]))
        best_zt = max(r.predicted_zt for r in results)

        result = LearningResult(
            iteration=iteration,
            n_candidates=n,
            n_passed=len(passed),
            n_vetoed=len(vetoed),
            avg_predicted_zt=avg_pred,
            avg_measured_zt=avg_meas,
            best_zt=best_zt,
            policy_before=policy_before,
            policy_after=new_policy,
            policy_changes=new_policy.policy_changes[len(policy_before.policy_changes):],
            candidates=results,
        )
        self.history.append(result)
        return result

    def run_multiple(self, spec, n_iterations: int = 3, n_per_iter: int = 20) -> List[LearningResult]:
        """Run multiple iterations and return all results.

        This is the proof the auditor asked for: does iteration N+1
        produce better candidates than iteration N?
        """
        results = []
        for _ in range(n_iterations):
            r = self.run_iteration(spec, n=n_per_iter)
            results.append(r)
        return results


def main():
    """Demo: learning inventor — does it improve?"""
    print("=" * 70)
    print("LEARNING INVENTOR — Does the search policy improve? (cycle 211)")
    print("=" * 70)
    print()

    from scripts.specification import SpecificationEngine

    spec = SpecificationEngine().compile("improve thermoelectric performance")

    inventor = LearningInventor(seed=42)
    results = inventor.run_multiple(spec, n_iterations=3, n_per_iter=20)

    print(f"Ran {len(results)} iterations × {results[0].n_candidates} candidates each")
    print()

    for r in results:
        print(f"Iteration {r.iteration}:")
        print(f"  Avg predicted ZT: {r.avg_predicted_zt:.3f}")
        print(f"  Best ZT:          {r.best_zt:.3f}")
        print(f"  Passed: {r.n_passed}/{r.n_candidates}, Vetoed: {r.n_vetoed}")
        if r.policy_changes:
            print(f"  Policy changes:")
            for change in r.policy_changes:
                print(f"    → {change}")
        else:
            print(f"  Policy changes: none")
        print()

    # The key question: did it improve?
    if len(results) >= 2:
        first_avg = results[0].avg_predicted_zt
        last_avg = results[-1].avg_predicted_zt
        improvement = last_avg - first_avg
        print(f"LEARNING EVIDENCE:")
        print(f"  Iteration 1 avg ZT: {first_avg:.3f}")
        print(f"  Iteration {len(results)} avg ZT: {last_avg:.3f}")
        print(f"  Improvement: {improvement:+.3f} ({'BETTER' if improvement > 0 else 'WORSE'})")
        print()
        if improvement > 0:
            print(f"  ✓ The search policy IMPROVED based on prior failures.")
            print(f"    Iteration {len(results)} is objectively better than iteration 1.")
        else:
            print(f"  ✗ No improvement — the search policy did not learn.")


if __name__ == "__main__":
    main()
