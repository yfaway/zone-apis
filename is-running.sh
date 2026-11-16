#!/usr/bin/env bash
set -euo pipefail

# Return exit code 0 (true) if running, 1 (false) if not
if pgrep -f "python3 src/starter.py" > /dev/null; then
  exit 0
else
  exit 1
fi
