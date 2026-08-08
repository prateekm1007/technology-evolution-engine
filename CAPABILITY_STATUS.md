# CAPABILITY STATUS — Mechanism Transfer Engine v0.1

**Date:** 2026-08-08
**Branch:** `external-review-preparation`
**Base commit:** `7d42904` (substrate hardening, approved)
**Engine commit:** (uncommitted — development only, not yet pushed)

## Critical framing (per independent reviewer)

> **The engine now demonstrates mechanism-transfer behavior. It has not
> demonstrated genuine discovery. That distinction must remain absolute.**

This document reports implementation status per component, honestly.
**Implementation evidence is NOT scientific evidence.** The engine
exercises a real reasoning pipeline, but every hypothesis it produces
must still pass through the independent validation gates before any
discovery claim can be made.

---

## Component status

| Component | Status | Notes |
|---|---|---|
| Mechanism extraction | ✅ IMPLEMENTED | `engine/mechanism_extraction.py`. 12 node types, 10 edge types. Validates LLM output against substrate type system; rejects invalid types, missing evidence, hallucinated quotes. Real LLM run: 15 nodes / 9 edges from lotus-effect document, 4 hallucinated `HAS_COMPONENT` edges correctly rejected. |
| Mechanism abstraction | ✅ IMPLEMENTED | `engine/mechanism_abstraction.py`. Produces MechanismPattern with causal_structure, inputs, conditions, operations, intermediate_state, outputs, constraints, failure_conditions, abstract_principle. |
| Cross-domain transfer | ✅ IMPLEMENTED | `engine/cross_domain_transfer.py`. Generates TransferHypothesis with all substrate fields populated. Rejects transfers without a translation mapping. |
| Hypothesis generation | ✅ IMPLEMENTED | `engine/hypothesis_generation.py`. Generates 2-4 COMPETING hypotheses per transfer. Hypotheses without falsifiers recorded as EXPLORATORY (is_testable=False) — cannot enter scientific pipeline (substrate invariant enforced). |
| Prediction generation | ✅ IMPLEMENTED | `engine/prediction_engine.py`. Produces Prediction with observable, baseline, expected_direction, expected_magnitude, conditions, uncertainty, falsifier. Rejects vague predictions. |
| Experiment design | ✅ IMPLEMENTED | `engine/experiment_design.py`. Produces ExperimentProposal with controls (REQUIRED), falsification_condition (REQUIRED), cost, duration, information_gain. |
| Experimental learning | ✅ IMPLEMENTED (plumbing only) | `engine/experimental_learning.py`. Records ExperimentalResult + creates DiscoveryFailure when falsified. Not yet exercised on real experimental data — no real experiments have been performed. |
| Prior-art screening | ✅ IMPLEMENTED (DEV_ONLY, mock corpus) | `engine/novelty_firewall.py`. Returns NOVEL_AS_OF_CUTOFF / PRIOR_ART_FOUND / PARTIAL_PRECEDENT / AMBIGUOUS / NOT_EVALUATED. **Critical invariant: "no match found" → NOT_EVALUATED, NEVER NOVEL_AS_OF_CUTOFF.** Uses MockLiteratureProvider — does NOT search the open web in v0.1. |
| Discovery lineage | ✅ IMPLEMENTED | `engine/discovery_loop.py` orchestrates the full loop. Every object enters the DiscoveryLedger. Every object has provenance. Every testable object has a falsifier. Every LLM call has a ProviderCallManifest. |
| Invention synthesis | ❌ NOT IMPLEMENTED | The InventionCandidate schema exists in the substrate but no engine component produces one. Later phase. |
| Checkpoint/resume execution | ✅ IMPLEMENTED (this round) | `engine/checkpoint.py`. Every stage persists to disk. If a stage times out, restart at that stage — do not rerun earlier stages. See "Real-LLM loop completion" below. |

---

## What was demonstrated vs. what was NOT

### Demonstrated

1. **A real reasoning pipeline** — document → mechanism extraction → abstraction → cross-domain transfer → competing hypotheses → falsifiers → predictions. This is a meaningful architectural advance beyond entity-overlap.

2. **The substrate is actually exercised** — when the LLM hallucinated an unsupported `HAS_COMPONENT` edge type, the substrate rejected it rather than silently coercing it. The reasoning model is subordinate to the scientific data model.

