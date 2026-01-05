#!/bin/bash
# Master UI/UX Validation Script

echo "🎨 ================================================"
echo "   UI/UX ENHANCEMENT - VALIDATION SUITE"
echo "================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0

# Activate virtual environment if exists
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Function to run validation
run_validation() {
    local name=$1
    local script=$2
    
    echo "🔍 Running: $name"
    if python "$script"; then
        echo -e "${GREEN}✅ PASSED${NC}\n"
    else
        echo -e "${RED}❌ FAILED${NC}\n"
        ((ERRORS++))
    fi
}

# Create reports directory
mkdir -p reports

# 1. Visual System Validation
run_validation "Visual System" "scripts/validation/validate_visual_system.py"

# 2. Message Templates Validation
run_validation "Message Templates" "scripts/validation/validate_message_templates.py"

# 3. Unicode Integration
run_validation "Unicode Font Integration" "scripts/validation/validate_unicode_integration.py"

# 4. Loading States
run_validation "Loading States" "scripts/validation/validate_loading_states.py"

# 5. Message Output
run_validation "Message Outputs" "scripts/validation/validate_message_output.py"

# 6. Generate Visual Preview
echo "🎨 Generating visual preview..."
if python scripts/validation/generate_visual_preview.py; then
    echo -e "${GREEN}✅ Preview generated${NC}\n"
else
    echo -e "${YELLOW}⚠️  Preview generation failed${NC}\n"
fi

# Summary
echo "================================================"
echo "   VALIDATION SUMMARY"
echo "================================================"

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ ALL VALIDATIONS PASSED!${NC}"
    echo ""
    echo "UI/UX enhancement is correctly implemented."
    echo ""
    echo "Next steps:"
    echo "  1. Review visual preview: reports/ui_visual_preview.txt"
    echo "  2. Test on actual Telegram"
    echo "  3. Gather user feedback"
    exit 0
else
    echo -e "${RED}❌ $ERRORS VALIDATION(S) FAILED${NC}"
    echo ""
    echo "Please fix the issues above and run validation again."
    exit 1
fi
