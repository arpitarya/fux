"""A deliberately slow observer — the arm that tests the CAP's actual promise.

[SR-OBSERVE](../../records/0157_observe.md) decision 10b corrected decision 6:
the cap **abandons** a thread, it does not kill one. Python cannot safely
interrupt arbitrary consumer code. So the claim that can be measured is not
*"the observer was stopped"* — it is:

> **a consumer's analytics cannot make `fux ask` slow, only itself.**

This observer sleeps for `FUX_SLOW_OBSERVER_MS` milliseconds, far past any
sensible `[observe] max_ms`. If the cap holds, `ask` returns at roughly
`off + max_ms` and **not** at `off + sleep`. If it does not, the difference is
the whole sleep and the promise is false.

⚠ **It still writes its line**, after the sleep, so the run can tell *abandoned*
(fux stopped waiting, the thread finished later) from *never ran*.
"""

from __future__ import annotations

import json
import os
import time


def observe(record: dict) -> None:
    time.sleep(float(os.environ.get("FUX_SLOW_OBSERVER_MS", "2000")) / 1000.0)
    path = os.environ.get("FUX_SLOW_OBSERVER_LOG")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
