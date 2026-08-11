# NORMALIZATION_APPROACHES — Phase 5.F Decision Document (frozen per CEO v3.4)

**Status:** decision document (analysis, not governance, not code). FROZEN.
**Location:** `evidence/observations/` (per CEO v3.1: observation layer, not constitutional layer).
**Phase:** 5.F (per CEO directive, post-Phase 5.E classification exercise; revised per CEO v3.3; frozen per CEO v3.4).

> The next cycle should be purely comparative. Do not build anything.
> Instead, evaluate three hypothetical approaches.
> The output should be a decision document, not code.
> — CEO directive, Phase 5.F (v3.2)

> I would soften one additional conclusion.
> You wrote: "The bottleneck is large enough to justify solving."
> I would instead write: "The bottleneck is large enough to justify
> investigating candidate solutions."
> That's a smaller claim, but a safer one.
> — CEO directive, Phase 5.F (v3.2)

> Instead of thinking in terms of three solutions, I would think
> in terms of three hypotheses. That subtle shift is important
> because it prevents the organization from treating an approach
> as inevitable.
>
> The word "unknown" is more accurate than "high" [for embeddings'
> expected gain] because the gain has not yet been measured.
>
> measurement ≠ explanation ≠ intervention. Right now you have
> measurements. You have some candidate explanations. You do not
> yet have sufficient evidence to justify intervention.
> — CEO directive, Phase 5.F (v3.3)

> I would add a fourth: H0 — no intervention. Its claim would be
> simple: "The present system is already sufficient, and the
> expected gain does not justify the constitutional risk."
> Without an H0, the entire framework implicitly assumes that
> intervention is inevitable. The existence of an explicit null
> hypothesis forces every future proposal to defeat the alternative
> of doing nothing.
>
> At that point, I would freeze the analytical phase completely
> and wait for an explicit Phase 6 authorization. The next step is
> no longer engineering. It is governance.
> — CEO directive, Phase 5.F (v3.4)

This document evaluates four **hypotheses** (H0 through H3) about
the normalization bottleneck identified in Phase 5.D and quantified
in Phase 5.E. It does NOT recommend a hypothesis. It does NOT
authorize implementation. It provides the comparative analysis the
CEO needs to decide whether ANY hypothesis (including H0, the null)
is worth pursuing.

### The four hypotheses (complete decision set)

| Hypothesis | Claim |
|---|---|
| **H0** | **No intervention is justified. The present system is sufficient; the expected gain does not justify the constitutional risk.** |
| H1 | Deterministic normalization captures most lost signal. |
| H2 | Ontology mapping captures additional signal beyond H1. |
| H3 | Semantic methods capture additional signal beyond H2. |

**H0 is the null hypothesis.** It is the default position unless a
future proposal defeats it. Without H0, the framework implicitly
assumes intervention is inevitable. With H0, every proposal must
prove it is better than doing nothing — not just better than the
status quo on the gain axis, but better when gain, risk, complexity,
maintenance, false-positive rate, and constitutional impact are all
weighed together.

The framing as hypotheses (not solutions) is deliberate. A solution
is something you build; a hypothesis is something you test. Until a
hypothesis is tested against real data AND defeats H0, it remains a
candidate explanation, not an intervention.

---

## Context (recap from Phase 5.E)

