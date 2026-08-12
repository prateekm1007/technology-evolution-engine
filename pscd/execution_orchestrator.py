"""
PSCD-1 Execution Orchestrator — Fail-Closed State Machine.

States:
  BLOCKED -> SEAL_VERIFIED -> PROTOCOL_VERIFIED -> PREDICTION_WINDOW_OPEN
  -> PREDICTIONS_COMMITTED -> PREDICTION_FREEZE_SEALED -> OUTCOME_RELEASE_AUTHORIZED
  -> SCORED -> ANALYZED -> DECISION_SEALED

Any invariant violation -> ABORTED (cannot continue automatically).

Automation may NEVER manufacture, infer, or substitute a real outcome seal.
"""
import json, hashlib, os, sys, time, enum
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from pscd.execution_gate import compute_gates
from pscd.real_seal_verifier import verify_real_seal


class OrchestratorState(enum.Enum):
    BLOCKED = "BLOCKED"
    SEAL_VERIFIED = "SEAL_VERIFIED"
    PROTOCOL_VERIFIED = "PROTOCOL_VERIFIED"
    PREDICTION_WINDOW_OPEN = "PREDICTION_WINDOW_OPEN"
    PREDICTIONS_COMMITTED = "PREDICTIONS_COMMITTED"
    PREDICTION_FREEZE_SEALED = "PREDICTION_FREEZE_SEALED"
    OUTCOME_RELEASE_AUTHORIZED = "OUTCOME_RELEASE_AUTHORIZED"
    SCORED = "SCORED"
    ANALYZED = "ANALYZED"
    DECISION_SEALED = "DECISION_SEALED"
    ABORTED = "ABORTED"


