"""The vocabulary lens — every word the index holds, what the analyzer makes
of a question, and where one word lives.

Three read-only views over the same `IndexView` + local `Dictionary` pair the
other lenses use, written for the explorer's **Words** tab (Arpit, 2026-09-27:
*"every index what are the words being picked scored etc create a view of that
as well dynamic"*). The tab renders what these return and computes nothing —
every `df`, `cf`, `idf` and share below is the engine's own number, read off
the index or produced by its own `idf()`.

- `vocabulary` — the terms, sorted, filtered and paged **here** so the page
  never re-sorts fux's rows.
- `analyze` — a question, token by token: what the analyzer kept, what it
  dropped, what each kept term is worth on THIS corpus.
- `term_documents` — the documents one term is on.

Names come from the local dictionary and are never committed
([SR-POSTINGS](../../../records/0112_postings.md) decision 2): an unnamed term
prints as its hash, which is a real state — its source is not readable from
here — and not a blank.
"""

from __future__ import annotations

from bisect import bisect_left


__all__ = ["vocabulary", "analyze", "term_documents", "SORTS"]

#: The sort keys the tab may ask for. Ties break on the hash so two runs of
#: the same index list the same order (L4).
SORTS = ("df", "cf", "idf", "word")


def _class(df: int, view) -> str:
    """boilerplate · distinctive · common — the view's own thresholds, which are
    the lenses' (`.fux/inspect.toml [thresholds]`), so there is one copy."""
    if view.n and df >= view.boilerplate_df:
        return "boilerplate"
    if df <= view.distinctive_df:
        return "distinctive"
    return "common"


def _row(view, dictionary, term_id: int) -> dict:
    h = view.term_of[term_id]
    df = int(view.df[term_id])
    return {
        "hash": h,
        "word": dictionary.name(h),
        "analyzed": dictionary.terms.get(h),
        "named": h in dictionary.terms,
        "df": df,
        "df_share": df / view.n if view.n else 0.0,
        "cf": int(view.cf[term_id]),
        "idf": view.idf(term_id),
        "class": _class(df, view),
        "hapax": df == 1,
    }


def _id_index(view) -> dict[str, int]:
    cached = getattr(view, "_id_by_hash", None)
    if cached is None:
        cached = {h: i for i, h in enumerate(view.term_of)}
        try:
            view._id_by_hash = cached
        except AttributeError:  # pragma: no cover
            pass
    return cached


def vocabulary(
    view, dictionary, *, sort: str = "df", ascending: bool = False, query: str = "",
    klass: str = "", limit: int = 200, offset: int = 0,
) -> dict:
    """The vocabulary, sorted and paged on the server.

    `query` is a case-insensitive substring of the printed word or the analyzed
    term; `klass` is one of `_class`'s answers or `hapax`.
    """
    if sort not in SORTS:
        raise ValueError(f"sort must be one of {', '.join(SORTS)}, not {sort!r}")
    n = len(view.term_of)
    q = query.strip().lower()
    ids = range(n)
    if q or klass:
        kept = []
        for i in ids:
            h = view.term_of[i]
            if q:
                word = dictionary.name(h).lower()
                term = (dictionary.terms.get(h) or "").lower()
                if q not in word and q not in term:
                    continue
            if klass:
                df = int(view.df[i])
                if klass == "hapax":
                    if df != 1:
                        continue
                elif _class(df, view) != klass:
                    continue
            kept.append(i)
        ids = kept
    if sort == "df":
        key = lambda i: (view.df[i], view.term_of[i])  # noqa: E731
    elif sort == "cf":
        key = lambda i: (view.cf[i], view.term_of[i])  # noqa: E731
    elif sort == "idf":
        key = lambda i: (view.idf(i), view.term_of[i])  # noqa: E731
    else:
        key = lambda i: (dictionary.name(view.term_of[i]).lower(), view.term_of[i])  # noqa: E731
    ordered = sorted(ids, key=key, reverse=not ascending)
    matched = len(ordered)
    page = ordered[max(0, offset): max(0, offset) + max(1, limit)]
    threshold = view.boilerplate_df
    hapax = sum(1 for i in range(n) if view.df[i] == 1)
    boiler = [i for i in range(n) if view.df[i] >= threshold]
    return {
        "documents": view.n,
        "terms": n,
        "postings": view.postings,
        "hapax": hapax,
        "boilerplate_terms": len(boiler),
        "boilerplate_postings": sum(int(view.df[i]) for i in boiler),
        "boilerplate_df": threshold,
        "distinctive_df": view.distinctive_df,
        "named": dictionary.coverage(view.term_of)[0],
        "matched": matched,
        "offset": max(0, offset),
        "sort": sort,
        "ascending": ascending,
        "rows": [_row(view, dictionary, i) for i in page],
    }


def analyze(view, dictionary, text: str, ids=None) -> dict:
    """A question as the analyzer reads it — kept terms with their index
    statistics, and the tokens it dropped, in order. `ids` are the repo's
    identifier families (W-233), so a canonical term shows as a kept term."""
    from ..query.analyzer import _WORD_RE, split_identifier
    from ..query.tokenize import _STOPWORDS, tokenize_pairs
    from ..store.format import term_hash

    by_hash = _id_index(view)
    tokens: list[dict] = []
    for raw in _WORD_RE.findall(text):
        for token in (raw, *split_identifier(raw)):
            if token.lower() in _STOPWORDS:
                tokens.append({"surface": token, "dropped": "stopword"})
    kept_pairs = tokenize_pairs(text, ids) if ids is not None else tokenize_pairs(text)
    kept: list[dict] = []
    for surface, analyzed in kept_pairs:
        h = term_hash(analyzed)
        i = by_hash.get(h)
        row = {"surface": surface, "analyzed": analyzed, "hash": h, "in_index": i is not None}
        if i is not None:
            row.update({k: v for k, v in _row(view, dictionary, i).items() if k not in ("hash", "analyzed")})
        kept.append(row)
    return {"text": text, "kept": kept, "dropped": tokens, "documents": view.n}


def term_documents(view, dictionary, term: str, *, limit: int) -> dict | None:
    """The documents carrying one term, named by its hash, its analyzed form or
    its printed word. `None` when no such term is in the index."""
    from ..store.format import term_hash

    by_hash = _id_index(view)
    i = by_hash.get(term)
    if i is None:
        i = by_hash.get(term_hash(term))
    if i is None:
        low = term.lower()
        for h, name in dictionary.surfaces.items():
            if name.lower() == low and h in by_hash:
                i = by_hash[h]
                break
    if i is None:
        return None
    docs = []
    for d_index, ids in enumerate(view.doc_terms):
        k = bisect_left(ids, i)
        if k < len(ids) and ids[k] == i:
            doc = view.docs[d_index]
            docs.append({"id": doc.id, "loc": doc.loc, "title": doc.title, "archived": doc.archived,
                         "superseded": doc.superseded})
    docs.sort(key=lambda d: d["loc"])
    row = _row(view, dictionary, i)
    return {"term": row, "documents": docs[:limit], "count": len(docs)}
