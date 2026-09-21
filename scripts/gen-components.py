#!/usr/bin/env python3
"""Render every record's **Components** block from the register's two tables.

**Why this exists.** [SR-WORK-OWNERSHIP](../records/0054_WORK-ownership.md)
decides *which* record owns a component and which records reach into it, and
both relations live in one place: `records/README.md`'s `OWNERSHIP` and
`DESCRIBES` tables. A reader opening a record could not see either — the
frontmatter's `owns:` key is a list of paths with no links, and `describes` is
not in the record at all. **So a record did not name the files it governs**,
which is W-208.

Writing the links by hand into 80-odd records is the restatement
[SR-LAW-0](../records/0002_LAW-0-authority.md) decision 1 forbids: the body and
the table would drift the first week and both would still look correct.
Decision 5 is the way out — **a generated view is permitted, and only while a
test binds it.** This script is the generator;
[`tests/test_record_components.py`](../tests/test_record_components.py) is the
bind. ⚠ **Remove that test and every block here violates decision 1.**

## The contract

- The block sits directly under the frontmatter, between
  `<!-- COMPONENTS-START … -->` and `<!-- COMPONENTS-END -->`, above the `# `
  heading, so it is the first thing after the metadata in every record.
- **Owns** — every ownership row whose owner is this record, each path as a
  relative link with its kind (`file` / `dir`).
- **Describes** — every describes row naming this record, as the register
  writes it (`path` or `path::symbol,symbol`), with the record that *owns* that
  path linked beside it.
- A record with neither, and which is not a law, carries the one honest-case
  line pointing at SR-WORK-OWNERSHIP decision 7. **A law with neither carries no
  block**: a law governs conduct, not components, and an "owns nothing" line on
  ten law records would be noise that trains a reader to skip the block.

🔴 **A link is rendered only for a path git tracks.** `node/dist/fux.mjs` is the
L10 build output — real on a machine that has built it, absent in CI — and a
link to it would make `tests/test_doc_links.py` pass here and fail there. The
rule is `sr-owns.py`'s: **the component is what the commit carries.** An
untracked path is rendered as a bare code span, which is what it is.

Run `python scripts/gen-components.py --write` after editing either table; run
it with `--check` (what CI and the test do) to prove the records agree.

⚠ **Run `scripts/sr-hash.py --write` after this one** — writing the block
changes the record, which moves its own `content_sha`.
"""

from __future__ import annotations

import argparse
import difflib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))

from sr_lib import (  # noqa: E402
    SR_DIR,
    describes_symbols,
    owner_of,
    ownership_table,
    register_names,
)

BEGIN = "<!-- COMPONENTS-START"
END = "<!-- COMPONENTS-END -->"

#: The exact opening marker. It names the generator, so a reader who is about to
#: edit the block by hand is told where the text actually lives before the test
#: tells them — the `gen-laws.py` convention.
BEGIN_LINE = (
    "<!-- COMPONENTS-START — GENERATED from records/README.md's OWNERSHIP and "
    "DESCRIBES tables by scripts/gen-components.py. Do not edit by hand: change "
    "the table, then run `python scripts/gen-components.py --write`. -->"
)

#: The line a record carrying neither relation gets. **The case letter is not
#: rendered**, and that is deliberate: the register states two honest cases and
#: nothing machine-readable says which one a given record claims — a generator
#: that guessed would be asserting something nobody checked, in the one position
#: a reader trusts. The record's own decisions say which, and they are what the
#: line points at.
OWNS_NOTHING = (
    "**Owns nothing** — [SR-WORK-OWNERSHIP](0054_WORK-ownership.md) decision 7, "
    "case (a|b); this record's own decisions say which."
)


