#!/usr/bin/env python3
"""W-287's two latency guardrails. Read-only once prepared.

    python3 latency.py --env <lab env> --questions questions.jsonl --rung <rung-10000> --prepare
    python3 latency.py --env <lab env> --questions questions.jsonl --rung <rung-10000> > latency.json

Frozen by hash in `PRE-REGISTRATION.md`. Run standalone, after every capture,
with nothing else of this run in flight; the load average is recorded before
and after.

1. **`answer` p95 on a 20 000-row sheet** (the work item's guardrail;
   SR-TABULAR's ~2.6 s case). One seeded `.csv` of 20 000 rows in its own repo
   per arm; 20 key lookups; three runs, arm order alternating by run; one
   warm-up per arm. The ratio is decided p95 over baseline p95; limit 1.2.
2. **`ask` median at `rung-10000`** (L13 decision 3): a copy of the golden
   ladder's `rung-10000` per arm, `fux doctor --fix` and `fux ingest --full`
   with this engine; every question's TEXT from this run's own set — never a
   golden question — timed as `fux ask <q> --json --top 10`, three runs,
   alternating. Limit: decided median minus baseline median <= 100 ms.

`--prepare` builds the four repositories and times nothing.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path

ARMS = (("tc-0.0", 0.0), ("tc-1.0", 1.0))
ROWS, LOOKUPS, RUNS = 20000, 20, 3
SEED = 2870


def _cli(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-m", "fux.cli", *args], cwd=root, capture_output=True,
                          text=True, encoding="utf-8", check=True)


def _set_weight(root: Path, weight: float) -> None:
    path = root / ".fux" / "tune.toml"
    lines = path.read_text(encoding="utf-8").split("\n")
    hits = [i for i, l in enumerate(lines) if l.split("=")[0].strip() == "table_column_weight"]
    assert len(hits) == 1
    lines[hits[0]] = f"table_column_weight     = {weight}"
    path.write_text("\n".join(lines), encoding="utf-8")


def _sheet() -> tuple[str, list[str]]:
    rng = random.Random(SEED)
    owners = ["Aarav", "Bina", "Chetan", "Divya", "Esha", "Farhan", "Gauri", "Hari"]
    lines = ["Ticket,Owner,Status,Service,Notes"]
    keys = []
    for i in range(ROWS):
        key = f"INC9{i:06d}"
        keys.append(key)
        lines.append(f"{key},{rng.choice(owners)},{rng.choice(['open', 'closed', 'blocked'])},"
                     f"{rng.choice(['payments', 'ledger', 'search'])},note {rng.randrange(1000)}")
    return "\n".join(lines) + "\n", [keys[rng.randrange(ROWS)] for _ in range(LOOKUPS)]


def prepare(env: Path, rung: Path) -> None:
    base = env / "base" / "repo"
    text, _ = _sheet()
    for arm, weight in ARMS:
        sheet = env / "latency" / "sheet" / arm / "repo"
        if sheet.exists():
            shutil.rmtree(sheet)
        shutil.copytree(base, sheet, symlinks=True)
        shutil.rmtree(sheet / "docs")
        (sheet / "docs").mkdir()
        (sheet / "docs" / "big.csv").write_text(text, encoding="utf-8")
        _set_weight(sheet, weight)
        _cli(sheet, "ingest", "--full")
        copy = env / "latency" / "rung" / arm / "rung-10000"
        if copy.exists():
            shutil.rmtree(copy)
        shutil.copytree(rung, copy, symlinks=True)
        _cli(copy, "doctor", "--fix")
        _set_weight(copy, weight)
        _cli(copy, "ingest", "--full")
        print(arm, "prepared", file=sys.stderr)


def _time(root: Path, *args: str) -> float:
    started = time.perf_counter()
    _cli(root, *args)
    return (time.perf_counter() - started) * 1000


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(round(0.95 * (len(ordered) - 1))))]


def measure(env: Path, questions: list[str]) -> dict:
    _, lookups = _sheet()
    load_before = os.getloadavg()
    sheet = {arm: env / "latency" / "sheet" / arm / "repo" for arm, _ in ARMS}
    rung = {arm: env / "latency" / "rung" / arm / "rung-10000" for arm, _ in ARMS}
    answer_ms = {arm: [] for arm, _ in ARMS}
    ask_ms = {arm: [] for arm, _ in ARMS}
    for arm, _ in ARMS:  # one warm-up each, not counted
        _time(sheet[arm], "answer", f"owner of {lookups[0]}", "--json")
        _time(rung[arm], "ask", questions[0], "--json", "--top", "10")
    for run in range(RUNS):
        order = [a for a, _ in ARMS] if run % 2 == 0 else [a for a, _ in reversed(ARMS)]
        for key in lookups:
            for arm in order:
                answer_ms[arm].append(_time(sheet[arm], "answer", f"owner of {key}", "--json"))
        for q in questions:
            for arm in order:
                ask_ms[arm].append(_time(rung[arm], "ask", q, "--json", "--top", "10"))
    base, dec = ARMS[0][0], ARMS[1][0]
    return {
        "answer_p95_ms": {arm: _p95(v) for arm, v in answer_ms.items()},
        "answer_p95_ratio": _p95(answer_ms[dec]) / _p95(answer_ms[base]),
        "ask_median_ms": {arm: statistics.median(v) for arm, v in ask_ms.items()},
        "ask_median_delta_ms": statistics.median(ask_ms[dec]) - statistics.median(ask_ms[base]),
        "calls": {"answer": {a: len(v) for a, v in answer_ms.items()}, "ask": {a: len(v) for a, v in ask_ms.items()}},
        "load_before": load_before,
        "load_after": os.getloadavg(),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", type=Path, required=True)
    ap.add_argument("--questions", type=Path, required=True)
    ap.add_argument("--rung", type=Path, required=True)
    ap.add_argument("--prepare", action="store_true")
    args = ap.parse_args()
    if args.prepare:
        prepare(args.env, args.rung)
        return 0
    questions = [json.loads(l)["question"] for l in args.questions.read_text(encoding="utf-8").splitlines() if l.strip()]
    print(json.dumps(measure(args.env, questions), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
