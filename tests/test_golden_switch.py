"""The sealed-key switch — what it takes down, what it never touches, and the
one promise `lock` makes: **a byte-identical restore.**

[L11](../records/0012_LAW-11-sealed-answer-key.md) decision 14 (Arpit,
2026-09-21). The switch is the first thing in this repository that can turn a
**law's** enforcement off, so the questions this file asks are narrow and
uncomfortable on purpose:

1. does `unlock` remove **every** read guard, or only the ones somebody listed?
2. does it leave `.gitignore` and `.fux/sources/dirs` alone — because *never
   committed* is the one clause no state relaxes?
3. does `lock` restore **the same bytes**, and refuse rather than guess when it
   cannot?
4. does the whole thing refuse an agent's shell?

🔴 **Every test here runs against a COPY of `.claude/settings.json` in a
`tmp_path`.** Nothing in this file unlocks the real tree — a test suite that
could would be a route around the law that runs on every CI job, which is
precisely the shape decision 14 warns about. The module constants are
monkeypatched, and `test_the_real_tree_is_untouched` asserts the obvious thing
afterwards.

🔴 **It opens no key path.** `retire` is exercised against a synthetic key
directory in `tmp_path`, not the real one, and the real one is never read,
listed or stat'd.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SWITCH_PATH = ROOT / "tools" / "golden-switch" / "switch.py"
REAL_SETTINGS = ROOT / ".claude" / "settings.json"


def locked_settings() -> bytes:
    """The **committed** `.claude/settings.json` — always the locked shape.

    🔴 **Read from git, never from the working tree, and that is a defect this
    file already shipped once.** The first version copied
    `.claude/settings.json` off disk, with a docstring arguing that the real
    file was the honest input. It is — right up to the moment
    `just golden-unlock` runs, which is a thing **this very program does**. On
    the first genuinely unlocked tree, seven tests failed with *"found no guard
    to remove"*: the fixture had been handed an already-open settings file and
    `unlock` correctly refused it.

    **A fixture that reads state its own subject can mutate is a fixture whose
    meaning changes underneath it.** git's copy cannot be unlocked, so these
    tests describe the same thing on a locked tree, an unlocked one, and a
    checkout in either state.
    """
    out = subprocess.run(
        ["git", "-C", str(ROOT), "show", "HEAD:.claude/settings.json"],
        capture_output=True, check=True,
    ).stdout
    assert out.count(b"golden-answer") >= 14, (
        "the COMMITTED settings.json has fewer than 14 rules naming the key. "
        "Either an unlocked settings.json was committed — which is a breach to "
        "declare — or the guards were narrowed at HEAD."
    )
    return out


def _load_switch():
    """Import the program by path — `tools/` is not a package."""
    spec = importlib.util.spec_from_file_location("golden_switch", SWITCH_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["golden_switch"] = module
    spec.loader.exec_module(module)
    return module


switch = _load_switch()


@pytest.fixture
def tree(tmp_path, monkeypatch):
    """A throwaway repo shaped like this one, with the COMMITTED settings copied in.

    **The real `settings.json` is the fixture's input on purpose** — a synthetic
    one with three tidy rules would let `unlock` pass while failing on the file
    it actually has to handle: 29 deny rules, two hook registrations inside one
    of two `PreToolUse` groups, and a third hook (`session-lock.sh`) that must
    survive. ⚠ **But the COMMITTED one, not the working tree's** — see
    `locked_settings`.
    """
    claude = tmp_path / ".claude"
    claude.mkdir()
    settings = claude / "settings.json"
    settings.write_bytes(locked_settings())

    state_dir = claude / ".golden-lock"
    monkeypatch.setattr(switch, "ROOT", tmp_path)
    monkeypatch.setattr(switch, "SETTINGS", settings)
    monkeypatch.setattr(switch, "STATE_DIR", state_dir)
    monkeypatch.setattr(switch, "STATE_FILE", state_dir / "STATE")
    monkeypatch.setattr(switch, "STASHED_SETTINGS", state_dir / "settings.json")
    monkeypatch.setattr(switch, "STASHED_SHA", state_dir / "settings.sha256")
    monkeypatch.setattr(switch, "KEY_DIR", tmp_path / "work" / "golden" / "golden-answers")
    monkeypatch.setattr(switch, "QUESTIONS", tmp_path / "work" / "golden" / "questions")
    monkeypatch.setattr(switch, "RETIRED", tmp_path / "work" / "golden" / "retired")
    # Not an agent's shell, for the tests that are not about that check.
    monkeypatch.delenv("CLAUDECODE", raising=False)
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    return tmp_path


def _deny(settings_path: Path) -> list[str]:
    return json.loads(settings_path.read_text(encoding="utf-8"))["permissions"]["deny"]


def _hook_commands(settings_path: Path) -> list[str]:
    data = json.loads(settings_path.read_text(encoding="utf-8"))
    return [
        h["command"]
        for group in data.get("hooks", {}).get("PreToolUse", [])
        for h in group.get("hooks", [])
    ]


# --- the tripwire -----------------------------------------------------------


@pytest.mark.parametrize("var", ["CLAUDECODE", "CLAUDE_CODE_SESSION_ID"])
@pytest.mark.parametrize("verb", ["unlock", "lock", "retire"])
def test_every_mutating_verb_refuses_an_agents_shell(tree, monkeypatch, var, verb):
    """🔴 A tripwire, and this test says so rather than calling it a guarantee.

    An agent that scrubs its own environment defeats it in one line. What binds
    that agent is L11 decision 14's sentence — *no agent runs it, by any route* —
    and the reason this check exists anyway is that the honest failure mode is
    somebody typing `just golden-unlock` into an integrated terminal without
    thinking about which shell they are in.
    """
    monkeypatch.setenv(var, "1")
    argv = [verb] if verb != "retire" else [verb, "set-1"]
    with pytest.raises(SystemExit) as exit_info:
        switch.main(argv)
    assert "Claude Code session" in str(exit_info.value)


def test_state_is_readable_by_anyone_and_opens_nothing(tree, capsys):
    """`state` is the one verb an agent may run: it reads one file under `.claude/`."""
    assert switch.main(["state"]) == 0
    assert capsys.readouterr().out.strip() == "locked"


# --- unlock -----------------------------------------------------------------


def test_unlock_removes_every_deny_rule_that_names_the_key(tree):
    before = _deny(switch.SETTINGS)
    assert sum(1 for r in before if switch.MARKER in r) > 10, "fixture sanity"

    assert switch.main(["unlock"]) == 0

    after = _deny(switch.SETTINGS)
    assert not [r for r in after if switch.MARKER in r], (
        "unlock left a deny rule naming the key. It matches on the marker rather "
        "than on a list precisely so this cannot happen — a list is one more thing "
        "to keep in step with settings.json."
    )


def test_unlock_deregisters_both_hooks_and_leaves_the_third_alone(tree):
    assert switch.main(["unlock"]) == 0
    commands = _hook_commands(switch.SETTINGS)
    for name in switch.HOOK_NAMES:
        assert not any(name in c for c in commands), f"{name} is still registered"
    assert any("session-lock.sh" in c for c in commands), (
        "session-lock.sh is the per-asset write lock (SR-WORK-BLOCKERS) and has "
        "nothing to do with the sealed key. An unlock that took it down would be "
        "removing a guard nobody asked about."
    )


def test_unlock_never_edits_or_moves_the_hook_FILES(tree):
    """🔴 Deregistered, never touched — which is what makes `lock`'s promise cheap.

    `lock` can guarantee a byte-identical restore of the hook files precisely
    because `unlock` never changed them. The only mutated file is
    `settings.json`.
    """
    hooks = ROOT / ".claude" / "hooks"
    before = {p.name: p.read_bytes() for p in hooks.glob("*.sh")}
    assert switch.main(["unlock"]) == 0
    after = {p.name: p.read_bytes() for p in hooks.glob("*.sh")}
    assert before == after


def test_unlock_is_refused_twice(tree, capsys):
    assert switch.main(["unlock"]) == 0
    assert switch.main(["unlock"]) == 1
    assert "already unlocked" in capsys.readouterr().err


def test_unlock_refuses_when_it_recognises_no_guard(tree):
    """A settings file with nothing to take down is either already open by some
    other route — a breach — or a shape this program no longer understands.
    **Both are stop conditions, and neither is "carry on".**"""
    switch.SETTINGS.write_text(json.dumps({"permissions": {"deny": []}, "hooks": {}}), encoding="utf-8")
    with pytest.raises(SystemExit) as exit_info:
        switch.main(["unlock"])
    assert "no guard to remove" in str(exit_info.value)


# --- lock -------------------------------------------------------------------


def test_lock_restores_the_exact_bytes(tree):
    """🔴 The one promise this switch makes, asserted as a digest.

    Not *"the rules are back"* — **the same bytes**. A settings file that came
    back semantically equal but formatted differently would pass a shallow check
    and quietly rewrite a file three other records describe.
    """
    original = switch.SETTINGS.read_bytes()
    assert switch.main(["unlock"]) == 0
    assert switch.SETTINGS.read_bytes() != original, "fixture sanity: unlock changed it"

    assert switch.main(["lock"]) == 0
    assert switch.SETTINGS.read_bytes() == original
    assert hashlib.sha256(switch.SETTINGS.read_bytes()).hexdigest() == hashlib.sha256(original).hexdigest()
    assert not switch.STATE_DIR.exists(), "the state directory goes with the lock"


def test_lock_refuses_a_tampered_stash_rather_than_overwriting(tree):
    """**A stash that no longer matches its digest is a breach to declare.**

    The wrong move here is the tempting one: write whatever is in the stash and
    report success. That silently installs somebody else's settings file under
    the name of a restore.
    """
    assert switch.main(["unlock"]) == 0
    switch.STASHED_SETTINGS.write_text('{"permissions": {"deny": []}}', encoding="utf-8")
    with pytest.raises(SystemExit) as exit_info:
        switch.main(["lock"])
    assert "does not match its own digest" in str(exit_info.value)


def test_lock_refuses_an_incomplete_stash(tree):
    assert switch.main(["unlock"]) == 0
    switch.STASHED_SHA.unlink()
    with pytest.raises(SystemExit) as exit_info:
        switch.main(["lock"])
    assert "stash is incomplete" in str(exit_info.value)


def test_lock_on_a_locked_tree_is_a_no_op_that_says_so(tree, capsys):
    assert switch.main(["lock"]) == 1
    assert "already locked" in capsys.readouterr().err


# --- retire -----------------------------------------------------------------


def test_retire_is_refused_while_locked(tree):
    """Retiring moves answers, which is reaching into the key directory."""
    with pytest.raises(SystemExit) as exit_info:
        switch.main(["retire", "set-1"])
    assert "LOCKED" in str(exit_info.value)


def test_retire_moves_questions_and_answers_together(tree):
    switch.QUESTIONS.mkdir(parents=True)
    switch.KEY_DIR.mkdir(parents=True)
    (switch.QUESTIONS / "set-1.jsonl").write_text('{"id":"s1-001"}\n', encoding="utf-8")
    (switch.KEY_DIR / "set-1.jsonl").write_text('{"id":"s1-001"}\n', encoding="utf-8")

    assert switch.main(["unlock"]) == 0
    assert switch.main(["retire", "set-1"]) == 0

    dest = switch.RETIRED / "set-1"
    assert (dest / "questions.jsonl").is_file()
    assert (dest / "expected.jsonl").is_file()
    assert not (dest / "answers.jsonl").exists(), (
        "the retired half must NOT be called answers.jsonl — `.gitignore` carries "
        "`**/answers.jsonl` so a key cannot be committed at any depth, and a "
        "retired set that lands on that name cannot reach the committed home "
        "decision 14 promises. See test_a_retired_set_can_actually_be_committed."
    )
    assert not (switch.QUESTIONS / "set-1.jsonl").exists(), "a set retires, it does not fork"
    assert not (switch.KEY_DIR / "set-1.jsonl").exists()
    readme = (dest / "README.md").read_text(encoding="utf-8")
    assert "no longer carries a golden claim" in readme, (
        "the retired tier's whole point is that these numbers stop being evidence; "
        "a directory that does not say so will be cited as a benchmark within a month"
    )


def test_retire_refuses_half_a_set(tree):
    """🔴 Questions without answers is how the retired tier becomes a second
    place where half a benchmark lives."""
    switch.QUESTIONS.mkdir(parents=True)
    switch.KEY_DIR.mkdir(parents=True)
    (switch.QUESTIONS / "set-9.jsonl").write_text("{}\n", encoding="utf-8")
    assert switch.main(["unlock"]) == 0
    with pytest.raises(SystemExit) as exit_info:
        switch.main(["retire", "set-9"])
    assert "retires WHOLE" in str(exit_info.value)


def test_retire_refuses_a_second_set_under_a_name_already_retired(tree):
    """A set retires ONCE, and the second attempt must not merge into the first.

    ⚠ **Re-running `retire` on the same name is normally caught one guard
    earlier** — the questions file has already moved, so it refuses on *no
    questions file* rather than on the destination. This test reaches the
    destination guard on purpose, by putting a *new* pair under the same name:
    that is the case that would otherwise overwrite a retired answer set, and
    it is the reason the check exists at all.
    """
    switch.QUESTIONS.mkdir(parents=True)
    switch.KEY_DIR.mkdir(parents=True)
    (switch.QUESTIONS / "set-2.jsonl").write_text("{}\n", encoding="utf-8")
    (switch.KEY_DIR / "set-2.jsonl").write_text("{}\n", encoding="utf-8")
    assert switch.main(["unlock"]) == 0
    assert switch.main(["retire", "set-2"]) == 0

    # A fresh pair arrives under the name that has already retired.
    (switch.QUESTIONS / "set-2.jsonl").write_text('{"id":"later"}\n', encoding="utf-8")
    (switch.KEY_DIR / "set-2.jsonl").write_text('{"id":"later"}\n', encoding="utf-8")
    with pytest.raises(SystemExit) as exit_info:
        switch.main(["retire", "set-2"])
    assert "already exists" in str(exit_info.value)
    assert (switch.RETIRED / "set-2" / "expected.jsonl").read_text(encoding="utf-8") == "{}\n", (
        "the first retirement's answers were overwritten by the second attempt"
    )


# --- the things no state relaxes -------------------------------------------


#: Anything that could touch a file. A line that names one of the never-relaxed
#: paths AND one of these is a line that reaches it; a line that only prints the
#: name is the switch telling the operator what it left alone.
_TOUCHES = ("Path(", "open(", "write_text", "write_bytes", "read_text", "read_bytes",
            "unlink", "mkdir", "shutil.", "rmtree", "replace(")


def test_the_switch_can_PRINT_the_never_relaxed_paths_but_never_reach_them():
    """🔴 *Never committed* is the one clause no state relaxes — L11.

    ⚠ **The first draft of this test forbade the substring outright and went red
    on the switch doing the right thing** — `unlock` prints *".gitignore and
    .fux/sources/dirs are UNTOUCHED"*, which is exactly the sentence an operator
    needs. The same mistake `tests/serve/test_page_computes_nothing.py` made
    about the word *stopword*: **naming a thing is not reaching it**, and a rule
    that cannot tell them apart punishes the honest version.

    So the check is on the *shape*: a line may say `.gitignore`, and it may not
    say `.gitignore` next to anything that opens a file. A future edit adding
    *"and relax the ignore rules while we are in here"* fails this before anybody
    reviews the diff.
    """
    source = SWITCH_PATH.read_text(encoding="utf-8")
    body = source.split('"""', 2)[-1]  # skip the module docstring, which explains them
    offenders = [
        line.strip()
        for line in body.splitlines()
        if any(never in line for never in (".gitignore", "sources/dirs"))
        and any(touch in line for touch in _TOUCHES)
    ]
    assert not offenders, (
        "the switch REACHES a path no state relaxes:\n  " + "\n  ".join(offenders)
        + "\n\nA key stays off every ref in both states. An unlock that can edit the "
        "ignore rules is not the switch L11 decision 14 describes."
    )


