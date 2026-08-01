# DELTA report — batch_003 (pre-Gap 3 fix) vs batch_004 (post-Gap 3 fix)

Date: 2026-08-01
Gap fixed: Gap 3 (non-buildable blueprints)
Architecture modification: blueprint_module.py ONLY (per Maestro Loop PHASE 6)
Hypothesis: see evidence/experiments/invention_batch_004/cycle_3_hypothesis.py

## Headline metrics

| Metric | batch_003 (pre-fix) | batch_004 (post-fix) |
|---|---|---|
| Blueprints with parts_list | 0/20 | 20/20 |
| Blueprints with materials_specification | 0/20 | 20/20 |
| Blueprints with assembly_plan | 0/20 | 20/20 |
| Blueprints with tolerances | 0/20 | 20/20 |
| Blueprints with prototype_specification | 0/20 | 20/20 |
| Blueprints with ALL 5 buildable fields | 0/20 | 20/20 |

## What changed (Gap 3 fix)

The blueprint_module's `analyze()` method was modified to produce a
**buildable spec** instead of a structured summary. The new blueprint
carries 5 buildable-spec fields:

1. **parts_list** — from Layer 2 required_materials + ALL prerequisites
   (components, principles, processes, subdomains). Each item carries
   id, label, type, source_layer, and a note that the engineer must map
   the graph node ID to a real supplier part number.

2. **materials_specification** — from Layer 6 materials, with a fallback
   to Layer 2 prerequisites when Layer 6 is empty. Each item carries id,
   label, constraints, source_layer.

3. **assembly_plan** — from Layer 4 subsystems + interfaces + inputs +
   outputs + energy_requirements + computational_requirements. A dict
   with all Layer 4 engineering-architecture data.

4. **tolerances** — from Layer 4 tolerances. A dict of constraint-type
   to tolerance-range pairs (e.g., "cost: ±15% of capex estimate").

5. **prototype_specification** — from Layer 9 prototype_v1/v2/v3 +
   timeline. A dict with all three prototype stages and the total
   timeline.

All 20 candidates now have all 5 fields non-empty.

## The hypothesis (PHASE 5 prediction)

> "At least 15/20 blueprints will have all 5 buildable-spec fields
> non-empty after the fix."

Result: **20/20** — the hypothesis is CONFIRMED (and exceeded).

## PHASE 10 — DECISION

**YES — reality supported the hypothesis.**

The modification is preserved.

## What did NOT change

- Unique composite scores: unchanged (Gap 3 doesn't affect scoring).
- Max collisions: unchanged (Gap 3 doesn't affect scoring).
- 0 compiler exceptions in both batches.
- Gaps 1, 2, 4, 5, 6, 7 are UNCHANGED.
- All other modules unchanged.

## What was modified

- invention_compiler/blueprint_module.py: replaced structured-summary
  blueprint with buildable spec. Added 5 new fields (parts_list,
  materials_specification, assembly_plan, tolerances,
  prototype_specification). Updated evidence block with buildable_
  fields_present count. Updated assumptions and falsification_criteria.
- tests/test_gap3_fix.py: 12 new tests locking the Gap 3 fix contract.
- evidence/experiments/invention_batch_004/: 20 YAML outputs + DELTA.md.

## What was NOT modified (per Maestro Loop PHASE 6)

- simulation_module.py (Gap 1)
- dependency_module.py (Gap 2+7)
- orchestrator.py (Gap 4)
- prototype_module.py (Gap 5)
- chemistry_knowledge_module.py (Gap 6)
- All other modules, hypothesis/, loops/, layer_status/, belief/, agent/

## Honest caveats (from the counterevidence in the hypothesis)

The blueprint is now *structurally* buildable — it has the 5 fields an
engineer needs. But the CONTENT of those fields is still templated:

- parts_list items are graph node IDs ("component_cyclone_chamber"),
  not real supplier part numbers.
- materials_specification items come from the prerequisite chain, not
  from a materials database.
- tolerances are keyword-derived priors ("±15% of capex estimate"),
  not engineering tolerances ("±0.1mm").
- prototype_specification is the same v1/v2/v3 template for every
  invention (Gap 5).

The distinction: the blueprint_module now COMPOSES existing layer data
into a buildable format. It does not ADD new analysis. The underlying
layers' quality determines the blueprint's quality. Gap 5 (templated
plans) is the next bottleneck on blueprint quality.

## Next gap (per priority table)

| Gap | Priority | Status |
|---|---|---|
| Gap 4 (missing counterevidence) | High | Next |
| Gap 6 (chemical differentiation) | Medium | After Gap 4 |
| Gap 5 (templated plans) | Medium | After Gap 6 |
