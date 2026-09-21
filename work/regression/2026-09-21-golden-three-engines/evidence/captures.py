#!/usr/bin/env python3
"""W-204 phase B — SR-WORK-BENCHMARK captures 1, 2, 5 and 6, per arm, per rung.

🔴 **Captures 3, 4 and 7 are DELIBERATELY not computed here.** Each needs the
answer key: `hit@k` needs `relevant`, the answer-layer capture needs
`answerable`, and the HTML report reports both. They are phase D's, after Arpit
pastes the key, and a number invented for them now would be indistinguishable
from a scored one.

**What this does compute:**

- **capture 1** — ranked lists per query per arm. They are the `handoff-*.jsonl`
  rows themselves; this prints their shape so the report can cite a count.
- **capture 2** — what MOVED between arms: top-1 changes and full-list changes,
  per pair, per set, never pooled.
- **capture 5** — committed index bytes per rung per arm.
- **capture 6** — speed, reported with the caveat SR-WORK-BENCHMARK requires.

🔴 **The two sets are never pooled and the three arms are compared pairwise**,
with the floor printed and NOT applied — decision 10b keeps a threshold in the
frozen pre-registration and out of the instrument.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path("/Users/arpitarya/my_programs/fux")
EV = ROOT / "work" / "regression" / "2026-09-21-golden-three-engines" / "evidence"
HEAD_EV = ROOT / "work" / "regression" / "2026-09-21-golden-ladder-outputs-set-3" / "evidence"
LAB = Path.home() / "my_programs" / "fux-lab"
RUNGS = ["rung-seed", "rung-00100", "rung-00200", "rung-00500",
         "rung-01000", "rung-02000", "rung-05000", "rung-10000"]
SETS = (1, 2, 3)


def rows(arm: str, rung: str, n: int) -> dict[str, dict] | None:
    path = (HEAD_EV if arm == "HEAD" else EV / arm) / rung / f"handoff-set-{n}.jsonl"
    if not path.is_file():
        return None
    return {r["id"]: r for r in map(json.loads, path.read_text().splitlines()) if r}


def index_kb(arm: str, rung: str) -> int | None:
    tree = (LAB / "corpora" / "golden" / rung) if arm == "HEAD" else (LAB / "arms" / "runs" / arm / rung)
    idx = tree / ".fux" / "index"
    if not idx.is_dir():
        return None
    out = subprocess.run(["du", "-sk", str(idx)], capture_output=True, text=True)
    return int(out.stdout.split()[0]) if out.returncode == 0 else None


def main() -> int:
    print("## Capture 1 — ranked lists, per arm\n")
    print("| arm | rungs | sets | rows |")
    print("|---|---:|---:|---:|")
    for arm in ("v1", "v2", "HEAD"):
        n = sum(len(rows(arm, r, s) or {}) for r in RUNGS for s in SETS)
        have = sum(1 for r in RUNGS if rows(arm, r, 1) is not None)
        print(f"| `{arm}` | {have} | {len(SETS)} | {n} |")

    print("\n## Capture 2 — what moved between arms, per set, never pooled\n")
    print("| pair | rung | set | n | top-1 changed | whole list changed |")
    print("|---|---|---:|---:|---:|---:|")
    for a, b in (("v1", "v2"), ("v2", "HEAD"), ("v1", "HEAD")):
        for rung in RUNGS:
            for s in SETS:
                ra, rb = rows(a, rung, s), rows(b, rung, s)
                if not ra or not rb:
                    continue
                ids = sorted(ra.keys() & rb.keys())
                top1 = sum(1 for i in ids
                           if (ra[i]["ranked"] or [None])[0] != (rb[i]["ranked"] or [None])[0])
                whole = sum(1 for i in ids if ra[i]["ranked"] != rb[i]["ranked"])
                print(f"| {a} → {b} | `{rung}` | {s} | {len(ids)} | {top1} | {whole} |")

    print("\n## Capture 5 — committed index bytes (KB), per rung per arm\n")
    print("| rung | v1 | v2 | HEAD |")
    print("|---|---:|---:|---:|")
    for rung in RUNGS:
        cells = [index_kb(a, rung) for a in ("v1", "v2", "HEAD")]
        print(f"| `{rung}` | " + " | ".join("—" if c is None else f"{c:,}".replace(",", " ")
                                            for c in cells) + " |")

    print("\n## Capture 6 — speed, `ask` p50 / p95 ms\n")
    print("⚠ NOT interleaved: the arms ran in blocks, so this is descriptive.\n")
    print("| rung | v1 p50 | v1 p95 | v2 p50 | v2 p95 | HEAD p50 | HEAD p95 |")
    print("|---|---:|---:|---:|---:|---:|---:|")
    for rung in RUNGS:
        cells = []
        for arm in ("v1", "v2", "HEAD"):
            ms = sorted(r["ask_ms"] for s in SETS for r in (rows(arm, rung, s) or {}).values())
            cells += ([f"{ms[len(ms)//2]:.0f}", f"{ms[int(len(ms)*0.95)]:.0f}"] if ms else ["—", "—"])
        print(f"| `{rung}` | " + " | ".join(cells) + " |")

    print("\n## 🔴 Captures 3, 4 and 7 — EMPTY until phase D\n")
    print("| # | capture | why it is empty |")
    print("|---|---|---|")
    print("| 3 | `hit@k` at 1/5/10/20/50 | needs `relevant` from the key |")
    print("| 4 | the answer layer vs the planted unanswerables | needs `answerable` |")
    print("| 7 | the HTML report, one slide per capture | it reports 3 and 4 |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
