"""`fux setup` — write the files a consumer owns, once, and never again.

Scaffolding has **two moments**, and the split is the whole point of this
module existing (SR-DOTFUX decision 6, SR-FETCHER decision 6):

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
never imported — which makes SR-FETCHER's adapter cap structural rather than a
rule someone has to remember. A fetcher fux imports is a fetcher fux owns.

Everything here is **write-if-missing**. An edited `http.py` survives every
later `fux setup`, exactly as an annotated `.fux/README.md` survives every
ingest.

This is also the one verb that may run before a repo root exists — it is what
writes the `fux.toml` that *makes* a directory a root, so demanding one first
would be circular. Every other verb errors without one.
"""

from __future__ import annotations

import json
import os
import re
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
from .ingest import fuxignore, pii, refusals
from .ingest.urlsrc import DEFAULT_MAX_PARALLEL
from .store import fuxdir

#: Generated name -> the package-data file it is copied from.
FETCHERS = {"http.py": "http.py.txt", "cdp.py": "cdp.py.txt"}

#: The starter refusal rules, shipped as package data like the fetchers.
REFUSALS_TEMPLATE = "refusals.toml.txt"
PII_TEMPLATE = "pii.toml.txt"
#: The scaffolded `fux.toml`, shipped the same way. See `config_text`.
CONFIG_TEMPLATE = "fux.toml.txt"

FETCHERS_DIR = "fetchers"

#: W-86 P7. Every built-in decoder is copied here at setup and the copy is what
#: runs — see `decoder_source` for why there is no `.py.txt` template.
DECODERS_DIR = "decoders"

#: What `fux setup` writes into `.fux/observers/`.
_OBSERVERS_README = """\
# `.fux/observers/` — tell your analytics what fux did, never what it read

Drop a `*.py` file here with one function:

```python
def observe(record: dict) -> None:
    ...  # append `record` somewhere; the return value is discarded
```

After a fux verb has **fully rendered** — stdout flushed, exit code fixed —
every file here is called once, in sorted filename order, with one record:

    verb · args_hash · band · answerable · n_results · n_related
    refer_verdicts · ms · expand_used · q_arms · fux_version

## What is NOT in it, and will not be

The question. Any `--expand` text. A document id, a path, a snippet, the
answer. Every value is a count, a boolean, a fixed name, or a hash — so this
hook can tell you how fux is being used and can never tell you what anyone
looked for. `args_hash` excludes the question too: it is a hash of the
normalised FLAGS, so you can join a run to a command without fingerprinting
the query.

## What it cannot do

Change anything. There is no return path, the record is a copy, and the
dispatch runs after every write the verb makes. An observer that raises is
skipped for that run; one that is slow is abandoned at `[observe] max_ms` in
`fux.toml`. Your analytics cannot make `fux ask` wrong, and cannot make it
slow.

`fux doctor` lists the files here and whether each one fired on the last run.
"""

#: W-170. `.fux/observers/` — the third readable-source extension point, beside
#: the two above. **Seeded with a README and no observer**, and the asymmetry
#: with `decoders`/`fetchers` is deliberate: a decoder and a fetcher have
#: useful built-in implementations, and an observer has none. fux carries no
#: knowledge of any subscriber (SR-OBSERVE decision 8), so there is nothing for
#: it to write here — a subscriber's own `setup` drops its own file in.
OBSERVERS_DIR = "observers"

#: vendor -> ((destination relative to the repo root, template under
#: `templates/agents/`), …) — SR-AGENT-POLICY decisions 3 and 4.
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

#: The begin marker of the verbatim policy block, matched by PREFIX exactly as
#: `tests/test_agent_policy_agreement.py` matches it — the marker line carries a
#: trailing reminder, so the full line is not a stable string to compare.
POLICY_BEGIN = "<!-- fux:policy:begin v1"

#: **The operating guides** (SR-AGENT-POLICY decision 15, Arpit 2026-09-11):
#: one skill per job the CLI supports, written to every skill surface from ONE
#: template each -- decision 10's agreement by construction, ten more times.
#: `fux-usage` stays the router and points at these by name.
#:
#: ⚠ **The last four write committed files that change the index**
#: (`fux-sources`, `fux-config`, `fux-fetcher`, `fux-pii`). Like `fux-decoder`
#: and `fux-enrich` they ship as SKILLS -- invoked, never ambient (decision 9a).
GUIDE_SKILLS: tuple[tuple[str, str], ...] = (
    ("fux-search", "SEARCH-SKILL.md"),
    ("fux-answer", "ANSWER-SKILL.md"),
    ("fux-graph", "GRAPH-SKILL.md"),
    ("fux-index", "INDEX-SKILL.md"),
    ("fux-maintain", "MAINTAIN-SKILL.md"),
    ("fux-mcp", "MCP-SKILL.md"),
    ("fux-sources", "SOURCES-SKILL.md"),
    ("fux-config", "CONFIG-SKILL.md"),
    ("fux-fetcher", "FETCHER-SKILL.md"),
    ("fux-pii", "PII-SKILL.md"),
    # `fux-inspect` writes nothing at all -- it is the only guide here whose
    # verb is read-only end to end (SR-INSPECT decision 1). It still ships as a
    # SKILL rather than as ambient steering: its whole job is to be reached
    # when somebody asks about the shape of a corpus, and an agent that read it
    # on every request would start volunteering index critiques.
    ("fux-inspect", "INSPECT-SKILL.md"),
    # `fux-correct` writes COMMITTED files and changes what the index holds, so
    # it is a skill and never ambient (decision 9a) -- and its own first
    # section is *propose the command, do not run it*, because the moment an
    # agent notices a bad result is exactly when it would be tempted to.
    ("fux-correct", "CORRECT-SKILL.md"),
)

#: **Path-scoped pointers** (decision 15): a short rule that loads when an agent
#: works on one of fux's own committed files, and names the skill that holds the
#: procedure. Same body on three vendors, native frontmatter on each -- Kiro
#: `inclusion: fileMatch`, Claude `.claude/rules/` `paths:`, Copilot
#: `applyTo:` with explicit globs (never `"**"`). Codex has no path-scoped
#: surface, so it gets none (its skills carry the same rules).
#:
#: ⚠ **On a Kiro CLI without inclusion-mode support every steering file is
#: ambient.** That cost is why each pointer is byte-bounded by a test and holds
#: rules and a pointer, never a procedure.
PATH_SCOPED_TOPICS: tuple[str, ...] = (
    "sources", "decoder", "enrich", "fetcher", "pii", "config", "index",
)

#: **Kiro auto-steering guides** (decision 15): `inclusion: auto`, loaded when a
#: request matches the description. Kiro-only -- Claude, Codex and Copilot
#: already get description-triggered loading from their skills. **Jobs that
#: write nothing committed only**: `index` (setup, ingest) and `maintain`
#: (hooks, `.gitattributes`) are excluded for the same reason the committed-write
#: planes are -- a description match can fire on a request that edits nothing.
AUTO_GUIDE_TOPICS: tuple[str, ...] = (
    "usage", "search", "answer", "graph", "mcp",
)


def _guide_skills(surface: str) -> tuple[tuple[str, str], ...]:
    return tuple((f"{surface}/{name}/SKILL.md", tpl) for name, tpl in GUIDE_SKILLS)


#: The one skill directory **Codex and Copilot both read** (SR-AGENT-POLICY
#: decision 16, Arpit 2026-09-12). Codex reads repository skills from
#: `.agents/skills` and nowhere else; Copilot reads `.github/skills`,
#: `.claude/skills` and `.agents/skills`.
#: <https://developers.openai.com/codex/skills> ·
#: <https://docs.github.com/en/copilot/concepts/agents/about-agent-skills>
SHARED_SKILL_SURFACE = ".agents/skills"

