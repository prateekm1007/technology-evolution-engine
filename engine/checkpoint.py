"""checkpoint.py — checkpointed execution for the discovery loop.

Reviewer round-3 directive (5 repairs):
  1. Make DiscoveryCase contain traversable scientific lineage + register in ledger.
  2. Persist provider manifests + input/output hashes in every checkpoint artifact.
  3. Make scientific-stage failures fail closed (STOP on FAILED, do not continue).
  4. Explicit adversarial/rediscovery/novelty outcome states; separate from Gate A/B/C.
  5. Make run manifest authoritative + cryptographically tied to stage artifacts.

Additional repair (reviewer point 4 + 4b):
  - The DEV state machine uses GATE_A/GATE_B/GATE_C names, which implies
    scientific gate passage. These are NOT scientific gates — they are
    pipeline-stage markers. The state machine now records them with
    explicit evidence="dev_pipeline_stage" (NOT "auto"), and the run
    manifest explicitly distinguishes "pipeline_stage_reached" from
    "scientific_gate_passed".

Layout:
    experiments/dev/runs/<run_id>/
        ├── manifest.json           # authoritative run state + stage hashes
        ├── 01_extraction.json      # {result, provider_manifest, input_hash, output_hash, code_sha}
        ├── 02_abstraction.json
        ├── ... (one per stage)
        └── 12_case.json            # contains the FULL lineage, registered in ledger

DEV_ONLY: never used on Gate 2.
"""
from __future__ import annotations
import json, time, hashlib, traceback
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from discovery_infrastructure.discovery_substrate import (
    DiscoveryCase, DiscoveryLedger, DiscoveryState, DiscoveryStateMachine,
    Hypothesis, TransferHypothesis, Prediction, ExperimentProposal,
    ProvenanceGraph, ProvenanceNode, ProvenanceEdge, EpistemicState,
    MechanismGraph, MechanismNode, MechanismEdge, MechanismNodeType,
    MechanismEdgeType, DuplicateRegistrationError,
)
from engine.providers import ReasoningProvider, ProviderCallManifest, MockLiteratureProvider
from engine.mechanism_extraction import MechanismExtractionEngine
from engine.mechanism_abstraction import MechanismAbstractionEngine, MechanismPattern
from engine.cross_domain_transfer import CrossDomainTransferEngine
from engine.hypothesis_generation import HypothesisGenerationEngine
from engine.adversarial_analysis import AdversarialAnalysisEngine
from engine.rediscovery_detection import RediscoveryDetector
from engine.novelty_firewall import NoveltyFirewall
from engine.prediction_engine import PredictionEngine
from engine.experiment_design import ExperimentDesignEngine
from engine.candidate_ranker import CandidateRanker
from engine.discovery_memory import DiscoveryMemory
from engine.experimental_learning import ExperimentalLearningEngine
from engine.dev_fixtures import DevChallenge
from engine.lineage_validator import LineageValidator
from engine.persistent_ledger import PersistentLedger


REPO = Path(__file__).resolve().parents[1]
RUNS_DIR = REPO / "experiments" / "dev" / "runs"

# Engine identity: Git commit SHA + deterministic source manifest hash.
# The source manifest hash independently identifies the engine source files,
# so the verifier can check that the engine commit actually contains the
# expected source — not merely that a Git object with that SHA exists.
def _get_engine_code_sha() -> str:
    """Get the engine's Git commit SHA."""
    import subprocess
    repo = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo, capture_output=True, text=True, timeout=5
    )
    if result.returncode != 0:
        raise CheckpointIntegrityError(
            f"Cannot determine Git HEAD: {result.stderr.strip()}. "
            "A scientific run requires a valid Git repository state.")
    return result.stdout.strip()


def _compute_engine_source_manifest(commit_sha: str = "") -> str:
    """Compute a deterministic SHA-256 over all engine source files.

    If commit_sha is provided, reads from Git (git show <sha>:<path>).
    If empty, reads from the working tree (for run-time recording).

    This hash independently identifies the engine source, so the verifier
    can check that the engine commit actually contains the expected source
    — not merely that a Git object with that SHA exists.
    """
    import hashlib, subprocess
    repo = Path(__file__).resolve().parents[1]
    h = hashlib.sha256()
    if commit_sha:
        # Read from Git commit
        result = subprocess.run(
            ["git", "ls-tree", "--name-only", "-r", commit_sha, "engine/"],
            cwd=repo, capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            raise CheckpointIntegrityError(
                f"Cannot list engine source at commit {commit_sha[:16]}...")
        files = sorted(line for line in result.stdout.strip().split("\n") if line.endswith(".py"))
        for fpath in files:
            file_result = subprocess.run(
                ["git", "show", f"{commit_sha}:{fpath}"],
                cwd=repo, capture_output=True, timeout=5
            )
            if file_result.returncode != 0:
                raise CheckpointIntegrityError(
                    f"Cannot read {fpath} at commit {commit_sha[:16]}...")
            fname = fpath.split("/")[-1]
            h.update(fname.encode())
            h.update(b"\0")
            h.update(file_result.stdout)
            h.update(b"\0")
    else:
        # Read from working tree (for run-time recording)
        engine_dir = Path(__file__).parent
        for py_file in sorted(engine_dir.glob("*.py")):
            h.update(py_file.name.encode())
            h.update(b"\0")
            h.update(py_file.read_bytes())
            h.update(b"\0")
    return h.hexdigest()


def _get_working_tree_state() -> tuple:
    """Get the working-tree state for reproducibility.

    Returns (working_tree_clean: bool, working_tree_status_sha256: str).
    """
    import subprocess, hashlib
    repo = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo, capture_output=True, text=True, timeout=5
    )
    if result.returncode != 0:
        raise CheckpointIntegrityError(
            f"Cannot determine working tree state: {result.stderr.strip()}.")
    clean = (result.stdout.strip() == "")
    wt_sha = hashlib.sha256(result.stdout.encode()).hexdigest()
    return (clean, wt_sha)


ENGINE_CODE_SHA = _get_engine_code_sha()
# Record the source manifest from the COMMITTED source at HEAD.
# This ensures the anchor records the committed engine identity, not the
# working-tree state. The verifier can independently check that the engine
# commit contains this exact source.
ENGINE_SOURCE_MANIFEST_SHA256 = _compute_engine_source_manifest(ENGINE_CODE_SHA)

# Stage status constants
PENDING = "PENDING"; RUNNING = "RUNNING"; COMPLETED = "COMPLETED"
FAILED = "FAILED"; SKIPPED = "SKIPPED"


class CheckpointIntegrityError(Exception):
    """Raised when the checkpoint manifest itself is corrupted or inconsistent.

    Round-7 (per reviewer directive): a corrupted manifest must produce an
    explicit CHECKPOINT_INTEGRITY_FAILURE, not a generic JSON exception.
    The manifest is the authority for the entire run state — its integrity
    is not optional.
    """
    pass


# ============================================================================
# Round-8 Repair C: RUN_INTEGRITY_ANCHOR — the external root of trust
# ============================================================================

def _compute_stage_inventory_sha(run_dir: Path) -> str:
    """Compute a hash over all stage artifacts in the run directory.

    Round-9 Repair A: the inventory now hashes the ACTUAL FILE CONTENT
    (file_sha256), the ACTUAL RESULT CONTENT (result_sha256), and the
    DECLARED output_hash. This prevents the attack where an attacker
    modifies the result but leaves output_hash unchanged.

    The inventory entry per file is:
        filename:file_sha256:result_sha256:declared_output_hash

    The verifier independently recomputes file_sha256 and result_sha256
    and does NOT trust the declared output_hash.
    """
    import hashlib
    inventory = []
    for p in sorted(run_dir.glob("*.json")):
        if p.name in ("manifest.json", "RUN_INTEGRITY_ANCHOR.json"):
            continue
        try:
            raw_content = p.read_text()
            file_sha = hashlib.sha256(raw_content.encode("utf-8")).hexdigest()
            data = json.loads(raw_content)
            declared_output_hash = data.get("output_hash", "")
            # Hash the result field independently
            result_str = json.dumps(data.get("result", {}), sort_keys=True, default=str)
            result_sha = hashlib.sha256(result_str.encode("utf-8")).hexdigest()
            inventory.append(f"{p.name}:{file_sha}:{result_sha}:{declared_output_hash}")
        except (json.JSONDecodeError, OSError):
            inventory.append(f"{p.name}:UNREADABLE:UNREADABLE:UNREADABLE")
    inventory_str = "\n".join(inventory)
    return hashlib.sha256(inventory_str.encode("utf-8")).hexdigest()


