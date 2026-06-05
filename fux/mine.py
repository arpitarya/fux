"""`fux mine` — surface *candidate* rules latent in the code ($0, plan §17.23).

Authored-only knowledge bases die of cold-start: only the rules someone bothered to
write exist. This inverts it — a deterministic, Daikon-flavoured first pass that
points at knowledge already in the code, as **draft candidates a human confirms**
(the same never-auto-author discipline as `capture` → `distill`). No LLM.

First miner: **magic numbers** — a non-trivial numeric literal repeated across ≥N
distinct sites is probably a named constant / convention waiting to be written.
Python literals come from the stdlib `ast`; other languages from a digit scan over
the comment/string-sanitized text (so numbers inside strings/comments don't count).
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

from fux import astextract, config, globs, paths

# Numbers too common to be "magic" — naming them would be noise.
_TRIVIAL = {0, 1, 2, -1, 10, 100, 1000}
_NUM = re.compile(r"(?<![\w.])\d+(?:\.\d+)?")


@dataclass
class Candidate:
    kind: str                 # "magic-number"
    key: str                  # the literal, as text
    sites: list[str]          # "file:line" occurrences

    def draft(self) -> str:
        where = ", ".join(self.sites[:6]) + (" …" if len(self.sites) > 6 else "")
        return (f"- **{self.key}** ({len(self.sites)}×) — name it as a `convention`? "
                f"sites: {where}")


def _iter(root: Path, cfg: dict):
    src = cfg.get("graph_globs") or cfg["important_globs"]
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if rel.startswith(".fux/") or rel.startswith(".git/"):
            continue
        if globs.match_any(rel, cfg["ignore_globs"]) or not globs.match_any(rel, src):
            continue
        try:
            yield rel, path.read_text(encoding="utf-8"), path.suffix
        except (OSError, UnicodeDecodeError):
            continue


def _numbers(text: str, suffix: str) -> list[tuple[str, int]]:
    """(literal-text, line) for numeric literals, ignoring strings/comments."""
    if suffix == ".py":
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return []
        out = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) \
                    and not isinstance(node.value, bool):
                out.append((repr(node.value), node.lineno))
        return out
    out = []
    for i, line in enumerate(astextract.sanitize_lines(text), 1):
        for m in _NUM.findall(line):
            out.append((m, i))
    return out


def mine(root: Path, cfg: dict | None = None, min_sites: int = 3) -> list[Candidate]:
    cfg = cfg or config.load(paths.Footprint(root).config)
    sites: dict[str, list[str]] = {}
    for rel, text, suffix in _iter(root, cfg):
        for lit, line in _numbers(text, suffix):
            try:
                if float(lit) in _TRIVIAL:
                    continue
            except ValueError:
                continue
            sites.setdefault(lit, []).append(f"{rel}:{line}")
    out = [Candidate("magic-number", lit, locs)
           for lit, locs in sites.items() if len(locs) >= min_sites]
    return sorted(out, key=lambda c: (-len(c.sites), c.key))


def render(candidates: list[Candidate]) -> str:
    if not candidates:
        return "· nothing to mine — no magic number repeats ≥3 sites."
    head = [f"# Mined candidates ({len(candidates)}) — drafts only, confirm before authoring",
            "", "## magic numbers", ""]
    return "\n".join(head + [c.draft() for c in candidates])