#: ⚠ **ONE tuple, used by both vendors' rows** -- so the two rosters cannot drift
#: apart, which is decision 10's agreement-by-construction applied to a row
#: rather than to bytes. Everything a vendor needs is still in its own row:
#: `install = ["codex"]` and `install = ["copilot"]` each get the full set.
#: `fux-archived-results` is deliberately absent -- it is ambient policy, and
#: reaches Codex through `AGENTS.md` and Copilot through `instructions/`.
SHARED_SKILLS: tuple[tuple[str, str], ...] = (
    (f"{SHARED_SKILL_SURFACE}/fux-enrich/SKILL.md", "ENRICH-SKILL.md"),
    (f"{SHARED_SKILL_SURFACE}/fux-usage/SKILL.md", "USAGE-SKILL.md"),
    (f"{SHARED_SKILL_SURFACE}/fux-decoder/SKILL.md", "DECODER-SKILL.md"),
    *_guide_skills(SHARED_SKILL_SURFACE),
)


#: **The five Claude-native surfaces beyond the document kinds**
#: (SR-AGENT-SURFACES decision 2, Arpit 2026-09-14). Skills, steering, rules,
#: instructions and `agents` files all INSTRUCT; these five do something else --
#: they fire on a tool call, gate a permission, are invoked by name, run as a
#: scoped agent, or shape a reply. They are **Claude-only on purpose**: no other
#: vendor fux ships to has an equivalent, and inventing one would be a rendering
#: with nothing to render into.
#:
#: WARNING **Every one goes through `_write_if_missing`.** A consumer's own
#: `settings.json`, hook or command is never touched -- decision 6's rule, and
#: the reason `settings.json` gets the `AGENTS.md` treatment (write if absent,
#: announce the snippet if not) rather than a merge nobody asked for.
#: WARNING **The Claude-only claim was FALSE and is corrected here**
#: (SR-AGENT-SURFACES decision 3a, 2026-09-14). Codex, Kiro and Copilot all ship
#: repo-level acting surfaces. Two real bounds survive: output styles are
#: Claude-only, and Codex slash-prompts live in `~/.codex/prompts/` and are
#: "not shared through your repository", so fux cannot write one.
KIRO_SURFACES: tuple[tuple[str, str], ...] = (
    (".kiro/hooks/fux-index-hint.json", "kiro-hook-fux-index-hint.json"),
    (".kiro/hooks/fux-index-hint.sh", "hook-fux-index-hint.sh"),
    (".kiro/agents/fux-researcher.md", "kiro-agent-fux-researcher.md"),
)

#: WARNING `.codex/hooks.json` is a whole-file config a consumer may already
#: own -- CO_OWNED, like `.claude/settings.json`. Its subagent is not.
CODEX_SURFACES: tuple[tuple[str, str], ...] = (
    (".codex/hooks.json", "codex-hooks.json"),
    (".codex/hooks/fux-index-hint.sh", "hook-fux-index-hint.sh"),
    (".codex/agents/fux-researcher.md", "codex-agent-fux-researcher.md"),
)

#: Copilot has no hook surface. It has the richest COMMAND surface of the four
#: -- prompt files carry `argument-hint` and `tools` natively -- and an agent
#: surface versioned by commit SHA that works in the IDE, the CLI and the cloud.
COPILOT_SURFACES: tuple[tuple[str, str], ...] = (
    (".github/prompts/fux-search.prompt.md", "copilot-prompt-fux-search.prompt.md"),
    (".github/prompts/fux-answer.prompt.md", "copilot-prompt-fux-answer.prompt.md"),
    (".github/prompts/fux-verify.prompt.md", "copilot-prompt-fux-verify.prompt.md"),
    (".github/agents/fux-researcher.md", "copilot-agent-fux-researcher.md"),
)

CLAUDE_SURFACES: tuple[tuple[str, str], ...] = (
    (".claude/hooks/fux-index-hint.sh", "hook-fux-index-hint.sh"),
    (".claude/commands/fux-search.md", "command-fux-search.md"),
    (".claude/commands/fux-answer.md", "command-fux-answer.md"),
    (".claude/commands/fux-verify.md", "command-fux-verify.md"),
    (".claude/agents/fux-researcher.md", "subagent-fux-researcher.md"),
    (".claude/output-styles/fux-cited.md", "output-style-fux-cited.md"),
    (".claude/settings.json", "settings-claude.json"),
)

#: Surfaces the CONSUMER owns and fux only seeds. Written when absent, never
#: over an existing file, and deliberately **exempt from the template drift
#: test**: this repo's own `.claude/settings.json` carries deny rules and hooks
#: that are nothing to do with fux, and so will every real consumer's.
#: SR-AGENT-SURFACES decision 6.
CO_OWNED_SURFACES: frozenset[str] = frozenset(
    {".claude/settings.json", ".codex/hooks.json"}
)

#: The one surface above that must be **executable** to do anything at all.
#: A hook written 0644 fails silently: the runner reports nothing and the hint
#: never appears.
EXECUTABLE_SURFACES: frozenset[str] = frozenset(
    {
        ".claude/hooks/fux-index-hint.sh",
        ".kiro/hooks/fux-index-hint.sh",
        ".codex/hooks/fux-index-hint.sh",
    }
)

