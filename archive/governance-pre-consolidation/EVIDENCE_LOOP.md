# EVIDENCE_LOOP

**Status:** Enforcement protocol for `EVIDENCE_STANDARDS.md` (EP-1 to EP-12).
**Location:** repo root.
**Phase:** Post-Phase-13 governance.

This document defines the operational loop that converts EP-1 through
EP-12 from prose rules into gates. Each gate is checkable. Each gate
either passes (artifact present, condition met) or fails (claim
cannot ship).

The loop has three checkpoints: pre-claim, pre-commit, pre-phase.
Each checkpoint has a fixed checklist. The checklists are run by the
coder (manual) and may be re-run by any reviewer.

---

## Checkpoint 1: Pre-claim (run before asserting any state-changing sentence)

For any sentence of the form "X is verified / pushed / tested /
committed / measured / achieved / falsified / confirmed":

| # | Check | Pass condition |
|---|---|---|
| 1.1 | Is the artifact attached in the same message? | A git log line, a diff, a JSON path, a test runner output, or a file path — pasted, not summarized. If no artifact, the sentence is deleted, not weakened. (EP-1) |
| 1.2 | Is the check scoped to exactly what was checked? | The file or function name is named. A clean result in `run_ablation.py` does not license a claim about `TIME_REVERSAL_PROTOCOL.md`. (EP-2) |
| 1.3 | If the claim is about a historical event's preconditions, was the precondition selected before the outcome was known? | If yes, ship as evidence. If no, ship as "retrospective consistency check" with that label in the sentence. Never "validated" or "backward explanatory power." (EP-3) |
| 1.4 | If the claim uses the word "necessary," "sufficient," "deep," or "fundamental," is a falsification condition pre-stated? | The falsifier must be in `EVIDENCE_FALSIFIERS.md` (created in Commit B of this governance pass) or in the document itself, with a date prior to the analysis. (EP-4) |
| 1.5 | If the claim is graded (deep / partial / none, strong / weak, etc.), was the grading done by an independent process? | The grader's identity and rubric are stated. Same-author, same-session grades are deleted, not published. (EP-5) |
| 1.6 | If the claim cites a threshold, was the threshold committed before the test that uses it? | The threshold's commit hash pre-dates the test's commit hash. Same-commit thresholds are rejected. (EP-6) |
| 1.7 | If the claim redefines a target, is the original marked `FALSIFIED` first? | The retraction appears before the new target is introduced. (EP-7) |
| 1.8 | If the claim cites a precision number, is the denominator (TP+FN) shown in the same table? | If not, the precision is withheld until the denominator is computed. (EP-8) |
| 1.9 | If the claim is an equivalence (X ≈ Y), are per-unit arrays shown, not just aggregate counts? | The raw per-T / per-case data is in the same message or cited file. (EP-9) |
| 1.10 | Does the sentence use promotional language? | "Most," "strongest," "groundbreaking," "mandated" (when describing one's own work), "robust" — delete or replace with a measurement. (EP-11) |

If any check fails, the sentence is not shippable. The coder edits
the sentence until all checks pass, or removes the sentence.

---

## Checkpoint 2: Pre-commit (run before `git commit`)

| # | Check | Pass condition |
|---|---|---|
| 2.1 | Has the diff been shown in the conversation, not just narrated? | The `git diff` output is in the message prior to the commit command. (EP-12) |
| 2.2 | Does the commit message use promotional language? | Same rule as 1.10. The commit message describes what was done; it does not characterize its importance. |
| 2.3 | If the commit introduces a threshold or criterion, is it a standalone commit (no test results in the same commit)? | The threshold commits first; the test that uses it commits later. (EP-6) |
| 2.4 | If the commit introduces a graded artifact, is the grader independent? | Same rule as 1.5. (EP-5) |
| 2.5 | If the commit redefines a target, does the same commit (or a prior commit) mark the original target `FALSIFIED`? | The retraction precedes the new target. (EP-7) |
| 2.6 | If the commit ships a precision number, is the denominator present in the same commit? | (EP-8) |
| 2.7 | If the commit ships an equivalence claim, are per-unit arrays present in the same commit or referenced in a prior artifact? | (EP-9) |
| 2.8 | Does the previous phase have open items? If yes, are they resolved or explicitly deferred with a stated reason in the commit message? | (EP-10) |
| 2.9 | If the markdown cites specific numbers from a JSON or other persisted artifact, do those numbers exist in the artifact at the cited path? | Grep each cited number against the artifact's actual fields. If the artifact has `null` or is missing the field the markdown cites, the commit fails. (EP-1, EP-12 — added per F-042) |

If any check fails, the commit is not made. The coder resolves the
failure and re-runs the checklist.

---

## Checkpoint 3: Pre-phase (run before starting Phase N+1)

| # | Check | Pass condition |
|---|---|---|
| 3.1 | Are all open items from Phase N resolved or explicitly deferred? | Each open item has a resolution commit or a deferral note with a reason. (EP-10) |
| 3.2 | Does the new phase's plan pre-state the falsification conditions for any explanatory claims it intends to make? | Falsifiers are written into the plan document before the analysis runs. (EP-4) |
| 3.3 | Does the new phase's plan specify who grades its outputs? | Either the human (with rubric) or an independent subagent (blind to TP/FP status). Same-author grading is forbidden. (EP-5) |
| 3.4 | Does the new phase's plan commit any thresholds as standalone artifacts before any test that uses them? | Thresholds land in their own commit, dated before the test commits. (EP-6) |
| 3.5 | If the new phase will redefine any target from prior phases, is the retraction scheduled to land before the new target? | (EP-7) |
| 3.6 | Does the new phase's plan include a "precondition selection" protocol that freezes the graph at `Y-k` before generating predictions? | If the phase will make claims about historical events, the precondition-selection protocol is forward-only. (EP-3) |

If any check fails, the phase does not start. The coder amends the
plan document until all checks pass.

---

## Loop diagram

```
   ┌──────────────────────────────────────────────────┐
   │  Pre-phase gate (Checkpoint 3)                    │
   │  Plan has falsifiers, graders, thresholds pre-stated │
   └──────────────────────────────────────────────────┘
                       │ pass
                       ▼
   ┌──────────────────────────────────────────────────┐
   │  Phase work                                       │
   │  Each artifact: precondition selection forward-only│
   └──────────────────────────────────────────────────┘
                       │
                       ▼
   ┌──────────────────────────────────────────────────┐
   │  Pre-claim gate (Checkpoint 1)                   │
   │  Every sentence with "verified / pushed / etc."  │
   │  has an artifact attached, scoped, falsifier-stated│
   └──────────────────────────────────────────────────┘
                       │ pass
                       ▼
   ┌──────────────────────────────────────────────────┐
   │  Pre-commit gate (Checkpoint 2)                  │
   │  Diff shown, no promotional language, thresholds  │
   │  are standalone, denominators present             │
   └──────────────────────────────────────────────────┘
                       │ pass
                       ▼
                    git commit
                       │
                       ▼
              (loop back to Pre-claim
               for the next artifact)
```

---

## Falsifier tracker

A companion file `EVIDENCE_FALSIFIERS.md` tracks every explanatory
claim the project makes and its pre-stated falsifier. Each entry:

```typescript
interface FalsifierEntry {
    claimId: string;          // e.g., "NEC-001"
    claimText: string;         // the explanatory claim
    falsifierText: string;     // the observation that would prove it false
    statedAt: string;          // ISO date and commit hash
    testedAt: string | null;  // when the test ran, or null if pending
    testResult: "CONFIRMED" | "FALSIFIED" | "PENDING" | null;
}
```

`EVIDENCE_FALSIFIERS.md` is created in Commit B of this governance
pass and seeded with the falsifiers for the surviving claims from
Phase 13 (the velocity × adjacency equivalence claim — falsifier:
any per-T array divergence; the necessity claim — falsifier: a TP
with rising-capability velocity below 0.20 at T-1).

---

## What this loop does NOT enforce

The loop is a checklist, not a guarantee. It cannot detect:

- Subtle semantic leakage (a precondition selected with outcome
  knowledge but framed neutrally).
- Thresholds that are pre-committed but chosen with implicit
  knowledge of likely outcomes.
- Self-grading done by an "independent" subagent that shares the
  coder's priors.

The loop catches the obvious violations. Subtle violations require
external audit — the same role the human plays in this conversation.

---

## Application to Phase 13 documents

Five Phase 13 documents violated EP rules at commit time. Per
the FAILURES.md convention (P66, account-deletion bug, F-035
through F-040) the failure records are retained, not deleted.
Commit C of this governance pass retitles each violating document
with a header that states the violation:

| Document | Violation | New header label |
|---|---|---|
| TIME_REVERSAL_PROTOCOL.md | EP-3 | "Retrospective consistency check; not evidence" |
| MECHANISM_REGISTRY.md | EP-5 | "Self-authored explanations; not independently graded" |
| NECESSITY_SUFFICIENCY.md | EP-4 | "Necessity claim has no pre-stated falsifier; treat as hypothesis" |
| CROSS_DOMAIN_STRESS_TEST.md | EP-6 | "Threshold not pre-registered; treat as proposal" |
| PHASE_13_SYNTHESIS.md | EP-5, EP-7 | "Relies on self-graded depth; contains silent scope change" |

The retitlings are append-only header additions. The original
content is unchanged (per CONSTITUTION.md Law 7, historical
permanence).
