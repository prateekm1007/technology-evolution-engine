# OPEN_QUESTIONS

**Status:** Phase 15 Deliverable 5.
**Location:** repo root.
**Phase:** 15.

> Questions only. No answers.
> — CEO directive, Phase 15

This document records the open questions that the reachability
engine architecture raises but does not resolve. Per the CEO's
directive, this document asks — it does not answer. Each question
is tagged with the deliverable or finding that produced it.

Answering these questions is the work of future phases. Recording
them now prevents them from being forgotten.

---

## Questions about the five classes

Q-001 [PROCESS_CLASSIFIER.md]
Are the five classes (Discovery, Emergence, Scaling, Coordination,
Recombination) exhaustive? Or does a sixth class exist that the
current event registries do not reveal?

Q-002 [PROCESS_CLASSIFIER.md]
The Discovery class is absent from all current event registries
(because the registries begin at commercialization, not at
discovery). How would a Discovery-class backtest be constructed?
What would the event registry look like?

Q-003 [PROCESS_CLASSIFIER.md]
Some events fit multiple classes (e.g., Emergence + Recombination).
The dominance rule says "the class whose absence would have
prevented the event dominates." Is this rule testable, or is it
an interpretation?

Q-004 [PROCESS_CLASSIFIER.md]
Can a single event transition between classes over time? For
example, an event that begins as Discovery (scientific result),
becomes Emergence (capability rises), and ends as Recombination
(combination realized). If so, how does the classifier handle
temporal evolution?

Q-005 [PROCESS_CLASSIFIER.md]
Is "regulatory change" a distinct class from Coordination? The
current taxonomy folds regulatory approval into Coordination
(MECH-C002), but regulatory events (spectrum auctions, drug
approvals) have different dynamics than standards-body consensus.
Should they be a sixth class?

---

## Questions about mechanisms

Q-006 [MECHANISM_REGISTRY_V2.md]
The frozen formula is an instrument for MECH-E001 + MECH-R001
+ MECH-R002 (the Emergence + Recombination mechanisms). What
instruments would detect the other 5 mechanisms?

Q-007 [MECHANISM_REGISTRY_V2.md]
MECH-E002 (acceleration) is cataloged but untested (H2 from
Phase 14R). What would a test of MECH-E002 look like? What
formula would detect acceleration, and how would it be compared
to the velocity-based frozen formula?

Q-008 [MECHANISM_REGISTRY_V2.md]
Are the 8 mechanisms exhaustive? Or do more mechanisms exist
within each class? For example, within Scaling, is "market
expansion" (more customers) the same mechanism as "cost reduction"
(cheaper production), or are they different?

Q-009 [MECHANISM_REGISTRY_V2.md]
Can two mechanisms fire simultaneously and produce the same
event? If so, how does the reachability engine attribute the
event to one mechanism vs the other?

Q-010 [MECHANISM_REGISTRY_V2.md]
The dominance rule for overlapping mechanisms (Section:
Mechanism overlap and dominance) says "the class whose absence
would have prevented the event dominates." Is this empirically
testable, or is it a definition?

---

## Questions about state variables

Q-011 [STATE_SPACE.md]
Are the eight state dimensions exhaustive? What state variable
would a ninth dimension cover if one were needed?

Q-012 [STATE_SPACE.md]
Three dimensions (institutional_state, regulatory_state,
coordination_state) are domain-specific. A formula using them
would break transferability (M4). Is there a way to abstract
these dimensions to be transferable without losing their
specificity?

Q-013 [STATE_SPACE.md]
The frozen formula uses only capability_state (as TRL). If a
new formula used capability_state + economic_state + coordination_state,
would the three dimensions be independent, or would they be
correlated (as cost_bonus was correlated with velocity in the
Phase 12 ablation)?

