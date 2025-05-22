#!/bin/bash

# Path to the automation directory
AUTOMATION_DIR="/Users/kdm/projects/digital-ext/business-os-automations"
JOURNAL_ROOT="/Users/kdm/projects/digital-ext/business-os/00_daily-journal"

# Change to the automation directory
cd "$AUTOMATION_DIR"

# Run the journal automation module
# Using the full path avoids issues with launchd not finding the Python interpreter
/opt/homebrew/bin/python3 -m journal_daily_setup.main --root "$JOURNAL_ROOT"