AGENT_FILES: dict[str, tuple[tuple[str, str], ...]] = {
    # `fux-enrich` is **INVOKED, never ambient** (W-76 Phase 8) -- and the rule
    # is *never ambient*, which was never the same thing as *claude only*.
    #
    # **An ambient rendering that writes files into a committed directory and
    # changes ranking is a different risk class.** Copilot's `applyTo: "**"`
    # and Kiro's `inclusion: always` enter every request for every developer in
    # the repo, so `ENRICH-SKILL.md` never goes to either, and its description
    # names trigger phrases rather than a topic.
    #
    # ⚠ **It shipped to Claude ALONE until 2026-09-06, and that was an
    # omission, not the rule.** Every skill surface below is
    # progressive-disclosure -- `.claude/skills`, `.kiro/skills` and the
    # `.agents/skills` Codex and Copilot share (decision 16) -- so the risk
    # class the rule names is absent from every one of them. SR-ENRICH decision 10 had **flagged the
    # gap in its own text** rather than leaving it to be discovered
    # (*"the reasoning that admits a Kiro skill elsewhere would admit one
    # here"*), and `fux-decoder` -- named in the SAME sentence, in the same
    # risk class -- had already shipped to three of them. Arpit ruled
    # 2026-09-06: extend it. **The exclusion that survives is the ambient one,
    # and only that one.**
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
        *_guide_skills(".claude/skills"),
        *((f".claude/rules/fux-{t}-files.md", f"rule-fux-{t}-files.md") for t in PATH_SCOPED_TOPICS),
        *CLAUDE_SURFACES,
    ),
    "copilot": (
        (".github/agents/fux.agent.md", "fux.agent.md"),
        (
            ".github/instructions/fux-archived-results.instructions.md",
            "fux-archived-results.instructions.md",
        ),
        (".github/instructions/fux-usage.instructions.md", "fux-usage.instructions.md"),
        # ⚠ **`.agents/skills/` is Copilot's non-ambient skill surface, and it is
        # SHARED with Codex** (SR-AGENT-POLICY decision 16, Arpit 2026-09-12).
        # Copilot reads project skills from `.github/skills`, `.claude/skills`
        # **and** `.agents/skills`; Codex reads `.agents/skills` **only**. One
        # directory both read, instead of `.github/skills` for Copilot and a
        # second for Codex, keeps Copilot at TWO same-name copies (this one plus
        # the `.claude/skills` cross-read, decision 13) instead of three.
        #
        # ⚠ **Written for Copilot as well as Codex**, although the paths are the
        # same: `install = ["copilot"]` **alone** must not silently get nothing
        # (decision 14). `_write_agents` writes a shared path once.
        #
        # ⚠ **`fux-usage` also reaches Copilot AMBIENTLY**, one line above, as
        # `instructions/fux-usage.instructions.md`. The skill is **additive, not
        # a replacement**: the instructions file is `applyTo: "**"` prose that
        # says *resolve the binary, read the JSON*; the skill is the
        # progressive-disclosure operating manual Claude, Kiro and Codex get.
        # Removing either would make Copilot the one vendor missing one of them.
        *SHARED_SKILLS,
        *(
            (f".github/instructions/fux-{t}-files.instructions.md", f"fux-{t}-files.instructions.md")
            for t in PATH_SCOPED_TOPICS
        ),
        *COPILOT_SURFACES,
    ),
    "kiro": (
        (".kiro/steering/fux-archived-results.md", "steering-fux-archived-results.md"),
        (".kiro/skills/fux-usage/SKILL.md", "USAGE-SKILL.md"),
        # Both committed-write skills ship to Kiro's SKILL surface and to
        # neither ambient one. W-82 established that a Kiro **skill** is
        # progressive-disclosure, not ambient — only Kiro *steering* is — which
        # is what admits them here while still excluding Copilot's
        # `instructions/`, which enter every request. ⚠ `fux-enrich` was
        # missing from this pair until 2026-09-06 on no surviving argument;
        # see the header comment.
        (".kiro/skills/fux-decoder/SKILL.md", "DECODER-SKILL.md"),
        (".kiro/skills/fux-enrich/SKILL.md", "ENRICH-SKILL.md"),
        *_guide_skills(".kiro/skills"),
        *((f".kiro/steering/fux-{t}-files.md", f"steering-fux-{t}-files.md") for t in PATH_SCOPED_TOPICS),
        *((f".kiro/steering/fux-{t}-guide.md", f"steering-fux-{t}-guide.md") for t in AUTO_GUIDE_TOPICS),
        *KIRO_SURFACES,
    ),
    # **Codex is decision 3 EXERCISED, not amended** — *"adding a fourth is a
    # template plus a rendering plus a row, not a new decision"*. It costs no
    # new template: Codex reads repository skills from
    # `.agents/skills/<name>/SKILL.md` (decision 16 -- it was `.codex/skills`
    # here until 2026-09-12, a path Codex's docs no longer list), the same open
    # Agent Skills standard
    # Claude and Kiro implement, so the identical `USAGE-SKILL.md` and
    # `DECODER-SKILL.md` bytes are valid here. That is decision 10's
    # agreement-by-construction for a third and fourth mapping.
    #
    # ⚠ **Codex has NO per-file ambient surface** — no `applyTo:`, no inclusion
    # mode. Its always-on context is the repo-root `AGENTS.md` and nothing
    # else. So the archived-results policy reaches Codex through `AGENTS.md`,
    # which already carries the verbatim block, and there is deliberately **no**
    # `.agents/skills/fux-archived-results/`: decision 9's test is *does an agent
    # that has never heard of Fux still need this sentence to avoid being
    # wrong?* — yes, and a skill has to be loaded to apply.
    # **`AGENTS_MD_VENDORS` below is the consequence**, and it is not optional.
    #
    "codex": SHARED_SKILLS + CODEX_SURFACES,
}

#: Vendors whose ONLY always-on surface is the repo-root `AGENTS.md`.
#:
#: ⚠ **This exists because a partial declaration would otherwise strand one,
#: silently.** `run()` writes the vendor-neutral root file only when every known
#: vendor installs — a partial declaration names what it wants, and a neutral
#: file nobody named is not covered by that naming (W-82 ruling 16). That
#: reasoning holds for Claude, Copilot and Kiro: each has its own ambient or
#: skill plane, so a narrowed declaration still delivers the archived-results
#: policy. **It does not hold for Codex.** `install = ["codex"]` would write two
#: skills and **no archived-results policy at all** — the exact silent failure
#: SR-AGENT-POLICY decision 1 exists to close, reintroduced by a config line.
AGENTS_MD_VENDORS = ("codex",)

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
# See SR-DIR-LIST.
"""

_TYPES_HEADER = """\
# Which files are documents, and which decoder reads each one. See SR-TYPES.
#
# THIS FILE IS OPTIONAL. Delete it and the built-in default applies -- an
# absent file never means "index everything" and never means "index nothing".
# If the file IS here it REPLACES the default entirely, which is why a file
# that admits nothing is an error rather than a silently empty index.
#
# WHAT IS BELOW IS THAT DEFAULT, written out at `fux setup`: prose, plus every
# format a built-in decoder reads. It is spelled out rather than left implicit
# so you can see what fux considers a document without reading its source
# (SR-TYPES decision 10). From here it is YOURS -- setup never rewrites this
# file, so the list stays exactly as you leave it.
#
# TWO KEYS, AND ONLY TWO. `include` lists globs that are already text.
# `[decoders]` maps an extension to the module that reads it -- and a bound
# extension IS a document, so it is never repeated in `include`. Any other key
# is an error (SR-TYPES decision 12).
#
# NOTHING HERE SUBTRACTS. To keep files out, write the pattern in
# .fux/.fuxignore, which is read first and outranks this file.
#
# NOTHING BELOW NEEDS INSTALLING. Every built-in decoder is stdlib-only and
# works out of the box. A format that needed something installed would appear
# under OPT-IN at the bottom, commented, with what enables it.
#
# What is OUT of the default, and why: source code, shell scripts and
# extensionless files. They have no decoder, machine data is not a document,
# and indexing it inflates `df` for exactly the terms your real documents are
# trying to be found by. Extensionless files are LICENSE, Makefile and
# Dockerfile far more often than they are prose.
#
# ADDING A DECODER DOES NOT WIDEN THIS. A decoder in .fux/decoders/ makes a
# format READABLE; an entry here is what makes it INDEXED, and a `[decoders]`
# binding is what makes it read by a NAMED module. All three are separate on
# purpose -- what counts as a document stays a committed line a human wrote.
"""

_TYPES_INCLUDE_NOTE = """\
# Already text: no decoder in the path. One glob per line. A glob with no `/`
# matches the file NAME anywhere, so "*.md" means every markdown file.
"""

_TYPES_DECODERS_NOTE = """\
# extension = "decoder module". THIS IS THE MAP: without it, "which decoder
# reads .csv" is a property of the code installed on a machine, and two people
# with different .fux/decoders/ could commit different indexes from the same
# sources with nothing saying so (SR-TYPES decision 11).
#
# THE BINDING IS CHECKED, NOT TRUSTED. A module that does not exist stops the
# run, and so does taking an extension AWAY from the decoder that claims it and
# giving it to one that does not. It is never a silent fallback: the wrong
# decoder does not fail visibly, it produces a plausible index with different
# postings.
#
# YOU CAN GIVE A DECODER A NEW EXTENSION. If nothing claims it, any decoder may
# be bound to it -- a .geojson is JSON, so `geojson = "json"` is all it takes.
# An extension with a dot is quoted: `"tar.gz" = "<module>"`.
"""

_TYPES_OPT_IN = """\
# --- OPT-IN ---------------------------------------------------------------
# Not indexed until you uncomment. Nothing here has a built-in decoder, so
# enable it first by writing one:
#
#   1. drop a decoder into .fux/decoders/  (`fux setup` writes every built-in
#      one there as a worked example; see the fux-decoder skill)
#   2. uncomment its line and name your module
#   3. `fux ingest`
#
# Listing "*.log" under `include` instead indexes it as RAW BYTES.
#
# log = "<your module>"
"""

_TYPES_CONVERTED_HEADER = """\
# Which files are documents, and which decoder reads each one. See SR-TYPES.
#
# CONVERTED by `fux setup` from .fux/sources/types, the line-grammar list this
# file replaced on 2026-09-11 (SR-TYPES decision 12). It states exactly what
# that file stated: every `*.ext decoder=<module>` line is a `[decoders]`
# binding, every other pattern is an `include` glob, and every `!` line moved
# to .fux/.fuxignore. Delete .fux/sources/types -- fux refuses to run while it
# exists, rather than guess which of the two you meant.
#
# TWO KEYS, AND ONLY TWO: `include` and `[decoders]`. A bound extension IS a
# document, so it is never repeated in `include`. Nothing here subtracts --
# exclusions live in .fux/.fuxignore.
"""


_FUXIGNORE = """\
# What fux does NOT index. Same grammar as .gitignore, and it is the ONE place
# exclusions belong -- this file is read before anything else, so a line here
# beats .fux/sources/dirs and .fux/formats.toml both.
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
# `!` MEANS THE OPPOSITE HERE OF WHAT IT MEANS IN .fux/sources/dirs. There `!`
# subtracts; here it adds back. That is the price of the file behaving like the
# one you already know. `fux ingest` warns if the same pattern is written in
# both places, which is where the confusion would actually bite.
#
# A `!` LINE OVERRIDES THE TYPE ALLOWLIST. `!*.py` really does index Python --
# as RAW BYTES, because no decoder claims .py, which is the exact shape
# .fux/formats.toml exists to prevent. It takes a line you wrote to get there.
#
# ONE DIVERGENCE FROM GIT, ON PURPOSE: a `#` after whitespace starts a comment,
# so `*.log   # noisy` is a pattern plus a note. Git reads that whole line as a
# pattern and matches nothing.
#
# THIS FILE IS OPTIONAL AND STARTS EMPTY. Absent or all-comments means nothing
# is ignored -- unlike .fux/formats.toml, where an empty file is an error,
# because this one only ever subtracts and so can never empty an index.
#
# See SR-FUXIGNORE.
"""


def _toml_scalar(value) -> str:
    """One Python default as the TOML literal a consumer would have typed."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, (tuple, list)):
        return "[" + ", ".join(_toml_scalar(v) for v in value) + "]"
    raise TypeError(type(value).__name__)


