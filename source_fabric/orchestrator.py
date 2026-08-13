"""
Source Fabric orchestrator (Issue #5).

End-to-end pipeline:
  1. Validate all sources (structural)
  2. Produce source registry manifest
  3. Produce domain map summary
  4. Verify snapshot discipline (live vs frozen separation)
  5. Produce forensic integrity report
  6. Honest boundary: NO_LIVE_INGEST (no credentials); framework ready

Honest boundaries (per Honest-Boundary rule):
  - NO_LIVE_INGEST: no live HTTP calls made. All connectors raise HarvestError
    when --live is not passed. To enable live harvest, operator must pass
    credentials via environment variables.
  - REAL_DATA_SEAL: FALSE. No real data has been harvested.
  - IS_SCIENTIFIC_RESULT: FALSE. Always.
  - PSCD-1 frozen. A2 unauthorized.
"""
from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

from .source_registry import (SOURCES, registry_manifest, get_all_sources,
                               get_primary_sources, get_aggregators)
from .domain_map import DOMAINS, domain_map_summary
from .source_validator import validate_all_sources
from .failure_recorder import FailureLog
from .snapshot_manager import create_snapshot, verify_snapshot
from .connector_base import HarvestedRecord, HarvestState, hash_payload, now_iso
from .provenance import PREDICATES, CROSS_CORPUS_PREDICATES, EMPIRICAL_PREDICATES
from .multilingual import SUPPORTED_LANGUAGES
from .knowledge_distance import WEIGHTS
from .cross_evidence_motifs import ALL_CROSS_EVIDENCE_MOTIFS


@dataclass
class FabricState:
    fabric_id: str
    generated_at: str
    total_sources: int
    primary_sources: int
    aggregator_sources: int
    total_domains: int
    total_universes: int
    structural_validation_pass: int
    structural_validation_fail: int
    live_check_performed: bool        # ALWAYS False in offline mode
    real_data_seal: bool              # ALWAYS False (no live ingest)
    is_scientific_result: bool        # ALWAYS False
    snapshot_created: bool
    snapshot_verified: bool
    failure_log_path: str
    registry_manifest: dict
    domain_map_summary: dict
    provenance_vocabulary_size: int
    cross_corpus_predicates: list[str]
    empirical_predicates: list[str]
    supported_languages_count: int
    cross_evidence_motif_count: int

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, default=str)


def run_fabric(output_dir: Path | None = None) -> dict:
    """Run the source fabric pipeline. Returns the final state + report path."""
    if output_dir is None:
        output_dir = Path(__file__).parent / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    # --- 1. Source registry manifest ---
    reg_manifest = registry_manifest()

    # --- 2. Domain map summary ---
    dmap = domain_map_summary()

    # --- 3. Structural validation of all sources ---
    validation = validate_all_sources()

    # --- 4. Initialize failure log (empty) ---
    failure_log = FailureLog(output_dir / "failure_log.jsonl")
    failure_summary = failure_log.summary()

    # --- 5. Create an EMPTY snapshot (no records harvested in offline mode) ---
    # The snapshot machinery is exercised, but contains no real records.
    # This is the honest boundary: we prove the snapshot discipline works,
    # but we cannot claim real data has been ingested.
    empty_records: list[HarvestedRecord] = []
    snapshot_result = create_snapshot(empty_records, cutoff=now_iso()[:10],
                                       snapshot_dir=output_dir / "empty_snapshot")
    snapshot_verify = verify_snapshot(output_dir / "empty_snapshot")

    # --- 6. Build final state ---
    state = FabricState(
        fabric_id=f"fabric:{reg_manifest['registry_content_hash'][:12]}",
        generated_at=datetime.now(timezone.utc).isoformat(),
        total_sources=reg_manifest["total_sources"],
        primary_sources=reg_manifest["primary_count"],
        aggregator_sources=reg_manifest["aggregator_count"],
        total_domains=dmap["total_domains"],
        total_universes=dmap["total_universes"],
        structural_validation_pass=validation["structural_pass"],
        structural_validation_fail=validation["structural_fail"],
        live_check_performed=False,
        real_data_seal=False,
        is_scientific_result=False,
        snapshot_created=True,
        snapshot_verified=snapshot_verify["valid"],
        failure_log_path=str(failure_log.path),
        registry_manifest=reg_manifest,
        domain_map_summary=dmap,
        provenance_vocabulary_size=len(PREDICATES),
        cross_corpus_predicates=sorted(CROSS_CORPUS_PREDICATES),
        empirical_predicates=sorted(EMPIRICAL_PREDICATES),
        supported_languages_count=len(SUPPORTED_LANGUAGES),
        cross_evidence_motif_count=len(ALL_CROSS_EVIDENCE_MOTIFS),
    )

    # --- 7. Write final report ---
    report_path = output_dir / "fabric_state.json"
    report_path.write_text(state.to_json())
    import hashlib
    h = hashlib.sha256(state.to_json().encode()).hexdigest()
    report_path.with_suffix(report_path.suffix + ".sha256").write_text(h)

    # --- 8. Write validation report ---
    val_path = output_dir / "source_validation_report.json"
    val_path.write_text(json.dumps(validation, sort_keys=True, indent=2, default=str))

    return {
        "state": asdict(state),
        "report_path": str(report_path),
        "validation_report_path": str(val_path),
        "snapshot_verify": snapshot_verify,
        "failure_log_summary": failure_summary,
    }


