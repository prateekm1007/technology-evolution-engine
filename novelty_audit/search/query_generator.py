"""
novelty_audit.search.query_generator — Deterministic query generation from pair evidence.

Generates search queries from Source A and Source B titles/abstracts.
NO TEE. NO LLM. NO human judgment. Deterministic from pair evidence.

Query types:
1. Direct combination: Source A mechanism terms AND Source B mechanism terms
2. Reverse combination: Source B mechanism terms AND Source A mechanism terms
3. Domain bridge: Source A domain AND Source B domain AND "mechanism"
4. Mechanism transfer: "transfer" OR "apply" + Source A terms + Source B domain
"""
import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class SearchQuery:
    """A single search query."""
    query_id: str
    pair_id: str
    query_type: str  # direct, reverse, domain_bridge, mechanism_transfer
    database: str  # openalex, semantic_scholar, crossref
    query_text: str
    query_hash: str

    def to_dict(self) -> dict:
        return {
            "query_id": self.query_id,
            "pair_id": self.pair_id,
            "query_type": self.query_type,
            "database": self.database,
            "query_text": self.query_text,
            "query_hash": self.query_hash,
        }


# Stopwords for query term extraction
STOPWORDS = {
    "the", "and", "for", "with", "from", "that", "this", "are", "was",
    "were", "has", "have", "had", "been", "not", "but", "all", "can",
    "may", "will", "its", "our", "their", "these", "those", "into",
    "than", "then", "them", "what", "when", "where", "which", "while",
    "a", "an", "in", "on", "at", "to", "of", "by", "as", "is", "it",
    "be", "or", "we", "they", "he", "she", "his", "her", "i", "you",
    "your", "us", "so", "if", "no", "do", "did", "does", "done",
    "about", "above", "after", "again", "against", "before", "being",
    "below", "between", "during", "few", "further", "here", "how",
    "more", "most", "other", "over", "own", "same", "should", "some",
    "such", "there", "through", "under", "up", "very", "via", "within",
    "without", "using", "based", "study", "studies", "research",
    "results", "show", "shown", "found", "also", "however", "which",
}

# Mechanism/transfer indicator terms for query construction
TRANSFER_TERMS = ["transfer", "apply", "adapt", "inspired", "biomimetic"]


def extract_mechanism_terms(text: str, max_terms: int = 5) -> List[str]:
    """Extract the most significant mechanism terms from text.

    Deterministic: extracts nouns/noun phrases by frequency, filtered by stopwords.
    NO LLM. NO semantic processing. Pure token frequency.
    """
    if not text:
        return []

    # Tokenize
    tokens = re.findall(r'\b[a-z]{4,}\b', text.lower())
    # Remove stopwords
    tokens = [t for t in tokens if t not in STOPWORDS]

    # Count frequency
    from collections import Counter
    freq = Counter(tokens)

    # Return top N by frequency (deterministic — Counter.most_common is stable)
    return [term for term, _ in freq.most_common(max_terms)]


def generate_queries_for_pair(
    pair_id: str,
    title_a: str,
    abstract_a: str,
    title_b: str,
    abstract_b: str,
    domain_a: str,
    domain_b: str,
    databases: List[str] = None,
) -> List[SearchQuery]:
    """Generate all search queries for one pair.

    Deterministic: same inputs → same queries. No LLM. No TEE.
    """
    if databases is None:
        databases = ["openalex", "semantic_scholar", "crossref"]

    # Extract mechanism terms from title + abstract
    text_a = f"{title_a} {abstract_a}"
    text_b = f"{title_b} {abstract_b}"
    terms_a = extract_mechanism_terms(text_a, max_terms=5)
    terms_b = extract_mechanism_terms(text_b, max_terms=5)

    queries = []

    for db in databases:
        # Query type 1: Direct combination
        # Source A terms AND Source B terms
        if terms_a and terms_b:
            query_text = f"{' '.join(terms_a[:3])} {' '.join(terms_b[:3])}"
            qid = f"Q-{pair_id}-direct-{db}"
            queries.append(SearchQuery(
                query_id=qid, pair_id=pair_id, query_type="direct",
                database=db, query_text=query_text,
                query_hash=hashlib.sha256(f"{qid}|{query_text}".encode()).hexdigest(),
            ))

        # Query type 2: Reverse combination (same terms, reversed — tests bidirectional)
        if terms_b and terms_a:
            query_text = f"{' '.join(terms_b[:3])} {' '.join(terms_a[:3])}"
            qid = f"Q-{pair_id}-reverse-{db}"
            queries.append(SearchQuery(
                query_id=qid, pair_id=pair_id, query_type="reverse",
                database=db, query_text=query_text,
                query_hash=hashlib.sha256(f"{qid}|{query_text}".encode()).hexdigest(),
            ))

        # Query type 3: Domain bridge
        # Domain A AND Domain B AND "mechanism"
        query_text = f"{domain_a} {domain_b} mechanism"
        qid = f"Q-{pair_id}-domain_bridge-{db}"
        queries.append(SearchQuery(
            query_id=qid, pair_id=pair_id, query_type="domain_bridge",
            database=db, query_text=query_text,
            query_hash=hashlib.sha256(f"{qid}|{query_text}".encode()).hexdigest(),
        ))

        # Query type 4: Mechanism transfer
        # "transfer" OR "apply" + Source A terms + Domain B
        if terms_a:
            query_text = f"transfer apply {' '.join(terms_a[:2])} {domain_b}"
            qid = f"Q-{pair_id}-mechanism_transfer-{db}"
            queries.append(SearchQuery(
                query_id=qid, pair_id=pair_id, query_type="mechanism_transfer",
                database=db, query_text=query_text,
                query_hash=hashlib.sha256(f"{qid}|{query_text}".encode()).hexdigest(),
            ))

    return queries


def freeze_queries(queries: List[SearchQuery]) -> dict:
    """Freeze all queries before execution. Returns manifest."""
    query_dicts = [q.to_dict() for q in queries]
    canonical = json.dumps(query_dicts, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    manifest_hash = hashlib.sha256(canonical.encode('utf-8')).hexdigest()

    return {
        "manifest_type": "QUERY_MANIFEST_V1",
        "query_count": len(queries),
        "manifest_hash": manifest_hash,
        "queries": query_dicts,
        "rule": "Queries are frozen BEFORE search execution. No post-hoc modification.",
    }
