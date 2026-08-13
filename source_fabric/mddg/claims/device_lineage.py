"""
MDDG V3 — Device Lineage & Entity Resolution (Fortune 50 directive #6, #7, #8).

#6. Device lineage: DEVICE_VERSION → DEVICE_FAMILY, predecessor/successor.
    Lineage evidence: 510(k) predicate citation, explicit regulatory successor,
    shared UDI-DI base + documented model evolution.
    NOT inferred from same company / similar name / similar product code.

#7. 4-tier entity resolution hierarchy:
    Tier 1: UDI-DI/GUDID, K-number, PMA number, De Novo number (authoritative identity)
    Tier 2: product_code + legal manufacturer (strong crosswalk)
    Tier 3: model/catalog/brand name (candidate identifiers, need corroboration)
    Tier 4: patent assignee, clinical-trial sponsor (association only)

#8. Modern-device forward seeding: start from recent MAUDE/recalls/trials,
    walk backward via FDA predicate chains.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional
from collections import defaultdict
import hashlib
import json


# =====================================================================
# 4-TIER ENTITY RESOLUTION (directive #7)
# =====================================================================

ENTITY_RESOLUTION_TIERS = {
    1: {"name": "AUTHORITATIVE_IDENTITY", "identifiers": ["udi_di", "gudid", "k_number", "pma_number", "denovo_number"]},
    2: {"name": "STRONG_CROSSWALK", "identifiers": ["product_code", "legal_manufacturer", "fei", "duns"]},
    3: {"name": "CANDIDATE_IDENTIFIERS", "identifiers": ["model_number", "catalog_number", "brand_name", "device_family"]},
    4: {"name": "ASSOCIATION_ONLY", "identifiers": ["patent_assignee", "clinical_trial_sponsor"]},
}


@dataclass(frozen=True)
class DeviceIdentity:
    """The resolved identity of a device across tiers.

    Per directive #7: Tier 1 establishes verified identity. Tier 2 establishes
    verified product category. Tier 3 requires corroboration. Tier 4 must NEVER
    automatically become product identity.
    """
    canonical_device_id: str     # the authoritative ID (Tier 1 if available)
    tier1_identifiers: dict      # UDI-DI, K-number, PMA, De Novo
    tier2_identifiers: dict      # product_code + manufacturer
    tier3_identifiers: dict      # model, catalog, brand
    tier4_identifiers: dict      # assignee, sponsor
    resolution_tier: int         # highest tier achieved (1=best, 4=weakest)
    resolution_method: str       # how the identity was resolved

    def is_authoritative(self) -> bool:
        """True if resolved at Tier 1 (authoritative identity)."""
        return self.resolution_tier == 1

    def canonical_dict(self) -> dict:
        return asdict(self)


def resolve_device_identity(record: dict) -> DeviceIdentity:
    """Resolve a device record's identity using the 4-tier hierarchy.

    Per directive #7: "Tier 4 must never automatically become product identity."
    """
    tier1 = {}
    tier2 = {}
    tier3 = {}
    tier4 = {}

    # Tier 1: authoritative identity
    for field_name in ["udi_di", "gudid", "k_number", "pma_number", "denovo_number"]:
        val = record.get(field_name, "")
        if val:
            tier1[field_name] = val

    # Tier 2: strong crosswalk
    pc = record.get("product_code", "")
    mfr = record.get("applicant", "") or record.get("legal_manufacturer", "") or record.get("manufacturer", "")
    if pc and mfr:
        tier2["product_code"] = pc
        tier2["legal_manufacturer"] = mfr
    fei = record.get("fei_number", "")
    if fei:
        tier2["fei"] = fei

    # Tier 3: candidate identifiers
    for field_name in ["model_number", "catalog_number", "brand_name", "device_name"]:
        val = record.get(field_name, "")
        if val:
            tier3[field_name] = val

    # Tier 4: association only
    assignee = record.get("assignee", "") or record.get("patent_assignee", "")
    sponsor = record.get("sponsor", "") or record.get("clinical_trial_sponsor", "")
    if assignee:
        tier4["patent_assignee"] = assignee
    if sponsor:
        tier4["clinical_trial_sponsor"] = sponsor

    # Determine resolution tier
    if tier1:
        resolution_tier = 1
        canonical_id = f"device:t1:{list(tier1.values())[0]}"
        method = "authoritative_identifier"
    elif tier2:
        resolution_tier = 2
        canonical_id = f"device:t2:{tier2.get('product_code','')}:{tier2.get('legal_manufacturer','')[:20]}"
        method = "product_code_plus_manufacturer"
    elif tier3:
        resolution_tier = 3
        canonical_id = f"device:t3:{list(tier3.values())[0][:20]}"
        method = "candidate_identifier_needs_corroboration"
    elif tier4:
        resolution_tier = 4
        canonical_id = f"device:t4:{list(tier4.values())[0][:20]}"
        method = "association_only_NOT_product_identity"
    else:
        resolution_tier = 0
        canonical_id = "device:unresolved"
        method = "unresolved"

    return DeviceIdentity(
        canonical_device_id=canonical_id,
        tier1_identifiers=tier1,
        tier2_identifiers=tier2,
        tier3_identifiers=tier3,
        tier4_identifiers=tier4,
        resolution_tier=resolution_tier,
        resolution_method=method,
    )


# =====================================================================
# DEVICE LINEAGE (directive #6)
# =====================================================================

LINEAGE_EDGE_TYPES = {
    "MEMBER_OF_FAMILY",         # DEVICE_VERSION → DEVICE_FAMILY
    "PREDECESSOR_OF",           # older device → newer device
    "SUCCESSOR_OF",             # newer device → older device
    "PREDICATE_DEVICE",         # 510(k) predicate citation
    "REGULATORY_SUCCESSOR",     # explicit regulatory successor language
}

LINEAGE_EVIDENCE_TYPES = {
    "510K_PREDICATE_CITATION",      # the 510(k) explicitly cites a predicate device
    "EXPLICIT_REGULATORY_SUCCESSOR", # regulatory filing says "successor to..."
    "SHARED_UDI_DI_BASE",            # same UDI-DI base + documented model evolution
    "EXPLICIT_LINEAGE_STATEMENT",    # manufacturer explicitly states lineage
    # NOT accepted:
    # "SAME_COMPANY" — does not establish lineage
    # "SIMILAR_NAME" — does not establish lineage
    # "SIMILAR_PRODUCT_CODE" — does not establish lineage
}


@dataclass(frozen=True)
class DeviceLineageEdge:
    """An evidence-backed lineage relationship between devices.

    Per directive #6: "Do not infer lineage merely because same company,
    similar name, similar product code, similar description."
    """
    edge_id: str
    edge_type: str               # one of LINEAGE_EDGE_TYPES
    source_device_id: str        # the predecessor/older device
    target_device_id: str        # the successor/newer device
    evidence_type: str           # one of LINEAGE_EVIDENCE_TYPES
    evidence_source: str         # source record ID
    evidence_text: str           # the actual text establishing lineage
    evidence_hash: str           # hash of the source record

    def __post_init__(self):
        if self.edge_type not in LINEAGE_EDGE_TYPES:
            raise ValueError(f"Bad lineage edge_type: {self.edge_type!r}")
        if self.evidence_type not in LINEAGE_EVIDENCE_TYPES:
            raise ValueError(f"Bad lineage evidence_type: {self.evidence_type!r}")

    def canonical_dict(self) -> dict:
        return asdict(self)


def extract_predicate_lineage(record: dict) -> Optional[DeviceLineageEdge]:
    """Extract a 510(k) predicate-device lineage edge.

    Per directive #8: "FDA predicate-device citation chains as an underused
    authoritative mechanism."

    510(k) records contain a "predicate" field that explicitly names the
    earlier device on which the new device is based.
    """
    predicate = record.get("predicate", "") or record.get("predicate_device", "")
    if not predicate:
        return None
    device_id = record.get("k_number", record.get("record_id", ""))
    if not device_id:
        return None
    return DeviceLineageEdge(
        edge_id=f"lineage:{hashlib.sha256(f'{predicate}->{device_id}'.encode()).hexdigest()[:12]}",
        edge_type="PREDICATE_DEVICE",
        source_device_id=f"device:{predicate}",
        target_device_id=f"device:{device_id}",
        evidence_type="510K_PREDICATE_CITATION",
        evidence_source=record.get("record_id", ""),
        evidence_text=f"510(k) {device_id} cites predicate device {predicate}",
        evidence_hash=record.get("_raw_hash", ""),
    )


# =====================================================================
# MODERN-DEVICE FORWARD SEEDING (directive #8)
# =====================================================================

def seed_from_modern_devices(maude_records: list[dict],
                              recall_records: list[dict],
                              trial_records: list[dict]) -> list[str]:
    """Seed the graph from currently meaningful technology.

    Per directive #8: "Do not start with arbitrary historical 510(k) records.
    Seed from recent MAUDE activity, active recalls, active clinical trials."
    """
    modern_device_ids = set()
    # Extract device identifiers from MAUDE records
    for record in maude_records:
        for device in record.get("device", []):
            pc = device.get("device_report_product_code", "")
            brand = device.get("brand_name", "")
            if pc:
                modern_device_ids.add(f"product_code:{pc}")
            if brand:
                modern_device_ids.add(f"brand:{brand}")
    # Extract from recalls
    for record in recall_records:
        pc = record.get("product_code", "")
        if pc:
            modern_device_ids.add(f"product_code:{pc}")
    # Extract from trials
    for record in trial_records:
        # Trials may reference device names in the intervention field
        intervention = record.get("interventions", [])
        if isinstance(intervention, list):
            for i in intervention:
                if isinstance(i, str) and len(i) > 5:
                    modern_device_ids.add(f"trial_intervention:{i[:50]}")
    return sorted(modern_device_ids)
