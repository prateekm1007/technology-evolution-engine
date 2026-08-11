"""
Tests for CTO review #3 directives.

Per ANTI_ENTROPY.md rule 1 (tests first), these tests are written
BEFORE the implementation. They lock:

  1. The 5 domain modules are renamed to *_knowledge_module.py.
  2. Each domain module declares its stage on the encode→reason→
     simulate→discover spectrum.
  3. The 5th benchmark category (Creation) exists.
  4. The benchmark report uses "expectations_satisfied" not "PASS"
     and carries an epistemic_caveat block.
  5. The experimentation_layer package is scaffolded.
  6. The 5-layer architecture is documented.
"""
import json
import pathlib
import sys
import os
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


# ----------------------------------------------------------------------
# 1. Knowledge-spectrum rename
# ----------------------------------------------------------------------

def test_5_domain_modules_renamed_to_knowledge_module():
    """The 5 domain modules (physics, chemistry, biology, mathematics,
    economics) must be named *_knowledge_module.py, per CTO review #3."""
    pkg = ROOT / "invention_compiler"
    expected = {
        "physics_knowledge_module.py",
        "chemistry_knowledge_module.py",
        "biology_knowledge_module.py",
        "mathematics_knowledge_module.py",
        "economics_knowledge_module.py",
    }
    actual = {f for f in os.listdir(pkg) if f.endswith(".py")}
    missing = expected - actual
    assert not missing, (
        f"CTO review #3 violation: domain modules not renamed to "
        f"*_knowledge_module.py. Missing: {missing}. "
        f"See ANTI_ENTROPY.md 'Use the knowledge spectrum honestly'."
    )


def test_old_domain_module_names_are_gone():
    """The old *_module.py names for the 5 domain modules must NOT
    exist (they were renamed to *_knowledge_module.py)."""
    pkg = ROOT / "invention_compiler"
    old_names = [
        "physics_module.py",
        "chemistry_module.py",
        "biology_module.py",
        "mathematics_module.py",
        "economics_module.py",
    ]
    for name in old_names:
        assert not (pkg / name).exists(), (
            f"old domain module name {name} still exists — should have "
            f"been renamed to *_knowledge_module.py per CTO review #3."
        )


def test_cross_cutting_modules_NOT_renamed():
    """The cross-cutting modules (constraint, dependency, resurrection,
    analogy, simulation, architecture, blueprint, prototype) are NOT
    knowledge-encoding modules — they stay as *_module.py."""
    pkg = ROOT / "invention_compiler"
    must_stay = [
        "constraint_module.py",
        "dependency_module.py",
        "resurrection_module.py",
        "analogy_module.py",
        "simulation_module.py",
        "architecture_module.py",
        "blueprint_module.py",
        "prototype_module.py",
    ]
    for name in must_stay:
        assert (pkg / name).exists(), (
            f"cross-cutting module {name} missing — these should NOT "
            f"be renamed to *_knowledge_module.py per CTO review #3."
        )


def test_each_domain_module_declares_its_stage():
    """Each domain module must declare its stage on the encode→reason→
    simulate→discover spectrum. Currently all are 'encode'."""
    from invention_compiler.physics_knowledge_module import PhysicsKnowledgeModule
    from invention_compiler.chemistry_knowledge_module import ChemistryKnowledgeModule
    from invention_compiler.biology_knowledge_module import BiologyKnowledgeModule
    from invention_compiler.mathematics_knowledge_module import MathematicsKnowledgeModule
    from invention_compiler.economics_knowledge_module import EconomicsKnowledgeModule
    for cls in (PhysicsKnowledgeModule, ChemistryKnowledgeModule,
                BiologyKnowledgeModule, MathematicsKnowledgeModule,
                EconomicsKnowledgeModule):
        # The class must expose a STAGE attribute.
        assert hasattr(cls, "STAGE"), \
            f"{cls.__name__} missing STAGE attribute"
        assert cls.STAGE in ("encode", "reason", "simulate", "discover"), \
            f"{cls.__name__}.STAGE={cls.STAGE!r} not a valid spectrum stage"
        # Currently all are at the encode stage.
        assert cls.STAGE == "encode", (
            f"{cls.__name__}.STAGE={cls.STAGE!r} — per CTO review #3, "
            f"the domain modules should be at the 'encode' stage. "
            f"Renaming to a higher stage requires pass+fail verification "
            f"in the ledger."
        )


