#!/usr/bin/env python3
"""
Check for hardcoded secrets in code.
"""

import re
import sys
from pathlib import Path
import json


SECRET_PATTERNS = [
    (r'BOT_TOKEN\s*=\s*["\'][0-9]{8,12}:[A-Za-z0-9_-]{35,}["\']', "Bot token"),
    (r'API_KEY\s*=\s*["\'][A-Za-z0-9]{20,}["\']', "API key"),
    (r'SECRET\s*=\s*["\'][A-Za-z0-9]{20,}["\']', "Secret key"),
    (r'PASSWORD\s*=\s*["\'][^"\']{6,}["\']', "Password"),
    (r'PRIVATE_KEY\s*=\s*["\']-----BEGIN', "Private key"),
    (r'sk_live_[A-Za-z0-9]{20,}', "Stripe secret key"),
    (r'sk_test_[A-Za-z0-9]{20,}', "Stripe test key"),
]

EXCLUDE_FILES = [
    "config.py.example",
    ".env.example",
    "__pycache__",
    "venv",
    ".venv"
]


def check_secrets(base_path: Path = Path(".")):
    """Check for hardcoded secrets."""
    issues = []
    
    for py_file in base_path.rglob("*.py"):
        # Skip excluded files
        if any(exc in str(py_file) for exc in EXCLUDE_FILES):
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for pattern, secret_type in SECRET_PATTERNS:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    issues.append({
                        "type": "hardcoded_secret",
                        "severity": "error",
                        "file": str(py_file),
                        "line": line_num,
                        "secret_type": secret_type,
                        "message": f"Potential hardcoded {secret_type} found"
                    })
        
        except Exception as e:
            pass  # Skip files that can't be read
    
    return issues


def main():
    """Main function."""
    print("🔍 Checking for hardcoded secrets...")
    
    issues = check_secrets()
    
    # Generate report
    report = {
        "validation": "secrets",
        "total_issues": len(issues),
        "errors": len(issues),
        "warnings": 0,
        "issues": issues
    }
    
    # Save report
    Path("reports").mkdir(exist_ok=True)
    with open("reports/secrets-report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    if issues:
        print(f"\n❌ Found {len(issues)} potential secrets:")
        for issue in issues:
            print(f"  ❌ {issue['file']}:{issue['line']} - {issue['message']}")
        print("\n💥 Secret check FAILED")
        sys.exit(1)
    else:
        print("✅ No hardcoded secrets found")
    
    sys.exit(0)


if __name__ == "__main__":
    main()
