"""
Phase 6 — Patent normalization (Issue #5).

Per directive: "Do not collapse a patent family into one patent record."

12 distinct fields kept SEPARATE:
  application, publication, grant, patent_document, family, priority,
  applicant, inventor, assignee, claims, description, legal_status,
  NPL_citations, CPC_IPC

Each is a distinct node in the graph. A patent_family node contains
member patent_document nodes. A patent_document node has separate
application/publication/grant sub-nodes (a single application can
produce multiple publications; a single publication can be granted or
rejected).
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional
import hashlib
import json


@dataclass(frozen=True)
class PatentApplication:
    application_id: str          # e.g. "app:EP:EP2024123456"
    filing_date: str             # ISO date
    jurisdiction: str            # EP | US | CN | IN | JP | KR | WO
    application_number: str
    applicant: str = ""

    def node_id(self) -> str:
        return self.application_id


@dataclass(frozen=True)
class PatentPublication:
    publication_id: str          # e.g. "pub:EP:EP1234567A1"
    publication_date: str
    publication_number: str
    jurisdiction: str
    kind_code: str = ""          # A1, A2, B1, B2, etc.

    def node_id(self) -> str:
        return self.publication_id


@dataclass(frozen=True)
class PatentGrant:
    grant_id: str                # e.g. "grant:EP:EP1234567B1"
    grant_date: str
    grant_number: str
    jurisdiction: str

    def node_id(self) -> str:
        return self.grant_id


@dataclass(frozen=True)
class PatentDocument:
    """A single patent document (one publication). Distinct from the family
    and from the application. May have a grant associated."""
    document_id: str
    publication_id: str
    application_id: str
    grant_id: Optional[str] = None
    title: str = ""
    abstract: str = ""
    jurisdiction: str = ""
    kind_code: str = ""

    def node_id(self) -> str:
        return self.document_id


@dataclass(frozen=True)
class PatentFamily:
    """A DOCDB simple family. Contains MULTIPLE member documents.
    NEVER collapsed into one record."""
    family_id: str               # e.g. "fam:DOCDB:12345678"
    earliest_priority_date: str
    member_document_ids: tuple[str, ...] = ()
    jurisdictions: tuple[str, ...] = ()

    def node_id(self) -> str:
        return self.family_id


@dataclass(frozen=True)
class PatentPriority:
    priority_id: str             # e.g. "prio:EP:EP2023123456"
    priority_date: str
    jurisdiction: str
    priority_number: str

    def node_id(self) -> str:
        return self.priority_id


@dataclass(frozen=True)
class PatentApplicant:
    applicant_id: str
    name: str
    jurisdiction: str = ""

    def node_id(self) -> str:
        return self.applicant_id


@dataclass(frozen=True)
class PatentInventor:
    inventor_id: str
    name: str

    def node_id(self) -> str:
        return self.inventor_id


@dataclass(frozen=True)
class PatentAssignee:
    """Current legal owner — distinct from applicant (who filed)."""
    assignee_id: str
    name: str
    jurisdiction: str = ""

    def node_id(self) -> str:
        return self.assignee_id


@dataclass(frozen=True)
class PatentClaims:
    """Patent claims — separate from the description. Each claim is atomic."""
    claims_id: str
    document_id: str
    independent_claims: tuple[str, ...] = ()
    dependent_claims: tuple[str, ...] = ()

    def node_id(self) -> str:
        return self.claims_id


@dataclass(frozen=True)
class PatentDescription:
    """The patent specification/description — separate from claims."""
    description_id: str
    document_id: str
    text: str = ""

    def node_id(self) -> str:
        return self.description_id


@dataclass(frozen=True)
class LegalStatus:
    """Legal status event — a patent may have many over time."""
    status_id: str
    document_id: str
    status: str                  # granted | refused | withdrawn | lapsed | expired | pending
    event_date: str
    jurisdiction: str = ""

    def node_id(self) -> str:
        return self.status_id


@dataclass(frozen=True)
class NPLCitation:
    """Non-Patent Literature citation — a paper cited as prior art."""
    npl_id: str
    citing_document_id: str
    cited_paper_id: str          # link to the paper corpus
    role: str                    # X | Y | A | T | D | *
    citation_date: str = ""

    def node_id(self) -> str:
        return self.npl_id


@dataclass(frozen=True)
class ClassificationCode:
    """CPC or IPC classification code."""
    code_id: str                 # e.g. "cpc:H01M10/0525"
    scheme: str                  # CPC | IPC
    code: str
    document_id: str = ""

    def node_id(self) -> str:
        return self.code_id


# =====================================================================
# Normalization: raw EPO/USPTO payload -> 12-field canonical form
# =====================================================================

def normalize_patent(raw: dict) -> dict:
    """Normalize a raw patent payload (EPO-OPS or USPTO shape) into the
    12-field canonical form. Each field is a separate sub-dict; none are
    collapsed into the document.

    The raw payload is expected to have fields like:
      application_number, filing_date, publication_number, publication_date,
      grant_date, grant_number, inventors, assignees, applicants, claims,
      description, family_id, priority_date, citations, classifications
    """
    normalized = {
        "application": None,
        "publication": None,
        "grant": None,
        "patent_document": None,
        "family": None,
        "priority": None,
        "applicant": [],
        "inventor": [],
        "assignee": [],
        "claims": None,
        "description": None,
        "legal_status": [],
        "npl_citations": [],
        "cpc_ipc": [],
    }
    # Application
    if raw.get("application_number"):
        normalized["application"] = PatentApplication(
            application_id=f"app:{raw.get('jurisdiction','XX')}:{raw['application_number']}",
            filing_date=raw.get("filing_date", ""),
            jurisdiction=raw.get("jurisdiction", ""),
            application_number=raw["application_number"],
            applicant=raw.get("applicant_name", ""),
        ).canonical_dict() if hasattr(PatentApplication, "canonical_dict") else asdict(PatentApplication(
            application_id=f"app:{raw.get('jurisdiction','XX')}:{raw['application_number']}",
            filing_date=raw.get("filing_date", ""),
            jurisdiction=raw.get("jurisdiction", ""),
            application_number=raw["application_number"],
            applicant=raw.get("applicant_name", ""),
        ))
    # Publication
    if raw.get("publication_number"):
        normalized["publication"] = asdict(PatentPublication(
            publication_id=f"pub:{raw.get('jurisdiction','XX')}:{raw['publication_number']}",
            publication_date=raw.get("publication_date", ""),
            publication_number=raw["publication_number"],
            jurisdiction=raw.get("jurisdiction", ""),
            kind_code=raw.get("kind_code", ""),
        ))
    # Grant
    if raw.get("grant_number") and raw.get("grant_date"):
        normalized["grant"] = asdict(PatentGrant(
            grant_id=f"grant:{raw.get('jurisdiction','XX')}:{raw['grant_number']}",
            grant_date=raw["grant_date"],
            grant_number=raw["grant_number"],
            jurisdiction=raw.get("jurisdiction", ""),
        ))
    # Document
    if raw.get("publication_number"):
        doc_id = f"doc:{raw.get('jurisdiction','XX')}:{raw['publication_number']}"
        normalized["patent_document"] = asdict(PatentDocument(
            document_id=doc_id,
            publication_id=normalized["publication"]["publication_id"] if normalized["publication"] else "",
            application_id=normalized["application"]["application_id"] if normalized["application"] else "",
            grant_id=normalized["grant"]["grant_id"] if normalized["grant"] else None,
            title=raw.get("title", ""),
            abstract=raw.get("abstract", ""),
            jurisdiction=raw.get("jurisdiction", ""),
            kind_code=raw.get("kind_code", ""),
        ))
    # Family
    if raw.get("family_id"):
        normalized["family"] = asdict(PatentFamily(
            family_id=f"fam:DOCDB:{raw['family_id']}",
            earliest_priority_date=raw.get("priority_date", ""),
            member_document_ids=(normalized["patent_document"]["document_id"],) if normalized["patent_document"] else (),
            jurisdictions=(raw.get("jurisdiction", ""),),
        ))
    # Priority
    if raw.get("priority_date"):
        normalized["priority"] = asdict(PatentPriority(
            priority_id=f"prio:{raw.get('jurisdiction','XX')}:{raw.get('priority_number','UNKNOWN')}",
            priority_date=raw["priority_date"],
            jurisdiction=raw.get("jurisdiction", ""),
            priority_number=raw.get("priority_number", ""),
        ))
    # Applicants (list)
    for a in raw.get("applicants", []):
        aid = f"applicant:{hashlib.sha256(a.encode()).hexdigest()[:8]}"
        normalized["applicant"].append(asdict(PatentApplicant(
            applicant_id=aid, name=a, jurisdiction=raw.get("jurisdiction", ""),
        )))
    # Inventors (list)
    for i in raw.get("inventors", []):
        iid = f"inventor:{hashlib.sha256(i.encode()).hexdigest()[:8]}"
        normalized["inventor"].append(asdict(PatentInventor(inventor_id=iid, name=i)))
    # Assignees (list — distinct from applicants)
    for a in raw.get("assignees", []):
        aid = f"assignee:{hashlib.sha256(a.encode()).hexdigest()[:8]}"
        normalized["assignee"].append(asdict(PatentAssignee(
            assignee_id=aid, name=a, jurisdiction=raw.get("jurisdiction", ""),
        )))
    # Claims
    if raw.get("claims"):
        normalized["claims"] = asdict(PatentClaims(
            claims_id=f"claims:{normalized['patent_document']['document_id']}" if normalized["patent_document"] else "claims:UNKNOWN",
            document_id=normalized["patent_document"]["document_id"] if normalized["patent_document"] else "",
            independent_claims=tuple(raw["claims"].get("independent", [])),
            dependent_claims=tuple(raw["claims"].get("dependent", [])),
        ))
    # Description
    if raw.get("description"):
        normalized["description"] = asdict(PatentDescription(
            description_id=f"desc:{normalized['patent_document']['document_id']}" if normalized["patent_document"] else "desc:UNKNOWN",
            document_id=normalized["patent_document"]["document_id"] if normalized["patent_document"] else "",
            text=raw["description"][:10000],  # truncate for storage
        ))
    # Legal status events (list)
    for ls in raw.get("legal_status_events", []):
        normalized["legal_status"].append(asdict(LegalStatus(
            status_id=f"status:{hashlib.sha256(json.dumps(ls, sort_keys=True).encode()).hexdigest()[:8]}",
            document_id=normalized["patent_document"]["document_id"] if normalized["patent_document"] else "",
            status=ls.get("status", ""),
            event_date=ls.get("date", ""),
            jurisdiction=raw.get("jurisdiction", ""),
        )))
    # NPL citations (list)
    for c in raw.get("npl_citations", []):
        normalized["npl_citations"].append(asdict(NPLCitation(
            npl_id=f"npl:{hashlib.sha256(json.dumps(c, sort_keys=True).encode()).hexdigest()[:8]}",
            citing_document_id=normalized["patent_document"]["document_id"] if normalized["patent_document"] else "",
            cited_paper_id=c.get("paper_id", ""),
            role=c.get("role", "*"),
            citation_date=c.get("date", ""),
        )))
    # CPC/IPC (list)
    for cl in raw.get("classifications", []):
        scheme = cl.get("scheme", "CPC")
        code = cl.get("code", "")
        normalized["cpc_ipc"].append(asdict(ClassificationCode(
            code_id=f"{scheme.lower()}:{code}",
            scheme=scheme, code=code,
            document_id=normalized["patent_document"]["document_id"] if normalized["patent_document"] else "",
        )))
    return normalized


def patent_field_count() -> int:
    """The 12+ distinct fields kept separate by the normalizer."""
    return 14  # application, publication, grant, document, family, priority,
               # applicant, inventor, assignee, claims, description, legal_status,
               # npl_citations, cpc_ipc
