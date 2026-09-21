"""Every sealed-key guard covers BOTH spellings, and none of them may narrow.

[L11](../records/0012_LAW-11-sealed-answer-key.md) decision 3 (Arpit,
2026-09-18) permits a key to exist on his machine, at one address —
``work/golden/golden-answers/`` — gitignored and closed to every agent. That
permission moves the law's central claim from *there is nothing on disk to
reach* back to *the guards are the defence*, so **each guard is now load-bearing
and each one's residual hole is a hole around a real key**.

⚠ **This is the test W-198 decision-of-done 6 asks for, and its job is the thing
nobody notices:** a guard narrowing. Every one of the six was written against
the **singular** spelling, and `golden-answer*` globs, substring matches and
regex alternations differ in whether they reach `golden-answers/`. A guard that
silently stops matching reads exactly like a guard that is working.

🔴 **This test opens nothing.** It reads the guard files themselves —
``.gitignore``, ``.claude/settings.json``, the two hooks, ``.fux/sources/dirs``
— and feeds *synthetic* paths to the hooks as subprocesses. No path under either
spelling is opened, listed, stat'd or globbed; ``git check-ignore`` answers from
git's rules, not from the filesystem. The companion gate for the committed half
is ``test_golden_key_never_committed.py``.

**The sixth guard, and why it exists.** ``guard-golden-answer.sh``'s TARGET
check is a plain substring and reaches both spellings. **Its Bash branch does
not** — it matches ``golden/golden-answer``, ``golden-answer/`` and
``golden-answer`` before a space, quote or end of string, and a bare
``golden-answers/k.jsonl`` hits none of the three. That hook also refuses every
edit to itself (its own filename contains the string it matches), which is a
property worth keeping rather than routing around, so the gap is closed by a
second hook, ``guard-sealed-key.sh``, and this file proves both.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _usable_bash() -> str | None:
    """The first `bash` that can actually RUN a script, or None.

    ⚠ **On a GitHub Windows runner, `bash` on PATH is the WSL stub in
    `System32`**, which exits 1 without running anything. Every guard
    invocation then came back 1, and because a guard denies with 2, all 32
    assertions in this file read as *the guard allowed it* — the exact
    sentence this file exists to make impossible to say by accident. A shell
    that never started is the most misleading result it can produce, so the
    shell is probed rather than assumed.
    """
    candidates: list[str] = []
    if os.name == "nt":
        # Git for Windows, which is what a shebang-carrying hook needs.
        candidates += [
            r"C:\Program Files\Git\bin\bash.exe",
            r"C:\Program Files\Git\usr\bin\bash.exe",
        ]
    found = shutil.which("bash")
    if found:
        candidates.append(found)
    for candidate in candidates:
        try:
            probe = subprocess.run([candidate, "-c", "exit 7"], capture_output=True, timeout=60)
        except OSError:
            continue
        if probe.returncode == 7:
            return candidate
    return None


BASH = _usable_bash()

# 🔴 `jq` is not optional here, and a missing one is a SKIP rather than a pass.
# Both guards fail closed when they cannot parse their input — they fall back
# to grepping the raw payload — so without `jq` this file would be asserting
# the fallback path's behaviour while claiming to assert the normal one. Two
# green results that mean different things is worse than one honest skip.
HAVE_JQ = bool(BASH) and subprocess.run(
    [BASH, "-c", "command -v jq"], capture_output=True
).returncode == 0

if not BASH or not HAVE_JQ:
    pytest.skip(
        "the guards need a working bash and jq; this platform has "
        f"bash={BASH!r} jq={HAVE_JQ}. The guards themselves are unchanged and "
        "are exercised on every posix leg of the matrix — what is missing here "
        "is a shell to run them in, not coverage of the rule.",
        allow_module_level=True,
    )


SETTINGS = ROOT / ".claude" / "settings.json"
GITIGNORE = ROOT / ".gitignore"
DIRS = ROOT / ".fux" / "sources" / "dirs"
HOOK_1 = ROOT / ".claude" / "hooks" / "guard-golden-answer.sh"
HOOK_2 = ROOT / ".claude" / "hooks" / "guard-sealed-key.sh"

# The canonical spelling and the older one. Both are matched by every guard;
# only the first is a place anything may be written.
CANONICAL = "work/golden/golden-answers"
LEGACY = "work/golden/golden-answer"


# --- the two hooks ----------------------------------------------------------


def run_hook(hook: Path, payload: dict) -> int:
    """Feed one PreToolUse payload to a guard. Returns its exit code (2 = deny)."""
    # 🔴 Through a PROBED `bash`, never as a bare path. Each guard carries a
    # `#!/usr/bin/env bash` shebang, which Windows does not honour: there a
    # bare `[str(hook)]` raises `WinError 193` before the guard runs at all.
    # Naming `bash` was the first fix and was not enough — see `_usable_bash`,
    # where the shell that answers on a Windows runner exits 1 without running
    # anything, which every assertion here then reads as an ALLOW.
    proc = subprocess.run(
        [BASH, str(hook)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    return proc.returncode


@pytest.mark.parametrize("hook", [HOOK_1, HOOK_2], ids=["guard-golden-answer", "guard-sealed-key"])
def test_the_hook_is_present_and_executable(hook):
    """A guard that cannot run is not a guard -- L11's own check 4."""
    assert hook.is_file(), f"{hook.name} is missing"
    if os.name == "nt":
        # Windows has no executable bit, so `st_mode & 0o111` answers a
        # question the filesystem cannot hold. What decides whether the guard
        # can run is the mode **git carries**, because that is the mode a posix
        # checkout — the only place a Claude session ever invokes one — gets.
        entry = subprocess.run(
            ["git", "ls-files", "-s", "--", hook.relative_to(ROOT).as_posix()],
            capture_output=True, text=True, cwd=ROOT, check=True,
        ).stdout.split()
        assert entry and entry[0] == "100755", (
            f"{hook.name} is committed as {entry[0] if entry else 'untracked'}, "
            "not 100755 — a posix checkout would not be able to run it"
        )
    else:
        assert hook.stat().st_mode & 0o111, f"{hook.name} is not executable"


