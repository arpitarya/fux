"""M5 through the real CLI and real git: hooks, and the merge driver.

The load-bearing test is `test_the_driver_resolves_what_git_cannot`: it runs
the *same* merge twice, once without the driver and once with, and asserts git
conflicts in the first case. Without that control the driver could be doing
nothing and the test would still pass.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

DRIVER = shutil.which("fux-merge-index")


def git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=check)


def fux(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "fux.cli", *args], cwd=cwd, capture_output=True, text=True
    )


def doc(text: str) -> str:
    return f"---\ntitle: {text}\n---\n# {text}\n\n{text} body\n"


def make_repo(path: Path, *, hooks: bool) -> str:
    (path / ".fux" / "sources").mkdir(parents=True)
    (path / "docs").mkdir()
    (path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    (path / ".fux" / "sources" / "dirs").write_text("docs\n", encoding="utf-8")
    # aa.md and gr.md land in the SAME shard, so an edit to each produces
    # adjacent changed lines — which is exactly what a textual merge cannot do.
    (path / "docs" / "aa.md").write_text(doc("aa one"), encoding="utf-8")
    (path / "docs" / "gr.md").write_text(doc("gr one"), encoding="utf-8")

    git(path, "init", "-q")
    git(path, "config", "user.email", "t@t.test")
    git(path, "config", "user.name", "T")
    # The developer's global config may sign commits; a fixture repo must not
    # depend on gpg being reachable (one test deliberately shrinks PATH).
    git(path, "config", "commit.gpgsign", "false")
    fux(path, "ingest")
    if hooks:
        fux(path, "hooks")
    git(path, "add", "-A")
    git(path, "commit", "-qm", "init")
    return git(path, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()


def diverge(path: Path, base: str) -> None:
    """Two branches, each editing a different record in the same shard."""
    git(path, "checkout", "-qb", "x")
    (path / "docs" / "aa.md").write_text(doc("aa TWO"), encoding="utf-8")
    fux(path, "ingest")
    git(path, "add", "-A")
    git(path, "commit", "-qm", "x")

    git(path, "checkout", "-q", base)
    git(path, "checkout", "-qb", "y")
    (path / "docs" / "gr.md").write_text(doc("gr TWO"), encoding="utf-8")
    fux(path, "ingest")
    git(path, "add", "-A")
    git(path, "commit", "-qm", "y")


@pytest.mark.skipif(DRIVER is None, reason="fux-merge-index not on PATH (editable install needed)")
def test_the_driver_resolves_what_git_cannot(tmp_path):
    """The control and the treatment, same scenario."""
    plain = tmp_path / "plain"
    plain.mkdir()
    base = make_repo(plain, hooks=False)
    diverge(plain, base)
    conflicted = git(plain, "merge", "x", "-m", "merge", check=False)
    assert conflicted.returncode != 0, "control: git should conflict without the driver"
    assert "CONFLICT" in conflicted.stdout

    wired = tmp_path / "wired"
    wired.mkdir()
    base = make_repo(wired, hooks=True)
    diverge(wired, base)
    merged = git(wired, "merge", "x", "-m", "merge", check=False)
    assert merged.returncode == 0, f"treatment: the driver should resolve it\n{merged.stdout}"

    shard = next((wired / ".fux" / "index").glob("*.jsonl"))
    records = [json.loads(l) for l in shard.read_text().splitlines()[1:]]
    by_id = {r["id"]: r for r in records}
    # BOTH sides' work survives, each at the ver its own edit produced.
    assert by_id["file:docs/aa.md"]["ver"] == 2
    assert by_id["file:docs/gr.md"]["ver"] == 2


def test_hooks_install_and_report_their_state(tmp_path):
    base = make_repo(tmp_path, hooks=False)
    assert base
    out = fux(tmp_path, "hooks").stdout
    assert "post-commit" in out and "merge driver registered" in out

    state = json.loads(fux(tmp_path, "hooks", "--json").stdout)
    assert state["hooks"] == {"post-commit": "fux", "post-merge": "fux", "post-checkout": "fux"}
    assert state["gitattributes"] is True


def test_hooks_refuse_to_clobber_an_existing_hook(tmp_path):
    make_repo(tmp_path, hooks=False)
    theirs = tmp_path / ".git" / "hooks" / "post-commit"
    theirs.parent.mkdir(parents=True, exist_ok=True)
    theirs.write_text("#!/bin/sh\necho ours\n", encoding="utf-8")

    out = fux(tmp_path, "hooks").stdout
    assert "REFUSED post-commit" in out
    assert theirs.read_text() == "#!/bin/sh\necho ours\n"


def test_uninstall_leaves_a_foreign_hook_alone(tmp_path):
    make_repo(tmp_path, hooks=True)
    theirs = tmp_path / ".git" / "hooks" / "post-commit"
    theirs.write_text("#!/bin/sh\necho ours\n", encoding="utf-8")

    out = fux(tmp_path, "hooks", "--uninstall").stdout
    assert "kept    post-commit" in out
    assert theirs.exists()
    assert not (tmp_path / ".git" / "hooks" / "post-merge").exists()


def test_the_post_commit_hook_reindexes_after_a_commit(tmp_path):
    """The lag is one commit, and the hook says so rather than hiding it.

    ⚠ **This test raced from 2026-08-22 until 2026-08-27.** It was written when
    `post-commit` re-indexed INLINE, so reading the index on the next line was
    sound. When the fork resolved to option B the hook became
    `fux ingest --spawn-runner` — it returns immediately and a detached process
    does the work — and this became a read against a runner that had not
    finished. **It failed roughly one run in three on a loaded machine and
    passed on a fast one**, which is the shape a flake takes before anyone
    calls it one. `_drain` is how every sibling test waits, and it is what was
    missing here.

    ⚠ **It now overlaps `test_post_commit_defers_and_a_detached_runner_drains_
    the_list` almost exactly** — same corpus, same commit, same assertion.
    Flagged rather than deleted: which of the two survives is a call about what
    the suite should say, not a fix for the race.
    """
    make_repo(tmp_path, hooks=True)

    (tmp_path / "docs" / "new.md").write_text(doc("brandnewterm"), encoding="utf-8")
    git(tmp_path, "add", "-A")
    committed = subprocess.run(
        ["git", "commit", "-m", "add new"], cwd=tmp_path, capture_output=True, text=True,
        env=_hook_env(),
    )
    assert committed.returncode == 0, "a hook must never block a commit"

    assert _drain(tmp_path), "the detached runner never finished"
    found = fux(tmp_path, "find", "brandnewterm", "--json").stdout
    assert "new.md" in found, "post-commit should have re-indexed the committed tree"


def _hook_env() -> dict:
    return dict(os.environ, PATH=f"{Path(sys.executable).parent}{os.pathsep}{os.environ['PATH']}")


def test_the_hook_environment_can_actually_find_fux(tmp_path):
    """The guard on every hook-driven test below — **a job that forgot the
    editable install must SAY so, not report green.**

    The hook's first line is `command -v fux >/dev/null 2>&1 || exit 0`, so with
    no `fux` on `PATH` it exits successfully having done nothing. Any test whose
    only assertion is *"the commit succeeded"* passes on that, proving only that
    a no-op is a no-op.

    ⚠ **The scale of this was overstated and is corrected here by
    measurement.** `work/OPEN-WORK.md` recorded *"four hook tests go green-by-
    vacuity without `fux` on `PATH`"*. Re-running this file on 2026-08-27 with
    `PATH=/usr/bin:/bin` (git present, fux absent) gives **4 failed, 9 passed**:
    the four post-commit re-index tests assert a term is findable afterwards and
    fail hard. Exactly **one** test passed vacuously —
    `test_nothing_fux_spawned_outlives_its_own_run`, whose subject is the
    ABSENCE of a resident process, and which no `fux`-absent run can distinguish
    from success.

    That one is unfixable in isolation — the assertion is about nothing being
    there — so the guard belongs at the environment, where it covers the whole
    class including tests nobody has written yet.
    """
    which = subprocess.run(
        ["sh", "-c", "command -v fux"], env=_hook_env(), capture_output=True, text=True
    )
    assert which.returncode == 0, (
        "`fux` is not on PATH inside the hook environment, so every hook in this "
        "file exits at its first line having done nothing. Install the package "
        "editable (`uv sync --extra dev`) before trusting a green run here."
    )
    version = subprocess.run(
        ["sh", "-c", "fux --version"], env=_hook_env(), capture_output=True, text=True
    )
    assert version.returncode == 0, (
        "`command -v fux` resolves but `fux --version` fails — a shim or a stale "
        f"entry, which is WORSE than absent: {version.stderr.strip()!r}. The hook "
        "would pass its guard and then fail silently into `|| exit 0`."
    )


def _drain(root: Path, timeout: float = 120.0) -> bool:
    """Wait for the detached runner to finish. True if it drained the list."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        pending = fux(root, "doctor", "--json").stdout
        try:
            state = json.loads(pending)["runner"]
        except (ValueError, KeyError):
            return False
        if not state["running"] and state["pending"] == 0:
            return True
        time.sleep(0.2)
    return False


