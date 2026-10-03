#!/usr/bin/env bash
# install.sh — project-level setup for wordcount.
#
# Installs the declared dependencies and the optional `wordcount` console
# script, then runs a cheap self-check that proves the program imports and
# counts.  It never starts a server and never touches the system package
# manager, so it is safe to re-run and safe for an unprivileged user.
set -euo pipefail
cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"

echo "==> Interpreter: $("$PYTHON" --version 2>&1) ($PYTHON)"

echo "==> Upgrading packaging tools: pip, setuptools, wheel"
"$PYTHON" -m pip install --upgrade pip setuptools wheel

echo "==> Installing project dependencies from requirements.txt"
"$PYTHON" -m pip install -r requirements.txt

echo "==> Installing the optional 'wordcount' console script (editable, no runtime deps)"
"$PYTHON" -m pip install --no-build-isolation -e .

echo "==> Self-check: import the program and count an example file"
"$PYTHON" -c "import wordcount; print('count_words(\"the quick brown fox\") ->', wordcount.count_words('the quick brown fox'))"
"$PYTHON" wordcount.py examples/sample.txt

echo
echo "Setup complete. Nothing is running in the background."
echo "  Count a file : $PYTHON wordcount.py <path>"
echo "  Walkthrough  : bash demo.sh"
echo "  Test suite   : $PYTHON -m pytest"
