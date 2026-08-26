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
    KNOWN_AGENTS,
    find_root,
    load,
)
from .errors import FuxError
from .store import fuxdir

#: Generated name -> the package-data file it is copied from.
FETCHERS = {"http.py": "http.py.txt", "cdp.py": "cdp.py.txt"}

FETCHERS_DIR = "fetchers"

#: vendor -> ((destination relative to the repo root, template under
#: `templates/agents/`), …) — ADR-AGENT-POLICY decisions 3 and 4.
#:
#: **Copilot has two entries and they are not alternatives.** The *agent* fires
#: when selected or routed to; the *instructions* fire on every matching
#: request. The gap between them is the dangerous case — someone runs `fux ask`
#: in a terminal and pastes the output into a chat the agent never saw — so
#: both ship.
#:
#: **This table is the whole of the routing, and that is deliberate.** There is
#: no `exists()` branch anywhere near it: which vendors install comes from
#: `[agents] install`, a declaration, never from sniffing the filesystem
#: (decision 5, and veto condition 4).
AGENT_FILES: dict[str, tuple[tuple[str, str], ...]] = {
    # `fux-enrich` is **claude-only and INVOKED, never ambient** (W-76 Phase 8).
    #
    # Two of the three renderings below are ambient -- Copilot's
    # `applyTo: "**"` and Kiro's `inclusion: always` -- and enter every request
    # for every developer in the repo. **An ambient skill that writes files
    # into a committed directory and changes ranking is a different risk
    # class**, so it ships only in the format that has an explicit-invocation
    # model, and its description names the trigger phrases rather than the
    # topic.
    #
    # **`USAGE-SKILL.md` is mapped TWICE, to two vendors, from one template**
    # (W-82 3.6). Kiro implements the same open Agent Skills standard Claude
    # does -- a folder with a `SKILL.md` carrying `name` + `description`,
    # loaded by progressive disclosure -- so the identical bytes are valid in
    # both. That is **agreement by construction**, which is strictly stronger
    # than decision 2's conformance test asserting two renderings still match.
    #
    # It ships as a **skill** for Kiro rather than steering, deliberately:
    # **Kiro CLI does not support steering inclusion modes**, so every file in
    # `.kiro/steering/` enters every interaction and `inclusion: manual` does
    # not protect anyone. A skill is progressive-disclosure on every surface.
    "claude": (
        (".claude/skills/fux-archived-results/SKILL.md", "SKILL.md"),
        (".claude/skills/fux-enrich/SKILL.md", "ENRICH-SKILL.md"),
        (".claude/skills/fux-usage/SKILL.md", "USAGE-SKILL.md"),
    ),
    "copilot": (
        (".github/agents/fux.agent.md", "fux.agent.md"),
        (
            ".github/instructions/fux-archived-results.instructions.md",
            "fux-archived-results.instructions.md",
        ),
        (".github/instructions/fux-usage.instructions.md", "fux-usage.instructions.md"),
    ),
    "kiro": (
        (".kiro/steering/fux-archived-results.md", "steering-fux-archived-results.md"),
        (".kiro/skills/fux-usage/SKILL.md", "USAGE-SKILL.md"),
    ),
}

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
# ever happens under `fux add <URL>` or `fux update` -- fux is offline by default.
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

