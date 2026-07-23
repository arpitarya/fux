"""`fux.toml` loading and validation.

Config is a frozen dataclass tree parsed with stdlib ``tomllib``. Validation
raises the single :class:`FuxError` with the offending key path; unknown keys
and tables are ignored (permissive, so newer configs open in older engines).
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from . import debug
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
    # Absolute confidence floor (handoff 0006 M4) — 0.0 disables it (pre-0.25
    # behaviour). Sits above the existing empty-pool early return, never below.
    min_confidence: float = 0.0


@dataclass(frozen=True)
class HybridParams:
    """[engine.hybrid] — RRF fusion of BM25F + bundled dense (engine v2)."""

    enabled: bool = True
    rrf_k: int = 60
    candidate_pool: int = 200
    # Rank offset applied in fusion to documents whose *author* marked them
    # superseded (frontmatter only — never inferred). A penalised chunk
    # contributes 1/(k + rank + penalty) instead of 1/(k + rank).
    #
    # 0 = off, and off is exact identity: the arithmetic is untouched, so
    # every ranking is byte-identical to v0.25.0. That property is what let the
    # knob land before calibration proved it safe to enable (ADR 0015).
    #
    # The unit is *ranks* rather than raw score because it is scale-free —
    # independent of rrf_k, corpus size, and how many lists fire — so a
    # magnitude calibrated on one corpus means the same thing on a 100k one.
    #
    # 15 is MEASURED, not chosen (docs/conformance/
    # 2026-07-24-supersession-penalty-calibration/). The safe interval is
    # [11, ∞), swept to 500 across all four eval sets: it recovers 100% of the
    # frontmatter-reachable inversions on two independent realistic corpora
    # (orbit 5/5, acme 3/3), with zero hit@5 regression on any gate and no
    # regression in any question kind. 15 sits inside the plateau, clear of the
    # 11 boundary. Enabled by default at Arpit's M5 sign-off, 2026-07-24.
    #
    # Do NOT move this on intuition — it is a measurement. Changing it means
    # re-running the four-eval-set sweep.
    supersession_penalty: int = 15


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
    lean_threshold: int = 10_000  # docs; below this, lean's trade is pure loss
    lean_cache_mb: int = 200
    prefilter_width: int = 500  # FuxVec Hamming prefilter (§6)


@dataclass(frozen=True)
class GitParams:
    """[git] — what ingest commits. State + lock are always committed (§8)."""

    commit_cache: bool = False


DEBUG_LEVELS = ("off", "info", "debug", "trace")
DEBUG_CATEGORIES = frozenset(
    {
        "config", "walk", "convert", "chunk", "index", "state", "lock",
        "query", "lexical", "dense", "graph", "answer", "hooks", "web",
    }
)


@dataclass(frozen=True)
class DebugParams:
    """[debug] — observability (handoff 0005). Never touches stdout.

    Only ``level`` has a flag/env override (see ``fux.debug`` precedence); the
    rest is toml-only, so a project's debug shape is reproducible from its
    committed config.
    """

    level: str = "off"  # off | info | debug | trace
    categories: tuple[str, ...] = ("*",)
    output: str = "stderr"  # "stderr" or a file path
    timing: bool = False
    redact: bool = True
    max_bytes: int = 5_000_000


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
    debug: DebugParams = DebugParams()
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
    penalty = hyb.get("supersession_penalty", HybridParams.supersession_penalty)
    if not isinstance(penalty, int) or isinstance(penalty, bool) or penalty < 0:
        raise FuxError(
            "[engine.hybrid] supersession_penalty must be a non-negative integer "
            "(rank offset; 0 disables)"
        )

    index_params = _parse_index(_table(raw, "index"))
    graph_params = _parse_graph(_table(_table(raw, "engine"), "graph"))
    git_params = _parse_git(_table(raw, "git"))
    debug_params = _parse_debug(_table(raw, "debug"))
    debug.apply_config(debug_params)

    ans = _table(raw, "answer")
    max_sentences = ans.get("max_sentences", AnswerParams.max_sentences)
    if not isinstance(max_sentences, int) or isinstance(max_sentences, bool) or max_sentences <= 0:
        raise FuxError("[answer] max_sentences must be a positive integer")
    min_confidence = ans.get("min_confidence", AnswerParams.min_confidence)
    if not isinstance(min_confidence, (int, float)) or isinstance(min_confidence, bool):
        raise FuxError("[answer] min_confidence must be a number")
    if not 0.0 <= min_confidence <= 1.0:
        raise FuxError("[answer] min_confidence must be between 0.0 and 1.0")

    return Config(
        root=root,
        sources=sources,
        ingest=IngestParams(max_kb=max_kb, exclude=tuple(exclude)),
        bm25f=BM25FParams(**params),
        answer=AnswerParams(max_sentences=max_sentences, min_confidence=float(min_confidence)),
        hybrid=HybridParams(
            enabled=enabled, rrf_k=rrf_k, candidate_pool=candidate_pool,
            supersession_penalty=penalty,
        ),
        index=index_params,
        graph=graph_params,
        git=git_params,
        web=web,
        debug=debug_params,
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
    for name in ("sqlite_threshold", "lean_threshold", "lean_cache_mb", "prefilter_width"):
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


def _parse_debug(table: dict) -> DebugParams:
    defaults = DebugParams()
    level = table.get("level", defaults.level)
    if level not in DEBUG_LEVELS:
        raise FuxError(f"[debug] level must be one of {', '.join(DEBUG_LEVELS)}")
    categories = table.get("categories", list(defaults.categories))
    if not isinstance(categories, list) or not all(isinstance(c, str) for c in categories):
        raise FuxError("[debug] categories must be a list of strings")
    for cat in categories:
        if cat != "*" and cat not in DEBUG_CATEGORIES:
            raise FuxError(
                f"[debug] unknown category {cat!r} — valid: *, "
                f"{', '.join(sorted(DEBUG_CATEGORIES))}"
            )
    output = table.get("output", defaults.output)
    if not isinstance(output, str) or not output:
        raise FuxError("[debug] output must be a non-empty string (\"stderr\" or a file path)")
    timing = table.get("timing", defaults.timing)
    if not isinstance(timing, bool):
        raise FuxError("[debug] timing must be true or false")
    redact = table.get("redact", defaults.redact)
    if not isinstance(redact, bool):
        raise FuxError("[debug] redact must be true or false")
    max_bytes = table.get("max_bytes", defaults.max_bytes)
    if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or max_bytes < 1:
        raise FuxError("[debug] max_bytes must be a positive integer")
    return DebugParams(
        level=level, categories=tuple(categories), output=output,
        timing=timing, redact=redact, max_bytes=max_bytes,
    )


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
