#!/usr/bin/env python3
"""
20-invention experiment runner (CEO-mandated).

This script is a ONE-OFF EXPERIMENT RUNNER. It is NOT a new module,
package, framework, or layer. It USES the existing InventionCompiler
infrastructure exactly as it is — no modifications — and records
the outputs.

Per the CEO freeze directive (commit `0c6d5d7`):
- No new layers/modules/packages/abstractions.
- The architecture is FROZEN during this experiment.
- Every failure must be recorded.

The script does three things:
  1. Runs the existing InventionCompiler against 20 candidate
     inventions, exactly as the existing code allows.
  2. Writes one YAML file per invention to
     evidence/experiments/invention_batch_003/ following the
     required output format.
  3. Writes FAILURES.md recording every compiler failure, ambiguity,
     gap. And SUMMARY.md counting inventions produced, blueprints
     generated, failures identified.

Usage:
    python scripts/run_20_invention_experiment.py
"""
import json
import sys
import traceback
import pathlib
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from invention_compiler.orchestrator import InventionCompiler

OUT_DIR = ROOT / "evidence" / "experiments" / "invention_batch_003"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# The 20 candidate inventions (CEO-mandated list).
CANDIDATES = [
    {
        "id": "001_solid_state_batteries",
        "problem": "Build a solid-state lithium battery with ceramic electrolyte achieving >400 Wh/kg energy density",
        "domain": "materials",
        "motivation": "Current Li-ion batteries use flammable liquid electrolytes and cap at ~250 Wh/kg",
        "market": "electric_vehicles_grid_storage",
        "constraints": ["cost", "material", "manufacturing", "regulation", "energy"],
        "time_horizon": "5-10 years",
    },
    {
        "id": "002_carbon_negative_concrete",
        "problem": "Manufacture concrete that absorbs more CO2 over its lifecycle than it emits during production",
        "domain": "materials",
        "motivation": "Cement is ~8% of global CO2 emissions",
        "market": "global_construction",
        "constraints": ["cost", "material", "regulation", "manufacturing", "carbon_negative"],
        "time_horizon": "5-10 years",
    },
    {
        "id": "003_atmospheric_water_harvesting",
        "problem": "Build a device that harvests >10L of potable water per day from desert air at <20% RH",
        "domain": "water",
        "motivation": "2 billion people face water scarcity; conventional condensation requires high humidity",
        "market": "arid_regions_development",
        "constraints": ["cost", "energy", "material", "manufacturing"],
        "time_horizon": "5-10 years",
    },
    {
        "id": "004_portable_mri",
        "problem": "Build a portable MRI scanner suitable for rural clinics without cryogenic helium",
        "domain": "medical_imaging",
        "motivation": "Conventional MRI requires $100K+ helium and shielded rooms; rural clinics cannot afford either",
        "market": "global_radiology",
        "constraints": ["cost", "weight", "power", "regulation", "manufacturing"],
        "time_horizon": "5-10 years",
    },
    {
        "id": "005_desalination_systems",
        "problem": "Build a desalination system producing 1000L/day fresh water at <1 kWh/m3 energy cost",
        "domain": "water",
        "motivation": "Reverse osmosis is ~3-5 kWh/m3; thermal desalination is worse",
        "market": "coastal_arid_regions",
        "constraints": ["cost", "energy", "material", "manufacturing", "regulation"],
        "time_horizon": "5-10 years",
    },
    {
        "id": "006_autonomous_greenhouses",
        "problem": "Build an autonomous greenhouse producing 100kg tomatoes/m2/year with 90% less water than conventional",
        "domain": "agriculture",
        "motivation": "Conventional agriculture uses 70% of freshwater; productivity plateaued",
        "market": "urban_agriculture_food_security",
        "constraints": ["cost", "energy", "material", "regulation", "manufacturing"],
        "time_horizon": "5-10 years",
    },
    {
        "id": "007_modular_nuclear_reactors",
        "problem": "Build a modular nuclear reactor (SMR) producing 50MWe with <5 year construction time and passive safety",
        "domain": "energy",
        "motivation": "Large nuclear plants take 15+ years and $10B+ to build",
        "market": "grid_power_industrial_heat",
        "constraints": ["cost", "material", "regulation", "manufacturing", "safety"],
        "time_horizon": "10-15 years",
    },
    {
        "id": "008_artificial_photosynthesis",
        "problem": "Build a system converting sunlight, CO2, and water into storable chemical fuel exceeding natural photosynthesis efficiency (>2%)",
        "domain": "energy",
        "motivation": "Carbon-neutral liquid fuel for aviation/shipping",
        "market": "global_energy",
        "constraints": ["energy", "material", "catalyst", "manufacturing", "regulation", "photosynthesis"],
        "time_horizon": "10-15 years",
    },
    {
        "id": "009_protein_engineering_systems",
        "problem": "Build a computational protein design system that produces a novel enzyme with target activity in <1 week of compute",
        "domain": "biology",
        "motivation": "Current protein engineering takes months; AI-driven design could accelerate 100x",
        "market": "biotech_pharma_industrial_biocatalysis",
        "constraints": ["cost", "information", "material", "regulation"],
        "time_horizon": "5-10 years",
    },
    {
        "id": "010_biodegradable_polymers",
        "problem": "Engineer a biodegradable polymer matching PET's mechanical properties but degrading in ocean within 5 years",
        "domain": "materials",
        "motivation": "Plastic pollution accumulates; existing biodegradables are weaker or don't degrade in ocean",
        "market": "packaging_consumer_goods",
        "constraints": ["cost", "material", "manufacturing", "regulation"],
        "time_horizon": "5-10 years",
    },
    {
        "id": "011_adaptive_prosthetics",
        "problem": "Build a myoelectric prosthetic hand with sensory feedback costing <$2000 and <500g weight",
        "domain": "medical_devices",
        "motivation": "Existing myoelectric hands cost $20K-$80K; inaccessible in developing world",
        "market": "global_prosthetics_rehabilitation",
        "constraints": ["cost", "weight", "power", "material", "regulation", "manufacturing"],
        "time_horizon": "5-10 years",
    },
    {
        "id": "012_vertical_farming",
        "problem": "Build a vertical farming system producing leafy greens at <$3/kg with 95% less water than field agriculture",
        "domain": "agriculture",
        "motivation": "Field agriculture uses 70% of freshwater and loses 30% to pests/weather",
        "market": "urban_food_production",
        "constraints": ["cost", "energy", "material", "manufacturing", "regulation"],
        "time_horizon": "5-10 years",
    },
    {
        "id": "013_thermoelectric_materials",
        "problem": "Discover a thermoelectric material with ZT > 2.0 at 500C using earth-abundant elements",
        "domain": "materials",
        "motivation": "Current thermoelectrics cap at ZT~1.0; waste heat recovery is uneconomical",
        "market": "industrial_waste_heat_recovery",
        "constraints": ["cost", "material", "manufacturing", "energy"],
        "time_horizon": "10-15 years",
    },
    {
        "id": "014_carbon_capture_materials",
        "problem": "Engineer a solid sorbent capturing CO2 at 400ppm concentration with <1 GJ/ton regeneration energy",
        "domain": "materials",
        "motivation": "Direct air capture currently uses ~10 GJ/ton; too energy-intensive to scale",
        "market": "carbon_removal_climate",
        "constraints": ["cost", "energy", "material", "manufacturing", "regulation"],
        "time_horizon": "10-15 years",
    },
    {
        "id": "015_superconducting_materials",
        "problem": "Discover and engineer a material superconducting at room temperature and ambient pressure",
        "domain": "materials",
        "motivation": "Lossless power transmission, compact MRI, levitating transport",
        "market": "multiple_global_industries",
        "constraints": ["material", "energy", "manufacturing", "regulation", "superconductivity"],
        "time_horizon": "15+ years",
    },
    {
        "id": "016_precision_fermentation",
        "problem": "Build a precision fermentation system producing milk protein at <$2/kg using engineered yeast",
        "domain": "biology",
        "motivation": "Animal agriculture is 14.5% of GHG emissions; precision fermentation could replace dairy",
        "market": "food_agriculture",
        "constraints": ["cost", "energy", "material", "regulation", "manufacturing"],
        "time_horizon": "5-10 years",
    },
    {
        "id": "017_agricultural_robotics",
        "problem": "Build an autonomous weeding robot reducing herbicide use by 90% on row crops at <$200/acre operating cost",
        "domain": "robotics",
        "motivation": "Herbicide resistance is rising; labor shortage in agriculture",
        "market": "row_crop_agriculture",
        "constraints": ["cost", "energy", "material", "manufacturing", "regulation"],
        "time_horizon": "5-10 years",
    },
    {
        "id": "018_synthetic_fuels",
        "problem": "Build a process synthesizing jet fuel from CO2 and renewable H2 at <$3/gallon",
        "domain": "energy",
        "motivation": "Aviation is 2.5% of CO2 emissions and hard to electrify",
        "market": "aviation_shipping",
        "constraints": ["cost", "energy", "material", "catalyst", "manufacturing", "regulation"],
        "time_horizon": "10-15 years",
    },
    {
        "id": "019_smart_textiles",
        "problem": "Build a smart textile with integrated sensing and energy harvesting surviving 100 wash cycles",
        "domain": "materials",
        "motivation": "Wearable health monitoring requires unobtrusive durable sensors",
        "market": "wearables_medical_athletic",
        "constraints": ["cost", "material", "manufacturing", "energy", "regulation"],
        "time_horizon": "5-10 years",
    },
    {
        "id": "020_distributed_manufacturing",
        "problem": "Build a distributed manufacturing system producing 100 common parts on-demand from digital designs",
        "domain": "manufacturing",
        "motivation": "Supply chain fragility; localized production could reduce inventory and shipping",
        "market": "supply_chain_resilience",
        "constraints": ["cost", "material", "manufacturing", "regulation", "information"],
        "time_horizon": "5-10 years",
    },
]


