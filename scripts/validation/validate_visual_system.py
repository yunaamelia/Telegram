"""Validate Visual System implementation."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def validate_visual_system():
    """Validate VisualSystem class."""
    issues = []

    try:
        from utils.visual_system import VisualSystem as vs

        # Check required attributes
        required_attrs = [
            'SPACING', 'DIVIDERS', 'ICONS', 'INDICATORS',
            'BADGES', 'header', 'card', 'list_item',
            'stat_row', 'progress_bar', 'tag', 'alert',
            'loading', 'empty_state', 'table', 'pricing'
        ]

        for attr in required_attrs:
            if not hasattr(vs, attr):
                issues.append(f"Missing required attribute: {attr}")

        print("Testing components...")

        # Test header
        header = vs.header("Test Title", "Test Subtitle", icon="🎯")
        if not isinstance(header, str):
            issues.append("header() should return string")

        # Test card
        card = vs.card("Title", "Content", icon="📦")
        if not isinstance(card, str):
            issues.append("card() should return string")
        if "┌" not in card or "└" not in card:
            issues.append("card() missing borders")

        # Test list_item
        item = vs.list_item(1, "Test Item", "Subtitle", "Rp 50,000", "✅ Available")
        if not isinstance(item, str):
            issues.append("list_item() should return string")

        # Test stat_row
        stat = vs.stat_row("Users", "1,247", icon="👥")
        if not isinstance(stat, str):
            issues.append("stat_row() should return string")

        # Test progress_bar
        progress = vs.progress_bar(75, width=10)
        if not isinstance(progress, str):
            issues.append("progress_bar() should return string")
        if "75%" not in progress:
            issues.append("progress_bar() missing percentage")
        if "█" not in progress:
            issues.append("progress_bar() missing filled blocks")

        # Test tag
        tag = vs.tag("Premium", style='success')
        if not isinstance(tag, str):
            issues.append("tag() should return string")

        # Test alert
        alert = vs.alert("Test message", alert_type='warning', title='Warning')
        if not isinstance(alert, str):
            issues.append("alert() should return string")

        # Test loading
        load = vs.loading("Processing")
        if not isinstance(load, str):
            issues.append("loading() should return string")
        if "⏳" not in load:
            issues.append("loading() missing icon")

        # Test empty_state
        empty = vs.empty_state("📦", "No Items", "Description", "Action")
        if not isinstance(empty, str):
            issues.append("empty_state() should return string")

        # Test table
        table = vs.table(
            ['Header1', 'Header2'],
            [['Row1Col1', 'Row1Col2'], ['Row2Col1', 'Row2Col2']]
        )
        if not isinstance(table, str):
            issues.append("table() should return string")
        if "│" not in table:
            issues.append("table() missing column separators")

        # Test pricing
        price = vs.pricing(50000, 35000, 30)
        if not isinstance(price, str):
            issues.append("pricing() should return string")

        if not issues:
            print("✅ All component tests passed")

    except ImportError as e:
        issues.append(f"Failed to import VisualSystem: {e}")
    except Exception as e:
        issues.append(f"Unexpected error: {e}")

    return issues


if __name__ == "__main__":
    print("🔍 Validating Visual System...")
    print("=" * 50)

    issues = validate_visual_system()

    if issues:
        print("\n❌ VALIDATION FAILED\n")
        for issue in issues:
            print(f"  • {issue}")
        sys.exit(1)
    else:
        print("\n✅ VALIDATION PASSED")
        print("Visual System is correctly implemented!")
        sys.exit(0)