The convergence formula's Signal C measures `shared_components /
total_components`. Under the current exact-label matching:

| Metric | Value |
|---|---:|
| Total distinct component labels | 140 |
| Exact matches (realized) | 10 |
| Potential matches (unrealized) | 6 |
| signal_loss | 37.5% |
| Current score (battery × EV) | 1.2182 |
| Perfect normalization score | 1.3273 (+0.1091) |
| Upper bound (all shared) | 1.4000 (+0.1818) |

The bottleneck is large enough to **justify investigating candidate
solutions** (per CEO's softened framing). It is NOT yet proven large
enough to justify implementing any specific solution — that depends
on the cost, risk, and constitutional impact of each approach, which
this document evaluates.

---

## The three approaches

| Approach | Benefit | Risk | Status in this document |
|---|---|---|---|
| 1. Exact normalization rules | High | Low | Evaluated |
| 2. Controlled ontology mapping | Medium | Medium | Evaluated |
| 3. Semantic embeddings | Potentially high | High | Evaluated |

Each approach is evaluated across 5 dimensions:

1. **Implementation complexity** — how much code, how many dependencies,
   how much testing.
2. **Maintenance burden** — ongoing work to keep the approach useful
   as new sources are ingested.
3. **Reproducibility risk** — does the approach satisfy Law 7
   (historical permanence)? Can the same input produce byte-exact
   output across runs?
4. **Expected gain** — how much would the convergence score improve,
   based on the Phase 5.E classification?
5. **Constitutional risk** — does the approach violate any of the 8
   Laws, the anti-entropy rules, or the session-hardened principles?

---

## Approach 1 — Exact normalization rules

### Description

Apply deterministic string transformations to component labels before
matching. Examples:

- **Plural stripping:** `batteries` → `battery` (strip trailing 's'
  if the singular form exists as a label).
- **Abbreviation expansion:** `MOF` → `metal-organic framework` (via
  a hardcoded abbreviation map).
- **Case normalization:** already done (lowercase + strip).
- **Possessive stripping:** `battery's` → `battery`.

These are pure string functions — no ML, no external services, no
probabilistic matching. The rules are explicit, auditable, and
deterministic.

### Implementation complexity: LOW

- ~50-100 lines of Python in a new function (e.g.,
  `normalize_label(label) -> str`).
- A hardcoded abbreviation map (~10-20 entries, grounded in the
  actual corpus).
- Unit tests for each normalization rule.
- No external dependencies. No model files. No API calls.

### Maintenance burden: LOW

- The abbreviation map is small and stable (abbreviations don't
  change often).
- Plural-stripping rules are language-level (English), not
  domain-specific.
- New rules can be added as new normalization gaps are discovered,
  but each rule is independent and low-cost.
- The rules are visible in a single file — easy to audit.

### Reproducibility risk: LOW

- **Law 7 (historical permanence):** SATISFIED. The rules are
  deterministic functions. The same input always produces the same
  output, byte-exact, across runs.
- **Law 8 (verification standard):** SATISFIED. The rules are
  replayable — re-running the normalization on the same graph
  produces the same merged labels.
- No model drift, no version dependencies, no external state.

### Expected gain: MEDIUM

Based on Phase 5.E classification:

- **Plural stripping:** would resolve 0 currently-observed gaps (no
  singular/plural pairs both in graph). BUT would prevent future
  gaps when plural forms ARE ingested. Preventive, not corrective.
- **Abbreviation expansion:** would resolve 2 of the 6 potential
  matches (MOF/metal-organic-framework, BMS/battery-management-system).
- **Other rules:** minimal additional gain.

**Estimated gain:** +2 shared components → score from 1.2182 to
~1.2545 (+0.0363). This is ~33% of the perfect-normalization gain
(+0.1091).

The gain is modest because exact rules only catch the cases where
the normalization is mechanically derivable (plural, abbreviation).
They don't catch hypernyms (electrode ↔ anode) or compound labels.

### Constitutional risk: LOW

- **Law 1 (transformation, not object):** SATISFIED. Normalization
  is a transformation, not a new object type.
- **Law 7 (historical permanence):** SATISFIED. Deterministic.
- **Law 8 (verification):** SATISFIED. Replayable.
- **"Use the word 'engine' honestly" (ANTI_ENTROPY):** SATISFIED.
  This is a module (deterministic string functions), not an engine.
- **Principle #2 (fix the thing, don't loosen the check):** NEEDS
  CARE. Normalization rules "loosen" the exact-match check by design.
  The mitigation: rules must be explicit, auditable, and each rule
  must cite the specific gap it addresses (with a real example from
  the corpus). No speculative rules.
