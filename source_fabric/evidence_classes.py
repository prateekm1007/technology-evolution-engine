"""
V5 Evidence Class System (Issue #5 V5, directive G).

Per CTO directive: "Never flatten them into generic 'evidence'."

10 distinct evidence classes. Each record in the graph MUST declare its
evidence_class. Cross-corpus edges track the evidence_class of both endpoints.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


EVIDENCE_CLASSES = {
    "SCIENTIFIC_OBSERVATION",    # peer-reviewed papers, preprints
    "PATENT_DISCLOSURE",         # patent description/specification
    "PATENT_CLAIM",              # patent claims (legally scoped)
    "DEVICE_REGULATORY_ACTION",  # FDA 510(k), PMA, De Novo, classification
    "CLINICAL_EVIDENCE",         # clinical trial protocols + results
    "ADVERSE_EVENT",             # MAUDE, FDA adverse event reports
    "CORPORATE_RISK",            # SEC 10-K risk factors
    "MARKET_SIGNAL",             # product launches, recalls (commercial)
    "DATASET",                   # experimental datasets (Materials Project, etc.)
    "SOFTWARE",                  # code repositories
}

# Mapping from source_id to evidence_class
SOURCE_TO_EVIDENCE_CLASS = {
    "src:openalex": "SCIENTIFIC_OBSERVATION",
    "src:pubmed": "SCIENTIFIC_OBSERVATION",
    "src:crossref": "SCIENTIFIC_OBSERVATION",
    "src:arxiv": "SCIENTIFIC_OBSERVATION",
    "src:huggingface_patents": "PATENT_DISCLOSURE",  # text = title+abstract+claims
    "src:google_patents": "PATENT_DISCLOSURE",
    "src:epo_ops": "PATENT_DISCLOSURE",
    "src:ct_gov": "CLINICAL_EVIDENCE",
    "src:sec_edgar": "CORPORATE_RISK",
    # FDA sources
    "src:fda_510k": "DEVICE_REGULATORY_ACTION",
    "src:fda_pma": "DEVICE_REGULATORY_ACTION",
    "src:fda_denovo": "DEVICE_REGULATORY_ACTION",
    "src:fda_maude": "ADVERSE_EVENT",
    "src:fda_recalls": "MARKET_SIGNAL",  # recalls are market signals + adverse events
    "src:fda_classification": "DEVICE_REGULATORY_ACTION",
    "src:fda_registration": "DEVICE_REGULATORY_ACTION",
    "src:fda_pas": "CLINICAL_EVIDENCE",  # post-approval studies
    # Datasets
    "src:materials_project": "DATASET",
    "src:pubchem": "DATASET",
    "src:zenodo": "DATASET",
    # Code
    "src:github": "SOFTWARE",
}


def get_evidence_class(source_id: str) -> str:
    """Return the evidence class for a source_id. FAILS CLOSED.

    Per CTO V6 directive: "Unknown source → UNCLASSIFIED → QUARANTINED →
    failure recorded. A new, misspelled, missing, or unregistered source
    can silently enter the graph as scientific evidence. That directly
    conflicts with no-silent-substitution."

    Unknown source_ids return "UNCLASSIFIED" — NOT "SCIENTIFIC_OBSERVATION".
    The caller MUST check for UNCLASSIFIED and quarantine the record.
    """
    return SOURCE_TO_EVIDENCE_CLASS.get(source_id, "UNCLASSIFIED")


def is_classified(evidence_class: str) -> bool:
    """True if the evidence class is a real class (not UNCLASSIFIED)."""
    return evidence_class in EVIDENCE_CLASSES


def quarantine_unclassified(source_id: str, record_id: str) -> dict:
    """Produce a quarantine record for an unclassified source.

    Per directive: unknown source → UNCLASSIFIED → QUARANTINED → failure recorded.
    """
    return {
        "record_id": record_id,
        "source_id": source_id,
        "evidence_class": "UNCLASSIFIED",
        "quarantine_reason": "UNKNOWN_SOURCE",
        "action": "QUARANTINED",
        "message": f"Source '{source_id}' is not in the evidence-class registry. "
                   f"Record quarantined. Add the source to SOURCE_TO_EVIDENCE_CLASS "
                   f"before this record can enter the graph.",
    }


def validate_evidence_class(ec: str) -> bool:
    return ec in EVIDENCE_CLASSES


# =====================================================================
# Patent document type classification (directive A)
# =====================================================================

PATENT_DOCUMENT_TYPES = {
    "PATENT_GRANT",          # issued/granted patent
    "PATENT_APPLICATION",    # published application (pre-grant)
    "PATENT_DOCUMENT",       # generic (type unknown)
}


def classify_patent_document(patent_type: str) -> str:
    """Classify a patent document as GRANT, APPLICATION, or generic DOCUMENT.

    The allenai/us-patents dataset has patent_type values like 'utility',
    'design', 'plant', 'reissue'. These are patent KINDS, not grant/application
    status. We need to infer from the patent_type field.

    Per CTO: "Do not count a document as a family."
    """
    pt = (patent_type or "").lower().strip()
    if "grant" in pt or "issued" in pt:
        return "PATENT_GRANT"
    if "application" in pt or "pre-grant" in pt or "pregrant" in pt:
        return "PATENT_APPLICATION"
    # The allenai dataset has 'utility', 'design', 'plant', 'reissue'
    # These are patent kinds, not grant/application. We label as DOCUMENT
    # since we cannot determine grant vs application from this field alone.
    return "PATENT_DOCUMENT"
