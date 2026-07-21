"""Profile resolution and the lean query path (handoff §G).

| profile | what persists | what a query does |
|---------|---------------|-------------------|
| `full` | chunks, postings, vectors in the index | reads them |
| `lean` | doc-level state + df sidecar only | re-derives candidates on demand |
| `auto` | lean when every source is re-derivable, else full | — |

**Why the rankings are identical, not merely close.** The lean path builds a
real `Searcher` over its re-derived candidates and injects the committed df
sidecar, so `tf` is exact (re-derivation is deterministic, verified by
`fux.lock`) and `df`/`n`/`avg_wlen` are exact (stored). Vectors are re-embedded
rather than loaded — the same model over the same text yields the same int8
vector. Every input the scorer sees is therefore the input the full profile
would have handed it, and the kernel above never learns which profile it is on.

`auto` picks lean only when every source can be re-derived offline. A web
*mirror* tier cannot: its text came from the network, so it must persist.
"""

from __future__ import annotations

from ..config import Config
from ..index.bm25f import Searcher

# Candidates re-derived per query before exact scoring (proposal §8c step 3).
LEAN_CANDIDATES = 50


def resolve(config: Config) -> str:
    """`full` or `lean` — never `auto`, which is a question, not an answer."""
    profile = config.index.profile
    if profile in ("full", "lean"):
        return profile
    # auto: a mirror tier's text exists only because we fetched it; re-deriving
    # would mean re-crawling, which a query must never do (the network fence).
    if config.web.urls and config.web.tier == "mirror":
        return "full"
    from ..ingest.lock import read as lock_read

    records = lock_read(config.root)
    if not _all_rederivable(config, records):
        return "full"
    # Footprint is what lean buys, and it costs cold-derive latency to buy it.
    # Below `lean_threshold` documents there is no footprint problem to solve,
    # so the trade is pure loss — auto stays on full and the choice remains
    # available explicitly.
    return "lean" if len(records) >= config.index.lean_threshold else "full"


def _all_rederivable(config: Config, records: dict) -> bool:
    """True when every tracked source is a local file we can convert again."""
    if not records:
        return False
    for doc_id, record in records.items():
        if record.get("kind") == "url":
            return False  # curated web: the page may be gone; keep its text
        if not (config.root / doc_id).is_file():
            return False
    return True


def lean_searcher(config: Config, query: str) -> Searcher | None:
    """A Searcher over this query's candidates, scored with corpus statistics.

    Returns None when the lean plane cannot answer (no state, no sidecar), so
    the caller can fall back rather than silently score against a subset.
    """
    from ..index import leancache
    from ..ingest.chunk import chunk_markdown
    from ..state.df import load_df
    from .cat import document_text
    from .lean import LeanCorpus

    stats = load_df(config.root)
    corpus = LeanCorpus(config)
    if stats is None or not corpus:
        return None

    ranked = corpus.search(query, top=LEAN_CANDIDATES)
    if not ranked:
        return None

    from ..index import doc_id_for
    from ..ingest.manifest import read as manifest_read

    offsets = {
        doc_id_for(e): e.get("line_offset") for e in manifest_read(config.root).values()
    }
    files: dict[str, dict] = {}
    for doc_id, _why in ranked:
        entry = corpus.docs.get(doc_id)
        sha12 = entry.sha12 if entry else ""
        chunks = leancache.get(config.root, doc_id, sha12)
        if chunks is None:
            try:
                body = document_text(config, doc_id)
            except Exception:
                continue  # source absent: omit rather than invent
            offset = offsets.get(doc_id)
            chunks = [
                {
                    "heading": c.heading_path,
                    "text": c.text,
                    "start": c.start_line + offset if offset is not None else None,
                    "end": c.end_line + offset if offset is not None else None,
                    "words": c.words,
                }
                for c in chunk_markdown(body)
            ]
            leancache.put(
                config.root, doc_id, sha12, chunks, config.index.lean_cache_mb
            )
        files[doc_id] = {
            "sha256": sha12,
            "fidelity": "inferred",
            "title": entry.title if entry else "",
            "chunks": chunks,
        }
    if not files:
        return None
    return Searcher(files, config.bm25f, stats=stats)


def lean_vectors(config: Config, files: dict) -> dict:
    """Re-embed candidate chunks: deterministic, so identical to what full stored."""
    from ..embed import get_model

    model = get_model()
    if model is None:
        return {}
    out = {}
    for doc_id, meta in files.items():
        out[doc_id] = {
            "sha": meta.get("sha256", ""),
            "fidelity": meta.get("fidelity", "inferred"),
            "vecs": [
                model.embed(f"{c['heading']}\n{c['text']}") for c in meta["chunks"]
            ],
        }
    return out
