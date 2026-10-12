#!/usr/bin/env python3
"""G0 — at `section_weight = 0.0` the pinned build captures what the pre-section engine captures. Read-only.

L13's first gate: *the change OFF is byte-identical to the engine without it,
over every golden row*. Frozen by hash in `PRE-REGISTRATION.md` §Freeze before
the generation-6 ladder exists and before any arm. Two captures of
`set-7-claude` on the SAME generation-6 `rung-01000` copy's sources:

- **before** — the pre-section engine, `main` at `dca6aaa4`, on its own
  `ingest --full` (`fux.index.v7`, no section plane);
- **after** — W-278's build (the engine pinned in PRE-REGISTRATION.md §Freeze), at `section_weight = 0.0`, on
  the base copy every arm is made from (`fux.index.v8`).

W-236 and W-269 chained their G0 through each other's captures; generation 5
has no earlier capture, so this compares with the pre-section engine directly.

    python3 g0.py <before evidence dir> <after evidence dir> > evidence/g0/g0.json

Each directory holds `handoff-set-7-claude.jsonl` and
`predictions-set-7-claude.jsonl`, as `golden_run.py` writes them. Every field of
every row is compared except the latencies and the stamps.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SET = "set-7-claude"
IGNORED = {"ask_ms", "answer_ms", "arm", "engine_commit", "repo_head"}


def rows(path: Path) -> dict[str, dict]:
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            out[row["id"]] = {k: v for k, v in row.items() if k not in IGNORED}
    return out


def main() -> int:
    before, after = Path(sys.argv[1]), Path(sys.argv[2])
    report = {
        "gate": "G0 - byte identity at section_weight = 0.0, W-278 build against the pre-section engine",
        "compared": "every field of every row except " + ", ".join(sorted(IGNORED)),
    }
    for kind in ("handoff", "predictions"):
        a, b = rows(before / f"{kind}-{SET}.jsonl"), rows(after / f"{kind}-{SET}.jsonl")
        if set(a) != set(b):
            raise SystemExit(f"refusing: the {kind} files disagree on ids")
        report[f"{kind}_rows"] = len(a)
        report[f"{kind}_rows_differing"] = sorted(i for i in a if a[i] != b[i])
    report["verdict"] = (
        "PASS" if not report["handoff_rows_differing"] and not report["predictions_rows_differing"] else "FAIL"
    )
    print(json.dumps(report, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
