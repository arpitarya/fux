"""The third sealed-key guard refuses a recursive walk that can reach the golden tree.

[W-223](../work/open/W-223-l11-breach-2026-09-25.md), ruled by Arpit on
2026-09-27 (*"implement the hard guard"*). On 2026-09-25 a ``grep -rln`` from
the repo root named nothing under ``work/golden/``, filtered its OUTPUT, and
still read every file there. The two guards that check what a call NAMES could
not see it. ``.claude/hooks/guard-golden-traversal.sh`` refuses a recursive
walker (grep -r, rg, ag, ack, fd, find, tree, ls -R) whose root can reach the
tree — the repo root, ``work/``, ``work/golden/``, ``..``, ``~``, an absolute
ancestor, or no path while cwd is one of those — unless the command carries a
golden exclusion.

🔴 **It pins both directions.** The denials are the breach and its cousins; the
allowances are the ordinary reading SR-WORK-GOLDEN once said such a hook would
have to block (*"every grep over work/"*). Either going red means the guard
moved, and a guard moves only on Arpit's ruling.

🔴 **This test opens nothing.** It feeds synthetic payloads to the hook as a
subprocess. The bash/jq probe and its honest skip are imported, never copied.
"""

from __future__ import annotations

import json
import subprocess

import pytest

from test_golden_key_guards import BASH, ROOT, SETTINGS, hook_argv  # noqa: F401 — the probe's skip propagates

HOOK = ROOT / ".claude" / "hooks" / "guard-golden-traversal.sh"


def run(command: str, cwd_rel: str = "") -> int:
    cwd = ROOT / cwd_rel if cwd_rel else ROOT
    # POSIX spelling on every OS: the hook compares with `/`, and a Windows
    # backslash path fails it closed (safe, but not what this pins).
    payload = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": cwd.as_posix()}
    proc = subprocess.run(
        hook_argv(HOOK),
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=ROOT,
        env={"CLAUDE_PROJECT_DIR": ROOT.as_posix(), "PATH": __import__("os").environ.get("PATH", "")},
    )
    return proc.returncode


DENIED = [
    ('grep -rln "W-222" . --exclude-dir=.git --exclude-dir=archive | grep -v golden', ""),  # the 2026-09-25 breach
    ("grep -rn foo", ""),
    ("grep -R foo ./", ""),
    ('grep -rE "a|b" .', ""),
    ("rg foo", ""),
    ("rg foo work", ""),
    ("rg -l foo ~", ""),
    ('find . -name "*.md"', ""),
    ("ls -R work", ""),
    ("tree", ""),
    ("fd md", ""),
    ("grep -r foo work/golden", ""),
    ("grep -rn foo .", "work"),
    ("grep -rn foo ..", "src"),
    ("cd work && grep -r x ../", ""),
    ("echo $(grep -r x .)", ""),
    # W-227 — the 2026-09-27 shape: a data heredoc, then the walk on a later line.
    (
        "cd /tmp && git mv a b && python3 - <<'EOF'\nimport os\nprint(os.getcwd())\nEOF\n"
        "grep -n foo work/OPEN-WORK.md\n"
        'grep -rn "open/W-226" work records docs src CLAUDE.md 2>/dev/null | grep -v "^work/golden"',
        "",
    ),
    # W-230 — a heredoc ended early by a body line that is exactly its terminator.
    ("cat >> t.py <<'EOF'\nx = '''\nEOF\ngrep -rn probe work\n'''\nEOF", ""),
    # W-230 — a `<<EOF` inside quotes is text, and must not hide the next line.
    ('echo "x <<EOF"\ngrep -rn probe work', ""),
    ("bash <<'EOF'\ngrep -rn x work\nEOF", ""),  # a body fed to a shell is commands
    ("false && grep -rn probe work", ""),  # the W-230 live probe
]

ALLOWED = [
    ("grep -rn foo . --exclude-dir=golden", ""),
    ("grep -rn foo --exclude-dir={.git,golden} .", ""),
    ("rg foo -g '!work/golden/**'", ""),
    ('find . -path ./work/golden -prune -o -name "*.md" -print', ""),
    (r"find . \( -path ./work/golden -prune \) -o -name x -print", ""),
    ('find . -not -path "*/golden/*" -name x', ""),
    ("fd md -E golden", ""),
    ("grep -rn foo src tests", ""),
    ('grep -rE "a|b" src', ""),
    ("rg -t py foo src", ""),
    ("grep -rn foo work/open work/regression", ""),
    ("grep -r foo work/golden/prompts", ""),
    ('find records -name "*.md"', ""),
    ("grep -n foo work/OPEN-WORK.md", ""),
    ("ls work", ""),
    ("git grep foo", ""),
    ("grep -rn foo .", "src"),
    ("grep -rn -A 3 foo records 2>/dev/null | head", ""),
    ('echo "use grep -r . to search"', ""),
    ("uv run pytest -q tests", ""),
    ("grep -rn foo work --exclude-dir=golden", ""),
    ("python3 - <<'EOF'\n# find . ; grep -r x .\nprint(1)\nEOF", ""),  # a data body is not shell
]


@pytest.mark.parametrize("command,cwd", DENIED)
def test_a_walk_that_can_reach_the_tree_is_denied(command, cwd):
    assert run(command, cwd) == 2, f"guard-golden-traversal.sh ALLOWED `{command}` from `{cwd or '.'}`"


@pytest.mark.parametrize("command,cwd", ALLOWED)
def test_ordinary_reading_is_not_blocked(command, cwd):
    assert run(command, cwd) == 0, (
        f"guard-golden-traversal.sh blocked `{command}` from `{cwd or '.'}`. "
        "A gate that fires wrongly is worse than one that does not fire."
    )


@pytest.mark.parametrize("expected,command", [(0, "sed -i '' 's/🟡 x/🟢 x/' work/OPEN-WORK.md"), (2, "echo 🟡 && grep -rn x work")])
def test_a_utf8_locale_does_not_change_the_verdict(expected, command):
    """W-230: a live session has LANG=…UTF-8 and this suite had none. macOS awk
    died on a 4-byte character there, and fail-closed made that a deny."""
    payload = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(ROOT)}
    env = {"CLAUDE_PROJECT_DIR": str(ROOT), "PATH": __import__("os").environ.get("PATH", ""), "LANG": "en_US.UTF-8", "LC_ALL": "en_US.UTF-8"}
    proc = subprocess.run(hook_argv(HOOK), input=json.dumps(payload), capture_output=True, text=True, cwd=ROOT, env=env)
    assert proc.returncode == expected, proc.stderr


def test_it_fails_closed_on_a_payload_it_cannot_parse():
    proc = subprocess.run(hook_argv(HOOK), input="not json grep -r x .", capture_output=True, text=True, cwd=ROOT)
    assert proc.returncode == 2


def test_a_non_shell_tool_is_not_its_business():
    payload = {"tool_name": "Read", "tool_input": {"file_path": "README.md"}}
    proc = subprocess.run(hook_argv(HOOK), input=json.dumps(payload), capture_output=True, text=True, cwd=ROOT)
    assert proc.returncode == 0


def test_it_is_registered_and_the_switch_knows_it():
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    commands = [h["command"] for g in settings["hooks"]["PreToolUse"] for h in g["hooks"]]
    assert any(HOOK.name in c for c in commands), "registered nowhere — a file, not a guard"
    switch = (ROOT / "tools" / "golden-switch" / "switch.py").read_text(encoding="utf-8")
    assert HOOK.name in switch, "golden-unlock would leave it up, and golden-lock could not promise a restore"
