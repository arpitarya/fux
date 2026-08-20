"""Where a hook-driven commit spends its time — the follow-up R5's FAIL demands.

R5 failed at the judged size: a 20-document commit costs **44 s** at 100 000
documents against a 1 s bound. "It is slow" is not a finding anyone can act on,
and this repo's own M1 lesson is that a result without an attribution is an
anecdote. So this splits the same commit into its parts, at the same sizes.

| part | what it is | O(?) |
|---|---|---|
| `git` | the commit with **no hook installed** — git's own staging and tree write | corpus |
| `ingest` | `fux ingest`, delta: parse + edges + write, extraction carried forward | corpus |
| `derive` | `fux build`, the T1 accelerator + graph plane, rebuilt from the committed index | corpus |
| `spawn` | `fux --version` — process start and interpreter import, paid once per hook | constant |

The point of the split is that **the three costs have different fixes**, and
without knowing the mix you cannot tell which fix is worth having. It is run
after the verdict, never before it, and it changes no threshold.

Usage:
    python tools/maintenance-bench/attribute.py --sizes 1000 10000 100000
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from run import _ENV, FUX, R5_COMMIT_DOCS, _doc, fux, git, make_repo  # noqa: E402


def _time(fn) -> float:
    start = time.perf_counter()
    fn()
    return time.perf_counter() - start


def attribute(size: int, repeats: int) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp) / "repo", size)
        # No `fux hooks --install` here on purpose: each part is timed on its
        # own, so the hook would double-count the ingest and the derive.
        parts: dict[str, list[float]] = {"git": [], "ingest": [], "derive": [], "spawn": []}
        for round_no in range(repeats):
            for i in range(R5_COMMIT_DOCS):
                (repo / "docs" / f"doc-{i}.md").write_text(_doc(i, round_no + 1), encoding="utf-8")
            git(repo, "add", "-A")
            parts["git"].append(_time(lambda: git(repo, "commit", "-qm", f"edit {round_no}")))
            parts["ingest"].append(_time(lambda: fux(repo, "ingest", "--no-accelerator")))
            parts["derive"].append(_time(lambda: fux(repo, "build")))
            parts["spawn"].append(_time(lambda: fux(repo, "--version")))
            git(repo, "add", "-A")
            git(repo, "commit", "-qm", f"edit {round_no} (index)", check=False)

        row = {"corpus_docs": size, "repeats": repeats}
        for name, samples in parts.items():
            samples.sort()
            row[f"{name}_median_s"] = round(samples[len(samples) // 2], 4)
        row["sum_median_s"] = round(sum(row[f"{n}_median_s"] for n in parts), 4)
        return row


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--sizes", type=int, nargs="+", default=[1_000, 10_000, 100_000])
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args(argv)

    rows = []
    for size in args.sizes:
        row = attribute(size, args.repeats)
        rows.append(row)
        print(
            f"  {size:>7} docs: git {row['git_median_s']:>7.3f}s  "
            f"ingest {row['ingest_median_s']:>7.3f}s  derive {row['derive_median_s']:>7.3f}s  "
            f"spawn {row['spawn_median_s']:>6.3f}s  = {row['sum_median_s']:>7.3f}s"
        )

    payload = {"parts": rows, "commit_docs": R5_COMMIT_DOCS, "fux": FUX}
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "attribution.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {args.out / 'attribution.json'}")
    else:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
