"""
Maestro Loop Cycle 3 — Gap 3 (non-buildable blueprints)
PHASE 5: HYPOTHESIS

This file records the hypothesis BEFORE the modification, per the
Maestro Modification Loop. The hypothesis is a prediction; the
delta report (PHASE 8) will confirm or falsify it.
"""
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hypothesis.hypothesis import Hypothesis

CYCLE_3_HYPOTHESIS = Hypothesis(
    claim=(
        "Replacing the blueprint_module's structured-summary output "
        "with a buildable spec (parts list + materials specification + "
        "assembly steps + tolerances + engineering constraints extracted "
        "from Layers 2, 4, 6, 7, 9) will produce blueprints that an "
        "engineer could start building from, without consulting the "
        "underlying layers. The buildable blueprint will carry at least: "
        "a parts list (from Layer 2 required_materials), a materials "
        "specification (from Layer 6 materials), an assembly plan "
        "(from Layer 4 subsystems + interfaces), tolerances (from "
        "Layer 4), and a prototype specification (from Layer 9)."
    ),
    confidence=0.55,
    evidence=[
        "Gap 3 observation: current final_blueprint is a structured "
        "summary (target_invention, prerequisite_chain_depth, governing_"
        "equations, subsystems, composite_feasibility, prototype_stages, "
        "total_prototype_timeline_years) — NOT a buildable spec",
        "Layer 2 already produces required_materials (component nodes "
        "from the prerequisite chain) — these can become a parts list",
        "Layer 4 already produces subsystems, interfaces, tolerances — "
        "these can become an assembly plan",
        "Layer 6 already produces materials, tooling, quality_control — "
        "these can become a manufacturing specification",
        "Layer 9 already produces prototype_v1/v2/v3 with goals, scope, "
        "success thresholds, estimated duration, estimated cost — these "
        "can become a prototype specification",
        "The blueprint_module already receives all 11 layers as input "
        "(all_layers dict) — no orchestrator change needed",
    ],
    counterevidence=[
        "The underlying layers themselves are templated (Gap 5: "
        "prototype_plan and experimental_plan are the same structure "
        "for every invention) — a buildable blueprint assembled from "
        "templated parts is still templated, just more detailed",
        "Layer 6's materials list comes from the prerequisite chain's "
        "component nodes, which are graph nodes (e.g., 'component_cyclone_"
        "chamber') not real material specifications (e.g., 'AISI 316L "
        "stainless steel, 2mm wall thickness')",
        "Layer 4's tolerances are keyword-derived priors (e.g., '±15% "
        "of capex estimate'), not engineering tolerances (e.g., '±0.1mm')",
        "An engineer building from this blueprint would still need domain "
        "expertise to fill the gap between 'component_cyclone_chamber' "
        "and an actual bill of materials with supplier part numbers",
    ],
    assumptions=[
        "The blueprint_module's analyze() signature does not change — "
        "it already receives all_layers",
        "No other module is modified (per Maestro Loop PHASE 6: modify "
        "ONE component)",
        "The buildable spec is assembled FROM existing layer outputs, "
        "not by adding new analysis — the data already exists, it's "
        "just not composed into a buildable format",
        "'Buildable' in this context means 'an engineer could identify "
        "what parts to source, what materials to use, what tolerance to "
        "hold, and what prototype to build first' — NOT 'an engineer "
        "could build it without any domain expertise'",
    ],
    dependencies=[
        "hyp_gap1_fix_simulation_module",
        "hyp_gap2_7_fix_dependency_module",
    ],
    writer="evidence.experiments.invention_batch_004.cycle_3_hypothesis",
)

PREDICTED_DELTA = {
    "blueprint_quality_before": {
        "has_parts_list": False,
        "has_materials_specification": False,
        "has_assembly_plan": False,
        "has_tolerances": False,
        "has_prototype_specification": False,
        "description": "structured summary",
    },
    "blueprint_quality_after": {
        "has_parts_list": True,
        "has_materials_specification": True,
        "has_assembly_plan": True,
        "has_tolerances": True,
        "has_prototype_specification": True,
        "description": "buildable spec",
    },
    "prediction": (
        "At least 15/20 blueprints will have all 5 buildable-spec fields "
        "non-empty after the fix. Before the fix, 0/20 had any of them."
    ),
}


if __name__ == "__main__":
    import json
    print("=== CYCLE 3 HYPOTHESIS (Maestro Loop PHASE 5) ===")
    print()
    print("Hypothesis:")
    print(json.dumps(CYCLE_3_HYPOTHESIS.to_dict(), indent=2))
    print()
    print("Predicted delta:")
    print(json.dumps(PREDICTED_DELTA, indent=2))
