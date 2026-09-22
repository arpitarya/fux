"""The L11 hooks fire on a shell command's PROSE, and that is accepted, not a bug.

[W-209](../work/open/W-209-l11-hook-prose-convention.md), ruled by Arpit on
2026-09-21: the guards are **not narrowed and not widened**. What is added is a
convention — *prose that must spell a key path is written with the Write/Edit
tool, never through a shell command* — stated once in
[SR-WORK-GOLDEN](../records/0066_WORK-golden.md) decision 7, and this file is its
gate.

**The class, and why it needed a gate rather than a fix.** Both guards grep a
`Bash` command's whole text for the key directory's name, so a heredoc or a
`python -c` that merely *writes prose* naming the path is refused — while the
same prose through the Write/Edit tool passes, because those calls are checked by
`file_path` alone. Recorded four times before it was ruled on; the fourth is
[the 2026-09-21 ladder rebuild](../work/regression/2026-09-21-ladder-set-3-rebuild/ANALYSIS.md)
§6. **Two strikes → a gate** ([SR-WORK-SESSION](../records/0060_WORK-session.md)
decision 13), and this is the gate.

🔴 **It pins a behaviour in both directions.** The Bash denial is asserted so a
later "usability" narrowing cannot land silently; the Write allowance is asserted
so a later widening cannot make the law undocumentable. Either assertion going
red means a guard moved, and a guard moves only on Arpit's ruling.

🔴 **This test opens nothing.** It feeds *synthetic* payloads to the two hooks as
subprocesses; no path under either spelling is read, listed, stat'd or globbed.

⚠ **It asserts the LOCKED state.** Under
[W-204](../work/open/W-204-golden-outputs-scoring-and-version-benchmark.md)'s
switch the guards can be turned off by `just golden-unlock`, and every assertion
here describes the guards as committed — which is what `just golden-lock`
restores. `tests/test_golden_key_guards.py` owns the both-states question; this
file owns the prose question and runs against the committed bytes.

**The probe is imported, never copied.** `test_golden_key_guards.py` carries a
`bash` probe that exists because a Windows runner answers with a WSL stub that
exits 1 without running anything — every guard assertion then reads as *ALLOWED*.
A second copy of that workaround is two things that could disagree while both
looking correct, so this module imports it; its module-level skip propagates
through the import and covers this file with the same honest message.
"""

from __future__ import annotations

import pytest

from test_golden_key_guards import (  # noqa: F401  (import triggers the shared skip)
    CANONICAL,
    HOOK_1,
    HOOK_2,
    LEGACY,
    run_hook,
    unlocked,
)

# 🔴 **The LOCKED state, and now that is a thing that can be false.**
# W-209 said so when the file was written — *"under W-204's switch the test runs
# against the locked state"* — and [L11](../records/0012_LAW-11-sealed-answer-key.md)
# decision 14 built the switch. While the tree is unlocked the two hooks are
# deregistered, so a `Bash` command spelling a key path is **allowed**, and every
# assertion here describes a tree that is not the one on disk.
#
# ⚠ **A skip, not a rewrite.** The convention this file gates — *prose that must
# spell a key path goes through Write/Edit* — is about what a session does on an
# ordinary day, and an ordinary day is locked. Rewriting the assertions to
# "whatever the hooks do right now" would make the file agree with the tree
# instead of with the rule, which is the opposite of a gate.
pytestmark = pytest.mark.skipif(
    unlocked(),
    reason=(
        "this tree is UNLOCKED (L11 decision 14): the hooks are deregistered by "
        "design, so the prose convention has nothing to enforce. `just golden-lock` "
        "and this file describes the tree again."
    ),
)

BOTH_HOOKS = pytest.mark.parametrize(
    "hook", [HOOK_1, HOOK_2], ids=["guard-golden-answer", "guard-sealed-key"]
)


# --- 1 · a shell command that only WRITES PROSE is still refused -------------