def _tracked() -> frozenset[str]:
    """Every path git tracks, as repo-relative POSIX strings.

    `git ls-files` rather than the filesystem, for `sr-owns.py`'s reason: a
    working tree carries build output and scratch files that the commit does
    not, and a view that renders differently on two machines is not a view.
    """
    try:
        out = subprocess.run(
            ["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True
        ).stdout
    except (OSError, subprocess.CalledProcessError) as exc:  # pragma: no cover
        raise SystemExit(
            f"gen-components needs `git ls-files` to decide which paths are real: {exc}"
        ) from exc
    return frozenset(n.decode("utf-8") for n in out.split(b"\0") if n)


def _link(path: str, tracked: frozenset[str], *, label: str | None = None) -> str:
    """`` `path` `` as a link into the repo, or a bare code span when untracked.

    A directory is tracked by its contents rather than by itself, so it counts
    as real when anything under it is.
    """
    shown = label or path
    real = path in tracked or any(t.startswith(path + "/") for t in tracked)
    return f"[`{shown}`](../{path})" if real else f"`{shown}`"


def _record_link(name: str, names: dict[str, Path]) -> str:
    """`SR-ASK` -> `[SR-ASK](0103_ask.md)`, or the bare name when unresolvable."""
    path = names.get(name)
    return f"[{name}]({path.name})" if path is not None else f"`{name}`"


def _kind(path: str) -> str:
    return "dir" if (ROOT / path).is_dir() else "file"


def _kind_of(record: Path | None) -> str:
    """A record's declared `kind:`. Written, never derived — the register says
    why (`component` and `process` are not distinguishable from `owns` alone),
    and the one thing this generator needs it for is the same distinction:
    **a law governs conduct, not components**, so it gets no block at all."""
    if record is None or not record.exists():
        return ""
    m = re.search(r"^kind:\s*(\S+)\s*$", record.read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else ""


def owns_by_record() -> dict[str, list[str]]:
    """SR-NAME -> the components the register's ownership table gives it."""
    out: dict[str, list[str]] = {}
    for component, owner in ownership_table().items():
        out.setdefault(owner, []).append(component)
    return {k: sorted(v) for k, v in out.items()}


def describes_by_record() -> dict[str, list[tuple[str, frozenset[str]]]]:
    """SR-NAME -> the `(component, symbols)` rows naming it, sorted."""
    out: dict[str, list[tuple[str, frozenset[str]]]] = {}
    for (component, record), symbols in describes_symbols().items():
        out.setdefault(record, []).append((component, symbols))
    return {k: sorted(v, key=lambda r: (r[0], sorted(r[1]))) for k, v in out.items()}


def render(name: str, *, owns, describes, tracked, names, table) -> str | None:
    """One record's block body — what sits between the markers, or `None`.

    `None` means *this record gets no block at all*, which is a law with
    neither relation and nothing else.
    """
    mine_owns = owns.get(name, [])
    mine_describes = describes.get(name, [])
    if not mine_owns and not mine_describes:
        return None if _kind_of(names.get(name)) == "law" else OWNS_NOTHING

    lines: list[str] = []
    if mine_owns:
        lines.append("**Owns** — the components this record decides:")
        lines.append("")
        for component in mine_owns:
            kind = _kind(component)
            shown = component + "/" if kind == "dir" else component
            lines.append(f"- {_link(component, tracked, label=shown)} · {kind}")
    if mine_describes:
        if lines:
            lines.append("")
        lines.append("**Describes** — reaches into, does not own:")
        lines.append("")
        for component, symbols in mine_describes:
            shown = component
            if symbols:
                shown = f"{component}::{','.join(sorted(symbols))}"
            owner = owner_of(component, table)
            who = _record_link(owner, names) if owner else "no record"
            lines.append(f"- {_link(component, tracked, label=shown)} · owned by {who}")
    return "\n".join(lines)


def _split(text: str) -> tuple[str, str, str] | None:
    """(head, block body, tail) around an existing block, or `None`."""
    if BEGIN not in text or END not in text:
        return None
    head, rest = text.split(BEGIN, 1)
    body, tail = rest.split("-->", 1)[1].split(END, 1)
    return head, body.strip("\n"), tail


def _frontmatter_end(text: str) -> int:
    """The offset just past the record's closing `---` line."""
    lines = text.split("\n")
    if not lines or lines[0].rstrip() != "---":
        raise SystemExit("a record with no frontmatter block")
    close = next((i for i in range(1, len(lines)) if lines[i].rstrip() == "---"), None)
    if close is None:
        raise SystemExit("a record whose frontmatter is opened and never closed")
    return len("\n".join(lines[: close + 1])) + 1


def apply(text: str, body: str | None) -> str:
    """`text` with its block set to `body`, inserted, replaced or removed."""
    found = _split(text)
    if found is None:
        if body is None:
            return text
        cut = _frontmatter_end(text)
        return text[:cut] + "\n" + BEGIN_LINE + "\n\n" + body + "\n\n" + END + "\n" + text[cut:]
    head, _, tail = found
    if body is None:
        return head.rstrip("\n") + "\n" + tail.lstrip("\n")
    return head + BEGIN_LINE + "\n\n" + body + "\n\n" + END + tail


def blocks() -> dict[Path, str | None]:
    """Every record's expected block body, keyed by its file."""
    owns, describes = owns_by_record(), describes_by_record()
    tracked, names, table = _tracked(), register_names(), ownership_table()
    out: dict[Path, str | None] = {}
    for name, path in sorted(names.items()):
        if not path.exists() or path.parent != SR_DIR:
            continue
        out[path] = render(
            name, owns=owns, describes=describes, tracked=tracked, names=names, table=table
        )
    return out


def current(path: Path) -> str | None:
    found = _split(path.read_text(encoding="utf-8"))
    return None if found is None else found[1]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="exit 1 if any record is stale")
    ap.add_argument("--write", action="store_true", help="regenerate every record's block")
    args = ap.parse_args(argv)

    expected = blocks()
    if args.write:
        changed = 0
        for path, body in expected.items():
            text = path.read_text(encoding="utf-8")
            new = apply(text, body)
            if new != text:
                path.write_text(new, encoding="utf-8")
                changed += 1
        print(f"{len(expected)} records: {changed} block(s) rewritten")
        print("now run: python scripts/sr-hash.py --write")
        return 0

    stale = []
    for path, body in expected.items():
        have = current(path)
        if have != body:
            stale.append((path, have, body))
    if not stale:
        print(f"{len(expected)} records: every Components block is current")
        return 0
    for path, have, body in stale:
        print(f"--- {path.name}", file=sys.stderr)
        diff = difflib.unified_diff(
            (have or "").splitlines(), (body or "").splitlines(),
            fromfile="record (committed)", tofile="records/README.md (the tables)",
            lineterm="",
        )
        print("\n".join(diff), file=sys.stderr)
    print(
        f"\n{len(stale)} record(s) carry a stale Components block. The register's "
        "tables are the source (SR-WORK-OWNERSHIP decision 2): fix the table, then "
        "run `python scripts/gen-components.py --write && python scripts/sr-hash.py --write`.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
