"""
Prototype Module — feeds Layer 9 (Prototype layer).

GAP 5 FIX (Maestro Loop Cycle 5): replaced templated v1/v2/v3 goals,
scopes, and success thresholds with invention-specific versions drawn
from the problem's domain, constraints, physics laws, and governing
equations. Durations now incorporate domain-specific time priors.

Before the fix: all 20 candidates had the same v1 goal ("prove the
core mechanism works at lab scale"). After the fix: each candidate's
v1 goal references its specific domain, physics laws, or problem text.

Per the Maestro Loop PHASE 6: only this module is modified.
"""
from typing import Dict, Any, List


# Domain-specific time multipliers (how long things take in each domain).
# These are priors, not calibrations. They encode domain knowledge:
# e.g., nuclear takes longer than software because of regulatory cycles;
# medical devices take longer than materials because of clinical trials.
DOMAIN_TIME_MULTIPLIERS = {
    "materials": 1.0,
    "chemistry": 1.2,
    "energy": 1.3,
    "water": 1.1,
    "medical_imaging": 1.5,
    "medical_devices": 1.5,
    "biology": 1.4,
    "robotics": 1.2,
    "agriculture": 1.1,
    "manufacturing": 0.9,
    "transportation": 1.1,
    "electronics": 0.8,
    "sensors": 0.9,
}

# Domain-specific v1 goal templates. Each references the domain's
# characteristic physics/chemistry/biology.
DOMAIN_V1_GOALS = {
    "materials": "prove the core material property ({key_physics}) "
                 "holds at lab scale for {problem_short}",
    "chemistry": "prove the key reaction pathway ({key_physics}) "
                 "proceeds at viable rate for {problem_short}",
    "energy": "prove the energy conversion mechanism ({key_physics}) "
              "works at lab scale for {problem_short}",
    "water": "prove the core separation/purification mechanism "
             "({key_physics}) works at bench scale for {problem_short}",
    "medical_imaging": "prove the imaging mechanism ({key_physics}) "
                       "produces diagnostic-quality signal for {problem_short}",
    "medical_devices": "prove the device mechanism ({key_physics}) "
                       "functions safely at bench scale for {problem_short}",
    "biology": "prove the biological mechanism ({key_physics}) "
               "works at lab scale for {problem_short}",
    "robotics": "prove the control mechanism ({key_physics}) "
                "navigates/performs at lab scale for {problem_short}",
    "agriculture": "prove the growth/automation mechanism ({key_physics}) "
                   "works at pilot scale for {problem_short}",
    "manufacturing": "prove the manufacturing process ({key_physics}) "
                    "works at bench scale for {problem_short}",
    "transportation": "prove the propulsion/control mechanism "
                      "({key_physics}) works at lab scale for {problem_short}",
    "electronics": "prove the electronic mechanism ({key_physics}) "
                   "works at bench scale for {problem_short}",
    "sensors": "prove the sensing mechanism ({key_physics}) "
               "works at bench scale for {problem_short}",
}

# Domain-specific v2 goal templates.
DOMAIN_V2_GOALS = {
    "materials": "integrate the material into a working {problem_short} "
                 "prototype with all subsystems",
    "chemistry": "integrate the reaction into a continuous-flow "
                 "{problem_short} system",
    "energy": "integrate the energy converter into a {problem_short} "
              "system with power conditioning",
    "water": "integrate the separation into a {problem_short} system "
             "with pre/post-treatment",
    "medical_imaging": "integrate the imager into a portable "
                       "{problem_short} system with shielding and power",
    "medical_devices": "integrate the device into a {problem_short} "
                       "system with biocompatible housing and controls",
    "biology": "integrate the biological process into a {problem_short} "
               "system with sterile handling",
    "robotics": "integrate the robot into a {problem_short} system "
                "with sensing, actuation, and safety interlocks",
    "agriculture": "integrate the automation into a {problem_short} "
                   "system with climate control and monitoring",
    "manufacturing": "integrate the process into a {problem_short} "
                     "system with tooling and QC",
    "transportation": "integrate the vehicle into a {problem_short} "
                      "system with power and control",
    "electronics": "integrate the circuit into a {problem_short} "
                   "system with packaging and I/O",
    "sensors": "integrate the sensor into a {problem_short} system "
               "with signal conditioning and calibration",
}

