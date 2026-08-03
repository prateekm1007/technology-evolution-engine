# PHASE_14R_REFLECTION

**Status:** Phase 14R reflection.
**Location:** repo root.
**Phase:** 14R.

> Is the theory wrong, or is the ontology of invention incomplete?
> — CEO directive, Phase 14R

This document engages with the CEO's four hypotheses (H1-H4) and
attempts to answer the central question. Per EP-11, no promotional
language. Per EP-4, any explanatory claims have pre-stated
falsifiers (noted inline). Per EP-5, this is self-authored
reflection — it is not independently graded and should not be
treated as evidence.

---

## The catalog (summary from BOUNDARY_REGISTRY.md)

28 boundary cases across 2 domains, in 5 patterns:

| Pattern | Count | Robust falsification? |
|---|---|---|
| 1. Scaling events (zero velocity) | 11 | YES |
| 2. Generation transitions (re-rise) | 7 | YES |
| 3. Threshold granularity (exactly 0.20) | 5 | NO (threshold-sensitive) |
| 4. Post-maturity exploitation | 2 | YES |
| 5. Adjacency competition | 3 | NO (formula architecture) |

**20 robust falsifications** of strict necessity (FEC-002). **8
non-robust failures** (fixable without touching the theory).

---

## Engagement with H1: capability emergence vs exploitation

### H1 (CEO's statement)

> The theory applies to capability emergence. It does not apply
> to capability exploitation.

### Evidence from the catalog

**Pattern 1 (scaling events, 11 cases) and Pattern 4 (post-maturity
exploitation, 2 cases) directly support H1.** These 13 cases are all
"exploitation" — invention that occurs within or after a mature
technology base, with zero rising-capability velocity.

The 5 Li-ion TPs (from Phase 11A) and the 2 real semiconductor TPs
(copper 1997, high-k 2007) are all "emergence" — invention that
occurs when a capability is rising from low TRL to TRL 9. The
theory correctly predicts these.

### What H1 explains

H1 explains why the theory works for Li-ion (all events were
emergence — no scaling events in the registry) and fails for
semiconductors (33% scaling events) and telecom (47% scaling events).
The ratio of emergence-to-exploitation events in each domain
predicts the theory's success rate.

### What H1 does NOT explain

H1 does not explain Pattern 2 (generation transitions, 7 cases).
The 2G, 3G, 4G, 5G transitions ARE emergence events — new
capabilities are genuinely emerging (digital cellular, packet
data, all-IP, mmWave). The theory should detect them under H1.
But it doesn't, because the trajectory model represents
WIRELESS_PROTOCOL as a single capability that rose once (1G)
and then plateaued.

This means H1 is necessary but not sufficient. There is a second
boundary: even for emergence events, the theory fails if the
capability has "re-risen" before.

### Verdict on H1

**H1 is supported by the data, but it is incomplete.** It explains
13 of 20 robust falsifications (Patterns 1 and 4). It does not
explain the other 7 (Pattern 2 — generation transitions, which
ARE emergence but are not detected).

**Falsifier for H1:** If a future domain has zero scaling events
(Pattern 1) and zero post-maturity exploitation (Pattern 4), and
the theory still fails, H1 is falsified. (This would be a domain
where all events are emergence, but the theory still cannot predict
them — pointing to a structural issue beyond emergence-vs-exploitation.)

---

## Engagement with H2: velocity vs acceleration

### H2 (CEO's statement)

> Velocity is not fundamental. Acceleration may be fundamental.
> You are currently measuring dTRL/dt. You may ultimately need
> d²TRL/dt².

### Evidence from the catalog

The trajectory registries record acceleration (d²TRL/dt²) but
the frozen formula uses only velocity. I did not test acceleration.
The catalog cannot directly confirm or refute H2.

### Indirect evidence

Pattern 3 (threshold granularity, 5 cases) might be addressable by
acceleration. The semiconductor capabilities rise in linear TRL
steps (1 TRL per 5 years), producing constant velocity 0.20 and
zero acceleration. If acceleration were used, these capabilities
would have zero acceleration — same problem.

Pattern 2 (generation transitions, 7 cases) might be addressable
by acceleration. A "re-rise" produces a velocity discontinuity:
velocity goes from 0 (plateau) to negative (drop) to positive
(re-rise). The acceleration at the transition point is large.
If the formula used acceleration, it might detect the transition.

