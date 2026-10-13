#!/usr/bin/env python3
"""G0 — at `section_weight = 0.0` the W-269 build captures what W-236's build captured. Read-only.

Written 2026-10-10 **before any W-269 build code existed**, frozen by hash in
`PRE-REGISTRATION.md` §Freeze. The gain-only change touches only arithmetic that
runs while `λ ≠ 0`, so at `0.0` the W-269 build must reproduce W-236's
`sw-0.0` capture row for row. W-236's own G0 already tied that capture to the
pre-section engine (`2026-10-10-section-records/evidence/g0/g0.json`, 0 of 90),
so this chains the W-269 build to the pre-section engine too.

    python3 g0.py <W-236 sw-0.0 evidence dir> <W-269 sw-0.0 evidence dir> > evidence/g0/g0.json

Each directory holds `handoff-set-5-claude.jsonl` and
`predictions-set-5-claude.jsonl`, as `golden_run.py` writes them. Every field of
every row is compared except the latencies and the stamps.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SET = "set-5-claude"
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
        "gate": "G0 - byte identity at section_weight = 0.0, W-269 build against W-236's sw-0.0 capture",
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
