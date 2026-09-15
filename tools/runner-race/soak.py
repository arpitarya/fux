"""W-182 — make the runner race happen on purpose.

**The flake.** `tests_e2e/test_maintenance.py::
test_two_commits_in_quick_succession_produce_one_runner_and_one_index` failed
once, on 2026-09-12, in a combined `tests tests_e2e` run. It has been green in
**11 subsequent attempts**, three of them the exact shape it failed in — two of
those while a 10 000-document corpus was being generated on the same machine, so
the load that might explain it was arguably present and it still did not fire.

⚠ **"Wait for it to happen again" is not a plan, and 11 attempts is the
evidence.** What was missing is not luck. It is a harness that puts the second
commit at a CHOSEN point in the first runner's lifetime instead of wherever the
scheduler happens to put it.

## The window this walks across

`run_once` ends `finally: release(root); _hand_off_if_leftovers_are_new(...)`.
A commit landing while the lock is held has its own `spawn` refused — correctly,
one writer — so the only thing that can pick its work up is that handoff, and
the handoff spawns **only for ids this runner never looked at**
(`remaining - seen`). Two consequences, and this harness exists to tell them
apart:

1. **A genuinely new id arriving in the tail** should hand off. If it does not,
   the repository is silently stale: `pending: 1`, `running: false`, and no
   process that will ever pick it up.
2. **An id already in `seen`** justifies no handoff by design — the runner did
   look at it. If the file CHANGED after that look, the identity bound says the
   work is done and the bytes say it is not.

## What this is NOT

⚠ **The first reproduction is a CAPTURE, not a fix** (W-140 row 21's own
instruction, and W-182 definition-of-done 2). This script changes nothing under
`src/`, injects nothing into the engine, and asserts nothing about what the
right behaviour would be. It commits, it watches, and it writes down what it
saw.

**An unreproducible result is a result.** A full sweep that never strands is
evidence that the observed failure was not this window, and it closes W-140
row 21 as honestly as a reproduction would.

Usage::

    python tools/runner-race/soak.py --trials 20
    python tools/runner-race/soak.py --trials 40 --docs 400 --json-out out.json
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
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


def git(
    cwd: Path, *args: str, env: dict | None = None, check: bool = True
) -> subprocess.CompletedProcess:
    proc = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", env=env
    )
    if check and proc.returncode != 0:
        raise AssertionError(
            f"git {' '.join(args)} exited {proc.returncode} in {cwd}\n"
            f"stdout: {proc.stdout.strip()}\nstderr: {proc.stderr.strip()}"
        )
    return proc


def fux(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "fux.cli", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def hook_env() -> dict:
    """The hook must be able to find `fux`, or every trial is vacuously green.

    Same guard `tests_e2e` puts on its hook-driven tests: `post-commit`'s first
    line is `command -v fux >/dev/null 2>&1 || exit 0`.
    """
    return dict(os.environ, PATH=f"{Path(sys.executable).parent}{os.pathsep}{os.environ['PATH']}")


def doc(text: str) -> str:
    return f"---\ntitle: {text}\n---\n# {text}\n\n{text} body\n"


def make_repo(path: Path, *, docs: int) -> None:
    """A hooked repo with `docs` filler documents — the ingest has to take time.

    ⚠ **Corpus size is the only knob that lengthens the window.** With two
    documents a background re-index finishes before the next `git commit` has
    parsed its own arguments, and every trial lands outside the run rather than
    inside it.
    """
    (path / ".fux" / "sources").mkdir(parents=True)
    (path / "docs").mkdir()
    (path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    (path / ".fux" / "sources" / "dirs").write_text("docs\n", encoding="utf-8")
    (path / ".fux" / "pii.toml").write_text("", encoding="utf-8")
    for i in range(docs):
        (path / "docs" / f"filler{i:04d}.md").write_text(
            doc(f"filler {i} " + " ".join(f"w{i}x{j}" for j in range(40))), encoding="utf-8"
        )
    git(path, "init", "-q")
    git(path, "config", "user.email", "t@t.test")
    git(path, "config", "user.name", "T")
    git(path, "config", "commit.gpgsign", "false")
    fux(path, "ingest")
    fux(path, "hooks")
    git(path, "add", "-A")
    subprocess.run(
        ["git", "commit", "-qm", "init"], cwd=path, capture_output=True, text=True,
        encoding="utf-8", env=hook_env(),
    )
    fux(path, "daemon", "stop")


def runner_state(path: Path) -> dict | None:
    """`fux doctor --json`'s runner block — the SHIPPED view, for the verdict."""
    proc = fux(path, "doctor", "--json")
    try:
        return json.loads(proc.stdout)["runner"]
    except (ValueError, KeyError):
        return None


