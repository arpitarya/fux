#!/usr/bin/env python3
"""W-287's capture — every arm's raw `answer` and `ask` output, and NO score.

    python3 capture.py --env <lab env> --questions <questions.jsonl> --out <captures dir>

Frozen by hash in `PRE-REGISTRATION.md` before any arm exists. It builds one
repository per arm from `<env>/base/repo` (a copy, so the base is never
touched), sets the arm's `[ranking] table_column_weight`, ingests, and asks
every question through `fux.api` — the CLI's own payload builders
(`build_answer`, `build_ask`), so what is captured is what `fux answer --json
--band` prints.

🔴 **It computes no endpoint.** It writes what each arm returned — the cited
documents, their rows, cells and `columns_matched`, the band — and the
questions' answers are read only by `decide.py`, which a hand that did not run
this capture runs (SR-RS decision 6, L13 decision 4).

**The arms** — one engine, one corpus, one index root per arm:

| arm | `table_column_weight` | ablation |
|---|---|---|
| `tc-0.0` | 0.0 | — the baseline: the mechanism off |
| `tc-1.0` | 1.0 | — **the decided arm**: B2–B5 as one mechanism |
| `tc-1.0-noB3` | 1.0 | the column selector returns no bonus and no column |
| `tc-1.0-noB4` | 1.0 | no table has a key column |
| `tc-1.0-noB5` | 1.0 | no table is a record |
| `tc-1.0-B2` | 1.0 | B3, B4 and B5 all off: the field split alone |

The ablations patch three functions in-process for their arm only; every
other arm runs the shipped code untouched.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

ARMS = {
    "tc-0.0": (0.0, ()),
    "tc-1.0": (1.0, ()),
    "tc-1.0-noB3": (1.0, ("B3",)),
    "tc-1.0-noB4": (1.0, ("B4",)),
    "tc-1.0-noB5": (1.0, ("B5",)),
    "tc-1.0-B2": (1.0, ("B3", "B4", "B5")),
}
TOP = 10


@contextlib.contextmanager
def ablated(off: tuple[str, ...]):
    from fux.refer import _rescore
    from fux.text import chunk as chunk_mod

    saved = (_rescore._selector, chunk_mod._key_column, chunk_mod._RECORD_HEADERS)
    try:
        if "B3" in off:
            _rescore._selector = lambda *a, **k: (0.0, ())
        if "B4" in off:
            chunk_mod._key_column = lambda values, width: -1
        if "B5" in off:
            chunk_mod._RECORD_HEADERS = frozenset()
        yield
    finally:
        _rescore._selector, chunk_mod._key_column, chunk_mod._RECORD_HEADERS = saved


def _set_weight(root: Path, weight: float) -> None:
    path = root / ".fux" / "tune.toml"
    lines = path.read_text(encoding="utf-8").split("\n")
    hits = [i for i, l in enumerate(lines) if l.split("=")[0].strip() == "table_column_weight"]
    assert len(hits) == 1, "the base repo's tune.toml must carry table_column_weight once"
    lines[hits[0]] = f"table_column_weight     = {weight}"
    path.write_text("\n".join(lines), encoding="utf-8")


def _index_digest(root: Path) -> str:
    h = hashlib.sha256()
    for path in sorted((root / ".fux" / "index").rglob("*")):
        if path.is_file():
            h.update(path.relative_to(root).as_posix().encode())
            h.update(path.read_bytes())
    return h.hexdigest()


def _passage(p: dict) -> dict:
    return {
        "id": p.get("id"), "loc": p.get("loc"), "heading": p.get("heading"),
        "ordinal": p.get("ordinal"), "score": p.get("score"),
        "table": p.get("table"), "row": p.get("row"), "cells": p.get("cells"),
        "columns_matched": p.get("columns_matched"),
        "text": p.get("text"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", type=Path, required=True)
    ap.add_argument("--questions", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    import fux
    from fux import api
    from fux.ingest.run import run as ingest

    questions = [json.loads(l) for l in args.questions.read_text(encoding="utf-8").splitlines() if l.strip()]
    args.out.mkdir(parents=True, exist_ok=True)
    base = args.env / "base" / "repo"
    meta = {"engine": fux.__file__, "version": fux.__version__, "arms": {}}
    for arm, (weight, off) in ARMS.items():
        root = args.env / "arms" / arm / "repo"
        if root.exists():
            shutil.rmtree(root)
        shutil.copytree(base, root, symlinks=True)
        _set_weight(root, weight)
        ingest(root, refresh_urls=False, full=True)
        fx = api.open(root)
        rows = []
        with ablated(off):
            for q in questions:
                started = time.perf_counter()
                answer = fx.answer(q["question"], audit=False, receipt=False, band=True).as_dict()
                elapsed = time.perf_counter() - started
                asked = fx.ask(q["question"], top=TOP, band=True).results
                passages = (answer.get("answer") or {}).get("passages") or []
                rows.append({
                    "id": q["id"],
                    "passages": [_passage(p) for p in passages[:TOP]],
                    "band": (answer.get("confidence") or {}).get("band"),
                    "source": answer.get("source"),
                    "ask": [r.as_dict() for r in asked],
                    "answer_ms": round(elapsed * 1000, 3),
                })
        with (args.out / f"{arm}.jsonl").open("w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, sort_keys=True) + "\n")
        meta["arms"][arm] = {"table_column_weight": weight, "ablated": list(off),
                             "index_digest": _index_digest(root), "questions": len(rows)}
        print(arm, "captured", len(rows), file=sys.stderr)
    (args.out / "meta.json").write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
