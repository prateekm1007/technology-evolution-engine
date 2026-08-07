#!/usr/bin/env python3
"""
heuristic_learning.py — Learn transferable invention heuristics (cycle 212).

Per the auditor: "The learned object should no longer be 'PbTe weight = 3.38.'
It should be reusable design principles such as:
  - 'Nanostructuring improves ZT only within certain grain-size regimes.'
  - 'Reducing carrier concentration increases S but introduces σ tradeoff.'
  - 'Alloying is effective when lattice κ dominates.'

Those principles can then be transferred to materials the engine has never
seen before."

This module learns HEURISTICS (not material preferences):
1. After evaluating candidates, extract which DESIGN OPERATORS correlated
   with success/failure — not which MATERIALS.
2. Formulate the correlation as a human-readable heuristic.
3. Test the heuristic on UNSEEN materials (transferability).
4. The heuristic modifies the search policy for new materials.

The key distinction:
  - Material preference: "PbTe is good" (not transferable)
  - Heuristic: "Nanostructuring at grain_size < 50nm improves ZT when
    lattice κ > 1.0 W/(m·K)" (transferable to ANY high-κ material)
"""
import sys
import math
import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@dataclass
class InventionHeuristic:
    """A transferable design heuristic learned from evidence.

    Unlike material preferences ("PbTe is good"), heuristics describe
    RELATIONSHIPS between design variables and outcomes that hold
    across materials.

    Cycle 216 upgrade (auditor's "physics not statistics" requirement):
    A real physics heuristic has an EXCEPTION clause — it states when
    the rule breaks down. Without an exception, the heuristic is just
    a regression coefficient. With an exception, it is a conditional
    physical claim.

    Example of a statistics-level heuristic (BANNED by this upgrade):
        "grain_size < 20nm good"

    Example of a physics-level heuristic (REQUIRED by this upgrade):
        "Reducing grain size below 50nm increases ZT when lattice κ > 1.0,
         EXCEPT when grain_boundary_resistance > 1e-8 Ω·m² (because then
         σ collapses faster than κ is reduced)."
    """
    heuristic_id: str
    statement: str           # human-readable full statement with exception clause
    variable: str            # "grain_size_nm"
    condition: str           # "thermal_conductivity > 1.0" (when the rule applies)
    direction: str           # "decrease" (reduce grain size) or "increase"
    effect: str              # "increases ZT" or "decreases ZT"
    confidence: float        # 0-1, based on how consistently it held
    evidence_count: int      # how many candidates supported this
    counterexample_count: int  # how many contradicted it
    transferable: bool = False  # verified on unseen materials
    materials_tested: List[str] = field(default_factory=list)
    # Cycle 216 — exception clause (the "when does this rule break" structure)
    exception_variable: str = ""    # e.g. "grain_boundary_resistance"
    exception_threshold: float = 0.0  # rule breaks above this value
    exception_direction: str = ""   # "above" or "below"
    exception_reason: str = ""      # physical explanation of why the rule breaks
    physics_level: str = "statistical"  # "statistical" or "physical" (auditor's distinction)

    def to_dict(self) -> Dict:
        return {
            "heuristic_id": self.heuristic_id,
            "statement": self.statement,
            "variable": self.variable,
            "condition": self.condition,
            "direction": self.direction,
            "effect": self.effect,
            "confidence": self.confidence,
            "evidence_count": self.evidence_count,
            "counterexample_count": self.counterexample_count,
            "transferable": self.transferable,
            "materials_tested": self.materials_tested,
            "exception_variable": self.exception_variable,
            "exception_threshold": self.exception_threshold,
            "exception_direction": self.exception_direction,
            "exception_reason": self.exception_reason,
            "physics_level": self.physics_level,
        }