Q-014 [STATE_SPACE.md]
How would the eight dimensions be combined? Multiplicatively
(like the frozen formula's velocity × adjacency)? Additively?
Through a more complex function (e.g., a neural network)?
What are the trade-offs of each?

Q-015 [STATE_SPACE.md]
Six of eight dimensions are NOT IMPLEMENTED (only capability_state
and partially manufacturing_state have data). What is the data
collection effort required to implement the others? Which are
feasible, and which are infeasible?

---

## Questions about the classifier

Q-016 [PROCESS_CLASSIFIER.md, REACHABILITY_CONSTITUTION.md Rule 1]
The classifier is a hard gate: no formula runs until the class
is identified. But what does the classifier LOOK like? Is it a
decision tree? A set of rules? A learned model? A human judgment?

Q-017 [PROCESS_CLASSIFIER.md]
Can the classifier be automated, or does it require human
judgment? If automated, what features would it use? If human,
what is the protocol for resolving disagreements?

Q-018 [PROCESS_CLASSIFIER.md]
What happens when the classifier assigns the wrong class? The
wrong formula runs, producing wrong predictions. How is this
detected? Through the backtest (low precision)? Through the
boundary registry (the event fits a known pattern of the wrong
class)?

Q-019 [PROCESS_CLASSIFIER.md]
Is classification binary (an event IS or IS NOT a class) or
graded (an event is 70% Emergence, 30% Recombination)? If
graded, how are mixed-class events handled?

---

## Questions about the boundary

Q-020 [BOUNDARY_THEOREM.md]
The boundary theorem states where the frozen formula applies.
But the boundary itself has a boundary — the 5 patterns
(BOUNDARY_REGISTRY.md) are cataloged from 2 domains. Do these
patterns hold in aviation, pharmaceuticals, and other domains?
Or do new domains reveal new patterns?

Q-021 [BOUNDARY_THEOREM.md]
The boundary theorem says the frozen formula "detects Emergence
and Recombination in monotonic-TRL domains." Is "monotonic-TRL"
a property of the DOMAIN or of the CAPABILITY? If it's a property
of the capability, can a single domain have both monotonic and
non-monotonic capabilities (and thus partial formula applicability)?

Q-022 [BOUNDARY_THEOREM.md]
The 2-of-4 cross-domain threshold (PHASE_14_ADVANCEMENT_CRITERIA.md)
was a proposal, not a pre-registered criterion (EP-6 violation).
What is the right threshold for the reachability engine? Should
it be per-class (e.g., "Emergence instrument must achieve
significance on Emergence events") or per-domain?

Q-023 [BOUNDARY_THEOREM.md]
The frozen formula's boundary is stated in terms of process
classes and TRL properties. But the boundary itself was discovered
through failure (Phase 14 stress tests). Can boundaries be
discovered without failure? Or is failure the only reliable
boundary-discovery mechanism?

---

## Questions about the north star

Q-024 [LESSONS_LEARNED.md, REACHABILITY_CONSTITUTION.md]
The north star is "understand how possibilities become reachable."
How is this measured? What would a "reachability estimate" look
like? Is it a probability (0-1)? A ranking? A classification?

Q-025 [LESSONS_LEARNED.md]
The frozen formula estimates susceptibility for one mechanism
(Emergence + Recombination). The reachability engine would
estimate reachability across multiple mechanisms. How are
multi-mechanism estimates combined? Are they additive
(more mechanisms = more reachable)? Multiplicative? Maximum?

Q-026 [LESSONS_LEARNED.md]
The CEO's reframing: "The north star is not predict inventions.
It is understand how possibilities become reachable." Is
"understand" measurable? Or is it interpretive (like the
self-graded explanatory depth that EP-5 retired)?

Q-027 [LESSONS_LEARNED.md]
Was the project a success? By the original north star
("predict inventions"), no — 0/4 domains survived. By the
refined north star ("understand reachability"), partially —
one mechanism was identified. By the meta-goal ("build a
system that can identify its own boundaries"), yes. Which
goal should future phases prioritize?

---

## Questions about evidence and governance

Q-028 [EVIDENCE_STANDARDS.md, REACHABILITY_CONSTITUTION.md]
The EP rules (EP-1 to EP-12) were created AFTER violations
occurred. They are remedial, not preventive. How would a future
project adopt them from the start? What changes in workflow
would be required?

Q-029 [EVIDENCE_FALSIFIERS.md]
The falsifier tracker (FEC-001 through FEC-005) records
falsifiers for existing claims. But the reachability engine
introduces new claims (the 5 classes, the 8 mechanisms, the
8 state dimensions). Each needs a falsifier. What are they?

Q-030 [FAILURES.md]
The failure taxonomy (F-001 through F-042) documents 42
failures. How many of these failures would the reachability
engine architecture have PREVENTED? How many would it have
DETECTED EARLIER? How many are independent of the architecture?

Q-031 [EVIDENCE_LOOP.md]
The evidence loop has 3 checkpoints (pre-claim, pre-commit,
pre-phase). The reachability engine adds a new step
(classification before prediction). Does this require a fourth
checkpoint (pre-classification)? Or does it fold into the
existing pre-phase checkpoint?

---

## Questions about what to build next

Q-032 [REACHABILITY_CONSTITUTION.md Rule 3]
"Mechanisms before formulas." The mechanisms are cataloged
(MECH-D001 through MECH-R002). Which formula should be built
first? The one for the most common mechanism? The one for the
mechanism with the most data? The one for the mechanism the
frozen formula already detects (to validate the approach)?

Q-033 [PHASE_14_PLAN.md]
Two stress-test domains remain: aviation and pharmaceuticals.
Should they be run under the OLD architecture (frozen formula,
expected to fail) or the NEW architecture (classify first, then
apply the appropriate instrument)? If the new architecture,
which instrument(s) would apply?

Q-034 [INVENTION_CLASSES.md]
The class distribution shows Discovery is absent from all event
registries. Should the project collect Discovery events
(scientific publications, patent filings) to test the Discovery
class? Or is Discovery upstream of what the project can
realistically model?

Q-035 [STATE_SPACE.md]
Six of eight state dimensions are NOT IMPLEMENTED. Which
dimension should be implemented first? The one with the most
available data? The one that addresses the most boundary
patterns? The one that is most transferable across domains?

---

## Meta-questions

Q-036 [LESSONS_LEARNED.md]
The project's deepest lesson: "invention is heterogeneous, not
homogeneous." Is this lesson specific to invention, or does it
generalize to other complex-system phenomena (e.g., market
crashes, ecosystem transitions, social movements)? Could the
reachability engine architecture apply beyond invention?

Q-037 [PHASE_14R_REFLECTION.md]
The CEO's central question — "is the theory wrong, or is the
ontology incomplete?" — remains unanswered. After Phase 15
(classification layer built), is the answer clearer? Or does
the classification layer simply make the question more precise
without resolving it?

Q-038 [LESSONS_LEARNED.md]
The project moved from "one phenomenon, one model, one formula"
to "many phenomena, many mechanisms, many instruments." Is this
a sign of progress (the project discovered the truth is more
complex than initially assumed) or a sign of retreat (the
project could not build the single model and is rationalizing)?

Q-039 [REACHABILITY_CONSTITUTION.md]
The six rules of the reachability constitution are stated as
axioms. Are they testable? Or are they commitments — rules the
project chooses to follow regardless of testability?

Q-040 [all deliverables]
Phase 15 built the classification layer. Nothing operational
was built. Is the classification layer useful without the
instruments (formulas) that would use it? Or is it premature
abstraction — designing a classifier before having the things
to classify?

---

## Closing note

These 40 questions are the project's honest accounting of what
it does not know. Some may be answered in future phases. Some
may remain open indefinitely. Some may turn out to be the wrong
questions — reformulated when more is understood.

Recording them now is the discipline. Per REACHABILITY_CONSTITUTION.md
Rule 5: "Failures are observations." Per Rule 4: "Boundaries are
assets." These open questions are the boundary of the project's
current understanding. They are assets, not gaps.

The questions do not commit the project to any particular answer.
They commit the project to NOT pretending it has answers it does
not have.
