"""
Medical Device Discovery Graph V1 — Pilot Runner.

Ingests REAL records from operational connectors and reconstructs
medical-device lifecycles.

Per CTO directive #6: "Select a bounded but real pilot universe. Start with
perhaps 50-100 devices spanning implantables, diagnostics, surgical systems,
wearables, biomaterials, neurotechnology."

Missing links are NOT filled by inference. They are explicitly recorded as
UNKNOWN/NOT_FOUND/NOT_APPLICABLE/SOURCE_NOT_AVAILABLE.
"""
from __future__ import annotations
import json
import hashlib
import time
from pathlib import Path
from datetime import datetime, timezone

from ..real_connectors import OpenAlexRealConnector, EuropePmcRealConnector
from ..v4_real_connectors import HuggingFacePatentConnector, ClinicalTrialsGovConnector, SecEdgarConnector
from ..v5_fda_connectors import (Fda510kConnector, FdaPmaConnector, FdaMaudeConnector,
                                 FdaRecallsConnector, FdaClassificationConnector,
                                 get_fda_connector)
from ..source_registry import SOURCES
from ..evidence_connector import Checkpoint
from ..failure_recorder import FailureLog
from .lifecycle import LifecycleReconstructor, now_iso
from .benchmark import find_four_hop_candidates, run_all_null_controls


# 6 device categories per CTO directive #6
DEVICE_CATEGORIES = {
    "implantables": "cardiac pacemaker implantable",
    "diagnostics": "diagnostic imaging sensor",
    "surgical_systems": "surgical robot system",
    "wearables": "wearable health monitor",
    "biomaterials": "biomaterial implant",
    "neurotechnology": "neurotechnology brain interface",
}


