"""
PROSPECTIVE EXPERIMENT — Pre-Registered Analysis Plan
======================================================

Stage 7b of the prospective pipeline. Applies the pre-registered statistical
analysis to the scored receipts.

CRITICAL INVARIANTS:
    (I24) The analysis plan is the ONE in the pre-registration manifest.
         No other analysis plan may be applied.
    (I25) The analysis is applied ONLY AFTER all scores are computed.
    (I26) The analysis is deterministic given the scores.
    (I27) The analysis output is hash-sealed and appended to the log.

Statistical test:
    Two-proportion z-test for each treatment-vs-control comparison:
        H0: p_treatment = p_control
        H1: p_treatment > p_control (one-sided)
    Multiple testing correction: Bonferroni (num_comparisons from plan)
    Significance threshold: alpha from plan (default 0.05)
    Minimum detectable effect: mde from plan (default 0.15)

Decision rule (pre-registered, immutable):
    POSITIVE_RESULT requires ALL of:
      - At least `meaningful_min_novel` GENUINE_NOVEL_PREDICTION cases
        across the treatment arm (default 3)
      - Treatment DPS=1 rate >= random DPS=1 rate + `material_advantage_pp`
        (default 15pp)
      - z-test p-value < alpha / num_comparisons (Bonferroni)
      - At least 1 CORRECT case with calibration_error <= calibration_threshold
        (the predictions are quantitatively accurate, not just directionally)
    Otherwise: NEGATIVE_RESULT.

    INDETERMINATE cases handled per `indeterminate_handling` in plan:
      - "excluded": drop from denominator
      - "counted_as_failure": count as DPS=0

DO NOT RUN THIS MODULE until all scores are computed.
"""
from __future__ import annotations

import json
import hashlib
import math
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

REPO = Path("/home/z/my-project/audit/technology-evolution-engine")
PROSPECTIVE_DIR = REPO / "discovery_fabric/prospective"
SCORES_DIR = PROSPECTIVE_DIR / "scores"
LOG_FILE = PROSPECTIVE_DIR / "manifests" / "append_only_log.jsonl"

# Default thresholds (overridden by analysis_plan from manifest)
DEFAULT_MEANINGFUL_MIN_NOVEL = 3
DEFAULT_MATERIAL_ADVANTAGE_PP = 15.0


# =============================================================================
# Statistical test
# =============================================================================

def two_proportion_z_test(
    successes_treatment: int, n_treatment: int,
    successes_control: int, n_control: int,
) -> dict:
    """Two-proportion z-test (one-sided, H1: p_treatment > p_control).

    Returns dict with z_statistic, p_value, and notes.
    """
    if n_treatment == 0 or n_control == 0:
        return {"z_statistic": None, "p_value": None, "reason": "zero sample size"}

    p_treat = successes_treatment / n_treatment
    p_ctrl = successes_control / n_control
    # Pooled proportion
    p_pooled = (successes_treatment + successes_control) / (n_treatment + n_control)
    # Standard error under H0
    se = math.sqrt(p_pooled * (1 - p_pooled) * (1/n_treatment + 1/n_control))
    if se == 0:
        return {"z_statistic": None, "p_value": None,
                "reason": "zero standard error (both proportions identical or both 0/1)"}

    z = (p_treat - p_ctrl) / se
    # One-sided p-value (H1: p_treatment > p_control)
    # Use math.erfc for the standard normal CDF tail
    p_value = 0.5 * math.erfc(z / math.sqrt(2))

    return {
        "z_statistic": round(z, 4),
        "p_value": round(p_value, 6),
        "p_treatment": round(p_treat, 4),
        "p_control": round(p_ctrl, 4),
        "se": round(se, 4),
        "n_treatment": n_treatment,
        "n_control": n_control,
        "successes_treatment": successes_treatment,
        "successes_control": successes_control,
    }


# =============================================================================
# Apply pre-registered analysis
# =============================================================================