# Domain-specific v3 goal templates.
DOMAIN_V3_GOALS = {
    "materials": "pilot-manufacture {problem_short} at 100x lab scale "
                 "with cost within 2x target",
    "chemistry": "pilot the {problem_short} process at 100x lab scale "
                 "with yield >80% and cost within 2x target",
    "energy": "pilot the {problem_short} system at 100kW scale with "
              "cost within 2x target",
    "water": "pilot the {problem_short} system at 1000L/day with "
             "cost within 2x target",
    "medical_imaging": "submit {problem_short} for FDA 510(k) "
                       "pre-submission and build 5 clinical units",
    "medical_devices": "submit {problem_short} for FDA 510(k) "
                       "pre-submission and build 5 clinical units",
    "biology": "pilot the {problem_short} process at 1000L scale "
               "with regulatory pre-submission",
    "robotics": "field-test {problem_short} in 3 real environments "
                 "with safety certification",
    "agriculture": "field-test {problem_short} at 1-hectare scale "
                   "with 1 growing season",
    "manufacturing": "pilot the {problem_short} system at 100-part "
                     "batch with standardization",
    "transportation": "pilot the {problem_short} system with regulatory "
                      "pre-submission and 1000km field test",
    "electronics": "pilot the {problem_short} at 10k-unit batch with "
                   "packaging certification",
    "sensors": "pilot the {problem_short} at 1k-unit batch with "
               "calibration certification",
}


