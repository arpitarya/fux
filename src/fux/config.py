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
from .constants import fixed

CONFIG_NAME = fixed("files", "config")

#: The shard count, `constants.toml [index] shards` — FIXED, because
#: shard = blake2b(id, digest_size=1) and another count rewrites every path in
#: the tree (SR-RECORD). `fux.toml [index] shards` only CHECKS it (SR-CONFIG
#: decision 3; SR-LAW-12 decision 9a).
FIXED_SHARDS = fixed("index", "shards")

#: What a missing key's error tells the reader to do — the same sentence
#: `tune.toml` and `output.toml` print (L12 decision 3).
_FIX_HINT = "`fux doctor --fix` writes every missing key from the template `fux setup` uses"

#: The keys `load()` REQUIRES, table by table (SR-LAW-12: a missing key is a
#: hard error naming it; no fallback). `[sources.url]`'s are required only when
#: the table is present, because its presence is itself the setting — absent
#: means this repo fetches nothing (SR-CONFIG decision 4). `routes` and
#: `config` are maps of the consumer's own entries, not values, so an absent
#: map is an empty one.
REQUIRED_KEYS: dict[str, tuple[str, ...]] = {
    "sources": ("dirs_file", "urls_file"),
    "index": ("shards", "git_timeout_s"),
    "observe": ("max_ms",),
    "agents": ("install",),
    "maintain": (
        "daemon_poll_s",
        "runner_poll_s",
        "stop_timeout_s",
        "last_cited_max",
        "stop_every_docs",
    ),
    "refer": ("fetch_cache_max_bytes", "timeout_seconds"),
    "doctor": (
        "thin_url_share",
        "thin_url_chars",
        "acquired_warn_share",
        "pii_rule_budget_ms",
    ),
}
REQUIRED_URL_KEYS: tuple[str, ...] = (
    "keep",
    "ttl",
    "enrich",
    "update",
    "fetch_at_answer",
    "max_parallel",
    "sweep_minutes",
    "acquired_max_bytes",
    "thin_words",
    "thin_words_per_kb",
    "failing_streak",
    "parallel_warn_at",
)

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
    "sources.url.routes",
    "sources.url.keep",
    "sources.url.ttl",
    "sources.url.enrich",
    "sources.url.update",
    "sources.url.fetch_at_answer",
    "sources.url.max_parallel",
    "sources.url.sweep_minutes",
    "sources.url.acquired_max_bytes",
    "sources.url.thin_words",
    "sources.url.thin_words_per_kb",
    "sources.url.failing_streak",
    "sources.url.parallel_warn_at",
    "index.shards",
    "index.git_timeout_s",
    "agents.install",
    # W-170. **`[observe] max_ms` is in `fux.toml` and not in `tune.toml`**,
    # because it is not a ranking knob: it bounds how long fux WAITS for a
    # consumer's analytics after the answer is already rendered, and cannot
    # move a result. `tune.toml`'s boundary rule (SR-TUNE decision 1) is about
    # what changes an answer; this changes nothing about one.
    "observe.max_ms",
    # W-225 stage 5e. Values the L12 classification homed here that stages 3-4
    # left in code: the maintenance plane's pacing, the fetch cache's bound,
    # and `fux doctor`'s thin-URL thresholds. None changes a ranking, so none is
    # `tune.toml`'s (SR-TUNE decision 1).
    "maintain.daemon_poll_s",
    "maintain.runner_poll_s",
    "maintain.stop_timeout_s",
    "maintain.last_cited_max",
    "maintain.stop_every_docs",
    "refer.fetch_cache_max_bytes",
    "refer.timeout_seconds",
    "doctor.thin_url_share",
    "doctor.thin_url_chars",
    "doctor.acquired_warn_share",
    "doctor.pii_rule_budget_ms",
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
    "sources.url.fetcher",
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


