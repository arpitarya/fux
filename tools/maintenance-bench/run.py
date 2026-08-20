"""R5 and R6 — the maintenance plane's two pre-registered gates, measured.

Both predictions are about a *real repository*, not about a function, so this
harness builds throwaway git repositories, wires them with `fux hooks`, and
drives git itself. Nothing is mocked: the hooks that run are the hooks that
ship, and the merge driver is invoked by git's own merge machinery.

## R5 — a 20-doc commit re-indexes in < 1 s via the hook

Reported **per corpus size**, never as a single number. M1's lesson, paid for:
an aggregate that hides which population a treatment reached is not evidence.
A 20-doc commit costs whatever a re-ingest of the whole corpus costs, so the
prediction is really a statement about the corpus sizes at which the hook is
usable, and that is what the table says.

## R6 — the three-tier merge harness

| tier | what merges | expected |
|---|---|---|
| 1 · machine, disjoint | both sides add documents | **no conflict** — the union |
| 2 · machine, one shard, two lines | two documents that share a shard file | **no conflict** — adjacency is not a disagreement |
| 3 · the same document, both sides | a genuine disagreement | **conflict preserved** — the prose conflicts, and the shard is left with both sides |

Tier 3 carries the asymmetry that is the whole design: the machine plane
refuses rather than picking, and human-authored files conflict exactly as they
always did. A harness that only proved "no conflicts" would be proving the
merge driver is dangerous.

Usage:
    python tools/maintenance-bench/run.py --out work/regression/<date>-<run>
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

#: The pre-registered bars. Do not edit these to make a run pass.
R5_BUDGET_S = 1.0
R5_COMMIT_DOCS = 20

#: **The repo's own venv first.** `shutil.which` on this machine finds a pyenv
#: shim belonging to a different project, and measuring a different build than
#: the one under test is the silent way to file a wrong number.
_LOCAL = ROOT / ".venv" / "bin" / "fux"
FUX = str(_LOCAL) if _LOCAL.exists() else (shutil.which("fux") or str(_LOCAL))

_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "bench",
    "GIT_AUTHOR_EMAIL": "bench@fux",
    "GIT_COMMITTER_NAME": "bench",
    "GIT_COMMITTER_EMAIL": "bench@fux",
    # L3: no wall clock on the maintenance path, in the fixtures either.
    "GIT_AUTHOR_DATE": "2026-01-01T00:00:00Z",
    "GIT_COMMITTER_DATE": "2026-01-01T00:00:00Z",
    "SOURCE_DATE_EPOCH": "1767225600",
    "PATH": str(Path(FUX).parent) + os.pathsep + os.environ.get("PATH", ""),
}


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, env=_ENV, check=check
    )


def fux(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [FUX, *args], cwd=repo, capture_output=True, text=True, env=_ENV, check=False
    )


def _doc(i: int, revision: int = 0) -> str:
    """A document with enough distinct vocabulary to make ingest do real work."""
    body = " ".join(f"term{i}{j}{revision}" for j in range(40))
    return (
        f"---\ntitle: Document {i}\ntype: runbook\n---\n\n"
        f"# Document {i}\n\nRevision {revision}. {body}\n\n"
        f"See [document {(i + 1) % 97}](doc-{(i + 1) % 97}.md).\n"
    )


def make_repo(directory: Path, docs: int) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    git(directory, "init", "-q")
    (directory / "docs").mkdir(exist_ok=True)
    for i in range(docs):
        (directory / "docs" / f"doc-{i}.md").write_text(_doc(i), encoding="utf-8")
    fux(directory, "setup")
    git(directory, "add", "-A")
    git(directory, "commit", "-qm", "corpus")
    fux(directory, "ingest")
    git(directory, "add", "-A")
    git(directory, "commit", "-qm", "index")
    return directory


# ---------------------------------------------------------------- R5


def measure_r5(sizes: list[int], repeats: int) -> list[dict]:
    rows = []
    for size in sizes:
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(Path(tmp) / "repo", size)
            fux(repo, "hooks", "--install")
            samples = []
            for run in range(repeats):
                for i in range(R5_COMMIT_DOCS):
                    (repo / "docs" / f"doc-{i}.md").write_text(_doc(i, run + 1), encoding="utf-8")
                git(repo, "add", "-A")
                start = time.perf_counter()
                # What the post-commit hook runs, run the way the hook runs it.
                git(repo, "commit", "-qm", f"edit {run}")
                samples.append(time.perf_counter() - start)
                git(repo, "add", "-A")
                git(repo, "commit", "-qm", f"index {run}", check=False)
            samples.sort()
            rows.append(
                {
                    "corpus_docs": size,
                    "commit_docs": R5_COMMIT_DOCS,
                    "runs": repeats,
                    "median_s": round(samples[len(samples) // 2], 4),
                    "max_s": round(samples[-1], 4),
                    "passes": samples[-1] < R5_BUDGET_S,
                }
            )
            print(f"  R5 {size:>6} docs: median {rows[-1]['median_s']}s  max {rows[-1]['max_s']}s")
    return rows


# ---------------------------------------------------------------- R6


def _branch_edit(repo: Path, branch: str, edits: dict[str, str]) -> None:
    git(repo, "checkout", "-q", "-b", branch)
    for name, text in edits.items():
        (repo / name).write_text(text, encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", f"{branch} content")
    fux(repo, "ingest")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", f"{branch} index", check=False)
    git(repo, "checkout", "-q", "-")


def _merge(repo: Path, branch: str) -> tuple[bool, list[str]]:
    """Merge and report `(conflicted, conflicting_paths)`."""
    result = git(repo, "merge", "--no-edit", branch, check=False)
    conflicted = result.returncode != 0
    paths = git(repo, "diff", "--name-only", "--diff-filter=U", check=False).stdout.split()
    return conflicted, sorted(paths)


def _tier(name: str, description: str, expect_conflict: bool, build) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp) / "repo", 100)
        fux(repo, "hooks", "--install")
        # `fux hooks` writes .gitattributes; it must be committed for git to
        # honour the driver during a merge.
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "wire the merge driver", check=False)
        conflicted, paths = build(repo)
        index_paths = [p for p in paths if p.startswith(".fux/index")]
        return {
            "tier": name,
            "description": description,
            "expected_conflict": expect_conflict,
            "conflicted": conflicted,
            "conflicting_paths": paths,
            "machine_plane_conflicts": index_paths,
            "passes": conflicted == expect_conflict and (expect_conflict or not index_paths),
        }


def tier1(repo: Path):
    """Both sides add different documents — the everyday case."""
    _branch_edit(repo, "left", {"docs/left.md": _doc(500)})
    _branch_edit(repo, "right", {"docs/right.md": _doc(600)})
    git(repo, "checkout", "-q", "left")
    return _merge(repo, "right")


def _same_shard_pair(repo: Path) -> tuple[str, str]:
    """Two document paths whose index lines land in the SAME shard file.

    Without this the harness is not testing anything: two ids in two different
    shards touch two different files, and a textual merge would have coped.
    The driver earns its place only when both sides edit one shard.
    """
    from fux.store.format import shard_for
    from fux.store.reader import read_index

    by_shard: dict[str, list[str]] = {}
    for doc_id in read_index(repo):
        by_shard.setdefault(shard_for(doc_id), []).append(doc_id)
    for ids in by_shard.values():
        if len(ids) >= 2:
            return tuple(sorted(ids)[:2])  # type: ignore[return-value]
    raise SystemExit("no two documents share a shard — raise the corpus size")


def tier2(repo: Path):
    """One shard, one line changed on each side. The case the driver is for.

    Two people edit two different documents that happen to hash into the same
    shard. The file changes on both sides; the *lines* do not overlap. A
    textual three-way merge sees neighbouring lines and can conflict on
    adjacency alone — this asserts the driver does not.
    """
    first, second = _same_shard_pair(repo)
    left = first.removeprefix("file:")
    right = second.removeprefix("file:")
    _branch_edit(repo, "left", {left: _doc(700, 1)})
    _branch_edit(repo, "right", {right: _doc(800, 2)})
    git(repo, "checkout", "-q", "left")
    conflicted, paths = _merge(repo, "right")
    if not conflicted:
        # Both edits must survive: LWW picked the higher ver per line, not per file.
        from fux.store.reader import read_index

        index = read_index(repo)
        assert index[first]["ver"] > 1 and index[second]["ver"] > 1, "an edit was lost"
    return conflicted, paths


def tier3(repo: Path):
    """A genuine disagreement — and both halves of the asymmetry at once.

    Both sides edit the *same* document differently. The human file conflicts,
    exactly as it always did; and the machine plane, facing two records at the
    same `ver` with different bytes, **refuses and leaves both sides** rather
    than silently publishing one. A harness that only proved "no conflicts"
    would be proving the merge driver is dangerous.
    """
    _branch_edit(repo, "left", {"docs/doc-0.md": _doc(0, 1)})
    _branch_edit(repo, "right", {"docs/doc-0.md": _doc(0, 2)})
    git(repo, "checkout", "-q", "left")
    conflicted, paths = _merge(repo, "right")
    shards = [repo / p for p in paths if p.startswith(".fux/index")]
    for shard in shards:
        text = shard.read_text(encoding="utf-8", errors="replace")
        assert "<<<<<<< ours" in text and ">>>>>>> theirs" in text, "the driver picked a side"
    return conflicted, paths


def measure_r6() -> list[dict]:
    tiers = [
        ("1 · machine, disjoint adds", "both sides add documents", False, tier1),
        ("2 · machine, one shard, two lines", "adjacency is not a disagreement", False, tier2),
        ("3 · the same document, both sides", "human conflict preserved; machine plane refuses", True, tier3),
    ]
    rows = []
    for name, description, expect, build in tiers:
        row = _tier(name, description, expect, build)
        rows.append(row)
        print(f"  R6 tier {name}: conflicted={row['conflicted']} passes={row['passes']}")
    return rows


# ----------------------------------------------------------------


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="directory to write report.json into")
    parser.add_argument("--sizes", type=int, nargs="+", default=[100, 1000, 5000])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--only", choices=["r5", "r6"], help="run one prediction")
    args = parser.parse_args(argv)

    report: dict = {"fux": FUX, "r5_budget_s": R5_BUDGET_S, "r5_commit_docs": R5_COMMIT_DOCS}

    if args.only != "r6":
        print("R5 — a 20-doc commit, re-indexed by the post-commit hook")
        report["r5"] = measure_r5(args.sizes, args.repeats)
        report["r5_passes"] = all(r["passes"] for r in report["r5"])

    if args.only != "r5":
        print("R6 — the three-tier merge harness")
        report["r6"] = measure_r6()
        report["r6_passes"] = all(r["passes"] for r in report["r6"])

    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {args.out / 'report.json'}")
    else:
        print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
