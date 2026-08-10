"""The refer plane — M4. Fetches cited documents from the systems that own
them (git dir / HTTP / Confluence), re-scores on fetched bytes, and cites a
fresh sha. Empty stub in M1: `fux ask` cites `loc` from the committed index
directly; no fetch, no network, no ARC cache yet (scope fence, M1 handoff §3).
"""

from __future__ import annotations
