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
from . import decode as decode_mod
from .errors import FuxError
from .ingest import fuxignore, refusals, sourcelist
from .ingest.urlsrc import DEFAULT_MAX_PARALLEL
from .store import fuxdir

#: Generated name -> the package-data file it is copied from.
FETCHERS = {"http.py": "http.py.txt", "cdp.py": "cdp.py.txt"}

#: The starter refusal rules, shipped as package data like the fetchers.
REFUSALS_TEMPLATE = "refusals.toml.txt"

FETCHERS_DIR = "fetchers"

#: W-86 P7. Every built-in decoder is copied here at setup and the copy is what
#: runs — see `decoder_source` for why there is no `.py.txt` template.
DECODERS_DIR = "decoders"

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
#: The repo-root, **vendor-neutral** agent file (W-82 ruling 16).
#:
#: ⚠ **Deliberately NOT in `AGENT_FILES`.** That map is keyed by vendor, and a
#: neutral file has none — put it under a vendor and all three race to write
#: the same path, and `--no-agents` would stop writing a file that is not any
#: vendor's. It gets its own slot for that reason.
#:
#: ⚠ **It stays POLICY-SHAPED and SHORT**, which is ruling 15 applied to
#: itself: Kiro loads `AGENTS.md` on every interaction, so a manual here is a
#: permanent context tax on every developer in the repo. It carries the
#: invocation ladder and the archived-results rule, and **points at** the
#: `fux-usage` skill instead of inlining it.
AGENTS_FILE = "AGENTS.md"
AGENTS_TEMPLATE = "AGENTS.md"

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
        (".claude/skills/fux-decoder/SKILL.md", "DECODER-SKILL.md"),
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
        # `fux-decoder` ships to the two SKILL surfaces and to neither ambient
        # one. ADR-ENRICH decision 10 made `fux-enrich` claude-only because the
        # other two renderings were ambient (`applyTo: "**"`, `inclusion:
        # always`) and *"an ambient skill that writes into a committed directory
        # and changes ranking is a different risk class"*. W-82 established that
        # a Kiro **skill** is progressive-disclosure, not ambient — only Kiro
        # *steering* is — so the reasoning admits Kiro here while still
        # excluding Copilot's `instructions/`, which enter every request.
        (".kiro/skills/fux-decoder/SKILL.md", "DECODER-SKILL.md"),
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
# Which files are documents, and which decoder reads each one. One glob per
# line; `!` subtracts. A pattern with no `/` matches the file NAME anywhere, so
# `*.md` means every markdown file.
#
# THIS FILE IS OPTIONAL. Delete it and the built-in default applies -- an
# absent file never means "index everything" and never means "index nothing".
# If the file IS here it REPLACES the default entirely, which is why a file
# with no active line is an error rather than a silently empty index.
#
# THE LINES BELOW ARE THAT DEFAULT, written out at `fux setup`: prose, plus
# every format a built-in decoder reads. They are spelled out rather than left
# implicit so you can see what fux considers a document without reading its
# source (ADR-TYPES decision 10). From here they are YOURS -- setup never
# rewrites this file, so the list stays exactly as you leave it.
#
# `decoder=` IS THE MAP: it BINDS an extension to the module that reads it.
# Without it, "which decoder reads .csv" is a property of the code installed on
# a machine -- a built-in's EXTENSIONS tuple, possibly replaced by a consumer
# module of the same name -- so two people with different .fux/decoders/ could
# commit different indexes from the same sources with nothing saying so. A
# binding makes the answer a committed line (ADR-TYPES decision 11).
#
# THE BINDING IS CHECKED, NOT TRUSTED. A line naming a module that does not
# exist stops the run, and so does one that takes an extension AWAY from the
# decoder that claims it and gives it to a module that does not. It is never a
# silent fallback: the wrong decoder does not fail visibly, it produces a
# plausible index with different postings.
#
# YOU CAN GIVE A DECODER A NEW EXTENSION. If nothing claims it, any decoder may
# be bound to it -- a .geojson is JSON, so `*.geojson decoder=jsondoc` is all it
# takes, with no module to copy or edit. EXTENSIONS is a decoder's DEFAULT
# CLAIM, not a list of what it can read. What is refused is REDIRECTING an
# extension another decoder already claims.
#
# A binding is per EXTENSION, so `decoder=` sits only on a bare `*.ext` line --
# dispatch sees a suffix and nothing about which glob admitted the file, so
# `docs/api/*.json decoder=jsondoc` would bind every .json in the corpus.
#
# A PROSE FORMAT CARRIES NO BINDING. It is already text and no decoder is in
# its path, so there is nothing to name.
#
# NOTHING BELOW NEEDS INSTALLING. fux's runtime is stdlib-only and declares no
# third-party dependencies, so every built-in decoder works out of the box. A
# format that needed something installed would appear under OPT-IN at the
# bottom, commented, with the command that enables it.
#
# What is OUT of the default, and why: source code, shell scripts and
# extensionless files. They have no decoder, machine data is not a document,
# and indexing it inflates `df` for exactly the terms your real documents are
# trying to be found by. Extensionless files are LICENSE, Makefile and
# Dockerfile far more often than they are prose.
#
# ADDING A DECODER DOES NOT WIDEN THIS. A decoder in .fux/decoders/ makes a
# format READABLE; a line here is what makes it INDEXED, and the binding on
# that line is what makes it read by a NAMED module. All three are separate on
# purpose -- what counts as a document stays a committed line a human wrote.
#
#   !*.min.md          # subtract a generated flavour
#
# See ADR-TYPES.
"""

_TYPES_OPT_IN = """\