def fetcher_defaults(name: str) -> "dict[str, object]":
    """A shipped fetcher's tunables and their current defaults — **read by
    `ast`, never executed.**

    ⚠ **The fetchers are package data precisely so they are not imported**
    (SR-CDP-FETCHER decision 8): `cdp.py` carries network code that has no
    business running inside an offline package, and `fux setup` is the last
    place that should launch a browser. So this parses the file and reads two
    things statically: the `_SETTINGS` map (config key -> module global) and
    the module-level assignment to each of those globals.

    **Derived, never transcribed.** The alternative was typing the values into
    `templates/fux.toml.txt`, and this repo has already paid for that once —
    `_urls_header()` below carries the same lesson (W-140 row 18: the table was
    transcribed and went stale).

    A value whose default is not a plain literal is skipped rather than
    guessed: a key absent from the scaffolded file falls back to the fetcher's
    own constant, which is correct, where a wrong literal would not be.
    """
    import ast

    tree = ast.parse(template_bytes(name).decode("utf-8"))
    globals_: dict[str, object] = {}
    settings: dict[str, str] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        if target.id == "_SETTINGS" and isinstance(node.value, ast.Dict):
            for k, v in zip(node.value.keys, node.value.values):
                if isinstance(k, ast.Constant) and isinstance(v, ast.Tuple) and v.elts:
                    first = v.elts[0]
                    if isinstance(first, ast.Constant):
                        settings[k.value] = first.value
            continue
        try:
            globals_[target.id] = ast.literal_eval(node.value)
        except (ValueError, SyntaxError):
            continue  # a computed default -- the fetcher's own value stands
    out: dict[str, object] = {}
    for key, global_name in settings.items():
        if global_name in globals_:
            out[key] = globals_[global_name]
    return out


def url_config_tables() -> str:
    """`[sources.url.config]` and one sub-table per shipped fetcher.

    ⚠ **Two tables, because one was BROKEN for any repo using both** (Arpit,
    2026-09-14). The single flat table went verbatim to every fetcher and each
    `configure()` raises on a key it does not know, so `cdp_port` made
    `http.py` refuse and `timeout_s` made `cdp.py` refuse. The scaffolded file
    could only ever comment the block out, which is how it shipped.

    The shared table stays, and stays **empty in the scaffold**: a key belongs
    there only when every fetcher a repo loads knows it, and fux cannot know
    that for a fetcher somebody writes tomorrow.
    """
    lines = [
        "# Handed to your fetcher's configure() verbatim; fux reads no key inside.",
        "# A key at THIS level goes to every fetcher -- only put one here that all",
        "# of yours know, because each configure() refuses a key it does not.",
        "[sources.url.config]",
        "",
    ]
    for generated, template in sorted(FETCHERS.items()):
        stem = generated.removesuffix(".py")
        defaults = fetcher_defaults(template)
        if not defaults:  # pragma: no cover - a fetcher with no tunables
            continue
        lines.append(f"# Only .fux/fetchers/{generated} receives these.")
        lines.append(f"[sources.url.config.{stem}]")
        width = max(len(k) for k in defaults)
        for key in sorted(defaults):
            lines.append(f"{key.ljust(width)} = {_toml_scalar(defaults[key])}")
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def config_text() -> str:
    """The scaffolded `fux.toml`, read out of the wheel like every other starter.

    ⚠ **It was a triple-quoted constant in this module until 2026-09-14**
    (Arpit: *"create a template for fux.toml file like others"*). It is now
    `templates/fux.toml.txt`, beside `pii.toml.txt`, `refusals.toml.txt` and
    the two fetchers — **read, never imported**, which for a `.toml` is a
    statement about where it lives rather than about safety: a starter a
    consumer is meant to read and edit belongs in a file they can open, not
    inside a Python string where a stray quote is a syntax error in the engine.

    ⚠ **`{default}` is SUBSTITUTED, not `.format`ted** (W-83's property, a
    safer mechanism). The number in the written `fux.toml` and the number the
    engine applies are the same object, so the file cannot drift from the
    behaviour. `str.replace` rather than `str.format` **because the template is
    now an editable file**: `format` would raise on any future `{` someone adds
    to a comment, turning a doc edit into a broken `fux setup`.
    `tests/test_setup.py` asserts the substitution happened.
    """
    text = template_bytes(CONFIG_TEMPLATE).decode("utf-8")
    text = text.replace("{default}", str(DEFAULT_MAX_PARALLEL))
    return text.replace("{url_config}", url_config_tables())

def _urls_header() -> str:
    """The starter `.fux/sources/urls`, with its attribute table DERIVED.

    ⚠ **It was transcribed, and it went stale** (W-140 row 18, fixed
    2026-09-11). The header said *"Two attributes, and the set is closed"*
    while the spec had grown to seven — `keep`, `ttl`, `enrich`, `archived`
    and `update` all landed after it was written — and it said
    *"`fux update` re-fetches every line"*, which stopped being true when
    narrow-by-default landed (W-82 ruling 3) and again when `update=never` did.
    Every repo set up in between got both sentences committed into it.
    ⚠ **The verb in that quote is `update` because that is what it SAID**; the
    verb it names is `fux ingest` from 2026-09-15 (W-177), and a rename that
    silently corrected the history would hide the defect this docstring exists
    to record.

    `_seed_types` already had the rule: **derived, never transcribed**, so the
    file cannot disagree with the engine that wrote it.
    """
    from .ingest.sourcelist import URLS

    pairs = [
        (f"{a.name}={'|'.join(a.values) if a.values else '<duration>'}", a.default)
        for a in URLS.attributes
    ]
    width = max(len(spelling) for spelling, _ in pairs)
    table = "\n".join(f"#   {spelling:<{width}}  default {default}" for spelling, default in pairs)
    return f"""\
# The URLs fux indexes. One per line. `#` starts a comment at the start of a
# line or after whitespace -- NOT inside a URL, so a fragment survives.
#
# {len(URLS.attributes)} attributes, and the set is closed:
{table}
#
#   https://example.com/handbook/oncall    fetch=http meta=hashed
#   https://wiki.corp/display/ENG/runbook  fetch=cdp  meta=hashed ttl=7d
#
# `fux add <URL>` writes a line here with every attribute stated, and fetches
# that one URL once. `fux ingest` re-fetches the lines known to be stale --
# `--refetch-all` every line, `--failed` the ones whose last run failed, and never a
# line that says `update=never`. Those are the engine's two networked paths;
# every other command is offline. See SR-URL-LIST.
"""


