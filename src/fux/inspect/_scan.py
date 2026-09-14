"""One pass over the committed shards, into the summaries every lens reads.

## Why this is its own module, and why it is one pass

`fux inspect` asks six questions of the whole corpus at once, and the naive
shape — a pass per lens — reads a 10 000-document index six times. The design
point is 10 000 documents ([SR-WORK-SCALE](../../../records/0057_WORK-scale.md)),
so the cost is real rather than theoretical.

⚠ **What it must NOT do is hold every record.** A record's `terms` is a dict of
16-hex strings, ~600 of them on this repo's documents; 10 000 of those is six
million short strings, and Python charges roughly 60 bytes apiece for the
string alone. So term hashes are **interned to `int` ids** on arrival and each
document keeps an `array("i")` of ids — six million of those is 24 MB, and the
two are not close.

⚠ **Every number here is derived from the COMMITTED index, never from
`.fux/runtime/`.** `inspect` has to work in a clone that has never run
`fux build`, and a report that silently described a stale accelerator instead
of the index would be the worst kind of wrong: plausible.
"""

from __future__ import annotations

from array import array
from dataclasses import dataclass, field
from pathlib import Path

from .. import store as store_mod
from ..query.bm25f import idf as _idf

__all__ = [
    "Doc",
    "IndexView",
    "read_index_view",
    "BOILERPLATE_DF_SHARE",
    "DISTINCTIVE_DF_SHARE",
]

#: A term at or above this document-frequency share is **boilerplate**: it is
#: on half the corpus or more, so `idf(df, n)` is at most `ln 2` ≈ 0.69 and it
#: separates almost nothing. Expressed as a SHARE rather than as an IDF floor
#: on purpose — an absolute IDF floor moves with `n`, so the same term would be
#: boilerplate on one rung of a corpus and not on the next, and the report's
#: own vocabulary would stop meaning one thing.
BOILERPLATE_DF_SHARE = 0.50

#: A term at or below this share is **distinctive** — rare enough that a query
#: carrying it is asking for a small part of the corpus. Same reasoning as
#: above: a share, not an IDF number. `max(1, …)` keeps it meaningful on a
#: corpus small enough that 10 % rounds below one document.
DISTINCTIVE_DF_SHARE = 0.10


@dataclass(frozen=True)
class Doc:
    """One committed record, reduced to what the lenses ask about.

    `nterms` is the count of DISTINCT terms, which is the document's own
    vocabulary size — the number the M1 pruning gate turned on (*"their
    documents' median vocabulary is 32-46 distinct terms, so top-128 was a
    no-op for 97 %+ of documents"*). `flen` is per-field TOKEN counts with
    duplicates, straight off the record, so the two answer different questions
    and neither substitutes for the other.
    """

    id: str
    loc: str
    title: str
    sha: str
    src: str
    mode: str
    archived: bool
    superseded: bool
    flen: tuple[int, ...]
    nterms: int
    phrases: tuple[str, ...]
    edges_out: int


@dataclass
class IndexView:
    """The corpus, summarised. Everything a lens needs and nothing it does not.

    `term_of` maps an interned id back to its 16-hex hash — the join key for
    the local dictionary, which is what turns an id into a word a human reads.
    """

    docs: list[Doc] = field(default_factory=list)
    #: interned term id -> the 16-hex term hash
    term_of: list[str] = field(default_factory=list)
    #: interned term id -> document frequency
    df: array = field(default_factory=lambda: array("i"))
    #: interned term id -> collection frequency (total occurrences, all fields)
    cf: array = field(default_factory=lambda: array("q"))
    #: document index (into `docs`) -> its distinct term ids, ascending
    doc_terms: list[array] = field(default_factory=list)
    #: interned term id -> `int(hash, 16)`, the 64-bit value minhash permutes
    term_value: array = field(default_factory=lambda: array("Q"))
    total_flen: tuple[int, ...] = ()
    postings: int = 0
    #: `(tokens so far, distinct terms so far)` after each document, in id
    #: order — the Heaps' law curve, sampled at every document.
    heaps: list[tuple[int, int]] = field(default_factory=list)
    #: every committed edge as `(src, kind, dst, grade)` — `Edge`'s own field
    #: order, so the graph lens lifts it with `Edge(*row)` and no mapping
    #: layer exists to get out of step with `graph/model.py`.
    edges: list[tuple[str, str, str, int]] = field(default_factory=list)
    #: shards read, and the content sha of each — the dictionary's cache key
    shards: dict[str, str] = field(default_factory=dict)

    @property
    def n(self) -> int:
        return len(self.docs)

    def idf(self, term_id: int) -> float:
        return _idf(self.df[term_id], self.n)

    @property
    def boilerplate_df(self) -> float:
        """The `df` at which a term becomes boilerplate on THIS corpus."""
        return self.n * BOILERPLATE_DF_SHARE

    @property
    def distinctive_df(self) -> float:
        """The `df` at or below which a term counts as distinctive here."""
        return max(1.0, self.n * DISTINCTIVE_DF_SHARE)


