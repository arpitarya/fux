"""Retrieval eval harness: hit@1 / hit@5 / MRR over committed Q→passage pairs.

    uv run python tests_e2e/eval/run_eval.py [--lexical-only] [--pairs FILE]
        [--project DIR] [--top N] [--quiet]

By default it builds a throwaway project from `tests_e2e/corpus/`, ingests it,
and scores every pair in `pairs.jsonl` via the real CLI. Point `--project` at a
real corpus (e.g. Anton) and `--pairs` at a private pairs file to eval there —
see README.md. This harness is the quality gate for engine v2 and the recorded
reopen-instrument for the reranker/weights decisions (handoff 0003).
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

EVAL_DIR = Path(__file__).parent
CORPUS = EVAL_DIR.parent / "corpus"


@dataclass
class Metrics:
    hit1: float
    hit5: float
    mrr: float
    n: int
    misses: list[str]

    def row(self, label: str) -> str:
        return f"{label:<14} hit@1 {self.hit1:.3f}   hit@5 {self.hit5:.3f}   MRR {self.mrr:.3f}   (n={self.n})"


def load_pairs(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def build_project(tmp: Path) -> Path:
    proj = tmp / "proj"
    shutil.copytree(CORPUS, proj)
    run_cli(proj, "setup", "-y", "--docs", "docs,notes,office", "--code", "code",
            "--data", "data", "--images", "assets")
    run_cli(proj, "ingest")
    return proj


def run_cli(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    proc = subprocess.run(
        [sys.executable, "-m", "fux", *args], cwd=cwd, capture_output=True, text=True
    )
    if proc.returncode != 0:
        raise SystemExit(f"fux {' '.join(args)} failed: {proc.stderr}")
    return proc


def rank_of(pair: dict, results: list[dict]) -> int | None:
    """1-based rank of the first result matching the expected file (+heading)."""
    for i, result in enumerate(results, start=1):
        if result["path"] != pair["file"]:
            continue
        heading = pair.get("heading")
        if heading:
            haystack = " > ".join(result.get("heading_path", [])) + " " + result.get("text", "")
            if heading.lower() not in haystack.lower():
                continue
        return i
    return None


def evaluate(project: Path, pairs: list[dict], top: int, lexical_only: bool) -> Metrics:
    hits1 = hits5 = 0
    rr_sum = 0.0
    misses: list[str] = []
    for pair in pairs:
        args = ["ask", pair["q"], "--json", "--top", str(top)]
        if lexical_only:
            args.append("--lexical-only")
        payload = json.loads(run_cli(project, *args).stdout)
        rank = rank_of(pair, payload["results"])
        if rank == 1:
            hits1 += 1
        if rank is not None and rank <= 5:
            hits5 += 1
        if rank is not None:
            rr_sum += 1.0 / rank
        else:
            misses.append(pair["q"])
    n = len(pairs)
    return Metrics(hits1 / n, hits5 / n, rr_sum / n, n, misses)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pairs", type=Path, default=EVAL_DIR / "pairs.jsonl")
    parser.add_argument("--project", type=Path, default=None,
                        help="existing ingested project (default: temp build of the fixture corpus)")
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--lexical-only", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    pairs = load_pairs(args.pairs)
    tmp = None
    try:
        if args.project is None:
            tmp = Path(tempfile.mkdtemp(prefix="fux-eval-"))
            project = build_project(tmp)
        else:
            project = args.project
        metrics = evaluate(project, pairs, args.top, args.lexical_only)
    finally:
        if tmp is not None:
            shutil.rmtree(tmp, ignore_errors=True)

    label = "lexical" if args.lexical_only else "default"
    print(metrics.row(label))
    if metrics.misses and not args.quiet:
        for q in metrics.misses:
            print(f"  miss: {q}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
