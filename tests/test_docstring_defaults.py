"""The docstring gate — W-146, [SR-LAW-0](../records/0002_LAW-0-authority.md) 4a.

**A docstring may name a key; it may not carry a default the code does not.**

L0's test for a restatement is *could this artifact and the record disagree
while both still look correct?* Applied to docstrings, Arpit ruled the narrow
reading on 2026-09-14: a docstring may explain **mechanism and rationale**, and
a docstring's table of keys-and-defaults is a restatement that becomes a link.

⚠ **The narrow reading left one exposure, and decision 4a names it**:
`config.py`'s `UrlSource` docstring explains every key *and its default*, so it
and SR-CONFIG could drift apart while each looked right. **This file is what
turns that from judgment into an enforcement.**

## What this checks, and the one place it deviates from 4a's wording

Decision 4a says the literal is asserted equal to *"the value the owning record
declares"*. **This file asserts it against the CODE**, and the difference is
deliberate:

- **Records declare a key's existence, not its value.** SR-CONFIG's `keys`
  block is a list of dotted paths with sigils; SR-TUNE's is the same. A record
  *may* name a default in prose (SR-CONFIG decision 5 does), and prose is
  exactly what decision 6 says cannot make a key real — so a parser that read
  values out of prose would be guessing, and a guess that fails a test is worse
  than no test.
- **The code is where a default lives**, and the drift that actually hurts is a
  docstring that no longer matches what the loader does. That is checkable
  exactly, with no guessing.
- **And the record is still covered**, by the gate that already exists:
  `tests/test_sr_config_keys.py` holds the declared key block and the code equal
  in both directions. Between the two, a key's *name* is bound to the record and
  its *value* is bound to the loader — and a docstring cannot drift from either.

**So the deviation narrows what is claimed, never what is enforced.** It is
stated here rather than in a commit message because a future reader comparing
4a's wording with this file will notice, and the answer should be where they
are looking.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "fux"

#: A default **claimed** in a docstring. The word `default` is required, and
#: that requirement is the whole design.
#:
#: 🔴 **A bare `` `key = value` `` is NOT a default claim, and matching it
#: produced eight false positives on the first run.** This codebase's
#: docstrings are dense with inline examples of exactly that shape —
#: ``under="docs/a"`` illustrating a prefix match, ``enabled = false``
#: naming a key in somebody's TOML file, ``hand_only = True`` naming a case.
#: None of them is a claim about a default, and flagging them would make the
#: gate noise.
#:
#: ⚠ **A gate that fires wrongly is worse than one that does not fire**, and
#: this repository has shipped the other failure already: `SR-FIND` veto 4
#: grepped a line that does not exist and read as passing for weeks. **Between
#: a check that cries wolf and a check that is silent, the silent one at least
#: does not train people to ignore it** — so the pattern requires the claim to
#: say it is a claim.
#:
#: ⚠ **Stated limit:** a default described in free prose — *"the default is
#: `.fux/fetchers/http.py`"* — is not matched. Matching it means parsing
#: English, and a checker that half-parses English fails on a comma.
_PATTERNS = (
    # `key = value` … default    (the word within a short window after it)
    re.compile(r"`(?P<key>[a-z_][a-z0-9_]*)\s*=\s*(?P<value>[^`]+)`(?=.{0,40}?\bdefault)", re.S),
    # `key` defaults to `value`  /  `key` default: `value`
    re.compile(r"`(?P<key>[a-z_][a-z0-9_]*)`[^`\n]{0,20}?\bdefaults?(?:\s+to)?:?\s+`(?P<value>[^`]+)`"),
)

#: Keys whose docstring literal is deliberately NOT the loader's value, each
#: with the reason. **Empty, and it should stay that way** — an entry here is a
#: docstring that is allowed to be wrong, which is the thing this file exists
#: to forbid. It exists so that a genuine exception is written down rather than
#: silently loosening the pattern above.
_EXEMPT: dict[str, str] = {}


def _literal(text: str):
    """The Python value a docstring wrote, or `None` if it is not a literal."""
    try:
        return ast.literal_eval(text.strip().rstrip("."))
    except (ValueError, SyntaxError):
        return None


def _defaults_here(node: ast.AST) -> dict[str, object]:
    """`name -> default` for **this definition's own** parameters and fields.

    🔴 **Scoped to the node, and the first version was not — it matched across
    the whole module and produced twelve false positives on the first run.**
    `tune.load`'s docstring explains `[cli.json] enabled = false`, a key in a
    TOML file; the module also has a Python parameter called `enabled` whose
    default is `True`, and a module-wide lookup called that a contradiction.

    ⚠ **A gate that fires wrongly is worse than one that does not fire.** It
    teaches every reader to pass over it, which is how `SR-FIND` veto 4 could
    grep a line that does not exist for weeks and read as passing. So the
    comparison only ever happens between a docstring and the thing it is the
    docstring OF — where a disagreement is unambiguous.
    """
    out: dict[str, object] = {}
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        args = node.args
        pairs = list(zip(args.args[len(args.args) - len(args.defaults):], args.defaults))
        pairs += [(a, d) for a, d in zip(args.kwonlyargs, args.kw_defaults) if d is not None]
        for arg, default in pairs:
            value = _literal_node(default)
            if value is not _MISSING:
                out[arg.arg] = value
    elif isinstance(node, ast.ClassDef):
        for stmt in node.body:
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name) and stmt.value:
                value = _literal_node(stmt.value)
                if value is not _MISSING:
                    out[stmt.target.id] = value
    return out


_MISSING = object()


def _literal_node(node: ast.AST):
    try:
        return ast.literal_eval(node)
    except (ValueError, SyntaxError):
        return _MISSING


def _modules() -> list[Path]:
    return sorted(p for p in SRC.rglob("*.py") if "__pycache__" not in p.parts)


def _claims(path: Path) -> list[tuple[str, str, object, dict]]:
    """`(where, key, claimed, its own defaults)` per docstring in `path`."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        doc = ast.get_docstring(node)
        if not doc:
            continue
        # `relative_to` only when the path is under the repo — the self-test
        # below plants a module in a tmp dir, and a label must not be the thing
        # that makes a gate raise.
        try:
            label = path.relative_to(ROOT)
        except ValueError:
            label = path
        where = f"{label}::{getattr(node, 'name', '<module>')}"
        mine = _defaults_here(node)
        for pattern in _PATTERNS:
            for match in pattern.finditer(doc):
                claimed = _literal(match.group("value"))
                if claimed is not None:
                    found.append((where, match.group("key"), claimed, mine))
    return found


