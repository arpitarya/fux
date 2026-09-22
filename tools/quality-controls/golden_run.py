#!/usr/bin/env python3
"""W-136 phase 5 — run both question sets on one rung and write the hand-off.

🔴 **It records what fux DID. It never says whether fux was right.**
There is no answer key anywhere and none reaches a Claude session by any route
([L11](../../records/0012_LAW-11-sealed-answer-key.md)); *correct* first appears
in prompt 6's output, from Codex, against a key Arpit pastes there. **A report
that guessed would train the next reader to trust a guess.**

Two `fux` calls per question — `ask --json --band --why --top 10` and
`answer --json` — and two files per set, **never merged**: the gap between a
Codex-authored set 1 and the Claude-authored sets is the measurement, and a mean
across them erases it.

⚠ **`--why` is there for exactly five integers** (W-212, 2026-09-22).
[SR-WORK-QUALITY](../../records/0056_WORK-quality.md) decision 1's funnel —
`reachable` → `in window` → `placed` → `answered`, plus `cut_score`, the score of
the last document inside the window — lives **only** in `ask --json --why`'s
`derivation.gates`. It is computed per query and thrown away unless somebody
asks for it, and W-204 phase D scored 11 716 rows without it and **could not
compute the headline funnel at all**: the cut line had been derived and discarded
11 716 times. **The rest of the derivation is not captured** — the per-term rows
are large and the funnel needs five numbers.

🔴 **`--sets` takes NAMES and is REQUIRED (2026-09-22, W-215).** It was a list of
integers with a `1,2,3` default until generation 1 retired — and the moment those
three files moved to `retired/`, that default named nothing that exists. L11
decision 14 names the next generation `set-<gen>-<x|u>` (`set-2-u`, `set-3-x`),
which is not an integer, so the token is now whatever sits between `set-` and
`.jsonl` and it is written out in the file names this run produces.

⚠ **Required rather than defaulted, deliberately.** A default is a guess about
which generation is current, and a run that guesses wrong files a complete-looking
hand-off for the wrong set. Naming the sets on the command line is how a run says
which ones it actually asked — and a named set with no file is **refused**, never
skipped, because *this rung has no set-2-u rows* and *set-2-u was never asked* are
indistinguishable in the evidence afterwards.

⚠ **Reads `id` and `question` from `work/golden/questions/` and nothing else**,
which is what SR-WORK-GOLDEN decision 2 permits. It opens no other path under
`work/golden/` except the rung's own manifest.

    python3 tools/quality-controls/golden_run.py --rung rung-00100 \
        --dest work/regression/<date>-golden-rung-00100 --sets 2-u
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUESTIONS = ROOT / "work" / "golden" / "questions"
CORPORA = Path.home() / "my_programs" / "fux-lab" / "corpora" / "golden"

#: SR-WORK-QUALITY decision 1's four gates plus the cut line, in funnel order.
#: **Named here once** so the writer, the per-rung document and phase D cannot
#: disagree about which five fields a hand-off owes.
GATE_FIELDS = ("reachable", "in_window", "placed", "answered", "cut_score")

#: What a `--sets` token may look like. It becomes both a path segment under
#: `work/golden/questions/` and a file name in the run's evidence, so it is
#: restricted rather than trusted — `..` in a set name would walk a run into the
#: one directory no agent may open.
SET_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]*")


def call(tree: Path, *args: str, fux: str | None = None) -> tuple[dict | None, float]:
    """One `fux` call in `tree`, timed.

    ⚠ **`fux` names the ENGINE BINARY, and it is a parameter because W-204
    phase B runs three of them.** The default is this tree's own module, which
    is what every single-arm run wants; an arm passes its own venv's `fux`.
    """
    cmd = [fux, *args] if fux else [sys.executable, "-m", "fux.cli", *args]
    t0 = time.perf_counter()
    out = subprocess.run(cmd, cwd=tree, capture_output=True, text=True)
    ms = (time.perf_counter() - t0) * 1000.0
    try:
        return json.loads(out.stdout), ms
    except Exception:
        return None, ms


def _cite(loc: str) -> dict:
    """`path:L30-L46` -> `{"doc": path, "lines": "L30-L46"}`.

    ⚠ **Split, not duplicated.** The hand-off schema names two fields and Codex
    reads them separately; emitting the whole locator twice would look correct
    in a spot check and give the scorer nothing to join a line range on.
    A locator with no range keeps an empty `lines` rather than inventing one.
    """
    doc, sep, lines = loc.rpartition(":")
    if sep and lines.startswith("L"):
        return {"doc": doc, "lines": lines}
    return {"doc": loc, "lines": ""}


def _gates(asked: dict | None) -> dict | None:
    """`ask --why`'s five funnel integers, or **`None` when nothing measured them**.

    🔴 **Never a dict of zeros.** `reachable: 0` is a claim — *the query reached
    no document* — and an arm that was never asked for its gates would file it
    for every question, which reads as a total retrieval collapse. Absent means
    *not measured on this run*; the per-rung document and phase D both say so in
    those words rather than printing a number nobody computed.
    """
    gates = ((asked or {}).get("derivation") or {}).get("gates")
    if not isinstance(gates, dict):
        return None
    return {field: gates.get(field) for field in GATE_FIELDS}


def one(tree: Path, rung: str, commit: str, row: dict, repo_head: str = "",
        *, fux: str | None = None, band: bool = True, why: bool = True,
        arm: str = "") -> tuple[dict, dict]:
    """`(prediction, handoff)` for one question. Two calls, one question.

    🔴 **`band` is per arm, and hardcoding it would have been silent.**
    `fux-engine 1.0.0`'s `ask` has no `--band`, and argparse exits **2** on an
    unknown flag — so an arm run with it would record an empty result for every
    question and the rows would read as a ranking collapse rather than a flag
    error. On an arm without it, `band` and `answerable` are **null**, never
    `weak`.

    🔴 **`why` is the same flag with the same trap, and it is not hypothetical:
    `fux-engine 1.0.0`'s `ask` has no `--why` either** — measured 2026-09-22
    against the arm venv W-204 phase B actually ran, `~/my_programs/fux-lab/arms/v1`.
    `2.0.1` has it. So a three-engine re-run that hardcoded `--why` would collapse
    the v1 arm to 2 992 empty rows and the funnel it was added for would arrive
    beside a fabricated regression. Pass `--no-why` for v1, and its `gates` are
    **null**, never zeros.
    """
    ask_args = ["ask", row["question"], "--json"]
    if band:
        ask_args.append("--band")
    if why:
        ask_args.append("--why")
    ask_args += ["--top", "10"]
    asked, ask_ms = call(tree, *ask_args, fux=fux)
    answered, ans_ms = call(tree, "answer", row["question"], "--json", fux=fux)

    results = (asked or {}).get("results") or []
    ranked = [r.get("loc") for r in results]
    band_block = (asked or {}).get("confidence") or {}
    band = band_block.get("band")
    answerable = band_block.get("answerable")

    # `answer`'s payload has two shapes (SR-ANSWER): `index` carries
    # {title, phrases}; `refer` carries {passages:[{heading,text,loc,score}]}.
    payload = (answered or {}).get("answer") or {}
    citation = (answered or {}).get("citation") or {}
    passages = payload.get("passages") or []
    if passages:
        answer_text = "\n\n".join(p.get("text", "") for p in passages)
        citations = [_cite(p.get("loc", "")) for p in passages]
    elif payload:
        answer_text = "\n".join(payload.get("phrases") or []) or (payload.get("title") or "")
        citations = [_cite(citation.get("loc", ""))] if citation else []
    else:
        answer_text, citations = "", []

    prediction = {
        "id": row["id"], "ranked": ranked,
        "answerable": answerable, "band": band,
    }
    handoff = {
        **prediction,
        "question": row["question"],
        "answer_text": answer_text,
        "citations": citations,
        # 🔴 SR-WORK-QUALITY decision 1's funnel, the one thing W-204 phase D
        # could not compute. Five integers, `None` as a whole when the arm was
        # not asked — see `_gates`.
        "gates": _gates(asked),
        # ⚠ `freshness` and `source` are ADDITIVE to prompt 5's schema, added
        # 2026-09-20 for W-204 phase A: the per-rung document it specifies has to
        # print a freshness verdict, and deriving the `.md` from anything other
        # than these rows is what lets a readable summary drift from the machine
        # evidence. A scorer reads by key, so a superset costs it nothing.
        "freshness": (citation or {}).get("freshness"),
        "source": (answered or {}).get("source"),
        "rung": rung,
        # Empty for a single-arm run; the arm's name for a version benchmark, so
        # a row can never be read as belonging to the wrong engine.
        "arm": arm,
        # 🔴 The FROZEN engine sha, not the repository's HEAD. A run that files
        # one rung per commit moves HEAD between rungs while the engine does
        # not, and a column that drifted rung to rung would read as eight
        # engines. `repo_head` carries the commit the call actually ran at, so
        # nothing is hidden and the two can be compared.
        "engine_commit": commit,
        "repo_head": repo_head or commit,
        "ask_ms": round(ask_ms, 1),
        "answer_ms": round(ans_ms, 1),
    }
    return prediction, handoff


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rung", required=True)
    ap.add_argument("--dest", type=Path, default=None,
                    help="a run directory; the files land in <dest>/evidence/")
    ap.add_argument("--evidence", type=Path, default=None,
                    help="the evidence directory itself — what a multi-rung run uses, "
                         "so each rung gets evidence/<rung>/ rather than eight runs")
    ap.add_argument("--limit", type=int, default=0, help="0 = every question")
    ap.add_argument("--fux", default=None,
                    help="the engine binary for THIS arm; default is this tree's own module")
    ap.add_argument("--tree", type=Path, default=None,
                    help="the corpus directory; default is the rung under fux-lab/corpora/golden. "
                         "An arm passes its own arm_corpus.py copy.")
    ap.add_argument("--arm", default="",
                    help="a label stamped on every row, so a row cannot be read as another engine's")
    ap.add_argument("--no-band", action="store_true",
                    help="omit --band: fux-engine 1.0.0's ask does not have it")
    ap.add_argument("--no-why", action="store_true",
                    help="omit --why: fux-engine 1.0.0's ask does not have it either, and "
                         "argparse exits 2 on an unknown flag. The row's `gates` are then null")
    ap.add_argument("--sets", required=True,
                    help="comma-separated question SET NAMES, e.g. 2-u or 2-u,3-x. Each is the "
                         "token between `set-` and `.jsonl` in work/golden/questions/, and it is "
                         "written into this run's file names. No default: generation 1 retired, "
                         "and a default would be a guess about which generation is current.")
    ap.add_argument("--engine-commit", default=None,
                    help="the FROZEN engine sha to stamp on every row; defaults to git HEAD. "
                         "Give it when the run spans several commits and the engine does not.")
    args = ap.parse_args(argv)
    if bool(args.dest) == bool(args.evidence):
        ap.error("give exactly one of --dest and --evidence")

    tree = args.tree or (CORPORA / args.rung)
    if not (tree / ".fux" / "index").is_dir():
        print(f"no index at {tree}", file=sys.stderr)
        return 1
    repo_head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True
    ).stdout.strip()
    commit = args.engine_commit or repo_head

    evidence = args.evidence or (args.dest / "evidence")
    evidence.mkdir(parents=True, exist_ok=True)

    wanted = [x.strip() for x in args.sets.split(",") if x.strip()]
    if not wanted:
        ap.error("--sets named no set")
    bad = [n for n in wanted if not SET_NAME.fullmatch(n)]
    if bad:
        # A set name lands in a file path and in a file name. Refusing anything
        # that is not `[A-Za-z0-9-]` keeps both, and keeps a stray `../` out of
        # a run whose whole neighbourhood is a directory no agent may open.
        ap.error(f"--sets: not a set name: {bad}")
    if len(set(wanted)) != len(wanted):
        ap.error(f"--sets names a set twice: {args.sets!r}")
    missing = [n for n in wanted if not (QUESTIONS / f"set-{n}.jsonl").is_file()]
    if missing:
        # 🔴 Refuse rather than skip. A missing set file is the difference between
        # "this rung has no set-3 rows" and "set 3 was never asked", and only one
        # of those is visible in the evidence afterwards.
        print(f"no question file for set(s) {missing} — refusing", file=sys.stderr)
        return 1

    for n in wanted:
        path = QUESTIONS / f"set-{n}.jsonl"
        rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
        if args.limit:
            rows = rows[: args.limit]
        print(f"set-{n}: {len(rows)} questions on {args.rung}", flush=True)

        predictions, handoffs = [], []
        for i, row in enumerate(rows, 1):
            p, h = one(tree, args.rung, commit, row, repo_head,
                       fux=args.fux, band=not args.no_band, why=not args.no_why,
                       arm=args.arm)
            predictions.append(p)
            handoffs.append(h)
            if i % 25 == 0:
                print(f"  {i}/{len(rows)}", flush=True)

        # 🔴 One file per set, never merged.
        (evidence / f"predictions-set-{n}.jsonl").write_text(
            "\n".join(json.dumps(r, sort_keys=True) for r in predictions) + "\n", encoding="utf-8"
        )
        (evidence / f"handoff-set-{n}.jsonl").write_text(
            "\n".join(json.dumps(r, sort_keys=True) for r in handoffs) + "\n", encoding="utf-8"
        )
        # ⚠ **Said at run time, not discovered at scoring time.** W-204 phase D
        # learned the funnel's input was missing four days after the 11 716 rows
        # were filed and a re-run was no longer worth it. A run that captured no
        # gates now says so while the operator is still standing there.
        with_gates = sum(1 for h in handoffs if h.get("gates"))
        print(f"  wrote predictions-set-{n}.jsonl and handoff-set-{n}.jsonl", flush=True)
        if with_gates == len(handoffs):
            print(f"  funnel gates captured on all {with_gates} row(s)\n", flush=True)
        else:
            print(f"  🔴 funnel gates on {with_gates}/{len(handoffs)} row(s) — "
                  "SR-WORK-QUALITY's funnel CANNOT be computed from this set\n", flush=True)

    print("🔴 No score is computed here and none may be. Scoring is prompt 6's, from Codex.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
