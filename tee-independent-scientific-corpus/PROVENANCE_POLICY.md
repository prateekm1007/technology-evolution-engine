# Provenance Policy

## Purpose

This document defines the provenance collection, verification, and preservation policy for the TEE Independent Scientific Corpus.

## Provenance Requirements

For every source record in the corpus, the following provenance information MUST be collected and preserved:

### Required Metadata Fields

1. **source_id**: Unique identifier assigned by the corpus custodian
2. **title**: Full title of the work
3. **authors**: Complete author list as provided by the source
4. **DOI**: Digital Object Identifier (if available)
5. **publisher**: Publishing entity
6. **publication_date**: Date of publication (YYYY-MM-DD or YYYY-MM or YYYY)
7. **source_uri**: URI where the source was acquired
8. **repository_uri**: Repository URI (if applicable)
9. **abstract**: Abstract text (if available)
10. **fulltext_uri**: URI to full-text content (where legally available)
11. **acquisition_timestamp**: ISO 8601 timestamp of acquisition
12. **provider**: Data provider (OpenAlex, Crossref, Semantic Scholar, OpenAIRE, etc.)
13. **version**: Version identifier (if applicable)
14. **sha256_hash**: SHA-256 hash of content
15. **license**: License or access information
16. **provenance**: Detailed provenance record

### Provenance Record Structure

Each provenance record must include:

```json
{
  "source_id": "...",
  "provider": "...",
  "query_parameters": {...},
  "acquisition_method": "...",
  "acquisition_timestamp": "YYYY-MM-DDTHH:MM:SSZ",
  "verification_status": "verified|unverified|partial",
  "verification_method": "...",
  "verification_timestamp": "YYYY-MM-DDTHH:MM:SSZ",
  "duplicate_check_performed": true/false,
  "retraction_check_performed": true/false,
  "retraction_status": "not_retracted|retracted|unknown",
  "metadata_completeness": {
    "field_name": "present|absent|partial"
  },
  "exclusion_reason": null or "machine_readable_reason"
}
```

## Provider Verification

Multiple providers MUST be used for provenance verification where possible:

1. **Primary Provider**: The source from which the record was initially acquired
2. **Secondary Provider(s)**: Independent verification from at least one additional provider when feasible

Discrepancies between providers must be recorded and adjudicated.

## Acquisition Logging

All acquisitions must be logged with:

- Timestamp (ISO 8601, UTC)
- Provider API endpoint or repository URI
- Query parameters used
- Response status
- Pagination/cursor information
- Rate limiting information (if applicable)
- Error handling records

## Content Hashing

Every acquired item must receive a SHA-256 hash:

- Hash computed on exact content received
- Hash stored in `corpus/hashes/`
- Hash included in metadata record
- Hash used for duplicate detection

## Duplicate Detection Protocol

The following duplicate checks MUST be performed:

1. **Exact content hashing**: Compare SHA-256 hashes
2. **DOI duplicate detection**: Identify records with identical DOI
3. **Bibliographic duplicate detection**: Compare title + authors + publication date
4. **Title similarity detection**: Fuzzy matching on titles (threshold documented)
5. **Near-duplicate detection**: Content similarity analysis

All detected duplicates must be recorded in `validation/duplicates.json` with:

- Duplicate type
- Affected source IDs
- Resolution decision (keep/discard/merge)
- Reason for decision

## Retraction and Correction Status

Where discoverable through provider APIs or independent checks:

- Retraction status must be checked
- Correction/amendment status must be noted
- Retracted sources must be flagged but NOT silently discarded
- Exclusion reason must be recorded if retracted sources are excluded

## Metadata Completeness Assessment

For each source, assess completeness of:

- Required fields (see above)
- Optional fields
- Provider-specific fields

Record completeness as:
- `present`: Field present and populated
- `absent`: Field not provided by source
- `partial`: Field present but incomplete

Do NOT fabricate missing metadata.

Explicitly record unavailable fields as `null` or with explicit marker.

## Exclusion Recording

Every exclusion MUST receive a machine-readable reason from this controlled vocabulary:

- `DUPLICATE_EXACT`: Exact duplicate by content hash
- `DUPLICATE_DOI`: Duplicate DOI
- `DUPLICATE_BIBLIOGRAPHIC`: Bibliographic duplicate
- `RETRACTED`: Source retracted
- `METADATA_INCOMPLETE`: Critical metadata missing
- `ACCESS_RESTRICTED`: No legal access to content
- `DOMAIN_MISMATCH`: Outside target domain scope
- `PUBLICATION_DATE_AFTER_CUTOFF`: Published after temporal cutoff
- `NON_SCHOLARLY`: Not a scholarly source
- `PROVENANCE_UNVERIFIABLE`: Cannot verify provenance

## Provenance Storage

Provenance records stored in:

- Individual metadata files: `corpus/metadata/{source_id}.json`
- Aggregated provenance logs: `provenance/acquisition_log_{date}.json`
- Validation reports: `validation/`

## Audit Trail

An immutable audit trail must be maintained:

- All acquisitions logged
- All exclusions logged with reasons
- All modifications logged (pre-freeze only)
- Post-freeze: NO modifications allowed

## Cryptographic Commitment

After corpus freeze:

1. Compute SHA-256 of entire corpus directory
2. Compute SHA-256 of manifest
3. Store hashes in `custodian/seals/`
4. Include in final custodian seal

## Verification Procedures

Independent verification should confirm:

1. All source records have complete provenance
2. Provider claims can be verified
3. Acquisition timestamps are consistent
4. Content hashes match stored values
5. Duplicate detection was performed correctly
6. Exclusion reasons are valid and documented

---

*Provenance is not optional. A source without verifiable provenance is not part of the scientific record.*