@dataclass
class SetupReport:
    written: list[str] = field(default_factory=list)
    kept: list[str] = field(default_factory=list)
    #: Paths written **outside `.fux/` and `fux.toml`** — i.e. into directories
    #: GitHub, AWS and Anthropic own. Tracked separately because
    #: SR-AGENT-POLICY decision 6 makes announcing them mandatory, and veto
    #: condition 1 fires on a write this list does not contain. A subset of
    #: `written`, never a replacement for it.
    outside: list[str] = field(default_factory=list)
    #: True when a hand-written repo-root `AGENTS.md` was found and left alone.
    #: **Announced rather than silently skipped** — W-82 ruling 16 consequence
    #: 2: write-if-missing makes the coverage absent precisely where a repo
    #: already has its own conventions, which is where it is most needed.
    skipped_agents_md: bool = False
    #: True when `.fux/formats.toml` was written FROM a leftover `.fux/sources/types`
    #: (SR-TYPES decision 12). Announced, because the old file still has to be
    #: deleted by hand and fux refuses to run until it is.
    converted_types: bool = False
    #: `!` patterns that moved from the old types file into `.fux/.fuxignore`.
    moved_exclusions: list[str] = field(default_factory=list)
    #: Paths this run DELETED — the Node reader's prune, and nothing else
    #: today. Separate from `written` because a consumer reading "wrote
    #: .fux/node/src/query/rank.mjs" about a file that is now gone would be
    #: told the opposite of what happened (SR-NODE-SEARCH decision 13).
    removed: list[str] = field(default_factory=list)
    #: Which shape `.fux/node/` was written in — `"A"` (the vendored bundle) or
    #: `"C"` (a workspace member). SR-NODE-SEARCH decision 13.
    node_shape: str = fuxdir.SHAPE_VENDORED
    #: The consumer manifest this run EDITED, repo-relative, or `None`.
    #: **Announced always** — decision 15 constraint 3: a silent write to a
    #: tracked file a team reviews is how trust goes.
    wired_manifest: "str | None" = None
    #: Why shape A was written where a monorepo was detected anyway. Printed,
    #: because "half-configured is not a state" is only honest if the fallback
    #: says which state it chose (decision 15 constraint 4).
    workspace_note: "str | None" = None
    #: The package manager whose install command the consumer now has to run.
    workspace_manager: "str | None" = None


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
    (SR-CDP-FETCHER decision 8). A decoder is stdlib-only and offline — it is
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

    ASCII-only by SR-CLI veto 7, which the shipped `AGENTS.md` already is —
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
    """`.fux/formats.toml`, with the built-in default spelled out.

    **A header alone is not a types file.** A file that admits nothing is one
    `read_types` refuses — so writing comments by themselves made `fux setup`
    followed by `fux ingest` fail on every fresh repo until 2026-08-27. SR-TYPES
    decision 10 always said this file ships "with the default spelled out"; it
    is spelled out here.

    **Derived, never transcribed.** The globs come from `DEFAULT_TYPES` at the
    moment setup runs, so the file cannot disagree with the engine that wrote
    it. What it does do is FREEZE: setup is write-if-missing, so a built-in
    decoder added later widens `DEFAULT_TYPES` and does not touch a repo that
    already has this file. That is decision 1a's rule applied to fux's own
    decoders — what counts as a document stays a committed line a human owns.

    ⚠ **`[decoders]` is grouped by module, not sorted by extension.** Sorting
    puts `cfg` next to `csv`, which different modules read, and splits
    `htm`/`html`/`xhtml`. Grouping is what makes the table legible AS a map;
    within a group the extensions are still sorted, so the output stays a pure
    function of the registry (L3).
    """
    from .ingest import typesfile
    from .ingest.gitdir import DEFAULT_TYPES

    bindings = {ext.lstrip("."): name for ext, name in decode_mod.builtin_bindings().items()}
    prose = [glob for glob in DEFAULT_TYPES if typesfile.pattern_extension(glob) not in bindings]
    text = typesfile.render(
        prose,
        bindings,
        header=_TYPES_HEADER,
        include_note=_TYPES_INCLUDE_NOTE,
        decoders_note=_TYPES_DECODERS_NOTE,
        footer=_TYPES_OPT_IN,
    )
    return text.encode("utf-8")


def _convert_legacy_types(root: Path, report: "SetupReport") -> None:
    """Write `.fux/formats.toml` from a leftover `.fux/sources/types` (SR-TYPES decision 12).

    **Only when the new file is missing** — setup is write-if-missing, and a
    repo holding both has already decided; `read_types` tells it to delete the
    old one. **The old file is never deleted here**: it is the human's, and
    removing it is a line in their diff, not a side effect of a scaffolding verb.

    The `!` lines move to `.fux/.fuxignore`, **above the first pattern a human
    wrote there**. `.fuxignore` is last-match-wins and already outranked the
    types list, so a re-include someone wrote against a types `!` line must keep
    winning — placing the moved lines first is what keeps it winning.
    """
    from .config import LEGACY_TYPES_FILE
    from .ingest import typesfile

    legacy = root / LEGACY_TYPES_FILE
    include, decoders, exclusions = typesfile.convert_legacy(
        legacy.read_text(encoding="utf-8"), origin=LEGACY_TYPES_FILE
    )
    text = typesfile.render(
        include,
        decoders,
        header=_TYPES_CONVERTED_HEADER,
        include_note=_TYPES_INCLUDE_NOTE,
        decoders_note=_TYPES_DECODERS_NOTE,
    )
    # Prove the converted file loads before it lands: a conversion that wrote a
    # file fux then refuses would trade one loud error for another.
    typesfile.parse(text, origin=DEFAULT_TYPES_FILE)
    _write_if_missing(root / DEFAULT_TYPES_FILE, text.encode("utf-8"), report, root)
    report.converted_types = True

    if not exclusions:
        return
    path = root / fuxignore.IGNORE_FILE
    existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    have = set(fuxignore.parse(existing).patterns()) if existing else set()
    moved = [pattern for pattern in exclusions if pattern not in have]
    if not moved:
        return
    lines = existing.split("\n") if existing else []
    at = _first_hand_pattern(lines)
    block = [f"# moved from {LEGACY_TYPES_FILE} by `fux setup` (SR-TYPES decision 12)", *moved, ""]
    lines[at:at] = block
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip("\n") + "\n", encoding="utf-8", newline="\n")
    report.moved_exclusions = moved


def _first_hand_pattern(lines: list[str]) -> int:
    """Index of the first hand-written pattern line outside a fux block, else the end."""
    block = None
    for i, raw in enumerate(lines):
        marker = raw.strip()
        if block is None:
            opened = next(
                (b for b in fuxignore.BLOCKS if marker == fuxignore._OPEN.format(name=b)), None
            )
            if opened is not None:
                block = opened
                continue
            if marker and not marker.startswith("#"):
                return i
        elif marker == fuxignore._CLOSE.format(name=block):
            block = None
    return len(lines)


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
    # ⚠ **A path two vendors share is written ONCE** (`SHARED_SKILLS`,
    # SR-AGENT-POLICY decision 16). Without this, Copilot's pass finds the file
    # Codex's pass wrote a moment earlier and reports it as `kept ... (yours;
    # never rewritten)` -- a claim about a file fux itself just wrote.
    seen: set[str] = set()
    for vendor in agents:
        for rel, template in AGENT_FILES[vendor]:
            if rel in seen:
                continue
            seen.add(rel)
            path = root / rel
            before = len(report.written)
            _write_if_missing(path, agent_template_bytes(template), report, root)
            if len(report.written) > before:
                # A hook written 0644 fails silently -- the runner reports
                # nothing and the hint never appears. Decision 5.
                if rel in EXECUTABLE_SURFACES:
                    path.chmod(0o755)
                # Recorded at the moment of writing, from the same branch that
                # wrote it, so the announcement cannot drift out of step with
                # the filesystem. Veto condition 1 is exactly this list being
                # incomplete.
                report.outside.append(rel)


