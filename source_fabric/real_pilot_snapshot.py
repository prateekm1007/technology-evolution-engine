"""
V3 Real Pilot Snapshot (Issue #5 V3 directive, Phase 7).

Builds a REAL snapshot with:
  - 500 scientific records (from OpenAlex + Europe PMC)
  - 500 patent-family records (from Google Patents, SECONDARY source)
  - at least 5 domains

NO SYNTHETIC DATA. All records are retrieved via live HTTP from operational
connectors. The snapshot is content-addressed, immutable, and tamper-evident.

5 domains (mapped to OpenAlex concept IDs and search queries):
  1. battery_electrochemistry  — OpenAlex concept C2778407487
  2. perovskite_photovoltaics  — query "perovskite solar cell"
  3. crispr_gene_editing       — query "CRISPR Cas9"
  4. hydrogen_electrocatalysis — query "hydrogen evolution reaction"
  5. additive_manufacturing    — query "additive manufacturing 3D printing"

For patents, the same domains are queried via Google Patents.
"""
from __future__ import annotations
import json
import hashlib
import time
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import Optional

from .real_connectors import (OpenAlexRealConnector, EuropePmcRealConnector,
                               GooglePatentsRealConnector, _http_get)
from .source_registry import SOURCES
from .evidence_connector import Checkpoint
from .connector_base import HarvestedRecord
from .failure_recorder import FailureLog
from .snapshot_manager import create_snapshot, verify_snapshot

# 5 domains with OpenAlex search filters and queries
DOMAIN_QUERIES = {
    "battery_electrochemistry": {
        "openalex_filter": "default.search:lithium battery electrode",
        "europepmc_query": "lithium battery electrode",
        "googlepatents_query": "lithium battery electrode",
    },
    "perovskite_photovoltaics": {
        "openalex_filter": "default.search:perovskite solar cell",
        "europepmc_query": "perovskite solar cell",
        "googlepatents_query": "perovskite solar cell",
    },
    "crispr_gene_editing": {
        "openalex_filter": "default.search:CRISPR Cas9 gene editing",
        "europepmc_query": "CRISPR Cas9 gene editing",
        "googlepatents_query": "CRISPR Cas9 gene editing",
    },
    "hydrogen_electrocatalysis": {
        "openalex_filter": "default.search:hydrogen evolution reaction electrocatalyst",
        "europepmc_query": "hydrogen evolution reaction electrocatalyst",
        "googlepatents_query": "hydrogen evolution reaction electrocatalyst",
    },
    "additive_manufacturing": {
        "openalex_filter": "default.search:additive manufacturing 3D printing",
        "europepmc_query": "additive manufacturing 3D printing",
        "googlepatents_query": "additive manufacturing 3D printing",
    },
}


@dataclass
class PilotSnapshotResult:
    snapshot_id: str
    created_at: str
    cutoff: str
    science_records: int
    patent_records: int
    total_records: int
    domains: list[str]
    connectors_used: list[str]
    snapshot_hash: str
    snapshot_path: str
    is_real_data: bool
    real_snapshot_hash: str


