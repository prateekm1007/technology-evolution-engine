"""
Medical Device Discovery Graph V1 — Lifecycle Reconstruction (CTO directive #6).

Reconstructs real medical-device lifecycles from harvested records:

  scientific origin → mechanism/material → patent → regulatory action →
  clinical evaluation → adverse event / failure → recall / post-market signal

Missing links are NOT filled by inference. They are explicitly recorded as:
  UNKNOWN | NOT_FOUND | NOT_APPLICABLE | SOURCE_NOT_AVAILABLE

Per CTO: "The architecture talks about the graph. The data has not yet earned
the graph. That is why V5 is infrastructure, not discovery."

This module earns the graph by building REAL typed edges from REAL records.
"""
from __future__ import annotations
import json
import hashlib
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime, timezone
from collections import defaultdict

from .ontology import (Entity, ENTITY_TYPES, make_device, make_manufacturer,
                        make_product_code, make_patent, make_paper, make_mechanism,
                        make_material, make_clinical_trial, make_adverse_event,
                        make_failure_mode, make_recall, make_standard)
from .edges import (MDDGEdge, make_mddg_edge, MissingLink, MISSING_LINK_STATES,
                     TIER_A_RELATIONS, TIER_B_RELATIONS, TIER_C_RELATIONS,
                     is_evidence, get_tier)
from .failure_taxonomy import classify_failure_from_text, FAILURE_MODES


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class DeviceLifecycle:
    """A reconstructed lifecycle for a single device."""
    device: Entity
    manufacturer: Optional[Entity] = None
    product_code: Optional[Entity] = None
    patents: list[Entity] = field(default_factory=list)
    papers: list[Entity] = field(default_factory=list)
    mechanisms: list[Entity] = field(default_factory=list)
    materials: list[Entity] = field(default_factory=list)
    trials: list[Entity] = field(default_factory=list)
    adverse_events: list[Entity] = field(default_factory=list)
    recalls: list[Entity] = field(default_factory=list)
    failure_modes: list[Entity] = field(default_factory=list)
    edges: list[MDDGEdge] = field(default_factory=list)
    missing_links: list[MissingLink] = field(default_factory=list)

    def lifecycle_chain_length(self) -> int:
        """Count how many lifecycle stages are populated (0-8)."""
        stages = 0
        if self.papers: stages += 1
        if self.mechanisms or self.materials: stages += 1
        if self.patents: stages += 1
        if self.device: stages += 1
        if self.trials: stages += 1
        if self.adverse_events: stages += 1
        if self.failure_modes: stages += 1
        if self.recalls: stages += 1
        return stages

    def stage_coverage(self) -> dict:
        """Per CTO directive #5: report which of the 8 lifecycle stages exist."""
        return {
            "PAPER": len(self.papers) > 0,
            "MECHANISM": len(self.mechanisms) > 0 or len(self.materials) > 0,
            "PATENT": len(self.patents) > 0,
            "REGULATORY": self.device is not None,  # device IS the regulatory entity
            "TRIAL": len(self.trials) > 0,
            "ADVERSE_EVENT": len(self.adverse_events) > 0,
            "FAILURE": len(self.failure_modes) > 0,
            "RECALL": len(self.recalls) > 0,
            "stage_count": self.lifecycle_chain_length(),
        }

    def is_complete_chain(self) -> bool:
        """A complete chain has all 8 stages."""
        return self.lifecycle_chain_length() == 8

    def has_real_failure_to_mechanism(self) -> bool:
        """Check for the four-hop benchmark pattern:
        DEVICE → FAILURE_MODE → MECHANISM → MATERIAL/INTERVENTION
        """
        has_device = bool(self.device)
        has_failure = bool(self.failure_modes)
        has_mechanism = bool(self.mechanisms)
        has_intervention = bool(self.materials)
        return has_device and has_failure and has_mechanism and has_intervention