def test_post_commit_defers_and_a_detached_runner_drains_the_list(tmp_path):
    """W-66 Phase 2, through the real hook, real git, and a real detached
    process. The commit returns before the re-index has happened — that is
    the whole of the fork's ruling — and the runner finishes it afterwards."""
    make_repo(tmp_path, hooks=True)

    (tmp_path / "docs" / "new.md").write_text(doc("dirtylistterm"), encoding="utf-8")
    git(tmp_path, "add", "-A")
    committed = subprocess.run(
        ["git", "commit", "-m", "add new"], cwd=tmp_path, capture_output=True, text=True,
        env=_hook_env(),
    )
    assert committed.returncode == 0, "a hook must never block a commit"

    assert _drain(tmp_path), "the detached runner never finished"
    found = fux(tmp_path, "find", "dirtylistterm", "--json").stdout
    assert "new.md" in found, "the deferred runner should have re-indexed the committed tree"


def test_the_commit_returns_before_the_re_index_has_happened(tmp_path):
    """ADR-MAINTENANCE veto condition 5, asserted **structurally rather than
    with a stopwatch** — the commit hands back while the work is still
    outstanding, which is the property, and it is observable without timing
    anything.

    > **This replaced a timed test, and the reason is worth keeping.** The
    > first version committed into a 50-document repo and an 800-document repo
    > and compared wall clock, asserting the larger stayed within 3×. It
    > passed locally and **failed both macOS arms in CI** — not on the ratio,
    > but because draining four full re-indexes of 800 documents blew the
    > drain timeout on a shared runner.
    >
    > Making the bound looser or the timeout longer would have been tuning a
    > flake until it hid. The real defect is that a **latency** assertion does
    > not belong in a suite that must be green on someone else's machine:
    > fux-lab's TEST-PLAN §2 already says latency is not comparable across
    > surfaces, and ADR-MAINTENANCE's own "How to check it" for veto 5 points
    > at `work/regression/.../reproduce.sh` — a measured run — rather than at
    > this file. The cross-size *measurement* is that harness's job. What
    > belongs here is that the deferral exists at all.

    The check is the **hook's own output**, which is deterministic: a deferring
    `post-commit` announces that it spawned and returned. An inline one printed
    `fux: ingested N docs …` and then `the index changed — commit .fux/index`,
    because it had done the work before handing back.

    > **Observing the *state* instead would be racy, and the reason is a real
    > property rather than a test artefact.** A first attempt asserted that the
    > runner was still live, or the dirty list still non-empty, immediately
    > after the commit. It failed locally with `docs: 152, changed: 0` — the
    > runner spawned by the *previous* commit was still going, and
    > `fux ingest` walks the **working tree**, so it had already indexed 150
    > files that were not committed yet. Deferral widens the window in which
    > that is true; the index is late either way, and a later run corrects it.
    > It does mean "is there outstanding work right now" is not a stable
    > observation, so this asserts the path taken rather than the state left.
    """
    make_repo(tmp_path, hooks=True)
    for i in range(30):
        (tmp_path / "docs" / f"bulk{i}.md").write_text(doc(f"bulkterm{i}"), encoding="utf-8")
    git(tmp_path, "add", "-A")
    committed = subprocess.run(
        ["git", "commit", "-m", "bulk"], cwd=tmp_path, capture_output=True, text=True,
        env=_hook_env(),
    )
    assert committed.returncode == 0, "a hook must never block a commit"

    output = committed.stdout + committed.stderr

    # **Two announcements, and both are deferral.** The hook either spawned a
    # runner ("re-indexing in the background") or found one already live and
    # left it to pick the work up ("a re-index is already running"). Which one
    # you get is a race with the previous commit's runner, and it goes the
    # second way routinely on a slower box — every Linux CI arm hit it while
    # macOS and Windows did not. The property under test is the same either
    # way: the hook did not do the work before handing back.
    assert "re-index" in output, (
        f"post-commit announced no deferred re-index at all. Output was:\n{output}"
    )
    assert "ingested" not in output, (
        f"post-commit ran an ingest inline — that is what R5 measured at 44 s.\n{output}"
    )
    assert _drain(tmp_path), "the detached runner never finished"


