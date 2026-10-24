#!/usr/bin/env python3
"""Run a FROZEN `g3.py` for ONE treatment arm, and merge the per-arm reports. W-281 DoD 3.

`g3.py` is hashed in its run's pre-registration and is never edited. It loops a
module-level `TREATMENTS` tuple; this driver imports the frozen file unchanged,
narrows that tuple to one arm, and calls its own `main()`. Its logic, its
baseline and its verdict rule are the frozen file's; only the *schedule*
differs (one process per arm, so the arms run side by side).

    python3 g3_one_arm.py run   <g3.py> <treatment arm> [g3 args...] > g3-<arm>.json
    python3 g3_one_arm.py merge g3-<arm>.json ...                    > g3.json

`merge` unions the `arms`, and the verdict is PASS iff every part is PASS. It
refuses parts that disagree on the gate, the question count or the
sectionless-document count, so a merge cannot hide a mismatched run.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def run(g3_path: str, arm: str, argv: list[str]) -> int:
    spec = importlib.util.spec_from_file_location("g3_frozen", g3_path)
    g3 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g3)
    if arm not in g3.TREATMENTS:
        raise SystemExit(f"refusing: {arm!r} is not one of the frozen treatments {g3.TREATMENTS}")
    g3.TREATMENTS = (arm,)
    sys.argv = [g3_path, *argv]
    return g3.main()


def merge(parts: list[dict]) -> dict:
    if not parts:
        raise SystemExit("refusing: nothing to merge")
    keys = ("gate", "questions", "sectionless_documents")
    for p in parts[1:]:
        if any(p.get(k) != parts[0].get(k) for k in keys):
            raise SystemExit("refusing: the parts disagree on gate/questions/sectionless_documents")
    out = {k: parts[0][k] for k in keys}
    out["arms"] = {}
    for p in parts:
        out["arms"].update(p["arms"])
    out["verdict"] = "PASS" if all(p.get("verdict") == "PASS" for p in parts) else "FAIL"
    return out


def main() -> int:
    if len(sys.argv) >= 4 and sys.argv[1] == "run":
        return run(sys.argv[2], sys.argv[3], sys.argv[4:])
    if len(sys.argv) >= 3 and sys.argv[1] == "merge":
        parts = [json.loads(Path(f).read_text(encoding="utf-8")) for f in sys.argv[2:]]
        print(json.dumps(merge(parts), indent=1, sort_keys=True))
        return 0
    raise SystemExit(__doc__)


if __name__ == "__main__":
    raise SystemExit(main())