def test_a_retired_set_can_actually_be_committed():
    """🔴 *"A committed home"* has to mean git will take the files.

    **Found the hard way on 2026-09-22**, by Arpit running the real
    `just golden-retire` on all three sets. The switch reported success three
    times; `git check-ignore` then claimed every `answers.jsonl` under
    `**/answers.jsonl` — one of the guards, whose job is that a key file cannot
    be committed at **any** depth. So the retired tier moved correctly and
    **could not be committed**, which is the half of decision 14 that makes the
    retirement mean anything.

    ⚠ **The fix was the destination's NAME, not a hole in the guard.** Negating
    `**/answers.jsonl` for one directory would weaken a pattern that exists to
    catch a key anywhere; `expected.jsonl` leaves every guard exactly as it was
    and says the truer thing — these are expected values for ordinary tests, not
    answers to a sealed benchmark.

    **This test is the gate that class now owes.** It asks git, not the
    filesystem, and it runs against whatever is actually in the retired tier.
    """
    retired = ROOT / "work" / "golden" / "retired"
    if not retired.is_dir():
        pytest.skip("no set has been retired in this tree yet")
    files = [p for p in retired.rglob("*") if p.is_file()]
    assert files, "the retired tier exists but is empty"
    ignored = [
        p.relative_to(ROOT).as_posix()
        for p in files
        if subprocess.run(
            ["git", "-C", str(ROOT), "check-ignore", "-q", str(p)], capture_output=True
        ).returncode == 0
    ]
    assert not ignored, (
        "these retired files are GITIGNORED and cannot reach the committed home "
        "L11 decision 14 promises:\n  " + "\n  ".join(ignored)
        + "\n\nDo NOT negate the ignore rule — it guards against a key being "
        "committable at any depth. Rename the destination instead."
    )


