#!/usr/bin/env python3
"""lexical-top-5-lost on the committed fixture gate (phase 9 M2).

Uses the e2e suite's own evaluator plumbing so the numbers are comparable to the
shipped v2 ship gate rather than a parallel reimplementation.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path("/Users/arpitarya/my_programs/fux")
sys.path.insert(0, str(REPO / "tests_e2e" / "eval"))
from run_eval import EVAL_DIR, load_pairs, rank_of  # noqa: E402

FUX = str(REPO / ".venv" / "bin" / "fux")
TOP = 5


def run_fux(project: Path, *args: str):
    return subprocess.run([FUX, *args], cwd=project, capture_output=True, text=True, check=True)


def ranks(project: Path, pair: dict, lexical: bool) -> int | None:
    args = ["ask", pair["q"], "--json", "--top", str(TOP)]
    if lexical:
        args.append("--lexical-only")
    payload = json.loads(run_fux(project, *args).stdout)
    return rank_of(pair, payload["results"])


def main() -> int:
    tmp = Path(tempfile.mkdtemp())
    proj = tmp / "proj"
    shutil.copytree(REPO / "tests_e2e" / "corpus", proj)
    run_fux(proj, "setup", "-y", "--docs", "docs,notes,office",
            "--code", "code", "--data", "data", "--images", "assets")
    run_fux(proj, "ingest")

    pairs = load_pairs(EVAL_DIR / "pairs.jsonl")
    lost, gained, both, neither = [], [], 0, 0
    for p in pairs:
        lex, hyb = ranks(proj, p, True), ranks(proj, p, False)
        row = {"q": p["q"], "lexical_rank": lex, "hybrid_rank": hyb}
        if lex is not None and hyb is None:
            lost.append(row)
        elif lex is None and hyb is not None:
            gained.append(row)
        elif lex is not None:
            both += 1
        else:
            neither += 1

    res = {"env": "fixture", "n_scorable": len(pairs), "penalty": "default",
           "lexical_top5_lost": len(lost), "lost_detail": lost,
           "hybrid_gained": len(gained), "gained_detail": gained,
           "both_found": both, "neither_found": neither}
    print(f"[fixture] n={len(pairs)}  LOST={len(lost)}  gained={len(gained)}  "
          f"both={both}  neither={neither}  net={len(gained)-len(lost):+d}")
    for r in lost:
        print(f"    LOST  lex={r['lexical_rank']} → hybrid out   {r['q'][:56]}")
    if "--out" in sys.argv:
        Path(sys.argv[sys.argv.index("--out") + 1]).write_text(json.dumps(res, indent=2) + "\n")
    shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