# A tool call that TARGETS a location. Both hooks substring-match these, so both
# must deny every one -- on both spellings.
TARGETING = [
    {"tool_name": "Read", "tool_input": {"file_path": f"{CANONICAL}/set-1.jsonl"}},
    {"tool_name": "Read", "tool_input": {"file_path": f"{LEGACY}/answers.jsonl"}},
    {"tool_name": "Write", "tool_input": {"file_path": f"{CANONICAL}/set-2.jsonl"}},
    {"tool_name": "Edit", "tool_input": {"file_path": f"/abs/{CANONICAL}/x"}},
    {"tool_name": "Glob", "tool_input": {"pattern": f"{CANONICAL}/**"}},
    {"tool_name": "NotebookEdit", "tool_input": {"notebook_path": f"{CANONICAL}/k.ipynb"}},
]


@pytest.mark.parametrize("hook", [HOOK_1, HOOK_2], ids=["guard-golden-answer", "guard-sealed-key"])
@pytest.mark.parametrize("payload", TARGETING, ids=range(len(TARGETING)))
def test_both_hooks_deny_a_call_that_targets_either_spelling(hook, payload):
    assert run_hook(hook, payload) == 2, (
        f"{hook.name} ALLOWED a tool call targeting a sealed-key path. "
        "A guard that stops matching one spelling reads exactly like one that works."
    )


# The shell surface. `guard-sealed-key.sh` must deny all of these; the first
# hook denies the first three and is DOCUMENTED as missing the bare plural.
SHELL_BOTH = [
    f"cat {CANONICAL}/set-1.jsonl",
    f"cat {LEGACY}/answers.jsonl",
    f"wc -l {LEGACY}/",
]
SHELL_PLURAL_ONLY = [
    "cat golden-answers/set-1.jsonl",
    "python -c \"open('golden-answers/k.jsonl')\"",
    "ls golden-answers",
]


@pytest.mark.parametrize("command", SHELL_BOTH + SHELL_PLURAL_ONLY)
def test_the_second_hook_denies_every_shell_form_on_both_spellings(command):
    payload = {"tool_name": "Bash", "tool_input": {"command": command}}
    assert run_hook(HOOK_2, payload) == 2, (
        "guard-sealed-key.sh ALLOWED a shell command reaching a sealed-key path. "
        "Closing exactly this gap is the only reason that hook exists."
    )


@pytest.mark.parametrize("command", SHELL_BOTH)
def test_the_first_hook_still_denies_the_shell_forms_it_always_did(command):
    payload = {"tool_name": "Bash", "tool_input": {"command": command}}
    assert run_hook(HOOK_1, payload) == 2


@pytest.mark.parametrize("command", SHELL_PLURAL_ONLY)
def test_the_first_hooks_bash_gap_is_asserted_rather_than_assumed(command):
    """The gap that `guard-sealed-key.sh` exists to close, pinned as a fact.

    🔴 **This test asserting ALLOW is not an endorsement.** It records the
    measured behaviour of a hook no Claude session can amend -- it refuses
    every edit to its own path -- so that the reason the second hook exists
    cannot quietly stop being true. **If this test ever fails, the first hook
    has been widened by a human and the second one may be reconsidered**;
    until then, coverage of these three forms rests entirely on
    ``guard-sealed-key.sh`` and on ``permissions.deny``.
    """
    payload = {"tool_name": "Bash", "tool_input": {"command": command}}
    assert run_hook(HOOK_1, payload) == 0


# Paths that merely CONTAIN the name inside a longer filename. None is a key,
# and the first hook's substring TARGET check denies every one of them -- which
# is why the work item that manages the directory cannot be edited by any Claude
# session, and why the guard's own file cannot either.
NOT_A_KEY = [
    ".claude/hooks/guard-golden-answer.sh",
    "work/open/W-198-golden-answers-canonical.md",
    "tests/test_golden_key_guards.py",
    "records/0012_LAW-11-sealed-answer-key.md",
]


