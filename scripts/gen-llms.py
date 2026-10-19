#!/usr/bin/env python3
"""Render this repository's own `llms.txt` and `llms-full.txt` with `fux llms`.

**Why this exists** (W-284, [SR-LLMS](../records/0162_llms.md)). The two files
at the root are what a language model reads to learn what fux is — from a clone
or from raw GitHub. They are generated, never hand-written: the index decides
the documents and their titles, each document's own `description:` is the note
on its link, and `--full` carries the text of the few documents that change
rarely. [`tests/test_llms.py`](../tests/test_llms.py) holds both files equal
to this script's output, so a generated view cannot drift from what it shows
(SR-LAW-0 decision 5).

The index lags the tree by one post-commit ingest, so after changing a listed
document's title: `fux ingest`, then `python scripts/gen-llms.py --write`
(`just llms`).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

TITLE = "Fux"
SUMMARY = (
    "Fux ranks a repository's documentation, decisions and runbooks from a small "
    "index committed to git, fetches the cited text from the system that owns it, "
    "and verifies freshness at answer time — deterministic, offline, $0, no model "
    "in the maintenance path. Agents reach it over MCP (`fux mcp`), editors over "
    "LSP (`fux lsp`), people over the CLI."
)
BASE_URL = "https://raw.githubusercontent.com/arpitarya/fux/main/"
#: llms.txt: the front door, the docs bundle, and every standing record.
LISTED = ["README.md", "CHANGELOG.md", "docs/GLOSSARY.md", "docs/index.md",
          "docs/paper/the-fux-index-paper.md", "records/"]
#: llms-full.txt: only what changes rarely — the front door, the docs bundle,
#: the paper and the fourteen Law records.
FULL = ["README.md", "docs/GLOSSARY.md", "docs/index.md",
        "docs/paper/the-fux-index-paper.md", "records/000", "records/001"]

FILES = {"llms.txt": (LISTED, False), "llms-full.txt": (FULL, True)}


def rendered() -> dict[str, str]:
    from fux.llms import render
    from fux.store import read_index

    records = read_index(ROOT)
    return {
        name: render(ROOT, records, prefixes=prefixes, title=TITLE, summary=SUMMARY,
                     base=BASE_URL, full=full)
        for name, (prefixes, full) in FILES.items()
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--write", action="store_true", help="rewrite the files")
    args = parser.parse_args()
    stale = []
    for name, text in rendered().items():
        path = ROOT / name
        if args.write:
            path.write_text(text, encoding="utf-8", newline="\n")
        elif not path.is_file() or path.read_text(encoding="utf-8") != text:
            stale.append(name)
    if stale:
        print(f"stale: {', '.join(stale)} — run `python scripts/gen-llms.py --write`", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
