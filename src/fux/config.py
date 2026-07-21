"""`fux.toml` loading and validation.

Config is a frozen dataclass tree parsed with stdlib ``tomllib``. Validation
raises the single :class:`FuxError` with the offending key path; unknown keys
and tables are ignored (permissive, so newer configs open in older engines).
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from .errors import FuxError

CONFIG_NAME = "fux.toml"
SOURCE_TYPES = ("docs", "code", "data", "images")
DEFAULT_EXCLUDES = (
    ".fux",
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "dist",
)


@dataclass(frozen=True)
class BM25FParams:
    heading: float = 3.0
    path: float = 2.0
    body: float = 1.0
    k1: float = 1.2
    b: float = 0.75


@dataclass(frozen=True)
class IngestParams:
    max_kb: int = 256
    exclude: tuple[str, ...] = DEFAULT_EXCLUDES


@dataclass(frozen=True)
class AnswerParams:
    max_sentences: int = 5


@dataclass(frozen=True)
class HybridParams:
    """[engine.hybrid] — RRF fusion of BM25F + bundled dense (engine v2)."""

    enabled: bool = True
    rrf_k: int = 60
    candidate_pool: int = 200


@dataclass(frozen=True)
class GraphParams:
    """[engine.graph] — deterministic PPR-lite expansion (handoff §E).

    Every constant is fixed and configurable rather than tuned at runtime:
    power iteration with a set iteration count and sorted traversal is
    reproducible, where "run until convergence" would not be.
    """

    damping: float = 0.85
    iterations: int = 3
    max_expanded: int = 10
    min_score: float = 0.01
    extracted_weight: float = 1.0
    inferred_weight: float = 0.6
    hop_decay: float = 0.8
    in_rrf: bool = True  # graph list joins fusion (open question 2; measured at M8)


@dataclass(frozen=True)
class IndexParams:
    """[index] — storage backend and footprint profile (handoff 0004).

    ``format`` selects the persistence backend; ``auto`` keeps the v1 JSON path
    for small corpora and switches to sqlite past ``sqlite_threshold`` chunks,
    so today's goldens stay byte-identical while big corpora get row lookups.
    """

    format: str = "auto"  # json | sqlite | auto
    profile: str = "auto"  # full | lean | auto
    sqlite_threshold: int = 25_000  # chunks; the JSON-load breakpoint (proposal §2)
    lean_cache_mb: int = 200
    prefilter_width: int = 500  # FuxVec Hamming prefilter (§6)


@dataclass(frozen=True)
class GitParams:
    """[git] — what ingest commits. State + lock are always committed (§8)."""

    commit_cache: bool = False


@dataclass(frozen=True)
class WebParams:
    """[sources.web] — the fenced network path (ingest-only, never query)."""

    urls: tuple[str, ...] = ()
    max_age_days: int = 30  # url staleness horizon for fux.lock (§8a)
    # curated: one cache file per page (reviewable as diffs).
    # mirror:  no file cache at all — converted text lives in fux.db rows,
    #          because 100k documents-as-files is impractical, git or not.
    tier: str = "curated"
    max_depth: int = 1
    same_domain: bool = True
    allow: tuple[str, ...] = ()  # extra allowed domains when same_domain
    attachments: tuple[str, ...] = ("pdf", "docx", "xlsx", "pptx")
    budget: int = 50  # pages+attachments fetched per run
    delay_s: float = 1.0  # crawl politeness (between fetches)
    max_fetch_kb: int = 2048
    render: str = "off"  # off | cdp
    cdp_port: int = 9222
    settle_ms: int = 500  # post-load settle before DOM capture (cdp)


@dataclass(frozen=True)
class Config:
    root: Path
    sources: dict[str, tuple[str, ...]] = field(default_factory=dict)
    ingest: IngestParams = IngestParams()
    bm25f: BM25FParams = BM25FParams()
    answer: AnswerParams = AnswerParams()
    hybrid: HybridParams = HybridParams()
    index: IndexParams = IndexParams()
    graph: GraphParams = GraphParams()
    git: GitParams = GitParams()
    web: WebParams = WebParams()
    raw: dict = field(default_factory=dict)


def find_root(start: Path | None = None) -> Path:
    """Nearest ancestor (inclusive) containing fux.toml — like git's root walk."""
    cur = (start or Path.cwd()).resolve()
    for candidate in (cur, *cur.parents):
        if (candidate / CONFIG_NAME).is_file():
            return candidate
    raise FuxError(
        f"no {CONFIG_NAME} found (searched from {cur} upward) — run `fux setup` first"
    )


