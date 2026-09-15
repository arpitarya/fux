"""The REFERENCE observer — representative of a seam, not of a subscriber.

⚠ **Read the warning before the number.** This observer appends one line and
returns. That prices the **dispatch seam** — find the directory, import a
module, build the record, call it, restore stdout — and it prices **nothing a
real subscriber does**. Cage's observer writes cage's ledger; a `p50` measured
here must never be reported as a subscriber's.

W-181 resolved the fork it was filed with in favour of running this **first**:
the seam's cost exists today and is fux's to know, while a subscriber's cost is
not fux's to write and not fux's to promise. **Cage's real observer is the
reopen trigger**, not an alternative to measuring what can be measured now.

Deliberately the CHEAPEST honest observer:

- one `open`/`write`/`close` per call, no buffering across runs, because a
  subscriber that batches in memory would be measuring an optimisation fux does
  not control;
- no import of anything outside the stdlib;
- no work derived from the record's contents, so the number does not move with
  what was asked.

Anything cheaper would not write at all, and an observer that writes nothing is
not an observer.
"""

from __future__ import annotations

import json
import os


def observe(record: dict) -> None:
    path = os.environ.get("FUX_REFERENCE_OBSERVER_LOG")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
