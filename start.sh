#!/usr/bin/env bash
set -euo pipefail

# Resolve the absolute directory where this script lives (folder xyz)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Switch working directory to xyz so relative file paths resolve properly
cd "${SCRIPT_DIR}"

# Run with relative paths and forward any CLI arguments
PYTHONPATH="src:lib/python3.12/site-packages" nohup python3 "src/starter.py" "$@"
