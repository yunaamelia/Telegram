"""Validate Loading States implementation."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import inspect


def validate_loading_states():
    """Validate LoadingStates class."""
    issues = []

    try:
        from utils.loading_states import LoadingStates, loading

        # Check required attributes
        required_attrs = [
            'LOADING_FRAMES', 'PROCESSING_FRAMES',
            'show_loading', 'with_loading', 'typing_indicator'
        ]

        for attr in required_attrs:
            if not hasattr(LoadingStates, attr):
                issues.append(f"Missing required attribute/method: {attr}")

        # Check loading frames
        if not LoadingStates.LOADING_FRAMES:
            issues.append("LOADING_FRAMES is empty")
        elif not isinstance(LoadingStates.LOADING_FRAMES, list):
            issues.append("LOADING_FRAMES should be a list")
        elif len(LoadingStates.LOADING_FRAMES) < 2:
            issues.append("LOADING_FRAMES should have at least 2 frames")

        # Check processing frames
        if not LoadingStates.PROCESSING_FRAMES:
            issues.append("PROCESSING_FRAMES is empty")
        elif not isinstance(LoadingStates.PROCESSING_FRAMES, list):
            issues.append("PROCESSING_FRAMES should be a list")

        # Check shorthand alias
        if loading != LoadingStates:
            issues.append("Shorthand alias 'loading' not set correctly")

        if not issues:
            print("✅ LoadingStates structure is valid")

        # Check if methods are async
        if not inspect.iscoroutinefunction(LoadingStates.show_loading):
            issues.append("show_loading() should be async")

        if not inspect.iscoroutinefunction(LoadingStates.with_loading):
            issues.append("with_loading() should be async")

        if not inspect.iscoroutinefunction(LoadingStates.typing_indicator):
            issues.append("typing_indicator() should be async")

        if not issues:
            print("✅ All methods are properly async")

    except ImportError as e:
        issues.append(f"Failed to import LoadingStates: {e}")
    except Exception as e:
        issues.append(f"Unexpected error: {e}")

    return issues


if __name__ == "__main__":
    print("🔍 Validating Loading States...")
    print("=" * 50)

    issues = validate_loading_states()

    if issues:
        print("\n❌ VALIDATION FAILED\n")
        for issue in issues:
            print(f"  • {issue}")
        sys.exit(1)
    else:
        print("\n✅ VALIDATION PASSED")
        print("Loading States are correctly implemented!")
        sys.exit(0)