# Each of these writes a *document about the rule*. None reads, lists or creates
# anything under a key path — and every one is denied, because a guard that tried
# to tell prose from access would be guessing at the one thing it must not guess
# at. The convention exists so nobody needs it to.
PROSE_THROUGH_A_SHELL = [
    pytest.param(
        f"cat > work/golden/README.md <<'EOF'\nThe key lives in {CANONICAL}/.\nEOF",
        id="heredoc",
    ),
    pytest.param(
        f'python3 -c "print(\'the key directory is {CANONICAL}\')"',
        id="python-c",
    ),
    pytest.param(
        f"echo 'never open {LEGACY}/' >> work/NOW.md",
        id="echo-append-legacy",
    ),
    pytest.param(
        f"git commit -m 'docs: name {CANONICAL} in the record'",
        id="commit-message",
    ),
]


@BOTH_HOOKS
@pytest.mark.parametrize("command", PROSE_THROUGH_A_SHELL)
def test_a_shell_command_naming_a_key_path_is_denied_even_when_it_only_writes_prose(
    hook, command
):
    """🔴 Asserted as the ruled behaviour, not as a defect.

    Arpit, 2026-09-21: the hook is **not narrowed**. If this ever goes green as
    an ALLOW, someone has taught a guard to distinguish prose from access by
    inspecting a shell command — the judgement call the whole guard design
    refuses to make.
    """
    assert run_hook(hook, {"tool_name": "Bash", "tool_input": {"command": command}}) == 2, (
        f"{hook.name} ALLOWED a shell command spelling a key path. The guards were "
        "ruled unnarrowed on 2026-09-21; the convention is to use Write/Edit, not "
        "to teach the hook what prose looks like."
    )


# --- 2 · the same prose through Write/Edit passes ---------------------------

# This is the route the convention names. The payloads carry the key path in
# their CONTENT and a perfectly ordinary path in `file_path`; the guards check
# targets, so they allow it — which is what makes the law documentable at all.
PROSE_THROUGH_WRITE = [
    pytest.param(
        {
            "tool_name": "Write",
            "tool_input": {
                "file_path": "work/golden/README.md",
                "content": f"# Golden\n\nThe one permitted key home is `{CANONICAL}/`.\n",
            },
        },
        id="write-readme",
    ),
    pytest.param(
        {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "records/0066_WORK-golden.md",
                "old_string": "the key directory",
                "new_string": f"`{CANONICAL}/` (and the older `{LEGACY}/`)",
            },
        },
        id="edit-record",
    ),
]


@BOTH_HOOKS
@pytest.mark.parametrize("payload", PROSE_THROUGH_WRITE)
def test_the_same_prose_through_write_or_edit_is_allowed(hook, payload):
    """The convention's other half — and the half that keeps L11 writable.

    Every record, README, work item and test in this repository names the path.
    A guard that refused this would leave the law with no legal way to state
    itself, which is the failure mode SR-WORK-GOLDEN decision 7 names.
    """
    assert run_hook(hook, payload) == 0, (
        f"{hook.name} blocked prose about the rule carried in a Write/Edit "
        f"CONTENT field. `{payload['tool_input']['file_path']}` is not a key, and "
        "the convention W-209 ruled depends on this route staying open."
    )


# --- 3 · targeting a key path is denied, whichever spelling -----------------


@BOTH_HOOKS
@pytest.mark.parametrize(
    "file_path",
    [
        f"{CANONICAL}/set-1.jsonl",
        f"{LEGACY}/answers.jsonl",
        f"/Users/arpit/my_programs/fux/{CANONICAL}/set-2.jsonl",
    ],
    ids=["canonical", "legacy", "absolute"],
)
def test_a_read_that_targets_either_spelling_is_denied(hook, file_path):
    """The thing the convention must never be confused with.

    Allowing prose is not a crack in the wall: a call that *targets* a key path
    is refused on both spellings, relative or absolute, by both guards. This is
    the assertion that makes the two above safe to have.
    """
    assert run_hook(hook, {"tool_name": "Read", "tool_input": {"file_path": file_path}}) == 2, (
        f"{hook.name} ALLOWED a Read targeting `{file_path}`. That is the breach "
        "L11 exists to prevent, and it does not fail loudly anywhere else."
    )
