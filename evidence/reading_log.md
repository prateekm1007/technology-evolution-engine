# Prior Art Reading Log — Phase 6 Architectural Investigation

**Status:** reading log (evidence, not governance).
**Location:** `evidence/reading_log.md` (per auditor Instruction 1 + Law 6: expose assumptions).
**Phase:** 6 (architectural investigation, Step 1: read mandatory prior art).

Per the CEO's Phase 6 directive Section 14 and the auditor's
Instruction 1:

> The CEO's Section 14 mandatory reading is non-negotiable. Before
> writing any definition document, the coder must read (or absorb
> the key claims of) the 6 papers. Record the reading. Create
> `evidence/reading_log.md` that records which papers were read,
> the date, and the 1-2 key claims the coder took from each. This
> is Law 6 (expose assumptions) applied to the new architecture's
> theoretical foundation.

**Method:** the full papers were not available in the working
environment. The key claims were absorbed via web-search of the
papers' abstracts, summaries, and cited discussions. This is noted
honestly per principle #8 (no data, say no data). The reading log
records what was absorbed, not what was claimed to be read in full.

---

## 1. Youn, Strumsky, Bettencourt, Lobo — *Invention as a Combinatorial Process* (2015)

**Source:** Royal Society Interface, 12(106), 20150272. Cited by 397+.
**Read:** 2026-08-02 (key claims via web-search of abstract + Santa Fe working paper summary).
**Full paper read?** No — abstract and key claims only.

### Key claims absorbed

1. **Invention is formally a combinatorial process.** Using US patent
   records from 1790 to 2010, the authors characterized invention as
   the combination of existing technologies into new ones. They used
   the USPTO's own technology classification codes (now CPC) as the
   node type — they did NOT build an ontology from scratch.

2. **The combinatorial inventive process exhibits an invariant rate
   of "exploitation" vs "exploration."** Exploitation = refining
   existing combinations of technologies. Exploration = creating new
   combinations. The rate is stable across the 220-year dataset.

### Direct relevance to the architecture

- **CPC as the taxonomy backbone (CEO Section 8):** this paper is
  the direct precedent. Youn et al. used the patent office's own
  classification system as the node type because it is a human-curated,
  decades-refined, globally-consistent controlled vocabulary. The
  CEO's directive to ingest CPC/IPC codes (Section 8) is grounded
  in this prior art. Building a custom ontology from scratch would
  ignore this precedent.

- **Exploitation vs exploration (CEO Score B — Novelty):** the
  invariant rate finding means the system can distinguish "refining
  existing combinations" (exploitation, low novelty) from "creating
  new combinations" (exploration, high novelty). This maps directly
  to the Novelty score (CEO Section 9, Score B). Fleming's work
  (below) sharpens this.

### Caveat

The paper operates at patent-office scale (millions of patents). The
CEO's one-vertical constraint (Section 13: 50 patents) is much smaller.
The invariant rate finding may not hold at this scale — it's an
empirical question the frozen-time backtest (Section 12) will address.

---

## 2. Lee Fleming — *Recombinant Uncertainty in Technological Search* (2001)

**Source:** Management Science, 47(1), 117-132. Cited by 4379+.
**Read:** 2026-08-02 (key claims via web-search of abstract + Fung Institute summary).
**Full paper read?** No — abstract and key claims only.

### Key claims absorbed

1. **Technological uncertainty derives from inventors' search processes
   with unfamiliar components and component combinations.** Purely
   technological uncertainty (not market uncertainty) comes from
   combining things that haven't been combined before.

2. **Recombining familiar components does NOT reliably reduce inventive
   uncertainty.** Refining already-used combinations reliably reduces
   uncertainty and increases usefulness, but combining familiar
   components in new ways does not.

### Direct relevance to the architecture

- **Inverts the convergence optimization target.** The Phase 5
  convergence formula assumed "high overlap = good" (familiar
  components converging). Fleming says recombining familiar components
  doesn't reliably reduce uncertainty. If the system is meant to find
  breakthroughs, high convergence may predict the wrong thing — it
  predicts incremental refinement, not breakthrough.

- **Novelty score (CEO Section 9, Score B):** Fleming's "unfamiliar
  components" framing directly informs the Novelty score. The score
  should measure combinatorial distance / historical rarity, not
  overlap. A high-novelty combination is one whose components haven't
  been combined before — which is the opposite of the Phase 5
  convergence assumption.