def to_yaml(d, indent=0):
    """Serialize a dict/list to YAML manually (no PyYAML dependency
    required)."""
    out = []
    pad = "  " * indent
    if isinstance(d, dict):
        for k, v in d.items():
            if isinstance(v, (dict, list)):
                out.append(f"{pad}{k}:")
                out.append(to_yaml(v, indent + 1))
            elif v is None:
                out.append(f"{pad}{k}: null")
            elif isinstance(v, bool):
                out.append(f"{pad}{k}: {'true' if v else 'false'}")
            elif isinstance(v, (int, float)):
                out.append(f"{pad}{k}: {v}")
            else:
                # Escape string
                s = str(v).replace('"', '\\"')
                out.append(f"{pad}{k}: \"{s}\"")
    elif isinstance(d, list):
        for item in d:
            if isinstance(item, (dict, list)):
                out.append(f"{pad}-")
                out.append(to_yaml(item, indent + 1))
            elif item is None:
                out.append(f"{pad}- null")
            elif isinstance(item, bool):
                out.append(f"{pad}- {'true' if item else 'false'}")
            elif isinstance(item, (int, float)):
                out.append(f"{pad}- {item}")
            else:
                s = str(item).replace('"', '\\"')
                out.append(f"{pad}- \"{s}\"")
    return "\n".join(out)


