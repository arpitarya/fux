"""ADR-MAINTENANCE veto condition 7 — the status surface never repairs.

Named by that record's own "How to check it" block, so the file lives at the
path the record points at. **Reporting must not repair**: a surface that can
report a stale lock and also clear it will eventually clear one whose owner is
alive, and that puts two runners inside `.fux/index/` at once.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from fux.maintain import dirty, runner


def _corpus(root: Path, docs: int = 3) -> None:
    listing = root / ".fux" / "sources" / "dirs"
    listing.parent.mkdir(parents=True, exist_ok=True)
    listing.write_text("docs\n", encoding="utf-8")
    (root / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    (root / "docs").mkdir(exist_ok=True)
    for i in range(docs):
        (root / "docs" / f"d{i}.md").write_text(f"# Doc {i}\n\nbody {i} words here\n", encoding="utf-8")




@pytest.mark.parametrize("held_by", ["alive", "stale"])
def test_every_status_path_leaves_the_lock_byte_identical(tmp_path, held_by):
    """ADR-MAINTENANCE veto 7: reporting must not repair. Run every read-only
    surface against a held and a stale lock and diff the bytes."""
    from fux import doctor

    _corpus(tmp_path)
    if held_by == "alive":
        pid = os.getpid()
    else:
        dead = subprocess.Popen([sys.executable, "-c", "pass"])
        dead.wait()
        pid = dead.pid
    runtime = tmp_path / ".fux" / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    lock = runtime / runner.LOCK_NAME
    lock.write_text(json.dumps({"pid": pid}), encoding="utf-8")
    before = lock.read_bytes()

    runner.status(tmp_path)
    runner.holder(tmp_path)
    runner.last_run(tmp_path)
    doctor._background_runner(tmp_path)

    assert lock.read_bytes() == before, "a status surface cleared the lock"


def test_status_reports_a_stale_lock_and_names_the_fix(tmp_path):
    dead = subprocess.Popen([sys.executable, "-c", "pass"])
    dead.wait()
    runtime = tmp_path / ".fux" / "runtime"
    runtime.mkdir(parents=True)
    (runtime / runner.LOCK_NAME).write_text(json.dumps({"pid": dead.pid}), encoding="utf-8")

    state = runner.status(tmp_path)
    assert state["lock"] == "stale" and state["running"] is False

    from fux import doctor

    check = doctor._background_runner(tmp_path)
    assert "fux ingest --stop" in check.detail, "a stale lock must name its remedy"


def test_status_counts_pending_documents(tmp_path):
    dirty.record(tmp_path, ["file:a.md", "file:b.md"])
    assert runner.status(tmp_path)["pending"] == 2
