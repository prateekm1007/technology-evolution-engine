# EPISTEMIC_ENGINE.md

Specification for the re-audit / adversarial-verification layer (DR-31–DR-37).
Written before implementation, per governance discipline: principle → specification →
implementation → benchmark → audit → revision.

Status: SPECIFICATION — nothing in this document is implemented yet. Do not cite this
file as evidence that `reaudit_loop.py`, `ExclusionEvent`, or any schema below exists in
source. Check `git log` before believing otherwise.

---

## 0. The principle

The fundamental unit of the system is not a claim. It is:

```text
claim
   ↓
counterclaim
   ↓
adjudication
```

A system that only produces the first term is a reporting engine, regardless of how
sophisticated its extraction, scoring, or graph construction is. Every mechanism in this
document exists to make the second and third terms structurally mandatory rather than
optional, discretionary, or dependent on an external party (a human, an auditor Claude
instance) happening to check.

Corollary, stated as the rule that governs every claim in the system:

> Every claim must remain vulnerable to attack.

Not "every claim must be correct." Correctness is an outcome, not a property you can
enforce directly. Vulnerability to attack is a property you *can* enforce directly, and
correctness follows from it probabilistically, the same way it does in adversarial peer
review, patent examination, and open-source security disclosure.

---

## 1. Why this document exists (provenance)

Cycle 67 produced PKG-DISC-001, a report claiming a genuine Swanson-style bridge
(mycelium → biomineralization → calcium_carbonate) labeled NOVEL HIT. Independent
adversarial search (external, not repo-internal) found the bridge already published as a
named subfield since at least 2018, with a standing 2021 review paper. Three of the
report's own five "independent" T2 sources were themselves part of the pre-existing
connecting literature. Correct classification: RETRIEVAL, NOT DISCOVERY — the same label
correctly applied to PKG-DISC-002 (cycle 68) on weaker evidence.

Root cause was not extraction quality, scoring quality, or corpus size. It was the
absence of a mandatory, structural step between "prediction locked" and "prediction
believed." Nothing in the pipeline was required to try to kill the claim before it
shipped as a PDF.

This is the same failure shape as F-060, F-061, and the Gentner constant-score bug —
different layer, same root: a claim (edge, score, mechanism, discovery) was accepted
because nothing was structurally required to attack it first.

---

## 2. Data model

### 2.1 Claim (supersedes bare `oracle_prediction` for discovery-class claims)

```python
@dataclass
class Claim:
    claim_id: str
    proposition: str              # the falsifiable statement itself
    claim_type: ClaimType         # EMPIRICAL | FORMAL (see §4)
    original_evidence: list[Evidence]
    original_verdict: Verdict     # NOVEL_HIT | RETRIEVAL | NULL
    confidence: float             # calibrated, see §6
    lock_time: datetime           # immutable once set
    challenges: list["Challenge"] = field(default_factory=list)
    adjudications: list["Reaudit"] = field(default_factory=list)

    @property
    def current_status(self) -> Verdict:
        """Recomputed from adjudications. Never stored, never edited directly."""
        if not self.adjudications:
            return self.original_verdict
        return self.adjudications[-1].verdict
```

The claim is permanent. The verdict is provisional. `original_verdict` is never
overwritten — history is append-only. `current_status` is a computed property, not a
field, specifically so nothing can set it directly.

### 2.2 Evidence (extends the existing `Evidence` type with temporal provenance)

```python
@dataclass
class Evidence:
    source_id: str
    publication_date: datetime
    retrieval_timestamp: datetime
    prediction_lock_time: datetime
    verification_timestamp: datetime
    provenance_hash: str          # hash of source content at retrieval time

    def __post_init__(self):
        assert self.publication_date < self.prediction_lock_time, (
            "F-064 class violation: evidence published after the prediction it "
            "verifies cannot be independent confirmation — check for circularity "
            "(did this source cite something the system itself published?)"
        )
        assert self.retrieval_timestamp <= self.verification_timestamp
```

This one invariant — `publication_date < prediction_lock_time` — is cheap to add now and
expensive to retrofit later. It doesn't catch the PKG-DISC-001 failure (all five sources
predate T1 there); it catches the next one, where a source only exists because something
TEE published got indexed and fed back in, making "independent" verification circular in
a way that isn't visible to a human skimming a PDF.

