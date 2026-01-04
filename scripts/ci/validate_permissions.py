#!/usr/bin/env python3
"""
Validate admin permission checks in handlers.
"""

import re
import sys
from pathlib import Path
import json


def validate_permissions(base_path: Path = Path("handlers/admin")):
    """Check if admin handlers have permission checks."""
    issues = []
    
    permission_patterns = [
        r'await db\.is_admin\(',
        r'await check_admin\(',
        r'await db\.is_super_admin\(',
        r'check_super_admin\(',
        r'@admin_required'
    ]
    
    for py_file in base_path.rglob("*.py"):
        if "__pycache__" in str(py_file) or py_file.name == "__init__.py":
            continue
        if "shared" in str(py_file):
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find async function definitions
            func_pattern = re.compile(r'async def (\w+)\(update.*?context')
            
            for match in func_pattern.finditer(content):
                func_name = match.group(1)
                
                # Skip utility functions
                if func_name.startswith(('_', 'get_', 'build_', 'format_', 'validate_', 'clear_', 'handle_noop')):
                    continue
                
                # Get function body
                func_start = match.start()
                next_func = content.find('\nasync def ', func_start + 1)
                if next_func == -1:
                    next_func = len(content)
                
                func_body = content[func_start:next_func]
                
                # Check for permission check
                has_check = any(re.search(p, func_body) for p in permission_patterns)
                
                # Skip simple handlers
                if len(func_body) < 200:
                    continue
                
                if not has_check:
                    line_num = content[:func_start].count('\n') + 1
                    issues.append({
                        "type": "missing_permission_check",
                        "severity": "warning",
                        "file": str(py_file),
                        "line": line_num,
                        "function": func_name,
                        "message": f"Function '{func_name}' may be missing admin permission check"
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
    print("🔒 Validating permission checks...")
    
    issues = validate_permissions()
    
    # Generate report
    report = {
        "validation": "permissions",
        "total_issues": len(issues),
        "errors": len([i for i in issues if i["severity"] == "error"]),
        "warnings": len([i for i in issues if i["severity"] == "warning"]),
        "issues": issues
    }
    
    # Save report
    Path("reports").mkdir(exist_ok=True)
    with open("reports/security-report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    if issues:
        print(f"\n⚠️ Found {len(issues)} permission issues:")
        for issue in issues[:10]:
            icon = "❌" if issue["severity"] == "error" else "⚠️"
            print(f"  {icon} {issue.get('file', 'N/A')}: {issue['message']}")
    else:
        print("✅ Permission validation PASSED")
    
    # Permission issues are warnings, not failures
    sys.exit(0)


if __name__ == "__main__":
    main()
