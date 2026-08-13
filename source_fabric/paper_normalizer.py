"""
Phase 7 — Paper normalization (Issue #5).

11 distinct fields kept SEPARATE:
  work, preprint_version, article, DOI, PMID, references, topics,
  abstract, fulltext, supplementary_data, code, datasets

A single scholarly "work" may have:
  - multiple preprint versions (arXiv v1, v2, v3)
  - multiple published articles (preprint + journal version + erratum)
  - one DOI (but some works have multiple DOIs across versions)
  - one PMID (if indexed in PubMed)
  - multiple references (each a separate edge)
  - multiple topics (OpenAlex concepts)
  - one abstract (but may differ across versions)
  - one fulltext (or none, if paywalled)
  - multiple supplementary data files
  - linked code repositories
  - linked datasets
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional
import hashlib


@dataclass(frozen=True)
class Work:
    """The abstract scholarly work — the canonical entity (OpenAlex W-id)."""
    work_id: str                # e.g. "work:openalex:W1234"
    title: str = ""
    publication_date: str = ""

    def node_id(self) -> str:
        return self.work_id


@dataclass(frozen=True)
class PreprintVersion:
    """A preprint version (e.g. arXiv v1, v2). Distinct from the published article."""
    preprint_id: str            # e.g. "preprint:arxiv:2401.12345v2"
    work_id: str
    repository: str             # arxiv | biorxiv | chemrxiv | osf
    version: str                # v1, v2, ...
    deposition_date: str = ""

    def node_id(self) -> str:
        return self.preprint_id


@dataclass(frozen=True)
class Article:
    """The published article — distinct from preprints and from the work."""
    article_id: str             # e.g. "article:doi:10.1000/xyz"
    work_id: str
    journal: str = ""
    volume: str = ""
    issue: str = ""
    pages: str = ""
    publication_date: str = ""

    def node_id(self) -> str:
        return self.article_id


@dataclass(frozen=True)
class DOI:
    doi_id: str                 # e.g. "doi:10.1000/xyz"
    work_id: str
    doi_string: str             # the canonical DOI string

    def node_id(self) -> str:
        return self.doi_id


@dataclass(frozen=True)
class PMID:
    pmid_id: str                # e.g. "pmid:12345678"
    work_id: str
    pmid_number: str

    def node_id(self) -> str:
        return self.pmid_id


@dataclass(frozen=True)
class Reference:
    """A citation edge — work A references work B. Each is a separate edge."""
    reference_id: str
    citing_work_id: str
    cited_work_id: str
    context: str = ""           # the citation context sentence

    def node_id(self) -> str:
        return self.reference_id


@dataclass(frozen=True)
class Topic:
    """A topic/concept — OpenAlex concept or MeSH term."""
    topic_id: str               # e.g. "topic:openalex:C1234"
    work_id: str
    topic_name: str
    score: float = 0.0

    def node_id(self) -> str:
        return self.topic_id


@dataclass(frozen=True)
class Abstract:
    abstract_id: str
    work_id: str
    text: str
    language: str = "en"

    def node_id(self) -> str:
        return self.abstract_id


@dataclass(frozen=True)
class FullText:
    fulltext_id: str
    work_id: str
    text: str = ""
    license: str = ""
    source: str = ""            # publisher | repository | ocr

    def node_id(self) -> str:
        return self.fulltext_id


@dataclass(frozen=True)
class SupplementaryData:
    supp_id: str
    work_id: str
    url: str
    file_type: str = ""

    def node_id(self) -> str:
        return self.supp_id


@dataclass(frozen=True)
class CodeLink:
    """A code repository linked to a paper."""
    code_id: str
    work_id: str
    repo_url: str
    platform: str = ""          # github | gitlab | bitbucket | zenodo

    def node_id(self) -> str:
        return self.code_id


@dataclass(frozen=True)
class DatasetLink:
    """A dataset linked to a paper."""
    dataset_id: str
    work_id: str
    dataset_url: str
    repository: str = ""        # zenodo | figshare | osf | dryad

    def node_id(self) -> str:
        return self.dataset_id


# =====================================================================
# Normalization: raw OpenAlex/Crossref payload -> 11-field canonical form
# =====================================================================

def normalize_paper(raw: dict) -> dict:
    """Normalize a raw paper payload (OpenAlex or Crossref shape) into the
    11-field canonical form."""
    work_id = f"work:openalex:{raw.get('openalex_id', raw.get('doi', 'UNKNOWN'))}"
    normalized = {
        "work": asdict(Work(work_id=work_id,
                            title=raw.get("title", ""),
                            publication_date=raw.get("publication_date", ""))),
        "preprint_version": [],
        "article": None,
        "doi": None,
        "pmid": None,
        "references": [],
        "topics": [],
        "abstract": None,
        "fulltext": None,
        "supplementary_data": [],
        "code": [],
        "datasets": [],
    }
    # Preprint versions (list)
    for pp in raw.get("preprints", []):
        normalized["preprint_version"].append(asdict(PreprintVersion(
            preprint_id=f"preprint:{pp.get('repository','rep')}:{pp.get('id','?')}v{pp.get('version','1')}",
            work_id=work_id,
            repository=pp.get("repository", ""),
            version=pp.get("version", "1"),
            deposition_date=pp.get("date", ""),
        )))
    # Article (the published version)
    if raw.get("doi"):
        article_id = f"article:doi:{raw['doi']}"
        normalized["article"] = asdict(Article(
            article_id=article_id, work_id=work_id,
            journal=raw.get("journal", ""),
            volume=raw.get("volume", ""),
            issue=raw.get("issue", ""),
            pages=raw.get("pages", ""),
            publication_date=raw.get("publication_date", ""),
        ))
    # DOI
    if raw.get("doi"):
        normalized["doi"] = asdict(DOI(
            doi_id=f"doi:{raw['doi']}", work_id=work_id,
            doi_string=raw["doi"],
        ))
    # PMID
    if raw.get("pmid"):
        normalized["pmid"] = asdict(PMID(
            pmid_id=f"pmid:{raw['pmid']}", work_id=work_id,
            pmid_number=raw["pmid"],
        ))
    # References (each is a separate edge)
    for ref in raw.get("references", []):
        rid = f"ref:{hashlib.sha256(f'{work_id}->{ref}'.encode()).hexdigest()[:8]}"
        normalized["references"].append(asdict(Reference(
            reference_id=rid, citing_work_id=work_id,
            cited_work_id=ref if isinstance(ref, str) else ref.get("work_id", ""),
            context=ref.get("context", "") if isinstance(ref, dict) else "",
        )))
    # Topics
    for t in raw.get("topics", []):
        tid = f"topic:{t.get('source','oa')}:{hashlib.sha256(t.get('name','').encode()).hexdigest()[:8]}"
        normalized["topics"].append(asdict(Topic(
            topic_id=tid, work_id=work_id,
            topic_name=t.get("name", ""),
            score=t.get("score", 0.0),
        )))
    # Abstract
    if raw.get("abstract"):
        normalized["abstract"] = asdict(Abstract(
            abstract_id=f"abstract:{work_id}", work_id=work_id,
            text=raw["abstract"], language=raw.get("language", "en"),
        ))
    # Fulltext
    if raw.get("fulltext"):
        normalized["fulltext"] = asdict(FullText(
            fulltext_id=f"fulltext:{work_id}", work_id=work_id,
            text=raw["fulltext"][:50000],
            license=raw.get("fulltext_license", ""),
            source=raw.get("fulltext_source", ""),
        ))
    # Supplementary data
    for s in raw.get("supplementary", []):
        normalized["supplementary_data"].append(asdict(SupplementaryData(
            supp_id=f"supp:{hashlib.sha256(s.get('url','').encode()).hexdigest()[:8]}",
            work_id=work_id, url=s.get("url", ""),
            file_type=s.get("type", ""),
        )))
    # Code links
    for c in raw.get("code", []):
        normalized["code"].append(asdict(CodeLink(
            code_id=f"code:{hashlib.sha256(c.get('url','').encode()).hexdigest()[:8]}",
            work_id=work_id, repo_url=c.get("url", ""),
            platform=c.get("platform", ""),
        )))
    # Dataset links
    for d in raw.get("datasets", []):
        normalized["datasets"].append(asdict(DatasetLink(
            dataset_id=f"dataset:{hashlib.sha256(d.get('url','').encode()).hexdigest()[:8]}",
            work_id=work_id, dataset_url=d.get("url", ""),
            repository=d.get("repository", ""),
        )))
    return normalized


def paper_field_count() -> int:
    """The 11+ distinct fields kept separate by the normalizer."""
    return 12  # work, preprint_version, article, doi, pmid, references, topics,
               # abstract, fulltext, supplementary_data, code, datasets