### 2.3 Reaudit

```python
@dataclass
class Reaudit:
    auditor: str                  # distinct from the agent/model that made original_verdict
    timestamp: datetime
    verdict: Verdict
    evidence: list[Evidence]
    confidence: float
    vocabulary_hash: str          # hash of search terms used — must differ from
                                   # the original extraction's entity vocabulary
```

`vocabulary_hash` exists to make "genuinely independent search" checkable rather than
declared. A re-audit whose vocabulary hash collides significantly with the original
claim's extraction vocabulary hasn't performed an adversarial search — it's re-run the
same query and gotten the same answer, which proves nothing.

### 2.4 Benchmark / ExclusionEvent (replaces the underspecified `BenchmarkMetadata`)

```python
@dataclass
class Benchmark:
    benchmark_id: str
    claim_id: str
    creation_time: datetime
    status: BenchmarkStatus       # ELIGIBLE | EXCLUDED | RETIRED
    exclusions: list["ExclusionEvent"] = field(default_factory=list)

@dataclass
class ExclusionEvent:
    timestamp: datetime
    actor: str
    reason_code: ReasonCode
    evidence: str
    source_reference: str         # must point to an F-XXX entry or an
                                   # automated trigger condition — never freeform

class ReasonCode(Enum):
    CONTAMINATED           # answer entered a governance-required-reading document
    DUPLICATE
    EXTERNAL_DISCLOSURE
    DATA_CORRUPTION
    CONSTITUTIONAL_EXPOSURE

class Verdict(Enum):
    NOVEL_HIT = "novel"
    RETRIEVAL = "retrieval"
    NULL = "null"
```

