"""
Maestro Loop Cycle 5 — Gap 5 (templated plans)
PHASE 5: HYPOTHESIS
"""
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hypothesis.hypothesis import Hypothesis

CYCLE_5_HYPOTHESIS = Hypothesis(
    claim=(
        "Making the prototype_module's v1/v2/v3 goals, scopes, and "
        "durations invention-specific (using the problem's domain, "
        "constraints, physics laws, and governing equations) will "
        "produce different prototype plans for different inventions. "
        "At least 15/20 candidates will have unique v1 goal strings, "
        "and at least 10/20 will have unique duration triples."
    ),
    confidence=0.55,
    evidence=[
        "Gap 5 observation: all 20 candidates produce the same v1 goal "
        "('prove the core mechanism works at lab scale'), same v2 goal "
        "('prove the subsystems integrate'), same v3 goal ('prove the "
        "manufacturing pathway')",
        "The prototype_module already receives the problem dict and "
        "all_layers — it has access to domain, constraints, physics "
        "laws, governing equations, failure modes",
        "Domain-specific vocabulary already exists in the problem "
        "definitions (e.g., 'electrolyte', 'MRI scanner', 'CO2 "
        "absorption', 'photosynthesis')",
        "The fix is compositional: use existing data to parameterize "
        "the prototype goals, not add new analysis",
    ],
    counterevidence=[
        "The prototype_module's durations are formula-based "
        "(6 + prereq_count months for v2, etc.) — making them "
        "invention-specific requires domain-specific time priors",
        "Even with invention-specific goals, the v1/v2/v3 structure "
        "(physics validation → engineering integration → production "
        "readiness) is a universal engineering pattern that doesn't "
        "change across inventions",
        "The problem text is free-form; extracting reliable "
        "invention-specific vocabulary requires keyword extraction "
        "that may produce similar results for similar problems",
    ],
    assumptions=[
        "Only prototype_module.py is modified (per Maestro Loop PHASE 6)",
        "Invention-specific goals are constructed FROM existing layer "
        "data (domain, constraints, physics laws, governing equations, "
        "failure modes) — no new analysis is added",
        "'Unique' means the string content differs, not just the "
        "parameters embedded in it",
    ],
    dependencies=[
        "hyp_gap1_fix_simulation_module",
        "hyp_gap2_7_fix_dependency_module",
        "hyp_gap3_fix_blueprint_module",
        "hyp_gap4_fix_orchestrator",
    ],
    writer="evidence.experiments.invention_batch_006.cycle_5_hypothesis",
)

PREDICTED_DELTA = {
    "v1_goals_before": {"unique": 1, "out_of": 20},
    "v1_goals_after": {"unique": 15, "out_of": 20, "min": 10},
    "prediction": "At least 15/20 candidates will have unique v1 goal strings.",
}