def live(path: Path) -> bool:
    """Is a runner holding the write lock, read IN PROCESS.

    ⚠ **`fux doctor --json` cannot see this window and that is arithmetic, not
    an opinion.** Each call starts an interpreter and costs 250–400 ms here,
    and a background re-index over a few hundred small documents finishes in
    under a second — so a poll loop built on the CLI samples the run two or
    three times and lands the second commit wherever it lands. Reading the lock
    file directly costs microseconds, which is the resolution the tail of a run
    needs.
    """
    from fux.maintain.runner import holder

    try:
        return holder(path) is not None
    except Exception:  # noqa: BLE001 - a torn read is "cannot tell", not a crash
        return False


def pending_ids(path: Path) -> set[str]:
    from fux.maintain import dirty

    try:
        return set(dirty.read(path))
    except Exception:  # noqa: BLE001
        return set()


def calibrate(docs: int) -> float:
    """How long ONE background re-index takes on this machine, in seconds.

    A fixed grid of delays measures the machine rather than the window: the
    same 0.5 s is the middle of a run on a loaded laptop and long past the end
    of one on an idle desktop.
    """
    tmp = Path(tempfile.mkdtemp(prefix="fux-race-cal-"))
    try:
        repo = tmp / "repo"
        repo.mkdir()
        make_repo(repo, docs=docs)
        started = commit(repo, "cal", "calterm")
        # Wait for the lock to appear, then for it to go.
        appeared = None
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            if live(repo):
                appeared = time.monotonic()
                break
            time.sleep(0.005)
        if appeared is None:
            return 1.0
        while time.monotonic() < deadline and live(repo):
            time.sleep(0.005)
        return max(time.monotonic() - started, 0.05)
    finally:
        fux(tmp / "repo", "daemon", "stop")
        shutil.rmtree(tmp, ignore_errors=True)


class StagingLost(AssertionError):
    """`git add -A` raced a live runner and lost. **A CAPTURE, not a crash.**

    ⚠ **This is the outcome the soak exists to produce**, so it is a value the
    trial records rather than an exception that ends the sweep. `_atomic_write`
    writes `.fux/index/<shard>.jsonl.tmp` beside the shard and renames it; the
    directory is COMMITTED and the temp file is neither tracked nor ignored, so
    a concurrent `git add -A` can list it and then fail to stat it.
    """


def commit(path: Path, name: str, term: str) -> float:
    """Write, stage and commit one document. Returns the wall clock at return."""
    (path / "docs" / f"{name}.md").write_text(doc(term), encoding="utf-8")
    staged = git(path, "add", "-A", check=False)
    if staged.returncode != 0:
        raise StagingLost(f"git add -A exited {staged.returncode}: {staged.stderr.strip()}")
    subprocess.run(
        ["git", "commit", "-qm", name], cwd=path, capture_output=True, text=True,
        encoding="utf-8", env=hook_env(),
    )
    return time.monotonic()


@dataclass
class Trial:
    index: int
    delay: float
    #: Seconds the first runner was observed `running`, or `None` if never seen.
    observed_run_seconds: float | None
    #: Was a runner still holding the lock when the second commit returned?
    second_commit_landed_inside_the_run: bool
    #: `git add -A` raced the runner and lost — a capture in its own right.
    staging_lost: str
    #: Final state after the settle window.
    stranded: bool
    findable: bool
    final_state: dict | None
    note: str


def settle(path: Path, timeout: float) -> dict | None:
    """Poll until idle, or return the last state seen at the deadline.

    ⚠ **A doctor call that does not parse is retried, never fatal.** One poll
    landing while the runner holds the index would otherwise fail the trial
    faster than a passing one, which is the defect `_drain` carried until
    2026-09-13.
    """
    deadline = time.monotonic() + timeout
    last: dict | None = None
    while time.monotonic() < deadline:
        state = runner_state(path)
        if state is not None:
            last = state
            if not state["running"] and state["pending"] == 0:
                return state
        time.sleep(0.2)
    return last


