#!/usr/bin/env bash
# Run the StyleAgent CLI locally.
# Usage: ./scripts/run_local.sh [CLI args]
# Example: ./scripts/run_local.sh analyze --image ./photo.jpg --occasion indian_casual

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Validate environment first
python3 scripts/validate_env.py

# Run the CLI
python3 src/main.py "$@"