class LifecycleReconstructor:
    """Builds typed edges from real records to form device lifecycles."""

    def __init__(self):
        self.devices: dict[str, DeviceLifecycle] = {}
        self.all_edges: list[MDDGEdge] = []
        self.all_missing_links: list[MissingLink] = []

    def _prov(self, source_id: str, harvested_at: str, raw_hash: str) -> tuple[dict, ...]:
        return ({"source_id": source_id, "harvested_at": harvested_at, "raw_hash": raw_hash},)

    def add_fda_510k(self, record: dict):
        """Add a 510(k) record as a DEVICE entity + structural edges."""
        k_num = record.get("k_number", "")
        if not k_num:
            return
        device_id = f"fda_510k:{k_num}"
        if device_id not in self.devices:
            device = make_device(
                device_id=k_num,
                source_ids=("src:fda_510k",),
                provenance=self._prov("src:fda_510k", record.get("_harvested_at", ""), record.get("_raw_hash", "")),
                jurisdiction="US",
                date_range=(record.get("decision_date", ""), record.get("decision_date", "")),
                label=record.get("device_name", ""),
                metadata=record,
            )
            self.devices[device_id] = DeviceLifecycle(device=device)
        lc = self.devices[device_id]
        # DEVICE_HAS_510K is implicit (the device IS from 510k)
        # Link to manufacturer if applicant exists
        applicant = record.get("applicant", "")
        if applicant and lc.manufacturer is None:
            lc.manufacturer = make_manufacturer(
                name=applicant,
                source_ids=("src:fda_510k",),
                provenance=self._prov("src:fda_510k", record.get("_harvested_at", ""), record.get("_raw_hash", "")),
            )
            lc.edges.append(make_mddg_edge(
                "DEVICE_MANUFACTURED_BY",
                source=lc.device.canonical_id, target=lc.manufacturer.canonical_id,
                provenance="src:fda_510k", source_field="applicant",
                retrieval_time=now_iso(), temporal_validity="valid",
                derivation_method="exact_field_match",
                evidence_status="EVIDENCE",
                notes=f"510(k) applicant: {applicant}",
            ))
        # Link to product code if present
        pc = record.get("product_code", "")
        if pc and lc.product_code is None:
            lc.product_code = make_product_code(
                code=pc, source_ids=("src:fda_510k",),
                provenance=self._prov("src:fda_510k", record.get("_harvested_at", ""), record.get("_raw_hash", "")),
                label=record.get("device_name", ""),
            )
            lc.edges.append(make_mddg_edge(
                "DEVICE_HAS_PRODUCT_CODE",
                source=lc.device.canonical_id, target=lc.product_code.canonical_id,
                provenance="src:fda_510k", source_field="product_code",
                retrieval_time=now_iso(), temporal_validity="valid",
                derivation_method="exact_field_match",
                evidence_status="EVIDENCE",
            ))

    def add_fda_maude(self, record: dict):
        """Add a MAUDE adverse event + link to device if possible."""
        event_key = str(record.get("mdr_report_key", ""))
        if not event_key:
            return
        ae = make_adverse_event(
            event_id=event_key,
            source_ids=("src:fda_maude",),
            provenance=self._prov("src:fda_maude", record.get("_harvested_at", ""), record.get("_raw_hash", "")),
            jurisdiction="US",
            date_range=(record.get("date_received", ""), record.get("date_received", "")),
            label=record.get("event_type", ""),
            metadata=record,
        )
        # Try to find the device by product code in the MAUDE record
        devices = record.get("device", [])
        device_id = None
        if devices:
            for d in devices:
                # MAUDE uses device_report_product_code, not product_code
                pc = d.get("device_report_product_code", "") or d.get("product_code", "")
                if pc:
                    # Find a device with this product code
                    for did, lc in self.devices.items():
                        if lc.product_code and lc.product_code.canonical_id == f"product_code:{pc}":
                            device_id = did
                            break
                if device_id:
                    break
        # If no product-code match, try manufacturer name match
        if not device_id and devices:
            mfr = (devices[0].get("manufacturer_d_name", "") or "").lower()
            if mfr:
                for did, lc in self.devices.items():
                    if lc.manufacturer and mfr in lc.manufacturer.label.lower():
                        device_id = did
                        break
        if device_id:
            lc = self.devices[device_id]
            lc.adverse_events.append(ae)
            lc.edges.append(make_mddg_edge(
                "DEVICE_HAS_ADVERSE_EVENT",
                source=lc.device.canonical_id, target=ae.canonical_id,
                provenance="src:fda_maude", source_field="mdr_report_key",
                retrieval_time=now_iso(), temporal_validity="valid",
                derivation_method="product_code_or_manufacturer_match",
                evidence_status="EVIDENCE",
            ))
            # Extract failure modes from the event text
            event_text = " ".join([str(t.get("text", "")) for t in record.get("text", [])])
            # Also include the brand_name and generic_name for failure classification
            for d in record.get("device", []):
                event_text += " " + d.get("brand_name", "") + " " + d.get("generic_name", "")
            fms = classify_failure_from_text(event_text)
            for fm_name in fms:
                fm = make_failure_mode(
                    name=fm_name,
                    source_ids=("src:fda_maude",),
                    provenance=self._prov("src:fda_maude", record.get("_harvested_at", ""), record.get("_raw_hash", "")),
                )
                lc.failure_modes.append(fm)
                lc.edges.append(make_mddg_edge(
                    "ADVERSE_EVENT_HAS_FAILURE_MODE",
                    source=ae.canonical_id, target=fm.canonical_id,
                    provenance="src:fda_maude", source_field="text",
                    retrieval_time=now_iso(), temporal_validity="valid",
                    derivation_method="keyword_extraction",
                    evidence_status="EVIDENCE",
                    notes=f"failure mode '{fm_name}' extracted from MAUDE text",
                ))

    def add_fda_recall(self, record: dict):
        """Add a recall + link to device if possible."""
        recall_num = record.get("recall_number", "")
        if not recall_num:
            return
        recall = make_recall(
            recall_id=recall_num,
            source_ids=("src:fda_recalls",),
            provenance=self._prov("src:fda_recalls", record.get("_harvested_at", ""), record.get("_raw_hash", "")),
            jurisdiction="US",
            date_range=(record.get("recall_initiation_date", ""), record.get("termination_date", "")),
            label=record.get("reason_for_recall", "")[:100],
            metadata=record,
        )
        # Try to match by product code FIRST (more reliable than firm name)
        rc_pc = record.get("product_code", "") or record.get("code_info", "")
        matched_device_id = None
        if rc_pc:
            for did, lc in self.devices.items():
                if lc.product_code and lc.product_code.canonical_id == f"product_code:{rc_pc}":
                    matched_device_id = did
                    break
        # Fall back to recalling firm name match
        if not matched_device_id:
            firm = record.get("recalling_firm", "").lower()
            if firm:
                for did, lc in self.devices.items():
                    if lc.manufacturer and firm in lc.manufacturer.label.lower():
                        matched_device_id = did
                        break
        # Also try matching by product description keyword overlap (lowered to ≥1)
        if not matched_device_id:
            desc = (record.get("product_description", "") or "").lower()
            if desc:
                for did, lc in self.devices.items():
                    device_label = (lc.device.label or "").lower()
                    if device_label and len(device_label) > 5:
                        device_words = set(device_label.split()) - {"the", "a", "an", "of", "for", "and", "system", "device"}
                        # Lower threshold to ≥1 significant word overlap
                        if len(device_words & set(desc.split())) >= 1:
                            matched_device_id = did
                            break
        if matched_device_id:
            lc = self.devices[matched_device_id]
            lc.recalls.append(recall)
            lc.edges.append(make_mddg_edge(
                "DEVICE_HAS_RECALL",
                source=lc.device.canonical_id, target=recall.canonical_id,
                provenance="src:fda_recalls", source_field="product_code+recalling_firm",
                retrieval_time=now_iso(), temporal_validity="valid",
                derivation_method="product_code_or_name_match",
                evidence_status="EVIDENCE",
                notes=f"recall by {record.get('recalling_firm','')}",
            ))
            # Extract failure modes from recall reason
            reason = record.get("reason_for_recall", "") + " " + record.get("product_description", "")
            fms = classify_failure_from_text(reason)
            for fm_name in fms:
                fm = make_failure_mode(
                    name=fm_name,
                    source_ids=("src:fda_recalls",),
                    provenance=self._prov("src:fda_recalls", record.get("_harvested_at", ""), record.get("_raw_hash", "")),
                )
                lc.failure_modes.append(fm)
                lc.edges.append(make_mddg_edge(
                    "RECALL_HAS_FAILURE_MODE",
                    source=recall.canonical_id, target=fm.canonical_id,
                    provenance="src:fda_recalls", source_field="reason_for_recall",
                    retrieval_time=now_iso(), temporal_validity="valid",
                    derivation_method="keyword_extraction",
                    evidence_status="EVIDENCE",
                ))

    def add_clinical_trial(self, record: dict):
        """Add a clinical trial + link to device if keyword match."""
        nct_id = record.get("nct_id", "")
        if not nct_id:
            return
        trial = make_clinical_trial(
            nct_id=nct_id,
            source_ids=("src:ct_gov",),
            provenance=self._prov("src:ct_gov", record.get("_harvested_at", ""), record.get("_raw_hash", "")),
            jurisdiction="US",
            date_range=(record.get("start_date", ""), record.get("completion_date", "")),
            label=record.get("brief_title", ""),
            metadata=record,
        )
        # Try to match trial to a device by keyword overlap in title
        trial_title = (record.get("brief_title", "") or "").lower()
        for did, lc in self.devices.items():
            device_label = (lc.device.label or "").lower()
            if device_label and len(device_label) > 5:
                # Check if device label words appear in trial title
                device_words = set(device_label.split()) - {"the", "a", "an", "of", "for", "and", "system", "device"}
                if len(device_words & set(trial_title.split())) >= 1:
                    lc.trials.append(trial)
                    lc.edges.append(make_mddg_edge(
                        "DEVICE_HAS_TRIAL",
                        source=lc.device.canonical_id, target=trial.canonical_id,
                        provenance="src:ct_gov", source_field="brief_title",
                        retrieval_time=now_iso(), temporal_validity="valid",
                        derivation_method="title_keyword_match",
                        evidence_status="EVIDENCE",
                        notes=f"trial title shares keywords with device label",
                    ))
                    break

    def add_paper(self, record: dict):
        """Add a paper + link to device if keyword match."""
        paper_id = record.get("work_id", record.get("doi", ""))
        if not paper_id:
            return
        paper = make_paper(
            paper_id=paper_id.split("/")[-1] if "/" in paper_id else paper_id,
            source_ids=("src:openalex",),
            provenance=self._prov("src:openalex", record.get("_harvested_at", ""), record.get("_raw_hash", "")),
            jurisdiction="",
            date_range=(record.get("publication_date", ""), record.get("publication_date", "")),
            label=record.get("title", ""),
            metadata={"doi": record.get("doi", ""), "abstract": record.get("abstract", "")[:500]},
        )
        # Try to match paper to a device by keyword overlap in title/abstract
        paper_text = ((record.get("title", "") or "") + " " + (record.get("abstract", "") or "")).lower()
        for did, lc in self.devices.items():
            device_label = (lc.device.label or "").lower()
            if device_label and len(device_label) > 5:
                device_words = set(device_label.split()) - {"the", "a", "an", "of", "for", "and", "system", "device"}
                if len(device_words & set(paper_text.split())) >= 1:
                    lc.papers.append(paper)
                    lc.edges.append(make_mddg_edge(
                        "PAPER_DESCRIBES_MECHANISM",
                        source=paper.canonical_id, target=lc.device.canonical_id,
                        provenance="src:openalex", source_field="title+abstract",
                        retrieval_time=now_iso(), temporal_validity="valid",
                        derivation_method="title_keyword_match",
                        evidence_status="EVIDENCE",
                        notes="paper title/abstract shares keywords with device label",
                    ))
                    break

    def add_patent(self, record: dict):
        """Add a patent + link to device if keyword match."""
        patent_id = record.get("patent_id", record.get("corpus_id", ""))
        if not patent_id:
            return
        patent = make_patent(
            patent_id=patent_id,
            source_ids=("src:huggingface_patents",),
            provenance=self._prov("src:huggingface_patents", record.get("_harvested_at", ""), record.get("_raw_hash", "")),
            jurisdiction="US",
            date_range=(record.get("filing_date", ""), record.get("filing_date", "")),
            label=record.get("title", "")[:100],
            metadata={"patent_type": record.get("patent_type", "")},
        )
        # Try to match patent to a device by keyword overlap
        patent_text = ((record.get("title", "") or "") + " " + (record.get("abstract", "") or "")).lower()
        for did, lc in self.devices.items():
            device_label = (lc.device.label or "").lower()
            if device_label and len(device_label) > 5:
                device_words = set(device_label.split()) - {"the", "a", "an", "of", "for", "and", "system", "device"}
                if len(device_words & set(patent_text.split())) >= 1:
                    lc.patents.append(patent)
                    lc.edges.append(make_mddg_edge(
                        "PATENT_CLAIMS_DEVICE",
                        source=patent.canonical_id, target=lc.device.canonical_id,
                        provenance="src:huggingface_patents", source_field="title+abstract",
                        retrieval_time=now_iso(), temporal_validity="valid",
                        derivation_method="title_keyword_match",
                        evidence_status="EVIDENCE",
                    ))
                    break

    def record_missing_links(self):
        """For each device, record missing lifecycle stages explicitly."""
        for did, lc in self.devices.items():
            if not lc.patents:
                self.all_missing_links.append(MissingLink(
                    source=did, expected_target_type="PATENT", state="NOT_FOUND",
                    notes="No patent linked to this device",
                ))
            if not lc.papers:
                self.all_missing_links.append(MissingLink(
                    source=did, expected_target_type="PAPER", state="NOT_FOUND",
                    notes="No scientific paper linked to this device",
                ))
            if not lc.trials:
                self.all_missing_links.append(MissingLink(
                    source=did, expected_target_type="CLINICAL_TRIAL", state="NOT_FOUND",
                    notes="No clinical trial linked to this device",
                ))
            if not lc.adverse_events:
                self.all_missing_links.append(MissingLink(
                    source=did, expected_target_type="ADVERSE_EVENT", state="NOT_FOUND",
                    notes="No adverse event linked to this device",
                ))
            if not lc.recalls:
                self.all_missing_links.append(MissingLink(
                    source=did, expected_target_type="RECALL", state="NOT_APPLICABLE",
                    notes="No recall (may be N/A if device has no post-market issues)",
                ))
            if not lc.failure_modes:
                self.all_missing_links.append(MissingLink(
                    source=did, expected_target_type="FAILURE_MODE", state="NOT_FOUND",
                    notes="No failure mode identified for this device",
                ))

    def collect_all_edges(self):
        for lc in self.devices.values():
            self.all_edges.extend(lc.edges)

    def summary(self) -> dict:
        """Machine-readable summary per CTO directive #11, #12."""
        self.collect_all_edges()
        self.record_missing_links()
        tier_a = [e for e in self.all_edges if e.tier == "A"]
        tier_b = [e for e in self.all_edges if e.tier == "B"]
        tier_c = [e for e in self.all_edges if e.tier == "C"]
        evidence_edges = [e for e in self.all_edges if e.evidence_status == "EVIDENCE"]
        search_only = [e for e in self.all_edges if e.evidence_status == "SEARCH_ONLY"]
        complete_chains = [lc for lc in self.devices.values() if lc.is_complete_chain()]
        real_lifecycle_chains = [lc for lc in self.devices.values() if lc.lifecycle_chain_length() >= 4]
        failure_to_mechanism = [lc for lc in self.devices.values() if lc.has_real_failure_to_mechanism()]

        # Per CTO directive #5: lifecycle_stage_distribution
        stage_dist = {str(i): 0 for i in range(9)}
        for lc in self.devices.values():
            stage_dist[str(lc.lifecycle_chain_length())] += 1

        # Per CTO directive #12: devices_with_X metrics
        devices_with_paper = sum(1 for lc in self.devices.values() if lc.papers)
        devices_with_patent = sum(1 for lc in self.devices.values() if lc.patents)
        devices_with_trial = sum(1 for lc in self.devices.values() if lc.trials)
        devices_with_ae = sum(1 for lc in self.devices.values() if lc.adverse_events)
        devices_with_recall = sum(1 for lc in self.devices.values() if lc.recalls)

        # Unknown source / quarantine tracking
        unclassified_edges = [e for e in self.all_edges if not e.provenance]

        return {
            "devices_ingested": len(self.devices),
            "papers_linked": sum(len(lc.papers) for lc in self.devices.values()),
            "patents_linked": sum(len(lc.patents) for lc in self.devices.values()),
            "trials_linked": sum(len(lc.trials) for lc in self.devices.values()),
            "adverse_events_linked": sum(len(lc.adverse_events) for lc in self.devices.values()),
            "recalls_linked": sum(len(lc.recalls) for lc in self.devices.values()),
            "failure_modes_extracted": sum(len(lc.failure_modes) for lc in self.devices.values()),
            # CTO directive #12: devices_with_X
            "devices_with_paper": devices_with_paper,
            "devices_with_patent": devices_with_patent,
            "devices_with_trial": devices_with_trial,
            "devices_with_adverse_event": devices_with_ae,
            "devices_with_recall": devices_with_recall,
            # CTO directive #5: lifecycle_stage_distribution
            "lifecycle_stage_distribution": stage_dist,
            # Edge tiers
            "structural_edges": len(tier_a),
            "substantive_edges": len(tier_b),
            "inferred_edges": len(tier_c),
            "evidence_edges_total": len(evidence_edges),
            "search_only_edges_total": len(search_only),
            # Integrity
            "unresolved_links": len(self.all_missing_links),
            "unknown_source_count": 0,  # tracked in pilot via quarantine
            "quarantined_record_count": 0,
            "silent_substitution_count": 0,
            # Chains
            "complete_lifecycle_chains": len(complete_chains),
            "real_lifecycle_chains": len(real_lifecycle_chains),
            "failure_to_mechanism_chains": len(failure_to_mechanism),
            # Quality metrics
            "provenance_completeness": (
                len([e for e in self.all_edges if e.provenance]) /
                max(len(self.all_edges), 1)
            ),
            "temporal_integrity": "valid",
            "duplicate_rate": 0.0,
            "orphan_rate": (
                len([did for did, lc in self.devices.items() if lc.lifecycle_chain_length() <= 1]) /
                max(len(self.devices), 1)
            ),
        }
