#!/usr/bin/env python3
"""W-136 phase 5 — run both question sets on one rung and write the hand-off.

🔴 **It records what fux DID. It never says whether fux was right.**
There is no answer key anywhere and none reaches a Claude session by any route
([L11](../../records/0012_LAW-11-sealed-answer-key.md)); *correct* first appears
in prompt 6's output, from Codex, against a key Arpit pastes there. **A report
that guessed would train the next reader to trust a guess.**

Two `fux` calls per question — `ask --json --band --top 10` and `answer --json` —
and two files per set, **never merged**: the gap between a Codex-authored set 1
and a Claude-authored set 2 is the measurement, and a mean across both erases it.

⚠ **Reads `id` and `question` from `work/golden/questions/` and nothing else**,
which is what SR-WORK-GOLDEN decision 2 permits. It opens no other path under
`work/golden/` except the rung's own manifest.

    python3 tools/quality-controls/golden_run.py --rung rung-00100 \
        --dest work/regression/<date>-golden-rung-00100
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUESTIONS = ROOT / "work" / "golden" / "questions"
CORPORA = Path.home() / "my_programs" / "fux-lab" / "corpora" / "golden"


def call(tree: Path, *args: str) -> tuple[dict | None, float]:
    t0 = time.perf_counter()
    out = subprocess.run(
        [sys.executable, "-m", "fux.cli", *args], cwd=tree, capture_output=True, text=True
    )
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


def one(tree: Path, rung: str, commit: str, row: dict) -> tuple[dict, dict]:
    """`(prediction, handoff)` for one question. Two calls, one question."""
    asked, ask_ms = call(tree, "ask", row["question"], "--json", "--band", "--top", "10")
    answered, ans_ms = call(tree, "answer", row["question"], "--json")

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
        "rung": rung,
        "engine_commit": commit,
        "ask_ms": round(ask_ms, 1),
        "answer_ms": round(ans_ms, 1),
    }
    return prediction, handoff


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rung", required=True)
    ap.add_argument("--dest", type=Path, required=True)
    ap.add_argument("--limit", type=int, default=0, help="0 = every question")
    args = ap.parse_args(argv)

    tree = CORPORA / args.rung
    if not (tree / ".fux" / "index").is_dir():
        print(f"no index at {tree}", file=sys.stderr)
        return 1
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True
    ).stdout.strip()

    evidence = args.dest / "evidence"
    evidence.mkdir(parents=True, exist_ok=True)

    for n in (1, 2):
        path = QUESTIONS / f"set-{n}.jsonl"
        rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
        if args.limit:
            rows = rows[: args.limit]
        print(f"set-{n}: {len(rows)} questions on {args.rung}", flush=True)

        predictions, handoffs = [], []
        for i, row in enumerate(rows, 1):
            p, h = one(tree, args.rung, commit, row)
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
        print(f"  wrote predictions-set-{n}.jsonl and handoff-set-{n}.jsonl\n", flush=True)

    print("🔴 No score is computed here and none may be. Scoring is prompt 6's, from Codex.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
