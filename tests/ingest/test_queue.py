"""W-86 P6 — the enrichment queue, and the write lock that guards the index.

Two things fux could not do before this: **say** that a document needs a model
(scope came only from a declared `dirs` line), and stop **two foreground
writers** touching the index at once.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

import pytest

from fux.errors import FuxError
from fux.ingest import queue as queue_mod
from fux.maintain import runner
from fux.store import fuxdir


@pytest.fixture
def repo(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    fuxdir.ensure_layout(tmp_path)
    fuxdir.derived_dir(tmp_path, "runtime")
    return tmp_path


E = queue_mod.QueueEntry


# -- the queue --------------------------------------------------------------


def test_the_queue_is_sorted_regardless_of_discovery_order():
    """Walk order is filesystem order. A queue that differed between two
    machines would make `git status` dirty for no reason at all.
    """
    a = queue_mod.render([E("file:z.png", "s2", "no decoder"), E("file:a.png", "s1", "no decoder")])
    b = queue_mod.render([E("file:a.png", "s1", "no decoder"), E("file:z.png", "s2", "no decoder")])
    assert a == b
    assert a.index("a.png") < a.index("z.png")


def test_the_queue_carries_no_timestamp():
    """A clock would make the file change on every run and turn a stable
    backlog into noise — and it would break L3 for a committed byte.
    """
    text = queue_mod.render([E("file:a.png", "sha", "no decoder for .png")])
    assert "20" not in text.replace("W-86", ""), "looks like a date crept in"


def test_the_queue_holds_no_content(repo):
    """L2: the index holds statistics, never documents. A queue that quoted the
    first line of an unreadable file would be the one place that leaked.
    """
    queue_mod.write(repo, [E("file:secret.png", "abc123", "no decoder for .png")])
    text = (repo / queue_mod.QUEUE_REL).read_text()
    assert "secret.png" in text and "abc123" in text
    assert len(text.splitlines()) == 5  # 4 header lines + 1 row


def test_an_unchanged_backlog_is_not_rewritten(repo):
    entries = [E("file:a.png", "s", "no decoder for .png")]
    assert queue_mod.write(repo, entries) is True
    assert queue_mod.write(repo, entries) is False, "identical bytes must not be rewritten"


def test_a_reason_distinguishes_a_missing_decoder_from_an_unreadable_document():
    """The queue's whole value is that difference: one is someone could write a
    decoder, the other is only a model will help.
    """
    from fux.decode import reason

    assert "no decoder" in reason("a.png")
    assert "pdfdoc" in reason("scan.pdf")


def test_a_malformed_row_is_skipped_not_fatal(repo):
    path = repo / queue_mod.QUEUE_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# h\ngarbage-with-no-tab\nfile:a.png\tsha\treason\n", encoding="utf-8")
    assert [e.doc_id for e in queue_mod.read(repo)] == ["file:a.png"]


def test_a_tab_in_a_reason_cannot_break_the_format():
    line = E("file:a.png", "s", "no\tdecoder\nfor .png").line()
    assert line.count("\t") == 2


def test_the_queue_file_is_invisible_to_the_enrichment_sha_glob(repo):
    """`.fux/enrich/` is globbed as `<sha>.md` and `enrich.py::prune` deletes
    orphans there. A queue file at the mercy of that glob would vanish.
    """
    queue_mod.write(repo, [E("file:a.png", "s", "r")])
    assert list((repo / ".fux" / "enrich").glob("*.md")) == []


# -- progress: local, and therefore different --------------------------------


def test_progress_is_local_and_subtracts_from_the_queue(repo):
    queue_mod.write(repo, [E("file:a.png", "s", "r"), E("file:b.png", "s", "r")])
    assert len(queue_mod.pending(repo)) == 2
    queue_mod.mark_done(repo, "file:a.png")
    assert [e.doc_id for e in queue_mod.pending(repo)] == ["file:b.png"]


def test_progress_lives_under_runtime_so_it_is_gitignored(repo):
    queue_mod.mark_done(repo, "file:a.png")
    assert (repo / queue_mod.PROGRESS_REL).is_file()
    assert "runtime" in queue_mod.PROGRESS_REL
    assert "runtime/" in (repo / ".fux" / ".gitignore").read_text()


# -- the write lock ---------------------------------------------------------


def test_the_lock_is_named_for_every_writer_not_for_the_runner():
    assert runner.LOCK_NAME == "write.lock"


def test_a_second_writer_is_refused_rather_than_allowed_through(repo):
    """The gap fork C closed: a foreground `fux ingest` evicted the background
    runner and then wrote holding nothing, so two of them raced.
    """
    with runner.write_lock(repo):
        with pytest.raises(FuxError, match="another fux process is writing"):
            runner.acquire(repo, required=True)


def test_two_foreground_writers_actually_race_without_it(repo):
    """⚠ The compare doc asserted this race from reading call sites and had
    never reproduced it. This is the reproduction the ruling demanded before
    anything was built on the claim: two processes, no lock, both succeed.
    """
    script = (
        "import sys,pathlib,os;from fux.maintain import runner;"
        "root=pathlib.Path(sys.argv[1]);"
        "print('GOT' if runner.acquire(root) else 'REFUSED')"
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        p for p in (str(pathlib.Path(__file__).resolve().parents[2] / "src"), env.get("PYTHONPATH", "")) if p
    )
    first = subprocess.run([sys.executable, "-c", script, str(repo)], capture_output=True, text=True, env=env)
    second = subprocess.run([sys.executable, "-c", script, str(repo)], capture_output=True, text=True, env=env)
    assert first.stdout.strip() == "GOT", first.stderr[-500:]
    # The second is refused *because the first leaked its lock on exit* — which
    # is exactly why `write_lock` releases in a `finally` rather than trusting
    # a process to tidy up after itself.
    assert second.stdout.strip() == "REFUSED"


def test_the_runner_may_re_enter_its_own_lock(repo):
    """A runner acquires the lock itself and then calls into the shared write
    path. Without re-entry it would deadlock against itself.
    """
    assert runner.acquire(repo) is True
    try:
        with runner.write_lock(repo):
            pass  # must not raise
        assert runner.lock_path(repo).exists(), "re-entry must not release the runner's lock"
    finally:
        runner.release(repo)


def test_a_background_runner_still_declines_quietly(repo):
    """The same line means opposite things to the two callers: a runner that
    cannot take the lock should step aside; a writer must not.
    """
    with runner.write_lock(repo):
        assert runner.acquire(repo, required=False) is False
