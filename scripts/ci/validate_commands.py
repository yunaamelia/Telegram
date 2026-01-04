#!/usr/bin/env python3
"""
Validate backward compatibility - check that required commands exist.
"""

import sys
from pathlib import Path
import json


REQUIRED_COMMANDS = [
    'addstock',
    'checkstock',
    'addproduct',
    'editproduct',
    'deleteproduct',
    'listproducts',
    'transactions',
    'refunds',
    'approverefund',
    'rejectrefund',
    'stats',
    'logs',
    'backupdb',
    'broadcast',
    'ban',
    'unban',
    'banlist',
    'addadmin',
    'removeadmin',
    'listadmin',
    'admin'
]


def check_command_exists(cmd: str, base_path: Path = Path("handlers/admin")) -> bool:
    """Check if a command handler exists."""
    patterns = [
        f'CommandHandler("{cmd}"',
        f"CommandHandler('{cmd}'",
        f'async def {cmd}_'
    ]
    
    for py_file in base_path.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if any(p in content for p in patterns):
                    return True
        except Exception:
            pass
    
    return False


def main():
    """Main function."""
    print("🔄 Checking backward compatibility...")
    
    issues = []
    found_commands = []
    
    for cmd in REQUIRED_COMMANDS:
        if check_command_exists(cmd):
            found_commands.append(cmd)
        else:
            issues.append({
                "type": "missing_command",
                "severity": "warning",
                "command": cmd,
                "message": f"Command handler not found: /{cmd}"
            })
    
    # Generate report
    report = {
        "validation": "commands",
        "total_commands": len(REQUIRED_COMMANDS),
        "found_commands": len(found_commands),
        "missing_commands": len(issues),
        "total_issues": len(issues),
        "errors": 0,
        "warnings": len(issues),
        "issues": issues
    }
    
    # Save report
    Path("reports").mkdir(exist_ok=True)
    with open("reports/compatibility-report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print(f"\n📊 Found {len(found_commands)}/{len(REQUIRED_COMMANDS)} commands")
    
    if issues:
        print(f"\n⚠️ Missing {len(issues)} commands:")
        for issue in issues:
            print(f"  ⚠️ /{issue['command']}")
    else:
        print("✅ All commands present")
    
    # Commands are warnings, not failures
    sys.exit(0)


if __name__ == "__main__":
    main()
