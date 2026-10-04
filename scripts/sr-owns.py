#!/usr/bin/env python3
"""Stamp each record's `owns:` entries with the content hash of what they own.

**Arpit, 2026-09-13:** *"in every SR, owns should have the file name and content
hash so that we can track if something changed — it should be updated in the SR
if there is a design/functional change."*

`owns: [src/fux/query/rank.py@a1b2c3d4e5f6]`. The suffix is the first 12 hex of
a SHA-256 over the component's bytes, so a record and the code it claims can be
compared without reading either.

**How a component is hashed**

- **A file** — SHA-256 of its bytes, LF-normalised.
- **A directory** — SHA-256 over `relpath\\0filehash\\n` for every file under it,
  sorted by relative path. Deterministic, and it moves when a file is added,
  removed, renamed or edited. `__pycache__`, `*.pyc` and `.DS_Store` are skipped
  because they are not the component.

🔴 **A directory is enumerated from `git ls-files`, NOT from the filesystem**
(2026-09-13). Walking the directory made the hash depend on what happened to be
sitting in the working tree: `node/` holds a gitignored `node/dist/` the moment
anyone builds the bundle, so a stamp written on that machine could never match
the same commit in CI — `tests/test_sr_owns_hash.py` went red on every runner
while passing for the person who stamped it. **The component is what the commit
carries**, which is exactly what a record can claim to own; untracked and
ignored files are not part of it. Tracked files are read from the WORKING TREE,
so an uncommitted edit still moves the hash — that is the prompt to re-read the
record, and it settles in the same commit that lands the edit.

**12 hex, not 64.** This is drift detection, not content addressing, and a
record owning five paths would otherwise carry 320 characters of hash. Collisions
at 48 bits are not a threat model here; a silent one would only mean a missed
prompt to re-read a record.

⚠ **What this CANNOT do, and it is the reason to read the failure rather than
obey it.** A hash moves on a typo, a comment, a reformat and a rewrite alike. It
says *this component is not the one the record was written against* — never
whether the change was a design or functional one. **That judgement stays with
whoever reads it**, which is the same place [SR-LAW-0](../records/0002_LAW-0-authority.md)
leaves coherence.

Usage::

    python scripts/sr-owns.py                     # check every record: exit 1 and name every stale claim
    python scripts/sr-owns.py --write 0109 0126   # stamp only the records you changed
    python scripts/sr-owns.py --write --all       # stamp every record — only on a tree nobody else is editing

🔴 **A bare `--write` is refused** (2026-09-27, W-226, the third occurrence). A
repo-wide stamp on a shared tree re-stamps another session's in-progress
records and silently satisfies the gate that exists to make them re-read those
records. [SR-WORK-OWNERSHIP](../records/0054_WORK-ownership.md) decision 13a.

🔴 **`--write` refuses while an owned directory holds an UNTRACKED file**
(2026-10-04, the third occurrence — work/LESSONS.md 2026-09-21, WORKLOG
2026-09-27 and 2026-10-04). The hash enumerates `git ls-files`, so a new file
stamped before `git add` is left out of it, and the gate fires on the next run
after the commit, naming a component you thought you had just stamped. **Order:
`git add`, then stamp.** `--untracked-ok` stamps anyway, for a file that is
another session's and is not meant to land with yours.

⚠ **Run `scripts/sr-hash.py --write` after this one** — stamping `owns` changes
the record, which moves its own `content_sha`.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "records"
WIDTH = 12
SKIP_NAMES = {"__pycache__", ".DS_Store"}
SKIP_SUFFIX = {".pyc", ".pyo"}

_OWNS = re.compile(r"^owns: \[(.*)\]$", re.M)


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _tracked_under(target: Path) -> list[Path]:
    """Every git-tracked file under `target`, as absolute paths.

    `git ls-files` rather than `rglob` on purpose: see the module docstring.
    A tracked file that has been deleted in the working tree is skipped — the
    deletion moves the hash by its absence, which is the correct signal.
    """
    try:
        out = subprocess.run(
            ["git", "ls-files", "-z", "--", str(target.relative_to(ROOT).as_posix())],
            cwd=ROOT, capture_output=True, check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as exc:  # pragma: no cover - environment
        raise SystemExit(
            f"sr-owns needs `git ls-files` to enumerate {target}: {exc}. "
            "Hashing the filesystem instead would make the stamp depend on "
            "untracked build output, which is the bug this replaced."
        ) from exc
    names = [n.decode("utf-8") for n in out.split(b"\0") if n]
    return [ROOT / n for n in names]


def component_digest(component: str) -> str | None:
    """12 hex for a file or a directory, or None when the path does not exist."""
    target = ROOT / component
    if target.is_file():
        return _file_digest(target)[:WIDTH]
    if target.is_dir():
        # 🔴 Sorted by the POSIX RELATIVE PATH, never by `Path`. `PurePath`
        # ordering compares parts, and on Windows it lowercases them first, so
        # a directory holding both `Makefile` and `mkdocs.yml` hashed in one
        # order on a Mac and another on a runner — the same component, two
        # hashes, and `tests/test_sr_owns_hash.py` red on Windows alone.
        rows = []
        for p in _tracked_under(target):
            if not p.is_file() or p.suffix in SKIP_SUFFIX:
                continue
            if SKIP_NAMES & set(p.parts):
                continue
            rows.append((p.relative_to(target).as_posix(), p))
        parts = [f"{rel}\0{_file_digest(p)}\n" for rel, p in sorted(rows)]
        return hashlib.sha256("".join(parts).encode("utf-8")).hexdigest()[:WIDTH]
    return None


def split_claim(claim: str) -> tuple[str, str | None]:
    """`path@sha` -> (path, sha); a bare path -> (path, None)."""
    claim = claim.strip().strip('"')
    if "@" in claim:
        path, _, sha = claim.rpartition("@")
        if re.fullmatch(r"[0-9a-f]{%d}" % WIDTH, sha):
            return path, sha
    return claim, None


def claims(text: str) -> list[str]:
    m = _OWNS.search(text)
    if not m or not m.group(1).strip():
        return []
    return [c.strip() for c in m.group(1).split(",") if c.strip()]


def restamp(text: str) -> tuple[str, list[str]]:
    """(new text, components whose hash was wrong or missing)."""
    m = _OWNS.search(text)
    if not m or not m.group(1).strip():
        return text, []
    moved, out = [], []
    for claim in claims(text):
        path, have = split_claim(claim)
        want = component_digest(path)
        if want is None:
            raise SystemExit(f"owns names a path that does not exist: {path!r}")
        if have != want:
            moved.append(path)
        out.append(f"{path}@{want}")
    return text[: m.start()] + "owns: [" + ", ".join(out) + "]" + text[m.end() :], moved


def untracked_under(component: str) -> list[str]:
    """Untracked, non-ignored files under a directory component — the files
    `git add` would bring into its hash. Empty for a file component."""
    target = ROOT / component
    if not target.is_dir():
        return []
    out = subprocess.run(
        ["git", "ls-files", "-z", "--others", "--exclude-standard", "--",
         target.relative_to(ROOT).as_posix()],
        cwd=ROOT, capture_output=True, check=True,
    ).stdout
    return [n.decode("utf-8") for n in out.split(b"\0") if n]


def records() -> list[Path]:
    return sorted(RECORDS.glob("[0-9][0-9][0-9][0-9]_*.md"))


#: Why a bare `--write` is refused. Stated here, printed on refusal.
_REFUSAL = (
    "refusing a repo-wide --write: name the records you changed "
    "(e.g. `0109` or records/0109_index-record.md), or pass --all when no other "
    "session shares this tree. A repo-wide stamp re-stamps ANOTHER session's "
    "in-progress records and silently satisfies the gate meant to make them "
    "re-read them (SR-WORK-OWNERSHIP decision 13a; work/LESSONS.md 2026-09-21)."
)


def select(every: list[Path], names: list[str]) -> list[Path]:
    """The records `names` picks out of `every` — a 4-digit number, a file
    name, or a path. An unknown name is an error, never a silent no-op."""
    picked = []
    for name in names:
        stem = Path(name).name
        hits = [p for p in every if p.name == stem or p.name.startswith(f"{stem}_")]
        if len(hits) != 1:
            raise SystemExit(f"{name!r} names {len(hits)} records; name exactly one")
        picked.append(hits[0])
    return sorted(set(picked))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true", help="recompute and stamp the named records' claims")
    ap.add_argument("--all", action="store_true", help="with --write: every record (a tree nobody else is editing)")
    ap.add_argument("--untracked-ok", action="store_true",
                    help="with --write: stamp even though an owned directory holds untracked files")
    ap.add_argument("records", nargs="*", help="record numbers, names or paths to act on")
    args = ap.parse_args()
    if args.write and not args.records and not args.all:
        print(_REFUSAL, file=sys.stderr)
        return 2
    chosen = select(records(), args.records) if args.records else records()
    if args.write and not args.untracked_ok:
        loose = sorted({
            f
            for path in chosen
            for claim in claims(path.read_text(encoding="utf-8"))
            for f in untracked_under(split_claim(claim)[0])
        })
        if loose:
            print("refusing --write: these files are untracked under a directory the "
                  "named records own, so the stamp would leave them out and go stale "
                  "the moment they are committed. `git add` them first, then stamp "
                  "(work/LESSONS.md 2026-09-21). If they are another session's, pass "
                  "--untracked-ok:", file=sys.stderr)
            for f in loose:
                print(f"  {f}", file=sys.stderr)
            return 2

    stale: list[str] = []
    for path in chosen:
        text = path.read_text(encoding="utf-8")
        new, moved = restamp(text)
        if not moved:
            continue
        if args.write:
            path.write_text(new, encoding="utf-8")
            print(f"{path.name}: {', '.join(moved)}")
        else:
            stale.extend(f"{path.name}: {c}" for c in moved)
    if stale:
        print(f"MOVED ({len(stale)}):")
        for s in stale:
            print(f"  {s}")
        print("\nRead the record before re-stamping: a hash moves on a typo and on a")
        print("redesign alike, and only one of those means the record is now wrong.")
        print("Then: python scripts/sr-owns.py --write <record…> && python scripts/sr-hash.py --write <record…>")
        return 1
    if not args.write:
        print(f"{len(records())} records: every owns hash is current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
