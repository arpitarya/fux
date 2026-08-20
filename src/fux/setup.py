"""`fux setup` — write the files a consumer owns, once, and never again.

Scaffolding has **two moments**, and the split is the whole point of this
module existing (ADR-DOTFUX decision 6, ADR-FETCHER decision 6):

| moment | writes | why |
|---|---|---|
| `ensure_layout`, at the head of every ingest | `.fux/README.md`, `.fux/.gitignore` | **mandatory and idempotent** — a fresh clone must be correct before a byte is written into the directory |
| `fux setup` | `fux.toml`, the two source lists with their headers, and the fetchers | **optional, explicit, once per repo** — a consumer asked for it |

**`ensure_layout` must never write a fetcher.** That is what keeps `fux ingest`
from putting 28 KB of WebSocket code into a repo that only wanted an index. It
is also why `DEFAULT_FETCHER` can name a file that exists: setup put it there,
because someone ran setup.

The two fetchers ship in the wheel as **package data under `templates/`, with
an extension Python's import machinery cannot resolve**. Bytes, copied out,
never imported — which makes ADR-FETCHER's adapter cap structural rather than a
rule someone has to remember. A fetcher fux imports is a fetcher fux owns.

Everything here is **write-if-missing**. An edited `http.py` survives every
later `fux setup`, exactly as an annotated `.fux/README.md` survives every
ingest.

This is also the one verb that may run before a repo root exists — it is what
writes the `fux.toml` that *makes* a directory a root, so demanding one first
would be circular. Every other verb errors without one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path

from .config import (
    CONFIG_NAME,
    DEFAULT_DIRS_FILE,
    DEFAULT_TYPES_FILE,
    DEFAULT_URLS_FILE,
    find_root,
    load,
)
from .errors import FuxError
from .store import fuxdir

#: Generated name -> the package-data file it is copied from.
FETCHERS = {"http.py": "http.py.txt", "cdp.py": "cdp.py.txt"}

FETCHERS_DIR = "fetchers"

_DIRS_HEADER = """\
# What fux indexes. One entry per line: a directory (walked recursively) or a
# single file, relative to the repo root. `#` starts a comment at the start of
# a line or after whitespace. The loader dedupes and sorts, so the order here
# is for humans only and cannot change a committed byte.
#
# One attribute, and the set is closed: `archived=true` marks a directory whose
# documents are history. It is DECLARED here, never derived from a path.
#
#   docs
#   handbook/runbooks
#   old/2023-platform        archived=true
#
# A `!` line SUBTRACTS from the walk -- a repo-relative glob, applied whatever
# order it appears in, matching a path or any directory above it. There is no
# un-exclude, so there is no precedence to remember:
#
#   !work/regression/*/evidence
#   !**/node_modules
#
# See ADR-DIR-LIST.
"""

_TYPES_HEADER = """\
# Which files are documents. One glob per line; `!` subtracts. A pattern with
# no `/` matches the file NAME anywhere, so `*.md` means every markdown file.
#
# THIS FILE IS OPTIONAL. Delete it and the built-in default below applies --
# an absent file never means "index everything" and never means "index
# nothing". If the file IS here, it replaces the default entirely.
#
# The built-in default, written out so you can see what you are getting:
*.md
*.markdown
*.txt
*.rst
*.adoc
*.org
#
# Prose only. No .json, .svg, .sh, .py or .mermaid -- machine data and diagram
# source are not documents, and indexing them inflates `df` for exactly the
# terms your real documents are trying to be found by. No extensionless files
# either: those are LICENSE, Makefile and Dockerfile far more often than they
# are prose.
#
#   !*.min.md          # subtract a generated flavour
#
# See ADR-TYPES.
"""

_CONFIG = """\
# fux.toml -- POLICY, not corpus. What gets indexed is `.fux/sources/dirs`
# and `.fux/sources/urls`, one entry per line, so a 5k-entry corpus diffs and
# merges line by line. Every key below has a default; they are here to be seen
# rather than to be required.

[sources]
#dirs_file = ".fux/sources/dirs"

# URL ingestion through YOUR fetcher files. Uncomment to enable. Fetching only
# ever happens under `fux ingest --refresh-urls` -- fux is offline by default.
#[sources.url]
#fetcher   = ".fux/fetchers/http.py"  # the file a line with no `fetch=` uses,
#                                     # and the directory `fetch=cdp` resolves in
#urls_file = ".fux/sources/urls"
#meta      = "hashed"                 # the floor; a line may loosen it to plain