# --- OPT-IN ---------------------------------------------------------------
# Not indexed until you uncomment. Nothing here has a built-in decoder, so a
# line you uncomment indexes RAW BYTES unless you enable it first by writing a
# decoder for it:
#
#   1. drop a decoder into .fux/decoders/  (`fux setup` writes every built-in
#      one there as a worked example; see the fux-decoder skill)
#   2. uncomment its glob here and add `decoder=<module stem>`
#   3. `fux ingest`
#
#*.log
"""

_FUXIGNORE = """\
# What fux does NOT index. Same grammar as .gitignore, and it is the ONE place
# exclusions belong -- this file is read before anything else, so a line here
# beats .fux/sources/dirs and .fux/sources/types both.
#
#   build/                 a DIRECTORY named build, at any depth (and all of it)
#   *.log                  a name glob; `*` never crosses a `/`
#   /notes.md              a leading `/` anchors at the repo root
#   docs/build             ANY `/` anchors -- this is not `build` at any depth
#   work/**/evidence       `**` is the explicit any-depth form
#   [0-9][0-9]-draft.md    character classes work; [!0-9] negates one
#   !keep.log              `!` RE-INCLUDES, exactly as in .gitignore
#
# LAST MATCH WINS, so order matters here and nowhere else in .fux/. And as in
# git, a file under an ignored DIRECTORY cannot be re-included: `build/` then
# `!build/keep.md` keeps nothing.
#
# `!` MEANS THE OPPOSITE HERE OF WHAT IT MEANS IN .fux/sources/. There `!`
# subtracts; here it adds back. That is the price of the file behaving like the
# one you already know. `fux ingest` warns if the same pattern is written in
# both places, which is where the confusion would actually bite.
#
# A `!` LINE OVERRIDES THE TYPE ALLOWLIST. `!*.py` really does index Python --
# as RAW BYTES, because no decoder claims .py, which is the exact shape
# .fux/sources/types exists to prevent. It takes a line you wrote to get there.
#
# ONE DIVERGENCE FROM GIT, ON PURPOSE: a `#` after whitespace starts a comment,
# so `*.log   # noisy` is a pattern plus a note. Git reads that whole line as a
# pattern and matches nothing.
#
# THIS FILE IS OPTIONAL AND STARTS EMPTY. Absent or all-comments means nothing
# is ignored -- unlike .fux/sources/types, where an empty file is an error,
# because this one only ever subtracts and so can never empty an index.
#
# See ADR-FUXIGNORE.
"""


_CONFIG = """\
# fux.toml -- POLICY, not corpus. What gets indexed is `.fux/sources/dirs`
# and `.fux/sources/urls`, one entry per line, so a 5k-entry corpus diffs and
# merges line by line. Every key below has a default; they are here to be seen
# rather than to be required.

