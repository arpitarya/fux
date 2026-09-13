"""SR-WORK-ENVIRONMENTS veto 1, made mechanical: no tool, test or script reads the sandbox.

[SR-WORK-ENVIRONMENTS](../records/0052_WORK-environments.md) gives each sibling
environment one job and states veto condition 1 as *"a tool, test, script or
filed run reads `fux-playground` after 2026-09-11"*. Its own check is a
`grep -rn` over `src tools tests scripts`, which cannot tell **naming** the
environment from **reading** it — and both exist here: forty-odd artifacts used
it as an instrument (now reconciled by W-138) and a dozen genuinely record what
was measured there before the law.

**So this file draws the line twice, both ways mechanical.**

- **Rule A — nothing may reach it.** In a `.py` file, no string constant other
  than a docstring may contain the name; in a `.sh` file, no line outside a
  comment may. A path is built out of string constants, so a read cannot hide
  from this. A comment or docstring recording history can, which is the point.
- **Rule B — every mention is named here, with a reason.** A new file that
  mentions the environment at all fails until someone writes down why, and an
  entry that stops mentioning it fails too, so the list cannot rot into a
  blanket permission.

⚠ **What this does NOT prove, stated rather than discovered.** It reads the name
`fux-playground`, so `Path.home() / "my_programs" / ("fux-" + "playground")`
passes, and so does a hard-coded `/Users/…` path that never spells it. It also
says nothing about **prose** — a README under `tools/` telling a human to run
something there is caught by Rule B (the file must be named) but its
*instruction* is not read by anything. Judgment covers the rest; this covers
what a check can.
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

NEEDLE = "fux-playground"
ROOTS = ("src", "tools", "tests", "scripts")

_SKIP_DIRS = {"__pycache__", ".venv", "node_modules", ".pytest_cache", ".mypy_cache"}

_SELF = "tests/test_work_environments.py"

# Rule A carve-outs: a string constant that names the environment WITHOUT
# reading it. Each one is an argument someone has to make in writing.
_LITERAL_OK = {
    "tests/test_doc_links.py": (
        "a link-checker exemption, not a path: `../fux-playground/` is a link "
        "target the checker must not try to resolve, and README.md points there "
        "deliberately. It opens nothing."
    ),
    _SELF: "this check, which has to spell what it forbids",
}

# Rule B: every file under ROOTS that mentions the environment, and why it may.
_NAMED = {
    # --- history: a measurement that was taken there, recorded where it matters
    "src/fux/store/reader.py": "a comment recording where the v1-shard trip was measured",
    "tests/store/test_writer_reader.py": "the same measurement, in the test's docstring",
    "tests/test_regression_runs.py": "a docstring naming a past run's corpus",
    "tools/archived-signal-eval/run.py": "a comment attributing a rule to the retired harness",
    "tools/refer-budget-sweep/budget_sweep.py": "a comment on where corpus roots are resolved from",
    # --- retargeted by W-138: the tool no longer defaults to it
    "tools/differential/goldens_grade.py": "docstring: what it was, and why it has no default now",
    "tools/differential/queryset.py": "docstring: where the hand-written goldens used to come from",
    "tools/quality/goldens.py": "docstring: the corpus the kappa = 0.960 annotation was made over",
    "tools/quality-controls/relevance_audit.py": "docstring: the goldens its filed count was taken over",
    "tools/quality-controls/w115_instrument.py": (
        "docstring: the three-corpora table naming WHY each could not see W-115 — "
        "the playground is one of the three, and the row is that its two arms produce "
        "a byte-identical index. Naming a corpus as a recorded negative is not reading it"),
    # --- prose under tools/, corrected in place and kept as history
    "tools/quality/README.md": "names the retired set that recall@k has no replacement for",
    "tools/quality-controls/README.md": "the decoys are unanswerable relative to THAT corpus",
    "tools/vector-gate/README.md": "the 2026-09-05 run's corpus, and what that costs W-106",
    # --- an item's TITLE, recorded in a comment because the id collided
    "tests/test_no_work_item_is_lost.py": (
        "a comment naming which of the two W-70 items is which: one of them IS the "
        "sandbox item, and the title is how a reader tells the pair apart. It reads "
        "nothing there"),
    # --- the two checks that have to spell what they forbid
    "tests/test_doc_links.py": "the link-checker exemption argued in _LITERAL_OK",
    _SELF: "this check",
}


def _files() -> list[Path]:
    out: list[Path] = []
    for root in ROOTS:
        base = ROOT / root
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            if any(part in _SKIP_DIRS for part in path.relative_to(ROOT).parts):
                continue
            out.append(path)
    return out


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _docstring_nodes(tree: ast.AST) -> set[int]:
    """`id()` of every Constant that is a module/class/function docstring."""
    out: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body = getattr(node, "body", None)
        if not body:
            continue
        first = body[0]
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
            out.add(id(first.value))
    return out


def test_no_code_under_the_four_roots_reaches_the_sandbox() -> None:
    """Rule A. A comment may remember it; a string literal may not name it."""
    offenders: list[str] = []
    for path in _files():
        rel = _rel(path)
        if rel in _LITERAL_OK:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if NEEDLE not in text:
            continue
        if path.suffix == ".py":
            tree = ast.parse(text, filename=rel)
            docstrings = _docstring_nodes(tree)
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Constant)
                    and isinstance(node.value, str)
                    and NEEDLE in node.value
                    and id(node) not in docstrings
                ):
                    offenders.append(f"{rel}:{node.lineno}: string literal names {NEEDLE!r}")
        elif path.suffix == ".sh":
            for i, line in enumerate(text.splitlines(), 1):
                if NEEDLE in line and not line.lstrip().startswith("#"):
                    offenders.append(f"{rel}:{i}: shell line names {NEEDLE!r}")
    assert not offenders, (
        "\n".join(offenders)
        + f"\n\nSR-WORK-ENVIRONMENTS veto 1: nothing under {'/ '.join(ROOTS)} reads that environment.\n"
        "If this is a historical note, put it in a comment or a docstring.\n"
        "If it genuinely must be a literal, add it to _LITERAL_OK with the argument."
    )


def test_every_mention_is_named_with_a_reason() -> None:
    """Rule B. The list is exhaustive in both directions, so it cannot rot."""
    found = {_rel(p) for p in _files() if NEEDLE in p.read_text(encoding="utf-8", errors="replace")}
    named = set(_NAMED)

    unnamed = sorted(found - named)
    stale = sorted(named - found)
    assert not unnamed, (
        "These files name the sandbox and are not on the list:\n  "
        + "\n  ".join(unnamed)
        + "\n\nAdd each to _NAMED with one line saying why it may — or remove the mention."
    )
    assert not stale, (
        "These are on the list and no longer mention it:\n  "
        + "\n  ".join(stale)
        + "\n\nDelete the row. A permission nobody uses reads as a permission."
    )


def test_every_reason_is_actually_written() -> None:
    """A blank reason is a blanket permission with extra steps."""
    empty = sorted(k for k, v in _NAMED.items() if not str(v).strip())
    assert not empty, f"no reason given for: {empty}"
