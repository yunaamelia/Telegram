"""Validate Unicode fonts are used in templates."""

import sys
import re
from pathlib import Path


def check_unicode_usage():
    """Check if Unicode fonts are properly used."""
    issues = []

    # Check message_templates.py
    template_file = Path('utils/message_templates.py')

    if not template_file.exists():
        return [{'error': 'message_templates.py not found'}]

    with open(template_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if uf is imported
    if 'from utils.unicode_fonts import UnicodeFonts' not in content:
        issues.append({
            'file': 'message_templates.py',
            'issue': 'missing_import',
            'message': 'UnicodeFonts not imported'
        })

    # Check if uf alias is used
    if ' as uf' not in content:
        issues.append({
            'file': 'message_templates.py',
            'issue': 'missing_alias',
            'message': 'UnicodeFonts alias "uf" not defined'
        })

    # Check usage of Unicode font methods
    font_methods = ['bold', 'italic', 'monospace', 'sans', 'small_caps']
    usage_count = 0

    for method in font_methods:
        pattern = f'uf\\.{method}\\('
        matches = re.findall(pattern, content)
        usage_count += len(matches)

    if usage_count == 0:
        issues.append({
            'file': 'message_templates.py',
            'issue': 'no_unicode_usage',
            'message': 'Unicode fonts not used in templates'
        })
    else:
        print(f"  ℹ️ Found {usage_count} Unicode font usages")

    return issues


if __name__ == "__main__":
    print("🔍 Checking Unicode font integration...")
    print("=" * 50)

    issues = check_unicode_usage()

    if issues:
        print(f"\n⚠️ Found {len(issues)} issues:\n")
        for issue in issues:
            msg = issue.get('message', str(issue))
            print(f"  • {msg}")
        sys.exit(1)
    else:
        print("\n✅ VALIDATION PASSED")
        print("Unicode fonts properly integrated!")
        sys.exit(0)
