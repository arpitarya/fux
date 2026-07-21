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
        fused = rrf(lists, k=self.config.hybrid.rrf_k)
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
