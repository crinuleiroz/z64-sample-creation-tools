#!/usr/bin/env bash
set -e

# Update PIP
python3 -m pip install --upgrade pip

# Install from requirements.txt
python3 -m pip install -r requirements.txt

echo ""
echo "Requirements installation complete."