def test_no_module_pretends_to_be_higher_than_encode():
    """No domain module file may declare a stage higher than 'encode'
    in its STAGE attribute, until the verification cycle records
    pass+fail for the higher capability."""
    pkg = ROOT / "invention_compiler"
    domain_files = [
        "physics_knowledge_module.py",
        "chemistry_knowledge_module.py",
        "biology_knowledge_module.py",
        "mathematics_knowledge_module.py",
        "economics_knowledge_module.py",
    ]
    for fname in domain_files:
        text = (pkg / fname).read_text()
        # Look for STAGE = "..." declarations.
        m = re.search(r'STAGE\s*=\s*["\'](\w+)["\']', text)
        assert m, f"{fname} does not declare STAGE"
        stage = m.group(1)
        assert stage == "encode", (
            f"{fname} declares STAGE={stage!r}. Until the verification "
            f"cycle records pass+fail for that stage, the module must "
            f"stay at 'encode'. See ANTI_ENTROPY.md 'Use the knowledge "
            f"spectrum honestly'."
        )


# ----------------------------------------------------------------------
# 2. 5-level benchmark hierarchy
# ----------------------------------------------------------------------

def test_benchmark_categories_has_5_levels():
    """BENCHMARK_CATEGORIES must include Creation as the 5th level."""
    from benchmarks.compiler import BENCHMARK_CATEGORIES
    assert "creation" in BENCHMARK_CATEGORIES, (
        "CTO review #3 violation: 'creation' level missing from "
        "BENCHMARK_CATEGORIES. See INVENTION_COMPILER.md 5-level "
        "benchmark hierarchy."
    )
    assert set(BENCHMARK_CATEGORIES.keys()) == {
        "reconstruction", "resurrection", "forecasting", "synthesis",
        "creation"
    }, f"unexpected categories: {set(BENCHMARK_CATEGORIES.keys())}"


def test_creation_category_has_correct_question():
    """The Creation level must ask 'Can we generate a blueprint that
    somebody can actually build?' per CTO review #3."""
    from benchmarks.compiler import BENCHMARK_CATEGORIES
    creation = BENCHMARK_CATEGORIES["creation"]
    assert "question" in creation
    q = creation["question"].lower()
    assert "blueprint" in q and "build" in q, (
        f"creation category question wrong: {creation['question']!r}"
    )


# ----------------------------------------------------------------------
# 3. Epistemic honesty in the benchmark report
# ----------------------------------------------------------------------

def test_benchmark_report_uses_expectations_satisfied_not_pass():
    """The benchmark report must use 'expectations_satisfied' as the
    verdict, NOT 'PASS' (which implies correctness)."""
    report_path = ROOT / "evidence" / "reports" / "compiler_benchmark_report.json"
    if not report_path.exists():
        import subprocess
        subprocess.run(
            [sys.executable, "scripts/run_compiler_benchmarks.py"],
            cwd=str(ROOT), check=True,
        )
    report = json.loads(report_path.read_text())
    summary = report.get("summary", {})
    # The summary's verdict key must be expectations_satisfied_count
    # (or equivalent), NOT pass_count.
    assert "expectations_satisfied" in summary or \
           "expectations_satisfied_count" in summary, \
        f"benchmark summary missing expectations_satisfied: {summary}"
    # The old "passed" key, if present, must equal expectations_satisfied.
    if "passed" in summary:
        es = summary.get("expectations_satisfied",
                         summary.get("expectations_satisfied_count"))
        assert summary["passed"] == es


def test_benchmark_report_carries_epistemic_caveat():
    """The benchmark report must carry an `epistemic_caveat` block that
    explicitly distinguishes 'expectations satisfied' from 'correctness'."""
    report_path = ROOT / "evidence" / "reports" / "compiler_benchmark_report.json"
    if not report_path.exists():
        import subprocess
        subprocess.run(
            [sys.executable, "scripts/run_compiler_benchmarks.py"],
            cwd=str(ROOT), check=True,
        )
    report = json.loads(report_path.read_text())
    assert "epistemic_caveat" in report, \
        "benchmark report missing epistemic_caveat block — CTO review #3 mandate"
    caveat = report["epistemic_caveat"].lower()
    assert "expectations" in caveat and "correctness" in caveat, \
        f"epistemic_caveat must mention both 'expectations' and 'correctness': {caveat}"


def test_benchmark_report_per_case_uses_expectations_satisfied():
    """Each per-case result must use 'expectations_satisfied' as the
    boolean key, not 'pass'."""
    report_path = ROOT / "evidence" / "reports" / "compiler_benchmark_report.json"
    if not report_path.exists():
        import subprocess
        subprocess.run(
            [sys.executable, "scripts/run_compiler_benchmarks.py"],
            cwd=str(ROOT), check=True,
        )
    report = json.loads(report_path.read_text())
    for case in report["cases"]:
        assert "expectations_satisfied" in case, \
            f"case {case.get('case_id')} missing 'expectations_satisfied' key"


# ----------------------------------------------------------------------
# 4. Experimentation layer scaffold
# ----------------------------------------------------------------------

def test_experimentation_layer_package_exists():
    """The experimentation_layer/ package must exist as a scaffold."""
    pkg = ROOT / "experimentation_layer"
    assert pkg.exists() and pkg.is_dir(), \
        "experimentation_layer/ package missing — CTO review #3 mandate"
    assert (pkg / "__init__.py").exists(), \
        "experimentation_layer/__init__.py missing"


