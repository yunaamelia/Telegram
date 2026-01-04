#!/usr/bin/env python3
"""
Validate callback data patterns follow admin:<category>:<action> format.
"""

import re
import sys
from pathlib import Path
import json


def validate_callbacks(base_path: Path = Path("handlers/admin")):
    """Validate callback_data patterns."""
    issues = []

    callback_pattern = re.compile(r'callback_data=["\']([^"\']+)["\']')

    for py_file in base_path.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue

        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()

            for line_num, line in enumerate(content.split('\n'), 1):
                matches = callback_pattern.findall(line)

                for callback in matches:
                    # Skip special callbacks
                    if callback in ["noop", "nav:back", "nav:close"]:
                        continue

                    # Admin callbacks should start with admin:
                    if not callback.startswith("admin:") and not callback.startswith("nav:"):
                        issues.append({
                            "type": "invalid_prefix",
                            "severity": "error",
                            "file": str(py_file),
                            "line": line_num,
                            "callback": callback,
                            "message": f"Callback missing 'admin:' prefix: {callback}"
                        })
                        continue

                    # Check format: admin:<category>:<action>
                    if callback.startswith("admin:"):
                        parts = callback.split(":")
                        if len(parts) < 3:
                            issues.append({
                                "type": "invalid_format",
                                "severity": "warning",
                                "file": str(py_file),
                                "line": line_num,
                                "callback": callback,
                                "message": f"Callback too short (need 3+ parts): {callback}"
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
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true", help="Only check, do not generate report")
    args = parser.parse_args()

    print("⌨️ Validating callback patterns...")

    issues = validate_callbacks()

    # Generate report if not check-only
    if not args.check_only:
        report = {
            "validation": "callbacks",
            "total_issues": len(issues),
            "errors": len([i for i in issues if i["severity"] == "error"]),
            "warnings": len([i for i in issues if i["severity"] == "warning"]),
            "issues": issues
        }

        # Save report
        Path("reports").mkdir(exist_ok=True)
        with open("reports/keyboard-report.json", "w") as f:
            json.dump(report, f, indent=2)

    # Print summary
    if issues:
        print(f"\n⚠️ Found {len(issues)} callback issues:")
        for issue in issues[:10]:
            icon = "❌" if issue["severity"] == "error" else "⚠️"
            print(f"  {icon} {issue.get('file', 'N/A')}:{issue.get('line', '?')} - {issue['message']}")

        if report["errors"] > 0:
            print("\n💥 Callback validation FAILED")
            sys.exit(1)
    else:
        print("✅ Callback validation PASSED")

    sys.exit(0)


if __name__ == "__main__":
    main()
