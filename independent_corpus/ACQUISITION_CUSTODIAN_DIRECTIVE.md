# Independent Corpus Acquisition — Custodian Directive v1.1

## Status

CORPUS ACQUISITION READY. No definitive benchmark is authorized by this document.

## Custodian role

The custodian shall acquire a broad scientific source pool without using TEE outputs, TEE rankings, TEE prompts, candidate hypotheses, or benchmark performance.

"Independent" means independent of TEE-driven selection. It does not mean that OpenAlex and Semantic Scholar constitute independent scientific realities; they are independent provider/corroboration channels over overlapping scholarly literature. Their provenance role must remain explicit.

## Acquisition universe

Primary sampling universe: OpenAlex.

Independent metadata/citation cross-check: Semantic Scholar.

No source-pair search, cross-domain bridge query, mechanism query, hypothesis query, or TEE-derived query is permitted during acquisition.

## Required sampling manifest

Before acquisition begins, freeze:

- source providers
- provider API versions/endpoints
- publication cutoff
- inclusion/exclusion rules
- external random seed
- pagination/sampling method
- requested pool size
- domain policy
- full-text policy
- license policy
- prior-exposure evidence universe
- software version / commit

The manifest hash must be recorded before sampling starts.

## Acquisition target

Acquire substantially more than the eventual N>=100 benchmark requirement. Target 2,000–5,000 candidate source records, subject to API limits, legal access, and corpus availability.

Do not pad the pool with synthetic or substitute records.

## Required source record

Each eligible source must retain:

- source_id
- provider
- provider_record_id
- title
- authors
- publication_date
- DOI where available
- source_uri
- full_text_uri where available
- publisher/repository
- license/access metadata
- domain metadata
- acquisition timestamp
- content SHA-256
- metadata SHA-256
- provenance metadata

## Cross-check

Semantic Scholar may corroborate DOI/title/date and bibliographic identity. A failed cross-check is a FLAGGED state, not silent deletion.

The pipeline must not treat provider agreement as proof that a scientific claim is true.

## Eligibility states

ELIGIBLE
FLAGGED
REJECTED
UNDETERMINABLE

Every exclusion/flag must retain an auditable reason code.

## TEE prior exposure

Exposure results must use the finite-evidence-universe semantics:

UNSEEN = no exposure detected within checked locations.

POSSIBLY_SEEN = evidence suggests possible prior exposure, but is inconclusive.

KNOWN_SEEN = direct prior exposure detected.

The result must list checked_locations / evidence universe. It must never claim that TEE has "never encountered" a source.

## No benchmark construction yet

The acquisition stage must NOT:

- select source pairs for discovery problems
- generate answer keys
- generate hypotheses
- run TEE
- score TEE
- rank sources by TEE usefulness
- search for cross-domain connections
- construct the N>=100 benchmark

## Aggregate report

Anything exposed to TEE before benchmark sealing must contain aggregate statistics only. No titles, abstracts, source text, identifiers that trivially recover source content, or custodian-only provenance records.

## Legal / licensing

Record source licensing and access conditions. Full text is usable for the benchmark only when the custodian has an appropriate lawful basis to use it for the intended evaluation. A metadata API result does not automatically grant rights to redistribute full text.

Semantic Scholar's API/data use is governed by its published license terms; the custodian must comply with those terms rather than assuming API availability implies unrestricted redistribution. 

## Stop condition

After the eligible source pool is acquired and audited, STOP.

The custodian then reviews the pool for independence, domain coverage, duplicates, exposure, and contamination before constructing any benchmark.

No TEE execution is permitted during acquisition.
