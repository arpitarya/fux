#!/usr/bin/env python3
"""G0 — with the key OFF, `answer` is the engine without stage B. Read-only.

    python3 g0.py --repo <arms/tc-0.0/repo> --questions questions.jsonl > g0.json

Frozen by hash in `PRE-REGISTRATION.md`. *The engine without B* is the same
engine with no row metadata at all: `chunk._row_meta` patched to return `None`,
so no passage carries a `TableRow` and nothing of B can be reached. Every
question is answered both ways in the `tc-0.0` repository and the cited
passages compared on what decides a citation — document, ordinal, heading,
text, score and order.

⚠ **The locator is not compared**, and that is the one field excluded: a
spreadsheet row's `book.xlsx#Sheet!R12` (C3) needs the row it is being taken
away from here. C3 is presentation, not stage B, and holds in both arms of the
run.

⚠ **Nor is the order WITHIN an exact score tie.** `rescore` and `assemble`
break a tie on the locator, so C3's new `.xlsx` locator can reorder rows that
score identically — the five `Dashboard` rows of `services.xlsx`, say. Each run
of equal scores is compared as a sorted group; a question whose groups agree but
whose order inside one does not is listed in `tie_reorders`, which is C3's
effect, descriptive, and not read by the gate. Found by the harness smoke run
on two throwaway questions, before the freeze.

Prints `{"questions", "differing", "rows", "tie_reorders"}`.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _key(p: dict) -> tuple:
    return (p.get("id"), p.get("ordinal"), p.get("heading"), p.get("text"), p.get("score"))


def _groups(keys: list[tuple]) -> list[list[tuple]]:
    """The cited passages as runs of equal score, each run sorted."""
    out: list[list[tuple]] = []
    for k in keys:
        if out and out[-1][0][-1] == k[-1]:
            out[-1].append(k)
        else:
            out.append([k])
    return [sorted(g, key=repr) for g in out]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--questions", type=Path, required=True)
    args = ap.parse_args()

    from fux import api
    from fux.text import chunk as chunk_mod

    questions = [json.loads(l) for l in args.questions.read_text(encoding="utf-8").splitlines() if l.strip()]
    fx = api.open(args.repo)
    tune = (args.repo / ".fux" / "tune.toml").read_text(encoding="utf-8")
    assert "table_column_weight     = 0.0" in tune, "G0 runs on the OFF arm"

    def answer(q):
        payload = fx.answer(q, audit=False, receipt=False, band=True).as_dict()
        return [_key(p) for p in ((payload.get("answer") or {}).get("passages") or [])]

    with_rows = {q["id"]: answer(q["question"]) for q in questions}
    saved = chunk_mod._row_meta
    chunk_mod._row_meta = lambda header, body: None
    try:
        without = {q["id"]: answer(q["question"]) for q in questions}
    finally:
        chunk_mod._row_meta = saved
    differing = sorted(i for i in with_rows if _groups(with_rows[i]) != _groups(without[i]))
    reorders = sorted(i for i in with_rows if with_rows[i] != without[i] and i not in differing)
    print(json.dumps({"questions": len(questions), "differing": len(differing), "rows": differing,
                      "tie_reorders": reorders}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