def test_nothing_fux_spawned_outlives_its_own_run(tmp_path):
    """ADR-MAINTENANCE veto condition 6. The runner is one-shot: it may
    outlive the *commit* (that is what deferral means) but it must exit, and
    nothing resident may remain once it has."""
    make_repo(tmp_path, hooks=True)
    (tmp_path / "docs" / "resident.md").write_text(doc("residentterm"), encoding="utf-8")
    git(tmp_path, "add", "-A")
    subprocess.run(
        ["git", "commit", "-qm", "resident"], cwd=tmp_path, capture_output=True, text=True,
        env=_hook_env(),
    )
    assert _drain(tmp_path)

    # ⚠ **The positive control.** Everything below is an assertion that
    # something is ABSENT, which a run where the hook never fired satisfies
    # perfectly. Measured 2026-08-27: with `PATH=/usr/bin:/bin` this test was
    # the ONLY one in the file that passed with `fux` unreachable. So prove the
    # work HAPPENED first -- then "nothing resident remains" means something.
    indexed = fux(tmp_path, "find", "residentterm", "--json").stdout
    assert "resident.md" in indexed, (
        "the hook never re-indexed, so this test is about to assert that a "
        "runner which never started is not running -- see "
        "test_the_hook_environment_can_actually_find_fux"
    )

    state = json.loads(fux(tmp_path, "doctor", "--json").stdout)["runner"]
    assert state["running"] is False
    assert state["lock"] == "free", "the runner exited without releasing its lock"


