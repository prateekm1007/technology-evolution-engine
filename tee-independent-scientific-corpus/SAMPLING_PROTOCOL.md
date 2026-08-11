# Sampling Protocol

## Purpose

This document defines the sampling methodology for constructing the TEE Independent Scientific Corpus. All procedures are designed to be:

- **Externally seeded**: Random seed fixed before sampling begins
- **Reproducible**: Another party can reproduce the exact sample
- **Documented**: All parameters and decisions recorded
- **Independent**: Not influenced by TEE outputs or preferences

## Frozen Parameters

### Random Seed

```
SAMPLING_SEED = 42871
```

This seed was fixed BEFORE any source acquisition began.

### Publication Cutoff

```
PUBLICATION_CUTOFF = 2024-06-30
```

All sources in the corpus must have publication dates on or before this date.

### Acquisition Window

```
ACQUISITION_START = 2025-01-01T00:00:00Z
ACQUISITION_END = 2025-01-31T23:59:59Z
```

All acquisitions occurred within this window.

## Target Domains

The corpus targets the following scientifically distinct domains:

1. **Physics** (including condensed matter, particle physics, optics)
2. **Chemistry** (including organic, inorganic, physical chemistry)
3. **Materials Science** (distinct from physics and chemistry)
4. **Biology** (including molecular biology, ecology, evolutionary biology)
5. **Computer Science** (including AI, algorithms, systems)
6. **Mechanical Engineering**
7. **Electrical Engineering**
8. **Chemical Engineering**
9. **Energy Sciences** (including renewable energy, batteries, fuel cells)
10. **Environmental Science** (including climate science, earth science)
11. **Neuroscience** (including cognitive neuroscience, neurobiology)
12. **Mathematics** (including applied mathematics, statistics)
13. **Robotics** (including control systems, autonomous systems)

**Note**: Related disciplines are NOT collapsed. For example:
- Biology ≠ Biochemistry ≠ Molecular Biology
- Physics ≠ Materials Science
- Computer Science ≠ Robotics

Each maintains distinct identity unless the taxonomy explicitly establishes otherwise.

## Sampling Algorithm

### Method: Stratified Random Sampling with Provider Rotation

```python
import random
import hashlib
from datetime import datetime

# Fixed seed
random.seed(42871)

# Domain stratification
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

# Target per domain (adjust based on availability)
TARGET_PER_DOMAIN = 300  # Approximately 3900 total

# Providers in rotation order
PROVIDERS = ["openalex", "crossref", "semantic_scholar", "openaire"]

def generate_query(domain, provider, page_size=100):
    """Generate provider-specific query parameters."""
    return {
        "query": f"{domain.replace('_', ' ')} research paper",
        "filter": f"publication_date:<={PUBLICATION_CUTOFF}",
        "per_page": page_size,
        "seed": hashlib.sha256(f"{SAMPLING_SEED}:{domain}:{provider}".encode()).hexdigest()[:8]
    }
```

## Provider-Specific Protocols

### OpenAlex

```json
{
  "base_url": "https://api.openalex.org/works",
  "parameters": {
    "filter": "publication_date:<2024-07-01",
    "per_page": 200,
    "seed": "{domain_seed}"
  },
  "pagination": "cursor-based",
  "rate_limit": "respect API limits"
}
```

Query strategy:
1. For each domain, construct search query using domain keywords
2. Apply publication date filter
3. Paginate through results using cursor
4. Collect up to TARGET_PER_DOMAIN per domain

### Crossref

```json
{
  "base_url": "https://api.crossref.org/works",
  "parameters": {
    "query": "{domain_keywords}",
    "filter": "until-publication-date:2024-06-30",
    "rows": 100
  },
  "pagination": "offset-based",
  "rate_limit": "polite pool recommended"
}
```

### Semantic Scholar

```json
{
  "base_url": "https://api.semanticscholar.org/graph/v1/paper/search",
  "parameters": {
    "query": "{domain_keywords}",
    "year": "2000-2024",
    "limit": 100
  },
  "pagination": "offset-based",
  "rate_limit": "100 requests per minute"
}
```