def load(root: Path) -> Config:
    path = root / CONFIG_NAME
    if not path.is_file():
        raise FuxError(f"no {CONFIG_NAME} in {root} — run `fux setup` first")
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise FuxError(f"{CONFIG_NAME} is not valid TOML: {exc}") from exc

    sources: dict[str, tuple[str, ...]] = {}
    sources_raw = dict(_table(raw, "sources"))
    web = _parse_web(sources_raw.pop("web", {}))
    for key, dirs in sources_raw.items():
        if key not in SOURCE_TYPES:
            raise FuxError(
                f"unknown source type {key!r} in [sources] — valid: {', '.join(SOURCE_TYPES)}"
            )
        if not isinstance(dirs, list) or not all(isinstance(d, str) for d in dirs):
            raise FuxError(f"[sources] {key} must be a list of directory strings")
        sources[key] = tuple(dirs)

    ing = _table(raw, "ingest")
    max_kb = ing.get("max_kb", IngestParams.max_kb)
    if not isinstance(max_kb, int) or isinstance(max_kb, bool) or max_kb <= 0:
        raise FuxError("[ingest] max_kb must be a positive integer")
    exclude = ing.get("exclude", list(DEFAULT_EXCLUDES))
    if not isinstance(exclude, list) or not all(isinstance(e, str) for e in exclude):
        raise FuxError("[ingest] exclude must be a list of names")

    bm = _table(_table(raw, "engine"), "bm25f")
    params = {}
    for name, default in (
        ("heading", 3.0),
        ("path", 2.0),
        ("body", 1.0),
        ("k1", 1.2),
        ("b", 0.75),
    ):
        val = bm.get(name, default)
        if not isinstance(val, (int, float)) or isinstance(val, bool) or val < 0:
            raise FuxError(f"[engine.bm25f] {name} must be a non-negative number")
        params[name] = float(val)
    if params["b"] > 1:
        raise FuxError("[engine.bm25f] b must be between 0 and 1")

    hyb = _table(_table(raw, "engine"), "hybrid")
    enabled = hyb.get("enabled", True)
    if not isinstance(enabled, bool):
        raise FuxError("[engine.hybrid] enabled must be true or false")
    rrf_k = hyb.get("rrf_k", 60)
    candidate_pool = hyb.get("candidate_pool", 200)
    for name, val in (("rrf_k", rrf_k), ("candidate_pool", candidate_pool)):
        if not isinstance(val, int) or isinstance(val, bool) or val < 1:
            raise FuxError(f"[engine.hybrid] {name} must be a positive integer")

    index_params = _parse_index(_table(raw, "index"))
    graph_params = _parse_graph(_table(_table(raw, "engine"), "graph"))
    git_params = _parse_git(_table(raw, "git"))

    ans = _table(raw, "answer")
    max_sentences = ans.get("max_sentences", AnswerParams.max_sentences)
    if not isinstance(max_sentences, int) or isinstance(max_sentences, bool) or max_sentences <= 0:
        raise FuxError("[answer] max_sentences must be a positive integer")

    return Config(
        root=root,
        sources=sources,
        ingest=IngestParams(max_kb=max_kb, exclude=tuple(exclude)),
        bm25f=BM25FParams(**params),
        answer=AnswerParams(max_sentences=max_sentences),
        hybrid=HybridParams(enabled=enabled, rrf_k=rrf_k, candidate_pool=candidate_pool),
        index=index_params,
        graph=graph_params,
        git=git_params,
        web=web,
        raw=raw,
    )


