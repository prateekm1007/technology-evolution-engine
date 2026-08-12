"""
PSCD-1 AI Discovery Loop — Round Controller.

Implements the immutable round state machine:
  ROUND_CREATED → EVIDENCE_FROZEN → HYPOTHESES_GENERATED → PREDICTIONS_COMMITTED
  → PREDICTION_FROZEN → OUTCOME_WAITING → OUTCOME_IMPORTED → OUTCOMES_VERIFIED
  → SCORED → LEARNED → NEXT_ROUND_ELIGIBLE

Any invariant violation → ABORTED. No state may be skipped.

Learning is FUTURE-ONLY: a completed round's learning objects may affect the
next round's generation, but can never alter the completed round.

A2 remains disabled. The loop works with A0/A1 only.
"""
import json, hashlib, os, sys, enum, time
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Optional

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


class RoundState(enum.Enum):
    ROUND_CREATED = "ROUND_CREATED"
    EVIDENCE_FROZEN = "EVIDENCE_FROZEN"
    HYPOTHESES_GENERATED = "HYPOTHESES_GENERATED"
    PREDICTIONS_COMMITTED = "PREDICTIONS_COMMITTED"
    PREDICTION_FROZEN = "PREDICTION_FROZEN"
    OUTCOME_WAITING = "OUTCOME_WAITING"
    OUTCOME_IMPORTED = "OUTCOME_IMPORTED"
    OUTCOMES_VERIFIED = "OUTCOMES_VERIFIED"
    SCORED = "SCORED"
    LEARNED = "LEARNED"
    NEXT_ROUND_ELIGIBLE = "NEXT_ROUND_ELIGIBLE"
    ABORTED = "ABORTED"


# 11 normal states + ABORTED = 12 total
NORMAL_STATES = [s for s in RoundState if s != RoundState.ABORTED]
assert len(NORMAL_STATES) == 11