def one_trial(index: int, delay: float, *, docs: int, settle_seconds: float) -> Trial:
    tmp = Path(tempfile.mkdtemp(prefix=f"fux-race-{index:03d}-"))
    try:
        repo = tmp / "repo"
        repo.mkdir()
        make_repo(repo, docs=docs)

        started = commit(repo, "alpha", "alphaterm")
        # Watch the first runner rather than assuming it started. The delay is
        # measured from the commit's RETURN, which is what a human types next,
        # and the lock is read in process so the sampling is finer than the run.
        observed: float | None = None
        seen_running = False
        while time.monotonic() - started < delay:
            if live(repo):
                seen_running = True
            elif seen_running and observed is None:
                observed = time.monotonic() - started
            time.sleep(0.002)

        inside = live(repo)
        staging_lost = ""
        try:
            commit(repo, "beta", "betaterm")
        except StagingLost as exc:
            staging_lost = str(exc)

        final = settle(repo, settle_seconds)
        stranded = bool(final and not final["running"] and final["pending"] > 0)
        found = "beta.md" in fux(repo, "find", "betaterm", "--json").stdout
        note = ""
        if staging_lost:
            note = f"STAGING LOST: {staging_lost}"
        elif stranded:
            note = "STRANDED: pending > 0 with nothing running"
        elif not found:
            note = "beta was never indexed, and the runner reported idle"
        return Trial(
            index=index,
            delay=delay,
            observed_run_seconds=observed,
            second_commit_landed_inside_the_run=inside,
            staging_lost=staging_lost,
            stranded=stranded,
            findable=found,
            final_state=final,
            note=note,
        )
    finally:
        fux(tmp / "repo", "daemon", "stop")
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--trials", type=int, default=20, help="trials per delay step")
    parser.add_argument("--docs", type=int, default=250, help="filler documents (lengthens the run)")
    parser.add_argument(
        "--delays",
        type=float,
        nargs="+",
        default=None,
        help="seconds to wait after the first commit before the second "
        "(default: a sweep calibrated to the observed run length)",
    )
    parser.add_argument("--settle", type=float, default=90.0, help="seconds to wait for idle")
    parser.add_argument("--json-out", type=Path, help="write every trial as JSON")
    args = parser.parse_args(argv)

    delays = args.delays
    if delays is None:
        print("calibrating: one run with no second commit ...")
        base = calibrate(args.docs)
        print(f"  a background re-index takes about {base:.3f}s here")
        # The tail is where the window is, so the grid is dense there and thin
        # at the front: 0.90-1.10 is release, handoff and exit.
        delays = [
            round(base * f, 3)
            for f in (0.2, 0.5, 0.75, 0.88, 0.92, 0.95, 0.97, 0.99, 1.0, 1.01, 1.03, 1.08, 1.2)
        ]

    results: list[Trial] = []
    reproduced = 0
    for delay in delays:
        for i in range(args.trials):
            trial = one_trial(len(results), delay, docs=args.docs, settle_seconds=args.settle)
            results.append(trial)
            captured = trial.stranded or trial.staging_lost or not trial.findable
            flag = "  <-- CAPTURED" if captured else ""
            if flag:
                reproduced += 1
            print(
                f"delay={delay:7.3f}s  trial {i + 1:3d}/{args.trials}  "
                f"inside={trial.second_commit_landed_inside_the_run!s:5}  "
                f"stranded={trial.stranded!s:5}  found={trial.findable!s:5}  "
                f"staging={'LOST' if trial.staging_lost else 'ok':4}{flag}"
            )
            if flag:
                print(f"    {trial.note}")
                print(f"    final state: {json.dumps(trial.final_state)}")

    if args.json_out:
        args.json_out.write_text(
            json.dumps([asdict(t) for t in results], indent=2), encoding="utf-8"
        )

    inside = sum(1 for t in results if t.second_commit_landed_inside_the_run)
    lost = sum(1 for t in results if t.staging_lost)
    stranded = sum(1 for t in results if t.stranded)
    print(
        f"\n{len(results)} trials, {inside} of them with the second commit inside the run, "
        f"{reproduced} captured  (staging lost: {lost}, stranded: {stranded})"
    )
    if reproduced:
        print("RACE REPRODUCED — this is a CAPTURE. Change nothing in src/ in this pass.")
        return 1
    print(
        "NOT REPRODUCED under deliberate stress. That is a result: file it, and W-140 row 21 "
        "stops waiting for a flake that a targeted sweep cannot summon."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
