"""Repo root discovery and `fux.toml` config loading.

Root = the nearest ancestor (starting at `start`, default cwd) that holds
`fux.toml` or a `.git` directory — `fux.toml` wins when both are present at
the same level. No root found is not an error here; callers decide whether
that's fatal.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from .errors import FuxError

#: The daemon's sweep cadence when `fux.toml` is silent (W-82 ruling 10).
#: Sixty minutes is conservative on purpose: the daemon covers the **tail**,
#: documents nobody is querying, so an hour of staleness there has no reader.
#: Defined here rather than imported from `maintain.daemon` so that reading a
#: config never drags the maintenance plane in.
DEFAULT_SWEEP_MINUTES = 60

CONFIG_NAME = "fux.toml"

FIXED_SHARDS = 256  # not yet configurable — shard = blake2b(id, digest_size=1); see SR-RECORD

#: Every key `fux.toml` may carry, as dotted paths.
#:
#: ⚠ **This is the IMPLEMENTATION, not a description of one.** `load()` refuses a
#: key that is not here (SR-CONFIG decision 14), so a wrong entry fails rather
#: than merely reading wrong — which is what SR-LAW-0 decision 4 permits an
#: artifact beside a record to do. `tests/test_sr_config_keys.py` asserts these
#: three tuples equal SR-CONFIG's declared key block **in both directions**, so
#: a key cannot exist in the code and not in the record, or the reverse.
KNOWN_KEYS: tuple[str, ...] = (
    "sources.dirs_file",
    "sources.urls_file",
    "sources.url.fetcher",
    "sources.url.meta",
    "sources.url.keep",
    "sources.url.ttl",
    "sources.url.enrich",
    "sources.url.update",
    "sources.url.fetch_at_answer",
    "sources.url.max_parallel",
    "sources.url.sweep_minutes",
    "sources.url.acquired_max_bytes",
    "index.shards",
    "agents.install",
    # W-170. **`[observe] max_ms` is in `fux.toml` and not in `tune.toml`**,
    # because it is not a ranking knob: it bounds how long fux WAITS for a
    # consumer's analytics after the answer is already rendered, and cannot
    # move a result. `tune.toml`'s boundary rule (SR-TUNE decision 1) is about
    # what changes an answer; this changes nothing about one.
    "observe.max_ms",
)

#: Tables fux accepts and does not look inside. **One entry, and it stays one.**
#: `[sources.url.config]` belongs to the consumer's fetcher, and declaring its
#: keys would put one fetcher's vocabulary into fux's config surface — the
#: adapter cap breached through the back door (SR-CONFIG decision 8).
OPAQUE_TABLES: tuple[str, ...] = ("sources.url.config",)

#: Spellings refused **by name, at any value**, each with an error naming where
#: the setting went. A key quietly not read is worse than one that errors,
#: because its author believes their setting is in force — the `[ranking]`
#: precedent, applied to every retirement since.
REFUSED_KEYS: tuple[str, ...] = (
    "sources.dirs",
    "sources.types_file",
    "sources.url.urls",
    "sources.url.urls_file",
    "sources.url.middleware",
    "ranking",
    "dense",
    "decode",
)


def find_root(start: Path | None = None) -> Path | None:
    here = (start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / CONFIG_NAME).is_file() or (candidate / ".git").exists():
            return candidate
    return None


DEFAULT_FETCHER = ".fux/fetchers/http.py"
DEFAULT_URLS_FILE = ".fux/sources/urls"
DEFAULT_DIRS_FILE = ".fux/sources/dirs"
#: Optional. Absent means the built-in allowlist in `gitdir.DEFAULT_TYPES`.
#: TOML, beside the other `.fux/*.toml` policy files -- read and written by
#: `ingest/typesfile.py` (SR-TYPES decision 12).
DEFAULT_TYPES_FILE = ".fux/formats.toml"
#: Where the types list lived until 2026-09-11, in the line grammar `dirs` and
#: `urls` still use. **Refused, never read**: a file fux silently ignored would
#: put the built-in default in its place and change the index with nothing
#: saying so (SR-TYPES decision 12). `fux setup` converts it.
LEGACY_TYPES_FILE = ".fux/sources/types"


#: The vendors `[agents] install` may name. Closed, and validated, because a
#: typo here fails **silently** in the worst way: the policy file a consumer
#: asked for is simply never written, and nothing says so.
KNOWN_AGENTS = ("claude", "codex", "copilot", "kiro")


def fetcher_config(table: dict, fetcher_path: str) -> dict:
    """One fetcher's slice of a two-level `[sources.url.config]`.

    Shared scalars first, then the sub-table named for the fetcher's file stem
    over them. A module-level function, not only a `UrlSource` method, because
    `ingest/urlsrc.fetch_all` holds the raw table rather than the object and
    two copies of this arithmetic is how the ingest path and the answer path
    end up configuring a fetcher differently.
    """
    shared = {k: v for k, v in table.items() if not isinstance(v, dict)}
    own = table.get(Path(fetcher_path).stem)
    return {**shared, **own} if isinstance(own, dict) else shared


@dataclass
class UrlSource:
    """`[sources.url]` — consumer-fetcher URL ingestion (SR-URL-INGEST/0011).

    - `fetcher` — repo-root-relative path to a consumer-owned Python file, and
      the **source-wide setting for `fetch`**: a URL line that declares no
      `fetch=` uses this file, and a line that declares `fetch=<name>` uses
      `<this file's directory>/<name>.py`. One key carries both, so relocating
      your fetchers is a one-line change (SR-FETCHER decision 5). The default
      is `.fux/fetchers/http.py` — a plain GET, which is what a URL with no
      attributes means (SR-HTTP-FETCHER decision 1).
    - `urls_file` — resolved from **`[sources] urls_file`**, not from this
      table (2026-09-14). It is carried here so every caller that already holds
      a `UrlSource` keeps one field to read. The list is a *file*, not a TOML
      array: a 5k-entry inline array is one diff hunk and one merge conflict,
      the same argument that sharded the index.
    - `meta` — privacy policy for display fields; `"hashed"` by default (L5),
      `"plain"` an explicit per-source opt-in for public content. It is the
      source-wide *floor*: a URL line may loosen it to `plain` for one public
      document, and there is deliberately no way to make one line stricter.
    - `config` — the `[sources.url.config]` table, handed to the fetcher's
      optional `configure(config)` hook. Fux validates that it is a table and
      **never reads a key inside it**: core knows there *is* config, never what
      it *means*. Same discipline as PEP 518's `[tool.*]` tables, and it is what
      keeps the adapter cap from leaking one fetcher's vocabulary into fux's
      config schema.
      ⚠ **Since 2026-09-14 it has two levels, and `config_for` is the only
      thing that reads them** (Arpit: *"create 2 separate tables, 1 for http and
      1 for cdp"*). Scalar keys at the top are **shared** — handed to every
      fetcher; a **sub-table is named for a fetcher's file stem** and is handed
      only to that one. **Fux still reads no KEY** — it matches a table name
      against a filename it already knows, which is the same information
      `fetch=<name>` resolution already uses (SR-FETCHER decision 5).
      ⚠ **The flat form was BROKEN for any repo using both shipped fetchers.**
      One table went verbatim to both, and each `configure()` raises on a key
      it does not know, so `cdp_port` made `http.py` refuse and `timeout_s`
      made `cdp.py` refuse. The only configurable state for a mixed repo was
      the empty table.
    - `max_parallel` — how many URLs may be fetched at once (W-82 §3.3).
      ⚠ **REQUIRED whenever `[sources.url]` exists** (W-85, Arpit: *"never
      commented. If it is commented, throw an error that the value has to be
      present."*). It is the only key here with no default: a repo that **can**
      fetch must say how hard, in the file. A repo with no `[sources.url]` at
      all is exempt — it fetches nothing, so there is nothing to bound.
      The effective value is `min(this, the fetcher's MAX_PARALLEL)`. This is
      **policy**, not capability: it is never clamped *up* past what a fetcher
      declared safe, and a large value is honoured with a warning rather than
      silently reduced — Arpit's rule, *state the cost, don't clamp the knob*.
      `< 1` is broken and refuses.
      ⚠ **It lives here and not in `tune.toml`** because it changes no byte in
      `.fux/index/` **and** is not a ranking value: it is operational, so it
      belongs beside the other `[sources.url]` keys.
    """

    fetcher: str
    urls_file: str
    meta: str  # "hashed" | "plain"
    #: SR-ACQUIRED, the source-wide layer of `keep`. A line still wins.
    keep: bool
    #: SR-URL-FRESHNESS, the source-wide layer of `ttl`. A line still wins.
    #: Stored **verbatim** as the human wrote it ("1h", not 3600) -- the same
    #: rule the list file follows, so config order can never change a byte.
    ttl: str
    config: dict
    #: ⚠ **No default, and that is the point** (W-85). Every other field here
    #: carries one; this one is required whenever `[sources.url]` exists,
    #: because a repo that can fetch must say how hard in a number a person can
    #: read. Leaving a default here would put the value back where W-85 took it
    #: from — implicit, and therefore unread.
    max_parallel: int
    #: How often `fux daemon` re-checks URLs (W-82 ruling 10). **Has a default,
    #: unlike `max_parallel`** — it bounds no blast radius, it only decides
    #: cadence, so silence here is unopinionated rather than dangerous.
    sweep_minutes: int = 60
    #: SR-PII, the source-wide layer of `enrich`. A line still wins. Off by
    #: default, exactly like the `dirs` list's attribute: enrichment is
    #: generated by a model in someone's agent, and opting a whole corpus in
    #: by default would plan work nobody asked for.
    enrich: bool = False
    #: SR-URL-LIST, the source-wide layer of `update`. A line still wins.
    #: `"auto"` (go out, today's behaviour) or `"never"` (this source is
    #: pinned; `fux update` does not open a socket for it). ⚠ **Not a
    #: duration** -- `ttl` above is ask-time and this is update-time, and a
    #: second time-shaped key here would be read as the same knob.
    update: str = "auto"
    #: SR-URL-FRESHNESS decision 16 -- may `fux answer` open a socket for these
    #: URLs at all? `True` is today's behaviour; `False` pins every `url:`
    #: citation to `.fux/acquired/` and the verdict becomes `as-ingested`.
    #: ⚠ **The name states its CLOCK, and that is the whole reason it is three
    #: words.** Decision 15 keeps two clocks apart on one line -- `ttl` is
    #: ask-time *how often*, `update` is update-time *at all* -- and this is
    #: the third cell: ask-time *at all*. `offline` was rejected (it collides
    #: with L4's vocabulary and reads as the whole engine) and `pinned` was
    #: rejected (one word over both clocks, which is the merge decision 15
    #: exists to prevent). **No line-level layer**, like `acquired_max_bytes`:
    #: it answers *"how do I reach these pages?"*, which a source answers for
    #: all of them at once (SR-ACQUIRED, the two-layer/three-layer test).
    fetch_at_answer: bool = True
    #: SR-ACQUIRED decision 8 -- the bound on `.fux/acquired/`, in bytes.
    #: `None` means the store's own `DEFAULT_MAX_BYTES`. **There is no
    #: line-level layer**, unlike `keep`: a cap is a property of the disk the
    #: store sits on, not of one URL, and a per-line override could only ever
    #: raise somebody else's bound.
    acquired_max_bytes: int | None = None

    def config_for(self, fetcher_path: str) -> dict:
        """What `configure()` receives for the fetcher at `fetcher_path`.

        Shared scalars, then that fetcher's own sub-table over them — so a
        per-fetcher value wins, and a key meant for another fetcher never
        reaches this one.

        **Keyed on the file STEM**, so `.fux/fetchers/cdp.py` takes
        `[sources.url.config.cdp]`. That is the same name `fetch=<name>` already
        resolves against, so there is one naming rule rather than two.

        ⚠ **A sub-table naming no fetcher is silently ignored here**, because
        the loader may not stat the fetchers directory to decide whether a
        config file is valid. `fux doctor`'s `fetcher config tables` row is
        where that becomes visible — a table quietly not read is a setting its
        author believes is in force, which is the defect
        [SR-CONFIG](0113_config.md) decision 14 exists for.
        """
        return fetcher_config(self.config, fetcher_path)


@dataclass
class Config:
    """What `fux.toml` says — **policy, not corpus**.

    The two source lists live in committed files under `.fux/sources/`
    (SR-DIR-LIST decision 1, SR-URL-LIST decision 1); this object carries
    only where they are. Reading them belongs to the plane that walks them,
    which is why there is no `source_dirs` here any more: config is how the
    engine behaves, the source lists are what it looks at.
    """

    root: Path
    dirs_file: str
    #: The committed URL list. ⚠ **It sits HERE, beside `dirs_file`, and moved
    #: out of `[sources.url]` on 2026-09-14** (Arpit): the two source lists are
    #: one kind of thing and belong in one place. **`[sources.url]`'s presence
    #: still enables URL ingestion** — this key names the file, it does not turn
    #: anything on, which is why a repo with no `[sources.url]` still resolves a
    #: path here rather than having none.
    urls_file: str
    shards: int
    #: `[observe] max_ms` — how long fux waits for one observer before
    #: abandoning it (SR-OBSERVE decision 6). Small by default: a consumer's
    #: analytics must not be able to make `fux ask` slow.
    #:
    #: ⚠ **It abandons a thread; it does not kill one.** Python cannot safely
    #: interrupt arbitrary consumer code, so past the cap fux stops *waiting*
    #: and the observer may keep running until the process exits. What the cap
    #: guarantees is the half that matters — the verb's latency — and saying it
    #: abandons rather than kills is the difference between a bound and a
    #: promise fux cannot keep.
    observe_max_ms: int = 50
    #: `[agents] install` — which vendors `fux setup` writes policy renderings
    #: for (SR-AGENT-POLICY decision 5). **Declared, never derived**: fux does
    #: not sniff for `.kiro/` or `.github/` and infer intent, which is the same
    #: derivation SR-DIR-LIST decision 4 refused for `archived`. Defaults to
    #: all three, and `setup` writes that default out **in full** so a consumer
    #: can see and edit it without reading the source. `[]` installs none.
    #: ⚠ **`KNOWN_AGENTS`, not a literal.** This read `("claude", "copilot",
    #: "kiro")` — three of four — from before Codex was added, and every caller
    #: goes through `load()`, which passes `_load_agents`'s own answer. So it
    #: was dead AND wrong, which is the worse half: a stale default reads as
    #: authority to anyone constructing a `Config` by hand. Found 2026-09-14;
    #: the constant moved above this class so there is one list, not two.
    agents: tuple[str, ...] = KNOWN_AGENTS
    url: UrlSource | None = None


def load(root: Path) -> Config:
    """Parse `fux.toml`: `[sources] dirs_file`, optional `[sources.url]`, `[index] shards`."""
    path = root / CONFIG_NAME
    if not path.is_file():
        raise FuxError(f"no {CONFIG_NAME} at {root} — run from a configured repo")
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise FuxError(f"{path}: invalid TOML ({exc})") from exc

    sources = data.get("sources", {})
    if "dirs" in sources:
        raise FuxError(
            f"{path}: [sources] dirs is not a TOML key any more — put one directory per line in "
            f"{DEFAULT_DIRS_FILE} (or point dirs_file elsewhere). A line may carry "
            "`archived=true`. See SR-DIR-LIST"
        )
    if "types_file" in sources:
        # Advertised by config.schema.json until 2026-09-11 and read by nothing
        # (that file was deleted on 2026-09-12 — SR-CONFIG decision 15):
        # every caller used DEFAULT_TYPES_FILE, so the key was silently ignored.
        # Refused by name rather than ignored (SR-CONFIG; SR-TYPES decision 12).
        raise FuxError(
            f"{path}: [sources] types_file is not a key - the types list is always "
            f"{DEFAULT_TYPES_FILE}, and this key was never read even when the schema listed "
            f"it. Delete it"
        )
    dirs_file = sources.get("dirs_file", DEFAULT_DIRS_FILE)
    if not isinstance(dirs_file, str) or not dirs_file.strip():
        raise FuxError(f"{path}: [sources] dirs_file must be a path to a line-oriented directory list")
    urls_file = sources.get("urls_file", DEFAULT_URLS_FILE)
    if not isinstance(urls_file, str) or not urls_file.strip():
        raise FuxError(f"{path}: [sources] urls_file must be a path to a line-oriented URL list")

    observe = data.get("observe", {})
    observe_max_ms = observe.get("max_ms", 50)
    if not isinstance(observe_max_ms, int) or isinstance(observe_max_ms, bool) or observe_max_ms < 1:
        raise FuxError(
            f"{path}: [observe] max_ms must be a positive integer of milliseconds "
            f"(got {observe_max_ms!r}). It bounds how long fux waits for one "
            f"`.fux/observers/` file after the answer has already been rendered"
        )
    shards = data.get("index", {}).get("shards", FIXED_SHARDS)
    if shards != FIXED_SHARDS:
        raise FuxError(f"{path}: [index] shards must be {FIXED_SHARDS} this milestone (got {shards!r})")

    # SR-TUNE decision 7: every knob that changes ORDER moved to
    # `.fux/tune.toml`, and the old keys are retired with an error naming the
    # new home rather than being silently ignored. The `middleware` -> `fetcher`
    # precedent below is the same shape, for the same reason: a key that is
    # quietly not read is worse than one that errors, because the reader
    # believes their setting is in force.
    if "ranking" in data:
        raise FuxError(
            f"{path}: [ranking] moved to .fux/tune.toml — it holds every knob that "
            f"changes how results are ORDERED, and none that changes what is indexed. "
            f"Run `fux setup` to write the file, move the keys across, and delete "
            f"[ranking] from here (SR-TUNE, 2026-08-24)"
        )
    if "dense" in data:
        # Retired TWICE: to tune.toml on 2026-08-24, then out of existence on
        # 2026-08-25 with the model. Someone whose fux.toml predates both gets
        # the final answer, not a forwarding address to a table that is also gone.
        raise FuxError(
            f"{path}: [dense] was REMOVED on 2026-08-25 along with the embedding model, "
            f"the committed per-chunk vectors and `ask --hybrid`. Delete the table. "
            f"Ranking is unchanged: the lane's `mode` defaulted to `off`, and the gate "
            f"that would have moved it measured 0 fixed / 2 broken"
        )

    # 2026-09-11 (Arpit): `[decode] max_table_rows` moved to `.fux/tune.toml
    # [index]`, beside `max_phrases`. Refused by name, not ignored — the
    # `[ranking]` precedent above: a key quietly not read is a setting its
    # author believes is in force.
    if "decode" in data:
        raise FuxError(
            f"{path}: [decode] moved to .fux/tune.toml — `max_table_rows` now lives in "
            f"its [index] table, beside `max_phrases`. Move the value across and delete "
            f"[decode] from here (SR-TUNE decision 13, 2026-09-11)"
        )

    # SR-CONFIG decision 14. Last, so that every key retired **by name** above
    # keeps its own error: those messages say where the setting went, and a
    # generic "unknown key" would be a worse answer to a better-understood
    # question. `[sources.url]`'s two retirements are checked inside
    # `_load_url_source`, which runs after this call — hence the `REFUSED_KEYS`
    # skip in the walk rather than an ordering trick.
    _refuse_unknown_keys(path, data)

    return Config(
        root=root,
        dirs_file=dirs_file.strip(),
        urls_file=urls_file.strip(),
        shards=shards,
        observe_max_ms=observe_max_ms,
        agents=_load_agents(path, data.get("agents")),
        url=_load_url_source(path, sources.get("url"), urls_file.strip()),
    )


#: Every legal table path, derived from the keys rather than listed again — a
#: second list would be the duplicate `KNOWN_KEYS` exists to avoid.
_TABLES: frozenset[str] = frozenset(
    k.rsplit(".", 1)[0] for k in KNOWN_KEYS if "." in k
) | frozenset(OPAQUE_TABLES)


def _refuse_unknown_keys(path: Path, data: dict) -> None:
    """Refuse a key `fux.toml` does not have. SR-CONFIG decision 14.

    **Why refusing beats ignoring.** `dirs_fil = "docs"` used to parse fine and
    do nothing: the consumer's setting was inert and nothing said so. That is the
    same defect as a key documented and never parsed, approached from the other
    end, and `.fux/tune.toml` has refused unknown keys by name since it existed.

    ⚠ **A key in `REFUSED_KEYS` is skipped here**, because it has a bespoke error
    naming its new home and that answer is strictly better than this one.
    `tests/test_sr_config_keys.py` asserts every one of them still errors, so
    the skip cannot become a hole.
    """
    known = frozenset(KNOWN_KEYS)
    opaque = frozenset(OPAQUE_TABLES)
    refused = frozenset(REFUSED_KEYS)

    def legal_in(prefix: str) -> list[str]:
        """What a reader may type at this level — keys and tables together, so
        the message never omits half the answer."""
        depth = prefix.count(".") + 1 if prefix else 0
        here = [
            k.split(".")[depth]
            for k in (*known, *opaque)
            if (not prefix or k.startswith(prefix + ".")) and k.count(".") >= depth
        ]
        tables = [
            t.split(".")[depth]
            for t in _TABLES
            if (not prefix or t.startswith(prefix + ".")) and t.count(".") == depth
        ]
        return sorted(set(here) | set(tables))

    def walk(table: dict, prefix: str) -> None:
        for key, value in table.items():
            dotted = f"{prefix}.{key}" if prefix else key
            if dotted in refused or dotted in opaque or dotted in known:
                continue
            if dotted in _TABLES:
                # A legal table holding the wrong type is not an unknown key;
                # its own loader says so in words that fit the value.
                if isinstance(value, dict):
                    walk(value, dotted)
                continue
            where = f"[{prefix}] " if prefix else ""
            raise FuxError(
                f"{path}: {where}{key} is not a fux.toml key — fux refuses a key it "
                f"does not read rather than ignoring it, because an ignored key is a "
                f"setting you believe is in force. Legal here: {legal_in(prefix)}. "
                f"Ranking knobs live in .fux/tune.toml (SR-TUNE); the full key list "
                f"is SR-CONFIG decision 13"
            )

    walk(data, "")




def _load_agents(path: Path, raw) -> tuple[str, ...]:
    """`[agents] install`. Absent means every known vendor; `[]` means none.

    **Absent and empty are deliberately different.** Absent is a repo that
    never expressed a preference and gets SR-AGENT-POLICY decision 5's
    default; `install = []` is a consumer who said no, and it is the durable
    form of `--no-agents`. Collapsing them would make the opt-out unwritable.
    """
    if raw is None:
        return KNOWN_AGENTS
    if not isinstance(raw, dict):
        raise FuxError(f"{path}: [agents] must be a table")
    if "install" not in raw:
        return KNOWN_AGENTS
    install = raw["install"]
    if not isinstance(install, list) or not all(isinstance(a, str) for a in install):
        raise FuxError(
            f"{path}: [agents] install must be a list of strings from "
            f"{list(KNOWN_AGENTS)} (got {install!r}). Use [] to install none"
        )
    unknown = [a for a in install if a not in KNOWN_AGENTS]
    if unknown:
        raise FuxError(
            f"{path}: [agents] install names unknown agent(s) {unknown} — "
            f"known: {list(KNOWN_AGENTS)}. A typo here would silently write nothing"
        )
    # Deduped and ordered by KNOWN_AGENTS, not by the file: what gets written
    # must not depend on the order someone happened to type.
    return tuple(a for a in KNOWN_AGENTS if a in install)


def _load_url_source(path: Path, raw, urls_file: str) -> UrlSource | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise FuxError(f"{path}: [sources.url] must be a table")
    if "urls" in raw:
        raise FuxError(
            f"{path}: [sources.url] urls is not a TOML key any more — put one URL per line in "
            f"{DEFAULT_URLS_FILE} (or point urls_file elsewhere)"
        )
    if "urls_file" in raw:
        raise FuxError(
            f"{path}: [sources.url] urls_file moved to [sources] urls_file — it names the "
            f"committed URL list, so it belongs beside dirs_file rather than inside the table "
            f"whose PRESENCE enables fetching. Move the key up one level and delete it here "
            f"(2026-09-14)"
        )
    if "middleware" in raw:
        raise FuxError(
            f"{path}: [sources.url] middleware was renamed to fetcher — "
            "rename the key, and move the file from .fux/middleware/ to .fux/fetchers/ "
            "(SR-FETCHER, 2026-08-19)"
        )
    fetcher = raw.get("fetcher", DEFAULT_FETCHER)
    if not isinstance(fetcher, str) or not fetcher.strip():
        raise FuxError(f"{path}: [sources.url] fetcher must be a path to a consumer-owned .py file")
    meta = raw.get("meta", "hashed")
    if meta not in ("hashed", "plain"):
        raise FuxError(f"{path}: [sources.url] meta must be \"hashed\" or \"plain\" (got {meta!r})")
    keep = raw.get("keep", True)
    if not isinstance(keep, bool):
        raise FuxError(
            f"{path}: [sources.url] keep must be true or false (got {keep!r}). "
            "It is the source-wide default for retaining fetched bytes in "
            ".fux/acquired/; a line's own `keep=` still wins"
        )
    # The ONE duration grammar. Validating this with a second copy is how
    # `--ttl 1x`, a hand-written `ttl=1x` and this key end up failing
    # differently. Imported inside the function because `ingest/__init__`
    # imports this module -- a top-level import here is a cycle.
    from .ingest import sourcelist

    ttl = raw.get("ttl", "24h")
    if not isinstance(ttl, str) or sourcelist.parse_duration(ttl) is None:
        raise FuxError(
            f"{path}: [sources.url] ttl must be a duration -- 0, or an integer "
            f"followed by s/m/h/d (got {ttl!r}). It is the source-wide default "
            "for how long a citation may go unchecked; a line's own `ttl=` still wins"
        )
    enrich = raw.get("enrich", False)
    if not isinstance(enrich, bool):
        raise FuxError(
            f"{path}: [sources.url] enrich must be true or false (got {enrich!r}). "
            "It is the source-wide default for whether `fux enrich` plans work for "
            "these URLs; a line's own `enrich=` still wins"
        )
    update = raw.get("update", "auto")
    if update not in ("auto", "never"):
        raise FuxError(
            f'{path}: [sources.url] update must be "auto" or "never" (got {update!r}). '
            "It is the source-wide default for whether `fux update` fetches these URLs "
            "at all; a line's own `update=` still wins. It takes no duration -- `ttl` is "
            "the ask-time knob and this one is update-time"
        )
    fetch_at_answer = raw.get("fetch_at_answer", True)
    if not isinstance(fetch_at_answer, bool):
        raise FuxError(
            f"{path}: [sources.url] fetch_at_answer must be true or false "
            f"(got {fetch_at_answer!r}). It decides whether `fux answer` may open a "
            "socket for these URLs at all; false answers from .fux/acquired/ instead. "
            "It is ask-time, like `ttl` -- `update` is the update-time knob"
        )
    config = raw.get("config", {})
    if not isinstance(config, dict):  # the ONLY validation fux does on it
        raise FuxError(f"{path}: [sources.url.config] must be a table (got {type(config).__name__})")
    # W-85 (Arpit): *"never commented. If it is commented, throw an error that
    # the value has to be present."* A repo that CAN fetch must say how hard,
    # in the file, in numbers a person can read -- so this is the one
    # `[sources.url]` key with no default. A repo with no `[sources.url]` at
    # all is not covered: it fetches nothing, so there is nothing to bound, and
    # demanding a bound there would make the key noise. Noise is how a safety
    # value stops being read.
    if "max_parallel" not in raw:
        # Imported here rather than at module scope: the constant belongs to the
        # fetch plane (SR-FETCHER owns `urlsrc.py`), and a top-level import
        # would put `fux.config` downstream of `fux.ingest` for one integer.
        from .ingest.urlsrc import DEFAULT_MAX_PARALLEL

        raise FuxError(
            f"{path}: [sources.url] max_parallel must be present -- it is how many URLs "
            f"fux may fetch at once, and it is not allowed to be implicit or commented out. "
            f"Add:\n\n    max_parallel = {DEFAULT_MAX_PARALLEL}\n\n"
            "under [sources.url]. The effective value is min(this, your fetcher's "
            "MAX_PARALLEL); raise it if your host can take it."
        )
    max_parallel = raw["max_parallel"]
    # Refuse what is BROKEN; warn about what is merely strong. A value below
    # 1 cannot mean anything -- there is no such thing as fetching less than
    # one URL at a time -- so it is an error here rather than a silent clamp
    # to 1, which would honour a number the consumer plainly did not mean.
    # The "this is a lot of connections" warning belongs at the point of use
    # (`urlsrc.resolve_parallel`), where the fetcher's own declared maximum
    # is known and the note can state the real cost.
    if isinstance(max_parallel, bool) or not isinstance(max_parallel, int):
        raise FuxError(
            f"{path}: [sources.url] max_parallel must be an integer >= 1 "
            f"(got {max_parallel!r})"
        )
    if max_parallel < 1:
        raise FuxError(
            f"{path}: [sources.url] max_parallel must be >= 1 (got {max_parallel}). "
            "1 fetches one URL at a time"
        )
    # `sweep_minutes` DOES have a default, and the asymmetry with max_parallel
    # above is deliberate rather than an oversight. `max_parallel` bounds a
    # blast radius, so a repo that can fetch must state it (W-85). This one only
    # decides how often the daemon comes round: a missing cadence is not
    # dangerous, merely unopinionated, and demanding it would make the required
    # key above look like one of a pair rather than the exception it is.
    sweep_minutes = raw.get("sweep_minutes", DEFAULT_SWEEP_MINUTES)
    if isinstance(sweep_minutes, bool) or not isinstance(sweep_minutes, int):
        raise FuxError(
            f"{path}: [sources.url] sweep_minutes must be an integer >= 1 "
            f"(got {sweep_minutes!r})"
        )
    if sweep_minutes < 1:
        raise FuxError(
            f"{path}: [sources.url] sweep_minutes must be >= 1 (got {sweep_minutes}). "
            "It is how often `fux daemon` re-checks URLs nobody has queried"
        )
    # SR-ACQUIRED decision 8. Optional, and `None` is not the same as a
    # number: it defers to the store's own default rather than freezing today's
    # constant into every repo that never thought about the question.
    acquired_max_bytes = raw.get("acquired_max_bytes")
    if acquired_max_bytes is not None:
        if isinstance(acquired_max_bytes, bool) or not isinstance(acquired_max_bytes, int):
            raise FuxError(
                f"{path}: [sources.url] acquired_max_bytes must be an integer number of "
                f"bytes (got {acquired_max_bytes!r})"
            )
        if acquired_max_bytes < 1:
            raise FuxError(
                f"{path}: [sources.url] acquired_max_bytes must be >= 1 "
                f"(got {acquired_max_bytes}). To retain nothing, set keep = false"
            )
    return UrlSource(
        fetcher=fetcher.strip(),
        urls_file=urls_file,
        meta=meta,
        keep=keep,
        ttl=ttl,
        enrich=enrich,
        update=update,
        fetch_at_answer=fetch_at_answer,
        config=dict(config),
        max_parallel=max_parallel,
        sweep_minutes=sweep_minutes,
        acquired_max_bytes=acquired_max_bytes,
    )