But this is speculation. I have not tested it. The frozen formula
uses velocity; testing acceleration would require unfreezing the
formula (forbidden by Rule 1).

### What H2 would require

To test H2, a new formula would be needed:

```
score = max(d²TRL/dt²) × adjacency
```

or

```
score = max(dTRL/dt, d²TRL/dt²) × adjacency
```

This is a new formula. It would be tested against the same
backtests. If it produces more TPs than the frozen formula
on the same data, H2 is supported. If it doesn't, H2 is
falsified.

### Verdict on H2

**H2 is untested.** It is plausible (especially for Pattern 2)
but not supported by current data. Testing it requires unfreezing
the formula, which is outside Phase 14's scope (Rule 1).

**Falsifier for H2:** If a future formula using acceleration
does not outperform the frozen formula on Li-ion (where the
frozen formula works), H2 is falsified. Li-ion is the right
test case because it's the domain where the frozen formula
has TPs — if acceleration doesn't improve on velocity there,
acceleration is not the issue.

---

## Engagement with H3: TRL as wrong state variable

### H3 (CEO's statement)

> TRL itself may be the wrong state variable. You might instead
> need something like: capability state, institutional state,
> cost state, infrastructure state, coordination state.

### Evidence from the catalog

**Pattern 2 (generation transitions, 7 cases) directly supports H3.**
The telecom "re-rise" problem is fundamentally about TRL being a
single scalar that cannot represent a capability with multiple
generations. WIRELESS_PROTOCOL at TRL 9 in 1990 (1G) and TRL 9
in 2020 (5G) are the same value but represent different states.

**Pattern 5 (adjacency competition, 3 cases) also supports H3.**
The 5G SA, 5G Advanced, and 5G mmWave events were missed not
because velocity was wrong, but because the formula could not
distinguish "WIRELESS_PROTOCOL at TRL 9 for 5G" from "WIRELESS_PROTOCOL
at TRL 9 for 4G." The state variable does not encode which
generation the capability is serving.

### What H3 explains

H3 explains why the theory fails on telecom even for emergence
events. TRL cannot represent:
- Which generation a capability is serving (1G vs 5G)
- Whether a capability is "active" (being deployed) or "legacy"
  (still operational but not the frontier)
- The coordination state (3GPP release cycle phase)
- The institutional state (spectrum auction timing)

These are all relevant to telecom invention, and TRL captures none
of them.

### What H3 does NOT explain

H3 does not explain Pattern 1 (scaling events). The semiconductor
scaling events (Intel 4004, 386, Pentium, etc.) occur within
capabilities that ARE at the right TRL (9, mature). The issue is
not that TRL is wrong — it's that the capabilities are being
exploited, not emerging. That's H1, not H3.

H3 also does not explain Pattern 4 (post-maturity exploitation).
The AMD 3D V-Cache event occurred when ADVANCED_PACKAGING was at
TRL 9 — the right TRL, correctly recorded. The issue is that
TRL 9 does not distinguish "just reached maturity" from "mature
for 10 years."

### Verdict on H3

**H3 is supported by Pattern 2 and Pattern 5, but not by Patterns
1 and 4.** It explains 10 of 28 cases. It is necessary but not
sufficient — like H1.

**Falsifier for H3:** If a future ontology uses multiple state
variables (capability state + institutional state + coordination
state) and the theory STILL fails on telecom, H3 is falsified.
This would mean the issue is not the state variable but something
deeper (possibly H4 — multiple invention classes).

---

## Engagement with H4: multiple classes of invention

### H4 (CEO's statement)

> There may be multiple classes of invention:
> - Emergence (capability formation)
> - Scaling (optimization)
> - Coordination (synchronization)
> - Recombination (adjacency)
> - Discovery (scientific advance)

### Evidence from the catalog

H4 is the deepest reframe. It suggests that "invention" is not
one thing but five (or more) different things, each with its own
mechanism. The current theory (`velocity × adjacency`) addresses
only emergence and recombination. It does not address scaling,
coordination, or discovery.

The catalog maps cleanly to H4's classes:

