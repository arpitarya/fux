"""Pass B — the corpus fold, and the one-document X-ray.

**W-220** ([SR-INSPECT](../../../records/0156_inspect.md) decisions 18–20). Four
zoom levels, and this module owns the three that are folds:

- **L1 · segments** — decoder × top folder × archived, one report card each.
- **L2 · triage** — one row per document that carries a finding, worst first.
  *Worst* is the **number** of findings, then the id: a count a reader can
  check, never a weighted score (decision 11 refuses a single number).
- **L3 · one document** — `document()`, computed on demand for the one a person
  clicked, and never for all of them up front (ruled 2026-09-23).

L0, the headline, is `__init__.render_markdown`'s.

⚠ **Nothing corpus-wide is stored per document.** The facts cache holds what a
document is on its own; which other documents share its title, and which link to
it, are read off the index at fold time — the invariant `ingest/edges.py` keeps
for the same reason: a per-document fact that depends on the corpus is stale the
moment any other document changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

__all__ = [
    "Fold",
    "LINK_TARGET_SHARE",
    "fold",
    "document",
]

#: A document whose inline link targets are at least this share of its body
#: tokens is flagged. **Provisional**, in SR-INSPECT's sense: tuned to no
#: corpus, printed with that word, and a flag is *attention*, never a failure.
LINK_TARGET_SHARE = 0.10

#: The findings a triage row can carry, in the order the report names them.
FINDINGS = (
    "unreadable",
    "no text",
    "no distinctive term",
    "shared title",
    "title probe miss",
    "word-cut passages",
    "page chrome indexed",
    "link targets indexed",
    "orphan",
)


@dataclass
class Fold:
    identity: dict = field(default_factory=dict)
    segments: list = field(default_factory=list)
    chunks: dict = field(default_factory=dict)
    probes: dict | None = None
    triage: list = field(default_factory=list)
    triage_count: int = 0
    documents: list = field(default_factory=list)


def _folder(loc: str, doc_id: str) -> str:
    if doc_id.startswith("url:"):
        return "url:"
    return loc.split("/", 1)[0] + "/" if "/" in loc else "."


def _title_groups(view) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for doc in view.docs:
        groups.setdefault((doc.title or "").strip(), []).append(doc.id)
    return groups


def fold(view, facts, findability, probes=None, *, top: int = 20) -> Fold:
    out = Fold()
    groups = _title_groups(view)
    shared = {title: sorted(ids) for title, ids in groups.items() if len(ids) > 1}
    peers = {doc_id: len(ids) - 1 for ids in shared.values() for doc_id in ids}
    unfindable = set(findability.unfindable)
    linked = {src for src, _k, _d, _g in view.edges} | {dst for _s, _k, dst, _g in view.edges}
    edges_by_src: dict[str, set] = {}
    for src, kind, dst, _g in view.edges:
        edges_by_src.setdefault(src, set()).add((kind, dst))

    # ---- identity ------------------------------------------------------
    data_docs = [d for d in view.docs if (facts.by_id.get(d.id) or {}).get("kind") == "data"]
    out.identity = {
        "groups": len(shared),
        "documents_sharing": len(peers),
        "documents": view.n,
        "data_documents": len(data_docs),
        "data_identifiable": sum(1 for d in data_docs if d.id not in peers),
        "top": [
            {"title": title, "count": len(ids), "members": ids[:5]}
            for title, ids in sorted(shared.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:top]
        ],
    }

    # ---- segments and chunks ------------------------------------------
    cards: dict[tuple, dict] = {}
    cuts_total = {"author": 0, "line": 0, "word": 0}
    by_decoder: dict[str, dict] = {}
    for doc in view.docs:
        f = facts.by_id.get(doc.id) or {}
        key = (f.get("decoder", "?"), _folder(doc.loc, doc.id), bool(doc.archived))
        card = cards.setdefault(key, {
            "decoder": key[0], "folder": key[1], "archived": key[2], "documents": 0,
            "unreadable": 0, "passages": 0, "word_cut_passages": 0, "body_tokens": 0,
            "link_target_tokens": 0, "chrome_tokens": 0, "shared_title": 0,
            "probed": 0, "title_in_top10": 0,
        })
        card["documents"] += 1
        card["unreadable"] += 0 if f.get("readable") else 1
        card["passages"] += f.get("passages", 0)
        card["word_cut_passages"] += (f.get("cuts") or {}).get("word", 0)
        card["body_tokens"] += f.get("body_tokens", 0)
        card["link_target_tokens"] += f.get("link_target_tokens", 0)
        card["chrome_tokens"] += f.get("chrome_tokens", 0)
        card["shared_title"] += 1 if doc.id in peers else 0
        if probes is not None and doc.id in probes.by_id:
            card["probed"] += 1
            card["title_in_top10"] += 1 if probes.by_id[doc.id]["title"] is not None else 0
        for rung, n in (f.get("cuts") or {}).items():
            cuts_total[rung] = cuts_total.get(rung, 0) + n
        dec = by_decoder.setdefault(f.get("decoder", "?"), {"documents": 0, "passages": 0, "word": 0})
        dec["documents"] += 1
        dec["passages"] += f.get("passages", 0)
        dec["word"] += (f.get("cuts") or {}).get("word", 0)
    out.segments = [cards[k] for k in sorted(cards, key=lambda k: (-cards[k]["documents"], k))]
    out.chunks = {
        "passages": sum(cuts_total.values()),
        "cuts": cuts_total,
        "by_decoder": {
            name: {**row, "word_share": (row["word"] / row["passages"]) if row["passages"] else 0.0}
            for name, row in sorted(by_decoder.items())
        },
    }

    # ---- probes --------------------------------------------------------
    if probes is not None:
        out.probes = _probe_lens(view, facts, probes, peers, top=top)

    # ---- per-document rows and the triage queue ------------------------
    rows = []
    for doc in view.docs:
        f = facts.by_id.get(doc.id) or {}
        probe = probes.by_id.get(doc.id) if probes is not None else None
        flags = []
        if not f.get("readable"):
            flags.append("unreadable")
        elif not f.get("passages"):
            flags.append("no text")
        if doc.id in unfindable:
            flags.append("no distinctive term")
        if doc.id in peers:
            flags.append("shared title")
        if probe is not None and probe["title"] is None:
            flags.append("title probe miss")
        if (f.get("cuts") or {}).get("word", 0):
            flags.append("word-cut passages")
        if f.get("chrome_tokens", 0):
            flags.append("page chrome indexed")
        body = f.get("body_tokens", 0)
        if body and f.get("link_target_tokens", 0) / body >= LINK_TARGET_SHARE:
            flags.append("link targets indexed")
        if doc.id not in linked:
            flags.append("orphan")
        edges = [list(e) for e in sorted(edges_by_src.get(doc.id, ()))]
        row = {
            "id": doc.id,
            "loc": doc.loc,
            "title": doc.title,
            "decoder": f.get("decoder", "?"),
            "kind": f.get("kind", "prose"),
            "archived": doc.archived,
            "nterms": doc.nterms,
            "flen": list(doc.flen),
            "passages": f.get("passages", 0),
            "word_cuts": (f.get("cuts") or {}).get("word", 0),
            "title_shared_with": peers.get(doc.id, 0),
            "edges": edges,
            "probe": None if probe is None else {
                "title": probe["title"],
                "headings_in_top10": sum(1 for _t, r in probe["headings"] if r is not None),
                "headings": len(probe["headings"]),
            },
            "findings": flags,
        }
        rows.append(row)
    out.documents = rows
    flagged = [r for r in rows if r["findings"]]
    out.triage_count = len(flagged)
    out.triage = sorted(flagged, key=lambda r: (-len(r["findings"]), r["id"]))[:top]
    return out


def _probe_lens(view, facts, probes, peers, *, top: int) -> dict:
    prose_title = prose_n = head_hit = head_n = 0
    data_n = data_ident = data_reach = data_both = 0
    misses = []
    for doc in view.docs:
        row = probes.by_id.get(doc.id)
        if row is None:
            continue
        kind = (facts.by_id.get(doc.id) or {}).get("kind", "prose")
        reached = row["title"] is not None
        if kind == "data":
            data_n += 1
            ident = doc.id not in peers
            data_ident += ident
            data_reach += reached
            data_both += ident and reached
        else:
            prose_n += 1
            prose_title += reached
            head_n += len(row["headings"])
            head_hit += sum(1 for _t, r in row["headings"] if r is not None)
        if not reached:
            misses.append({"id": doc.id, "title": doc.title, "kind": kind})
    return {
        "sampled": probes.sampled,
        "documents": probes.documents,
        "queries": probes.queries,
        "estimate": not probes.whole_corpus,
        "prose": {"documents": prose_n, "title_in_top10": prose_title,
                  "headings": head_n, "headings_in_top10": head_hit},
        "data": {"documents": data_n, "identifiable": data_ident, "reachable": data_reach,
                 "both": data_both},
        "title_misses": misses[: top],
        "title_miss_count": len(misses),
    }


# --------------------------------------------------------------------------
# L3 — one document, on demand
# --------------------------------------------------------------------------


def document(root: Path, view, loc: str, *, passages_cap: int = 200, words: int = 25) -> dict:
    """The X-ray of one document: what was ingested, what was indexed, how it links.

    Computed for this document alone — its facts entry is refreshed through the
    same cache as pass A, and its words are named by re-tokenising **its own**
    fields, redacted, exactly as the dictionary does for the corpus. Nothing here
    walks any other document's bytes.
    """
    from ..errors import FuxError
    from ..ingest import register
    from ..refer._chunk import chunk
    from . import facts as facts_mod

    index = next((i for i, d in enumerate(view.docs) if d.loc == loc or d.id == loc), None)
    if index is None:
        raise FuxError(f"no indexed document at {loc!r}")
    doc = view.docs[index]
    facts = facts_mod.load_or_compute_one(root, view, doc)
    reg = register.read(root).get(doc.loc)

    raw = facts_mod.source_bytes(root, doc.id, doc.loc)
    passage_rows: list[dict] = []
    total_passages = 0
    field_words: dict[str, list] = {}
    if raw is not None:
        text, generated = facts_mod.readable_text(root, doc.id, doc.loc, raw)
        bounds = facts_mod.refer_bounds(root)
        cut = chunk(text, min_passage_bytes=bounds[0], max_passage_bytes=bounds[1],
                    line_numbers=not generated) if text else []
        total_passages = len(cut)
        passage_rows = [
            {"ordinal": p.ordinal, "heading": p.heading, "lines": [p.line_start, p.line_end],
             "bytes": p.nbytes, "cut": p.cut or "author"}
            for p in cut[:passages_cap]
        ]
        field_words = _named_terms(root, view, doc, raw, words=words)

    from ..store import TF_FIELDS

    groups = [d.id for d in view.docs if d.title == doc.title and d.id != doc.id]
    titles = {d.id: d.title for d in view.docs}
    out_edges = sorted({(k, dst) for src, k, dst, _g in view.edges if src == doc.id})
    in_edges = sorted({(k, src) for src, k, dst, _g in view.edges if dst == doc.id})
    return {
        "id": doc.id,
        "loc": doc.loc,
        "title": doc.title,
        "sha": doc.sha,
        "archived": doc.archived,
        "superseded": doc.superseded,
        "register": None if reg is None else {
            "kind": reg.kind, "sha": reg.sha, "decoder": reg.decoder, "fetcher": reg.fetcher,
        },
        "ingested": {k: v for k, v in sorted(facts.items()) if k != "key"},
        "indexed": {
            "fields": dict(zip(TF_FIELDS, doc.flen)),
            "distinct_terms": doc.nterms,
            "headings": list(doc.phrases),
            "words": field_words,
        },
        "passages": passage_rows,
        "passage_count": total_passages,
        "links": {
            "out": [{"kind": k, "id": dst, "title": titles.get(dst, "")} for k, dst in out_edges],
            "in": [{"kind": k, "id": src, "title": titles.get(src, "")} for k, src in in_edges],
        },
        "identity": {"shares_title_with": groups[:20], "shares_title_count": len(groups)},
    }


def _named_terms(root: Path, view, doc, raw: bytes, *, words: int) -> dict[str, list]:
    """Per field, this document's rarest words — named, with `df` from the index.

    Re-tokenised from the document's own bytes with the repository's `pii.toml`
    applied first, in `dictionary.build`'s order, so a value the index never held
    is never printed here either.
    """
    from ..ingest import pii as pii_mod
    from ..ingest.extract import _headings_and_body, _title
    from ..ingest.parse import parse_document
    from ..query.tokenize import tokenize_pairs
    from ..store import TF_FIELDS, term_hash
    from .dictionary import _enrichment

    parsed = parse_document(raw, doc.loc, root) if not doc.id.startswith("url:") else None
    if parsed is None:
        return {}
    try:
        rules = pii_mod.load(root)
    except Exception:  # pragma: no cover
        rules = ()
    body, meta = parsed.body, parsed.meta
    if rules:
        body, _ = pii_mod.redact(rules, body)
        front = meta.get("title")
        if isinstance(front, str) and front:
            redacted, hits = pii_mod.redact(rules, front)
            if hits:
                meta = {**meta, "title": redacted}
    headings, stripped = _headings_and_body(doc.loc, body)
    texts = (
        stripped,
        " ".join(headings),
        _title(meta, headings, doc.loc),
        doc.loc.replace("/", " ").replace(".", " "),
        _enrichment(root, doc.sha, rules),
    )
    df_of = _df_index(view)
    out: dict[str, list] = {}
    for name, text in zip(TF_FIELDS, texts):
        counts: dict[str, list] = {}
        for surface, analyzed in tokenize_pairs(text or ""):
            h = term_hash(analyzed)
            row = counts.setdefault(h, [surface, analyzed, 0])
            row[2] += 1
        rows = [
            {"word": s, "term": a, "tf": tf, "df": df_of.get(h, 0)}
            for h, (s, a, tf) in counts.items()
        ]
        rows.sort(key=lambda r: (r["df"], -r["tf"], r["term"]))
        out[name] = rows[:words]
    return out


def _df_index(view) -> dict[str, int]:
    cached = getattr(view, "_df_by_hash", None)
    if cached is None:
        cached = {h: view.df[i] for i, h in enumerate(view.term_of)}
        try:
            view._df_by_hash = cached
        except AttributeError:  # pragma: no cover
            pass
    return cached