@pytest.mark.parametrize("rel", NOT_A_KEY)
def test_the_second_hook_does_not_block_a_file_merely_named_after_the_rule(rel):
    """Anchored to a path component, exactly as the committed-key gate is.

    That gate's first draft used a substring, immediately flagged
    ``guard-golden-answer.sh`` -- one of the guards -- and was anchored for
    precisely this reason. The same anchoring is applied here so the sixth
    guard does not inherit a false positive that already has a precedent
    against it.
    """
    payload = {"tool_name": "Edit", "tool_input": {"file_path": rel}}
    assert run_hook(HOOK_2, payload) == 0, (
        f"guard-sealed-key.sh blocked `{rel}`, which is not a key. A guard whose "
        "false positives include the records and work items that govern it is a "
        "guard people route around."
    )


@pytest.mark.parametrize("rel", NOT_A_KEY[:2])
def test_the_first_hooks_target_false_positive_is_asserted_rather_than_assumed(rel):
    """🔴 Asserted as a measured fact, not endorsed.

    ``guard-golden-answer.sh`` substring-matches TARGETS, so it refuses every
    edit to its own file and to ``W-198-golden-answers-canonical.md``. **That
    makes both unmaintainable by any Claude session** — the W-198 build of
    2026-09-20 could not write its own closing note into its own item file and
    recorded it in ``work/IMPLEMENTATION.md`` instead. Filed for Arpit, because
    the one-line fix is an edit to a file the hook will not let an agent touch.

    If this test ever fails, a human has anchored that hook and the note in
    W-198 §Built should be revisited.
    """
    payload = {"tool_name": "Edit", "tool_input": {"file_path": rel}}
    assert run_hook(HOOK_1, payload) == 2


def test_a_hook_never_blocks_prose_about_the_rule():
    """Writing about the law is legal and necessary -- L11 decision 12.

    Every record, test and commit message in this repo names the path. A guard
    that blocked that would make the law undocumentable.
    """
    for hook in (HOOK_1, HOOK_2):
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "test -x .claude/hooks/guard-golden-answer.sh"},
        }
        assert run_hook(hook, payload) == 0, (
            f"{hook.name} blocks a command naming the GUARD's own filename. "
            "That is the false positive the first hook was already shaped around."
        )


# --- .claude/settings.json --------------------------------------------------


def deny_rules() -> list[str]:
    return json.loads(SETTINGS.read_text(encoding="utf-8"))["permissions"]["deny"]


@pytest.mark.parametrize(
    "tool", ["Read", "Edit", "Write", "MultiEdit", "NotebookEdit", "Glob", "Grep"]
)
def test_every_file_tool_is_denied_on_both_spellings(tool):
    """`**/golden-answer/**` does NOT match `golden-answers/`. The glob must be
    `golden-answer*/**`, which is exactly the narrowing this test exists for."""
    rules = deny_rules()
    assert f"{tool}(**/golden-answer*/**)" in rules, (
        f"{tool} has no deny rule covering BOTH spellings. "
        f"`{tool}(**/golden-answer/**)` matches the singular only."
    )


@pytest.mark.parametrize(
    "cmd",
    ["cat", "ls", "head", "tail", "grep", "rg", "find", "wc", "shasum", "md5", "cp", "mv", "rm", "open"],
)
def test_every_named_shell_command_is_denied(cmd):
    """These are substring patterns, so `*golden-answer*` already reaches the
    plural. Asserted so a later tidy-up to a glob form cannot silently drop it."""
    assert f"Bash({cmd}:*golden-answer*)" in deny_rules()


def test_both_hooks_are_registered_as_pretooluse_guards():
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    commands = [
        h["command"]
        for group in settings["hooks"]["PreToolUse"]
        for h in group["hooks"]
    ]
    for hook in (HOOK_1, HOOK_2):
        assert any(hook.name in c for c in commands), (
            f"{hook.name} exists but is not registered in settings.json. "
            "An unregistered hook is a file, not a guard."
        )


# --- .gitignore and .fux/sources/dirs ---------------------------------------


def test_git_ignores_both_spellings():
    """Answered by `git check-ignore`, which reads git's rules and not the disk.

    Never committed is the ONE half of L11 a machine can decide, and it is the
    half that decides whether a leak is an incident or is permanent.
    """
    for rel in (CANONICAL, LEGACY, "Claude outputs/golden-answers"):
        proc = subprocess.run(
            ["git", "check-ignore", "-q", rel], cwd=ROOT, capture_output=True
        )
        assert proc.returncode == 0, (
            f"`{rel}` is NOT gitignored. A key there is one `git commit -a` from "
            "being in history permanently and in every clone."
        )


def test_fux_never_indexes_the_key():
    """fux's own corpus excludes the sealed benchmark -- its parent and both
    spellings explicitly, so narrowing the parent line cannot open the key."""
    text = DIRS.read_text(encoding="utf-8")
    assert "!work/golden" in text
    for rel in (CANONICAL, LEGACY):
        assert f"!{rel}" in text, f"`{rel}` is not excluded from .fux/sources/dirs by name"
