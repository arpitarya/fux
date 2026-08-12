"""The derived plane — the T1 accelerator (M2).

Everything here is rebuildable from the committed shards and is never
committed. Deleting `.fux/runtime/` costs a rebuild and nothing else.

The law this package lives under: **its results are identical to
`query/scan.py`'s, byte for byte**. See `accel` for the argument and
`tools/differential/` for the proof.
"""

from __future__ import annotations

from .accel import Runtime, accel_candidates, ask, block_bound, is_fresh
from .build import BuildReport, build
from .format import BLOCK_SIZE, ENTRY_SIZE, RUNTIME_SCHEMA, runtime_dir

__all__ = [
    "BLOCK_SIZE",
    "ENTRY_SIZE",
    "RUNTIME_SCHEMA",
    "BuildReport",
    "Runtime",
    "accel_candidates",
    "ask",
    "block_bound",
    "build",
    "is_fresh",
    "runtime_dir",
]
