# EVIDENCE_STANDARDS

**Status:** Addendum to CONSTITUTION.md.
**Location:** repo root.
**Triggered by:** Phase 13 retrospective leakage (TIME_REVERSAL_PROTOCOL.md written with outcomes known), self-graded explanatory-depth audit (MECHANISM_REGISTRY.md explanations graded DEEP by their own author), post-hoc threshold (CROSS_DOMAIN_STRESS_TEST.md 2-of-4 criterion written in the same session as the synthesis that uses it), silent scope change (inevitability → susceptibility mid-synthesis without marking the original falsified).

These rules apply to every artifact produced after this commit. They
apply retroactively as labels, not as edits — Phase 13 documents that
violate them are retitled in place (Commit C of this governance pass),
not deleted, per the FAILURES.md convention that the failure record
has value.

---

## EP-1. No claim without an artifact in the same message.

"Pushed," "verified," "tests pass," "committed" are not receipts. The receipt
is the git log output, the diff, the test runner output, the JSON — pasted,
not summarized. No artifact attached means the claim doesn't exist yet.

## EP-2. A check is scoped to exactly what it checked.

Confirming no leakage in `run_ablation.py` says nothing about
`TIME_REVERSAL_PROTOCOL.md`. Name the file/function checked. A clean result
in one artifact does not imply cleanliness elsewhere in the same phase.

## EP-3. Any precondition or explanation for a historical event must be selected
before the outcome is known to whoever is selecting it — or it gets labeled
a consistency check, not evidence.

If you already know Li-ion succeeded and then go looking for which
preconditions were present, you will always find them. The only valid form:
freeze the graph at `Y-k`, generate predictions forward, then check the
outcome. Anything else is "retrospective consistency check" in the document
itself, never "backward explanatory power" or "validated."

## EP-4. No explanatory claim ("necessary," "deep," "sufficient," "fundamental")
ships without a pre-stated falsification condition, written before the
analysis that tests it.

If you can't state what observation would prove the claim false, it's a
narrative device — label it a hypothesis, not a finding.

## EP-5. No self-grading.

Whoever wrote the explanation does not grade its depth or correctness.
Either the human grades it against a pre-agreed rubric, or an independent
process grades it blind to which case is TP/FP/counterexample. Same-author,
same-session grades get deleted before they reach a synthesis doc.

## EP-6. Thresholds are committed before the test that uses them runs, not
alongside the results.

A threshold written in the same commit or session as the document evaluating
against it is not pre-registration — it's a number chosen with the answer
already visible. Commit criteria as their own artifact first, run the test
as a separate, later step.

## EP-7. Redefining the target is a retraction, not a rewording.

If "inevitability" becomes "susceptibility" mid-document, the original
claim is marked `FALSIFIED`, with the reason stated, before the new target is
introduced. Scope changes are argued for explicitly or they don't happen.

## EP-8. Precision without a recall/denominator is not a result.

Every precision number ships with total actual positives (`TP+FN`) in the
same table. If the denominator isn't computed, say so — don't publish the
ratio alone.

## EP-9. Equivalence claims require per-unit data, not the aggregate.

"Formula B ≈ velocity+adjacency" needs the raw per-T score arrays shown, not
just matching TP/FP counts. Two formulas can agree on aggregate counts while
ranking differently underneath.

## EP-10. No new phase starts until the previous phase's open items are
resolved or explicitly deferred with a stated reason.

Documentation volume is not progress if it sits on an unverified base — it
just makes the eventual audit longer.

## EP-11. Strip promotional language from technical deliverables.

"Most epistemologically important," "the CEO mandated," "stronger, not
weaker" — describe what was done and what it shows, flatly. If a result
needs adjectives to be convincing, it isn't convincing yet.

## EP-12. Diff before commit, always.

Show the file change and let it be reviewed before committing. Narrating a
completed action and demonstrating one are different acts — only the
second counts as done.
