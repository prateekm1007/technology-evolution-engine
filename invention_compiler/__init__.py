"""
Invention Compiler — Top-level package.

This package implements the directive in INVENTION_COMPILER.md:
the system is an invention compiler, not an idea generator. Every
invention emitted by the compiler must produce all 11 layers, from
Layer 0 (Opportunity definition) through Layer 10 (Final blueprint).

Module-to-layer mapping (per INVENTION_COMPILER.md, post-CTO-review):

  Layer 0  — OpportunityDefinition (this orchestrator) + analogy_module
  Layer 1  — physics_module, chemistry_module, biology_module,
              mathematics_module, economics_module
  Layer 2  — dependency_module, resurrection_module
  Layer 3  — mathematics_module, constraint_module
  Layer 4  — constraint_module (subsystems/tolerances) + architecture_module
  Layer 5  — simulation_module
  Layer 6  — constraint_module (materials/suppliers/tooling)
  Layer 7  — economics_module
  Layer 8  — verification_engine (the one true "engine" — explicit
              model + empirical validation + reproducible results)
  Layer 9  — prototype_module
  Layer 10 — blueprint_module

NAMING RULE (CTO-mandated, see ANTI_ENTROPY.md):
  The word "engine" is reserved for modules with explicit model +
  empirical validation + reproducible results. Currently only
  verification_engine meets this bar. Everything else is a "module"
  — it does keyword matching, not scientific reasoning. Renaming a
  module back to "engine" requires recorded pass+fail against real
  data in the verification ledger.

Law 8 honesty rule (per ANTI_ENTROPY.md): every layer that emits a
scalar must also emit:
  - evidence: the inputs that produced the scalar
  - assumptions: what the scalar assumes
  - falsification_criteria: what would prove the scalar wrong
"""
