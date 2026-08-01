# DELTA report — batch_002 (pre-Gap 2+7 fix) vs batch_003 (post-Gap 2+7 fix)

Date: 2026-08-01
Gap fixed: Gap 2 + Gap 7 (arbitrary dependency selection + weak causal graph)
Architecture modification: dependency_module.py ONLY (per CEO 'pick one' rule)

## Headline metrics

| Metric | batch_002 (pre-fix) | batch_003 (post-fix) |
|---|---|---|
| Unique composite scores | 18 | 18 |
| Max candidates sharing one score | 2 | 2 |
| Min composite | 0.2592 | 0.2488 |
| Max composite | 0.5777 | 0.5777 |
| Range (max-min) | 0.3185 | 0.3289 |

## What changed (Gap 2+7 fix)

The Gap 2+7 fix modified dependency_module.py's `_pick_target` method
to replace arbitrary target selection (first system node in matching
domain) with **problem-aware relevance-scored target selection**.

The new scoring:
- domain match: +3.0
- constraint keyword overlap: +1.0 per match
- problem-text keyword overlap: +0.5 per match
- node type preference: system 2.0, industry 1.5, subdomain 1.5, component 1.0
- **has prerequisites bonus: +2.0** (the key Gap 7 fix — prefer nodes
  that have outgoing requires/depends_on edges, so the causal
  classification has something to classify)

## Target selection changes (Gap 2 fix)

Before the fix: the dependency_module picked the first system node
in the matching domain, or the first system node period. All system
nodes in this graph have NO prerequisites, so:
- prerequisite chains were depth=0 for most candidates
- causal classifications were all-zero (no prereqs to classify)

After the fix: the dependency_module scores ALL nodes (not just
system nodes) by relevance AND by whether they have prerequisites.
Subdomain, component, and industry nodes that HAVE prerequisites
are preferred over system nodes that don't.

Result: targets now have non-empty prerequisite chains, and the
causal classifications are non-zero (contributing or necessary).

## Causal classification changes (Gap 7 fix)

Before the fix: causal_classifications was all-zero for most
candidates because the arbitrary system-node targets had no
prerequisites.

After the fix: most candidates now have non-zero causal
classifications (typically contributing:1, because the selected
target has 1 prerequisite that is a component node, classified
as "contributing" by the existing heuristic).

## What did NOT change

- Unique composite scores: 18 in both batches (Gap 1 fix already
  achieved this — the Gap 2+7 fix doesn't affect scoring directly).
- Max collisions: 2 in both batches (same reason).
- 0 compiler exceptions in both batches.
- The 11-layer output structure is unchanged.
- Gaps 1, 3, 4, 5, 6 are UNCHANGED. Per the CEO 'pick one' rule,
  only Gap 2+7 was addressed.

## What was modified (per the strict 'pick one' rule)

- invention_compiler/dependency_module.py: replaced `_pick_target`
  with problem-aware relevance-scored selection. Added
  `_last_target_selection` metadata. Updated `analyze()` evidence
  block to expose `target_selection` and `novel_relative_to_graph`.
- tests/test_gap2_7_fix.py: new test file (10 tests) locking the
  Gap 2+7 fix contract.
- tests/test_gap1_fix.py: updated the "only simulation_module was
  modified" test to also allow dependency_module.py (Gap 2+7
  iteration).
- scripts/run_20_invention_experiment_v3.py: copy of the experiment
  runner that writes to batch_003/. NOT a new module — a one-off
  script.
- scripts/generate_delta_report_v2.py: delta report generator for
  batch_002 vs batch_003.

## What was NOT modified

- invention_compiler/simulation_module.py: unchanged (Gap 1 — leave alone).
- invention_compiler/blueprint_module.py: unchanged (Gap 3).
- invention_compiler/orchestrator.py: unchanged (Gap 4).
- invention_compiler/prototype_module.py: unchanged (Gap 5).
- invention_compiler/chemistry_knowledge_module.py: unchanged (Gap 6).
- invention_compiler/physics_knowledge_module.py: unchanged.
- invention_compiler/mathematics_knowledge_module.py: unchanged.
- invention_compiler/constraint_module.py: unchanged.
- hypothesis/hypothesis.py: unchanged.
- loops/*: unchanged.
- layer_status/*: unchanged.
- belief/*: unchanged.
- agent/*: unchanged.

## Per the CEO directive

> Pick one. Fix it. Run all twenty inventions again. Observe what
> changes. Only then move to the next one.

This delta report is the OBSERVE step for Gap 2+7. The next
iteration will pick ONE more gap (likely Gap 3 — non-buildable
blueprints, which is Critical priority), fix it, re-run all 20
inventions, and produce batch_004/DELTA.md comparing batch_003
vs batch_004.