- **CONTRIBUTING.md principle #9 (downstream blast radius):** the
  normalization function would be applied at ingestion time, affecting
  every component label. Must be tested against all existing
  fixtures to ensure no regression.

### Summary for Approach 1

| Dimension | Rating | Notes |
|---|---|---|
| Implementation complexity | LOW | ~50-100 lines, no dependencies |
| Maintenance burden | LOW | Small abbreviation map, stable rules |
| Reproducibility risk | LOW | Deterministic, byte-exact |
| Expected gain | MEDIUM | +0.0363 (~33% of perfect normalization) |
| Constitutional risk | LOW | Satisfies Laws 1, 7, 8; needs careful principle #2 framing |

---

## Approach 2 — Controlled ontology mapping

### Description

Maintain a curated mapping file (YAML or JSON) that maps component
labels to canonical forms. Examples:

```yaml
# ontology/component_mappings.yaml
sorbent:
  canonical: sorbent
  aliases:
    - adsorbent
    - absorbent
electrode:
  canonical: electrode
  aliases:
    - anode
    - cathode
    - current collector
metal-organic framework:
  canonical: metal-organic framework
  aliases:
    - mof
    - mofs
    - metal organic frameworks
```

At ingestion time, each extracted component label is looked up in
the mapping. If it's an alias, it's replaced with the canonical form.
If not, the label is kept as-is.

The mapping is human-curated — a domain expert decides which labels
are aliases of which canonical forms.

### Implementation complexity: MEDIUM

