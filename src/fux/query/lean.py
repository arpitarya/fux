"""Doc-level retrieval from the committed state plane alone (proposal §8c).

This is what a fresh clone can do before `fux ingest` has run: `.fux/state/`
is committed, `.fux/index/` is not, so there are no chunks, no postings and no
text — only a 32 B code and a Bloom signature per document.

Two independent weak signals, fused the way the engine fuses everything else:

1. **Lexical** — probe each document's Bloom signature with the query terms.
   One-sided: a miss is proof of absence, a hit is a maybe. False positives
   only add candidates, which exact scoring downstream then discards.
2. **Dense** — Hamming distance between the query's code and each doc code.
   A full-corpus scan, because 32 B per doc makes that affordable.

RRF over the two ranked lists (the same k the hybrid engine uses), with ties
broken by doc id so the result is reproducible.

Passages then come from **re-deriving** the top documents' text on demand —
the premise being that deterministic converters make re-derivation equal to
what was indexed, verified by `fux.lock`.
"""

from __future__ import annotations

from ..config import Config
from ..index.bm25f import tokenize
from ..index.fuse import rrf
from ..state import bloom, load_state

DEFAULT_DOCS = 50  # candidate width before exact scoring


class LeanCorpus:
    """The committed plane, ready to answer doc-level questions."""

    def __init__(self, config: Config):
        self.config = config
        self.docs = load_state(config.root)

    def __bool__(self) -> bool:
        return bool(self.docs)

    def search(self, query: str, *, top: int = DEFAULT_DOCS) -> list[tuple[str, dict]]:
        """Ranked ``(doc_id, why)`` pairs. ``why`` records each signal's rank."""
        terms = [t for t in dict.fromkeys(tokenize(query))]
        lexical = self._lexical_ranking(terms)
        dense = self._dense_ranking(query)
        if not lexical and not dense:
            return []
        lists = [lst for lst in (lexical, dense) if lst]
        # The same supersession down-rank the full engine applies (ADR 0015).
        # Lean carries the marker in its committed state flags, so honouring it
        # here is what keeps lean and full rankings *provably* the same rather
        # than same-until-the-knob-is-on. 0 = identity, as everywhere.
        penalty = self.config.hybrid.supersession_penalty
        offsets = (
            {doc_id: penalty for doc_id, e in self.docs.items() if "superseded" in e.flags}
            if penalty > 0 else {}
        )
        fused = rrf(lists, k=self.config.hybrid.rrf_k, offsets=offsets)
        lex_rank = {doc: i for i, doc in enumerate(lexical, start=1)}
        dense_rank = {doc: i for i, doc in enumerate(dense, start=1)}
        ordered = sorted(fused.items(), key=lambda kv: (-kv[1], kv[0]))
        out = []
        for doc_id, score in ordered[:top]:
            entry = self.docs[doc_id]
            out.append(
                (
                    doc_id,
                    {
                        "title": entry.title,
                        "signature_rank": lex_rank.get(doc_id),
                        "dense_rank": dense_rank.get(doc_id),
                        "rrf": round(score, 5),
                    },
                )
            )
        return out

    def _lexical_ranking(self, terms: list[str]) -> list[str]:
        if not terms:
            return []
        scored = []
        for doc_id, entry in self.docs.items():
            hits = bloom.match_count(entry.sig, terms)
            if hits:
                scored.append((-hits, doc_id))
        return [doc_id for _, doc_id in sorted(scored)]

    def scored_searcher(self, doc_ids: list[str]):
        """Exact BM25F over a re-derived subset, scored with corpus statistics.

        This is the whole lean guarantee in one method: **tf** comes from
        re-deriving the candidate documents (deterministic converters make that
        equal to what was indexed, verified by `fux.lock`), and **df / n /
        avg_wlen** come from the committed sidecar. Both inputs are exact, so
        the ranking equals the full profile's — by construction.

        Returns ``None`` when no sidecar is committed; the caller then falls
        back to doc-level ordering rather than scoring against a subset, which
        would silently be a different ranking.
        """
        from ..index.bm25f import Searcher
        from ..ingest.chunk import chunk_markdown
        from ..query.cat import document_text
        from ..state.df import load_df

        from ..index import doc_id_for
        from ..ingest.manifest import read as manifest_read

        stats = load_df(self.config.root)
        if stats is None:
            return None
        # The title is part of the *heading* field, so it must be the title the
        # full profile indexed — the state plane carries it for exactly this.
        # Line offsets are operational, so they exist only when the manifest
        # does; without it, citations are body-relative (a fresh clone has no
        # source-line mapping to be faithful to).
        offsets = {
            doc_id_for(e): e.get("line_offset") for e in manifest_read(self.config.root).values()
        }
        files: dict[str, dict] = {}
        for doc_id in doc_ids:
            try:
                body = document_text(self.config, doc_id)
            except Exception:
                continue  # source absent in this clone: omit, never invent
            entry = self.docs.get(doc_id)
            offset = offsets.get(doc_id)
            files[doc_id] = {
                "sha256": entry.sha12 if entry else "",
                "fidelity": "inferred",
                "title": entry.title if entry else "",
                "chunks": [
                    {
                        "heading": c.heading_path,
                        "text": c.text,
                        "start": c.start_line + offset if offset is not None else None,
                        "end": c.end_line + offset if offset is not None else None,
                        "words": c.words,
                    }
                    for c in chunk_markdown(body)
                ],
            }
        if not files:
            return None
        return Searcher(files, self.config.bm25f, stats=stats)

    def _dense_ranking(self, query: str) -> list[str]:
        from ..embed import get_model
        from ..embed.fuxvec import hamming, quantize

        model = get_model()
        if model is None:
            return []
        vec = model.embed(query)
        if vec is None:  # all-OOV query: dense has nothing to say
            return []
        code = quantize(vec)
        scored = []
        for doc_id, entry in self.docs.items():
            if entry.code is not None:
                scored.append((hamming(code, entry.code), doc_id))
        return [doc_id for _, doc_id in sorted(scored)]


def has_state_only(config: Config) -> bool:
    """True on a fresh clone: state is committed, the runtime plane is not."""
    from ..index import sqlstore, store

    built = (
        sqlstore.db_path(config.root).is_file() or store.index_path(config.root).is_file()
    )
    from ..state import exists

    return not built and exists(config.root)
