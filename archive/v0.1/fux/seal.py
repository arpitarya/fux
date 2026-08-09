"""Proof-carrying rules — AST seals ($0, deterministic, plan §17.22).

A rule's `seal:` binds it to a **normalized-AST fingerprint** of the code its
`code_refs` point at — names and literals folded, so the seal tracks *structure*,
not text. Whitespace, comments, and renames don't break it; a flipped comparison,
an added branch, or a changed call shape does. `fux check` recomputes on every run
and emits an `unsealed` finding when the structure has drifted from what was
affirmed — strictly *advisory*: only a human re-affirms, via `fux seal <id>`.

This upgrades drift from "the file's mtime moved" (git-based, §8) to "the thing I
claimed about structurally changed." Python uses the stdlib `ast`; brace languages
fall back to a sanitized, whitespace-folded span hash (shares the `astextract`
comment/string sanitizer).
"""
from __future__ import annotations

import ast
import hashlib
import re
from pathlib import Path

from fux import astextract
from fux.model import Rule

_REF_RE = re.compile(r"^([^#]+)(?:#L(\d+)(?:-L?(\d+))?)?$")


def _hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def _skeleton(node: ast.AST) -> str:
    """Structural shape of a node: class names nested, identifiers/constants folded.

    Operators (`Lt`/`Gt`/`Add`…) are themselves AST nodes, so a flipped comparison
    or arithmetic change alters the skeleton; a variable/function *rename* does not.
    """
    parts = [type(node).__name__]
    parts += [_skeleton(c) for c in ast.iter_child_nodes(node)]
    return "(" + " ".join(parts) + ")"


def _overlap(node: ast.AST, lo: int, hi: int) -> bool:
    start = getattr(node, "lineno", None)
    if start is None:
        return False
    end = getattr(node, "end_lineno", start)
    return start <= hi and end >= lo


def _py_fp(text: str, lo: int | None, hi: int | None) -> str | None:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return _brace_fp(text, lo, hi)
    if lo is None:
        return _hash(_skeleton(tree))
    defs = [n for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and _overlap(n, lo, hi)]
    picked = defs or [n for n in tree.body if _overlap(n, lo, hi)]
    if not picked:
        return None
    picked.sort(key=lambda n: n.lineno)
    return _hash("|".join(_skeleton(n) for n in picked))


def _brace_fp(text: str, lo: int | None, hi: int | None) -> str | None:
    san = astextract.sanitize_lines(text)        # blanks comments + string literals
    span = san[(lo - 1):hi] if lo else san
    norm = " ".join("".join(span).split())       # fold all whitespace
    return _hash(norm) if norm else None


def fingerprint(text: str, suffix: str, lo: int | None, hi: int | None) -> str | None:
    """Structural fingerprint of a code span; None if nothing resolvable is there."""
    return _py_fp(text, lo, hi) if suffix == ".py" else _brace_fp(text, lo, hi)


def current(root: Path, r: Rule) -> str | None:
    """Combined fingerprint across all of a rule's resolvable `code_refs`.

    None when no `code_ref` resolves to readable code — an unsealable rule (we never
    fabricate a seal, so glossary/adr-style entries simply opt out).
    """
    parts: list[str] = []
    for ref in r.code_refs:
        m = _REF_RE.match(ref.strip())
        rel = (m.group(1) if m else ref).rstrip("/")
        lo = int(m.group(2)) if (m and m.group(2)) else None
        hi = int(m.group(3)) if (m and m.group(3)) else lo
        target = root / rel
        if not target.is_file():
            continue
        try:
            text = target.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        fp = fingerprint(text, target.suffix, lo, hi)
        if fp:
            parts.append(f"{rel}:{fp}")
    return _hash("|".join(parts)) if parts else None


_SEAL_LINE = re.compile(r"^seal\s*:", re.M)


def _write_seal(path: Path, fp: str) -> None:
    """Insert/replace only the top-level `seal:` line — preserve all other formatting.

    A surgical edit, *not* a full re-serialize: sealing must not reformat a rule's
    frontmatter (e.g. flatten inline lists), so the diff is a single line.
    """
    lines = path.read_text(encoding="utf-8").split("\n")
    fence = [i for i, ln in enumerate(lines) if ln.strip() == "---"]
    if len(fence) < 2:
        return                              # no frontmatter block — refuse to touch
    start, end = fence[0] + 1, fence[1]
    new = f"seal: {fp}"
    for i in range(start, end):
        if _SEAL_LINE.match(lines[i]):
            lines[i] = new
            break
    else:
        lines.insert(end, new)              # just before the closing fence
    path.write_text("\n".join(lines), encoding="utf-8")


def stamp(root: Path, rules: list[Rule]) -> list[str]:
    """Write the current fingerprint into each rule's `seal:` frontmatter.

    Returns the ids actually (re)sealed. Skips rules with no resolvable code.
    """
    sealed: list[str] = []
    for r in rules:
        fp = current(root, r)
        if fp is None or r.fm.get("seal") == fp:
            continue
        r.fm["seal"] = fp
        _write_seal(r.path, fp)
        sealed.append(r.id)
    return sealed
