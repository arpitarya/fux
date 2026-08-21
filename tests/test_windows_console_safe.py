"""Nothing the CLI prints may be unencodable on a Windows console.

**This is a gate because the failure class has now happened twice** — the
two-strikes rule in CLAUDE.md, applied in the change that recorded the second
occurrence.

1. **v0.30.0** — `fux doctor`'s Unicode checkmarks crashed on Windows' console
   codepage. Caught by CI after the release push, fixed in a follow-up.
2. **v0.35.0** — `fux add <a rejected file type>` printed a `→` (U+2192) in its
   explanation. Both Windows arms went red on the release commit; every POSIX
   arm was green, and so was every local run.

## Why a Windows console is the constraint

`sys.stdout` on Windows defaults to the **active console codepage**, which is
`cp1252` on a Western install and something narrower elsewhere. A character
outside it raises `UnicodeEncodeError` from `print()` — so the command does not
render badly, it **crashes**, exits non-zero, and takes any script calling it
down with it. `PYTHONIOENCODING`/`PYTHONUTF8` fix it for people who know to set
them, which is not a property the engine can rely on.

`cp1252` is the target rather than pure ASCII because it is what the crash is
actually measured against, and it is wide enough to keep the punctuation this
repo's prose depends on: `—` (U+2014), `·` (U+00B7), `'` and `"` all encode.
`→`, `✓`, `█` and `░` do not.

## What is checked, and what is deliberately not

**Only string literals that can reach a stream**: the arguments of `print()`,
`FuxError()`, and `*.write()`. Everything else is skipped, and the skips are
what make the check usable rather than a nuisance:

- **Docstrings.** A module docstring is never encoded to the console, and this
  codebase uses arrows and box-drawing to explain itself in prose.
- **Data.** `store/canonical.py` and `ingest/urlsrc.py` hold U+2028, U+2029 and
  U+0085 as the *sentinels they strip*. Both tripped the first version of this
  check, which is how the scope got narrowed — a guard that flags the code
  defending against a character is a guard people learn to switch off.

`src/fux/progress.py` is exempt **by name**: its bar is `█`/`░` on **stderr**,
and it paints only when stderr is a TTY under a codepage it has already
probed. Exempting a whole file is a blunt instrument, and it is the honest one
here — the alternative is a per-literal allowlist that would go stale.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src" / "fux"

#: The codepage a Windows console gets by default on a Western install, and the
#: one both recorded failures were measured against.
CONSOLE_ENCODING = "cp1252"

#: Painted only on a TTY stderr, never on the answer stream. See the module
#: docstring for why this is a file-level exemption rather than a literal one.
EXEMPT = {"progress.py"}


def _offending(text: str) -> set[str]:
    """The characters in `text` a Windows console could not encode."""
    bad = set()
    for ch in text:
        if ord(ch) < 128:
            continue
        try:
            ch.encode(CONSOLE_ENCODING)
        except UnicodeEncodeError:
            bad.add(ch)
    return bad


#: Calls whose string arguments end up on a stream a user reads.
_STREAMING_CALLS = {"print", "FuxError", "write"}


def _callee(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""


def _streamed_literals(tree: ast.AST):
    """Every string constant reachable from a call that writes to a stream.

    Walking the whole call subtree deliberately: an f-string is a `JoinedStr`
    of constants, and a message built across a parenthesised implicit
    concatenation is several constants. Both are things a person reads.
    """
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or _callee(node) not in _STREAMING_CALLS:
            continue
        for child in ast.walk(node):
            if isinstance(child, ast.Constant) and isinstance(child.value, str):
                yield child


def _modules() -> list[Path]:
    return sorted(p for p in SRC.rglob("*.py") if p.name not in EXEMPT)


@pytest.mark.parametrize("module", _modules(), ids=lambda p: p.name)
def test_no_string_literal_is_unprintable_on_a_windows_console(module: Path) -> None:
    tree = ast.parse(module.read_text(encoding="utf-8"))

    problems: list[str] = []
    for node in _streamed_literals(tree):
        bad = _offending(node.value)
        if bad:
            problems.append(f"line {node.lineno}: {''.join(sorted(bad))}")

    assert not problems, (
        f"{module.name} has string literals a Windows console cannot encode "
        f"({CONSOLE_ENCODING}):\n  " + "\n  ".join(problems) + "\n\n"
        "`print()` raises UnicodeEncodeError there, so the command crashes rather "
        "than rendering badly. Use ASCII (`->`, `[OK]`) in anything that can reach "
        "a stream. Prose in docstrings is exempt and is not what failed."
    )


def test_the_check_actually_looks_at_the_verbs_output() -> None:
    """A scope this narrow could silently cover nothing — so pin that it does not.

    `sources.py` is where the v0.35.0 crash was, and it must be a file this
    check has real literals from. Without this, narrowing the scope to
    streaming calls could pass by finding nothing at all.
    """
    tree = ast.parse((SRC / "sources.py").read_text(encoding="utf-8"))
    literals = [n.value for n in _streamed_literals(tree)]
    assert len(literals) > 20, "the streaming-call scope found almost nothing — it is too narrow"
    assert any("type allowlist rejects it" in s for s in literals), (
        "the line that crashed Windows at v0.35.0 is not in scope any more"
    )


def test_the_check_would_catch_the_two_failures_it_was_written_for() -> None:
    """A guard that cannot fail is not a guard — so prove it fires.

    Both recorded regressions, as literals: v0.30.0's checkmark and v0.35.0's
    arrow. If `CONSOLE_ENCODING` is ever loosened to something that encodes
    these, this test says so instead of the suite going quietly green.
    """
    assert _offending("  → the line is listed") == {"→"}
    assert _offending("[✓] python version") == {"✓"}
    assert _offending("in .fux/sources/dirs — docs still listed") == set()  # em dash is fine
    assert _offending("plain ascii") == set()
