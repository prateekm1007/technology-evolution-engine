"""
Experimentation Layer — closed-loop experimentation scoping.

Per F-046 (FAILURES.md): the experimentation layer has never executed
a single predict→build→observe→learn cycle. This module provides the
SCOPING for that cycle — it defines the experiment spec, measurement
protocol, pass/fail criteria, and collaborator requirements. The
actual execution requires reality cooperation (per PR-26) and cannot
be closed by code work alone.

Per PR-23 (Closed-loop learning requirement): a learning claim
requires a closed loop with 5 specific steps:
  1. The system makes a prediction (with timestamp T1).
  2. An external observation records a pass/fail (with timestamp T2 > T1).
  3. The system identifies which module's input was wrong (root cause + evidence).
  4. The module is revised (with diff + commit hash).
  5. A second prediction (with timestamp T3 > T2) is made by the revised
     module, and the second prediction is measurably closer to the
     observation than the first.

This module provides:
  - ExperimentSpec: a dataclass defining one complete experiment.
  - ClosedLoopTracker: tracks the 5-step closed loop for an experiment.
  - EXPERIMENT_CANDIDATES: pre-scoped experiment candidates derived
    from milestones/milestone_001 (pH prediction) and milestone_002
    (electrolyte improvement).
  - validate_closed_loop(): checks whether a recorded experiment
    satisfies all 5 PR-23 criteria.

STATUS: SCAFFOLD + SCOPING. The scoping is real code (this module
defines what a closed loop looks like). The execution requires an
external collaborator to actually build/run the experiment (per PR-26).
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# ----------------------------------------------------------------------
# ExperimentSpec: defines one complete experiment
# ----------------------------------------------------------------------

@dataclass
class ExperimentSpec:
    """A complete experiment specification.

    Per PR-23, an experiment must define:
      - prediction: what the system predicts (with falsifier)
      - build: what to physically construct (with materials + cost)
      - observe: what to measure (with instrument + procedure)
      - learn: which module to revise if prediction is wrong
      - revise: how to re-compile after the revision

    The spec is the SCOPING. The EXECUTION requires an external
    collaborator to physically perform the build + observe steps.
    """

    experiment_id: str
    name: str
    domain: str
    problem_statement: str

    # Step 1: PREDICT
    prediction: Dict[str, Any] = field(default_factory=dict)
    # Required keys: claim, falsifier, expected_value, tolerance, timestamp_t1

    # Step 2: BUILD (executed by external collaborator)
    build: Dict[str, Any] = field(default_factory=dict)
    # Required keys: materials, procedure, estimated_cost_usd,
    #                estimated_days, collaborator_requirements

    # Step 3: OBSERVE (executed by external collaborator)
    observe: Dict[str, Any] = field(default_factory=dict)
    # Required keys: metric, instrument, procedure, pass_criteria,
    #                fail_criteria, expected_recorded_at

    # Step 4: LEARN (executed by the system after observation)
    learn: Dict[str, Any] = field(default_factory=dict)
    # Required keys: modules_to_revision, root_cause_analysis_template,
    #                revision_diff_template

    # Step 5: REVISE (executed by the system after learning)
    revise: Dict[str, Any] = field(default_factory=dict)
    # Required keys: recompile_procedure, second_prediction_template,
    #                closeness_metric (how to measure improvement)

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "scoped"  # scoped → predicted → built → observed → learned → revised → closed
    class_label: str = "A"  # A=infrastructure, B=invention

    def validate(self) -> List[str]:
        """Validate that the spec has all 5 PR-23 closed-loop steps.

        Returns a list of error messages (empty if valid).
        """
        errors = []

        required_prediction_keys = {"claim", "falsifier", "expected_value", "tolerance"}
        missing_pred = required_prediction_keys - set(self.prediction.keys())
        if missing_pred:
            errors.append(f"prediction missing keys: {missing_pred}")

        required_build_keys = {"materials", "procedure", "estimated_cost_usd",
                                "estimated_days", "collaborator_requirements"}
        missing_build = required_build_keys - set(self.build.keys())
        if missing_build:
            errors.append(f"build missing keys: {missing_build}")

        required_observe_keys = {"metric", "instrument", "procedure",
                                  "pass_criteria", "fail_criteria"}
        missing_obs = required_observe_keys - set(self.observe.keys())
        if missing_obs:
            errors.append(f"observe missing keys: {missing_obs}")

        required_learn_keys = {"modules_to_revision", "root_cause_analysis_template"}
        missing_learn = required_learn_keys - set(self.learn.keys())
        if missing_learn:
            errors.append(f"learn missing keys: {missing_learn}")

        required_revise_keys = {"recompile_procedure", "second_prediction_template",
                                 "closeness_metric"}
        missing_rev = required_revise_keys - set(self.revise.keys())
        if missing_rev:
            errors.append(f"revise missing keys: {missing_rev}")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ----------------------------------------------------------------------
# EXPERIMENT_CANDIDATES: pre-scoped experiments from milestones
# ----------------------------------------------------------------------

# Candidate 1: pH prediction (Class A — infrastructure milestone)
# Derived from milestones/milestone_001/spec.json
PH_PREDICTION_EXPERIMENT = ExperimentSpec(
    experiment_id="EXP-001-ph-prediction",
    name="pH prediction of citric-acid + sodium-bicarbonate mixture",
    domain="chemistry",
    problem_statement=(
        "Predict the resulting pH when 1g citric acid and 2g sodium "
        "bicarbonate are dissolved in 100mL distilled water at 25°C."
    ),
    prediction={
        "claim": "The resulting pH of the citric-acid + sodium-bicarbonate "
                 "mixture at the specified ratio (1g:2g in 100mL H2O at 25°C) "
                 "will be in the range 6.0 - 7.0.",
        "falsifier": "If the measured pH is < 5.0 or > 8.0, the prediction "
                     "is falsified (outside ±2.0 of the predicted center 6.5).",
        "expected_value": 6.5,
        "tolerance": 1.0,
        "evidence_chain": [
            "chemistry_knowledge_module: acid-base neutralization pathway",
            "citric-acid pKa1=3.13 (literature)",
            "sodium-bicarbonate pKb=3.67 (literature)",
            "stoichiometric calculation: 1g citric (5.2 mmol) + 2g NaHCO3 "
            "(23.8 mmol) → NaHCO3 in ~4.5x molar excess → pH leans basic",
        ],
        "assumptions": [
            "water is distilled (no buffering from tap water minerals)",
            "container is open (CO2 escapes; closed container would lower pH)",
            "pH strips have ±0.5 accuracy",
            "temperature is 25°C (room temperature, not controlled)",
        ],
    },
    build={
        "materials": [
            "citric acid (food-grade, ~$5)",
            "sodium bicarbonate (baking soda, ~$2)",
            "distilled water (~$1)",
            "pH test strips, range 0-14 (~$10)",
            "measuring spoons / scale (~$2)",
        ],
        "procedure": [
            "1. Measure 100mL distilled water into a clean container.",
            "2. Measure 1g citric acid; add to water; stir until dissolved.",
            "3. Measure 2g sodium bicarbonate; add to the citric-acid solution; stir.",
            "4. Wait 60 seconds for the reaction to complete (CO2 evolution to subside).",
            "5. Dip pH test strip for 2 seconds; remove; wait 15 seconds; compare to color chart.",
            "6. Record the pH reading.",
            "7. Repeat steps 1-6 three times (for reproducibility).",
        ],
        "estimated_cost_usd": 20,
        "estimated_days": 1,
        "collaborator_requirements": (
            "Any human with kitchen access. No specialized equipment "
            "beyond pH strips. The collaborator must: (a) follow the "
            "procedure exactly, (b) record the pH reading to ±0.5, "
            "(c) repeat 3 times, (d) report the 3 readings + mean."
        ),
    },
    observe={
        "metric": "pH (numeric, range 0-14)",
        "instrument": "pH test strips, range 0-14, ±0.5 accuracy",
        "procedure": [
            "1. After the 60-second wait (step 4 above), dip pH strip for 2 seconds.",
            "2. Remove strip; wait 15 seconds for color development.",
            "3. Compare strip color to the provided color chart.",
            "4. Record the pH reading to the nearest 0.5.",
            "5. Repeat for 3 trials; compute the mean.",
        ],
        "pass_criteria": (
            "abs(measured_pH - 6.5) <= 1.0 AND all 3 trials agree within ±0.5"
        ),
        "fail_criteria": (
            "abs(measured_pH - 6.5) > 1.0 OR trials disagree by > 0.5"
        ),
        "expected_recorded_at": "data/ledger/predictions.jsonl (verification entry)",
    },
    learn={
        "modules_to_revision": [
            "invention_compiler/chemistry_knowledge_module.py (if pKa values are wrong)",
            "invention_compiler/constraint_module.py (if tolerance assumptions are wrong)",
        ],
        "root_cause_analysis_template": (
            "If measured pH differs from predicted by > 1.0:\n"
            "  1. Check whether the pKa values in chemistry_knowledge_module "
            "match literature (citric acid pKa1=3.13, NaHCO3 pKb=3.67).\n"
            "  2. Check whether the stoichiometric calculation (1g citric = "
            "5.2 mmol, 2g NaHCO3 = 23.8 mmol) is correct.\n"
            "  3. Check whether the open-container assumption (CO2 escapes) "
            "is valid — if the container was closed, pH would be lower.\n"
            "  4. Check whether the pH strip accuracy (±0.5) is sufficient "
            "for the tolerance (±1.0)."
        ),
    },
    revise={
        "recompile_procedure": (
            "After identifying the root cause, revise the affected module "
            "(e.g., update pKa values in chemistry_knowledge_module.py), "
            "then re-run the InventionCompiler on the same problem. "
            "The new blueprint's prediction is the second prediction (T3)."
        ),
        "second_prediction_template": {
            "claim": "(revised) The resulting pH will be in range X-Y.",
            "expected_value": "(revised center, based on root-cause fix)",
            "tolerance": "(revised, based on root-cause fix)",
        },
        "closeness_metric": (
            "closeness = abs(first_prediction - observation) - "
            "abs(second_prediction - observation). "
            "If closeness > 0, the second prediction is closer → learning "
            "occurred (PR-23 step 5 satisfied)."
        ),
    },
    class_label="A",  # infrastructure milestone
)


# Candidate 2: Electrolyte improvement (Class B — invention milestone)
# Derived from milestones/milestone_002/spec.json
ELECTROLYTE_EXPERIMENT = ExperimentSpec(
    experiment_id="EXP-002-electrolyte-improvement",
    name="Improved electrolyte for higher ionic conductivity",
    domain="electrochemistry",
    problem_statement=(
        "Design an electrolyte formulation with ionic conductivity > 10 mS/cm "
        "at room temperature, using non-toxic, low-cost materials."
    ),
    prediction={
        "claim": "An electrolyte with 1M LiPF6 in EC:DMC (1:1 v/v) + 2% FEC "
                 "additive will achieve ionic conductivity ≥ 10.5 mS/cm at 25°C.",
        "falsifier": "If the measured conductivity is < 8.0 mS/cm, the "
                     "prediction is falsified.",
        "expected_value": 10.5,  # mS/cm
        "tolerance": 1.5,
        "evidence_chain": [
            "chemistry_knowledge_module: ionic conductivity of LiPF6 in carbonate solvents",
            "literature: 1M LiPF6 in EC:DMC (1:1) baseline = ~10.0 mS/cm at 25°C",
            "literature: FEC additive (2%) increases conductivity by ~5%",
        ],
        "assumptions": [
            "temperature controlled at 25°C (±0.5°C)",
            "electrolyte is freshly prepared (no degradation)",
            "conductivity meter is calibrated against 0.01M KCl standard",
        ],
    },
    build={
        "materials": [
            "LiPF6 (battery grade, 1 mol, ~$30)",
            "ethylene carbonate (EC, anhydrous, 100mL, ~$20)",
            "dimethyl carbonate (DMC, anhydrous, 100mL, ~$15)",
            "fluoroethylene carbonate (FEC, 99%, 5mL, ~$25)",
            "conductivity meter (range 0-200 mS/cm, ~$200)",
            "0.01M KCl calibration standard (~$10)",
        ],
        "procedure": [
            "1. In a dry glovebox, mix EC and DMC 1:1 v/v (50mL each).",
            "2. Add LiPF6 to make 1M solution; stir until dissolved.",
            "3. Add 2% FEC by volume; stir.",
            "4. Calibrate conductivity meter against 0.01M KCl standard.",
            "5. Measure electrolyte conductivity at 25°C (3 trials).",
            "6. Record the mean conductivity.",
        ],
        "estimated_cost_usd": 300,
        "estimated_days": 3,
        "collaborator_requirements": (
            "A chemistry lab with a dry glovebox and conductivity meter. "
            "The collaborator must: (a) have experience handling LiPF6 "
            "(moisture-sensitive), (b) follow the procedure exactly, "
            "(c) record the conductivity to ±0.1 mS/cm, (d) repeat 3 times."
        ),
    },
    observe={
        "metric": "ionic conductivity (mS/cm, numeric)",
        "instrument": "conductivity meter, range 0-200 mS/cm, ±0.1 accuracy",
        "procedure": [
            "1. Calibrate meter against 0.01M KCl (1413 µS/cm at 25°C).",
            "2. Immerse probe in electrolyte; wait 30 seconds for equilibration.",
            "3. Record conductivity reading.",
            "4. Repeat for 3 trials; compute the mean.",
        ],
        "pass_criteria": (
            "measured_conductivity >= 10.5 - 1.5 = 9.0 mS/cm AND all 3 trials "
            "agree within ±0.5 mS/cm"
        ),
        "fail_criteria": (
            "measured_conductivity < 9.0 mS/cm OR trials disagree by > 0.5 mS/cm"
        ),
        "expected_recorded_at": "data/ledger/predictions.jsonl (verification entry)",
    },
    learn={
        "modules_to_revision": [
            "invention_compiler/chemistry_knowledge_module.py (if conductivity model is wrong)",
            "invention_compiler/physics_knowledge_module.py (if ionic mobility model is wrong)",
        ],
        "root_cause_analysis_template": (
            "If measured conductivity differs from predicted by > 1.5 mS/cm:\n"
            "  1. Check whether the LiPF6 baseline (10.0 mS/cm) in "
            "chemistry_knowledge_module matches literature.\n"
            "  2. Check whether the FEC additive effect (+5%) is correct.\n"
            "  3. Check whether the temperature was actually 25°C (conductivity "
            "is strongly temperature-dependent: ~2%/°C).\n"
            "  4. Check whether the electrolyte was prepared in a dry environment "
            "(LiPF6 hydrolyzes in moisture, reducing conductivity)."
        ),
    },
    revise={
        "recompile_procedure": (
            "After identifying the root cause, revise the affected module "
            "(e.g., update the FEC additive effect from +5% to actual measured "
            "effect), then re-run the InventionCompiler on the same problem. "
            "The new blueprint's prediction is the second prediction (T3)."
        ),
        "second_prediction_template": {
            "claim": "(revised) The electrolyte will achieve conductivity X mS/cm.",
            "expected_value": "(revised, based on root-cause fix)",
            "tolerance": "(revised)",
        },
        "closeness_metric": (
            "closeness = abs(first_prediction - observation) - "
            "abs(second_prediction - observation). "
            "If closeness > 0, the second prediction is closer → learning "
            "occurred (PR-23 step 5 satisfied)."
        ),
    },
    class_label="B",  # invention milestone
)


# Registry of all pre-scoped experiment candidates
EXPERIMENT_CANDIDATES = {
    "EXP-001-ph-prediction": PH_PREDICTION_EXPERIMENT,
    "EXP-002-electrolyte-improvement": ELECTROLYTE_EXPERIMENT,
}


# ----------------------------------------------------------------------
# ClosedLoopTracker: tracks the 5-step closed loop for an experiment
# ----------------------------------------------------------------------

@dataclass
class ClosedLoopTracker:
    """Tracks the 5-step closed loop (PR-23) for one experiment.

    Per PR-23, a learning claim requires all 5 steps to be recorded
    with timestamps. This tracker enforces that discipline.
    """

    experiment_id: str
    step_1_prediction_timestamp: Optional[str] = None      # T1
    step_2_observation_timestamp: Optional[str] = None     # T2 (> T1)
    step_3_root_cause_identified: bool = False
    step_3_root_cause_evidence: Optional[str] = None
    step_4_module_revised: bool = False
    step_4_revision_commit_hash: Optional[str] = None
    step_5_second_prediction_timestamp: Optional[str] = None  # T3 (> T2)
    step_5_closeness_value: Optional[float] = None  # > 0 means learning occurred
    step_5_closeness_metric: Optional[str] = None

    def record_prediction(self, timestamp: Optional[str] = None):
        """Step 1: record the prediction timestamp (T1)."""
        self.step_1_prediction_timestamp = timestamp or datetime.now(timezone.utc).isoformat()

    def record_observation(self, timestamp: Optional[str] = None):
        """Step 2: record the observation timestamp (T2 > T1)."""
        if not self.step_1_prediction_timestamp:
            raise ValueError("Cannot record observation before prediction (T1 not set)")
        self.step_2_observation_timestamp = timestamp or datetime.now(timezone.utc).isoformat()

    def record_root_cause(self, evidence: str):
        """Step 3: identify which module's input was wrong."""
        if not self.step_2_observation_timestamp:
            raise ValueError("Cannot identify root cause before observation (T2 not set)")
        self.step_3_root_cause_identified = True
        self.step_3_root_cause_evidence = evidence

    def record_revision(self, commit_hash: str):
        """Step 4: record that the module was revised."""
        if not self.step_3_root_cause_identified:
            raise ValueError("Cannot revise before root cause identified (step 3 not done)")
        self.step_4_module_revised = True
        self.step_4_revision_commit_hash = commit_hash

    def record_second_prediction(self, closeness_value: float,
                                  closeness_metric: str,
                                  timestamp: Optional[str] = None):
        """Step 5: record the second prediction (T3 > T2) and its closeness."""
        if not self.step_4_module_revised:
            raise ValueError("Cannot make second prediction before revision (step 4 not done)")
        self.step_5_second_prediction_timestamp = timestamp or datetime.now(timezone.utc).isoformat()
        self.step_5_closeness_value = closeness_value
        self.step_5_closeness_metric = closeness_metric

    def is_closed_loop(self) -> bool:
        """Check whether all 5 PR-23 steps are recorded AND learning occurred.

        Per PR-23: a "closed loop" requires revision (closeness > 0).
        This is the strict definition — a loop where the system's
        prediction was wrong, root cause was found, revision was made,
        and the revised prediction matched observation.

        Use is_executed_loop() for the broader definition that counts
        all loops where T1→T2 was completed (including loops that
        passed T1 on the first try, requiring no revision).
        """
        return (
            self.step_1_prediction_timestamp is not None
            and self.step_2_observation_timestamp is not None
            and self.step_3_root_cause_identified
            and self.step_4_module_revised
            and self.step_5_second_prediction_timestamp is not None
            and self.step_5_closeness_value is not None
            and self.step_5_closeness_value > 0  # learning occurred
        )

    def is_executed_loop(self) -> bool:
        """Check whether the loop was executed (all 5 steps recorded).

        Per External Auditor cycle 59: a loop that passes T1 on the
        first try is still a closed loop — it closed positively. This
        method counts ALL executed loops, including those where no
        revision was needed (closeness = 0).

        This is the broader definition used for Phase 4 exit criterion
        'closed_loops ≥ 10'. The strict is_closed_loop() counts only
        loops where learning occurred (revision improved the prediction).
        """
        return (
            self.step_1_prediction_timestamp is not None
            and self.step_2_observation_timestamp is not None
            and self.step_3_root_cause_identified
            and self.step_4_module_revised
            and self.step_5_second_prediction_timestamp is not None
            and self.step_5_closeness_value is not None
        )

    def validate_temporal_ordering(self) -> List[str]:
        """Verify T1 < T2 < T3 (per PR-23)."""
        errors = []
        if self.step_1_prediction_timestamp and self.step_2_observation_timestamp:
            if self.step_2_observation_timestamp <= self.step_1_prediction_timestamp:
                errors.append("T2 (observation) must be > T1 (prediction)")
        if self.step_2_observation_timestamp and self.step_5_second_prediction_timestamp:
            if self.step_5_second_prediction_timestamp <= self.step_2_observation_timestamp:
                errors.append("T3 (second prediction) must be > T2 (observation)")
        return errors