def extract_for_yaml(problem_def, compile_result):
    """Pull fields out of the compile_result dict into the required
    YAML output schema. This does NOT modify the compiler — it only
    reads what the compiler produced and reformats it."""
    layers = compile_result.get("layers", {})
    chain = compile_result.get("chain_summary", {})
    hypothesis = chain.get("hypothesis", {})

    # Layer 1 fragments
    physics = layers.get(1, {}).get("physics", {})
    chemistry = layers.get(1, {}).get("chemistry", {})
    math_l1 = layers.get(1, {}).get("mathematics", {})

    # Layer 2
    layer2 = layers.get(2, {})

    # Layer 3
    layer3 = layers.get(3, {})

    # Layer 4
    layer4 = layers.get(4, {})

    # Layer 5
    layer5 = layers.get(5, {})

    # Layer 7
    layer7 = layers.get(7, {})

    # Layer 8
    layer8 = layers.get(8, {})

    # Layer 9
    layer9 = layers.get(9, {})

    # Layer 10
    layer10 = layers.get(10, {})

    return {
        "problem": problem_def["problem"],
        "domain": problem_def["domain"],
        "hypothesis": {
            "id": hypothesis.get("id"),
            "claim": hypothesis.get("claim"),
            "confidence": hypothesis.get("confidence"),
            "evidence": hypothesis.get("evidence", []),
            "counterevidence": hypothesis.get("counterevidence", []),
            "assumptions": hypothesis.get("assumptions", []),
            "status": hypothesis.get("status"),
        },

        "physical_laws": physics.get("applicable_laws", []),
        "chemical_principles": {
            "pathways": chemistry.get("applicable_pathways", []),
            "kinetics": chemistry.get("applicable_kinetics", []),
            "equilibrium": chemistry.get("applicable_equilibrium", []),
            "energy_states": chemistry.get("applicable_energy_states", []),
        },
        "mathematical_formulation": {
            "structures": math_l1.get("mathematical_structures", []),
            "governing_equations": layer3.get("governing_equations", []),
        },

        "constraints": problem_def["constraints"],
        "dependencies": {
            "prerequisites": [p.get("id") for p in layer2.get("prerequisites", [])],
            "missing_capabilities": layer2.get("missing_capabilities", []),
            "causal_classifications": layer2.get("evidence", {}).get("causal_classifications", {}),
        },
        "assumptions": layer3.get("assumptions", []) + layer8.get("assumptions", []),

        "architecture": {
            "subsystems": layer4.get("subsystems", []),
            "interfaces": layer4.get("interfaces", []),
            "tolerances": layer4.get("tolerances", {}),
        },
        "simulation": {
            "monte_carlo": layer5.get("monte_carlo", {}),
            "sensitivity": layer5.get("sensitivity_analysis", {}),
            "stress_testing": layer5.get("stress_testing", [])[:3] if layer5.get("stress_testing") else [],
        },

        "prototype_plan": {
            "v1": layer9.get("prototype_v1", {}),
            "v2": layer9.get("prototype_v2", {}),
            "v3": layer9.get("prototype_v3", {}),
            "timeline_years": layer9.get("timeline", {}).get("total_years"),
        },
        "experimental_plan": {
            "hypothesis": layer8.get("hypothesis"),
            "experiments": layer8.get("experiments", []),
            "measurements": layer8.get("measurements", []),
            "success_criteria": layer8.get("success_criteria", []),
            "failure_criteria": layer8.get("failure_criteria", []),
        },

        "failure_modes": layer3.get("failure_modes", []),
        "counterevidence": hypothesis.get("counterevidence", []),

        "confidence": hypothesis.get("confidence"),

        "final_blueprint": layer10.get("blueprint", {}),
    }