# Fux marks retired documents `archived` and states no conclusion. These files
# teach your agents how to READ that mark -- they are the difference between an
# agent citing a retired design confidently and one that says it is retired.
#
# THEY ARE WRITTEN OUTSIDE .fux/, into directories GitHub, AWS and Anthropic
# own, which is why the default is spelled out here rather than left implicit:
#
#   claude   -> .claude/skills/fux-archived-results/SKILL.md
#   copilot  -> .github/agents/fux.agent.md
#               .github/instructions/fux-archived-results.instructions.md
#   kiro     -> .kiro/steering/fux-archived-results.md
#
# Two of them are AMBIENT (`applyTo: "**"`, `inclusion: always`) and enter every
# request in this repo, for every developer, whether or not they are using fux.
# Delete a name to stop installing it; `install = []` installs none. Editing a
# file that is already there is safe -- fux never rewrites one.
[agents]
install = ["claude", "copilot", "kiro"]
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
# `fux add <URL>` writes a line here with every attribute stated, and fetches
# that one URL. `fux update` re-fetches every line. Those are the engine's two
# networked paths; every other command is offline. See ADR-URL-LIST.
"""


@dataclass
class SetupReport:
    written: list[str] = field(default_factory=list)
    kept: list[str] = field(default_factory=list)
    #: Paths written **outside `.fux/` and `fux.toml`** — i.e. into directories
    #: GitHub, AWS and Anthropic own. Tracked separately because
    #: ADR-AGENT-POLICY decision 6 makes announcing them mandatory, and veto
    #: condition 1 fires on a write this list does not contain. A subset of
    #: `written`, never a replacement for it.
    outside: list[str] = field(default_factory=list)


def template_bytes(name: str) -> bytes:
    """Read one shipped fetcher out of the wheel. **Read, never imported.**"""
    try:
        return (resources.files("fux") / "templates" / name).read_bytes()
    except (FileNotFoundError, ModuleNotFoundError) as exc:  # pragma: no cover - broken install
        raise FuxError(
            f"the shipped fetcher {name!r} is missing from this install — "
            "reinstall fux-engine, or write .fux/fetchers/ yourself"
        ) from exc


def agent_template_bytes(name: str) -> bytes:
    """Read one shipped agent rendering out of the wheel. Read, never imported.

    Separate from `template_bytes` only because the error message has to name a
    different remedy: a missing fetcher means URL ingestion is broken, a
    missing rendering means the policy layer is.
    """
    try:
        return (resources.files("fux") / "templates" / "agents" / name).read_bytes()
    except (FileNotFoundError, ModuleNotFoundError) as exc:  # pragma: no cover - broken install
        raise FuxError(
            f"the shipped agent policy {name!r} is missing from this install — "
            "reinstall fux-engine, or run `fux setup --no-agents`"
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


def _agents_to_install(root: Path, requested: bool) -> tuple[str, ...]:
    """Which vendors this run writes for — **read, never sniffed**.

    `requested=False` is `--no-agents`: a one-shot escape that wins over the
    declaration. Its durable form is `install = []` in `fux.toml`.

    `fux.toml` may not exist yet (setup is the verb that writes it) and may be
    mid-edit, so a config that will not load degrades to the default rather
    than failing the whole run — `cmd_setup` re-loads it at the end and reports
    a broken file there, which is where that error belongs.
    """
    if not requested:
        return ()
    try:
        return load(root).agents
    except FuxError:
        return KNOWN_AGENTS


def _write_agents(root: Path, report: SetupReport, agents: tuple[str, ...]) -> None:
    for vendor in agents:
        for rel, template in AGENT_FILES[vendor]:
            path = root / rel
            before = len(report.written)
            _write_if_missing(path, agent_template_bytes(template), report, root)
            if len(report.written) > before:
                # Recorded at the moment of writing, from the same branch that
                # wrote it, so the announcement cannot drift out of step with
                # the filesystem. Veto condition 1 is exactly this list being
                # incomplete.
                report.outside.append(rel)


def run(root: Path, *, agents: bool = True) -> SetupReport:
    """Write the consumer-owned files, write-if-missing. Returns what happened.

    `agents=False` is `--no-agents`, and it must write **nothing** under
    `.github/`, `.kiro/` or `.claude/` — ADR-AGENT-POLICY veto condition 1a:
    the opt-out is the whole of a user's control over a default-on install, and
    a leak turns a default into a mandate.
    """
    # Imported here rather than at module level: `..tune` pulls in
    # `query.bm25f` for the defaults it quotes, and through it the whole query
    # package. `setup` never ranks anything, so paying for the ranker to write
    # a commented file is a cost with no return. There is no import cycle to
    # dodge — this is latency, in the same spirit as ADR-CLI decision 7.
    from .tune import TUNE_NAME, specimen

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
    # Every key commented out, so a fresh repo runs on the engine's own
    # defaults and the file is a menu rather than a configuration (ADR-TUNE
    # decisions 2 and 3). Write-if-missing like everything else here: this is
    # the file fux promised never to rewrite, and `fux tune` prints rather than
    # edits for the same reason.
    #
    # **Inside `.fux/`, so it is not a `report.outside` path.** That list is
    # for writes into directories other vendors own, which is what makes
    # announcing them mandatory; a file in fux's own directory is not one.
    _write_if_missing(root / TUNE_NAME, specimen().encode("utf-8"), report, root)

    # After `fux.toml`, so a first run reads the default this very call just
    # wrote out in full, and a later run reads whatever the consumer edited it
    # to (ADR-AGENT-POLICY decision 5).
    _write_agents(root, report, _agents_to_install(root, agents))
    return report


def cmd_setup(args) -> int:
    # The one verb that may run before a root exists: it is what *creates* the
    # marker (`fux.toml`), so requiring one first would be circular. Everywhere
    # else, no root is an error.
    root = find_root() or Path.cwd()
    report = run(root, agents=not getattr(args, "no_agents", False))
    for rel in report.written:
        print(f"  wrote {rel}")
    for rel in report.kept:
        print(f"  kept  {rel} (yours; never rewritten)")
    if not report.written:
        print("setup: nothing to do - every consumer-owned file is already here")
    else:
        print(
            f"setup: {len(report.written)} file(s) written. They are yours: commit them, "
            "edit them, fux will not rewrite them."
        )

    # ADR-AGENT-POLICY decision 6. The install is default-on, so **this
    # announcement is the entire remaining safeguard** — a user who did not
    # want these files must be able to learn they exist from the terminal they
    # just ran, not from a later `git status` on a repo they share with a team.
    # Veto condition 1 fires on any agent file written without appearing here.
    # ASCII only: these bytes reach a Windows console (ADR-CLI veto 7).
    if report.outside:
        print()
        print(
            f"  note: {len(report.outside)} of those are OUTSIDE .fux/ - they teach your "
            "agents how to read this index:"
        )
        for rel in report.outside:
            print(f"        {rel}")
        print(
            "        Turn them off with [agents] install = [] in fux.toml, "
            "or `fux setup --no-agents`."
        )

    load(root)  # a hand-edited fux.toml fails loudly here, not on the first ingest
    print("next: add entries to .fux/sources/dirs, then `fux ingest`")
    return 0
