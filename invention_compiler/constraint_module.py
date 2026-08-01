"""
Constraint Module — feeds Layer 3 (assumptions, failure_modes,
optimization_targets) AND Layer 4 (tolerances) AND Layer 6 (materials,
suppliers, tooling, quality_control).

This is the cross-cutting engine: it appears in multiple layers because
constraints propagate through every layer of the compiler. The engine
is split into three methods, one per layer it feeds.
"""
from typing import Dict, Any, List


class ConstraintModule:
    """Aggregates constraints from the prerequisite chain and proposes
    failure modes, tolerances, and manufacturing constraints."""

    # Map: constraint keyword -> likely failure mode if violated.
    FAILURE_MODE_PRIORS = {
        "cost": "cost_overrun",
        "energy": "energy_budget_exceeded",
        "material": "material_unavailable_or_too_expensive",
        "regulation": "regulatory_rejection",
        "manufacturing": "manufacturing_yield_too_low",
        "supply_chain": "supply_chain_disruption",
        "time": "schedule_slippage",
        "information": "information_asymmetry",
        "safety": "safety_incident",
        "maintenance": "maintenance_burden_too_high",
    }

    # Map: constraint keyword -> typical tolerance range.
    TOLERANCE_PRIORS = {
        "cost": "±15% of capex estimate",
        "energy": "±10% of energy budget",
        "material": "±5% of material property target",
        "regulation": "binary (pass/fail)",
        "manufacturing": "±3% yield",
        "supply_chain": "±30% lead time",
        "time": "±20% schedule",
        "information": "information completeness >= 95%",
        "safety": "zero incidents",
        "maintenance": "MTBF >= target",
    }

    def __init__(self, graph: Dict[str, Any]):
        self.graph = graph

    def analyze_layer3(self, problem: Dict[str, Any],
                        dependency_output: Dict[str, Any],
                        physics_output: Dict[str, Any]) -> Dict[str, Any]:
        """Layer 3: failure modes + optimization targets + assumptions."""
        # Aggregate all constraints from prerequisites.
        all_constraints = []
        for p in dependency_output.get("prerequisites", []):
            for c in (p.get("constraints") or []):
                all_constraints.append(str(c).lower())
        # Plus the problem's own constraints.
        for c in problem.get("constraints", []):
            all_constraints.append(str(c).lower())

        # Failure modes: derive from constraint keywords.
        failure_modes = []
        for c in all_constraints:
            for kw, fm in self.FAILURE_MODE_PRIORS.items():
                if kw in c and fm not in failure_modes:
                    failure_modes.append(fm)

        # Optimization targets: the problem's stated constraints ARE
        # the optimization targets (maximize feasibility, minimize cost).
        opt_targets = []
        for c in problem.get("constraints", []):
            cl = str(c).lower()
            if "cost" in cl:
                opt_targets.append("minimize_cost")
            if "weight" in cl:
                opt_targets.append("minimize_weight")
            if "power" in cl or "energy" in cl:
                opt_targets.append("minimize_energy")
            if "time" in cl:
                opt_targets.append("minimize_time_to_market")
            if "regulation" in cl or "safety" in cl:
                opt_targets.append("maximize_safety_margin")
        if not opt_targets:
            opt_targets = ["maximize_composite_feasibility"]

        # Assumptions: explicit statement of what we're assuming.
        assumptions = [
            "Failure modes are derived from constraint keywords via a "
            "small prior map. Real failure modes require FMEA.",
            "Optimization targets are derived from the problem's stated "
            "constraints. Implicit targets (e.g., 'minimize complexity') "
            "are not captured.",
        ]

        return {
            "failure_modes": failure_modes,
            "optimization_targets": opt_targets,
            "assumptions": assumptions,
            "evidence": {
                "constraints_aggregated": all_constraints,
                "constraint_count": len(all_constraints),
                "failure_mode_count": len(failure_modes),
            },
            "falsification_criteria": (
                "If an FMEA on the candidate invention surfaces a failure "
                "mode not in this engine's output, the failure-mode prior "
                "map is incomplete."
            ),
        }

    def analyze_layer4(self, problem: Dict[str, Any],
                        constraint_layer3: Dict[str, Any]) -> Dict[str, Any]:
        """Layer 4: tolerances + subsystems."""
        constraints = constraint_layer3.get("evidence", {}).get(
            "constraints_aggregated", [])
        tolerances = {}
        for c in constraints:
            for kw, tol in self.TOLERANCE_PRIORS.items():
                if kw in c and kw not in tolerances:
                    tolerances[kw] = tol
        # Subsystems: derived from the prerequisite chain's component
        # nodes — each component is a candidate subsystem.
        return {
            "tolerances": tolerances,
            "subsystems_provisional": [
                f"subsystem_for_{kw}" for kw in tolerances.keys()
            ],
            "evidence": {
                "constraint_count": len(constraints),
                "tolerance_count": len(tolerances),
            },
            "assumptions": [
                "Tolerances are derived from a constraint-keyword prior map. "
                "Real tolerances require detailed engineering analysis.",
                "Subsystems are provisionally named after the constraints "
                "they manage. This is a placeholder for a real "
                "architecture decomposition.",
            ],
            "falsification_criteria": (
                "If a real tolerance analysis disagrees with these values "
                "by more than 2x, the prior map is wrong."
            ),
        }

    def analyze_layer6(self, problem: Dict[str, Any],
                        dependency_output: Dict[str, Any]) -> Dict[str, Any]:
        """Layer 6: manufacturing layer (materials, suppliers, tooling,
        assembly, quality_control, scaling_constraints)."""
        # Materials: from the dependency chain's component nodes.
        materials = []
        for p in dependency_output.get("prerequisites", []):
            if p.get("type") == "component":
                materials.append({
                    "id": p["id"],
                    "label": p.get("label"),
                    "constraints": p.get("constraints", []),
                })

        # Suppliers: not in the graph. We mark this honestly.
        suppliers = "NOT_IN_GRAPH — supplier data requires external integration"

        # Tooling: inferred from constraint types.
        constraints = []
        for p in dependency_output.get("prerequisites", []):
            for c in (p.get("constraints") or []):
                constraints.append(str(c).lower())
        tooling = []
        for c in set(constraints):
            for kw, _fm in self.FAILURE_MODE_PRIORS.items():
                if kw in c and f"tooling_for_{kw}" not in tooling:
                    tooling.append(f"tooling_for_{kw}")
                    break

        # Quality control: derived from constraint keywords.
        qc = []
        if any("safety" in c for c in constraints):
            qc.append("safety_certification")
        if any("manufacturing" in c for c in constraints):
            qc.append("yield_monitoring")
        if any("material" in c for c in constraints):
            qc.append("material_property_verification")
        if not qc:
            qc.append("functional_test")

        # Scaling constraints: hard limits from the constraint set.
        scaling = []
        if any("manufacturing" in c for c in constraints):
            scaling.append("manufacturing_throughput_ceiling")
        if any("supply_chain" in c for c in constraints):
            scaling.append("supply_chain_lead_time")
        if any("regulation" in c for c in constraints):
            scaling.append("regulatory_approval_per_facility")

        return {
            "materials": materials,
            "suppliers": suppliers,
            "tooling": tooling,
            "assembly": "modular_assembly_assumed" if len(materials) > 3
                        else "integrated_assembly_assumed",
            "quality_control": qc,
            "scaling_constraints": scaling,
            "evidence": {
                "material_count": len(materials),
                "tooling_count": len(tooling),
                "constraint_count": len(constraints),
            },
            "assumptions": [
                "Supplier data is NOT in the civilization graph. This "
                "engine flags the gap honestly rather than fabricating "
                "supplier names.",
                "Assembly strategy is inferred from component count. Real "
                "assembly decisions require DFM analysis.",
            ],
            "falsification_criteria": (
                "If a real manufacturing analysis surfaces materials, "
                "tooling, or scaling constraints not in this engine's "
                "output, the prior maps are incomplete or the graph has "
                "a coverage gap."
            ),
        }