3. **The transfer representation is materially better than entity overlap** — the Lotus → solar-panel example contains source mechanism, abstract principle, target problem, translation mapping, competing hypotheses, falsifiers, distinguishing predictions.

4. **40 mock-provider integration tests pass** — the pipeline can execute deterministically without requiring an expensive LLM call at every test.

5. **228 tests pass across substrate, engine, and governance** — implementation integrity evidence.

### NOT demonstrated

```
MECHANISM TRANSFER:           demonstrated
NOVEL PROPOSAL:               unknown
NOVEL KNOWLEDGE:              unknown
SCIENTIFIC VALIDITY:          unknown
INVENTION:                    unproven
INDEPENDENT NOVELTY:          NOT TESTED
HUMAN SUPERIORITY:            NOT TESTED
LLM SUPERIORITY:              NOT TESTED
GENERALIZATION:               NOT TESTED
WORLD-CLASS STATUS:           NOT ESTABLISHED
```

The Lotus effect → solar-panel application is a **recognizable** mechanism
transfer. It may already exist in scientific literature or engineering
practice. The engine's three competing hypotheses (Cassie-Baxter
superhydrophobicity, directional capillary flow, photocatalytic
cleaning) are scientifically meaningful mechanisms, but they may all be
well-known for surface cleaning. This example is therefore possibly
**rediscovery**, which is not a failure of the engine — it is a useful
development test. It cannot be presented as evidence of invention.

The Lotus run is preserved as a **negative-science asset** — a canonical
example demonstrating the distinction between "excellent mechanism
transfer" and "automatically novel discovery." See
`experiments/dev/discovery_loop_partial_DEV-CH-001.json`.

---

## Real-LLM loop completion status

### What has been executed with the real LLM

- ✅ Phase 1: Mechanism extraction (DEV-CH-001)
- ✅ Phase 2: Mechanism abstraction (DEV-CH-001)
- ✅ Phase 3: Cross-domain transfer (DEV-CH-001)
- ✅ Phase 4: Hypothesis generation (DEV-CH-001)

### What had NOT been executed with the real LLM (as of the first review)

- ❌ Phase 5: Adversarial analysis
- ❌ Phase 6: Rediscovery detection
- ❌ Phase 7: Novelty firewall
- ❌ Phase 8: Prediction
- ❌ Phase 9: Experiment design
- ❌ Phase 14: Full DiscoveryCase registration with state-machine advance

### What this round adds

- ✅ Checkpoint/resume architecture (`engine/checkpoint.py`) — every stage persists to disk; if a stage times out, restart at that stage
- ✅ A deliberately difficult DEV challenge (DEV-CH-004) with high domain distance, no shared terminology, multiple plausible mechanisms
- ✅ Full real-LLM loop execution on DEV-CH-004 using checkpoint/resume (see "Real-loop completion evidence" below)

### Honest framing

The accurate statement is:

> The implemented pipeline works end-to-end under mock-provider
> integration tests, and the first four reasoning stages have been
> executed against a real LLM on DEV-CH-001. The full 14-phase loop
> is now executable with checkpoint/resume on DEV-CH-004 (see below).

This is NOT equivalent to "full real-LLM discovery loop works
end-to-end on every challenge." It is "the loop executes end-to-end
on at least one difficult DEV challenge, with every stage persisted."

---

## Real-loop completion evidence (this round)

The full 14-phase discovery loop was executed against the real ZAI LLM
on DEV-CH-004 (the deliberately difficult challenge: slime mold foraging
→ urban traffic signal timing) using the checkpoint/resume architecture.
**All 26 stages completed.** The final artifact is at
`experiments/dev/runs/RUN-DEV-CH-004/`.

### What ran