def _parse_index(table: dict) -> IndexParams:
    defaults = IndexParams()
    fmt = table.get("format", defaults.format)
    if fmt not in ("json", "sqlite", "auto"):
        raise FuxError('[index] format must be "json", "sqlite" or "auto"')
    profile = table.get("profile", defaults.profile)
    if profile not in ("full", "lean", "auto"):
        raise FuxError('[index] profile must be "full", "lean" or "auto"')
    out = {}
    for name in ("sqlite_threshold", "lean_cache_mb", "prefilter_width"):
        val = table.get(name, getattr(defaults, name))
        if not isinstance(val, int) or isinstance(val, bool) or val < 1:
            raise FuxError(f"[index] {name} must be a positive integer")
        out[name] = val
    return IndexParams(format=fmt, profile=profile, **out)


def _parse_graph(table: dict) -> GraphParams:
    defaults = GraphParams()
    out = {}
    for name in ("damping", "min_score", "extracted_weight", "inferred_weight", "hop_decay"):
        val = table.get(name, getattr(defaults, name))
        if not isinstance(val, (int, float)) or isinstance(val, bool) or not 0 <= val <= 1:
            raise FuxError(f"[engine.graph] {name} must be a number between 0 and 1")
        out[name] = float(val)
    for name in ("iterations", "max_expanded"):
        val = table.get(name, getattr(defaults, name))
        if not isinstance(val, int) or isinstance(val, bool) or val < 1:
            raise FuxError(f"[engine.graph] {name} must be a positive integer")
        out[name] = val
    in_rrf = table.get("in_rrf", defaults.in_rrf)
    if not isinstance(in_rrf, bool):
        raise FuxError("[engine.graph] in_rrf must be true or false")
    return GraphParams(in_rrf=in_rrf, **out)


def _parse_git(table: dict) -> GitParams:
    commit_cache = table.get("commit_cache", GitParams.commit_cache)
    if not isinstance(commit_cache, bool):
        raise FuxError("[git] commit_cache must be true or false")
    return GitParams(commit_cache=commit_cache)


def _parse_web(table) -> WebParams:
    if not isinstance(table, dict):
        raise FuxError("[sources.web] must be a table")
    if not table:
        return WebParams()
    urls = table.get("urls", [])
    if not isinstance(urls, list) or not all(
        isinstance(u, str) and u.startswith(("http://", "https://")) for u in urls
    ):
        raise FuxError("[sources.web] urls must be a list of http(s) URLs")
    defaults = WebParams()
    out = {}
    for name, kind, check in (
        ("max_depth", int, lambda v: v >= 0),
        ("same_domain", bool, lambda v: True),
        ("budget", int, lambda v: v >= 1),
        ("delay_s", (int, float), lambda v: v >= 0),
        ("max_fetch_kb", int, lambda v: v >= 1),
        ("cdp_port", int, lambda v: 0 < v < 65536),
        ("settle_ms", int, lambda v: v >= 0),
        ("max_age_days", int, lambda v: v >= 1),
    ):
        val = table.get(name, getattr(defaults, name))
        if isinstance(val, bool) and kind is not bool or not isinstance(val, kind) or not check(val):
            raise FuxError(f"[sources.web] {name} is invalid")
        out[name] = val
    for name in ("allow", "attachments"):
        val = table.get(name, list(getattr(defaults, name)))
        if not isinstance(val, list) or not all(isinstance(v, str) for v in val):
            raise FuxError(f"[sources.web] {name} must be a list of strings")
        out[name] = tuple(v.lstrip(".").lower() for v in val)
    render = table.get("render", "off")
    if render not in ("off", "cdp"):
        raise FuxError('[sources.web] render must be "off" or "cdp"')
    tier = table.get("tier", WebParams.tier)
    if tier not in ("curated", "mirror"):
        raise FuxError('[sources.web] tier must be "curated" or "mirror"')
    return WebParams(urls=tuple(urls), render=render, tier=tier, **out)


def _table(raw: dict, name: str) -> dict:
    value = raw.get(name, {})
    if not isinstance(value, dict):
        raise FuxError(f"[{name}] must be a table")
    return value