### OpenAIRE

```json
{
  "base_url": "https://api.openaire.eu/search/publications",
  "parameters": {
    "keyword": "{domain_keywords}",
    "enddate": "2024-06-30",
    "size": 100
  },
  "pagination": "page-based",
  "rate_limit": "respect API limits"
}
```

## Inclusion Rules

A source is INCLUDED if ALL of the following are true:

1. ✅ Publication date ≤ 2024-06-30
2. ✅ Belongs to one of the target domains
3. ✅ Is a scholarly work (peer-reviewed paper, preprint, conference paper, thesis)
4. ✅ Has at minimum: title, authors, publication date
5. ✅ Has verifiable provenance from at least one provider
6. ✅ Is not a retraction notice alone
7. ✅ Passes duplicate detection (or is kept as representative duplicate)
8. ✅ Metadata completeness ≥ 60% of required fields

## Exclusion Rules

A source is EXCLUDED if ANY of the following are true:

1. ❌ Publication date > 2024-06-30
2. ❌ Not a scholarly work (news article, blog post, advertisement)
3. ❌ Critical metadata missing (no title, no authors, no date)
4. ❌ Provenance cannot be verified from any provider
5. ❌ Is an exact duplicate (by content hash) of already-included source
6. ❌ Domain cannot be determined or is outside target domains
7. ❌ Is a retracted work (unless specifically retained for audit purposes)

## Pagination and Cursor Handling

For each provider:

1. Record initial query parameters
2. Track pagination state (cursor, offset, or page number)
3. Log each page request with timestamp
4. Handle rate limiting with exponential backoff
5. Stop when:
   - Target count reached for domain
   - No more results available
   - API error rate exceeds threshold

## Acquisition Logging

Every acquisition MUST be logged:

```json
{
  "log_id": "unique_log_identifier",
  "timestamp": "2025-01-15T14:32:17Z",
  "provider": "openalex",
  "domain": "physics",
  "query_parameters": {...},
  "page_info": {
    "type": "cursor",
    "value": "eyJpZCI6IjEyMzQ1Njc4OTAifQ==",
    "page_number": 15
  },
  "results_returned": 200,
  "results_accepted": 187,
  "results_rejected": 13,
  "rejection_reasons": {
    "DUPLICATE_DOI": 8,
    "METADATA_INCOMPLETE": 3,
    "DOMAIN_MISMATCH": 2
  },
  "response_status": 200,
  "rate_limit_remaining": 95,
  "error_message": null
}
```

## Reproducibility Checklist

To reproduce this sampling:

- [ ] Use identical random seed: 42871
- [ ] Use identical publication cutoff: 2024-06-30
- [ ] Use identical domain list and definitions
- [ ] Use identical provider queries and parameters
- [ ] Use identical inclusion/exclusion rules
- [ ] Process providers in same order
- [ ] Handle pagination identically
- [ ] Apply duplicate detection with same thresholds
- [ ] Record all exclusion reasons identically

## Sample Size Determination

Target corpus size: **2,000–5,000 source records**

Final size determined by:
1. Availability of scholarly material in each domain
2. Quality filters (metadata completeness, provenance verification)
3. Duplicate removal
4. Domain balance considerations

Do NOT stop at arbitrary numbers. Let the sampling protocol determine final size.

## Domain Assignment Protocol

When a source could belong to multiple domains:

1. Use primary classification from the providing API
2. If multiple classifications exist, use the most specific
3. If still ambiguous, assign to ALL applicable domains (record multi-domain status)
4. Do NOT force single-domain assignment if source is genuinely interdisciplinary

Record domain assignment confidence:
- `high`: Clear single-domain assignment
- `medium`: Primary domain clear, secondary possible
- `low`: Interdisciplinary, multiple domains applicable
- `assigned_multi`: Explicitly assigned to multiple domains

---

*This protocol was frozen before sampling began. Any deviation requires documentation and justification.*