class ExecutionOrchestrator:
    """Fail-closed state machine for PSCD-1 execution."""

    def __init__(self, dry_run: bool = False):
        self.state = OrchestratorState.BLOCKED
        self.dry_run = dry_run
        self.event_log = []
        self.artifacts = {}
        self.start_time = datetime.now(timezone.utc)

    def _log(self, event: str, data: dict = None):
        entry = {
            "event": event,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "state": self.state.value,
            "data": data or {},
        }
        self.event_log.append(entry)
        icon = "✓" if "VERIFIED" in event or "PASS" in event or "COMMITTED" in event else "→"
        print(f"  {icon} [{self.state.value}] {event}")

    def _abort(self, reason: str):
        self.state = OrchestratorState.ABORTED
        self._log("ABORTED", {"reason": reason})
        raise RuntimeError(f"ORCHESTRATOR ABORTED: {reason}")

    def run(self):
        """Execute the full state machine. Returns final state + artifacts."""
        print("=" * 72)
        print(f"PSCD-1 EXECUTION ORCHESTRATOR {'(DRY RUN)' if self.dry_run else '(PRODUCTION)'}")
        print("=" * 72)
        print()

        # State 1: BLOCKED -> SEAL_VERIFIED
        self._verify_seal()

        # State 2: SEAL_VERIFIED -> PROTOCOL_VERIFIED
        self._verify_protocol()

        # State 3: PROTOCOL_VERIFIED -> PREDICTION_WINDOW_OPEN
        self._open_prediction_window()

        # State 4: PREDICTION_WINDOW_OPEN -> PREDICTIONS_COMMITTED
        self._run_predictions()

        # State 5: PREDICTIONS_COMMITTED -> PREDICTION_FREEZE_SEALED
        self._freeze_predictions()

        # State 6: PREDICTION_FREEZE_SEALED -> OUTCOME_RELEASE_AUTHORIZED
        self._authorize_outcome_release()

        # State 7: OUTCOME_RELEASE_AUTHORIZED -> SCORED
        self._score()

        # State 8: SCORED -> ANALYZED
        self._analyze()

        # State 9: ANALYZED -> DECISION_SEALED
        self._seal_decision()

        self._log("COMPLETE")
        return self._produce_result_package()

    def _verify_seal(self):
        """Verify the external custodian seal."""
        self._log("VERIFYING_SEAL")
        seal = verify_real_seal()
        if not seal["valid"] and not self.dry_run:
            self._abort(f"Seal verification failed: {seal['reason']}")
        if self.dry_run and not seal["valid"]:
            self._log("SEAL_BYPASSED_DRY_RUN", {"reason": seal["reason"]})
        else:
            self._log("SEAL_VERIFIED", {"seal_id": seal.get("seal_id", "")})
        self.artifacts["seal"] = seal
        self.state = OrchestratorState.SEAL_VERIFIED

    def _verify_protocol(self):
        """Verify all frozen protocol artifacts."""
        self._log("VERIFYING_PROTOCOL")
        gates = compute_gates()
        # In dry-run, skip REAL_SEAL_READY
        required = [k for k in gates if k not in ("REAL_SEAL_READY", "SCIENTIFIC_EXECUTION_PERMITTED",
                    "A2_AUTHORIZATION_REQUESTED", "blocking_items", "generated_at", "gate_hash")]
        failed = [k for k in required if not gates.get(k, False)]
        if failed and not self.dry_run:
            self._abort(f"Protocol verification failed: {failed}")
        if failed:
            self._log("PROTOCOL_PARTIAL_DRY_RUN", {"failed": failed})
        else:
            self._log("PROTOCOL_VERIFIED", {"gate_hash": gates.get("gate_hash", "")[:32]})
        self.artifacts["gates"] = gates
        self.state = OrchestratorState.PROTOCOL_VERIFIED

    def _open_prediction_window(self):
        """Open the prediction generation window."""
        self._log("OPENING_PREDICTION_WINDOW")
        self.artifacts["prediction_window_opened_at"] = datetime.now(timezone.utc).isoformat()
        self._log("PREDICTION_WINDOW_OPEN")
        self.state = OrchestratorState.PREDICTION_WINDOW_OPEN

    def _run_predictions(self):
        """Run A0 and A1 for each case. Hash-commit predictions."""
        self._log("RUNNING_PREDICTIONS")
        if self.dry_run:
            # Dry-run: use synthetic predictions
            predictions = [
                {"prediction_id": f"DRY-A0-{i:03d}", "arm": "A0", "case_id": f"DRY-{i:03d}",
                 "claim": "Synthetic dry-run claim", "quantitative_forecast": "N/A",
                 "retrieval_negative_attestation": {"is_retrieval_negative": True,
                 "entailment_check_result": "NOT_ENTAILED"}}
                for i in range(5)
            ] + [
                {"prediction_id": f"DRY-A1-{i:03d}", "arm": "A1", "case_id": f"DRY-{i:03d}",
                 "claim": "Synthetic dry-run claim with retrieval", "quantitative_forecast": "N/A",
                 "retrieval_negative_attestation": {"is_retrieval_negative": True,
                 "entailment_check_result": "NOT_ENTAILED"}}
                for i in range(5)
            ]
        else:
            # Production: run actual A0/A1 runners
            from pscd_v7_final_measurement import run_arm_v7
            snapshot = json.load(open(REPO / "pscd/retrieval_snapshot_v1.json"))
            # Would iterate over sealed cases — but we need the case set from the seal
            # For now, this path is blocked because REAL_SEAL_READY=FALSE
            self._abort("Production prediction run requires real sealed cases — not yet available")

        self.artifacts["predictions"] = predictions
        self.artifacts["prediction_count"] = len(predictions)
        self._log("PREDICTIONS_COMMITTED", {"count": len(predictions)})
        self.state = OrchestratorState.PREDICTIONS_COMMITTED

    def _freeze_predictions(self):
        """Hash the complete prediction set. Write PREDICTION_FREEZE.json."""
        self._log("FREEZING_PREDICTIONS")
        pred_data = json.dumps(self.artifacts.get("predictions", []), sort_keys=True, ensure_ascii=False)
        freeze_hash = hashlib.sha256(pred_data.encode()).hexdigest()
        freeze = {
            "prediction_freeze_hash": freeze_hash,
            "frozen_at": datetime.now(timezone.utc).isoformat(),
            "n_predictions": self.artifacts.get("prediction_count", 0),
            "dry_run": self.dry_run,
        }
        self.artifacts["prediction_freeze"] = freeze
        self._log("PREDICTION_FREEZE_SEALED", {"freeze_hash": freeze_hash[:32]})
        self.state = OrchestratorState.PREDICTION_FREEZE_SEALED

    def _authorize_outcome_release(self):
        """Verify outcome release is authorized AFTER prediction freeze."""
        self._log("AUTHORIZING_OUTCOME_RELEASE")
        if self.dry_run:
            self._log("OUTCOME_RELEASE_AUTHORIZED_DRY_RUN")
        else:
            # In production, the custodian must authorize release
            # This would check: custodian signature, timestamp ordering, etc.
            self._abort("Production outcome release requires custodian authorization — not yet available")
        self.state = OrchestratorState.OUTCOME_RELEASE_AUTHORIZED

    def _score(self):
        """Deterministic scoring. No LLM judging. No post-hoc thresholds."""
        self._log("SCORING")
        predictions = self.artifacts.get("predictions", [])

        # Dry-run scoring: all synthetic, no real confirmations
        scores = []
        for p in predictions:
            score = {
                "prediction_id": p["prediction_id"],
                "arm": p["arm"],
                "case_id": p["case_id"],
                "retrieval_negative": p.get("retrieval_negative_attestation", {}).get("is_retrieval_negative", False),
                "non_entailed": p.get("retrieval_negative_attestation", {}).get("entailment_check_result") == "NOT_ENTAILED",
                "later_confirmed": False,  # Dry-run: no real outcomes
                "is_foil": "FOIL" in p.get("case_id", ""),
                "primary_endpoint_hit": False,  # retrieval_negative + non_entailed + later_confirmed
            }
            score["primary_endpoint_hit"] = score["retrieval_negative"] and score["non_entailed"] and score["later_confirmed"]
            scores.append(score)

        self.artifacts["scores"] = scores
        self._log("SCORED", {"n_scores": len(scores)})
        self.state = OrchestratorState.SCORED

    def _analyze(self):
        """Compute aggregate metrics, foil analysis, confidence intervals."""
        self._log("ANALYZING")
        scores = self.artifacts.get("scores", [])

        # Per-arm analysis
        arms = {}
        for s in scores:
            arm = s["arm"]
            if arm not in arms:
                arms[arm] = {"n": 0, "true_confirmed": 0, "foil_confirmed": 0,
                            "retrieval_negative": 0, "non_entailed": 0}
            arms[arm]["n"] += 1
            if s["primary_endpoint_hit"] and not s["is_foil"]:
                arms[arm]["true_confirmed"] += 1
            if s["primary_endpoint_hit"] and s["is_foil"]:
                arms[arm]["foil_confirmed"] += 1
            if s["retrieval_negative"]:
                arms[arm]["retrieval_negative"] += 1
            if s["non_entailed"]:
                arms[arm]["non_entailed"] += 1

        for arm, m in arms.items():
            m["true_confirmation_rate"] = m["true_confirmed"] / max(m["n"], 1)
            m["foil_confirmation_rate"] = m["foil_confirmed"] / max(m["n"], 1)
            m["net_discovery_rate"] = m["true_confirmation_rate"] - m["foil_confirmation_rate"]

        self.artifacts["analysis"] = {
            "per_arm": arms,
            "primary_endpoint": "retrieval_negative + non_entailed + later_confirmed",
            "dry_run": self.dry_run,
            "note": "Dry-run: all later_confirmed=False. No real discovery claims." if self.dry_run else "",
        }
        self._log("ANALYZED")
        self.state = OrchestratorState.ANALYZED

    def _seal_decision(self):
        """Apply AINT-1 kill switch. Seal the decision."""
        self._log("SEALING_DECISION")
        analysis = self.artifacts.get("analysis", {})
        arms = analysis.get("per_arm", {})

        # AINT-1: if A2 - A1 <= 0, FABRIC_STATUS = RETIRED
        # (A2 not implemented — so A2 doesn't exist. Decision is N/A.)
        a1_rate = arms.get("A1", {}).get("net_discovery_rate", 0)
        a2_rate = arms.get("A2", {}).get("net_discovery_rate", 0)

        if a2_rate - a1_rate <= 0:
            fabric_status = "RETIRED" if "A2" in arms else "NOT_APPLICABLE"
        else:
            fabric_status = "PROVISIONAL_ADVANTAGE"

        decision = {
            "fabric_status": fabric_status,
            "aint_1_result": "A2_NOT_RUN" if "A2" not in arms else ("RETIRED" if a2_rate <= a1_rate else "PROVISIONAL_ADVANTAGE"),
            "a0_net_discovery_rate": arms.get("A0", {}).get("net_discovery_rate", 0),
            "a1_net_discovery_rate": a1_rate,
            "a2_net_discovery_rate": a2_rate if "A2" in arms else None,
            "dry_run": self.dry_run,
            "decision_sealed_at": datetime.now(timezone.utc).isoformat(),
        }
        self.artifacts["decision"] = decision
        self._log("DECISION_SEALED", {"fabric_status": fabric_status})
        self.state = OrchestratorState.DECISION_SEALED

    def _produce_result_package(self) -> dict:
        """Produce the immutable result package."""
        event_chain = json.dumps(self.event_log, sort_keys=True, ensure_ascii=False)
        event_chain_hash = hashlib.sha256(event_chain.encode()).hexdigest()

        package = {
            "schema_version": "1.0.0",
            "result_type": "DRY_RUN" if self.dry_run else "SCIENTIFIC_RESULT",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "protocol_hash": self.artifacts.get("gates", {}).get("PREDICTION_PROTOCOL_HASH", ""),
            "gate_hash": self.artifacts.get("gates", {}).get("gate_hash", ""),
            "seal_id": self.artifacts.get("seal", {}).get("seal_id", ""),
            "prediction_freeze_hash": self.artifacts.get("prediction_freeze", {}).get("prediction_freeze_hash", ""),
            "n_predictions": self.artifacts.get("prediction_count", 0),
            "per_arm_analysis": self.artifacts.get("analysis", {}).get("per_arm", {}),
            "decision": self.artifacts.get("decision", {}),
            "event_chain_hash": event_chain_hash,
            "fabric_status": self.artifacts.get("decision", {}).get("fabric_status", ""),
            "aint_1_result": self.artifacts.get("decision", {}).get("aint_1_result", ""),
            "dry_run": self.dry_run,
        }

        # Seal
        pkg_for_hash = {k: v for k, v in package.items() if k != "package_hash"}
        canonical = json.dumps(pkg_for_hash, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        package["package_hash"] = hashlib.sha256(canonical.encode()).hexdigest()

        # Write forensic report
        self._write_forensic_report(package)

        return package

    def _write_forensic_report(self, package: dict):
        """Write PSCD_FORENSIC_RUN_REPORT.md"""
        report = f"""# PSCD-1 FORENSIC RUN REPORT

**Date:** {package['generated_at']}
**Type:** {package['result_type']}
**Package hash:** `{package.get('package_hash','')[:32]}...`

## Event Chain

| # | Event | Timestamp | State |
|---|---|---|---|
"""
        for i, e in enumerate(self.event_log):
            report += f"| {i+1} | {e['event']} | {e['timestamp']} | {e['state']} |\n"

        report += f"""

## Gate Results

"""
        gates = self.artifacts.get("gates", {})
        for k, v in gates.items():
            if k not in ("blocking_items", "generated_at", "gate_hash"):
                report += f"- {k}: {v}\n"

        report += f"""

## Prediction Freeze

- Hash: `{package.get('prediction_freeze_hash','')[:32]}...`
- N predictions: {package.get('n_predictions', 0)}

## Per-Arm Analysis

"""
        for arm, m in package.get("per_arm_analysis", {}).items():
            report += f"### {arm}\n"
            for k, v in m.items():
                report += f"- {k}: {v}\n"
            report += "\n"

        report += f"""## Decision

- FABRIC_STATUS: {package.get('fabric_status', '')}
- AINT-1: {package.get('aint_1_result', '')}

## Event Chain Hash

`{package.get('event_chain_hash', '')[:32]}...`

## Blocking Items

{gates.get('blocking_items', [])}

## Notes

- This is a {'DRY RUN' if self.dry_run else 'PRODUCTION'} run.
- {'No real outcomes were used. All later_confirmed=False.' if self.dry_run else 'Real outcomes were used.'}
- {'SCIENTIFIC_RESULT label is NOT applied to dry runs.' if self.dry_run else ''}

---

**End of Forensic Report.**
"""
        report_path = REPO / "pscd" / "PSCD_FORENSIC_RUN_REPORT.md"
        report_path.write_text(report)
        self._log("FORENSIC_REPORT_WRITTEN", {"path": str(report_path)})


def main():
    """Run the orchestrator in dry-run mode (plumbing test)."""
    orch = ExecutionOrchestrator(dry_run=True)
    try:
        result = orch.run()
        print(f"\n{'='*72}")
        print("ORCHESTRATOR RESULT")
        print(f"{'='*72}")
        for k, v in result.items():
            if k != "package_hash":
                print(f"  {k}: {v}")
        print(f"\n  package_hash: {result.get('package_hash','')[:32]}...")

        # Write result package
        Path(REPO / "pscd" / "PSCD_RESULT_PACKAGE.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False)
        )
        print(f"\n  Result package: pscd/PSCD_RESULT_PACKAGE.json")
        print(f"  Forensic report: pscd/PSCD_FORENSIC_RUN_REPORT.md")

    except RuntimeError as e:
        print(f"\n  ✗ {e}")
        sys.exit(1)

    print(f"\n  SCIENTIFIC_EXECUTION_PERMITTED: {result.get('fabric_status','') != 'NOT_APPLICABLE' and not result.get('dry_run', True)}")
    print(f"  REAL_SEAL_READY: False (dry-run)")
    print(f"  A2_AUTHORIZATION_REQUESTED: false")


if __name__ == "__main__":
    main()