def _carries_policy(path: Path) -> bool:
    """Does this `AGENTS.md` already carry fux's policy block?

    The same marker `tests/test_agent_policy_agreement.py` compares on, so the
    two cannot disagree about what "fux's policy is in this file" means. A
    consumer who pasted the snippet by hand counts as carrying it — which is
    the point: they were told once and they did it.
    """
    try:
        return POLICY_BEGIN in path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False


def _write_root_agents(root: Path, report: SetupReport) -> None:
    """Write `AGENTS.md`, or announce that we did not — W-82 ruling 16.

    ⚠ **`_write_if_missing` puts the coverage exactly where it is not needed.**
    A repo that already has a hand-written `AGENTS.md` gets nothing and, worse,
    no error — so the one place fux's guidance is most likely to be missing is
    the one place nothing says so. SR-AGENT-POLICY decision 6 makes the
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
    if AGENTS_FILE in report.kept and not _carries_policy(root / AGENTS_FILE):
        # ⚠ **Kept is not the same as HAND-WRITTEN** (W-140 row 18, fixed
        # 2026-09-11). After the first `fux setup`, fux's own `AGENTS.md` is
        # the file that gets kept — so every later run printed *this repo
        # already has AGENTS.md ... nothing here tells them the index exists*
        # and re-printed the whole template, about a file fux had written that
        # says exactly that. The announcement is for a file fux did NOT write,
        # so the policy marker is what decides it, not the report.
        report.skipped_agents_md = True
    if len(report.written) > before:
        # Repo root is outside `.fux/`, so decision 6's announcement applies
        # exactly as it does to `.github/` and `.kiro/`.
        report.outside.append(AGENTS_FILE)


# ---------------------------------------------------------------------------
# The monorepo shape -- SR-NODE-SEARCH decision 15, ruled by Arpit 2026-09-12
# ("Auto detect. Auto detect and set it up as well.").
#
# 🔴 **This is fux's FIRST write to a file it does not own and a team reviews.**
# `fux hooks` writes `.git/`, which is machinery; a root `package.json` is
# source, and a one-line addition arriving as a whole-file reformat is a bad
# diff in somebody's pull request. Hence: text edits, never a re-serialize.
#
# ⚠ **It lives in `setup.py` and NOT in `fuxdir.py` on purpose.**
# `fuxdir.ensure_layout` runs at the head of every ingest; a manifest edit
# reachable from there would rewrite the consumer's `package.json` on a no-op
# ingest (decision 15 constraint 1). Structure, rather than a comment asking
# nobody to call it.
#
# ⚠ **Why detection does not conflict with "declared, never detected"**:
# SR-FETCHER decision 5 and W-86 fork E govern INGEST, where detection makes
# the INDEX a function of the environment and L3 forbids it. Scaffolding is not
# the index; no law reaches it.
# ---------------------------------------------------------------------------

#: The workspace path fux asks for. MEASURED to link in npm, pnpm, yarn 1 and
#: bun (work/regression/2026-09-12-workspace-dotpath-probe) — the dot prefix
#: breaks nothing — and MEASURED not to be picked up by a `packages/*` glob in
#: any of the four, which is why the wiring is required rather than convenient.
WORKSPACE_MEMBER = ".fux/node"


@dataclass(frozen=True)
class Workspace:
    """A monorepo fux found, and the one file it would have to edit."""

    #: `pnpm` / `npm` / `yarn` / `bun` — used for the install command printed
    #: at the end, and for nothing else. The SHAPE does not depend on it.
    manager: str
    #: The manifest carrying the workspace list.
    manifest: Path
    #: `"pnpm-yaml"` or `"package-json"` — which editor applies.
    kind: str


def _package_manager(root: Path) -> str:
    """Whose install command to print, from the lockfile that is actually here."""
    for name, manager in (
        ("pnpm-lock.yaml", "pnpm"),
        ("bun.lockb", "bun"),
        ("bun.lock", "bun"),
        ("yarn.lock", "yarn"),
        ("package-lock.json", "npm"),
    ):
        if (root / name).is_file():
            return manager
    return "npm"


def _yarn_berry_linker(root: Path) -> "str | None":
    """Yarn 2+'s `nodeLinker`, or `None` when this is not a Berry repository.

    🔴 **MEASURED on 2026-09-12, and the answer splits on this one key**
    ([probe 2](../../work/regression/2026-09-12-yarn-berry-probe/report.md), Yarn
    4.1.0):

    | `nodeLinker` | `.fux/node` links | where `fux` lands | shape |
    |---|---|---|---|
    | `node-modules` | yes | the workspace ROOT's `node_modules/.bin` | **C** |
    | `pnp` (Berry's default) | yes | nowhere — there is no `node_modules` | **A** |

    So the dot path was never the problem in Berry either; **the linker is.**
    Under PnP a binary is reached through Yarn's own resolver, which a
    three-line `/bin/sh` shim cannot do, and shape A is both correct and
    offline. `None` means *not Berry* and the ordinary detection continues.

    ⚠ **Checked BEFORE the `workspaces` array, which is not the order
    SR-NODE-SEARCH decision 15's table was written in — and the table was
    wrong.** A Berry repository declares `workspaces` in `package.json` exactly
    like npm does, so a literal first-hit reading of that table gave every
    Berry repo shape C, including the PnP ones the record's own warning says
    must not have it. The record is amended with this change.
    """
    rc = next((root / n for n in (".yarnrc.yml", ".yarnrc.yaml") if (root / n).is_file()), None)
    manifest = root / "package.json"
    berry = rc is not None
    shape_object = False
    if manifest.is_file():
        try:
            meta = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            meta = {}
        declared = meta.get("packageManager")
        if isinstance(declared, str) and declared.startswith("yarn@"):
            major = declared[len("yarn@") :].split(".")[0]
            berry = berry or (major.isdigit() and int(major) >= 2)
        # The object form (`workspaces: {packages: [...]}`) is Berry's own and
        # is not a list the array splicer can extend.
        shape_object = isinstance(meta.get("workspaces"), dict)
    if not berry:
        return None
    if shape_object:
        return "object-form"
    linker = None
    if rc is not None:
        m = re.search(r"^nodeLinker\s*:\s*[\"']?([\w-]+)", rc.read_text(encoding="utf-8"), re.M)
        linker = m.group(1) if m else None
    # Berry's default is PnP, so an unset key means PnP — never "assume the
    # convenient one". Getting this backwards would wire a workspace whose
    # reader nothing can resolve, which is the state decision 15 forbids.
    return linker or "pnp"


def detect_workspace(root: Path) -> "Workspace | None":
    """The monorepo shape, or `None` when there is no monorepo here.

    ⚠ **Yarn Berry comes back as a workspace fux will NOT wire**, rather than
    as `None`. The difference is what the consumer is told: `None` means "no
    monorepo", and saying that to somebody who has one would be false. The
    refusal path prints the real reason and writes shape A.
    """
    linker = _yarn_berry_linker(root)
    if linker is not None and linker != "node-modules":
        return Workspace(manager="yarn", manifest=root / "package.json", kind=f"yarn-{linker}")
    for name in ("pnpm-workspace.yaml", "pnpm-workspace.yml"):
        path = root / name
        if path.is_file() and re.search(r"^packages\s*:", path.read_text(encoding="utf-8"), re.M):
            return Workspace(manager="pnpm", manifest=path, kind="pnpm-yaml")
    manifest = root / "package.json"
    if manifest.is_file():
        try:
            text = manifest.read_text(encoding="utf-8")
        except OSError:
            return None
        try:
            meta = json.loads(text)
        except ValueError:
            # ⚠ **A manifest fux cannot parse but that CLAIMS workspaces is
            # still a monorepo**, and returning `None` here would write shape A
            # with nothing said about it. It comes back as a workspace the
            # refusal path declines, so the run prints the reason (constraint 4).
            if '"workspaces"' in text:
                return Workspace(
                    manager=_package_manager(root), manifest=manifest, kind="package-json"
                )
            return None
        if isinstance(meta.get("workspaces"), list):
            return Workspace(
                manager=_package_manager(root), manifest=manifest, kind="package-json"
            )
    return None


def _matching_bracket(text: str, start: int) -> int:
    """Index of the `]` closing the `[` at `start`, skipping string contents."""
    depth = 0
    i = start
    while i < len(text):
        ch = text[i]
        if ch == '"':
            i += 1
            while i < len(text) and text[i] != '"':
                i += 2 if text[i] == "\\" else 1
        elif ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def _insert_into_json_array(text: str, key: str, member: str) -> "str | None":
    """Add `member` to the array at `key`, preserving the file's shape.

    Returns the new text, or `None` when the edit is not safe to make — which
    is a fallback to shape A, never a best-effort write (decision 15
    constraint 4). Indentation, key order and the trailing newline survive
    because nothing is re-serialized: this is a splice.

    The key may be quoted (`"workspaces":`, JSON) or bare (`packages:`, a
    pnpm flow sequence) — one splicer, because the bracket shapes are identical
    and a second copy would be the drift this repo keeps paying for.
    """
    m = re.search(r'"?%s"?\s*:\s*' % re.escape(key), text)
    if m is None:
        return None
    open_at = text.find("[", m.end())
    if open_at == -1 or text[m.end() : open_at].strip():
        return None
    close_at = _matching_bracket(text, open_at)
    if close_at == -1:
        return None
    inner = text[open_at + 1 : close_at]
    if f'"{member}"' in inner:
        return text  # already wired; idempotent (constraint 3)
    quoted = f'"{member}"'
    if "\n" not in inner:
        spliced = quoted if not inner.strip() else f"{inner.rstrip()}, {quoted}"
        return text[: open_at + 1] + spliced + text[close_at:]
    # Multi-line: copy the last element's own indentation, and give it the comma
    # it did not need while it was last. The line holding the closing bracket's
    # indentation is part of `inner` and is left exactly as it was.
    lines = inner.splitlines()
    filled = [i for i, line in enumerate(lines) if line.strip()]
    if not filled:
        return None
    at = filled[-1]
    last = lines[at].rstrip()
    indent = lines[at][: len(lines[at]) - len(lines[at].lstrip())]
    lines[at] = last if last.endswith(",") else last + ","
    lines.insert(at + 1, indent + quoted)
    return text[: open_at + 1] + "\n".join(lines) + text[close_at:]


def _insert_into_pnpm_yaml(text: str, member: str) -> "str | None":
    """Add `member` to `pnpm-workspace.yaml`'s `packages:` list.

    Handles the block form (`- 'packages/*'`) and the flow form
    (`packages: ["packages/*"]`), matching the quoting style already there.
    Anything else returns `None` and falls back to shape A.
    """
    m = re.search(r"^packages\s*:(?P<rest>.*)$", text, re.M)
    if m is None:
        return None
    if m.group("rest").strip().startswith("["):
        # The flow form is JSON enough for the array splicer, applied to the
        # tail so an earlier `[` in a comment cannot be matched by mistake.
        spliced = _insert_into_json_array(text[m.start() :], "packages", member)
        return None if spliced is None else text[: m.start()] + spliced
    lines = text.splitlines(keepends=True)
    start = text[: m.start()].count("\n")
    items: list[int] = []
    for i in range(start + 1, len(lines)):
        stripped = lines[i].strip()
        if not stripped or stripped.startswith("#"):
            continue
        if re.match(r"^\s+-\s", lines[i]):
            items.append(i)
            continue
        break  # the next key -- the list is over
    if not items:
        return None
    sample = lines[items[-1]]
    if member in sample or any(member in lines[i] for i in items):
        return text  # already wired
    indent = sample[: len(sample) - len(sample.lstrip())]
    quote = '"' if '"' in sample else ("'" if "'" in sample else "")
    ending = "\n" if sample.endswith("\n") else ""
    lines.insert(items[-1] + 1, f"{indent}- {quote}{member}{quote}{ending or chr(10)}")
    return "".join(lines)


def wire_workspace(root: Path, workspace: Workspace) -> "tuple[bool, str | None]":
    """Declare `.fux/node` in the consumer's manifest.

    Returns `(edited, refusal)`. `edited` is False with a `refusal` string when
    the manifest cannot be changed safely — comments in the JSON, an unknown
    list shape, a read-only file. **Half-configured is not a state**: the caller
    then writes shape A and says why.
    """
    path = workspace.manifest
    try:
        before = path.read_text(encoding="utf-8")
    except OSError as exc:
        return False, f"{path.name} could not be read ({exc.strerror})"
    if not os.access(path, os.W_OK):
        return False, f"{path.name} is read-only"

    if workspace.kind == "yarn-pnp":
        return False, (
            "this is a Yarn Berry repository using PnP, which has NO node_modules for "
            "`.fux/fux` to resolve a binary from - measured, not assumed "
            "(SR-NODE-SEARCH decision 15). Set `nodeLinker: node-modules` and re-run "
            "`fux setup` if you would rather have the workspace shape"
        )
    if workspace.kind == "yarn-object-form":
        return False, (
            "this manifest declares `workspaces` as an object, which fux will not edit by "
            "guess (SR-NODE-SEARCH decision 15 constraint 4)"
        )
    if workspace.kind == "pnpm-yaml":
        after = _insert_into_pnpm_yaml(before, WORKSPACE_MEMBER)
    else:
        try:
            json.loads(before)
        except ValueError:
            return False, f"{path.name} is not plain JSON (comments or trailing commas?)"
        after = _insert_into_json_array(before, "workspaces", WORKSPACE_MEMBER)
    if after is None:
        return False, f"{path.name}'s workspace list is in a shape fux will not edit by guess"
    if after == before:
        return True, None  # already declared -- idempotent, and still shape C
    try:
        path.write_text(after, encoding="utf-8")
    except OSError as exc:
        return False, f"{path.name} could not be written ({exc.strerror})"
    return True, None


def run(root: Path, *, agents: bool = True) -> SetupReport:
    """Write the consumer-owned files, write-if-missing. Returns what happened.

    `agents=False` is `--no-agents`, and it must write **nothing** under
    `.github/`, `.kiro/` or `.claude/` — SR-AGENT-POLICY veto condition 1a:
    the opt-out is the whole of a user's control over a default-on install, and
    a leak turns a default into a mandate.
    """
    # Imported here rather than at module level: `..tune` pulls in
    # `query.bm25f` for the defaults it quotes, and through it the whole query
    # package. `setup` never ranks anything, so paying for the ranker to write
    # a commented file is a cost with no return. There is no import cycle to
    # dodge — this is latency, in the same spirit as SR-CLI decision 7.
    from .tune import TUNE_NAME, specimen
    from .output_config import OUTPUT_NAME, specimen as output_specimen

    report = SetupReport()
    # 🔴 **The monorepo shape is decided ONCE, here.** `ensure_layout` runs at
    # the head of every ingest and must never edit a consumer manifest
    # (SR-NODE-SEARCH decision 15 constraint 1); what it gets is the answer,
    # already decided, as a keyword.
    workspace = detect_workspace(root)
    if workspace is not None:
        wired, refusal = wire_workspace(root, workspace)
        if wired:
            report.node_shape = fuxdir.SHAPE_WORKSPACE
            report.wired_manifest = workspace.manifest.relative_to(root).as_posix()
            report.workspace_manager = workspace.manager
        else:
            # Half-configured is not a state (constraint 4): shape A, and the
            # reason travels to the consumer rather than into a log nobody reads.
            report.workspace_note = refusal
    for path in fuxdir.ensure_layout(root, node_shape=report.node_shape):
        rel = path.relative_to(root).as_posix()
        # `ensure_node_reader` returns what it wrote AND what it pruned; at this
        # moment, existence is exactly the difference between the two.
        (report.written if path.exists() else report.removed).append(rel)

    directory = fuxdir.fux_dir(root)
    for name, template in FETCHERS.items():
        _write_if_missing(directory / FETCHERS_DIR / name, template_bytes(template), report, root)

    # W-86 P7, ruled by Arpit 2026-08-26: every built-in decoder is written into
    # `.fux/decoders/`, and **the copy is what runs** (SR-DECODE decision 11).
    for name in decode_mod.BUILTIN_MODULES:
        _write_if_missing(
            directory / DECODERS_DIR / f"{name}.py", decoder_source(name), report, root
        )

    # W-170 — the directory exists so a consumer can find it, with a README
    # saying what goes in it. An empty directory git cannot commit would be
    # indistinguishable from a fux too old to have observers.
    _write_if_missing(
        directory / OBSERVERS_DIR / "README.md", _OBSERVERS_README.encode("utf-8"), report, root
    )

    _write_if_missing(root / DEFAULT_DIRS_FILE, _seed_dirs(root), report, root)
    _write_if_missing(root / DEFAULT_URLS_FILE, _urls_header().encode("utf-8"), report, root)
    # Header only, no patterns: an ignore file that arrives with guesses in it
    # is one whose first act is to hide a document nobody asked it to hide.
    # Empty is a legal, meaningful state here (SR-FUXIGNORE decision 6) in a
    # way it is not for `types`, so the seed can be honest about knowing
    # nothing. Write-if-missing like the rest -- `fux setup` never rewrites it.
    _write_if_missing(root / fuxignore.IGNORE_FILE, _FUXIGNORE.encode("utf-8"), report, root)
    # AFTER `.fuxignore`, because a conversion moves `!` lines into it.
    # Written with the default spelled out rather than left implicit: a consumer
    # should be able to see what fux considers a document without reading its
    # source (SR-TYPES decision 10), and a file that admits nothing is one
    # `read_types` rejects — see `_seed_types`. A repo still holding the old
    # `.fux/sources/types` gets it CONVERTED instead (decision 12).
    from .config import LEGACY_TYPES_FILE

    if (root / LEGACY_TYPES_FILE).is_file() and not (root / DEFAULT_TYPES_FILE).exists():
        _convert_legacy_types(root, report)
    else:
        _write_if_missing(root / DEFAULT_TYPES_FILE, _seed_types(), report, root)
    # SR-REFUSAL: policy, not code. Written once, never rewritten -- the rules
    # in it are the consumer's to delete, including the vendor ones.
    _write_if_missing(
        refusals.rules_path(root), template_bytes(REFUSALS_TEMPLATE), report, root
    )
    # SR-PII decision 17: the one consumer file every command REQUIRES. The
    # starter's safe rules arrive enabled; the consumer edits or empties them,
    # and a repo that already has the file keeps it -- empty or not.
    _write_if_missing(pii.rules_path(root), template_bytes(PII_TEMPLATE), report, root)
    _write_if_missing(root / CONFIG_NAME, config_text().encode("utf-8"), report, root)
    # Every key commented out, so a fresh repo runs on the engine's own
    # defaults and the file is a menu rather than a configuration (SR-TUNE
    # decisions 2 and 3). Write-if-missing like everything else here: this is
    # the file fux promised never to rewrite, and `fux tune` prints rather than
    # edits for the same reason.
    #
    # **Inside `.fux/`, so it is not a `report.outside` path.** That list is
    # for writes into directories other vendors own, which is what makes
    # announcing them mandatory; a file in fux's own directory is not one.
    _write_if_missing(root / TUNE_NAME, specimen().encode("utf-8"), report, root)
    # SR-OUTPUT decision 1: the same contract as `tune.toml`, one boundary
    # further in — tune changes WHICH documents come back, this changes how
    # they are SHOWN. Write-if-missing for the same reason, and `fux output`
    # prints rather than edits.
    _write_if_missing(root / OUTPUT_NAME, output_specimen().encode("utf-8"), report, root)

    # After `fux.toml`, so a first run reads the default this very call just
    # wrote out in full, and a later run reads whatever the consumer edited it
    # to (SR-AGENT-POLICY decision 5).
    installing = _agents_to_install(root, agents)
    _write_agents(root, report, installing)
    # ⚠ **Gated on the RESOLVED set, not on the `agents` flag.** `--no-agents`
    # is one opt-out; a `[agents] install = []` declaration is the other, and a
    # repo-root file is the most visible thing either could leak
    # (SR-AGENT-POLICY veto 1a). ⚠ **And only when EVERY vendor installs**: a
    # partial declaration names what it wants, and a neutral file nobody named
    # is not covered by that naming.
    # ⚠ **…OR when a vendor installs for which the root file is the whole
    # ambient plane** (`AGENTS_MD_VENDORS`). Without this clause
    # `install = ["codex"]` writes two skills and no policy, and nothing says so.
    if installing == KNOWN_AGENTS or any(v in installing for v in AGENTS_MD_VENDORS):
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
    for rel in report.removed:
        print(f"  removed {rel} (stale: the reader ships as one bundle now)")
    if report.wired_manifest:
        # Announced, always. Decision 15 constraint 3: a silent write to a
        # tracked file a team reviews is how trust goes.
        print()
        print(f"  monorepo detected: declared {WORKSPACE_MEMBER} in {report.wired_manifest}")
        print(
            f"        .fux/node/ holds a manifest only; run `{report.workspace_manager} install`"
            " and then `.fux/fux ask ...`"
        )
    elif report.workspace_note:
        print()
        print("  note: a monorepo was detected, and fux vendored the offline bundle")
        print("        into .fux/node/ rather than wiring a workspace, because:")
        print(f"        {report.workspace_note}")
    if not report.written:
        print("setup: nothing to do - every consumer-owned file is already here")
    else:
        print(
            f"setup: {len(report.written)} file(s) written. They are yours: commit them, "
            "edit them, fux will not rewrite them."
        )

    # SR-AGENT-POLICY decision 6. The install is default-on, so **this
    # announcement is the entire remaining safeguard** — a user who did not
    # want these files must be able to learn they exist from the terminal they
    # just ran, not from a later `git status` on a repo they share with a team.
    # Veto condition 1 fires on any agent file written without appearing here.
    # ASCII only: these bytes reach a Windows console (SR-CLI veto 7).
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
    if report.converted_types:
        from .config import LEGACY_TYPES_FILE

        print()
        print(
            f"  converted {LEGACY_TYPES_FILE} -> {DEFAULT_TYPES_FILE} (SR-TYPES decision 12)."
        )
        if report.moved_exclusions:
            print(
                f"  moved {len(report.moved_exclusions)} `!` line(s) to "
                f"{fuxignore.IGNORE_FILE}: {', '.join(report.moved_exclusions)}"
            )
        print(
            f"  now delete {LEGACY_TYPES_FILE} - fux refuses to run while it exists, rather "
            "than guess which of the two files you meant"
        )
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
