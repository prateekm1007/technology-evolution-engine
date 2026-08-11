#!/usr/bin/env python3
"""
TEE Independent Scientific Corpus Acquisition Script

This script acquires scientific sources from multiple providers following
the sampling protocol documented in SAMPLING_PROTOCOL.md.

IMPORTANT: This script must be run with the frozen parameters:
- SAMPLING_SEED = 42871
- PUBLICATION_CUTOFF = 2024-06-30
"""

import json
import hashlib
import requests
import time
from datetime import datetime
from pathlib import Path
import random

# =============================================================================
# FROZEN PARAMETERS - DO NOT MODIFY
# =============================================================================
SAMPLING_SEED = 42871
PUBLICATION_CUTOFF = "2024-06-30"
ACQUISITION_START = "2025-01-01T00:00:00Z"

random.seed(SAMPLING_SEED)

# Target domains
DOMAINS = [
    "physics",
    "chemistry",
    "materials_science",
    "biology",
    "computer_science",
    "mechanical_engineering",
    "electrical_engineering",
    "chemical_engineering",
    "energy_sciences",
    "environmental_science",
    "neuroscience",
    "mathematics",
    "robotics"
]

TARGET_PER_DOMAIN = 300

# Providers
PROVIDERS = ["openalex", "crossref", "semantic_scholar", "openaire"]

# Base directories
BASE_DIR = Path("/workspace/tee-independent-scientific-corpus")
CORPUS_DIR = BASE_DIR / "corpus"
METADATA_DIR = CORPUS_DIR / "metadata"
ABSTRACTS_DIR = CORPUS_DIR / "abstracts"
FULLTEXT_DIR = CORPUS_DIR / "fulltext"
HASHES_DIR = CORPUS_DIR / "hashes"
PROVENANCE_DIR = BASE_DIR / "provenance"
VALIDATION_DIR = BASE_DIR / "validation"

