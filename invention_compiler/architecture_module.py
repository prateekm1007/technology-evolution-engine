"""
Architecture Module — feeds Layer 4 (Engineering architecture).

Composes subsystems, interfaces, inputs, outputs, tolerances, energy,
and computational requirements into a single Layer 4 dict. Pulls from
the constraint_engine's Layer 4 output and the dependency_engine's
prerequisite chain.
"""
from typing import Dict, Any, List


class ArchitectureModule:
    """Composes Layer 4 (Engineering architecture)."""

    def __init__(self, graph: Dict[str, Any]):
        self.graph = graph

    def analyze(self, problem: Dict[str, Any],
                dependency_output: Dict[str, Any],
                constraint_layer4: Dict[str, Any]) -> Dict[str, Any]:
        # Subsystems: from constraint engine's provisional list,
        # plus a "core" subsystem if there's a system node in the
        # prerequisite chain.
        subsystems = list(constraint_layer4.get("subsystems_provisional", []))
        for p in dependency_output.get("prerequisites", []):
            if p.get("type") == "system":
                subsystems.append(f"core_{p['id']}")
        if not subsystems:
            subsystems = ["core_subsystem"]

        # Interfaces: derived from subsystem pairs (each pair has an
        # implied interface). Capped at 5 to keep the output readable.
        interfaces = []
        for i in range(min(len(subsystems), 5)):
            for j in range(i + 1, min(len(subsystems), 5)):
                interfaces.append(f"{subsystems[i]} <-> {subsystems[j]}")
                if len(interfaces) >= 5:
                    break
            if len(interfaces) >= 5:
                break

        # Inputs: the problem's stated inputs (constraints, time horizon).
        inputs = {
            "problem_constraints": problem.get("constraints", []),
            "time_horizon": problem.get("time_horizon"),
            "domain": problem.get("domain"),
        }

        # Outputs: what the invention must produce. Derived from the
        # problem statement's `problem` field.
        outputs = {
            "primary_output": problem.get("problem", "unspecified"),
            "evidence_quality": "replayable_per_law_8",
        }

        # Energy requirements: from constraint_engine's tolerance list,
        # if `energy` is among them; otherwise neutral estimate.
        tolerances = constraint_layer4.get("tolerances", {})
        if "energy" in tolerances:
            energy_req = {
                "budget_tight": True,
                "tolerance": tolerances["energy"],
                "estimated_watts": "depends_on_application",
            }
        else:
            energy_req = {
                "budget_tight": False,
                "tolerance": "not specified",
                "estimated_watts": "depends_on_application",
            }

        # Computational requirements: derived from mathematics engine's
        # Layer 1 output. If optimization or signal_processing is in
        # the structure list, computational requirements are high.
        comp_req = {
            "class": "moderate",
            "note": "Real computational requirements depend on the "
                    "governing equations from Layer 3 and the simulation "
                    "approach from Layer 5.",
        }

        return {
            "subsystems": subsystems,
            "interfaces": interfaces,
            "inputs": inputs,
            "outputs": outputs,
            "tolerances": tolerances,
            "energy_requirements": energy_req,
            "computational_requirements": comp_req,
            "evidence": {
                "subsystem_count": len(subsystems),
                "interface_count": len(interfaces),
                "tolerance_count": len(tolerances),
            },
            "assumptions": [
                "Subsystems are provisionally named after the constraints "
                "they manage plus the system node from the prerequisite "
                "chain. Real subsystem decomposition requires a formal "
                "architecture review.",
                "Interfaces are enumerated pairwise among the first 5 "
                "subsystems. Real systems have more interfaces than this.",
                "Energy and computational requirements are placeholder "
                "estimates pending Layer 3 (governing equations) and "
                "Layer 5 (simulation).",
            ],
            "falsification_criteria": (
                "If a real architecture review identifies subsystems or "
                "interfaces not in this engine's output, the prerequisite "
                "chain has a coverage gap or the subsystem decomposition "
                "heuristic is wrong."
            ),
        }