def test_two_commits_in_quick_succession_produce_one_runner_and_one_index(tmp_path):
    """The `git rebase` case, in miniature. A naive implementation spawns one
    runner per commit; the lock is what makes it one."""
    make_repo(tmp_path, hooks=True)
    for i in range(4):
        (tmp_path / "docs" / f"rapid{i}.md").write_text(doc(f"rapidterm{i}"), encoding="utf-8")
        git(tmp_path, "add", "-A")
        subprocess.run(
            ["git", "commit", "-qm", f"rapid {i}"], cwd=tmp_path, capture_output=True, text=True,
            env=_hook_env(),
        )
    assert _drain(tmp_path)

    for i in range(4):
        assert f"rapid{i}.md" in fux(tmp_path, "find", f"rapidterm{i}", "--json").stdout, (
            f"rapid{i} was dropped - the union in the dirty list did not hold"
        )


def test_ingest_stop_exits_zero_with_nothing_running(tmp_path):
    """ADR-CLI, 2026-08-22: "make sure it is not running" has succeeded when
    it was not running. Every script that calls it defensively depends on it."""
    make_repo(tmp_path, hooks=False)
    result = fux(tmp_path, "ingest", "--stop")
    assert result.returncode == 0
    assert "no background re-index was running" in result.stdout