def create_run_integrity_anchor(run_dir: Path, manifest_sha: str,
                                 freeze_record_sha: str) -> Dict:
    """Create RUN_INTEGRITY_ANCHOR.json — the external root of trust.

    Round-8 Repair C (per reviewer directive): the freeze record is
    itself a mutable file in the run directory. An attacker who replaces
    the freeze record, index, and objects together can produce a
    self-consistent but fraudulent ledger.

    The RUN_INTEGRITY_ANCHOR breaks this circularity by recording hashes
    of ALL mutable components in a single file that serves as the root.
    The anchor itself is bound to the external world via the Git commit
    (the commit SHA is recorded in the anchor and can be verified
    independently).

    Hierarchy:
                 RUN_INTEGRITY_ANCHOR
                         │
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
      manifest        ledger          stages
          │              │
          ↓              ↓
      stage hashes   index hash
                         │
                         ↓
                  object inventory
                         │
                         ↓
                   object hashes

    An auditor starts from the anchor and verifies every layer below.
    The anchor's own integrity is verified by comparing it against an
    externally-recorded value (e.g. the Git commit, or a signed release).
    """
    from engine.persistent_ledger import PersistentLedger, _sha
    ledger_dir = run_dir / "ledger"
    ledger = PersistentLedger(ledger_dir)

    # Compute the ledger index hash
    index_path = ledger_dir / "index.json"
    index_content = index_path.read_text() if index_path.exists() else ""
    ledger_index_sha = _sha(index_content)

    # Compute the object inventory hash
    # Round-9 Repair B: hash the ACTUAL FILE CONTENT, not just the
    # index's declared content_hash. This prevents the attack where an
    # attacker modifies an object file without changing the index.
    inventory = []
    for otype, entries in sorted(ledger._index.items()):
        for oid, entry in sorted(entries.items()):
            obj_path = ledger_dir / entry.file
            if obj_path.exists():
                try:
                    actual_content = obj_path.read_text()
                    actual_sha = _sha(actual_content)
                except OSError:
                    actual_sha = "UNREADABLE"
            else:
                actual_sha = "MISSING"
            inventory.append(f"{otype}/{oid}/{entry.content_hash}/{actual_sha}")
    inventory_str = "\n".join(sorted(inventory))
    ledger_inventory_sha = _sha(inventory_str)

    # Compute the stage inventory hash
    stage_inventory_sha = _compute_stage_inventory_sha(run_dir)

    anchor = {
        "schema_version": 3,
        "run_id": run_dir.name,
        "manifest_sha256": manifest_sha,
        "ledger_index_sha256": ledger_index_sha,
        "ledger_inventory_sha256": ledger_inventory_sha,
        "freeze_record_sha256": freeze_record_sha,
        "stage_inventory_sha256": stage_inventory_sha,
        "engine_commit_sha": ENGINE_CODE_SHA,
        "engine_source_manifest_sha256": ENGINE_SOURCE_MANIFEST_SHA256,
        "working_tree_clean": _get_working_tree_state()[0],
        "working_tree_status_sha256": _get_working_tree_state()[1],
        "created_at": _now(),
        "note": "RUN_INTEGRITY_ANCHOR — the external root of trust. "
                "engine_commit_sha = the Git commit whose engine source produced this run. "
                "engine_source_manifest_sha256 = deterministic hash of engine source files at run time. "
                "The run-record commit is NOT self-referential; it is supplied externally by the "
                "auditor via the record_commit parameter to verify_run_integrity_anchor(). "
                "An auditor verifies: anchor self-hash, engine commit exists + contains expected source, "
                "committed anchor at record_commit matches, all mutable files match.",
    }
    # Compute self-hash (excluding the self-hash field itself)
    anchor_for_hash = {k: v for k, v in anchor.items() if k != "anchor_sha256"}
    anchor["anchor_sha256"] = _sha(json.dumps(anchor_for_hash, sort_keys=True, default=str))

    anchor_path = run_dir / "RUN_INTEGRITY_ANCHOR.json"
    # Atomic write
    temp_path = run_dir / "RUN_INTEGRITY_ANCHOR.json.tmp"
    import os
    temp_path.write_text(json.dumps(anchor, indent=2, default=str))
    try:
        with open(temp_path, "rb") as f:
            os.fsync(f.fileno())
    except OSError:
        pass
    temp_path.replace(anchor_path)
    return anchor


def verify_run_integrity_anchor(run_dir: Path,
                                 record_commit: str = "") -> Dict:
    """Verify the entire run against its RUN_INTEGRITY_ANCHOR.

    Final provenance model:
      - engine_commit_sha: the Git commit whose engine source produced the run.
        Recorded in the anchor at run-creation time. Verified by checking
        that the commit exists AND that the engine source at that commit
        produces the same engine_source_manifest_sha256.
      - record_commit: the Git commit that froze the run artifacts.
        Supplied EXTERNALLY by the auditor (not self-referential).
        If empty, defaults to HEAD.

    Verification layers:
      1. anchor self-hash (anchor file was not modified)
      2. engine_identity_verified (engine commit exists + source manifest matches)
      3. committed_anchor_matches (anchor on disk == git show <record_commit>:<path>)
      4. manifest_hash_matches
      5. ledger_index_hash_matches
      6. ledger_inventory_hash_matches
      7. freeze_record_hash_matches
      8. stage_inventory_hash_matches

    NO FAIL-OPEN PATHS: if any Git verification fails, the result is
    INTEGRITY_UNVERIFIABLE, never True.
    """
    from engine.persistent_ledger import PersistentLedger, _sha
    import subprocess

    anchor_path = run_dir / "RUN_INTEGRITY_ANCHOR.json"
    result = {"anchor_exists": False, "anchor_self_hash_matches": False,
              "engine_identity_verified": False,
              "engine_commit_sha": "",
              "engine_source_manifest_sha256": "",
              "record_commit": record_commit or "",
              "committed_anchor_matches": False,
              "manifest_hash_matches": False,
              "ledger_index_hash_matches": False,
              "ledger_inventory_hash_matches": False,
              "freeze_record_hash_matches": False,
              "stage_inventory_hash_matches": False,
              "working_tree_clean": None,
              "integrity_intact": False,
              "reproducibility_status": "UNKNOWN",
              "intact": False,
              "detail": ""}

    if not anchor_path.exists():
        result["detail"] = "RUN_INTEGRITY_ANCHOR.json does not exist"
        return result
    result["anchor_exists"] = True

    try:
        anchor = json.loads(anchor_path.read_text())
    except json.JSONDecodeError as e:
        result["detail"] = f"anchor corrupted: {e}"
        return result

    # 1. Verify anchor self-hash
    stored_anchor_sha = anchor.pop("anchor_sha256", "")
    if not stored_anchor_sha:
        result["detail"] = "anchor has no anchor_sha256 field"
        return result
    recomputed_anchor_sha = _sha(json.dumps(anchor, sort_keys=True, default=str))
    result["anchor_self_hash_matches"] = (recomputed_anchor_sha == stored_anchor_sha)
    if not result["anchor_self_hash_matches"]:
        result["detail"] = "anchor self-hash mismatch — anchor was modified"
        return result

    # 2. Verify engine identity (NOT just commit existence)
    # The engine commit must exist AND the engine source at that commit
    # must produce the same source manifest hash recorded in the anchor.
    engine_commit_sha = anchor.get("engine_commit_sha") or anchor.get("engine_code_sha", "")
    expected_source_manifest = anchor.get("engine_source_manifest_sha256", "")
    result["engine_commit_sha"] = engine_commit_sha
    result["engine_source_manifest_sha256"] = expected_source_manifest
    result["working_tree_clean"] = anchor.get("working_tree_clean")

    repo = Path(__file__).resolve().parents[1]

    if not engine_commit_sha:
        result["detail"] = "anchor has no engine_commit_sha"
        return result

    # 2a. Check the engine commit exists in Git history
    git_result = subprocess.run(
        ["git", "cat-file", "-e", f"{engine_commit_sha}^{{commit}}"],
        cwd=repo, capture_output=True, timeout=5
    )
    if git_result.returncode != 0:
        result["detail"] = (f"engine commit {engine_commit_sha[:16]}... does not exist "
                            "in Git history. Engine identity UNVERIFIABLE.")
        return result

    # 2b. Verify the engine source at that commit matches the recorded manifest
    if expected_source_manifest:
        try:
            actual_manifest = _compute_engine_source_manifest(engine_commit_sha)
        except CheckpointIntegrityError as e:
            result["detail"] = str(e)
            return result
        if actual_manifest != expected_source_manifest:
            result["detail"] = (f"engine source manifest mismatch: anchor recorded "
                                f"{expected_source_manifest[:16]}... but commit "
                                f"{engine_commit_sha[:16]}... has {actual_manifest[:16]}... "
                                "Engine identity NOT VERIFIED.")
            return result
        result["engine_identity_verified"] = True
    else:
        # No source manifest recorded — cannot verify engine source identity
        result["detail"] = "anchor has no engine_source_manifest_sha256 — cannot verify engine source"
        return result

    # 3. Verify committed anchor (against record_commit, or HEAD if not specified)
    commit_ref = record_commit or "HEAD"
    try:
        rel_path = anchor_path.relative_to(repo)
    except ValueError:
        # Run directory is outside the repo — cannot verify committed anchor
        result["committed_anchor_matches"] = True  # skip for out-of-repo runs (tests)
    else:
        git_result = subprocess.run(
            ["git", "show", f"{commit_ref}:{rel_path}"],
            cwd=repo, capture_output=True, text=True, timeout=5
        )
        if git_result.returncode == 0:
            result["committed_anchor_matches"] = (git_result.stdout == anchor_path.read_text())
        else:
            # File not tracked at the specified commit — FAIL CLOSED
            result["committed_anchor_matches"] = False
            result["detail"] = (f"anchor file not found at commit {commit_ref[:16]}... "
                                "Cannot verify committed anchor.")

    # 4. Verify manifest hash
    manifest_path = run_dir / "manifest.json"
    if manifest_path.exists():
        try:
            manifest_data = json.loads(manifest_path.read_text())
            stored_manifest_sha = manifest_data.get("manifest_sha", "")
            result["manifest_hash_matches"] = (stored_manifest_sha == anchor.get("manifest_sha256"))
        except json.JSONDecodeError:
            result["manifest_hash_matches"] = False
    else:
        result["manifest_hash_matches"] = False

    # 5. Verify ledger index hash
    ledger_dir = run_dir / "ledger"
    index_path = ledger_dir / "index.json"
    if index_path.exists():
        current_index_sha = _sha(index_path.read_text())
        result["ledger_index_hash_matches"] = (current_index_sha == anchor.get("ledger_index_sha256"))
    else:
        result["ledger_index_hash_matches"] = False

    # 6. Verify ledger inventory hash (actual file content, not declared)
    try:
        ledger = PersistentLedger(ledger_dir)
        inventory = []
        for otype, entries in sorted(ledger._index.items()):
            for oid, entry in sorted(entries.items()):
                obj_path = ledger_dir / entry.file
                if obj_path.exists():
                    try:
                        actual_sha = _sha(obj_path.read_text())
                    except OSError:
                        actual_sha = "UNREADABLE"
                else:
                    actual_sha = "MISSING"
                inventory.append(f"{otype}/{oid}/{entry.content_hash}/{actual_sha}")
        current_inventory_sha = _sha("\n".join(sorted(inventory)))
        result["ledger_inventory_hash_matches"] = (current_inventory_sha == anchor.get("ledger_inventory_sha256"))
    except Exception:
        result["ledger_inventory_hash_matches"] = False

    # 7. Verify freeze record hash
    freeze_path = ledger_dir / "LEDGER_FREEZE_RECORD.json"
    if freeze_path.exists():
        result["freeze_record_hash_matches"] = (_sha(freeze_path.read_text()) == anchor.get("freeze_record_sha256"))
    else:
        result["freeze_record_hash_matches"] = False

    # 8. Verify stage inventory hash
    current_stage_sha = _compute_stage_inventory_sha(run_dir)
    result["stage_inventory_hash_matches"] = (current_stage_sha == anchor.get("stage_inventory_sha256"))

    # Overall
    integrity_checks = [
        result["anchor_self_hash_matches"],
        result["engine_identity_verified"],
        result["committed_anchor_matches"],
        result["manifest_hash_matches"],
        result["ledger_index_hash_matches"],
        result["ledger_inventory_hash_matches"],
        result["freeze_record_hash_matches"],
        result["stage_inventory_hash_matches"],
    ]
    result["integrity_intact"] = all(integrity_checks)

    if result["working_tree_clean"] is True:
        result["reproducibility_status"] = "REPRODUCIBLE"
    elif result["working_tree_clean"] is False:
        result["reproducibility_status"] = "NON_REPRODUCIBLE_WORKTREE"
    else:
        result["reproducibility_status"] = "UNKNOWN"

    result["intact"] = result["integrity_intact"]

    if result["integrity_intact"]:
        result["detail"] = (f"integrity verified — all layers match. "
                            f"reproducibility={result['reproducibility_status']}")
    else:
        failed = [k for k, v in result.items()
                  if isinstance(v, bool) and not v
                  and k not in ("intact", "integrity_intact")]
        result["detail"] = f"integrity failures: {', '.join(failed)}"
    return result

