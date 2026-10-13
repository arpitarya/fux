#!/usr/bin/env python3
"""L13's latency guardrail — median `ask` at `rung-10000`, baseline against the decided arm. Read-only.

Frozen by hash in `PRE-REGISTRATION.md` §Freeze before the generation-6 ladder
exists and before any arm. L13 decision 3: *the median rises by at most 100 ms,
measured standalone on `rung-10000`, three runs per arm, never read from a
loaded capture.*

    python3 latency.py --fux <pinned build fux> --arms <dir holding sw-<λ>/rung-10000> \\
        --questions work/golden/questions/set-7-claude.jsonl > evidence/latency/latency.json

- **Standalone:** run on its own, after every capture, with nothing else of
  this run in flight. It records the load average before and after, so a
  reader can see what else the machine carried; it does not refuse on load,
  because no threshold for that was frozen.
- **Three runs per arm, interleaved:** each run walks every question once and,
  per question, times one `fux ask <q> --json --top 10` in each arm, the arm
  order alternating by run, so drift over the session falls on both arms
  alike. One warm-up call per arm comes first and is not counted.
- **The median** is over every timed call of the arm (3 × the set's size).

It reads `id` and `question` from the released question file and nothing else
under `work/golden/`. It opens no key and runs no scorer. JSON to stdout only.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import time
from pathlib import Path

BASELINE, DECIDED = "sw-0.0", "sw-1.0"
RUNG = "rung-10000"
RUNS = 3
LIMIT_MS = 100.0


def timed(fux: str, tree: Path, question: str) -> float:
    start = time.perf_counter()
    subprocess.run([fux, "ask", question, "--json", "--top", "10"],
                   cwd=tree, capture_output=True, text=True, check=True)
    return (time.perf_counter() - start) * 1000.0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--fux", required=True)
    ap.add_argument("--arms", type=Path, required=True)
    ap.add_argument("--questions", type=Path, required=True)
    args = ap.parse_args()

    rows = [json.loads(l) for l in args.questions.read_text(encoding="utf-8").splitlines() if l.strip()]
    questions = [r["question"] for r in rows]
    trees = {arm: args.arms / arm / RUNG for arm in (BASELINE, DECIDED)}
    for arm, tree in trees.items():
        if not (tree / ".fux" / "index").is_dir():
            raise SystemExit(f"refusing: no index at {tree}")
        timed(args.fux, tree, questions[0])  # warm-up, not counted

    load_before = os.getloadavg()
    ms = {arm: [] for arm in trees}
    for run in range(RUNS):
        order = (BASELINE, DECIDED) if run % 2 == 0 else (DECIDED, BASELINE)
        for q in questions:
            for arm in order:
                ms[arm].append(timed(args.fux, trees[arm], q))
    load_after = os.getloadavg()

    medians = {arm: round(statistics.median(v), 1) for arm, v in ms.items()}
    rise = round(medians[DECIDED] - medians[BASELINE], 1)
    report = {
        "guardrail": "median ask latency at rung-10000, decided arm minus baseline, <= 100 ms (L13 decision 3)",
        "runs_per_arm": RUNS,
        "calls_per_arm": {arm: len(v) for arm, v in ms.items()},
        "median_ms": medians,
        "rise_ms": rise,
        "limit_ms": LIMIT_MS,
        "load_average_before": [round(x, 2) for x in load_before],
        "load_average_after": [round(x, 2) for x in load_after],
        "verdict": "PASS" if rise <= LIMIT_MS else "FAIL",
    }
    print(json.dumps(report, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
