#!/usr/bin/env bash
set -e

# Go to script directory
cd "$(dirname "$0")"

# Create venv if missing
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install deps
pip install --upgrade pip
pip install -r requirements.txt

# Run app
python3 app.py