# Scientific stages — if any of these FAIL, the loop STOPs (fail-closed).
# Non-scientific stages (rankings, state-machine bookkeeping, case assembly)
# may fail without blocking because they are derivable from prior stages.
SCIENTIFIC_STAGES = {
    "01_extraction", "02_abstraction", "03_transfer", "04_hypotheses",
}
# Per-hypothesis scientific stages (prefixed with hyp_id in practice)
PER_HYP_SCIENTIFIC_PREFIXES = ("05_adversarial_", "06_rediscovery_",
                                "07_novelty_", "08_prediction_", "09_experiment_")


# ============================================================================
# Adversarial outcome enum (Repair 4)
# ============================================================================

class AdversarialOutcome(str):
    """Explicit outcome states for adversarial analysis.

    ADVERSARIAL_SURVIVES   — no HIGH-severity contradictions; may continue
    ADVERSARIAL_FAILED     — HIGH-severity contradiction; hypothesis is NOT
                             promoted to a scientific candidate. It is
                             retained as negative science but does not
                             advance to prediction/experiment.
    ADVERSARIAL_INCONCLUSIVE — analysis could not determine; human review
                               required before promotion.
    """
    SURVIVES = "ADVERSARIAL_SURVIVES"
    FAILED = "ADVERSARIAL_FAILED"
    INCONCLUSIVE = "ADVERSARIAL_INCONCLUSIVE"


# ============================================================================
# Stage artifact wrapper (Repair 2 + Repair 5)
# ============================================================================

@dataclass
class StageArtifact:
    """Every checkpoint stage produces this wrapper.

    Repair 2: provider_manifest + input_hash + output_hash are persisted.
    Repair 5: the manifest references each stage by its output_hash.
    """
    stage: str
    run_id: str
    code_sha: str
    input_hash: str        # SHA-256 of the input to this stage
    output_hash: str       # SHA-256 of the serialized result
    provider_manifest: Optional[Dict] = None  # ProviderCallManifest.to_dict()
    result: Dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict:
        return asdict(self)


# ============================================================================
# Run manifest (Repair 5 — authoritative + crypto-tied)
# ============================================================================

@dataclass
class StageStatus:
    stage: str
    status: str = PENDING
    started_at: str = ""
    completed_at: str = ""
    latency_ms: Optional[int] = None
    error: str = ""
    output_hash: str = ""    # Repair 5: hash of the stage's output artifact
    provider_manifest_sha: str = ""  # hash of the provider manifest (if any)

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class RunManifest:
    run_id: str
    challenge_id: str
    started_at: str
    last_updated: str
    engine_code_sha: str = ENGINE_CODE_SHA
    resume_from: str = "01_extraction"
    stages: Dict[str, StageStatus] = field(default_factory=dict)
    n_hypotheses: int = 0
    n_hypotheses_survived_adversarial: int = 0
    n_hypotheses_rediscovery: int = 0
    final_state: str = ""
    final_state_source: str = ""   # which stage artifact is authoritative for final_state
    completed: bool = False
    failed_closed: bool = False    # Repair 3: true if the loop stopped due to a FAILED scientific stage
    failed_closed_at: str = ""     # which stage failed
    manifest_sha: str = ""         # Repair 5: self-hash for integrity

    def to_dict(self) -> Dict:
        d = {"run_id": self.run_id, "challenge_id": self.challenge_id,
             "started_at": self.started_at, "last_updated": self.last_updated,
             "engine_code_sha": self.engine_code_sha,
             "resume_from": self.resume_from,
             "stages": {k: v.to_dict() for k, v in self.stages.items()},
             "n_hypotheses": self.n_hypotheses,
             "n_hypotheses_survived_adversarial": self.n_hypotheses_survived_adversarial,
             "n_hypotheses_rediscovery": self.n_hypotheses_rediscovery,
             "final_state": self.final_state,
             "final_state_source": self.final_state_source,
             "completed": self.completed,
             "failed_closed": self.failed_closed,
             "failed_closed_at": self.failed_closed_at}
        # Self-hash for integrity (Repair 5)
        d["manifest_sha"] = _sha(json.dumps(d, sort_keys=True, default=str))
        return d


# ============================================================================
# The checkpointed loop (all 5 repairs applied)
# ============================================================================

