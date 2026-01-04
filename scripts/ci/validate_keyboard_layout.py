#!/usr/bin/env python3
"""
Validate keyboard layout.
Ensures max 3 columns per row for reply keyboards.
"""
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from utils.reply_keyboards import UserReplyKeyboard, AdminReplyKeyboard

def validate_keyboard(name, keyboard):
    print(f"Checking {name}...")
    issues = []

    # keyboard.keyboard is a list of lists of KeyboardButton
    for i, row in enumerate(keyboard.keyboard):
        if len(row) > 3:
            issues.append(f"Row {i+1} has {len(row)} buttons (max 3 allowed)")

    if issues:
        print(f"❌ {name} Failed:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print(f"✅ {name} Passed")
        return True

def main():
    success = True

    # Check User Keyboard
    if not validate_keyboard("UserReplyKeyboard", UserReplyKeyboard.build()):
        success = False

    # Check Admin Keyboard (Page 1..Total)
    total_pages = AdminReplyKeyboard.get_total_pages()
    for page in range(1, total_pages + 1):
        if not validate_keyboard(f"AdminReplyKeyboard (Page {page})", AdminReplyKeyboard.build(page)):
            success = False

    if success:
        print("\n✅ All keyboard layouts valid.")
        sys.exit(0)
    else:
        print("\n❌ Keyboard layout validation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
