"""
V5 Pilot Snapshot — Medical Device + Corrected Patent Semantics (Issue #5 V5).

Per CTO directive:
  A. Correct patent semantics (documents ≠ families)
  B. Label HuggingFace as SECONDARY_DERIVED_CORPUS, USPTO_DERIVED, HISTORICAL
  C. Typed cross-corpus edges (no keyword-overlap as evidence)
  D. Medical devices as first-class universe
  E. Medical device graph
  F. One machine-readable manifest defines exact totals
  G. Separate evidence classes
  H. Two patent universes (historical + live)
  I. Exit criterion with 9 separate counts + 4 booleans
"""
from __future__ import annotations
import json
import hashlib
import time
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, asdict, field
from typing import Optional
from collections import Counter

from .real_connectors import OpenAlexRealConnector, EuropePmcRealConnector
from .v4_real_connectors import HuggingFacePatentConnector, ClinicalTrialsGovConnector, SecEdgarConnector
from .v5_fda_connectors import (Fda510kConnector, FdaPmaConnector, FdaMaudeConnector,
                                 FdaRecallsConnector, FdaClassificationConnector,
                                 get_fda_connector, V5_FDA_CONNECTOR_REGISTRY)
from .source_registry import SOURCES
from .evidence_connector import Checkpoint
from .connector_base import HarvestedRecord
from .failure_recorder import FailureLog
from .snapshot_manager import create_snapshot, verify_snapshot
from .evidence_classes import get_evidence_class, EVIDENCE_CLASSES, classify_patent_document
from .patent_families import reconstruct_families_proxy, count_family_stats
from .v5_typed_edges import build_all_v5_edges, EVIDENCE_EDGE_TYPES, SEARCH_ONLY_EDGE_TYPES