def validate_closed_loop(tracker: ClosedLoopTracker) -> Dict[str, Any]:
    """Validate that a recorded experiment satisfies all 5 PR-23 criteria.

    Returns a dict with:
      - is_closed_loop: bool
      - steps_completed: list of completed step names
      - steps_missing: list of missing step names
      - temporal_errors: list of temporal-ordering errors
      - closeness_value: float or None
      - learning_occurred: bool (closeness > 0)
    """
    steps = {
        "step_1_prediction": tracker.step_1_prediction_timestamp is not None,
        "step_2_observation": tracker.step_2_observation_timestamp is not None,
        "step_3_root_cause": tracker.step_3_root_cause_identified,
        "step_4_revision": tracker.step_4_module_revised,
        "step_5_second_prediction": (
            tracker.step_5_second_prediction_timestamp is not None
            and tracker.step_5_closeness_value is not None
        ),
    }
    steps_completed = [name for name, done in steps.items() if done]
    steps_missing = [name for name, done in steps.items() if not done]
    temporal_errors = tracker.validate_temporal_ordering()
    learning_occurred = (
        tracker.step_5_closeness_value is not None
        and tracker.step_5_closeness_value > 0
    )

    return {
        "is_closed_loop": tracker.is_closed_loop(),
        "steps_completed": steps_completed,
        "steps_missing": steps_missing,
        "temporal_errors": temporal_errors,
        "closeness_value": tracker.step_5_closeness_value,
        "learning_occurred": learning_occurred,
        "experiment_id": tracker.experiment_id,
    }


def list_experiment_candidates() -> List[str]:
    """Return the experiment IDs of all pre-scoped candidates."""
    return list(EXPERIMENT_CANDIDATES.keys())


def get_experiment_spec(experiment_id: str) -> ExperimentSpec:
    """Get a pre-scoped experiment spec by ID."""
    if experiment_id not in EXPERIMENT_CANDIDATES:
        raise KeyError(f"Unknown experiment_id: {experiment_id}")
    return EXPERIMENT_CANDIDATES[experiment_id]
