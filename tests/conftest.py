"""Put `tests/` itself on the import path, for the suite's shared helpers.

Test modules in subdirectories (`tests/query/`, `tests/refer/`, …) import
`l12_fixtures` — the one place a hand-built repository gets the config files L12
makes mandatory — and pytest's default import mode only adds a test file's own
directory. `sr_lib` needed no such help because every importer sits beside it.
"""

from __future__ import annotations

import sys
from pathlib import Path

_TESTS = str(Path(__file__).resolve().parent)
if _TESTS not in sys.path:
    sys.path.insert(0, _TESTS)
