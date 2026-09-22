#!/usr/bin/env python3
"""Find the hand-offs in a filed run, and label each one. **It reads no key.**

`just golden-score` calls this and scores what it prints, one tab-separated line
per hand-off: `handoff  arm  rung  set`. It is split out of the recipe so the
three evidence layouts can be tested without starting the scorer, which no agent
does ([L11](../../records/0012_LAW-11-sealed-answer-key.md) decision 13). This
file opens hand-offs by path and nothing else, so **any session may run it**.

| layout | arm | rung |
|---|---|---|
| `<run>/evidence/<arm>/rung-*/handoff-set-*.jsonl` | the directory | the directory |
| `<run>/evidence/rung-*/handoff-set-*.jsonl` | `single` | the directory |
| `<run>/evidence/handoff-set-*.jsonl` | `single` | `--rung`, else the run's `PRE-REGISTRATION.md` |

⚠ **The flat layout is W-218's.** The `set-2-u` baseline filed its hand-off
there, with the rung in the run name, and the recipe globbed only the first two
— so it exited *"no handoff-set-\\*.jsonl"* on the one run it had to score.

🔴 **A flat hand-off with no rung is refused, never guessed.** The rung goes into
the score file's path and its `"rung"` field, and a wrong one files a number
under an index it was not measured on. A pre-registration that names two rungs
is refused for the same reason.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# L11 decision 14: generation 2 names sets `set-<gen>-<x|u>`; generation 1 used a
# bare integer. The scorer accepts the same spellings.
SET_NAME = re.compile(r"^\d+(-[xu])?$")
_RUNG = re.compile(r"\brung-\d+\b")
_FRONT_RUNG = re.compile(r"^rung:\s*[\"']?(rung-\d+)[\"']?\s*$", re.M)


def set_name(handoff: Path) -> str:
    name = handoff.name.removeprefix("handoff-set-").removesuffix(".jsonl")
    if not SET_NAME.match(name):
        raise SystemExit(f"refusing: {handoff.name} does not name a set as set-<n> or set-<gen>-<x|u>")
    return name


def rung_from_preregistration(run: Path) -> str:
    """The rung a flat hand-off was captured on, from the run's own
    pre-registration: a `rung:` frontmatter line wins; otherwise the file must
    name exactly one distinct `rung-NNNNN`."""
    prereg = run / "PRE-REGISTRATION.md"
    if not prereg.is_file():
        raise SystemExit(f"refusing: a flat hand-off in {run} needs --rung, and there is no PRE-REGISTRATION.md to read it from")
    text = prereg.read_text(encoding="utf-8")
    front = _FRONT_RUNG.search(text.split("\n---", 1)[0]) if text.startswith("---") else None
    if front:
        return front.group(1)
    named = sorted(set(_RUNG.findall(text)))
    if len(named) != 1:
        raise SystemExit(
            f"refusing: {prereg} names {len(named)} rungs ({', '.join(named) or 'none'}); "
            "pass --rung so a flat hand-off is never filed under a guessed index"
        )
    return named[0]


def discover(run: Path, rung: str | None = None) -> list[tuple[Path, str, str, str]]:
    """`(handoff, arm, rung, set)` for every hand-off under `<run>/evidence/`,
    sorted by path so the scoring order is stable."""
    evidence = run / "evidence"
    if not evidence.is_dir():
        raise SystemExit(f"no {evidence}/ — is that a filed run?")
    out: list[tuple[Path, str, str, str]] = []
    for handoff in sorted(evidence.glob("*/rung-*/handoff-set-*.jsonl")):
        out.append((handoff, handoff.parent.parent.name, handoff.parent.name, set_name(handoff)))
    for handoff in sorted(evidence.glob("rung-*/handoff-set-*.jsonl")):
        out.append((handoff, "single", handoff.parent.name, set_name(handoff)))
    flat = sorted(evidence.glob("handoff-set-*.jsonl"))
    if flat:
        flat_rung = rung or rung_from_preregistration(run)
        if not _RUNG.fullmatch(flat_rung):
            raise SystemExit(f"refusing: --rung {flat_rung!r} is not rung-NNNNN")
        out.extend((h, "single", flat_rung, set_name(h)) for h in flat)
    return out


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not 1 <= len(args) <= 2:
        print("usage: handoffs.py <run> [rung]", file=sys.stderr)
        return 2
    found = discover(Path(args[0]), args[1] if len(args) == 2 and args[1] else None)
    if not found:
        print(f"no handoff-set-*.jsonl under {args[0]}/evidence/", file=sys.stderr)
        return 1
    for handoff, arm, rung, s in found:
        print(f"{handoff}\t{arm}\t{rung}\t{s}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