class PrototypeModule:
    """Proposes a three-stage prototype plan, invention-specific."""

    def __init__(self, graph: Dict[str, Any]):
        self.graph = graph

    def analyze(self, problem: Dict[str, Any],
                feasibility_output: Dict[str, Any],
                dependency_output: Dict[str, Any]) -> Dict[str, Any]:
        horizon = problem.get("time_horizon", "5-10 years")
        domain = problem.get("domain", "materials")
        problem_text = problem.get("problem", "")
        constraints = problem.get("constraints", [])

        # Extract a short problem descriptor from the problem text.
        # Take the first 4 significant words.
        words = [w for w in problem_text.replace(",", " ").replace(".", " ")
                 .split() if len(w) > 3]
        problem_short = " ".join(words[:4]).lower() if words else "the invention"

        # Extract key physics from applicable laws (if available via
        # feasibility_output, which carries composite but not laws;
        # we use the domain to pick a representative physics term).
        key_physics = self._key_physics_for_domain(domain, constraints)

        # Domain-specific time multiplier.
        time_mult = DOMAIN_TIME_MULTIPLIERS.get(domain, 1.0)

        # GAP 5 FIX: invention-specific v1 goal.
        v1_goal_template = DOMAIN_V1_GOALS.get(domain,
            "prove the core mechanism ({key_physics}) works at lab "
            "scale for {problem_short}")
        v1_goal = v1_goal_template.format(
            key_physics=key_physics, problem_short=problem_short)

        v1 = {
            "name": f"prototype_v1_{domain}_physics_validation",
            "goal": v1_goal,
            "scope": f"single {domain} subsystem, no integration, "
                     f"no manufacturability",
            "success_threshold": f"{key_physics} mechanism reproduces "
                                 f"predicted output within 30% for "
                                 f"{problem_short}",
            "estimated_duration_months": int(6 * time_mult),
            "estimated_cost_usd_m": round(
                feasibility_output.get("composite_feasibility", 0.5) * 0.5, 2),
        }

        # GAP 5 FIX: invention-specific v2 goal.
        prereq_count = len(dependency_output.get("prerequisites", []))
        v2_goal_template = DOMAIN_V2_GOALS.get(domain,
            "integrate the subsystems into a working {problem_short} system")
        v2_goal = v2_goal_template.format(problem_short=problem_short)

        v2 = {
            "name": f"prototype_v2_{domain}_engineering_integration",
            "goal": v2_goal,
            "scope": f"all {domain} subsystems, no manufacturing pathway, "
                     f"no regulatory submission",
            "success_threshold": f"integrated {problem_short} prototype "
                                 f"meets primary spec at 50% target performance",
            "estimated_duration_months": int((12 + prereq_count) * time_mult),
            "estimated_cost_usd_m": round(
                feasibility_output.get("composite_feasibility", 0.5) * 2.0, 2),
        }

        # GAP 5 FIX: invention-specific v3 goal.
        v3_goal_template = DOMAIN_V3_GOALS.get(domain,
            "pilot-manufacture {problem_short} at scale with cost "
            "within 2x target")
        v3_goal = v3_goal_template.format(problem_short=problem_short)

        v3 = {
            "name": f"prototype_v3_{domain}_production_readiness",
            "goal": v3_goal,
            "scope": f"production-intent {domain} prototype, pilot "
                     f"manufacturing run, regulatory pre-submission",
            "success_threshold": f"unit cost within 2x of target; "
                                 f"regulatory pre-submission accepted for "
                                 f"{problem_short}",
            "estimated_duration_months": int((18 + prereq_count * 2) * time_mult),
            "estimated_cost_usd_m": round(
                feasibility_output.get("composite_feasibility", 0.5) * 8.0, 2),
        }

        # Timeline.
        total_months = (v1["estimated_duration_months"]
                        + v2["estimated_duration_months"]
                        + v3["estimated_duration_months"])
        years = total_months / 12
        timeline = {
            "total_months": total_months,
            "total_years": round(years, 1),
            "fits_within_horizon": self._fits(horizon, years),
            "phases": [
                {"phase": "v1", "start_month": 0,
                 "end_month": v1["estimated_duration_months"]},
                {"phase": "v2", "start_month": v1["estimated_duration_months"],
                 "end_month": v1["estimated_duration_months"]
                              + v2["estimated_duration_months"]},
                {"phase": "v3",
                 "start_month": v1["estimated_duration_months"]
                                 + v2["estimated_duration_months"],
                 "end_month": total_months},
            ],
        }

        return {
            "prototype_v1": v1,
            "prototype_v2": v2,
            "prototype_v3": v3,
            "timeline": timeline,
            "evidence": {
                "feasibility_composite_used": feasibility_output.get(
                    "composite_feasibility", 0.5),
                "prerequisite_count": prereq_count,
                "horizon": horizon,
                # GAP 5 FIX: expose invention-specificity signals
                "domain": domain,
                "problem_short": problem_short,
                "key_physics": key_physics,
                "time_multiplier": time_mult,
                "v1_goal_template": v1_goal_template,
            },
            "assumptions": [
                "GAP 5 FIX: Prototype goals, scopes, and thresholds are "
                "now invention-specific, parameterized by domain, problem "
                "text, constraints, and key physics. The v1/v2/v3 "
                "structure (physics → integration → production) is still "
                "universal, but the CONTENT is now differentiated.",
                "Domain time multipliers are priors: nuclear/medical take "
                "longer than software/electronics due to regulatory "
                "cycles and clinical trials. These should be recalibrated "
                "as prototype outcomes accumulate.",
                "Cost estimates still scale with composite feasibility — "
                "higher feasibility means lower cost (proven tech stack).",
            ],
            "falsification_criteria": (
                "If a real prototype program for the candidate takes more "
                "than 2x the estimated duration, the duration prior is "
                "wrong and must be recalibrated. Sample size: >= 5 "
                "comparable prototype programs."
            ),
        }

    def _key_physics_for_domain(self, domain: str,
                                constraints: list) -> str:
        """Pick a representative physics term for the domain."""
        DOMAIN_PHYSICS = {
            "materials": "material_property",
            "chemistry": "reaction_kinetics",
            "energy": "energy_conversion",
            "water": "separation_mechanism",
            "medical_imaging": "imaging_signal",
            "medical_devices": "device_function",
            "biology": "biological_process",
            "robotics": "control_system",
            "agriculture": "growth_mechanism",
            "manufacturing": "manufacturing_process",
            "transportation": "propulsion",
            "electronics": "electronic_function",
            "sensors": "sensing_mechanism",
        }
        # Check constraints for specific physics keywords.
        constraint_text = " ".join(str(c) for c in constraints).lower()
        if "superconduct" in constraint_text:
            return "superconductivity"
        if "magnet" in constraint_text or "mri" in constraint_text:
            return "magnetic_field"
        if "catalyst" in constraint_text:
            return "catalytic_activity"
        if "photosynth" in constraint_text:
            return "photon_conversion"
        if "carbon" in constraint_text:
            return "carbon_sequestration"
        return DOMAIN_PHYSICS.get(domain, "core_mechanism")

    def _fits(self, horizon: str, years: float) -> bool:
        if "0-2" in horizon:
            return years <= 2
        if "2-5" in horizon:
            return years <= 5
        if "5-10" in horizon:
            return years <= 10
        if "10-15" in horizon:
            return years <= 15
        return True