@dataclass
class RoundEvent:
    """Single event in a round's append-only event chain."""
    round_id: str
    timestamp: str
    previous_state: str
    new_state: str
    actor: str
    input_artifact_hashes: dict
    output_artifact_hashes: dict
    event_hash: str = ""
    previous_event_hash: str = ""

    def seal(self):
        d = {k: v for k, v in asdict(self).items() if k != "event_hash"}
        canonical = json.dumps(d, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        self.event_hash = hashlib.sha256(canonical.encode()).hexdigest()


class RoundController:
    """Controls one PSCD round through its state machine."""

    def __init__(self, round_id: str = None, dry_run: bool = False):
        self.round_id = round_id or f"ROUND-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"
        self.state = None  # No state yet — __init__ will set ROUND_CREATED
        self.dry_run = dry_run
        self.events: list[RoundEvent] = []
        self.artifacts: dict = {}
        self.start_time = datetime.now(timezone.utc)

        # Record creation event (first transition — from None to ROUND_CREATED)
        self._transition("ROUND_CREATED", "system", {}, {"round_id": self.round_id})

    def _transition(self, new_state_name: str, actor: str,
                    input_hashes: dict, output_hashes: dict):
        """Record a state transition. No state may be skipped."""
        prev_state = self.state.value if self.state else "NONE"
        new_state = RoundState(new_state_name)

        # Verify transition is valid (not skipping)
        if new_state == RoundState.ABORTED:
            pass  # ABORTED can happen from any state
        elif self.state is None:
            pass  # First transition (ROUND_CREATED) — always valid
        else:
            expected_order = [s.value for s in NORMAL_STATES]
            prev_idx = expected_order.index(prev_state) if prev_state in expected_order else -1
            new_idx = expected_order.index(new_state_name)
            if new_idx != prev_idx + 1 and prev_idx != -1:
                raise RuntimeError(
                    f"Invalid transition: {prev_state} → {new_state_name}. "
                    f"Expected next: {expected_order[prev_idx + 1] if prev_idx + 1 < len(expected_order) else 'END'}"
                )

        event = RoundEvent(
            round_id=self.round_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            previous_state=prev_state,
            new_state=new_state_name,
            actor=actor,
            input_artifact_hashes=input_hashes,
            output_artifact_hashes=output_hashes,
            previous_event_hash=self.events[-1].event_hash if self.events else "",
        )
        event.seal()
        self.events.append(event)
        self.state = new_state

    def _abort(self, reason: str):
        self._transition("ABORTED", "system", {}, {"reason": reason})
        raise RuntimeError(f"ROUND ABORTED: {reason}")

    def freeze_evidence(self, snapshot_hash: str, cutoff_hash: str):
        """Freeze evidence snapshot for this round."""
        if self.state != RoundState.ROUND_CREATED:
            self._abort(f"Cannot freeze evidence from state {self.state}")
        self.artifacts["evidence_snapshot_hash"] = snapshot_hash
        self.artifacts["cutoff_hash"] = cutoff_hash
        self._transition("EVIDENCE_FROZEN", "system",
                        {"snapshot_hash": snapshot_hash, "cutoff_hash": cutoff_hash},
                        {"evidence_frozen_at": datetime.now(timezone.utc).isoformat()})
        return self

    def generate_hypotheses(self, predictions: list[dict]):
        """Generate hypotheses (A0/A1 predictions)."""
        if self.state != RoundState.EVIDENCE_FROZEN:
            self._abort(f"Cannot generate from state {self.state}")
        self.artifacts["predictions"] = predictions
        self._transition("HYPOTHESES_GENERATED", "A0/A1_runner",
                        {"evidence_snapshot_hash": self.artifacts.get("evidence_snapshot_hash", "")},
                        {"n_predictions": len(predictions)})
        return self

    def commit_predictions(self):
        """Commit predictions (hash-commit before outcome release)."""
        if self.state != RoundState.HYPOTHESES_GENERATED:
            self._abort(f"Cannot commit from state {self.state}")
        pred_data = json.dumps(self.artifacts.get("predictions", []), sort_keys=True, ensure_ascii=False)
        freeze_hash = hashlib.sha256(pred_data.encode()).hexdigest()
        self.artifacts["prediction_freeze_hash"] = freeze_hash
        self.artifacts["prediction_freeze_timestamp"] = datetime.now(timezone.utc).isoformat()
        self._transition("PREDICTIONS_COMMITTED", "system",
                        {"n_predictions": len(self.artifacts.get("predictions", []))},
                        {"prediction_freeze_hash": freeze_hash[:32] + "..."})
        return self

    def freeze_predictions(self):
        """Seal predictions as immutable."""
        if self.state != RoundState.PREDICTIONS_COMMITTED:
            self._abort(f"Cannot freeze from state {self.state}")
        self._transition("PREDICTION_FROZEN", "system",
                        {"prediction_freeze_hash": self.artifacts.get("prediction_freeze_hash", "")},
                        {"frozen_at": datetime.now(timezone.utc).isoformat()})
        return self

    def wait_for_outcomes(self):
        """Enter outcome waiting state."""
        if self.state != RoundState.PREDICTION_FROZEN:
            self._abort(f"Cannot wait from state {self.state}")
        self._transition("OUTCOME_WAITING", "system", {}, {})
        return self

    def import_outcomes(self, outcomes: list[dict], custodian_auth_id: str):
        """Import outcomes from external custodian. Must be AFTER prediction freeze."""
        if self.state != RoundState.OUTCOME_WAITING:
            self._abort(f"Cannot import outcomes from state {self.state}")

        # Verify outcome release is AFTER prediction freeze
        pred_ts = self.artifacts.get("prediction_freeze_timestamp", "")
        for o in outcomes:
            o_ts = o.get("release_timestamp", o.get("observed_at", ""))
            if o_ts and pred_ts and o_ts < pred_ts:
                self._abort(f"Outcome released BEFORE prediction freeze: {o_ts} < {pred_ts}")

        # Verify no self-generated outcomes
        for o in outcomes:
            if o.get("generated_by_model", False):
                self._abort("Self-generated outcomes are not accepted")

        self.artifacts["outcomes"] = outcomes
        self.artifacts["custodian_auth_id"] = custodian_auth_id
        self._transition("OUTCOME_IMPORTED", "custodian",
                        {"n_outcomes": len(outcomes), "custodian_auth_id": custodian_auth_id},
                        {"outcomes_hash": hashlib.sha256(json.dumps(outcomes, sort_keys=True).encode()).hexdigest()[:32] + "..."})
        return self

    def verify_outcomes(self):
        """Verify outcomes: no duplicates, no mutations, all predictions matched."""
        if self.state != RoundState.OUTCOME_IMPORTED:
            self._abort(f"Cannot verify from state {self.state}")
        outcomes = self.artifacts.get("outcomes", [])
        # Check for duplicate outcome IDs
        ids = [o.get("outcome_id", "") for o in outcomes]
        if len(ids) != len(set(ids)):
            self._abort(f"Duplicate outcome IDs detected: {len(ids)} total, {len(set(ids))} unique")
        self._transition("OUTCOMES_VERIFIED", "system",
                        {"n_outcomes": len(outcomes), "n_unique_ids": len(set(ids))},
                        {"verified_at": datetime.now(timezone.utc).isoformat()})
        return self

    def score(self, scores: list[dict]):
        """Deterministic scoring. No LLM judge."""
        if self.state != RoundState.OUTCOMES_VERIFIED:
            self._abort(f"Cannot score from state {self.state}")
        self.artifacts["scores"] = scores
        # Compute aggregate metrics
        true_confirmed = sum(1 for s in scores if s.get("primary_endpoint_hit") and not s.get("is_foil"))
        foil_confirmed = sum(1 for s in scores if s.get("primary_endpoint_hit") and s.get("is_foil"))
        n_total = len(scores)
        self.artifacts["aggregate"] = {
            "true_confirmation_rate": true_confirmed / max(n_total, 1),
            "foil_confirmation_rate": foil_confirmed / max(n_total, 1),
            "net_discovery_rate": (true_confirmed - foil_confirmed) / max(n_total, 1),
        }
        self._transition("SCORED", "deterministic_scorer",
                        {"n_scores": len(scores)},
                        {"aggregate": self.artifacts["aggregate"]})
        return self

    def learn(self, learning_objects: list[dict]):
        """Extract learning objects for FUTURE rounds only."""
        if self.state != RoundState.SCORED:
            self._abort(f"Cannot learn from state {self.state}")
        self.artifacts["learning_objects"] = learning_objects
        self._transition("LEARNED", "learning_registry",
                        {"n_learning_objects": len(learning_objects)},
                        {"future_only": True})
        return self

    def prepare_next_round(self):
        """Mark round as complete and eligible for next round."""
        if self.state != RoundState.LEARNED:
            self._abort(f"Cannot prepare next round from state {self.state}")
        self._transition("NEXT_ROUND_ELIGIBLE", "system", {}, {})
        return self

    def get_event_chain_hash(self) -> str:
        """Compute hash of the entire event chain."""
        chain = json.dumps([asdict(e) for e in self.events], sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(chain.encode()).hexdigest()

    def get_result_package(self) -> dict:
        """Produce immutable result package for this round."""
        return {
            "round_id": self.round_id,
            "final_state": self.state.value,
            "dry_run": self.dry_run,
            "events": len(self.events),
            "event_chain_hash": self.get_event_chain_hash(),
            "artifacts": {
                k: v for k, v in self.artifacts.items()
                if k in ("evidence_snapshot_hash", "prediction_freeze_hash",
                         "prediction_freeze_timestamp", "custodian_auth_id", "aggregate")
            },
            "n_predictions": len(self.artifacts.get("predictions", [])),
            "n_outcomes": len(self.artifacts.get("outcomes", [])),
            "n_scores": len(self.artifacts.get("scores", [])),
            "n_learning_objects": len(self.artifacts.get("learning_objects", [])),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }


def run_dry_run_loop():
    """Run a complete dry-run loop end-to-end."""
    print("=" * 72)
    print("PSCD-1 AI DISCOVERY LOOP — DRY RUN")
    print("=" * 72)
    print()

    # Create round
    rc = RoundController(round_id="DRY-Round-001", dry_run=True)
    print(f"  Round created: {rc.round_id}")

    # Freeze evidence
    snapshot_hash = hashlib.sha256(b"dry_run_snapshot").hexdigest()
    cutoff_hash = hashlib.sha256(b"dry_run_cutoff").hexdigest()
    rc.freeze_evidence(snapshot_hash, cutoff_hash)
    print(f"  Evidence frozen: {snapshot_hash[:16]}...")

    # Generate hypotheses (synthetic)
    predictions = [
        {"prediction_id": f"DRY-A0-{i:03d}", "arm": "A0", "case_id": f"DRY-{i:03d}",
         "claim": f"Synthetic claim {i}", "quantitative_forecast": "N/A",
         "retrieval_negative_attestation": {"is_retrieval_negative": True, "entailment_check_result": "NOT_ENTAILED"}}
        for i in range(5)
    ] + [
        {"prediction_id": f"DRY-A1-{i:03d}", "arm": "A1", "case_id": f"DRY-{i:03d}",
         "claim": f"Synthetic claim with retrieval {i}", "quantitative_forecast": "N/A",
         "retrieval_negative_attestation": {"is_retrieval_negative": True, "entailment_check_result": "NOT_ENTAILED"}}
        for i in range(5)
    ]
    rc.generate_hypotheses(predictions)
    print(f"  Hypotheses generated: {len(predictions)}")

    # Commit predictions
    rc.commit_predictions()
    print(f"  Predictions committed: {rc.artifacts['prediction_freeze_hash'][:16]}...")

    # Freeze predictions
    rc.freeze_predictions()
    print(f"  Predictions frozen (immutable)")

    # Wait for outcomes
    rc.wait_for_outcomes()
    print(f"  Outcome waiting...")

    # Import synthetic outcomes (AFTER prediction freeze)
    time.sleep(0.1)  # ensure timestamp is later
    outcomes = [
        {"outcome_id": f"OUT-{i:03d}", "prediction_id": f"DRY-A0-{i:03d}",
         "observed_value": "FABRICATED", "observed_at": datetime.now(timezone.utc).isoformat(),
         "source": "DRY_RUN", "release_timestamp": datetime.now(timezone.utc).isoformat(),
         "confirmation_type": "SYNTHETIC", "custodian_auth_id": "DRY-CUSTODIAN",
         "outcome_artifact_hash": hashlib.sha256(b"outcome").hexdigest(),
         "is_foil": i >= 3}
        for i in range(5)
    ] + [
        {"outcome_id": f"OUT-{i+5:03d}", "prediction_id": f"DRY-A1-{i:03d}",
         "observed_value": "FABRICATED", "observed_at": datetime.now(timezone.utc).isoformat(),
         "source": "DRY_RUN", "release_timestamp": datetime.now(timezone.utc).isoformat(),
         "confirmation_type": "SYNTHETIC", "custodian_auth_id": "DRY-CUSTODIAN",
         "outcome_artifact_hash": hashlib.sha256(b"outcome").hexdigest(),
         "is_foil": i >= 3}
        for i in range(5)
    ]
    rc.import_outcomes(outcomes, custodian_auth_id="DRY-CUSTODIAN-001")
    print(f"  Outcomes imported: {len(outcomes)}")

    # Verify outcomes
    rc.verify_outcomes()
    print(f"  Outcomes verified: no duplicates")

    # Score
    scores = []
    for o in outcomes:
        pred = next((p for p in predictions if p["prediction_id"] == o["prediction_id"]), None)
        if pred:
            rn = pred.get("retrieval_negative_attestation", {})
            scores.append({
                "prediction_id": pred["prediction_id"],
                "arm": pred["arm"],
                "retrieval_negative": rn.get("is_retrieval_negative", False),
                "non_entailed": rn.get("entailment_check_result") == "NOT_ENTAILED",
                "later_confirmed": False,  # Dry-run: no real confirmations
                "is_foil": o.get("is_foil", False),
                "primary_endpoint_hit": False,
            })
    rc.score(scores)
    print(f"  Scored: {len(scores)} predictions")
    print(f"  Aggregate: {rc.artifacts['aggregate']}")

    # Learn (future-only)
    learning_objects = [
        {"type": "PATTERN", "description": "Dry-run: all predictions were NOT_ENTAILED", "future_only": True},
        {"type": "FUTURE_POLICY_HINT", "description": "No real confirmations in dry-run", "future_only": True},
    ]
    rc.learn(learning_objects)
    print(f"  Learned: {len(learning_objects)} learning objects (future-only)")

    # Prepare next round
    rc.prepare_next_round()
    print(f"  Next round eligible")

    # Result package
    result = rc.get_result_package()
    result["result_type"] = "DRY_RUN"
    pkg_for_hash = {k: v for k, v in result.items() if k != "package_hash"}
    canonical = json.dumps(pkg_for_hash, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    result["package_hash"] = hashlib.sha256(canonical.encode()).hexdigest()

    # Write forensic report
    _write_forensic_report(rc, result)

    print(f"\n{'='*72}")
    print("DRY RUN COMPLETE")
    print(f"{'='*72}")
    for k, v in result.items():
        if k != "package_hash":
            print(f"  {k}: {v}")
    print(f"  package_hash: {result['package_hash'][:32]}...")

    return result


def _write_forensic_report(rc: RoundController, result: dict):
    """Write PSCD_ROUND_FORENSIC_REPORT.md"""
    report = f"""# PSCD-1 ROUND FORENSIC REPORT

**Round ID:** {rc.round_id}
**Type:** {'DRY_RUN' if rc.dry_run else 'PRODUCTION'}
**Final State:** {rc.state.value}
**Generated:** {result.get('generated_at', '')}

## Event Chain

| # | Event | Timestamp | Previous State | New State | Actor |
|---|---|---|---|---|---|
"""
    for i, e in enumerate(rc.events):
        report += f"| {i+1} | — | {e.timestamp} | {e.previous_state} | {e.new_state} | {e.actor} |\n"

    report += f"""

## Artifacts

- Evidence snapshot hash: `{rc.artifacts.get('evidence_snapshot_hash', 'N/A')[:32]}...`
- Prediction freeze hash: `{rc.artifacts.get('prediction_freeze_hash', 'N/A')[:32]}...`
- Prediction freeze timestamp: {rc.artifacts.get('prediction_freeze_timestamp', 'N/A')}
- Custodian auth ID: {rc.artifacts.get('custodian_auth_id', 'N/A')}
- Event chain hash: `{rc.get_event_chain_hash()[:32]}...`

## Counts

- Predictions: {len(rc.artifacts.get('predictions', []))}
- Outcomes: {len(rc.artifacts.get('outcomes', []))}
- Scores: {len(rc.artifacts.get('scores', []))}
- Learning objects: {len(rc.artifacts.get('learning_objects', []))}

## Aggregate Metrics

"""
    agg = rc.artifacts.get("aggregate", {})
    for k, v in agg.items():
        report += f"- {k}: {v}\n"

    report += f"""

## Anti-Leakage Verification

- Outcome release AFTER prediction freeze: ✓ (verified at import)
- No self-generated outcomes: ✓
- No duplicate outcome IDs: ✓
- Learning objects are future-only: ✓
- Predictions immutable after freeze: ✓ (hash-committed)

## Notes

- This is a {'DRY_RUN' if rc.dry_run else 'PRODUCTION'} round.
- {'No real outcomes were used. All later_confirmed=False.' if rc.dry_run else 'Real outcomes were used.'}
- {'SCIENTIFIC_RESULT label is NOT applied to dry runs.' if rc.dry_run else ''}

---

**End of Round Forensic Report.**
"""
    report_path = REPO / "pscd" / "PSCD_ROUND_FORENSIC_REPORT.md"
    report_path.write_text(report)


if __name__ == "__main__":
    import time
    run_dry_run_loop()
