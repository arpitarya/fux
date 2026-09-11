#!/usr/bin/env python3
"""renumber-adrs.py — ONE-SHOT migration, 2026-09-11. Delete after its commit lands.

WHAT IT DOES
  Ruled by Arpit, 2026-09-11: **`0001`-`0100` belong to the Law records;
  every other record starts at `0101`.** Today the laws are `0001` (ADR-LAWS)
  and `0002`-`0010` (ADR-LAW-0 ... ADR-LAW-8); `0011`-`0100` stay EMPTY as
  reserved placeholders — no dummy files. Every non-law record moves up by 90,
  in its current order: `0011_cli-surface.md` -> `0101_cli-surface.md`, ...,
  `0064_doctor.md` -> `0154_doctor.md`.

WHAT IT REWRITES
  Every exact `NNNN_slug.md` token of a moved record, in every text file,
  plus the register's `[NNNN](NNNN_slug.md)` link text. A token is rewritten
  only if it names a record that exists and moves — a bare number in prose, a
  stale link to an old slug, or an illustrative path in a skill example is
  never touched (guessing which bare numbers mean a record is how a renumber
  lies).

WHAT IT SKIPS
  `.git/`, `.venv/`, caches, `.fux/index/` and `.fux/runtime/` (derived:
  re-ingest after, never sed a content-addressed index), and the archived
  v0.26 lines under `archive/v0.26*/` — a different, frozen numbering.

USAGE (from the repository root)
  python3 scripts/renumber-adrs.py            # dry run: the plan and the check
  python3 scripts/renumber-adrs.py --apply    # git mv + rewrite + verify
Then: `fux ingest`, `uv run pytest -q tests tests_e2e`, one commit.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()
ADR = ROOT / "docs" / "adr"
OFFSET = 90
LAW_MAX = 100
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".ruff_cache", "node_modules"}
SKIP_PREFIXES = (".fux/index/", ".fux/runtime/", "archive/v0.26/", "archive/v0.26-docs/",
                 ".claude/.locks/")
FILE_RE = re.compile(r"^(\d{4})_([A-Za-z0-9-]+)\.md$")


def plan() -> dict[str, str]:
    moves: dict[str, str] = {}
    for p in sorted(ADR.iterdir()):
        m = FILE_RE.match(p.name)
        if not m:
            continue
        n = int(m.group(1))
        if n <= 10:
            if not (m.group(2) == "LAWS" or m.group(2).startswith("LAW-")):
                sys.exit(f"!! {p.name}: a non-law record inside 0001-0010")
            continue
        if n > LAW_MAX:
            sys.exit(f"!! {p.name}: already above {LAW_MAX} — has this run before?")
        if m.group(2) == "LAWS" or m.group(2).startswith("LAW-"):
            sys.exit(f"!! {p.name}: a law record outside 0001-0010; the script does not know where it goes")
        moves[p.name] = f"{n + OFFSET:04d}_{m.group(2)}.md"
    for new in moves.values():
        if (ADR / new).exists():
            sys.exit(f"!! target exists: {new}")
    return moves


def text_files() -> list[Path]:
    try:
        out = subprocess.run(["git", "ls-files", "-z"], capture_output=True, check=True).stdout
        rels = [r for r in out.decode().split("\0") if r]
    except (subprocess.CalledProcessError, FileNotFoundError):
        rels = []
        for dp, dns, fns in os.walk(ROOT):
            dns[:] = [d for d in dns if d not in SKIP_DIRS]
            for fn in fns:
                rels.append(os.path.relpath(os.path.join(dp, fn), ROOT))
    keep = []
    for r in rels:
        r = r.replace(os.sep, "/")
        if r.startswith(SKIP_PREFIXES) or any(part in SKIP_DIRS for part in r.split("/")):
            continue
        keep.append(ROOT / r)
    return keep


LINK_RE = re.compile(r"\]\(([^)\s#]*?\d{4}_[A-Za-z0-9-]+\.md)(?:#[^)]*)?\)")


def unresolved_adr_links(files: list[Path]) -> set[tuple[str, str]]:
    bad = set()
    for f in files:
        if f.suffix not in {".md", ".py", ".txt", ".html", ".toml", ".sh"}:
            continue
        try:
            t = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
            continue
        for m in LINK_RE.finditer(t):
            target = m.group(1)
            if "://" in target:
                continue
            if not (f.parent / target).resolve().exists():
                bad.add((str(f.relative_to(ROOT)), target))
    return bad


def main() -> None:
    apply = "--apply" in sys.argv
    moves = plan()
    print(f"== plan: {len(moves)} records move by +{OFFSET}; 0001-0010 untouched; 0011-{LAW_MAX} left empty")
    for old, new in moves.items():
        print(f"   {old} -> {new}")
    files = text_files()
    before = unresolved_adr_links(files)
    in_git = (ROOT / ".git").exists()
    if apply:
        # Move FIRST, then rewrite the files where they now live. Computing edits
        # before the move and writing them after would recreate every old path and
        # leave the moved records with their old links.
        for old, new in moves.items():
            if in_git:
                subprocess.run(["git", "mv", f"docs/adr/{old}", f"docs/adr/{new}"], check=True)
            else:
                (ADR / old).rename(ADR / new)
        files = [f for f in text_files() if f.exists()]
    token = re.compile(r"(?<![0-9A-Za-z_])(" + "|".join(re.escape(o) for o in moves) + r")")
    bracket = re.compile(r"\[(\d{4})\]\((\d{4})_([A-Za-z0-9-]+\.md)\)")
    old_num = {new: old[:4] for old, new in moves.items()}

    edits: dict[Path, str] = {}
    hits = 0
    for f in files:
        try:
            t = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
            continue
        u, n = token.subn(lambda m: moves[m.group(1)], t)

        def fix(m: re.Match) -> str:
            fname = f"{m.group(2)}_{m.group(3)}"
            if fname in old_num and m.group(1) == old_num[fname]:
                return f"[{m.group(2)}]({fname})"
            return m.group(0)
        u = bracket.sub(fix, u)
        if u != t:
            edits[f] = u
            hits += n
    print(f"== rewrite: {hits} path tokens in {len(edits)} files")
    if not apply:
        by_top: dict[str, int] = {}
        for f in edits:
            top = str(f.relative_to(ROOT)).split("/")[0]
            by_top[top] = by_top.get(top, 0) + 1
        print("   files by top-level dir:", dict(sorted(by_top.items())))
        print(f"== dry run only. unresolved ADR links today: {len(before)} (pre-existing). Re-run with --apply.")
        return

    for f, u in edits.items():
        f.write_text(u, encoding="utf-8")
    leftover = [str(f.relative_to(ROOT)) for f in text_files()
                if f.exists() and not (f.parent == ADR and f.name in moves)
                and token.search(f.read_text(encoding="utf-8", errors="ignore"))]
    if leftover:
        print("!! old paths still named in:", *leftover[:20], sep="\n   ")
        sys.exit(1)
    after = unresolved_adr_links(text_files())
    new_bad = sorted(after - {(a, b) for a, b in before})
    # a pre-existing stale link whose file moved is still the same stale link, so compare by file too
    print(f"== verify: unresolved ADR links before {len(before)}, after {len(after)}")
    if len(after) > len(before):
        print("!! the renumber broke links:")
        for a, b in new_bad[:40]:
            print(f"   {a}: {b}")
        sys.exit(1)
    print("== ok. Next: fux ingest; uv run pytest -q tests tests_e2e; one commit; delete this script.")


if __name__ == "__main__":
    main()