#: Where a `fetch=<stem>` resolves: `<FETCHERS_DIR>/<stem>.py`.
#:
#: ⚠ **This replaced `DEFAULT_FETCHER` on 2026-09-20** (W-199 D2). That constant
#: did two jobs — it was the source-wide default for `fetch=` **and** its parent
#: directory located every fetcher file. Arpit deleted the default outright
#: (*"There is no default fetch"*), and the directory was never a separate
#: decision: [SR-DOTFUX](../../records/0102_fux-directory.md) declares
#: `.fux/fetchers/` and that is where it always was.
#:
#: 🔴 **A consumer who had relocated their fetchers by pointing
#: `[sources.url] fetcher` at another directory loses that**, and the refusal
#: message says so. It was never documented as a relocation mechanism; it
#: worked as one.
FETCHERS_DIR = fixed("files", "fetchers_dir")
#: Optional. Absent means the built-in allowlist in `gitdir.DEFAULT_TYPES`.
#: TOML, beside the other `.fux/*.toml` policy files -- read and written by
#: `ingest/typesfile.py` (SR-TYPES decision 12).
DEFAULT_TYPES_FILE = fixed("files", "formats")
#: Where the types list lived until 2026-09-11, in the line grammar `dirs` and
#: `urls` still use. **Refused, never read**: a file fux silently ignored would
#: put the built-in default in its place and change the index with nothing
#: saying so (SR-TYPES decision 12). `fux setup` converts it.
LEGACY_TYPES_FILE = fixed("files", "formats_legacy")


#: The vendors `[agents] install` may name. Closed, and validated, because a
#: typo here fails **silently** in the worst way: the policy file a consumer
#: asked for is simply never written, and nothing says so.
KNOWN_AGENTS = ("claude", "codex", "copilot", "kiro")