| H4 class | Catalog pattern | Count | Theory's coverage |
|---|---|---|---|
| Emergence | (Li-ion TPs, semiconductor real TPs) | 7 TPs | COVERED |
| Scaling | Pattern 1 (scaling events) | 11 | NOT COVERED |
| Coordination | Pattern 2 (generation transitions) | 7 | NOT COVERED |
| Recombination | (some TPs involve combining capabilities) | (subset of 7) | PARTIALLY COVERED |
| Discovery | (none in the catalog — no pure-discovery events) | 0 | UNTESTED |
| Post-maturity exploitation | Pattern 4 | 2 | NOT COVERED |
| Adjacency competition | Pattern 5 | 3 | PARTIALLY COVERED (formula issue) |
| Threshold granularity | Pattern 3 | 5 | NOT COVERED (threshold issue) |

### What H4 explains

H4 explains why no single formula can predict all invention.
The frozen formula `velocity × adjacency` is an emergence-and-recombination
detector. It cannot detect scaling (which requires an optimization
metric, not a trajectory metric), coordination (which requires a
consensus metric, not a TRL metric), or discovery (which requires
a scientific-advance metric).

The theory was never wrong — it was over-extended. It was applied
to invention classes it was not designed for.

### What H4 does NOT explain

H4 does not explain why the theory fails on telecom emergence events
(2G, 3G, 4G, 5G transitions). These ARE emergence events — new
capabilities are forming. Under H4, the theory should detect them.
But it doesn't, because of the TRL representation issue (H3).

So H4 is also necessary but not sufficient. It explains the
scaling and coordination failures but not the generation-transition
emergence failures.

### Verdict on H4

**H4 is the most explanatory hypothesis.** It accounts for 18 of
28 cases (Patterns 1, 2, 4 — the scaling, coordination, and
post-maturity cases). It does not explain Patterns 3 and 5 (which
are formula issues, not theory issues) or the generation-transition
emergence failures (which require H3).

H4 also reframes the project's original assumption. The project
started with "invention is one thing." H4 suggests invention is
at least five things. If H4 is correct, the project's goal of a
single formula for invention was misconceived.

**Falsifier for H4:** If a future domain has events from only one
H4 class (e.g., only emergence events) and the theory STILL fails,
H4 is falsified. (This would mean the theory cannot predict even
its "home" class.) The Li-ion domain is close to this test — its
events are mostly emergence — and the theory produced 5 TPs there.
So H4 is not yet falsified.

---

## The central question: theory wrong, or ontology incomplete?

### The case for "theory wrong"

The frozen formula `velocity × adjacency` produced:
- Li-ion: 5 TPs, p=0.2188 (not significant)
- Semiconductors: 4 TPs (2 real), p=0.5000 (not significant)
- Telecom: 0 TPs, p=0.5000 (worse than NULL)

The formula has not achieved statistical significance in ANY
domain. It has lost to NULL in telecom. It has produced only 2
real TPs across 2 stress-test domains.

If the formula cannot beat NULL at p<0.05 in any domain, it is
not a predictive theory. It is at best a directional heuristic
that works for emergence events in domains with monotonic TRL.

**This is the "theory wrong" position.** The formula captures
something real (emergence) but not enough to predict invention
better than random.

### The case for "ontology incomplete"

The formula's failures are not random — they follow patterns
(Patterns 1-5 in the catalog). These patterns correspond to
specific structural features of the domains:
- Scaling events occur when capabilities are mature (Pattern 1)
- Generation transitions occur when capabilities re-rise (Pattern 2)
- Threshold issues occur when TRL granularity is coarse (Pattern 3)
- Post-maturity exploitation occurs after TRL 9 (Pattern 4)
- Adjacency competition occurs when multiple high-velocity combos exist (Pattern 5)

If the formula's failures are STRUCTURED (not random), the
formula is detecting something real but missing something
specific. The "something missing" is what H1, H3, and H4 identify:
- H1: the emergence-vs-exploitation distinction
- H3: multi-dimensional state (not just TRL)
- H4: multiple invention classes (not just emergence)

An incomplete ontology would produce exactly this pattern: correct
predictions for the class it covers (emergence), structured failures
for the classes it doesn't (scaling, coordination, post-maturity).

**This is the "ontology incomplete" position.** The formula is
correct for emergence; the ontology (single TRL per capability)
is wrong for generation transitions and multi-class invention.

### Which position does the data support?

**The data supports "ontology incomplete" over "theory wrong," but
not conclusively.**