def test_the_real_trees_state_is_SELF_CONSISTENT_whichever_it_is():
    """Every test above runs on a copy. This one looks at the actual repository.

    ⚠ **It cannot assert *locked*, and the first version did.** A deliberate
    `just golden-unlock` is a legitimate state — it is the whole point of the
    switch — so a test demanding a locked tree fails on a correct one, which is
    how a suite teaches people to ignore it.

    🔴 **What it CAN assert is that the two halves agree.** An unlocked tree with
    no stash cannot be closed again; a locked tree carrying a stash means a lock
    half-finished or something writing into the state directory. Both are breaches
    to declare, and neither is visible from either half alone.
    """
    state_dir = ROOT / ".claude" / ".golden-lock"
    stash = state_dir / "settings.json"
    live_rules = sum(1 for r in _deny(REAL_SETTINGS) if switch.MARKER in r)

    if switch.is_unlocked():
        assert stash.is_file(), (
            "this tree is UNLOCKED and the stash is gone — `just golden-lock` "
            "cannot restore byte-identically. Declare it."
        )
        assert live_rules == 0, (
            "unlocked, but deny rules naming the key are still in settings.json. "
            "The unlock did not finish, or something rewrote the file."
        )
    else:
        assert not state_dir.exists(), (
            "a LOCKED tree carrying a state directory — a lock half-finished, or "
            "a test leaking into the real repository. Declare it."
        )
        assert live_rules >= 14, "locked, and the deny rules have been narrowed"