Exclusion is an event, not a state. `is_retired = True` is a single silent write that
deletes an inconvenient benchmark without appearing to. An `ExclusionEvent` appended to
an immutable list, requiring a `source_reference`, is auditable by construction —
including auditable for whether exclusions themselves are being used to launder failing
results out of the pool. (Add that check to §8's meta-audit.)

---

## 3. The outcome matrix must be symmetric

The earlier draft of this system implicitly only modeled downgrade:
`Novel → Retrieval`. That's institutional pessimism, not calibration — a reward
structure that only ever demotes claims produces an equilibrium strategy of
"when uncertain, downgrade," which is a bias away from truth in the opposite direction
from overclaiming, not an absence of bias.

| Original  | Re-audit  | Result     |
|-----------|-----------|------------|
| Novel     | Novel     | upheld     |
| Novel     | Retrieval | overturned |
| Novel     | Null      | unresolved |
| Retrieval | Novel     | overturned |
| Retrieval | Retrieval | upheld     |
| Retrieval | Null      | unresolved |
| Null      | Novel     | overturned |
| Null      | Retrieval | overturned |
| Null      | Null      | upheld     |

Truth is the invariant. Not novelty, not caution.

---

## 4. Claim types have different termination conditions

Not every claim TEE produces is empirical, and treating all of them as if they require a
physical-world observation to terminate will eventually produce a formal-verification
step that pointlessly reaches for web search, or an empirical claim that gets waved
through on "technically this is a logical statement" grounds.

| Claim type    | Termination condition        | Example in TEE                          |
|---------------|-------------------------------|------------------------------------------|
| Empirical     | Independent observation       | BACON fitting a formula to real data     |
| Experimental  | Independent replication       | An EXP-XXX closed loop                   |
| Statistical   | Independent dataset           | causal_density measured on held-out corpus |
| Computational | Independent implementation    | A second implementation of Swanson search |
| Logical       | Independent derivation        | Altshuller contradiction count on a fixed graph |
| Mathematical  | Independent proof              | Dimensional-consistency pruning correctness |

Constitutional principle, scoped accordingly:

> No chain of internal validation is sufficient in itself. Every empirical claim must
> terminate in an independently observable fact outside the system. Every formal claim
> must terminate in an independently reproducible derivation.

This is the exit ramp for the audit → meta-audit → meta-meta-audit regress. It doesn't
solve the regress; it stops it. Without a rule like this, arbitrarily many internally
consistent agents agreeing with each other is bureaucracy, not knowledge.

---

## 5. Blindness by procedure, not secrecy

True secrecy is unavailable to this system — both operators have full read access to the
repository, the ledger, the failure log, and the conversation history that produced this
document. The property actually being protected is not secrecy. It's **resistance to
contamination**: the property that a benchmark's outcome isn't influenced by who selected
it, when, or with what prior expectation.

### 5.1 Sample selection

```python
seed = sha256(
    cycle_number.to_bytes(...)
    + latest_commit_hash.encode()
    + external_entropy
).digest()

sample = random.Random(seed).sample(eligible_claims, k=sample_size)
```

### 5.2 The bar for `external_entropy`

Not `random.random()`. Not `uuid.uuid4()`. Both are internal entropy wearing an external
name — generated by, and reproducible by, the same actor selecting the sample.

The required property: no actor can predict the value, influence the value, regenerate
the value, or choose among multiple candidate values. Acceptable sources: a public
randomness beacon (e.g. NIST), a not-yet-mined block hash at seed-generation time, an
independently timestamped public value that does not exist yet when the seed is
constructed.

The test: **could someone rerun the cycle until they obtained a sample they preferred?**
If yes, the entropy source is not external enough. This is a mechanical test, not a
judgment call — verify it by checking whether the entropy source's value is knowable at
the moment the seed is constructed. If it is, reject it.

---

## 6. Calibration is the actual target, not zero error

An open-domain discovery engine reading real, ambiguous, incomplete literature cannot
reach "never claims anything false" — some claims will always be judgment calls that
later evidence overturns, the same way published science gets overturned. The target is
calibration: a claim tagged high confidence should be right close to that rate; a claim
tagged moderate confidence should be right proportionally less often. Track this with
expected calibration error (ECE) or Brier score computed from `reaudit_result` outcomes
bucketed by `Claim.confidence`, once ≥20 re-audited claims exist (smaller samples produce
noise, not a calibration curve).

---

## 7. Implementation sequence (DR-31 through DR-37)

Order matters — a re-audit system built on a non-reproducible, hand-steered pipeline
audits noise.

- **DR-31 — Ledger schema first.** Register `Claim`, `Reaudit`, `Benchmark`,
  `ExclusionEvent` types in `test_ledger_integrity.py`'s `known_writers` in the *same
  commit* that adds the writer producing them. This is not a style preference — the
  `baseline_measurement` / `mechanism_verification` gap has been open and unfixed since
  cycle 55, nine cycles as of this writing, and has since silently absorbed three more
  unregistered types (`blind_test_hypothesis`, `blind_test_result`,
  `blind_test_verification`) rather than being caught and closed. Close the existing debt
  in this same commit, not as separate scope.
- **DR-32 — Reproducible blind-discovery runner.** Before any re-audit exists, blind runs
  themselves need to record: pre-registration of both literatures, locked hypothesis,
  fixed corpus snapshot (hash it), extraction method used, candidate bridges with scores,
  full verification source list with `Evidence` objects (§2.2), final outcome label.
- **DR-33 — Cadence loop.** `scripts/reaudit_loop.py`. Every 10 cycles: construct the
  seed per §5.1, draw the sample, run adversarial verification with `vocabulary_hash`
  checked against the original claim's extraction vocabulary. Exit criterion: 3
  unprompted runs by week 5 — triggered by the cadence, not by a human invoking the
  script, or it's not a cadence system.
- **DR-34 — Apollo table column + adversary scoreboard.** "Confirmed on re-audit" as a
  column next to Novel Hits and Verified Mechanisms — not a new row, which only rewards
  production volume. Separate `adversary_performance` ledger:
  `{claims_reviewed, claims_killed, claims_missed_then_caught_later}`. The third field is
  the one under most pressure to be skipped; it's also the only one that would have
  caught PKG-DISC-001 automatically.
- **DR-35 — Overturn-rate trend.** No trend claimed before ≥4 ten-cycle windows exist.
  Report sample size alongside every rate — a 0% overturn rate on n=2 means nothing.
- **DR-36 — Calibration.** Per §6, ≥20 samples before the ECE/Brier number is reported.
- **DR-37 — Audit the auditor.** Recurring, no close date. Every ~30 cycles, an
  independent check (ideally a different Claude instance with no context on how the
  re-audit loop was built) cold-verifies 2–3 `upheld` verdicts, plus specifically checks
  whether any `ExclusionEvent` lacks a valid `source_reference`. If the meta-audit
  overturns something the automated re-audit upheld, log it as its own F-XXX, not folded
  into `adversary_performance` — that discrepancy is more important than any individual
  claim's correctness.

---

## 8. PKG-DISC-001 disposition

PKG-DISC-001 cannot serve as the first re-audit test case. The correct classification is
already known to both operators and, once logged, will enter `FAILURES.md` — a file
`MASTER_PROTOCOL.md` requires be read before every commit. Any `reaudit_loop.py` built in
compliance with existing governance will have read the answer before running. A clean
`overturned` result at that point would prove the system follows its own governance
files, not that it can independently detect this class of error. Those are different and
both worth measuring, but they are not the same experiment.

Disposition:

1. Correct `product/DISCOVERY_REPORT.md`/`.pdf` immediately. `CURRENT STATUS: RETRIEVAL,
   NOT DISCOVERY`. `CORRECTION SOURCE: manual adversarial review, external web search,
   predates reaudit system`. Do not sit on a known error to preserve a benchmark — the
   cost of an org operating on a false "first novel hit" outweighs the cost of losing one
   canary.
2. Log F-063 in `FAILURES.md`, with an explicit annotation: `NOT ELIGIBLE AS FUTURE BLIND
   CANARY — corrected via manual review prior to reaudit_loop.py existing`.
3. Record an `ExclusionEvent` for PKG-DISC-001's `Benchmark` entry:
   `reason_code=CONSTITUTIONAL_EXPOSURE`, `source_reference="F-063"`.
4. The first genuine blind canary is selected *after* DR-33 exists, from the pool of
   claims produced *after* this document is committed (so no claim discussed in this
   specification's own drafting is eligible), via the §5.1 procedure. Nobody — including
   whoever writes `reaudit_loop.py` — should know which claim was selected until the seed
   resolves.

---

## 9. What this document is not

This is not proof that any of the above works. It's the specification the
implementation should be checked against — the next artifact should be
`scripts/reaudit_loop.py` built to this spec, followed by an external, independent audit
of whether the implementation actually matches it. That audit should not be performed by
the same session, instance, or context that wrote either this document or the code.

---

## 10. DR-49 — Outcome-quality gate (cycle 135, rebuild of unpushed cycle 132 work)

### The principle

Every scoring function in `nine_tenths_loop.py` must have an outcome-quality
gate. Infrastructure points can contribute to the score but cannot exceed
7/10 without a measured outcome. Scores above 7/10 require a measured
outcome (P/R/F1, ECE, accuracy, overturn rate) that justifies the higher
score.

### Why this exists

F-068 (CALIB-SCORE-DESIGN) and F-069 (F-068-RECURRING) documented the
pattern: scoring functions awarded points for infrastructure existing
(calibration code exists → points; relation extraction pipeline exists →
points) without measuring whether the infrastructure actually produced
correct results. This is the same pattern as F-067 (scorecard fabricated
outside committed code) at a deeper level: the code exists, but the
score reflects what is built, not what works.

### The rule

For each generation's `assess_*()` function:

```
infra_score (max 7)  +  outcome_score (max 3, requires measured outcome)  =  total (max 10)
```

- **Infra points (0-7):** awarded for code existing, tests passing,
  infrastructure wired. Capped at 7.
- **Outcome points (0-3):** awarded only when a benchmark has been run
  and produced a measured result. The score is a function of the metric:
  - F1 >= 0.75 → +3
  - F1 >= 0.50 → +2
  - F1 >= 0.25 → +1
  - F1 < 0.25  → +0
  - (For ECE: ECE <= 0.05 → +3; <= 0.10 → +2; <= 0.15 → +1; > 0.15 → +0)
  - (For overturn rate: >= 20% → +3; >= 10% → +2; > 0% → +1; 0% → +0)

### Enforcement

The `assess_*()` functions must read the benchmark result from
`benchmarks/reports/<name>_score.json` (produced by the benchmark runner).
If the report file does not exist, outcome points = 0. The scorecard
cannot award outcome points without a measured result on disk.

### What this makes structurally impossible

The F-068/F-069 pattern — scoring what exists, not what works — is now
structurally impossible. A scoring function cannot produce >7/10 without
a benchmark result file on disk. The scorecard is honest (DR-48: from
committed code) AND conservative (DR-49: infra alone caps at 7/10).