def test_doctor_json_reports_the_runner(tmp_path):
    """W-66 Phase 4: a status an agent cannot parse is not a status."""
    make_repo(tmp_path, hooks=False)
    payload = json.loads(fux(tmp_path, "doctor", "--json").stdout)
    assert set(payload["runner"]) >= {"running", "pid", "lock", "pending", "last_run"}
    assert any(c["name"] == "background runner" for c in payload["checks"])


def test_doctor_reports_a_stale_lock_without_clearing_it(tmp_path):
    """Veto 7 through the shipped CLI: reporting must not repair."""
    make_repo(tmp_path, hooks=False)
    dead = subprocess.Popen([sys.executable, "-c", "pass"])
    dead.wait()
    # ⚠ Was the literal `"runner.lock"`, which stopped naming a real file on
    # 2026-08-26 when W-86 P6 renamed it to `write.lock` — every command that
    # writes the committed index holds it now, not just the runner. The test
    # kept passing its own fabricated path to itself and asserting doctor saw
    # nothing wrong, which was true and meaningless. Imported, never spelled.
    from fux.maintain.runner import LOCK_NAME

    lock = tmp_path / ".fux" / "runtime" / LOCK_NAME
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text(json.dumps({"pid": dead.pid}), encoding="utf-8")
    before = lock.read_bytes()

    text = fux(tmp_path, "doctor").stdout
    assert "fux ingest --stop" in text, "a stale lock must name its remedy"
    assert lock.read_bytes() == before, "doctor cleared the lock it was only asked to report"

    assert fux(tmp_path, "ingest", "--stop").returncode == 0
    assert not lock.exists(), "the explicit takeover should have cleared it"


def test_ask_declares_a_pending_reindex_on_stderr_never_stdout(tmp_path):
    """W-66 Phase 3. Simulates the lagging window Phase 2's deferral will
    open — a dirty list with no completed run behind it yet."""
    make_repo(tmp_path, hooks=False)
    quiet = fux(tmp_path, "ask", "aa", "--json")
    assert quiet.stderr == ""

    dirty_path = tmp_path / ".fux" / "runtime" / "dirty"
    dirty_path.parent.mkdir(parents=True, exist_ok=True)
    dirty_path.write_text("file:docs/aa.md\nfile:docs/gr.md\n", encoding="utf-8")

    loud = fux(tmp_path, "ask", "aa", "--json")
    assert loud.stdout == quiet.stdout  # the declaration never touches the contract
    assert "2 changed path(s) pending re-index" in loud.stderr


def test_a_hook_never_blocks_a_commit_even_when_fux_is_absent(tmp_path):
    """`command -v fux || exit 0` — asserted by running with an empty PATH."""
    make_repo(tmp_path, hooks=True)
    (tmp_path / "docs" / "x.md").write_text(doc("x"), encoding="utf-8")
    git(tmp_path, "add", "-A")
    result = subprocess.run(
        ["git", "commit", "-m", "no fux on path"],
        cwd=tmp_path, capture_output=True, text=True,
        env={"PATH": "/usr/bin:/bin", "HOME": os.environ.get("HOME", "")},
    )
    assert result.returncode == 0, result.stderr