[sources]
dirs_file = ".fux/sources/dirs"

# URL ingestion through YOUR fetcher files. Nothing is fetched until a URL is
# listed in .fux/sources/urls, and the only thing that lists one is an explicit
# `fux add <URL>` -- fux is offline by default, and THAT is the gate.
[sources.url]
fetcher      = ".fux/fetchers/http.py"  # the file a line with no `fetch=` uses,
                                        # and the directory `fetch=cdp` resolves in
urls_file    = ".fux/sources/urls"
meta         = "hashed"                 # the floor; a line may loosen it to plain

# HOW MANY URLs MAY BE IN FLIGHT AT ONCE, across `fux add <URL>`, `fux update`
# and `fux ingest --refresh-urls`. (`fux ask` verifies cited URLs one at a time,
# and `fux build` opens no socket at all -- neither is affected.)
#
# THIS KEY IS REQUIRED AND MAY NOT BE COMMENTED OUT. Every other key above has
# a default; this one does not, on purpose. A repo that CAN fetch has to say how
# hard, in a number a person can read, because the failure it prevents -- a
# hundred connections opened at your own intranet -- is not one you find out
# about by reading code. Comment it out and fux refuses to load and tells you so.
#
# THE EFFECTIVE VALUE IS min(this, what your fetcher declares). Your fetcher
# declares what is SAFE -- `MAX_PARALLEL` in the module, 8 for the shipped
# http.py, 1 for cdp.py because it reuses one WebSocket. This key is what is
# POLITE, and it is the one your intranet cares about.
#
# Raising it is honoured, never clamped: a bigger number is merely rude, and at
# 16+ fux says so on stderr rather than quietly reducing it. Below 1 refuses.
max_parallel = {default}

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
""".format(default=DEFAULT_MAX_PARALLEL)
#: ⚠ **`{default}` is interpolated, not typed** (W-83). The number in the
#: written `fux.toml` and the number the engine actually applies are the same
#: object, so the comment cannot drift from the behaviour the way the constant
#: itself did before W-83 made it effective. `tests/test_setup.py` asserts it.

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
    #: True when a hand-written repo-root `AGENTS.md` was found and left alone.
    #: **Announced rather than silently skipped** — W-82 ruling 16 consequence
    #: 2: write-if-missing makes the coverage absent precisely where a repo
    #: already has its own conventions, which is where it is most needed.
    skipped_agents_md: bool = False


def template_bytes(name: str) -> bytes:
    """Read one shipped fetcher out of the wheel. **Read, never imported.**"""
    try:
        return (resources.files("fux") / "templates" / name).read_bytes()
    except (FileNotFoundError, ModuleNotFoundError) as exc:  # pragma: no cover - broken install
        raise FuxError(
            f"the shipped fetcher {name!r} is missing from this install — "
            "reinstall fux-engine, or write .fux/fetchers/ yourself"
        ) from exc


def decoder_source(name: str) -> bytes:
    """One built-in decoder's source, read out of the installed package.

    **There is no `.py.txt` template for a decoder, and the asymmetry with the
    fetchers is deliberate.** A fetcher template must be un-importable because
    it carries network code that has no business inside an offline package
    (ADR-CDP-FETCHER decision 8). A decoder is stdlib-only and offline — it is
    already a legitimate module — so the module *is* the template, and there is
    exactly one copy of every decoder in the repo rather than two that agree by
    habit. That was the `_MdParser` defect, and repeating it sixteen times would
    be worse than committing it once.

    The modules use absolute imports for this reason: the bytes fux ships and
    the bytes the consumer edits are identical, and a path-loaded copy still
    resolves `fux.decode._zip`.
    """
    try:
        return (resources.files("fux") / "decode" / f"{name}.py").read_bytes()
    except (FileNotFoundError, ModuleNotFoundError) as exc:  # pragma: no cover
        raise FuxError(
            f"the built-in decoder {name!r} is missing from this install — "
            "reinstall fux-engine"
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


def agent_template_text(name: str) -> str:
    """The same template as text, for printing rather than writing.

    ASCII-only by ADR-CLI veto 7, which the shipped `AGENTS.md` already is —
    `agent_template_bytes` decoding cleanly as ASCII is asserted in tests.
    """
    return agent_template_bytes(name).decode("utf-8")


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


def _seed_types() -> bytes:
    """The type allowlist, with the built-in default spelled out as live lines.

    **A header alone is not a types file.** Every line of `_TYPES_HEADER` is a
    comment, and `read_types` treats a file with no active pattern as an error
    — so writing the header by itself made `fux setup` followed by `fux ingest`
    fail on every fresh repo. ADR-TYPES decision 10 always said this file ships
    "with the default spelled out"; it is spelled out here.

    **Derived, never transcribed.** The globs come from `DEFAULT_TYPES` at the
    moment setup runs, so the file cannot disagree with the engine that wrote
    it. What it does do is FREEZE: setup is write-if-missing, so a built-in
    decoder added later widens `DEFAULT_TYPES` and does not touch a repo that
    already has this file. That is decision 1a's rule applied to fux's own
    decoders — what counts as a document stays a committed line a human owns.
    """
    from .ingest.gitdir import DEFAULT_TYPES

    bindings = decode_mod.builtin_bindings()
    decoded = {f"*{ext}" for ext in bindings}
    prose = [glob for glob in DEFAULT_TYPES if glob not in decoded]
    body = ["", "# --- prose: already text, no decoder in the path ---"]
    body += sorted(prose)
    body += ["", "# --- decoded: extension -> the module that reads it ---"]
    body += [
        "# stdlib only, nothing to install. The binding on each line is what",
        "# dispatch resolves; fux checks it against the module it names.",
    ]
    # ⚠ **Grouped by decoder, not by extension.** Sorting the whole block
    # alphabetically puts `*.csv` next to `*.cfg`, which are read by different
    # modules, and splits `*.htm`/`*.html`/`*.xhtml` across the list. Grouping
    # is what makes the file legible AS a map; within a group the extensions
    # are still sorted, so the output stays a pure function of the registry.
    for name in sorted(set(bindings.values())):
        body.append("")
        body += [
            sourcelist.render_line(f"*{ext}", {"decoder": name}, sourcelist.TYPES)
            for ext in sorted(e for e, n in bindings.items() if n == name)
        ]
    return (_TYPES_HEADER + "\n".join(body) + "\n" + _TYPES_OPT_IN).encode("utf-8")


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


def _write_root_agents(root: Path, report: SetupReport) -> None:
    """Write `AGENTS.md`, or announce that we did not — W-82 ruling 16.

    ⚠ **`_write_if_missing` puts the coverage exactly where it is not needed.**
    A repo that already has a hand-written `AGENTS.md` gets nothing and, worse,
    no error — so the one place fux's guidance is most likely to be missing is
    the one place nothing says so. ADR-AGENT-POLICY decision 6 makes the
    announcement mandatory, so `skipped_agents_md` carries it and `fux setup`
    prints the snippet for the human to paste.
    """
    before = len(report.written)
    # ⚠ **No `.exists()` here, deliberately.** `_write_if_missing` already
    # decides, and `test_the_installer_never_branches_on_a_vendor_directory_existing`
    # asserts this region never sniffs the filesystem — *which agents install is
    # DECLARED, never sniffed*. Reading the outcome off the report keeps one
    # decision in one place instead of two that can disagree.
    _write_if_missing(root / AGENTS_FILE, agent_template_bytes(AGENTS_TEMPLATE), report, root)
    if AGENTS_FILE in report.kept:
        report.skipped_agents_md = True
    if len(report.written) > before:
        # Repo root is outside `.fux/`, so decision 6's announcement applies
        # exactly as it does to `.github/` and `.kiro/`.
        report.outside.append(AGENTS_FILE)


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
    from .output_config import OUTPUT_NAME, specimen as output_specimen

    report = SetupReport()
    for path in fuxdir.ensure_layout(root):
        report.written.append(path.relative_to(root).as_posix())

    directory = fuxdir.fux_dir(root)
    for name, template in FETCHERS.items():
        _write_if_missing(directory / FETCHERS_DIR / name, template_bytes(template), report, root)

    # W-86 P7, ruled by Arpit 2026-08-26: every built-in decoder is written into
    # `.fux/decoders/`, and **the copy is what runs** (ADR-DECODE decision 11).
    for name in decode_mod.BUILTIN_MODULES:
        _write_if_missing(
            directory / DECODERS_DIR / f"{name}.py", decoder_source(name), report, root
        )

    _write_if_missing(root / DEFAULT_DIRS_FILE, _seed_dirs(root), report, root)
    # Written with the default spelled out as LIVE lines rather than left
    # implicit: a consumer should be able to see what fux considers a document
    # without reading its source (ADR-TYPES decision 10), and a file of nothing
    # but comments is one `read_types` rejects — see `_seed_types`.
    _write_if_missing(root / DEFAULT_TYPES_FILE, _seed_types(), report, root)
    _write_if_missing(root / DEFAULT_URLS_FILE, _URLS_HEADER.encode("utf-8"), report, root)
    # Header only, no patterns: an ignore file that arrives with guesses in it
    # is one whose first act is to hide a document nobody asked it to hide.
    # Empty is a legal, meaningful state here (ADR-FUXIGNORE decision 6) in a
    # way it is not for `types`, so the seed can be honest about knowing
    # nothing. Write-if-missing like the rest -- `fux setup` never rewrites it.
    _write_if_missing(root / fuxignore.IGNORE_FILE, _FUXIGNORE.encode("utf-8"), report, root)
    # ADR-REFUSAL: policy, not code. Written once, never rewritten -- the rules
    # in it are the consumer's to delete, including the vendor ones.
    _write_if_missing(
        refusals.rules_path(root), template_bytes(REFUSALS_TEMPLATE), report, root
    )
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
    # ADR-OUTPUT decision 1: the same contract as `tune.toml`, one boundary
    # further in — tune changes WHICH documents come back, this changes how
    # they are SHOWN. Write-if-missing for the same reason, and `fux output`
    # prints rather than edits.
    _write_if_missing(root / OUTPUT_NAME, output_specimen().encode("utf-8"), report, root)

    # After `fux.toml`, so a first run reads the default this very call just
    # wrote out in full, and a later run reads whatever the consumer edited it
    # to (ADR-AGENT-POLICY decision 5).
    installing = _agents_to_install(root, agents)
    _write_agents(root, report, installing)
    # ⚠ **Gated on the RESOLVED set, not on the `agents` flag.** `--no-agents`
    # is one opt-out; a `[agents] install = []` declaration is the other, and a
    # repo-root file is the most visible thing either could leak
    # (ADR-AGENT-POLICY veto 1a). ⚠ **And only when EVERY vendor installs**: a
    # partial declaration names what it wants, and a neutral file nobody named
    # is not covered by that naming.
    if installing == KNOWN_AGENTS:
        _write_root_agents(root, report)
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
    if report.skipped_agents_md:
        # W-82 ruling 16 consequence 2. The snippet is printed rather than
        # merged: `AGENTS.md` is the consumer's file and fux does not edit
        # files it did not write.
        print()
        print(
            "  note: this repo already has AGENTS.md, so fux left it alone.\n"
            "        Agents read it on every interaction, so nothing here tells\n"
            "        them the index exists. Paste this into it:"
        )
        print()
        for line in agent_template_text(AGENTS_TEMPLATE).splitlines():
            print(f"    {line}" if line else "")
        print()
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
    print("      anything you do NOT want indexed goes in .fux/.fuxignore")
    return 0