Reasons for "ontology incomplete":
1. The formula's failures are structured (Patterns 1-5), not random.
2. The formula works for emergence events (7 TPs across Li-ion and semiconductors).
3. The telecom "re-rise" failures (Pattern 2) are clearly an ontology issue (single TRL per capability), not a formula issue.
4. H4's multiple-invention-classes framework explains why one formula cannot cover all events.

Reasons for "theory wrong":
1. The formula has not achieved statistical significance in any domain.
2. The telecom domain produced 0 TPs — worse than NULL.
3. Even for emergence events (telecom 2G/3G/4G/5G), the formula fails when the ontology is correct (the capabilities ARE rising, but the model records them as plateaued).
4. The 2 real semiconductor TPs (copper, high-k) are both high-velocity (0.40), suggesting the formula only works when velocity is unambiguously high — a narrow condition.

### The honest answer

**I do not know whether the theory is wrong or the ontology is
incomplete. The CEO was correct to say "I do not think we know
the answer."**

What I can say:
1. The theory is NOT universally applicable. It fails on telecom
   and semiconductors in structured ways.
2. The theory IS applicable to emergence events in domains with
   monotonic TRL (Li-ion, partial semiconductors).
3. The boundary between "theory works" and "theory fails" is
   determined by:
   - Whether the event is emergence or exploitation (H1)
   - Whether TRL is monotonic or re-rising (H3)
   - Whether the invention class is emergence/recombination or
     scaling/coordination/discovery (H4)
4. The frozen formula cannot be modified (Rule 1), so these
   hypotheses cannot be tested by changing the formula. They
   can only be tested by:
   - Running more domains (aviation, pharmaceuticals) to see if
     the patterns hold
   - Building new formulas (post-Phase-14) that test H2
     (acceleration), H3 (multi-dimensional state), or H4
     (class-specific formulas)

### What this means for Phase 14

The CEO paused before aviation. The reflection suggests this was
correct. Running aviation and pharmaceuticals would add more data
points, but they would likely fall into the same patterns:
- Aviation: slow velocity (0.05-0.10) → Pattern 3 (threshold)
  or Pattern 1 (scaling, if events are post-maturity)
- Pharmaceuticals: non-monotonic TRL (clinical trial failures) →
  Pattern 2 (re-rise equivalent) or a new pattern (TRL drops)

The marginal value of running aviation and pharmaceuticals is
LOW if they confirm the existing patterns. The marginal value is
HIGH if they reveal a NEW pattern not in the catalog.

**Recommendation (not a decision):** Run aviation and pharmaceuticals
ONLY if there is reason to believe they will reveal a new pattern.
If they will merely confirm Patterns 1-5, the project's time is
better spent on:
- Building a new formula that tests H2 (acceleration)
- Building a multi-dimensional ontology that tests H3
- Building class-specific formulas that test H4

But these are post-Phase-14 activities. They require unfreezing
the formula or the ontology, which is outside Phase 14's scope.

---

## What this reflection does NOT do

- It does not conclude definitively. The CEO said "I do not think
  we know the answer." This reflection preserves that uncertainty.
- It does not grade itself. Per EP-5, this is self-authored
  reflection. It should be reviewed by an independent process
  (Phase 14F external adversaries) before being treated as
  evidence.
- It does not propose fixes. The formula is frozen. Any fix is a
  new formula, tested separately.
- It does not claim M5. The theory has not survived falsification.
  It has identified its own boundary, which is progress but not
  validation.

---

## Pre-stated falsifiers for claims in this document (EP-4)

| Claim | Falsifier |
|---|---|
| H1 (emergence vs exploitation) explains Patterns 1 and 4 | A domain with zero scaling events where the theory still fails. |
| H2 (acceleration) might explain Pattern 2 | A new formula using acceleration that does not outperform velocity on Li-ion. |
| H3 (TRL is wrong state variable) explains Pattern 2 | A multi-state ontology that still fails on telecom generation transitions. |
| H4 (multiple invention classes) explains Patterns 1, 2, 4 | A single-class domain where the theory still fails. |
| The theory is "ontology incomplete" not "theory wrong" | A new ontology that still produces 0 TPs on telecom. |
| The theory is "theory wrong" not "ontology incomplete" | A new formula (not ontology) that produces TPs on telecom generation transitions. |

All falsifiers are pending. None have been tested.
