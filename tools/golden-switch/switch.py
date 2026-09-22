#!/usr/bin/env python3
"""The sealed-key switch — `just golden-unlock` / `golden-lock` / `golden-retire`.

🔴 **Read [L11](../../records/0012_LAW-11-sealed-answer-key.md) decision 14 before
this file.** Arpit ruled on 2026-09-21: *"Remove the checks through a just recipe
and then you can access everything. Once the testing is done, move the questions
somewhere they can be reused for regular testing, feature testing. Then lock it
again and create new test data."* This program is that switch; **the law is what
binds anyone near it**, and nothing here is a permission.

🔴 **NO AGENT RUNS THIS.** Not `unlock`, not `lock`, not `retire`, not directly,
not through a subagent, a hook, a skill or a script it wrote. **Creating,
editing, moving or deleting the state file below is the same breach as opening
the key**, because it *is* opening the key — and it is the one route the guards
cannot see, since a command named `just golden-unlock` contains none of the
strings the `Bash` deny patterns match. **The law covers that; nothing else
does.** If you are an agent and you need the key, say you are blocked and stop.

The environment check below is a **tripwire, not the rule** — the same shape
`tools/golden-score/score.py` carries under decision 13. An agent that scrubs its
own environment defeats it in one line, and is bound by the paragraph above.

## What `unlock` actually turns off, and what it deliberately does not

**Off:** the `permissions.deny` rules that name the key directory, and the two
`PreToolUse` hook registrations. That is the whole of what stands between a
Claude tool call and the key.

🔴 **Untouched, in both states, permanently:**

| guard | why it never moves |
|---|---|
| `.gitignore` | **never committed is the one clause no state relaxes** (L11). A key must stay off every ref whether the tree is open or shut |
| `!work/golden` in `.fux/sources/dirs` | the benchmark's vocabulary must not enter fux's own committed index either way |
| the two hook **files** | they are only *deregistered*, never edited or moved — which is what makes `lock` able to promise a byte-identical restore of something it never changed |
| `tools/golden-score/score.py`'s own refusals | decision 13's carve-out is a **different permission** and an unlock does not widen it |

**So exactly one file is mutated: `.claude/settings.json`.** `unlock` copies its
bytes into the state directory first, and `lock` puts those bytes back and
verifies the digest. A restore that does not match is reported as a breach to
declare rather than shrugged off — **a guard that comes back changed is not a
guard that came back.**

⚠ **Restoring from the stash, not from git, is deliberate.** `git checkout --
.claude/settings.json` would also revert any *unrelated* edit somebody made to
that file while the tree was open, silently. The stash restores exactly what was
taken and nothing else.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

#: The one permitted key home — [L11](../../records/0012_LAW-11-sealed-answer-key.md)
#: decision 3. Named here because a guard matches paths and an unnamed path is
#: one nothing can cover; the same reason the `justfile` names it.
KEY_DIR = ROOT / "work" / "golden" / "golden-answers"

#: Where a retired set lands — committed, ordinary regression data, readable by
#: any session in any state (decision 14).
RETIRED = ROOT / "work" / "golden" / "retired"

QUESTIONS = ROOT / "work" / "golden" / "questions"
SETTINGS = ROOT / ".claude" / "settings.json"

#: 🔴 **Gitignored, and it must stay that way.** It holds a copy of
#: `settings.json`, not a key — but a committed lock-state would put "this tree
#: is open" into history, and the state of a switch is a property of one machine
#: at one moment.
STATE_DIR = ROOT / ".claude" / ".golden-lock"
STATE_FILE = STATE_DIR / "STATE"
STASHED_SETTINGS = STATE_DIR / "settings.json"
STASHED_SHA = STATE_DIR / "settings.sha256"

#: The substring every deny rule and both hook filenames share. Matching on it
#: is what makes `unlock` remove *all* of them rather than a list somebody has to
#: keep in step with `settings.json`.
MARKER = "golden-answer"

HOOK_NAMES = ("guard-golden-answer.sh", "guard-sealed-key.sh")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _refuse_if_agent() -> None:
    """🔴 L11 decision 14 — the switch is Arpit's hand and no agent's.

    A tripwire, exactly as `score.py`'s is, and stated as one: an agent that
    scrubs its environment defeats it, and the law is what binds that agent.
    **A false positive here IS the true positive** — `just golden-unlock` typed
    into an agent's integrated terminal is precisely the case the ruling
    excludes.
    """
    if os.environ.get("CLAUDECODE") or os.environ.get("CLAUDE_CODE_SESSION_ID"):
        sys.exit(
            "refusing: this looks like a Claude Code session's shell.\n"
            "  LAW L11 decision 14 gives this switch to Arpit's own hand and to no\n"
            "  agent, by any route. Open a plain shell.\n"
            "  If you are an agent and you need the key: say you are blocked, and stop."
        )


def is_unlocked() -> bool:
    """The one question every other surface asks. **Opens no key path.**"""
    return STATE_FILE.is_file() and STATE_FILE.read_text(encoding="utf-8").strip() == "unlocked"


def _load_settings() -> tuple[bytes, dict]:
    raw = SETTINGS.read_bytes()
    return raw, json.loads(raw.decode("utf-8"))


def _strip_guards(settings: dict) -> tuple[dict, int, int]:
    """Return settings with the read guards removed, plus what was removed.

    **Matched on the marker, never on a list kept here.** A list would be one
    more thing to keep in step with `settings.json`, and the failure mode is a
    rule this program silently leaves in place while reporting the tree open.
    """
    out = json.loads(json.dumps(settings))  # a deep copy, cheaply

    deny = out.get("permissions", {}).get("deny", [])
    kept_deny = [rule for rule in deny if MARKER not in rule]
    removed_deny = len(deny) - len(kept_deny)
    out.setdefault("permissions", {})["deny"] = kept_deny

    removed_hooks = 0
    groups = out.get("hooks", {}).get("PreToolUse", [])
    kept_groups = []
    for group in groups:
        hooks = group.get("hooks", [])
        kept = [h for h in hooks if not any(name in h.get("command", "") for name in HOOK_NAMES)]
        removed_hooks += len(hooks) - len(kept)
        if kept:
            group = dict(group, hooks=kept)
            kept_groups.append(group)
        # ⚠ A group left with no hooks is DROPPED, not kept empty: an empty
        # matcher group is a shape the settings reader has no reason to expect,
        # and `lock` restores the original bytes anyway.
    if "hooks" in out:
        out["hooks"]["PreToolUse"] = kept_groups
    return out, removed_deny, removed_hooks


def cmd_unlock(_args) -> int:
    _refuse_if_agent()
    if is_unlocked():
        print("already unlocked — `just golden-lock` puts the guards back.", file=sys.stderr)
        return 1
    if not SETTINGS.is_file():
        sys.exit(f"refusing: {SETTINGS} is missing; there is nothing to take down safely.")

    raw, settings = _load_settings()
    opened, removed_deny, removed_hooks = _strip_guards(settings)
    if not removed_deny and not removed_hooks:
        sys.exit(
            "refusing: found no guard to remove. Either the tree is already open by\n"
            "  some other route — which is a breach to declare — or settings.json has\n"
            "  been restructured and this program no longer recognises it."
        )

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STASHED_SETTINGS.write_bytes(raw)
    STASHED_SHA.write_text(_sha(raw) + "\n", encoding="utf-8")
    SETTINGS.write_text(json.dumps(opened, indent=2) + "\n", encoding="utf-8")
    STATE_FILE.write_text("unlocked\n", encoding="utf-8")

    print("UNLOCKED.")
    print(f"  removed {removed_deny} deny rule(s) and {removed_hooks} hook registration(s)")
    print(f"  the previous settings.json is stashed at {STASHED_SETTINGS.relative_to(ROOT)}")
    print("  .gitignore and .fux/sources/dirs are UNTOUCHED — a key is never committed,")
    print("  in either state, and that clause does not move.")
    print()
    print("  Every number measured or scored from here is `informed` PERMANENTLY.")
    print("  When the scoring is done:  just golden-retire <set>   then   just golden-lock")
    return 0


def cmd_lock(_args) -> int:
    _refuse_if_agent()
    if not is_unlocked():
        print("already locked — nothing to restore.", file=sys.stderr)
        return 1
    if not STASHED_SETTINGS.is_file() or not STASHED_SHA.is_file():
        sys.exit(
            "refusing: the stash is incomplete, so a byte-identical restore cannot be\n"
            f"  promised. Restore {SETTINGS.relative_to(ROOT)} from git by hand, run\n"
            "  `just golden-guards`, and declare it."
        )

    raw = STASHED_SETTINGS.read_bytes()
    expected = STASHED_SHA.read_text(encoding="utf-8").strip()
    if _sha(raw) != expected:
        sys.exit(
            "refusing: the stashed settings.json does not match its own digest.\n"
            "  Something edited the stash while the tree was open. That is a breach to\n"
            "  declare, not a thing to overwrite."
        )

    SETTINGS.write_bytes(raw)
    if _sha(SETTINGS.read_bytes()) != expected:  # pragma: no cover - a write that did not take
        sys.exit("refusing: the restore did not land byte-identically. Declare it.")

    shutil.rmtree(STATE_DIR)
    print("LOCKED. settings.json restored byte-identically; the guards are back.")
    print("  verify with:  just golden-guards")
    print("  the next generation of test data is authored SEALED — `set-<gen>-<x|u>`.")
    return 0


def cmd_retire(args) -> int:
    """Move a scored set's questions AND answers into committed, reusable data.

    🔴 **This is the only way anything leaves L11** (decision 14). After it, that
    set is ordinary regression and feature-test data any session may read in any
    state — **and it never carries a golden claim again**, because the family
    that reads it also tunes against it.
    """
    _refuse_if_agent()
    if not is_unlocked():
        sys.exit(
            "refusing: the tree is LOCKED. Retiring a set moves its answers, which is\n"
            "  reaching into the key directory. `just golden-unlock` first."
        )

    name = args.set
    dest = RETIRED / name
    questions = QUESTIONS / f"{name}.jsonl"
    answers = KEY_DIR / f"{name}.jsonl"

    if not questions.is_file():
        sys.exit(f"refusing: no questions file at {questions.relative_to(ROOT)}")
    if not answers.is_file():
        sys.exit(
            f"refusing: no answers file for {name} in the permitted key directory.\n"
            "  A set retires WHOLE — questions and answers together — or the retired\n"
            "  tier becomes a second place where half a benchmark lives."
        )
    if dest.exists():
        sys.exit(f"refusing: {dest.relative_to(ROOT)} already exists; a set retires once.")

    dest.mkdir(parents=True)
    shutil.move(str(questions), dest / "questions.jsonl")
    # 🔴 **`expected.jsonl`, NOT `answers.jsonl`, and the name is the fix for a
    # real defect.** `.gitignore` carries `**/answers.jsonl` as one of the
    # guards — a key file must not be committable at any depth, under any
    # directory. The first version of this function moved the key to
    # `answers.jsonl`, which meant the "committed home" decision 14 promises
    # **could not be committed**: `git check-ignore` claimed it, silently, and
    # the retire looked like it had worked.
    #
    # The two available fixes were not equal. Negating the ignore rule for this
    # directory would punch a hole in a pattern whose whole job is to catch a
    # key file **anywhere**; renaming the destination leaves every guard exactly
    # as it was. **A guard you route around is a guard.**
    #
    # The name also says the right thing: these are expected values for ordinary
    # tests, not answers to a sealed benchmark. The rename is the semantic shift
    # decision 14 describes, made visible in the filesystem.
    shutil.move(str(answers), dest / "expected.jsonl")
    # ⚠ **Frontmatter with a `type`, because this tree is a declared OKF v0.1
    # bundle** and `tests/test_okf_bundle.py` requires one on every document.
    # The first version wrote a bare heading and put three files into the bundle
    # that could not declare what they were — found by the same real retire that
    # found the `answers.jsonl` collision.
    (dest / "README.md").write_text(
        "---\n"
        "type: Reference\n"
        f'description: "{name} — RETIRED golden data. Open, reusable regression and '
        'feature-test material; NOT a benchmark, and no number measured on it is '
        'evidence about the engine\'s quality."\n'
        "---\n\n"
        f"# {name} — RETIRED golden data\n\n"
        "🔴 **This set no longer carries a golden claim, and no number measured on it\n"
        "is evidence about the engine's quality.** Its questions and expected values\n"
        "are open: any session may read them, in any state, as ordinary regression and\n"
        "feature-test data. That is exactly why they are no longer a benchmark — the\n"
        "model family that reads them also tunes against them.\n\n"
        "⚠ **`expected.jsonl`, not `answers.jsonl`.** `.gitignore` carries\n"
        "`**/answers.jsonl` so that a key file cannot be committed at any depth; the\n"
        "retired tier is named around that guard rather than through it.\n\n"
        "Retired under [L11](../../../../records/0012_LAW-11-sealed-answer-key.md)\n"
        "decision 14 by `just golden-retire`. The sealed successor is the next\n"
        "generation, named `set-<gen>-<x|u>`.\n",
        encoding="utf-8",
    )
    print(f"RETIRED {name} -> {dest.relative_to(ROOT)}")
    print("  questions.jsonl + expected.jsonl are now committed, reusable test data.")
    print("  They are NOT a benchmark any more. Do not file a golden number from them.")
    return 0


def cmd_state(_args) -> int:
    """**Safe for anyone, including an agent**: it reads the state file and nothing else.

    No key path is opened, listed or stat'd — `is_unlocked()` looks at one file
    under `.claude/`. This is how a test, a session or `just golden-guards` asks
    *which state is this tree in* without going anywhere near the directory.
    """
    print("unlocked" if is_unlocked() else "locked")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="golden-switch",
        description="L11 decision 14's switch. Arpit's hand only, except `state`.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("unlock", help="take down the read guards (ARPIT ONLY)").set_defaults(func=cmd_unlock)
    sub.add_parser("lock", help="restore every guard byte-identically (ARPIT ONLY)").set_defaults(func=cmd_lock)
    retire = sub.add_parser("retire", help="move a scored set into open test data (ARPIT ONLY)")
    retire.add_argument("set", help="the set's name, e.g. set-1")
    retire.set_defaults(func=cmd_retire)
    sub.add_parser("state", help="print `locked` or `unlocked` (safe for anyone)").set_defaults(func=cmd_state)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