def forensic_audit(report_path: Path) -> dict:
    """Forensic audit of the fabric state report."""
    import hashlib
    checks = []
    if not report_path.exists():
        checks.append({"check": "REPORT_EXISTS", "passed": False})
        return {"passed": False, "checks": checks}
    checks.append({"check": "REPORT_EXISTS", "passed": True})

    hash_path = report_path.with_suffix(report_path.suffix + ".sha256")
    if not hash_path.exists():
        checks.append({"check": "HASH_SIDECAR_EXISTS", "passed": False})
        return {"passed": False, "checks": checks}
    checks.append({"check": "HASH_SIDECAR_EXISTS", "passed": True})

    content = report_path.read_text()
    expected = hash_path.read_text().strip()
    actual = hashlib.sha256(content.encode()).hexdigest()
    if actual != expected:
        checks.append({"check": "HASH_MATCHES", "passed": False,
                       "reason": "report hash mismatch (tampered)"})
        return {"passed": False, "checks": checks}
    checks.append({"check": "HASH_MATCHES", "passed": True})

    state = json.loads(content)
    # Honest-boundary checks
    if state.get("live_check_performed") is True:
        checks.append({"check": "LIVE_CHECK_HONEST", "passed": False,
                       "reason": "live_check_performed=True in offline mode"})
    else:
        checks.append({"check": "LIVE_CHECK_HONEST", "passed": True})

    if state.get("real_data_seal") is True:
        checks.append({"check": "REAL_DATA_SEAL_HONEST", "passed": False,
                       "reason": "real_data_seal=True without live ingest"})
    else:
        checks.append({"check": "REAL_DATA_SEAL_HONEST", "passed": True})

    if state.get("is_scientific_result") is True:
        checks.append({"check": "NOT_CLAIMED_AS_SCIENTIFIC", "passed": False})
    else:
        checks.append({"check": "NOT_CLAIMED_AS_SCIENTIFIC", "passed": True})

    if state.get("total_sources", 0) < 100:
        checks.append({"check": "MIN_100_SOURCES", "passed": False,
                       "reason": f"total_sources={state.get('total_sources')} < 100"})
    else:
        checks.append({"check": "MIN_100_SOURCES", "passed": True})

    if state.get("structural_validation_fail", 0) > 0:
        checks.append({"check": "ALL_SOURCES_STRUCTURALLY_VALID", "passed": False,
                       "reason": f"{state['structural_validation_fail']} sources failed"})
    else:
        checks.append({"check": "ALL_SOURCES_STRUCTURALLY_VALID", "passed": True})

    if not state.get("snapshot_verified"):
        checks.append({"check": "SNAPSHOT_VERIFIED", "passed": False})
    else:
        checks.append({"check": "SNAPSHOT_VERIFIED", "passed": True})

    if state.get("total_domains", 0) < 30:
        checks.append({"check": "MIN_30_DOMAINS", "passed": False})
    else:
        checks.append({"check": "MIN_30_DOMAINS", "passed": True})

    if state.get("total_universes", 0) != 6:
        checks.append({"check": "SIX_UNIVERSES", "passed": False})
    else:
        checks.append({"check": "SIX_UNIVERSES", "passed": True})

    if state.get("provenance_vocabulary_size", 0) < 15:
        checks.append({"check": "PROVENANCE_VOCAB_RICH", "passed": False})
    else:
        checks.append({"check": "PROVENANCE_VOCAB_RICH", "passed": True})

    all_pass = all(c["passed"] for c in checks)
    return {"passed": all_pass, "checks": checks, "state": state}
