# 20-invention experiment — SUMMARY

Date: 2026-08-01T17:36:14.254313+00:00
Architecture: FROZEN (no modifications made during experiment)

## Counts

- Total candidates: 20
- Inventions produced (compiled successfully): 20
- Compiler exceptions: 0
- Blueprints generated (final_blueprint non-null): 20
- Hypotheses with counterevidence: 0
- Outputs with physical_laws: 20/20
- Outputs with chemical_pathways: 20/20
- Outputs with failure_modes: 20/20
- Outputs with prototype_plan: 20/20
- Outputs with experimental_plan: 20/20

## Confidence distribution

- min: 0.3678
- max: 0.6827
- mean: 0.6027
- all values: [0.3678, 0.5428, 0.5553, 0.5777, 0.5777, 0.5777, 0.5777, 0.5777, 0.5777, 0.5777, 0.5777, 0.6128, 0.6477, 0.6477, 0.6603, 0.6753, 0.6753, 0.6827, 0.6827, 0.6827]

## Observed gaps in the architecture (recorded for review, NOT modified)

These gaps were observed by running the compiler against 20 real
invention problems. Per the CEO freeze directive, the architecture
is NOT modified in this experiment — only reviewed. The next
iteration may modify the architecture to address these gaps, but
ONLY after the CEO/CTO review the failures.

### Gap 1: Identical composite feasibility across dissimilar domains

Multiple candidates from radically different domains (medical imaging,
chemistry, materials) produce composite feasibility scores within
0.05 of each other. This suggests the simulation_module's complexity
penalty is not differentiating well across domains — it over-weights
keyword presence in the problem statement.

### Gap 2: Missing prerequisites for novel inventions

For inventions not in the civilization_graph (most of the 20),
the dependency_module picks an arbitrary target_node_id (first
system node in the matching domain, or the first system node
period). The prerequisite chain is then unrelated to the actual
invention. This is honest in the output — missing_capabilities
lists are short — but the blueprint's prerequisite_chain_depth
is uninformative for novel inventions.

### Gap 3: final_blueprint is a structured summary, not a buildable spec

The final_blueprint field carries target_invention, prerequisite_
chain_depth, governing_equations, subsystems, composite_feasibility,
prototype_stages, total_prototype_timeline_years. That's a summary,
not a buildable spec. An engineer cannot start building from this
blueprint without consulting the underlying layers. The blueprint
does not satisfy the CEO directive's 'blueprint generated' criterion
in the strong sense.

### Gap 4: Counterevidence is often empty

Many candidates have empty counterevidence lists in their headline
hypothesis. The orchestrator's _chain_summary constructs evidence
from Layer 1 laws/pathways + Layer 3 equations + Layer 7 capex, but
does not pull counterevidence from any layer. The hypothesis has a
counterevidence field but it's not populated by the compiler.

### Gap 5: prototype_plan and experimental_plan are templated

The prototype_module emits v1/v2/v3 stages with the same structure
for every invention. The experimental_plan from verification_module
proposes one experiment per failure_mode + a generic 'build it and
see' experiment. These are templates, not invention-specific plans.

### Gap 6: No domain-specific differentiation in chemical principles

Candidates from materials, energy, water, and biology domains all
surface the same small set of chemical pathways (electrolysis,
polymerization, calcination, etc.) because the chemistry_knowledge_
module's keyword filter is narrow. Real inventions in these domains
would invoke domain-specific chemistry that's not encoded.

### Gap 7: dependencies.causal_classifications is often all-zero

When the dependency_module picks an arbitrary target node (Gap 2),
the causal_classifications count (necessary/sufficient/contributing)
is often all-zero because the target has no prerequisites in the
graph. The counterfactual_analysis is then empty.

## What was NOT modified (per CEO freeze)

- No new modules, layers, packages, classes, or abstractions added.
- No existing module's logic modified.
- The InventionCompiler class used as-is.
- The civilization_graph.json used as-is.
- The 5 loop modules used as-is.
- The Hypothesis class used as-is (with id field).
- Tests, governor files: unchanged except for freeze declaration.

## Next step

Per the CEO directive: 'Only after reviewing the failures should
the architecture change.' The next iteration is a review of the
gaps above, NOT a code change. The CEO/CTO decides which gaps
warrant architectural modification.
