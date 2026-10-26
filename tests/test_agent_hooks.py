"""The agent hooks SR-LAW-14, SR-WORK-NOW, SR-WORK-CLEANUP, SR-WORK-BLOCKERS and
SR-WORK-SESSION own are lockmaster's kit since 2026-10-26 (SR-WORK-SESSION
decision 15, lockmaster W-09).

Their behaviour — the disk budget asking past the approved ceiling one GB per
yes, the NOW ledger's one row per live session, worktree cleanup never losing a
file and never forcing, lock release — is tested where the code lives:
lockmaster's `tests/test_kit_hooks.py`, ported from this file's earlier tests.
What stays here is what only this repository can show:

- the kit is installed and pinned: every file `.claude/lockmaster.lock` names is
  on disk with the hash it names (an edit made here instead of in the kit fails);
- every kit hook is registered exactly once — no second entry left from the
  hand-copied hooks' command spelling;
- this repo's `work/MACHINE.md` and `work/NOW.md` are in the shape the kit reads.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / ".claude" / "lockmaster.lock"
SETTINGS = ROOT / ".claude" / "settings.json"
HOOKS = ROOT / ".claude" / "hooks"


def _lock() -> dict:
    return json.loads(LOCK.read_text(encoding="utf-8"))


def test_the_kit_is_installed_and_pinned():
    files = _lock()["files"]
    assert any(rel.endswith("block-main.py") for rel in files), "the kit is not installed"
    for rel, digest in files.items():
        path = ROOT / rel
        assert path.is_file(), f"{rel} is pinned in .claude/lockmaster.lock but missing"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, (
            f"{rel} differs from the installed kit. Change it in the lockmaster repository's "
            "kit/ and run `lockmaster install .` — never edit the installed copy."
        )


def test_every_kit_hook_is_registered_exactly_once():
    pairs = [(event, h["command"]) for event, groups in json.loads(SETTINGS.read_text(encoding="utf-8"))["hooks"].items()
             for g in groups for h in g["hooks"]]
    commands = [c for _, c in pairs]
    kit = set(_lock()["settings"])
    counts = Counter(p for p in pairs if p[1] in kit)  # once per event: release-locks runs at Stop and at SessionEnd
    assert {c for _, c in counts} == kit, f"kit hooks not registered: {sorted(kit - {c for _, c in counts})}"
    assert all(n == 1 for n in counts.values()), {p: n for p, n in counts.items() if n > 1}
    pinned = {Path(rel).name for rel in _lock()["files"]}
    stray = [c for c in commands if c not in kit
             and (m := re.search(r"\.claude/hooks/([^\" ]+)", c)) and m.group(1) in pinned]
    assert not stray, f"a kit hook registered under another spelling runs twice: {stray}"


def test_the_budget_row_is_one_the_kit_reads():
    spec = importlib.util.spec_from_file_location("kit_disk_budget", HOOKS / "disk-budget.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.MACHINE == ROOT / "work" / "MACHINE.md"
    assert re.search(r"^\|\s*budget\s*\|\s*[\d.]+\s*GB", mod.MACHINE.read_text(encoding="utf-8"), re.M), (
        "work/MACHINE.md has no `| budget | N GB … |` row; the kit falls back to 5 GB silently"
    )


def test_now_md_has_the_two_tables_the_ledger_writes():
    text = (ROOT / "work" / "NOW.md").read_text(encoding="utf-8")
    assert "## In flight" in text and "| session | surface | started | working on |" in text
    assert "## Resources this session created" in text
    assert "| kind | where | host | session | created |" in text