- A mapping file (YAML, ~50-200 entries to be useful).
- A lookup function (`canonicalize(label) -> str`).
- A governance process for adding/removing mappings (who decides?
  what's the review cycle?).
- Unit tests for each mapping.
- Documentation of the curation criteria (what makes two labels
  "the same"?).

### Maintenance burden: MEDIUM

- The mapping file must grow as new sources are ingested and new
  vocabulary appears.
- Mappings can become stale (e.g., if a term's usage shifts in the
  literature).
- The curation process requires domain expertise — not purely
  mechanical.
- Risk of "mapping drift" — the file grows without pruning,
  accumulating edge cases.

### Reproducibility risk: LOW-MEDIUM

- **Law 7 (historical permanence):** SATISFIED IF the mapping file
  is versioned in git. The same mapping file + same input → same
  output, byte-exact.
- **Law 8 (verification):** SATISFIED IF the mapping is deterministic
  (no fuzzy matching, just exact alias lookup).
- The risk is governance, not technology: if the mapping file is
  edited without proper review, historical labels might be re-
  mapped, breaking replayability.

### Expected gain: MEDIUM

Based on Phase 5.E classification:

- **Hypernyms:** would resolve 1 of the 6 potential matches
  (sorbent/adsorbent). Debatable — are they truly the same?
- **Compound labels:** could resolve 3 of the 6 potential matches
  (the 3 compound labels containing shorter labels as words).
- **Abbreviations:** could also handle the 2 abbreviation gaps
  (same as Approach 1, if the mapping includes them).
- **Plurals:** could handle via mapping (battery ↔ batteries).

**Estimated gain:** +4 to +6 shared components → score from 1.2182
to ~1.29-1.33 (+0.07 to +0.11). This is ~65-100% of the perfect-
normalization gain.

The gain is higher than Approach 1 because the ontology can capture
semantic relationships (hypernyms, compounds) that exact rules can't.

### Constitutional risk: MEDIUM

- **Law 1 (transformation):** SATISFIED. Mapping is a transformation.
- **Law 7 (historical permanence):** SATISFIED IF versioned. Risk
  if the mapping file is edited without governance.
- **Law 8 (verification):** SATISFIED IF deterministic.
- **"Use the word 'engine' honestly":** SATISFIED. This is a
  module (lookup table), not an engine.
- **Principle #2 (fix the thing, don't loosen the check):** the
  mapping IS a loosening of exact-match. Each mapping entry must
  be justified by a real example from the corpus.
- **Principle #5 (match the label to the evidence):** the mapping
  makes subjective decisions about what's "the same." The curation
  process must document WHY each mapping is correct.
- **CONTRIBUTING.md principle #3 (one source of truth):** the
  mapping file becomes a new source of truth for "which labels are
  equivalent." Must be governed carefully.
- **Risk of dogma:** the CEO's Phase 5.E warning ("the system risks
  gradually converting measurements into dogma") applies. A curated
  ontology can become dogma if mappings are added without evidence.

### Summary for Approach 2

| Dimension | Rating | Notes |
|---|---|---|
| Implementation complexity | MEDIUM | Mapping file + lookup + governance process |
| Maintenance burden | MEDIUM | File grows, needs domain expertise |
| Reproducibility risk | LOW-MEDIUM | Versioned file → deterministic; governance risk |
| Expected gain | MEDIUM | +0.07 to +0.11 (~65-100% of perfect normalization) |
| Constitutional risk | MEDIUM | Subjective decisions; risk of dogma; needs governance |

---

## Approach 3 — Semantic embeddings

### Description

Use a pre-trained embedding model (word2vec, GloVe, sentence-
transformers, etc.) to compute vector representations of component
labels. Two labels are considered "the same" if their cosine
similarity exceeds a threshold (e.g., 0.85).

Example: `battery` and `batteries` would have cosine similarity
~0.95 (same stem). `sorbent` and `adsorbent` would have ~0.80
(related but not identical). `electrode` and `anode` would have
~0.75 (subtype relationship).

### Implementation complexity: HIGH

- A pre-trained embedding model (downloaded or loaded from a
  library like sentence-transformers).
- Vector computation for each label (at ingestion time).
- Similarity threshold tuning (what's the right cutoff?).
- Vector storage (or re-computation on each run).
- A model dependency in requirements.txt.
- Handling of multi-word labels (average embeddings? sentence
  embeddings?).
- Extensive testing to avoid false positives.

### Maintenance burden: HIGH

- Embedding models have versions. A model update can change the
  vectors, breaking reproducibility.
- The similarity threshold needs calibration as the corpus grows.
- New vocabulary (e.g., "metal-organic framework") may not be in
  the pre-trained model's vocabulary — requires fallback to
  subword embeddings or fine-tuning.
- The model file is large (100MB-1GB), affecting repo size and
  clone time.

### Reproducibility risk: HIGH

- **Law 7 (historical permanence):** VIOLATED unless the model is
  pinned to a specific version AND the model file is archived. Even
  then, model loading can have non-determinism (GPU vs CPU, library
  versions).
- **Law 8 (verification):** PARTIALLY VIOLATED. The matching is
  probabilistic (cosine similarity threshold), not deterministic.
  The same input might produce different matches if the model
  version changes.
- **Principle #1 (run it, don't reason about it):** the model's
  behavior is opaque — you can't inspect WHY two labels are
  matched, only that their cosine similarity is high.

### Expected gain: UNKNOWN (not measured)

Per CEO v3.3: "The word 'unknown' is more accurate than 'high' because
the gain has not yet been measured." The gain for H3 has NOT been
measured. Calling it "potentially high" overstated the evidence.

Based on Phase 5.E classification:

- Could potentially resolve some of the 123 "truly unique" labels
  if they are semantically related to existing labels.
- BUT: the 123 truly unique labels include many that are GENUINELY
  unique (e.g., "8 μm to 13 μm and 16 μm to 28 μm" — a wavelength
  range, not a component).
- The potential gain is UNVERIFIED. The +0.1091 perfect-
  normalization gain from Phase 5.E assumes ALL 6 potential matches
  are resolved — embeddings might resolve more, but might also
  introduce false positives that DECREASE the score.

**Estimated gain:** unknown. Could be +0.05 (if embeddings only
catch the same 6 gaps as exact rules + ontology). Could be +0.15+
(if embeddings catch semantic relationships humans didn't identify).
Could be NEGATIVE (if false positives merge labels that should stay
separate, reducing the discrimination delta).

### Constitutional risk: HIGH

- **Law 1 (transformation):** SATISFIED (embeddings are a
  transformation).
- **Law 7 (historical permanence):** VIOLATED. Model versions
  change. Reproducibility requires pinning the model AND the
  library versions AND the hardware (GPU vs CPU can produce
  different floating-point results).
- **Law 8 (verification):** VIOLATED. The matching is probabilistic,
  not deterministic. There is no "successful prediction, failed
  prediction, and replayable evidence" — only a cosine similarity
  score.
- **"Use the word 'engine' honestly":** VIOLATED. If we call this
  an "engine," we're lying. It's a probabilistic matcher, not a
  model with empirical validation. Per ANTI_ENTROPY: "Until a
  module satisfies all three [explicit model, empirical validation,
  reproducible results], it is a `module`, not an `engine`." This
  approach fails the reproducibility criterion.
- **Principle #2 (fix the thing, don't loosen the check):** VIOLATED.
  Embeddings dramatically loosen the exact-match check, with no
  way to audit WHY a match was made.
- **Principle #5 (match the label to the evidence):** VIOLATED.
  The "evidence" is a cosine similarity score, not a verifiable
  semantic relationship.
- **Principle #8 (no data, say no data):** at risk. Embeddings
  produce a number for every pair, even when there's no real
  relationship. The system might claim "these are the same" when
  it has no evidence.
- **The CEO's most important instruction (Phase 5.D):** "Do not
  interpret this as permission to build semantic matching." This
  approach IS semantic matching. It is the thing the CEO explicitly
  warned against until the evidence supports it.

### Summary for Approach 3

| Dimension | Rating | Notes |
|---|---|---|
| Implementation complexity | HIGH | Model dependency, threshold tuning, storage |
| Maintenance burden | HIGH | Model versions, threshold drift, vocabulary gaps |
| Reproducibility risk | HIGH | Violates Law 7; probabilistic, not deterministic |
| Expected gain | UNKNOWN (not measured) | Could be +0.05 to +0.15+; could be negative. Per CEO v3.3: "unknown" is more accurate than "high" |
| False-positive risk | HIGH | Cosine similarity threshold is opaque; no way to audit why a match was made |
| Constitutional risk | HIGH | Violates Laws 7, 8; violates CEO's explicit warning |

---

## Comparative summary

Per CEO v3.4, H0 (the null hypothesis: no intervention) is added to
the table. H0 is the DEFAULT — it is the position the system holds
unless a future proposal defeats it. The table now includes the
complete decision set: H0, H1, H2, H3.

| Dimension | **H0: No intervention** | H1: Exact normalization | H2: Controlled ontology | H3: Semantic embeddings |
|---|---|---|---|---|
| Implementation complexity | **None** (do nothing) | Low | Medium | High |
| Maintenance burden | **None** | Low | Medium | High |
| Reproducibility | **High** (no change) | High (deterministic) | Medium–High (versioned file) | Low (model versions drift) |
| Expected gain | **0** (current score stays at 1.2182) | Moderate (+0.0363, measured) | Moderate–High (+0.07 to +0.11, estimated) | **Unknown** (not measured; could be negative) |
| False-positive risk | **None** (no matching changes) | Low (rules are explicit) | Medium (subjective mapping decisions) | High (cosine similarity threshold is opaque) |
| Constitutional risk | **None** (no constitutional changes) | Low | Medium | High (violates Laws 7, 8 + CEO warning) |
| **CEO's "semantic matching" warning** | **Not applicable** (no intervention) | Not applicable | Not applicable | **DIRECTLY VIOLATES** |
| **Status** | **DEFAULT — the null hypothesis. Must be defeated by any proposal.** | Candidate — must defeat H0 | Candidate — must defeat H0 AND H1's gain | Candidate — must defeat H0 AND H1 AND H2 AND the CEO's explicit warning |

### What H0 means in practice

H0 is not "give up." H0 is "the present system is sufficient until a
proposal proves otherwise." Under H0:

- The parser stays frozen.
- The convergence formula stays unchanged.
- The CONVERGENCE.md prerequisite chain continues at step 5 of 7.
- The 2028 validation dates remain the path to real-world confirmation.
- The cumulative Phase 5 delta (+0.0182 for battery×EV) stands as
  a structural measurement, not a real-world convergence claim.

H0 is the honest default because the Phase 5.E ceiling analysis
showed the potential gain is +0.1091 — meaningful, but NOT yet proven
to justify the cost, risk, and constitutional impact of any specific
intervention. Until a proposal is tested AND defeats H0 on the full
axis (gain + risk + complexity + maintenance + false-positives +
constitutional impact), H0 holds.

### Key observations

1. **H0 is the default.** Every proposal (H1, H2, H3) must defeat it.
   "Defeating H0" means proving the proposal is better than doing
   nothing when ALL dimensions are weighed — not just the gain axis.

2. **H1 (exact normalization) is the safest candidate to test against
   H0.** Low complexity, low maintenance, high reproducibility, low
   false-positive risk, low constitutional risk. Its gain is modest
   (+0.0363) but real and verifiable. Whether +0.0363 defeats H0
   depends on whether the CEO judges the gain worth the (low)
   implementation cost and (low) constitutional risk.

3. **H2 (ontology mapping) has higher estimated gain but higher
   governance cost.** It could resolve 4-6 of the 6 potential
   matches (+0.07 to +0.11), but requires a curated mapping file
   with a governance process. The risk of "dogma" (the CEO's
   Phase 5.E warning) is real — mappings added without evidence
   become constitutional.

4. **H3 (semantic embeddings) has UNKNOWN gain and HIGH risk.** The
   gain has not been measured — it could be high, moderate, or
   negative (if false positives merge labels that should stay
   separate, reducing the discrimination delta). Per CEO v3.3:
   "unknown" is more accurate than "high" because the gain has
   not yet been measured. H3 also violates Law 7 (reproducibility),
   Law 8 (verification), and the CEO's explicit warning against
   semantic matching.

5. **The gain gap between hypotheses is not proportional to the
   risk gap.** H1 gives 33% of the perfect-normalization gain at
   LOW risk. H2 gives 65-100% at MEDIUM risk. H3 gives an UNKNOWN
   amount at HIGH risk. The marginal gain from H1 → H2 is +0.04 to
   +0.07. The marginal gain from H2 → H3 is unknown and carries
   the highest risk.

6. **The CEO's "semantic matching" warning applies specifically
   to H3.** H1 and H2 are deterministic string transformations — they
   are NOT semantic matching in the probabilistic sense. H3 IS
   semantic matching. The CEO's directive does NOT authorize H3
   regardless of the gain.

---

## Decision framework (for the CEO, not the coder)

This document does NOT recommend an approach. It provides the
comparative analysis the CEO needs to decide. The decision framework:

### If the CEO decides the bottleneck is NOT worth solving

- Continue with exact-label matching.
- Accept that the convergence score has saturated under the current
  strategy.
- Wait for the 2028 validation dates to execute CONVERGENCE.md's
  validation plan.
- No parser changes, no formula changes.

### If the CEO decides the bottleneck IS worth solving

- **Approach 1 (exact rules)** is the lowest-risk option. It gives
  a modest but verifiable gain. It can be implemented and tested
  without violating any constitutional rule. It is the natural
  first step if any approach is pursued.

- **Approach 2 (ontology mapping)** is a viable second step if
  Approach 1's gain is insufficient. It requires a governance
  process for the mapping file — each mapping must cite a real
  example from the corpus (per principle #5). The mapping file
  should be versioned and reviewed.

- **Approach 3 (embeddings)** should NOT be pursued until the CEO
  explicitly authorizes semantic matching AND the constitutional
  layer is updated to accommodate probabilistic matching (Law 7
  and Law 8 would need amendments). This is a constitutional
  change, not a technical one.

### What this document does NOT do

- It does NOT recommend an approach.
- It does NOT authorize implementation.
- It does NOT modify the parser, formula, ontology, or governance.
- It does NOT close F-039 (the saturation finding).
- It does NOT override the CEO's "do not build semantic matching"
  instruction.

### What this document DOES do

- It provides the comparative analysis the CEO requested.
- It estimates the 5 dimensions for each of the 3 approaches.
- It identifies which approach is lowest-risk (Approach 1).
- It identifies which approach is forbidden by current governance
  (Approach 3, per CEO's explicit warning).
- It gives the CEO the data to decide whether ANY approach is
  worth pursuing, and if so, which.

---

## The single most important distinction

Per the CEO's Phase 5.D instruction (still in force):

> The evidence currently supports only this statement:
>   Exact-label matching is the limiting factor.
> It does not support the statement:
>   Semantic matching is the correct solution.

Per CEO v3.2 (still in force):

> The evidence also supports this statement:
>   The bottleneck is large enough to justify investigating
>   candidate solutions.
> It does NOT support the statement:
>   The bottleneck is large enough to justify implementing any
>   specific solution.

Per CEO v3.3 (still in force), the separation is explicit:

```text
measurement      ≠ explanation      ≠ intervention
```

- **Measurement:** we HAVE this. Phase 5.D + 5.E quantified the gap
  (37.5% signal loss, +0.1091 potential gain). Phase 5.E classified
  the 140 labels. These are facts about the current state.

- **Explanation:** we HAVE candidate explanations. H0, H1, H2, H3
  are four hypotheses about whether and how the gap might be closed.
  H0 is the null — no intervention. H1, H2, H3 are candidate
  interventions. All four are candidate explanations, not verified
  theories.

- **Intervention:** we do NOT have sufficient evidence to justify
  intervention. No hypothesis has been tested against real data.
  No approach has been authorized. H0 holds as the default. The
  CEO's "do not build semantic matching" instruction (Phase 5.D)
  is still in force. The decision to intervene belongs to the CEO,
  not the coder.

### The phase structure (per CEO v3.4 — FROZEN)

```text
Phase 5.A  Measurement
Phase 5.B  Measurement
Phase 5.C  Measurement
Phase 5.D  Classification
Phase 5.E  Ceiling analysis
Phase 5.F  Comparative analysis (this document — FROZEN)
Phase 6    Decision phase (governance, not engineering)
```

Phase 6 is the **decision phase**. Per CEO v3.4: "At that point, I
would freeze the analytical phase completely and wait for an explicit
Phase 6 authorization. The next step is no longer engineering. It is
governance."

**The analytical phase is now FROZEN.** This document is the endpoint
of Phase 5. No further measurement, classification, ceiling analysis,
or comparative analysis is authorized without a new CEO directive.
The decision to intervene (or not) belongs to the CEO. Until that
decision is made, H0 holds as the default: the present system is
sufficient, and no intervention is justified.

---

## Implementation status

| Item | Status |
|---|---|
| Comparative analysis of 3 approaches | COMPLETE (this document) |
| Parser changes | NONE (forbidden) |
| Formula changes | NONE (forbidden) |
| Ontology changes | NONE (forbidden) |
| Governance changes | NONE (forbidden) |
| New code | NONE (this is a decision document, not code) |
| Phase 5.F status | COMPLETE. Decision document delivered. Awaiting CEO directive. |

The CEO now has:
1. The measurement (Phase 5.D + 5.E): the bottleneck is real and quantified.
2. The classification (Phase 5.E): 37.5% signal loss, +0.1091 potential gain.
3. The comparative analysis (Phase 5.F, this document): 3 approaches
   evaluated across 5 dimensions.

The next decision is the CEO's: whether to authorize investigating
a specific approach further, or to accept the current saturation
and wait for validation.
