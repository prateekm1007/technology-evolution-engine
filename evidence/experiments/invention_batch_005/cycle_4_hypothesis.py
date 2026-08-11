"""
Maestro Loop Cycle 4 — Gap 4 (missing counterevidence)
PHASE 5: HYPOTHESIS
"""
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hypothesis.hypothesis import Hypothesis

CYCLE_4_HYPOTHESIS = Hypothesis(
    claim=(
        "Pulling counterevidence from Layer 3 (failure_modes), Layer 5 "
        "(stress_testing), Layer 7 (commercial_risks), and Layer 10 "
        "(technical_risks) into the headline hypothesis will produce "
        "non-empty counterevidence lists for at least 15/20 candidates. "
        "Before the fix, 0/20 had non-empty counterevidence."
    ),
    confidence=0.60,
    evidence=[
        "Gap 4 observation: 0/20 hypotheses have counterevidence",
        "Layer 3 already produces failure_modes (e.g., cost_overrun, "
        "regulatory_rejection, manufacturing_yield_too_low)",
        "Layer 5 already produces stress_testing (worst-case composites)",
        "Layer 7 already produces commercial_risks (market_size_too_small, "
        "capex_exceeds_half_of_market_size, s_curve_adoption)",
        "Layer 10 already produces technical_risks (failure_modes + "
        "stress_scenario_composites)",
        "The orchestrator already builds evidence from these layers but "
        "does not extract counterevidence from them — the data exists, "
        "it's just not composed into the hypothesis",
    ],
    counterevidence=[
        "Some candidates may have empty failure_modes if their constraints "
        "don't match the constraint_engine's keyword priors",
        "Some candidates may have empty commercial_risks if their market "
        "size is large enough and adoption is bass_diffusion",
        "Even with counterevidence populated, the items are keyword-derived "
        "labels (e.g., 'cost_overrun'), not quantitative risk assessments",
    ],
    assumptions=[
        "Only orchestrator.py is modified (per Maestro Loop PHASE 6)",
        "The counterevidence is assembled FROM existing layer outputs, "
        "not by adding new analysis",
        "'Non-empty counterevidence' means at least 1 item in the list",
    ],
    dependencies=[
        "hyp_gap1_fix_simulation_module",
        "hyp_gap2_7_fix_dependency_module",
        "hyp_gap3_fix_blueprint_module",
    ],
    writer="evidence.experiments.invention_batch_005.cycle_4_hypothesis",
)

PREDICTED_DELTA = {
    "counterevidence_before": {"non_empty": 0, "out_of": 20},
    "counterevidence_after": {"non_empty": 15, "out_of": 20, "min": 1, "max": 8},
    "prediction": "At least 15/20 hypotheses will have non-empty counterevidence.",
}
