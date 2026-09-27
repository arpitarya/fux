"""Make `tests/l12_fixtures.py` importable here too.

The e2e suite builds repositories by hand in a few places, and L12 makes every
config key mandatory; those repositories get their config the same way the unit
suite's do — from `l12_fixtures.write_config`, which runs the engine's own writer.
"""

from __future__ import annotations

import sys
from pathlib import Path

_TESTS = str(Path(__file__).resolve().parents[1] / "tests")
if _TESTS not in sys.path:
    sys.path.insert(0, _TESTS)
