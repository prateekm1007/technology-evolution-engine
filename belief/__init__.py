"""
Belief package — the emerging fifth entity.

STATUS: SCAFFOLD. Declared but NOT implemented. Per CTO review #6
(commit `874ec10`), this package exists as a documented target
toward which the system should converge. It does not yet do
anything.

# Why this layer exists

The CTO observed that the system now has four entities:

    Agent → Hypothesis → Experiment → Observation

And a fifth is emerging:

    Belief

Because the system will eventually need to answer:

  - Which hypotheses do we currently believe?
  - How strongly do we believe them?
  - What evidence would change our minds?

That is a very different problem from storing documents. A Belief
is the system's current committed position on a hypothesis,
given all observed evidence to date.

# The distinction between Hypothesis and Belief

A Hypothesis is a claim with confidence and evidence, awaiting
reconciliation. The `confidence` field is the system's PRIOR —
what it believed BEFORE observation.

A Belief is the system's POSTERIOR — what it believes AFTER
observation, given all evidence accumulated to date. A Hypothesis
without a Belief is just a stored assertion; a Hypothesis WITH a
Belief is a live claim the system is committed to.

Concretely:
  - Hypothesis.confidence = prior (set at construction)
  - Belief.confidence = posterior (updated by Bayes as observations
    accumulate)

# The Bayesian substrate

The Belief layer's first concrete deliverable: a function that,
given a Hypothesis and a list of related Observations, returns a
Belief (the Hypothesis's confidence updated by the observations).

For a Hypothesis with N observations:
  - Each pass observation increases the Belief confidence.
  - Each fail observation decreases the Belief confidence.
  - The exact update rule is Bayesian (or a simpler heuristic
    initially; the rule itself is a Hypothesis about how beliefs
    should update, and can be reconciled by the verification cycle).

# The committed-position semantics

Beliefs answer the three CTO questions:

  1. Which hypotheses do we currently believe?
     -> The set of Hypotheses whose Belief.confidence > threshold
        (e.g., 0.5).
  2. How strongly do we believe them?
     -> The Belief.confidence value (the posterior).
  3. What evidence would change our minds?
     -> For each Belief, the counterevidence list (from the
        underlying Hypothesis) plus the observations that would
        flip the Belief below threshold (computed from the
        Bayesian update rule).

# What "implemented" means

This layer is NOT implemented when:
  - It exists only as a docstring.
  - It declares functions but the functions raise NotImplementedError.
  - It has no tests for an actual
    Hypothesis + Observations -> Belief update cycle on real data.

This layer IS implemented when:
  - At least one Belief has been computed from a real Hypothesis
    with at least one real Observation.
  - The Belief can answer the three CTO questions for that
    Hypothesis.
  - The Belief is recorded in the ledger alongside the Hypothesis
    (Law 7: historical permanence — both the prior and the
    posterior are preserved).

Until those conditions are met, this package is a scaffold and a
docstring. The first concrete Belief will be computed when
milestone_001 or milestone_002 closes — the system will then have
a real Hypothesis with a real Observation, and a Belief can be
computed.

# The provisional Belief interface

The eventual Belief class will likely expose:

    class Belief:
        hypothesis_id: str             # the Hypothesis this Belief is about
        posterior_confidence: float   # updated by Bayes from observations
        observations: list[Observation]  # the observations that updated it
        committed_at: str             # ISO8601 UTC
        # Methods:
        def update(self, observation: Observation) -> None
        def what_would_change_my_mind(self) -> list[Observation]
        @classmethod
        def from_hypothesis(cls, h: Hypothesis) -> "Belief"

This is provisional. The first concrete Belief implementation may
diverge — the package is scaffolded, not specified.

# Relationship to the agent layer

The agent layer (agent/) proposes Hypotheses; the Belief layer
(belief/) updates them based on Observations. Together they form
the learning loop:

    agent.propose(problem) -> Hypothesis
    agent.design_experiment(hypothesis) -> Experiment
    [external collaborator runs the experiment]
    agent.record_observation(experiment_id, observation) -> Observation
    belief.update(hypothesis, observation) -> Belief
    # The agent's next proposal is informed by the updated Belief.

The agent layer is scaffolded; the Belief layer is scaffolded.
Both are required for a learning system. Neither is implemented
yet.
"""