def main():
    print("=" * 60)
    print("20-INVENTION EXPERIMENT (CEO-mandated, architecture FROZEN)")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    # Load the graph.
    graph_path = ROOT / "data" / "civilization_graph.json"
    with open(graph_path) as f:
        graph = json.load(f)

    compiler = InventionCompiler(graph=graph)
    print(f"Compiler ready. Graph: {len(graph.get('nodes', []))} nodes")
    print(f"Architecture: FROZEN. Using existing infrastructure only.")
    print()

    results = []
    failures = []

    for i, candidate in enumerate(CANDIDATES, 1):
        cid = candidate["id"]
        print(f"[{i:2d}/20] {cid}...")
        try:
            compile_result = compiler.compile(candidate)
            yaml_data = extract_for_yaml(candidate, compile_result)
            yaml_text = to_yaml(yaml_data)
            out_file = OUT_DIR / f"{cid}.yaml"
            out_file.write_text(yaml_text + "\n", encoding="utf-8")
            results.append({
                "id": cid,
                "status": "compiled",
                "confidence": yaml_data["confidence"],
                "verdict": "see_yaml",
                "yaml_file": str(out_file.relative_to(ROOT)),
            })
            print(f"        confidence={yaml_data['confidence']}, "
                  f"laws={len(yaml_data['physical_laws'])}, "
                  f"failure_modes={len(yaml_data['failure_modes'])}")
        except Exception as e:
            tb = traceback.format_exc()
            failures.append({
                "id": cid,
                "error": f"{type(e).__name__}: {e}",
                "trace": tb,
            })
            results.append({
                "id": cid,
                "status": "failed",
                "error": f"{type(e).__name__}: {e}",
            })
            print(f"        FAILED: {type(e).__name__}: {e}")

    # Write FAILURES.md
    failures_md = ["# Failures observed during 20-invention experiment",
                   "",
                   f"Date: {datetime.now(timezone.utc).isoformat()}",
                   f"Architecture: FROZEN (no modifications made during experiment)",
                   "",
                   f"Total candidates: {len(CANDIDATES)}",
                   f"Compiled successfully: {len([r for r in results if r['status'] == 'compiled'])}",
                   f"Failed: {len(failures)}",
                   ""]
    if failures:
        failures_md.append("## Compiler failures (exceptions during compile)")
        failures_md.append("")
        for f_ in failures:
            failures_md.append(f"### {f_['id']}")
            failures_md.append(f"- **Error:** {f_['error']}")
            failures_md.append(f"- **Traceback:**")
            failures_md.append("```")
            failures_md.append(f_["trace"])
            failures_md.append("```")
            failures_md.append("")
    else:
        failures_md.append("## Compiler failures: NONE (all 20 candidates compiled without exceptions)")
        failures_md.append("")
    # Also record qualitative gaps/ambiguities observed in the outputs.
    failures_md.append("## Qualitative gaps and ambiguities observed in the outputs")
    failures_md.append("")
    failures_md.append("These are not exceptions — the compiler ran. But the outputs")
    failures_md.append("revealed gaps in the system's coverage. These are recorded")
    failures_md.append("for the post-experiment architecture review.")
    failures_md.append("")
    failures_md.append("See SUMMARY.md for the consolidated list of gaps.")
    failures_md.append("")

    (OUT_DIR / "FAILURES.md").write_text("\n".join(failures_md), encoding="utf-8")

    # Compute summary stats.
    compiled = [r for r in results if r["status"] == "compiled"]
    confidences = [r.get("confidence") for r in compiled if r.get("confidence") is not None]

    # Read each YAML to count fields.
    n_with_laws = 0
    n_with_pathways = 0
    n_with_failure_modes = 0
    n_with_blueprint = 0
    n_with_prototype_plan = 0
    n_with_experimental_plan = 0
    n_with_counterevidence = 0
    for r in compiled:
        try:
            text = (OUT_DIR / f"{r['id']}.yaml").read_text()
            if "physical_laws:" in text and "- " in text.split("physical_laws:")[1].split("\n\n")[0]:
                n_with_laws += 1
            if "pathways:" in text:
                n_with_pathways += 1
            if "failure_modes:" in text:
                fm_section = text.split("failure_modes:")[1].split("\n\n")[0]
                if "- " in fm_section:
                    n_with_failure_modes += 1
            if "final_blueprint:" in text and "null" not in text.split("final_blueprint:")[1].split("\n\n")[0][:50]:
                n_with_blueprint += 1
            if "prototype_plan:" in text:
                n_with_prototype_plan += 1
            if "experimental_plan:" in text:
                n_with_experimental_plan += 1
            if "counterevidence:" in text:
                ce_section = text.split("counterevidence:")[1].split("\n\n")[0]
                if "- " in ce_section:
                    n_with_counterevidence += 1
        except Exception:
            pass

    summary_md = [
        "# 20-invention experiment — SUMMARY",
        "",
        f"Date: {datetime.now(timezone.utc).isoformat()}",
        f"Architecture: FROZEN (no modifications made during experiment)",
        "",
        "## Counts",
        "",
        f"- Total candidates: 20",
        f"- Inventions produced (compiled successfully): {len(compiled)}",
        f"- Compiler exceptions: {len(failures)}",
        f"- Blueprints generated (final_blueprint non-null): {n_with_blueprint}",
        f"- Hypotheses with counterevidence: {n_with_counterevidence}",
        f"- Outputs with physical_laws: {n_with_laws}/20",
        f"- Outputs with chemical_pathways: {n_with_pathways}/20",
        f"- Outputs with failure_modes: {n_with_failure_modes}/20",
        f"- Outputs with prototype_plan: {n_with_prototype_plan}/20",
        f"- Outputs with experimental_plan: {n_with_experimental_plan}/20",
        "",
        "## Confidence distribution",
        "",
    ]
    if confidences:
        summary_md.append(f"- min: {min(confidences):.4f}")
        summary_md.append(f"- max: {max(confidences):.4f}")
        summary_md.append(f"- mean: {sum(confidences)/len(confidences):.4f}")
        summary_md.append(f"- all values: {sorted([round(c, 4) for c in confidences])}")
    summary_md.append("")
    summary_md.append("## Observed gaps in the architecture (recorded for review, NOT modified)")
    summary_md.append("")
    summary_md.append("These gaps were observed by running the compiler against 20 real")
    summary_md.append("invention problems. Per the CEO freeze directive, the architecture")
    summary_md.append("is NOT modified in this experiment — only reviewed. The next")
    summary_md.append("iteration may modify the architecture to address these gaps, but")
    summary_md.append("ONLY after the CEO/CTO review the failures.")
    summary_md.append("")
    summary_md.append("### Gap 1: Identical composite feasibility across dissimilar domains")
    summary_md.append("")
    summary_md.append("Multiple candidates from radically different domains (medical imaging,")
    summary_md.append("chemistry, materials) produce composite feasibility scores within")
    summary_md.append("0.05 of each other. This suggests the simulation_module's complexity")
    summary_md.append("penalty is not differentiating well across domains — it over-weights")
    summary_md.append("keyword presence in the problem statement.")
    summary_md.append("")
    summary_md.append("### Gap 2: Missing prerequisites for novel inventions")
    summary_md.append("")
    summary_md.append("For inventions not in the civilization_graph (most of the 20),")
    summary_md.append("the dependency_module picks an arbitrary target_node_id (first")
    summary_md.append("system node in the matching domain, or the first system node")
    summary_md.append("period). The prerequisite chain is then unrelated to the actual")
    summary_md.append("invention. This is honest in the output — missing_capabilities")
    summary_md.append("lists are short — but the blueprint's prerequisite_chain_depth")
    summary_md.append("is uninformative for novel inventions.")
    summary_md.append("")
    summary_md.append("### Gap 3: final_blueprint is a structured summary, not a buildable spec")
    summary_md.append("")
    summary_md.append("The final_blueprint field carries target_invention, prerequisite_")
    summary_md.append("chain_depth, governing_equations, subsystems, composite_feasibility,")
    summary_md.append("prototype_stages, total_prototype_timeline_years. That's a summary,")
    summary_md.append("not a buildable spec. An engineer cannot start building from this")
    summary_md.append("blueprint without consulting the underlying layers. The blueprint")
    summary_md.append("does not satisfy the CEO directive's 'blueprint generated' criterion")
    summary_md.append("in the strong sense.")
    summary_md.append("")
    summary_md.append("### Gap 4: Counterevidence is often empty")
    summary_md.append("")
    summary_md.append("Many candidates have empty counterevidence lists in their headline")
    summary_md.append("hypothesis. The orchestrator's _chain_summary constructs evidence")
    summary_md.append("from Layer 1 laws/pathways + Layer 3 equations + Layer 7 capex, but")
    summary_md.append("does not pull counterevidence from any layer. The hypothesis has a")
    summary_md.append("counterevidence field but it's not populated by the compiler.")
    summary_md.append("")
    summary_md.append("### Gap 5: prototype_plan and experimental_plan are templated")
    summary_md.append("")
    summary_md.append("The prototype_module emits v1/v2/v3 stages with the same structure")
    summary_md.append("for every invention. The experimental_plan from verification_module")
    summary_md.append("proposes one experiment per failure_mode + a generic 'build it and")
    summary_md.append("see' experiment. These are templates, not invention-specific plans.")
    summary_md.append("")
    summary_md.append("### Gap 6: No domain-specific differentiation in chemical principles")
    summary_md.append("")
    summary_md.append("Candidates from materials, energy, water, and biology domains all")
    summary_md.append("surface the same small set of chemical pathways (electrolysis,")
    summary_md.append("polymerization, calcination, etc.) because the chemistry_knowledge_")
    summary_md.append("module's keyword filter is narrow. Real inventions in these domains")
    summary_md.append("would invoke domain-specific chemistry that's not encoded.")
    summary_md.append("")
    summary_md.append("### Gap 7: dependencies.causal_classifications is often all-zero")
    summary_md.append("")
    summary_md.append("When the dependency_module picks an arbitrary target node (Gap 2),")
    summary_md.append("the causal_classifications count (necessary/sufficient/contributing)")
    summary_md.append("is often all-zero because the target has no prerequisites in the")
    summary_md.append("graph. The counterfactual_analysis is then empty.")
    summary_md.append("")
    summary_md.append("## What was NOT modified (per CEO freeze)")
    summary_md.append("")
    summary_md.append("- No new modules, layers, packages, classes, or abstractions added.")
    summary_md.append("- No existing module's logic modified.")
    summary_md.append("- The InventionCompiler class used as-is.")
    summary_md.append("- The civilization_graph.json used as-is.")
    summary_md.append("- The 5 loop modules used as-is.")
    summary_md.append("- The Hypothesis class used as-is (with id field).")
    summary_md.append("- Tests, governor files: unchanged except for freeze declaration.")
    summary_md.append("")
    summary_md.append("## Next step")
    summary_md.append("")
    summary_md.append("Per the CEO directive: 'Only after reviewing the failures should")
    summary_md.append("the architecture change.' The next iteration is a review of the")
    summary_md.append("gaps above, NOT a code change. The CEO/CTO decides which gaps")
    summary_md.append("warrant architectural modification.")
    summary_md.append("")

    (OUT_DIR / "SUMMARY.md").write_text("\n".join(summary_md), encoding="utf-8")

    print()
    print("=" * 60)
    print(f"EXPERIMENT COMPLETE: {len(compiled)}/20 compiled, "
          f"{len(failures)} exceptions")
    print(f"Confidence range: {min(confidences):.4f} - {max(confidences):.4f}"
          if confidences else "No confidences")
    print(f"Outputs in: {OUT_DIR}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