def read_index_view(root: Path, *, progress=None) -> IndexView:
    """Read `.fux/index/` into an `IndexView`. One pass, sorted by doc id.

    Raises whatever the reader raises — `inspect` is a report, but a report
    over an index that cannot be read is not a finding, it is a missing input,
    and the CLI boundary already renders that as an error the reader can act on.
    """
    from ..progress import NULL as _NULL_PROGRESS

    progress = progress or _NULL_PROGRESS
    view = IndexView()
    term_ids: dict[str, int] = {}
    raw: list[tuple[dict, array]] = []
    total_flen = [0] * len(store_mod.TF_FIELDS)

    import json

    paths = list(store_mod.iter_shard_paths(root))
    with progress.phase("read", len(paths), "shards") as p:
        for path in paths:
            data = path.read_bytes()
            view.shards[path.name] = store_mod.content_sha(data)
            _, lines = store_mod.raw_record_lines(path)
            for line in lines:
                record = json.loads(line)
                ids = array("i")
                for term, tf in record.get("terms", {}).items():
                    term_id = term_ids.get(term)
                    if term_id is None:
                        term_id = len(view.term_of)
                        term_ids[term] = term_id
                        view.term_of.append(term)
                        view.df.append(0)
                        view.cf.append(0)
                        view.term_value.append(int(term, 16))
                    view.df[term_id] += 1
                    view.cf[term_id] += sum(tf)
                    ids.append(term_id)
                # Ascending, so the minhash and the Jaccard both read a stable
                # order and two runs cannot differ on dict iteration order.
                # (`dict` preserves insertion order, which is the SHARD's
                # order, not the corpus's — sorting is what makes it a fact.)
                ids = array("i", sorted(ids))
                flen = tuple(record.get("flen", []))
                for i, count in enumerate(flen):
                    total_flen[i] += count
                raw.append((record, ids))
            p.update(1)

    # Sorted by id, exactly as `derive/_build.py` sorts, so a document's index
    # is the same number in both planes and a reader can line up two reports.
    raw.sort(key=lambda pair: pair[0]["id"])

    seen: set[int] = set()
    tokens = 0
    for record, ids in raw:
        view.docs.append(
            Doc(
                id=record["id"],
                loc=record.get("loc", ""),
                title=store_mod.display_title(record),
                sha=record.get("sha", ""),
                src=record.get("src", ""),
                mode=record.get("mode", ""),
                archived=bool(record.get("archived", False)),
                superseded=bool(record.get("superseded", False)),
                flen=tuple(record.get("flen", [])),
                nterms=len(ids),
                phrases=tuple(record.get("phrases", []) or ()),
                edges_out=len(record.get("edges", []) or ()),
            )
        )
        view.doc_terms.append(ids)
        view.postings += len(ids)
        tokens += sum(record.get("flen", []) or ())
        seen.update(ids)
        view.heaps.append((tokens, len(seen)))
        for edge in record.get("edges", []) or ():
            view.edges.append(
                (record["id"], edge["kind"], edge["dst"], int(edge["grade"]))
            )

    view.total_flen = tuple(total_flen)
    return view
