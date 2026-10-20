#!/usr/bin/env bash
# Offline installer for file_flag (Linux/macOS).
# NOTE: the bundled wheels target Windows x86_64 / CPython 3.11. On another
# platform, re-run ./build_bundle.sh to fetch matching wheels.
set -euo pipefail
WHEELS="$(cd "$(dirname "$0")/wheels" && pwd)"

echo "Using wheels in: $WHEELS"
python3 -m pip install --no-index --find-links "$WHEELS" --upgrade pip setuptools wheel
python3 -m pip install --no-index --find-links "$WHEELS" file_flag==0.1.2
echo "Done. Verify with: python3 -m file_flag --help"
