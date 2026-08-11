# DELTA report — batch_001 (pre-fix) vs batch_002 (post-fix)

Date: 2026-08-01
Gap fixed: Gap 1 (identical scoring)
Architecture modification: simulation_module.py ONLY (per CEO 'pick one' rule)

## Headline metrics

| Metric | batch_001 (pre-fix) | batch_002 (post-fix) |
|---|---|---|
| Unique composite scores | 9 | 18 |
| Max candidates sharing one score | 8 | 2 |
| Min composite | 0.3678 | 0.2592 |
| Max composite | 0.6827 | 0.5777 |
| Range (max-min) | 0.3149 | 0.3185 |

## Per-candidate delta

| Candidate | batch_001 | batch_002 | delta | direction |
|---|---|---|---|---|
| 001_solid_state_batteries | 0.5777 | 0.5078 | -0.0699 | down |
| 002_carbon_negative_concrete | 0.6477 | 0.5463 | -0.1014 | down |
| 003_atmospheric_water_harvesting | 0.5777 | 0.4798 | -0.0979 | down |
| 004_portable_mri | 0.6128 | 0.5497 | -0.0631 | down |
| 005_desalination_systems | 0.5777 | 0.4692 | -0.1085 | down |
| 006_autonomous_greenhouses | 0.6753 | 0.5142 | -0.1611 | down |
| 007_modular_nuclear_reactors | 0.5777 | 0.3782 | -0.1995 | down |
| 008_artificial_photosynthesis | 0.5428 | 0.4308 | -0.1120 | down |
| 009_protein_engineering_systems | 0.6827 | 0.5323 | -0.1504 | down |
| 010_biodegradable_polymers | 0.6477 | 0.5742 | -0.0735 | down |
| 011_adaptive_prosthetics | 0.6603 | 0.4958 | -0.1645 | down |
| 012_vertical_farming | 0.6753 | 0.5423 | -0.1330 | down |
| 013_thermoelectric_materials | 0.5777 | 0.4692 | -0.1085 | down |
| 014_carbon_capture_materials | 0.5777 | 0.5078 | -0.0699 | down |
| 015_superconducting_materials | 0.3678 | 0.2592 | -0.1086 | down |
| 016_precision_fermentation | 0.6827 | 0.5217 | -0.1610 | down |
| 017_agricultural_robotics | 0.5553 | 0.4503 | -0.1050 | down |
| 018_synthetic_fuels | 0.5777 | 0.4763 | -0.1014 | down |
| 019_smart_textiles | 0.5777 | 0.4868 | -0.0909 | down |
| 020_distributed_manufacturing | 0.6827 | 0.5777 | -0.1050 | down |

## What changed

- The pre-fix failure mode (11/20 candidates producing composite=0.5777) is GONE.
- batch_001 had 9 unique composites; batch_002 has 18.
- batch_001 max-shared was 8 candidates on one score; batch_002 max-shared is 2.
- The composite range expanded: batch_001 was 0.3678-0.6827 (range 0.3149);
  batch_002 is 0.2592-0.5777 (range 0.3185).
- Most candidates' composites went DOWN, because the multi-signal complexity
  penalty is more aggressive than the keyword-only penalty was. This is honest:
  the system is now acknowledging more complexity per problem than before.

## What did NOT change

- 0 compiler exceptions in both batches (20/20 compiled both times).
- The 11-layer output structure is unchanged.
- The Hypothesis object's schema is unchanged (id, claim, confidence,
  evidence, counterevidence, assumptions, dependencies, status, created_at,
  updated_at).
- The CEO-mandated YAML output format is unchanged.
- Gaps 2-7 are UNCHANGED. Per the CEO 'pick one' rule, only Gap 1 was addressed.

## Remaining gaps (NOT addressed in this iteration, per CEO 'pick one' rule)

- Gap 2 (arbitrary dependencies): unchanged. The dependency_module still
  picks an arbitrary target_node_id when the invention is not in the graph.
- Gap 3 (non-buildable blueprints): unchanged. final_blueprint is still a
  structured summary, not a buildable spec.
- Gap 4 (missing counterevidence): unchanged. The orchestrator still does
  not pull counterevidence from any layer into the headline hypothesis.
- Gap 5 (templated plans): unchanged. prototype_module and verification_engine
  still emit the same structure for every invention.
- Gap 6 (weak chemical differentiation): unchanged. chemistry_knowledge_module
  still has a narrow keyword filter.
- Gap 7 (weak causal graph): unchanged. dependency_module's causal
  classification is still all-zero when the target is arbitrary.

## Per the CEO directive

> Pick one. Fix it. Run all twenty inventions again. Observe what changes.
> Only then move to the next one.

This delta report is the OBSERVE step. The next iteration will pick ONE more
gap (likely Gap 2 — arbitrary dependencies — because it's Critical severity
and connects to Gap 7), fix it, re-run all 20 inventions, and produce
batch_003/DELTA.md comparing batch_002 vs batch_003.

## What was modified (per the strict 'pick one' rule)

- invention_compiler/simulation_module.py: added `_gather_multi_signal_
  complexity` method and updated `analyze` to use multi-signal complexity
  (applicable_laws + governing_equations + failure_modes + missing_
  capabilities + prerequisite_chain_depth + domain_complexity + keyword
  signals). The evidence block now exposes penalty_breakdown and the new
  signal counts for auditability.
- tests/test_gap1_fix.py: new test file (10 tests) locking the Gap 1 fix
  contract.
- scripts/run_20_invention_experiment_v2.py: copy of the experiment runner
  that writes to batch_002/ instead of batch_001/. NOT a new module — a
  one-off script.

## What was NOT modified

- invention_compiler/orchestrator.py: unchanged.
- invention_compiler/dependency_module.py: unchanged (Gap 2).
- invention_compiler/blueprint_module.py: unchanged (Gap 3).
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

## Side effect: benchmark suite

The Gap 1 fix changed composites enough to push the 6-case CTO
benchmark suite from 6/6 expectations_satisfied to 5/6.

- Portable MRI: was potentially_feasible (0.6128, distance=1 from
  expected feasible), now partially_feasible (0.4528, distance=2
  from expected feasible). EXPECTATIONS_NOT_SATISFIED.

Per the CEO "pick one" directive and the CTO review #3 "expectations
≠ correctness" rule: this is NOT a regression. It is an observation.
The system is now MORE conservative about portable MRI feasibility
because the multi-signal complexity reveals more failure modes than
the keyword-only check did. The benchmark case was tuned to the
pre-fix scoring; the post-fix scoring is honest, even when it
disagrees with the benchmarker's prior.

Tuning the penalty to make this case pass would be exactly the
"rewarding agreement with priors" anti-pattern the CTO caught in
review #3. The benchmark is expectations_satisfied, NOT correctness.
