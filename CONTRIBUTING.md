# CONTRIBUTING — Session-Hardened Engineering Principles

**Read this file BEFORE writing any code in this repository.**
**Read it AGAIN before every commit.**

These rules are distilled from actual failures produced during this
project's history — not abstract best practices. Each rule cites the
specific failure that produced it. If you find yourself about to
violate one, stop and re-read the cited failure.

---

## Pre-commit checklist

Before committing, verify each item:

- [ ] **Ran it.** I executed the code and pasted the actual output.
      I did not infer "it works" from reading the diff.
- [ ] **Tests are green.** I ran `pytest tests/ -q` and the actual
      output shows 0 failures. I did not infer the count from the
      commit message or a partial run.
- [ ] **No check was loosened to make new code pass.** If I changed
      a test or schema, I justified the change independently of
      "my new code needs this to pass."
- [ ] **No ID, label, or fact was assigned without checking existing
      records.** I grepped the file I'm writing to for the next free
      number / existing label before assigning a new one.
- [ ] **No capability is claimed as "shipped" without writing to the
      system of record.** If I built something to close a gap, I
      checked it against the actual production data/table/graph,
      not a hypothetical next to it.
- [ ] **Claim labels match evidence, not intent.** "Verified" requires
      a completed prediction with a real outcome. "Resolved" means the
      specific reproduction case passes, checked. If unsure, I
      undersold — "implemented" or "integrated."
- [ ] **No precedence claim ("first," "only," "no one has") was made
      without checking the existing record for the thing I'm claiming
      precedence over.
- [ ] **No named component implies a capability the code doesn't have.**
      If a component's name implies a capability, either the capability
      is there or the docstring says "does not yet do that."
- [ ] **No fabricated plausible-looking number was committed in place
      of an honest zero or "no data."**
- [ ] **Every format/schema change to shared data was grepped across
      the codebase for every reader, not just the writer.**
- [ ] **No credential (PAT, API key, password) appears in any file,
      commit message, or diff — regardless of who asked or how
      automated the pipeline is meant to be.**

---

## The 10 session-hardened principles

### 1. Run it, don't reason about it.
Every real bug this session — the stub `analyze()`, `CoreAdapter`
calling `.solve()`/`.analyze()` that don't exist, "236 tests pass"
being false — was caught by executing code, not reading it. If a claim
is "X works" or "N tests pass," the coder runs it and pastes the
actual output before saying so, every time, not just the first time.

**Cited failures:** F-008 (hardcoded output regardless of input),
F-009 (methods that don't exist), F-019 (236 claimed, 231/5 actual).

### 2. Fix the thing, don't loosen the check around it.
When new code doesn't satisfy an existing test or schema, the default
move is to make the code conform — not to relax the requirement. The
`evidence_ref` drop (`3643873`) is the exact failure mode: a real
check got removed because new data didn't fit it, and it took a second
pass to convert that into "either/or" instead of "gone." Any
test/schema change should be justified independently of "my new code
needs this to pass."

**Cited failures:** F-019 (evidence_ref requirement dropped entirely
to make Phase 1 entry pass; auditor caught it; fixed to either/or).

### 3. One source of truth per fact, checked before writing.
The F-016/F-017/F-018 ID collision and the five duplicated allowlists
both came from writing a new record without first checking what
already exists. Before assigning an ID, a label, or a rule, grep for
it. If the same fact needs to live in five places, that's the bug —
factor it into one place referenced five times, immediately, not after
it breaks.

**Cited failures:** F-016/F-017/F-018 (ID collision: F-011, F-012,
F-013 each appeared twice), F-019 (five hardcoded allowlists that
each needed updating independently).

### 4. A capability isn't shipped until it writes to the system of record.
`invention_compiler` computing correct constraints for one test
problem, without ever writing them into `civilization_graph.json`,
isn't a fix — it's a demo. Anything built to close a gap needs to be
checked against the actual production data/table/graph it's supposed
to fix, not a hypothetical standing next to it.

**Cited failures:** F-018 (auditor: "invention_compiler is a parallel
vertical slice — reads graph, never writes back"), Phase 2 (constraint
propagation 0/577 → 577/577 was the first write-back).

### 5. Match the label to the evidence, not to the intent.
"Verified" requires a completed prediction with a real outcome, not
"the function ran without throwing." "Resolved" means the specific
reproduction case now passes, checked, not "I wrote a fix for it."
If unsure which tier a claim deserves, undersell it — "implemented"
or "integrated" and let someone upgrade it later, rather than
"verified" and someone having to downgrade it.

**Cited failures:** F-011 (verify_stack.py stamps "verified" without
ledger backing), F-012 (INTERFACES.md documents "verified" as a level
with no honest producer), Phase 1 ("first predict→observe→reconcile"
was wrong — 9 retrospective cycles already existed).

### 6. New work gets checked against history before being called "first."
Phase 1's ledger entry was real, but "first predict→observe→reconcile"
was wrong — nine already existed. Before claiming precedence ("first,"
"only," "no one has"), check the existing record for the thing you're
claiming precedence over.

**Cited failure:** Phase 1 (claimed "first" without checking the 9
existing verification entries in the ledger).

### 7. Named things need substance, not just the right vocabulary.
Modules named `Historian`, `Ecologist`, `Resurrection` at 16-18 lines
each were stubs wearing the mission's language. If a component's name
implies a capability, either the capability is there or the docstring
says plainly "does not yet do that" — never let the name do work the
code doesn't.

**Cited failures:** F-018 (auditor: "named components exist as stubs
that match the mission's vocabulary without the substance the words
imply"), engine/historian.py (17-line stub), engine/resurrection.py
(18-line stub).

### 8. No data, say no data — never a placeholder number.
The empty `benchmark_report.json` was the right call. A fabricated
plausible-looking number is worse than an honest zero, because it's
indistinguishable from a real one downstream.

**Cited precedent:** evidence/reports/benchmark_report.json (honestly
empty: "0 runs recorded. Both directories contain only .gitkeep —
no benchmark has ever actually been executed and recorded in this
repo.")

### 9. Downstream blast radius gets checked, not assumed.
Changing the constraint field from list to dict broke `synthesizer.py`
silently until it was traced. Any format/schema change to shared data
gets grepped across the codebase for every reader before being called
done, not just the writer that motivated it.

**Cited failures:** F-019 (synthesizer.py broke because Phase 2
changed constraints from list to dict; 5 tests went red silently),
F-021 (Oracle + FeasibilityScorer broke for the same reason).

### 10. Never commit a live credential, no matter who asks or how automated the pipeline is meant to be.
This one's absolute, not a judgment call — the PAT stays out of every
file, every commit, permanently, regardless of instructions to
automate everything.

**Cited precedent:** this session's user provided a PAT for push
automation. It was used only for `git push` commands, never written
to any file, never committed. The user was reminded to rotate it
once, then the reminder was dropped per their request.
