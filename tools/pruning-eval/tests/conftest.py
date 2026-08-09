"""Path wiring: the harness plus the archived engine it measures.

The archived engine is imported, never installed and never modified — the
harness's whole contract is that `archive/v0.26/` is read-only reference code.
"""

from __future__ import annotations

import sys
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1]
REPO = TOOL.parents[1]
ARCHIVE_SRC = REPO / "archive" / "v0.26" / "src"

for path in (str(TOOL), str(ARCHIVE_SRC)):
    if path not in sys.path:
        sys.path.insert(0, path)