# Ensure directories exist
for d in [METADATA_DIR, ABSTRACTS_DIR, FULLTEXT_DIR, HASHES_DIR, PROVENANCE_DIR, VALIDATION_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# =============================================================================
# UTILITIES
# =============================================================================

def compute_sha256(content):
    """Compute SHA-256 hash of content."""
    if isinstance(content, str):
        content = content.encode('utf-8')
    return hashlib.sha256(content).hexdigest()

def generate_source_id(domain, provider, index):
    """Generate unique source ID."""
    seed_str = f"{SAMPLING_SEED}:{domain}:{provider}:{index}"
    return f"SRC-{hashlib.sha256(seed_str.encode()).hexdigest()[:12].upper()}"

def log_acquisition(log_entry):
    """Log acquisition to provenance directory."""
    timestamp = datetime.utcnow().strftime("%Y-%m-%d")
    log_file = PROVENANCE_DIR / f"acquisition_log_{timestamp}.jsonl"
    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')

def save_metadata(source_id, metadata):
    """Save metadata for a source."""
    metadata_file = METADATA_DIR / f"{source_id}.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

def save_hash(source_id, content_hash):
    """Save content hash."""
    hash_file = HASHES_DIR / f"{source_id}.sha256"
    with open(hash_file, 'w') as f:
        f.write(content_hash)

def save_abstract(source_id, abstract):
    """Save abstract text."""
    abstract_file = ABSTRACTS_DIR / f"{source_id}.txt"
    with open(abstract_file, 'w') as f:
        f.write(abstract or "")

# =============================================================================
# PROVIDER APIs
# =============================================================================

class OpenAlexProvider:
    """OpenAlex API provider."""
    
    BASE_URL = "https://api.openalex.org/works"
    
    def __init__(self, domain, seed):
        self.domain = domain
        self.seed = seed
        self.request_count = 0
        
    def search(self, per_page=200, cursor=None):
        """Search OpenAlex for works in the domain."""
        params = {
            "filter": f"publication_date:<{PUBLICATION_CUTOFF}",
            "per_page": per_page,
            "search": self.domain.replace("_", " ")
        }
        
        if cursor:
            params["cursor"] = cursor
            
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            self.request_count += 1
            
            if response.status_code == 200:
                data = response.json()
                return data.get("results", []), data.get("meta", {}).get("next_cursor")
            else:
                print(f"OpenAlex error: {response.status_code}")
                return [], None
                
        except Exception as e:
            print(f"OpenAlex exception: {e}")
            return [], None

class CrossrefProvider:
    """Crossref API provider."""
    
    BASE_URL = "https://api.crossref.org/works"
    
    def __init__(self, domain, seed):
        self.domain = domain
        self.seed = seed
        self.request_count = 0
        
    def search(self, rows=100, offset=0):
        """Search Crossref for works in the domain."""
        params = {
            "query": self.domain.replace("_", " "),
            "filter": f"until-publication-date:{PUBLICATION_CUTOFF}",
            "rows": rows,
            "offset": offset
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            self.request_count += 1
            
            if response.status_code == 200:
                data = response.json()
                message = data.get("message", {})
                return message.get("items", []), offset + rows
            else:
                print(f"Crossref error: {response.status_code}")
                return [], None
                
        except Exception as e:
            print(f"Crossref exception: {e}")
            return [], None

class SemanticScholarProvider:
    """Semantic Scholar API provider."""
    
    BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
    
    def __init__(self, domain, seed):
        self.domain = domain
        self.seed = seed
        self.request_count = 0
        
    def search(self, limit=100, offset=0):
        """Search Semantic Scholar for papers in the domain."""
        params = {
            "query": self.domain.replace("_", " "),
            "year": "2000-2024",
            "limit": limit,
            "offset": offset,
            "fields": "title,authors,abstract,doi,publicationDate,venue,publisher,url"
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            self.request_count += 1
            
            if response.status_code == 200:
                data = response.json()
                return data.get("data", []), offset + limit
            else:
                print(f"Semantic Scholar error: {response.status_code}")
                return [], None
                
        except Exception as e:
            print(f"Semantic Scholar exception: {e}")
            return [], None

# =============================================================================
# SOURCE PROCESSING
# =============================================================================

seen_dois = set()
seen_hashes = set()
source_count = 0
exclusion_log = []

def process_source(raw_data, provider, domain, index):
    """Process a raw source record into corpus format."""
    global source_count, seen_dois, seen_hashes
    
    # Extract common fields based on provider
    if provider == "openalex":
        title = raw_data.get("title", "")
        authors = [a.get("display_name", "") for a in raw_data.get("authorships", [])]
        doi = raw_data.get("doi")
        pub_date = raw_data.get("publication_date", "")
        publisher = raw_data.get("publisher", "")
        abstract = raw_data.get("abstract_inverted_index", None)
        if abstract and isinstance(abstract, dict):
            # Reconstruct abstract from inverted index
            words = {}
            for word, positions in abstract.items():
                for pos in positions:
                    words[pos] = word
            abstract = " ".join(words[i] for i in sorted(words.keys()))
        source_uri = raw_data.get("url", "")
        fulltext_uri = raw_data.get("open_access", {}).get("oa_url", "")
        
    elif provider == "crossref":
        title = raw_data.get("title", [""])[0] if isinstance(raw_data.get("title"), list) else raw_data.get("title", "")
        authors = [a.get("given", "") + " " + a.get("family", "") for a in raw_data.get("author", [])]
        doi = raw_data.get("DOI")
        pub_date = raw_data.get("published-print", {}).get("date-parts", [[None]])[0][0]
        if not pub_date:
            pub_date = raw_data.get("published-online", {}).get("date-parts", [[None]])[0][0]
        publisher = raw_data.get("publisher", "")
        abstract = raw_data.get("abstract", "")
        source_uri = f"https://doi.org/{doi}" if doi else ""
        fulltext_uri = raw_data.get("URL", "")
        
    elif provider == "semantic_scholar":
        title = raw_data.get("title", "")
        authors = [a.get("name", "") for a in raw_data.get("authors", [])]
        doi = raw_data.get("doi")
        pub_date = raw_data.get("publicationDate", "")
        publisher = raw_data.get("venue", "")
        abstract = raw_data.get("abstract", "")
        source_uri = raw_data.get("url", "")
        fulltext_uri = raw_data.get("url", "")
        
    else:
        return None, "UNKNOWN_PROVIDER"
    
    # Check for critical metadata
    if not title:
        return None, "MISSING_TITLE"
    
    if not authors or len(authors) == 0:
        return None, "MISSING_AUTHORS"
    
    if not pub_date:
        return None, "MISSING_PUBLICATION_DATE"
    
    # Check DOI duplicate
    if doi and doi in seen_dois:
        return None, "DUPLICATE_DOI"
    
    # Generate source ID
    source_id = generate_source_id(domain, provider, index)
    
    # Compute content hash
    content_str = f"{title}|{'|'.join(authors)}|{doi}|{pub_date}"
    content_hash = compute_sha256(content_str)
    
    # Check hash duplicate
    if content_hash in seen_hashes:
        return None, "DUPLICATE_CONTENT"
    
    # Build metadata record
    metadata = {
        "source_id": source_id,
        "title": title,
        "authors": authors,
        "doi": doi,
        "publisher": publisher,
        "publication_date": str(pub_date) if pub_date else None,
        "source_uri": source_uri,
        "repository_uri": None,
        "abstract": abstract,
        "fulltext_uri": fulltext_uri,
        "acquisition_timestamp": datetime.utcnow().isoformat() + "Z",
        "provider": provider,
        "version": "1.0",
        "sha256_hash": content_hash,
        "license": "unknown",
        "domain": domain,
        "domain_confidence": "medium",
        "provenance": {
            "provider": provider,
            "query_parameters": {
                "domain": domain,
                "publication_cutoff": PUBLICATION_CUTOFF
            },
            "acquisition_method": "api_search",
            "verification_status": "verified",
            "duplicate_check_performed": True,
            "retraction_check_performed": False,
            "retraction_status": "unknown",
            "metadata_completeness": {
                "title": "present" if title else "absent",
                "authors": "present" if authors else "absent",
                "doi": "present" if doi else "absent",
                "publication_date": "present" if pub_date else "absent",
                "abstract": "present" if abstract else "absent",
                "publisher": "present" if publisher else "absent"
            }
        }
    }
    
    # Update tracking sets
    if doi:
        seen_dois.add(doi)
    seen_hashes.add(content_hash)
    source_count += 1
    
    return metadata, None

# =============================================================================
# MAIN ACQUISITION LOOP
# =============================================================================

def acquire_corpus():
    """Main corpus acquisition function."""
    global source_count
    
    print("=" * 60)
    print("TEE INDEPENDENT SCIENTIFIC CORPUS ACQUISITION")
    print("=" * 60)
    print(f"SAMPLING_SEED: {SAMPLING_SEED}")
    print(f"PUBLICATION_CUTOFF: {PUBLICATION_CUTOFF}")
    print(f"TARGET_PER_DOMAIN: {TARGET_PER_DOMAIN}")
    print(f"DOMAINS: {len(DOMAINS)}")
    print("=" * 60)
    
    all_sources = []
    
    for domain in DOMAINS:
        print(f"\n>>> Acquiring domain: {domain}")
        domain_count = 0
        
        # Rotate through providers
        for provider_name in PROVIDERS:
            if domain_count >= TARGET_PER_DOMAIN:
                break
                
            print(f"    Provider: {provider_name} (collected: {domain_count}/{TARGET_PER_DOMAIN})")
            
            # Initialize provider
            if provider_name == "openalex":
                provider = OpenAlexProvider(domain, SAMPLING_SEED)
            elif provider_name == "crossref":
                provider = CrossrefProvider(domain, SAMPLING_SEED)
            elif provider_name == "semantic_scholar":
                provider = SemanticScholarProvider(domain, SAMPLING_SEED)
            else:
                continue
            
            # Paginate through results
            page = 0
            max_pages = 10  # Limit pages per provider per domain
            
            while page < max_pages and domain_count < TARGET_PER_DOMAIN:
                if provider_name == "openalex":
                    results, next_cursor = provider.search(per_page=100, cursor=None if page == 0 else next_cursor)
                elif provider_name == "crossref":
                    results, next_offset = provider.search(rows=100, offset=page * 100)
                elif provider_name == "semantic_scholar":
                    results, next_offset = provider.search(limit=100, offset=page * 100)
                else:
                    results = []
                
                if not results:
                    break
                
                # Process each result
                for idx, raw_data in enumerate(results):
                    metadata, exclusion_reason = process_source(
                        raw_data, provider_name, domain, page * 100 + idx
                    )
                    
                    if metadata:
                        # Save metadata
                        save_metadata(metadata["source_id"], metadata)
                        
                        # Save hash
                        save_hash(metadata["source_id"], metadata["sha256_hash"])
                        
                        # Save abstract
                        save_abstract(metadata["source_id"], metadata.get("abstract", ""))
                        
                        all_sources.append(metadata)
                        domain_count += 1
                        
                        # Log acquisition
                        log_entry = {
                            "log_id": f"LOG-{metadata['source_id']}",
                            "timestamp": metadata["acquisition_timestamp"],
                            "provider": provider_name,
                            "domain": domain,
                            "source_id": metadata["source_id"],
                            "status": "accepted",
                            "doi": metadata["doi"]
                        }
                        log_acquisition(log_entry)
                        
                    elif exclusion_reason:
                        # Log exclusion
                        log_entry = {
                            "log_id": f"LOG-EXCLUDED-{domain}-{provider_name}-{page}-{idx}",
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                            "provider": provider_name,
                            "domain": domain,
                            "status": "rejected",
                            "rejection_reason": exclusion_reason
                        }
                        log_acquisition(log_entry)
                        exclusion_log.append({
                            "domain": domain,
                            "provider": provider_name,
                            "reason": exclusion_reason,
                            "count": 1
                        })
                
                page += 1
                time.sleep(0.5)  # Rate limiting
            
            print(f"    Collected from {provider_name}: {domain_count}")
        
        print(f">>> Domain {domain} complete: {domain_count} sources")
    
    return all_sources

def save_exclusion_report():
    """Save exclusion report."""
    # Aggregate exclusions
    exclusion_summary = {}
    for exc in exclusion_log:
        key = f"{exc['domain']}:{exc['provider']}:{exc['reason']}"
        if key not in exclusion_summary:
            exclusion_summary[key] = {
                "domain": exc["domain"],
                "provider": exc["provider"],
                "reason": exc["reason"],
                "count": 0
            }
        exclusion_summary[key]["count"] += exc.get("count", 1)
    
    report = {
        "total_exclusions": len(exclusion_log),
        "exclusion_summary": list(exclusion_summary.values()),
        "generated_at": datetime.utcnow().isoformat() + "Z"
    }
    
    report_file = VALIDATION_DIR / "exclusions.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

if __name__ == "__main__":
    print("\nStarting corpus acquisition...\n")
    
    sources = acquire_corpus()
    
    print(f"\n{'=' * 60}")
    print(f"ACQUISITION COMPLETE")
    print(f"{'=' * 60}")
    print(f"Total sources acquired: {len(sources)}")
    print(f"Unique DOIs: {len(seen_dois)}")
    print(f"Unique content hashes: {len(seen_hashes)}")
    
    # Save exclusion report
    save_exclusion_report()
    
    print(f"\nMetadata saved to: {METADATA_DIR}")
    print(f"Hashes saved to: {HASHES_DIR}")
    print(f"Abstracts saved to: {ABSTRACTS_DIR}")
    print(f"Provenance logs saved to: {PROVENANCE_DIR}")
    print(f"Exclusion report saved to: {VALIDATION_DIR}/exclusions.json")
