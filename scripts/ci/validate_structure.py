#!/usr/bin/env python3
"""
Validate directory structure for Admin System Enhancement.
"""

import os
import sys
from pathlib import Path
import json

REQUIRED_STRUCTURE = {
    "handlers/admin/ui": [
        "__init__.py",
        "dashboard.py",
        "stock_ui.py",
        "product_ui.py",
        "transaction_ui.py",
        "user_ui.py",
        "system_ui.py",
        "confirmation.py"
    ],
    "handlers/admin/wizards": [
        "__init__.py",
        "stock_wizard.py",
        "product_wizard.py"
    ],
    "handlers/admin/shared": [
        "__init__.py"
    ],
    "utils": [
        "admin_keyboards.py"
    ]
}


def validate_structure(base_path: Path = Path(".")):
    """Validate directory structure."""
    issues = []
    
    for dir_path, required_files in REQUIRED_STRUCTURE.items():
        full_dir = base_path / dir_path
        
        # Check if directory exists
        if not full_dir.exists():
            issues.append({
                "type": "missing_dir",
                "severity": "error",
                "path": dir_path,
                "message": f"Required directory missing: {dir_path}"
            })
            continue
        
        # Check required files
        for required_file in required_files:
            file_path = full_dir / required_file
            if not file_path.exists():
                issues.append({
                    "type": "missing_file",
                    "severity": "error",
                    "path": f"{dir_path}/{required_file}",
                    "message": f"Required file missing: {dir_path}/{required_file}"
                })
    
    return issues


def main():
    """Main validation function."""
    print("📁 Validating directory structure...")
    
    issues = validate_structure()
    
    # Generate report
    report = {
        "validation": "structure",
        "total_issues": len(issues),
        "errors": len([i for i in issues if i["severity"] == "error"]),
        "warnings": len([i for i in issues if i["severity"] == "warning"]),
        "issues": issues
    }
    
    # Save report
    os.makedirs("reports", exist_ok=True)
    with open("reports/structure-report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    if issues:
        print(f"\n❌ Found {len(issues)} issues:")
        for issue in issues:
            icon = "❌" if issue["severity"] == "error" else "⚠️"
            print(f"  {icon} {issue['message']}")
        
        if report["errors"] > 0:
            print("\n💥 Validation FAILED")
            sys.exit(1)
    else:
        print("✅ Structure validation PASSED")
    
    sys.exit(0)


if __name__ == "__main__":
    main()
