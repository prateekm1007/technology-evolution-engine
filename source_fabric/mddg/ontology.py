"""
Medical Device Discovery Graph V1 — Ontology (CTO directive #3).

18 canonical entity types. Each entity has:
  canonical_id, source_ids, provenance, jurisdiction, date_range, confidence_status

These are not merely labels — they are the node types of the medical-device
lifecycle graph. Every record in the graph MUST be typed as one of these.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional
import hashlib
import json


ENTITY_TYPES = {
    "DEVICE",
    "MANUFACTURER",
    "PRODUCT_CODE",
    "PATENT",
    "PATENT_FAMILY",
    "PAPER",
    "MECHANISM",
    "MATERIAL",
    "COMPONENT",
    "INDICATION",
    "PROCEDURE",
    "CLINICAL_TRIAL",
    "CLINICAL_ENDPOINT",
    "ADVERSE_EVENT",
    "FAILURE_MODE",
    "RECALL",
    "STANDARD",
    "MANUFACTURING_PROCESS",
}


@dataclass(frozen=True)
class Entity:
    """A canonical medical-device graph entity.

    Every entity has 6 mandatory fields per CTO directive #3.
    """
    canonical_id: str
    entity_type: str
    source_ids: tuple[str, ...]
    provenance: tuple[dict, ...]
    jurisdiction: str
    date_range: tuple[Optional[str], Optional[str]]
    confidence_status: str = "VERIFIED"
    label: str = ""
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.entity_type not in ENTITY_TYPES:
            raise ValueError(f"Bad entity_type: {self.entity_type!r}. "
                             f"Allowed: {sorted(ENTITY_TYPES)}")
        if self.confidence_status not in ("VERIFIED", "INFERRED", "UNVERIFIED", "DISPUTED"):
            raise ValueError(f"Bad confidence_status: {self.confidence_status!r}")

    def content_hash(self) -> str:
        return hashlib.sha256(
            json.dumps(asdict(self), sort_keys=True, default=str).encode()
        ).hexdigest()


def make_device(*, device_id, source_ids, provenance, jurisdiction="US",
                date_range=(None, None), label="", metadata=None):
    return Entity(canonical_id=f"device:{device_id}", entity_type="DEVICE",
                  source_ids=source_ids, provenance=provenance,
                  jurisdiction=jurisdiction, date_range=date_range,
                  confidence_status="VERIFIED", label=label, metadata=metadata or {})

def make_manufacturer(*, name, source_ids, provenance, jurisdiction="US", metadata=None):
    mid = hashlib.sha256(name.encode()).hexdigest()[:12]
    return Entity(canonical_id=f"manufacturer:{mid}", entity_type="MANUFACTURER",
                  source_ids=source_ids, provenance=provenance, jurisdiction=jurisdiction,
                  date_range=(None, None), label=name, metadata=metadata or {})

def make_product_code(*, code, source_ids, provenance, jurisdiction="US", label="", metadata=None):
    return Entity(canonical_id=f"product_code:{code}", entity_type="PRODUCT_CODE",
                  source_ids=source_ids, provenance=provenance, jurisdiction=jurisdiction,
                  date_range=(None, None), label=label, metadata=metadata or {})

def make_patent(*, patent_id, source_ids, provenance, jurisdiction="US",
                date_range=(None, None), label="", metadata=None):
    return Entity(canonical_id=f"patent:{patent_id}", entity_type="PATENT",
                  source_ids=source_ids, provenance=provenance, jurisdiction=jurisdiction,
                  date_range=date_range, label=label, metadata=metadata or {})

def make_paper(*, paper_id, source_ids, provenance, jurisdiction="",
               date_range=(None, None), label="", metadata=None):
    return Entity(canonical_id=f"paper:{paper_id}", entity_type="PAPER",
                  source_ids=source_ids, provenance=provenance, jurisdiction=jurisdiction,
                  date_range=date_range, label=label, metadata=metadata or {})

def make_mechanism(*, name, source_ids, provenance, label="", metadata=None):
    mid = hashlib.sha256(name.encode()).hexdigest()[:12]
    return Entity(canonical_id=f"mechanism:{mid}", entity_type="MECHANISM",
                  source_ids=source_ids, provenance=provenance, jurisdiction="",
                  date_range=(None, None), label=label or name, metadata=metadata or {})

def make_material(*, name, source_ids, provenance, label="", metadata=None):
    mid = hashlib.sha256(name.encode()).hexdigest()[:12]
    return Entity(canonical_id=f"material:{mid}", entity_type="MATERIAL",
                  source_ids=source_ids, provenance=provenance, jurisdiction="",
                  date_range=(None, None), label=label or name, metadata=metadata or {})

def make_clinical_trial(*, nct_id, source_ids, provenance, jurisdiction="US",
                        date_range=(None, None), label="", metadata=None):
    return Entity(canonical_id=f"trial:{nct_id}", entity_type="CLINICAL_TRIAL",
                  source_ids=source_ids, provenance=provenance, jurisdiction=jurisdiction,
                  date_range=date_range, label=label, metadata=metadata or {})

def make_adverse_event(*, event_id, source_ids, provenance, jurisdiction="US",
                       date_range=(None, None), label="", metadata=None):
    return Entity(canonical_id=f"adverse_event:{event_id}", entity_type="ADVERSE_EVENT",
                  source_ids=source_ids, provenance=provenance, jurisdiction=jurisdiction,
                  date_range=date_range, label=label, metadata=metadata or {})

def make_failure_mode(*, name, source_ids, provenance, label="", metadata=None):
    fid = hashlib.sha256(name.encode()).hexdigest()[:12]
    return Entity(canonical_id=f"failure_mode:{fid}", entity_type="FAILURE_MODE",
                  source_ids=source_ids, provenance=provenance, jurisdiction="",
                  date_range=(None, None), label=label or name, metadata=metadata or {})

def make_recall(*, recall_id, source_ids, provenance, jurisdiction="US",
                date_range=(None, None), label="", metadata=None):
    return Entity(canonical_id=f"recall:{recall_id}", entity_type="RECALL",
                  source_ids=source_ids, provenance=provenance, jurisdiction=jurisdiction,
                  date_range=date_range, label=label, metadata=metadata or {})

def make_standard(*, standard_id, source_ids, provenance, jurisdiction="",
                  date_range=(None, None), label="", metadata=None):
    return Entity(canonical_id=f"standard:{standard_id}", entity_type="STANDARD",
                  source_ids=source_ids, provenance=provenance, jurisdiction=jurisdiction,
                  date_range=date_range, label=label, metadata=metadata or {})
