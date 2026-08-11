"""
independent_corpus.acquisition.sampler — Pre-declared deterministic sampling.

The sampling procedure is pre-declared and deterministic.
No TEE influence. No "interestingness." No connection search.

SAMPLING PROCEDURE:
1. Query OpenAlex for all articles published before date_cutoff with DOIs
2. Sort by publication_date descending (most recent first within cutoff)
3. Page through results deterministically using cursor pagination
4. Sample every Nth result (deterministic, seeded)
5. No keyword search, no domain filter, no connection search

The seed determines WHICH Nth result to start from, not WHICH papers to find.
"""
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class AcquisitionManifest:
    """Pre-declared acquisition manifest. Frozen before execution."""
    provider: str
    provider_version: str
    query_space: str  # Description of what was queried (NOT what was searched for)
    sampling_method: str  # Description of the sampling procedure
    random_seed: str  # External seed
    random_seed_hash: str  # SHA-256 of seed
    date_cutoff: str  # Temporal cutoff
    license_policy: str  # License requirements
    domain_policy: str  # Domain acquisition policy
    inclusion_rules: List[str]  # What must be true for inclusion
    exclusion_rules: List[str]  # What causes exclusion
    n_requested: int  # How many were requested
    n_received: int = 0  # How many were actually received
    n_eligible: int = 0  # How many passed intake
    no_tee_influence: bool = True  # Verified: no TEE input to sampling
    no_connection_search: bool = True  # Verified: no cross-domain queries
    manifest_hash: str = ""  # Computed after construction

    def to_dict(self) -> dict:
        d = {
            "provider": self.provider,
            "provider_version": self.provider_version,
            "query_space": self.query_space,
            "sampling_method": self.sampling_method,
            "random_seed_hash": self.random_seed_hash,
            "date_cutoff": self.date_cutoff,
            "license_policy": self.license_policy,
            "domain_policy": self.domain_policy,
            "inclusion_rules": self.inclusion_rules,
            "exclusion_rules": self.exclusion_rules,
            "n_requested": self.n_requested,
            "n_received": self.n_received,
            "n_eligible": self.n_eligible,
            "no_tee_influence": self.no_tee_influence,
            "no_connection_search": self.no_connection_search,
        }
        return d

    def compute_hash(self) -> str:
        """Compute SHA-256 of the manifest (excluding manifest_hash itself)."""
        import json
        d = self.to_dict()
        canonical = json.dumps(d, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
        self.manifest_hash = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
        return self.manifest_hash


def create_acquisition_manifest(
    date_cutoff: str,
    random_seed: str,
    n_requested: int = 5000,
    provider: str = "openalex",
) -> AcquisitionManifest:
    """Create a pre-declared acquisition manifest.

    This manifest is FROZEN before any acquisition begins.
    It documents EXACTLY what will be sampled and how.
    """
    manifest = AcquisitionManifest(
        provider=provider,
        provider_version="2024-08",
        query_space=(
            "All articles in OpenAlex with DOIs, published before "
            f"{date_cutoff}, retrieved via cursor pagination sorted by "
            "publication_date descending. NO keyword search. NO domain filter. "
            "NO connection search."
        ),
        sampling_method=(
            "Deterministic cursor pagination: retrieve pages of 200 results "
            "sorted by publication_date desc, starting from cursor='*'. "
            "Sample every Nth result where N is derived from the external seed. "
            "No re-ranking. No filtering by 'interestingness'. "
            "No TEE input."
        ),
        random_seed=random_seed,
        random_seed_hash=hashlib.sha256(random_seed.encode('utf-8')).hexdigest(),
        date_cutoff=date_cutoff,
        license_policy=(
            "Accept all licenses. Record license for each source. "
            "Flag sources without open access for custodian review."
        ),
        domain_policy=(
            "Acquire from ALL domains. Do NOT filter by domain during acquisition. "
            "Domain classification happens AFTER acquisition using the frozen "
            "custodian taxonomy. No domain is preferred or excluded."
        ),
        inclusion_rules=[
            "Has DOI",
            "Type = article",
            f"publication_date <= {date_cutoff}",
            "Has title",
        ],
        exclusion_rules=[
            "No DOI",
            "Type != article",
            "Publication date after cutoff",
            "Duplicate content hash",
            "TEE prior-exposure: KNOWN_SEEN",
            "Contamination: CONTAMINATED",
        ],
        n_requested=n_requested,
        no_tee_influence=True,
        no_connection_search=True,
    )
    manifest.compute_hash()
    return manifest


def verify_no_tee_influence(manifest: AcquisitionManifest) -> List[str]:
    """Verify that the acquisition manifest has no TEE influence.

    Returns list of violations (empty = clean).
    """
    violations = []

    # Check query_space for TEE-related terms
    query = manifest.query_space.lower()
    forbidden_terms = ["tee", "hypothesis", "discovery", "interesting", "promising", "score", "ranking"]
    for term in forbidden_terms:
        if term in query:
            violations.append(f"FORBIDDEN_TERM_IN_QUERY: '{term}' found in query_space")

    # Check sampling_method for connection search
    method = manifest.sampling_method.lower()
    connection_terms = ["combine", "bridge", "cross-domain", "connection", "transfer"]
    for term in connection_terms:
        if term in method:
            violations.append(f"CONNECTION_SEARCH_TERM: '{term}' found in sampling_method")

    # Check inclusion rules for TEE references (exclusion rules MAY reference TEE for security)
    for rule in manifest.inclusion_rules:
        rule_lower = rule.lower()
        for term in ["tee", "model", "hypothesis", "score"]:
            if term in rule_lower:
                violations.append(f"TEE_REFERENCE_IN_INCLUSION_RULE: '{term}' in rule '{rule}'")

    # Verify flags
    if not manifest.no_tee_influence:
        violations.append("no_tee_influence flag is False")
    if not manifest.no_connection_search:
        violations.append("no_connection_search flag is False")

    return violations