def apply_analysis(
    scores: list[dict],
    analysis_plan: dict,
) -> dict:
    """Apply the pre-registered analysis plan to the scores.

    Args:
        scores: list of score records (from deterministic_scorer)
        analysis_plan: the pre-registered analysis plan from the manifest

    Returns:
        Sealed analysis result.
    """
    alpha = analysis_plan.get("alpha", 0.05)
    mde = analysis_plan.get("mde", 0.15)
    indeterminate_handling = analysis_plan.get("indeterminate_handling", "excluded")
    cal_threshold = analysis_plan.get("calibration_threshold", 0.50)
    num_comparisons = analysis_plan.get("num_comparisons", 3)
    meaningful_min = analysis_plan.get("meaningful_min_novel", DEFAULT_MEANINGFUL_MIN_NOVEL)
    material_advantage = analysis_plan.get("material_advantage_pp", DEFAULT_MATERIAL_ADVANTAGE_PP)

    # Bonferroni-corrected alpha
    alpha_corrected = alpha / num_comparisons

    # Group scores by arm
    by_arm = {}
    for s in scores:
        arm = s.get("arm")
        if arm not in by_arm:
            by_arm[arm] = []
        by_arm[arm].append(s)

    # Compute per-arm metrics (apply indeterminate_handling)
    arm_metrics = {}
    for arm, arm_scores in by_arm.items():
        n_total = len(arm_scores)
        n_indeterminate = sum(1 for s in arm_scores if s["final_classification"] == "INDETERMINATE")
        if indeterminate_handling == "excluded":
            effective_scores = [s for s in arm_scores if s["final_classification"] != "INDETERMINATE"]
            n_effective = len(effective_scores)
        else:  # "counted_as_failure"
            effective_scores = arm_scores
            n_effective = n_total

        n_dps_1 = sum(1 for s in effective_scores if s["DISCOVERY_PREDICTION_SCORE"] == 1.0)
        n_correct = sum(1 for s in effective_scores if s["final_classification"] == "CORRECT")
        n_genuine_novel = sum(1 for s in effective_scores
                              if s["information_content"]["classification"] == "GENUINE_NOVEL_PREDICTION")
        n_reconstruction = sum(1 for s in effective_scores
                                if s["final_classification"] == "RECONSTRUCTION")
        n_incorrect = sum(1 for s in effective_scores if s["final_classification"] == "INCORRECT")

        # Quantitatively-accurate CORRECT cases (cal_error <= threshold)
        n_cal_accurate = sum(1 for s in effective_scores
                             if s["final_classification"] == "CORRECT"
                             and s["quantitative_accuracy"].get("calibration_error") is not None
                             and s["quantitative_accuracy"]["calibration_error"] <= cal_threshold)

        arm_metrics[arm] = {
            "n_total": n_total,
            "n_indeterminate": n_indeterminate,
            "n_effective": n_effective,
            "n_DPS_1": n_dps_1,
            "DPS_1_rate": round(n_dps_1 / max(n_effective, 1), 4),
            "n_correct": n_correct,
            "n_genuine_novel": n_genuine_novel,
            "n_reconstruction": n_reconstruction,
            "n_incorrect": n_incorrect,
            "n_cal_accurate": n_cal_accurate,
        }

    # Pairwise treatment-vs-control comparisons
    control_arm = "D_random"
    treatment_arms = [a for a in by_arm.keys() if a != control_arm]
    comparisons = {}
    for treat in treatment_arms:
        treat_metrics = arm_metrics.get(treat, {})
        ctrl_metrics = arm_metrics.get(control_arm, {})
        z_test = two_proportion_z_test(
            successes_treatment=treat_metrics.get("n_DPS_1", 0),
            n_treatment=treat_metrics.get("n_effective", 0),
            successes_control=ctrl_metrics.get("n_DPS_1", 0),
            n_control=ctrl_metrics.get("n_effective", 0),
        )
        treat_rate = treat_metrics.get("DPS_1_rate", 0)
        ctrl_rate = ctrl_metrics.get("DPS_1_rate", 0)
        advantage_pp = (treat_rate - ctrl_rate) * 100
        comparisons[treat] = {
            "treatment_arm": treat,
            "control_arm": control_arm,
            "treatment_DPS_1_rate": treat_rate,
            "control_DPS_1_rate": ctrl_rate,
            "advantage_pp": round(advantage_pp, 2),
            "z_test": z_test,
            "significant_at_corrected_alpha": (
                z_test.get("p_value") is not None
                and z_test["p_value"] < alpha_corrected
            ),
        }

    # Pre-registered decision rule
    # POSITIVE requires ALL of:
    #   - At least meaningful_min GENUINE_NOVEL across each treatment arm
    #   - Best treatment advantage_pp >= material_advantage
    #   - Best treatment z-test significant at corrected alpha
    #   - At least 1 cal_accurate CORRECT case in best treatment arm
    best_treatment = max(treatment_arms,
                          key=lambda a: arm_metrics.get(a, {}).get("DPS_1_rate", 0),
                          default=None)
    if best_treatment:
        best_metrics = arm_metrics[best_treatment]
        best_comparison = comparisons[best_treatment]
        gate_novel = best_metrics.get("n_genuine_novel", 0) >= meaningful_min
        gate_advantage = best_comparison["advantage_pp"] >= material_advantage
        gate_significance = best_comparison["significant_at_corrected_alpha"]
        gate_cal_accurate = best_metrics.get("n_cal_accurate", 0) >= 1
        decision = "POSITIVE_RESULT" if all([gate_novel, gate_advantage,
                                              gate_significance, gate_cal_accurate]) else "NEGATIVE_RESULT"
        decision_reason = (
            f"best_treatment={best_treatment} "
            f"gate_novel={gate_novel} (n_genuine_novel={best_metrics.get('n_genuine_novel', 0)} >= {meaningful_min}) "
            f"gate_advantage={gate_advantage} (advantage_pp={best_comparison['advantage_pp']} >= {material_advantage}) "
            f"gate_significance={gate_significance} (p={best_comparison['z_test'].get('p_value')} < {alpha_corrected}) "
            f"gate_cal_accurate={gate_cal_accurate} (n_cal_accurate={best_metrics.get('n_cal_accurate', 0)} >= 1)"
        )
    else:
        decision = "NEGATIVE_RESULT"
        decision_reason = "no treatment arm found"

    result = {
        "schema_version": "1.0.0",
        "result_type": "PRE_REGISTERED_ANALYSIS",
        "analysis_plan_applied": analysis_plan,
        "alpha_corrected": alpha_corrected,
        "arm_metrics": arm_metrics,
        "comparisons": comparisons,
        "best_treatment_arm": best_treatment,
        "decision": decision,
        "decision_reason": decision_reason,
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }

    # Seal
    canonical = json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    result["result_hash"] = hashlib.sha256(canonical.encode()).hexdigest()
    return result


