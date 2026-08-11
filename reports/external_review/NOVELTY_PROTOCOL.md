# Novelty Protocol

For each claimed discovery, the following chain must be completed with evidence at every step:

```
Claimed relationship
        ↓
Source A (full text)
        ↓
Source B (full text)
        ↓
Engine proposal (exact output from discover_shared_entities)
        ↓
Prior-art search (independent literature search)
        ↓
Independent expert review (domain expert, blinded)
        ↓
Novelty classification
```

## Evidence requirements

### Claimed relationship
- Record the exact bridge concept the engine is credited with discovering
- Record which gold discovery this corresponds to

### Source A
- Record the full input snippet
- Record all extracted entities from Source A
- Determine: is the bridge concept explicitly present in Source A?

### Source B
- Record the full input snippet
- Record all extracted entities from Source B
- Determine: is the bridge concept explicitly present in Source B?

### Engine proposal
- Record the exact output of `discover_shared_entities(lit_a_entities, lit_b_entities)`
- Determine: is the bridge concept in the shared entity set?
- If not in shared entities but in ambient entities, flag as AMBIENT_FALLBACK

### Prior-art search
- Search Google Scholar, PubMed, arXiv for the bridge concept in connection with both domains
- Record: was this connection published before the benchmark was constructed?
- Classify: NOVEL / PREVIOUSLY_KNOWN / PARTIAL_PRECEDENT / AMBIGUOUS / UNSUPPORTED

### Independent expert review
- Present the bridge concept and both sources to a domain expert
- Do NOT tell the expert which is AI-generated
- Ask: "Is this relationship genuinely non-obvious? Is it scientifically meaningful? Was it already known?"
- Record the expert's assessment

### Novelty classification
- Combine prior-art search + expert review
- Final classification: NOVEL / PREVIOUSLY_KNOWN / PARTIAL_PRECEDENT / AMBIGUOUS / UNSUPPORTED

## The engine's own generated explanation is not sufficient evidence

The engine may generate prose explaining why two domains are connected. This prose is NOT evidence of discovery. It is evidence of language generation capability.

Only independent verification (literature search + expert review) constitutes evidence of novelty.
