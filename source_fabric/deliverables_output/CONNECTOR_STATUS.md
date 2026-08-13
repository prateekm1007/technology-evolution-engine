# Connector Status (Issue #5, Phase 12)

Generated: 2026-08-13T00:58:41.627411+00:00

## Status Vocabulary

- `NOT_BUILT` — no connector code exists
- `BUILT` — connector code exists, not yet probed live
- `VERIFIED` — connector probed live, schema confirmed
- `OPERATIONAL` — connector is actively harvesting records

## GitHub Open-Source Ecosystem

Total projects researched: **44**
Connector candidates: **20**
Projects giving data access (bundled data): **1**

Per directive: *'Never claim an open-source project gives access to data merely because it exists.'*

## Connector Status Table

| source_id | name | connector_status | probe_result | github_projects |
|-----------|------|-----------------|-------------|-----------------|
| `src:openalex` | OpenAlex | NOT_BUILT | NOT_PROBED | 2 |
| `src:crossref` | Crossref | NOT_BUILT | NOT_PROBED | 1 |
| `src:arxiv` | arXiv | NOT_BUILT | NOT_PROBED | 2 |
| `src:pubmed` | PubMed | NOT_BUILT | NOT_PROBED | 3 |
| `src:semantic_scholar` | Semantic Scholar | NOT_BUILT | NOT_PROBED | 1 |
| `src:doaj` | Directory of Open Access Journals | NOT_BUILT | NOT_PROBED | 1 |
| `src:core` | CORE | NOT_BUILT | NOT_PROBED | 0 |
| `src:unpaywall` | Unpaywall | NOT_BUILT | NOT_PROBED | 0 |
| `src:base` | Bielefeld Academic Search Engine | NOT_BUILT | NOT_PROBED | 0 |
| `src:dblp` | DBLP | NOT_BUILT | NOT_PROBED | 0 |
| `src:ieee_xplore` | IEEE Xplore | NOT_BUILT | NOT_PROBED | 0 |
| `src:acm_dl` | ACM Digital Library | NOT_BUILT | NOT_PROBED | 0 |
| `src:scopus` | Scopus | NOT_BUILT | NOT_PROBED | 0 |
| `src:wos` | Web of Science | NOT_BUILT | NOT_PROBED | 0 |
| `src:clockss` | LOCKSS/CLOCKSS | NOT_BUILT | NOT_PROBED | 0 |
| `src:portico` | Portico | NOT_BUILT | NOT_PROBED | 0 |
| `src:epo_ops` | EPO Open Patent Services | NOT_BUILT | NOT_PROBED | 3 |
| `src:uspto_odp` | USPTO Open Data Portal | NOT_BUILT | NOT_PROBED | 1 |
| `src:patentsview` | PatentsView | NOT_BUILT | NOT_PROBED | 1 |
| `src:wipo_patentscope` | WIPO PATENTSCOPE | NOT_BUILT | NOT_PROBED | 0 |
| `src:google_patents` | Google Patents | NOT_BUILT | NOT_PROBED | 1 |
| `src:cnipa` | CNIPA (China) | NOT_BUILT | NOT_PROBED | 1 |
| `src:ip_india` | IP India | NOT_BUILT | NOT_PROBED | 0 |
| `src:jpo` | JPO (Japan) | NOT_BUILT | NOT_PROBED | 1 |
| `src:kipo` | KIPO (Korea) | NOT_BUILT | NOT_PROBED | 0 |
| `src:espacenet` | Espacenet | NOT_BUILT | NOT_PROBED | 0 |
| `src:lens` | The Lens | NOT_BUILT | NOT_PROBED | 0 |
| `src:opentext_ePO` | EPO Register | NOT_BUILT | NOT_PROBED | 0 |
| `src:uspto_ppat` | USPTO Patent Public Search | NOT_BUILT | NOT_PROBED | 0 |
| `src:nasa_ntrs` | NASA Technical Reports Server | NOT_BUILT | NOT_PROBED | 1 |
| `src:doe_osti` | DOE OSTI | NOT_BUILT | NOT_PROBED | 0 |
| `src:nist_pubs` | NIST Publications | NOT_BUILT | NOT_PROBED | 0 |
| `src:dtic` | DTIC (DoD Technical Reports) | NOT_BUILT | NOT_PROBED | 0 |
| `src:worldcat` | WorldCat | NOT_BUILT | NOT_PROBED | 0 |
| `src:eric` | ERIC | NOT_BUILT | NOT_PROBED | 0 |
| `src:gsdrl` | GS DoD Resources & Education | NOT_BUILT | NOT_PROBED | 0 |
| `src:iso_catalog` | ISO Catalog | NOT_BUILT | NOT_PROBED | 1 |
| `src:iec_catalog` | IEC Catalog | NOT_BUILT | NOT_PROBED | 0 |
| `src:astm_catalog` | ASTM Standards | NOT_BUILT | NOT_PROBED | 0 |
| `src:nist_srd` | NIST Standard Reference Data | NOT_BUILT | NOT_PROBED | 0 |
| `src:ansi_catalog` | ANSI Webstore | NOT_BUILT | NOT_PROBED | 0 |
| `src:ieee_standards` | IEEE Standards Dictionary | NOT_BUILT | NOT_PROBED | 0 |
| `src:iso_639_lang` | ISO 639 language codes | NOT_BUILT | NOT_PROBED | 0 |
| `src:zenodo` | Zenodo | NOT_BUILT | NOT_PROBED | 2 |
| `src:figshare` | Figshare | NOT_BUILT | NOT_PROBED | 0 |
| `src:dataone` | DataONE | NOT_BUILT | NOT_PROBED | 1 |
| `src:gbif` | GBIF | NOT_BUILT | NOT_PROBED | 0 |
| `src:ncbi_sra` | NCBI SRA | NOT_BUILT | NOT_PROBED | 0 |
| `src:pdb` | RCSB PDB | NOT_BUILT | NOT_PROBED | 2 |
| `src:materials_project` | Materials Project | NOT_BUILT | NOT_PROBED | 2 |
| `src:aflow` | AFLOW | NOT_BUILT | NOT_PROBED | 1 |
| `src:oqmd` | OQMD | NOT_BUILT | NOT_PROBED | 0 |
| `src:nomad` | NOMAD | NOT_BUILT | NOT_PROBED | 0 |
| `src:icsd` | ICSD | NOT_BUILT | NOT_PROBED | 0 |
| `src:cod` | Crystallography Open Database | NOT_BUILT | NOT_PROBED | 0 |
| `src:usgs_data` | USGS Science Data | NOT_BUILT | NOT_PROBED | 0 |
| `src:noaa_ncei` | NOAA NCEI | NOT_BUILT | NOT_PROBED | 0 |
| `src:esa_cds` | ESA Climate Data Store | NOT_BUILT | NOT_PROBED | 0 |
| `src:nasa_earthdata` | NASA EarthData | NOT_BUILT | NOT_PROBED | 0 |
| `src:ckan_gov` | data.gov (CKAN) | NOT_BUILT | NOT_PROBED | 0 |
| `src:eu_opendata` | EU Open Data Portal | NOT_BUILT | NOT_PROBED | 0 |
| `src:github` | GitHub | NOT_BUILT | NOT_PROBED | 1 |
| `src:gitlab` | GitLab | NOT_BUILT | NOT_PROBED | 0 |
| `src:bitbucket` | Bitbucket | NOT_BUILT | NOT_PROBED | 0 |
| `src:zenodo_code` | Zenodo (code) | NOT_BUILT | NOT_PROBED | 0 |
| `src:osf` | Open Science Framework | NOT_BUILT | NOT_PROBED | 2 |
| `src:ascl` | Astrophysics Source Code Library | NOT_BUILT | NOT_PROBED | 0 |
| `src:ros_index` | ROS Index | NOT_BUILT | NOT_PROBED | 0 |
| `src:conda` | conda-forge | NOT_BUILT | NOT_PROBED | 0 |
| `src:pypi` | PyPI | NOT_BUILT | NOT_PROBED | 0 |
| `src:cran` | CRAN | NOT_BUILT | NOT_PROBED | 0 |
| `src:bioconductor` | Bioconductor | NOT_BUILT | NOT_PROBED | 0 |
| `src:dockerhub` | Docker Hub | NOT_BUILT | NOT_PROBED | 0 |
| `src:huggingface` | Hugging Face Hub | NOT_BUILT | NOT_PROBED | 0 |
| `src:paperswithcode` | Papers with Code | NOT_BUILT | NOT_PROBED | 0 |
| `src:nist_webbook` | NIST WebBook | NOT_BUILT | NOT_PROBED | 1 |
| `src:beilstein` | Beilstein Database | NOT_BUILT | NOT_PROBED | 0 |
| `src:gmelin` | Gmelin Database | NOT_BUILT | NOT_PROBED | 0 |
| `src:pubchem` | PubChem | NOT_BUILT | NOT_PROBED | 1 |
| `src:chembl` | ChEMBL | NOT_BUILT | NOT_PROBED | 1 |
| `src:bindingdb` | BindingDB | NOT_BUILT | NOT_PROBED | 0 |
| `src:pdbe` | PDBe (EMBL-EBI) | NOT_BUILT | NOT_PROBED | 0 |
| `src:emdb` | EMDB (Electron Microscopy) | NOT_BUILT | NOT_PROBED | 0 |
| `src:icgc` | ICGC Data Portal | NOT_BUILT | NOT_PROBED | 0 |
| `src:tcga` | TCGA | NOT_BUILT | NOT_PROBED | 0 |
| `src:chemSpider` | ChemSpider | NOT_BUILT | NOT_PROBED | 0 |
| `src:reaction_predictor` | Reaxys Reactions | NOT_BUILT | NOT_PROBED | 0 |
| `src:ct_gov` | ClinicalTrials.gov | NOT_BUILT | NOT_PROBED | 1 |
| `src:eu_ctr` | EU CTR | NOT_BUILT | NOT_PROBED | 0 |
| `src:isrctn` | ISRCTN | NOT_BUILT | NOT_PROBED | 0 |
| `src:who_ictrp` | WHO ICTRP | NOT_BUILT | NOT_PROBED | 0 |
| `src:japic_cti` | JapicCTI (Japan) | NOT_BUILT | NOT_PROBED | 0 |
| `src:anzctr` | ANZCTR | NOT_BUILT | NOT_PROBED | 0 |
| `src:fda_devices` | FDA 510(k) Devices | NOT_BUILT | NOT_PROBED | 0 |
| `src:fda_drugs` | FDA Drugs@FDA | NOT_BUILT | NOT_PROBED | 0 |
| `src:ema_drugs` | EMA Drugs | NOT_BUILT | NOT_PROBED | 0 |
| `src:uspto_tm` | USPTO Trademark | NOT_BUILT | NOT_PROBED | 0 |
| `src:cec_db` | DOE appliance standards | NOT_BUILT | NOT_PROBED | 0 |
| `src:energystar` | EnergyStar product list | NOT_BUILT | NOT_PROBED | 0 |
| `src:ul_db` | UL Product IQ | NOT_BUILT | NOT_PROBED | 0 |
| `src:fda_recalls` | FDA Recalls | NOT_BUILT | NOT_PROBED | 0 |
| `src:cpsc_recalls` | CPSC Recalls | NOT_BUILT | NOT_PROBED | 0 |
| `src:nhtsa_recalls` | NHTSA Recalls | NOT_BUILT | NOT_PROBED | 0 |
| `src:retraction_watch` | Retraction Watch | NOT_BUILT | NOT_PROBED | 1 |
| `src:cochrane_revman` | Cochrane Reviews | NOT_BUILT | NOT_PROBED | 0 |
| `src:ntsb_reports` | NTSB Reports | NOT_BUILT | NOT_PROBED | 0 |
| `src:csb_reports` | CSB Reports | NOT_BUILT | NOT_PROBED | 0 |
| `src:plazi` | Plazi TreatmentBank | NOT_BUILT | NOT_PROBED | 0 |
| `src:open_citations` | OpenCitations | NOT_BUILT | NOT_PROBED | 1 |
| `src:crossref_fundref` | Crossref Funder Registry | NOT_BUILT | NOT_PROBED | 0 |
| `src:orcid` | ORCID | NOT_BUILT | NOT_PROBED | 0 |
| `src:ror` | ROR (Research Org Registry) | NOT_BUILT | NOT_PROBED | 0 |
| `src:rad` | Reusable Data | NOT_BUILT | NOT_PROBED | 0 |
| `src:eu_horizon` | EU CORDIS | NOT_BUILT | NOT_PROBED | 0 |
| `src:grants_gov` | Grants.gov | NOT_BUILT | NOT_PROBED | 0 |
| `src:nih_reporter` | NIH RePORTER | NOT_BUILT | NOT_PROBED | 0 |
| `src:nsf_awards` | NSF Awards | NOT_BUILT | NOT_PROBED | 0 |
| `src:doe_funding` | DOE PAMS | NOT_BUILT | NOT_PROBED | 0 |
| `src:oai_arxiv` | arXiv OAI-PMH | NOT_BUILT | NOT_PROBED | 2 |
| `src:crossref_rest` | Crossref REST | NOT_BUILT | NOT_PROBED | 0 |
| `src:oa_webfeed` | OpenAlex Web Feed | NOT_BUILT | NOT_PROBED | 0 |
| `src:doaj_rss` | DOAJ RSS | NOT_BUILT | NOT_PROBED | 0 |
| `src:pubmed_rss` | PubMed RSS | NOT_BUILT | NOT_PROBED | 0 |
| `src:dimensions` | Dimensions | NOT_BUILT | NOT_PROBED | 0 |
| `src:altmetric` | Altmetric | NOT_BUILT | NOT_PROBED | 0 |
| `src:plumx` | PlumX | NOT_BUILT | NOT_PROBED | 0 |
| `src:usda_ree` | USDA REE | NOT_BUILT | NOT_PROBED | 0 |
| `src:epa_scihub` | EPA Science Hub | NOT_BUILT | NOT_PROBED | 0 |
| `src:oecd_stats` | OECD Stats | NOT_BUILT | NOT_PROBED | 0 |
| `src:world_bank` | World Bank Open Data | NOT_BUILT | NOT_PROBED | 1 |
| `src:microryza` | Experiment.com | NOT_BUILT | NOT_PROBED | 0 |
| `src:archive_org_scholarly` | Internet Archive Scholar | NOT_BUILT | NOT_PROBED | 0 |
| `src:sharedit` | Springer SharedIt | NOT_BUILT | NOT_PROBED | 0 |

## Honest Boundary

**LIVE_INGEST = FALSE.** No live HTTP probes have been performed.
All `probe_result` values are `NOT_PROBED`. All `connector_status` values are `NOT_BUILT`.
To make connectors operational: set credentials, run `--live`, probe each source.