def _url_routes(path: Path, raw) -> dict[str, str]:
    """`[sources.url.routes]` — a host map fux READS, validated at load.

    ⚠ **Validated here rather than at first use**, so a bad pattern is a named
    error when the config loads — `fux doctor` sees it offline, and nobody
    discovers it mid-fetch. The grammar and the collision rule live in
    `ingest/routes.py`; this function only checks the table's shape and hands
    it over.
    """
    if not isinstance(raw, dict):
        raise FuxError(
            f"{path}: [sources.url.routes] must be a table of "
            f'pattern = "<fetcher stem>" (got {type(raw).__name__})'
        )
    # Imported inside the function for the same reason `sourcelist` is:
    # `ingest/__init__` imports this module, so a top-level import is a cycle.
    from .ingest import routes as _routes

    _routes.validate({str(k): v for k, v in raw.items()}, where=f"{path}: [sources.url.routes]")
    return {str(k): str(v) for k, v in raw.items()}


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

    - `routes` — a host-to-fetcher map, `{pattern = "<stem>"}`, consulted by
      `fux add` when no `--fetch` was given (SR-FETCHER decision 16). Four
      pattern shapes: `example.com`, `*.example.com` (⚠ **not** the apex),
      `example.com:8443`, and `re:<regex>` compiled and anchored at load.
      🔴 **Two patterns matching one host is a hard error naming both** — there
      is no non-arbitrary order between two regexes, and a guessed one builds a
      plausible index with the wrong fetcher.
      ⚠ **There is no `fetcher` key any more.** It was the source-wide default
      for `fetch=` and it was deleted on 2026-09-20 (W-199 D2): every URL line
      states its own fetcher, and a repo carrying the old key fails to load by
      name.

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
      present."*). It was the only key here with no default until SR-LAW-12
      made every one required. A repo with no `[sources.url]` at all is
      exempt — it fetches nothing, so there is nothing to bound.
      The effective value is `min(this, the fetcher's MAX_PARALLEL)`. This is
      **policy**, not capability: it is never clamped *up* past what a fetcher
      declared safe, and a large value is honoured with a warning rather than
      silently reduced — Arpit's rule, *state the cost, don't clamp the knob*.
      `< 1` is broken and refuses.
      ⚠ **It lives here and not in `tune.toml`** because it changes no byte in
      `.fux/index/` **and** is not a ranking value: it is operational, so it
      belongs beside the other `[sources.url]` keys.
    """

    #: `{host pattern: fetcher stem}` — [SR-CONFIG](../../records/0113_config.md)
    #: decision 16b. 🔴 **A BINDING fux reads, not an opaque table it passes
    #: through.** `[sources.url.config]` is the opaque one, and the two sit under
    #: the same prefix: the adapter-cap argument applies to that one and never to
    #: this one, because deciding which fetcher retrieves a URL is fux's job.
    #: Validated at load; `re:` patterns are compiled and anchored there, so a
    #: bad pattern is a named error before a byte moves.
    routes: dict[str, str]
    urls_file: str
    #: SR-ACQUIRED, the source-wide layer of `keep`. A line still wins.
    keep: bool
    #: SR-URL-FRESHNESS, the source-wide layer of `ttl`. A line still wins.
    #: Stored **verbatim** as the human wrote it ("1h", not 3600) -- the same
    #: rule the list file follows, so config order can never change a byte.
    ttl: str
    config: dict
    #: W-85: a repo that can fetch must say how hard, in a number a person can
    #: read. Since SR-LAW-12 no field here has a default — `load()` requires
    #: every one, and `fux doctor --fix` writes a missing one from the template.
    max_parallel: int
    #: How often `fux daemon` re-checks URLs (W-82 ruling 10).
    sweep_minutes: int
    #: SR-PII, the source-wide layer of `enrich`. A line still wins. The
    #: template ships it off, like the `dirs` list's attribute: enrichment is
    #: generated by a model in someone's agent, and opting a whole corpus in
    #: would plan work nobody asked for.
    enrich: bool
    #: SR-URL-LIST, the source-wide layer of `update`. A line still wins.
    #: `"auto"` (go out, today's behaviour) or `"never"` (this source is
    #: pinned; `fux ingest` does not open a socket for it). ⚠ **Not a
    #: duration** -- `ttl` above is ask-time and this is update-time, and a
    #: second time-shaped key here would be read as the same knob.
    update: str
    #: SR-URL-FRESHNESS decision 16 -- may `fux answer` open a socket for these
    #: URLs at all? `True` is today's behaviour; `False` pins every `url:`
    #: citation to `.fux/acquired/` and the verdict becomes `as-ingested`.
    #: ⚠ **The name states its CLOCK, and that is the whole reason it is three
    #: words.** Decision 15 keeps two clocks apart on one line -- `ttl` is
    #: ask-time *how often*, `update` is update-time *at all* -- and this is
    #: the third cell: ask-time *at all*. `offline` was rejected (it collides
    #: with L5's vocabulary and reads as the whole engine) and `pinned` was
    #: rejected (one word over both clocks, which is the merge decision 15
    #: exists to prevent). **No line-level layer**, like `acquired_max_bytes`:
    #: it answers *"how do I reach these pages?"*, which a source answers for
    #: all of them at once (SR-ACQUIRED, the two-layer/three-layer test).
    fetch_at_answer: bool
    #: SR-ACQUIRED decision 8 -- the bound on `.fux/acquired/`, in bytes.
    #: Required since SR-LAW-12. **There is no
    #: line-level layer**, unlike `keep`: a cap is a property of the disk the
    #: store sits on, not of one URL, and a per-line override could only ever
    #: raise somebody else's bound.
    acquired_max_bytes: int
    #: A fetched page decoding to fewer than `thin_words` words AND fewer than
    #: `thin_words_per_kb` words per KiB of source is reported as thin.
    thin_words: int
    thin_words_per_kb: float
    #: Consecutive failed runs before a URL is named as failing.
    failing_streak: int
    #: A `max_parallel` at or above this prints the "that is a lot of
    #: connections" note. Never a clamp.
    parallel_warn_at: int

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
    #: abandoning it (SR-OBSERVE decision 6). The template ships it small: a
    #: consumer's analytics must not be able to make `fux ask` slow.
    #:
    #: ⚠ **It abandons a thread; it does not kill one.** Python cannot safely
    #: interrupt arbitrary consumer code, so past the cap fux stops *waiting*
    #: and the observer may keep running until the process exits. What the cap
    #: guarantees is the half that matters — the verb's latency — and saying it
    #: abandons rather than kills is the difference between a bound and a
    #: promise fux cannot keep.
    observe_max_ms: int
    #: `[agents] install` — which vendors `fux setup` writes policy renderings
    #: for (SR-AGENT-POLICY decision 5). **Declared, never derived**: fux does
    #: not sniff for `.kiro/` or `.github/` and infer intent, which is the same
    #: derivation SR-DIR-LIST decision 4 refused for `archived`. Required
    #: (SR-LAW-12); the template writes every known vendor **in full** so a
    #: consumer can see and edit it without reading the source. `[]` installs
    #: none.
    agents: tuple[str, ...]
    #: `None` when `[sources.url]` is absent: this repo fetches nothing.
    url: UrlSource | None
    #: `[index] git_timeout_s` -- the bound on ingest's one `git log` call for
    #: recency priors (W-225 stage 5e).
    git_timeout_s: float
    #: `[maintain]` -- the runner's and daemon's pacing (W-225 stage 5e).
    maintain: "Maintain"
    #: `[refer] fetch_cache_max_bytes` -- the fetch cache's disk bound.
    fetch_cache_max_bytes: int
    #: `[refer] timeout_seconds` -- how long `fux answer` waits for one fetch
    #: under the ALWAYS freshness policy (W-225 stage 6).
    refer_timeout_seconds: int
    #: `[doctor]` -- the thresholds its advisory checks warn at.
    doctor: "Doctor"


@dataclass(frozen=True)
class Maintain:
    """`fux.toml [maintain]` -- pacing, never behaviour (SR-MAINTENANCE)."""

    #: The daemon wakes this often to notice `stop`.
    daemon_poll_s: float
    #: `stop` / `take_over` poll the runner this often.
    runner_poll_s: float
    #: How long `stop` waits for a cooperative exit.
    stop_timeout_s: float
    #: How many remembered questions `.fux/runtime/last-cited.json` keeps.
    last_cited_max: int
    #: Ingest polls the cooperative stop once per this many documents.
    stop_every_docs: int


@dataclass(frozen=True)
class Doctor:
    """`fux.toml [doctor]` -- where the thin-URL check starts to warn (SR-DOCTOR)."""

    thin_url_share: float
    thin_url_chars: int
    #: The acquired-plane row warns once `.fux/acquired/` passes this share of
    #: `[sources.url] acquired_max_bytes`.
    acquired_warn_share: float
    #: The `pii timing` row warns when one rule takes longer than this on a
    #: stress string (SR-PII decision 18).
    pii_rule_budget_ms: float


def _number(path: Path, where: str, value, *, whole: bool, positive: bool):
    """A required number: whole or real, and `> 0` or `>= 0`. Named on error."""
    kinds = (int,) if whole else (int, float)
    if isinstance(value, bool) or not isinstance(value, kinds):
        noun = "an integer" if whole else "a number"
        raise FuxError(f"{path}: {where} must be {noun} (got {value!r})")
    if (value <= 0) if positive else (value < 0):
        bound = "> 0" if positive else ">= 0"
        raise FuxError(f"{path}: {where} must be {bound} (got {value!r})")
    return value


def load(root: Path) -> Config:
    """Parse `fux.toml`. Every key is required (SR-LAW-12) except inside an absent
    `[sources.url]`, whose absence is itself the setting (SR-CONFIG decision 4)."""
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
            "the file `[sources] dirs_file` names. A line may carry `archived=true`. See SR-DIR-LIST"
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
    _refuse_retired_url_keys(path, sources.get("url"))

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
    # SR-LAW-12 decision 3: every missing key, named in one pass, AFTER the
    # retirements and unknown keys above — each of those is a better answer
    # than "missing" to the reader who typed it.
    _refuse_missing_keys(path, data)

    dirs_file = sources["dirs_file"]
    if not isinstance(dirs_file, str) or not dirs_file.strip():
        raise FuxError(f"{path}: [sources] dirs_file must be a path to a line-oriented directory list")
    urls_file = sources["urls_file"]
    if not isinstance(urls_file, str) or not urls_file.strip():
        raise FuxError(f"{path}: [sources] urls_file must be a path to a line-oriented URL list")

    observe_max_ms = data["observe"]["max_ms"]
    if not isinstance(observe_max_ms, int) or isinstance(observe_max_ms, bool) or observe_max_ms < 1:
        raise FuxError(
            f"{path}: [observe] max_ms must be a positive integer of milliseconds "
            f"(got {observe_max_ms!r}). It bounds how long fux waits for one "
            f"`.fux/observers/` file after the answer has already been rendered"
        )
    shards = data["index"]["shards"]
    if shards != FIXED_SHARDS:
        raise FuxError(f"{path}: [index] shards must be {FIXED_SHARDS} this milestone (got {shards!r})")

    m = data["maintain"]
    maintain = Maintain(
        daemon_poll_s=_number(path, "[maintain] daemon_poll_s", m["daemon_poll_s"], whole=False, positive=True),
        runner_poll_s=_number(path, "[maintain] runner_poll_s", m["runner_poll_s"], whole=False, positive=True),
        stop_timeout_s=_number(path, "[maintain] stop_timeout_s", m["stop_timeout_s"], whole=False, positive=True),
        last_cited_max=_number(path, "[maintain] last_cited_max", m["last_cited_max"], whole=True, positive=True),
        stop_every_docs=_number(path, "[maintain] stop_every_docs", m["stop_every_docs"], whole=True, positive=True),
    )
    d = data["doctor"]
    doctor = Doctor(
        thin_url_share=_number(path, "[doctor] thin_url_share", d["thin_url_share"], whole=False, positive=False),
        thin_url_chars=_number(path, "[doctor] thin_url_chars", d["thin_url_chars"], whole=True, positive=False),
        acquired_warn_share=_number(
            path, "[doctor] acquired_warn_share", d["acquired_warn_share"], whole=False, positive=True
        ),
        pii_rule_budget_ms=_number(
            path, "[doctor] pii_rule_budget_ms", d["pii_rule_budget_ms"], whole=False, positive=True
        ),
    )

    return Config(
        root=root,
        dirs_file=dirs_file.strip(),
        urls_file=urls_file.strip(),
        shards=shards,
        observe_max_ms=observe_max_ms,
        agents=_load_agents(path, data["agents"]),
        url=_load_url_source(path, sources.get("url"), urls_file.strip()),
        git_timeout_s=_number(path, "[index] git_timeout_s", data["index"]["git_timeout_s"], whole=False, positive=True),
        maintain=maintain,
        fetch_cache_max_bytes=_number(
            path, "[refer] fetch_cache_max_bytes", data["refer"]["fetch_cache_max_bytes"], whole=True, positive=True
        ),
        doctor=doctor,
        refer_timeout_seconds=_number(
            path, "[refer] timeout_seconds", data["refer"]["timeout_seconds"], whole=True, positive=True
        ),
    )


def _refuse_missing_keys(path: Path, data: dict) -> None:
    """Every required key `fux.toml` lacks, named in one error (SR-LAW-12)."""
    missing: list[str] = []
    for table, keys in REQUIRED_KEYS.items():
        node = data.get(table)
        if node is not None and not isinstance(node, dict):
            raise FuxError(f"{path}: [{table}] must be a table")
        missing += [f"[{table}] {key} is missing" for key in keys if key not in (node or {})]
    url = data.get("sources", {}).get("url")
    if isinstance(url, dict):
        missing += [f"[sources.url] {key} is missing" for key in REQUIRED_URL_KEYS if key not in url]
    if missing:
        raise FuxError(f"{path}:\n  " + "\n  ".join(missing) + f"\n  {_FIX_HINT}")


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




def _load_agents(path: Path, raw: dict) -> tuple[str, ...]:
    """`[agents] install` — required (SR-LAW-12); `[]` means none.

    ⚠ **Absent meant every known vendor until W-225 stage 3b.** It is now a
    missing key like any other, and `fux doctor --fix` writes the template's
    list — the same four vendors absent used to mean — so a repo that never
    expressed a preference keeps its behaviour, now written down.
    """
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


def _refuse_retired_url_keys(path: Path, raw) -> None:
    """`[sources.url]`'s retired keys, each refused by name with its new home."""
    if raw is None:
        return
    if not isinstance(raw, dict):
        raise FuxError(f"{path}: [sources.url] must be a table")
    if "urls" in raw:
        raise FuxError(
            f"{path}: [sources.url] urls is not a TOML key any more — put one URL per line in "
            "the file `[sources] urls_file` names"
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
    if "fetcher" in raw:
        raise FuxError(
            f"{path}: [sources.url] fetcher was DELETED on 2026-09-20 — there is no default "
            "fetcher. Every URL line states its own `fetch=<stem>`, and a host map lives in "
            "[sources.url.routes]. Delete this key; fetchers are read from .fux/fetchers/. "
            "(W-199, SR-CONFIG decision 16)"
        )


def _load_url_source(path: Path, raw, urls_file: str) -> UrlSource | None:
    """`[sources.url]`, or `None` when the table is absent — this repo fetches
    nothing. Its retired keys and missing keys were refused before this runs."""
    if raw is None:
        return None
    # A map of the consumer's own entries, not a value: absent is empty.
    routes = _url_routes(path, raw.get("routes", {}))
    keep = raw["keep"]
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

    ttl = raw["ttl"]
    if not isinstance(ttl, str) or sourcelist.parse_duration(ttl) is None:
        raise FuxError(
            f"{path}: [sources.url] ttl must be a duration -- 0, or an integer "
            f"followed by s/m/h/d (got {ttl!r}). It is the source-wide default "
            "for how long a citation may go unchecked; a line's own `ttl=` still wins"
        )
    enrich = raw["enrich"]
    if not isinstance(enrich, bool):
        raise FuxError(
            f"{path}: [sources.url] enrich must be true or false (got {enrich!r}). "
            "It is the source-wide default for whether `fux enrich` plans work for "
            "these URLs; a line's own `enrich=` still wins"
        )
    update = raw["update"]
    if update not in ("auto", "never"):
        raise FuxError(
            f'{path}: [sources.url] update must be "auto" or "never" (got {update!r}). '
            "It is the source-wide default for whether `fux ingest` fetches these URLs "
            "at all; a line's own `update=` still wins. It takes no duration -- `ttl` is "
            "the ask-time knob and this one is update-time"
        )
    fetch_at_answer = raw["fetch_at_answer"]
    if not isinstance(fetch_at_answer, bool):
        raise FuxError(
            f"{path}: [sources.url] fetch_at_answer must be true or false "
            f"(got {fetch_at_answer!r}). It decides whether `fux answer` may open a "
            "socket for these URLs at all; false answers from .fux/acquired/ instead. "
            "It is ask-time, like `ttl` -- `update` is the update-time knob"
        )
    # Opaque, the consumer's fetchers' own: absent is empty, like `routes`.
    config = raw.get("config", {})
    if not isinstance(config, dict):  # the ONLY validation fux does on it
        raise FuxError(f"{path}: [sources.url.config] must be a table (got {type(config).__name__})")
    # W-85 (Arpit): *"never commented. If it is commented, throw an error that
    # the value has to be present."* Since SR-LAW-12 every key here is, and
    # `_refuse_missing_keys` has already named it.
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
    sweep_minutes = raw["sweep_minutes"]
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
    # SR-ACQUIRED decision 8. Required since SR-LAW-12: `None` used to defer
    # to the store's own constant, which was a value held in code.
    acquired_max_bytes = raw["acquired_max_bytes"]
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
        routes=routes,
        urls_file=urls_file,
        keep=keep,
        ttl=ttl,
        enrich=enrich,
        update=update,
        fetch_at_answer=fetch_at_answer,
        config=dict(config),
        max_parallel=max_parallel,
        sweep_minutes=sweep_minutes,
        acquired_max_bytes=acquired_max_bytes,
        thin_words=_number(path, "[sources.url] thin_words", raw["thin_words"], whole=True, positive=False),
        thin_words_per_kb=_number(
            path, "[sources.url] thin_words_per_kb", raw["thin_words_per_kb"], whole=False, positive=False
        ),
        failing_streak=_number(path, "[sources.url] failing_streak", raw["failing_streak"], whole=True, positive=True),
        parallel_warn_at=_number(
            path, "[sources.url] parallel_warn_at", raw["parallel_warn_at"], whole=True, positive=True
        ),
    )
