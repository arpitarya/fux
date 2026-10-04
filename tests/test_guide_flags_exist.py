"""A flag the agent guides tell a reader to type exists on the parser.

**What this enforces:** [SR-AGENT-POLICY](../records/0132_agent-policy.md)
decision 15g -- *a guide that names a workaround flag must be edited in the same
change that removes it*, and until now **nothing enforced that; the sentence was
the guard**. Every `fux <verb> --flag` token in a code span or fenced block of
`src/fux/templates/agents/*.md` must parse against `build_parser()`: the verb is a
real subcommand and the flag is one of its option strings. A removed workaround
flag reddens the guide. W-246 (B-068).

**What it cannot do.** It proves the *token exists*, not that the guide uses it
correctly or that the prose around it is still true -- that stays the drafter's.
A placeholder (`<q>`) is skipped, and so is a verb that is not a subcommand: the
guides name the deleted `fux update` deliberately, to say it is gone. A verb followed by a nested verb (`fux daemon
start --x`) is checked against the nested parser.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pytest

from fux.cli import build_parser

AGENTS = Path(__file__).resolve().parents[1] / "src" / "fux" / "templates" / "agents"
_STOP = re.compile(r"[|;&>)]|\s#")


def _choices(parser: argparse.ArgumentParser) -> dict[str, argparse.ArgumentParser]:
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return dict(action.choices)
    return {}


def _spans(text: str):
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            yield line.strip()
        else:
            yield from re.findall(r"`([^`\n]+)`", line)


def _commands(text: str):
    for span in _spans(text):
        span = re.sub(r"^(?:\$\s*|uv run\s+|\S*/bin/)", "", span.strip())
        if not re.match(r"fux\s+[a-z]", span):
            continue
        yield _STOP.split(span, maxsplit=1)[0].split()[1:]


def _problems(path: Path) -> list[str]:
    root = build_parser()
    bad = []
    for words in _commands(path.read_text(encoding="utf-8")):
        parser, name = root, words[0]
        verbs = _choices(root)
        if name not in verbs:
            continue  # a deleted verb (`fux update`) is named on purpose, to say it is gone
        parser = verbs[name]
        rest = words[1:]
        nested = _choices(parser)
        if rest and rest[0] in nested:
            parser, rest = nested[rest[0]], rest[1:]
        known = set(parser._option_string_actions) | {"-h", "--help"}
        for tok in rest:
            if tok.startswith("--"):
                flag = tok.split("=", 1)[0].strip(".,:;\"'")
                if flag and flag not in known:
                    bad.append(f"fux {name} {flag}: not an option of this verb")
    return bad


def test_the_guides_are_found():
    assert len(list(AGENTS.glob("*.md"))) > 10


@pytest.mark.parametrize("path", sorted(AGENTS.glob("*.md")), ids=lambda p: p.name)
def test_every_flag_a_guide_names_parses(path: Path) -> None:
    """SR-AGENT-POLICY d15g: a removed workaround flag reddens the guide."""
    bad = _problems(path)
    assert not bad, f"{path.name} names what the parser does not accept:\n  " + "\n  ".join(bad)


def test_the_gate_catches_a_removed_flag(tmp_path) -> None:
    """Self-test: a guide naming a flag that does not exist is reported."""
    p = tmp_path / "G.md"
    p.write_text("Run `fux ask \"q\" --no-such-workaround --json` first.\n", encoding="utf-8")
    assert _problems(p) == ["fux ask --no-such-workaround: not an option of this verb"]