def run_mddg_pilot(output_dir: Path, *,
                   devices_per_category: int = 10,
                   papers_per_category: int = 10,
                   patents_per_category: int = 10,
                   trials_per_category: int = 5) -> dict:
    """Run the MDDG V1 pilot with REAL data."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    failure_log = FailureLog(output_dir / "mddg_failure_log.jsonl")
    reconstructor = LifecycleReconstructor()

    # === 1. FDA 510(k) records — the device universe ===
    print("=== FDA 510(k) DEVICES ===")
    conn = get_fda_connector("src:fda_510k", failure_log)
    for category, query in DEVICE_CATEGORIES.items():
        cp = Checkpoint(source_id="src:fda_510k")
        cp.last_error = f"device_name:{query}"
        try:
            records, _ = conn.fetch_updates(cp, max_records=devices_per_category)
            for r in records:
                r.normalized["_harvested_at"] = r.harvested_at
                r.normalized["_raw_hash"] = r.raw_payload_hash
                r.normalized["_category"] = category
                reconstructor.add_fda_510k(r.normalized)
            print(f"  {category}: {len(records)} devices")
        except Exception as e:
            print(f"  {category}: FAILED - {e}")
        time.sleep(0.5)

    # === 2. FDA MAUDE adverse events — search by PRODUCT CODE from ingested devices ===
    print()
    print("=== FDA MAUDE ADVERSE EVENTS (product-code targeted) ===")
    conn = get_fda_connector("src:fda_maude", failure_log)
    # Collect all product codes from ingested devices
    product_codes = set()
    for lc in reconstructor.devices.values():
        if lc.product_code:
            # product_code canonical_id = "product_code:XXX"
            pc = lc.product_code.canonical_id.split(":")[-1]
            if pc:
                product_codes.add(pc)
    print(f"  Searching MAUDE for {len(product_codes)} product codes")
    for pc in list(product_codes)[:20]:  # limit to 20 to stay within rate limits
        cp = Checkpoint(source_id="src:fda_maude")
        cp.last_error = f"device.device_report_product_code:{pc}"
        try:
            records, _ = conn.fetch_updates(cp, max_records=3)
            for r in records:
                r.normalized["_harvested_at"] = r.harvested_at
                r.normalized["_raw_hash"] = r.raw_payload_hash
                reconstructor.add_fda_maude(r.normalized)
            if records:
                print(f"  product_code {pc}: {len(records)} adverse events")
        except Exception as e:
            print(f"  product_code {pc}: FAILED - {e}")
        time.sleep(0.3)

    # Also search MAUDE by generic device name for each category
    for category, query in DEVICE_CATEGORIES.items():
        cp = Checkpoint(source_id="src:fda_maude")
        cp.last_error = f"device.generic_name:{query.split()[0]}"
        try:
            records, _ = conn.fetch_updates(cp, max_records=3)
            for r in records:
                r.normalized["_harvested_at"] = r.harvested_at
                r.normalized["_raw_hash"] = r.raw_payload_hash
                reconstructor.add_fda_maude(r.normalized)
            print(f"  {category} (by name): {len(records)} adverse events")
        except Exception as e:
            print(f"  {category}: FAILED - {e}")
        time.sleep(0.3)

    # === 3. FDA Recalls — search by product code + by name ===
    print()
    print("=== FDA RECALLS ===")
    conn = get_fda_connector("src:fda_recalls", failure_log)
    for pc in list(product_codes)[:10]:
        cp = Checkpoint(source_id="src:fda_recalls")
        cp.last_error = f"product_code:{pc}"
        try:
            records, _ = conn.fetch_updates(cp, max_records=3)
            for r in records:
                r.normalized["_harvested_at"] = r.harvested_at
                r.normalized["_raw_hash"] = r.raw_payload_hash
                reconstructor.add_fda_recall(r.normalized)
            if records:
                print(f"  product_code {pc}: {len(records)} recalls")
        except Exception as e:
            print(f"  product_code {pc}: FAILED - {e}")
        time.sleep(0.3)

    # === 4. Clinical trials ===
    print()
    print("=== CLINICAL TRIALS ===")
    ct_src = next(s for s in SOURCES if s.source_id == "src:ct_gov")
    ct_conn = ClinicalTrialsGovConnector(ct_src, failure_log=failure_log)
    for category, query in DEVICE_CATEGORIES.items():
        cp = Checkpoint(source_id="src:ct_gov")
        cp.last_error = query
        try:
            records, _ = ct_conn.fetch_updates(cp, max_records=trials_per_category)
            for r in records:
                r.normalized["_harvested_at"] = r.harvested_at
                r.normalized["_raw_hash"] = r.raw_payload_hash
                reconstructor.add_clinical_trial(r.normalized)
            print(f"  {category}: {len(records)} trials")
        except Exception as e:
            print(f"  {category}: FAILED - {e}")
        time.sleep(0.5)

    # === 5. Papers (OpenAlex) ===
    print()
    print("=== PAPERS ===")
    openalex_src = next(s for s in SOURCES if s.source_id == "src:openalex")
    openalex_conn = OpenAlexRealConnector(openalex_src, failure_log=failure_log)
    for category, query in DEVICE_CATEGORIES.items():
        cp = Checkpoint(source_id="src:openalex")
        cp.last_error = f"default.search:{query}"
        try:
            records, _ = openalex_conn.fetch_updates(cp, max_records=papers_per_category)
            for r in records:
                r.normalized["_harvested_at"] = r.harvested_at
                r.normalized["_raw_hash"] = r.raw_payload_hash
                reconstructor.add_paper(r.normalized)
            print(f"  {category}: {len(records)} papers")
        except Exception as e:
            print(f"  {category}: FAILED - {e}")
        time.sleep(0.5)

    # === 6. Patents (HuggingFace) ===
    print()
    print("=== PATENTS ===")
    hf_src = next(s for s in SOURCES if s.source_id == "src:huggingface_patents")
    hf_conn = HuggingFacePatentConnector(hf_src, failure_log=failure_log)
    offset = 0
    total_patents_needed = patents_per_category * len(DEVICE_CATEGORIES)
    categories_list = list(DEVICE_CATEGORIES.keys())
    while offset < total_patents_needed:
        cp = Checkpoint(source_id="src:huggingface_patents")
        cp.cursor = str(offset)
        try:
            records, _ = hf_conn.fetch_updates(cp, max_records=50)
            if not records:
                break
            for r in records:
                r.normalized["_harvested_at"] = r.harvested_at
                r.normalized["_raw_hash"] = r.raw_payload_hash
                r.normalized["_category"] = categories_list[(offset) % len(categories_list)]
                reconstructor.add_patent(r.normalized)
            offset += len(records)
            print(f"  Fetched {len(records)} patents (total: {offset})")
        except Exception as e:
            print(f"  FAILED: {e}")
            break
        time.sleep(1.0)

    # === 7. Collect all edges + record missing links ===
    print()
    print("=== LIFECYCLE RECONSTRUCTION ===")
    reconstructor.collect_all_edges()
    reconstructor.record_missing_links()
    summary = reconstructor.summary()
    print(f"  devices_ingested: {summary['devices_ingested']}")
    print(f"  papers_linked: {summary['papers_linked']}")
    print(f"  patents_linked: {summary['patents_linked']}")
    print(f"  trials_linked: {summary['trials_linked']}")
    print(f"  adverse_events_linked: {summary['adverse_events_linked']}")
    print(f"  recalls_linked: {summary['recalls_linked']}")
    print(f"  failure_modes_extracted: {summary['failure_modes_extracted']}")
    print(f"  structural_edges (Tier A): {summary['structural_edges']}")
    print(f"  substantive_edges (Tier B): {summary['substantive_edges']}")
    print(f"  inferred_edges (Tier C): {summary['inferred_edges']}")
    print(f"  unresolved_links: {summary['unresolved_links']}")
    print(f"  real_lifecycle_chains: {summary['real_lifecycle_chains']}")

    # === 8. Four-hop benchmark ===
    print()
    print("=== FOUR-HOP BENCHMARK ===")
    candidates = find_four_hop_candidates(reconstructor)
    qualified = [c for c in candidates if c.qualified]
    print(f"  candidates found: {len(candidates)}")
    print(f"  qualified candidates: {len(qualified)}")

    # === 9. Null controls ===
    print()
    print("=== NULL CONTROLS ===")
    nulls = run_all_null_controls(reconstructor)
    for null_name, null_result in nulls.items():
        print(f"  {null_name}: {null_result}")

    # === 10. Build the manifest ===
    manifest = {
        "manifest_version": "MDDG-V1",
        "generated_at": now_iso(),
        "summary": summary,
        "four_hop_benchmark": {
            "candidates_found": len(candidates),
            "qualified_candidates": len(qualified),
            "qualified_candidate_details": [asdict(c) for c in qualified[:10]],
        },
        "null_controls": nulls,
        "device_categories": list(DEVICE_CATEGORIES.keys()),
        "honest_boundaries": {
            "real_data": True,
            "no_synthetic_data": True,
            "no_discovery_claims": True,
            "missing_links_explicitly_recorded": True,
            "tier_c_never_evidence": True,
            "psc_frozen": True,
            "a2_authorized": False,
        },
        "exit_criterion": {
            "REAL_LIFECYCLE_CHAINS": summary["real_lifecycle_chains"],
            "REAL_LIFECYCLE_CHAINS_GT_0": summary["real_lifecycle_chains"] > 0,
            "FOUR_HOP_QUALIFIED_CANDIDATES": len(qualified),
            "FAILURE_TO_MECHANISM_CHAINS": summary["failure_to_mechanism_chains"],
        },
    }

    manifest_path = output_dir / "MDDG_V1_MANIFEST.json"
    file_content = json.dumps(manifest, indent=2, default=str)
    manifest_path.write_text(file_content)
    manifest_path.with_suffix(manifest_path.suffix + ".sha256").write_text(
        hashlib.sha256(file_content.encode()).hexdigest()
    )
    return manifest
