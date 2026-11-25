"""
Pytest configuration for SQE pretix unit tests.
Ensures repository root is importable so upstream scoped production logic executes cleanly.
"""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pretix.settings")