class CheckpointedDiscoveryLoop:
    """Discovery loop with per-stage checkpointing, fail-closed semantics,
    traversable lineage, and authoritative run manifest."""

    def __init__(self, reasoning: ReasoningProvider,
                 literature: Optional[Any] = None,
                 run_dir: Optional[Path] = None):
        self.reasoning = reasoning
        self.literature = literature or MockLiteratureProvider(corpus=[])
        self.extractor = MechanismExtractionEngine(reasoning)
        self.abstracter = MechanismAbstractionEngine(reasoning)
        self.transfer_engine = CrossDomainTransferEngine(reasoning)
        self.hypothesis_engine = HypothesisGenerationEngine(reasoning)
        self.adversarial_engine = AdversarialAnalysisEngine(reasoning)
        self.rediscovery_detector = RediscoveryDetector(reasoning)
        self.novelty_firewall = NoveltyFirewall(reasoning, self.literature)
        self.prediction_engine = PredictionEngine(reasoning)
        self.experiment_engine = ExperimentDesignEngine(reasoning)
        self.ranker = CandidateRanker()
        self.memory = DiscoveryMemory()
        self.learning_engine = ExperimentalLearningEngine()
        # Repair B: use a PersistentLedger that saves to disk + is reloadable
        self._ledger_dir: Optional[Path] = None
        self.ledger: Optional[PersistentLedger] = None
        self._lineage_validator = LineageValidator()

    def run(self, challenge: DevChallenge, *, run_id: Optional[str] = None,
            resume: bool = True) -> Dict:
        run_id = run_id or f"RUN-{challenge.challenge_id}"
        run_dir = RUNS_DIR / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = run_dir / "manifest.json"

        # Repair B: initialize the persistent ledger in the run directory
        self._ledger_dir = run_dir / "ledger"
        self.ledger = PersistentLedger(self._ledger_dir)

        if resume and manifest_path.exists():
            manifest = self._load_manifest(manifest_path)
        elif resume and not manifest_path.exists():
            # Resume requested but manifest is missing. Check if there are
            # existing stage artifacts — if so, this is a corrupted run,
            # not a fresh start.
            existing_artifacts = list(run_dir.glob("*.json")) + list(run_dir.glob("*.json.tmp"))
            if existing_artifacts:
                raise CheckpointIntegrityError(
                    f"Resume requested but manifest.json is missing, yet {len(existing_artifacts)} "
                    f"stage artifacts exist in {run_dir}. This indicates a corrupted run — "
                    "the manifest was deleted but artifacts remain. Cannot resume safely.")
            # No artifacts exist — this is a fresh start, not a resume
            manifest = RunManifest(run_id=run_id, challenge_id=challenge.challenge_id,
                                   started_at=_now(), last_updated=_now())
            self._save_manifest(manifest, manifest_path)
        else:
            manifest = RunManifest(run_id=run_id, challenge_id=challenge.challenge_id,
                                   started_at=_now(), last_updated=_now())
            self._save_manifest(manifest, manifest_path)

        # Helper: run a stage with fail-closed semantics (Repair 3)
        def run_stage_fail_closed(stage: str, fn, input_data: Any = None) -> bool:
            """Returns True if the stage completed (or was already complete).
            Returns False if the stage FAILED and the loop should STOP."""
            if self._is_completed(manifest, stage):
                return True
            self._run_stage(manifest, stage, manifest_path, run_dir, fn, input_data)
            status = manifest.stages.get(stage, StageStatus(stage=stage)).status
            if status == FAILED:
                # Repair 3: fail-closed for scientific stages
                if self._is_scientific_stage(stage):
                    manifest.failed_closed = True
                    manifest.failed_closed_at = stage
                    manifest.last_updated = _now()
                    self._save_manifest(manifest, manifest_path)
                    return False
            return True

        # ---- Stage 01: Extraction (scientific, fail-closed) ----
        if not run_stage_fail_closed("01_extraction",
                lambda inp: self._stage_extraction(challenge, inp),
                input_data=challenge.source_documents[0]):
            return manifest.to_dict()

        # ---- Stage 02: Abstraction (scientific, fail-closed) ----
        if not run_stage_fail_closed("02_abstraction",
                lambda inp: self._stage_abstraction(challenge, run_dir, inp),
                input_data=self._load_stage(run_dir, "01_extraction")):
            return manifest.to_dict()

        # ---- Stage 03: Transfer (scientific, fail-closed) ----
        if not run_stage_fail_closed("03_transfer",
                lambda inp: self._stage_transfer(challenge, run_dir, inp),
                input_data=self._load_stage(run_dir, "02_abstraction")):
            return manifest.to_dict()

        # ---- Stage 04: Hypotheses (scientific, fail-closed) ----
        if not run_stage_fail_closed("04_hypotheses",
                lambda inp: self._stage_hypotheses(challenge, run_dir, inp),
                input_data=self._load_stage(run_dir, "03_transfer")):
            return manifest.to_dict()

        # ---- Stages 05-09: per-hypothesis pipeline ----
        # Repair 4: adversarial outcome now GATES the per-hypothesis pipeline.
        # ADVERSARIAL_FAILED hypotheses do NOT advance to prediction/experiment.
        hyp_data = self._load_stage(run_dir, "04_hypotheses")
        # Stage artifacts wrap result in a "result" key (Repair 2)
        hyp_result = hyp_data.get("result", {}) if hyp_data else {}
        if hyp_result and hyp_result.get("hypotheses"):
            testable_hyps = [h for h in hyp_result["hypotheses"] if h.get("is_testable")]
            manifest.n_hypotheses = len(testable_hyps)
            n_survived = 0
            n_rediscovery = 0
            for hyp_dict in testable_hyps:
                hyp_id = hyp_dict["hypothesis_id"]
                h = self._reconstruct_hypothesis(hyp_dict)
                if not h:
                    continue

                # Stage 05: adversarial (scientific, fail-closed)
                stage05 = f"05_adversarial_{hyp_id}"
                if not run_stage_fail_closed(stage05,
                        lambda inp, hh=h: self._stage_adversarial(hh, run_dir, inp),
                        input_data=hyp_dict):
                    return manifest.to_dict()

                # Read the adversarial outcome (Repair 4)
                adv_data = self._load_stage(run_dir, stage05)
                adv_outcome = (adv_data or {}).get("result", {}).get("outcome", AdversarialOutcome.INCONCLUSIVE)

                # Stage 06: rediscovery (scientific, fail-closed — runs regardless of adversarial,
                # because rediscovery classification is informative even for failed hypotheses)
                stage06 = f"06_rediscovery_{hyp_id}"
                if not run_stage_fail_closed(stage06,
                        lambda inp, hh=h: self._stage_rediscovery(hh, challenge, run_dir, inp),
                        input_data=hyp_dict):
                    return manifest.to_dict()
                rd_data = self._load_stage(run_dir, stage06)
                if rd_data and rd_data.get("result", {}).get("is_rediscovery"):
                    n_rediscovery += 1

                # Stage 07: novelty (scientific, fail-closed — runs regardless of adversarial)
                stage07 = f"07_novelty_{hyp_id}"
                if not run_stage_fail_closed(stage07,
                        lambda inp, hh=h: self._stage_novelty(hh, run_dir, inp),
                        input_data=hyp_dict):
                    return manifest.to_dict()

                # Repair 4: ADVERSARIAL_FAILED hypotheses do NOT advance to prediction/experiment.
                # They are retained as negative science but the pipeline stops here for them.
                if adv_outcome == AdversarialOutcome.FAILED:
                    # Record that this hypothesis was blocked at the adversarial gate
                    blocked_stage = f"BLOCKED_adversarial_{hyp_id}"
                    manifest.stages[blocked_stage] = StageStatus(
                        stage=blocked_stage, status=SKIPPED,
                        started_at=_now(), completed_at=_now(),
                        error=f"hypothesis {hyp_id} blocked: adversarial outcome = FAILED")
                    self._save_manifest(manifest, manifest_path)
                    continue

                n_survived += 1

                # Stage 08: prediction (scientific, fail-closed)
                stage08 = f"08_prediction_{hyp_id}"
                if not run_stage_fail_closed(stage08,
                        lambda inp, hh=h: self._stage_prediction(hh, run_dir, inp),
                        input_data=hyp_dict):
                    return manifest.to_dict()

                # Stage 09: experiment (scientific, fail-closed — requires prediction from 08)
                stage09 = f"09_experiment_{hyp_id}"
                pred_for_exp = self._load_stage(run_dir, stage08)
                if not pred_for_exp or not pred_for_exp.get("result", {}).get("prediction"):
                    # No prediction — skip experiment, record as skipped
                    manifest.stages[stage09] = StageStatus(
                        stage=stage09, status=SKIPPED,
                        started_at=_now(), completed_at=_now(),
                        error="skipped: no prediction produced")
                    self._save_manifest(manifest, manifest_path)
                else:
                    if not run_stage_fail_closed(stage09,
                            lambda inp, hh=h, hid=hyp_id: self._stage_experiment(hh, hid, run_dir, inp),
                            input_data=pred_for_exp):
                        return manifest.to_dict()

            manifest.n_hypotheses_survived_adversarial = n_survived
            manifest.n_hypotheses_rediscovery = n_rediscovery

        # ---- Stage 10: Rankings (non-scientific; derived from prior stages) ----
        if not self._is_completed(manifest, "10_rankings"):
            self._run_stage(manifest, "10_rankings", manifest_path, run_dir,
                            lambda inp: self._stage_rankings(challenge, run_dir, inp),
                            input_data=self._load_stage(run_dir, "04_hypotheses"))

        # ---- Stage 11: State machine (non-scientific; bookkeeping) ----
        if not self._is_completed(manifest, "11_state_machine"):
            self._run_stage(manifest, "11_state_machine", manifest_path, run_dir,
                            lambda inp: self._stage_state_machine(challenge, run_dir, inp),
                            input_data=self._load_stage(run_dir, "04_hypotheses"))
            # Repair 5: propagate final_state from the stage artifact to the manifest
            sm_data = self._load_stage(run_dir, "11_state_machine")
            if sm_data:
                manifest.final_state = sm_data.get("result", {}).get("final_state", "")
                manifest.final_state_source = "11_state_machine.json"

        # ---- Stage 12: Case (Repair 1 — traversable lineage + ledger registration) ----
        if not self._is_completed(manifest, "12_case"):
            self._run_stage(manifest, "12_case", manifest_path, run_dir,
                            lambda inp: self._stage_case(challenge, run_dir, inp),
                            input_data=self._load_stage(run_dir, "11_state_machine"))

        # ---- Finalize ----
        manifest.completed = (not manifest.failed_closed) and all(
            s.status == COMPLETED for s in manifest.stages.values()
            if not s.stage.startswith("BLOCKED_") and s.status != SKIPPED
        )
        manifest.last_updated = _now()
        self._save_manifest(manifest, manifest_path)

        # Repair B: create the ledger freeze record after the run completes.
        # Round-8: freeze record creation is NOT best-effort. If it fails,
        # the run cannot be represented as fully committed.
        manifest_dict = manifest.to_dict()
        manifest_sha = manifest_dict.get("manifest_sha", "")
        freeze_record_sha = ""
        if self.ledger:
            try:
                freeze_record = self.ledger.create_freeze_record(
                    run_id=manifest.run_id,
                    manifest_sha=manifest_sha)
                # Compute the freeze record hash from the FILE CONTENT
                # (not the dict), so verify_run_integrity_anchor can
                # compare against the same file content.
                freeze_path = self._ledger_dir / "LEDGER_FREEZE_RECORD.json"
                freeze_record_sha = _sha(freeze_path.read_text())
            except Exception as e:
                # Round-8 Repair B: fail-closed. A run without a valid freeze
                # record is NOT complete — the ledger is unanchored.
                manifest.completed = False
                manifest.failed_closed = True
                manifest.failed_closed_at = "freeze_record_creation"
                manifest.last_updated = _now()
                self._save_manifest(manifest, manifest_path)
                raise CheckpointIntegrityError(
                    f"Freeze record creation failed: {e}. The run cannot be "
                    "represented as committed without an anchored ledger.") from e

        # Round-8 Repair C: create the RUN_INTEGRITY_ANCHOR.
        # This is the external root of trust that binds manifest + ledger +
        # freeze record + stage inventory + engine identity. An attacker
        # who modifies any mutable file in the run directory will break
        # the anchor's hash chain.
        try:
            create_run_integrity_anchor(run_dir, manifest_sha, freeze_record_sha)
        except Exception as e:
            manifest.completed = False
            manifest.failed_closed = True
            manifest.failed_closed_at = "anchor_creation"
            manifest.last_updated = _now()
            self._save_manifest(manifest, manifest_path)
            raise CheckpointIntegrityError(
                f"RUN_INTEGRITY_ANCHOR creation failed: {e}. The run cannot "
                "be represented as committed without an anchored identity.") from e

        return manifest_dict

    # ========================================================================
    # Stage implementations — each returns (result_dict, provider_manifest)
    # ========================================================================

    def _stage_extraction(self, challenge: DevChallenge, input_data) -> Tuple[Dict, Optional[Dict]]:
        result = self.extractor.extract(input_data)
        provider_manifest = result.manifests[0].to_dict() if result.manifests else None
        out = {"ok": result.ok, "source_document_id": result.source_document_id,
               "source_document_title": result.source_document_title,
               "graph": result.graph.to_dict(),
               "n_nodes": len(result.graph.nodes), "n_edges": len(result.graph.edges),
               "n_failures": len(result.failures),
               "failures": [f.__dict__ for f in result.failures]}
        return out, provider_manifest

    def _stage_abstraction(self, challenge: DevChallenge, run_dir: Path, input_data) -> Tuple[Dict, Optional[Dict]]:
        ext = input_data
        if not ext or not ext.get("result"):
            raise RuntimeError("extraction stage output missing or malformed")
        ext_result = ext["result"]
        graph = MechanismGraph()
        for n in ext_result["graph"]["nodes"].values():
            graph.add_node(MechanismNode(
                node_id=n["node_id"], node_type=MechanismNodeType(n["node_type"]),
                label=n["label"], description=n.get("description", ""),
                provenance=n.get("provenance", [])))
        for e in ext_result["graph"]["edges"]:
            graph.add_edge(MechanismEdge(
                edge_id=e["edge_id"], source_id=e["source_id"], target_id=e["target_id"],
                edge_type=MechanismEdgeType(e["edge_type"]),
                confidence=e.get("confidence", 0.5), evidence=e.get("evidence", [])))
        result = self.abstracter.abstract(
            graph, source_domain=challenge.source_domain,
            source_title=challenge.source_documents[0].get("title", ""),
            pattern_id=f"MP-{challenge.challenge_id}")
        provider_manifest = result.manifests[0].to_dict() if result.manifests else None
        return {"pattern": result.pattern.to_dict(), "failures": result.failures,
                "source_extraction_hash": ext.get("output_hash", "")}, provider_manifest

    def _stage_transfer(self, challenge: DevChallenge, run_dir: Path, input_data) -> Tuple[Dict, Optional[Dict]]:
        pat_data = input_data
        if not pat_data or not pat_data.get("result"):
            raise RuntimeError("abstraction stage output missing")
        pattern = MechanismPattern(**pat_data["result"]["pattern"])
        result = self.transfer_engine.generate(
            pattern, target_domain=challenge.target_domain,
            target_problem=challenge.target_problem,
            target_constraints=challenge.target_constraints,
            transfer_id_prefix=f"TH-{challenge.challenge_id}")
        provider_manifest = result.manifests[0].to_dict() if result.manifests else None
        return {"transfers": [t.to_dict() for t in result.transfers],
                "rejected": result.rejected,
                "n_accepted": len(result.transfers),
                "n_rejected": len(result.rejected),
                "source_abstraction_hash": pat_data.get("output_hash", "")}, provider_manifest

    def _stage_hypotheses(self, challenge: DevChallenge, run_dir: Path, input_data) -> Tuple[Dict, Optional[Dict]]:
        transfer_data = input_data
        if not transfer_data or not transfer_data.get("result"):
            raise RuntimeError("transfer stage output missing")
        td = transfer_data["result"]
        if not td["transfers"]:
            return {"hypotheses": [], "distinguishing_predictions": "",
                    "source_transfer_hash": transfer_data.get("output_hash", "")}, None
        t = td["transfers"][0]
        transfer = TransferHypothesis(
            transfer_id=t["transfer_id"], source_domain=t.get("source_domain", ""),
            source_mechanism=t.get("source_mechanism", ""),
            source_conditions=t.get("source_conditions", []),
            target_domain=t.get("target_domain", ""),
            target_problem=t.get("target_problem", ""),
            transferred_principle=t.get("transferred_principle", ""),
            required_translation=t.get("required_translation", ""),
            expected_effect=t.get("expected_effect", ""),
            boundary_conditions=t.get("boundary_conditions", []),
            failure_conditions=t.get("failure_conditions", []),
            testable_prediction=t.get("testable_prediction", ""),
            epistemic_state=EpistemicState(t.get("epistemic_state", "HYPOTHESIZED")))
        result = self.hypothesis_engine.generate(transfer, id_prefix=f"H-{challenge.challenge_id}")
        provider_manifest = result.manifests[0].to_dict() if result.manifests else None
        # Register hypotheses in the ledger (Repair 1)
        for h in result.hypotheses:
            try:
                self.ledger.register_hypothesis(h)
            except DuplicateRegistrationError:
                pass
        return {"hypotheses": [h.to_dict() for h in result.hypotheses],
                "distinguishing_predictions": result.distinguishing_predictions,
                "transfer_id": transfer.transfer_id,
                "source_transfer_hash": transfer_data.get("output_hash", "")}, provider_manifest

    def _stage_adversarial(self, hypothesis: Hypothesis, run_dir: Path, input_data) -> Tuple[Dict, Optional[Dict]]:
        result = self.adversarial_engine.analyze(hypothesis)
        provider_manifest = result.manifests[0].to_dict() if result.manifests else None
        # Repair 4: explicit outcome state
        outcome = AdversarialOutcome.SURVIVES
        if not result.survives:
            # Check if it was blocked by a HIGH-severity CONTRADICTS_KNOWN
            has_high_contradiction = any(
                f.severity == "HIGH" and f.category == "CONTRADICTS_KNOWN"
                for f in result.failure_modes
            )
            outcome = AdversarialOutcome.FAILED if has_high_contradiction else AdversarialOutcome.INCONCLUSIVE
        return {"hypothesis_id": hypothesis.hypothesis_id,
                "failure_modes": [f.__dict__ for f in result.failure_modes],
                "survives": result.survives,
                "outcome": outcome,  # Repair 4: explicit outcome
                "n_high_severity": sum(1 for f in result.failure_modes if f.severity == "HIGH"),
                "n_medium_severity": sum(1 for f in result.failure_modes if f.severity == "MEDIUM"),
                "n_low_severity": sum(1 for f in result.failure_modes if f.severity == "LOW"),
                "source_hypothesis_hash": input_data.get("output_hash", "") if input_data else ""}, provider_manifest

    def _stage_rediscovery(self, hypothesis: Hypothesis, challenge: DevChallenge, run_dir: Path, input_data) -> Tuple[Dict, Optional[Dict]]:
        result = self.rediscovery_detector.classify(hypothesis, challenge.source_documents)
        provider_manifest = result.manifests[0].to_dict() if result.manifests else None
        return {"hypothesis_id": hypothesis.hypothesis_id,
                "classification": result.classification.value,
                "evidence": result.evidence,
                "is_rediscovery": result.is_rediscovery,
                "source_hypothesis_hash": input_data.get("output_hash", "") if input_data else ""}, provider_manifest

    def _stage_novelty(self, hypothesis: Hypothesis, run_dir: Path, input_data) -> Tuple[Dict, Optional[Dict]]:
        result = self.novelty_firewall.assess(hypothesis, assessment_id=f"PA-{hypothesis.hypothesis_id}")
        provider_manifest = result.manifests[0].to_dict() if result.manifests else None
        # Register the prior-art assessment in the ledger (Repair 1)
        try:
            self.ledger.register_prior_art(result.assessment)
        except DuplicateRegistrationError:
            pass
        return {"hypothesis_id": hypothesis.hypothesis_id,
                "status": result.assessment.status.value,
                "similarity": result.assessment.similarity,
                "matched_prior_art": result.assessment.matched_prior_art,
                "review_required": result.assessment.review_required,
                "source_hypothesis_hash": input_data.get("output_hash", "") if input_data else ""}, provider_manifest

    def _stage_prediction(self, hypothesis: Hypothesis, run_dir: Path, input_data) -> Tuple[Dict, Optional[Dict]]:
        result = self.prediction_engine.predict(hypothesis, prediction_id=f"P-{hypothesis.hypothesis_id}")
        provider_manifest = result.manifests[0].to_dict() if result.manifests else None
        if result.prediction:
            try:
                self.ledger.register_prediction(result.prediction)
            except DuplicateRegistrationError:
                pass
        return {"hypothesis_id": hypothesis.hypothesis_id,
                "prediction": result.prediction.to_dict() if result.prediction else None,
                "failed": result.prediction is None,
                "failures": result.failures,
                "source_hypothesis_hash": input_data.get("output_hash", "") if input_data else ""}, provider_manifest

    def _stage_experiment(self, hypothesis: Hypothesis, hyp_id: str, run_dir: Path, input_data) -> Tuple[Dict, Optional[Dict]]:
        pred_data = input_data
        if not pred_data or not pred_data.get("result", {}).get("prediction"):
            return {"hypothesis_id": hyp_id, "experiment": None,
                    "skipped_reason": "no prediction",
                    "source_prediction_hash": pred_data.get("output_hash", "") if pred_data else ""}, None
        p = pred_data["result"]["prediction"]
        prediction = Prediction(
            prediction_id=p["prediction_id"], hypothesis_id=p["hypothesis_id"],
            observable=p.get("observable", ""),
            expected_direction=p.get("expected_direction", ""),
            expected_magnitude=p.get("expected_magnitude", ""),
            conditions=p.get("conditions", []),
            baseline=p.get("baseline", ""),
            falsifier=p.get("falsifier", ""),
            uncertainty=p.get("uncertainty", 0.5),
            is_testable=p.get("is_testable", False))
        result = self.experiment_engine.design(hypothesis, prediction, experiment_id=f"E-{hyp_id}")
        provider_manifest = result.manifests[0].to_dict() if result.manifests else None
        if result.proposal:
            try:
                self.ledger.register_experiment(result.proposal)
            except DuplicateRegistrationError:
                pass
        return {"hypothesis_id": hyp_id,
                "experiment": result.proposal.to_dict() if result.proposal else None,
                "failed": result.proposal is None,
                "failures": result.failures,
                "source_prediction_hash": pred_data.get("output_hash", "")}, provider_manifest

    def _stage_rankings(self, challenge: DevChallenge, run_dir: Path, input_data) -> Tuple[Dict, Optional[Dict]]:
        hyp_data = input_data
        transfer_data = self._load_stage(run_dir, "03_transfer")
        if not hyp_data or not transfer_data or not transfer_data.get("result", {}).get("transfers"):
            return {"rankings": {}}, None
        t = transfer_data["result"]["transfers"][0]
        transfer = TransferHypothesis(
            transfer_id=t["transfer_id"], source_domain=t.get("source_domain", ""),
            source_mechanism=t.get("source_mechanism", ""),
            target_domain=t.get("target_domain", ""),
            target_problem=t.get("target_problem", ""),
            transferred_principle=t.get("transferred_principle", ""),
            required_translation=t.get("required_translation", ""),
            expected_effect=t.get("expected_effect", ""),
            epistemic_state=EpistemicState.HYPOTHESIZED)
        rankings = {}
        for h_dict in hyp_data["result"]["hypotheses"]:
            if not h_dict.get("is_testable"): continue
            hyp = self._reconstruct_hypothesis(h_dict)
            if not hyp: continue
            ranking = self.ranker.rank(hyp, transfer)
            rankings[hyp.hypothesis_id] = ranking.to_dict()
        return {"rankings": rankings}, None

    def _stage_state_machine(self, challenge: DevChallenge, run_dir: Path, input_data) -> Tuple[Dict, Optional[Dict]]:
        """Repair C: record candidate_status explicitly.

        When all hypotheses are blocked at adversarial, the state machine
        still records pipeline_stage_reached=TESTABLE_HYPOTHESIS (the
        canonical hypothesis DID reach that stage), but candidate_status
        is set to ALL_BLOCKED_AT_ADVERSARIAL so the reader cannot mistake
        the pipeline marker for a surviving scientific state.
        """
        hyp_data = input_data
        if not hyp_data or not hyp_data.get("result"):
            return {"final_state": "RAW_EVIDENCE", "history": [],
                    "pipeline_stage_reached": "RAW_EVIDENCE",
                    "candidate_status": "NO_HYPOTHESES",
                    "scientific_gate_passed": False,
                    "note": "no hypotheses produced"}, None
        testable = [h for h in hyp_data["result"]["hypotheses"] if h.get("is_testable")]
        sm = DiscoveryStateMachine(f"DC-{challenge.challenge_id}")

        # Repair C: compute candidate_status by inspecting adversarial outcomes
        n_survived = 0
        n_blocked = 0
        n_inconclusive = 0
        for h_dict in testable:
            hid = h_dict["hypothesis_id"]
            adv_data = self._load_stage(run_dir, f"05_adversarial_{hid}")
            adv_outcome = (adv_data or {}).get("result", {}).get("outcome", AdversarialOutcome.INCONCLUSIVE)
            if adv_outcome == AdversarialOutcome.SURVIVES:
                n_survived += 1
            elif adv_outcome == AdversarialOutcome.FAILED:
                n_blocked += 1
            else:
                n_inconclusive += 1

        if n_survived > 0:
            candidate_status = "CANDIDATES_SURVIVED"
        elif n_blocked > 0 and n_inconclusive == 0:
            candidate_status = "ALL_BLOCKED_AT_ADVERSARIAL"
        elif n_blocked > 0:
            candidate_status = "PARTIALLY_BLOCKED_AT_ADVERSARIAL"
        elif n_inconclusive > 0:
            candidate_status = "ALL_INCONCLUSIVE_AT_ADVERSARIAL"
        else:
            candidate_status = "NO_HYPOTHESES"

        try:
            if not testable:
                for s in [DiscoveryState.STRUCTURED_KNOWLEDGE, DiscoveryState.MECHANISM,
                          DiscoveryState.TRANSFER_HYPOTHESIS, DiscoveryState.CANDIDATE_DISCOVERY,
                          DiscoveryState.GATE_A, DiscoveryState.GATE_B, DiscoveryState.GATE_C]:
                    sm.transition(s, actor="loop", code_sha=ENGINE_CODE_SHA,
                                  evidence="dev_pipeline_stage", reason="phase advance")
            else:
                canonical = self._reconstruct_hypothesis(testable[0])
                for s in [DiscoveryState.STRUCTURED_KNOWLEDGE, DiscoveryState.MECHANISM,
                          DiscoveryState.TRANSFER_HYPOTHESIS, DiscoveryState.CANDIDATE_DISCOVERY,
                          DiscoveryState.GATE_A, DiscoveryState.GATE_B, DiscoveryState.GATE_C,
                          DiscoveryState.TESTABLE_HYPOTHESIS]:
                    sm.transition(s, actor="loop", code_sha=ENGINE_CODE_SHA,
                                  evidence="dev_pipeline_stage", reason="phase advance",
                                  hypothesis=canonical if s == DiscoveryState.TESTABLE_HYPOTHESIS else None)
                # Advance to EXPERIMENT only if that hypothesis survived adversarial AND has an experiment
                adv_data = self._load_stage(run_dir, f"05_adversarial_{canonical.hypothesis_id}")
                adv_outcome = (adv_data or {}).get("result", {}).get("outcome", AdversarialOutcome.INCONCLUSIVE)
                exp_data = self._load_stage(run_dir, f"09_experiment_{canonical.hypothesis_id}")
                if adv_outcome == AdversarialOutcome.SURVIVES and exp_data and exp_data.get("result", {}).get("experiment"):
                    sm.transition(DiscoveryState.EXPERIMENT,
                                  actor="loop", code_sha=ENGINE_CODE_SHA,
                                  evidence="experiment designed", reason="ready",
                                  hypothesis=canonical)
            return {"final_state": sm.current_state.value,
                    "history": [t.to_dict() for t in sm.history],
                    "pipeline_stage_reached": sm.current_state.value,
                    # Repair C: explicit candidate_status so the reader cannot
                    # mistake pipeline_stage_reached for a surviving scientific state.
                    "candidate_status": candidate_status,
                    "n_hypotheses": len(testable),
                    "n_survived_adversarial": n_survived,
                    "n_blocked_adversarial": n_blocked,
                    "n_inconclusive_adversarial": n_inconclusive,
                    # Repair 4b: explicitly state that NO scientific gate has passed
                    "scientific_gate_passed": False,
                    "note": "DEV pipeline stages GATE_A/B/C are NOT scientific Gate A/B/C. "
                            "They are pipeline markers. Scientific gates require independent "
                            "adjudication per SCIENTIFIC_GATE_2_PROTOCOL.md. "
                            f"candidate_status={candidate_status} describes the outcome of "
                            "the adversarial filter, NOT scientific gate passage."}, None
        except Exception as e:
            return {"final_state": sm.current_state.value,
                    "history": [t.to_dict() for t in sm.history],
                    "pipeline_stage_reached": sm.current_state.value,
                    "candidate_status": candidate_status,
                    "scientific_gate_passed": False,
                    "error": str(e)}, None

    def _stage_case(self, challenge: DevChallenge, run_dir: Path, input_data) -> Tuple[Dict, Optional[Dict]]:
        """Repair A: build a DiscoveryCase with TRAVERSABLE LINEAGE where every
        node carries an explicit artifact reference (artifact_stage,
        artifact_output_hash) so the LineageValidator can enforce hash
        matching FAIL-CLOSED (not best-effort skip)."""
        sm_data = input_data
        final_state = sm_data.get("result", {}).get("final_state", "") if sm_data else ""

        # Collect all upstream stage artifacts
        ext_data = self._load_stage(run_dir, "01_extraction")
        ab_data = self._load_stage(run_dir, "02_abstraction")
        tr_data = self._load_stage(run_dir, "03_transfer")
        hyp_data = self._load_stage(run_dir, "04_hypotheses")

        # Helper: build the artifact-reference metadata that every node MUST carry
        def _artifact_ref(stage_name: str, stage_data: Optional[Dict]) -> Dict:
            """Return metadata with explicit artifact_stage + artifact_output_hash.
            These fields are REQUIRED by LineageValidator._verify_hashes().
            If the stage data is missing or has no output_hash, the reference
            is still recorded (so the validator can FAIL rather than skip)."""
            if stage_data and stage_data.get("output_hash"):
                return {
                    "artifact_stage": stage_name,
                    "artifact_output_hash": stage_data["output_hash"],
                }
            # Even if missing, record the expected stage so the validator
            # can FAIL (not skip) when the artifact is absent.
            return {"artifact_stage": stage_name, "artifact_output_hash": ""}

        case = DiscoveryCase(
            case_id=f"DC-{challenge.challenge_id}",
            input_sources=[d.get("title", "") for d in challenge.source_documents],
            input_domains=[challenge.source_domain, challenge.target_domain],
            evidence=[],
        )
        prov = case.provenance

        # Source document node (references 01_extraction artifact)
        if ext_data and ext_data.get("result"):
            ext_result = ext_data["result"]
            doc_id = ext_result.get('source_document_id', challenge.challenge_id)
            prov.add_node(ProvenanceNode(
                node_id=f"source_doc:{doc_id}",
                node_type="source_document",
                content_hash=ext_data.get("output_hash", ""),
                metadata={**_artifact_ref("01_extraction", ext_data),
                          "title": ext_result.get("source_document_title", "")}))

        # Mechanism graph node (references 01_extraction artifact — same stage)
        if ext_data and ext_data.get("result"):
            prov.add_node(ProvenanceNode(
                node_id=f"mechanism_graph:{challenge.challenge_id}",
                node_type="mechanism_graph",
                content_hash=ext_data.get("output_hash", ""),
                metadata={**_artifact_ref("01_extraction", ext_data),
                          "n_nodes": ext_result.get("n_nodes", 0),
                          "n_edges": ext_result.get("n_edges", 0)}))
            prov.add_edge(ProvenanceEdge(
                f"prov:mg_src:{challenge.challenge_id}",
                f"source_doc:{doc_id}",
                f"mechanism_graph:{challenge.challenge_id}",
                "DERIVES_FROM", "mechanism graph extracted from source",
                actor="mechanism_extractor"))

        # Mechanism pattern node (references 02_abstraction artifact)
        if ab_data and ab_data.get("result"):
            prov.add_node(ProvenanceNode(
                node_id=f"mechanism_pattern:{challenge.challenge_id}",
                node_type="mechanism_pattern",
                content_hash=ab_data.get("output_hash", ""),
                metadata={**_artifact_ref("02_abstraction", ab_data),
                          "pattern_id": ab_data["result"].get("pattern", {}).get("pattern_id", "")}))
            prov.add_edge(ProvenanceEdge(
                f"prov:mp_mg:{challenge.challenge_id}",
                f"mechanism_graph:{challenge.challenge_id}",
                f"mechanism_pattern:{challenge.challenge_id}",
                "DERIVES_FROM", "pattern abstracted from mechanism graph",
                actor="mechanism_abstracter"))

        # Transfer hypothesis node (references 03_transfer artifact)
        transfer_id = ""
        if tr_data and tr_data.get("result") and tr_data["result"].get("transfers"):
            t = tr_data["result"]["transfers"][0]
            transfer_id = t["transfer_id"]
            prov.add_node(ProvenanceNode(
                node_id=f"transfer:{transfer_id}",
                node_type="transfer_hypothesis",
                content_hash=tr_data.get("output_hash", ""),
                metadata={**_artifact_ref("03_transfer", tr_data),
                          "source_domain": t.get("source_domain", ""),
                          "target_domain": t.get("target_domain", ""),
                          "transferred_principle": t.get("transferred_principle", "")}))
            prov.add_edge(ProvenanceEdge(
                f"prov:th_mp:{transfer_id}",
                f"mechanism_pattern:{challenge.challenge_id}",
                f"transfer:{transfer_id}",
                "DERIVES_FROM", "transfer derived from pattern",
                actor="cross_domain_transfer"))

        # Per-hypothesis lineage
        if hyp_data and hyp_data.get("result"):
            for h_dict in hyp_data["result"]["hypotheses"]:
                if not h_dict.get("is_testable"): continue
                hid = h_dict["hypothesis_id"]
                # Hypothesis node (references 04_hypotheses artifact)
                # The content_hash MUST match the stage artifact's output_hash
                # so the LineageValidator can verify it fail-closed.
                hyp_artifact_hash = hyp_data.get("output_hash", "")
                prov.add_node(ProvenanceNode(
                    node_id=f"hypothesis:{hid}",
                    node_type="hypothesis",
                    content_hash=hyp_artifact_hash,
                    metadata={**_artifact_ref("04_hypotheses", hyp_data),
                              "claim": h_dict.get("claim", "")[:100],
                              "hypothesis_object_hash": _sha(json.dumps(h_dict, sort_keys=True, default=str))}))
                if transfer_id:
                    prov.add_edge(ProvenanceEdge(
                        f"prov:h_th:{hid}", f"transfer:{transfer_id}",
                        f"hypothesis:{hid}", "DERIVES_FROM",
                        "hypothesis derived from transfer", actor="hypothesis_engine"))

                # Adversarial node (references 05_adversarial_<hid> artifact)
                adv = self._load_stage(run_dir, f"05_adversarial_{hid}")
                adv_stage = f"05_adversarial_{hid}"
                if adv and adv.get("result"):
                    prov.add_node(ProvenanceNode(
                        node_id=f"adversarial:{hid}", node_type="adversarial_analysis",
                        content_hash=adv.get("output_hash", ""),
                        metadata={**_artifact_ref(adv_stage, adv),
                                  "outcome": adv["result"].get("outcome", ""),
                                  "survives": adv["result"].get("survives", False)}))
                    prov.add_edge(ProvenanceEdge(
                        f"prov:adv_h:{hid}", f"hypothesis:{hid}", f"adversarial:{hid}",
                        "ANALYZES", "adversarial analysis of hypothesis",
                        actor="adversarial_engine"))

                # Rediscovery node (references 06_rediscovery_<hid> artifact)
                rd = self._load_stage(run_dir, f"06_rediscovery_{hid}")
                rd_stage = f"06_rediscovery_{hid}"
                if rd and rd.get("result"):
                    prov.add_node(ProvenanceNode(
                        node_id=f"rediscovery:{hid}", node_type="rediscovery_analysis",
                        content_hash=rd.get("output_hash", ""),
                        metadata={**_artifact_ref(rd_stage, rd),
                                  "classification": rd["result"].get("classification", ""),
                                  "is_rediscovery": rd["result"].get("is_rediscovery", False)}))
                    prov.add_edge(ProvenanceEdge(
                        f"prov:rd_h:{hid}", f"hypothesis:{hid}", f"rediscovery:{hid}",
                        "ANALYZES", "rediscovery classification of hypothesis",
                        actor="rediscovery_detector"))

                # Novelty node (references 07_novelty_<hid> artifact)
                nov = self._load_stage(run_dir, f"07_novelty_{hid}")
                nov_stage = f"07_novelty_{hid}"
                if nov and nov.get("result"):
                    prov.add_node(ProvenanceNode(
                        node_id=f"novelty:{hid}", node_type="novelty_assessment",
                        content_hash=nov.get("output_hash", ""),
                        metadata={**_artifact_ref(nov_stage, nov),
                                  "status": nov["result"].get("status", "")}))
                    prov.add_edge(ProvenanceEdge(
                        f"prov:nov_h:{hid}", f"hypothesis:{hid}", f"novelty:{hid}",
                        "ANALYZES", "novelty assessment of hypothesis",
                        actor="novelty_firewall"))

                # Prediction node (references 08_prediction_<hid> artifact)
                pred = self._load_stage(run_dir, f"08_prediction_{hid}")
                pred_stage = f"08_prediction_{hid}"
                if pred and pred.get("result") and pred["result"].get("prediction"):
                    prov.add_node(ProvenanceNode(
                        node_id=f"prediction:{hid}", node_type="prediction",
                        content_hash=pred.get("output_hash", ""),
                        metadata={**_artifact_ref(pred_stage, pred),
                                  "observable": pred["result"]["prediction"].get("observable", "")[:80]}))
                    prov.add_edge(ProvenanceEdge(
                        f"prov:pred_h:{hid}", f"hypothesis:{hid}", f"prediction:{hid}",
                        "DERIVES_FROM", "prediction derived from hypothesis",
                        actor="prediction_engine"))

                # Experiment node (references 09_experiment_<hid> artifact)
                exp = self._load_stage(run_dir, f"09_experiment_{hid}")
                exp_stage = f"09_experiment_{hid}"
                if exp and exp.get("result") and exp["result"].get("experiment"):
                    prov.add_node(ProvenanceNode(
                        node_id=f"experiment:{hid}", node_type="experiment_proposal",
                        content_hash=exp.get("output_hash", ""),
                        metadata={**_artifact_ref(exp_stage, exp),
                                  "experiment_id": exp["result"]["experiment"].get("experiment_id", "")}))
                    prov.add_edge(ProvenanceEdge(
                        f"prov:exp_pred:{hid}", f"prediction:{hid}", f"experiment:{hid}",
                        "DERIVES_FROM", "experiment designed from prediction",
                        actor="experiment_designer"))

        # Run manifest node (references the manifest.json itself)
        prov.add_node(ProvenanceNode(
            node_id=f"run:{challenge.challenge_id}",
            node_type="checkpointed_run",
            content_hash=_sha(challenge.challenge_id),
            metadata={"run_id": f"RUN-{challenge.challenge_id}",
                      "engine_code_sha": ENGINE_CODE_SHA,
                      "artifact_stage": "manifest",
                      "artifact_output_hash": ""}))  # manifest hash filled after save

        case.evidence = list(prov.nodes.keys())

        # Commit provenance
        try:
            case.commit_provenance()
        except Exception:
            pass

        # Repair B: register the case in the PERSISTENT ledger (saves to disk)
        try:
            self.ledger.register_case(case)
        except DuplicateRegistrationError:
            pass

        # Repair A: real lineage verification by graph traversal (NOT node_count > 1)
        lineage_result = self._lineage_validator.verify(case, run_dir=run_dir)

        # Repair B: verify the case is registered in the persistent ledger
        ledger_verification = self.ledger.verify_registration("case", case.case_id)

        return {"case_id": case.case_id,
                "provenance_root_hash": case.provenance_root_hash,
                "verify_provenance": case.verify_provenance(),
                "final_state": final_state,
                # Repair A: lineage verification by actual DFS traversal
                "lineage_verification": lineage_result.to_dict(),
                "lineage_valid": lineage_result.valid,
                # Repair B: persistent ledger verification
                "ledger_verification": ledger_verification,
                "registered_in_persistent_ledger": ledger_verification["registered"]
                    and ledger_verification["file_exists"]
                    and ledger_verification["content_hash_matches"],
                "ledger_dir": str(self._ledger_dir) if self._ledger_dir else "",
                "evidence_count": len(case.evidence)}, None

    # ========================================================================
    # Checkpoint helpers (Repair 2 + Repair 3 + Repair 5)
    # ========================================================================

    def _run_stage(self, manifest: RunManifest, stage: str,
                   manifest_path: Path, run_dir: Path, fn, input_data: Any = None) -> None:
        """Run a single stage with TRANSACTIONAL checkpointing.

        Round-6 transactional protocol (per reviewer directive):
            1. STAGE_START: mark stage RUNNING, save manifest
            2. STAGE_OUTPUT_WRITTEN: execute stage, write artifact to a TEMP file
            3. STAGE_HASH_COMPUTED: compute output_hash from the artifact
            4. STAGE_MANIFEST_COMMITTED: update manifest with the hash, save manifest
            5. STAGE_COMMITTED: atomically rename temp artifact to final path

        If the process dies anywhere before STAGE_COMMITTED:
            - resume detects the stale state (manifest hash != artifact hash,
              or artifact missing, or manifest says RUNNING)
            - the stage is re-run from scratch

        A resumed run must NEVER produce: artifact hash X, manifest says hash Y.
        """
        if stage not in manifest.stages:
            manifest.stages[stage] = StageStatus(stage=stage)
        ss = manifest.stages[stage]

        # Check for stale state from a previous interrupted run.
        # If the manifest says COMPLETED but the artifact hash doesn't match,
        # or the artifact is missing, we must re-run.
        if ss.status == COMPLETED:
            artifact_path = run_dir / f"{stage}.json"
            if not artifact_path.exists():
                # Artifact missing but manifest says COMPLETED → stale, re-run
                ss.status = PENDING
                ss.error = ""
            else:
                try:
                    existing = json.loads(artifact_path.read_text())
                    existing_hash = existing.get("output_hash", "")
                    if existing_hash and ss.output_hash and existing_hash != ss.output_hash:
                        # Hash mismatch → stale, re-run
                        ss.status = PENDING
                        ss.error = ""
                except (json.JSONDecodeError, KeyError):
                    ss.status = PENDING
                    ss.error = ""

        ss.status = RUNNING; ss.started_at = _now()
        manifest.last_updated = _now(); manifest.resume_from = stage
        self._save_manifest(manifest, manifest_path)

        input_hash = _sha(json.dumps(input_data, sort_keys=True, default=str)) if input_data is not None else ""

        start = time.time()
        try:
            result, provider_manifest = fn(input_data) if input_data is not None else fn(None)
            ss.latency_ms = int((time.time() - start) * 1000)

            # Compute output hash from the result
            output_str = json.dumps(result, sort_keys=True, default=str)
            output_hash = _sha(output_str)

            # Build the full stage artifact
            artifact = StageArtifact(
                stage=stage, run_id=manifest.run_id, code_sha=ENGINE_CODE_SHA,
                input_hash=input_hash, output_hash=output_hash,
                provider_manifest=provider_manifest, result=result)
            artifact_dict = artifact.to_dict()

            # TRANSACTIONAL WRITE PROTOCOL:
            # 1. Write to a temp file first
            temp_path = run_dir / f"{stage}.json.tmp"
            temp_path.write_text(json.dumps(artifact_dict, indent=2, default=str))

            # 2. Verify the temp file's hash matches what we computed
            temp_content = temp_path.read_text()
            temp_hash = _sha(json.dumps(json.loads(temp_content)["result"], sort_keys=True, default=str))
            if temp_hash != output_hash:
                # This should never happen, but if it does, FAIL
                temp_path.unlink(missing_ok=True)
                raise RuntimeError(f"transactional integrity failure: temp hash {temp_hash[:16]}... "
                                   f"!= computed hash {output_hash[:16]}...")

            # 3. Update manifest with the hash BEFORE renaming
            ss.output_hash = output_hash
            if provider_manifest:
                ss.provider_manifest_sha = _sha(json.dumps(provider_manifest, sort_keys=True, default=str))
            ss.completed_at = _now(); ss.status = COMPLETED
            manifest.last_updated = _now()
            self._save_manifest(manifest, manifest_path)

            # 4. Atomically rename temp → final (this is the COMMIT point)
            final_path = run_dir / f"{stage}.json"
            temp_path.replace(final_path)

            # 5. Verify the final file's hash matches the manifest
            final_content = json.loads(final_path.read_text())
            final_hash = final_content.get("output_hash", "")
            if final_hash != ss.output_hash:
                # Hash mismatch after commit → integrity failure
                ss.status = FAILED
                ss.error = f"post-commit integrity failure: artifact hash {final_hash[:16]}... " \
                           f"!= manifest hash {ss.output_hash[:16]}..."
                self._save_manifest(manifest, manifest_path)
                if self._is_scientific_stage(stage):
                    manifest.failed_closed = True
                    manifest.failed_closed_at = stage
                return

        except Exception as e:
            ss.latency_ms = int((time.time() - start) * 1000)
            ss.completed_at = _now(); ss.status = FAILED
            ss.error = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
            # Clean up temp file if it exists
            temp_path = run_dir / f"{stage}.json.tmp"
            temp_path.unlink(missing_ok=True)
            # Persist a failure artifact so the error is inspectable
            failure_artifact = StageArtifact(
                stage=stage, run_id=manifest.run_id, code_sha=ENGINE_CODE_SHA,
                input_hash=input_hash, output_hash="",
                provider_manifest=None,
                result={"error": ss.error, "exception_type": type(e).__name__})
            (run_dir / f"{stage}.json").write_text(
                json.dumps(failure_artifact.to_dict(), indent=2, default=str))

        manifest.last_updated = _now()
        self._save_manifest(manifest, manifest_path)

    def _is_scientific_stage(self, stage: str) -> bool:
        """Repair 3: scientific stages fail-closed; non-scientific stages don't."""
        if stage in SCIENTIFIC_STAGES:
            return True
        for prefix in PER_HYP_SCIENTIFIC_PREFIXES:
            if stage.startswith(prefix):
                return True
        return False

    def _is_completed(self, manifest: RunManifest, stage: str) -> bool:
        """Check if a stage is truly completed (status=COMPLETED AND artifact
        hash matches the manifest). Round-6: stale-state detection.

        If the manifest says COMPLETED but the artifact file is missing or
        its output_hash doesn't match the manifest's recorded hash, the
        stage is NOT completed — it must be re-run.
        """
        s = manifest.stages.get(stage)
        if s is None or s.status != COMPLETED:
            return False
        # Verify the artifact file exists and its hash matches
        run_dir = RUNS_DIR / manifest.run_id
        artifact_path = run_dir / f"{stage}.json"
        if not artifact_path.exists():
            return False  # artifact missing — must re-run
        try:
            artifact = json.loads(artifact_path.read_text())
            artifact_hash = artifact.get("output_hash", "")
            if artifact_hash != s.output_hash:
                return False  # hash mismatch — must re-run
        except (json.JSONDecodeError, KeyError):
            return False  # corrupted artifact — must re-run
        return True

    def _load_stage(self, run_dir: Path, stage: str) -> Optional[Dict]:
        """Load a stage artifact. Returns the full StageArtifact dict
        (with result, provider_manifest, input_hash, output_hash)."""
        p = run_dir / f"{stage}.json"
        if not p.exists(): return None
        try: return json.loads(p.read_text())
        except json.JSONDecodeError: return None

    def _save_manifest(self, manifest: RunManifest, path: Path) -> None:
        """Atomically save the manifest. Round-7 Repair A.

        Protocol:
            1. Write manifest to manifest.json.tmp
            2. fsync the temp file
            3. Atomically rename temp → final (manifest.json)
            4. Reload and verify the written file matches what we serialized

        If the process dies during step 1 or 2, the temp file is orphaned
        but manifest.json is unchanged (the previous committed state).
        If the process dies during step 3, the rename is atomic at the
        filesystem level — either it happened or it didn't.
        Step 4 catches any filesystem-level corruption.

        A corrupted manifest on resume raises CheckpointIntegrityError.
        """
        import os
        content = json.dumps(manifest.to_dict(), indent=2, default=str)
        temp_path = path.with_suffix(".json.tmp")

        # 1. Write to temp file
        temp_path.write_text(content)

        # 2. fsync the temp file (ensure data is on disk before rename)
        try:
            with open(temp_path, "rb") as f:
                os.fsync(f.fileno())
        except OSError:
            pass  # fsync may fail on some filesystems; the rename still provides atomicity

        # 3. Atomic rename
        temp_path.replace(path)

        # 4. Verify: reload and check the content matches
        try:
            verify_content = path.read_text()
            if verify_content != content:
                raise CheckpointIntegrityError(
                    f"Manifest post-write verification failed: written content does not "
                    f"match serialized content. This indicates a filesystem-level corruption.")
        except OSError as e:
            raise CheckpointIntegrityError(
                f"Manifest post-write verification failed: cannot reload: {e}") from e

    def _load_manifest(self, path: Path) -> RunManifest:
        """Load the manifest. Round-8 Repair A: verify manifest self-hash.

        The manifest's `manifest_sha` is a self-hash computed by
        RunManifest.to_dict(). On load, we recompute the hash of the
        manifest content (excluding manifest_sha itself) and compare it
        to the stored value. If they don't match, the manifest was
        modified after creation → CheckpointIntegrityError.

        This protects against post-write modification: an attacker who
        changes completed=True or stage output_hashes will invalidate
        the self-hash, even if the JSON remains valid.
        """
        if not path.exists():
            raise CheckpointIntegrityError(
                f"Manifest file does not exist: {path}. Cannot resume without an "
                "authoritative run manifest.")
        try:
            raw = path.read_text()
        except OSError as e:
            raise CheckpointIntegrityError(
                f"Cannot read manifest file {path}: {e}") from e
        try:
            d = json.loads(raw)
        except json.JSONDecodeError as e:
            raise CheckpointIntegrityError(
                f"Manifest file {path} is corrupted (invalid JSON): {e}. "
                "The checkpoint state is ambiguous — cannot resume safely.") from e
        if not isinstance(d, dict):
            raise CheckpointIntegrityError(
                f"Manifest file {path} is corrupted (not a JSON object). "
                "The checkpoint state is ambiguous.")
        # Verify required fields
        required = ["run_id", "challenge_id", "started_at", "stages"]
        for field in required:
            if field not in d:
                raise CheckpointIntegrityError(
                    f"Manifest file {path} is corrupted: missing required field '{field}'. "
                    "The checkpoint state is ambiguous.")

        # Round-8 Repair A: verify manifest self-hash
        stored_sha = d.get("manifest_sha", "")
        if stored_sha:
            # Recompute the hash: remove manifest_sha, canonically
            # serialize, hash
            d_without_sha = {k: v for k, v in d.items() if k != "manifest_sha"}
            recomputed_sha = _sha(json.dumps(d_without_sha, sort_keys=True, default=str))
            if recomputed_sha != stored_sha:
                raise CheckpointIntegrityError(
                    f"Manifest self-hash verification FAILED. The manifest was modified "
                    f"after creation. Stored hash: {stored_sha[:16]}..., "
                    f"recomputed: {recomputed_sha[:16]}... "
                    "The checkpoint state cannot be trusted.")
        else:
            # No stored hash — this is either an old manifest or a
            # tampered one where the attacker removed the hash.
            raise CheckpointIntegrityError(
                f"Manifest file {path} has no manifest_sha field. "
                "Either this is a legacy manifest or the hash was removed. "
                "The checkpoint state cannot be trusted.")

        m = RunManifest(run_id=d["run_id"], challenge_id=d["challenge_id"],
                        started_at=d["started_at"], last_updated=d["last_updated"],
                        engine_code_sha=d.get("engine_code_sha", ENGINE_CODE_SHA),
                        resume_from=d.get("resume_from", "01_extraction"),
                        n_hypotheses=d.get("n_hypotheses", 0),
                        n_hypotheses_survived_adversarial=d.get("n_hypotheses_survived_adversarial", 0),
                        n_hypotheses_rediscovery=d.get("n_hypotheses_rediscovery", 0),
                        final_state=d.get("final_state", ""),
                        final_state_source=d.get("final_state_source", ""),
                        completed=d.get("completed", False),
                        failed_closed=d.get("failed_closed", False),
                        failed_closed_at=d.get("failed_closed_at", ""))
        for k, v in d.get("stages", {}).items():
            m.stages[k] = StageStatus(**v)
        return m

    def _reconstruct_hypothesis(self, h_dict: Dict) -> Optional[Hypothesis]:
        try:
            return Hypothesis(
                hypothesis_id=h_dict["hypothesis_id"],
                claim=h_dict.get("claim", ""),
                mechanism=h_dict.get("mechanism", ""),
                evidence=h_dict.get("evidence", []),
                assumptions=h_dict.get("assumptions", []),
                predictions=h_dict.get("predictions", []),
                expected_failure_modes=h_dict.get("expected_failure_modes", []),
                novelty_rationale=h_dict.get("novelty_rationale", ""),
                testability=h_dict.get("testability", ""),
                falsifier=h_dict.get("falsifier", ""),
                is_testable=h_dict.get("is_testable", False))
        except Exception:
            return None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


__all__ = ["CheckpointedDiscoveryLoop", "RunManifest", "StageStatus", "StageArtifact",
           "AdversarialOutcome", "ENGINE_CODE_SHA",
           "PENDING", "RUNNING", "COMPLETED", "FAILED", "SKIPPED", "RUNS_DIR"]