def test_experimentation_layer_docstring_describes_loop():
    """The package docstring must describe the predict→build→observe→
    learn loop."""
    init = (ROOT / "experimentation_layer" / "__init__.py").read_text()
    text = init.lower()
    assert "predict" in text and "build" in text \
           and "observe" in text and "learn" in text, \
        "experimentation_layer docstring must describe predict→build→observe→learn loop"


def test_experimentation_layer_declares_status_as_scaffold():
    """The package must honestly declare it is a scaffold, not
    implemented — per the 'don't reward agreement' rule."""
    init = (ROOT / "experimentation_layer" / "__init__.py").read_text()
    text = init.lower()
    assert "scaffold" in text or "not implemented" in text \
           or "declared" in text, \
        "experimentation_layer must declare itself as scaffold/not-implemented"


# ----------------------------------------------------------------------
# 5. 5-layer architecture documentation
# ----------------------------------------------------------------------

def test_invention_compiler_md_documents_5_layer_architecture():
    """The 5-layer architecture (Observation → Knowledge → Reasoning →
    Blueprint → Experimentation) must be documented somewhere in the repo.
    Originally in INVENTION_COMPILER.md (archived during MASTER_PROTOCOL
    consolidation); now in experimentation_layer/__init__.py."""
    # PF-001 fix: INVENTION_COMPILER.md was archived. The 5-layer
    # architecture is now documented in experimentation_layer/__init__.py.
    text = (ROOT / "experimentation_layer" / "__init__.py").read_text().lower()
    for layer in ("observation layer", "knowledge layer",
                  "reasoning layer", "blueprint layer",
                  "experimentation layer"):
        assert layer in text, \
            f"experimentation_layer/__init__.py missing 5-layer architecture entry: {layer!r}"


def test_invention_compiler_md_documents_5_level_benchmark_hierarchy():
    """The 5-level benchmark hierarchy (Reconstruction, Resurrection,
    Forecasting, Synthesis, Creation) must be documented in the
    benchmark suite.
    Originally in INVENTION_COMPILER.md; now in benchmarks/compiler/__init__.py."""
    # PF-001 fix: INVENTION_COMPILER.md was archived.
    text = (ROOT / "benchmarks" / "compiler" / "__init__.py").read_text().lower()
    for level in ("reconstruction", "resurrection", "forecasting",
                  "synthesis", "creation"):
        assert level in text, \
            f"benchmarks/compiler/__init__.py missing benchmark level: {level!r}"


def test_invention_compiler_md_documents_knowledge_spectrum():
    """The encode→reason→simulate→discover spectrum must be documented.
    Originally in INVENTION_COMPILER.md; now in the knowledge modules
    (physics, chemistry, biology, mathematics, economics)."""
    # PF-001 fix: INVENTION_COMPILER.md was archived.
    # The knowledge spectrum is documented in the knowledge modules.
    text = (ROOT / "invention_compiler" / "physics_knowledge_module.py").read_text().lower()
    assert "encode" in text, \
        "physics_knowledge_module.py missing encode stage"
    assert "reason" in text, \
        "physics_knowledge_module.py missing reason stage"
    assert "simulate" in text, \
        "physics_knowledge_module.py missing simulate stage"
    assert "discover" in text, \
        "physics_knowledge_module.py missing discover stage"


def test_invention_compiler_md_documents_epistemic_caveat():
    """The epistemic caveat ('expectations satisfied ≠ correctness')
    must be documented.
    Originally in INVENTION_COMPILER.md; now in scripts/run_compiler_benchmarks.py."""
    # PF-001 fix: INVENTION_COMPILER.md was archived.
    text = (ROOT / "scripts" / "run_compiler_benchmarks.py").read_text().lower()
    assert "expectations" in text and "correctness" in text, \
        "scripts/run_compiler_benchmarks.py missing epistemic caveat discussion"


# ----------------------------------------------------------------------
# 6. Compiler still works after rename
# ----------------------------------------------------------------------

def test_compiler_orchestrator_uses_new_module_names():
    """The orchestrator must import the renamed modules."""
    text = (ROOT / "invention_compiler" / "orchestrator.py").read_text()
    for name in ("physics_knowledge_module", "chemistry_knowledge_module",
                 "biology_knowledge_module", "mathematics_knowledge_module",
                 "economics_knowledge_module"):
        assert name in text, \
            f"orchestrator.py missing import of {name} — rename incomplete"
    # Old names must NOT appear in imports.
    for old in ("from .physics_module", "from .chemistry_module",
                "from .biology_module", "from .mathematics_module",
                "from .economics_module"):
        assert old not in text, \
            f"orchestrator.py still imports {old} — rename incomplete"
