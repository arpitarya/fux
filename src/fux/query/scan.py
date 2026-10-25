"""`fux ask` — the B2 byte-prefilter scan over committed shards + BM25F.

Every shard line is read as raw bytes; a line is `json.loads`'d only if it
passes a substring check against the query's term hashes (B2, index-format
compare doc §2/§7) — full JSON parsing is the thing this scan exists to
avoid on the common case (a shard full of documents that don't match).

Corpus statistics (`df`, `n`, `avg_wlen`) are derived in this same pass and
never stored: `n`/`avg_wlen` need every document's `wlen`, which is pulled
via a cheap byte-level regex (not a full parse) so non-candidate lines still
never pay for `json.loads`; `df` falls out of the same substring check that
finds candidates, at no extra cost.

**This is the reference implementation of `ask`.** It answers a fresh clone
with no build step, and it is the oracle the derived accelerator
(`fux.derive`) is asserted byte-for-byte against. When the two disagree, this
one is right by definition — which is why scoring and sorting live in
`rank.py` and are shared rather than duplicated here.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .. import store as store_mod
from .rank import AskResult, Corpus, rank
from ..store import TF_FIELDS
from .bm25f import Scoring, derive_wlen
from ..text import identifiers as ids_mod
from . import sections as sections_mod
from ..text.identifiers import EMPTY, IdentifierRules
from ..text.tokenize import tokenize

#: W-168 step 1 — one `ref` edge's anchor length and its target, off the raw
#: bytes.
#:
#: **Key order here is `canonical_dumps`'s, not the writer's**: committed lines
#: have sorted keys, so an edge object reads `{"al":N,"at":{...},"dst":"...",
#: "grade":N,"kind":"ref"}` and `al` is guaranteed to precede `dst`. `at` is a
#: flat hash -> int map with no nested object, which is what makes `[^}]*\}`
#: safe to step over.
#:
#: This runs on **every line in the corpus**, candidate or not, and only when
#: the anchor field is switched on — a document's anchor LENGTH is needed for
#: its `wlen` whether or not it matches the query, and `avg_wlen` needs the
#: corpus total. An unconfigured corpus never compiles a match here.
_EDGE_ANCHOR_RE = re.compile(rb'"al":(?P<len>\d+),"at":\{[^}]*\},"dst":"(?P<dst>[^"]+)"')

#: The byte-level oracle, now over per-field counts (W-76 Phase 1).
#:
#: `wlen` used to be committed and could be read with one integer capture.
#: It is now DERIVED from `flen` at the weights in force, so this pass parses
#: the array and applies `derive_wlen` — the same function the scorer, the
#: accelerator's bound and the refer plane use, so the four cannot drift.
#:
#: Still a raw-bytes read rather than a JSON parse: this runs on every line in
#: the corpus, candidate or not, and parsing every record to sum a length is
#: what the prefilter exists to avoid.
_FLEN_RE = re.compile(rb'"flen":\[([0-9,\s]*)\]')




def _flen_from_line(line: bytes) -> list[int] | None:
    m = _FLEN_RE.search(line)
    if m is None:
        return None
    inner = m.group(1).strip()
    if not inner:
        return []
    return [int(part) for part in inner.split(b",")]

__all__ = [
    "AskResult", "Segment", "ask", "merged_ask", "merged_candidates", "merged_hashes",
    "query_term_hashes", "scan_candidates", "segments_for",
]


def query_term_hashes(query: str, ids: IdentifierRules = EMPTY) -> list[str]:
    """Query terms as index hashes, deduped, order preserved.

    🔴 **`ids` must be the repo's identifier families** (`identifiers.for_root`)
    on every path that matches the result against the index: the index was
    written with them, and a question analyzed without them misses the
    canonical term silently. `tests/query/test_identifiers_threaded.py`
    holds every call in `src/` to that.

    Order is load-bearing: `rank()` sums BM25F contributions in this order, so
    both candidate generators must derive it identically from the same string.
    """
    return list(dict.fromkeys(store_mod.term_hash(t) for t in tokenize(query, ids)))


def scan_candidates(
    root: Path, query_hashes: list[str], *, scoring: Scoring
) -> tuple[list[dict], dict[str, int], Corpus]:
    """The B2 pass: candidate records, `df`, and the corpus statistics.

    One segment — the repository at `root` — weighted into a `Corpus` here.
    The raw pass is `_scan_segment`, which W-300's merged query calls once per
    segment and sums before weighting (`merged_candidates`).
    """
    candidates, df, n, total_flen, total_anchor_len = _scan_segment(
        root, query_hashes, scoring=scoring
    )
    return (
        candidates,
        df,
        Corpus(n=n, total_wlen=derive_wlen(total_flen, scoring, total_anchor_len)),
    )


def _scan_segment(
    root: Path, query_hashes: list[str], *, scoring: Scoring
) -> tuple[list[dict], dict[str, int], int, list[int], int]:
    """The raw B2 pass over one segment: candidates, `df`, `n`, the five RAW
    per-field token totals and the anchor token total — never weighted here,
    so a sum over segments is weighted ONCE (SR-PKG-INDEX d10).

    ## W-168 step 1 — what the anchor field adds to this pass

    Nothing at all when `scoring.anchor` is `0.0`, which is the default: the
    three `anchor_on` branches below are not taken and this function does the
    work it did before the field existed.

    When it is on, the same single pass also folds the **in-edge** map:

    - every line contributes its edges' anchor LENGTHS to their targets, by
      byte regex, candidate or not — a document's `wlen` needs its own anchor
      length whether or not it matches, and `avg_wlen` needs the corpus total;
    - a line the prefilter already parsed contributes its edges' anchor TERMS
      to their targets, for the query's hashes only.

    🔴 **Then the retrieval half**: a document whose only match is a linker's
    wording was never a candidate — its own line carries none of the query's
    hashes, so the prefilter never looked at it. Those records are fetched
    afterwards, from `shard_for(id)`, which names the one shard each lives in.
    Without this step the scoring fold is dead code: *a document is never a
    candidate for a word it does not contain.*

    ⚠ **`df` is NOT touched by any of it.** Anchor terms never enter the
    committed postings, so they never enter a `df` — and `derive/accel.py`
    counts `df` from the postings alone, so making them would be an immediate
    differential-law break. It is also the better ranking: switching the field
    on cannot move `idf` for a document that has nothing to do with the query.
    """
    patterns = {h: f'"{h}"'.encode("ascii") for h in query_hashes}
    anchor_on = scoring.anchor_on
    wanted = {h.encode("ascii") for h in query_hashes}
    #: doc id -> anchor term counts over the query's hashes, and -> anchor
    #: token total. Accumulated over the SOURCES that link to each document.
    anchor_tf: dict[str, dict[str, int]] = {}
    anchor_len: dict[str, int] = {}
    total_anchor_len = 0

    total_docs = 0
    # Per-field token-count totals, summed raw and weighted ONCE at the end.
    # Summing `derive_wlen` per record would give the same number today and
    # would silently bake the weights into a running total the moment anything
    # here started caching it — the accelerator's stats plane made exactly that
    # mistake (SR-TUNE, 2026-08-24).
    total_flen = [0] * len(TF_FIELDS)
    df: dict[str, int] = dict.fromkeys(query_hashes, 0)
    candidates: list[dict] = []
    section_on = scoring.section_on

    for path in store_mod.iter_shard_paths(root):
        _, lines = store_mod.raw_record_lines(path)
        for line in lines:
            total_docs += 1
            flen = _flen_from_line(line)
            if flen is not None:
                for i, count in enumerate(flen):
                    total_flen[i] += count
            # The substring check is a prefilter only: a query hash can appear
            # as a literal 16-hex string somewhere outside `terms` (a title,
            # an id, a sha — anything quoted) without the document actually
            # containing that term. Once a line is worth parsing at all, `df`
            # is counted from the parsed record's own `terms` keys, which is
            # exact, rather than from the raw substring match, which is not.
            # Getting this wrong is exactly the class of bug derive/build.py's
            # `_assert_invariants` tripwire exists to catch on the accelerator
            # side — this is the same fix on the scan side, at the root.
            if anchor_on:
                for m in _EDGE_ANCHOR_RE.finditer(line):
                    length = int(m.group("len"))
                    dst = m.group("dst").decode("utf-8")
                    anchor_len[dst] = anchor_len.get(dst, 0) + length
                    total_anchor_len += length
            if not any(pattern in line for pattern in patterns.values()):
                continue
            record = json.loads(line)
            record_terms = record.get("terms", {})
            for h in query_hashes:
                if h in record_terms:
                    df[h] += 1
            if anchor_on:
                # This line was parsed because a query hash appears somewhere
                # in it — and an `at` key IS such an appearance, so a document
                # that merely *links* using the word is parsed here for free.
                # That is the whole reason anchor terms are committed as
                # hashes: the prefilter finds them at no extra cost.
                _fold_out_edges(record, wanted, anchor_tf)
            candidates.append(record)

    if section_on:
        sections_mod.attach(root, candidates, query_hashes)

    if anchor_on:
        _add_anchor_only_candidates(root, candidates, anchor_tf)
        for record in candidates:
            doc_id = record["id"]
            record["atf"] = anchor_tf.get(doc_id, {})
            record["alen"] = anchor_len.get(doc_id, 0)

    return candidates, df, total_docs, total_flen, total_anchor_len


def _fold_out_edges(record: dict, wanted: set[bytes], anchor_tf: dict[str, dict[str, int]]) -> None:
    """Add this record's out-edge anchor terms to their targets' bags.

    Only the query's hashes are kept. The full `at` map is on the line either
    way, so restricting here is about what the fold has to carry, not about
    what it has to read.
    """
    for edge in record.get("edges", ()):
        at = edge.get("at")
        if not at:
            continue
        dst = edge["dst"]
        for term, count in at.items():
            if term.encode("ascii") in wanted:
                bag = anchor_tf.setdefault(dst, {})
                bag[term] = bag.get(term, 0) + count


def _add_anchor_only_candidates(
    root: Path, candidates: list[dict], anchor_tf: dict[str, dict[str, int]]
) -> None:
    """Fetch the records reachable ONLY through a linker's wording.

    🔴 **This is the retrieval half of W-168 step 1.** A scoring fold alone
    changes nothing for these documents: their own lines carry none of the
    query's hashes, so the prefilter above never parsed them and they are not
    in `candidates` at all.

    **`shard_for(id)` is what makes the second pass cheap** — a document's id
    names the one shard it can be in, so this reads at most one shard per
    missing document rather than re-scanning the corpus, and reads nothing
    when nobody linked using the query's words.

    ⚠ **`df` is deliberately NOT counted here.** A document whose own `terms`
    carry the hash was already parsed and counted in the pass above; counting
    it again would double it, and counting one that does not carry the hash
    would make `df` mean something the accelerator's postings-derived `df`
    does not.
    """
    # Every key here is a `ref` edge's `dst`, so every key is a document id:
    # only `ref` edges carry `at`, and a `tag` node is never a `ref` target.
    missing = set(anchor_tf) - {record["id"] for record in candidates}
    by_shard: dict[str, set[str]] = {}
    for doc_id in missing:
        by_shard.setdefault(store_mod.shard_for(doc_id), set()).add(doc_id)
    for shard in sorted(by_shard):
        path = store_mod.shard_path(root, shard)
        if not path.exists():
            continue
        _, lines = store_mod.raw_record_lines(path)
        ids = by_shard[shard]
        for line in lines:
            record = json.loads(line)
            if record["id"] in ids:
                candidates.append(record)


def ask(
    root: Path,
    query: str,
    top: int,
    *,
    archived_dirs: frozenset[str] = frozenset(),
    weighting=None,
    scoring: Scoring,
    stats_out: dict | None = None,
    expansion=None,
) -> list[AskResult]:
    """The reference path. `expansion` is W-109's `Expansion`, or `None`.

    ⚠ **Candidates are collected over the expansion's hashes too**, so an
    expansion term can lift a document the original query already matches.
    A document that matches *only* expansion terms becomes a candidate here and
    is dropped by `rank()` — the guard lives there because it is the one
    function both paths reach.
    """
    query_hashes = query_term_hashes(query, ids_mod.for_root(root))
    if not query_hashes:
        # A query that tokenizes to nothing still owes the caller its corpus
        # statistics, or `confidence` cannot tell "no terms" from "not run".
        if stats_out is not None:
            stats_out.setdefault("df", {})
            stats_out.setdefault("n", 0)
        return []
    collect = list(expansion.hashes) if expansion is not None else query_hashes
    candidates, df, corpus = scan_candidates(root, collect, scoring=scoring)
    return rank(
        candidates, collect, df, corpus, top,
        archived_dirs=archived_dirs,
        weighting=weighting, scoring=scoring, stats_out=stats_out,
        expansion=expansion,
    )


# -- W-300: one query over many segments (SR-PKG-INDEX decision 10) ----------


@dataclass(frozen=True)
class Segment:
    """One index the merged query ranks over.

    `root` is laid out as a repository — the repository itself, or a pinned
    package's verified runtime under `.fux/runtime/pkg/<name>@<version>/`
    (SR-PKG-INDEX d8) — so the same B2 pass reads either. `package` is the
    pin's name, `None` for the repository; it is copied onto every candidate
    record the segment yields, so a hit can say where it came from.
    """

    root: Path
    package: str | None
    ids: IdentifierRules


def segments_for(root: Path, scope: str) -> list[Segment]:
    """The segments `scope` names, the repository first, then every pin by name.

    🔴 **Every pin is verified before a byte of it is read** — `segments.inflate`
    runs `plugins.locate_index`, which refuses a missing, other, drifted or
    FOREIGN segment by name (SR-PKG-INDEX d6, d7), and builds its runtime only
    when the pin digest moved. A foreign `_format`, `analyzer` or `tf_fields`
    therefore stops the query; it is never scored and never skipped.
    """
    from ..constants import fixed
    from ..errors import FuxError

    repo, packages, everything = (fixed("scope", k) for k in ("repo", "packages", "all"))
    if scope not in (repo, packages, everything):
        raise FuxError(f"scope must be one of {repo}, {packages}, {everything} — got {scope!r}")
    out: list[Segment] = []
    if scope in (repo, everything):
        out.append(Segment(root=root, package=None, ids=ids_mod.for_root(root)))
    if scope in (packages, everything):
        from .. import plugins
        from ..derive import segments as segments_mod

        for name, pin in sorted(plugins.indexes(root).items()):
            segments_mod.inflate(root, pin)
            seg_root = segments_mod.segment_dir(root, pin)
            out.append(Segment(root=seg_root, package=name, ids=ids_mod.for_root(seg_root)))
    return out


def merged_hashes(query: str, segments: list[Segment]) -> list[str]:
    """The query hashed ONCE PER DISTINCT `identifiers` digest, unioned in order.

    Term keys are unsalted `blake2b(term)`, so equal tokens meet across
    segments; what differs between segments built under different identifier
    rules is only which canonical identifier terms the analyzer ADDS
    (`RF 118` -> `rf-118`). Hashing once per digest is what lets a package's
    family identifier match inside that package at all.

    **The union is the one hash list every segment is scanned for and `rank()`
    sums over**, in a fixed order: the first segment's hashes, then each later
    digest's new ones. Scanning every segment for the union keeps `df` exact
    for every hash in every segment — a per-segment list would count a
    package-rule term as absent from the repository without having looked.
    """
    by_digest: dict[str, list[str]] = {}
    for segment in segments:
        digest = segment.ids.digest
        if digest not in by_digest:
            by_digest[digest] = query_term_hashes(query, segment.ids)
    return list(dict.fromkeys(h for hashes in by_digest.values() for h in hashes))


def merged_candidates(
    segments: list[Segment], query_hashes: list[str], *, scoring: Scoring
) -> tuple[list[dict], dict[str, int], Corpus]:
    """Every segment's B2 pass, statistics SUMMED, weighted once.

    `df = Σ df`, `n = Σ n`, `total_flen = Σ total_flen` (per field, raw),
    and the anchor total likewise; `avg_wlen` is then derived ONCE from the
    sums, so the merged corpus has one yardstick and a shared `idf`. Anchor
    text folds **within** a segment only: each pass resolves its own edges'
    targets against its own records, so a package's edges never reach the
    repository (W-300 §Hazards).
    """
    candidates: list[dict] = []
    df: dict[str, int] = dict.fromkeys(query_hashes, 0)
    n = 0
    total_flen = [0] * len(TF_FIELDS)
    total_anchor_len = 0
    for segment in segments:
        seg_candidates, seg_df, seg_n, seg_flen, seg_anchor = _scan_segment(
            segment.root, query_hashes, scoring=scoring
        )
        if segment.package is not None:
            for record in seg_candidates:
                record["package"] = segment.package
        candidates.extend(seg_candidates)
        for h in query_hashes:
            df[h] += seg_df[h]
        n += seg_n
        for i, count in enumerate(seg_flen):
            total_flen[i] += count
        total_anchor_len += seg_anchor
    return (
        candidates,
        df,
        Corpus(n=n, total_wlen=derive_wlen(total_flen, scoring, total_anchor_len)),
    )


def merged_ask(
    segments: list[Segment],
    query_hashes: list[str],
    top: int,
    *,
    archived_dirs: frozenset[str] = frozenset(),
    weighting=None,
    scoring: Scoring,
    stats_out: dict | None = None,
    expansion=None,
) -> list[AskResult]:
    """`ask` over several segments — ONE `rank()` call over the union.

    `query_hashes` is `merged_hashes`' list. Scores from separate corpora are
    never fused (`fuse.py` is refused for this by design): the candidates of
    every segment are scored together, against the summed statistics.
    """
    if not query_hashes:
        if stats_out is not None:
            stats_out.setdefault("df", {})
            stats_out.setdefault("n", 0)
        return []
    collect = list(expansion.hashes) if expansion is not None else query_hashes
    candidates, df, corpus = merged_candidates(segments, collect, scoring=scoring)
    return rank(
        candidates, collect, df, corpus, top,
        archived_dirs=archived_dirs,
        weighting=weighting, scoring=scoring, stats_out=stats_out,
        expansion=expansion,
    )