def save_result(result: dict) -> Path:
    """Save the analysis result, append to log, and append to the tamper-evident
    audit chain as the FINAL ANALYSIS entry."""
    out_path = SCORES_DIR / "analysis_result.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    entry = {
        "log_entry_type": "PRE_REGISTERED_ANALYSIS",
        "result_hash": result["result_hash"],
        "timestamp": result["computed_at"],
        "decision": result["decision"],
        "best_treatment": result["best_treatment_arm"],
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    # Append to tamper-evident audit chain (FINAL ANALYSIS entry)
    from discovery_fabric.prospective.tamper_evident_chain import append_chain_entry
    append_chain_entry(
        entry_type="ANALYSIS",
        payload_hash=result["result_hash"],
        metadata={
            "decision": result["decision"],
            "best_treatment": result["best_treatment_arm"],
            "computed_at": result["computed_at"],
        },
    )
    return out_path


# =============================================================================
# NEW (Forensic Gate): Analysis plan immutability enforcement
# =============================================================================

def verify_analysis_plan_immutability(
    applied_plan: dict,
    manifest_plan: dict,
    observations: list[dict],
) -> tuple[bool, list[str]]:
    """Verify that the analysis plan was not modified after the first outcome
    was ingested.

    The analysis plan is sealed in the manifest at registration time (I5).
    This function additionally checks that the applied plan MATCHES the
    manifest plan exactly (I24), and that no observation was collected
    before the plan was sealed.

    Returns (all_ok, list_of_failures).
    """
    failures = []

    # Check that applied plan matches manifest plan on all key fields
    key_fields = ["alpha", "mde", "indeterminate_handling", "calibration_threshold",
                  "num_comparisons", "sample_size_per_arm", "primary_endpoint",
                  "comparison", "ic_threshold"]
    for k in key_fields:
        if applied_plan.get(k) != manifest_plan.get(k):
            failures.append(
                f"analysis_plan.{k}: applied={applied_plan.get(k)} vs "
                f"manifest={manifest_plan.get(k)} — plan was modified after sealing"
            )

    # Check that no observation was collected before the manifest's registration_timestamp
    # (the plan was sealed at registration, so any observation before that would
    # suggest the plan was modified to fit pre-known outcomes)
    manifest_ts = (
        applied_plan.get("registration_timestamp")
        or applied_plan.get("created_at")
    )
    if manifest_ts:
        try:
            mt = datetime.fromisoformat(manifest_ts.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            mt = None
        if mt:
            for obs in observations:
                coll = obs.get("collected_at")
                if coll:
                    try:
                        ct = datetime.fromisoformat(coll.replace("Z", "+00:00"))
                        if ct < mt:
                            failures.append(
                                f"observation {obs.get('problem_id')} collected_at {ct} "
                                f"is BEFORE plan-sealing timestamp {mt} — plan may have "
                                f"been modified after observing outcomes"
                            )
                    except (ValueError, TypeError):
                        failures.append(f"cannot parse collected_at: {coll}")

    return (len(failures) == 0, failures)


# =============================================================================
# Main — infrastructure check only
# =============================================================================

def main():
    """Verify the analysis infrastructure with synthetic scores."""
    print("=" * 72)
    print("PROSPECTIVE EXPERIMENT — PRE-REGISTERED ANALYSIS INFRASTRUCTURE CHECK")
    print("=" * 72)
    print()

    # Synthetic scores: 4 arms × 5 problems each
    arms = ["B_llm_only", "C_mechanism", "F_full", "D_random"]
    scores = []
    for arm in arms:
        for i in range(5):
            # F_full gets 2 CORRECT, others get 0
            if arm == "F_full" and i < 2:
                final = "CORRECT"
                dps = 1.0
                ic_class = "GENUINE_NOVEL_PREDICTION"
                cal = 0.1
            else:
                final = "INCORRECT"
                dps = 0.0
                ic_class = "GENUINE_NOVEL_PREDICTION"
                cal = 1.5
            scores.append({
                "candidate_id": f"PROS-{i:03d}-{arm}",
                "problem_id": f"PROS-{i:03d}",
                "arm": arm,
                "final_classification": final,
                "DISCOVERY_PREDICTION_SCORE": dps,
                "information_content": {"classification": ic_class, "information_content_score": 0.9},
                "quantitative_accuracy": {"verdict": final, "calibration_error": cal,
                                          "predicted": 100, "observed": 110, "tolerance_bounds": [50, 200]},
            })

    analysis_plan = {
        "alpha": 0.05,
        "mde": 0.15,
        "indeterminate_handling": "excluded",
        "calibration_threshold": 0.50,
        "num_comparisons": 3,
        "meaningful_min_novel": 3,
        "material_advantage_pp": 15.0,
    }

    result = apply_analysis(scores, analysis_plan)
    print(f"Synthetic analysis:")
    print(f"  Decision: {result['decision']}")
    print(f"  Best treatment: {result['best_treatment_arm']}")
    print(f"  Decision reason: {result['decision_reason']}")
    print(f"\nPer-arm metrics:")
    for arm, m in result["arm_metrics"].items():
        print(f"  {arm}: DPS_1_rate={m['DPS_1_rate']:.2f} ({m['n_DPS_1']}/{m['n_effective']}) "
              f"novel={m['n_genuine_novel']} cal_accurate={m['n_cal_accurate']}")
    print(f"\nComparisons:")
    for arm, c in result["comparisons"].items():
        print(f"  {arm} vs D_random: advantage={c['advantage_pp']:.1f}pp "
              f"p={c['z_test'].get('p_value')} sig={c['significant_at_corrected_alpha']}")
    print(f"\nResult hash: {result['result_hash'][:32]}...")

    print()
    print("Analysis infrastructure is in place. To run real analysis:")
    print("  1. Wait until all scores are computed")
    print("  2. Load the analysis plan FROM the pre-registration manifest")
    print("  3. Call apply_analysis(scores, analysis_plan)")
    print("  4. Save result and append to log")
    print()
    print("DO NOT apply any analysis plan other than the one in the manifest.")


if __name__ == "__main__":
    main()
