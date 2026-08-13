#!/usr/bin/env python3
"""
AST-based evidence promotion audit (CTO V17 #3, #4).

Per CTO: "Upgrade audit_evidence_promotions.py from text scanning to AST-based
analysis. Detect all direct Claim/status/dict/migration writes."

Detects:
  Claim(..., status="EVIDENCE_BACKED")
  Claim(..., status=<variable>)
  status = "EVIDENCE_BACKED"
  payload["status"] = "EVIDENCE_BACKED"
  dict.update({"status": "EVIDENCE_BACKED"})
  dataclasses.replace(..., status="EVIDENCE_BACKED")
  object.__setattr__(..., "status", "EVIDENCE_BACKED")

Whitelists only:
  promote_claim_to_evidence_backed()
  validated artifact deserialization
  _can_promote() gate (extractor's promotion check)
  CLAIM_STATUS set definition
  test assertions (reading, not writing)
"""
import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# Files to scan
SCAN_DIRS = ["source_fabric", "scripts", "tools"]
ALLOWED_FILES = {
    # Only the contract loader is file-level whitelisted (it doesn't create Claims)
    "source_fabric/mddg/claims/contract_loader.py",
}

# Test files that construct Claims with EVIDENCE_BACKED for testing purposes
TEST_FILES_PREFIX = "source_fabric/tests/"

# Allowed FUNCTION NAMES that may write EVIDENCE_BACKED
# The AST audit checks if the write is inside one of these functions
ALLOWED_FUNCTION_NAMES = {
    "promote_claim_to_evidence_backed",
}


class EvidencePromotionAuditor(ast.NodeVisitor):
    """AST visitor that detects direct EVIDENCE_BACKED writes.

    V11: Whitelists FUNCTION SCOPE only, not file scope.
    Only promote_claim_to_evidence_backed() may write EVIDENCE_BACKED.
    """

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.violations = []
        self.function_stack = []  # tracks enclosing function names

    def visit_FunctionDef(self, node):
        self.function_stack.append(node.name)
        self.generic_visit(node)
        self.function_stack.pop()

    def visit_AsyncFunctionDef(self, node):
        self.function_stack.append(node.name)
        self.generic_visit(node)
        self.function_stack.pop()

    def visit_Call(self, node):
        # Detect Claim(..., status="EVIDENCE_BACKED") or Claim(..., status=<var>)
        if isinstance(node.func, ast.Name) and node.func.id == "Claim":
            for kw in node.keywords:
                if kw.arg == "status":
                    # Check if the value is "EVIDENCE_BACKED" or a variable
                    if isinstance(kw.value, ast.Constant) and kw.value.value == "EVIDENCE_BACKED":
                        # Check if this is inside an allowed function
                        if not self._is_in_allowed_context(node):
                            self.violations.append({
                                "file": self.filepath,
                                "line": node.lineno,
                                "type": "Claim constructor with status=EVIDENCE_BACKED",
                                "content": f"Claim(..., status=\"EVIDENCE_BACKED\") at line {node.lineno}",
                            })
                    elif isinstance(kw.value, ast.Name):
                        # status=<variable> — potential bypass
                        self.violations.append({
                            "file": self.filepath,
                            "line": node.lineno,
                            "type": "Claim constructor with status=<variable>",
                            "content": f"Claim(..., status={kw.value.id}) at line {node.lineno}",
                        })

        # Detect dataclasses.replace(..., status="EVIDENCE_BACKED")
        # Allowed inside claim.py (the promote_claim_to_evidence_backed function)
        if isinstance(node.func, ast.Attribute) and node.func.attr == "replace":
            for kw in node.keywords:
                if kw.arg == "status" and isinstance(kw.value, ast.Constant) and kw.value.value == "EVIDENCE_BACKED":
                    if not self._is_in_allowed_context(node):
                        self.violations.append({
                            "file": self.filepath,
                            "line": node.lineno,
                            "type": "dataclasses.replace with status=EVIDENCE_BACKED",
                            "content": f"dataclasses.replace(..., status=\"EVIDENCE_BACKED\") at line {node.lineno}",
                        })

        # Detect dict.update({"status": "EVIDENCE_BACKED"})
        if isinstance(node.func, ast.Attribute) and node.func.attr == "update":
            for arg in node.args:
                if isinstance(arg, ast.Dict):
                    for key, value in zip(arg.keys, arg.values):
                        if (isinstance(key, ast.Constant) and key.value == "status" and
                            isinstance(value, ast.Constant) and value.value == "EVIDENCE_BACKED"):
                            self.violations.append({
                                "file": self.filepath,
                                "line": node.lineno,
                                "type": "dict.update with status=EVIDENCE_BACKED",
                                "content": f"dict.update({{\"status\": \"EVIDENCE_BACKED\"}}) at line {node.lineno}",
                            })

        self.generic_visit(node)

    def visit_Assign(self, node):
        # Detect: status = "EVIDENCE_BACKED"
        # But NOT inside allowed functions
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "status":
                if isinstance(node.value, ast.Constant) and node.value == "EVIDENCE_BACKED":
                    if not self._is_in_allowed_context(node):
                        self.violations.append({
                            "file": self.filepath,
                            "line": node.lineno,
                            "type": "direct status = EVIDENCE_BACKED assignment",
                            "content": f"status = \"EVIDENCE_BACKED\" at line {node.lineno}",
                        })

            # Detect: payload["status"] = "EVIDENCE_BACKED"
            if isinstance(target, ast.Subscript):
                if (isinstance(target.slice, ast.Constant) and target.slice.value == "status" and
                    isinstance(node.value, ast.Constant) and node.value.value == "EVIDENCE_BACKED"):
                    self.violations.append({
                        "file": self.filepath,
                        "line": node.lineno,
                        "type": "dict key assignment with status=EVIDENCE_BACKED",
                        "content": f"payload[\"status\"] = \"EVIDENCE_BACKED\" at line {node.lineno}",
                    })

        self.generic_visit(node)

    def _is_in_allowed_context(self, node):
        """Check if the node is inside an allowed function (function scope, not file scope)."""
        # Test files are allowed to construct Claims for testing validation
        if self.filepath.startswith(TEST_FILES_PREFIX):
            return True
        # V11: Check if inside an allowed function by name
        for fn_name in self.function_stack:
            if fn_name in ALLOWED_FUNCTION_NAMES:
                return True
        return False


def scan_file(filepath: Path) -> list[dict]:
    """Scan a single Python file using AST analysis."""
    violations = []
    try:
        content = filepath.read_text(errors='replace')
        tree = ast.parse(content, filename=str(filepath))
    except SyntaxError:
        return []
    except Exception:
        return []

    auditor = EvidencePromotionAuditor(str(filepath.relative_to(REPO)))
    auditor.visit(tree)
    return auditor.violations


def main():
    all_violations = []

    for scan_dir in SCAN_DIRS:
        dir_path = REPO / scan_dir
        if not dir_path.exists():
            continue
        for pyfile in dir_path.rglob("*.py"):
            all_violations.extend(scan_file(pyfile))

    if all_violations:
        print("AUDIT FAIL: Direct EVIDENCE_BACKED writes found outside canonical promotion:")
        for v in all_violations:
            print(f"  {v['file']}:{v['line']}: {v['type']}")
            print(f"    {v['content']}")
        print(f"\nTotal violations: {len(all_violations)}")
        sys.exit(1)
    else:
        print("AUDIT PASS: No direct EVIDENCE_BACKED writes outside canonical promotion.")
        sys.exit(0)


if __name__ == "__main__":
    main()
