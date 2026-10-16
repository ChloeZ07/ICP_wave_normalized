#!/bin/bash

cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 was not found."
  echo "Install Python 3 from: https://www.python.org/downloads/macos/"
  read -r -p "Press Return to close..."
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "First run: creating a local Python environment..."
  python3 -m venv .venv
fi

PYTHON=".venv/bin/python"

if ! "$PYTHON" -c "import numpy,pandas,scipy,matplotlib" >/dev/null 2>&1; then
  echo "Installing required packages..."
  "$PYTHON" -m pip install -r requirements.txt
fi

"$PYTHON" icp_wave_normalized.py

echo
echo "Finished. Results are in the result folder beside this program."
read -r -p "Press Return to close..."
