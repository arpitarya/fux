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

CONFIG_NAME = "fux.toml"
FIXED_SHARDS = 256  # not yet configurable — shard = blake2b(id, digest_size=1); see ADR-RECORD


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
DEFAULT_TYPES_FILE = ".fux/sources/types"


@dataclass
class UrlSource:
    """`[sources.url]` — consumer-fetcher URL ingestion (ADR-URL-INGEST/0011).

    - `fetcher` — repo-root-relative path to a consumer-owned Python file, and
      the **source-wide setting for `fetch`**: a URL line that declares no
      `fetch=` uses this file, and a line that declares `fetch=<name>` uses
      `<this file's directory>/<name>.py`. One key carries both, so relocating
      your fetchers is a one-line change (ADR-FETCHER decision 5). The default
      is `.fux/fetchers/http.py` — a plain GET, which is what a URL with no
      attributes means (ADR-HTTP-FETCHER decision 1).
    - `urls_file` — repo-root-relative path to the line-oriented URL list. The
      list is a *file*, not a TOML array: a 5k-entry inline array is one diff
      hunk and one merge conflict, the same argument that sharded the index.
    - `meta` — privacy policy for display fields; `"hashed"` by default (L5),
      `"plain"` an explicit per-source opt-in for public content. It is the
      source-wide *floor*: a URL line may loosen it to `plain` for one public
      document, and there is deliberately no way to make one line stricter.
    - `config` — the `[sources.url.config]` table, passed **verbatim** to the
      fetcher's optional `configure(config)` hook. Fux validates that it is
      a table and never reads a key inside it: core knows there *is* config,
      never what it *means*. Same discipline as PEP 518's `[tool.*]` tables,
      and it is what keeps the adapter cap from leaking one fetcher's
      vocabulary into fux's config schema.
    - `max_parallel` — how many URLs may be fetched at once (W-82 §3.3).
      **`None` means "whatever the fetcher declares"**, which is `1` unless the
      module sets `MAX_PARALLEL`. This is **policy**, not capability: it is
      never clamped *up* past what a fetcher declared safe, and a large value is
      honoured with a warning rather than silently reduced — Arpit's rule,
      *state the cost, don't clamp the knob*. `< 1` is broken and refuses.
      ⚠ **It lives here and not in `tune.toml`** because it changes no byte in
      `.fux/index/` **and** is not a ranking value: it is operational, so it
      belongs beside the other `[sources.url]` keys.
    """

    fetcher: str
    urls_file: str
    meta: str  # "hashed" | "plain"
    config: dict
    max_parallel: int | None = None


@dataclass
class Config:
    """What `fux.toml` says — **policy, not corpus**.

    The two source lists live in committed files under `.fux/sources/`
    (ADR-DIR-LIST decision 1, ADR-URL-LIST decision 1); this object carries
    only where they are. Reading them belongs to the plane that walks them,
    which is why there is no `source_dirs` here any more: config is how the
    engine behaves, the source lists are what it looks at.
    """

    root: Path
    dirs_file: str
    shards: int
    #: `[agents] install` — which vendors `fux setup` writes policy renderings
    #: for (ADR-AGENT-POLICY decision 5). **Declared, never derived**: fux does
    #: not sniff for `.kiro/` or `.github/` and infer intent, which is the same
    #: derivation ADR-DIR-LIST decision 4 refused for `archived`. Defaults to
    #: all three, and `setup` writes that default out **in full** so a consumer
    #: can see and edit it without reading the source. `[]` installs none.
    agents: tuple[str, ...] = ("claude", "copilot", "kiro")
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
            "`archived=true`. See ADR-DIR-LIST"
        )
    dirs_file = sources.get("dirs_file", DEFAULT_DIRS_FILE)
    if not isinstance(dirs_file, str) or not dirs_file.strip():
        raise FuxError(f"{path}: [sources] dirs_file must be a path to a line-oriented directory list")

    shards = data.get("index", {}).get("shards", FIXED_SHARDS)
    if shards != FIXED_SHARDS:
        raise FuxError(f"{path}: [index] shards must be {FIXED_SHARDS} this milestone (got {shards!r})")

    # ADR-TUNE decision 7: every knob that changes ORDER moved to
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
            f"[ranking] from here (ADR-TUNE, 2026-08-24)"
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

    return Config(
        root=root,
        dirs_file=dirs_file.strip(),
        shards=shards,
        agents=_load_agents(path, data.get("agents")),
        url=_load_url_source(path, sources.get("url")),
    )


#: The vendors `[agents] install` may name. Closed, and validated, because a
#: typo here fails **silently** in the worst way: the policy file a consumer
#: asked for is simply never written, and nothing says so.
KNOWN_AGENTS = ("claude", "copilot", "kiro")


def _load_agents(path: Path, raw) -> tuple[str, ...]:
    """`[agents] install`. Absent means all three; `[]` means none.

    **Absent and empty are deliberately different.** Absent is a repo that
    never expressed a preference and gets ADR-AGENT-POLICY decision 5's
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


def _load_url_source(path: Path, raw) -> UrlSource | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise FuxError(f"{path}: [sources.url] must be a table")
    if "urls" in raw:
        raise FuxError(
            f"{path}: [sources.url] urls is not a TOML key any more — put one URL per line in "
            f"{DEFAULT_URLS_FILE} (or point urls_file elsewhere)"
        )
    if "middleware" in raw:
        raise FuxError(
            f"{path}: [sources.url] middleware was renamed to fetcher — "
            "rename the key, and move the file from .fux/middleware/ to .fux/fetchers/ "
            "(ADR-FETCHER, 2026-08-19)"
        )
    fetcher = raw.get("fetcher", DEFAULT_FETCHER)
    if not isinstance(fetcher, str) or not fetcher.strip():
        raise FuxError(f"{path}: [sources.url] fetcher must be a path to a consumer-owned .py file")
    urls_file = raw.get("urls_file", DEFAULT_URLS_FILE)
    if not isinstance(urls_file, str) or not urls_file.strip():
        raise FuxError(f"{path}: [sources.url] urls_file must be a path to a line-oriented URL list")
    meta = raw.get("meta", "hashed")
    if meta not in ("hashed", "plain"):
        raise FuxError(f"{path}: [sources.url] meta must be \"hashed\" or \"plain\" (got {meta!r})")
    config = raw.get("config", {})
    if not isinstance(config, dict):  # the ONLY validation fux does on it
        raise FuxError(f"{path}: [sources.url.config] must be a table (got {type(config).__name__})")
    max_parallel = raw.get("max_parallel")
    if max_parallel is not None:
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
                "1 fetches one URL at a time, which is the default"
            )
    return UrlSource(
        fetcher=fetcher.strip(),
        urls_file=urls_file.strip(),
        meta=meta,
        config=dict(config),
        max_parallel=max_parallel,
    )