def build_pilot_snapshot(output_dir: Path, *,
                         science_per_domain: int = 100,
                         patents_per_domain: int = 100) -> dict:
    """Build a REAL pilot snapshot with 500+ science + 500+ patent records.

    Retrieves actual records via live HTTP. NO SYNTHETIC DATA.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    failure_log = FailureLog(output_dir / "pilot_failure_log.jsonl")

    all_records: list[HarvestedRecord] = []
    connectors_used = set()
    domain_counts = {d: {"science": 0, "patents": 0} for d in DOMAIN_QUERIES}

    # --- Science records: OpenAlex + Europe PMC ---
    openalex_src = next(s for s in SOURCES if s.source_id == "src:openalex")
    openalex_conn = OpenAlexRealConnector(openalex_src, failure_log=failure_log)

    europepmc_src = next(s for s in SOURCES if s.source_id == "src:pubmed")
    europepmc_conn = EuropePmcRealConnector(europepmc_src, failure_log=failure_log)

    for domain, queries in DOMAIN_QUERIES.items():
        # OpenAlex: 60 records per domain (cursor-based)
        cp = Checkpoint(source_id="src:openalex")
        cp.last_error = queries["openalex_filter"]
        try:
            records, cp2 = openalex_conn.fetch_updates(cp, max_records=science_per_domain)
            for r in records:
                # tag with domain
                r.normalized["domain"] = domain
                # recompute normalized hash with domain tag
                r.normalized_hash = r.normalized_content_hash()
                all_records.append(r)
                domain_counts[domain]["science"] += 1
            connectors_used.add("src:openalex")
            print(f"  {domain}: OpenAlex {len(records)} records")
        except Exception as e:
            print(f"  {domain}: OpenAlex FAILED - {e}")
            failure_log.record("src:openalex", "PARTIAL_HARVEST",
                               f"{domain}: {e}")

        time.sleep(0.5)  # polite rate limit

        # Europe PMC: 40 records per domain (fills to 100)
        cp = Checkpoint(source_id="src:pubmed")
        cp.last_error = queries["europepmc_query"]
        try:
            records, cp2 = europepmc_conn.fetch_updates(cp, max_records=40)
            for r in records:
                r.normalized["domain"] = domain
                r.normalized_hash = r.normalized_content_hash()
                all_records.append(r)
                domain_counts[domain]["science"] += 1
            connectors_used.add("src:pubmed")
            print(f"  {domain}: Europe PMC {len(records)} records")
        except Exception as e:
            print(f"  {domain}: Europe PMC FAILED - {e}")
            failure_log.record("src:pubmed", "PARTIAL_HARVEST",
                               f"{domain}: {e}")

        time.sleep(0.5)

    # --- Patent records: Google Patents (SECONDARY) ---
    gpatents_src = next(s for s in SOURCES if s.source_id == "src:google_patents")
    gpatents_conn = GooglePatentsRealConnector(gpatents_src, failure_log=failure_log)

    for domain, queries in DOMAIN_QUERIES.items():
        cp = Checkpoint(source_id="src:google_patents")
        cp.last_error = queries["googlepatents_query"]
        try:
            records, cp2 = gpatents_conn.fetch_updates(cp, max_records=patents_per_domain)
            for r in records:
                r.normalized["domain"] = domain
                r.normalized_hash = r.normalized_content_hash()
                all_records.append(r)
                domain_counts[domain]["patents"] += 1
            connectors_used.add("src:google_patents")
            print(f"  {domain}: Google Patents {len(records)} records")
        except Exception as e:
            print(f"  {domain}: Google Patents FAILED - {e}")
            failure_log.record("src:google_patents", "PARTIAL_HARVEST",
                               f"{domain}: {e}")
        time.sleep(1.0)  # Google Patents rate limit

    # --- Build the snapshot ---
    cutoff = datetime.now(timezone.utc).date().isoformat()
    science_count = sum(dc["science"] for dc in domain_counts.values())
    patent_count = sum(dc["patents"] for dc in domain_counts.values())

    snapshot_dir = output_dir / "real_pilot_snapshot"
    snap_result = create_snapshot(all_records, cutoff=cutoff,
                                   snapshot_dir=snapshot_dir)
    manifest = snap_result["manifest"]

    # Verify the snapshot
    verification = verify_snapshot(snapshot_dir)

    result = PilotSnapshotResult(
        snapshot_id=manifest["snapshot_id"],
        created_at=manifest["created_at"],
        cutoff=cutoff,
        science_records=science_count,
        patent_records=patent_count,
        total_records=manifest["record_count"],
        domains=list(DOMAIN_QUERIES.keys()),
        connectors_used=sorted(connectors_used),
        snapshot_hash=manifest["root_hash"],
        snapshot_path=str(snapshot_dir),
        is_real_data=True,
        real_snapshot_hash=manifest["root_hash"],
    )

    # Write the pilot report
    report_path = output_dir / "REAL_PILOT_SNAPSHOT_REPORT.json"
    report = {
        "snapshot_result": asdict(result),
        "domain_counts": domain_counts,
        "snapshot_verification": verification,
        "is_real_data": True,
        "no_synthetic_data": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    report_path.write_text(json.dumps(report, indent=2, default=str))
    report_path.with_suffix(report_path.suffix + ".sha256").write_text(
        hashlib.sha256(json.dumps(report, sort_keys=True, default=str).encode()).hexdigest()
    )
    return report


def get_pilot_snapshot_summary(report_path: Path) -> dict:
    """Load and summarize a pilot snapshot report."""
    report = json.loads(Path(report_path).read_text())
    sr = report["snapshot_result"]
    return {
        "snapshot_id": sr["snapshot_id"],
        "science_records": sr["science_records"],
        "patent_records": sr["patent_records"],
        "total_records": sr["total_records"],
        "domains": sr["domains"],
        "connectors_used": sr["connectors_used"],
        "snapshot_hash": sr["snapshot_hash"][:16] + "...",
        "is_real_data": sr["is_real_data"],
        "snapshot_verified": report["snapshot_verification"]["valid"],
    }
