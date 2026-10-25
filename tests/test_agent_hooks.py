"""The four agent hooks SR-LAW-14, SR-WORK-NOW and SR-WORK-CLEANUP own.

- `worktree-cleanup.py` — removes a worktree only when nothing can be lost, and
  never with `--force` or `-D` (SR-WORK-CLEANUP decisions 1–3).
- `disk-budget.py` — asks past the approved ceiling, one GB per yes, and forgets
  the approvals back under the budget (SR-LAW-14 decisions 1, 3, 4).
- `now-ledger.py` — one row per live session; a session's rows leave NOW.md
  when it ends (SR-WORK-NOW decisions 2–4).
- `release-locks.sh` — a session's own write locks are released, a fresh lock
  of another session's is kept (SR-WORK-CLEANUP decision 8).

Every test runs on a temporary repository; nothing here touches this tree's
worktrees, NOW.md or locks.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / ".claude" / "hooks"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), HOOKS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod  # a dataclass resolves its module here
    spec.loader.exec_module(mod)
    return mod


def _git(cwd: Path, *argv: str) -> str:
    return subprocess.run(
        ["git", "-c", "commit.gpgsign=false", "-c", "user.email=t@fux", "-c", "user.name=t", *argv],
        cwd=cwd, capture_output=True, text=True, encoding="utf-8", check=True,
    ).stdout


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q", "-b", "main")
    (root / ".gitignore").write_text("node_modules/\nnotes.local\n", encoding="utf-8")
    (root / "a.md").write_text("a\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "init")
    return root


def _worktree(repo: Path, name: str) -> Path:
    path = repo.parent / name
    _git(repo, "worktree", "add", "-q", "-b", name, str(path))
    return path


# ── worktree-cleanup.py ──────────────────────────────────────────────────────

def test_a_merged_clean_worktree_is_safe_and_removed(repo):
    wc = _load("worktree-cleanup")
    path = _worktree(repo, "done")
    (path / "node_modules").mkdir()
    (path / "node_modules" / "x.js").write_text("x", encoding="utf-8")  # build output
    [wt] = wc.verdicts(repo)
    assert wt.safe, wt.reasons
    assert wc.clean(wt, repo) is None
    assert not path.exists()
    assert "done" not in _git(repo, "branch", "--list", "done")


def test_an_unmerged_commit_is_red_and_untouched(repo):
    wc = _load("worktree-cleanup")
    path = _worktree(repo, "wip")
    (path / "b.md").write_text("b\n", encoding="utf-8")
    _git(path, "add", "-A")
    _git(path, "commit", "-qm", "wip")
    [wt] = wc.verdicts(repo)
    assert not wt.safe and "not in main" in wt.reasons[0]
    assert wc.clean(wt, repo).startswith("not safe")
    assert path.exists()


@pytest.mark.parametrize("name", ["untracked.md", "notes.local"])
def test_an_unsaved_or_ignored_non_build_file_is_red(repo, name):
    wc = _load("worktree-cleanup")
    path = _worktree(repo, "dirty")
    (path / name).write_text("keep me\n", encoding="utf-8")
    [wt] = wc.verdicts(repo)
    assert not wt.safe, "a file that is not build output would be lost"


def test_cleanup_never_forces():
    src = (HOOKS / "worktree-cleanup.py").read_text(encoding="utf-8")
    code = "\n".join(line for line in src.splitlines() if not line.lstrip().startswith(("#", '"')))
    assert '"--force"' not in code and '"-D"' not in code


# ── disk-budget.py ───────────────────────────────────────────────────────────

@pytest.fixture
def budget(tmp_path, monkeypatch):
    mod = _load("disk-budget")
    machine = tmp_path / "MACHINE.md"
    machine.write_text("| what | value |\n|---|---|\n| budget | 5 GB for the whole project |\n", encoding="utf-8")
    monkeypatch.setattr(mod, "MACHINE", machine)
    monkeypatch.setattr(mod, "STATE", tmp_path / "state")
    monkeypatch.setattr(mod, "USAGE", tmp_path / "usage")
    return mod


def _use(mod, monkeypatch, gb: float):
    monkeypatch.setattr(mod, "usage_kb", lambda fresh=False: int(gb * mod.GB))


def test_the_number_is_read_from_machine_md(budget):
    assert budget.budget_gb() == 5
    assert budget.budget_gb((ROOT / "work" / "MACHINE.md").read_text(encoding="utf-8")) >= 1


def test_under_the_budget_nothing_is_asked(budget, monkeypatch):
    _use(budget, monkeypatch, 4.0)
    assert budget.pre({"tool_name": "Bash", "tool_use_id": "t1"}) is None


def test_past_the_budget_one_yes_approves_one_gb(budget, monkeypatch):
    _use(budget, monkeypatch, 5.2)
    asked = budget.pre({"tool_name": "Bash", "tool_use_id": "t1"})
    assert asked["hookSpecificOutput"]["permissionDecision"] == "ask"
    budget.post({"tool_name": "Bash", "tool_use_id": "t1"})  # the tool ran: a yes
    assert json.loads(budget.STATE.read_text())["approved_gb"] == 6
    assert budget.pre({"tool_name": "Bash", "tool_use_id": "t2"}) is None  # 5.2 < 6
    # a later, unrelated tool run approves nothing more
    budget.post({"tool_name": "Bash", "tool_use_id": "t9"})
    assert json.loads(budget.STATE.read_text())["approved_gb"] == 6


def test_a_new_agent_asks_from_ninety_percent(budget, monkeypatch):
    _use(budget, monkeypatch, 4.6)
    assert budget.pre({"tool_name": "Bash", "tool_use_id": "t1"}) is None
    assert budget.pre({"tool_name": "Agent", "tool_use_id": "t2"})["hookSpecificOutput"]["permissionDecision"] == "ask"


def test_reads_never_ask(budget, monkeypatch):
    _use(budget, monkeypatch, 50.0)
    assert budget.pre({"tool_name": "Read", "tool_use_id": "t1"}) is None


def test_approvals_reset_back_under_the_budget(budget, monkeypatch):
    budget.STATE.write_text(json.dumps({"approved_gb": 8}))
    _use(budget, monkeypatch, 1.0)
    assert budget.ceiling_gb(5, budget.usage_kb()) == 5
    assert json.loads(budget.STATE.read_text()) == {}


# ── now-ledger.py ────────────────────────────────────────────────────────────

@pytest.fixture
def ledger(tmp_path, monkeypatch):
    mod = _load("now-ledger")
    now = tmp_path / "NOW.md"
    # the live file's shape, never its rows: a session running on this tree
    # would otherwise be counted by every test below
    text = (ROOT / "work" / "NOW.md").read_text(encoding="utf-8")
    text = mod.set_rows(text, mod.FLIGHT, [])
    now.write_text(text, encoding="utf-8")
    monkeypatch.setattr(mod, "NOW_MD", now)
    monkeypatch.setattr(mod, "SESSIONS", tmp_path / "sessions")
    monkeypatch.setattr(mod, "LOCK", tmp_path / "now.lock")
    monkeypatch.setattr(mod, "NUDGED", tmp_path / "nudged")
    monkeypatch.setattr(mod, "_worktree_paths", lambda: set())
    return mod


def test_a_session_has_one_row_and_loses_it_at_the_end(ledger):
    ledger.start({"session_id": "abcdef1234"})
    ledger.start({"session_id": "abcdef1234"})
    flight = ledger.rows(ledger.NOW_MD.read_text(), ledger.FLIGHT)
    assert [r[0] for r in flight] == ["abcdef12"]
    ledger.end({"session_id": "abcdef1234"})
    assert ledger.rows(ledger.NOW_MD.read_text(), ledger.FLIGHT) == []


def test_another_sessions_row_is_never_touched(ledger):
    ledger.start({"session_id": "aaaaaaaa"})
    ledger.start({"session_id": "bbbbbbbb"})
    ledger.end({"session_id": "aaaaaaaa"})
    assert [r[0] for r in ledger.rows(ledger.NOW_MD.read_text(), ledger.FLIGHT)] == ["bbbbbbbb"]


def test_a_dead_session_is_closed_at_the_next_start(ledger):
    text = ledger.set_rows(ledger.NOW_MD.read_text(), ledger.FLIGHT,
                           [["deadbeef", "Cowork", "2000-01-01 00:00", "gone"]])
    ledger.NOW_MD.write_text(text)
    ledger.start({"session_id": "cafecafe"})
    assert [r[0] for r in ledger.rows(ledger.NOW_MD.read_text(), ledger.FLIGHT)] == ["cafecafe"]


def test_stop_asks_once_for_an_empty_working_on_cell(ledger):
    ledger.start({"session_id": "abcdef12"})
    assert ledger.stop({"session_id": "abcdef12"})["decision"] == "block"
    assert ledger.stop({"session_id": "abcdef12"}) is None


def test_the_committed_now_md_is_two_empty_tables(ledger):
    text = (ROOT / "work" / "NOW.md").read_text(encoding="utf-8")
    assert ledger.rows(text, ledger.FLIGHT) == [] or all(len(r) == 4 for r in ledger.rows(text, ledger.FLIGHT))
    assert all(len(r) == 5 for r in ledger.rows(text, ledger.RESOURCES))


# ── release-locks.sh ─────────────────────────────────────────────────────────

@pytest.mark.skipif(sys.platform == "win32" or not shutil.which("jq"), reason="bash + jq hook")
def test_release_locks_frees_own_and_keeps_a_fresh_foreign_lock(repo):
    hooks = repo / ".claude" / "hooks"
    hooks.mkdir(parents=True)
    shutil.copy2(HOOKS / "release-locks.sh", hooks / "release-locks.sh")
    locks = repo / ".claude" / ".locks"
    now = int(time.time())
    for key, owner in (("mine", "me"), ("theirs", "them"), ("stale", "them")):
        (locks / key).mkdir(parents=True)
        when = now if key != "stale" else now - 3600
        (locks / key / "owner").write_text(f"{owner} {when} x.md\n", encoding="utf-8")
    subprocess.run(["bash", str(hooks / "release-locks.sh")], input='{"session_id":"me"}',
                   text=True, check=True, env={**os.environ, "CLAUDE_SESSION_ID": "me"})
    assert sorted(p.name for p in locks.iterdir()) == ["theirs"]