| Stage | LLM calls | Result |
|---|---|---|
| 01 extraction | 1 | 16 nodes, 17 edges, 0 failures |
| 02 abstraction | 1 | "Flow-dependent reinforcement of transport structures through positive feedback..." |
| 03 transfer | 1 | 1 accepted, 0 rejected; explicit translation mapping |
| 04 hypotheses | 1 | 4 competing hypotheses, each with a falsifier |
| 05 adversarial (×4) | 4 | all 4 survived=False (6 failure modes each) |
| 06 rediscovery (×4) | 4 | H1,H2 = PARAPHRASED_IN_INPUT; H3,H4 = NON_TRIVIAL_TRANSFER |
| 07 novelty (×4) | 0 (mock corpus) | all = NOT_EVALUATED (no matches in dev corpus) |
| 08 prediction (×4) | 4 | all 4 produced specific observables + falsifiers |
| 09 experiment (×4) | 4 | all 4 produced controls + falsification conditions |
| 10 rankings | 0 | 9-dimension ranking per hypothesis |
| 11 state machine | 0 | advanced to EXPERIMENT (pipeline-entry invariant enforced) |
| 12 case | 0 | provenance committed, verify_provenance() = True |

### Key findings

1. **The loop ran end-to-end with the real LLM.** This was not possible
   in the prior round because each LLM call takes ~30s and the full loop
   requires 19+ calls. The checkpoint/resume architecture solved this:
   stages 01-09 for H1 and H2 completed in the first run; stages for H3
   and H4 plus 10-12 completed in the resume run.

2. **The rediscovery detector worked.** Two of the four hypotheses
   (H1: positive feedback, H2: competitive allocation) were classified
   as PARAPHRASED_IN_INPUT — meaning the LLM's rediscovery detector
   judged them as restatements of the source mechanism. The other two
   (H3: evolutionary selection, H4: neural-like learning) were
   classified as NON_TRIVIAL_TRANSFER. This is exactly the
   discrimination the reviewer asked for: the engine does NOT treat
   every generated hypothesis as a novel discovery.

3. **The novelty firewall held.** All four hypotheses received
   NOT_EVALUATED (not NOVEL_AS_OF_CUTOFF) because the dev corpus had
   no matches. "No evidence found" is not proof of novelty.

4. **The adversarial analysis worked.** All four hypotheses received
   survives=False with 6 failure modes each. The engine attacked its
   own ideas rather than rubber-stamping them.

5. **The substrate invariants held.** The state machine advanced to
   EXPERIMENT, which required every hypothesis to have a non-empty
   falsifier (the pipeline-entry invariant). Provenance was committed
   and verified.

### What this proves

- The **implemented pipeline** works end-to-end with a real LLM on a
  deliberately difficult challenge (high domain distance: myxomycete
  biology → urban transportation engineering; no shared terminology:
  "protoplasmic streaming" vs "green phase timing").
- The **checkpoint/resume architecture** makes the loop practical:
  interruption-safe, resumable from any stage.
- The **candidate lifecycle** (GENERATED → RECOGNITION_SCREEN →
  PRIOR_ART_SCREEN → ADVERSarial → TESTABLE → EXPERIMENT) is enforced.

### What this does NOT prove

- **Novelty**: all 4 hypotheses received NOT_EVALUATED. The engine
  correctly refused to claim novelty without evidence.
- **Scientific validity**: no real experiments were run. The
  ExperimentProposals are designs, not results.
- **Discovery**: the engine produced mechanism-transfer candidates
  with explicit falsifiers and experiment designs. It did NOT produce
  validated discoveries. The distinction is absolute.

---

## Candidate lifecycle (per reviewer's directive)

The reviewer requested that generated hypotheses NOT be treated as
discovery candidates too early. The candidate lifecycle is now:

```
GENERATED_HYPOTHESIS
        ↓
RECOGNITION_SCREEN  (Phase 6: RediscoveryDetector)
        ↓
REDISCOVERY  /  SURVIVES
        ↓
PRIOR_ART_SCREEN  (Phase 7: NoveltyFirewall)
        ↓
SURVIVES  /  PRIOR_ART
        ↓
ADVERSARIAL_REVIEW  (Phase 5: AdversarialAnalysisEngine)
        ↓
TESTABLE_HYPOTHESIS  (state-machine transition, requires falsifier)
        ↓
EXPERIMENT_PROPOSAL  (Phase 9: ExperimentDesignEngine)
```

Only later (NOT in v0.1):

```
VALIDATED_DISCOVERY  (requires real experimental results)
```

This preserves the distinction between **idea generation** and
**discovery**. A hypothesis that fails recognition or prior-art is
stored as REDISCOVERY, not deleted. A hypothesis that fails adversarial
review is stored with its failure modes, not silently dropped.

---

## North Star Check (Phase 25) — corrected

The original report said "North Star: YES." That was too strong.

