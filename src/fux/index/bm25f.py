"""BM25F scoring — weighted-tf-then-saturate (correct BM25F, not naive per-field
BM25 summed). Fields: heading (heading path + doc title), path (source path
tokens), body. Defaults heading 3.0 / path 2.0 / body 1.0, k1=1.2, b=0.75, all
overridable under `[engine.bm25f]` (see compare/query-engine.compare.md)."""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from ..config import BM25FParams

_TOKEN_RE = re.compile(r"[a-z0-9_]+")
_PATH_SPLIT_RE = re.compile(r"[/._\-]+")


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def path_tokens(rel: str) -> list[str]:
    return tokenize(" ".join(_PATH_SPLIT_RE.split(rel)))


@dataclass
class ScoredChunk:
    file: str
    heading: str
    text: str
    start: int | None  # source line span; None for synthetic bodies
    end: int | None
    score: float
    ordinal: int = 0  # chunk index within its file (vector-cache alignment)
    terms: dict = field(default_factory=dict)  # per-term explain detail
    hybrid: dict | None = None  # rank/similarity/rrf detail when fused (v2)


class Searcher:
    """In-memory postings over the stored chunks; built once per process.

    ``stats`` injects corpus-level BM25F inputs (total chunk count, average
    weighted length, per-term document frequency) from the committed df
    sidecar instead of deriving them from ``files``. The lean profile needs
    that: it scores a re-derived *subset* of documents, so its local postings
    know exact tf but would otherwise compute idf against the subset. With the
    sidecar injected, lean and full pass the scorer identical numbers, which is
    what makes their rankings provably — not approximately — the same.

    The scoring math below is untouched either way; only the provenance of its
    inputs differs.
    """

    def __init__(self, files: dict[str, dict], params: BM25FParams, stats=None):
        self.params = params
        self.stats = stats
        self.chunks: list[dict] = []
        self.postings: dict[str, list[tuple[int, int, int, int]]] = defaultdict(list)
        total_wlen = 0.0
        for rel in sorted(files):
            meta = files[rel]
            ptoks = Counter(path_tokens(rel))
            title = meta.get("title", "")
            for ordinal, chunk in enumerate(meta["chunks"]):
                htoks = Counter(tokenize(chunk["heading"]) + tokenize(title))
                btoks = Counter(tokenize(chunk["text"]))
                wlen = (
                    params.heading * sum(htoks.values())
                    + params.path * sum(ptoks.values())
                    + params.body * sum(btoks.values())
                )
                ix = len(self.chunks)
                self.chunks.append(
                    {
                        "file": rel,
                        "heading": chunk["heading"],
                        "text": chunk["text"],
                        "start": chunk["start"],
                        "end": chunk["end"],
                        "ordinal": ordinal,
                        "wlen": wlen,
                    }
                )
                for term in set(htoks) | set(ptoks) | set(btoks):
                    self.postings[term].append((ix, htoks[term], ptoks[term], btoks[term]))
                total_wlen += wlen
        self.avg_wlen = total_wlen / len(self.chunks) if self.chunks else 1.0

    def search(self, query: str, top: int = 5) -> list[ScoredChunk]:
        p = self.params
        # Corpus-level inputs: from the df sidecar when injected (lean), else
        # from what we hold (full). Identical values, different provenance.
        n = self.stats.total_chunks if self.stats else len(self.chunks)
        avg_wlen = self.stats.avg_wlen(p) if self.stats else self.avg_wlen
        if n == 0 or not self.chunks:
            return []
        scores: dict[int, float] = defaultdict(float)
        detail: dict[int, dict] = defaultdict(dict)
        for term in dict.fromkeys(tokenize(query)):
            plist = self.postings.get(term)
            if not plist:
                continue
            df = self.stats.df_of(term) if self.stats else len(plist)
            idf = math.log((n - df + 0.5) / (df + 0.5) + 1)
            for ix, tf_h, tf_p, tf_b in plist:
                wtf = p.heading * tf_h + p.path * tf_p + p.body * tf_b
                denom = wtf + p.k1 * (1 - p.b + p.b * self.chunks[ix]["wlen"] / avg_wlen)
                contribution = idf * wtf * (p.k1 + 1) / denom
                scores[ix] += contribution
                detail[ix][term] = {
                    "idf": round(idf, 4),
                    "tf": {"heading": tf_h, "path": tf_p, "body": tf_b},
                    "contribution": round(contribution, 4),
                }
        ranked = sorted(
            scores.items(),
            key=lambda kv: (-round(kv[1], 9), self.chunks[kv[0]]["file"], kv[0]),
        )
        out = []
        for ix, score in ranked[:top]:
            c = self.chunks[ix]
            out.append(
                ScoredChunk(
                    file=c["file"],
                    heading=c["heading"],
                    text=c["text"],
                    start=c["start"],
                    end=c["end"],
                    score=score,
                    ordinal=c["ordinal"],
                    terms=detail[ix],
                )
            )
        return out
