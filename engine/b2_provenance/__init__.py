#!/usr/bin/env python3
"""b2_provenance — B2 provenance spine and generation null package.

The provenance spine is the foundation of the B2 causal chain:
    raw output → content-addressed blob → frozen parser → candidate(rank) →
    candidate SHA → derivation verification → append-only ledger → adjudication

The generation null is the fair baseline that produces candidates through
a different mechanism (concatenation, not transfer+generation) while
sharing the same provenance spine.
"""
from .content_addressed_storage import (
    compute_sha256,
    store_raw_output,
    retrieve_raw_output,
    verify_blob_integrity,
    blob_exists,
    list_all_blobs,
)
from .frozen_parser import (
    parse_candidates,
    get_candidate_by_rank,
    compute_candidate_sha256,
    verify_derivation,
    get_parser_sha256,
    get_parser_config_sha256,
    get_parser_version,
    PARSER_CONFIG,
)
from .provenance_ledger import (
    ProvenanceLedger,
    LEDGER_PATH,
    EVENT_TYPE_CANDIDATE_GENERATED,
    EVENT_TYPE_ADJUDICATION_RECORDED,
)
from .generation_null import (
    compute_universal_seed,
    compute_shared_entity,
    construct_candidate,
    generate_null_raw_output,
    generate_null_candidates,
    record_null_in_ledger,
    NullGenerationResult,
    NULL_CONFIG,
    verify_frozen_components,
)

__all__ = [
    # Content-addressed storage
    "compute_sha256",
    "store_raw_output",
    "retrieve_raw_output",
    "verify_blob_integrity",
    "blob_exists",
    "list_all_blobs",
    # Frozen parser
    "parse_candidates",
    "get_candidate_by_rank",
    "compute_candidate_sha256",
    "verify_derivation",
    "get_parser_sha256",
    "get_parser_config_sha256",
    "get_parser_version",
    "PARSER_CONFIG",
    # Provenance ledger
    "ProvenanceLedger",
    "LEDGER_PATH",
    "EVENT_TYPE_CANDIDATE_GENERATED",
    "EVENT_TYPE_ADJUDICATION_RECORDED",
    # Generation null
    "compute_universal_seed",
    "compute_shared_entity",
    "construct_candidate",
    "generate_null_raw_output",
    "generate_null_candidates",
    "record_null_in_ledger",
    "NullGenerationResult",
    "NULL_CONFIG",
]