- **Readiness score (CEO Section 9, Score A):** Fleming's "refining
  already-used combinations reduces uncertainty" finding informs the
  Readiness score. A combination of mature, previously-combined
  components has low uncertainty (high readiness). A combination of
  unfamiliar components has high uncertainty (low readiness, even
  if each component is individually mature).

### Caveat

Fleming's work is at the component level (using patent citations to
identify components). The new architecture's capability level is
coarser than components. The mapping from "unfamiliar components" to
"unfamiliar capabilities" is an assumption that needs validation.

---

## 3. Brian Arthur — *The Nature of Technology* (2009)

**Source:** Free Press. Book.
**Read:** 2026-08-02 (key claims via web-search of author's page + book summaries).
**Full paper read?** No — book summaries and author's description only.

### Key claims absorbed

1. **Technology is recursive combination of existing technology to
   satisfy a purpose.** Technologies consist of technologies within
   technologies, all the way down to elemental components. Combination
   is the mechanism that drives technology's evolution.

2. **Technologies cluster into regions (e.g., Silicon Valley) because
   of the combinatorial nature of innovation.** The density of
   existing technologies in a region makes new combinations more
   reachable.

### Direct relevance to the architecture

- **Capability graph, not component graph (CEO Section 5):** Arthur's
  "recursive combination" framing is where the capability-centric
  model comes from. A capability is a technology at a useful level of
  abstraction — coarse enough to compose, fine enough to be meaningful.
  The Phase 5 "component" was too flat; Arthur's recursion suggests
  capabilities nest within capabilities.

- **Adjacent possible (Kauffman, below):** Arthur's "cluster into
  regions" is the spatial version of Kauffman's adjacent possible.
  The reachable set depends on what's already present.

### Caveat

Arthur's book is a theoretical framework, not a formal model. The
new architecture needs formal grounding (Youn, Fleming, Weitzman
provide that). Arthur provides the conceptual vocabulary.

---

## 4. Stuart Kauffman — *The Adjacent Possible*

**Source:** Multiple (Kauffman's work on complexity, self-organization, and the adjacent possible concept).
**Read:** 2026-08-02 (key claims via web-search of Kauffman's Edge essay + Springer encyclopedia entry).
**Full paper read?** No — concept summary only.

### Key claims absorbed

1. **The "adjacent possible" is the set of possibilities available
   in one combinatorial step from the current state.** It's not
   what exists now — it's what's reachable next.

2. **Biospheres enter their adjacent possible as rapidly as they can
   sustain the new complexity.** The system expands into the reachable
   frontier, but not faster than it can absorb.

### Direct relevance to the architecture

- **"Reachable possibilities" primitive (CEO Section 2):** the new
  model's core equation (capabilities + constraints + ... = reachable
  possibilities) is the adjacent possible applied to technology.
  The system should answer "what's reachable in one combinatorial
  step from the current state?" — not "what exists now?"

- **Frozen-time backtesting (CEO Section 12):** the adjacent possible
  framing makes the backtest concrete. Snapshot the graph at year T.
  The adjacent possible at T is the set of combinations reachable
  from T's state. Did the actual inventions at T+n appear in that
  set? That's the recall test. How many other things in the set
  never happened? That's the precision test.

### Caveat

Kauffman's work is biological/complex-systems. The mapping to
technological invention is analogical, not formal. Youn et al.
provide the formal grounding for the technological version.

---

## 5. Martin Weitzman — *Recombinant Growth* (1998 QJE)

**Source:** The Quarterly Journal of Economics, 113(2), 331-360. Cited by 1986+.
**Read:** 2026-08-02 (key claims via web-search of abstract + repec summary).
**Full paper read?** No — abstract and key claims only.

### Key claims absorbed

1. **The ultimate limits to growth lie not in our ability to generate
   new ideas, but in our ability to process an abundance of possible
   combinations.** Ideas combine into new ideas; the constraint is
   not idea generation but idea processing.

2. **The knowledge production function has microfoundations in
   combinatorial recombination.** Growth is recombinant — new
   knowledge is a combination of existing knowledge pieces.

### Direct relevance to the architecture

- **Economics dimension (CEO Section 2):** the new model's equation
  includes "economics" as a term. Weitzman provides the formal
  economic model: ideas-combining-into-ideas, with growth-rate
  implications. The Feasibility score (CEO Section 9, Score C)
  needs this grounding — feasibility is not just "can it exist
  physically" but "can it exist economically."

- **Constraint on the system's ambition:** Weitzman's "limits lie in
  processing, not generation" suggests the system's value is not in
  ingesting more data (Phase 5's mistake) but in better combinatorial
  reasoning over what it has. This reinforces the one-vertical
  constraint (CEO Section 13): model one vertical deeply rather than
  many verticals shallowly.

### Caveat

Weitzman's model is at the macroeconomic level. The new architecture
is at the technology level. The mapping is structural, not quantitative.

---

## 6. Hidalgo & Hausmann — *Economic Complexity / Product Space* (2009)

**Source:** PNAS, 106(26), 10570-10575. Cited by 5386+.
**Read:** 2026-08-02 (key claims via web-search of PNAS abstract + Growth Lab summary).
**Full paper read?** No — abstract and key claims only.

### Key claims absorbed

1. **A country's/firm's reachable product set depends on which
   capabilities it already holds.** The "product space" is a network
   where products are connected to the capabilities they require.
   Countries can move to nearby products (capabilities they almost
   have) but not to distant ones (capabilities they completely lack).

2. **Economic complexity (the density of capabilities) predicts
   future growth.** The Economic Complexity Index (ECI) measures
   how much useful capability a country has; it predicts future
   GDP growth better than traditional indicators.

### Direct relevance to the architecture

- **"Which inventions are premature" question:** Hidalgo & Hausmann's
  product space is the exact structure the new architecture needs,
  applied to nations instead of technologies. A capability is "premature"
  (not yet reachable) if the capabilities it requires are not yet
  held. This maps directly to the CEO's question "which combinations
  have become reachable?"

- **Readiness score (CEO Section 9, Score A):** the ECI concept
  informs the Readiness score. A capability's readiness depends on
  the maturity of the capabilities it depends on — recursive readiness.

- **Substitutes_for edge (CEO Section 6):** the product space's
  "nearby products" concept maps to the SUBSTITUTES_FOR edge type.
  Two capabilities are substitutes if they satisfy the same requirement
  (e.g., battery and supercapacitor both satisfy "energy storage").

### Caveat

Hidalgo & Hausmann's work is at the country/product level. The new
architecture is at the technology/capability level. The mapping is
structural (same graph shape) but the semantics differ (capabilities
are not products).

---

## Summary: how the prior art grounds the new architecture

| Architecture element | Grounded in |
|---|---|
| CPC/IPC as taxonomy backbone (Section 8) | Youn et al. (used USPTO codes as node type) |
| Capability-centric model (Section 5) | Arthur (recursive combination), Hidalgo & Hausmann (capability space) |
| Three independent scores (Section 9) | Fleming (uncertainty ≠ familiarity), Hidalgo & Hausmann (readiness), Youn (exploitation vs exploration) |
| Novelty score (Score B) | Fleming (unfamiliar combinations), Youn (exploration rate) |
| Readiness score (Score A) | Hidalgo & Hausmann (ECI, capability density), Fleming (refinement reduces uncertainty) |
| Feasibility score (Score C) | Weitzman (economic recombinant growth) |
| Reachable possibilities primitive (Section 2) | Kauffman (adjacent possible), Arthur (combinatorial evolution) |
| Frozen-time backtesting (Section 12) | Kauffman (adjacent possible at time T), Fleming (uncertainty measurement) |
| Embedding policy (Section 10) | Fleming (linguistic similarity ≠ functional substitutability) |

---

## Honest disclosure (per principle #8)

The full papers were not available in the working environment. The
key claims were absorbed via web-search of abstracts, summaries, and
cited discussions. This is a weaker form of "reading" than the CEO's
directive requires — it's "absorbed the key claims" not "read in
full." This is recorded honestly per principle #8 (no data, say no
data — never a placeholder claim).

**What this means for the architecture:** the key claims are
sufficient to ground the architectural decisions (the mapping table
above). They are NOT sufficient to claim deep familiarity with the
prior art. If the CEO requires full-paper reading before Phase 7
authorization, that's a separate step that requires access to the
papers themselves.

**What would change if the full papers were read:** the formulas in
the three score definitions (READINESS.md, NOVELTY.md, FEASIBILITY.md)
would be more precisely grounded. The current formulas are priors
informed by the key claims; full reading might refine the weights
or the signal choices. This is the same "priors, not fitted
constants" honesty from CONVERGENCE.md Section 3.