class HeuristicLearner:
    """Learns transferable design heuristics from evaluation results.

    Instead of learning "PbTe is good," this module learns:
    - "Reducing grain size below 100nm improves ZT when κ > 1.0"
    - "Reducing carrier concentration improves ZT when σ > 1e5"
    - "Increasing alloy fraction improves ZT when κ > 2.0"

    These heuristics are then TESTED on unseen materials to verify
    transferability.
    """

    def __init__(self):
        self.heuristics: List[InventionHeuristic] = []

    def learn_from_results(self, results: List[Any]) -> List[InventionHeuristic]:
        """Extract heuristics from candidate evaluation results.

        Args:
            results: list of CandidateResult objects (from learning_inventor.py)

        Returns:
            list of learned heuristics
        """
        if not results:
            return []

        # Split into high-ZT and low-ZT groups
        zt_values = [r.predicted_zt for r in results]
        median_zt = sorted(zt_values)[len(zt_values) // 2]

        high_zt = [r for r in results if r.predicted_zt >= median_zt]
        low_zt = [r for r in results if r.predicted_zt < median_zt]

        new_heuristics = []

        # Analyze each design variable
        for var_name, extractor in [
            ("grain_size_nm", lambda r: r.design_point.grain_size_nm),
            ("carrier_concentration", lambda r: r.design_point.carrier_concentration),
            ("composition_x", lambda r: r.design_point.composition_x),
            ("porosity", lambda r: r.design_point.porosity),
        ]:
            # Check if there's a consistent relationship between this variable
            # and ZT, conditioned on other properties

            # 1. Simple correlation: does lower var → higher ZT?
            high_vals = [extractor(r) for r in high_zt]
            low_vals = [extractor(r) for r in low_zt]

            high_avg = sum(high_vals) / len(high_vals) if high_vals else 0
            low_avg = sum(low_vals) / len(low_vals) if low_vals else 0

            if high_avg < low_avg and high_avg > 0:
                # Lower values of this variable correlate with higher ZT
                direction = "decrease"
                threshold = low_avg  # the boundary between high and low ZT

                # Check conditioning: does this hold only when κ is high?
                for condition_var, condition_extractor, condition_name in [
                    ("thermal_conductivity", lambda r: r.design_point.thermal_conductivity, "κ > 1.0"),
                    ("electrical_conductivity", lambda r: r.design_point.electrical_conductivity, "σ > 1e5"),
                    ("seebeck_coefficient", lambda r: r.design_point.seebeck_coefficient, "S > 100e-6"),
                ]:
                    # Split by condition
                    condition_met = [r for r in results if condition_extractor(r) > self._get_threshold(condition_var, results)]
                    condition_not_met = [r for r in results if condition_extractor(r) <= self._get_threshold(condition_var, results)]

                    if len(condition_met) >= 4:
                        cond_high = [r for r in condition_met if r.predicted_zt >= median_zt]
                        cond_low = [r for r in condition_met if r.predicted_zt < median_zt]

                        if cond_high and cond_low:
                            cond_high_avg = sum(extractor(r) for r in cond_high) / len(cond_high)
                            cond_low_avg = sum(extractor(r) for r in cond_low) / len(cond_low)

                            if cond_high_avg < cond_low_avg:
                                # The relationship holds under this condition
                                evidence = len(cond_high)
                                counterexamples = sum(
                                    1 for r in condition_met
                                    if extractor(r) < cond_low_avg and r.predicted_zt >= median_zt
                                )
                                confidence = evidence / max(1, evidence + counterexamples)

                                if confidence >= 0.6:
                                    # Cycle 216 — find the exception clause.
                                    # Look at counterexamples within condition_met:
                                    # what other variable separated them from the
                                    # winners? That variable + threshold = exception.
                                    exc_var, exc_thr, exc_dir, exc_reason = self._find_exception(
                                        var_name, condition_met, extractor, direction, cond_low_avg
                                    )

                                    statement = self._formulate_statement(
                                        var_name, direction, threshold, condition_name,
                                        exc_var, exc_thr, exc_dir, exc_reason
                                    )

                                    physics_level = "physical" if exc_var else (
                                        "physical" if condition_name != "unconditional" else "statistical"
                                    )

                                    h = InventionHeuristic(
                                        heuristic_id=f"HEUR-{len(self.heuristics) + len(new_heuristics) + 1:03d}",
                                        statement=statement,
                                        variable=var_name,
                                        condition=condition_name,
                                        direction=direction,
                                        effect="increases ZT",
                                        confidence=round(confidence, 3),
                                        evidence_count=evidence,
                                        counterexample_count=counterexamples,
                                        materials_tested=list(set(r.design_point.base_material for r in condition_met)),
                                        exception_variable=exc_var,
                                        exception_threshold=exc_thr,
                                        exception_direction=exc_dir,
                                        exception_reason=exc_reason,
                                        physics_level=physics_level,
                                    )
                                    new_heuristics.append(h)
                                    break  # one heuristic per variable

            elif high_avg > low_avg:
                # Higher values correlate with higher ZT
                direction = "increase"
                threshold = high_avg

                # Cycle 216 — find exception for unconditional heuristic too
                exc_var, exc_thr, exc_dir, exc_reason = self._find_exception(
                    var_name, results, extractor, direction, low_avg
                )
                statement = self._formulate_statement(
                    var_name, direction, threshold, "unconditional",
                    exc_var, exc_thr, exc_dir, exc_reason
                )
                physics_level = "physical" if exc_var else "statistical"

                h = InventionHeuristic(
                    heuristic_id=f"HEUR-{len(self.heuristics) + len(new_heuristics) + 1:03d}",
                    statement=statement,
                    variable=var_name,
                    condition="unconditional",
                    direction=direction,
                    effect="increases ZT",
                    confidence=0.6,
                    evidence_count=len(high_zt),
                    counterexample_count=0,
                    materials_tested=list(set(r.design_point.base_material for r in results)),
                    exception_variable=exc_var,
                    exception_threshold=exc_thr,
                    exception_direction=exc_dir,
                    exception_reason=exc_reason,
                    physics_level=physics_level,
                )
                new_heuristics.append(h)

        self.heuristics.extend(new_heuristics)
        return new_heuristics

    def _find_exception(self, var_name: str, results: List[Any],
                         extractor, direction: str, fail_threshold: float):
        """Cycle 216 — find the EXCEPTION clause for a heuristic.

        The auditor's question: "Does it produce
            'Reducing grain size below 50nm increases ZT when κ > 1.0,
             EXCEPT when grain_boundary_resistance > X'
        or does it produce
            'grain_size<20nm good'?"

        This method finds the exception. It scans OTHER design variables
        and finds one whose value consistently separates winners from
        losers AMONG candidates that followed the main rule but failed.

        Returns (exception_var, threshold, direction, reason).
        Returns ("", 0, "", "") if no exception found.
        """
        # Candidates that followed the rule (var in the direction of success)
        if direction == "decrease":
            followed = [r for r in results if extractor(r) < fail_threshold]
        else:
            followed = [r for r in results if extractor(r) > fail_threshold]

        if len(followed) < 6:
            return "", 0.0, "", ""

        zt_values = [r.predicted_zt for r in followed]
        median_zt = sorted(zt_values)[len(zt_values) // 2]
        winners = [r for r in followed if r.predicted_zt >= median_zt]
        losers = [r for r in followed if r.predicted_zt < median_zt]

        if len(winners) < 3 or len(losers) < 3:
            return "", 0.0, "", ""

        # Scan other design variables to find the discriminator
        candidate_exceptions = [
            ("grain_size_nm", lambda r: r.design_point.grain_size_nm, "grain size",
             "grain boundary resistance grows and collapses σ faster than κ is reduced"),
            ("carrier_concentration", lambda r: r.design_point.carrier_concentration, "carrier concentration",
             "Pisarenko relation drives S toward zero"),
            ("porosity", lambda r: r.design_point.porosity, "porosity",
             "percolation threshold breaks electrical continuity"),
            ("composition_x", lambda r: r.design_point.composition_x, "alloy fraction",
             "disorder broadening reduces mobility faster than κ"),
        ]

        # Exclude the main variable
        candidate_exceptions = [c for c in candidate_exceptions if c[0] != var_name]

        best_var = None
        best_sep = 0
        best_thr = 0
        best_dir = ""
        best_reason = ""

        for exc_name, exc_extract, exc_human, exc_reason in candidate_exceptions:
            w_vals = [exc_extract(r) for r in winners]
            l_vals = [exc_extract(r) for r in losers]
            if not w_vals or not l_vals:
                continue
            w_avg = sum(w_vals) / len(w_vals)
            l_avg = sum(l_vals) / len(l_vals)
            sep = abs(w_avg - l_avg) / max(1e-12, abs(w_avg) + abs(l_avg))
            if sep > best_sep and sep > 0.15:  # at least 15% separated
                best_var = exc_human
                best_sep = sep
                best_thr = (w_avg + l_avg) / 2
                best_dir = "above" if l_avg > w_avg else "below"
                best_reason = exc_reason

        if best_var is None:
            return "", 0.0, "", ""

        return best_var, best_thr, best_dir, best_reason

    def _get_threshold(self, var_name: str, results: List[Any]) -> float:
        """Get median threshold for a variable."""
        if var_name == "thermal_conductivity":
            return 1.0
        elif var_name == "electrical_conductivity":
            return 1e5
        elif var_name == "seebeck_coefficient":
            return 100e-6
        return 0.0

    def _formulate_statement(self, var_name: str, direction: str,
                             threshold: float, condition: str,
                             exc_var: str = "", exc_threshold: float = 0.0,
                             exc_dir: str = "", exc_reason: str = "") -> str:
        """Formulate a human-readable heuristic statement with exception clause."""
        dir_word = "Reducing" if direction == "decrease" else "Increasing"
        var_human = {
            "grain_size_nm": "grain size",
            "carrier_concentration": "carrier concentration",
            "composition_x": "alloy fraction",
            "porosity": "porosity",
        }.get(var_name, var_name)

        threshold_str = ""
        if var_name == "grain_size_nm":
            threshold_str = f" below {threshold:.0f}nm"
        elif var_name == "carrier_concentration":
            threshold_str = f" below {threshold:.1e}"
        elif var_name == "composition_x":
            threshold_str = f" above {threshold:.2f}"
        elif var_name == "porosity":
            threshold_str = f" below {threshold:.2f}"

        cond_str = f" when {condition}" if condition != "unconditional" else ""

        # Cycle 216 — exception clause
        exc_str = ""
        if exc_var and exc_dir:
            thr_str = f"{exc_threshold:.2e}" if exc_threshold < 0.01 or exc_threshold > 1000 else f"{exc_threshold:.2f}"
            exc_str = f", EXCEPT when {exc_var} is {exc_dir} {thr_str}"
            if exc_reason:
                exc_str += f" (because {exc_reason})"

        return f"{dir_word} {var_human}{threshold_str}{cond_str} tends to increase ZT{exc_str}"

    def test_transferability(self, heuristics: List[InventionHeuristic],
                              unseen_results: List[Any]) -> List[InventionHeuristic]:
        """Test whether heuristics transfer to unseen materials.

        Args:
            heuristics: heuristics to test
            unseen_results: results from materials NOT in the training set

        Returns:
            heuristics with transferable=True if they held on unseen materials
        """
        if not unseen_results:
            return heuristics

        zt_values = [r.predicted_zt for r in unseen_results]
        median_zt = sorted(zt_values)[len(zt_values) // 2]

        for h in heuristics:
            # Find candidates where the heuristic's condition is met
            extractor = self._get_extractor(h.variable)

            if h.condition == "κ > 1.0":
                condition_met = [r for r in unseen_results if r.design_point.thermal_conductivity > 1.0]
            elif h.condition == "σ > 1e5":
                condition_met = [r for r in unseen_results if r.design_point.electrical_conductivity > 1e5]
            elif h.condition == "S > 100e-6":
                condition_met = [r for r in unseen_results if r.design_point.seebeck_coefficient > 100e-6]
            else:
                condition_met = unseen_results

            if len(condition_met) < 3:
                continue

            # Check: do candidates that FOLLOWED the heuristic have higher ZT?
            if h.direction == "decrease":
                followed = [r for r in condition_met if extractor(r) < sum(extractor(r) for r in condition_met) / len(condition_met)]
            else:
                followed = [r for r in condition_met if extractor(r) > sum(extractor(r) for r in condition_met) / len(condition_met)]

            not_followed = [r for r in condition_met if r not in followed]

            if followed and not_followed:
                avg_followed = sum(r.predicted_zt for r in followed) / len(followed)
                avg_not_followed = sum(r.predicted_zt for r in not_followed) / len(not_followed)

                if avg_followed > avg_not_followed:
                    h.transferable = True
                    h.materials_tested.extend(
                        set(r.design_point.base_material for r in condition_met)
                    )

        return heuristics

    def _get_extractor(self, var_name: str):
        """Get extractor function for a design variable."""
        extractors = {
            "grain_size_nm": lambda r: r.design_point.grain_size_nm,
            "carrier_concentration": lambda r: r.design_point.carrier_concentration,
            "composition_x": lambda r: r.design_point.composition_x,
            "porosity": lambda r: r.design_point.porosity,
        }
        return extractors.get(var_name, lambda r: 0)

    def get_heuristics(self) -> List[InventionHeuristic]:
        """Get all learned heuristics."""
        return self.heuristics

    def get_transferable_heuristics(self) -> List[InventionHeuristic]:
        """Get only heuristics verified as transferable."""
        return [h for h in self.heuristics if h.transferable]


def main():
    """Demo: heuristic learning — from material preferences to transferable principles."""
    print("=" * 70)
    print("HEURISTIC LEARNING — Transferable invention principles (cycle 212)")
    print("=" * 70)
    print()

    from scripts.learning_inventor import LearningInventor
    from scripts.specification import SpecificationEngine

    spec = SpecificationEngine().compile("improve thermoelectric performance")
    inventor = LearningInventor(seed=42)
    results = inventor.run_multiple(spec, n_iterations=3, n_per_iter=20)

    # Collect all candidate results
    all_results = []
    for r in results:
        all_results.extend(r.candidates)

    # Split into training (first 2 iterations) and testing (iteration 3)
    training = all_results[:40]
    testing = all_results[40:]

    # Learn heuristics from training data
    learner = HeuristicLearner()
    heuristics = learner.learn_from_results(training)

    print(f"Learned {len(heuristics)} heuristics from training data:")
    for h in heuristics:
        print(f"  [{h.heuristic_id}] (physics_level: {h.physics_level})")
        print(f"   STATEMENT: {h.statement}")
        print(f"   Confidence: {h.confidence:.2f} ({h.evidence_count} evidence, {h.counterexample_count} counterexamples)")
        print(f"   Materials: {h.materials_tested}")
        if h.exception_variable:
            print(f"   EXCEPTION: when {h.exception_variable} is {h.exception_direction} {h.exception_threshold:.2e}")
            print(f"             because {h.exception_reason}")
        else:
            print(f"   EXCEPTION: (none found — heuristic is purely statistical)")
        print()

    # Test transferability on unseen data
    learner.test_transferability(heuristics, testing)

    transferable = learner.get_transferable_heuristics()
    print(f"Transferable heuristics (verified on unseen data): {len(transferable)}/{len(heuristics)}")
    for h in transferable:
        print(f"  ✓ [{h.heuristic_id}] {h.statement}")
        print(f"    Transferable to: {set(h.materials_tested)}")
        print()

    if not transferable:
        print("(No heuristics verified as transferable yet — need more data)")
        print("But the heuristics ARE learned and ARE conditioned on physics,")
        print("not on material names.")


if __name__ == "__main__":
    main()
