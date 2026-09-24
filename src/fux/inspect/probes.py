"""Pass C — probes: does a document come back for what a person would type?

**W-220's second rung** ([SR-INSPECT](../../../records/0156_inspect.md) decision
19). A probe is **the document's own title, and each of its headings**, asked as a
real `ask` (`query.run_query`, the ranking `fux ask` prints). The question is the
Google-style one Arpit set on 2026-09-22: *is it in the top ten?*

## Why this replaces self-retrieval as the headline

Self-retrieval asks for a document's **rarest** terms, and a document's path is
indexed vocabulary and unique by construction — so it reads 100 % on every rung
and on a planted-bad corpus alike (decision 9a). A title is what a person types.
On this repository, 21 of 120 title probes missed their own top ten while
self-retrieval read 100 % (W-220 finding 1).

## What it may claim

- **A sample, labelled an estimate**, unless every document was probed (decision
  7's rule, already in force). Evenly spaced, never the first `k`.
- **Titles AND headings** (ruled 2026-09-23; accepted cost ≈ 7.8× the probes per
  prose document). A data document is probed by its title alone and is reported
  on two bars side by side — **identifiable** (no other document shares its
  title) and **reachable** (in its own probe's top ten). Never averaged.
- ⚠ **Title probes favour documents whose title is also in their body.** The
  report says so. And **a probe number is this corpus describing itself** — never
  a claim about engine quality (SR-RS).

## The cache

`.fux/runtime/inspect/probes.json`: `probe text -> the ten ids it returned`,
under one key — the committed shards' content shas plus the `tune.toml` bytes,
because both decide a ranking. The spec named the index root alone; the tune is
added because a probe cached under one `[bm25f]` and read under another would
report a ranking nobody ran.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

__all__ = [
    "PROBE_RANK", "DEFAULT_PROBE_SAMPLE", "Probes", "run", "probe_texts", "ranking_key",
    "open_cache", "save_cache",
]

PROBES_NAME = "probes.json"
SCHEMA = "fux.inspect.probes.v1"

#: The bar: in the top ten, the list an agent is handed.
PROBE_RANK = 10

#: Documents probed when no size is given. Each prose document is ~8 queries, so
#: 50 is ~400 queries — minutes cold, instant from the cache.
DEFAULT_PROBE_SAMPLE = 50


@dataclass
class Probes:
    """Per-document probe outcomes over the sampled documents."""

    #: doc id -> {"title": rank|None, "headings": [[text, rank|None], ...]}
    by_id: dict[str, dict] = field(default_factory=dict)
    sampled: int = 0
    documents: int = 0
    queries: int = 0

    @property
    def whole_corpus(self) -> bool:
        return self.sampled == self.documents


def probe_texts(doc, kind: str) -> list[str]:
    """Title first, then each heading — data documents are probed by title alone."""
    title = (doc.title or "").strip()
    texts = [title] if title else []
    if kind != "data":
        for heading in doc.phrases:
            heading = heading.strip()
            if heading and heading not in texts:
                texts.append(heading)
    return texts


def ranking_key(root: Path, view) -> str:
    tune = root / ".fux" / "tune.toml"
    try:
        tune_bytes = tune.read_bytes()
    except OSError:
        tune_bytes = b""
    h = hashlib.sha256()
    for name, sha in sorted(view.shards.items()):
        h.update(f"{name} {sha}\n".encode())
    h.update(b"tune\n" + tune_bytes)
    return h.hexdigest()


def _path(root: Path) -> Path:
    from .dictionary import inspect_dir

    return inspect_dir(root) / PROBES_NAME


def _load(root: Path, key: str) -> dict[str, list[str]]:
    try:
        payload = json.loads(_path(root).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if payload.get("schema") != SCHEMA or payload.get("key") != key:
        return {}
    return dict(payload.get("results", {}))


def _save(root: Path, key: str, results: dict[str, list[str]]) -> None:
    try:
        _path(root).write_text(
            json.dumps({"schema": SCHEMA, "key": key, "results": dict(sorted(results.items()))},
                       sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except OSError:  # pragma: no cover - a cache that cannot be written is a slower next run
        pass


def _ask(root: Path, text: str) -> list[str]:
    """The ten ids `ask` returns for `text`. **Never raises** — a failed query is a miss."""
    from ..query import run_query

    try:
        results, _ = run_query(root, text, PROBE_RANK, force_scan=False)
    except Exception:  # pragma: no cover - a report must not fail a command
        return []
    return [r.id for r in results]


def _rank(ids: list[str], doc_id: str) -> int | None:
    for position, other in enumerate(ids, start=1):
        if other == doc_id:
            return position
    return None


def open_cache(root: Path, view) -> tuple[str, dict[str, list[str]]]:
    """`(ranking key, query -> ids)` — shared with self-retrieval (`lenses`)."""
    key = ranking_key(root, view)
    return key, _load(root, key)


def save_cache(root: Path, key: str, cache: dict[str, list[str]], *, before: int) -> None:
    if len(cache) != before:
        _save(root, key, cache)


def run(root: Path, view, facts, *, sample: int = DEFAULT_PROBE_SAMPLE, progress=None,
        only: list[int] | None = None, cache: tuple[str, dict] | None = None) -> Probes:
    """Probe the sampled documents (or `only` those indices) and return outcomes.

    `cache` is an `open_cache` pair a caller already holds; without it this
    opens and saves its own.
    """
    from ..progress import NULL as _NULL_PROGRESS
    from .lenses import _sample_indices

    progress = progress or _NULL_PROGRESS
    owned = cache is None
    key, cache = open_cache(root, view) if owned else cache
    before = len(cache)
    indices = only if only is not None else _sample_indices(view.n, sample)
    out = Probes(sampled=len(indices), documents=view.n)
    plan = []
    for index in indices:
        doc = view.docs[index]
        kind = (facts.by_id.get(doc.id) or {}).get("kind") or ("data" if _is_data(doc.loc) else "prose")
        plan.append((doc, probe_texts(doc, kind)))
    total = sum(len(texts) for _doc, texts in plan)
    with progress.phase("probes", total, "queries") as p:
        for doc, texts in plan:
            row: dict = {"title": None, "headings": []}
            for i, text in enumerate(texts):
                p.update(1)
                ids = cache.get(text)
                if ids is None:
                    ids = _ask(root, text)
                    cache[text] = ids
                out.queries += 1
                rank = _rank(ids, doc.id)
                if i == 0 and text == (doc.title or "").strip():
                    row["title"] = rank
                else:
                    row["headings"].append([text, rank])
            out.by_id[doc.id] = row
    if owned:
        save_cache(root, key, cache, before=before)
    return out


def _is_data(loc: str) -> bool:
    from .facts import is_data

    return is_data(loc)