# Fetcher tunables. Fux passes this table to the fetcher's optional
# `configure(config)` VERBATIM and never reads a key inside it -- the keys mean
# something to your fetcher, nothing to fux.
#[sources.url.config]
#cdp_port  = 9222
#timeout_s = 30

[index]
# Fixed at 256 (shard = blake2b(id, digest_size=1) -> 00..ff); this key
# documents the value rather than setting it.
shards = 256
"""

_URLS_HEADER = """\
# The URLs fux indexes. One per line. `#` starts a comment at the start of a
# line or after whitespace -- NOT inside a URL, so a fragment survives.
#
# Two attributes, and the set is closed:
#   fetch=http|cdp    which file under .fux/fetchers/ retrieves this URL
#   meta=hashed|plain whether the index may hold readable display text
#
#   https://example.com/handbook/oncall    fetch=http meta=hashed
#   https://wiki.corp/display/ENG/runbook  fetch=cdp  meta=hashed
#
# `fux url <URL>` writes a line here with every attribute stated. Fetching only
# ever happens under `fux ingest --refresh-urls`. See ADR-URL-LIST.
"""


@dataclass
class SetupReport:
    written: list[str] = field(default_factory=list)
    kept: list[str] = field(default_factory=list)


def template_bytes(name: str) -> bytes:
    """Read one shipped fetcher out of the wheel. **Read, never imported.**"""
    try:
        return (resources.files("fux") / "templates" / name).read_bytes()
    except (FileNotFoundError, ModuleNotFoundError) as exc:  # pragma: no cover - broken install
        raise FuxError(
            f"the shipped fetcher {name!r} is missing from this install — "
            "reinstall fux-engine, or write .fux/fetchers/ yourself"
        ) from exc


def _write_if_missing(path: Path, content: bytes, report: SetupReport, root: Path) -> None:
    rel = path.relative_to(root).as_posix()
    if path.exists():
        report.kept.append(rel)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    report.written.append(rel)


def _seed_dirs(root: Path) -> bytes:
    """The starter directory list: the header, plus what this repo obviously has.

    A seeded line is a suggestion in a file the human owns, not a guess the
    engine keeps making — setup runs once, and every later run keeps whatever
    the file says.
    """
    seeds = [name for name in ("README.md", "docs") if (root / name).exists()]
    body = "".join(f"{name}\n" for name in sorted(seeds))
    return (_DIRS_HEADER + ("\n" + body if body else "")).encode("utf-8")


def run(root: Path) -> SetupReport:
    """Write the consumer-owned files, write-if-missing. Returns what happened."""
    report = SetupReport()
    for path in fuxdir.ensure_layout(root):
        report.written.append(path.relative_to(root).as_posix())

    directory = fuxdir.fux_dir(root)
    for name, template in FETCHERS.items():
        _write_if_missing(directory / FETCHERS_DIR / name, template_bytes(template), report, root)

    _write_if_missing(root / DEFAULT_DIRS_FILE, _seed_dirs(root), report, root)
    # Written with the default spelled out rather than left implicit: a
    # consumer should be able to see what fux considers a document without
    # reading its source (ADR-TYPES).
    _write_if_missing(root / DEFAULT_TYPES_FILE, _TYPES_HEADER.encode("utf-8"), report, root)
    _write_if_missing(root / DEFAULT_URLS_FILE, _URLS_HEADER.encode("utf-8"), report, root)
    _write_if_missing(root / CONFIG_NAME, _CONFIG.encode("utf-8"), report, root)
    return report


def cmd_setup(args) -> int:
    # The one verb that may run before a root exists: it is what *creates* the
    # marker (`fux.toml`), so requiring one first would be circular. Everywhere
    # else, no root is an error.
    root = find_root() or Path.cwd()
    report = run(root)
    for rel in report.written:
        print(f"  wrote {rel}")
    for rel in report.kept:
        print(f"  kept  {rel} (yours; never rewritten)")
    if not report.written:
        print("setup: nothing to do — every consumer-owned file is already here")
    else:
        print(
            f"setup: {len(report.written)} file(s) written. They are yours: commit them, "
            "edit them, fux will not rewrite them."
        )
    load(root)  # a hand-edited fux.toml fails loudly here, not on the first ingest
    print("next: add entries to .fux/sources/dirs, then `fux ingest`")
    return 0
