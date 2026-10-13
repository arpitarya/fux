#!/usr/bin/env python3
"""G3 — a sectionless document scores at every λ exactly what it scores at 0.0. Read-only.

W-269's `g3.py` (sha256 `12e19e39…e641c070`) with **the treatment arms changed
and nothing else in the gate**: W-270 decides `sw-2.0` and reports `sw-4.0`.
Frozen by hash in `PRE-REGISTRATION.md` §Freeze before the generation-5 ladder
exists and before any arm. With W-273's option (b) the `.csv`, `.json` and
`.jsonl` documents are sectionless too, so this gate covers them; the
generation-5 ladder holds none, so it covers them by construction there.

    python3 g3.py --fux <pinned build fux> --arms <dir holding sw-<λ>/rung-01000> \\
        --questions work/golden/questions/set-6-claude.jsonl > evidence/g3/g3.json

It reads `id` and `question` from the released question file and nothing else
under `work/golden/` (SR-WORK-GOLDEN decision 2). It opens no key and runs no
scorer. It writes JSON to stdout and nothing to disk. The three conditions it
checks, and why it compares `rank()`'s term rather than the final `score`, are
W-269's, unchanged.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

BASELINE = "sw-0.0"
TREATMENTS = ("sw-2.0", "sw-4.0")
RUNG = "rung-01000"
TOP = "1000"
ZERO = {"id": None, "contribution": 0.0}


def sectionless(tree: Path) -> set[str]:
    """The ids of every document whose committed record carries no `nsec`."""
    out = set()
    for path in sorted((tree / ".fux" / "index").glob("??.jsonl")):
        for line in path.read_bytes().split(b"\n")[1:]:
            if line:
                record = json.loads(line)
                if "nsec" not in record:
                    out.add(record["id"])
    return out


def derivation(fux: str, tree: Path, question: str) -> dict[str, dict]:
    out = subprocess.run(
        [fux, "ask", question, "--json", "--why", "--top", TOP],
        cwd=tree, capture_output=True, text=True, check=True,
    )
    return {d["id"]: d for d in json.loads(out.stdout)["derivation"]["documents"]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--fux", required=True)
    ap.add_argument("--arms", type=Path, required=True)
    ap.add_argument("--questions", type=Path, required=True)
    args = ap.parse_args()

    rows = [json.loads(l) for l in args.questions.read_text(encoding="utf-8").splitlines() if l.strip()]
    questions = [(r["id"], r["question"]) for r in rows]
    trees = {arm: args.arms / arm / RUNG for arm in (BASELINE, *TREATMENTS)}
    bare = {arm: sectionless(tree) for arm, tree in trees.items()}
    if len({frozenset(s) for s in bare.values()}) != 1:
        raise SystemExit("refusing: the arms disagree on which documents are sectionless — not one index")
    bare_ids = bare[BASELINE]

    report = {
        "gate": "G3 - every sectionless document's term at every lambda equals lambda = 0",
        "questions": len(questions),
        "sectionless_documents": len(bare_ids),
        "arms": {},
    }
    base = {qid: derivation(args.fux, trees[BASELINE], q) for qid, q in questions}
    for arm in TREATMENTS:
        compared, failures = 0, []
        for qid, q in questions:
            got = derivation(args.fux, trees[arm], q)
            want = base[qid]
            for doc in sorted(bare_ids & (set(got) | set(want))):
                compared += 1
                if doc not in got or doc not in want:
                    failures.append({"id": qid, "doc": doc, "why": "in one arm's derivation only"})
                elif got[doc].get("section") != ZERO:
                    failures.append({"id": qid, "doc": doc, "why": "section is not {id: null, contribution: 0.0}"})
                elif json.dumps(got[doc]["matched"], sort_keys=True) != json.dumps(want[doc]["matched"], sort_keys=True):
                    failures.append({"id": qid, "doc": doc, "why": "matched contributions differ from sw-0.0"})
        report["arms"][arm] = {"compared": compared, "failures": len(failures), "first_failures": failures[:20]}
    report["verdict"] = "PASS" if all(a["failures"] == 0 and a["compared"] > 0 for a in report["arms"].values()) else "FAIL"
    print(json.dumps(report, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