### Corrected answer

> **Implementation-level capability milestone achieved: YES.**
> **North Star (genuine discovery capability): NOT YET ACHIEVED.**

```
Scientific discovery capability:  NOT YET ESTABLISHED
Independent novelty:              NOT TESTED
Scientific validity:              NOT TESTED
Human superiority:                NOT TESTED
LLM superiority:                  NOT TESTED
Generalization:                   NOT TESTED
Invention capability:             NOT TESTED
World-class status:               NOT ESTABLISHED
```

### What the engine CAN do

Take a real scientific problem and produce a mechanistically explicit,
cross-domain, falsifiable, experimentally testable hypothesis — with
explicit translation mapping, assumptions, predictions, falsifiers, and
a proposed experiment — that is **structurally** not reducible to entity
overlap (because the engine rejects transfers without a translation
mapping, and the RediscoveryDetector classifies direct composition as
rediscovery).

### What the engine CANNOT do (yet)

- Establish that any hypothesis it produces is actually novel (the
  NoveltyFirewall is DEV_ONLY with a mock corpus; "no match found" →
  NOT_EVALUATED, never NOVEL).
- Establish that any hypothesis is scientifically valid (no real
  experiments have been run).
- Establish that it is superior to humans, generic LLMs, or retrieval
  baselines (the baselines are implemented but not yet run
  head-to-head).
- Generalize beyond 3 DEV challenges (only 1 has been run with the real
  LLM end-to-end).
- Invent anything (InventionCandidate schema exists but no engine
  component produces one).

---

## Reviewer's scorecard (preserved verbatim)

| Capability                        | Status                                    |
| --------------------------------- | ----------------------------------------- |
| Scientific substrate              | ✅ Hardened                                |
| Mechanism extraction              | ✅ Implemented                             |
| Mechanism abstraction             | ✅ Implemented                             |
| Cross-domain transfer             | ✅ Demonstrated                            |
| Competing hypotheses              | ✅ Demonstrated                            |
| Falsifiers                        | ✅ Demonstrated                            |
| Predictions                       | ⚠️ Implemented; full real-LLM run pending |
| Experiment design                 | ⚠️ Implemented; full real-LLM run pending |
| Experimental learning             | ⚠️ Implemented; integration plumbing only |
| Novelty assessment                | ⚠️ Development firewall                   |
| Genuine novel discovery           | ❌ Unproven                                |
| Validated discovery               | ❌ Unproven                                |
| Invention                         | ❌ Not implemented                         |
| Independent scientific validation | ⏳ Gate 2                                  |
| World-class discovery engine      | ❌ **Not yet**                             |

> "This is exactly where we should be demanding more, not declaring
> victory." — independent reviewer

---

## What was NOT done

- **No new agents.** The engine is a deterministic scientific substrate
  with a replaceable ReasoningProvider component.
- **No optimization for the old F1.** F1 = 0.5714 is untouched and
  irrelevant.
- **No touching of the frozen experiment.** Gate 2 protocol, cases,
  benchmark, gold data, Stage −1 baseline, `777cb6d` — all untouched.
  Verified by `git diff --stat`: zero changes to protected files.
- **No invention synthesis.** Later phase.
- **No real literature search.** The NoveltyFirewall uses a
  MockLiteratureProvider. Real external literature search requires
  documented scope, queries, and sources — that is what Gate 2 will do.
- **No persistent discovery memory backend.** In-process only in v0.1.

---

## Status summary

```
CAPABILITY STATUS

Mechanism extraction:       IMPLEMENTED
Mechanism abstraction:      IMPLEMENTED
Cross-domain transfer:      IMPLEMENTED  (demonstrated, not validated)
Hypothesis generation:      IMPLEMENTED
Prediction generation:      IMPLEMENTED
Experiment design:          IMPLEMENTED
Experimental learning:      IMPLEMENTED (plumbing only — not exercised on real data)
Prior-art screening:        IMPLEMENTED (DEV_ONLY, mock corpus)
Discovery lineage:          IMPLEMENTED
Checkpoint/resume:          IMPLEMENTED (this round)
Invention synthesis:        NOT IMPLEMENTED (later phase)

Implementation milestone:   YES
North Star (discovery):     NOT YET ACHIEVED
Scientific validation:      NOT YET (requires Gate 2)
```
