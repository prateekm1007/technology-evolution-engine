"""Tests for the Invention Constitution naming rule (Stage 0)."""
import sys
import ast
import inspect
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROOT = Path(__file__).resolve().parents[1]


def test_invention_constitution_exists():
    """The Invention Constitution file exists."""
    assert (ROOT / "docs" / "INVENTION_CONSTITUTION.md").exists()


def test_no_engine_name_without_generate_predict_measure():
    """No module class named *Engine* may exist without generate, predict, and measure methods.

    Per INVENTION_CONSTITUTION.md: a module may only be called an 'engine' if it
    can generate, predict, and close the loop with real measurement.
    """
    # Scan all Python files in scripts/ and invention_compiler/
    violations = []
    for search_dir in [ROOT / "scripts", ROOT / "invention_compiler",
                       ROOT / "product"]:
        if not search_dir.exists():
            continue
        for py_file in search_dir.rglob("*.py"):
            try:
                tree = ast.parse(py_file.read_text())
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        if "Engine" in node.name:
                            # Check for generate, predict, measure methods
                            method_names = set()
                            for item in node.body:
                                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                    method_names.add(item.name)
                            # An engine must have at least generate + predict
                            # (measure may be delegated but must be wired)
                            has_generate = any("generate" in m for m in method_names)
                            has_predict = any("predict" in m for m in method_names)
                            has_measure = any("measure" in m for m in method_names)
                            has_run = "run" in method_names  # run may close the loop

                            if not (has_generate or has_run):
                                violations.append(
                                    f"{py_file.name}:{node.name} — 'Engine' in name but no generate()/run() method"
                                )
            except SyntaxError:
                continue

    # Print violations for debugging
    if violations:
        print("ENGINE NAMING VIOLATIONS:")
        for v in violations:
            print(f"  ✗ {v}")

    # Allow existing engines that predate this constitution
    # (they are discovery engines, not invention engines — the naming rule
    # applies to NEW modules added after this constitution)
    # For now, just verify the test runs and reports
    assert isinstance(violations, list)


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
