#!/usr/bin/env python3
"""Fail if the version string disagrees across the files that carry it.

`CLAUDE.md` §Package identity says the version is "bumped in
`src/fux/__init__.py` only — it is the single source". **That was true only for
the Python half.** The Node read plane (W-107) added three more hand-written
copies, and nothing checked them, so a bump could ship `fux --version` naming
one release and the npm tarball naming another.

Two callers, one implementation — the `scripts/gen-laws.py` +
`tests/test_claude_md_laws.py` shape:

    python scripts/check-version-parity.py       # the release workflow
    pytest tests/test_version_parity.py          # every push

Stdlib only, and it parses rather than imports: the release workflow runs it
before anything is installed.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Each entry: path, a human name for the error, and how to pull the version out.
# A new copy of the version anywhere in the tree belongs in this list — that is
# the whole point of the file.
SOURCE = Path("src/fux/__init__.py")


def _re(path: str, pattern: str):
    def read(root: Path) -> str | None:
        m = re.search(pattern, (root / path).read_text(encoding="utf-8"), re.M)
        return m.group(1) if m else None

    return read


def _pkg_json(root: Path) -> str | None:
    return json.loads((root / "node/package.json").read_text(encoding="utf-8")).get("version")


SITES = {
    "src/fux/__init__.py": _re("src/fux/__init__.py", r'^__version__\s*=\s*"([^"]+)"'),
    "node/package.json": _pkg_json,
    "node/fux.mjs": _re("node/fux.mjs", r'^const VERSION\s*=\s*"([^"]+)"'),
    "node/src/verbs/mcp.mjs": _re(
        "node/src/verbs/mcp.mjs", r'serverInfo:\s*\{[^}]*version:\s*"([^"]+)"'
    ),
}


def check(root: Path = ROOT) -> list[str]:
    """Return a list of problems; empty means the tree agrees."""
    found: dict[str, str | None] = {name: read(root) for name, read in SITES.items()}

    problems = [f"{name}: no version string matched — the pattern or the file moved"
                for name, v in found.items() if v is None]
    if problems:
        return problems

    want = found[str(SOURCE)]
    problems += [
        f"{name}: {v!r} != {want!r} (src/fux/__init__.py is the source)"
        for name, v in found.items()
        if v != want
    ]
    return problems


def main() -> int:
    problems = check()
    if problems:
        print("✗ version parity:", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        print("\n  Bump src/fux/__init__.py, then match every site above.", file=sys.stderr)
        return 1
    print(f"✔ version parity: all {len(SITES)} sites agree on {SITES[str(SOURCE)](ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
