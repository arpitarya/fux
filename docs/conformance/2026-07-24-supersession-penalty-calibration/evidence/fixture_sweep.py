#!/usr/bin/env python3
"""Fixture-gate arm of the penalty sweep (phase 7, M3).

Reuses the e2e suite's own evaluator against the committed fixture corpus, so
these numbers are directly comparable to the shipped v2 ship gate rather than a
parallel reimplementation of it.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve()
REPO = Path("/Users/arpitarya/my_programs/fux")
sys.path.insert(0, str(REPO / "tests_e2e" / "eval"))
sys.path.insert(0, str(REPO / "tests_e2e"))

from run_eval import EVAL_DIR, evaluate, load_pairs  # noqa: E402

FUX = str(REPO / ".venv" / "bin" / "fux")


def run_fux(project: Path, *args: str) -> None:
    subprocess.run([FUX, *args], cwd=project, capture_output=True, text=True, check=True)


def set_penalty(toml_path: Path, value: int) -> None:
    text = toml_path.read_text(encoding="utf-8")
    if "supersession_penalty" in text:
        text = re.sub(r"supersession_penalty\s*=\s*\d+", f"supersession_penalty = {value}", text)
    elif "[engine.hybrid]" in text:
        text = text.replace("[engine.hybrid]", f"[engine.hybrid]\nsupersession_penalty = {value}", 1)
    else:
        text = text.rstrip("\n") + f"\n\n[engine.hybrid]\nsupersession_penalty = {value}\n"
    toml_path.write_text(text, encoding="utf-8")


def main() -> int:
    values = [int(v) for v in sys.argv[1].split(",")]
    out = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else None

    tmp = Path(tempfile.mkdtemp())
    proj = tmp / "proj"
    shutil.copytree(REPO / "tests_e2e" / "corpus", proj)
    run_fux(proj, "setup", "-y", "--docs", "docs,notes,office",
            "--code", "code", "--data", "data", "--images", "assets")
    run_fux(proj, "ingest")

    pairs = load_pairs(EVAL_DIR / "pairs.jsonl")
    results = {}
    for v in values:
        set_penalty(proj / "fux.toml", v)
        hybrid = evaluate(proj, pairs, top=10, lexical_only=False)
        lexical = evaluate(proj, pairs, top=10, lexical_only=True)
        results[str(v)] = {
            "hybrid": {"hit@1": round(hybrid.hit1, 3), "hit@5": round(hybrid.hit5, 3),
                       "MRR": round(hybrid.mrr, 3), "n": hybrid.n, "misses": hybrid.misses},
            "lexical": {"hit@1": round(lexical.hit1, 3), "hit@5": round(lexical.hit5, 3),
                        "MRR": round(lexical.mrr, 3), "n": lexical.n},
        }
        h = results[str(v)]["hybrid"]
        print(f"  penalty={v}: hybrid hit@1 {h['hit@1']} · hit@5 {h['hit@5']} · MRR {h['MRR']}"
              f"  |  lexical hit@5 {results[str(v)]['lexical']['hit@5']}", flush=True)

    if out:
        out.write_text(json.dumps({"env": "fixture", "results": results}, indent=2) + "\n")
        print(f"wrote {out}")
    shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
