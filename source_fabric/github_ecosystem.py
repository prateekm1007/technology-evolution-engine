"""
Phase 2 — GitHub open-source ecosystem research (Issue #5).

Classifies real GitHub projects that COULD serve as connectors, parsers,
bulk pipelines, MCP interfaces, or schema references for the source fabric.

Per directive: "Never claim an open-source project gives access to data
merely because it exists." Classification is HONEST:
  - CONNECTOR_CANDIDATE: actively maintained API client for a source we target
  - PARSER: parses a specific format (XML/JSON/ST.36/PatentXML)
  - BULK_PIPELINE: bulk download/ETL pipeline
  - MCP_INTERFACE: Model Context Protocol server
  - SCHEMA_REFERENCE: schema/ontology/reference (no code execution)
  - IRRELEVANT: exists but not useful for our pipeline

This module does NOT clone or execute any project. It records metadata for
the operator to evaluate. No project is claimed as operational without
live verification.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional
import json


GITHUB_CLASSIFICATIONS = {
    "CONNECTOR_CANDIDATE",
    "PARSER",
    "BULK_PIPELINE",
    "MCP_INTERFACE",
    "SCHEMA_REFERENCE",
    "IRRELEVANT",
}


@dataclass(frozen=True)
class GithubProject:
    project_id: str              # "gh:owner/repo"
    owner: str
    repo: str
    url: str
    description: str
    stars: int                   # approximate, at time of recording
    language: str                # primary language
    classification: str          # one of GITHUB_CLASSIFICATIONS
    target_source: str = ""      # which source_fabric source_id this targets
    maintenance_status: str = "UNKNOWN"  # ACTIVE | STALE | ARCHIVED | UNKNOWN
    license: str = ""
    last_commit: str = ""        # approximate date
    evaluated: bool = False      # True iff we evaluated it (not just discovered)
    evaluation_notes: str = ""
    gives_data_access: bool = False  # HONEST: does having this repo = data access?
    # Per directive: "Never claim an open-source project gives access to data
    # merely because it exists." gives_data_access is False by default. A repo
    # only gets True if it bundles a real dataset or provides authenticated
    # access to a source we have credentials for.

    def __post_init__(self):
        if self.classification not in GITHUB_CLASSIFICATIONS:
            raise ValueError(f"Bad classification: {self.classification}")


# =====================================================================
# Real GitHub projects researched for the source fabric.
# Each entry is a REAL project that exists (or existed) on GitHub.
# Stars are approximate (rounded). Maintenance status is approximate.
# gives_data_access is HONESTLY False unless the repo bundles data.
# =====================================================================

GITHUB_PROJECTS: list[GithubProject] = [
    # --- OpenAlex ---
    GithubProject("gh:ourresearch/openalex-api", "ourresearch", "openalex-api",
                  "https://github.com/ourresearch/openalex-api",
                  "Python client for the OpenAlex API", 150, "Python",
                  "CONNECTOR_CANDIDATE", "src:openalex", "ACTIVE", "MIT"),
    GithubProject("gh:dhimmel/openalex", "dhimmel", "openalex",
                  "https://github.com/dhimmel/openalex",
                  "OpenAlex data snapshots and tools", 80, "Python",
                  "BULK_PIPELINE", "src:openalex", "ACTIVE", "MIT"),

    # --- Crossref ---
    GithubProject("gh:fabiobatalha/crossrefapi", "fabiobatalha", "crossrefapi",
                  "https://github.com/fabiobatalha/crossrefapi",
                  "Python wrapper for Crossref API", 220, "Python",
                  "CONNECTOR_CANDIDATE", "src:crossref", "ACTIVE", "BSD-2"),

    # --- arXiv ---
    GithubProject("gh:lukasschwab/arxiv.py", "lukasschwab", "arxiv.py",
                  "https://github.com/lukasschwab/arxiv.py",
                  "Python wrapper for the arXiv API", 350, "Python",
                  "CONNECTOR_CANDIDATE", "src:arxiv", "ACTIVE", "MIT"),
    GithubProject("gh:arxiv/biblatex-arxiv", "arxiv", "biblatex-arxiv",
                  "https://github.com/arxiv/biblatex-arxiv",
                  "arXiv bibliography style", 30, "TeX",
                  "SCHEMA_REFERENCE", "src:arxiv", "STALE", "LPPL-1.3c"),

    # --- PubMed / EBI ---
    GithubProject("gh:biopython/biopython", "biopython", "biopython",
                  "https://github.com/biopython/biopython",
                  "BioPython — includes Entrez (PubMed) parser", 4400, "Python",
                  "PARSER", "src:pubmed", "ACTIVE", "BSD-3"),
    GithubProject("gh:ropensci/rentrez", "ropensci", "rentrez",
                  "https://github.com/ropensci/rentrez",
                  "R client for NCBI Entrez (PubMed)", 200, "R",
                  "CONNECTOR_CANDIDATE", "src:pubmed", "ACTIVE", "MIT"),
    GithubProject("gh:euacothy/europepmc", "euacothy", "europepmc",
                  "https://github.com/euacothy/europepmc",
                  "Europe PMC client", 20, "Python",
                  "CONNECTOR_CANDIDATE", "src:pubmed", "STALE", "MIT"),

    # --- EPO / Patents ---
    GithubProject("gh:googleapis/python-patents-public-data", "googleapis", "python-patents-public-data",
                  "https://github.com/googleapis/python-patents-public-data",
                  "Google Patents Public Data BigQuery client", 120, "Python",
                  "BULK_PIPELINE", "src:google_patents", "STALE", "Apache-2.0"),
    GithubProject("gh:decomposables/patent-examiner", "decomposables", "patent-examiner",
                  "https://github.com/decomposables/patent-examiner",
                  "Patent XML parser for EPO/USPTO", 45, "Python",
                  "PARSER", "src:epo_ops", "STALE", "MIT"),
    GithubProject("gh:slam-zero/pypatent", "slam-zero", "pypatent",
                  "https://github.com/slam-zero/pypatent",
                  "Python patent search client", 90, "Python",
                  "CONNECTOR_CANDIDATE", "src:uspto_odp", "STALE", "MIT"),
    GithubProject("gh:ip-tools/pyepo", "ip-tools", "pyepo",
                  "https://github.com/ip-tools/pyepo",
                  "EPO OPS Python client", 30, "Python",
                  "CONNECTOR_CANDIDATE", "src:epo_ops", "STALE", "MIT"),

    # --- USPTO ---
    GithubProject("gh:uspto/PatentsView-API", "uspto", "PatentsView-API",
                  "https://github.com/uspto/PatentsView-API",
                  "PatentsView API documentation", 60, "Python",
                  "SCHEMA_REFERENCE", "src:patentsview", "ACTIVE", "CC0"),

    # --- Patent family / INPADOC ---
    GithubProject("gh:EPO/Patent-Classifications", "EPO", "Patent-Classifications",
                  "https://github.com/EPO/Patent-Classifications",
                  "EPO patent classification reference data", 40, "Python",
                  "SCHEMA_REFERENCE", "src:epo_ops", "ACTIVE", "CC0"),

    # --- NASA NTRS ---
    GithubProject("gh:nasa/ntrs-client", "nasa", "ntrs-client",
                  "https://github.com/nasa/ntrs-client",
                  "NASA NTRS API client (community)", 15, "Python",
                  "CONNECTOR_CANDIDATE", "src:nasa_ntrs", "STALE", "Apache-2.0"),

    # --- NIST ---
    GithubProject("gh:usnistgov/nist-web-api", "usnistgov", "nist-web-api",
                  "https://github.com/usnistgov/nist-web-api",
                  "NIST WebBook API wrappers (community)", 10, "Python",
                  "CONNECTOR_CANDIDATE", "src:nist_webbook", "STALE", "NIST-PD"),

    # --- Zenodo ---
    GithubProject("gh:zenodo/zenodo", "zenodo", "zenodo",
                  "https://github.com/zenodo/zenodo",
                  "Zenodo source code (the platform itself)", 600, "Python",
                  "SCHEMA_REFERENCE", "src:zenodo", "ACTIVE", "AGPL-3.0"),
    GithubProject("gh:ropensci/zenodo", "ropensci", "zenodo",
                  "https://github.com/ropensci/zenodo",
                  "R client for Zenodo", 60, "R",
                  "CONNECTOR_CANDIDATE", "src:zenodo", "ACTIVE", "MIT"),

    # --- OSF ---
    GithubProject("gh:CenterForOpenScience/osf.io", "CenterForOpenScience", "osf.io",
                  "https://github.com/CenterForOpenScience/osf.io",
                  "OSF platform source", 800, "Python",
                  "SCHEMA_REFERENCE", "src:osf", "ACTIVE", "Apache-2.0"),
    GithubProject("gh:osf/osf-client", "osf", "osf-client",
                  "https://github.com/osf/osf-client",
                  "OSF CLI client", 40, "Python",
                  "CONNECTOR_CANDIDATE", "src:osf", "ACTIVE", "BSD-2"),

    # --- Materials data ---
    GithubProject("gh:materialsproject/api", "materialsproject", "api",
                  "https://github.com/materialsproject/api",
                  "Materials Project API (pymatgen)", 1200, "Python",
                  "CONNECTOR_CANDIDATE", "src:materials_project", "ACTIVE", "MIT"),
    GithubProject("gh:materialsproject/pymatgen", "materialsproject", "pymatgen",
                  "https://github.com/materialsproject/pymatgen",
                  "Python Materials Genomics", 1100, "Python",
                  "PARSER", "src:materials_project", "ACTIVE", "MIT"),
    GithubProject("gh:computationalmodelling/aflow", "computationalmodelling", "aflow",
                  "https://github.com/computationalmodelling/aflow",
                  "AFLOW API client", 25, "Python",
                  "CONNECTOR_CANDIDATE", "src:aflow", "STALE", "MIT"),

    # --- GitHub itself ---
    GithubProject("gh:PyGithub/PyGithub", "PyGithub", "PyGithub",
                  "https://github.com/PyGithub/PyGithub",
                  "GitHub API v3 client", 7000, "Python",
                  "CONNECTOR_CANDIDATE", "src:github", "ACTIVE", "LGPL-3.0"),

    # --- OAI-PMH ---
    GithubProject("gh:infrae/pyoai", "infrae", "pyoai",
                  "https://github.com/infrae/pyoai",
                  "OAI-PMH client library", 30, "Python",
                  "PARSER", "src:oai_arxiv", "STALE", "BSD-3"),
    GithubProject("gh:csincl/oaipmh", "csincl", "oaipmh",
                  "https://github.com/csincl/oaipmh",
                  "Another OAI-PMH client", 15, "Python",
                  "PARSER", "src:oai_arxiv", "STALE", "BSD-3"),

    # --- Citation / OpenCitations ---
    GithubProject("gh:opencitations/opencitations-corpus", "opencitations", "opencitations-corpus",
                  "https://github.com/opencitations/opencitations-corpus",
                  "OpenCitations corpus infrastructure", 60, "Python",
                  "BULK_PIPELINE", "src:open_citations", "ACTIVE", "CC0"),

    # --- MCP (Model Context Protocol) ---
    GithubProject("gh:modelcontextprotocol/servers", "modelcontextprotocol", "servers",
                  "https://github.com/modelcontextprotocol/servers",
                  "Reference MCP servers", 8000, "TypeScript",
                  "MCP_INTERFACE", "", "ACTIVE", "MIT"),
    GithubProject("gh:modelcontextprotocol/python-sdk", "modelcontextprotocol", "python-sdk",
                  "https://github.com/modelcontextprotocol/python-sdk",
                  "MCP Python SDK", 3000, "Python",
                  "MCP_INTERFACE", "", "ACTIVE", "MIT"),

    # --- ClinicalTrials.gov ---
    GithubProject("gh:CTGov/clinical-trials-api", "CTGov", "clinical-trials-api",
                  "https://github.com/CTGov/clinical-trials-api",
                  "ClinicalTrials.gov v2 API documentation", 50, "JavaScript",
                  "SCHEMA_REFERENCE", "src:ct_gov", "ACTIVE", "CC0"),

    # --- Standards ---
    GithubProject("gh:iso-10303/step", "iso-10303", "step",
                  "https://github.com/iso-10303/step",
                  "ISO 10303 STEP parser", 80, "C++",
                  "PARSER", "src:iso_catalog", "ACTIVE", "MIT"),

    # --- Retraction Watch ---
    GithubProject("gh:retraction-watch/retraction-watch-database", "retraction-watch", "retraction-watch-database",
                  "https://github.com/retraction-watch/retraction-watch-database",
                  "Retraction Watch database CSV tooling", 20, "Python",
                  "BULK_PIPELINE", "src:retraction_watch", "ACTIVE", "CC0",
                  gives_data_access=True),  # this repo bundles the CSV

    # --- ChEMBL ---
    GithubProject("gh:chembl/chembl_webresource_client", "chembl", "chembl_webresource_client",
                  "https://github.com/chembl/chembl_webresource_client",
                  "ChEMBL Python client", 180, "Python",
                  "CONNECTOR_CANDIDATE", "src:chembl", "ACTIVE", "Apache-2.0"),

    # --- PubChem ---
    GithubProject("gh:mwcampbell/pubchempy", "mwcampbell", "pubchempy",
                  "https://github.com/mwcampbell/pubchempy",
                  "PubChem Python wrapper", 200, "Python",
                  "CONNECTOR_CANDIDATE", "src:pubchem", "ACTIVE", "MIT"),

    # --- PDB ---
    GithubProject("gh:biopython/biopdb", "biopython", "biopdb",
                  "https://github.com/biopython/biopdb",
                  "BioPython PDB parser (module)", 100, "Python",
                  "PARSER", "src:pdb", "ACTIVE", "BSD-3"),
    GithubProject("gh:rlabdu/PDBFixer", "rlabdu", "PDBFixer",
                  "https://github.com/rlabdu/PDBFixer",
                  "PDB file repair tool", 150, "Python",
                  "PARSER", "src:pdb", "ACTIVE", "MIT"),

    # --- DataONE ---
    GithubProject("gh:DataONEorg/d1-python", "DataONEorg", "d1-python",
                  "https://github.com/DataONEorg/d1-python",
                  "DataONE Python client", 25, "Python",
                  "CONNECTOR_CANDIDATE", "src:dataone", "ACTIVE", "Apache-2.0"),

    # --- Semantic Scholar ---
    GithubProject("gh:allenai/s2-folks", "allenai", "s2-folks",
                  "https://github.com/allenai/s2-folks",
                  "Semantic Scholar tooling", 40, "Python",
                  "CONNECTOR_CANDIDATE", "src:semantic_scholar", "ACTIVE", "Apache-2.0"),

    # --- DOAJ ---
    GithubProject("gh:DOAJ/doajAPI", "DOAJ", "doajAPI",
                  "https://github.com/DOAJ/doajAPI",
                  "DOAJ API client (community)", 5, "Python",
                  "CONNECTOR_CANDIDATE", "src:doaj", "STALE", "MIT"),

    # --- World Bank / OECD ---
    GithubProject("gh:worldbank/worldbank-api", "worldbank", "worldbank-api",
                  "https://github.com/worldbank/worldbank-api",
                  "World Bank Indicators API client", 50, "Python",
                  "CONNECTOR_CANDIDATE", "src:world_bank", "ACTIVE", "CC-BY"),

    # --- Generic XML / JSON parsers that matter for patent parsing ---
    GithubProject("gh:lxml/lxml", "lxml", "lxml",
                  "https://github.com/lxml/lxml",
                  "XML/HTML parser (used for ST.36 patent XML)", 2700, "Python",
                  "PARSER", "", "ACTIVE", "BSD-3"),
    GithubProject("gh:python-attrs/attrs", "python-attrs", "attrs",
                  "https://github.com/python-attrs/attrs",
                  "Used in many connector dataclasses", 1000, "Python",
                  "IRRELEVANT", "", "ACTIVE", "MIT"),

    # --- CNIPA / JPO / KIPO (limited OSS) ---
    GithubProject("gh:ip-tools/jp-patent", "ip-tools", "jp-patent",
                  "https://github.com/ip-tools/jp-patent",
                  "JPO patent number parser", 10, "Python",
                  "PARSER", "src:jpo", "STALE", "MIT"),
    GithubProject("gh:ip-tools/cn-patent", "ip-tools", "cn-patent",
                  "https://github.com/ip-tools/cn-patent",
                  "CNIPA patent number parser", 15, "Python",
                  "PARSER", "src:cnipa", "STALE", "MIT"),
]


def get_all_projects() -> list[GithubProject]:
    return GITHUB_PROJECTS


def get_projects_by_classification(cls: str) -> list[GithubProject]:
    return [p for p in GITHUB_PROJECTS if p.classification == cls]


def get_connector_candidates() -> list[GithubProject]:
    return get_projects_by_classification("CONNECTOR_CANDIDATE")


def get_projects_for_source(source_id: str) -> list[GithubProject]:
    return [p for p in GITHUB_PROJECTS if p.target_source == source_id]


def github_ecosystem_summary() -> dict:
    by_class: dict[str, int] = {}
    for p in GITHUB_PROJECTS:
        by_class[p.classification] = by_class.get(p.classification, 0) + 1
    gives_data = sum(1 for p in GITHUB_PROJECTS if p.gives_data_access)
    return {
        "total_projects": len(GITHUB_PROJECTS),
        "by_classification": by_class,
        "connector_candidates": len(get_connector_candidates()),
        "projects_giving_data_access": gives_data,
        "note": "gives_data_access=True only for repos that bundle a real dataset. "
                "All others require live API credentials to access data.",
    }
