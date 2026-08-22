"""R5 and R6 — M5's two pre-registered gates, measured.

**The threshold, the arms and the verdict rules live in
[`PRE-REGISTRATION.md`](PRE-REGISTRATION.md), not here.** This file is the
instrument; that file is the contract, and it was committed first. Nothing in
this module may restate a threshold in looser words — the constants below are
copied from it and are not to be edited to make a run pass.

Both predictions are about a *real repository*, not about a function, so this
harness builds throwaway git repositories, wires them with `fux hooks`, and
drives git itself. Nothing is mocked: the hooks that run are the hooks that
ship, and the merge driver is invoked by git's own merge machinery.

## R5 — a 20-document commit re-indexes in < 1 s via the hook

Judged at **100 000 documents** (pre-registration §2), with 1 000 and 10 000
reported alongside as the population curve and never blended into the verdict.
What is timed is the wall-clock of **`git commit` itself** — the hook's process
spawn, the interpreter start, the ingest and the derived build are all inside
the number, because the prediction says *via the hook* and a library-call
timing would measure something no user experiences.

Two arms per size. **`edit`** rewrites twenty existing documents and is the
judged one: it is the steady state a repository is in almost all of the time.
**`add`** creates twenty new ones, changing the corpus id set, and is reported
unjudged because it is the more expensive case and hiding it would flatter the
result.

## R6 — the three-tier merge harness, with a control arm

| tier | what merges | expected |
|---|---|---|
| 1 · machine, disjoint adds | both sides add documents | **no conflict** — the union |
| 2 · machine, one shard, two lines | two documents sharing a shard file | **no conflict** — adjacency is not a disagreement |
| 3 · the same document, both sides | a genuine disagreement | **conflict preserved**, both sides left |

**Every tier runs twice — with the driver registered and without it.** Without
the control, a tier that passes proves nothing: the driver could be doing
nothing at all and git's textual merge could be succeeding by luck. A tier that
merges cleanly in *both* arms is reported as **uninformative** and does not
count toward the pass (pre-registration §3.1).

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
MERGE_DRIVER = "fux-index"  # mirrors maintain.hooks.MERGE_DRIVER_NAME

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


def _commit_and_time(repo: Path, message: str) -> float:
    """Stage, commit, and return the wall-clock of the commit itself.

    The `git add` is deliberately *outside* the timer. Staging is the
    developer's own action and happens whether or not fux is installed; what
    the prediction is about is the cost the hook adds to the moment they press
    enter on `git commit`.
    """
    git(repo, "add", "-A")
    start = time.perf_counter()
    git(repo, "commit", "-qm", message)
    elapsed = time.perf_counter() - start
    # The hook re-indexed after the commit, so the index is now dirty. Commit
    # it separately and untimed: that second commit is not what R5 is about,
    # and folding it in would double-count the same work.
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", f"{message} (index)", check=False)
    return elapsed


def _arm(repo: Path, arm: str, round_no: int) -> None:
    """Make the edit this arm is named for. Twenty documents either way."""
    for i in range(R5_COMMIT_DOCS):
        if arm == "edit":
            (repo / "docs" / f"doc-{i}.md").write_text(_doc(i, round_no + 1), encoding="utf-8")
        else:  # add — changes the corpus id set, which is the expensive case
            (repo / "docs" / f"new-{round_no}-{i}.md").write_text(
                _doc(900_000 + round_no * 1000 + i), encoding="utf-8"
            )


def measure_r5(sizes: list[int], repeats: int) -> list[dict]:
    rows = []
    for size in sizes:
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(Path(tmp) / "repo", size)
            fux(repo, "hooks", "--install")
            _commit_and_time(repo, "wire the hooks")  # discarded warm-up

            for arm in ("edit", "add"):
                samples = []
                for round_no in range(repeats):
                    _arm(repo, arm, round_no)
                    samples.append(_commit_and_time(repo, f"{arm} {round_no}"))
                samples.sort()
                row = {
                    "corpus_docs": size,
                    "arm": arm,
                    "judged": arm == "edit",
                    "commit_docs": R5_COMMIT_DOCS,
                    "runs": repeats,
                    "median_s": round(samples[len(samples) // 2], 4),
                    "max_s": round(samples[-1], 4),
                    "samples_s": [round(x, 4) for x in samples],
                    "passes": samples[-1] <= R5_BUDGET_S,
                }
                rows.append(row)
                print(
                    f"  R5 {size:>7} docs · {arm:<4}: median {row['median_s']}s  "
                    f"max {row['max_s']}s  {'PASS' if row['passes'] else 'FAIL'}"
                    f"{'' if row['judged'] else '  (unjudged)'}"
                )
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


def _make_wired_repo(tmp: str, treatment: bool) -> Path:
    """A repo with the hooks installed, and the merge driver on or off.

    In the **control** arm the driver is unregistered while `.gitattributes`
    still names it. git then falls back to its ordinary text merge — which is
    exactly the world this feature exists to improve on, and the only baseline
    against which "no conflict" means anything.
    """
    repo = make_repo(Path(tmp) / "repo", 100)
    fux(repo, "hooks", "--install")
    if not treatment:
        git(repo, "config", "--local", "--remove-section", f"merge.{MERGE_DRIVER}", check=False)
    # `fux hooks` writes .gitattributes; it must be committed for git to consult
    # it during a merge at all.
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "wire the merge driver", check=False)
    return repo


def _run_tier(build, treatment: bool) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        repo = _make_wired_repo(tmp, treatment)
        conflicted, paths = build(repo, treatment)
        return {
            "conflicted": conflicted,
            "conflicting_paths": paths,
            "machine_plane_conflicts": [p for p in paths if p.startswith(".fux/index")],
        }


def _tier(name: str, description: str, expect_conflict: bool, build) -> dict:
    """One tier, both arms, and the informativeness test between them."""
    treatment = _run_tier(build, treatment=True)
    control = _run_tier(build, treatment=False)

    matches = treatment["conflicted"] == expect_conflict and (
        expect_conflict or not treatment["machine_plane_conflicts"]
    )
    # Informative means: without the driver this merge does NOT come out the way
    # the treatment did. For the two clean tiers that is a control conflict; for
    # tier 3 informativeness is not claimed — a genuine disagreement conflicts
    # in both arms by design, and that is the point rather than a weakness.
    informative = control["machine_plane_conflicts"] != [] if not expect_conflict else None
    return {
        "tier": name,
        "description": description,
        "expected_conflict": expect_conflict,
        "treatment": treatment,
        "control": control,
        "informative": informative,
        "passes": matches and (informative is not False),
        "matches_expectation": matches,
    }


def tier1_disjoint(repo: Path, treatment: bool):
    """Both sides add different documents — the everyday case. **Unjudged.**

    This was the pre-registered tier 1 on 2026-08-20 and it turned out
    uninformative: two documents added on two branches usually hash into two
    different shard files, and git's textual merge handles two different files
    without help. Under
    [`PRE-REGISTRATION-R6-v2.md`](PRE-REGISTRATION-R6-v2.md) §3 the judged tier
    1 is the one-shard variant below, and this stays as a reported arm —
    "most concurrent adds need no driver" is a true finding, and dropping the
    arm that shows it would be deleting a result.
    """
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


def tier2(repo: Path, treatment: bool):
    """One shard, one line changed on each side. The case the driver is for."""
    first, second = _same_shard_pair(repo)
    _branch_edit(repo, "left", {first.removeprefix("file:"): _doc(700, 1)})
    _branch_edit(repo, "right", {second.removeprefix("file:"): _doc(800, 2)})
    git(repo, "checkout", "-q", "left")
    conflicted, paths = _merge(repo, "right")
    if treatment and not conflicted:
        # Both edits must survive: LWW picked the higher ver per line, not per
        # file. A "clean merge" that silently dropped one side would otherwise
        # read as a pass.
        from fux.store.reader import read_index

        index = read_index(repo)
        assert index[first]["ver"] > 1 and index[second]["ver"] > 1, "an edit was lost"
    return conflicted, paths


def tier3(repo: Path, treatment: bool):
    """A genuine disagreement — and both halves of the asymmetry at once.

    Both sides edit the *same* document differently. The human file conflicts,
    exactly as it always did; and the machine plane, facing two records at the
    same `ver` with different bytes, **refuses and leaves both sides** rather
    than silently publishing one.
    """
    _branch_edit(repo, "left", {"docs/doc-0.md": _doc(0, 1)})
    _branch_edit(repo, "right", {"docs/doc-0.md": _doc(0, 2)})
    git(repo, "checkout", "-q", "left")
    conflicted, paths = _merge(repo, "right")
    if treatment:
        for shard in (repo / p for p in paths if p.startswith(".fux/index")):
            text = shard.read_text(encoding="utf-8", errors="replace")
            assert "<<<<<<< ours" in text and ">>>>>>> theirs" in text, "the driver picked a side"
    return conflicted, paths


def tier1(repo: Path, treatment: bool):
    """Disjoint adds into ONE shard — **the judged tier 1 since R6-v2.**

    Two people add documents at the same time, and the pair is pinned into one
    shard file so the scenario actually exercises the driver rather than git's
    ordinary two-different-files merge.

    **This function's body is unchanged from when it was `tier1b`**, the
    post-hoc arm added on 2026-08-20 after the original tier 1 came out
    uninformative. Promoting it rather than rewriting it is deliberate: the
    definition is in git history from before the re-specification, so *what* is
    being measured does not depend on this session's word for it
    ([`PRE-REGISTRATION-R6-v2.md`](PRE-REGISTRATION-R6-v2.md) §0). Its
    post-hoc *result* remains inadmissible; only the specification carries over.

    The pair is found by hashing candidate names at run time, so nothing here
    depends on the corpus generator's ordering.
    """
    from fux.store.format import shard_for

    target = shard_for("file:docs/doc-0.md")
    names = [
        f"docs/extra-{i}.md" for i in range(4000) if shard_for(f"file:docs/extra-{i}.md") == target
    ][:2]
    if len(names) < 2:  # pragma: no cover - 256 shards, 4000 candidates
        raise SystemExit("could not find two names sharing a shard")
    _branch_edit(repo, "left", {names[0]: _doc(500)})
    _branch_edit(repo, "right", {names[1]: _doc(600)})
    git(repo, "checkout", "-q", "left")
    return _merge(repo, "right")


def measure_r6() -> list[dict]:
    tiers = [
        ("1 · machine, disjoint adds, one shard", "both sides add documents sharing a shard", False, tier1, False),
        ("1-disjoint · machine, disjoint adds", "UNJUDGED — the everyday case; needs no driver", False, tier1_disjoint, True),
        ("2 · machine, one shard, two lines", "adjacency is not a disagreement", False, tier2, False),
        ("3 · the same document, both sides", "human conflict preserved; machine plane refuses", True, tier3, False),
    ]
    rows = []
    for name, description, expect, build, post_hoc in tiers:
        row = _tier(name, description, expect, build)
        row["post_hoc"] = post_hoc
        rows.append(row)
        info = {True: "informative", False: "UNINFORMATIVE", None: "n/a"}[row["informative"]]
        # An unjudged arm must never print PASS or FAIL. It contributes to no
        # verdict, and a reader scanning this output for a red word should not
        # find one on a line that decides nothing.
        outcome = "unjudged" if post_hoc else ("PASS" if row["passes"] else "FAIL")
        print(
            f"  R6 tier {name}: treatment conflicted={row['treatment']['conflicted']} · "
            f"control conflicted={row['control']['conflicted']} · {info} · {outcome}"
        )
    return rows


# ----------------------------------------------------------------


#: The judged corpus size, from PRE-REGISTRATION.md §2. Not a default to be
#: overridden into a friendlier number: `--sizes` exists to add rows to the
#: population curve, and the verdict is read from this one.
R5_JUDGED_DOCS = 100_000


def _engine_sha() -> str:
    out = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True
    )
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True)
    return out.stdout.strip() + ("+dirty" if dirty.stdout.strip() else "")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="directory to write report.json into")
    parser.add_argument(
        "--sizes", type=int, nargs="+", default=[1_000, 10_000, R5_JUDGED_DOCS],
        help="the population curve; the verdict is still read from the judged size",
    )
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--only", choices=["r5", "r6"], help="run one prediction")
    args = parser.parse_args(argv)

    report: dict = {
        "fux": FUX,
        "engine_sha": _engine_sha(),
        "python": sys.version.split()[0],
        "platform": f"{os.uname().sysname} {os.uname().release} {os.uname().machine}",
        "r5_budget_s": R5_BUDGET_S,
        "r5_commit_docs": R5_COMMIT_DOCS,
        "r5_judged_docs": R5_JUDGED_DOCS,
        "pre_registration": "tools/maintenance-bench/PRE-REGISTRATION.md",
    }

    if args.only != "r6":
        print("R5 — a 20-doc commit, re-indexed by the post-commit hook")
        report["r5"] = measure_r5(args.sizes, args.repeats)
        judged = [r for r in report["r5"] if r["judged"] and r["corpus_docs"] == R5_JUDGED_DOCS]
        if judged:
            report["r5_verdict"] = "PASS" if judged[0]["passes"] else "FAIL"
        else:
            # Refusing to rule is the correct behaviour, not a gap: the judged
            # size is pre-registered, and a verdict read off a different one
            # would be the threshold moving under another name.
            report["r5_verdict"] = "NOT RULED — the judged size was not run"
        print(f"  R5 verdict: {report['r5_verdict']}")

    if args.only != "r5":
        print("R6 — the three-tier merge harness, with a control arm")
        report["r6"] = measure_r6()
        judged = [r for r in report["r6"] if not r.get("post_hoc")]
        matches = all(r["matches_expectation"] for r in judged)
        clean_tiers = [r for r in judged if r["informative"] is not None]
        all_informative = all(r["informative"] for r in clean_tiers)
        none_informative = not any(r["informative"] for r in clean_tiers)
        # PRE-REGISTRATION-R6-v2.md §3.2, applied literally — four rows, and
        # every possible result now lands on exactly one of them. `PARTIAL` is
        # the row the 2026-08-20 frozen table lacked, which is what made that
        # run's outcome a reading rather than a verdict; it resolves nothing on
        # purpose and routes to Arpit, per CLAUDE.md.
        if not matches:
            report["r6_verdict"] = "FAIL"
        elif all_informative:
            report["r6_verdict"] = "PASS"
        elif none_informative:
            report["r6_verdict"] = "INCONCLUSIVE"
        else:
            report["r6_verdict"] = "PARTIAL — all tiers match; exactly one of tiers 1/2 is informative (Arpit's call)"
        report["r6_pre_registration"] = "tools/maintenance-bench/PRE-REGISTRATION-R6-v2.md"
        print(f"  R6 verdict: {report['r6_verdict']}")

    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {args.out / 'report.json'}")
    else:
        print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
