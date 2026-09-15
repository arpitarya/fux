"""Edge extraction — `ref`/`tag`/`code`, written now, used at M3 (graph lane).

Deterministic and extraction-only: every edge comes off an artifact the
document already contains — a markdown link, a frontmatter tag, or a
backtick-quoted path matching another ingested document. `ref`/`code`
targets that don't resolve to a corpus doc are dangling and dropped (a fact
about the source, not a relationship — archived graph/extract.py's rule).

Grades: `EXTRACTED` (10) for a deterministic, unambiguous resolution;
`AMBIG` (8) for a `code` span that only resolves by basename among several
candidates. `INFERRED` (6, matching the archived EXTRACTED:INFERRED ≈
1.0:0.6 weight ratio) is unused until the enriched tier (M8).

## Anchor terms ride the EDGE — W-168 step 1, option (c)

A `ref` edge carries two extra keys, `at` (anchor term hash -> count) and
`al` (the token total), taken from the **link text** of every markdown link
this document writes to that target.

🔴 **The byte stays on the document that wrote it.** `Edge(src=B, dst=A)`
already lives on `B`'s committed record, so editing `B` rewrites `B`'s bytes
and moves nothing of `A`'s. The field as originally specified — an `anchor`
field on `A`, built from what everyone else calls it — would have made a
committed per-document byte a function of OTHER documents, and the invariant
it breaks is sharper than "no cross-document dependencies":

> **A committed per-document byte is a function of that document alone.
> Everything corpus-wide is a read-time fold.**

`df` and `avg_wlen` are corpus-wide and cost nothing because they are counted
at read time; the anchor fold is the same shape. Ruled by Arpit, 2026-09-15,
option (c) of three. `tests/ingest/test_edges.py::
test_edge_text_is_a_function_of_its_source_alone` is the gate: edit the
linker, re-index it alone, assert the target's committed bytes did not move.

## Why HASHES and not the anchor string

[L2](../../records/0004_LAW-2-content-never-durable.md) — content is never
durable outside its source system. Link text is a verbatim fragment of the
source document's prose, so committing it plainly would put content in the
index and would need L5's hashed-meta branch on top. A term hash is a
*statistic*, which is what the index holds, and it is already the currency
`terms` is written in — so the scan's byte prefilter finds an anchor source
by the same substring check it already runs, at no extra cost.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import PurePosixPath

from ..query.tokenize import tokenize
from .parse import ParsedDoc

#: The namespace a tag node lives in. Minted here because this is the only
#: place a tag edge is created; `graph/model.py` imports it rather than
#: keeping a second copy, because two spellings of `"tag:"` that drift apart
#: would silently split the graph into documents and orphaned labels.
TAG_PREFIX = "tag:"

EXTRACTED_GRADE = 10
AMBIG_GRADE = 8
INFERRED_GRADE = 6

#: ⚠ **Group 1 is the ANCHOR TEXT and it used to be discarded.** It sat in a
#: non-capturing class until W-168 step 1, so the proposal's *"edges are
#: already extracted"* was half true: the edges were, the words were not.
_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
_INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")


@dataclass(frozen=True)
class DocScan:
    #: `(anchor text, target)` pairs, in document order. **Was a list of bare
    #: targets until W-168 step 1** — the shape had to change because the words
    #: are not extracted anywhere else in the engine.
    links: list[tuple[str, str]]
    code_spans: list[str]
    tags: list[str]
    #: Frontmatter `supersedes:` — paths this document retires. **Declared,
    #: never inferred** (W-76 Phase 2): nothing guesses supersession from
    #: titles, numbering or dates. Same rule SR-DIR-LIST decision 10 applies
    #: to `archived`, for the same reason -- a heuristic that is exact for the
    #: repo that invented it is a silent convention for everyone else.
    supersedes: list[str]


def scan(doc: ParsedDoc) -> DocScan:
    return DocScan(
        links=[(m.group(1), m.group(2)) for m in _LINK_RE.finditer(doc.body)],
        code_spans=[m.group(1) for m in _INLINE_CODE_RE.finditer(doc.body)],
        tags=_scan_tags(doc.meta),
        supersedes=_scan_supersedes(doc.meta),
    )


def basename_index(known_ids: set[str]) -> dict[str, list[str]]:
    """basename -> sorted doc ids sharing it — for ambiguous `code` resolution."""
    index: dict[str, list[str]] = {}
    for doc_id in known_ids:
        basename = doc_id.rsplit("/", 1)[-1]
        index.setdefault(basename, []).append(doc_id)
    for ids in index.values():
        ids.sort()
    return index


def resolve(
    doc_id: str,
    doc_scan: DocScan,
    known_ids: set[str],
    by_basename: dict[str, list[str]],
    hash_of: Callable[[str], str],
) -> list[dict]:
    """This document's resolved edges, with anchor terms on the `ref` ones.

    `hash_of` is the run's single `CollisionTracker.hash_of` — the same
    function `terms` is hashed through, passed in rather than imported so this
    module stays free of `store` and so a caller cannot silently hash anchor
    terms with a *second* tracker. It has **no default**: an anchor-less
    fallback would be a silent off-switch on a retrieval feature, which is the
    one kind of bug a query cannot show you.
    """
    edges: dict[tuple[str, str], int] = {}
    #: dst -> raw anchor term counts, merged across every link this document
    #: writes to that target. Merged rather than kept per-link because
    #: `edges` is already deduplicated by `(kind, dst)` — two links from B to
    #: A are one edge, so their words are one bag.
    anchor: dict[str, Counter] = {}

    for text, target in doc_scan.links:
        dst = _resolve_ref(doc_id, target, known_ids)
        if dst and dst != doc_id:
            edges[("ref", dst)] = EXTRACTED_GRADE
            # Analyzed with the engine's own tokenizer, so an anchor term and
            # a body term for the same word are the same hash. A link whose
            # text is empty, punctuation, or nothing but stopwords contributes
            # no terms and the edge keeps its pre-W-168 shape.
            terms = tokenize(text)
            if terms:
                anchor.setdefault(dst, Counter()).update(terms)

    for target in doc_scan.supersedes:
        # **Repo-root relative, not document relative.** A markdown link is
        # written relative to the file it sits in, so `_resolve_ref` resolves
        # it that way. A frontmatter `supersedes:` entry is a DECLARATION, and
        # every other declared path in fux -- `.fux/sources/dirs`, its `!`
        # exclusions, `[priority]` keys -- is written from the repo root. A
        # declaration that resolved relative to its own directory would be the
        # only one in the system that did.
        #
        # Reusing `_resolve_ref`'s existing absolute branch rather than adding
        # a second resolver: one code path, one set of `/index.md` fallbacks.
        dst = _resolve_ref(doc_id, "/" + target.lstrip("/"), known_ids)
        if dst and dst != doc_id:
            # Graded EXTRACTED: the document said so in its own frontmatter.
            edges[("supersedes", dst)] = EXTRACTED_GRADE

    for tag in doc_scan.tags:
        edges[("tag", f"{TAG_PREFIX}{tag}")] = EXTRACTED_GRADE

    for span in doc_scan.code_spans:
        resolved = _resolve_code(span, known_ids, by_basename)
        if resolved and resolved[0] != doc_id:
            dst, grade = resolved
            edges[("code", dst)] = max(grade, edges.get(("code", dst), 0))

    out: list[dict] = []
    for (kind, dst), grade in sorted(edges.items()):
        edge = {"kind": kind, "dst": dst, "grade": grade}
        counts = anchor.get(dst) if kind == "ref" else None
        if counts:
            # `al` is `sum(at.values())` and is therefore redundant — kept
            # because `query/scan.py` needs a document's anchor LENGTH off the
            # raw bytes of every line in the corpus, candidate or not, and a
            # byte regex can read one integer where summing a map cannot.
            # `derive/_build.py` asserts the two agree on every record, so the
            # redundancy cannot drift.
            edge["at"] = {hash_of(term): count for term, count in sorted(counts.items())}
            edge["al"] = sum(counts.values())
        out.append(edge)
    return out


def _resolve_ref(doc_id: str, target: str, known_ids: set[str]) -> str | None:
    target = target.split("#", 1)[0].strip()
    if not target or target.startswith(("mailto:", "tel:")):
        return None
    if target.startswith(("http://", "https://")):
        # An absolute link resolves iff that exact URL is itself an ingested
        # doc (SR-URL-INGEST); anything else is dangling and dropped, same rule
        # as an unresolved path.
        candidate_id = f"url:{target}"
        return candidate_id if candidate_id in known_ids else None
    if doc_id.startswith("url:"):
        return None  # relative links inside fetched pages are not repo paths
    rel = doc_id.removeprefix("file:")
    if target.startswith("/"):
        candidate = target.lstrip("/")
    else:
        base = PurePosixPath(rel).parent
        candidate = str(PurePosixPath(base) / target) if str(base) != "." else target
    candidate = _normalize_path(candidate)
    for probe in (candidate, f"{candidate}/index.md", f"{candidate}/README.md"):
        candidate_id = f"file:{_normalize_path(probe)}"
        if candidate_id in known_ids:
            return candidate_id
    return None


def _resolve_code(span: str, known_ids: set[str], by_basename: dict[str, list[str]]) -> tuple[str, int] | None:
    span = span.strip()
    if not span or " " in span or "\t" in span:
        return None
    candidate_id = f"file:{_normalize_path(span.lstrip('/'))}"
    if candidate_id in known_ids:
        return candidate_id, EXTRACTED_GRADE
    basename = span.rsplit("/", 1)[-1]
    matches = by_basename.get(basename, [])
    if len(matches) == 1:
        return matches[0], AMBIG_GRADE
    return None


def _normalize_path(path: str) -> str:
    parts: list[str] = []
    for part in path.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if parts:
                parts.pop()
            continue
        parts.append(part)
    return "/".join(parts)


def _scan_supersedes(meta: dict) -> list[str]:
    """`supersedes:` as a list, or a single string, or absent."""
    raw = meta.get("supersedes")
    if isinstance(raw, str):
        return [raw.strip()] if raw.strip() else []
    if isinstance(raw, list):
        return [item.strip() for item in raw if isinstance(item, str) and item.strip()]
    return []


def _scan_tags(meta: dict) -> list[str]:
    raw = meta.get("tags")
    if isinstance(raw, str):
        raw = [t.strip() for t in raw.split(",")]
    if not isinstance(raw, list):
        return []
    return sorted({str(t).strip().lower() for t in raw if str(t).strip()})
