# TECHNOLOGY EVOLUTION ENGINE
# CONSTITUTIONAL ROADMAP V2

## (Grounded in Current Repository Reality)

Cycle 258. Supersedes prior roadmaps. Canonical project plan.

---

# Current State (Verified)

The repository contains **four major systems**, all at different maturity levels.

| System      | Reality                                                            |
| ----------- | ------------------------------------------------------------------ |
| Discovery   | Functional pipeline but benchmark currently untrustworthy          |
| Invention   | Can generate proposals but proposal quality is still low           |
| Search      | Strongest part of the repository. L1-L5 research largely complete. |
| Measurement | Exists but is now the bottleneck of the entire project             |

The audit changes everything.

The bottleneck is **NOT invention.**

The bottleneck is **measurement.**

---

# New Architecture

Instead of

```
Discovery

↓

Invention

↓

Product
```

the architecture becomes

```
Measurement Engine
        ↓
Discovery Engine
        ↓
Proposal Engine
        ↓
Invention Engine
        ↓
Product
```

Everything depends on Measurement.

Nothing bypasses Measurement.

---

# Principle 1

No capability work until the measurement layer proves it can measure that capability.

This becomes constitutional.

---

# PROGRAM A

# Computational Metrology

(Project Priority #1)

Goal

Build a measurement engine that behaves like a scientific instrument.

Not a score.

An instrument.

---

## Stage M1

Measurement Specification

Deliverables

MeasurementEngineSpecification.md

Every metric must define

Inputs

Outputs

Assumptions

Known failure modes

Uncertainty

Evidence tier

Calibration status

Owner

Acceptance

Every metric documented.

No undocumented metric remains.

---

## Stage M2

Measurement Provenance

Every score becomes

```
Score

± uncertainty

Evidence tier

Calibration version

Evaluator version

Prompt version

Judge version

Timestamp

Benchmark version
```

No naked numbers.

---

## Stage M3

Bootstrap Statistics

Current

```
F1 = 0.91
```

Becomes

```
F1 = 0.91 ± 0.07

95% CI

N

Bootstrap

Variance

Distribution
```

Every metric.

---

## Stage M4

Repeatability

Run identical benchmark

100 times

Different seeds

Measure

variance

drift

stability

Acceptance

Coefficient of variation below threshold.

---

## Stage M5

Reproducibility

Run

different hardware

different LLMs

different prompts

different operating systems

different temperatures

Question

Do conclusions survive?

---

## Stage M6

Sensitivity

Perturb

input

gold

prompt

proposal

confidence

mechanism

Measure

how much outputs move.

---

## Stage M7

Failure Envelope

Instead of

"When does it work?"

Answer

"When does it fail?"

Every evaluator must have

Failure Envelope document.

---

## Stage M8

Measurement Constitution

Rules every future metric must satisfy.

Examples

No self validation.

Independent rescoring.

Confidence calibration.

Evidence tiers.

Adversarial testing.

Historical permanence.

---

# PROGRAM B

Discovery Recovery

(Project Priority #2)

Discovery work is frozen until benchmark recovery completes.

---

## Stage D1

Proposal-first Benchmark

Stop benchmarking entities.

Benchmark proposals.

---

## Stage D2

Mechanism-first Benchmark

Entity overlap removed.

Bridge measured through

mechanism

prediction

falsifier

evidence

---

## Stage D3

External Baselines

Repository must beat

BM25

Entity overlap

Random

LLM baseline

Naive bridge search

---

## Stage D4

Historical Recalibration

Recompute

every published score

from Cycle 1 onward.

Publish

before

after

reason

No hiding historical reductions.

---

## Stage D5

Final Discovery Verdict

Only after

bootstrap

calibration

human review

external baseline

historical recalibration

may Discovery become

TRUSTWORTHY.

---

# PROGRAM C

Proposal Science

(Project Priority #3)

Current Proposal Composer is Generation 0.

Frozen.

Never modified.

---

## Stage P1

Mechanism-driven Proposal Composer

Instead of

```
shared entity

↓

template
```

Build

```
Mechanism graph

↓

causal chain

↓

prediction

↓

falsifier

↓

proposal
```

---

## Stage P2

ScientificClaim Object

Repository currently experiments with multiple representations.

The audit showed no representation is yet validated.

Design one canonical object.

Candidate

```
ScientificClaim

Mechanism

Prediction

Assumptions

Alternative explanations

Counterexamples

Falsification experiment

Evidence graph

Confidence

Provenance

Measurement history
```

Everything downstream consumes this object.

---

## Stage P3

Proposal Calibration

Every proposal receives

internal evaluation

LLM evaluation

expert evaluation

experimental evaluation (future)

Track calibration over generations.

Gen0

Gen1

Gen2

...

Never overwrite history.

---

# PROGRAM D

Evaluation Science

(Project Priority #4)

Treat evaluators as scientific instruments.

---

## Stage E1

Evaluator Reliability

Agreement

Bias

Variance

Drift

Calibration

Failure modes

---

## Stage E2

Objective vs Subjective Split

Never allow

Novelty

Importance

Plausibility

to be mixed with

Structure

Prediction exists

Falsifier exists

Evidence exists

Separate them permanently.

---

## Stage E3

Human Expert Layer

Tier 2

External domain experts.

Not optional.

---

## Stage E4

Evaluator Constitution

Every evaluator must satisfy

repeatability

reproducibility

robustness

adversarial resistance

calibration

before deployment.

---

# PROGRAM E

Invention Engine

(Project Priority #5)

Notice:

Invention is no longer priority one.

It depends on Programs A-D.

---

Current state

Generate

Predict

Measure

Search

Learn

all exist.

Do not expand.

Instead

improve proposal quality

using

better mechanisms

better measurement

better evaluation.

---

# PROGRAM F

Search Theory

(Project Priority #6)

L1-L5 research chapter is effectively complete.

Do NOT continue adding DSL operators.

The repository has already falsified:

✓ Better search

✓ Deeper composition

✓ Parameterization

✓ Landscape-derived operators

Those are closed research directions.

The next frontier is representation, not optimization.

---

Future work becomes

Representation Discovery

not

Optimizer Discovery.

---

# PROGRAM G

Research Infrastructure

(Project Priority #7)

This becomes a permanent capability.

Every experiment automatically produces

Hypothesis

Null hypothesis

Method

Result

Negative result

Confidence

Limitations

Replication instructions

Artifacts

This turns the repository into a self-documenting scientific laboratory.

---

# STOP BUILDING LIST

The coder is forbidden from building any of the following until Programs A-D are complete:

❌ Better Proposal Composer (beyond Gen0 experiments)

❌ New discovery algorithms

❌ New invention algorithms

❌ L6 search

❌ Product features

❌ UI improvements

❌ Commercialization work

❌ Benchmark tuning

❌ Score improvements

If any of these are attempted before measurement is trustworthy, reject the work.

---

# GO / NO-GO Gates

### Gate 1 — Measurement

Pass only if:

* Bootstrap statistics implemented.
* Confidence intervals on all metrics.
* Evaluator reliability quantified.
* Calibration documented.
* Repeatability demonstrated.

### Gate 2 — Discovery

Pass only if:

* Proposal benchmark replaces entity benchmark.
* External baselines included.
* Historical recalibration complete.
* FP floor acceptable.
* Human review completed.

### Gate 3 — Proposal

Pass only if:

* Mechanism-driven proposals outperform Gen0.
* Independent evaluation improves.
* Calibration bias decreases relative to Gen0.

### Gate 4 — Invention

Pass only if:

* Proposal engine trusted.
* Measurement engine trusted.
* Discovery benchmark trusted.

Only then resume invention work.

---

# Success Criteria

The repository is no longer trying to answer:

> "Can AI invent?"

It is trying to answer a deeper question:

> "Can we build a scientific system that knows when an AI invention should be believed?"

That is a substantially stronger objective. If achieved, it would make the invention engine far more credible than simply generating more hypotheses, because every future capability would rest on a measurement system whose limitations, uncertainty, and calibration are explicitly characterized. This roadmap also reflects the audit's central conclusion: the next breakthrough is not another invention algorithm, but trustworthy scientific measurement.