@pytest.mark.parametrize("path", _modules(), ids=lambda p: p.relative_to(SRC).as_posix())
def test_a_docstring_default_equals_the_one_the_code_uses(path: Path) -> None:
    """🔴 **The exposure the narrow reading left open, closed.**

    A docstring that says `max_parallel = 4` while the loader defaults to `8`
    is the shape L0 decision 1 forbids: two artifacts that disagree while both
    look correct. Nothing caught it before this file, because a docstring is
    not executed and no reader diffs one against a dataclass.
    """
    wrong = []
    for where, key, claimed, actual in _claims(path):
        if key in _EXEMPT or key not in actual:
            continue
        if actual[key] != claimed:
            wrong.append(f"{where}: `{key} = {claimed!r}` but the code uses {actual[key]!r}")
    assert not wrong, (
        "a docstring states a default the code does not use — SR-LAW-0 decision 4a:\n  "
        + "\n  ".join(wrong)
        + "\n\nFix the DOCSTRING, never the code: the loader is what runs."
    )


def test_the_gate_would_actually_catch_a_drifted_docstring(tmp_path: Path) -> None:
    """**The gate proves it can fail**, because a check that cannot is worse
    than none — this repo has shipped one of those already (SR-FIND veto 4
    grepped a line that does not exist, and read as passing for weeks).
    """
    planted = tmp_path / "drifted.py"
    planted.write_text(
        'def f(timeout_s=30):\n    """Waits. `timeout_s = 10` by default."""\n',
        encoding="utf-8",
    )
    claims = _claims(planted)
    assert claims, "the pattern did not even see the claim"
    assert any(
        actual[key] != claimed for _, key, claimed, actual in claims if key in actual
    ), "the gate did not notice a docstring saying 10 where the code says 30"


def test_the_exemption_list_is_empty() -> None:
    """An entry in `_EXEMPT` is a docstring allowed to be wrong.

    It is a real escape hatch and it must stay visible: a list that quietly
    grows is how a gate becomes decoration. If one is ever needed, the reason
    goes beside it and this test's message is where the next reader is told
    that happened.
    """
    assert _EXEMPT == {}, (
        "a docstring has been exempted from the default gate: "
        + "; ".join(f"{k} ({why})" for k, why in _EXEMPT.items())
    )