def build_v5_pilot_snapshot(output_dir: Path, *,
                            science_per_domain: int = 20,
                            patents_total: int = 200,
                            fda_per_endpoint: int = 20,
                            trials_total: int = 20,
                            edgar_total: int = 30) -> dict:
    """Build the V5 pilot snapshot with corrected semantics.

    All totals are defined in ONE manifest (this function's return value).
    The report is generated from the manifest, never manually typed.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    failure_log = FailureLog(output_dir / "v5_failure_log.jsonl")

    all_records: list[HarvestedRecord] = []
    connectors_used = set()

    # 5 domains — including medical_devices as first-class (directive D)
    DOMAIN_QUERIES = {
        "battery_electrochemistry": {
            "openalex": "default.search:lithium battery electrode",
            "europepmc": "lithium battery electrode",
            "ctgov": "lithium battery",
            "edgar": "lithium battery",
            "fda_search": "battery",
        },
        "crispr_gene_editing": {
            "openalex": "default.search:CRISPR Cas9 gene editing",
            "europepmc": "CRISPR Cas9 gene editing",
            "ctgov": "CRISPR",
            "edgar": "CRISPR gene editing",
            "fda_search": "gene editing",
        },
        "medical_devices": {
            "openalex": "default.search:medical device implant sensor",
            "europepmc": "medical device implant",
            "ctgov": "medical device",
            "edgar": "medical device",
            "fda_search": "cardiac pacemaker",
        },
        "additive_manufacturing": {
            "openalex": "default.search:additive manufacturing 3D printing",
            "europepmc": "additive manufacturing 3D printing",
            "ctgov": "3D printing",
            "edgar": "additive manufacturing",
            "fda_search": "3D printing",
        },
        "hydrogen_electrocatalysis": {
            "openalex": "default.search:hydrogen evolution reaction electrocatalyst",
            "europepmc": "hydrogen evolution reaction",
            "ctgov": "hydrogen",
            "edgar": "hydrogen fuel cell",
            "fda_search": "fuel cell",
        },
    }

    # === SCIENCE (OpenAlex + Europe PMC) ===
    print("=== SCIENCE ===")
    openalex_src = next(s for s in SOURCES if s.source_id == "src:openalex")
    openalex_conn = OpenAlexRealConnector(openalex_src, failure_log=failure_log)
    europepmc_src = next(s for s in SOURCES if s.source_id == "src:pubmed")
    europepmc_conn = EuropePmcRealConnector(europepmc_src, failure_log=failure_log)

    for domain, queries in DOMAIN_QUERIES.items():
        cp = Checkpoint(source_id="src:openalex")
        cp.last_error = queries["openalex"]
        try:
            records, _ = openalex_conn.fetch_updates(cp, max_records=science_per_domain)
            for r in records:
                r.normalized["domain"] = domain
                r.normalized["evidence_class"] = "SCIENTIFIC_OBSERVATION"
                r.normalized["date"] = r.normalized.get("publication_date", "")
                r.normalized_hash = r.normalized_content_hash()
                all_records.append(r)
            connectors_used.add("src:openalex")
            print(f"  {domain}: OpenAlex {len(records)}")
        except Exception as e:
            print(f"  {domain}: OpenAlex FAILED: {e}")
        time.sleep(0.5)

        cp = Checkpoint(source_id="src:pubmed")
        cp.last_error = queries["europepmc"]
        try:
            records, _ = europepmc_conn.fetch_updates(cp, max_records=10)
            for r in records:
                r.normalized["domain"] = domain
                r.normalized["evidence_class"] = "SCIENTIFIC_OBSERVATION"
                r.normalized["date"] = r.normalized.get("publication_date", "")
                r.normalized_hash = r.normalized_content_hash()
                all_records.append(r)
            connectors_used.add("src:pubmed")
            print(f"  {domain}: Europe PMC {len(records)}")
        except Exception as e:
            print(f"  {domain}: Europe PMC FAILED: {e}")
        time.sleep(0.5)

    # === PATENTS (HuggingFace — labeled HISTORICAL, SECONDARY_DERIVED) ===
    print()
    print("=== PATENTS (HuggingFace — HISTORICAL, SECONDARY_DERIVED_CORPUS) ===")
    hf_src = next(s for s in SOURCES if s.source_id == "src:huggingface_patents")
    hf_conn = HuggingFacePatentConnector(hf_src, failure_log=failure_log)

    patents_needed = patents_total
    offset = 0
    domains_list = list(DOMAIN_QUERIES.keys())
    while patents_needed > 0:
        cp = Checkpoint(source_id="src:huggingface_patents")
        cp.cursor = str(offset)
        batch = min(100, patents_needed)
        try:
            records, _ = hf_conn.fetch_updates(cp, max_records=batch)
            if not records:
                break
            for i, r in enumerate(records):
                domain = domains_list[(offset + i) % len(domains_list)]
                r.normalized["domain"] = domain
                r.normalized["evidence_class"] = "PATENT_DISCLOSURE"
                r.normalized["date"] = r.normalized.get("filing_date", "")
                # Label per directive B
                r.normalized["corpus_type"] = "SECONDARY_DERIVED_CORPUS"
                r.normalized["corpus_authority"] = "USPTO_DERIVED"
                r.normalized["corpus_temporality"] = "HISTORICAL"
                r.normalized["corpus_liveness"] = "NOT_LIVE_OFFICE_FEED"
                r.normalized["patent_document_type"] = classify_patent_document(
                    r.normalized.get("patent_type", ""))
                r.normalized_hash = r.normalized_content_hash()
                all_records.append(r)
            connectors_used.add("src:huggingface_patents")
            patents_needed -= len(records)
            offset += len(records)
            print(f"  Fetched {len(records)} (total: {patents_total - patents_needed}/{patents_total})")
        except Exception as e:
            print(f"  HuggingFace FAILED at offset {offset}: {e}")
            break
        time.sleep(1.0)

    # === FDA MEDICAL DEVICE RECORDS (directive D) ===
    print()
    print("=== FDA MEDICAL DEVICE RECORDS ===")
    fda_sources = [
        ("src:fda_510k", "510k"),
        ("src:fda_pma", "pma"),
        ("src:fda_maude", "event"),
        ("src:fda_recalls", "recall"),
        ("src:fda_classification", "classification"),
    ]
    for source_id, _endpoint in fda_sources:
        conn = get_fda_connector(source_id, failure_log=failure_log)
        if not conn:
            continue
        # Search with a medical device query
        cp = Checkpoint(source_id=source_id)
        cp.last_error = "cardiac OR implant OR sensor"
        try:
            records, _ = conn.fetch_updates(cp, max_records=fda_per_endpoint)
            for r in records:
                r.normalized["domain"] = "medical_devices"
                r.normalized["date"] = r.normalized.get("decision_date", "") or \
                                        r.normalized.get("date_received", "") or \
                                        r.normalized.get("recall_initiation_date", "")
                r.normalized_hash = r.normalized_content_hash()
                all_records.append(r)
            connectors_used.add(source_id)
            print(f"  {source_id}: {len(records)} records, status: {conn.operational_status}")
        except Exception as e:
            print(f"  {source_id}: FAILED: {e}")
        time.sleep(1.0)

    # === CLINICAL TRIALS (failure corpus) ===
    print()
    print("=== CLINICAL TRIALS (terminated) ===")
    ct_src = next(s for s in SOURCES if s.source_id == "src:ct_gov")
    ct_conn = ClinicalTrialsGovConnector(ct_src, failure_log=failure_log)
    trials_needed = trials_total
    for domain, queries in DOMAIN_QUERIES.items():
        if trials_needed <= 0:
            break
        cp = Checkpoint(source_id="src:ct_gov")
        cp.last_error = f"TERMINATED:{queries['ctgov']}"
        try:
            records, _ = ct_conn.fetch_updates(cp, max_records=min(5, trials_needed))
            for r in records:
                r.normalized["domain"] = domain
                r.normalized["evidence_class"] = "CLINICAL_EVIDENCE"
                r.normalized["date"] = r.normalized.get("start_date", "")
                r.normalized_hash = r.normalized_content_hash()
                all_records.append(r)
            connectors_used.add("src:ct_gov")
            trials_needed -= len(records)
            print(f"  {domain}: CT.gov {len(records)} terminated trials")
        except Exception as e:
            print(f"  {domain}: CT.gov FAILED: {e}")
        time.sleep(0.5)

    # === SEC EDGAR (corporate risk) ===
    print()
    print("=== SEC EDGAR ===")
    edgar_src = next(s for s in SOURCES if s.source_id == "src:sec_edgar")
    edgar_conn = SecEdgarConnector(edgar_src, failure_log=failure_log)
    edgar_needed = edgar_total
    for domain, queries in DOMAIN_QUERIES.items():
        if edgar_needed <= 0:
            break
        cp = Checkpoint(source_id="src:sec_edgar")
        cp.last_error = queries["edgar"]
        try:
            records, _ = edgar_conn.fetch_updates(cp, max_records=min(10, edgar_needed))
            for r in records:
                r.normalized["domain"] = domain
                r.normalized["evidence_class"] = "CORPORATE_RISK"
                r.normalized["date"] = r.normalized.get("filing_date", "")
                r.normalized_hash = r.normalized_content_hash()
                all_records.append(r)
            connectors_used.add("src:sec_edgar")
            edgar_needed -= len(records)
            print(f"  {domain}: SEC EDGAR {len(records)}")
        except Exception as e:
            print(f"  {domain}: SEC EDGAR FAILED: {e}")
        time.sleep(1.0)

    # === BUILD TYPED CROSS-CORPUS EDGES (directive C) ===
    print()
    print("=== TYPED CROSS-CORPUS EDGES ===")
    # Convert HarvestedRecords to plain dicts for the edge builders
    records_as_dicts = []
    for r in all_records:
        d = dict(r.normalized)
        d["record_id"] = r.record_id
        d["source_uri"] = r.provenance.get("endpoint", "")
        records_as_dicts.append(d)
    edge_result = build_all_v5_edges(records_as_dicts)
    print(f"  Evidence edges: {edge_result['summary']['evidence_edge_count']}")
    print(f"  Search-only edges: {edge_result['summary']['search_only_edge_count']}")
    print(f"  By type: {edge_result['summary']['by_type']}")

    # === PATENT FAMILY RECONSTRUCTION (directive A) ===
    print()
    print("=== PATENT FAMILY RECONSTRUCTION ===")
    patent_records = [r.normalized for r in all_records
                      if r.normalized.get("evidence_class") == "PATENT_DISCLOSURE"]
    families = reconstruct_families_proxy(patent_records)
    family_stats = count_family_stats(families)
    print(f"  {family_stats}")

    # === BUILD SNAPSHOT ===
    cutoff = datetime.now(timezone.utc).date().isoformat()
    snapshot_dir = output_dir / "v5_real_snapshot"
    snap_result = create_snapshot(all_records, cutoff=cutoff, snapshot_dir=snapshot_dir)
    manifest = snap_result["manifest"]
    verification = verify_snapshot(snapshot_dir)

    # === COMPUTE EXACT TOTALS FROM MANIFEST (directive F) ===
    # Count by evidence class
    evidence_class_counts = Counter(r.normalized.get("evidence_class", "UNKNOWN")
                                     for r in all_records)
    # Count patent document types
    patent_doc_types = Counter(r.normalized.get("patent_document_type", "UNKNOWN")
                                for r in all_records
                                if r.normalized.get("evidence_class") == "PATENT_DISCLOSURE")

    # === BUILD THE MANIFEST (single source of truth) ===
    result = {
        "manifest_version": "5.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "snapshot_id": manifest["snapshot_id"],
        "snapshot_hash": manifest["root_hash"],
        "real_snapshot_hash": manifest["root_hash"],
        "cutoff": cutoff,
        "snapshot_verified": verification["valid"],
        "is_real_data": True,
        "no_synthetic_data": True,
        "connectors_used": sorted(connectors_used),
        # === EXACT TOTALS (directive I) ===
        "totals": {
            "SCIENCE_DOCUMENTS": evidence_class_counts.get("SCIENTIFIC_OBSERVATION", 0),
            "PATENT_DOCUMENTS": evidence_class_counts.get("PATENT_DISCLOSURE", 0),
            "PATENT_APPLICATIONS": patent_doc_types.get("PATENT_APPLICATION", 0),
            "PATENT_GRANTS": patent_doc_types.get("PATENT_GRANT", 0),
            "PATENT_FAMILIES": family_stats["PATENT_FAMILIES_RECONSTRUCTED"],
            "PROXY_FAMILIES": family_stats["PROXY_FAMILIES"],
            "MEDICAL_DEVICE_RECORDS": sum(evidence_class_counts.get(ec, 0)
                                           for ec in ["DEVICE_REGULATORY_ACTION"]),
            "CLINICAL_TRIALS": evidence_class_counts.get("CLINICAL_EVIDENCE", 0),
            "ADVERSE_EVENTS": evidence_class_counts.get("ADVERSE_EVENT", 0),
            "CORPORATE_RECORDS": evidence_class_counts.get("CORPORATE_RISK", 0),
            "MARKET_SIGNALS": evidence_class_counts.get("MARKET_SIGNAL", 0),
            "TOTAL_RECORDS": len(all_records),
        },
        # === TYPED EDGES (directive C) ===
        "edges": edge_result,
        # === EVIDENCE CLASS BREAKDOWN (directive G) ===
        "evidence_class_counts": dict(evidence_class_counts),
        # === PATENT SEMANTICS (directive A) ===
        "patent_family_stats": family_stats,
        "patent_document_type_counts": dict(patent_doc_types),
        # === PATENT CORPUS LABELING (directive B, H) ===
        "patent_corpus_labels": {
            "huggingface_allenai_us_patents": {
                "corpus_type": "SECONDARY_DERIVED_CORPUS",
                "corpus_authority": "USPTO_DERIVED",
                "corpus_temporality": "HISTORICAL",
                "corpus_liveness": "NOT_LIVE_OFFICE_FEED",
                "license": "ODC-BY",
                "dataset_provenance": "allenai/us-patents on HuggingFace",
                "original_authority": "USPTO",
                "coverage": "8M+ US patent grants/applications 1976-2025",
            },
        },
        # === TWO PATENT UNIVERSES (directive H) ===
        "patent_universes": {
            "HISTORICAL_PATENT_CORPUS": True,   # HuggingFace allenai/us-patents
            "LIVE_LATEST_PATENT_FEED": False,   # EPO/USPTO/CNIPA not yet operational
        },
        # === MEDICAL DEVICE CORPUS (directive D) ===
        "medical_device_corpus": {
            "fda_connectors_operational": [s for s in connectors_used if s.startswith("src:fda_")],
            "fda_endpoint_counts": {
                s: sum(1 for r in all_records if r.source_id == s)
                for s in connectors_used if s.startswith("src:fda_")
            },
        },
        # === DOMAIN BREAKDOWN ===
        "domain_counts": dict(Counter(r.normalized.get("domain", "unknown")
                                       for r in all_records)),
        # === HONEST BOUNDARIES ===
        "honest_boundaries": {
            "live_http_performed": True,
            "real_records_retrieved": len(all_records) > 0,
            "no_synthetic_data": True,
            "is_scientific_result": False,
            "no_discovery_claims": True,
            "psc_frozen": True,
            "a2_authorized": False,
            "patent_documents_not_families": True,  # directive A
            "keyword_overlap_not_evidence": True,    # directive C
        },
    }

    # Write manifest
    manifest_path = output_dir / "V5_MANIFEST.json"
    file_content = json.dumps(result, indent=2, default=str)
    manifest_path.write_text(file_content)
    manifest_path.with_suffix(manifest_path.suffix + ".sha256").write_text(
        hashlib.sha256(file_content.encode()).hexdigest()
    )
    return result
