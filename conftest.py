"""Pytest bootstrap: make the project root importable however pytest is invoked.

The configuration in pyproject.toml already adds the root to ``sys.path``; this
keeps ``import wordcount`` working for someone who runs pytest from inside
``tests/`` or points it at a single file.
"""

import sys
from pathlib import Path

PROJECT_ROOT = str(Path(__file__).resolve().parent)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
