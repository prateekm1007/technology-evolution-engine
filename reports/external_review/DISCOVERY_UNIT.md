# Discovery Unit Definition

## The problem

The terms "entity", "relation", "mechanism", "hypothesis", "discovery", and "invention" are often used interchangeably in this repository's history. They must not be.

An independent evaluator must be able to answer: **What exactly did the engine discover that wasn't already present?**

## Definitions

### ENTITY
An extracted noun phrase from input text. Example: "calcium carbonate", "nanofiber membrane".

An entity is NOT a discovery. It is a recognition of something present in the input.

### RELATION
A subject-predicate-object triple extracted from input text. Example: "calcium carbonate → precipitates → via fungi".

A relation is NOT a discovery. It is a recognition of something stated in the input.

### MECHANISM
A causal explanation for why two domains are connected. Example: "Biomineralization connects mycelium research to calcium carbonate materials because fungi precipitate calcium carbonate through mineral precipitation processes."

A mechanism IS a candidate for discovery IF it is not explicitly stated in either input and is not trivially derivable from lexical overlap.

### HYPOTHESIS
A testable prediction derived from a proposed mechanism. Example: "If biomineralization is the bridge, then manipulating fungal growth conditions should affect calcium carbonate precipitation rates."

A hypothesis is NOT a discovery. It is a downstream product of a mechanism.

### DISCOVERY
A cross-domain connection (bridge concept + mechanism) that:
- Is NOT explicitly stated in either input
- Is NOT retrievable by lexical overlap alone
- Is supported by a plausible causal mechanism
- Is NOT already well-known in the literature
- Would be considered non-obvious by a domain expert

### INVENTION
A discovery that has been validated by:
- Independent replication
- Expert review
- Prior-art search confirming novelty
- Experimental or observational confirmation

An invention is the strongest claim. The repository does NOT currently claim invention.

## What the engine produces

The engine currently produces:
1. **Entities** (extracted from input via spaCy NLP)
2. **Shared entities** (entities appearing in both inputs — this is the "discovery proposal")
3. **Bridge matches** (checking if a shared entity matches a gold bridge via `_bridge_matches()`)

The engine does NOT currently produce:
- Explicit mechanisms (the `ProposalComposer` generates template-level text, not causal explanations)
- Testable hypotheses
- Novelty assertions backed by literature search

## What the evaluator should check

For each claimed discovery, the evaluator must determine:

1. **Is the bridge concept explicitly present in the input text?**
   - If YES → this is recognition, not discovery
   - If NO → continue

2. **Is the bridge concept in the shared entity set?**
   - If NO → this is ambient fallback, not proposal (DEFECT-001)
   - If YES → continue

3. **Does the match depend on token overlap?**
   - If YES → this is lexical matching, not semantic discovery
   - If NO → continue

4. **Is the connection already published?**
   - If YES → this is retrieval, not discovery
   - If NO → continue

5. **Is there a plausible mechanism?**
   - If NO → this is unsupported
   - If YES → this is a candidate discovery

Only if all five checks pass can the result be called a discovery.
