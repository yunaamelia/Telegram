#!/usr/bin/env python3
"""
Validate imports - check for circular imports and proper import structure.
"""

import ast
import sys
from pathlib import Path
import json


def check_imports(base_path: Path = Path("handlers/admin")):
    """Check import patterns in Python files."""
    issues = []
    
    for py_file in base_path.rglob("*.py"):
        if "__pycache__" in str(py_file) or py_file.name == "__init__.py":
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content, filename=str(py_file))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    
                    # Check for circular imports between ui and wizards
                    if 'handlers.admin.ui' in module and 'wizards' in str(py_file):
                        issues.append({
                            "type": "circular_import",
                            "severity": "warning",
                            "file": str(py_file),
                            "line": node.lineno,
                            "message": f"Potential circular import: {module} in wizard file"
                        })
                    
                    if 'handlers.admin.wizards' in module and 'ui' in str(py_file):
                        issues.append({
                            "type": "circular_import",
                            "severity": "warning",
                            "file": str(py_file),
                            "line": node.lineno,
                            "message": f"Potential circular import: {module} in ui file"
                        })
        
        except SyntaxError as e:
            issues.append({
                "type": "syntax_error",
                "severity": "error",
                "file": str(py_file),
                "line": e.lineno,
                "message": f"Syntax error: {e.msg}"
            })
        except Exception as e:
            issues.append({
                "type": "parse_error",
                "severity": "warning",
                "file": str(py_file),
                "message": f"Failed to parse: {str(e)}"
            })
    
    return issues


def main():
    """Main validation function."""
    print("🔍 Validating imports...")
    
    issues = check_imports()
    
    # Generate report
    report = {
        "validation": "imports",
        "total_issues": len(issues),
        "errors": len([i for i in issues if i["severity"] == "error"]),
        "warnings": len([i for i in issues if i["severity"] == "warning"]),
        "issues": issues
    }
    
    # Save report
    Path("reports").mkdir(exist_ok=True)
    with open("reports/imports-report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    if issues:
        print(f"\n⚠️ Found {len(issues)} import issues:")
        for issue in issues[:10]:
            icon = "❌" if issue["severity"] == "error" else "⚠️"
            print(f"  {icon} {issue.get('file', 'N/A')}: {issue['message']}")
        
        if report["errors"] > 0:
            print("\n💥 Import validation FAILED")
            sys.exit(1)
    else:
        print("✅ Import validation PASSED")
    
    sys.exit(0)


if __name__ == "__main__":
    main()
