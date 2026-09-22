"""🔴 **The committed `.claude/settings.json` is always the LOCKED one.**

[L11](../records/0012_LAW-11-sealed-answer-key.md) decision 14 made the
prohibition a state, and `just golden-unlock` mutates exactly one file to change
it. **That file is committed**, so an unlock leaves the repository one careless
`git commit` away from putting *"the guards are down"* into history and into
every clone — where it would stay until somebody noticed, which is the same
never-fails-loudly shape the whole law is written around.

**Two strikes → a gate** ([SR-WORK-SESSION](../records/0060_WORK-session.md)
decision 13). The class is *a commit took more than the author staged*, and it
happened three times in one session on 2026-09-22:

| | what |
|---|---|
| `a0140874` | `git commit -- <pathspec>` **discarded** a partial stage built specifically to keep another session's rows out — it commits the WORKING TREE, not the index |
| `f425a79a` | a bare `git commit` **took the whole index**, including a concurrent session's staged SR-WORK-REGISTRY work, under a message describing only half of it |
| `163313a1` | the same again, sweeping 67 re-ingested index shards into a commit about the switch |

⚠ **The general problem has no mechanical check** — nothing can know which of
the staged paths the author meant. **This one does**, and it is the one that
matters: whatever else a stray commit carries, it must never carry an unlocked
settings file.

🔴 **This test opens no key path.** It reads `git show HEAD:.claude/settings.json`
— git's object store, not the filesystem — and counts rules. It says nothing
about the working tree, which is *expected* to be unlocked while somebody is
scoring.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

#: The substring every deny rule and both hook filenames share.
MARKER = "golden-answer"

#: The committed file carries 29 today. The floor is the one
#: `tests/test_golden_key_guards.py` already uses, so the two cannot drift into
#: disagreeing about what "the guards are present" means.
MINIMUM_RULES = 14


def _committed_settings() -> dict | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(ROOT), "show", "HEAD:.claude/settings.json"],
            capture_output=True, check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    return json.loads(out.decode("utf-8"))


def test_the_committed_settings_file_still_carries_the_deny_rules():
    settings = _committed_settings()
    if settings is None:
        pytest.skip("not a git checkout, or no committed settings.json — nothing to audit")
    rules = [r for r in settings.get("permissions", {}).get("deny", []) if MARKER in r]
    assert len(rules) >= MINIMUM_RULES, (
        f"HEAD's .claude/settings.json carries only {len(rules)} deny rule(s) naming "
        "the sealed key.\n\n"
        "If the tree is unlocked, AN UNLOCKED SETTINGS FILE HAS BEEN COMMITTED — "
        "declare it, restore the file from the stash or from an earlier ref, and "
        "commit the locked one. `just golden-unlock` mutates this file and nothing "
        "else; it is never meant to reach a ref.\n\n"
        "If the tree is locked, somebody narrowed the guards at HEAD, which is "
        "tests/test_golden_key_guards.py's subject."
    )


def test_the_committed_settings_file_still_registers_both_hooks():
    settings = _committed_settings()
    if settings is None:
        pytest.skip("not a git checkout, or no committed settings.json — nothing to audit")
    commands = [
        h.get("command", "")
        for group in settings.get("hooks", {}).get("PreToolUse", [])
        for h in group.get("hooks", [])
    ]
    for hook in ("guard-golden-answer.sh", "guard-sealed-key.sh"):
        assert any(hook in c for c in commands), (
            f"HEAD's .claude/settings.json does not register {hook}. An unlock "
            "deregisters both hooks — if that state was committed, declare it and "
            "restore the locked file. An unregistered hook is a file, not a guard."
        )
