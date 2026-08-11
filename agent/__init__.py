"""
Agent package — the substrate beneath the hypothesis.

STATUS: SCAFFOLD. Declared but NOT implemented. Per CTO review #5
(commit `0029759`), this package exists as a documented target
toward which the system should converge. It does not yet do
anything.

# Why this layer exists

The CTO observed that the current model is:

    hypothesis → loop → ledger

But eventually it becomes:

    agent → hypothesis → experiment → observation → hypothesis

Hypotheses are not static. They evolve. An agent:

  1. PROPOSES a hypothesis (a claim with confidence and evidence).
  2. DESIGNS an experiment to test the hypothesis.
  3. RECORDS the observation when the experiment is run.
  4. UPDATES the hypothesis (or, per Law 7, creates a new one
     with the old one's history preserved).
  5. LEARNS — the agent's future proposals are informed by what
     was observed.

That's a learning loop, not a static assertion. The Hypothesis
object is one stage in that loop; the Agent is the thing that
cycles through the stages.

# What "implemented" means

This layer is NOT implemented when:
  - It exists only as a docstring.
  - It declares functions but the functions raise NotImplementedError.
  - It has no tests for an actual
    propose→design→observe→update→learn cycle on a real problem.

This layer IS implemented when:
  - At least one agent has been instantiated.
  - That agent has proposed a hypothesis for a real problem
    (a small milestone, per the small-milestone rule).
  - That hypothesis has been tested by an actual experiment.
  - The observation has been recorded.
  - The hypothesis has been updated (or a new one created).
  - The agent has used the observation to inform its next proposal.

Until those conditions are met, this package is a scaffold and a
docstring. The first concrete agent will be the one that closes
the first small milestone at `milestones/milestone_001/`.

# The agent interface (provisional)

The eventual Agent class will likely expose:

    class Agent:
        def propose(self, problem: dict) -> Hypothesis
        def design_experiment(self, hypothesis: Hypothesis) -> dict
        def record_observation(self, experiment_id: str, observation: dict) -> None
        def update(self, hypothesis: Hypothesis, observation: dict) -> Hypothesis
        def learn(self) -> dict  # summarize what the agent has learned

This is provisional. The first concrete agent implementation may
diverge — the package is scaffolded, not specified.

# Relationship to the loops

The 5 loops in `loops/` are the cycles the agent runs. Loop 1
(reconstruction) and Loop 2 (resurrection) are partially closed
today via historical data; Loops 3, 4, 5 require the agent layer
to close.

The agent does NOT replace the loops — it operates them. Each
loop is a different kind of agent cycle:
  - reconstruction agent: compares its prediction to humanity's
    recorded observation.
  - resurrection agent: predicts whether an abandoned idea will
    become feasible again.
  - forecasting agent: predicts what will become feasible.
  - experimentation agent: designs experiments and updates its
    models from observations.
  - creation agent: proposes blueprints and learns from build
    outcomes.

# Relationship to Law 8

Law 8 (CONSTITUTION.md): "No 'verified' label without a successful
prediction, a failed prediction, and replayable evidence."

The agent layer is what makes Law 8 enforceable in real time.
Today, the verification cycle runs on historical data — it's
a "bench test" of the system's predictive capability. The agent
layer is the live version: the system predicts, observes, and
learns in real time.

Until the agent layer is implemented on at least one real
milestone, every "expectations_satisfied" verdict in the
benchmark suite is provisional.
"""
